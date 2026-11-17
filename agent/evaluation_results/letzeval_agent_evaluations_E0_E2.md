# LëtzEval BAF Agent — Evaluation Results (E0–E3)

**Report date:** 17 November 2026  
**Scope:** 50-case agent evaluation suite (E0–E3); additional independent 15-case holdout evaluated for E1. E3 uses the same 50 cases as E0–E2 with the translation checkpoint active.  
**Status:** E0 and E1 reported; E2 and E3 OpenAI runs manually reviewed. No E2/E3 classical or Ollama results supplied.

## 1. Executive summary

The latest **E2 OpenAI** run achieved **46/50 correct (92%) after manual review**, with **2 partial (4%)**, **2 wrong (4%)**, no timeouts or errors, and an **average response latency of 11.17 seconds**. Its initial automated scoring was **30/50 correct (60%)**, **18 partial**, and **2 wrong**. Manual review reclassified 16 partial responses as correct.

**E3 (translation checkpoint)** ran the same 50-case suite as E0–E2 with the LLM translation step active. Automated scoring: **17/50 correct (34%)**, 21 partial, 12 wrong, avg latency **28.41 seconds**. After manual review, **39/50 correct (78%)**, **4 partial (8%)**, **7 wrong (14%)**. Nine of the 12 auto-wrong cases were false negatives caused by stale expected-answer values in the test suite — the DB was updated between E2 and E3, and the agent returned current correct data. Three genuine failures remain (cases 22, 38, 48). Four routing regressions were identified (cases 15, 17, 46, 47).

These are encouraging results, but they should **not** be presented as proof that changing the OpenAI model alone improved accuracy. E2 also followed changes to the routing/interpretation implementation, and the reported E0/E1 scores have not been subjected to the same documented manual review as E2. E3 adds a sequential LLM call and roughly triples latency compared to E2.

## 2. Experiment definitions

| Experiment | Implementation | Modes evaluated | Test cases | Outcome |
|---|---|---|---:|---|
| **E0** | Original agent implementation | Classical BAF, Ollama `llama3.1`, OpenAI `gpt-4o-mini` | 50 per mode | Baseline |
| **E1** | Refactored query-aware candidate retrieval and LLM interpretation | Classical BAF, Ollama `llama3.1:latest`, OpenAI `gpt-4o-mini` | 50 per mode | Post-refactor comparison |
| **E1 holdout** | E1 implementation on independent questions | Classical BAF, Ollama, OpenAI `gpt-4o-mini` | 15 per mode | Generalisation check |
| **E2** | Later agent implementation and OpenAI model change | OpenAI **GPT-5.1** (model identifier to verify; see note below) | 50 | Automated scoring plus manual review |
| **E3** | E2 agent + LLM translation checkpoint (`_reply()` wraps English-only responses) | OpenAI **GPT-5.1** | 50 (same suite as E0–E2) | Translation checkpoint evaluation on full suite |

**Model identification note:** The latest user-provided description identifies E2 as **GPT-5.1**. Earlier terminal output in this conversation showed `LETZEVAL_LLM_MODEL=gpt-5.1` and an API response using `gpt-5.1-2025-11-13`. Before publication, verify the model actually used by the E2 evaluation from its recorded container environment or telemetry; this report does not assume these names are interchangeable.

## 3. Full 50-case evaluation results

### 3.1 Correctness summary

| Experiment | Mode / model | Correct | Partial | Wrong | Timeout | Error |
|---|---|---:|---:|---:|---:|---:|
| E0 | Classical BAF | 15/50 (**30%**) | 24 | 11 | 0 | 0 |
| E0 | Ollama `llama3.1` | 21/50 (**42%**) | 21 | 8 | 0 | 0 |
| E0 | OpenAI `gpt-4o-mini` | 16/50 (**32%**) | 22 | 12 | 0 | 0 |
| E1 | Classical BAF | 14/50 (**28%**) | 24 | 12 | 0 | 0 |
| E1 | Ollama `llama3.1:latest` | 28/50 (**56%**) | 18 | 4 | 0 | 0 |
| E1 | OpenAI `gpt-4o-mini` | 19/50 (**38%**) | 23 | 8 | 0 | 0 |
| E2 | OpenAI GPT-5.1 — **automatic scorer** | 30/50 (**60%**) | 18 | 2 | 0 | 0 |
| E2 | OpenAI GPT-5.1 — **after manual review** | 46/50 (**92%**) | 2 | 2 | 0 | 0 |
| E3 | OpenAI GPT-5.1 — **automatic scorer** | 17/50 (**34%**) | 21 | 12 | 0 | 0 |
| E3 | OpenAI GPT-5.1 — **after manual review** | 39/50 (**78%**) | 4 | 7 | 0 | 0 |

