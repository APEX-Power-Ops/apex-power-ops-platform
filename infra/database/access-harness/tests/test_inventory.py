"""Integration tests for access_harness.inventory.populate_meta.

Skip-guarded: every test skips when D:\\TCC_NEW.accdb or the Access
ODBC driver / ACE OLE DB provider is unavailable.

Tests run against tcc_fidelity_test (via the pg fixture from conftest.py).
The Access file is opened READ-ONLY.
"""
import os

import pytest

from access_harness import extract
from access_harness.freeze import FrozenSource, record_extraction_run
from access_harness.inventory import populate_meta

_ACCDB = r"D:\TCC_NEW.accdb"


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------

def _accdb_present() -> bool:
    return os.path.exists(_ACCDB)


def _odbc_driver_present() -> bool:
    try:
        import pyodbc
    except Exception:
        return False
    return any("Microsoft Access Driver" in d for d in pyodbc.drivers())


def _ace_present() -> bool:
    try:
        import win32com.client  # noqa: F401
    except Exception:
        return False
    return True


_SKIP_REASON_ACCDB = f"accdb absent: {_ACCDB} not found"
_SKIP_REASON_ODBC = "Microsoft Access ODBC driver not installed"
_SKIP_REASON_ACE = "ACE OLE DB provider / pywin32 not available"


# ---------------------------------------------------------------------------
# Module-scoped Access fixtures (skip with reason when prerequisites missing)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def data_conn():
    if not _accdb_present():
        pytest.skip(_SKIP_REASON_ACCDB)
    if not _odbc_driver_present():
        pytest.skip(_SKIP_REASON_ODBC)
    c = extract.connect_data(_ACCDB)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture(scope="module")
def ace_conn():
    if not _accdb_present():
        pytest.skip(_SKIP_REASON_ACCDB)
    if not _ace_present():
        pytest.skip(_SKIP_REASON_ACE)
    try:
        c = extract.connect_ace(_ACCDB)
    except Exception as e:
        pytest.skip(f"ACE OLE DB open failed: {type(e).__name__}: {e}")
    try:
        yield c
    finally:
        c.Close()


# ---------------------------------------------------------------------------
# Helper: seed a minimal extraction_run row and return the run_id.
# ---------------------------------------------------------------------------

def _seed_run(pg_conn, run_id: str = "test-inv-001") -> str:
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
# Tests
# ---------------------------------------------------------------------------

def test_populate_meta_records_pk_and_columns_and_states(pg, data_conn, ace_conn):
    """populate_meta writes correct PKs, column counts, and load_state values.

    Uses two real TCC tables:
      - Breaker_TMTFrameSizes: expected 26 columns, PK=['StyleID','FrameDesc']
      - Breaker_TMTFrameAmps: expected to be inventoried_only
    """
    run_id = _seed_run(pg, "test-inv-pk-001")

    all_tables = ["Breaker_TMTFrameSizes", "Breaker_TMTFrameAmps"]
    loaded_tables = {"Breaker_TMTFrameSizes"}

    populate_meta(
        pg_conn=pg,
        data_conn=data_conn,
        ace_conn=ace_conn,
        run_id=run_id,
        all_tables=all_tables,
        loaded_tables=loaded_tables,
    )

    # ----------------------------------------------------------------
    # Verify primary_keys for Breaker_TMTFrameSizes
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT key_columns, coverage_source "
            "FROM access_meta.primary_keys "
            "WHERE run_id = %s AND table_name = %s",
            (run_id, "Breaker_TMTFrameSizes"),
        )
        pk_row = cur.fetchone()

    assert pk_row is not None, "No primary_keys row for Breaker_TMTFrameSizes"
    key_columns, coverage_source = pk_row
    assert key_columns == ["StyleID", "FrameDesc"], (
        f"Unexpected PK columns: {key_columns}"
    )
    assert coverage_source == "cursor.statistics"

    # ----------------------------------------------------------------
    # Verify column count for Breaker_TMTFrameSizes == 26
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM access_meta.columns "
            "WHERE run_id = %s AND table_name = %s",
            (run_id, "Breaker_TMTFrameSizes"),
        )
        (col_count,) = cur.fetchone()

    assert col_count == 26, (
        f"Expected 26 columns for Breaker_TMTFrameSizes, got {col_count}"
    )

    # ----------------------------------------------------------------
    # Verify load_state: FrameSizes='loaded', FrameAmps='inventoried_only'
    # ----------------------------------------------------------------
    with pg.cursor() as cur:
        cur.execute(
            "SELECT table_name, load_state "
            "FROM access_meta.tables "
            "WHERE run_id = %s AND table_name = ANY(%s) "
            "ORDER BY table_name",
            (run_id, ["Breaker_TMTFrameSizes", "Breaker_TMTFrameAmps"]),
        )
        state_rows = {r[0]: r[1] for r in cur.fetchall()}

    assert state_rows.get("Breaker_TMTFrameSizes") == "loaded", (
        f"FrameSizes load_state: {state_rows.get('Breaker_TMTFrameSizes')!r}"
    )
    assert state_rows.get("Breaker_TMTFrameAmps") == "inventoried_only", (
        f"FrameAmps load_state: {state_rows.get('Breaker_TMTFrameAmps')!r}"
    )


