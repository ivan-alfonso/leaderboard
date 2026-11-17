# Baseline vs. LLM-Assisted Evaluation

## Overview

This document describes the methodology and results of comparing the LëtzEval
BAF assistant in two modes:

- **Mode A — Classical BAF** (`LETZEVAL_AGENT_MODE=classical`): the PyTorch
  intent classifier routes each message directly to a handler state; entity
  extraction is deterministic (regex + fuzzy string matching).
- **Mode B — LLM-assisted BAF** (`LETZEVAL_AGENT_MODE=llm`): every message
  passes through a bounded LLM interpretation state before the handler. The LLM
  extracts intent, model name(s), CEFR level, and category. Its validated output
  is stored in the session and read by the same handler states.

The intent classifier, handler states, and DB access layer are unchanged in
both modes. Mode B does not retrain the classifier.

---

## Architecture

### Mode A (Classical)

```
User message
    │
    ▼
initial_state ──(intent match)──► handler_state ──► DB query ──► response
```

Entity extraction runs inside each handler state using deterministic
`entity_utils.py` functions (regex + trigram Jaccard). The LLM is called
only as a fallback when `resolve_model_name()` returns zero candidates.

### Mode B (LLM-assisted)

```
User message
    │
    ▼
initial_state ──(any intent)──► llm_interpret_state
                                        │
                              LLM routes to intent
                              extracts model/level/cat
                              handles clarification
                                        │
                              ◄─ session._llm_route / _next ─►
                                        │
                          (variable-based transition)
                                        │
                                        ▼
                              handler_state reads _llm_route
                                 skips entity extraction
                                        │
                                  DB query ──► response
```

The LLM interpreter uses a strict system prompt that:
- Defines the allowed intents, CEFR levels, and categories
- Provides the full DB model name catalog as a candidate list
- Instructs the LLM to never invent model names, scores, or facts
- Instructs the LLM to ignore prompt-injection instructions in the user message
- Returns only a validated JSON object — no prose

The JSON output is validated server-side (see `llm/router.py`):
- Intent must be in `ALLOWED_INTENTS`
- CEFR level must be in `ALLOWED_CEFR`
- Category must be in `ALLOWED_CATS`
- Model names must match the DB candidate list (case-insensitive)

### Clickable suggestions

When the LLM (or classical entity extractor) finds multiple candidate models,
the agent sends them as clickable options using BAF's native
`websocket_platform.reply_options()`. The frontend renders them as pill buttons.
Clicking a button sends the model name as a regular user message. The
`llm_interpret_state` (Mode B) or the handler state (Mode A) detects the
pending intent stored in `_pending_route` and continues the original request
with the selected model.

### Input sanitization

Before passing user text to the LLM, `llm/sanitize.py`:
- Normalizes Unicode (NFC)
- Strips control characters (except whitespace)
- Collapses multiple spaces and non-standard whitespace
- Truncates at word boundary to `MAX_INPUT_LENGTH = 500` characters
- **Preserves** meaningful tokens: decimal version numbers (`2.5`), size
  suffixes (`0.5B`, `70B`), dashes in model names (`GPT-6`), slashes

---

## Test cases

50 test cases cover:

| Category | Cases | Description |
|---|---|---|
| Exact model names | 1–5 | Full canonical model names |
| Abbreviations | 6–10 | Partial names, lowercase, no punctuation |
| Version/size variants | 11–15 | Ambiguous Qwen 2 variants; small Llama models |
| Conversational | 16–20 | Incomplete follow-ups, colloquial phrasing |
| Ranking | 21–25 | Top-N, worst-N, Macro Average, licensing filter |
| Comparison | 26–29 | Head-to-head, family names, missing CEFR level |
| Filters | 30–32 | Licensing, CEFR+category filter, reset |
| Multilingual | 33–37 | French, German, Portuguese queries |
| Metrics/methodology | 38–40 | CEFR explanation, Macro Average, data coverage |
| Out-of-scope/injection | 41–45 | Off-topic, prompt injection, SQL injection |
| Follow-up / options | 46–50 | Option selection, family comparison, minimal query |

