"""Tests for access_harness.d4d5_governed_generation.

Task 1: manifest + six fail-closed gates.
Task 2: read_class (governed reader + verbatim transform), build_report,
        and governed-vs-direct parity regression (live).

Non-live tests run on tcc_fidelity_test (via the pg fixture from conftest.py).
The normal suite NEVER touches tcc_fidelity_governed.

Gate scenarios seeded inline using pg fixture:
  run_clean       -- all 3 gates pass (owner matches, recon True, key unique, all cols present)
  runA/runB       -- owner mismatch (table stamped to runB, we request runA)
  run_recon_false -- checksum_reconciliation.matches = False
  run_key_dupe    -- key_quality.is_unique = False
  run_missing_col -- access_raw style table is missing one required column
  Gate 2 (absent run_id): no extraction_run row at all with that id -> refuse

Live tests (marker: live) require tcc_fidelity_governed + frozen Access.
Run only when ACCESS_HARNESS_SUPERUSER_DSN is set and the governed DB is
reachable.  Excluded by: uv run pytest -m "not live".
"""
import os

import psycopg
import pytest
from access_harness import config
from access_harness import d4d5_governed_generation as gen


# ---------------------------------------------------------------------------
# Gate 1: assert_governed_source refuses non-governed DB
# ---------------------------------------------------------------------------

def test_assert_governed_source_refuses_non_governed(pg):
    """pg fixture connects to tcc_fidelity_test, which is NOT tcc_fidelity_governed."""
    # pg is already an open connection to tcc_fidelity_test -- use it directly.
    with pytest.raises(gen.GenerationRefused, match="tcc_fidelity_governed"):
        gen.assert_governed_source(pg)


# ---------------------------------------------------------------------------
# Seed helpers -- all seed into the schema created by the pg fixture.
# ---------------------------------------------------------------------------

def _seed_run(conn, run_id):
    with conn.cursor() as cur:
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


def _stamp_owner(conn, table_name, run_id):
    """Upsert access_meta.materialized_owner for layer=access_raw."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.materialized_owner
                (layer, table_name, run_id, snapshot_id, updated_at)
            VALUES ('access_raw', %s, %s, NULL, now())
            ON CONFLICT (layer, table_name) DO UPDATE
                SET run_id=EXCLUDED.run_id, updated_at=EXCLUDED.updated_at
            """,
            (table_name, run_id),
        )


def _seed_recon(conn, run_id, table_name, matches):
    """Upsert access_validation.checksum_reconciliation."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_validation.checksum_reconciliation
                (run_id, table_name, access_checksum, staging_checksum, matches)
            VALUES (%s, %s, 'aaa', 'aaa', %s)
            ON CONFLICT (run_id, table_name) DO UPDATE
                SET matches=EXCLUDED.matches
            """,
            (run_id, table_name, matches),
        )


def _seed_key_quality(conn, run_id, table_name, is_unique):
    """Upsert access_validation.key_quality."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_validation.key_quality
                (run_id, table_name, candidate_key, is_unique, distinct_count, total_count)
            VALUES (%s, %s, ARRAY['ID'], %s, 3, 3)
            ON CONFLICT (run_id, table_name) DO UPDATE
                SET is_unique=EXCLUDED.is_unique
            """,
            (run_id, table_name, is_unique),
        )


STYLE_TABLES = ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles")


def _create_style_table_full(conn, table_name, required_cols):
    """Create access_raw.<table_name> with ALL required_cols as TEXT columns."""
    col_defs = ", ".join(f'"{c}" text' for c in required_cols)
    with conn.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS access_raw."{table_name}" ({col_defs})'
        )


def _create_style_table_missing_one(conn, table_name, required_cols):
    """Create access_raw.<table_name> missing the LAST required column."""
    cols = required_cols[:-1]  # drop the last one
    col_defs = ", ".join(f'"{c}" text' for c in cols)
    with conn.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS access_raw."{table_name}" ({col_defs})'
        )


# ---------------------------------------------------------------------------
# Seed all scenarios into the pg fixture's fresh schema.
# We seed multiple run IDs in one fixture call so the pg fixture is invoked once
# per test function.
# ---------------------------------------------------------------------------

def _seed_clean(pg):
    """Seed run_clean: all 3 gate-checks pass for all 3 style tables."""
    run_id = "run_clean"
    _seed_run(pg, run_id)
    for cls_key, m in gen.MANIFEST.items():
        tbl = m["access_table"]
        _stamp_owner(pg, tbl, run_id)
        _seed_recon(pg, run_id, tbl, True)
        _seed_key_quality(pg, run_id, tbl, True)
        _create_style_table_full(pg, tbl, m["required_cols"])


def _seed_owner_mismatch(pg):
    """Seed runA + runB. Tables are stamped to runB; requesting runA must refuse."""
    run_a = "runA"
    run_b = "runB"
    _seed_run(pg, run_a)
    _seed_run(pg, run_b)
    for cls_key, m in gen.MANIFEST.items():
        tbl = m["access_table"]
        # Stamp as owned by runB, not runA
        _stamp_owner(pg, tbl, run_b)
        # Still seed recon/key_quality for runA so only gate 3 should fail
        _seed_recon(pg, run_a, tbl, True)
        _seed_key_quality(pg, run_a, tbl, True)


def _seed_recon_false(pg):
    """Seed run_recon_false: owner matches, but checksum_reconciliation.matches = False for ICCB."""
    run_id = "run_recon_false"
    _seed_run(pg, run_id)
    for cls_key, m in gen.MANIFEST.items():
        tbl = m["access_table"]
        _stamp_owner(pg, tbl, run_id)
        # Only ICCB gets matches=False; that's enough to refuse
        if cls_key == "ICCB":
            _seed_recon(pg, run_id, tbl, False)
        else:
            _seed_recon(pg, run_id, tbl, True)
        _seed_key_quality(pg, run_id, tbl, True)


def _seed_key_dupe(pg):
    """Seed run_key_dupe: owner + recon OK, but key_quality.is_unique = False for MCCB.

    We also create the access_raw style tables with all required cols so Gate 6 does
    not fire before Gate 5 (we want Gate 5 to be the one that refuses).
    """
    run_id = "run_key_dupe"
    _seed_run(pg, run_id)
    for cls_key, m in gen.MANIFEST.items():
        tbl = m["access_table"]
        _stamp_owner(pg, tbl, run_id)
        _seed_recon(pg, run_id, tbl, True)
        if cls_key == "MCCB":
            _seed_key_quality(pg, run_id, tbl, False)
        else:
            _seed_key_quality(pg, run_id, tbl, True)
        # Create the style table with all required cols so Gate 6 does not fire first.
        _create_style_table_full(pg, tbl, m["required_cols"])


def _seed_missing_col(pg):
    """Seed run_missing_col: all meta gates pass, but PCB style table is missing one required column."""
    run_id = "run_missing_col"
    _seed_run(pg, run_id)
    for cls_key, m in gen.MANIFEST.items():
        tbl = m["access_table"]
        _stamp_owner(pg, tbl, run_id)
        _seed_recon(pg, run_id, tbl, True)
        _seed_key_quality(pg, run_id, tbl, True)
        if cls_key == "PCB":
            _create_style_table_missing_one(pg, tbl, m["required_cols"])
        else:
            _create_style_table_full(pg, tbl, m["required_cols"])


