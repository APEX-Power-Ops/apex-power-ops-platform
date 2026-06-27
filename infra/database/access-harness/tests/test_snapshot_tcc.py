"""Integration tests for access_harness.snapshot_tcc.

The snapshot bridge pulls key-sets / counts from the governed tcc.* schema,
which lives on a SEPARATE host Postgres reachable only over the mesh
(100.64.0.1:5432, db tcc_breaker_viewer_20260625, role tcc_breaker_ro).

An EXCEPT / anti-join cannot cross Postgres instances, so snapshot_tcc()
materialises the needed tcc.* data LOCALLY into the tcc_snapshot.* schema so
later validation runs local-to-local.

Skip-guarded: every live test skips with a clear reason when TCC_BREAKER_RO_PW
is unset OR the host is unreachable (connect attempt fails).  On the build
machine the host IS reachable, so these tests RUN.

The local side uses the pg fixture (conftest.py) -> tcc_fidelity_test with
sql/001_schemas.sql applied (schemas tcc_snapshot + access_meta.tcc_snapshot
+ access_meta.tcc_snapshot_table already exist).
"""
import os

import psycopg
import pytest

from access_harness.snapshot_tcc import host_tcc_conn, snapshot_tcc

# tcc.tmt_frames row count on the governed host (verified live this session).
_EXPECTED_TMT_FRAMES = 42069

_SKIP_REASON = "TCC_BREAKER_RO_PW unset or host unreachable"


# ---------------------------------------------------------------------------
# Availability helper: env var present AND a real connect succeeds.
# ---------------------------------------------------------------------------

def _host_available() -> bool:
    if not os.environ.get("TCC_BREAKER_RO_PW"):
        return False
    try:
        conn = host_tcc_conn()
    except Exception:
        return False
    try:
        conn.close()
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# Helper: seed a minimal extraction_run row and return the run_id.
# ---------------------------------------------------------------------------

def _seed_run(pg_conn, run_id: str = "test-snap-001") -> str:
    """Insert a minimal extraction_run row (idempotent via ON CONFLICT)."""
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


# ---------------------------------------------------------------------------
# test_snapshot_pulls_frames_and_records_provenance
# ---------------------------------------------------------------------------

def test_snapshot_pulls_frames_and_records_provenance(pg):
    """snapshot_tcc materialises tmt_frames locally, records count-only for
    tmt_curves, and writes provenance rows.
    """
    if not _host_available():
        pytest.skip(_SKIP_REASON)

    run_id = _seed_run(pg, "test-snap-frames-001")

    sid = snapshot_tcc(
        pg,
        run_id,
        {
            "tmt_frames": ["id", "breaker_style_id", "size"],
            "tmt_curves": None,  # count-only: do NOT pull 1.14M rows
        },
    )

    assert isinstance(sid, str) and sid, "snapshot_tcc must return a non-empty snapshot_id"

    # ----------------------------------------------------------------
    # tcc_snapshot.tmt_frames materialised locally with the full row count.
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM tcc_snapshot.tmt_frames')
        (local_frames,) = cur.fetchone()
    assert local_frames == _EXPECTED_TMT_FRAMES, (
        f"Expected {_EXPECTED_TMT_FRAMES} rows in tcc_snapshot.tmt_frames, "
        f"got {local_frames}"
    )

    # Only the requested column subset was materialised.
    with pg.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='tcc_snapshot' AND table_name='tmt_frames' "
            "ORDER BY column_name"
        )
        local_cols = {r[0] for r in cur.fetchall()}
    assert local_cols == {"id", "breaker_style_id", "size"}, (
        f"Unexpected materialised columns: {local_cols}"
    )

    # ----------------------------------------------------------------
    # access_meta.tcc_snapshot_table tmt_frames count == 42069.
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT tcc_row_count FROM access_meta.tcc_snapshot_table "
            "WHERE snapshot_id=%s AND table_name=%s",
            (sid, "tmt_frames"),
        )
        row = cur.fetchone()
    assert row is not None, "No tcc_snapshot_table row for tmt_frames"
    assert row[0] == _EXPECTED_TMT_FRAMES, (
        f"Recorded tmt_frames count {row[0]} != {_EXPECTED_TMT_FRAMES}"
    )

    # ----------------------------------------------------------------
    # tmt_curves recorded count-only: a table row exists with a non-zero
    # count, but NO tcc_snapshot.tmt_curves table was created.
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT tcc_row_count FROM access_meta.tcc_snapshot_table "
            "WHERE snapshot_id=%s AND table_name=%s",
            (sid, "tmt_curves"),
        )
        curves_row = cur.fetchone()
    assert curves_row is not None, "No tcc_snapshot_table row for tmt_curves"
    assert curves_row[0] > 0, "tmt_curves count-only should record a positive count"

    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='tcc_snapshot' AND table_name='tmt_curves'"
        )
        (curves_table_exists,) = cur.fetchone()
    assert curves_table_exists == 0, (
        "tmt_curves is count-only -- no tcc_snapshot.tmt_curves table must be created"
    )

    # ----------------------------------------------------------------
    # Provenance row records host / db / role.
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT run_id, host, db_name, role, captured_at "
            "FROM access_meta.tcc_snapshot WHERE snapshot_id=%s",
            (sid,),
        )
        prov = cur.fetchone()
    assert prov is not None, "No access_meta.tcc_snapshot provenance row"
    assert prov[0] == run_id
    assert prov[1] == "100.64.0.1"
    assert prov[2] == "tcc_breaker_viewer_20260625"
    assert prov[3] == "tcc_breaker_ro"
    assert prov[4] is not None, "captured_at must be set"


# ---------------------------------------------------------------------------
# test_host_connection_is_read_only
# ---------------------------------------------------------------------------

def test_host_connection_is_read_only():
    """host_tcc_conn() yields a read-only connection: any write attempt raises.

    The role is SELECT-only on tcc.*; additionally the session is opened
    read-only so even a CREATE TEMP TABLE is rejected.  We assert a write
    raises a psycopg error.
    """
    if not _host_available():
        pytest.skip(_SKIP_REASON)

    conn = host_tcc_conn()
    try:
        with pytest.raises(psycopg.Error):
            with conn.cursor() as cur:
                cur.execute("CREATE TEMP TABLE _harness_write_probe (x int)")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# test_host_tcc_conn_raises_when_password_unset
# ---------------------------------------------------------------------------

def test_host_tcc_conn_raises_when_password_unset(monkeypatch):
    """host_tcc_conn() must raise a clear error when TCC_BREAKER_RO_PW is unset."""
    monkeypatch.delenv("TCC_BREAKER_RO_PW", raising=False)
    with pytest.raises(RuntimeError, match="TCC_BREAKER_RO_PW"):
        host_tcc_conn()