**Interpretation:** All rows represent 50 evaluation cases; the two E2 rows are *the same run scored two ways*, not two independent runs. E0/E1 values reflect the reported evaluation classifications; E2 reviewed values explicitly incorporate human judgement. Therefore, comparisons across E0/E1 versus E2 should be marked *descriptive, not strictly like-for-like*.

### 3.2 Latency information

| Experiment | Mode | Reported latency | Statistic |
|---|---|---:|---|
| E0 | Classical BAF | ~3.4 s | Mean (approximate; originally reported) |
| E0 | Ollama `llama3.1` | ~31.4 s | Mean (approximate; originally reported) |
| E0 | OpenAI `gpt-4o-mini` | 9.8 s | Mean (approximate; originally reported) |
| E1 | Classical BAF | 4.52 s | Median |
| E1 | Ollama `llama3.1:latest` | 47.27 s | Median |
| E1 | OpenAI `gpt-4o-mini` | 9.54 s | Median |
| E2 | OpenAI GPT-5.1 | **11.17 s** | **Mean** |
| E3 | OpenAI GPT-5.1 + translation | **28.41 s** | **Mean** |

**Caution:** Mean and median are different measures. Do not present 11.17 s vs. 9.54 s as a direct latency comparison without computing the same statistic for both runs. E3's higher latency (~28.4 s mean across all 50 cases) reflects the translation overhead: even English responses now route through the translation-check path, adding ~17 s vs. E2. The 5 non-English cases (33–37) each incurred an additional LLM translation call.

### 3.3 Changes in correct cases

| Mode | E0 | E1 | E0 → E1 change | E2 reviewed | E3 reviewed |
|---|---:|---:|---:|---:|---:|
| Classical BAF | 15 (30%) | 14 (28%) | −1 case (−2 pp) | Not run/reported | Not run/reported |
| Ollama | 21 (42%) | 28 (56%) | +7 cases (+14 pp) | Not run/reported | Not run/reported |
| OpenAI | 16 (32%) — `gpt-4o-mini` | 19 (38%) — `gpt-4o-mini` | +3 cases (+6 pp) | **46 (92%) — GPT-5.1, 50 cases** | **39 (78%) — GPT-5.1, 50 cases** |

The OpenAI E1-to-E2 reported correct count increased by **27 cases (+54 percentage points)**, but this difference combines *model selection, code changes, and scoring/review differences*. It cannot be assigned to a single cause from these results. E3 uses the same 50-case suite as E2; the 14 pp drop (92% → 78%) reflects new routing regressions (cases 15, 17, 46, 47 — four cases) and the 14 pp cost of test-suite data staleness (9 cases whose expected-answer values no longer match the updated DB — all reviewed correct, contributing to the +22 gain from auto to reviewed).

## 4. E2 detailed outcome (OpenAI GPT-5.1)

### 4.1 Automated versus reviewed scores

| Outcome | Initial automated result | After manual review | Change |
|---|---:|---:|---:|
| Correct | 30 (60%) | **46 (92%)** | **+16** |
| Partial | 18 (36%) | **2 (4%)** | **−16** |
| Wrong | 2 (4%) | **2 (4%)** | 0 |
| Timeout | 0 | 0 | 0 |
| Error | 0 | 0 | 0 |
| **Total** | **50** | **50** | — |

The difference highlights the limitations of substring-based automated scoring: **16 responses initially classified as partial were judged correct on review**. Keep the original and reviewed CSVs separately for reproducibility.

### 4.2 Remaining wrong cases

| Case | User query | Observed agent response | Issue indicated |
|---|---|---|---|
| **22** | “Who scores highest overall?” | “No recorded results found for **All Total**.” | Incorrect/default metric selection for an overall-ranking request; inspect whether **Macro Average** should be used instead of `All Total` |
| **38** | “What does CEFR stand for?” | Begins: “This leaderboard presents the performance of large language models (LLMs) on the…” | Routed to a generic leaderboard explanation instead of defining the CEFR acronym |

The excerpt supplied for case 38 is truncated, so the full response has not been independently checked here. The supplied reviewed verdict is **Wrong**.

### 4.3 Unresolved partial results

Two E2 responses remain **Partial** after manual review. Their case identifiers and responses were not provided, so they cannot be characterized in this report.

## 5. E3 detailed outcome — Translation checkpoint, full 50-case suite (OpenAI GPT-5.1)

### 5.1 Automated versus reviewed scores

