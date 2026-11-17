# Evaluation Results

This directory contains the output of `agent/tests/evaluation_runner.py`.

## File naming convention

```
{mode}_{YYYYMMDD_HHMMSS}.csv
```

- `classical_*.csv` — results with `LETZEVAL_AGENT_MODE=classical`
- `llm_*.csv` — results with `LETZEVAL_AGENT_MODE=llm`

## How to run the evaluation

Start the agent in the mode you want to test:

```bash
# Terminal 1 — start agent in classical mode
LETZEVAL_AGENT_MODE=classical /home/adhav/besser-demo/.venv/bin/python3 agent.py

# Terminal 2 — run evaluation
cd leaderboard/agent
LETZEVAL_AGENT_MODE=classical \
  /home/adhav/besser-demo/.venv/bin/python3 tests/evaluation_runner.py \
  --url ws://localhost:8765 \
  --timeout 30 \
  --output evaluation_results/classical_run.csv
```

Then repeat with `LETZEVAL_AGENT_MODE=llm` (requires a configured LLM provider).

## Result CSV columns

| Column | Description |
|---|---|
| `id` | Test case ID (see `tests/evaluation_cases.py`) |
| `input` | User message sent to the agent |
| `lang` | UI language code |
| `expected_intent` | Expected BAF intent |
| `expected_answer` | Expected substring in correct response |
| `clarification_ok` | Whether requesting clarification is a correct outcome |
| `notes` | What the case tests |
| `response` | Agent's response (truncated to 500 chars) |
| `has_options` | True if agent sent clickable options |
| `score` | `correct` / `partial` / `wrong` / `timeout` / `error` |
| `latency_s` | Time from send to last response |
| `error` | Connection or protocol error, if any |

## Score definitions

- **correct** — expected answer substring found, or clarification given when `clarification_ok=True`
- **partial** — response is non-empty but auto-scoring inconclusive; requires manual review
- **wrong** — response contradicts expected answer
- **timeout** — no response within the per-case timeout
- **error** — connection or parsing error
