"""Enforce the ban on the broken Access ODBC catalog methods.

This is the load-bearing O4 guarantee: the harness must NEVER call
cursor.columns(), cursor.primaryKeys(), or cursor.foreignKeys() -- they are
broken/unsupported on the Access ODBC driver.  These tests run WITHOUT a
database so the ban is verified on every machine and in CI.

Two independent guards:
  1. SOURCE SCAN (AST) -- parse every .py under access_harness/ with ast.parse
     and walk for an ast.Call whose func is an ast.Attribute named columns /
     primaryKeys / foreignKeys (any receiver).  The AST ignores strings and
     comments entirely, so docstrings that MENTION the names are fine while a
     real call is caught -- and the bare-closing-triple-quote exploit that
     fooled the old string-heuristic scanner cannot hide.  Holds even if a
     future driver stops crashing.
  2. TRAP CURSOR -- drive the metadata functions against a fake cursor whose
     columns()/primaryKeys()/foreignKeys() raise AssertionError('forbidden')
     and assert none of them trip the trap.  (pyodbc.Cursor is an immutable
     C type and cannot be monkeypatched, so the trap lives on the fake; the
     real ban is anchored by the AST source scan above.)
"""
import ast
import pathlib

import pytest

from access_harness import extract

_PKG_DIR = pathlib.Path(extract.__file__).parent

_FORBIDDEN_ATTRS = {"columns", "primaryKeys", "foreignKeys"}


def _scan_source_for_forbidden_calls(path: pathlib.Path) -> list:
    """Return [(lineno, attr)] for every forbidden catalog-method CALL in `path`.

    AST-based and un-foolable: parses the file and walks for an ``ast.Call``
    whose ``func`` is an ``ast.Attribute`` with ``attr`` in the forbidden set
    (any receiver -- ``cur.columns()``, ``self.cur.columns()``, etc.).  Strings
    and comments are not part of the AST, so they can never register as calls.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _FORBIDDEN_ATTRS
        ):
            hits.append((node.func.lineno, node.func.attr))
    return hits


def test_source_scan_no_forbidden_calls():
    """No .py file under access_harness/ CALLS a forbidden catalog method."""
    offenders = []
    for py in sorted(_PKG_DIR.rglob("*.py")):
        for lineno, attr in _scan_source_for_forbidden_calls(py):
            offenders.append(f"{py.name}:{lineno}: .{attr}(")
    assert not offenders, "forbidden catalog-method call(s) found:\n" + "\n".join(
        offenders
    )


def test_ast_scanner_catches_bare_triple_quote_exploit(tmp_path):
    """PROVE the AST scanner catches the shape that fooled the string scanner.

    The old scanner tracked docstrings with string heuristics: a bare closing
    triple-quote on its own line was misread as a docstring OPENER, swallowing
    the next line -- so the forbidden call below slipped through undetected.
    The AST never sees strings/comments, so this call is caught.
    """
    exploit = tmp_path / "exploit.py"
    exploit.write_text(
        'SQL = """\n'
        "q\n"
        '"""\n'
        "cur.columns()\n",
        encoding="utf-8",
    )
    hits = _scan_source_for_forbidden_calls(exploit)
    assert hits, "AST scanner failed to catch the bare-triple-quote exploit"
    assert any(attr == "columns" for _lineno, attr in hits)
    # The call is on the 4th line of the exploit file.
    assert hits[0][0] == 4


def test_ast_scanner_ignores_forbidden_names_in_strings_and_comments(tmp_path):
    """Docstrings/comments may MENTION the names; only real calls are flagged."""
    benign = tmp_path / "benign.py"
    benign.write_text(
        '"""This module never calls cur.columns() or .primaryKeys()."""\n'
        "# foreignKeys() is banned -- see the driver-fact note.\n"
        'NOTE = "do not use cursor.columns() here"\n'
        "x = 1\n",
        encoding="utf-8",
    )
    assert _scan_source_for_forbidden_calls(benign) == []


def test_real_package_tree_passes_the_scan():
    """The shipped access_harness/ tree is clean (extract.py calls none of them)."""
    offenders = []
    for py in sorted(_PKG_DIR.rglob("*.py")):
        offenders.extend(_scan_source_for_forbidden_calls(py))
    assert offenders == []


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
    and a trap on columns/primaryKeys/foreignKeys, so any accidental call raises.
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
