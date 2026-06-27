"""access_harness.validate -- the CORE F-79-03 evidence engine.

Compare the local Access mirror (access_raw.*) against the local copy of the
governed tcc (tcc_snapshot.*, materialised by snapshot_tcc) and write PURELY
DESCRIPTIVE structural evidence into access_validation.*.

HR1 (load-bearing): NO BEHAVIORAL INTERPRETATION.
-------------------------------------------------
Every row written here is structural evidence ONLY: counts, deltas, enumerated
key tuples, per-key count deltas, and booleans-of-structure.  This module NEVER
decides whether a delta is "correct", "a gap", "expected", or anything
interpretive.  It records WHAT differs; it never opines on WHY or whether that
is acceptable.  (The hr1_guard test asserts no interpretive column names exist.)

Public API
----------
key_quality(pg_conn, schema, table, key_cols, *, run_id=None, write=False)
    -> {'is_unique', 'distinct_count', 'total_count'}.  Optionally writes an
    access_validation.key_quality row.

antijoin_keyset(pg_conn, left_schema, left_table, right_schema, right_table,
                key_cols) -> dict
    Local-to-local anti-join of the two key-sets.  If the LEFT key is UNIQUE,
    uses an exact SET-DIFF and enumerates the missing / extra key tuples.  If
    the LEFT key is NON-UNIQUE, falls back to a Counter-based MULTISET diff
    keyed on the canonical string of each key tuple (the Task-2 contract: the
    Counter keys are canonical strings, not raw tuples, and both sides use
    identical col_types).

antijoin_vs_tcc(pg_conn, run_id, snapshot_id, access_table, access_key_cols)
    Write ONE access_validation.antijoin_vs_tcc row for the table.  Computed /
    derived tcc tables (curves / thermal_adj) are COUNT-ONLY (no row EXCEPT --
    curves is ~1.1M rows).  1:1_load tables run the style-mediated guard
    (assert_key_allowed) for EVERY key col -- a surrogate -> tmt_frames.id
    keying RAISES ForbiddenKeyError -- then the local anti-join.

reconcile_counts(pg_conn, run_id)
    Write access_validation.row_count_reconciliation per loaded table
    (access_row_count vs staging_row_count + delta) from access_meta.tables.

All identifiers are quoted via psycopg.sql.Identifier (never f-string-injected).
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from psycopg import sql
from psycopg.types.json import Jsonb

from access_harness.checksum import canonical_row, multiset_diff
from access_harness.projection import ProjectionMap, assert_key_allowed
from access_harness.typemap import ColumnType

# Cap on how many missing key tuples are enumerated into the jsonb column.  The
# FULL count is always recorded separately in missing_in_tcc_count, so capping
# the enumeration bounds the row size without losing the headline number.
ENUMERATION_CAP = 1000


# ---------------------------------------------------------------------------
# Internal: a neutral ColumnType for canonicalisation of key tuples.
# ---------------------------------------------------------------------------

def _neutral_col_types(n: int) -> List[ColumnType]:
    """Return n neutral ColumnTypes for canonicalising key tuples.

    The Task-2 contract requires BOTH compare sides to canonicalise with
    IDENTICAL col_types.  Key columns read back from Postgres come back as
    native Python scalars (int / str / Decimal / datetime / bytes), and
    canonical_row encodes each by the value's *nature* -- the only col_type
    field it consults is pg_type, and only to force '.17g' float formatting.
    Key columns are never floats (anti-join keys are discrete), so a single
    neutral 'text' pg_type is correct and identical on both sides.
    """
    return [
        ColumnType(
            access_type="",
            pg_type="text",
            nullable=True,
            size=None,
            precision=None,
            round_trippable=True,
            name="",
        )
        for _ in range(n)
    ]


# ---------------------------------------------------------------------------
# Internal: read all key tuples from a table.
# ---------------------------------------------------------------------------

def _read_key_tuples(pg_conn, schema: str, table: str, key_cols: List[str]) -> List[tuple]:
    """SELECT the key columns from schema.table and return them as a list of tuples."""
    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in key_cols)
    stmt = sql.SQL("SELECT {cols} FROM {schema}.{table}").format(
        cols=col_ids,
        schema=sql.Identifier(schema),
        table=sql.Identifier(table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        return [tuple(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# key_quality
# ---------------------------------------------------------------------------

def key_quality(
    pg_conn,
    schema: str,
    table: str,
    key_cols: List[str],
    *,
    run_id: Optional[str] = None,
    write: bool = False,
) -> Dict[str, object]:
    """Return key-uniqueness evidence for schema.table over key_cols.

    Runs a single SELECT count(*), count(DISTINCT (key_cols...)) so the row scan
    is shared.  is_unique is True iff distinct_count == total_count.

    Parameters
    ----------
    pg_conn  : open psycopg connection.
    schema   : schema name (e.g. 'access_raw').
    table    : table name (verbatim, may contain spaces).
    key_cols : the candidate key columns.
    run_id   : when write=True, the FK recorded on the key_quality row.
    write    : when True, upsert one access_validation.key_quality row.

    Returns
    -------
    {'is_unique': bool, 'distinct_count': int, 'total_count': int}
    """
    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in key_cols)
    # count(DISTINCT (a, b)) counts distinct ROW values; ROW() makes the tuple
    # explicit so a single key column behaves identically to a composite key.
    stmt = sql.SQL(
        "SELECT count(*), count(DISTINCT ROW({cols})) "
        "FROM {schema}.{table}"
    ).format(
        cols=col_ids,
        schema=sql.Identifier(schema),
        table=sql.Identifier(table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        total_count, distinct_count = cur.fetchone()

    total_count = int(total_count)
    distinct_count = int(distinct_count)
    is_unique = distinct_count == total_count

    result = {
        "is_unique": is_unique,
        "distinct_count": distinct_count,
        "total_count": total_count,
    }

    if write:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_validation.key_quality
                    (run_id, table_name, candidate_key, is_unique,
                     distinct_count, total_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, table_name) DO UPDATE SET
                    candidate_key = EXCLUDED.candidate_key,
                    is_unique = EXCLUDED.is_unique,
                    distinct_count = EXCLUDED.distinct_count,
                    total_count = EXCLUDED.total_count
                """,
                (run_id, table, list(key_cols), is_unique,
                 distinct_count, total_count),
            )

    return result


