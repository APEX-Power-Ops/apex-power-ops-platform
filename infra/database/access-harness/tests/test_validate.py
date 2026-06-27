"""Tests for access_harness.validate -- the CORE F-79-03 evidence engine.

These compare access_raw.* against tcc_snapshot.* and write DESCRIPTIVE
evidence to access_validation.* with ZERO behavioral interpretation (HR1).

All fixtures are PINNED synthetic tables built locally in tcc_fidelity_test so
the deltas are KNOWN and asserted EXACTLY (this is the regression layer; the
live numbers are a later task's job, not here).  The synthetic access_raw /
tcc_snapshot tables carry only the columns needed for the key/compare under
test -- they do NOT have to match the full real schema.  The REAL ProjectionMap
entries are used for amps/curves so col_map / tcc_build_kind come from the real
map.
"""
import pytest

from access_harness.projection import ForbiddenKeyError
from access_harness.validate import (
    antijoin_keyset,
    antijoin_vs_tcc,
    key_quality,
    reconcile_counts,
)


# ---------------------------------------------------------------------------
# Helpers: seed a minimal run + snapshot so FK references resolve.
# ---------------------------------------------------------------------------

def _seed_run(pg_conn, run_id: str = "test-validate-run") -> str:
    """Insert a minimal extraction_run row (idempotent)."""
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.extraction_run (
                run_id, source_path, frozen_copy_path, source_size,
                source_mtime_utc, source_sha256, extracted_at_utc,
                driver_name, dbms_version, read_only, harness_version
            ) VALUES (
                %s, '/tmp/test.accdb', '/tmp/frozen.accdb', 0,
                now(), 'deadbeef00000000', now(),
                'TEST', '0.0.0', TRUE, '0.1.0'
            )
            ON CONFLICT (run_id) DO NOTHING
            """,
            (run_id,),
        )
    return run_id


def _seed_snapshot(pg_conn, run_id: str, snapshot_id: str) -> str:
    """Insert a minimal tcc_snapshot provenance row (idempotent)."""
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tcc_snapshot
                (snapshot_id, run_id, host, db_name, captured_at, role)
            VALUES (%s, %s, 'testhost', 'testdb', now(), 'testrole')
            ON CONFLICT (snapshot_id) DO NOTHING
            """,
            (snapshot_id, run_id),
        )
    return snapshot_id


