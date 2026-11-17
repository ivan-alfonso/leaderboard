"""
Upsert model evaluation results from a TSV file into the Lux Leaderboard SQLite DB.

Default (no --update): only inserts models NOT already in the DB.
With --update: replaces the measure rows for any model already present,
               then inserts models that are entirely new.

Usage:
    python append_new_models.py --tsv <path> --db <path> [--dry-run] [--update]

Filtering (applied before any DB work):
    - Exclude rows where Model ends with   -lb
    - Exclude rows where Model contains    -luxit-
    - Exclude rows where Model starts with eu-institutional-llm-v1
                                           eu-institutional-mm-v1
"""
import argparse
import sqlite3
import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# TSV column  →  DB metric name (30 entries, name-based matching)
# ---------------------------------------------------------------------------
TSV_TO_METRIC = {}
for _level in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
    TSV_TO_METRIC[f'{_level}_grammar']                 = f'{_level} Grammar'
    TSV_TO_METRIC[f'{_level}_listening_comprehension'] = f'{_level}_LC'
    TSV_TO_METRIC[f'{_level}_reading_comprehension']   = f'{_level}_RC'
    TSV_TO_METRIC[f'{_level}_vocabulary']              = f'{_level} vocab'
    TSV_TO_METRIC[f'{_level}_total']                   = f'{_level} Total'

