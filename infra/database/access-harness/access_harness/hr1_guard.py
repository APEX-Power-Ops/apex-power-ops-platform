"""access_harness.hr1_guard -- HR1 structural-columns-only enforcement.

HR1 rule: access_validation tables must contain ONLY structural columns
(counts, deltas, hashes, key tuples, booleans of structure, load-process
states).  Interpretive/verdict columns are forbidden.

INTERPRETIVE_DENYLIST: set of forbidden token strings.  A column name is
flagged if it EQUALS any token OR CONTAINS any token as a substring
(case-insensitive).

False-positive audit (all existing access_validation column names checked
against the denylist -- 2026-06-26):
  Existing columns: run_id, table_name, access_row_count, staging_row_count,
    delta, access_checksum, staging_checksum, matches, column_name,
    access_type, mapped_pg_type, coercion, not_comparable_coerced,
    candidate_key, is_unique, distinct_count, total_count, method,
    missing_in_tcc_count, extra_in_tcc_count, frames_with_deficit,
    enumerated_missing, row_antijoin_not_applicable, query_name,
    captured_at, row_count, result_snapshot, snapshot_id, access_table,
    tcc_table.
  None of these contain any denylist token as a substring.  Zero false
  positives confirmed.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Denylist
# ---------------------------------------------------------------------------

INTERPRETIVE_DENYLIST: set = {
    "is_gap",
    "gap",
    "correct",
    "is_correct",
    "expected",
    "category",
    "verdict",
    "judgment",
    "is_valid",
}


# ---------------------------------------------------------------------------
# Guard function
# ---------------------------------------------------------------------------

def assert_no_interpretive_columns(pg_conn) -> list:
    """Return a list of (table_name, column_name) for any interpretive column in
    access_validation schema.

    A column is flagged when its lowercased name EQUALS or CONTAINS any token
    from INTERPRETIVE_DENYLIST as a substring.

    Parameters
    ----------
    pg_conn : open psycopg connection.

    Returns
    -------
    list of (table_name, column_name) tuples.  Empty list means no violations.
    """
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'access_validation'
            ORDER BY table_name, ordinal_position
            """
        )
        rows = cur.fetchall()

    violations = []
    for table_name, column_name in rows:
        col_lower = column_name.lower()
        for token in INTERPRETIVE_DENYLIST:
            if token in col_lower:
                violations.append((table_name, column_name))
                break  # one violation per column is enough

    return violations
