"""
Build a combined flat TSV from individual per-model summary.tsv files.

Each model directory under --results-dir must contain a summary.tsv with rows:
    Level   TOTAL   grammar   listening_comprehension   reading_comprehension   vocabulary

The output matches the format expected by append_new_models.py:
    Model   A1_grammar   A1_listening_comprehension   ...   C2_vocabulary

Filtering (same rules as append_new_models.py):
    - Skip dirs ending with   -lb
    - Skip dirs containing    -luxit-
    - Skip dirs starting with eu-institutional-llm-v1
                               eu-institutional-mm-v1

Usage:
    python build_combined_tsv.py --results-dir <path> --output <path.tsv>
    python build_combined_tsv.py --results-dir <path> --output <path.tsv> --overwrite
"""
import argparse
import csv
import sys
from pathlib import Path

LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
METRICS = ['grammar', 'listening_comprehension', 'reading_comprehension', 'total', 'vocabulary']

# TSV col header order (must match append_new_models.py TSV_TO_METRIC keys)
HEADER = ['Model'] + [f'{lvl}_{m}' for lvl in LEVELS for m in METRICS]

EXCLUDE_PATTERNS = [
    lambda s: s.endswith('-lb'),
    lambda s: '-luxit-' in s,
    lambda s: s.startswith('eu-institutional-llm-v1'),
    lambda s: s.startswith('eu-institutional-mm-v1'),
]


def should_exclude(name: str) -> bool:
    return any(p(name) for p in EXCLUDE_PATTERNS)


def read_model_summary(tsv_path: Path) -> dict | None:
    """Return {A1_grammar: '0.769', ...} or None on error."""
    data = {}
    try:
        with tsv_path.open(encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                lvl = row.get('Level', '').strip().upper()
                if lvl not in LEVELS:
                    continue  # skip MACRO_AVG and any unexpected rows
                for col in ('grammar', 'listening_comprehension',
                             'reading_comprehension', 'vocabulary'):
                    data[f'{lvl}_{col}'] = row.get(col, '').strip()
                data[f'{lvl}_total'] = row.get('TOTAL', '').strip()
    except Exception as exc:
        print(f"  [WARN] Could not read {tsv_path}: {exc}", file=sys.stderr)
        return None
    if not data:
        return None
    return data


def main():
    ap = argparse.ArgumentParser(
        description="Combine per-model summary.tsv files into a single flat TSV")
    ap.add_argument("--results-dir", required=True, type=Path,
                    help="Root directory containing one sub-dir per model")
    ap.add_argument("--output", required=True, type=Path,
                    help="Output TSV path")
    ap.add_argument("--overwrite", action="store_true",
                    help="Overwrite output file if it already exists")
    args = ap.parse_args()

    if not args.results_dir.is_dir():
        sys.exit(f"Results dir not found: {args.results_dir}")

    if args.output.exists() and not args.overwrite:
        sys.exit(
            f"Output file already exists: {args.output}\n"
            "Pass --overwrite to replace it."
        )

    model_dirs = sorted(
        d for d in args.results_dir.iterdir()
        if d.is_dir() and not should_exclude(d.name)
    )

    rows = []
    skipped = []
    for d in model_dirs:
        tsv_path = d / 'summary.tsv'
        if not tsv_path.exists():
            skipped.append((d.name, 'no summary.tsv'))
            continue
        data = read_model_summary(tsv_path)
        if data is None:
            skipped.append((d.name, 'parse error'))
            continue
        row = {'Model': d.name}
        row.update(data)
        rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written {len(rows)} model rows → {args.output}")
    if skipped:
        print(f"Skipped {len(skipped)} dirs:")
        for name, reason in skipped:
            print(f"  {name!r} ({reason})")


if __name__ == "__main__":
    main()
