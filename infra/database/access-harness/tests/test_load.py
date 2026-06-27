"""Tests for access_harness.load.

All tests use the pg fixture (conftest.py), which connects to tcc_fidelity_test
and applies 001_schemas.sql (so access_raw/access_meta schemas exist).

No Access .accdb file is needed -- rows are synthetic in-memory tuples.

The pg fixture provides a connection with autocommit=True.  load_table requires
autocommit=False, so each test creates an extra connection via psycopg.connect
with the default (autocommit=False) for the load path.  The pg fixture
connection is used only for setup (inserting extraction_run rows) and for
post-test queries.
"""
import psycopg
import pytest

from access_harness.config import test_pg_dsn
from access_harness.load import (
    ADVISORY_LOCK_KEY,
    create_access_raw_table,
    load_table,
    single_writer,
)
from access_harness.typemap import ColumnType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, pg_type: str = "text", nullable: bool = True) -> ColumnType:
    """Build a minimal ColumnType with the given name and pg_type."""
    return ColumnType(
        access_type="<class 'str'>",
        pg_type=pg_type,
        nullable=nullable,
        size=None,
        precision=None,
        round_trippable=True,
        name=name,
    )


def _insert_run(conn, run_id: str = "test-run-001") -> str:
    """Insert a minimal extraction_run row so access_meta.tables FK passes."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.extraction_run
                (run_id, source_path, frozen_copy_path, source_size,
                 source_mtime_utc, source_sha256, extracted_at_utc,
                 driver_name, dbms_version, read_only, harness_version)
            VALUES
                (%s, '/tmp/test.accdb', '/tmp/frozen.accdb', 0,
                 now(), 'deadbeef', now(),
                 'TEST', '0.0.0', TRUE, '0.1.0')
            ON CONFLICT (run_id) DO NOTHING
            """,
            (run_id,),
        )
    return run_id


def _open_load_conn() -> psycopg.Connection:
    """Open a second psycopg connection with autocommit=False for load_table."""
    return psycopg.connect(test_pg_dsn(), autocommit=False)


# ---------------------------------------------------------------------------
# test_load_is_idempotent_not_doubled
# ---------------------------------------------------------------------------

def test_load_is_idempotent_not_doubled(pg):
    """load_table called twice with 3 rows must yield count==3 both times.

    The access_raw table must have exactly 3 rows after the second call, not 6,
    because TRUNCATE before each load prevents doubling.
    """
    run_id = _insert_run(pg, "run-idem-001")
    col_types = [_make_col("id", "integer"), _make_col("label", "text")]
    rows = [(1, "alpha"), (2, "beta"), (3, "gamma")]

    lconn = _open_load_conn()
    try:
        count1 = load_table(lconn, "Idempotent Table", col_types, rows, run_id)
        assert count1 == 3

        count2 = load_table(lconn, "Idempotent Table", col_types, rows, run_id)
        assert count2 == 3
    finally:
        lconn.close()

    # Verify actual row count in the staging table
    with pg.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM access_raw."Idempotent Table"')
        (db_count,) = cur.fetchone()
    assert db_count == 3, f"Expected 3 rows, got {db_count}"

    # Verify access_meta.tables reflects the final load
    with pg.cursor() as cur:
        cur.execute(
            "SELECT load_state, staging_row_count FROM access_meta.tables "
            "WHERE run_id=%s AND table_name=%s",
            (run_id, "Idempotent Table"),
        )
        row = cur.fetchone()
    assert row is not None
    assert row[0] == "loaded"
    assert row[1] == 3


# ---------------------------------------------------------------------------
# test_failure_sets_load_state_failed_and_no_partial
# ---------------------------------------------------------------------------

