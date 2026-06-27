"""Tests for access_harness.golden -- HR2 fail-closed golden capture.

These are pure-logic + fake-connection tests.  They MUST NOT open the real
D:\\TCC_NEW.accdb writable (that could mutate the frozen file).  The
"writable connection rejected" factor is exercised with a small FakeConn that
mimics what conn_is_read_only() expects -- never a real writable Access
connection.
"""
import pytest

from access_harness.golden import (
    Query,
    capture_golden,
    conn_is_read_only,
    golden_exec_guard,
    statement_is_single_select,
)


class FakeConn:
    """Minimal stand-in for an Access pyodbc connection.

    Exposes BOTH avenues conn_is_read_only() understands:
      * a `read_only` attribute (the easy, test-facing path), and
      * a getinfo(info_type) method returning 'Y'/'N' for
        SQL_DATA_SOURCE_READ_ONLY -- the same shape a real pyodbc conn returns,
        so the read-only factor is exercised exactly as in production.

    It also supports the capture path used by capture_golden(): a cursor whose
    execute() records the SQL, description yields columns, and fetchall yields
    rows.  No real database is involved.
    """

    def __init__(self, read_only=True, columns=None, rows=None):
        self.read_only = read_only
        self._columns = columns or []
        self._rows = rows or []
        self.executed = []

    # -- read-only reporting (real-pyodbc-shaped) --------------------------
    def getinfo(self, info_type):
        # Mirrors pyodbc.SQL_DATA_SOURCE_READ_ONLY -> 'Y'/'N'.
        return "Y" if self.read_only else "N"

    # -- capture path ------------------------------------------------------
    def cursor(self):
        return _FakeCursor(self)


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self.description = None

    def execute(self, sql):
        self._conn.executed.append(sql)
        self.description = [(c,) for c in self._conn._columns]
        return self

    def fetchall(self):
        return list(self._conn._rows)

    def close(self):
        pass


# ---------------------------------------------------------------------------
# statement_is_single_select
# ---------------------------------------------------------------------------
def test_guard_rejects_action_and_multistatement():
    for sql in (
        "UPDATE t SET x=1",
        "DELETE FROM t",
        "INSERT INTO t VALUES(1)",
        "SELECT * INTO u FROM t",
        "SELECT 1; DROP TABLE t",
    ):
        assert statement_is_single_select(sql) is False


def test_guard_tolerates_one_trailing_semicolon():
    assert statement_is_single_select("SELECT a, b FROM MyQuery;") is True
    assert statement_is_single_select("SELECT a FROM q") is True


# ---------------------------------------------------------------------------
# golden_exec_guard (multi-factor, fail-closed)
# ---------------------------------------------------------------------------
def test_name_not_in_allowlist_rejected_even_if_clean_select():
    ro = FakeConn(read_only=True)
    assert (
        golden_exec_guard(Query("NotListed", "SELECT 1", "SELECT", 0), {"OK"}, ro)
        is False
    )


def test_writable_connection_rejected():
    rw = FakeConn(read_only=False)
    assert golden_exec_guard(Query("OK", "SELECT 1", "SELECT", 0), {"OK"}, rw) is False


def test_nonselect_type_or_params_rejected():
    ro = FakeConn(read_only=True)
    assert golden_exec_guard(Query("OK", "SELECT 1", "ACTION", 0), {"OK"}, ro) is False
    assert golden_exec_guard(Query("OK", "SELECT 1", "SELECT", 1), {"OK"}, ro) is False


def test_clean_allowlisted_parameterless_select_passes():
    ro = FakeConn(read_only=True)
    assert golden_exec_guard(Query("OK", "SELECT 1", "SELECT", 0), {"OK"}, ro) is True


# ---------------------------------------------------------------------------
# conn_is_read_only -- both avenues
# ---------------------------------------------------------------------------
def test_conn_is_read_only_via_attr_and_getinfo():
    assert conn_is_read_only(FakeConn(read_only=True)) is True
    assert conn_is_read_only(FakeConn(read_only=False)) is False


# ---------------------------------------------------------------------------
# capture_golden -- fail-closed before any execution
# ---------------------------------------------------------------------------
def test_capture_golden_raises_when_guard_fails():
    rw = FakeConn(read_only=False)
    with pytest.raises(Exception):
        capture_golden(rw, Query("OK", "SELECT 1", "SELECT", 0), {"OK"})


def test_capture_golden_does_not_execute_when_guard_fails():
    """Fail-closed: a rejected query must NEVER reach the cursor."""
    rw = FakeConn(read_only=False, columns=["a"], rows=[(1,)])
    with pytest.raises(Exception):
        capture_golden(rw, Query("OK", "SELECT 1", "SELECT", 0), {"OK"})
    assert rw.executed == []  # nothing was executed against the connection


def test_capture_golden_returns_result_set_on_pass():
    ro = FakeConn(read_only=True, columns=["a", "b"], rows=[(1, 2), (3, 4)])
    out = capture_golden(ro, Query("OK", "SELECT a, b FROM q", "SELECT", 0), {"OK"})
    assert out["name"] == "OK"
    assert out["columns"] == ["a", "b"]
    assert out["rows"] == [(1, 2), (3, 4)]
    assert out["row_count"] == 2
    assert ro.executed == ["SELECT a, b FROM q"]
