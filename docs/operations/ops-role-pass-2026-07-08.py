#!/usr/bin/env python3
"""Value-silent functional role-boundary proof against the ops database.

Proves BEHAVIOR (not just static grants) of the two ops login roles and the
SECURITY DEFINER elevation path. Every write probe runs inside a transaction
that is ALWAYS rolled back -> zero residue. Nothing about the DSNs
(host/password) is ever printed; only probe id, verdict, and the observed
SQLSTATE class are emitted.

Target DB: each role DSN's dbname is overridden to $OPS_PROOF_DB when set
(roles are cluster-global, so the same credentials authenticate against any DB
the role may CONNECT to). This lets us drive the roles against ops_dev where the
012 boundary is applied, independent of the DSN's own dbname.

Three-way SQLSTATE classification:
  * ACL_DENY   = 42501  (insufficient_privilege) -- the boundary said no.
  * MISSING    = 42P01/3F000/42883/42704 -- object/schema/function absent
                 (a substrate problem, NOT a permission result).
  * REACHED    = ok, or any other error (23xxx not-null/fk, P0001 business
                 raise, ...) -- the ACL let us reach the object body.
An "allowed" probe PASSES on REACHED; a "denied" probe PASSES on ACL_DENY.
Any MISSING is a distinct FAIL (schema not present on the target DB).
"""
import os
import sys
import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

WRITER = os.environ.get("OPS_INTAKE_WRITER_DSN")
API = os.environ.get("OPS_API_DSN")
TARGET = os.environ.get("OPS_PROOF_DB")  # e.g. ops_dev

missing = [n for n, v in (("OPS_INTAKE_WRITER_DSN", WRITER), ("OPS_API_DSN", API)) if not v]
if missing:
    print("SETUP_FAIL missing:" + ",".join(missing))
    sys.exit(3)

ACL_DENY = {"42501"}
MISSING = {"42P01", "3F000", "42883", "42704"}


def retarget(dsn, db):
    if not db:
        return dsn
    d = conninfo_to_dict(dsn)
    d["dbname"] = db
    return make_conninfo(**d)  # contains password; never printed


def klass(state):
    if state in ACL_DENY:
        return "ACL_DENY"
    if state in MISSING:
        return "MISSING"
    return "REACHED"  # any other error class -> reached object body


def probe(dsn, sql, params=None):
    """Run one statement in an always-rolled-back tx.
    Returns 'REACHED' | 'ACL_DENY' | 'MISSING' | 'CONNECT_ERR:<state>'."""
    try:
        conn = psycopg.connect(dsn, connect_timeout=10)
    except psycopg.Error as e:
        return "CONNECT_ERR:" + str(e.sqlstate)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '10s'")
            cur.execute(sql, params or ())
            try:
                cur.fetchone()
            except psycopg.ProgrammingError:
                pass  # no result set (e.g. INSERT)
        return "REACHED"
    except psycopg.Error as e:
        return klass(e.sqlstate)
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


def whoami(dsn):
    try:
        conn = psycopg.connect(dsn, connect_timeout=10)
    except psycopg.Error as e:
        return "connect_err:" + str(e.sqlstate)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user || '@' || current_database()")
            return cur.fetchone()[0]
    finally:
        conn.rollback()
        conn.close()


