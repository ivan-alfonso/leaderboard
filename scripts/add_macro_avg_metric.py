"""
Add 'Macro Avg.' as a new metric (id=31) to the Lux Leaderboard DB and populate
per-model values from per-model summary.tsv files.

Optionally inserts new models from a TSV file first (same filtering + lookup logic
as append_new_models.py — use this for GPT or any future closed-source batch).

Usage:
    # Add Macro Avg. only (populates all models that have a summary.tsv):
    python add_macro_avg_metric.py \\
        --db  leaderboard/backend/data/AI_Sandbox.db \\
        --results-dir /path/to/00_luxeval_vllm_results

    # Insert new GPT models, then add Macro Avg. for everyone:
    python add_macro_avg_metric.py \\
        --db  leaderboard/backend/data/AI_Sandbox.db \\
        --results-dir /path/to/00_luxeval_vllm_results \\
        --tsv /path/to/final_summary_gpt.tsv

    # Dry-run (preview, no writes):
    python add_macro_avg_metric.py ... --dry-run

Filtering (applied to any --tsv rows and to folder names under --results-dir):
    - Exclude slugs ending with        -lb
    - Exclude slugs containing         -luxit-
    - Exclude slugs starting with      eu-institutional-llm-v1
    - Exclude slugs starting with      eu-institutional-mm-v1
"""
import argparse
import sqlite3
import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# TSV column → DB metric name  (30 metrics, for new-model insertion)
# ---------------------------------------------------------------------------
TSV_TO_METRIC = {}
for _level in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
    TSV_TO_METRIC[f'{_level}_grammar']                 = f'{_level} Grammar'
    TSV_TO_METRIC[f'{_level}_listening_comprehension'] = f'{_level}_LC'
    TSV_TO_METRIC[f'{_level}_reading_comprehension']   = f'{_level}_RC'
    TSV_TO_METRIC[f'{_level}_vocabulary']              = f'{_level} vocab'
    TSV_TO_METRIC[f'{_level}_total']                   = f'{_level} Total'