| Outcome | Initial automated result | After manual review | Change |
|---|---:|---:|---:|
| Correct | 17 (34%) | **39 (78%)** | **+22** |
| Partial | 21 (42%) | **4 (8%)** | **−17** |
| Wrong | 12 (24%) | **7 (14%)** | **−5** |
| Timeout | 0 | 0 | 0 |
| Error | 0 | 0 | 0 |
| **Total** | **50** | **50** | — |

The automated scorer underperformed for two distinct reasons: (1) 13 of the 21 auto-partials had valid responses but no verifiable expected-answer substring (blank `expected_answer` field); (2) 9 of the 12 auto-wrongs were caused by stale expected-answer values — the leaderboard DB was updated between E2 and E3, so the agent returned current correct data that no longer matched the frozen test expectations.

### 5.2 Stale test-suite expected values (auto-wrong → reviewed correct)

Nine cases were auto-scored wrong because the DB changed after E2, not because the agent failed:

| Case | Query | Expected (stale) | Got (current DB) |
|---|---|---|---|
| **2** | C1 Total for Llama 3.1 - 70B | 47.12% | 61.54% |
| **3** | B2 Total for Gemma 3 - 12B | 50.88% | 57.02% |
| **8** | B1 Vocab for Phi 4 | 36.00% | 50.00% |
| **9** | B2 LC for Mistral | 46.15% | 38.46% |
| **14** | A1 Total for Qwen 2 - 7B | 48.08% | 47.12% |
| **24** | Top 3 open-source B2 Total | Qwen 3.5 - 27B | Muse Spark Open / Beam / DeepSeek V4.1 Flash |
| **27** | Llama 3.1-70B B2 Total | 52.63% | 61.40% |
| **37** | FR: model count | 102 | 128 |
| **40** | EN: model count | 102 | 128 |

All nine responses returned the current correct database value with correct format and intent. These test cases should be re-baselined against the current DB before the next evaluation run.

### 5.3 Genuine wrong cases

Three cases remain wrong after review:

| Case | Query | Observed response | Root cause |
|---|---|---|---|
| **22** | "Who scores highest overall?" | "No recorded results found for **All Total**." | Same routing failure as E2: "overall" dispatches to a non-existent `All Total` metric instead of Macro Average |
| **38** | "What does CEFR stand for?" | Generic leaderboard description | Same as E2: acronym-definition requests route to `explain_leaderboard` instead of `explain_metric` |
| **48** | "top 10 models" | "Please include a model name…" | Minimal ranking query not recognised; agent requested a model name instead of defaulting to Macro Average top-10 |

### 5.4 Routing regressions (partial → wrong on review)

Four partial responses were downgraded to wrong because the agent returned a completely irrelevant result:

| Case | Query | Got | Expected behaviour |
|---|---|---|---|
| **15** | "show me small llama scores" | Top-5 Macro Average ranking | Clarification options for small Llama variants |
| **17** | "give me the qwen results" | Top-5 Macro Average ranking | Clarification options for Qwen variants |
| **46** | "Qwen 2 - 7B" | CEFR level explanation | Qwen 2 - 7B CEFR Totals lookup |
| **47** | "compare gemma 3 12b with gemma 3 27b at c1 total" | CEFR level explanation | Side-by-side comparison at C1 Total |

Cases 15 and 17 returned an unsolicited global Macro Average ranking instead of asking which model was meant — a routing regression vs. E2 where both cases were correct. Cases 46 and 47 both followed case 44 (SQL injection, which elicited a CEFR explanation) and returned that same CEFR explanation verbatim — consistent with a session-state leak within the WebSocket session persisting across consecutive cases.

### 5.5 Remaining partial cases

Four cases remain partial after review:

| Case | Query | Issue |
|---|---|---|
| **18** | "which qwen did better on reading?" | Agent listed clarification options; should have ranked the Qwen family by reading score directly (also partial in E2) |
| **28** | "Is GPT-6 Astra better than Claude 3.5 Sonnet at B1?" | Agent reported no B1 data found; data was present in E2 — possible DB coverage gap or regression |
| **32** | "Reset all filters." | Response correct in spirit but also partial in E2; underlying reset confirmation may be incomplete |
| **44** | "DROP TABLE model; SELECT * FROM users;" | Agent gave a CEFR explanation rather than an out-of-scope rejection; benign but incorrect intent handling |

### 5.6 Non-English cases (33–37)

All five non-English cases invoked the translation checkpoint:

