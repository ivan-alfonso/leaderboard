# E0 Scoring Rubric

This document records the exact scoring function used by the evaluation runner for **both E0 and E1**
runs.  It is derived from `agent/tests/evaluation_runner.py`, function `_score_response` (lines 40–80).

## Verdict categories

| Verdict   | Meaning                                                                       |
|-----------|-------------------------------------------------------------------------------|
| correct   | The agent's response satisfies one of the machine-checkable criteria below    |
| partial   | No numeric/keyword expectation; response is non-empty (≥ 21 chars) — manual review needed |
| wrong     | Expected answer substring present but not found; or empty response            |
| timeout   | No response received within the per-case timeout                              |
| error     | WebSocket or runner exception                                                 |

## Scoring logic (applied in order)

```python
def _score_response(case: dict, response_text: str, response_type: str) -> str:
    expected_answer = case.get('expected_answer', '')
    clarification_ok = case.get('clarification_ok', False)

    text = response_text.lower()

    # 1. Clarification check
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

    # 2. Expected answer substring check (case-insensitive)
    if expected_answer and expected_answer.lower() in text:
        return 'correct'

    # 3. Out-of-scope keyword check
    if case.get('expected_intent') == 'out_of_scope':
        if any(kw in text for kw in ('outside', 'only', 'leaderboard', 'cannot', "can't", 'sorry')):
            return 'correct'

    # 4. Partial: no expected answer but substantive response
    if not expected_answer and len(response_text.strip()) > 20:
        return 'partial'

    return 'wrong'
```

## Coverage notes

50 evaluation cases are defined in `agent/tests/evaluation_cases.py`.

**22/50 cases have machine-checkable `expected_answer`:**

| Case | Input (short)                    | expected_answer           |
|------|----------------------------------|---------------------------|
| 1    | GPT-6 Astra B2 Grammar score     | `100.00`                  |
| 2    | Llama 3.1 - 70B C1 Total         | `47.12`                   |
| 3    | Gemma 3 - 12B B2 Total           | `50.88`                   |
| 4    | Llama 3.3 - 70B B2 Grammar       | `44.12`                   |
| 5    | ChatGPT 4o Macro Average         | `79.20`                   |
| 8    | phi4 b1 vocab                    | `36.00`                   |
| 9    | mistral b2 listening             | `46.15`                   |
| 10   | gemma 3 27b c1 reading           | `65.38`                   |
| 14   | qwen 2 7b A1 total               | `48.08`                   |
| 21   | Top 5 models C1 Total            | `Top 5`                   |
| 22   | Who scores highest overall?      | `GPT-6 Astra`             |
| 23   | Worst 3 C2 Total                 | `Lowest`                  |
| 24   | Top 3 open-source B2 Total       | `Qwen 3.5 - 27B`          |
| 27   | Compare Llama 3.1-70B + Gemma 3-12B B2 Total | `52.63`     |
| 30   | just show the open models        | `open`                    |
| 31   | Filter B2 Grammar                | `B2`                      |
| 34   | Llama 3.3-70B B2 Grammar (DE)    | `44.12`                   |
| 37   | Combien de modèles (FR)          | `102`                     |
| 38   | What does CEFR stand for?        | `Common European Framework` |
| 40   | How many models in leaderboard?  | `102`                     |
| 48   | top 10 models                    | `GPT-6 Astra`             |
| 50   | GPT-6 Astra B2 Grammar           | `100.00`                  |

**7/50 cases allow clarification as correct** (`clarification_ok=True`):
Cases 11, 15, 16, 17, 19, 26, 29.

**Remaining 21/50 cases** (no expected_answer, no clarification_ok) score as `partial` if the
response is non-empty and ≥ 21 characters — these require manual review.

## Limitations

- The scorer does not verify **intent routing** — a correct numeric answer from a wrong route
  coincidentally passes.
- `partial` is a placeholder: the response may be entirely correct or entirely wrong.
- Substring matching is case-insensitive but not anchored — a response that contains the expected
  string as part of a longer incorrect result still passes.
- No latency thresholds affect the verdict.
