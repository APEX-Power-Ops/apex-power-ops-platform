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
# audit_log owner (must be records_fn_owner after the cross-role transfer).
AUDIT_LOG_OWNER = (
    "select pg_get_userbyid(relowner) from pg_class where oid='records.audit_log'::regclass"
)
# records_fn_owner EXACT ALLOWLIST residue: the ONLY permitted pg_shdepend 'a' edge is
# USAGE on schema records in THIS db. The transient CREATE-on-schema grant taken during
# the cross-role transfer must be revoked -> this stays 0 (mirrors 048 assert :142-148).
FN_OWNER_ACL_ALLOWLIST_RESIDUE = (
    "select count(*) from pg_shdepend s join pg_roles r on r.oid=s.refobjid "
    "where r.rolname='records_fn_owner' and s.deptype='a' "
    "  and not (s.classid='pg_namespace'::regclass "
    "           and s.dbid=(select oid from pg_database where datname=current_database()) "
    "           and s.objid=(select oid from pg_namespace where nspname='records'))"
)
# fn_owner must NOT hold CREATE on schema records at rest (transient CREATE revoked).
FN_OWNER_HAS_CREATE = (
    "select has_schema_privilege('records_fn_owner','records','CREATE')"
)
# temp-authority residue (046 [4] form): no NON-admin role holds a USABLE
# (set/inherit) membership INTO records_owner or records_fn_owner (postgres EXEMPT).
TEMP_AUTHORITY_RESIDUE = (
    "select count(*) from pg_auth_members am "
    "join pg_roles ow on ow.oid=am.roleid and ow.rolname in ('records_owner','records_fn_owner') "
    "join pg_roles m on m.oid=am.member "
    "where (am.set_option or am.inherit_option) and m.oid <> 'postgres'::regrole"
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


# --------------------------------------------------------------------------------------
# SUPABASE-COMPAT green-proof (Task 2.4). Self-driving on RECORDS_PG_ADMIN_DSN: it builds a
# disposable DB, applies 001-044 + adapted 045 + 046 + 047 + 048 through the NON-super
# applier, and asserts the adapted 048 SUCCEEDS with the applied posture: audit_log +
# fn_audit_capture owned by records_fn_owner, audit_log FORCE-RLS, fn_audit_capture
# SECURITY DEFINER with no PUBLIC EXECUTE, the exact-allowlist residue clean (fn_owner
# holds EXACTLY USAGE on schema records - the transient CREATE taken for the cross-role
# transfer is revoked; fn_owner does NOT hold CREATE), and the temp-authority residue
# clean (no usable non-admin membership into an owner role). It then ALSO drives the WHOLE
# committed 048_records_audit_log_down.sql through the SAME non-super applier and asserts
# the objects are dropped + the roles retained. This is the green mirror of
# test_supabase_compat_redproof.py; 048's compat proof exercises the FULL cross-role
# create-in-schema + transfer choreography locally, because by 048 the records schema is
# records_owner-owned even locally (unlike 046's FRESH applier-owned case) - a stronger
# local proof. It is a LOCAL APPROXIMATION (a real Supabase branch is the fidelity
# authority, Phase 3).
# --------------------------------------------------------------------------------------
import run_validation as rv  # noqa: E402

_ADMIN = os.environ.get("RECORDS_PG_ADMIN_DSN")

compat = pytest.mark.skipif(
    not _ADMIN, reason="RECORDS_PG_ADMIN_DSN not set - non-super compat green-proof skipped"
)

# Cluster-level roles the compat proof may leave behind (aborted prior run). Drop the
# password-less, orphaned set before/after each module run so the proof is idempotent;
# password-carrying roles are LEFT IN PLACE (DEV-7 safety).
_DISPOSABLE_ROLES = (
    "records_api", "records_intake_writer", "records_owner", "records_reclaim_owner",
    "records_fn_owner", "records_auditor",
)


def _drop_disposable_roles():
    with psycopg.connect(_ADMIN, autocommit=True) as c:
        for role in _DISPOSABLE_ROLES:
            if not c.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                continue
            haspw = c.execute(
                "select rolpassword is not null from pg_authid where rolname=%s", (role,)
            ).fetchone()[0]
            if haspw:
                continue  # out-of-band password: never drop (DEV-7 discipline)
            try:
                c.execute(f'drop owned by "{role}"')
                c.execute(f'drop role "{role}"')
            except psycopg.errors.DependentObjectsStillExist:
                pass  # cross-DB dependency: leave in place


@pytest.fixture(scope="module")
def compat_child():
    """Disposable DB with 001-044 + adapted 045/046/047/048 applied AS the non-super
    applier; yields (admin_child_dsn, applier_apply_dsn): the ADMIN child DSN for catalog
    introspection, and the non-super APPLIER's own apply DSN so a test can drive further
    SQL (e.g. 048_down) through the SAME non-super identity that applied 048 UP - the
    identity whose transient owner-role memberships are exactly what Task 2.4's cross-role
    choreography establishes and revokes. The fixture succeeding IS the green proof that
    adapted 048 applies under the non-super applier. Value-silent."""
    if not _ADMIN:
        pytest.skip("RECORDS_PG_ADMIN_DSN not set")
    rv.check_admin_dsn(_ADMIN)
    _drop_disposable_roles()  # clean any orphaned cluster-level roles before applying
    val = rv.make_val_name()
    rv.assert_val_name(val)
    applier = rv.make_local_applier(_ADMIN, rv.LOCAL_APPLIER_ENVELOPE)
    rv.assert_applier_name(applier.role)
    with psycopg.connect(_ADMIN, autocommit=True) as c:
        c.execute(f'create database "{val}"')
    try:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(applier.create_sql)
            c.execute(f'grant create on database "{val}" to "{applier.role}"')
        apply_dsn = rv.derive_child_dsn(applier.dsn, val)
        migs, _ = rv.enumerate_stack(rv.HERE)
        for num, fname in migs:
            if num > 48:
                break
            rv._apply_as_applier(fname, apply_dsn)  # 001-044, adapted 045/046/047/048; each succeeds
        yield rv.derive_child_dsn(_ADMIN, val), apply_dsn
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_048_applies_under_non_super(compat_child):
    # Reaching here means adapted 048 applied AS the non-super applier without raising -
    # the full create-in-schema + cross-role ownership transfer + owner-only DDL under the
    # non-super applier is green.
    admin_dsn, apply_dsn = compat_child
    assert admin_dsn and apply_dsn


@compat
def test_compat_audit_objects_owned_by_fn_owner(compat_child):
    # audit_log + fn_audit_capture must both be owned by records_fn_owner (the cross-role
    # transfer AS records_owner, holding WITH SET in records_fn_owner, landed).
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(AUDIT_LOG_OWNER).fetchone()[0] == "records_fn_owner", \
            "audit_log must be owned by records_fn_owner after the cross-role transfer"
        owner, secdef, sp_pinned = c.execute(FN_META).fetchone()
        assert owner == "records_fn_owner", "fn_audit_capture must be owned by records_fn_owner"
        assert secdef is True, "fn_audit_capture must be SECURITY DEFINER"
        assert sp_pinned is True, "fn_audit_capture search_path must be pinned"


@compat
def test_compat_audit_log_force_rls_and_no_public_execute(compat_child):
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(FORCED_RLS).fetchone()[0] is True, "audit_log must be FORCE-RLS"
        assert c.execute(FN_PUBLIC_EXECUTE).fetchone()[0] == 0, \
            "fn_audit_capture must have no PUBLIC EXECUTE"


@compat
def test_compat_fn_owner_exact_allowlist_and_no_create(compat_child):
    # invariant-8 residue + exact allowlist (048 :137-148): fn_owner holds EXACTLY USAGE on
    # schema records and NO CREATE - the transient CREATE taken for the cross-role transfer
    # was revoked before commit.
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(FN_OWNER_ACL_ALLOWLIST_RESIDUE).fetchone()[0] == 0, \
            "records_fn_owner holds an ACL edge beyond USAGE on schema records (transient CREATE leaked?)"
        assert c.execute(FN_OWNER_HAS_CREATE).fetchone()[0] is False, \
            "records_fn_owner must NOT hold CREATE on schema records at rest"


@compat
def test_compat_temp_authority_residue_clean(compat_child):
    # temp-authority residue (046 [4] form): no NON-admin role holds a usable (set/inherit)
    # membership into records_owner/records_fn_owner. The three transient transfer grants
    # (postgres->records_owner, postgres->records_fn_owner, records_owner->records_fn_owner)
    # must be revoked; postgres is EXEMPT.
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        n = c.execute(TEMP_AUTHORITY_RESIDUE).fetchone()[0]
        assert n == 0, f"{n} usable non-admin membership edge(s) into an owner role survived 048 UP"


@compat
def test_compat_048_down_full_file_applies_under_non_super(compat_child):
    # Task 2.4 FULL-FILE RED/GREEN proof: applies the WHOLE committed
    # 048_records_audit_log_down.sql AS THE SAME NON-SUPER APPLIER that applied 001-048 UP,
    # then asserts the audit objects are DROPPED and records_fn_owner + records_auditor are
    # RETAINED (048_down runs BEFORE 047_down, so both roles still exist here). This is the
    # strongest local proof - the entire file, single BEGIN...COMMIT, under the true
    # non-super applier - the analog of 047_down's full-file proof.
    #
    # Two independent 42501s must both be fixed for this to be GREEN, and reverting EITHER
    # turns it RED (the whole file is one transaction, so any failure rolls back everything):
    #   1. `revoke usage on schema records from <role>` ([d1]): needs to run under the schema
    #      owner's authority (SET ROLE into the derived schema owner records_owner), because
    #      REVOKE of a schema-USAGE grant requires owning the schema / GRANT OPTION, which the
    #      bare applier lacks.
    #   2. `drop function`/`drop table` ([d2]): needs SET ROLE records_fn_owner (via a
    #      transient WITH SET grant), because DROP requires OWNERSHIP and the objects are
    #      records_fn_owner-owned.
    # Driven via rv._apply_as_applier (whole file from disk under the applier DSN, mirroring
    # the compat fixture's own UP applies) - NOT via _dbtest.run_psql on RECORDS_DEV_DSN,
    # which runs as the walk's trusted superuser child DB and would mask BOTH bugs.
    admin_dsn, apply_dsn = compat_child
    rv._apply_as_applier(DOWN, apply_dsn)  # raises ApplierApplyError on a 42501 regression
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(AUDIT_LOG_EXISTS).fetchone()[0] == 0, \
            "audit_log must be DROPPED by 048_down under the non-super applier"
        assert c.execute(FN_EXISTS).fetchone()[0] == 0, \
            "fn_audit_capture must be DROPPED by 048_down under the non-super applier"
        assert c.execute(
            "select count(*) from pg_roles where rolname='records_fn_owner'"
        ).fetchone()[0] == 1, "records_fn_owner must be RETAINED (047_down owns its drop)"
        assert c.execute(
            "select count(*) from pg_roles where rolname='records_auditor'"
        ).fetchone()[0] == 1, "records_auditor must be RETAINED (LOGIN-leave)"