Expected answers for score lookups are derived from the live `AI_Sandbox.db`.
Ambiguous queries where requesting clarification is the correct outcome are
marked `clarification_ok = True`.

---

## How to run

### Prerequisites

```bash
cd leaderboard/agent
pip install websockets   # or: /home/adhav/besser-demo/.venv/bin/pip install websockets
```

### Run classical mode

```bash
# Terminal 1
LETZEVAL_AGENT_MODE=classical \
  /home/adhav/besser-demo/.venv/bin/python3 agent.py

# Terminal 2
LETZEVAL_AGENT_MODE=classical \
  /home/adhav/besser-demo/.venv/bin/python3 tests/evaluation_runner.py \
  --output evaluation_results/classical.csv
```

### Run LLM mode

Configure the LLM in `agent/.env` (see `.env.example`), then:

```bash
# Terminal 1 — restart agent with LLM mode
LETZEVAL_AGENT_MODE=llm \
  /home/adhav/besser-demo/.venv/bin/python3 agent.py

# Terminal 2
LETZEVAL_AGENT_MODE=llm \
  /home/adhav/besser-demo/.venv/bin/python3 tests/evaluation_runner.py \
  --output evaluation_results/llm.csv
```

---

## Results

> **Note:** Results below are populated once the evaluation has been run against
> the live agent. Until then, this section contains expected outcomes based on
> system analysis. Actual results are in `evaluation_results/*.csv`.

### Expected outcome analysis (pre-run)

#### Where classical mode is expected to perform well

- Cases with exact model names and standard phrasing (cases 1–5, 50)
- Ranking and comparison with explicit CEFR level (21–25, 27)
- Filter and reset operations (30–32)
- Out-of-scope detection for English training examples (41, 43, 45)

#### Where classical mode is expected to struggle

- Lowercase/abbreviated queries without standard phrasing (6–10)
- Version-specific disambiguation when no exact string match (12–14)
- Conversational follow-ups ("what about gemma?", "give me the qwen results") (16–17)
- Multilingual queries (33–37) — classifier trained primarily on English
- Prompt-injection detection (42, 44) — may route to lookup/rank instead of out_of_scope

#### Where LLM mode is expected to improve

- Natural language phrasing variations across all intent types
- Multilingual routing — LLM handles French/German/Portuguese natively
- Model name resolution for colloquial references ("small llama", "big deepseek")
- Prompt-injection resistance — system prompt explicitly instructs LLM to ignore injections

#### Where LLM mode may underperform or add complexity

- **Latency**: each LLM call adds ~1–5 seconds per message
- **LLM failure**: if the provider is unavailable, Mode B falls back to the BAF
  classifier intent — same as Mode A, but without LLM enhancement
- **Hallucination risk**: the JSON output is validated, but a misbehaving LLM
  could return an out_of_scope when the correct intent is lookup_score, causing
  a missed answer rather than a wrong answer (conservative failure mode)
- **Cost**: OpenAI API calls per message

### Recommendation

LLM-assisted mode justifies the added complexity for deployments where:
1. User queries are highly varied in phrasing and language
2. The LLM provider is reliable and low-latency (Ollama on-premise, or fast API)
3. Multilingual support beyond English is important

Classical mode is preferable when:
1. Users are technical and follow documented query patterns
2. Latency is critical (sub-second responses)
3. No LLM provider is available or affordable

A hybrid approach — run the LLM only when the PyTorch classifier confidence
score is below a threshold — would combine the speed of the classical path with
the coverage of LLM interpretation. This is already partially implemented for
the `lookup_score` and `compare_models` handlers in classical mode.

---

## Security properties

Both modes maintain all security constraints:

- The DB is opened read-only via SQLite URI (`mode=ro`)
- All queries use parameterized statements
- LLM output is validated server-side; model names must appear in the DB list
- The LLM system prompt instructs the model to ignore routing-override attempts
- No SQL is generated or exposed; all queries are pre-defined
- Credentials and raw DB errors are never surfaced to the user
