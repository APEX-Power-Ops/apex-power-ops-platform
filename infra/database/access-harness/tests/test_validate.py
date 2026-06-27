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
from access_harness.typemap import ColumnType
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
    # enumerated_missing carries ONLY positive-delta (access-missing) keys -- I2 fix.
    # rating=100 (+1) and rating=200 (+1) appear; rating=300 (-1/tcc-excess) must NOT.
    assert isinstance(enumerated, dict)
    deltas = {k: v["delta"] for k, v in enumerated.items()}
    assert all(d > 0 for d in deltas.values()), (
        f"enumerated_missing must contain ONLY positive-delta keys, got: {deltas!r}"
    )
    assert set(deltas.values()) == {1, 1}, f"unexpected positive deltas: {deltas!r}"
    # The tcc-excess key (rating=300, delta=-1) must NOT appear in enumerated_missing.
    for v in enumerated.values():
        assert v["delta"] > 0, (
            f"tcc-excess (negative delta) must not appear in enumerated_missing: {v!r}"
        )


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


def test_reconcile_counts_includes_checksummed_tables(pg):
    """Regression (cross-task seam): reconcile_checksums upgrades a loaded table's
    load_state to 'checksummed' and runs BEFORE reconcile_counts in run_all, so
    reconcile_counts must count 'checksummed' tables too -- otherwise the
    access-vs-staging row_count_reconciliation evidence is silently EMPTY after a
    real checksummed run."""
    run_id = _seed_run(pg, "run-recon-checksummed")
    with pg.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, object_type, load_state,
                 access_row_count, staging_row_count, tcc_build_kind)
            VALUES (%s, 'TblCk', 'TABLE', 'checksummed', 12, 12, '1:1_load')
            """,
            (run_id,),
        )

    reconcile_counts(pg, run_id)

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_row_count, staging_row_count, delta "
            "FROM access_validation.row_count_reconciliation "
            "WHERE run_id=%s AND table_name=%s",
            (run_id, "TblCk"),
        )
        row = cur.fetchone()
    assert row == (12, 12, 0), (
        "reconcile_counts must include checksummed tables (else the row-count "
        "reconciliation evidence is empty after a real checksummed run)")


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


# ---------------------------------------------------------------------------
# test_multiset_enumerated_missing_is_capped  (I1 regression)
# ---------------------------------------------------------------------------

def test_multiset_enumerated_missing_is_capped(pg):
    """multiset enumerated_missing is capped at ENUMERATION_CAP distinct keys.

    Seeds a non-unique left key (access) with many distinct discrepant keys so
    that the positive-delta count exceeds a small sentinel.  Asserts:
      - enumerated_missing length <= ENUMERATION_CAP
      - missing_in_tcc_count reflects the FULL row-count sum (not truncated)
    """
    from access_harness.validate import ENUMERATION_CAP

    run_id = _seed_run(pg, "test-validate-run-cap")
    sid = _seed_snapshot(pg, run_id, "snap-multiset-cap")

    # Build a dataset with many MORE distinct missing keys than ENUMERATION_CAP.
    # Use a non-unique left by duplicating key 1 so the multiset path is taken.
    # Then add ENUMERATION_CAP + 50 distinct keys present in access but not tcc.
    EXTRA = ENUMERATION_CAP + 50
    access_rows = [(1,), (1,)]  # duplicate -> forces multiset path
    for i in range(2, EXTRA + 2):
        access_rows.append((i,))

    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)')
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            access_rows,
        )
        # tcc_snapshot: only rating=1 once (so rating=1 has +1, all others missing).
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(1,)],
        )

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameAmps", ["rating"])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "enumerated_missing "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        row = cur.fetchone()

    assert row is not None
    method, missing_ct, extra_ct, enumerated = row
    assert method == "multiset"

    # Full scalar: rating=1 (+1 access-excess) + EXTRA distinct keys missing (+1 each)
    # = EXTRA + 1 total row-count excess.
    expected_missing_ct = EXTRA + 1
    assert missing_ct == expected_missing_ct, (
        f"scalar missing_in_tcc_count must be {expected_missing_ct}, got {missing_ct}"
    )
    assert extra_ct == 0

    # Enumeration must be capped.
    assert isinstance(enumerated, dict)
    assert len(enumerated) <= ENUMERATION_CAP, (
        f"enumerated_missing must be capped at {ENUMERATION_CAP}, "
        f"got {len(enumerated)} keys"
    )
    # All enumerated entries must be positive-delta.
    for k, v in enumerated.items():
        assert v["delta"] > 0, (
            f"enumerated_missing must contain only positive-delta keys, "
            f"found delta={v['delta']} for key {k!r}"
        )


# ---------------------------------------------------------------------------
# test_multiset_enumerated_missing_excludes_tcc_excess  (I2 regression)
# ---------------------------------------------------------------------------

def test_multiset_enumerated_missing_excludes_tcc_excess(pg):
    """multiset enumerated_missing must NOT carry tcc-excess (negative-delta) keys.

    Scenario: access has key X once, tcc has key X twice AND key Y once.
      - key X: delta = +1 - +2 = -1 (tcc-excess / extra_in_tcc)  -- must NOT appear
      - key Y: delta = 0 - 1 = -1 (tcc-excess / extra_in_tcc)    -- must NOT appear
      - key Z: access has it twice, tcc zero -> delta = +2         -- MUST appear
    Scalar extra_in_tcc_count must be 3 (1 + 1 + 1 from X/Y/... contributions).
    """
    run_id = _seed_run(pg, "test-validate-run-dir")
    sid = _seed_snapshot(pg, run_id, "snap-multiset-dir")

    with pg.cursor() as cur:
        # access: key=1 x2 (makes left non-unique -> multiset), key=3 x2.
        cur.execute('CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)')
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(1,), (1,), (3,), (3,)],
        )
        # tcc: rating=1 x3, rating=2 x1 (tcc-excess on both).
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(1,), (1,), (1,), (2,)],
        )

    antijoin_vs_tcc(pg, run_id, sid, "Breaker_TMTFrameAmps", ["rating"])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT method, missing_in_tcc_count, extra_in_tcc_count, "
            "enumerated_missing "
            "FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        row = cur.fetchone()

    assert row is not None
    method, missing_ct, extra_ct, enumerated = row
    assert method == "multiset"

    # rating=1: access=2, tcc=3 -> delta=-1 (tcc-excess)
    # rating=2: access=0, tcc=1 -> delta=-1 (tcc-excess)
    # rating=3: access=2, tcc=0 -> delta=+2 (access-missing)
    assert missing_ct == 2, f"expected missing_in_tcc_count=2 (rating=3 x2), got {missing_ct}"
    assert extra_ct == 2, f"expected extra_in_tcc_count=2 (1+1 from rating=1,2), got {extra_ct}"

    # enumerated_missing must contain ONLY positive-delta keys.
    assert isinstance(enumerated, dict)
    for k, v in enumerated.items():
        assert v["delta"] > 0, (
            f"tcc-excess key (negative delta) found in enumerated_missing: "
            f"key={k!r}, delta={v['delta']}"
        )
    # Specifically, rating=3 (positive delta=+2) should be present.
    # rating=1 and rating=2 (negative deltas) must NOT be present.
    enumerated_deltas = {k: v["delta"] for k, v in enumerated.items()}
    assert all(d > 0 for d in enumerated_deltas.values()), (
        f"enumerated_missing must be all positive-delta, got: {enumerated_deltas!r}"
    )
    assert len(enumerated) >= 1, "rating=3 (positive delta) must appear in enumerated_missing"


# ---------------------------------------------------------------------------
# Fixes 5+6: fail-closed on superseded materialised access_raw / tcc_snapshot.
#
# The access_raw.* and tcc_snapshot.* materialised tables are LATEST-ONLY:
# load.py drops+recreates access_raw.<table> and snapshot_tcc.py replaces
# tcc_snapshot.<table>, while validate is keyed by run_id / snapshot_id.
# Ownership is recorded PER (layer, table): each load_table stamps ONLY the
# table it just replaced, and snapshot_tcc stamps ONLY the tables it actually
# materialised.  Validating an OLD run_id/snapshot_id whose owned tables were
# PARTIALLY replaced by a later partial load/snapshot would otherwise read a
# table left from a DIFFERENT run (mixed evidence for the wrong source).  The
# per-(layer, table) access_meta.materialized_owner marker +
# assert_materialized_owner make validate FAIL CLOSED for EACH table it reads
# whose owner differs from the requested id.
# ---------------------------------------------------------------------------

def _stamp_owner(pg_conn, layer, table_name, *, run_id=None, snapshot_id=None):
    """Stamp the per-table materialised owner (simulates load/snapshot stamping)."""
    from access_harness.validate import stamp_materialized_owner
    stamp_materialized_owner(
        pg_conn, layer, table_name, run_id=run_id, snapshot_id=snapshot_id
    )


def test_validate_superseded_run_id_raises(pg):
    """A run_id that no longer owns the materialised access_raw table it would
    read must RAISE rather than silently anti-join against the newer load's
    data."""
    from access_harness.validate import SupersededMaterializationError

    old_run = _seed_run(pg, "run-old-001")
    new_run = _seed_run(pg, "run-new-001")
    sid = _seed_snapshot(pg, new_run, "snap-superseded-run")

    # Build the access_raw + tcc_snapshot tables the antijoin reads.
    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(100,), (200,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(100,)],
        )

    # The CURRENT owners: access_raw."Breaker_TMTFrameAmps" -> new_run,
    # tcc_snapshot.tmt_amps -> sid.
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameAmps", run_id=new_run)
    _stamp_owner(pg, "tcc_snapshot", "tmt_amps", snapshot_id=sid)

    # Validating the OLD run_id must fail closed (it no longer owns the table).
    with pytest.raises(SupersededMaterializationError):
        antijoin_vs_tcc(pg, old_run, sid, "Breaker_TMTFrameAmps", ["rating"])

    # Validating the CURRENT run_id works.
    antijoin_vs_tcc(pg, new_run, sid, "Breaker_TMTFrameAmps", ["rating"])
    with pg.cursor() as cur:
        cur.execute(
            "SELECT missing_in_tcc_count FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (new_run, "Breaker_TMTFrameAmps"),
        )
        row = cur.fetchone()
    assert row is not None and row[0] == 1, "current run_id must validate cleanly"


def test_validate_superseded_snapshot_id_raises(pg):
    """A snapshot_id that no longer owns the materialised tcc_snapshot table it
    would read must RAISE rather than read the newer snapshot's materialised
    tables."""
    from access_harness.validate import SupersededMaterializationError

    run_id = _seed_run(pg, "run-snap-guard-001")
    old_sid = _seed_snapshot(pg, run_id, "snap-old-001")
    new_sid = _seed_snapshot(pg, run_id, "snap-new-001")

    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(100,), (200,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(100,)],
        )

    # access_raw owned by run_id; tcc_snapshot.tmt_amps owned by the NEW snapshot.
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameAmps", run_id=run_id)
    _stamp_owner(pg, "tcc_snapshot", "tmt_amps", snapshot_id=new_sid)

    # Validating with the OLD snapshot_id must fail closed.
    with pytest.raises(SupersededMaterializationError):
        antijoin_vs_tcc(pg, run_id, old_sid, "Breaker_TMTFrameAmps", ["rating"])

    # The CURRENT snapshot works.
    antijoin_vs_tcc(pg, run_id, new_sid, "Breaker_TMTFrameAmps", ["rating"])
    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        (n,) = cur.fetchone()
    assert n == 1, "current snapshot_id must validate cleanly"


# ---------------------------------------------------------------------------
# PER-TABLE ownership (Codex review-b53189fc): a PARTIAL/subset materialisation
# must NOT stamp whole-layer ownership.  Run A materialises {X, Y}; run B then
# materialises ONLY {X}, leaving Y from A.  Validating B against Y (owned by A)
# must FAIL CLOSED; validating B against X (which B owns) must work.
# ---------------------------------------------------------------------------

def test_validate_partial_access_raw_run_reads_stale_table_raises(pg):
    """Run B replaced only access_raw.X; access_raw.Y is still owned by run A.
    Validating run B against Y (the stale table) must RAISE; against X works."""
    from access_harness.validate import SupersededMaterializationError

    run_a = _seed_run(pg, "run-partial-A")
    run_b = _seed_run(pg, "run-partial-B")
    sid = _seed_snapshot(pg, run_b, "snap-partial-ab")

    # X = Breaker_TMTFrameAmps (-> tcc tmt_amps); Y = Breaker_TMTFrameSettings
    # (-> tcc tmt_settings).  Both are 1:1_load tables in the real ProjectionMap.
    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(100,), (200,)],
        )
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameSettings" (id integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameSettings" (id) VALUES (%s)',
            [(1,), (2,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(100,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_settings (id integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_settings (id) VALUES (%s)",
            [(1,)],
        )

    # Run A materialised BOTH access_raw tables; run B then replaced ONLY
    # Breaker_TMTFrameAmps -> Breaker_TMTFrameSettings is LEFT owned by run A.
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameAmps", run_id=run_a)
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameSettings", run_id=run_a)
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameAmps", run_id=run_b)
    _stamp_owner(pg, "tcc_snapshot", "tmt_amps", snapshot_id=sid)
    _stamp_owner(pg, "tcc_snapshot", "tmt_settings", snapshot_id=sid)

    # Validating run B against the STALE table (owned by A) must fail closed.
    with pytest.raises(SupersededMaterializationError) as exc:
        antijoin_vs_tcc(pg, run_b, sid, "Breaker_TMTFrameSettings", ["id"])
    msg = str(exc.value)
    assert "Breaker_TMTFrameSettings" in msg, "error must name the stale table"
    assert run_a in msg and run_b in msg, "error must name owning vs requested id"

    # Validating run B against the table it DOES own works.
    antijoin_vs_tcc(pg, run_b, sid, "Breaker_TMTFrameAmps", ["rating"])
    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_b, "Breaker_TMTFrameAmps"),
        )
        (n,) = cur.fetchone()
    assert n == 1, "run B must validate cleanly against the table it owns"


def test_validate_partial_tcc_snapshot_subset_reads_stale_table_raises(pg):
    """Snapshot S1 materialised {tmt_frames, tmt_amps}; S2 materialised only
    {tmt_frames}, leaving tmt_amps from S1.  Validating S2 against tmt_amps (the
    stale snapshot table) must RAISE; validating S2 against tmt_frames works."""
    from access_harness.validate import SupersededMaterializationError

    run_id = _seed_run(pg, "run-snap-subset")
    s1 = _seed_snapshot(pg, run_id, "snap-S1")
    s2 = _seed_snapshot(pg, run_id, "snap-S2")

    # access_raw side: the two access tables behind tmt_amps + the frame sizes
    # table (-> tcc tmt_frames is computed in the real map, but for this guard
    # test we use the 1:1_load amps table against tmt_amps and a plain count on
    # the frames table -- the guard is about the tcc_snapshot owner, so we drive
    # it through antijoin_vs_tcc on Breaker_TMTFrameAmps which reads
    # tcc_snapshot.tmt_amps).
    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Breaker_TMTFrameAmps" (rating integer)'
        )
        cur.executemany(
            'INSERT INTO access_raw."Breaker_TMTFrameAmps" (rating) VALUES (%s)',
            [(100,), (200,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_frames (id integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_frames (id) VALUES (%s)",
            [(1,)],
        )
        cur.execute("CREATE TABLE tcc_snapshot.tmt_amps (rating integer)")
        cur.executemany(
            "INSERT INTO tcc_snapshot.tmt_amps (rating) VALUES (%s)",
            [(100,)],
        )

    # access_raw owned by run_id (single run).
    _stamp_owner(pg, "access_raw", "Breaker_TMTFrameAmps", run_id=run_id)
    # S1 materialised BOTH tcc tables; S2 then replaced ONLY tmt_frames ->
    # tcc_snapshot.tmt_amps is LEFT owned by S1.
    _stamp_owner(pg, "tcc_snapshot", "tmt_frames", snapshot_id=s1)
    _stamp_owner(pg, "tcc_snapshot", "tmt_amps", snapshot_id=s1)
    _stamp_owner(pg, "tcc_snapshot", "tmt_frames", snapshot_id=s2)

    # Validating S2's anti-join against tmt_amps (owned by S1) must fail closed.
    with pytest.raises(SupersededMaterializationError) as exc:
        antijoin_vs_tcc(pg, run_id, s2, "Breaker_TMTFrameAmps", ["rating"])
    msg = str(exc.value)
    assert "tmt_amps" in msg, "error must name the stale snapshot table"
    assert s1 in msg and s2 in msg, "error must name owning vs requested snapshot id"

    # S1 (which owns tmt_amps) validates cleanly.
    antijoin_vs_tcc(pg, run_id, s1, "Breaker_TMTFrameAmps", ["rating"])
    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM access_validation.antijoin_vs_tcc "
            "WHERE run_id=%s AND access_table=%s",
            (run_id, "Breaker_TMTFrameAmps"),
        )
        (n,) = cur.fetchone()
    assert n == 1, "snapshot S1 must validate cleanly against tmt_amps"


# ---------------------------------------------------------------------------
# P2: reconcile_checksums must guard against superseded access_raw ownership.
# ---------------------------------------------------------------------------

def test_reconcile_checksums_superseded_run_id_raises(pg):
    """reconcile_checksums must call assert_materialized_owner BEFORE reading
    access_raw.<table>, so a superseded run_id raises SupersededMaterializationError
    instead of silently checksumming data owned by a different run.

    Setup: build access_raw.T_chksuper with data, stamp its owner as new_run,
    then call reconcile_checksums with old_run -> must raise.
    When stamped with old_run -> must pass (existing behaviour unchanged).
    """
    from access_harness.validate import (
        SupersededMaterializationError,
        reconcile_checksums,
        stamp_materialized_owner,
    )

    old_run = _seed_run(pg, "run-chk-old")
    new_run = _seed_run(pg, "run-chk-new")

    # Build a minimal access_raw table and seed the meta row for both runs.
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."T_chksuper" (a integer)')
        cur.executemany(
            'INSERT INTO access_raw."T_chksuper" (a) VALUES (%s)',
            [(1,), (2,)],
        )
    _seed_loaded_table(pg, old_run, "T_chksuper", 2)
    _seed_loaded_table(pg, new_run, "T_chksuper", 2)

    col_types = {"T_chksuper": [_ct("a")]}
    access_rows = {"T_chksuper": [(1,), (2,)]}

    # Stamp the table as owned by new_run -> old_run is superseded.
    stamp_materialized_owner(pg, "access_raw", "T_chksuper", run_id=new_run)

    # Calling reconcile_checksums with old_run must fail closed.
    with pytest.raises(SupersededMaterializationError):
        reconcile_checksums(pg, old_run, ["T_chksuper"], col_types,
                            access_rows_for=lambda t: access_rows[t])

    # Calling reconcile_checksums with new_run (the real owner) must pass.
    reconcile_checksums(pg, new_run, ["T_chksuper"], col_types,
                        access_rows_for=lambda t: access_rows[t])
    with pg.cursor() as cur:
        cur.execute(
            "SELECT matches FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (new_run, "T_chksuper"))
        row = cur.fetchone()
    assert row is not None and row[0] is True, (
        "reconcile_checksums with the current owner must succeed and record matches=True"
    )


# ---------------------------------------------------------------------------
# Task 2: reconcile_checksums + assert_style_parents_faithful
# ---------------------------------------------------------------------------

def _ct(name, pg_type="integer"):
    """A minimal ColumnType for checksum canonicalization in tests."""
    return ColumnType(
        access_type="", pg_type=pg_type, nullable=True, size=None,
        precision=None, round_trippable=True, name=name,
    )


def _seed_loaded_table(pg_conn, run_id, table, staging_count):
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, object_type, load_state,
                 access_row_count, staging_row_count, tcc_build_kind)
            VALUES (%s, %s, 'TABLE', 'loaded', %s, %s, '1:1_load')
            ON CONFLICT (run_id, table_name) DO UPDATE SET load_state='loaded'
            """,
            (run_id, table, staging_count, staging_count),
        )


