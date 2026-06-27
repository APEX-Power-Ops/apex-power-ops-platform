"""Enforce the ban on the broken Access ODBC catalog methods.

This is the load-bearing O4 guarantee: the harness must NEVER call
cursor.columns(), cursor.primaryKeys(), or cursor.foreignKeys() -- they are
broken/unsupported on the Access ODBC driver.  These tests run WITHOUT a
database so the ban is verified on every machine and in CI.

Two independent guards:
  1. SOURCE SCAN -- no .py under access_harness/ has a non-comment line that
     CALLS one of the forbidden methods.  Holds even if a future driver
     stops crashing.
  2. TRAP CURSOR -- drive the metadata functions against a fake cursor whose
     columns()/primaryKeys()/foreignKeys() raise AssertionError('forbidden')
     and assert none of them trip the trap.  (pyodbc.Cursor is an immutable
     C type and cannot be monkeypatched, so the trap lives on the fake; the
     real ban is anchored by the source scan above.)
"""
import pathlib
import re

import pytest

from access_harness import extract

_PKG_DIR = pathlib.Path(extract.__file__).parent

# Forbidden method-call patterns.  We match ".name(" so that an attribute
# access like `cursor.columns(` is caught, while string mentions inside
# comments/docstrings are stripped out before matching.
_FORBIDDEN_CALL = re.compile(r"\.(columns|primaryKeys|foreignKeys)\s*\(")


def _strip_comments_and_strings(line: str) -> str:
    """Best-effort removal of #-comments and quoted string contents.

    Docstrings and comments are allowed to MENTION the forbidden names (this
    module's own extract.py documents them).  We only want to flag real calls,
    so we blank out the contents of quotes and drop everything after a #.
    """
    # Drop inline comment.
    hash_idx = line.find("#")
    if hash_idx != -1:
        line = line[:hash_idx]
    # Blank out single- and double-quoted string contents.
    line = re.sub(r"'[^']*'", "''", line)
    line = re.sub(r'"[^"]*"', '""', line)
    return line


def test_source_scan_no_forbidden_calls():
    """No .py file under access_harness/ CALLS a forbidden catalog method."""
    offenders = []
    for py in sorted(_PKG_DIR.rglob("*.py")):
        text = py.read_text(encoding="utf-8")
        in_docstring = False
        doc_delim = None
        for lineno, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            # Track triple-quoted docstring/comment blocks and skip them.
            if in_docstring:
                if doc_delim in stripped:
                    in_docstring = False
                continue
            for delim in ('"""', "'''"):
                if stripped.startswith(delim) and stripped.count(delim) == 1:
                    in_docstring = True
                    doc_delim = delim
                    break
            if in_docstring:
                continue
            code = _strip_comments_and_strings(raw)
            if _FORBIDDEN_CALL.search(code):
                offenders.append(f"{py.name}:{lineno}: {raw.strip()}")
    assert not offenders, "forbidden catalog-method call(s) found:\n" + "\n".join(
        offenders
    )


# ---------------------------------------------------------------------------
# Monkeypatch trap fakes
# ---------------------------------------------------------------------------
class _TrapError(AssertionError):
    pass


def _forbidden(*_a, **_k):
    raise _TrapError("forbidden")


class _FakeCursor:
    """Minimal stand-in for pyodbc.Cursor exercised by the metadata functions.

    Provides description/statistics/execute/fetchone -- the WORKING surfaces --
    and inherits the forbidden columns/primaryKeys/foreignKeys from the
    monkeypatched pyodbc.Cursor via the trap, so any accidental call raises.
    """

    def __init__(self, description, stat_rows):
        self._description = description
        self._stat_rows = stat_rows

    # WORKING surfaces -------------------------------------------------------
    def execute(self, _sql, *_a):
        return self

    @property
    def description(self):
        return self._description

    def statistics(self, *_a, **_k):
        return _FakeFetch(self._stat_rows)

    def fetchone(self):
        return None

    def close(self):
        pass

    # FORBIDDEN surfaces -- routed to the trap so a call fails the test.
    columns = _forbidden
    primaryKeys = _forbidden
    foreignKeys = _forbidden


class _FakeFetch:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def _stat_row(non_unique, index_name, ordinal, column):
    """Build a 13-wide statistics() row matching pyodbc's column order."""
    row = [None] * 13
    row[3] = non_unique
    row[5] = index_name
    row[6] = 3  # type (non-TABLE_STAT)
    row[7] = ordinal
    row[8] = column
    return tuple(row)


def test_column_meta_does_not_call_forbidden():
    desc = [
        ("ID", int, None, 10, 10, 0, False),
        ("StyleID", int, None, 10, 10, 0, True),
        ("FrameDesc", str, None, 255, 0, 0, True),
    ]
    conn = _FakeConn(_FakeCursor(desc, []))
    cols = extract.column_meta(conn, "Breaker_TMTFrameSizes")
    assert len(cols) == 3
    assert [c.access_type for c in cols] == [str(int), str(int), str(str)]


def test_primary_key_does_not_call_forbidden():
    stat = [
        _stat_row(0, "PrimaryKey", 1, "StyleID"),
        _stat_row(0, "PrimaryKey", 2, "FrameDesc"),
        _stat_row(1, "Ordinal", 1, "StyleID"),
    ]
    conn = _FakeConn(_FakeCursor([], stat))
    assert extract.primary_key(conn, "Breaker_TMTFrameSizes") == [
        "StyleID",
        "FrameDesc",
    ]


def test_unique_indexes_does_not_call_forbidden():
    stat = [
        _stat_row(0, "PrimaryKey", 1, "StyleID"),
        _stat_row(0, "PrimaryKey", 2, "FrameDesc"),
        _stat_row(1, "NonUniqueIdx", 1, "FrameSize"),
        (None,) * 13,  # SQL_TABLE_STAT marker -- must be skipped
    ]
    conn = _FakeConn(_FakeCursor([], stat))
    uniq = extract.unique_indexes(conn, "Breaker_TMTFrameSizes")
    assert len(uniq) == 1
    assert uniq[0]["name"] == "PrimaryKey"
    assert uniq[0]["columns"] == ["StyleID", "FrameDesc"]
    assert uniq[0]["is_unique"] is True


def test_calling_a_forbidden_method_actually_trips_the_trap():
    """Sanity: the trap really does fire if a forbidden method is called."""
    cur = _FakeCursor([], [])
    with pytest.raises(AssertionError):
        cur.columns(table="x")
    with pytest.raises(AssertionError):
        cur.primaryKeys("x")
    with pytest.raises(AssertionError):
        cur.foreignKeys("x")
