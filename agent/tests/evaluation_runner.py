"""
Evaluation runner for LëtzEval BAF agent — Mode A (classical) vs Mode B (LLM).

Usage (from leaderboard/agent/):
    python tests/evaluation_runner.py [--url ws://localhost:8765]
                                      [--timeout 30]
                                      [--output evaluation_results/results.csv]

The runner connects to the running agent via WebSocket, sends each test case,
waits for all responses (up to --timeout seconds), and records the outcome.

Run twice — once with LETZEVAL_AGENT_MODE=classical and once with =llm —
and compare the two output CSV files.

Results are NEVER fabricated; if the agent does not respond within the timeout
the row is recorded as a timeout.
"""
import argparse
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tests.evaluation_cases import CASES
try:
    from tests.holdout_cases import HOLDOUT_CASES
except ImportError:
    HOLDOUT_CASES = []

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


# ── Result helpers ────────────────────────────────────────────────────────────

def _score_response(case: dict, response_text: str, response_type: str) -> str:
    """Return 'correct', 'partial', 'wrong', or 'clarification' for a response.

    Evaluation logic:
    - If expected_answer is non-empty: 'correct' if the substring appears in response.
    - If clarification_ok and response indicates clarification: 'correct'.
    - If expected_answer is empty and response is non-empty: 'partial' (content check needed).
    - Otherwise: 'wrong'.
    """
    expected_answer = case.get('expected_answer', '')
    clarification_ok = case.get('clarification_ok', False)

    text = response_text.lower()

    # Check if it's a clarification/options response
    is_clarification = (
        response_type == 'options'
        or 'which' in text
        or 'please specify' in text
        or 'clarif' in text
        or 'multiple' in text
        or 'which model' in text
        or 'could you specify' in text
    )
    if is_clarification and clarification_ok:
        return 'correct'

    # Check expected answer substring
    if expected_answer and expected_answer.lower() in text:
        return 'correct'

    # For out_of_scope, check that the reply doesn't invent a score
    if case.get('expected_intent') == 'out_of_scope':
        if any(kw in text for kw in ('outside', 'only', 'leaderboard', 'cannot', "can't", 'sorry')):
            return 'correct'

    # If no numeric answer expected but response is substantive
    if not expected_answer and len(response_text.strip()) > 20:
        return 'partial'  # manual review needed

    return 'wrong'


# ── WebSocket evaluation ──────────────────────────────────────────────────────

async def _run_case(url: str, case: dict, timeout: float, lang: str = 'en',
                   quiet_timeout: float = 3.0) -> dict:
    """Connect, send the test message, collect all agent replies, return result dict."""
    start = time.monotonic()
    collected_texts: list[str] = []
    collected_options: list[list[str]] = []
    final_score = 'timeout'
    error_msg = ''

    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            # Set language and eval case ID (case ID used by debug telemetry)
            await ws.send(json.dumps({'action': 'user_set_variable',
                                      'message': {'ui_language': lang,
                                                  '_eval_case_id': str(case.get('id', ''))}}))


            # Drain the greeting: consume any messages that arrive within 1.5s.
            # These are BAF's automatic greeting/state-entry messages, not answers.
            drain_deadline = time.monotonic() + 1.5
            while time.monotonic() < drain_deadline:
                try:
                    await asyncio.wait_for(ws.recv(),
                                           timeout=drain_deadline - time.monotonic())
                except (asyncio.TimeoutError, Exception):
                    break

            # Send the test message
            await ws.send(json.dumps({'action': 'user_message', 'message': case['input']}))

            # Collect responses until quiet or timeout.
            # quiet_timeout: seconds of silence after the last received message
            # before declaring the agent done.  Use 3s for classical, 20s+ for LLM.
            deadline = start + timeout
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, quiet_timeout))
                    payload = json.loads(raw)
                    action = payload.get('action', '')
                    msg = payload.get('message', '')

                    if action == 'agent_reply_options':
                        try:
                            opts = list(json.loads(msg).values())
                            collected_options.append(opts)
                            collected_texts.append('[OPTIONS: ' + ', '.join(opts) + ']')
                        except Exception:
                            pass
                    elif action in ('agent_reply_str', 'agent_reply_markdown', ''):
                        if isinstance(msg, str) and msg and not msg.startswith('__UI_ACTION__'):
                            collected_texts.append(msg)
                except asyncio.TimeoutError:
                    if collected_texts or collected_options:
                        break   # agent has been quiet for quiet_timeout — assume done
                    # else keep waiting up to deadline
    except Exception as exc:
        error_msg = str(exc)
        final_score = 'error'

    elapsed = round(time.monotonic() - start, 2)
    full_response = '\n'.join(collected_texts)
    has_options = bool(collected_options)
    response_type = 'options' if has_options and not any(
        len(t) > 40 for t in collected_texts if not t.startswith('[OPTIONS')
    ) else 'text'

    if error_msg:
        final_score = 'error'
    elif not full_response:
        final_score = 'timeout'
    else:
        final_score = _score_response(case, full_response, response_type)

    return {
        'id': case['id'],
        'input': case['input'],
        'lang': case['lang'],
        'expected_intent': case['expected_intent'],
        'expected_answer': case.get('expected_answer', ''),
        'clarification_ok': case.get('clarification_ok', False),
        'notes': case.get('notes', ''),
        'response': full_response[:500],
        'has_options': has_options,
        'score': final_score,
        'latency_s': elapsed,
        'error': error_msg,
    }