# ---------------------------------------------------------------------------
# antijoin_keyset
# ---------------------------------------------------------------------------

def antijoin_keyset(
    pg_conn,
    left_schema: str,
    left_table: str,
    right_schema: str,
    right_table: str,
    key_cols: List[str],
) -> Dict[str, object]:
    """Anti-join two LOCAL key-sets and report the differences descriptively.

    Reads the key tuples from both tables.  Branch:

      * LEFT key UNIQUE (no duplicate key tuples) -> exact SET-DIFF:
          missing_in_right = left_keys - right_keys
          extra_in_right   = right_keys - left_keys
        each returned as a sorted list of raw key TUPLES; method='setdiff'.

      * LEFT key NON-UNIQUE -> MULTISET diff:
        build a collections.Counter keyed on the CANONICAL STRING of each key
        tuple (Task-2 contract: keys are canonical strings, identical col_types
        on both sides) and run multiset_diff -> per-key {access, tcc, delta};
        method='multiset'.  missing_in_right / extra_in_right carry that
        per-key delta mapping.

    Returns
    -------
    {'method', 'missing_in_right', 'extra_in_right',
     'missing_count', 'extra_count'}

    For setdiff:  missing_count = len(missing tuples), extra_count = len(extra).
    For multiset: missing_count = sum of POSITIVE deltas (left/access excess),
                  extra_count   = sum of |NEGATIVE deltas| (right/tcc excess).
    """
    left_rows = _read_key_tuples(pg_conn, left_schema, left_table, key_cols)
    right_rows = _read_key_tuples(pg_conn, right_schema, right_table, key_cols)

    left_unique = len(left_rows) == len(set(left_rows))

    if left_unique:
        left_set = set(left_rows)
        right_set = set(right_rows)
        missing = sorted(left_set - right_set)
        extra = sorted(right_set - left_set)
        return {
            "method": "setdiff",
            "missing_in_right": missing,
            "extra_in_right": extra,
            "missing_count": len(missing),
            "extra_count": len(extra),
        }

    # Non-unique left key -> multiset path.  Canonicalise each key tuple to a
    # string with identical col_types on both sides (Task-2 contract).
    col_types = _neutral_col_types(len(key_cols))
    left_counter: Counter = Counter(
        canonical_row(row, col_types) for row in left_rows
    )
    right_counter: Counter = Counter(
        canonical_row(row, col_types) for row in right_rows
    )
    diff = multiset_diff(left_counter, right_counter)

    # delta = access(left) - tcc(right): positive -> left excess (missing in
    # right), negative -> right excess (extra in right).
    missing_count = sum(v["delta"] for v in diff.values() if v["delta"] > 0)
    extra_count = sum(-v["delta"] for v in diff.values() if v["delta"] < 0)

    return {
        "method": "multiset",
        "missing_in_right": diff,
        "extra_in_right": diff,
        "missing_count": missing_count,
        "extra_count": extra_count,
    }


