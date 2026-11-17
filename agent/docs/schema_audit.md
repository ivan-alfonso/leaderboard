# LëtzEval DB Schema Audit

## Database provenance

| Field | Value |
|---|---|
| File | `backend/data/AI_Sandbox.db` |
| SQLite version | 3.x (system) |
| Row count — `measure` | 3162 (102 models × 31 metrics, no duplicates) |
| Row count — `model` | 102 |
| Row count — `metric` | 31 |
| Single observation | `observation.id = 1`, `whenObserved = 2025-10-30` |
| Single evaluation | `evaluation.id = 1`, `status = Done` |
| Snapshot used | DB as of 2026-10-27 audit |

**Status legend:** VERIFIED = confirmed by direct query; INFERRED = deduced from schema; UNKNOWN = not established.

---

## Key tables used by the agent

### `model` (102 rows)
- `id INTEGER PK` — joins to `element.id` (SQLAlchemy single-table inheritance)
- `pid VARCHAR(100)` — human-readable name, identical to `element.name` for all 102 rows (VERIFIED)
- `data VARCHAR(100)` — parameter size label (e.g. "0.5", "70", "500") (VERIFIED)
- `source VARCHAR(100)` — model family/org name (e.g. "Meta", "Google", "OpenAI") (VERIFIED)
- `licensing VARCHAR(11)` — values: Open_Source or Proprietary; never NULL (VERIFIED)

### `element` (102 rows, all type_spec='model')
- `id INTEGER PK`
- `name VARCHAR(100)` — model display name (e.g. "Llama 3.2 - 1B") (VERIFIED)
- `project_id INTEGER` — all 102 rows reference `project.id = 1` (VERIFIED)

**Join:** `model.id = element.id` (shared primary key) — VERIFIED

### `metric` (31 rows)
- `id INTEGER PK` — fixed IDs verified from audit
- `name VARCHAR(100)` — metric label (e.g. "A1 Grammar", "B2 Total", "Macro Avg.")
- `type_spec VARCHAR(50)` — "Direct" (30 rows) or "Derived" (1 row: Macro Avg.)

### `measure` (3162 rows)
- `id INTEGER PK`
- `value VARCHAR(100) NOT NULL` — numeric string, always percent (e.g. "76.47") (VERIFIED)
- `unit VARCHAR(100)` — always "percent" for all 3162 rows (VERIFIED)
- `metric_id INTEGER FK → metric.id`
- `measurand_id INTEGER FK → element.id` (= model.id)
- `observation_id INTEGER` — always 1 (VERIFIED)
- No NULL values in `value` (VERIFIED); `value` stores floats as text (VERIFIED)

**Join for queries:** `model.id = measure.measurand_id AND metric.id = measure.metric_id`

---

## Metric ID reference table (all 31 metrics)

| ID | Name | Level | Category |
|---|---|---|---|
| 1 | A1 Grammar | A1 | Grammar |
| 2 | A1_LC | A1 | LC |
| 3 | A1_RC | A1 | RC |
| 4 | A1 vocab | A1 | Vocab |
| 5 | A1 Total | A1 | Total |
| 6 | A2 Grammar | A2 | Grammar |
| 7 | A2_LC | A2 | LC |
| 8 | A2_RC | A2 | RC |
| 9 | A2 vocab | A2 | Vocab |
| 10 | A2 Total | A2 | Total |
| 11 | B1 Grammar | B1 | Grammar |
| 12 | B1_LC | B1 | LC |
| 13 | B1_RC | B1 | RC |
| 14 | B1 vocab | B1 | Vocab |
| 15 | B1 Total | B1 | Total |
| 16 | B2 Grammar | B2 | Grammar |
| 17 | B2_LC | B2 | LC |
| 18 | B2_RC | B2 | RC |
| 19 | B2 vocab | B2 | Vocab |
| 20 | B2 Total | B2 | Total |
| 21 | C1 Grammar | C1 | Grammar |
| 22 | C1_LC | C1 | LC |
| 23 | C1_RC | C1 | RC |
| 24 | C1 vocab | C1 | Vocab |
| 25 | C1 Total | C1 | Total |
| 26 | C2 Grammar | C2 | Grammar |
| 27 | C2_LC | C2 | LC |
| 28 | C2_RC | C2 | RC |
| 29 | C2 vocab | C2 | Vocab |
| 30 | C2 Total | C2 | Total |
| 31 | Macro Avg. | All | — |

**Agent key map:** `METRIC_IDS` dict in `agent/db/safe_db.py` maps `(level, category)` tuples to these IDs.
All SQL queries use `metric_id = ?` with a literal integer — no string manipulation on metric names.

---

## Missing vs zero scores

All 3162 measure rows are populated (102 × 31, no missing rows). (VERIFIED)
However, some models may have a stored value of `'0.0'` for metrics where no actual result exists.
The agent treats a literal `0.0` as a recorded zero, not as missing — matching the source data.

---

## Tables NOT exposed to the agent

The following tables are excluded from all agent SQL queries:
- `comments` — does not exist in this DB (confirmed; no comment table found) (VERIFIED)
- `sqlite_master` / `sqlite_schema` — blocked by schema (not included in allowed tables)
- `confparam`, `legalrequirement`, `project`, `tool`, `configuration` — internal metadata
- Any future tables added to the schema

The agent uses only `model`, `element`, `measure`, `metric` — the four tables directly needed for published evaluation results.

---

## Query safety approach

1. All queries are **parameterized** (`?` placeholders) — no user string is ever concatenated into SQL.
2. The DB connection is opened **read-only** via SQLite URI (`file:...?mode=ro`).
3. Metric IDs are resolved from a **compile-time dictionary**, not from user-provided strings.
4. **NL→SQL is disabled** — the BAF `db_handler` NL→SQL feature is not used.
5. Maximum rows returned per query: **25** (enforced in `LIMIT ?` clause).
6. Security tests from `sql_security_tests.csv` are verified against state body logic, not the SQL layer.