def catbool(dsn, expr):
    """Evaluate a boolean catalog-privilege expression as the connected role
    (exact oracle: has_*_privilege, not a collapsed error class). Read-only."""
    conn = psycopg.connect(dsn, connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT " + expr)
            return cur.fetchone()[0]
    finally:
        conn.rollback()
        conn.close()


W = retarget(WRITER, TARGET)
A = retarget(API, TARGET)
rows = []


def rec(pid, desc, expect, observed, ok):
    rows.append((pid, desc, expect, observed, "PASS" if ok else "FAIL"))


# Identity binding (+ which DB we actually proved against)
wu = whoami(W)
rec("I0", "writer DSN binds ops_intake_writer@<target>", "ops_intake_writer@" + (TARGET or "?"),
    wu, wu == "ops_intake_writer@" + (TARGET or wu.split("@")[-1]))
au = whoami(A)
rec("I1", "api DSN binds ops_api@<target>", "ops_api@" + (TARGET or "?"),
    au, au == "ops_api@" + (TARGET or au.split("@")[-1]))

ATTEST = "SELECT ops.attest_apparatus_complete(gen_random_uuid(), gen_random_uuid(), %s)"

# Writer path
r = probe(W, "INSERT INTO ops.intake_runs DEFAULT VALUES")
rec("W1", "writer CAN write intake surface (ops.intake_runs)", "REACHED", r, r == "REACHED")
r = probe(W, "INSERT INTO ops.revenue_recognition_event DEFAULT VALUES")
rec("W2", "writer CANNOT write recognition table directly", "ACL_DENY", r, r == "ACL_DENY")
r = probe(W, ATTEST, ("role-proof",))
rec("W3", "writer CANNOT invoke recognition SECDEF fn", "ACL_DENY", r, r == "ACL_DENY")

# API path
r = probe(A, "SELECT count(*) FROM ops.v_completion_recognition_worklist")
rec("A1", "api CAN read its recognition view", "REACHED", r, r == "REACHED")
r = probe(A, "SELECT 1 FROM ops.projects LIMIT 1")
rec("A2", "api CANNOT read out-of-scope table (ops.projects)", "ACL_DENY", r, r == "ACL_DENY")
r = probe(A, "INSERT INTO ops.revenue_recognition_event DEFAULT VALUES")
rec("A3", "api CANNOT write recognition table directly", "ACL_DENY", r, r == "ACL_DENY")
r = probe(A, ATTEST, ("role-proof",))
rec("A4", "api CAN invoke SECDEF fn (EXECUTE + reached body)", "REACHED", r, r == "REACHED")

# --- Catalog-exact privilege oracle (independent of the behavioral SQLSTATE) ---
# Answers "42501 is too broad": each C-probe tests ONE exact privilege via
# has_*_privilege as the connected role, so behavior and catalog must agree.
SIG = "'ops.attest_apparatus_complete(uuid,uuid,text)'"
cat = [
    ("C1", "writer USAGE on schema ops", W, "has_schema_privilege('ops','USAGE')", True),
    ("C2", "writer INSERT on ops.intake_runs", W, "has_table_privilege('ops.intake_runs','INSERT')", True),
    ("C3", "writer INSERT on ops.revenue_recognition_event", W, "has_table_privilege('ops.revenue_recognition_event','INSERT')", False),
    ("C4", "writer EXECUTE on recognition fn", W, "has_function_privilege(" + SIG + ",'EXECUTE')", False),
    ("C5", "api USAGE on schema ops", A, "has_schema_privilege('ops','USAGE')", True),
    ("C6", "api SELECT on recognition worklist view", A, "has_table_privilege('ops.v_completion_recognition_worklist','SELECT')", True),
    ("C7", "api SELECT on ops.projects (out of scope)", A, "has_table_privilege('ops.projects','SELECT')", False),
    ("C8", "api INSERT on ops.revenue_recognition_event", A, "has_table_privilege('ops.revenue_recognition_event','INSERT')", False),
    ("C9", "api EXECUTE on recognition fn", A, "has_function_privilege(" + SIG + ",'EXECUTE')", True),
]
for pid, desc, dsn, expr, want in cat:
    try:
        got = catbool(dsn, expr)
    except psycopg.Error as e:
        got = "ERR:" + str(e.sqlstate)
    rec(pid, desc, str(want), str(got), isinstance(got, bool) and got == want)

width = max(len(x[1]) for x in rows)
allpass = all(x[4] == "PASS" for x in rows)
print("target_db=%s" % (TARGET or "<dsn-default>"))
print("PROBE | %-*s | expect   | observed          | verdict" % (width, "assertion"))
for pid, desc, expect, observed, verdict in rows:
    print("%-5s | %-*s | %-8s | %-17s | %s" % (pid, width, desc, expect, observed, verdict))
print("RESIDUE: rolled-back (every write probe rolled back)")
print("OVERALL: %s" % ("PASS" if allpass else "FAIL"))
sys.exit(0 if allpass else 1)