def test_failure_sets_load_state_failed_and_no_partial(pg):
    """A rows iterable that raises mid-iteration must leave load_state='failed'
    and zero committed rows in access_raw (transaction rolled back).
    """
    run_id = _insert_run(pg, "run-fail-001")
    col_types = [_make_col("val", "text")]

    def bad_rows():
        yield ("good row",)
        raise RuntimeError("simulated extraction failure")

    lconn = _open_load_conn()
    try:
        with pytest.raises(RuntimeError, match="simulated extraction failure"):
            load_table(lconn, "Failing Table", col_types, bad_rows(), run_id)
    finally:
        lconn.close()

    # load_state must be 'failed'
    with pg.cursor() as cur:
        cur.execute(
            "SELECT load_state FROM access_meta.tables "
            "WHERE run_id=%s AND table_name=%s",
            (run_id, "Failing Table"),
        )
        row = cur.fetchone()
    assert row is not None, "access_meta.tables row not found"
    assert row[0] == "failed", f"Expected 'failed', got {row[0]!r}"

    # access_raw table was rolled back -- either does not exist or has 0 rows
    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='access_raw' AND table_name='Failing Table'"
        )
        (exists,) = cur.fetchone()

    if exists:
        with pg.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM access_raw."Failing Table"')
            (raw_count,) = cur.fetchone()
        assert raw_count == 0, f"Rolled-back table must have 0 rows, got {raw_count}"


# ---------------------------------------------------------------------------
# test_single_writer_blocks_second_acquire
# ---------------------------------------------------------------------------

def test_single_writer_blocks_second_acquire(pg):
    """While single_writer holds the advisory lock on conn1, a second connection
    must not be able to acquire the same lock (pg_try_advisory_xact_lock returns
    False).
    """
    # conn1 will hold the advisory lock inside single_writer
    conn1 = _open_load_conn()
    # conn2 will attempt a non-blocking try-acquire
    conn2 = _open_load_conn()
    try:
        # Start a transaction on conn1 and acquire the lock
        with conn1.cursor() as cur1:
            # Begin explicit transaction (autocommit is False so a transaction
            # starts implicitly, but we force it with a BEGIN to be explicit)
            cur1.execute("BEGIN")

        with single_writer(conn1):
            # Now conn1 holds pg_advisory_xact_lock(ADVISORY_LOCK_KEY).
            # conn2 must not be able to get it.
            with conn2.cursor() as cur2:
                cur2.execute(
                    "SELECT pg_try_advisory_xact_lock(%s)",
                    (ADVISORY_LOCK_KEY,),
                )
                (acquired,) = cur2.fetchone()

            assert acquired is False, (
                "pg_try_advisory_xact_lock must return False while "
                "conn1 holds the lock, but got True"
            )

        conn1.commit()
    finally:
        try:
            conn1.rollback()
        except Exception:
            pass
        try:
            conn2.rollback()
        except Exception:
            pass
        conn1.close()
        conn2.close()


# ---------------------------------------------------------------------------
# test_create_access_raw_table_quotes_weird_names
# ---------------------------------------------------------------------------

def test_create_access_raw_table_quotes_weird_names(pg):
    """Table name and column name containing spaces must be created without
    error and must be discoverable in information_schema.columns.
    """
    weird_table = "My Weird Table"
    col_types = [
        _make_col("id col", "integer"),
        _make_col("label col", "text"),
    ]

    # create_access_raw_table commits its own DDL when conn is autocommit=True
    # (the pg fixture uses autocommit=True, so we can call it directly).
    create_access_raw_table(pg, weird_table, col_types)

    # Verify the table exists in information_schema
    with pg.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='access_raw' AND table_name=%s",
            (weird_table,),
        )
        (tbl_count,) = cur.fetchone()
    assert tbl_count == 1, f"Table '{weird_table}' not found in information_schema"

    # Verify the columns exist
    with pg.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='access_raw' AND table_name=%s "
            "ORDER BY ordinal_position",
            (weird_table,),
        )
        cols = [r[0] for r in cur.fetchall()]
    assert "id col" in cols, f"'id col' not found; got {cols}"
    assert "label col" in cols, f"'label col' not found; got {cols}"
