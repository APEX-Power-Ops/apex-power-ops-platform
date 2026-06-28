"""Tests for access_harness.d4d5_governed_generation -- Task 1: manifest + six fail-closed gates.

All tests run on tcc_fidelity_test (via the pg fixture from conftest.py).
The normal suite NEVER touches tcc_fidelity_governed.

Gate scenarios seeded inline using pg fixture:
  run_clean       -- all 3 gates pass (owner matches, recon True, key unique, all cols present)
  runA/runB       -- owner mismatch (table stamped to runB, we request runA)
  run_recon_false -- checksum_reconciliation.matches = False
  run_key_dupe    -- key_quality.is_unique = False
  run_missing_col -- access_raw style table is missing one required column
  Gate 2 (absent run_id): no extraction_run row at all with that id -> refuse
"""
import psycopg
import pytest
from access_harness import config
from access_harness import d4d5_governed_generation as gen

# ---------------------------------------------------------------------------
# Helper: open a fresh connection to tcc_fidelity_test (NOT autocommit so the
# pg fixture's teardown cannot interfere with connections open during the test).
# ---------------------------------------------------------------------------

def _test_conn(autocommit=True):
    dsn = config.test_pg_dsn()
    return psycopg.connect(dsn, autocommit=autocommit)


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