# ---------------------------------------------------------------------------
# Gate 2: select_run_id refuses absent run_id
# ---------------------------------------------------------------------------

def test_select_run_id_refuses_when_absent(pg):
    """No extraction_run row with that id -> GenerationRefused mentioning run_id."""
    # pg fixture gives a clean schema -- no runs seeded
    with pytest.raises(gen.GenerationRefused, match="run_id"):
        gen.select_run_id(pg, "does-not-exist")


def test_select_run_id_returns_requested_when_present(pg):
    """If the run_id exists in extraction_run, select_run_id returns it."""
    _seed_run(pg, "my-run-001")
    result = gen.select_run_id(pg, "my-run-001")
    assert result == "my-run-001"


def test_select_run_id_returns_sole_run_when_none_requested(pg):
    """With exactly one extraction_run row and no requested id, return that sole run."""
    _seed_run(pg, "sole-run-001")
    result = gen.select_run_id(pg, None)
    assert result == "sole-run-001"


def test_select_run_id_refuses_ambiguous(pg):
    """With two runs and no requested id, refuse (ambiguous)."""
    _seed_run(pg, "run-abc")
    _seed_run(pg, "run-xyz")
    with pytest.raises(gen.GenerationRefused):
        gen.select_run_id(pg, None)


# ---------------------------------------------------------------------------
# Gate 3: materialized_owner mismatch refuses
# ---------------------------------------------------------------------------

def test_materialized_owner_mismatch_refuses(pg):
    """Tables are stamped to runB but we call assert_style_evidence with runA -> refuse."""
    _seed_owner_mismatch(pg)
    with pytest.raises(gen.GenerationRefused, match="materialized_owner"):
        gen.assert_style_evidence(pg, run_id="runA")


# ---------------------------------------------------------------------------
# Gate 4: checksum reconciliation False refuses
# ---------------------------------------------------------------------------

def test_reconciliation_false_refuses(pg):
    """ICCB checksum_reconciliation.matches=False -> assert_style_evidence refuses."""
    _seed_recon_false(pg)
    with pytest.raises(gen.GenerationRefused, match="reconcil"):
        gen.assert_style_evidence(pg, run_id="run_recon_false")


# ---------------------------------------------------------------------------
# Gate 5: key_quality not unique refuses
# ---------------------------------------------------------------------------

def test_key_quality_not_unique_refuses(pg):
    """MCCB key_quality.is_unique=False -> assert_style_evidence refuses."""
    _seed_key_dupe(pg)
    with pytest.raises(gen.GenerationRefused, match="key_quality|unique"):
        gen.assert_style_evidence(pg, run_id="run_key_dupe")


# ---------------------------------------------------------------------------
# Gate 6: missing manifest column refuses
# ---------------------------------------------------------------------------

def test_missing_manifest_column_refuses(pg):
    """PCB style table is missing one required column -> assert_style_evidence refuses."""
    _seed_missing_col(pg)
    with pytest.raises(gen.GenerationRefused, match="column"):
        gen.assert_style_evidence(pg, run_id="run_missing_col")


# ---------------------------------------------------------------------------
# Clean: all gates pass
# ---------------------------------------------------------------------------

def test_clean_run_passes(pg):
    """All six gates satisfied for run_clean -> assert_style_evidence does not raise."""
    _seed_clean(pg)
    # Should not raise
    gen.assert_style_evidence(pg, run_id="run_clean")


# ---------------------------------------------------------------------------
# MANIFEST structure checks (no DB needed)
# ---------------------------------------------------------------------------

def test_manifest_has_three_classes():
    assert set(gen.MANIFEST.keys()) == {"ICCB", "MCCB", "PCB"}


def test_manifest_required_cols_are_sorted_unique():
    for cls_key, m in gen.MANIFEST.items():
        req = m["required_cols"]
        assert req == sorted(set(req)), f"{cls_key}: required_cols must be sorted unique"


def test_manifest_pcb_has_no_d4():
    assert gen.MANIFEST["PCB"]["has_d4"] is False
    assert gen.MANIFEST["PCB"]["d4_cols"] == []


def test_manifest_iccb_mccb_have_d4():
    for cls_key in ("ICCB", "MCCB"):
        assert gen.MANIFEST[cls_key]["has_d4"] is True
        assert len(gen.MANIFEST[cls_key]["d4_cols"]) == 6


def test_manifest_pcb_has_ninst_cols():
    """PCB must have r_int_ninst_* and r_iec_ninst_* in required_cols."""
    req = gen.MANIFEST["PCB"]["required_cols"]
    assert "r_int_ninst_240" in req
    assert "r_int_ninst_480" in req
    assert "r_int_ninst_600" in req
    assert "r_iec_ninst_220" in req


def test_manifest_iccb_has_no_ninst_cols():
    """ICCB must NOT have r_int_ninst_* or r_iec_ninst_* in required_cols."""
    req = gen.MANIFEST["ICCB"]["required_cols"]
    assert "r_int_ninst_240" not in req
    assert "r_iec_ninst_220" not in req


def test_manifest_all_classes_have_id_and_instovramps():
    """ID and InstOvrAmps must be in every class's required_cols."""
    for cls_key, m in gen.MANIFEST.items():
        req = m["required_cols"]
        assert "ID" in req, f"{cls_key}: ID missing from required_cols"
        assert "InstOvrAmps" in req, f"{cls_key}: InstOvrAmps missing from required_cols"


# ===========================================================================
# Task 2 -- Unit tests: read_class + build_report (no live deps)
# ===========================================================================

# ---------------------------------------------------------------------------
# Helper: seed a minimal style table into access_raw for unit testing.
# ---------------------------------------------------------------------------

def _seed_style_table_for_read_class(conn, cls_key, rows_data):
    """Seed access_raw.<access_table> with minimal rows for read_class unit tests.

    rows_data: list of dicts with at least 'ID' key; missing keys are NULL.
    Builds the table with all required_cols for cls_key.
    """
    m = gen.MANIFEST[cls_key]
    tbl = m["access_table"]
    req = m["required_cols"]
    col_defs = ", ".join(f'"{c}" text' for c in req)
    with conn.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS access_raw."{tbl}" ({col_defs})'
        )
        for row in rows_data:
            col_names = ", ".join(f'"{c}"' for c in req)
            placeholders = ", ".join("%s" for _ in req)
            values = [row.get(c) for c in req]
            cur.execute(
                f'INSERT INTO access_raw."{tbl}" ({col_names}) VALUES ({placeholders})',
                values,
            )


def test_read_class_returns_expected_keys(pg):
    """read_class returns a dict with the documented keys."""
    _seed_style_table_for_read_class(pg, "ICCB", [{"ID": "1"}])
    result = gen.read_class(pg, "ICCB")
    for key in ("d4_rows", "d5_rows", "counts"):
        assert key in result, f"read_class result missing key {key!r}"
    counts = result["counts"]
    for key in (
        "total_styles",
        "d4_update_count",
        "d5_insert_count",
        "real_override_count",
        "rating_only_count",
        "d4_nonnull_per_col",
        "d5_block_present_counts",
        "samples",
    ):
        assert key in counts, f"counts missing key {key!r}"


