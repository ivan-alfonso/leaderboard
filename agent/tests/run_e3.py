"""
E3 evaluation runner — Translation checkpoint.

Usage (from leaderboard/agent/):
    /home/adhav/besser-demo/.venv/bin/python3 tests/run_e3.py \
        [--url ws://localhost:8765] [--timeout 60] [--output evaluation_results/E3/openai_E3.csv]
"""
import argparse
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tests.e3_translation_cases import E3_CASES

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


def _score_response(case: dict, response_text: str) -> str:
    expected = case.get('expected_answer', '')
    text = response_text.lower()

    if expected and expected.lower() in text:
        return 'correct'
    if case.get('expected_intent') == 'out_of_scope':
        if any(k in text for k in ('outside', 'only', 'leaderboard', 'cannot', "can't")):
            return 'correct'
    if not expected and len(response_text.strip()) > 20:
        return 'partial'
    return 'wrong'


async def _run_case(url: str, case: dict, timeout: float, quiet: float = 20.0) -> dict:
    start = time.monotonic()
    texts: list[str] = []
    has_opts = False
    error_msg = ''

    try:
        async with websockets.connect(url, open_timeout=10) as ws:
            await ws.send(json.dumps({
                'action': 'user_set_variable',
                'message': {'ui_language': case.get('lang', 'en'), '_eval_case_id': str(case['id'])},
            }))
            # Drain greeting
            drain = time.monotonic() + 1.5
            while time.monotonic() < drain:
                try:
                    await asyncio.wait_for(ws.recv(), timeout=drain - time.monotonic())
                except Exception:
                    break

            await ws.send(json.dumps({'action': 'user_message', 'message': case['input']}))

            deadline = start + timeout
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, quiet))
                    payload = json.loads(raw)
                    action = payload.get('action', '')
                    msg = payload.get('message', '')
                    if action == 'agent_reply_options':
                        try:
                            opts = list(json.loads(msg).values())
                            texts.append('[OPTIONS: ' + ', '.join(opts) + ']')
                            has_opts = True
                        except Exception:
                            pass
                    elif isinstance(msg, str) and msg and not msg.startswith('__UI_ACTION__'):
                        texts.append(msg)
                except asyncio.TimeoutError:
                    if texts or has_opts:
                        break
    except Exception as exc:
        error_msg = str(exc)

    elapsed = round(time.monotonic() - start, 2)
    full = '\n'.join(texts)

    if error_msg:
        score = 'error'
    elif not full:
        score = 'timeout'
    else:
        score = _score_response(case, full)

    return {
        'id': case['id'],
        'input': case['input'],
        'lang': case.get('lang', 'en'),
        'expected_intent': case['expected_intent'],
        'expected_answer': case.get('expected_answer', ''),
        'clarification_ok': case.get('clarification_ok', False),
        'notes': case.get('notes', ''),
        'response': full[:600],
        'has_options': has_opts,
        'score': score,
        'latency_s': elapsed,
        'error': error_msg,
    }


async def _run_all(url: str, cases: list[dict], timeout: float,
                   quiet: float, checkpoint: str) -> list[dict]:
    results = []
    _init = False

    def _save(r: dict) -> None:
        nonlocal _init
        if not checkpoint:
            return
        fields = ['id', 'input', 'lang', 'expected_intent', 'expected_answer',
                  'clarification_ok', 'notes', 'response', 'has_options',
                  'score', 'latency_s', 'error']
        os.makedirs(os.path.dirname(os.path.abspath(checkpoint)), exist_ok=True)
        write_hdr = not _init and not os.path.exists(checkpoint)
        with open(checkpoint, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if write_hdr:
                w.writeheader()
            w.writerow({k: r.get(k, '') for k in fields})
        _init = True

    for i, case in enumerate(cases):
        print(f"  [{i+1:>2}/{len(cases)}] {case['id']} [{case.get('lang','en').upper()}] {case['input'][:55]!r}...", end='', flush=True)
        r = await _run_case(url, case, timeout, quiet)
        print(f" → {r['score']} ({r['latency_s']}s)")
        results.append(r)
        _save(r)
        await asyncio.sleep(0.5)
    return results


def _summary(results: list[dict]) -> None:
    total = len(results)
    counts: dict[str, int] = {}
    for r in results:
        counts[r['score']] = counts.get(r['score'], 0) + 1

    correct = counts.get('correct', 0)
    partial = counts.get('partial', 0)
    wrong = counts.get('wrong', 0)
    timeout = counts.get('timeout', 0)
    error = counts.get('error', 0)

    print("\n── E3 Summary ───────────────────────────────────────────")
    print(f"  Total         : {total}")
    print(f"  Correct       : {correct}  ({100*correct/total:.1f}%)")
    print(f"  Partial       : {partial}  (manual language-quality review needed)")
    print(f"  Wrong         : {wrong}")
    print(f"  Timeout       : {timeout}")
    print(f"  Error         : {error}")
    avg = sum(r['latency_s'] for r in results) / total if total else 0
    print(f"  Avg latency   : {avg:.2f}s")
    print()

    # Per-language breakdown
    langs_seen = sorted({r['lang'] for r in results})
    print("── Per language ─────────────────────────────────────────")
    for lg in langs_seen:
        sub = [r for r in results if r['lang'] == lg]
        c = sum(1 for r in sub if r['score'] == 'correct')
        p = sum(1 for r in sub if r['score'] == 'partial')
        w = sum(1 for r in sub if r['score'] in ('wrong', 'timeout', 'error'))
        print(f"  {lg.upper():3s}  correct={c}  partial={p}  wrong/err={w}  (n={len(sub)})")

    if wrong or timeout or error:
        print("\n── Failed cases ─────────────────────────────────────────")
        for r in results:
            if r['score'] in ('wrong', 'timeout', 'error'):
                print(f"  [{r['id']}] {r['score'].upper():8s}  [{r['lang'].upper()}] {r['input'][:50]!r}")
                if r['error']:
                    print(f"           Error:  {r['error']}")
                elif r['response']:
                    print(f"           Got:    {r['response'][:100]!r}")


def _save_csv(results: list[dict], path: str) -> None:
    fields = ['id', 'input', 'lang', 'expected_intent', 'expected_answer',
              'clarification_ok', 'notes', 'response', 'has_options',
              'score', 'latency_s', 'error']
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, '') for k in fields})
    print(f"\nResults saved → {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="E3 translation evaluation")
    ap.add_argument('--url',           default='ws://localhost:8765')
    ap.add_argument('--timeout',       type=float, default=60.0)
    ap.add_argument('--quiet-timeout', type=float, default=20.0,
                    help='Seconds of silence after last message (default 20 for LLM+translation)')
    ap.add_argument('--output',        default='evaluation_results/E3/openai_E3.csv')
    args = ap.parse_args()

    if not HAS_WEBSOCKETS:
        print("ERROR: install websockets  (pip install websockets)")
        sys.exit(1)

    agent_mode = os.environ.get('LETZEVAL_AGENT_MODE', 'llm')
    print(f"LëtzEval E3 — Translation evaluation")
    print(f"  URL           : {args.url}")
    print(f"  Mode          : {agent_mode}")
    print(f"  Cases         : {len(E3_CASES)}")
    print(f"  Timeout       : {args.timeout}s | Quiet: {args.quiet_timeout}s")
    print(f"  Output        : {args.output}")
    print()

    results = asyncio.run(_run_all(args.url, E3_CASES, args.timeout,
                                   args.quiet_timeout, args.output))
    _summary(results)
    _save_csv(results, args.output)


if __name__ == '__main__':
    main()