def _record_snapshot_count(pg_conn, snapshot_id: str, table_name: str, count: int) -> None:
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tcc_snapshot_table
                (snapshot_id, table_name, tcc_row_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (snapshot_id, table_name)
            DO UPDATE SET tcc_row_count = EXCLUDED.tcc_row_count
            """,
            (snapshot_id, table_name, count),
        )


# ---------------------------------------------------------------------------
# test_setdiff_enumerates_exact_missing_keys
# ---------------------------------------------------------------------------

def test_setdiff_enumerates_exact_missing_keys(pg):
    """Unique left key -> setdiff path; the (2,300) key is enumerated exactly."""
    run_id = _seed_run(pg)
    sid = _seed_snapshot(pg, run_id, "snap-setdiff")

    with pg.cursor() as cur:
        # access_raw side: 3 rows, one of which ((2,300)) is absent from tcc.
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" '
            "(frame_ref integer, rating integer)"
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (frame_ref, rating) '
            "VALUES (%s, %s)",
            [(1, 100), (1, 200), (2, 300)],
        )
        # tcc_snapshot side: tmt_amps has matching key cols (frame_ref, rating)
        # carrying 2 of the 3 access rows (missing (2,300)).
        cur.execute(
            "CREATE TABLE tcc_snapshot.tmt_amps (frame_ref integer, rating integer)"
        )
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (frame_ref, rating) VALUES (%s, %s)",
            [(1, 100), (1, 200)],
        )

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameAmps", ["frame_ref", "rating"])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "enumerated_missing, row_antijoin_not_applicable, tcc_table "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        row = cur.fetchone()

    assert row is not None, "no antijoin_vs_tcc row written"
    method, missing_ct, extra_ct, enumerated, not_applicable, tcc_table = row
    assert method == "setdiff"
    assert missing_ct == 1
    assert extra_ct == 0
    assert not_applicable is False
    assert tcc_table == "tmt_amps"
    # enumerated_missing is a jsonb array of the missing key tuples (as lists).
    assert enumerated == [[2, 300]], f"expected exactly [[2,300]], got {enumerated!r}"


# ---------------------------------------------------------------------------
# test_nonunique_key_uses_multiset
# ---------------------------------------------------------------------------

def test_nonunique_key_uses_multiset(pg):
    """A duplicated left key tuple forces the multiset path with exact deltas."""
    run_id = _seed_run(pg)
    sid = _seed_snapshot(pg, run_id, "snap-multiset")

    with pg.cursor() as cur:
        # access_raw: key 'rating' alone, with a DUPLICATE (100 appears twice).
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(100,), (100,), (200,)],
        )
        # tcc_snapshot: rating=100 once, rating=300 once.
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(100,), (300,)],
        )

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameAmps", ["rating"])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "enumerated_missing, row_antijoin_not_applicable "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        row = cur.fetchone()

    assert row is not None
    method, missing_ct, extra_ct, enumerated, not_applicable = row
    assert method == "multiset"
    assert not_applicable is False
    # access has rating=100 x2 (tcc x1 -> +1 deficit), rating=200 x1 (tcc x0 -> +1).
    # access excess total = 2.  tcc excess: rating=300 x1 (access x0) = 1.
    assert missing_ct == 2, f"expected 2 access-excess, got {missing_ct}"
    assert extra_ct == 1, f"expected 1 tcc-excess, got {extra_ct}"
    # The per-key deltas are carried in enumerated_missing for the multiset path.
    # Canonical string keys map to {access, tcc, delta} dicts.
    assert isinstance(enumerated, dict)
    deltas = {k: v["delta"] for k, v in enumerated.items()}
    assert set(deltas.values()) == {1, 1, -1}, f"unexpected deltas: {deltas!r}"


# ---------------------------------------------------------------------------
# test_computed_table_is_count_only
# ---------------------------------------------------------------------------

def test_computed_table_is_count_only(pg):
    """A 'computed' table (curves) is COUNT-ONLY: no EXCEPT, no enumeration."""
    run_id = _seed_run(pg)
    sid = _seed_snapshot(pg, run_id, "snap-curves")

    with pg.cursor() as cur:
        # access_raw curves: 5 rows (only the count matters here).
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameCurves" (x integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameCurves" (x) VALUES (%s)',
            [(i,) for i in range(5)],
        )
    # tcc count recorded in snapshot_table (no tcc_snapshot.tmt_curves table --
    # count-only, mirrors the 1.1M-row reality).
    _record_snapshot_count(pg, sid, "tmt_curves", 7)

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameCurves", ["x"])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "enumerated_missing, row_antijoin_not_applicable, tcc_table "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameCurves"),
        )
        row = cur.fetchone()

    assert row is not None
    method, missing_ct, extra_ct, enumerated, not_applicable, tcc_table = row
    assert method == "count_only"
    assert not_applicable is True
    assert enumerated is None, "count-only must NOT enumerate keys"
    assert tcc_table == "tmt_curves"
    # access=5, tcc=7 -> tcc has 2 MORE -> extra_in_tcc=2, missing_in_tcc=0.
    assert missing_ct == 0
    assert extra_ct == 2


# ---------------------------------------------------------------------------
# test_surrogate_key_antijoin_is_forbidden
# ---------------------------------------------------------------------------

def test_surrogate_key_antijoin_is_forbidden(pg):
    """A key that maps to tmt_frames.id raises ForbiddenKeyError (red-team guard).

    Breaker_TMTFrameSizes is a 1:1_load whose tcc_table is tmt_frames; keying on
    the raw surrogate 'ID' targets tmt_frames.id -> must raise, not be caught.
    """
    run_id = _seed_run(pg)
    sid = _seed_snapshot(pg, run_id, "snap-forbidden")

    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameSizes" (id integer)'
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_frames (id integer)")

    with pytest.raises(ForbiddenKeyError):
        antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameSizes", ["ID"])


# ---------------------------------------------------------------------------
# test_key_quality_detects_uniqueness
# ---------------------------------------------------------------------------

def test_key_quality_detects_uniqueness(pg):
    """key_quality reports is_unique + distinct/total counts correctly."""
    _seed_run(pg)

    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."UniqTbl" (a integer, b integer)')
        cur.executemany(
            'INSERT INTO access_raw."UniqTbl" (a, b) VALUES (%s, %s)',
            [(1, 1), (1, 2), (2, 1)],
        )
        cur.execute('CREATE TABLE access_raw."DupTbl" (a integer)')
        cur.executemany(
            'INSERT INTO access_raw."DupTbl" (a) VALUES (%s)',
            [(1,), (1,), (2,)],
        )

    uniq = key_quality(pg, "access_raw", "UniqTbl", ["a", "b"])
    assert uniq["is_unique"] is True
    assert uniq["distinct_count"] == 3
    assert uniq["total_count"] == 3

    dup = key_quality(pg, "access_raw", "DupTbl", ["a"])
    assert dup["is_unique"] is False
    assert dup["distinct_count"] == 2
    assert dup["total_count"] == 3


# ---------------------------------------------------------------------------
# test_antijoin_keyset_direct (lower-level helper, exact deltas both directions)
# ---------------------------------------------------------------------------

def test_antijoin_keyset_setdiff_both_directions(pg):
    """antijoin_keyset (unique left) reports missing and extra key tuples."""
    _seed_run(pg)
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."L" (a integer, b integer)')
        cur.executemany(
            'INSERT INTO access_raw."L" (a, b) VALUES (%s, %s)',
            [(1, 1), (2, 2)],
        )
        cur.execute('CREATE TABLE tcc_snapshot."R" (a integer, b integer)')
        cur.executemany(
            'INSERT INTO tcc_snapshot."R" (a, b) VALUES (%s, %s)',
            [(2, 2), (3, 3)],
        )
    res = antijoin_keyset(pg, "access_raw", "L", "tcc_snapshot", "R", ["a", "b"])
    assert res["method"] == "setdiff"
    assert res["missing_count"] == 1
    assert res["extra_count"] == 1
    assert list(res["missing_in_right"]) == [(1, 1)]
    assert list(res["extra_in_right"]) == [(3, 3)]


# ---------------------------------------------------------------------------
# test_reconcile_counts
# ---------------------------------------------------------------------------

def test_reconcile_counts_writes_row_count_reconciliation(pg):
    """reconcile_counts writes access vs staging counts + delta per loaded table."""
    run_id = _seed_run(pg)

    with pg.cursor() as cur:
        # A loaded table with access_row_count and staging_row_count recorded.
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, object_type, load_state,
                 access_row_count, staging_row_count, tcc_build_kind)
            VALUES (%s, 'TblA', 'TABLE', 'loaded', 10, 9, '1:1_load')
            """,
            (run_id,),
        )

    reconcile_counts(pg, run_id)

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_row_count, staging_row_count, delta "
            "FROM access_validation.row_count_reconciliation "
            "WHERE run_id=%s AND table_name=%s",
            (run_id, "TblA"),
        )
        row = cur.fetchone()
    assert row is not None
    assert row == (10, 9, 1)


