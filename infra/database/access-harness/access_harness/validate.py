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

from access_harness.checksum import canonical_row, multiset_diff, table_checksum
from access_harness.projection import ProjectionMap, assert_key_allowed
from access_harness.typemap import ColumnType

# Cap on how many missing key tuples are enumerated into the jsonb column.  The
# FULL count is always recorded separately in missing_in_tcc_count, so capping
# the enumeration bounds the row size without losing the headline number.
ENUMERATION_CAP = 1000


# ---------------------------------------------------------------------------
# Multi-run isolation guard (fixes 5+6): fail closed on superseded materialise.
#
# The access_raw.* and tcc_snapshot.* materialised tables are LATEST-ONLY:
# load.py drops+recreates access_raw.<table> PER TABLE and snapshot_tcc.py
# replaces tcc_snapshot.<table> PER MATERIALISED TABLE, while META/evidence rows
# are keyed by run_id / snapshot_id (retain-all-runs, D3).  Because validate
# reads the materialised tables but is keyed by run_id / snapshot_id, validating
# an OLD run_id / snapshot_id after a later load / snapshot replaced a table
# would silently read the NEWER materialised data = mixed evidence for the WRONG
# source.
#
# Ownership is recorded PER (layer, table_name): each load_table stamps ONLY the
# table it replaced; each snapshot stamps ONLY the tables it materialised.  A
# WHOLE-LAYER marker would be UNSOUND because a PARTIAL/subset materialisation (a
# default run after a prior --with-curves run; a mid-slice failure after earlier
# commits; a subset snapshot that omits a table) replaces only SOME tables -- a
# later run could stamp the whole layer while a table from a PRIOR run/snapshot
# survives, and the guard would pass while validate reads the stale table.
# assert_materialized_owner checks, FOR EACH table it is about to read, that THAT
# table's owner equals the requested id; it raises if any differs (fail closed).
# ---------------------------------------------------------------------------

_ACCESS_RAW_LAYER = "access_raw"
_TCC_SNAPSHOT_LAYER = "tcc_snapshot"


class SupersededMaterializationError(RuntimeError):
    """Raised when a requested run_id / snapshot_id no longer owns a materialised
    table it would read (a later load / snapshot replaced THAT table)."""