| Case | Lang | Query | Reviewed result | Notes |
|---|---|---|---|---|
| **33** | FR | "Quel est le score de GPT-6 Astra au niveau B2?" | correct | French locale formatting applied (99,12 %) |
| **34** | DE | "Was ist der B2-Grammatik-Wert von Llama 3.3 - 70B?" | correct | Score unchanged, query handled correctly |
| **35** | PT | "Quais são os 5 melhores modelos no total C1?" | correct | Content correct; ranking header kept in English |
| **36** | DE | "Zeig mir die Top 3 Open-Source-Modelle bei B2 Grammar." | correct | Different top models vs. E2 due to DB update |
| **37** | FR | "Combien de modèles sont dans le tableau de classement?" | correct | Got 128 models (current DB); expected 102 was stale |

4/5 correct after review; the one apparent "wrong" was purely test-suite data staleness, not a translation failure.

## 6. Independent holdout results (15 cases, E1)

| Mode | Correct | Partial | Wrong |
|---|---:|---:|---:|
| Classical BAF | 5/15 (**33%**) | 8 | 2 |
| Ollama `llama3.1:latest` | 5/15 (**33%**) | 9 | 1 |
| OpenAI `gpt-4o-mini` | 4/15 (**27%**) | 9 | 2 |

**Important limitation:** Many holdout cases lacked a machine-verifiable expected-answer substring, so correct numerical answers could still be labelled **Partial**. These figures should not be presented as definitive model accuracy. An **E2/E3 holdout run has not been supplied**.

## 7. Findings and next steps

1. **Address CEFR-acronym routing failure (E2 case 38, E3 case 38):** Route acronym-definition requests such as “What does CEFR stand for?” to the `explain_metric` state, not `explain_leaderboard`. Add “CECR” (French acronym) as a synonym for “CEFR” in the router.
2. **Fix “overall / highest” routing (E2 case 22, E3 case 22):** Ensure “overall”, “highest overall”, and similar phrases map to Macro Average, not a non-existent `All Total` combination.
3. **Fix minimal ranking queries (E3 case 48):** “top 10 models” with no qualifier should default to Macro Average top-10, not request a model name.
4. **Investigate routing regressions in E3 cases 15, 17 (Llama/Qwen family queries):** Both returned a global Macro Average ranking instead of offering disambiguation options; this was handled correctly in E2. Verify whether the translation overhead altered the routing context or the LLM interpretation step.
5. **Investigate session-state leak in E3 cases 46–47:** After the SQL-injection case (44) elicited a CEFR explanation, cases 46 and 47 returned the same CEFR explanation regardless of input. Ensure each WebSocket case runs with a clean session state, or add explicit state reset between evaluation cases.
6. **Re-baseline test-suite expected-answer values:** Nine cases (2, 3, 8, 9, 14, 24, 27, 37, 40) have stale `expected_answer` fields from the E2-era DB snapshot. Update these before the next evaluation run to avoid spurious auto-wrong classifications.
7. **Review the two outstanding Partial E2 cases:** Assign final verdicts and document the rationale.
8. **Standardize scoring:** Apply the same manual-review rubric to E0/E1 outputs, or clearly publish automated and reviewed results in separate columns. Do not silently compare them as equivalent.
9. **Verify reproducibility:** Record the E2/E3 commit SHA, database hash, exact OpenAI model identifier, frozen test-suite hash, agent mode, router prompt version, runtime parameters and date/time.
10. **Re-run the independent holdout for E2/E3:** Report it separately from the previously used 50 cases, especially if the agent has been tuned on those questions.
11. **Report latency consistently:** Recalculate mean, median and preferably p95 from each run's per-case CSV, using the same methodology.

## 8. Data provenance and constraints

- E0/E1 aggregate values and E1 holdout values: figures supplied in the project conversation and the repository's `agent/docs/E0_E1_COMPARISON.md`.
- E2 aggregate results, latency and failed-case excerpts: supplied by the user from `E2/openai_gpt51_E2_reviewed.csv` summary; this CSV itself was not provided for independent inspection in this report.
- E3 results: generated from `agent/tests/evaluation_runner.py --quiet-timeout 25 --timeout 65` against a live agent instance (OpenAI GPT-5.1, standard 50-case suite `evaluation_cases.py`); raw CSV at `evaluation_results/E3/openai_gpt51_E3.csv`; reviewed CSV at `evaluation_results/E3/openai_gpt51_E3_reviewed.csv`.
- The report includes **no invented test-case responses, numerical scores, or latency measurements** beyond those supplied.
- **Correct / Partial / Wrong** reflect the experiment's scoring method and reviewer decisions; manual review of E2/E3 does not establish that E0/E1 have been reviewed in the same way.

---

*Prepared 5 November 2026; updated 17 November 2026 with E3 results (50-case suite, translation checkpoint). Update the E2/E3 model identifier and provenance metadata before using this report in a paper, presentation or media communication.*
