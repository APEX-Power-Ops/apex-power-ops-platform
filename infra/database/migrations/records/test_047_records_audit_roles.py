import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "047_records_audit_roles.sql"
DOWN = "047_records_audit_roles_down.sql"

ROLE_FLAGS = (
    "select rolname, rolsuper, rolbypassrls, rolcanlogin, "
    "rolcreatedb, rolcreaterole, rolreplication "
    "from pg_roles where rolname in ('records_fn_owner','records_auditor') "
    "order by rolname"
)

MEMBERSHIP_EDGES = (
    "select count(*) from pg_auth_members am "
    "where am.roleid in (select oid from pg_roles where rolname in "
    "  ('records_fn_owner','records_auditor')) "
    "   or am.member in (select oid from pg_roles where rolname in "
    "  ('records_fn_owner','records_auditor'))"
)

ROLE_EXISTS = (
    "select count(*) from pg_roles where rolname in "
    "('records_fn_owner','records_auditor')"
)


def _q(dsn, sql):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql).fetchall()


def test_047_applied_then_down_up():
    # Runner contract: 047 is ALREADY applied by the walk. Assert the applied
    # posture, exercise DOWN then UP, and LEAVE 047 applied (do NOT re-apply
    # first, do NOT leave reversed).
    # _dbtest.dsn() reads RECORDS_DEV_DSN (the walk's disposable child DB via
    # _child_env), skips the module loudly if absent, and refuses records_dev.
    dsn = _dbtest.dsn()

    # (1) applied posture: both roles exist, correct login flags, neither
    # super/bypassrls/createdb/createrole/replication, zero membership edges.
    rows = _q(dsn, ROLE_FLAGS)
    assert [r[0] for r in rows] == ["records_auditor", "records_fn_owner"]
    by_name = {r[0]: r for r in rows}
    fn_owner = by_name["records_fn_owner"]
    auditor = by_name["records_auditor"]
    # (rolname, rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, rolreplication)
    assert fn_owner[1:] == (False, False, False, False, False, False)  # NOLOGIN
    assert auditor[1:] == (False, False, True, False, False, False)  # LOGIN
    assert _q(dsn, MEMBERSHIP_EDGES)[0][0] == 0

    # (2) DOWN -> both roles dropped on the disposable DB (records_fn_owner is
    # a fail-loud NOLOGIN pure-owner drop; records_auditor is passwordless/
    # harness-created here, so the DEV-7 guard drops it rather than retaining).
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, ROLE_EXISTS)[0][0] == 0

    # (3) UP -> re-apply 047 and LEAVE it applied.
    _dbtest.run_psql(MIG, dsn)
    rows = _q(dsn, ROLE_FLAGS)
    assert [r[0] for r in rows] == ["records_auditor", "records_fn_owner"]
    by_name = {r[0]: r for r in rows}
    assert by_name["records_fn_owner"][1:] == (False, False, False, False, False, False)
    assert by_name["records_auditor"][1:] == (False, False, True, False, False, False)
    assert _q(dsn, MEMBERSHIP_EDGES)[0][0] == 0