async def _run_all(url: str, cases: list[dict], timeout: float,
                  quiet_timeout: float = 3.0,
                  checkpoint_path: str = '') -> list[dict]:
    """Run all cases sequentially (avoid overloading the agent).

    If checkpoint_path is set, each completed result is immediately appended
    to that CSV so a crash/interruption doesn't lose finished work.
    The caller is responsible for ensuring checkpoint_path does not already
    contain rows for the cases being run (use --ids to skip completed ones).
    """
    results = []

    # Initialise checkpoint file with header on first write
    _checkpoint_initialised = False

    def _append_checkpoint(result: dict) -> None:
        nonlocal _checkpoint_initialised
        if not checkpoint_path:
            return
        fields = [
            'id', 'input', 'lang', 'expected_intent', 'expected_answer',
            'clarification_ok', 'notes', 'response', 'has_options',
            'score', 'latency_s', 'error',
        ]
        os.makedirs(os.path.dirname(os.path.abspath(checkpoint_path)), exist_ok=True)
        write_header = not _checkpoint_initialised and not os.path.exists(checkpoint_path)
        with open(checkpoint_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if write_header:
                writer.writeheader()
            writer.writerow({k: result.get(k, '') for k in fields})
        _checkpoint_initialised = True

    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] Case {case['id']}: {case['input'][:60]!r}...", end='', flush=True)
        result = await _run_case(url, case, timeout, lang=case.get('lang', 'en'),
                                 quiet_timeout=quiet_timeout)
        print(f" → {result['score']} ({result['latency_s']}s)")
        results.append(result)
        _append_checkpoint(result)
        await asyncio.sleep(0.5)   # small pause between requests
    return results


# ── Report ────────────────────────────────────────────────────────────────────

def _print_summary(results: list[dict]) -> None:
    total = len(results)
    counts = {}
    for r in results:
        counts[r['score']] = counts.get(r['score'], 0) + 1

    correct  = counts.get('correct', 0)
    partial  = counts.get('partial', 0)
    wrong    = counts.get('wrong', 0)
    timeout  = counts.get('timeout', 0)
    error    = counts.get('error', 0)

    print("\n── Summary ──────────────────────────────────────────────")
    print(f"  Total cases   : {total}")
    print(f"  Correct       : {correct}  ({100*correct/total:.1f}%)")
    print(f"  Partial       : {partial}  (manual review needed)")
    print(f"  Wrong         : {wrong}")
    print(f"  Timeout       : {timeout}")
    print(f"  Error         : {error}")
    avg_latency = sum(r['latency_s'] for r in results) / total if total else 0
    print(f"  Avg latency   : {avg_latency:.2f}s")

    if wrong or timeout or error:
        print("\n── Failed cases ─────────────────────────────────────────")
        for r in results:
            if r['score'] in ('wrong', 'timeout', 'error'):
                print(f"  [{str(r['id']):>4s}] {r['score'].upper():8s}  {r['input'][:50]!r}")
                if r['error']:
                    print(f"           Error: {r['error']}")
                elif r['response']:
                    print(f"           Got:   {r['response'][:80]!r}")


def _save_csv(results: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fields = [
        'id', 'input', 'lang', 'expected_intent', 'expected_answer',
        'clarification_ok', 'notes', 'response', 'has_options',
        'score', 'latency_s', 'error',
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, '') for k in fields})
    print(f"\nResults saved → {path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="LëtzEval agent evaluation runner")
    parser.add_argument('--url',     default='ws://localhost:8765', help='Agent WebSocket URL')
    parser.add_argument('--timeout', type=float, default=30.0,     help='Per-case timeout (s)')
    parser.add_argument('--output',  default='',                    help='Output CSV path')
    parser.add_argument('--holdout', action='store_true',
                        help='Run holdout_cases.py instead of evaluation_cases.py')
    parser.add_argument('--ids',           default='',
                        help='Comma-separated case IDs to run (default: all)')
    parser.add_argument('--quiet-timeout', type=float, default=3.0,
                        help='Seconds of silence after last message before declaring done (default 3; '
                             'use 20+ for LLM mode)')
    args = parser.parse_args()

    if not HAS_WEBSOCKETS:
        print("ERROR: 'websockets' package not installed.")
        print("Install with: pip install websockets")
        sys.exit(1)

    # Select case suite
    if args.holdout:
        if not HOLDOUT_CASES:
            print("ERROR: holdout_cases.py not found or HOLDOUT_CASES is empty.")
            sys.exit(1)
        cases = HOLDOUT_CASES
    else:
        cases = CASES

    # Filter cases if --ids specified
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(',')}
        # Support both int IDs (50-case suite) and string IDs like 'H01' (holdout)
        cases = [c for c in cases if str(c['id']) in wanted]

    agent_mode = os.environ.get('LETZEVAL_AGENT_MODE', 'classical')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = args.output or f'evaluation_results/{agent_mode}_{timestamp}.csv'

    print(f"LëtzEval agent evaluation")
    print(f"  URL           : {args.url}")
    print(f"  Mode          : {agent_mode}")
    print(f"  Cases         : {len(cases)}")
    print(f"  Timeout       : {args.timeout}s per case")
    print(f"  Quiet timeout : {args.quiet_timeout}s")
    print(f"  Output        : {output}")
    print()

    results = asyncio.run(_run_all(args.url, cases, args.timeout,
                                   quiet_timeout=args.quiet_timeout,
                                   checkpoint_path=output))
    _print_summary(results)
    # Final write overwrites checkpoint with identical content (consistent header+rows)
    _save_csv(results, output)


if __name__ == '__main__':
    main()