def stamp_materialized_owner(
    pg_conn,
    layer: str,
    table_name: str,
    *,
    run_id: Optional[str] = None,
    snapshot_id: Optional[str] = None,
) -> None:
    """Record that (run_id | snapshot_id) now owns the materialised *table*.

    Called by load (layer='access_raw', run_id=..., the one table it just
    dropped+recreated) and snapshot_tcc (layer='tcc_snapshot', snapshot_id=...,
    each table it actually materialised) AFTER they replace the materialised
    table, so validate can fail closed for a superseded id.  Upserts the per-
    table marker row (PK = (layer, table_name)).
    """
    from datetime import datetime, timezone

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.materialized_owner
                (layer, table_name, run_id, snapshot_id, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (layer, table_name) DO UPDATE SET
                run_id = EXCLUDED.run_id,
                snapshot_id = EXCLUDED.snapshot_id,
                updated_at = EXCLUDED.updated_at
            """,
            (layer, table_name, run_id, snapshot_id,
             datetime.now(tz=timezone.utc)),
        )


def assert_materialized_owner(
    pg_conn,
    layer: str,
    tables,
    *,
    run_id: Optional[str] = None,
    snapshot_id: Optional[str] = None,
) -> None:
    """Raise SupersededMaterializationError unless (run_id | snapshot_id) is the
    CURRENT owner of EVERY materialised *table* in *tables* it would read.

    *tables* is the iterable of table names validate is about to READ on *layer*.
    For layer='access_raw' the owning key is run_id; for layer='tcc_snapshot' it
    is snapshot_id.  For EACH table:
      * No per-table marker (first run / synthetic fixture that built the table
        directly without stamping) -> NO-OP for that table (do not block).
      * A marker that names a DIFFERENT owner -> fail closed, naming the table
        plus the owning vs requested id (the genuine superseded case, incl. a
        PARTIAL materialisation that left this table from another run/snapshot).
    """
    if layer == _ACCESS_RAW_LAYER:
        expected, col = run_id, "run_id"
    elif layer == _TCC_SNAPSHOT_LAYER:
        expected, col = snapshot_id, "snapshot_id"
    else:  # pragma: no cover - defensive
        raise ValueError(f"unknown materialised layer: {layer!r}")

    for table_name in tables:
        with pg_conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT {col} FROM access_meta.materialized_owner "
                    "WHERE layer=%s AND table_name=%s"
                ).format(col=sql.Identifier(col)),
                (layer, table_name),
            )
            row = cur.fetchone()

        # No marker for this table -> nothing has claimed ownership (first run /
        # synthetic fixture): do not block.  A marker naming a different owner ->
        # fail closed.
        if row is None or row[0] is None:
            continue
        current = row[0]
        if current != expected:
            raise SupersededMaterializationError(
                f"{col}={expected!r} is SUPERSEDED for materialised table "
                f"{layer}.{table_name!r}: that table is owned by "
                f"{col}={current!r}.  The materialised {layer}.{table_name} "
                f"table was replaced (or left) by a different load/snapshot; "
                f"validating {expected!r} would read mixed evidence for the "
                f"wrong source.  Re-run extract/load/snapshot for {expected!r}, "
                f"or validate the current owner {current!r}."
            )


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

    # Separate directions: missing = positive-delta only; extra = negative only.
    missing_in_right = {k: v for k, v in diff.items() if v["delta"] > 0}
    extra_in_right = {k: v for k, v in diff.items() if v["delta"] < 0}

    return {
        "method": "multiset",
        "missing_in_right": missing_in_right,
        "extra_in_right": extra_in_right,
        "missing_count": missing_count,
        "extra_count": extra_count,
        # Full count of distinct keys that have ANY discrepancy (both directions).
        "distinct_discrepant_count": len(diff),
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


def _access_count_or_meta(pg_conn, run_id: str, access_table: str) -> Optional[int]:
    """Access-side row count, preferring the materialised access_raw table.

    Returns count(*) from access_raw.<access_table> when that table exists
    (it was data-loaded).  When it does NOT exist (e.g. curves was deliberately
    NOT data-loaded -- the count-only path), falls back to the row count
    inventory recorded in access_meta.tables.access_row_count for this run.
    Returns None if neither is available (honest absence -- never a fabricated 0).
    """
    # access_raw table present?
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='access_raw' AND table_name=%s",
            (access_table,),
        )
        present = cur.fetchone() is not None
    if present:
        return _access_count(pg_conn, access_table)
    # fall back to the inventory-recorded access_row_count
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT access_row_count FROM access_meta.tables "
            "WHERE run_id=%s AND table_name=%s",
            (run_id, access_table),
        )
        row = cur.fetchone()
    return int(row[0]) if row is not None and row[0] is not None else None


def antijoin_vs_tcc(
    pg_conn,
    run_id: str,
    snapshot_id: str,
    access_table: str,
    access_key_cols: List[str],
    *,
    numeric_keys: bool = False,
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

    numeric_keys (CROSS-TYPE GUARD, brief item 2): when True, every key cell is
    normalised through a canonical NUMERIC form (Decimal(str(v)).normalize())
    SYMMETRICALLY on both sides BEFORE canonicalisation, so an Access float
    (TripAmp 1200.0) and a tcc numeric (rating Decimal('1200')) compare equal
    instead of fabricating a spurious full delta.  The normalisation is applied
    identically to both the access and the tcc side.  Used for the amps
    rating-value anti-join (a frame-free value key -- see the deferral note in
    the Task-11 report; row-level frame resolution is blocked by the tcc
    surrogate re-sequencing + computed `size`).
    """
    pm = ProjectionMap.for_table(access_table)
    tcc_table = pm.tcc_table

    # Fail closed if this run_id / snapshot_id no longer owns the SPECIFIC
    # materialised access_raw / tcc_snapshot tables this anti-join reads
    # (per-table guard, fixes 5+6 + Codex review-b53189fc).
    assert_materialized_owner(
        pg_conn, _ACCESS_RAW_LAYER, [access_table], run_id=run_id
    )
    assert_materialized_owner(
        pg_conn, _TCC_SNAPSHOT_LAYER, [tcc_table], snapshot_id=snapshot_id
    )

    # -- COUNT-ONLY branch for computed / derived tcc tables. ----------------
    if pm.tcc_build_kind in ("computed", "derived"):
        # Curves is NOT data-loaded into access_raw (count-only path), so prefer
        # the access_raw table when present and fall back to the inventory count.
        access_count = _access_count_or_meta(pg_conn, run_id, access_table)
        if access_count is None:
            access_count = 0
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
        numeric_keys=numeric_keys,
    )

    if result["method"] == "setdiff":
        missing_tuples = result["missing_in_right"]
        # Cap the enumeration; the FULL count is missing_count.
        capped = [list(t) for t in missing_tuples[:ENUMERATION_CAP]]
        enumerated = Jsonb(capped)
    else:  # multiset -> per-key delta mapping (positive-delta / access-missing only)
        # Cap to ENUMERATION_CAP distinct keys; the scalar missing_in_tcc_count
        # carries the FULL row-count (sum of positive deltas), not truncated.
        missing_entries = result["missing_in_right"]
        if len(missing_entries) > ENUMERATION_CAP:
            capped_keys = list(missing_entries.keys())[:ENUMERATION_CAP]
            missing_entries = {k: missing_entries[k] for k in capped_keys}
        enumerated = Jsonb(missing_entries)

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