# ---------------------------------------------------------------------------
# Model slug  →  (display_name, family, param_size_str, licensing)
# display_name must match exactly what is (or will be) stored in element.name.
# ---------------------------------------------------------------------------
MODEL_LOOKUP = {
    # ---- Existing models already in DB (slug → current DB display name) ----
    'aya-23-8b':                      ('Aya-23',               'Aya',          '8',   'Open_Source'),
    'aya-23-35b':                     ('Aya-23 - 35B',         'Aya',          '35',  'Open_Source'),
    'c4ai-command-r-v01':             ('Command-R',            'Command-R',    '35',  'Open_Source'),
    'deepseek-r1-distill-llama-70b':  ('DeepSeek-R1 - 70B',   'DeepSeek',     '70',  'Open_Source'),
    'deepseek-r1-distill-llama-8b':   ('DeepSeek-R1 - 8B',    'DeepSeek',     '8',   'Open_Source'),
    'eurollm-1.7b-instruct':          ('EuroLLM - 1.7B',      'EuroLLM',      '1',   'Open_Source'),
    'eurollm-9b-instruct':            ('EuroLLM - 9B',        'EuroLLM',      '9',   'Open_Source'),
    'gemma-2-2b-it':                  ('Gemma 2 - 2B',        'Gemma',        '2',   'Open_Source'),
    'gemma-2-9b-it':                  ('Gemma 2 - 9B',        'Gemma',        '9',   'Open_Source'),
    'gemma-2-27b-it':                 ('Gemma 2 - 27B',       'Gemma',        '27',  'Open_Source'),
    'glm-4-9b-chat':                  ('GLM 4',               'GLM',          '9',   'Open_Source'),
    'gpt-6-astra':                    ('GPT-6 Astra',         'ChatGPT',      '0',   'Proprietary'),
    'gpt-6-luna':                     ('GPT-6 Luna',          'ChatGPT',      '0',   'Proprietary'),
    'gpt-6.1-sol':                    ('GPT-6.1 Sol',         'ChatGPT',      '0',   'Proprietary'),
    'llama-2-7b-chat':                ('Llama 2 - 7B',        'Llama',        '7',   'Open_Source'),
    'llama-2-13b-chat':               ('Llama 2 - 13B',       'Llama',        '13',  'Open_Source'),
    'llama-2-70b-chat':               ('Llama 2 - 70B',       'Llama',        '70',  'Open_Source'),
    'meta-llama-3-8b-instruct':       ('Llama 3 - 8B',        'Llama',        '8',   'Open_Source'),
    'meta-llama-3-70b-instruct':      ('Llama 3 - 70B',       'Llama',        '70',  'Open_Source'),
    'mistral-7b-instruct-v0.3':       ('Mistral',             'Mistral',      '7',   'Open_Source'),
    'mistral-nemo-instruct-2407':     ('Mistral-Nemo',        'Mistral',      '12',  'Open_Source'),
    'mistral-small-instruct-2409':    ('Mistral Small - 22B', 'Mistral',      '22',  'Open_Source'),
    'phi-3-mini-4k-instruct':         ('Phi 3',               'Phi',          '3',   'Open_Source'),
    'phi-3-medium-4k-instruct':       ('Phi 3 Medium',        'Phi',          '14',  'Open_Source'),
    'phi-3.5-mini-instruct':          ('Phi 3.5',             'Phi',          '3',   'Open_Source'),
    'qwen2-0.5b-instruct':            ('Qwen 2 - 0.5B',      'Qwen',         '0',   'Open_Source'),
    'qwen2-1.5b-instruct':            ('Qwen 2 - 1.5B',      'Qwen',         '1',   'Open_Source'),
    'qwen2-7b-instruct':              ('Qwen 2 - 7B',        'Qwen',         '7',   'Open_Source'),
    'qwen2-72b-instruct':             ('Qwen 2 - 72B',       'Qwen',         '72',  'Open_Source'),
    'qwq-32b':                        ('QWQ',                 'QWQ',          '32',  'Open_Source'),
    'stablelm-2-1.6b-chat':           ('StableLM 2',          'StableLM',     '1',   'Open_Source'),
    'stablelm-2-12b-chat':            ('StableLM 2 - 12B',   'StableLM',     '12',  'Open_Source'),
    'wizardlm-2-7b':                  ('WizardLM 2',          'WizardLM',     '7',   'Open_Source'),
    # ---- Gemma 3 ----
    'gemma-3-270m-it':                ('Gemma 3 - 270M',      'Gemma',        '0',   'Open_Source'),
    'gemma-3-1b-it':                  ('Gemma 3 - 1B',        'Gemma',        '1',   'Open_Source'),
    'gemma-3-4b-it':                  ('Gemma 3 - 4B',        'Gemma',        '4',   'Open_Source'),
    'gemma-3-12b-it':                 ('Gemma 3 - 12B',       'Gemma',        '12',  'Open_Source'),
    'gemma-3-27b-it':                 ('Gemma 3 - 27B',       'Gemma',        '27',  'Open_Source'),
    # ---- Gemma 4 ----
    'gemma-4-e2b-it':                 ('Gemma 4 - E2B',       'Gemma',        '2',   'Open_Source'),
    'gemma-4-e4b-it':                 ('Gemma 4 - E4B',       'Gemma',        '4',   'Open_Source'),
    'gemma-4-12b-it':                 ('Gemma 4 - 12B',       'Gemma',        '12',  'Open_Source'),
    'gemma-4-26b-a4b-it':             ('Gemma 4 - 26B A4B',   'Gemma',        '26',  'Open_Source'),
    'gemma-4-31b-it':                 ('Gemma 4 - 31B',       'Gemma',        '31',  'Open_Source'),
    # ---- Granite 4.0 ----
    'granite-4.0-h-tiny':             ('Granite 4.0 H-Tiny',  'Granite',      '7',   'Open_Source'),
    'granite-4.0-h-micro':            ('Granite 4.0 H-Micro', 'Granite',      '3',   'Open_Source'),
    'granite-4.0-micro':              ('Granite 4.0 Micro',   'Granite',      '3',   'Open_Source'),
    'granite-4.0-h-small':            ('Granite 4.0 H-Small', 'Granite',      '32',  'Open_Source'),
    # ---- Llama 3.x ----
    'llama-3.2-1b-instruct':          ('Llama 3.2 - 1B',      'Llama',        '1',   'Open_Source'),
    'llama-3.2-3b-instruct':          ('Llama 3.2 - 3B',      'Llama',        '3',   'Open_Source'),
    'llama-3.3-70b-instruct':         ('Llama 3.3 - 70B',     'Llama',        '70',  'Open_Source'),
    'meta-llama-3.1-8b-instruct':     ('Llama 3.1 - 8B',      'Llama',        '8',   'Open_Source'),
    'meta-llama-3.1-70b-instruct':    ('Llama 3.1 - 70B',     'Llama',        '70',  'Open_Source'),
    # ---- Ministral 3 ----
    'ministral-3-3b-instruct-2512':   ('Ministral 3 - 3B Instruct',   'Mistral', '3',  'Open_Source'),
    'ministral-3-3b-reasoning-2512':  ('Ministral 3 - 3B Reasoning',  'Mistral', '3',  'Open_Source'),
    'ministral-3-8b-instruct-2512':   ('Ministral 3 - 8B Instruct',   'Mistral', '8',  'Open_Source'),
    'ministral-3-8b-reasoning-2512':  ('Ministral 3 - 8B Reasoning',  'Mistral', '8',  'Open_Source'),
    'ministral-3-14b-instruct-2512':  ('Ministral 3 - 14B Instruct',  'Mistral', '14', 'Open_Source'),
    'ministral-3-14b-reasoning-2512': ('Ministral 3 - 14B Reasoning', 'Mistral', '14', 'Open_Source'),
    # ---- Mistral Small ----
    'mistral-small-3.1-24b-instruct-2503': ('Mistral Small 3.1 - 24B', 'Mistral', '24', 'Open_Source'),
    'mistral-small-3.2-24b-instruct-2506': ('Mistral Small 3.2 - 24B', 'Mistral', '24', 'Open_Source'),
    # ---- Mixtral ----
    'mixtral-8x7b-instruct-v0.1':     ('Mixtral - 8x7B',      'Mistral',      '56',  'Open_Source'),
    # ---- Phi 4 ----
    'phi-4':                          ('Phi 4',                'Phi',          '14',  'Open_Source'),
    'phi-4-mini-instruct':            ('Phi 4 Mini',           'Phi',          '4',   'Open_Source'),
    'phi-4-mini-reasoning':           ('Phi 4 Mini Reasoning', 'Phi',          '4',   'Open_Source'),
    'phi-4-reasoning':                ('Phi 4 Reasoning',      'Phi',          '14',  'Open_Source'),
    'phi-4-reasoning-plus':           ('Phi 4 Reasoning Plus', 'Phi',          '14',  'Open_Source'),
    # ---- Qwen 2.5 ----
    'qwen2.5-0.5b-instruct':          ('Qwen 2.5 - 0.5B',    'Qwen',         '0',   'Open_Source'),
    'qwen2.5-1.5b-instruct':          ('Qwen 2.5 - 1.5B',    'Qwen',         '1',   'Open_Source'),
    'qwen2.5-7b-instruct':            ('Qwen 2.5 - 7B',      'Qwen',         '7',   'Open_Source'),
    'qwen2.5-72b-instruct':           ('Qwen 2.5 - 72B',     'Qwen',         '72',  'Open_Source'),
    # ---- Qwen 3 ----
    'qwen3-0.6b':                     ('Qwen 3 - 0.6B',       'Qwen',         '0',   'Open_Source'),
    'qwen3-1.7b':                     ('Qwen 3 - 1.7B',       'Qwen',         '1',   'Open_Source'),
    'qwen3-4b-instruct-2507':         ('Qwen 3 - 4B Instruct','Qwen',         '4',   'Open_Source'),
    'qwen3-4b-thinking-2507':         ('Qwen 3 - 4B Thinking','Qwen',         '4',   'Open_Source'),
    'qwen3-8b':                       ('Qwen 3 - 8B',         'Qwen',         '8',   'Open_Source'),
    'qwen3-14b':                      ('Qwen 3 - 14B',        'Qwen',         '14',  'Open_Source'),
    'qwen3-32b':                      ('Qwen 3 - 32B',        'Qwen',         '32',  'Open_Source'),
    'qwen3-30b-a3b-instruct-2507':    ('Qwen 3 - 30B A3B Instruct', 'Qwen',  '30',  'Open_Source'),
    'qwen3-30b-a3b-thinking-2507':    ('Qwen 3 - 30B A3B Thinking', 'Qwen',  '30',  'Open_Source'),
    # ---- Qwen 3.5 ----
    'qwen3.5-0.8b':                   ('Qwen 3.5 - 0.8B',    'Qwen',         '0',   'Open_Source'),
    'qwen3.5-2b':                     ('Qwen 3.5 - 2B',      'Qwen',         '2',   'Open_Source'),
    'qwen3.5-4b':                     ('Qwen 3.5 - 4B',      'Qwen',         '4',   'Open_Source'),
    'qwen3.5-9b':                     ('Qwen 3.5 - 9B',      'Qwen',         '9',   'Open_Source'),
    'qwen3.5-9b-nothink':             ('Qwen 3.5 - 9B NoThink', 'Qwen',      '9',   'Open_Source'),
    'qwen3.5-27b':                    ('Qwen 3.5 - 27B',     'Qwen',         '27',  'Open_Source'),
    'qwen3.5-35b-a3b':                ('Qwen 3.5 - 35B A3B', 'Qwen',         '35',  'Open_Source'),
    # ---- Qwen 3.6 ----
    'qwen3.6-27b':                    ('Qwen 3.6 - 27B',     'Qwen',         '27',  'Open_Source'),
    'qwen3.6-35b-a3b':                ('Qwen 3.6 - 35B A3B', 'Qwen',         '35',  'Open_Source'),
    # ---- Qwen 3.8 (new) ----
    'qwen3.8-27b':                    ('Qwen 3.8 - 27B',     'Qwen',         '27',  'Open_Source'),
    # ---- NEW: Apertus (Swiss AI) ----
    'apertus-70b-instruct-2509':      ('Apertus - 70B',       'Apertus',      '70',  'Open_Source'),
    'apertus-8b-instruct-2509':       ('Apertus - 8B',        'Apertus',      '8',   'Open_Source'),
    'apertus-v1.1-0.5b-instruct':     ('Apertus v1.1 - 0.5B','Apertus',      '0',   'Open_Source'),
    'apertus-v1.1-1.5b-instruct':     ('Apertus v1.1 - 1.5B','Apertus',      '1',   'Open_Source'),
    'apertus-v1.1-4b-instruct':       ('Apertus v1.1 - 4B',  'Apertus',      '4',   'Open_Source'),
    # ---- NEW: Beam (Reflection AI) ----
    'beam-fp4':                       ('Beam',                 'Reflection',   '7',   'Open_Source'),
    # ---- NEW: Claude 5.5 (Anthropic) ----
    'claude-haiku-5-5':               ('Claude Haiku 5.5',    'Claude',       '0',   'Proprietary'),
    'claude-sonnet-5-5':              ('Claude Sonnet 5.5',   'Claude',       '0',   'Proprietary'),
    'claude-opus-5-5':                ('Claude Opus 5.5',     'Claude',       '0',   'Proprietary'),
    # ---- NEW: DeepSeek V4 / V4.1 ----
    'deepseek-v4-pro-0813-fp8':       ('DeepSeek V4 Pro',     'DeepSeek',     '671', 'Open_Source'),
    'deepseek-v4.1-flash-1017-fp8':   ('DeepSeek V4.1 Flash', 'DeepSeek',     '0',   'Open_Source'),
    # ---- NEW: GLM 5.x (ZhipuAI / zai-org) ----
    'glm-5.2-fp4':                    ('GLM 5.2',             'GLM',          '9',   'Open_Source'),
    'glm-5.3-fp4':                    ('GLM 5.3',             'GLM',          '9',   'Open_Source'),
    'glm-5.3-flash-fp4':              ('GLM 5.3 Flash',       'GLM',          '9',   'Open_Source'),
    # ---- NEW: GPT OSS (OpenAI open-weights) ----
    'gpt-oss-120b-fp4':               ('GPT OSS 120B',        'ChatGPT',      '120', 'Open_Source'),
    # ---- NEW: Hermes 4 (NousResearch) ----
    'hermes-4-405b-fp8':              ('Hermes 4 - 405B',     'NousResearch', '405', 'Open_Source'),
    # ---- NEW: Kimi (Moonshot AI) ----
    'kimi-k3-fp4':                    ('Kimi K3',             'Kimi',         '0',   'Open_Source'),
    'kimi-k3.1-pro-fp4':              ('Kimi K3.1 Pro',       'Kimi',         '0',   'Open_Source'),
    # ---- NEW: MiniMax ----
    'minimax-m3-fp4':                 ('MiniMax M3',          'MiniMax',      '0',   'Open_Source'),
    'minimax-m3.1-flash-fp4':         ('MiniMax M3.1 Flash',  'MiniMax',      '0',   'Open_Source'),
    # ---- NEW: Muse Spark ----
    'muse-spark-open-fp4':            ('Muse Spark Open',     'Muse',         '0',   'Open_Source'),
    # ---- NEW: Nemotron (Nvidia) ----
    'nemotron-3-ultra-550b-a55b-fp4': ('Nemotron 3 Ultra 550B',     'Nemotron', '550', 'Open_Source'),
    'nemotron-3.5-lightning-30b-a3b': ('Nemotron 3.5 Lightning 30B','Nemotron', '30',  'Open_Source'),
    'nemotron-3.5-super-vl-bf16':     ('Nemotron 3.5 Super VL',     'Nemotron', '0',   'Open_Source'),
}

