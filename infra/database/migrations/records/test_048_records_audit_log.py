import os
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "048_records_audit_log.sql"
DOWN = "048_records_audit_log_down.sql"

# --- static-catalog probes (run on an autocommit connection) ---------------
FORCED_RLS = (
    "select relforcerowsecurity from pg_class where oid='records.audit_log'::regclass"
)
FN_META = (
    "select pg_get_userbyid(proowner), prosecdef, "
    "  exists (select 1 from unnest(coalesce(proconfig,'{}'::text[])) x "
    "          where x like 'search_path=%') "
    "from pg_proc where oid='records.fn_audit_capture()'::regprocedure"
)
FN_PUBLIC_EXECUTE = (
    "select count(*) from pg_proc p, "
    "  lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
    "where p.oid='records.fn_audit_capture()'::regprocedure "
    "  and a.grantee=0 and a.privilege_type='EXECUTE'"
)
# metadata-minimal: none of these forbidden content columns may exist.
FORBIDDEN_COLS = (
    "select count(*) from information_schema.columns "
    "where table_schema='records' and table_name='audit_log' "
    "  and column_name in ('before_row','after_row','row_hash')"
)
AUDIT_LOG_EXISTS = (
    "select count(*) from pg_class where oid=to_regclass('records.audit_log')"
)
FN_EXISTS = (
    "select count(*) from pg_proc where oid=to_regprocedure('records.fn_audit_capture()')"
)
INS_POLICY_EXISTS = (
    "select count(*) from pg_policies "
    "where schemaname='records' and tablename='audit_log' and policyname='p_audit_log_ins'"
)


def _q(dsn, sql):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql).fetchall()


# Fire the definer path through a REAL trigger. fn_audit_capture is a trigger
# function (TG_OP/TG_ARGV/NEW/OLD) and CANNOT be invoked directly; every capture
# proof uses a temp table + scratch trigger so the definer actually runs.
_PROBE_DDL = (
    "create temp table _g5probe(id int primary key) on commit drop",
    "create trigger _t after insert on _g5probe "
    "for each row execute function records.fn_audit_capture('id')",
)