def _normalize_numeric_tuple(row: tuple) -> tuple:
    """Symmetrically normalise every cell of a key tuple to a canonical numeric.

    A NULL stays None.  A numeric-looking value (int / float / Decimal / numeric
    string) is normalised through Decimal(str(v)).normalize() and re-emitted as a
    fixed-point string, so an Access float 1200.0 and a tcc numeric Decimal('1200')
    collapse to the IDENTICAL token '1200'.  A non-numeric value is left untouched
    (str-compared as before).  Applied to BOTH sides identically (brief item 2).
    """
    import decimal as _dec

    out = []
    for v in row:
        if v is None:
            out.append(None)
            continue
        try:
            d = _dec.Decimal(str(v)).normalize()
            out.append(format(d, "f"))
        except (_dec.InvalidOperation, ValueError):
            out.append(v)
    return tuple(out)


def _antijoin_keyset_mapped(
    pg_conn,
    access_table: str,
    access_key_cols: List[str],
    tcc_table: str,
    tcc_key_cols: List[str],
    numeric_keys: bool = False,
) -> Dict[str, object]:
    """antijoin_keyset variant that reads each side with ITS OWN key columns.

    The access side keys on access_key_cols; the tcc snapshot side keys on the
    mapped tcc_key_cols (which may differ in name, e.g. TripAmp -> rating).
    The compare is positional -- column i on the left aligns to column i on the
    right -- so the tuples are directly comparable.

    numeric_keys: when True, both sides' key tuples are run through
    _normalize_numeric_tuple SYMMETRICALLY before any compare, so a float-vs-
    numeric storage difference cannot fabricate a spurious delta (brief item 2).
    """
    left_rows = _read_key_tuples(pg_conn, "access_raw", access_table, access_key_cols)
    right_rows = _read_key_tuples(pg_conn, "tcc_snapshot", tcc_table, tcc_key_cols)

    if numeric_keys:
        left_rows = [_normalize_numeric_tuple(r) for r in left_rows]
        right_rows = [_normalize_numeric_tuple(r) for r in right_rows]

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

    # Separate directions: missing = positive-delta only; extra = negative only.
    missing_in_right = {k: v for k, v in diff.items() if v["delta"] > 0}
    extra_in_right = {k: v for k, v in diff.items() if v["delta"] < 0}

    return {
        "method": "multiset",
        "missing_in_right": missing_in_right,
        "extra_in_right": extra_in_right,
        "missing_count": missing_count,
        "extra_count": extra_count,
        # Full count of distinct keys that have ANY discrepancy (both directions).
        "distinct_discrepant_count": len(diff),
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


# ---------------------------------------------------------------------------
# reconcile_vs_tcc -- access_raw vs tcc_snapshot count delta (the F-79-03 shortfall)
# ---------------------------------------------------------------------------

# The breaker/TMT slice's 5 access-frame/child tables and their tcc counterparts.
# Sourced from the real ProjectionMap so the names stay in one place.
_TMT_RECON_TABLES = [
    "Breaker_TMTFrameSizes",
    "Breaker_TMTFrameAmps",
    "Breaker_TMTFrameSettings",
    "Breaker_TMTFrameCurves",
    "Breaker_TMTThermalTripAdj",
]


def reconcile_vs_tcc(pg_conn, run_id: str, snapshot_id: str) -> None:
    """Write access_validation.tcc_count_reconciliation for the 5 TMT tables.

    For each Access frame/child table in the breaker/TMT slice, record the
    access_raw row count against the recorded tcc_snapshot count and the delta
    (access - tcc).  This is the access-vs-governed-tcc count reconciliation --
    it reproduces the F-79-03 shortfalls -- and is DISTINCT from
    reconcile_counts (which compares access vs the harness's own staging load).

    Purely structural: counts and a signed delta only.  Never opines on whether
    a delta is a "gap" or "expected".  delta is NULL-safe (NULL if either side
    is absent -- absence recorded honestly, never fabricated as zero).
    """
    # Fail closed if a later load / snapshot superseded any SPECIFIC materialised
    # table this run_id / snapshot_id reads (per-table guard, fixes 5+6 + Codex
    # review-b53189fc).  Count-only tables are not materialised, so they carry no
    # per-table marker and the guard is a no-op for them.
    _tcc_recon_tcc_tables = [
        ProjectionMap.for_table(t).tcc_table for t in _TMT_RECON_TABLES
    ]
    assert_materialized_owner(
        pg_conn, _ACCESS_RAW_LAYER, _TMT_RECON_TABLES, run_id=run_id
    )
    assert_materialized_owner(
        pg_conn, _TCC_SNAPSHOT_LAYER, _tcc_recon_tcc_tables,
        snapshot_id=snapshot_id,
    )

    for access_table in _TMT_RECON_TABLES:
        pm = ProjectionMap.for_table(access_table)
        tcc_table = pm.tcc_table
        access_ct = _access_count_or_meta(pg_conn, run_id, access_table)
        tcc_ct = _tcc_snapshot_count(pg_conn, snapshot_id, tcc_table)
        if access_ct is None or tcc_ct is None:
            delta = None
        else:
            delta = int(access_ct) - int(tcc_ct)
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO access_validation.tcc_count_reconciliation
                    (run_id, access_table, tcc_table, snapshot_id,
                     access_row_count, tcc_row_count, delta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id, access_table) DO UPDATE SET
                    tcc_table = EXCLUDED.tcc_table,
                    snapshot_id = EXCLUDED.snapshot_id,
                    access_row_count = EXCLUDED.access_row_count,
                    tcc_row_count = EXCLUDED.tcc_row_count,
                    delta = EXCLUDED.delta
                """,
                (run_id, access_table, tcc_table, snapshot_id,
                 access_ct, tcc_ct, delta),
            )


# ---------------------------------------------------------------------------
# resolve_style_classes -- the STYLE-MEDIATED frame resolution (count-only, honest)
# ---------------------------------------------------------------------------

# Access style tables in the slice, in class order.
_ACCESS_STYLE_TABLES = {
    "MCCB": "BreakerMCCBStyles",
    "ICCB": "BreakerICCBStyles",
    "PCB": "BreakerPCBStyles",
}


def _distinct_int_ids(pg_conn, schema: str, table: str, col: str) -> set:
    """Return the DISTINCT non-null values of schema.table.col as a set of ints.

    Cast to text then int is avoided; the column is an Access integer surrogate
    loaded as integer, so a plain DISTINCT is exact.  NULLs are dropped (a NULL
    style id resolves to no class -- counted as unresolved, not fabricated).
    """
    stmt = sql.SQL(
        "SELECT DISTINCT {col} FROM {schema}.{table} WHERE {col} IS NOT NULL"
    ).format(
        col=sql.Identifier(col),
        schema=sql.Identifier(schema),
        table=sql.Identifier(table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        return {int(r[0]) for r in cur.fetchall()}


def resolve_style_classes(
    pg_conn,
    run_id: str,
    frame_table: str = "Breaker_TMTFrameSizes",
    styleid_col: str = "StyleID",
) -> Dict[str, int]:
    """Record the style-mediated frame-resolution AMBIGUITY as structural counts.

    The Access frame's breaker class is IMPLICIT: only frame_table.styleid_col is
    recorded, and a StyleID can appear across more than one Access style-table ID
    space (the per-class (class,id) overlap).  For every DISTINCT StyleID we count
    in how many of the three Access style-table ID spaces it appears:

      * exactly ONE   -> resolved_single_class (clean; tallied per class).
      * TWO or more   -> ambiguous_multi_class -- the class CANNOT be picked
                         without fabricating it.  We RECORD the count; we never
                         choose a class.
      * ZERO          -> unresolved_no_class (no matching style row).

    These counts ARE the F-79-03 evidence for the operator.  Writes one
    access_validation.style_resolution row.  Returns the count dict.

    HR1: counts only.  No verdict, no "gap", no chosen class.
    """
    # Fail closed if a later load superseded any SPECIFIC materialised access_raw
    # table this run_id reads -- the frame table plus the three style tables
    # (per-table guard, fixes 5+6 + Codex review-b53189fc).
    assert_materialized_owner(
        pg_conn,
        _ACCESS_RAW_LAYER,
        [frame_table, *_ACCESS_STYLE_TABLES.values()],
        run_id=run_id,
    )

    style_ids = _distinct_int_ids(pg_conn, "access_raw", frame_table, styleid_col)

    class_id_sets = {
        cls: _distinct_int_ids(pg_conn, "access_raw", tbl, "ID")
        for cls, tbl in _ACCESS_STYLE_TABLES.items()
    }

    single = 0
    ambiguous = 0
    none = 0
    mccb_only = 0
    iccb_only = 0
    pcb_only = 0
    for sid in style_ids:
        memberships = [cls for cls, ids in class_id_sets.items() if sid in ids]
        if len(memberships) == 0:
            none += 1
        elif len(memberships) == 1:
            single += 1
            cls = memberships[0]
            if cls == "MCCB":
                mccb_only += 1
            elif cls == "ICCB":
                iccb_only += 1
            elif cls == "PCB":
                pcb_only += 1
        else:
            ambiguous += 1

    counts = {
        "distinct_styleid_count": len(style_ids),
        "resolved_single_class_count": single,
        "ambiguous_multi_class_count": ambiguous,
        "unresolved_no_class_count": none,
        "mccb_only_count": mccb_only,
        "iccb_only_count": iccb_only,
        "pcb_only_count": pcb_only,
    }

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_validation.style_resolution
                (run_id, access_frame_table, distinct_styleid_count,
                 resolved_single_class_count, ambiguous_multi_class_count,
                 unresolved_no_class_count, mccb_only_count, iccb_only_count,
                 pcb_only_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, access_frame_table) DO UPDATE SET
                distinct_styleid_count = EXCLUDED.distinct_styleid_count,
                resolved_single_class_count = EXCLUDED.resolved_single_class_count,
                ambiguous_multi_class_count = EXCLUDED.ambiguous_multi_class_count,
                unresolved_no_class_count = EXCLUDED.unresolved_no_class_count,
                mccb_only_count = EXCLUDED.mccb_only_count,
                iccb_only_count = EXCLUDED.iccb_only_count,
                pcb_only_count = EXCLUDED.pcb_only_count
            """,
            (run_id, frame_table, counts["distinct_styleid_count"],
             counts["resolved_single_class_count"],
             counts["ambiguous_multi_class_count"],
             counts["unresolved_no_class_count"],
             counts["mccb_only_count"], counts["iccb_only_count"],
             counts["pcb_only_count"]),
        )

    return counts