def test_populate_meta_is_idempotent(pg, data_conn, ace_conn):
    """Calling populate_meta twice with the same run_id must not duplicate rows."""
    run_id = _seed_run(pg, "test-inv-idem-001")

    all_tables = ["Breaker_TMTFrameSizes"]
    loaded_tables: set = set()

    populate_meta(
        pg_conn=pg,
        data_conn=data_conn,
        ace_conn=ace_conn,
        run_id=run_id,
        all_tables=all_tables,
        loaded_tables=loaded_tables,
    )
    populate_meta(
        pg_conn=pg,
        data_conn=data_conn,
        ace_conn=ace_conn,
        run_id=run_id,
        all_tables=all_tables,
        loaded_tables=loaded_tables,
    )

    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM access_meta.tables "
            "WHERE run_id = %s AND table_name = %s",
            (run_id, "Breaker_TMTFrameSizes"),
        )
        (tbl_count,) = cur.fetchone()

    assert tbl_count == 1, (
        f"Expected exactly 1 row in access_meta.tables after idempotent call, got {tbl_count}"
    )

    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM access_meta.columns "
            "WHERE run_id = %s AND table_name = %s",
            (run_id, "Breaker_TMTFrameSizes"),
        )
        (col_count,) = cur.fetchone()

    assert col_count == 26, (
        f"Expected 26 column rows after idempotent call, got {col_count}"
    )


def test_populate_meta_writes_indexes(pg, data_conn, ace_conn):
    """populate_meta must write at least one index row for Breaker_TMTFrameSizes."""
    run_id = _seed_run(pg, "test-inv-idx-001")

    populate_meta(
        pg_conn=pg,
        data_conn=data_conn,
        ace_conn=ace_conn,
        run_id=run_id,
        all_tables=["Breaker_TMTFrameSizes"],
        loaded_tables=set(),
    )

    with pg.cursor() as cur:
        cur.execute(
            "SELECT index_name, is_unique, coverage_source "
            "FROM access_meta.indexes "
            "WHERE run_id = %s AND table_name = %s",
            (run_id, "Breaker_TMTFrameSizes"),
        )
        idx_rows = cur.fetchall()

    assert idx_rows, "Expected at least one index row for Breaker_TMTFrameSizes"
    names = {r[0] for r in idx_rows}
    assert "PrimaryKey" in names, f"PrimaryKey index not found; got {names}"
    sources = {r[2] for r in idx_rows}
    assert "ace.adSchemaIndexes" in sources


def test_populate_meta_writes_queries(pg, data_conn, ace_conn):
    """populate_meta must write saved query rows (33 expected from TCC_NEW.accdb)."""
    run_id = _seed_run(pg, "test-inv-qry-001")

    # Pass at least one table so the run is valid.
    populate_meta(
        pg_conn=pg,
        data_conn=data_conn,
        ace_conn=ace_conn,
        run_id=run_id,
        all_tables=["Breaker_TMTFrameSizes"],
        loaded_tables=set(),
    )

    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM access_meta.queries WHERE run_id = %s",
            (run_id,),
        )
        (qry_count,) = cur.fetchone()

    assert qry_count == 33, (
        f"Expected 33 saved query rows from TCC_NEW.accdb, got {qry_count}"
    )