def test_read_class_empty_table(pg):
    """read_class on an empty table returns zero counts."""
    _seed_style_table_for_read_class(pg, "ICCB", [])
    result = gen.read_class(pg, "ICCB")
    counts = result["counts"]
    assert counts["total_styles"] == 0
    assert counts["d4_update_count"] == 0
    assert counts["d5_insert_count"] == 0
    assert counts["real_override_count"] == 0
    assert counts["rating_only_count"] == 0
    assert result["d4_rows"] == []
    assert result["d5_rows"] == []


def test_read_class_d4_row_only_when_nonnull(pg):
    """d4_rows only includes rows with >= 1 non-null D4 column."""
    # Row 1: all D4 cols null -> no d4 row.
    # Row 2: TMT_TCCNumber set -> one d4 row.
    rows = [
        {"ID": "1"},  # all D4 null
        {"ID": "2", "TMT_TCCNumber": "ABC"},
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["d4_update_count"] == 1
    assert len(result["d4_rows"]) == 1
    sid, d4vals = result["d4_rows"][0]
    assert str(sid) == "2"
    # d4vals is keyed by pg column names (tmt_tcc_number, not TMT_TCCNumber).
    assert d4vals["tmt_tcc_number"] == "ABC"


def test_read_class_d5_row_only_when_nonnull_block(pg):
    """d5_rows only includes rows with >= 1 non-null block."""
    # Row 1: all D5 cols null -> no d5 row.
    # Row 2: InstOvrAmps set -> one d5 row (inst_override block non-null).
    rows = [
        {"ID": "1"},  # all D5 null
        {"ID": "2", "InstOvrAmps": "100.0"},
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["d5_insert_count"] == 1
    assert len(result["d5_rows"]) == 1


def test_read_class_pcb_no_d4(pg):
    """PCB has has_d4=False; d4_update_count must always be 0."""
    rows = [{"ID": "1", "TMT_TCCNumber": "X"}]  # D4 col present but PCB has no D4
    _seed_style_table_for_read_class(pg, "PCB", rows)
    result = gen.read_class(pg, "PCB")
    assert result["counts"]["d4_update_count"] == 0
    assert result["d4_rows"] == []


def test_read_class_policy_a_no_row_dropped(pg):
    """Policy (a): InstOvrAmps > 0 is a metric only -- it does NOT drop rows.

    A row with InstOvrAmps=0 (not real) but with an inst_override block present
    must still appear in d5_rows (the block is non-null).
    """
    rows = [
        {"ID": "1", "InstOvrAmps": "0", "InstOvrMinTolerance": "5"},
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["d5_insert_count"] == 1, (
        "row with InstOvrAmps=0 must be retained (policy a)"
    )
    assert result["counts"]["real_override_count"] == 0
    assert result["counts"]["rating_only_count"] == 0  # no r_int/r_iec either


def test_read_class_real_override_count(pg):
    """real_override_count counts rows where InstOvrAmps > 0."""
    rows = [
        {"ID": "1", "InstOvrAmps": "200.0"},  # real
        {"ID": "2", "InstOvrAmps": "0"},       # not real
        {"ID": "3", "InstOvrAmps": None},      # not real
        {"ID": "4", "InstOvrAmps": "50.5"},    # real
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["real_override_count"] == 2


def test_read_class_rating_only_count(pg):
    """rating_only_count: no real override but r_int or r_iec block present."""
    rows = [
        {"ID": "1", "InstOvrAmps": "200.0", "r_int_inst_240": "10"},  # real, not rating-only
        {"ID": "2", "r_int_inst_240": "10"},                           # rating-only (no InstOvrAmps)
        {"ID": "3", "r_iec_inst_220": "20"},                           # rating-only
        {"ID": "4", "InstOvrMinTolerance": "5"},                       # not real, no ratings -> neither
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["real_override_count"] == 1
    assert result["counts"]["rating_only_count"] == 2


def test_read_class_policy_a_partition(pg):
    """d5_insert_count == real_override_count + rating_only_count + neither.

    Every d5 row is retained regardless of the override metric.
    """
    # Seed rows: real(1) + rating-only(1) + neither-but-has-inst(1) + all-null(1)
    rows = [
        {"ID": "1", "InstOvrAmps": "100.0"},                          # real override
        {"ID": "2", "r_int_inst_240": "5"},                           # rating-only
        {"ID": "3", "InstOvrMinTolerance": "3"},                      # inst block present but no real/rating
        {"ID": "4"},                                                   # all null -> NOT in d5
    ]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    c = result["counts"]
    total_d5 = c["d5_insert_count"]
    real = c["real_override_count"]
    rating = c["rating_only_count"]
    # d5_insert_count must equal real + rating + "neither-but-in-d5"
    # The partition must be lossless: total_d5 >= real + rating (all retained).
    assert total_d5 == 3, "3 rows with non-null blocks must be in d5"
    assert real == 1
    assert rating == 1
    neither = total_d5 - real - rating
    assert neither == 1
    # Partition identity: no row is double-counted or dropped.
    assert total_d5 == real + rating + neither


def test_read_class_d5_blocks_keyed_by_manifest_cols(pg):
    """Block membership must use MANIFEST d5_block_cols (exact lists, not prefixes).

    The ninst_override block for ICCB must contain NInstOvr* columns.
    PCB must include r_int_ninst_* in its r_int block.
    ICCB must NOT include r_int_ninst_* (that prefix does NOT exist in ICCB
    block cols).
    """
    # Seed an ICCB row with both InstOvr and NInstOvr values.
    rows = [{"ID": "1", "InstOvrAmps": "50", "NInstOvrAmps": "60"}]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert result["counts"]["d5_insert_count"] == 1
    _, blocks = result["d5_rows"][0]
    assert blocks["inst_override"] is not None, "inst_override block must be non-null"
    assert "InstOvrAmps" in blocks["inst_override"]
    assert blocks["ninst_override"] is not None, "ninst_override block must be non-null"
    assert "NInstOvrAmps" in blocks["ninst_override"]


def test_read_class_samples_max_three(pg):
    """samples must contain at most 3 rows (first 3 with any non-null block)."""
    rows = [{"ID": str(i), "InstOvrAmps": "1.0"} for i in range(10)]
    _seed_style_table_for_read_class(pg, "ICCB", rows)
    result = gen.read_class(pg, "ICCB")
    assert len(result["counts"]["samples"]) <= 3


def test_build_report_returns_expected_keys(pg):
    """build_report returns a dict with 'provenance' and 'classes' keys."""
    run_id = "run_rpt"
    _seed_run(pg, run_id)
    # Seed minimal access_meta.tcc_snapshot row (snapshot_id PK, run_id FK).
    with pg.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tcc_snapshot
                (snapshot_id, run_id, host, db_name, role, captured_at)
            VALUES ('snap-001', %s, 'testhost', 'testdb', 'reader', now())
            ON CONFLICT (snapshot_id) DO NOTHING
            """,
            (run_id,),
        )
        # Seed a table row so access_meta.tables + checksum_reconciliation can be read.
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, load_state)
            VALUES (%s, 'BreakerICCBStyles', 'checksummed')
            ON CONFLICT (run_id, table_name) DO NOTHING
            """,
            (run_id,),
        )
        cur.execute(
            """
            INSERT INTO access_validation.checksum_reconciliation
                (run_id, table_name, access_checksum, staging_checksum, matches)
            VALUES (%s, 'BreakerICCBStyles', 'abc', 'abc', TRUE)
            ON CONFLICT (run_id, table_name) DO NOTHING
            """,
            (run_id,),
        )
    result = gen.build_report(pg, run_id)
    assert "provenance" in result, "build_report must return 'provenance'"
    assert "classes" in result, "build_report must return 'classes'"
    prov = result["provenance"]
    assert "run_id" in prov
    assert prov["run_id"] == run_id


# ===========================================================================
# Task 2 -- Live tests (marker: live)
# Require: tcc_fidelity_governed reachable + frozen Access present.
# Excluded by: uv run pytest -m "not live"
# ===========================================================================

_ACCDB = r"D:\TCC_NEW.accdb"


def _governed_dsn_available():
    """Return (ok, reason): probe governed DB reachability without touching data."""
    if not os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN"):
        return False, "ACCESS_HARNESS_SUPERUSER_DSN unset"
    try:
        conn = psycopg.connect(config.governed_pg_dsn(), autocommit=True, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001
        return False, f"tcc_fidelity_governed unreachable: {exc!r}"
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            (db,) = cur.fetchone()
        if db != "tcc_fidelity_governed":
            return False, f"DSN resolved to {db!r}, not tcc_fidelity_governed"
    finally:
        conn.close()
    return True, ""


def _accdb_available():
    """Return (ok, reason): probe the frozen Access file + pyodbc driver."""
    import pathlib
    if not pathlib.Path(_ACCDB).exists():
        return False, f"{_ACCDB} not present"
    try:
        import pyodbc  # noqa: F401
    except Exception:  # noqa: BLE001
        return False, "pyodbc not importable (non-Windows / no ACE driver)"
    return True, ""


@pytest.fixture(scope="module")
def governed_conn():
    """Module-scoped connection to tcc_fidelity_governed (live tests only).

    Skips with a clear reason when the governed DB is unavailable.
    """
    ok, reason = _governed_dsn_available()
    if not ok:
        pytest.skip(f"governed DB prerequisite absent: {reason}")
    conn = psycopg.connect(config.governed_pg_dsn(), autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


@pytest.mark.live
def test_read_class_iccb_live_counts(governed_conn):
    """ICCB: total_styles==608, d5_insert_count==608, real_override_count==241."""
    result = gen.read_class(governed_conn, "ICCB")
    c = result["counts"]
    assert c["total_styles"] == 608, f"ICCB total_styles={c['total_styles']}, expected 608"
    assert c["d5_insert_count"] == 608, f"ICCB d5_insert_count={c['d5_insert_count']}, expected 608"
    assert c["real_override_count"] == 241, (
        f"ICCB real_override_count={c['real_override_count']}, expected 241"
    )


@pytest.mark.live
def test_read_class_mccb_live_counts(governed_conn):
    """MCCB: total_styles==10335, real_override_count==129."""
    result = gen.read_class(governed_conn, "MCCB")
    c = result["counts"]
    assert c["total_styles"] == 10335, f"MCCB total_styles={c['total_styles']}, expected 10335"
    assert c["real_override_count"] == 129, (
        f"MCCB real_override_count={c['real_override_count']}, expected 129"
    )


@pytest.mark.live
def test_read_class_pcb_live_counts(governed_conn):
    """PCB: total_styles==3279, real_override_count==317."""
    result = gen.read_class(governed_conn, "PCB")
    c = result["counts"]
    assert c["total_styles"] == 3279, f"PCB total_styles={c['total_styles']}, expected 3279"
    assert c["real_override_count"] == 317, (
        f"PCB real_override_count={c['real_override_count']}, expected 317"
    )


@pytest.mark.live
def test_policy_a_iccb_no_row_dropped_live(governed_conn):
    """Policy (a): d5_insert_count == real + rating_only + neither (ICCB live).

    No row is dropped by the InstOvrAmps > 0 metric.
    real_override_count must be 241 for ICCB.
    """
    result = gen.read_class(governed_conn, "ICCB")
    c = result["counts"]
    total_d5 = c["d5_insert_count"]
    real = c["real_override_count"]
    rating = c["rating_only_count"]
    # All D5 rows are retained; partition must be exhaustive.
    neither = total_d5 - real - rating
    assert neither >= 0, "d5_insert_count must be >= real + rating"
    assert total_d5 == real + rating + neither
    assert real == 241, f"ICCB real_override_count must be 241, got {real}"


@pytest.mark.live
def test_generate_compose_live(governed_conn, tmp_path):
    """generate() orchestrator: files written + report['classes'] populated for all 3 classes.

    Closes Task-2 Minor 2: build_report returns classes:{} and the orchestrator
    merges them with the per-class counts from read_class.
    """
    result = gen.generate(governed_conn, None, str(tmp_path))
    # All 3 output files must exist
    import pathlib
    assert pathlib.Path(result["sql_029"]).exists(), "029_d4_data.sql not written"
    assert pathlib.Path(result["sql_030"]).exists(), "030_d5_data.sql not written"
    assert pathlib.Path(result["report_json"]).exists(), "generation_report.json not written"
    # report["classes"] must be populated for all 3 classes
    classes = result["classes"]
    assert set(classes.keys()) == {"ICCB", "MCCB", "PCB"}, \
        f"Expected ICCB/MCCB/PCB in classes, got {set(classes.keys())}"
    for cls in ("ICCB", "MCCB", "PCB"):
        c = classes[cls]
        assert "d4_update_count" in c, f"{cls} missing d4_update_count"
        assert "d5_insert_count" in c, f"{cls} missing d5_insert_count"
        assert c["d5_insert_count"] > 0, f"{cls} d5_insert_count should be > 0"
    # PCB has no D4
    assert classes["PCB"]["d4_update_count"] == 0, "PCB d4_update_count must be 0"
    # ICCB + MCCB have D4
    assert classes["ICCB"]["d4_update_count"] > 0, "ICCB d4_update_count must be > 0"
    assert classes["MCCB"]["d4_update_count"] > 0, "MCCB d4_update_count must be > 0"


@pytest.mark.live
def test_governed_vs_direct_parity(governed_conn):
    """Governed-vs-direct parity: counts from access_raw must match frozen Access.

    For each class, asserts IDENTICAL total_styles, d5_insert_count,
    real_override_count, rating_only_count between governed and direct reads.
    Also asserts identical key-set + value of one inst_override block row
    to confirm no drift in type representation (Decimal/text/numeric).
    """
    import pathlib

    ok_accdb, reason_accdb = _accdb_available()
    if not ok_accdb:
        pytest.skip(f"frozen Access prerequisite absent: {reason_accdb}")

    import pyodbc

    # -- Resolve the frozen copy path from the governed DB --
    with governed_conn.cursor() as cur:
        cur.execute(
            "SELECT frozen_copy_path FROM access_meta.extraction_run "
            "ORDER BY extracted_at_utc DESC LIMIT 1"
        )
        row = cur.fetchone()
    if row is None:
        pytest.skip("no extraction_run row in governed DB")
    frozen_path = row[0]
    if not frozen_path or not pathlib.Path(frozen_path).exists():
        # Fall back to the known constant path.
        frozen_path = _ACCDB
    if not pathlib.Path(frozen_path).exists():
        pytest.skip(f"frozen copy not found at {frozen_path!r}")

    # -- Direct read from frozen Access via pyodbc (verbatim dry-run logic) --
    cs = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
        + frozen_path
        + ";Mode=Read"
    )
    cx = pyodbc.connect(cs, readonly=True)
    direct_counts = {}
    direct_sample_blocks = {}  # cls -> first inst_override block dict (or None)
    try:
        for cls_key, m in gen.MANIFEST.items():
            atbl = m["access_table"]
            has_d4 = m["has_d4"]
            block_cols = m["d5_block_cols"]
            cur_a = cx.cursor()
            cur_a.execute("SELECT * FROM [%s]" % atbl)
            cols = [d[0] for d in cur_a.description]
            rows = [dict(zip(cols, r)) for r in cur_a.fetchall()]

            total = len(rows)
            real_override = 0
            rating_only = 0
            d5_count = 0
            sample_block = None

            for row in rows:
                # D5 blocks -- use MANIFEST exact col lists (not startswith).
                blocks = {}
                for bname, bcols in block_cols.items():
                    blk = {
                        c: row[c]
                        for c in bcols
                        if c in row and row[c] is not None
                    }
                    blocks[bname] = blk if blk else None

                inst_amps = row.get("InstOvrAmps")
                # Coerce defensively (same as governed reader).
                try:
                    inst_amps_f = float(inst_amps) if inst_amps is not None else None
                except (TypeError, ValueError):
                    inst_amps_f = None
                is_real = inst_amps_f is not None and inst_amps_f > 0
                has_rating = blocks.get("r_int") is not None or blocks.get("r_iec") is not None

                if is_real:
                    real_override += 1
                elif has_rating:
                    rating_only += 1

                if any(b is not None for b in blocks.values()):
                    d5_count += 1
                    if sample_block is None and blocks.get("inst_override"):
                        # Normalise values to str for comparison (both sides).
                        sample_block = {
                            k: str(v) if v is not None else None
                            for k, v in blocks["inst_override"].items()
                        }

            direct_counts[cls_key] = {
                "total_styles": total,
                "d5_insert_count": d5_count,
                "real_override_count": real_override,
                "rating_only_count": rating_only,
            }
            direct_sample_blocks[cls_key] = sample_block
    finally:
        cx.close()

    # -- Governed read --
    gov_counts = {}
    gov_sample_blocks = {}
    for cls_key in gen.MANIFEST:
        result = gen.read_class(governed_conn, cls_key)
        c = result["counts"]
        gov_counts[cls_key] = {
            "total_styles": c["total_styles"],
            "d5_insert_count": c["d5_insert_count"],
            "real_override_count": c["real_override_count"],
            "rating_only_count": c["rating_only_count"],
        }
        # Find first inst_override sample block.
        blk = None
        for _, blocks in result["d5_rows"]:
            if blocks.get("inst_override"):
                blk = {
                    k: str(v) if v is not None else None
                    for k, v in blocks["inst_override"].items()
                }
                break
        gov_sample_blocks[cls_key] = blk

    # -- Assert parity per class --
    for cls_key in gen.MANIFEST:
        d = direct_counts[cls_key]
        g = gov_counts[cls_key]
        assert d["total_styles"] == g["total_styles"], (
            f"{cls_key}: total_styles mismatch direct={d['total_styles']} gov={g['total_styles']}"
        )
        assert d["d5_insert_count"] == g["d5_insert_count"], (
            f"{cls_key}: d5_insert_count mismatch direct={d['d5_insert_count']} gov={g['d5_insert_count']}"
        )
        assert d["real_override_count"] == g["real_override_count"], (
            f"{cls_key}: real_override_count mismatch "
            f"direct={d['real_override_count']} gov={g['real_override_count']}"
        )
        assert d["rating_only_count"] == g["rating_only_count"], (
            f"{cls_key}: rating_only_count mismatch "
            f"direct={d['rating_only_count']} gov={g['rating_only_count']}"
        )
        # Key-set parity on first inst_override block.
        d_blk = direct_sample_blocks[cls_key]
        g_blk = gov_sample_blocks[cls_key]
        if d_blk is not None or g_blk is not None:
            assert (d_blk is None) == (g_blk is None), (
                f"{cls_key}: one side has an inst_override sample block and the other does not"
            )
            if d_blk is not None:
                assert set(d_blk.keys()) == set(g_blk.keys()), (
                    f"{cls_key}: inst_override block key-set mismatch "
                    f"direct={set(d_blk.keys())} gov={set(g_blk.keys())}"
                )
                assert d_blk == g_blk, (
                    f"{cls_key}: inst_override block value mismatch "
                    f"direct={d_blk!r} gov={g_blk!r}"
                )


# ===========================================================================
# Task 3 -- Unit (non-live) tests: emit_029 + emit_030 shape checks
# ===========================================================================

# Synthetic data for emit shape tests (no DB required).

_SAMPLE_REPORT = {
    "provenance": {
        "run_id": "run-unit-test-001",
        "source_sha256": "aabbccdd" * 8,
        "frozen_copy_path": "/frozen/TCC_NEW.accdb",
        "driver_name": "TestDriver",
        "dbms_version": "0.0.0",
        "read_only": True,
        "snapshot_id": "snap-unit-001",
        "host": "testhost",
        "db_name": "tcc_fidelity_governed",
        "role": "reader",
        "table_checksums": {
            "BreakerICCBStyles": {"checksum": "aa", "matches": True},
            "BreakerMCCBStyles": {"checksum": "bb", "matches": True},
            "BreakerPCBStyles": {"checksum": "cc", "matches": True},
        },
        "generator_version": "0.2.0",
        "generated_at": "2026-06-27T00:00:00Z",
    },
    "classes": {
        "ICCB": {
            "d4_update_count": 2,
            "d5_insert_count": 3,
            "total_styles": 3,
            "real_override_count": 1,
            "rating_only_count": 1,
            "d4_nonnull_per_col": {},
            "d5_block_present_counts": {},
            "samples": [],
        },
        "MCCB": {
            "d4_update_count": 1,
            "d5_insert_count": 1,
            "total_styles": 1,
            "real_override_count": 0,
            "rating_only_count": 1,
            "d4_nonnull_per_col": {},
            "d5_block_present_counts": {},
            "samples": [],
        },
        "PCB": {
            "d4_update_count": 0,
            "d5_insert_count": 2,
            "total_styles": 2,
            "real_override_count": 0,
            "rating_only_count": 2,
            "d4_nonnull_per_col": None,
            "d5_block_present_counts": {},
            "samples": [],
        },
    },
}

_SAMPLE_READS = {
    "ICCB": {
        "d4_rows": [
            (101, {
                "tmt_tcc_number": "TCC-A",
                "tmt_notes": "note one",
                "tmt_trip_plug": 0,
                "tmt_breaker_type": 1,
                "tmt_thermal_magnetic": None,
                "tmt_thermal": 0,
            }),
            (102, {
                "tmt_tcc_number": None,
                "tmt_notes": None,
                "tmt_trip_plug": 1,
                "tmt_breaker_type": 0,
                "tmt_thermal_magnetic": 1,
                "tmt_thermal": None,
            }),
        ],
        "d5_rows": [
            (101, {"inst_override": {"InstOvrAmps": 100.0}, "ninst_override": None,
                   "brk_times": None, "r_int": {"r_int_inst_240": 50}, "r_iec": None}),
            (102, {"inst_override": None, "ninst_override": None,
                   "brk_times": {"BrkTimesMechOpening50": 30}, "r_int": None, "r_iec": None}),
            (103, {"inst_override": {"InstOvrAmps": 0}, "ninst_override": None,
                   "brk_times": None, "r_int": None, "r_iec": {"r_iec_inst_220": 25}}),
        ],
        "counts": _SAMPLE_REPORT["classes"]["ICCB"],
    },
    "MCCB": {
        "d4_rows": [
            (201, {
                "tmt_tcc_number": "TCC-B",
                "tmt_notes": None,
                "tmt_trip_plug": 0,
                "tmt_breaker_type": 0,
                "tmt_thermal_magnetic": 0,
                "tmt_thermal": 1,
            }),
        ],
        "d5_rows": [
            (201, {"inst_override": None, "ninst_override": None,
                   "brk_times": None, "r_int": {"r_int_inst_480": 65}, "r_iec": None}),
        ],
        "counts": _SAMPLE_REPORT["classes"]["MCCB"],
    },
    "PCB": {
        "d4_rows": [],
        "d5_rows": [
            (301, {"inst_override": {"InstOvrAmps": 200}, "ninst_override": None,
                   "brk_times": None, "r_int": None, "r_iec": None}),
            (302, {"inst_override": None, "ninst_override": None,
                   "brk_times": None, "r_int": {"r_int_inst_600": 85}, "r_iec": None}),
        ],
        "counts": _SAMPLE_REPORT["classes"]["PCB"],
    },
}


class TestEmit029Shape:
    """Shape tests for emit_029 (no DB required)."""

    def setup_method(self):
        self.sql = gen.emit_029(_SAMPLE_READS, _SAMPLE_REPORT)

    def test_contains_create_temp_table_stage(self):
        assert "CREATE TEMP TABLE stage_029_" in self.sql, \
            "emit_029 must create a per-class temp stage table"

    def test_contains_begin_and_commit(self):
        assert "BEGIN;" in self.sql
        assert "COMMIT;" in self.sql

    def test_contains_on_error_stop(self):
        assert "\\set ON_ERROR_STOP on" in self.sql, \
            "emit_029 must set ON_ERROR_STOP"

    def test_contains_provenance_run_id(self):
        assert "run-unit-test-001" in self.sql, \
            "emit_029 must embed the run_id in the provenance header"

    def test_guard_stage_count(self):
        """Stage-count guard must be present."""
        assert "stage row count" in self.sql or "v_stage_count" in self.sql, \
            "emit_029 must contain a stage row count guard"

    def test_guard_duplicate(self):
        """Duplicate source_id guard must be present."""
        assert "duplicate" in self.sql.lower() or "HAVING count(*) > 1" in self.sql, \
            "emit_029 must contain a duplicate source_id guard"

    def test_guard_ddl_present(self):
        """DDL-present guard (information_schema.columns) must be present."""
        assert "information_schema.columns" in self.sql, \
            "emit_029 must check DDL presence via information_schema.columns"

    def test_guard_coverage_antijoin(self):
        """Coverage anti-join guard (orphan rows) must be present."""
        assert "orphan" in self.sql.lower() or "LEFT JOIN" in self.sql or "NOT EXISTS" in self.sql, \
            "emit_029 must contain a coverage anti-join guard"

    def test_contains_update(self):
        assert "UPDATE tcc." in self.sql, "emit_029 must emit UPDATE tcc.<table>"

    def test_post_write_assertion(self):
        """Post-write assertion (DO block after UPDATE) must be present."""
        # The post-write DO block comes AFTER the UPDATE
        update_pos = self.sql.rfind("UPDATE tcc.")
        postwrite_pos = self.sql.find("post-write", update_pos)
        assert postwrite_pos > update_pos, \
            "emit_029 must contain a post-write count assertion after the UPDATE"

    def test_no_dryrun_lock(self):
        """emit_029 is prod-bound -- must NOT contain the dryrun sandbox guard."""
        assert "dryrun" not in self.sql.lower(), \
            "emit_029 must NOT contain a dryrun database guard"

    def test_iccb_and_mccb_both_present(self):
        assert "stage_029_iccb" in self.sql, "ICCB stage table missing"
        assert "stage_029_mccb" in self.sql, "MCCB stage table missing"

    def test_on_commit_drop(self):
        assert "ON COMMIT DROP" in self.sql, "Temp stage table must use ON COMMIT DROP"


class TestEmit030Shape:
    """Shape tests for emit_030 (no DB required)."""

    def setup_method(self):
        self.sql = gen.emit_030(_SAMPLE_READS, _SAMPLE_REPORT)

    def test_contains_stage_030_d5(self):
        assert "stage_030_d5" in self.sql, "emit_030 must create stage_030_d5"

    def test_contains_on_conflict(self):
        assert "ON CONFLICT (breaker_class, source_id) DO UPDATE" in self.sql, \
            "emit_030 must use ON CONFLICT (breaker_class, source_id) DO UPDATE"

    def test_contains_target_table(self):
        assert "brk_style_native_overrides" in self.sql, \
            "emit_030 must target brk_style_native_overrides"

    def test_contains_begin_and_commit(self):
        assert "BEGIN;" in self.sql
        assert "COMMIT;" in self.sql

    def test_contains_on_error_stop(self):
        assert "\\set ON_ERROR_STOP on" in self.sql

    def test_contains_provenance_run_id(self):
        assert "run-unit-test-001" in self.sql

    def test_guard_stage_count(self):
        assert "stage row count" in self.sql or "v_stage_count" in self.sql

    def test_guard_duplicate(self):
        assert "duplicate" in self.sql.lower() or "HAVING count(*) > 1" in self.sql

    def test_guard_ddl_present(self):
        assert "information_schema.tables" in self.sql or "information_schema.columns" in self.sql

    def test_guard_pk_shape(self):
        """PK must be exactly (breaker_class, source_id)."""
        assert "PRIMARY KEY" in self.sql or "v_pk_cols" in self.sql, \
            "emit_030 must verify the PK shape"

    def test_guard_coverage_antijoin(self):
        """Per-class coverage anti-join must be present."""
        assert "NOT EXISTS" in self.sql or "orphan" in self.sql.lower(), \
            "emit_030 must contain a per-class coverage anti-join guard"

    def test_post_write_assertion(self):
        insert_pos = self.sql.rfind("INSERT INTO tcc.brk_style_native_overrides")
        postwrite_pos = self.sql.find("post-write", insert_pos)
        assert postwrite_pos > insert_pos, \
            "emit_030 must contain a post-write assertion after the INSERT"

    def test_on_commit_drop(self):
        assert "ON COMMIT DROP" in self.sql


# ===========================================================================
# Task 3 -- LIVE apply test on tcc_fidelity_test
# Proves the coverage anti-join guard is real and raises on orphan rows.
# ===========================================================================

@pytest.fixture(scope="module")
def tcc_test_conn():
    """Module-scoped connection to tcc_fidelity_test for Task 3 live apply tests.

    Skips if ACCESS_HARNESS_SUPERUSER_DSN is unset.
    """
    if not os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN"):
        pytest.skip("ACCESS_HARNESS_SUPERUSER_DSN unset -- skipping live apply tests")
    from access_harness.config import test_pg_dsn
    import psycopg
    conn = psycopg.connect(test_pg_dsn(), autocommit=True)
    # Verify we are on tcc_fidelity_test
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        (db,) = cur.fetchone()
    if db != "tcc_fidelity_test":
        conn.close()
        pytest.skip(f"Expected tcc_fidelity_test, got {db!r}")
    yield conn
    conn.close()


def _create_minimal_tcc_schema(conn):
    """Create a minimal tcc schema with the 3 style tables and brk_style_native_overrides.

    Used by the live apply test to simulate the migration-029/030 DDL without
    touching the real tcc DB.
    """
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS tcc CASCADE")
        cur.execute("CREATE SCHEMA tcc")

        # brk_iccb_styles with tmt_* columns (mig 029 shape)
        cur.execute("""
            CREATE TABLE tcc.brk_iccb_styles (
                id serial PRIMARY KEY,
                source_id integer NOT NULL UNIQUE,
                tmt_tcc_number       text,
                tmt_notes            text,
                tmt_trip_plug        smallint,
                tmt_breaker_type     smallint,
                tmt_thermal_magnetic smallint,
                tmt_thermal          smallint
            )
        """)

        # brk_mccb_styles with tmt_* columns
        cur.execute("""
            CREATE TABLE tcc.brk_mccb_styles (
                id serial PRIMARY KEY,
                source_id integer NOT NULL UNIQUE,
                tmt_tcc_number       text,
                tmt_notes            text,
                tmt_trip_plug        smallint,
                tmt_breaker_type     smallint,
                tmt_thermal_magnetic smallint,
                tmt_thermal          smallint
            )
        """)

        # brk_pcb_styles (no D4 cols needed for apply test, but needed for D5 coverage)
        cur.execute("""
            CREATE TABLE tcc.brk_pcb_styles (
                id serial PRIMARY KEY,
                source_id integer NOT NULL UNIQUE
            )
        """)

        # brk_style_native_overrides (mig 030 shape)
        cur.execute("""
            CREATE TABLE tcc.brk_style_native_overrides (
                breaker_class  text    NOT NULL,
                source_id      integer NOT NULL,
                inst_override  jsonb,
                ninst_override jsonb,
                brk_times      jsonb,
                r_int          jsonb,
                r_iec          jsonb,
                ovr_curves     jsonb,
                CONSTRAINT brk_style_native_overrides_class_chk
                    CHECK (breaker_class IN ('ICCB','MCCB','PCB')),
                CONSTRAINT brk_style_native_overrides_source_id_chk
                    CHECK (source_id > 0),
                PRIMARY KEY (breaker_class, source_id)
            )
        """)


def _seed_style_rows(conn, source_ids_by_class):
    """Seed style rows so the coverage guard has something to join against."""
    with conn.cursor() as cur:
        for sid in source_ids_by_class.get("ICCB", []):
            cur.execute("INSERT INTO tcc.brk_iccb_styles (source_id) VALUES (%s)", (sid,))
        for sid in source_ids_by_class.get("MCCB", []):
            cur.execute("INSERT INTO tcc.brk_mccb_styles (source_id) VALUES (%s)", (sid,))
        for sid in source_ids_by_class.get("PCB", []):
            cur.execute("INSERT INTO tcc.brk_pcb_styles (source_id) VALUES (%s)", (sid,))


def _exec_sql_script(conn, sql_str):
    """Execute a multi-statement SQL script string against the connection.

    psql metacommands (lines starting with backslash, e.g. \\set ON_ERROR_STOP)
    are not valid SQL and cannot be passed to psycopg.execute().  Strip them
    before execution -- the ON_ERROR_STOP behaviour is irrelevant when running
    via psycopg because any error already raises immediately.

    Runs the entire script in one cursor.execute() call so multi-statement
    execution (including DO blocks and DDL) works correctly.
    """
    # Strip psql metacommand lines (\\set, \\i, \\c, etc.)
    cleaned_lines = [
        line for line in sql_str.splitlines()
        if not line.strip().startswith("\\")
    ]
    cleaned = "\n".join(cleaned_lines)
    with conn.cursor() as cur:
        cur.execute(cleaned)


@pytest.mark.live
def test_emit_029_030_apply_and_tamper_guard(tcc_test_conn):
    """LIVE apply test: prove the coverage anti-join guard RAISEs on orphan rows.

    Steps:
      1. Create a minimal tcc schema in tcc_fidelity_test.
      2. Seed a few source_id rows in the style tables.
      3. Build small synthetic class_reads whose source_ids EXIST in the target.
      4. Apply emit_029 -- assert it COMMITs and values landed.
      5. Apply emit_030 -- assert it COMMITs and rows landed.
      6. TAMPER: build class_reads with a source_id NOT in the target (orphan).
      7. Apply tampered emit_029 -- assert a psycopg error is raised (guard fires).
      8. Assert nothing was written (txn aborted).
    """
    import psycopg

    conn = tcc_test_conn

    # --- Setup: minimal tcc schema + seed rows ---
    _create_minimal_tcc_schema(conn)
    _seed_style_rows(conn, {"ICCB": [10, 20], "MCCB": [30], "PCB": [40, 50]})

    # --- Build class_reads that are KNOWN-GOOD (all source_ids exist) ---
    good_reads = {
        "ICCB": {
            "d4_rows": [
                (10, {"tmt_tcc_number": "TCC-X", "tmt_notes": None,
                      "tmt_trip_plug": 0, "tmt_breaker_type": 1,
                      "tmt_thermal_magnetic": 0, "tmt_thermal": 0}),
                (20, {"tmt_tcc_number": None, "tmt_notes": "note2",
                      "tmt_trip_plug": 1, "tmt_breaker_type": 0,
                      "tmt_thermal_magnetic": 1, "tmt_thermal": 1}),
            ],
            "d5_rows": [
                (10, {"inst_override": {"InstOvrAmps": 100}, "ninst_override": None,
                      "brk_times": None, "r_int": None, "r_iec": None}),
                (20, {"inst_override": None, "ninst_override": None,
                      "brk_times": {"BrkTimesMechOpening50": 20},
                      "r_int": None, "r_iec": None}),
            ],
            "counts": {"d4_update_count": 2, "d5_insert_count": 2,
                       "total_styles": 2, "real_override_count": 1,
                       "rating_only_count": 0, "d4_nonnull_per_col": {},
                       "d5_block_present_counts": {}, "samples": []},
        },
        "MCCB": {
            "d4_rows": [
                (30, {"tmt_tcc_number": "TCC-Y", "tmt_notes": None,
                      "tmt_trip_plug": 0, "tmt_breaker_type": 0,
                      "tmt_thermal_magnetic": 0, "tmt_thermal": 0}),
            ],
            "d5_rows": [
                (30, {"inst_override": None, "ninst_override": None,
                      "brk_times": None, "r_int": {"r_int_inst_480": 65}, "r_iec": None}),
            ],
            "counts": {"d4_update_count": 1, "d5_insert_count": 1,
                       "total_styles": 1, "real_override_count": 0,
                       "rating_only_count": 1, "d4_nonnull_per_col": {},
                       "d5_block_present_counts": {}, "samples": []},
        },
        "PCB": {
            "d4_rows": [],
            "d5_rows": [
                (40, {"inst_override": {"InstOvrAmps": 200}, "ninst_override": None,
                      "brk_times": None, "r_int": None, "r_iec": None}),
                (50, {"inst_override": None, "ninst_override": None,
                      "brk_times": None, "r_int": {"r_int_inst_600": 85}, "r_iec": None}),
            ],
            "counts": {"d4_update_count": 0, "d5_insert_count": 2,
                       "total_styles": 2, "real_override_count": 1,
                       "rating_only_count": 1, "d4_nonnull_per_col": None,
                       "d5_block_present_counts": {}, "samples": []},
        },
    }

    good_report = {
        "provenance": {
            "run_id": "apply-test-001",
            "source_sha256": "deadbeef",
            "frozen_copy_path": "/test/frozen.accdb",
            "driver_name": "TestDriver",
            "dbms_version": "0.0.0",
            "read_only": True,
            "snapshot_id": "snap-apply-001",
            "host": "testhost",
            "db_name": "tcc_fidelity_test",
            "role": "test",
            "table_checksums": {},
            "generator_version": "0.2.0",
        },
        "classes": {
            "ICCB": good_reads["ICCB"]["counts"],
            "MCCB": good_reads["MCCB"]["counts"],
            "PCB": good_reads["PCB"]["counts"],
        },
    }

    # --- Apply emit_029 (good) -- should COMMIT ---
    sql_029_good = gen.emit_029(good_reads, good_report)
    _exec_sql_script(conn, sql_029_good)

    # Verify values landed for ICCB source_id=10
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tmt_tcc_number, tmt_trip_plug FROM tcc.brk_iccb_styles WHERE source_id=10"
        )
        row = cur.fetchone()
    assert row is not None, "ICCB source_id=10 must exist after emit_029 apply"
    assert row[0] == "TCC-X", f"tmt_tcc_number mismatch: {row[0]!r}"
    assert row[1] == 0, f"tmt_trip_plug mismatch: {row[1]!r}"

    # --- Apply emit_030 (good) -- should COMMIT ---
    sql_030_good = gen.emit_030(good_reads, good_report)
    _exec_sql_script(conn, sql_030_good)

    # Verify D5 row landed for ICCB source_id=10
    with conn.cursor() as cur:
        cur.execute(
            "SELECT inst_override FROM tcc.brk_style_native_overrides "
            "WHERE breaker_class='ICCB' AND source_id=10"
        )
        row = cur.fetchone()
    assert row is not None, "D5 row for ICCB source_id=10 must exist after emit_030 apply"
    assert row[0] is not None, "inst_override must be non-null for ICCB source_id=10"
    assert row[0].get("InstOvrAmps") == 100, f"InstOvrAmps mismatch: {row[0]!r}"

    # --- TAMPER: add an orphan source_id (9999) not in tcc.brk_iccb_styles ---
    tampered_reads = {
        "ICCB": {
            "d4_rows": [
                (10, {"tmt_tcc_number": "TAMPERED", "tmt_notes": None,
                      "tmt_trip_plug": 0, "tmt_breaker_type": 0,
                      "tmt_thermal_magnetic": 0, "tmt_thermal": 0}),
                # orphan: source_id 9999 does not exist in brk_iccb_styles
                (9999, {"tmt_tcc_number": "ORPHAN", "tmt_notes": None,
                        "tmt_trip_plug": 0, "tmt_breaker_type": 0,
                        "tmt_thermal_magnetic": 0, "tmt_thermal": 0}),
            ],
            "d5_rows": good_reads["ICCB"]["d5_rows"],
            "counts": {
                "d4_update_count": 2,  # 2 rows so count guard passes
                "d5_insert_count": 2, "total_styles": 2,
                "real_override_count": 0, "rating_only_count": 0,
                "d4_nonnull_per_col": {}, "d5_block_present_counts": {}, "samples": [],
            },
        },
        "MCCB": good_reads["MCCB"],
        "PCB": good_reads["PCB"],
    }
    tampered_report = dict(good_report)
    tampered_report = {
        "provenance": good_report["provenance"],
        "classes": {
            "ICCB": tampered_reads["ICCB"]["counts"],
            "MCCB": good_reads["MCCB"]["counts"],
            "PCB": good_reads["PCB"]["counts"],
        },
    }

    sql_029_tampered = gen.emit_029(tampered_reads, tampered_report)

    # The coverage anti-join guard MUST RAISE -- the orphan source_id 9999 has no
    # matching row in tcc.brk_iccb_styles.
    tamper_raised = False
    tamper_exc = None
    try:
        _exec_sql_script(conn, sql_029_tampered)
    except Exception as exc:  # noqa: BLE001
        tamper_raised = True
        tamper_exc = exc

    # The guard raised -- but the connection is now in an aborted transaction block
    # (BEGIN was issued before the DO block raised).  Roll back so subsequent
    # statements can execute on the same connection.
    with conn.cursor() as cur:
        cur.execute("ROLLBACK")

    if tamper_raised:
        err_str = str(tamper_exc).lower()
        # Guard message must mention 'orphan' or '029 guard'
        assert "orphan" in err_str or "029 guard" in err_str or "no match" in err_str, \
            f"Expected orphan/guard error, got: {tamper_exc!r}"

    assert tamper_raised, (
        "Tampered emit_029 (orphan source_id=9999) MUST raise via the coverage anti-join guard -- "
        "guard is NOT enforcing row-level coverage"
    )

    # Verify the ICCB row was NOT updated to 'TAMPERED' (txn aborted -- rollback confirmed)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tmt_tcc_number FROM tcc.brk_iccb_styles WHERE source_id=10"
        )
        row = cur.fetchone()
    assert row is not None
    assert row[0] == "TCC-X", (
        f"tmt_tcc_number must still be 'TCC-X' (not 'TAMPERED') after aborted txn: {row[0]!r}"
    )

    # Cleanup: drop tcc schema so other tests in this module are not affected
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS tcc CASCADE")