def test_reconcile_checksums_match(pg):
    """Identical access + staging rows -> matches=True, checksum recorded,
    load_state='checksummed', access_checksum == staging_checksum."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-match")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."T1" (a integer, b integer)')
        cur.executemany(
            'INSERT INTO access_raw."T1" (a, b) VALUES (%s, %s)',
            [(1, 10), (2, 20), (3, 30)],
        )
    _seed_loaded_table(pg, run_id, "T1", 3)

    col_types = {"T1": [_ct("a"), _ct("b")]}
    access_rows = {"T1": [(1, 10), (2, 20), (3, 30)]}  # identical -> match

    reconcile_checksums(pg, run_id, ["T1"], col_types,
                        access_rows_for=lambda t: access_rows[t])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_checksum, staging_checksum, matches "
            "FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T1"))
        access_ck, staging_ck, matches = cur.fetchone()
        cur.execute(
            "SELECT checksum, load_state FROM access_meta.tables "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T1"))
        meta_ck, state = cur.fetchone()

    assert matches is True
    assert access_ck == staging_ck
    assert meta_ck == staging_ck and meta_ck is not None
    assert state == "checksummed"


def test_reconcile_checksums_mismatch_records_not_raises(pg):
    """Differing access vs staging -> matches=False, both checksums recorded and
    distinct, no exception (HR1: records the discrepancy, never opines)."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-mismatch")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."T2" (a integer)')
        cur.executemany('INSERT INTO access_raw."T2" (a) VALUES (%s)',
                        [(1,), (2,), (3,)])
    _seed_loaded_table(pg, run_id, "T2", 3)

    col_types = {"T2": [_ct("a")]}
    access_rows = {"T2": [(1,), (2,), (999,)]}  # one differing row

    reconcile_checksums(pg, run_id, ["T2"], col_types,
                        access_rows_for=lambda t: access_rows[t])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_checksum, staging_checksum, matches "
            "FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T2"))
        access_ck, staging_ck, matches = cur.fetchone()
    assert matches is False
    assert access_ck != staging_ck
    assert access_ck and staging_ck