EXCLUDE_PATTERNS = [
    lambda s: s.endswith('-lb'),
    lambda s: '-luxit-' in s,
    lambda s: s.startswith('eu-institutional-llm-v1'),
    lambda s: s.startswith('eu-institutional-mm-v1'),
]


def should_exclude(slug: str) -> bool:
    return any(p(slug) for p in EXCLUDE_PATTERNS)


def load_tsv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            slug = row['Model'].strip()
            if not should_exclude(slug):
                rows.append(row)
    return rows


def load_db_state(conn) -> tuple[dict, dict, int, int]:
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM element")
    name_to_id = {r[1]: r[0] for r in cur.fetchall()}
    cur.execute("SELECT id, name FROM metric")
    metric_name_to_id = {r[1]: r[0] for r in cur.fetchall()}
    cur.execute("SELECT MAX(id) FROM element")
    max_elem_id = cur.fetchone()[0] or 0
    cur.execute("SELECT id FROM dataset ORDER BY id LIMIT 1")
    dataset_id = cur.fetchone()[0]
    return name_to_id, metric_name_to_id, max_elem_id, dataset_id


def insert_model(conn, elem_id: int, display_name: str, family: str,
                 param_size: str, licensing: str, dataset_id: int, dry_run: bool):
    if dry_run:
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO element(id, project_id, type_spec, name, description) VALUES (?,?,?,?,?)",
        (elem_id, 1, 'model', display_name, 'Lux Language Test')
    )
    cur.execute(
        "INSERT INTO model(id, pid, data, source, licensing) VALUES (?,?,?,?,?)",
        (elem_id, display_name, param_size, family, licensing)
    )
    cur.execute(
        "INSERT INTO model_dataset(models, dataset) VALUES (?,?)",
        (elem_id, dataset_id)
    )
    conn.commit()


