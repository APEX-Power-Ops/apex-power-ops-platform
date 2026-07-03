import os
import sys

import psycopg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "046_records_ownership.sql"
DOWN = "046_records_ownership_down.sql"

# Ownership counted across ALL THREE catalogs (pg_class + pg_proc + pg_namespace)
# so functions (fn_set_updated_at) and the records schema itself are covered,
# not tables alone. The three %s slots are the expected owner role name.
OWNED_NE = (
    "select "
    "(select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
    " where ns.nspname='records' and c.relkind in ('r','v','m','S') "
    "   and pg_get_userbyid(c.relowner) <> '%s') "
    "+ (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace "
    "   where ns.nspname='records' and pg_get_userbyid(p.proowner) <> '%s') "
    "+ (select case when pg_get_userbyid(nspowner) <> '%s' then 1 else 0 end "
    "   from pg_namespace where nspname='records')"
)

def _q(dsn, sql):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql).fetchall()

def test_046_applied_then_down_up():
    # Runner contract: 046 is ALREADY applied by the walk. Assert the applied
    # posture, exercise DOWN then UP, and LEAVE 046 applied (do NOT re-apply
    # first, do NOT leave reversed).
    # _dbtest.dsn() reads RECORDS_DEV_DSN (the walk's disposable child DB via
    # _child_env), skips the module loudly if absent, and refuses records_dev.
    dsn = _dbtest.dsn()
    # (1) applied posture: everything records_owner-owned across all catalogs
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
    assert _q(dsn, "select rolsuper, rolbypassrls, rolcanlogin "
                   "from pg_roles where rolname='records_owner'")[0] == (False, False, False)
    assert _q(dsn, "select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
                   "where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity")[0][0] == 0
    # FORCE teeth: the owner is bound by RLS. SET SESSION AUTHORIZATION makes
    # session_user the role (SET ROLE would leave session_user=postgres).
    with psycopg.connect(dsn, autocommit=True) as c:
        base = c.execute("select count(*) from records.neta_tables").fetchone()[0]
        assert base > 0
        c.execute("set session authorization records_owner")
        assert c.execute("select count(*) from records.neta_tables").fetchone()[0] == 0
        c.execute("reset session authorization")
        c.execute("set session authorization records_api")
        assert c.execute("select count(*) from records.neta_tables").fetchone()[0] == base
        c.execute("reset session authorization")
    # (2) DOWN -> reversed to the postgres pre-state (all catalogs) + role dropped
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, OWNED_NE % ("postgres", "postgres", "postgres"))[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_owner'")[0][0] == 0
    # (3) UP -> re-apply 046 and LEAVE it applied
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