# ---------------------------------------------------------------------------
# Full model lookup: slug → (display_name, family, param_size, licensing)
# Add new entries here when a new evaluation family is introduced.
# ---------------------------------------------------------------------------
MODEL_LOOKUP = {
    # ── Gemma 3 ──────────────────────────────────────────────────────────────
    'gemma-3-270m-it':             ('Gemma 3 - 270M',              'Gemma',   '0',  'Open_Source'),
    'gemma-3-1b-it':               ('Gemma 3 - 1B',                'Gemma',   '1',  'Open_Source'),
    'gemma-3-4b-it':               ('Gemma 3 - 4B',                'Gemma',   '4',  'Open_Source'),
    'gemma-3-12b-it':              ('Gemma 3 - 12B',               'Gemma',   '12', 'Open_Source'),
    'gemma-3-27b-it':              ('Gemma 3 - 27B',               'Gemma',   '27', 'Open_Source'),
    # ── Gemma 4 ──────────────────────────────────────────────────────────────
    'gemma-4-e2b-it':              ('Gemma 4 - E2B',               'Gemma',   '2',  'Open_Source'),
    'gemma-4-e4b-it':              ('Gemma 4 - E4B',               'Gemma',   '4',  'Open_Source'),
    'gemma-4-12b-it':              ('Gemma 4 - 12B',               'Gemma',   '12', 'Open_Source'),
    'gemma-4-26b-a4b-it':          ('Gemma 4 - 26B A4B',           'Gemma',   '26', 'Open_Source'),
    'gemma-4-31b-it':              ('Gemma 4 - 31B',               'Gemma',   '31', 'Open_Source'),
    # ── Granite 4.0 (IBM hybrid mamba-2) ─────────────────────────────────────
    # h-tiny=7B/1B-active, h-micro=3B, micro=3B, h-small=32B/9B-active
    'granite-4.0-h-tiny':          ('Granite 4.0 H-Tiny',          'Granite', '7',  'Open_Source'),
    'granite-4.0-h-micro':         ('Granite 4.0 H-Micro',         'Granite', '3',  'Open_Source'),
    'granite-4.0-micro':           ('Granite 4.0 Micro',           'Granite', '3',  'Open_Source'),
    'granite-4.0-h-small':         ('Granite 4.0 H-Small',         'Granite', '32', 'Open_Source'),
    # ── Llama ────────────────────────────────────────────────────────────────
    'llama-3.2-1b-instruct':       ('Llama 3.2 - 1B',              'Llama',   '1',  'Open_Source'),
    'llama-3.2-3b-instruct':       ('Llama 3.2 - 3B',              'Llama',   '3',  'Open_Source'),
    'llama-3.3-70b-instruct':      ('Llama 3.3 - 70B',             'Llama',   '70', 'Open_Source'),
    'meta-llama-3.1-8b-instruct':  ('Llama 3.1 - 8B',              'Llama',   '8',  'Open_Source'),
    'meta-llama-3.1-70b-instruct': ('Llama 3.1 - 70B',             'Llama',   '70', 'Open_Source'),
    # ── Ministral 3 ──────────────────────────────────────────────────────────
    'ministral-3-3b-instruct-2512':   ('Ministral 3 - 3B Instruct',   'Mistral', '3',  'Open_Source'),
    'ministral-3-3b-reasoning-2512':  ('Ministral 3 - 3B Reasoning',  'Mistral', '3',  'Open_Source'),
    'ministral-3-8b-instruct-2512':   ('Ministral 3 - 8B Instruct',   'Mistral', '8',  'Open_Source'),
    'ministral-3-8b-reasoning-2512':  ('Ministral 3 - 8B Reasoning',  'Mistral', '8',  'Open_Source'),
    'ministral-3-14b-instruct-2512':  ('Ministral 3 - 14B Instruct',  'Mistral', '14', 'Open_Source'),
    'ministral-3-14b-reasoning-2512': ('Ministral 3 - 14B Reasoning', 'Mistral', '14', 'Open_Source'),
    # ── Mistral Small ────────────────────────────────────────────────────────
    'mistral-small-3.1-24b-instruct-2503': ('Mistral Small 3.1 - 24B', 'Mistral', '24', 'Open_Source'),
    'mistral-small-3.2-24b-instruct-2506': ('Mistral Small 3.2 - 24B', 'Mistral', '24', 'Open_Source'),
    # ── Mixtral ──────────────────────────────────────────────────────────────
    'mixtral-8x7b-instruct-v0.1':  ('Mixtral - 8x7B',              'Mistral', '56', 'Open_Source'),
    # ── Phi 4 ────────────────────────────────────────────────────────────────
    'phi-4':                       ('Phi 4',                        'Phi',     '14', 'Open_Source'),
    'phi-4-mini-instruct':         ('Phi 4 Mini',                   'Phi',     '4',  'Open_Source'),
    'phi-4-mini-reasoning':        ('Phi 4 Mini Reasoning',         'Phi',     '4',  'Open_Source'),
    'phi-4-reasoning':             ('Phi 4 Reasoning',              'Phi',     '14', 'Open_Source'),
    'phi-4-reasoning-plus':        ('Phi 4 Reasoning Plus',         'Phi',     '14', 'Open_Source'),
    # ── Qwen 2.5 ─────────────────────────────────────────────────────────────
    'qwen2.5-0.5b-instruct':       ('Qwen 2.5 - 0.5B',             'Qwen',    '0',  'Open_Source'),
    'qwen2.5-1.5b-instruct':       ('Qwen 2.5 - 1.5B',             'Qwen',    '1',  'Open_Source'),
    'qwen2.5-7b-instruct':         ('Qwen 2.5 - 7B',               'Qwen',    '7',  'Open_Source'),
    'qwen2.5-72b-instruct':        ('Qwen 2.5 - 72B',              'Qwen',    '72', 'Open_Source'),
    # ── Qwen 3 ───────────────────────────────────────────────────────────────
    'qwen3-0.6b':                  ('Qwen 3 - 0.6B',               'Qwen',    '0',  'Open_Source'),
    'qwen3-1.7b':                  ('Qwen 3 - 1.7B',               'Qwen',    '1',  'Open_Source'),
    'qwen3-4b-instruct-2507':      ('Qwen 3 - 4B Instruct',        'Qwen',    '4',  'Open_Source'),
    'qwen3-4b-thinking-2507':      ('Qwen 3 - 4B Thinking',        'Qwen',    '4',  'Open_Source'),
    'qwen3-8b':                    ('Qwen 3 - 8B',                 'Qwen',    '8',  'Open_Source'),
    'qwen3-14b':                   ('Qwen 3 - 14B',                'Qwen',    '14', 'Open_Source'),
    'qwen3-32b':                   ('Qwen 3 - 32B',                'Qwen',    '32', 'Open_Source'),
    'qwen3-30b-a3b-instruct-2507': ('Qwen 3 - 30B A3B Instruct',   'Qwen',    '30', 'Open_Source'),
    'qwen3-30b-a3b-thinking-2507': ('Qwen 3 - 30B A3B Thinking',   'Qwen',    '30', 'Open_Source'),
    # ── Qwen 3.5 ─────────────────────────────────────────────────────────────
    'qwen3.5-0.8b':                ('Qwen 3.5 - 0.8B',             'Qwen',    '0',  'Open_Source'),
    'qwen3.5-2b':                  ('Qwen 3.5 - 2B',               'Qwen',    '2',  'Open_Source'),
    'qwen3.5-4b':                  ('Qwen 3.5 - 4B',               'Qwen',    '4',  'Open_Source'),
    'qwen3.5-9b':                  ('Qwen 3.5 - 9B',               'Qwen',    '9',  'Open_Source'),
    'qwen3.5-9b-nothink':          ('Qwen 3.5 - 9B NoThink',       'Qwen',    '9',  'Open_Source'),
    'qwen3.5-27b':                 ('Qwen 3.5 - 27B',              'Qwen',    '27', 'Open_Source'),
    'qwen3.5-35b-a3b':             ('Qwen 3.5 - 35B A3B',          'Qwen',    '35', 'Open_Source'),
    # ── Qwen 3.6 ─────────────────────────────────────────────────────────────
    'qwen3.6-27b':                 ('Qwen 3.6 - 27B',              'Qwen',    '27', 'Open_Source'),
    'qwen3.6-35b-a3b':             ('Qwen 3.6 - 35B A3B',          'Qwen',    '35', 'Open_Source'),
    # ── GPT-6 (OpenAI, Proprietary) ──────────────────────────────────────────
    'gpt-6-astra':                 ('GPT-6 Astra',                  'GPT',     '0',  'Proprietary'),
    'gpt-6-luna':                  ('GPT-6 Luna',                   'GPT',     '0',  'Proprietary'),
    'gpt-6.1-sol':                 ('GPT-6.1 Sol',                  'GPT',     '0',  'Proprietary'),
}