# ---------------------------------------------------------------------------
# antijoin_vs_tcc
# ---------------------------------------------------------------------------

def _tcc_snapshot_count(pg_conn, snapshot_id: str, tcc_table: str) -> Optional[int]:
    """Return the recorded tcc row count for (snapshot_id, tcc_table), or None."""
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT tcc_row_count FROM access_meta.tcc_snapshot_table "
            "WHERE snapshot_id=%s AND table_name=%s",
            (snapshot_id, tcc_table),
        )
        row = cur.fetchone()
    return int(row[0]) if row is not None else None


def _access_count(pg_conn, access_table: str) -> int:
    """SELECT count(*) FROM access_raw.<access_table>."""
    stmt = sql.SQL("SELECT count(*) FROM {schema}.{table}").format(
        schema=sql.Identifier("access_raw"),
        table=sql.Identifier(access_table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        (n,) = cur.fetchone()
    return int(n)


def antijoin_vs_tcc(
    pg_conn,
    run_id: str,
    snapshot_id: str,
    access_table: str,
    access_key_cols: List[str],
) -> None:
    """Write ONE access_validation.antijoin_vs_tcc row of structural evidence.

    Dispatch on the projection's tcc_build_kind:

      * 'computed' / 'derived'  -> COUNT-ONLY.  Compare the access_raw count
        against the recorded tcc snapshot count; record method='count_only',
        row_antijoin_not_applicable=True, enumerated_missing=NULL.  NO row
        EXCEPT is run (curves is ~1.1M rows).  Direction:
            delta = access_count - tcc_count
            delta > 0 -> missing_in_tcc_count = delta,  extra_in_tcc_count = 0
            delta < 0 -> extra_in_tcc_count = -delta,   missing_in_tcc_count = 0

      * '1:1_load' -> map access_key_cols to tcc cols via pm.col_map (unmapped
        cols keep their name), then call assert_key_allowed for EVERY key col
        (so a surrogate -> tmt_frames.id keying RAISES ForbiddenKeyError -- the
        red-team guard; it is NOT caught), then run antijoin_keyset against
        tcc_snapshot.<pm.tcc_table>.  For setdiff, enumerated_missing is the
        capped (<= ENUMERATION_CAP) jsonb array of missing key tuples; the FULL
        count is in missing_in_tcc_count.  For multiset, enumerated_missing is
        the per-key delta mapping.
    """
    pm = ProjectionMap.for_table(access_table)
    tcc_table = pm.tcc_table

    # -- COUNT-ONLY branch for computed / derived tcc tables. ----------------
    if pm.tcc_build_kind in ("computed", "derived"):
        access_count = _access_count(pg_conn, access_table)
        tcc_count = _tcc_snapshot_count(pg_conn, snapshot_id, tcc_table)
        if tcc_count is None:
            # Fall back to counting a materialised local table if it exists;
            # otherwise treat the tcc side as absent (count 0) so the evidence
            # is still descriptive rather than crashing.
            tcc_count = _count_local_if_present(pg_conn, "tcc_snapshot", tcc_table)
        delta = access_count - tcc_count
        missing_in_tcc = delta if delta > 0 else 0
        extra_in_tcc = -delta if delta < 0 else 0
        _write_antijoin_row(
            pg_conn,
            run_id=run_id,
            snapshot_id=snapshot_id,
            access_table=access_table,
            tcc_table=tcc_table,
            method="count_only",
            missing_in_tcc_count=missing_in_tcc,
            extra_in_tcc_count=extra_in_tcc,
            enumerated_missing=None,
            row_antijoin_not_applicable=True,
        )
        return

    # -- 1:1_load branch: style-mediated guard then local anti-join. ---------
    # Map each access key col to its tcc col (unmapped keeps its own name).
    tcc_key_cols = [pm.col_map.get(c, c) for c in access_key_cols]

    # RED-TEAM GUARD: assert_key_allowed for EVERY key col.  A raw surrogate
    # (ID / FrameSizeID) -> tmt_frames.id RAISES ForbiddenKeyError; we do NOT
    # catch it -- the structurally-dishonest join must be impossible.
    for a_col, t_col in zip(access_key_cols, tcc_key_cols):
        assert_key_allowed(
            pm,
            f"{access_table}.{a_col}",
            f"{tcc_table}.{t_col}",
        )

    # The local anti-join keys on the access column NAMES against the tcc
    # snapshot table; the snapshot table is materialised with the tcc column
    # names, so we read each side with its own column list.
    result = _antijoin_keyset_mapped(
        pg_conn,
        access_table=access_table,
        access_key_cols=access_key_cols,
        tcc_table=tcc_table,
        tcc_key_cols=tcc_key_cols,
    )

    if result["method"] == "setdiff":
        missing_tuples = result["missing_in_right"]
        # Cap the enumeration; the FULL count is missing_count.
        capped = [list(t) for t in missing_tuples[:ENUMERATION_CAP]]
        enumerated = Jsonb(capped)
    else:  # multiset -> per-key delta mapping
        enumerated = Jsonb(result["missing_in_right"])

    _write_antijoin_row(
        pg_conn,
        run_id=run_id,
        snapshot_id=snapshot_id,
        access_table=access_table,
        tcc_table=tcc_table,
        method=result["method"],
        missing_in_tcc_count=result["missing_count"],
        extra_in_tcc_count=result["extra_count"],
        enumerated_missing=enumerated,
        row_antijoin_not_applicable=False,
    )


def _count_local_if_present(pg_conn, schema: str, table: str) -> int:
    """Count rows in schema.table if it exists locally, else 0."""
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name=%s",
            (schema, table),
        )
        (exists,) = cur.fetchone()
    if not exists:
        return 0
    stmt = sql.SQL("SELECT count(*) FROM {schema}.{table}").format(
        schema=sql.Identifier(schema), table=sql.Identifier(table)
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        (n,) = cur.fetchone()
    return int(n)


def _antijoin_keyset_mapped(
    pg_conn,
    access_table: str,
    access_key_cols: List[str],
    tcc_table: str,
    tcc_key_cols: List[str],
) -> Dict[str, object]:
    """antijoin_keyset variant that reads each side with ITS OWN key columns.

    The access side keys on access_key_cols; the tcc snapshot side keys on the
    mapped tcc_key_cols (which may differ in name, e.g. TripAmp -> rating).
    The compare is positional -- column i on the left aligns to column i on the
    right -- so the tuples are directly comparable.
    """
    left_rows = _read_key_tuples(pg_conn, "access_raw", access_table, access_key_cols)
    right_rows = _read_key_tuples(pg_conn, "tcc_snapshot", tcc_table, tcc_key_cols)

    left_unique = len(left_rows) == len(set(left_rows))

    if left_unique:
        left_set = set(left_rows)
        right_set = set(right_rows)
        missing = sorted(left_set - right_set)
        extra = sorted(right_set - left_set)
        return {
            "method": "setdiff",
            "missing_in_right": missing,
            "extra_in_right": extra,
            "missing_count": len(missing),
            "extra_count": len(extra),
        }

    col_types = _neutral_col_types(len(access_key_cols))
    left_counter: Counter = Counter(canonical_row(r, col_types) for r in left_rows)
    right_counter: Counter = Counter(canonical_row(r, col_types) for r in right_rows)
    diff = multiset_diff(left_counter, right_counter)
    missing_count = sum(v["delta"] for v in diff.values() if v["delta"] > 0)
    extra_count = sum(-v["delta"] for v in diff.values() if v["delta"] < 0)
    return {
        "method": "multiset",
        "missing_in_right": diff,
        "extra_in_right": diff,
        "missing_count": missing_count,
        "extra_count": extra_count,
    }


def _write_antijoin_row(
    pg_conn,
    *,
    run_id: str,
    snapshot_id: str,
    access_table: str,
    tcc_table: str,
    method: str,
    missing_in_tcc_count: int,
    extra_in_tcc_count: int,
    enumerated_missing,
    row_antijoin_not_applicable: bool,
) -> None:
    """Upsert ONE access_validation.antijoin_vs_tcc row (PK run_id, access_table)."""
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_validation.antijoin_vs_tcc
                (run_id, snapshot_id, access_table, tcc_table, method,
                 missing_in_tcc_count, extra_in_tcc_count, frames_with_deficit,
                 enumerated_missing, row_antijoin_not_applicable)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s, %s)
            ON CONFLICT (run_id, access_table) DO UPDATE SET
                snapshot_id = EXCLUDED.snapshot_id,
                tcc_table = EXCLUDED.tcc_table,
                method = EXCLUDED.method,
                missing_in_tcc_count = EXCLUDED.missing_in_tcc_count,
                extra_in_tcc_count = EXCLUDED.extra_in_tcc_count,
                enumerated_missing = EXCLUDED.enumerated_missing,
                row_antijoin_not_applicable = EXCLUDED.row_antijoin_not_applicable
            """,
            (run_id, snapshot_id, access_table, tcc_table, method,
             int(missing_in_tcc_count), int(extra_in_tcc_count),
             enumerated_missing, row_antijoin_not_applicable),
        )


# ---------------------------------------------------------------------------
# reconcile_counts
# ---------------------------------------------------------------------------

def reconcile_counts(pg_conn, run_id: str) -> None:
    """Write access_validation.row_count_reconciliation per loaded table.

    Reads access_meta.tables for the run (load_state='loaded') and writes one
    row_count_reconciliation row per table: access_row_count, staging_row_count,
    and delta = access_row_count - staging_row_count.  Purely descriptive.
    """
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, access_row_count, staging_row_count
            FROM access_meta.tables
            WHERE run_id = %s AND load_state = 'loaded'
            """,
            (run_id,),
        )
        rows = cur.fetchall()

    with pg_conn.cursor() as cur:
        for table_name, access_ct, staging_ct in rows:
            # delta is NULL-safe: if either count is NULL the delta is NULL
            # (no fabricated zero -- absence is recorded honestly).
            if access_ct is None or staging_ct is None:
                delta = None
            else:
                delta = int(access_ct) - int(staging_ct)
            cur.execute(
                """
                INSERT INTO access_validation.row_count_reconciliation
                    (run_id, table_name, access_row_count, staging_row_count, delta)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (run_id, table_name) DO UPDATE SET
                    access_row_count = EXCLUDED.access_row_count,
                    staging_row_count = EXCLUDED.staging_row_count,
                    delta = EXCLUDED.delta
                """,
                (run_id, table_name, access_ct, staging_ct, delta),
            )
