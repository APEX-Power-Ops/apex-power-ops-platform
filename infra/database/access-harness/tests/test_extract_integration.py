"""Integration tests for access_harness.extract against the real Access file.

Skip-guarded: every test skips (with a REASON) when D:\\TCC_NEW.accdb or the
Access ODBC driver / ACE OLE DB provider is unavailable.  On the build machine
the file and providers ARE present, so these tests RUN and PASS -- they never
silently no-op.

Connections are READ-ONLY.
"""
import os

import pytest

from access_harness import extract
from access_harness.typemap import ColumnType

_ACCDB = r"D:\TCC_NEW.accdb"


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


# ---------------------------------------------------------------------------
# Fixtures (module-scoped; skip with a reason when prerequisites are missing).
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def conn():
    if not _accdb_present():
        pytest.skip(f"accdb absent: {_ACCDB} not found")
    if not _odbc_driver_present():
        pytest.skip("Microsoft Access ODBC driver not installed")
    c = extract.connect_data(_ACCDB)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture(scope="module")
def ace_conn():
    if not _accdb_present():
        pytest.skip(f"accdb absent: {_ACCDB} not found")
    if not _ace_present():
        pytest.skip("ACE OLE DB provider / pywin32 not available")
    try:
        c = extract.connect_ace(_ACCDB)
    except Exception as e:  # provider not registered, etc.
        pytest.skip(f"ACE OLE DB open failed: {type(e).__name__}: {e}")
    try:
        yield c
    finally:
        c.Close()


# ---------------------------------------------------------------------------
# Driver-fact documentation: the catalog methods we ban are unsupported.
# ---------------------------------------------------------------------------
def test_catalog_methods_known_broken(conn):
    """Document WHY the catalog methods are banned.

    primaryKeys() and foreignKeys() reliably raise IM001 'Driver does not
    support this' on the Access ODBC driver -- the harness must source that
    metadata via cursor.statistics() and ACE OpenSchema instead.

    columns() is ALSO banned by policy (it raises UnicodeDecodeError on some
    installs); on this machine it happens to succeed, so we assert the
    reliably-broken pair here and rely on test_forbidden_methods.py to enforce
    the no-call ban for all three.
    """
    cur = conn.cursor()
    with pytest.raises(Exception):
        cur.primaryKeys("Breaker_TMTFrameSizes").fetchall()
    cur2 = conn.cursor()
    with pytest.raises(Exception):
        cur2.foreignKeys("Breaker_TMTFrameSizes").fetchall()


# ---------------------------------------------------------------------------
# Working metadata sources.
# ---------------------------------------------------------------------------
def test_list_user_tables_is_79(ace_conn):
    assert len(extract.list_user_tables(ace_conn)) == 79


def test_column_meta_frames_is_26(conn):
    cols = extract.column_meta(conn, "Breaker_TMTFrameSizes")
    assert len(cols) == 26
    assert all(isinstance(c, ColumnType) for c in cols)


def test_primary_key_is_composite(conn):
    assert extract.primary_key(conn, "Breaker_TMTFrameSizes") == [
        "StyleID",
        "FrameDesc",
    ]


def test_unique_indexes_includes_primary_key(conn):
    uniq = extract.unique_indexes(conn, "Breaker_TMTFrameSizes")
    names = {u["name"] for u in uniq}
    assert "PrimaryKey" in names
    pk = next(u for u in uniq if u["name"] == "PrimaryKey")
    assert pk["columns"] == ["StyleID", "FrameDesc"]
    assert pk["is_unique"] is True


def test_saved_queries_total_33(ace_conn):
    queries = extract.saved_queries(ace_conn)
    assert len(queries) == 33
    # Each entry carries name/type/sql_text keys.
    assert all({"name", "type", "sql_text"} <= set(q) for q in queries)


def test_foreign_keys_returns_list(ace_conn):
    # Shape contract: a list of dicts (may be empty for a given table).
    fks = extract.foreign_keys(ace_conn, "Breaker_TMTFrameSizes")
    assert isinstance(fks, list)
    for fk in fks:
        assert {"fk_name", "fk_column", "pk_table", "pk_column", "ordinal"} <= set(fk)


def test_indexes_returns_primary_key_flag(ace_conn):
    idxs = extract.indexes(ace_conn, "Breaker_TMTFrameSizes")
    assert isinstance(idxs, list) and idxs
    assert any(i["is_primary_key"] for i in idxs)


def test_driver_info(conn):
    name, ver = extract.driver_info(conn)
    assert "ACE" in name.upper() or "ODBC" in name.upper()
    assert isinstance(ver, str) and ver


def test_read_rows_streams_tuples(conn):
    it = extract.read_rows(conn, "Breaker_TMTFrameSizes")
    first = next(it)
    assert isinstance(first, tuple)
    # Row width must match the column count from metadata.
    ncols = len(extract.column_meta(conn, "Breaker_TMTFrameSizes"))
    assert len(first) == ncols
