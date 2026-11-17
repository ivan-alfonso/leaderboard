"""
Read-only SQLite data access for LëtzEval BAF agent.
All queries use parameterized statements (? placeholders).
The DB is opened in read-only mode via SQLite URI; DDL/DML is structurally impossible.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional

_DEFAULT_DB = Path(__file__).parent.parent.parent / 'backend' / 'data' / 'AI_Sandbox.db'
DB_PATH = Path(os.environ.get('LETZEVAL_DB_PATH', str(_DEFAULT_DB)))

# Verified metric IDs from DB audit (measure table, 102 models × 31 metrics = 3162 rows confirmed)
METRIC_IDS: dict[tuple[str, str], int] = {
    ('A1', 'Grammar'): 1,  ('A1', 'LC'): 2,  ('A1', 'RC'): 3,  ('A1', 'Vocab'): 4,  ('A1', 'Total'): 5,
    ('A2', 'Grammar'): 6,  ('A2', 'LC'): 7,  ('A2', 'RC'): 8,  ('A2', 'Vocab'): 9,  ('A2', 'Total'): 10,
    ('B1', 'Grammar'): 11, ('B1', 'LC'): 12, ('B1', 'RC'): 13, ('B1', 'Vocab'): 14, ('B1', 'Total'): 15,
    ('B2', 'Grammar'): 16, ('B2', 'LC'): 17, ('B2', 'RC'): 18, ('B2', 'Vocab'): 19, ('B2', 'Total'): 20,
    ('C1', 'Grammar'): 21, ('C1', 'LC'): 22, ('C1', 'RC'): 23, ('C1', 'Vocab'): 24, ('C1', 'Total'): 25,
    ('C2', 'Grammar'): 26, ('C2', 'LC'): 27, ('C2', 'RC'): 28, ('C2', 'Vocab'): 29, ('C2', 'Total'): 30,
    ('All', 'Macro'): 31,
}

CEFR_LEVELS = ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
CATEGORIES = ('Grammar', 'LC', 'RC', 'Vocab', 'Total')
MAX_ROWS = 25


def _conn() -> sqlite3.Connection:
    """Open a SQLite read-only connection via URI."""
    uri = f'file:{DB_PATH}?mode=ro'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def lookup_score(model_name: str, level: str, category: str) -> Optional[dict]:
    """Look up one verified score. Returns None if model or metric not found."""
    if level == 'All' and category in ('Macro', 'Total'):
        key = ('All', 'Macro')
    else:
        key = (level, category)
    metric_id = METRIC_IDS.get(key)
    if metric_id is None:
        return None
    with _conn() as c:
        row = c.execute(
            """SELECT e.name AS model_name, met.name AS metric_name,
                      ms.value, ms.unit
               FROM model m
               JOIN element e ON e.id = m.id
               JOIN measure ms ON ms.measurand_id = m.id AND ms.metric_id = ?
               JOIN metric met ON met.id = ms.metric_id
               WHERE LOWER(e.name) = LOWER(?)""",
            (metric_id, model_name)
        ).fetchone()
    return dict(row) if row else None


def rank_models(
    level: str,
    category: str,
    top_n: int = 5,
    ascending: bool = False,
    licensing: Optional[str] = None,
    family: Optional[str] = None,
) -> list[dict]:
    """Rank models by a specific verified metric. Returns up to MAX_ROWS results."""
    key = (level, category)
    metric_id = METRIC_IDS.get(key)
    if metric_id is None:
        return []

    n = min(max(1, top_n), MAX_ROWS)
    direction = 'ASC' if ascending else 'DESC'

    sql = """SELECT e.name AS model_name, m.source AS family,
                    m.licensing, CAST(ms.value AS REAL) AS score
             FROM model m
             JOIN element e ON e.id = m.id
             JOIN measure ms ON ms.measurand_id = m.id AND ms.metric_id = ?
             WHERE 1=1"""
    params: list = [metric_id]

    if licensing:
        sql += " AND m.licensing = ?"
        params.append(licensing)
    if family:
        sql += " AND LOWER(m.source) = LOWER(?)"
        params.append(family)

    sql += f" ORDER BY score {direction} LIMIT ?"
    params.append(n)

    with _conn() as c:
        rows = c.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def compare_models(model_names: list[str], level: str, category: str) -> list[dict]:
    """Fetch the same metric for 2–3 named models."""
    key = (level, category)
    metric_id = METRIC_IDS.get(key)
    if metric_id is None:
        return []
    if not model_names:
        return []

    placeholders = ','.join('?' * len(model_names))
    names_lower = [n.lower() for n in model_names]

    sql = f"""SELECT e.name AS model_name, m.source AS family,
                     CAST(ms.value AS REAL) AS score, ms.unit
              FROM model m
              JOIN element e ON e.id = m.id
              JOIN measure ms ON ms.measurand_id = m.id AND ms.metric_id = ?
              WHERE LOWER(e.name) IN ({placeholders})
              ORDER BY score DESC"""

    with _conn() as c:
        rows = c.execute(sql, [metric_id] + names_lower).fetchall()
    return [dict(r) for r in rows]


def lookup_all_cefr_totals(model_name: str) -> list[dict]:
    """Fetch all six CEFR-level Total scores for a model in A1→C2 order."""
    total_ids = [
        METRIC_IDS[('A1', 'Total')],
        METRIC_IDS[('A2', 'Total')],
        METRIC_IDS[('B1', 'Total')],
        METRIC_IDS[('B2', 'Total')],
        METRIC_IDS[('C1', 'Total')],
        METRIC_IDS[('C2', 'Total')],
    ]
    placeholders = ','.join('?' * len(total_ids))
    with _conn() as c:
        rows = c.execute(
            f"""SELECT e.name AS model_name, met.name AS metric_name,
                       CAST(ms.value AS REAL) AS score
                FROM model m
                JOIN element e ON e.id = m.id
                JOIN measure ms ON ms.measurand_id = m.id AND ms.metric_id IN ({placeholders})
                JOIN metric met ON met.id = ms.metric_id
                WHERE LOWER(e.name) = LOWER(?)
                ORDER BY ms.metric_id""",
            total_ids + [model_name]
        ).fetchall()
    return [dict(r) for r in rows]


def find_models(query: str, max_results: int = 8) -> list[dict]:
    """Partial name search: returns models whose name contains the query string."""
    with _conn() as c:
        rows = c.execute(
            """SELECT e.name, m.source AS family, m.licensing, m.data AS size
               FROM model m JOIN element e ON e.id = m.id
               WHERE LOWER(e.name) LIKE ?
               ORDER BY e.name LIMIT ?""",
            (f'%{query.lower()}%', min(max_results, MAX_ROWS))
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_model_names() -> list[str]:
    with _conn() as c:
        rows = c.execute(
            "SELECT e.name FROM model m JOIN element e ON e.id = m.id ORDER BY e.name"
        ).fetchall()
    return [r['name'] for r in rows]


def get_model_count() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM model").fetchone()[0]


def get_model_families() -> list[str]:
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT source FROM model ORDER BY source"
        ).fetchall()
    return [r['source'] for r in rows]


def get_coverage_stats() -> dict:
    """Return coverage statistics for the leaderboard."""
    with _conn() as c:
        model_count = c.execute("SELECT COUNT(*) FROM model").fetchone()[0]
        families = c.execute("SELECT COUNT(DISTINCT source) FROM model").fetchone()[0]
        open_source = c.execute(
            "SELECT COUNT(*) FROM model WHERE licensing != 'Proprietary'"
        ).fetchone()[0]
    return {
        'model_count': model_count,
        'families': families,
        'open_source': open_source,
        'proprietary': model_count - open_source,
        'cefr_levels': list(CEFR_LEVELS),
        'categories': list(CATEGORIES),
        'total_metrics': 31,
    }