def test_reconcile_checksums_only_processes_listed_tables(pg):
    """Tables NOT in loaded_tables get no checksum row (count-only/unloaded are
    excluded by the caller)."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-skip")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."Kept" (a integer)')
        cur.execute('INSERT INTO access_raw."Kept" (a) VALUES (1)')
    _seed_loaded_table(pg, run_id, "Kept", 1)

    reconcile_checksums(pg, run_id, ["Kept"], {"Kept": [_ct("a")]},
                        access_rows_for=lambda t: [(1,)])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s", (run_id,))
        (n,) = cur.fetchone()
    assert n == 1, "only the one listed table should be checksummed"


def test_reconcile_checksums_type_roundtrip(pg):
    """AC-3: diverse column types round-trip through a REAL access_raw readback so
    the access-side and staging-side canonicalize identically (matches=True)."""
    from datetime import date, datetime
    from decimal import Decimal
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-types")
    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Typed" ('
            '"i" integer, "f" double precision, "n" numeric, "d" date, '
            '"ts" timestamp, "b" boolean, "by" bytea, "t" text)'
        )
        rows = [
            (1, 1.5, Decimal("2.50"), date(2026, 6, 27),
             datetime(2026, 6, 27, 12, 0, 0), True, b"\x01\x02\xff", "memo text"),
            (None, None, None, None, None, None, None, None),
        ]
        cur.executemany(
            'INSERT INTO access_raw."Typed" '
            '("i","f","n","d","ts","b","by","t") VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            rows,
        )
    _seed_loaded_table(pg, run_id, "Typed", len(rows))
    col_types = {"Typed": [
        _ct("i", "integer"), _ct("f", "double precision"), _ct("n", "numeric"),
        _ct("d", "date"), _ct("ts", "timestamp"), _ct("b", "boolean"),
        _ct("by", "bytea"), _ct("t", "text"),
    ]}
    # access-side rows == the SAME logical values; a faithful round-trip -> match.
    reconcile_checksums(pg, run_id, ["Typed"], col_types,
                        access_rows_for=lambda t: list(rows))

    with pg.cursor() as cur:
        cur.execute(
            "SELECT matches FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "Typed"))
        (matches,) = cur.fetchone()
    assert matches is True, (
        "diverse-typed access vs staging readback must canonicalize identically")


def test_assert_style_parents_faithful_gate(pg):
    """AC-3: the gate raises when a present style parent has matches=False (or no
    recorded checksum), and is a no-op when all present style parents match."""
    from access_harness.validate import (
        ChecksumFidelityError, assert_style_parents_faithful, reconcile_checksums,
    )

    run_id = _seed_run(pg, "run-style-gate")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."BreakerICCBStyles" ("ID" integer)')
        cur.executemany(
            'INSERT INTO access_raw."BreakerICCBStyles" ("ID") VALUES (%s)',
            [(1,), (2,)],
        )
    _seed_loaded_table(pg, run_id, "BreakerICCBStyles", 2)

    # Faithful -> gate passes.
    reconcile_checksums(pg, run_id, ["BreakerICCBStyles"],
                        {"BreakerICCBStyles": [_ct("ID")]},
                        access_rows_for=lambda t: [(1,), (2,)])
    assert_style_parents_faithful(pg, run_id)  # must not raise

    # Force a mismatch -> gate raises, naming the offending table.
    reconcile_checksums(pg, run_id, ["BreakerICCBStyles"],
                        {"BreakerICCBStyles": [_ct("ID")]},
                        access_rows_for=lambda t: [(1,), (999,)])
    with pytest.raises(ChecksumFidelityError, match="BreakerICCBStyles"):
        assert_style_parents_faithful(pg, run_id)


# ---------------------------------------------------------------------------
# Task 3: reconcile_style_key_quality
# ---------------------------------------------------------------------------

def test_style_key_quality_coverage(pg):
    """reconcile_style_key_quality writes a key_quality row (is_unique on ID) for
    each BreakerXXXStyles table present in access_raw."""
    from access_harness.validate import reconcile_style_key_quality

    run_id = _seed_run(pg, "run-style-kq")
    with pg.cursor() as cur:
        for tbl in ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles"):
            cur.execute(f'CREATE TABLE access_raw."{tbl}" ("ID" integer)')
            cur.executemany(
                f'INSERT INTO access_raw."{tbl}" ("ID") VALUES (%s)',
                [(1,), (2,), (3,)],
            )

    reconcile_style_key_quality(pg, run_id)

    with pg.cursor() as cur:
        cur.execute(
            "SELECT table_name, is_unique, distinct_count, total_count "
            "FROM access_validation.key_quality "
            "WHERE run_id=%s ORDER BY table_name", (run_id,))
        rows = cur.fetchall()
    names = [r[0] for r in rows]
    assert names == ["BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles"]
    for _name, is_unique, distinct_ct, total_ct in rows:
        assert is_unique is True
        assert distinct_ct == 3 and total_ct == 3
