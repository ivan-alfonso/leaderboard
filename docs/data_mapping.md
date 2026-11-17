# Data Mapping: LuxEval Results → Leaderboard DB

This document describes how evaluation results from `/mnt/d/0_wsl_workspace/00_luxeval_vllm_results`
are mapped into `backend/data/AI_Sandbox.db`.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/build_combined_tsv.py` | Merge individual per-model `summary.tsv` files into one flat TSV |
| `scripts/append_new_models.py`  | Upsert the flat TSV into the DB (insert new / replace measures for existing) |
| `scripts/model_names.csv`       | Human-readable reference of all slug → display name mappings |

---

## Filters (applied by both scripts)

Results directories / TSV rows matching any of these patterns are **excluded**:

| Pattern | Example |
|---------|---------|
| ends with `-lb` | `qwen3-8b-lb` |
| contains `-luxit-` | `qwen3.5-9b-luxit-e1-think` |
| starts with `eu-institutional-llm-v1` | `eu-institutional-llm-v1-instruct` |
| starts with `eu-institutional-mm-v1` | `eu-institutional-mm-v1-instruct` |

---

## How to run

### Step 1 — Build combined TSV

Reads every non-excluded model directory that has a `summary.tsv` and produces a
single flat TSV (`Model`, `A1_grammar`, `A1_listening_comprehension`, … `C2_vocabulary`).

```bash
python3 scripts/build_combined_tsv.py \
  --results-dir /mnt/d/0_wsl_workspace/00_luxeval_vllm_results \
  --output /tmp/all_models.tsv \
  --overwrite
```

### Step 2 — Dry-run to preview changes

```bash
python3 scripts/append_new_models.py \
  --tsv /tmp/all_models.tsv \
  --db  backend/data/AI_Sandbox.db \
  --update \
  --dry-run
```

Review the output:
- **SKIP** — model already in DB, no `--update` flag given
- **UPDATE** — model already in DB, measures will be replaced
- **INSERT** — new model; element + model + measures will be added
- **[WARN]** — slug has no entry in `MODEL_LOOKUP`; add it to `append_new_models.py` before re-running

### Step 3 — Apply changes

```bash
python3 scripts/append_new_models.py \
  --tsv /tmp/all_models.tsv \
  --db  backend/data/AI_Sandbox.db \
  --update
```

---

## Slug → Display name mapping

The `MODEL_LOOKUP` table in `scripts/append_new_models.py` maps every evaluation
slug to its DB display name, model family, parameter size, and licensing type.
`scripts/model_names.csv` is the same data in CSV form for quick reference.

### Naming conventions

- **display_name** must match exactly what is stored in `element.name` in the DB.
  If the model is new, this will become the stored name.
- **family** is the `source` column in the `model` table (used for grouping/filtering).
  Proprietary OpenAI models use `ChatGPT` to stay consistent with existing entries.
- **param_size** is stored as a plain integer string in the `data` column of `model`.
  `0` means unknown or not applicable (e.g. closed-source models, MoE active-param ambiguity).
- **licensing**: `Open_Source` or `Proprietary`.

### Provider mapping examples

| Slug prefix | Family in DB | Notes |
|-------------|-------------|-------|
| `gpt-*` | `ChatGPT` | All OpenAI models, including open-weights |
| `claude-*` | `Claude` | Anthropic models |
| `gemma-*` | `Gemma` | Google Gemma 2/3/4 |
| `llama-*` / `meta-llama-*` | `Llama` | Meta Llama 2/3/3.1/3.2/3.3 |
| `qwen*` | `Qwen` | Alibaba Qwen 2/2.5/3/3.5/3.6/3.8 |
| `phi-*` | `Phi` | Microsoft Phi 3/3.5/4 |
| `mistral-*` / `mixtral-*` / `ministral-*` | `Mistral` | Mistral AI |
| `deepseek-*` | `DeepSeek` | DeepSeek AI |
| `glm-*` | `GLM` | ZhipuAI (zai-org) |
| `kimi-*` | `Kimi` | Moonshot AI |
| `minimax-*` | `MiniMax` | MiniMax AI |
| `nemotron-*` | `Nemotron` | NVIDIA |
| `apertus-*` | `Apertus` | Swiss AI |
| `hermes-*` | `NousResearch` | NousResearch |
| `beam-fp4` | `Reflection` | Reflection AI (reflection/beam) |
| `muse-spark-open-fp4` | `Muse` | meta-models/muse-spark-open |

---

## DB schema reference

```
element(id, project_id, type_spec, name, description)
model(id, pid, data, source, licensing)
model_dataset(models, dataset)
measure(value, error, uncertainty, unit, observation_id, metric_id, measurand_id)
metric(id, name)
```

- `element.id = model.id = measure.measurand_id`
- `measure.value` stores percentages (0–100); the TSV stores fractions (0–1)
- All models share `observation_id = 1` (the single LuxEval observation)

---

## Adding a new model in future

1. Add a `summary.tsv` in its directory under the results root (same per-level format).
2. Add an entry to `MODEL_LOOKUP` in `scripts/append_new_models.py`:
   ```python
   'my-new-model-slug': ('Display Name', 'Family', 'param_size', 'Open_Source'),
   ```
3. Add the same entry to `scripts/model_names.csv`.
4. Re-run Steps 1–3 above (`--update` is not needed for brand-new models).