# ---------------------------------------------------------------------------
# test_no_interpretive_columns_after_writes
# ---------------------------------------------------------------------------

def test_no_interpretive_columns_after_writes(pg):
    """After all validate writes, the HR1 guard finds NO interpretive columns."""
    from access_harness.hr1_guard import assert_no_interpretive_columns

    run_id = _seed_run(pg)
    sid = _seed_snapshot(pg, run_id, "snap-hr1")

    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" '
            "(frame_ref integer, rating integer)"
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (frame_ref, rating) '
            "VALUES (%s, %s)",
            [(1, 100), (2, 300)],
        )
        cur.execute(
            "CREATE TABLE tcc_snapshot.tmt_amps (frame_ref integer, rating integer)"
        )
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (frame_ref, rating) VALUES (%s, %s)",
            [(1, 100)],
        )
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, object_type, load_state,
                 access_row_count, staging_row_count, tcc_build_kind)
            VALUES (%s, 'TblA', 'TABLE', 'loaded', 2, 2, '1:1_load')
            """,
            (run_id,),
        )

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameAmps", ["frame_ref", "rating"])
    reconcile_counts(pg, run_id)
    key_quality(
        pg, "access_raw", "Breaker_TMTFrameAmps", ["frame_ref", "rating"],
        run_id=run_id, write=True,
    )

    assert assert_no_interpretive_columns(pg) == []
