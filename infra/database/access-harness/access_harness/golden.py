"""access_harness.golden -- HR2 fail-closed "golden" capture (Phase 1).

WHY THIS MODULE IS PARANOID (do not relax without re-deriving)
-------------------------------------------------------------
A "golden" is the Access-side result set of a SAVED Access query, captured so
that Phase 2 can diff it against what the harness rebuilt in access_raw.  The
hazard is that executing a saved Access query can MUTATE the frozen
D:\\TCC_NEW.accdb: Access "queries" are not all SELECTs -- the same .accdb stores
UPDATE / DELETE / INSERT / MAKE-TABLE (SELECT ... INTO) / DDL action queries
under the identical "saved query" surface.  Running one of those, or running a
crafted multi-statement string, against a writable connection would silently
edit the file we are sworn to preserve.

HR2 is therefore OPT-IN and FAIL-CLOSED.  golden_exec_guard() returns True only
when ALL FIVE independent factors agree, and capture_golden() re-invokes the
guard and RAISES (executing nothing) on any failure.  No single check is load-
bearing; defeating the gate requires defeating every factor at once:

  (a) name allow-list   -- only an explicitly enumerated query may even be
                           considered (opt-in; an unknown/new query is rejected).
  (b) ACE-reported type -- the driver's own classification must be 'SELECT'
                           (catches action queries the driver already knows are
                           not selects, without us having to parse them).
  (c) zero parameters   -- a parameterised query is rejected (we capture only
                           deterministic, parameter-free goldens).
  (d) read-only conn    -- the connection handed in must report read-only
                           (SQL_DATA_SOURCE_READ_ONLY == 'Y').  Passing the
                           connection IN (Codex CX3) makes this factor actually
                           checkable rather than assumed.
  (e) single SELECT SQL -- a fail-closed text scan of the SQL itself
                           (statement_is_single_select), independent of what the
                           driver claims, rejecting action verbs, SELECT ... INTO
                           make-table, and any second statement.

statement_is_single_select tolerates exactly ONE optional trailing ';'
(Codex CX4): 'SELECT a FROM q;' is fine, but 'SELECT 1; DROP TABLE t' -- a ';'
followed by more non-whitespace -- is rejected.

Phase 1 only CAPTURES the Access-side result set.  The diff against access_raw is
deferred to Phase 2.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Query value type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    """A saved Access query as reported by the ACE catalog.

    Attributes
    ----------
    name : str
        The saved-query name (the allow-list key).
    sql_text : str
        The query's SQL definition text.
    qtype : str
        The ACE-reported query type, e.g. 'SELECT'.  Compared case-insensitively
        against 'SELECT' by the guard.
    param_count : int
        Number of parameters the query declares.  Must be 0 to be golden-capturable.
    """

    name: str
    sql_text: str
    qtype: str
    param_count: int


# ---------------------------------------------------------------------------
# Factor (e): single-SELECT text scan
# ---------------------------------------------------------------------------

# Action / DDL verbs that, appearing as the leading keyword OR anywhere as a
# whole word in the stripped SQL, disqualify the statement.  EXEC is included so
# a saved query cannot smuggle a stored-procedure call.
_ACTION_VERBS = {
    "UPDATE",
    "DELETE",
    "INSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "EXEC",
    "EXECUTE",
}

# Whole-word matcher (case-insensitive); used for both the action verbs and the
# top-level INTO (make-table) clause.
_WORD_RE = re.compile(r"[A-Za-z_]+")


def _strip_literals_and_comments(sql: str) -> str:
    """Remove string literals and comments so a ';' or 'INTO' inside a quoted
    value or a comment cannot cause a false reject (or, worse, hide a real one).

    Replaces the CONTENTS of '...' and "..." literals with a single space
    (preserving token boundaries), and drops '--' line comments and C-style
    /* ... */ block comments.  This is a conservative lexical pass; it does not
    need to be a full SQL parser because every downstream check is fail-closed.
    """
    out = []
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        # -- single / double quoted string literal --
        if ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if sql[i] == quote:
                    # doubled quote = escaped quote inside the literal
                    if i + 1 < n and sql[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append(" ")  # collapse the whole literal to a boundary space
            continue
        # -- line comment -- ... to end of line --
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] not in ("\n", "\r"):
                i += 1
            out.append(" ")
            continue
        # -- block comment /* ... */ --
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            i += 2
            while i + 1 < n and not (sql[i] == "*" and sql[i + 1] == "/"):
                i += 1
            i += 2
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def statement_is_single_select(sql: str) -> bool:
    """Return True ONLY if `sql` is a single SELECT statement.

    Fail-closed text scan, independent of any driver classification.

    Accepts:
      * exactly one SELECT statement, with at most ONE optional trailing ';'
        ('SELECT a FROM q' and 'SELECT a, b FROM MyQuery;' both pass).

    Rejects (returns False):
      * empty / non-SELECT leading keyword;
      * any action / DDL verb (UPDATE/DELETE/INSERT/DROP/ALTER/CREATE/EXEC) as a
        whole word anywhere in the (literal-stripped) text;
      * a top-level INTO clause (SELECT ... INTO == make-table);
      * any additional statement -- i.e. a ';' followed by more non-whitespace.

    Case-insensitive.  String literals and comments are stripped first so a ';'
    or the word INTO inside a quoted value cannot create a false positive or
    mask a real second statement.
    """
    if sql is None:
        return False

    stripped = _strip_literals_and_comments(sql).strip()
    if not stripped:
        return False

    # Tolerate exactly ONE optional trailing ';' (Codex CX4): drop a single
    # trailing ';' (and any whitespace after it).  Any ';' that is NOT the final
    # non-whitespace character means a second statement follows -> reject.
    core = stripped.rstrip()
    if core.endswith(";"):
        core = core[:-1].rstrip()
    if ";" in core:
        # a remaining ';' implies content after it (we already removed the lone
        # trailing one) -> additional statement -> reject.
        return False
    if not core:
        return False

    # Leading keyword must be SELECT.
    lead = _WORD_RE.match(core)
    if lead is None or lead.group(0).upper() != "SELECT":
        return False

    # No action / DDL verb anywhere as a whole word.
    words = {w.upper() for w in _WORD_RE.findall(core)}
    if words & _ACTION_VERBS:
        return False

    # No top-level INTO (SELECT ... INTO == make-table). INTO as a whole word
    # disqualifies; ordinary SELECTs never contain a bare INTO keyword.
    if "INTO" in words:
        return False

    return True


# ---------------------------------------------------------------------------
# Factor (d): read-only connection detection
# ---------------------------------------------------------------------------

# pyodbc.SQL_DATA_SOURCE_READ_ONLY information-type id (25).  Hard-coded so this
# module does not import pyodbc just to read a constant; a real pyodbc conn is
# still queried via conn.getinfo() at runtime.
_SQL_DATA_SOURCE_READ_ONLY = 25


def conn_is_read_only(conn) -> bool:
    """Return whether an Access connection reports itself read-only.

    Two avenues, in priority order, so this works for BOTH a real pyodbc
    connection and a lightweight fake in tests:

      1. conn.getinfo(SQL_DATA_SOURCE_READ_ONLY) -> 'Y'/'N' (a real pyodbc
         connection; 'Y' means read-only).  This is the authoritative,
         driver-reported signal.
      2. a plain `read_only` boolean attribute -- the convenience path a fake
         object can expose to drive the guard without a live ODBC handle.

    Returns False (fail-closed) if neither avenue yields a definitive answer.
    """
    getinfo = getattr(conn, "getinfo", None)
    if callable(getinfo):
        try:
            val = getinfo(_SQL_DATA_SOURCE_READ_ONLY)
        except Exception:
            val = None
        if val is not None:
            if isinstance(val, str):
                return val.strip().upper() == "Y"
            return bool(val)

    if hasattr(conn, "read_only"):
        return bool(conn.read_only)

    return False  # fail-closed: cannot prove read-only


# ---------------------------------------------------------------------------
# The multi-factor fail-closed gate
# ---------------------------------------------------------------------------


def golden_exec_guard(query: Query, allowlist: set, conn_access) -> bool:
    """Fail-closed gate: True ONLY if ALL five factors agree.

    (a) query.name is in `allowlist`              (opt-in)
    (b) query.qtype.upper() == 'SELECT'           (ACE-reported type)
    (c) query.param_count == 0                     (no parameters)
    (d) conn_is_read_only(conn_access) is True     (connection is read-only)
    (e) statement_is_single_select(query.sql_text) (single-SELECT text scan)

    ANY failing factor -> False.  Passing the connection in (Codex CX3) makes
    factor (d) genuinely checkable instead of assumed.
    """
    if query.name not in allowlist:
        return False
    if str(query.qtype).upper() != "SELECT":
        return False
    if query.param_count != 0:
        return False
    if not conn_is_read_only(conn_access):
        return False
    if not statement_is_single_select(query.sql_text):
        return False
    return True


# ---------------------------------------------------------------------------
# Phase-1 capture (CAPTURE ONLY; diff deferred to Phase 2)
# ---------------------------------------------------------------------------


class GoldenGuardRejected(Exception):
    """Raised by capture_golden when golden_exec_guard rejects the query.

    The query is NOT executed; the frozen .accdb is never touched.
    """


def capture_golden(conn_access, query: Query, allowlist: set) -> dict:
    """Capture the Access-side result set of an allow-listed golden SELECT.

    Re-invokes golden_exec_guard FIRST; on any failure it RAISES
    GoldenGuardRejected WITHOUT executing anything (fail-closed -- nothing is
    ever run against the connection unless every factor passes).

    On pass, executes the SELECT (read-only) and returns:
        {'name', 'columns', 'rows', 'row_count'}
    where `columns` is the ordered column-name list from cursor.description,
    `rows` is the captured rows (as returned by fetchall), and `row_count` is
    len(rows).

    Phase 1 only CAPTURES; the diff vs access_raw is deferred to Phase 2.
    """
    if not golden_exec_guard(query, allowlist, conn_access):
        raise GoldenGuardRejected(
            f"golden_exec_guard rejected query {query.name!r}; not executed "
            f"(fail-closed). The frozen .accdb was not touched."
        )

    cur = conn_access.cursor()
    try:
        cur.execute(query.sql_text)
        columns = [d[0] for d in (cur.description or [])]
        rows = list(cur.fetchall())
    finally:
        cur.close()

    return {
        "name": query.name,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }
