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
