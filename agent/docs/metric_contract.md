# LëtzEval Metric Contract

## Score units and range

All scores are **percentage-correct** values in the range [0, 100].
Stored as `VARCHAR(100)` in `measure.value`; the agent casts with `CAST(value AS REAL)`.
Unit column value: always `"percent"` (verified for all 3162 rows).

---

## Metric definitions

### Direct metrics (30)

| Metric | Definition |
|---|---|
| `{level} Grammar` | % correct on multiple-choice grammar questions at the specified CEFR level |
| `{level}_LC` | % correct on listening comprehension questions at the specified CEFR level |
| `{level}_RC` | % correct on reading comprehension questions at the specified CEFR level |
| `{level} vocab` | % correct on vocabulary questions at the specified CEFR level |
| `{level} Total` | Unweighted mean of Grammar, LC, RC, and Vocab at the specified level |

Where `{level}` ∈ {A1, A2, B1, B2, C1, C2}.

### Derived metric (1)

| Metric | Definition |
|---|---|
| `Macro Avg.` | Arithmetic mean of the six level Total scores (A1 Total … C2 Total), weighted equally |

**Verified formula:** `(A1_Total + A2_Total + B1_Total + B2_Total + C1_Total + C2_Total) / 6`
Confirmed correct for `model.id = 48` (ChatGPT 3.5): stored = 80.68, computed = 80.6833, diff = 0.003 (rounding only).

---

## User-facing category names → DB category tokens

| User says | Agent maps to | DB metric name pattern |
|---|---|---|
| Grammar | Grammar | `{level} Grammar` |
| Vocabulary / Vocab | Vocab | `{level} vocab` |
| Reading Comprehension / RC | RC | `{level}_RC` |
| Listening Comprehension / LC | LC | `{level}_LC` |
| Total / Overall | Total | `{level} Total` |
| Macro Average / Overall (no level) | Macro | `Macro Avg.` |

---

## Score comparison rules

1. Compare two scores only if they share the **same metric_id** (same level + category).
2. Express differences in **percentage points** (pp), not percentage relative change.
3. Ties: report as tied; do not invent a tiebreaker.
4. Missing scores (absent row) ≠ recorded zero. The agent reports missing as "not found", not as 0%.

---

## Baseline reference values (chance level)

Used in the chart's baseline reference line; not returned by the agent in text.

| Level | Chance baseline |
|---|---|
| A1 | 37.7% |
| A2 | 37.4% |
| B1 | 33.6% |
| B2 | 32.8% |
| C1 | 32.3% |
| C2 | 33.7% |
| Macro (all levels) | ~34.6% |

---

## Guardrails

- Do **not** compute or infer scores not stored in the DB.
- Do **not** claim a model's CEFR-level proficiency from its benchmark score.
- Do **not** aggregate across categories without documented formula (no cross-category mean).
- Do **not** derive an "overall score" unless explicitly asked for Macro Average.