EXCLUDE_PATTERNS = [
    lambda s: s.endswith('-lb'),
    lambda s: '-luxit-' in s,
    lambda s: s.startswith('eu-institutional-llm-v1'),
    lambda s: s.startswith('eu-institutional-mm-v1'),
]

MACRO_AVG_METRIC = {
    'name':        'Macro Avg.',
    'type_spec':   'Derived',
    'description': 'MACRO AVG',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def should_exclude(slug: str) -> bool:
    return any(p(slug) for p in EXCLUDE_PATTERNS)


def load_tsv_rows(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return [row for row in reader if not should_exclude(row['Model'].strip())]


def read_macro_avg_total(summary_tsv: Path) -> float | None:
    """Return MACRO_AVG TOTAL as a float fraction (0-1), or None if missing."""
    with summary_tsv.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get('Level', '').strip() == 'MACRO_AVG':
                raw = row.get('TOTAL', '').strip()
                if raw:
                    return float(raw)
    return None


def load_db_state(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM element")
    name_to_id = {r[1]: r[0] for r in cur.fetchall()}
    cur.execute("SELECT id, name FROM metric")
    metric_name_to_id = {r[1]: r[0] for r in cur.fetchall()}
    cur.execute("SELECT MAX(id) FROM element")
    max_elem_id = cur.fetchone()[0] or 0
    cur.execute("SELECT id FROM dataset ORDER BY id LIMIT 1")
    dataset_id = cur.fetchone()[0]
    cur.execute("SELECT id FROM observation ORDER BY id LIMIT 1")
    obs_id = cur.fetchone()[0]
    return name_to_id, metric_name_to_id, max_elem_id, dataset_id, obs_id


# ---------------------------------------------------------------------------
# Phase 1 — insert new models from TSV (same logic as append_new_models.py)
# ---------------------------------------------------------------------------

def phase_insert_new_models(conn, tsv_rows, name_to_id, metric_name_to_id,
                             max_elem_id, dataset_id, obs_id, dry_run):
    cur = conn.cursor()
    next_id = max_elem_id + 1
    inserted, skipped = [], []

    for row in tsv_rows:
        slug = row['Model'].strip()
        if slug not in MODEL_LOOKUP:
            print(f"  [WARN] No mapping for slug '{slug}' — skipping", file=sys.stderr)
            continue

        display_name, family, param_size, licensing = MODEL_LOOKUP[slug]

        if display_name in name_to_id:
            skipped.append((slug, display_name))
            continue

        elem_id = next_id
        next_id += 1

        if not dry_run:
            cur.execute(
                "INSERT INTO element(id, project_id, type_spec, name, description) VALUES (?,?,?,?,?)",
                (elem_id, 1, 'model', display_name, 'Lux Language Test'),
            )
            cur.execute(
                "INSERT INTO model(id, pid, data, source, licensing) VALUES (?,?,?,?,?)",
                (elem_id, display_name, param_size, family, licensing),
            )
            cur.execute(
                "INSERT INTO model_dataset(models, dataset) VALUES (?,?)",
                (elem_id, dataset_id),
            )

            for tsv_col, metric_name in TSV_TO_METRIC.items():
                metric_id = metric_name_to_id.get(metric_name)
                if metric_id is None:
                    print(f"  [WARN] Unknown metric '{metric_name}'", file=sys.stderr)
                    continue
                raw = row.get(tsv_col, '').strip()
                value = str(round(float(raw) * 100, 4)) if raw else 'Not Available'
                cur.execute(
                    "INSERT INTO measure(value, error, uncertainty, unit, observation_id, metric_id, measurand_id) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (value, 'Not Available', 0.0, 'percent', obs_id, metric_id, elem_id),
                )

            conn.commit()
            name_to_id[display_name] = elem_id

        inserted.append((elem_id, slug, display_name, family, param_size))

    return inserted, skipped


# ---------------------------------------------------------------------------
# Phase 2 — ensure "Macro Avg." metric row exists
# ---------------------------------------------------------------------------

def phase_ensure_metric(conn, metric_name_to_id, dry_run) -> int:
    name = MACRO_AVG_METRIC['name']
    if name in metric_name_to_id:
        metric_id = metric_name_to_id[name]
        print(f"  Metric '{name}' already exists (id={metric_id})")
        return metric_id

    cur = conn.cursor()
    cur.execute("SELECT MAX(id) FROM metric")
    new_id = (cur.fetchone()[0] or 0) + 1
    if not dry_run:
        cur.execute(
            "INSERT INTO metric(id, type_spec, name, description) VALUES (?,?,?,?)",
            (new_id, MACRO_AVG_METRIC['type_spec'], name, MACRO_AVG_METRIC['description']),
        )
        conn.commit()
        metric_name_to_id[name] = new_id
    print(f"  {'[DRY] Would insert' if dry_run else 'Inserted'} metric '{name}' id={new_id}")
    return new_id


# ---------------------------------------------------------------------------
# Phase 3 — populate Macro Avg. for all models with a summary.tsv
# ---------------------------------------------------------------------------

def phase_populate_macro_avg(conn, results_dir: Path, name_to_id: dict,
                              macro_metric_id: int, obs_id: int, dry_run: bool):
    cur = conn.cursor()

    # Build slug → element_id from known lookup + DB state
    slug_to_elem_id: dict[str, int] = {}
    for slug, (display_name, *_) in MODEL_LOOKUP.items():
        if display_name in name_to_id:
            slug_to_elem_id[slug] = name_to_id[display_name]

    # Collect existing Macro Avg. measures to avoid duplicate inserts
    cur.execute(
        "SELECT measurand_id FROM measure WHERE observation_id=? AND metric_id=?",
        (obs_id, macro_metric_id),
    )
    already_inserted = {r[0] for r in cur.fetchall()}

    inserted, skipped_dup, skipped_no_folder, skipped_no_db = [], [], [], []

    for slug, elem_id in sorted(slug_to_elem_id.items()):
        if should_exclude(slug):
            continue

        summary_path = results_dir / slug / 'summary.tsv'
        if not summary_path.exists():
            skipped_no_folder.append((slug, elem_id))
            continue

        if elem_id in already_inserted:
            skipped_dup.append((slug, elem_id))
            continue

        macro_frac = read_macro_avg_total(summary_path)
        if macro_frac is None:
            print(f"  [WARN] No MACRO_AVG TOTAL in {summary_path}", file=sys.stderr)
            continue

        value = str(round(macro_frac * 100, 4))

        if not dry_run:
            cur.execute(
                "INSERT INTO measure(value, error, uncertainty, unit, observation_id, metric_id, measurand_id) "
                "VALUES (?,?,?,?,?,?,?)",
                (value, 'Not Available', 0.0, 'percent', obs_id, macro_metric_id, elem_id),
            )
        inserted.append((slug, elem_id, value))

    if not dry_run:
        conn.commit()

    return inserted, skipped_dup, skipped_no_folder


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Add 'Macro Avg.' metric and populate it from per-model summary.tsv files."
    )
    ap.add_argument('--db',          required=True, type=Path, help='Path to AI_Sandbox.db')
    ap.add_argument('--results-dir', required=True, type=Path,
                    help='Directory containing per-model subdirs with summary.tsv')
    ap.add_argument('--tsv',         type=Path, default=None,
                    help='Optional: TSV of new models to insert before adding Macro Avg.')
    ap.add_argument('--dry-run',     action='store_true',
                    help='Preview changes without writing to the DB')
    args = ap.parse_args()

    if not args.db.exists():
        sys.exit(f"DB not found: {args.db}")
    if not args.results_dir.is_dir():
        sys.exit(f"Results dir not found: {args.results_dir}")
    if args.tsv and not args.tsv.exists():
        sys.exit(f"TSV not found: {args.tsv}")

    prefix = '[DRY-RUN] ' if args.dry_run else ''

    conn = sqlite3.connect(args.db.as_posix())
    name_to_id, metric_name_to_id, max_elem_id, dataset_id, obs_id = load_db_state(conn)

    # ── Phase 1: insert new models from TSV ──────────────────────────────────
    if args.tsv:
        tsv_rows = load_tsv_rows(args.tsv)
        print(f"\n{prefix}=== Phase 1: Insert new models from {args.tsv.name} ===")
        print(f"Rows after filtering: {len(tsv_rows)}")
        inserted_models, skipped_models = phase_insert_new_models(
            conn, tsv_rows, name_to_id, metric_name_to_id,
            max_elem_id, dataset_id, obs_id, args.dry_run,
        )
        print(f"Skipped (already in DB): {len(skipped_models)}")
        for slug, name in skipped_models:
            print(f"  SKIP  {slug!r:55s} → {name!r}")
        print(f"\n{'Would insert' if args.dry_run else 'Inserted'}: {len(inserted_models)} model(s)")
        for elem_id, slug, name, family, size in inserted_models:
            print(f"  {'[DRY] ' if args.dry_run else 'INSERT'} id={elem_id}  {slug!r:55s} → {name!r}  [{family}, {size}B]")
    else:
        print(f"\n{prefix}=== Phase 1: Skipped (no --tsv provided) ===")

    # ── Phase 2: ensure metric row ────────────────────────────────────────────
    print(f"\n{prefix}=== Phase 2: Ensure 'Macro Avg.' metric ===")
    macro_metric_id = phase_ensure_metric(conn, metric_name_to_id, args.dry_run)

    # ── Phase 3: populate Macro Avg. measures ─────────────────────────────────
    print(f"\n{prefix}=== Phase 3: Populate Macro Avg. measures ===")
    inserted_m, skipped_dup, skipped_no_folder = phase_populate_macro_avg(
        conn, args.results_dir, name_to_id, macro_metric_id, obs_id, args.dry_run,
    )

    print(f"{'Would insert' if args.dry_run else 'Inserted'}: {len(inserted_m)} measure(s)")
    for slug, elem_id, value in inserted_m:
        display = next(v[0] for k, v in MODEL_LOOKUP.items() if k == slug)
        print(f"  {'[DRY] ' if args.dry_run else 'OK    '} {slug!r:55s} → {display!r}  value={value}%")

    if skipped_dup:
        print(f"\nSkipped (already has Macro Avg.): {len(skipped_dup)}")
        for slug, elem_id in skipped_dup:
            print(f"  DUP   {slug!r}")

    if skipped_no_folder:
        print(f"\nSkipped (no summary.tsv folder): {len(skipped_no_folder)}")
        for slug, elem_id in skipped_no_folder:
            print(f"  MISS  {slug!r}")

    conn.close()
    print(f"\n{prefix}Done.")


if __name__ == '__main__':
    main()