# ---------------------------------------------------------------------------
# style_provenance_antijoin -- the CLEANLY-KEYABLE child anti-join
# ---------------------------------------------------------------------------

def style_provenance_antijoin(
    pg_conn,
    run_id: str,
    breaker_class: str,
) -> Dict[str, object]:
    """Anti-join Access BreakerXXXStyles.ID against tcc brk_xxx_styles.source_id.

    This is the ONE cross-instance key that does NOT route through the
    re-sequenced tmt_frames.id surrogate, so it is the cleanly-keyable child
    anti-join the slice can honestly run.  The Access style table is in
    access_raw; the tcc source_id set is in tcc_snapshot (materialised by
    snapshot_tcc).

    Both sides are read as native integers and compared as a Python set-diff.
    (Storage on the tcc side is integer source_id and on the Access side is the
    integer ID, so no int-vs-numeric mismatch arises; the compare is symmetric.)

    Writes one access_validation.style_provenance_antijoin row and returns the
    result dict.  Purely structural set-diff cardinalities + enumerated missing.
    """
    bc = breaker_class.upper()
    access_table = _ACCESS_STYLE_TABLES[bc]
    tcc_table = f"brk_{bc.lower()}_styles"

    # Fail closed if a later load superseded the SPECIFIC materialised access_raw
    # style table this run_id reads (per-table guard, fixes 5+6 + Codex
    # review-b53189fc).  (The tcc_snapshot style table is owned by snapshot_id,
    # which this function is not given; it is guarded at the run's
    # antijoin_vs_tcc / reconcile_vs_tcc entry points which carry the
    # snapshot_id.  We still guard the tcc table here when a marker for it exists
    # and the run's own snapshot owner cannot be checked -- but absent the
    # snapshot_id we cannot assert a match, so we only guard the access side.)
    assert_materialized_owner(
        pg_conn, _ACCESS_RAW_LAYER, [access_table], run_id=run_id
    )

    access_ids = _distinct_int_ids(pg_conn, "access_raw", access_table, "ID")
    tcc_src = _distinct_int_ids(pg_conn, "tcc_snapshot", tcc_table, "source_id")

    missing = sorted(access_ids - tcc_src)   # in Access, absent from tcc
    extra = sorted(tcc_src - access_ids)     # in tcc, absent from Access

    enumerated = Jsonb([int(x) for x in missing[:ENUMERATION_CAP]])

    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_validation.style_provenance_antijoin
                (run_id, breaker_class, access_style_table, tcc_style_table,
                 access_id_count, tcc_source_id_count,
                 missing_in_tcc_count, extra_in_tcc_count, enumerated_missing)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, breaker_class) DO UPDATE SET
                access_style_table = EXCLUDED.access_style_table,
                tcc_style_table = EXCLUDED.tcc_style_table,
                access_id_count = EXCLUDED.access_id_count,
                tcc_source_id_count = EXCLUDED.tcc_source_id_count,
                missing_in_tcc_count = EXCLUDED.missing_in_tcc_count,
                extra_in_tcc_count = EXCLUDED.extra_in_tcc_count,
                enumerated_missing = EXCLUDED.enumerated_missing
            """,
            (run_id, bc, access_table, tcc_table,
             len(access_ids), len(tcc_src),
             len(missing), len(extra), enumerated),
        )

    return {
        "breaker_class": bc,
        "access_id_count": len(access_ids),
        "tcc_source_id_count": len(tcc_src),
        "missing_in_tcc_count": len(missing),
        "extra_in_tcc_count": len(extra),
    }


# ---------------------------------------------------------------------------
# reconcile_checksums -- per-table access-vs-staging checksum reconciliation
# ---------------------------------------------------------------------------

def _read_all_rows(pg_conn, schema: str, table: str, col_names: list) -> list:
    """SELECT col_names (in order) from schema.table; return list of tuples.

    Reading by the SAME column order used to build col_types guarantees the row
    tuples align positionally with col_types for canonical_row / table_checksum.
    """
    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in col_names)
    stmt = sql.SQL("SELECT {cols} FROM {schema}.{table}").format(
        cols=col_ids, schema=sql.Identifier(schema), table=sql.Identifier(table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        return [tuple(r) for r in cur.fetchall()]


def reconcile_checksums(
    pg_conn,
    run_id: str,
    loaded_tables,
    col_types_by_table: dict,
    access_rows_for,
) -> None:
    """Record a per-table checksum + the access-vs-staging reconciliation.

    For each table in loaded_tables, compute:
      * staging checksum = table_checksum(access_raw.<table> rows, col_types)
      * access  checksum = table_checksum(access_rows_for(table), col_types)
    using the SAME col_types (the Task-2 symmetric-canonicalization contract).
    Write access_meta.tables.checksum = staging checksum + load_state='checksummed',
    and upsert access_validation.checksum_reconciliation (access/staging/matches).

    Purely structural (a hash + a boolean). HR1: records WHAT differs (matches),
    never opines on whether a mismatch is acceptable. Does NOT raise on mismatch.
    """
    for table in loaded_tables:
        col_types = col_types_by_table[table]
        col_names = [ct.name for ct in col_types]
        staging_rows = _read_all_rows(pg_conn, "access_raw", table, col_names)
        staging_ck = table_checksum(staging_rows, col_types)
        access_ck = table_checksum(access_rows_for(table), col_types)
        matches = access_ck == staging_ck

        with pg_conn.cursor() as cur:
            cur.execute(
                """
                UPDATE access_meta.tables
                   SET checksum = %s, load_state = 'checksummed'
                 WHERE run_id = %s AND table_name = %s
                """,
                (staging_ck, run_id, table),
            )
            cur.execute(
                """
                INSERT INTO access_validation.checksum_reconciliation
                    (run_id, table_name, access_checksum, staging_checksum, matches)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (run_id, table_name) DO UPDATE SET
                    access_checksum = EXCLUDED.access_checksum,
                    staging_checksum = EXCLUDED.staging_checksum,
                    matches = EXCLUDED.matches
                """,
                (run_id, table, access_ck, staging_ck, matches),
            )


# ---------------------------------------------------------------------------
# ChecksumFidelityError + assert_style_parents_faithful (AC-3 fail-closed gate)
# ---------------------------------------------------------------------------

class ChecksumFidelityError(RuntimeError):
    """A governed/certified table's access_raw mirror did not round-trip
    (checksum_reconciliation.matches != True). A mirror that is not byte-faithful
    must not be certified for population -- fail closed."""


def assert_style_parents_faithful(pg_conn, run_id: str) -> None:
    """Fail closed (AC-3) if any present style parent did not round-trip.

    The 3 BreakerXXXStyles tables are the D4/D5 carriers feeding the 029/030
    population, so matches=False (or no recorded checksum) there means the mirror
    is not byte-faithful and must not be certified. The reconciliation evidence is
    already persisted by reconcile_checksums; this only READS it and raises
    ChecksumFidelityError naming the offender(s). Style tables not present this run
    are skipped (not every run loads them).
    """
    offenders = []
    for table in sorted(_ACCESS_STYLE_TABLES.values()):
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='access_raw' AND table_name=%s", (table,))
            if cur.fetchone() is None:
                continue
            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s", (run_id, table))
            row = cur.fetchone()
        if row is None:
            offenders.append(f"{table} (no checksum recorded)")
        elif row[0] is not True:
            offenders.append(f"{table} (matches={row[0]!r})")
    if offenders:
        raise ChecksumFidelityError(
            "style-parent access_raw mirror is NOT byte-faithful; refusing to "
            "certify for population. Offending: " + ", ".join(offenders)
        )