def test_048_applied_then_down_up():
    # Runner contract: 048 is ALREADY applied by the walk. Assert the applied
    # posture, exercise DOWN then UP, and LEAVE 048 applied (do NOT re-apply
    # first, do NOT leave reversed). dsn() reads RECORDS_DEV_DSN (the walk's
    # disposable child DB), skips loudly if absent, and refuses records_dev.
    dsn = _dbtest.dsn()

    # (1) STATIC POSTURE ----------------------------------------------------
    # audit_log is FORCE-RLS (so its owner records_fn_owner is bound by RLS -
    # otherwise the definer, which runs AS that owner, would bypass the policy).
    assert _q(dsn, FORCED_RLS)[0][0] is True
    # function: owned by records_fn_owner, SECURITY DEFINER, search_path pinned.
    owner, secdef, sp_pinned = _q(dsn, FN_META)[0]
    assert owner == "records_fn_owner"
    assert secdef is True
    assert sp_pinned is True
    # no PUBLIC EXECUTE on the definer entry point.
    assert _q(dsn, FN_PUBLIC_EXECUTE)[0][0] == 0
    # metadata-minimal: no before/after row values, no content hash column.
    assert _q(dsn, FORBIDDEN_COLS)[0][0] == 0

    # (2) POSITIVE (executable definer path) --------------------------------
    # A NON-autocommit connection: the temp table + audit rows live inside one
    # transaction we roll back at the end (leaves zero residue in audit_log).
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            for ddl in _PROBE_DDL:
                cur.execute(ddl)
            cur.execute("insert into _g5probe values (1)")
            # exactly one audit row, captured by the definer running as the
            # table owner; the INSERT policy TO records_fn_owner admits it.
            cur.execute(
                "select action, table_name, row_pk, actor_role, definer_role, "
                "actor_is_superuser, txid "
                "from records.audit_log where table_name='_g5probe'"
            )
            rows = cur.fetchall()
        assert len(rows) == 1
        action, tbl, row_pk, actor_role, definer_role, is_su, txid = rows[0]
        assert action == "insert"
        assert tbl == "_g5probe"
        assert row_pk == "1"
        assert definer_role == "records_fn_owner"
        # actor_role is session_user (the connecting identity, not the definer).
        assert actor_role is not None and actor_role != ""
        assert txid is not None
        pc.rollback()

    # After rollback the probe row is gone (audit_log holds no _g5probe rows).
    assert _q(
        dsn, "select count(*) from records.audit_log where table_name='_g5probe'"
    )[0][0] == 0

    # (3) NEGATIVE CONTROL (savepoint discipline) ---------------------------
    # Prove the landing is the INSERT POLICY, not owner bypass: drop the policy
    # inside a savepoint, re-fire the insert -> RLS rejects it (42501); then
    # rollback to the savepoint (which un-drops the policy). If the policy were
    # a no-op (FORCE missing / owner bypass) the insert would SUCCEED here.
    with psycopg.connect(dsn) as pc:
        with pc.cursor() as cur:
            for ddl in _PROBE_DDL:
                cur.execute(ddl)
            cur.execute("savepoint s")
            cur.execute("drop policy p_audit_log_ins on records.audit_log")
            raised = False
            try:
                cur.execute("insert into _g5probe values (2)")
            except psycopg.errors.InsufficientPrivilege as e:
                raised = True
                # SQLSTATE 42501, message mentions the RLS policy violation.
                assert e.sqlstate == "42501"
                assert "row-level security policy" in str(e)
            assert raised, (
                "negative control FAILED: insert succeeded with the INSERT "
                "policy dropped -> policy is a no-op (FORCE RLS missing or owner "
                "bypass). audit_log admission is NOT policy-gated."
            )
            # the failed statement aborted the transaction; recover to s, which
            # also restores (un-drops) p_audit_log_ins.
            cur.execute("rollback to savepoint s")
        pc.rollback()

    # the policy is back (savepoint rollback un-dropped it; no residue).
    assert _q(dsn, INS_POLICY_EXISTS)[0][0] == 1

    # (4) READ ISOLATION ----------------------------------------------------
    # records_api / records_intake_writer are NOT granted SELECT and have no
    # SELECT policy -> reading audit_log is denied. SET SESSION AUTHORIZATION
    # makes session_user the role (a true identity switch, not SET ROLE).
    for role in ("records_api", "records_intake_writer"):
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(f"set session authorization {role}")
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                c.execute("select count(*) from records.audit_log").fetchone()
    # records_auditor CAN read (USAGE on schema + SELECT grant + SELECT policy).
    with psycopg.connect(dsn, autocommit=True) as c:
        c.execute("set role records_auditor")
        n = c.execute("select count(*) from records.audit_log").fetchone()[0]
        assert n >= 0  # a successful, non-erroring SELECT is the proof
        c.execute("reset role")

    # (5) DOWN -> table + function gone (the walk fingerprint captures both, so
    # this reversal is the reversibility teeth).
    assert _q(dsn, AUDIT_LOG_EXISTS)[0][0] == 1
    assert _q(dsn, FN_EXISTS)[0][0] == 1
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, AUDIT_LOG_EXISTS)[0][0] == 0
    assert _q(dsn, FN_EXISTS)[0][0] == 0

    # (6) UP -> re-apply 048 and LEAVE it applied (fingerprint pre==post).
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, AUDIT_LOG_EXISTS)[0][0] == 1
    assert _q(dsn, FN_EXISTS)[0][0] == 1
    assert _q(dsn, FORCED_RLS)[0][0] is True
    assert _q(dsn, INS_POLICY_EXISTS)[0][0] == 1