def delete_measures(conn, elem_id: int, dry_run: bool):
    if dry_run:
        return
    conn.cursor().execute("DELETE FROM measure WHERE measurand_id = ?", (elem_id,))
    conn.commit()


def insert_measures(conn, elem_id: int, obs_id: int,
                    metric_name_to_id: dict, tsv_row: dict, dry_run: bool) -> int:
    inserted = 0
    cur = conn.cursor()
    for tsv_col, metric_name in TSV_TO_METRIC.items():
        metric_id = metric_name_to_id.get(metric_name)
        if metric_id is None:
            print(f"  [WARN] Unknown metric '{metric_name}' — skipping", file=sys.stderr)
            continue
        raw = tsv_row.get(tsv_col, '').strip()
        if raw:
            try:
                value = str(round(float(raw) * 100, 4))
            except ValueError:
                value = raw
        else:
            value = 'Not Available'
        if not dry_run:
            cur.execute(
                "INSERT INTO measure(value, error, uncertainty, unit, observation_id, metric_id, measurand_id) "
                "VALUES (?,?,?,?,?,?,?)",
                (value, 'Not Available', 0.0, 'percent', obs_id, metric_id, elem_id)
            )
        inserted += 1
    if not dry_run:
        conn.commit()
    return inserted


def main():
    ap = argparse.ArgumentParser(description="Upsert model results to Lux Leaderboard DB")
    ap.add_argument("--tsv", required=True, type=Path)
    ap.add_argument("--db",  required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would be done without writing to the DB")
    ap.add_argument("--update", action="store_true",
                    help="Replace measure rows for models already in DB (default: skip them)")
    args = ap.parse_args()

    if not args.tsv.exists():
        sys.exit(f"TSV not found: {args.tsv}")
    if not args.db.exists():
        sys.exit(f"DB not found: {args.db}")

    rows = load_tsv(args.tsv)
    print(f"TSV rows after filtering: {len(rows)}")

    conn = sqlite3.connect(args.db.as_posix())
    name_to_id, metric_name_to_id, max_elem_id, dataset_id = load_db_state(conn)

    cur = conn.cursor()
    cur.execute("SELECT id FROM observation ORDER BY id LIMIT 1")
    obs_id = cur.fetchone()[0]

    next_id = max_elem_id + 1
    skipped, updated_models, inserted_models = [], [], []
    total_measures = 0

    for row in rows:
        slug = row['Model'].strip()
        if slug not in MODEL_LOOKUP:
            print(f"[WARN] No mapping for slug '{slug}' — skipping", file=sys.stderr)
            continue

        display_name, family, param_size, licensing = MODEL_LOOKUP[slug]

        if display_name in name_to_id:
            if not args.update:
                skipped.append((slug, display_name))
                continue
            # Update: replace measures only
            elem_id = name_to_id[display_name]
            delete_measures(conn, elem_id, args.dry_run)
            n = insert_measures(conn, elem_id, obs_id, metric_name_to_id, row, args.dry_run)
            total_measures += n
            updated_models.append((elem_id, slug, display_name))
        else:
            elem_id = next_id
            next_id += 1
            insert_model(conn, elem_id, display_name, family, param_size, licensing,
                         dataset_id, args.dry_run)
            n = insert_measures(conn, elem_id, obs_id, metric_name_to_id, row, args.dry_run)
            total_measures += n
            inserted_models.append((elem_id, slug, display_name, family, param_size))

    conn.close()

    prefix = "[DRY-RUN] " if args.dry_run else ""

    print(f"\n{prefix}=== Summary ===")
    print(f"Models skipped (already in DB, no --update): {len(skipped)}")
    for slug, name in skipped:
        print(f"  SKIP   {slug!r:55s} → {name!r}")

    print(f"\nModels updated (measures replaced): {len(updated_models)}")
    for elem_id, slug, name in updated_models:
        print(f"  {'[DRY] ' if args.dry_run else 'UPDATE'} id={elem_id}  {slug!r:55s} → {name!r}")

    print(f"\nModels inserted (new): {len(inserted_models)}")
    for elem_id, slug, name, family, size in inserted_models:
        print(f"  {'[DRY] ' if args.dry_run else 'INSERT'} id={elem_id}  {slug!r:55s} → {name!r}  [{family}, {size}B]")

    print(f"\n{prefix}Measure rows {'would be ' if args.dry_run else ''}written: {total_measures}")
    print(f"{prefix}Done.")


if __name__ == "__main__":
    main()
