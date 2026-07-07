import os
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

MIG = "046_records_ownership.sql"
DOWN = "046_records_ownership_down.sql"

# Ownership counted across ALL THREE catalogs (pg_class[incl. matview 'm'] + pg_proc
# + pg_namespace) so functions (fn_set_updated_at) and the records schema itself are
# covered, not tables alone. The three %s slots are the expected owner role name.
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

OWNED_EQ = (
    "select "
    "(select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
    " where ns.nspname='records' and c.relkind in ('r','v','m','S') "
    "   and pg_get_userbyid(c.relowner) = '%s') "
    "+ (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace "
    "   where ns.nspname='records' and pg_get_userbyid(p.proowner) = '%s') "
    "+ (select count(*) from pg_namespace where nspname='records' "
    "   and pg_get_userbyid(nspowner) = '%s')"
)


def _q(dsn, sql):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(sql).fetchall()


def test_046_applied_then_down_up():
    # Runner contract: 046 is ALREADY applied by the walk. Assert the applied posture,
    # exercise DOWN (parks on records_reclaim_owner, drops records_owner, keeps reclaim)
    # then UP (branches on records_reclaim_owner), and LEAVE 046 applied.
    # _dbtest.dsn() reads RECORDS_DEV_DSN (the walk's disposable child DB via _child_env),
    # skips the module loudly if absent, and refuses records_dev.
    #
    # NOTE (fidelity): in --apply-as-non-superuser mode the WALK applies 046 as the
    # disposable non-super applier (so records_owner/records_reclaim_owner are applier-
    # created), but THIS test connects as the admin child DSN (local superuser). The
    # DOWN + re-UP below therefore run as a superuser, which can always take the transient
    # WITH SET grants the reclaim choreography needs. The NON-super RE-UP-from-reclaim path
    # (postgres holding admin on an applier-created records_reclaim_owner) is proven only on
    # a real Supabase branch (Phase 3); locally it is code-review-verified. The self-driving
    # compat green-proof below applies the ADAPTED 046 UP through the non-super applier.
    dsn = _dbtest.dsn()
    # (1) applied posture: everything records_owner-owned across all catalogs; reclaim owns
    # nothing; both owner roles non-super/non-bypass/non-login.
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
    assert _q(dsn, OWNED_EQ % (("records_reclaim_owner",) * 3))[0][0] == 0
    assert _q(dsn, "select rolsuper, rolbypassrls, rolcanlogin "
                   "from pg_roles where rolname='records_owner'")[0] == (False, False, False)
    assert _q(dsn, "select rolsuper, rolbypassrls, rolcanlogin "
                   "from pg_roles where rolname='records_reclaim_owner'")[0] == (False, False, False)
    assert _q(dsn, "select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
                   "where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity")[0][0] == 0
    # FORCE teeth: the owner is bound by RLS. SET SESSION AUTHORIZATION makes session_user
    # the role (SET ROLE would leave session_user=postgres).
    with psycopg.connect(dsn, autocommit=True) as c:
        base = c.execute("select count(*) from records.neta_tables").fetchone()[0]
        assert base > 0
        c.execute("set session authorization records_owner")
        assert c.execute("select count(*) from records.neta_tables").fetchone()[0] == 0
        c.execute("reset session authorization")
        c.execute("set session authorization records_api")
        assert c.execute("select count(*) from records.neta_tables").fetchone()[0] == base
        c.execute("reset session authorization")
    # (2) DOWN -> objects parked on records_reclaim_owner; records_owner DROPPED; reclaim persists.
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, OWNED_NE % (("records_reclaim_owner",) * 3))[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_owner'")[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_reclaim_owner'")[0][0] == 1
    # (3) UP -> 046 branches on records_reclaim_owner, transfers back to records_owner, and
    # LEAVE it applied. reclaim persists but owns nothing again.
    _dbtest.run_psql(MIG, dsn)
    assert _q(dsn, OWNED_NE % ("records_owner", "records_owner", "records_owner"))[0][0] == 0
    assert _q(dsn, OWNED_EQ % (("records_reclaim_owner",) * 3))[0][0] == 0
    assert _q(dsn, "select count(*) from pg_roles where rolname='records_reclaim_owner'")[0][0] == 1


# --------------------------------------------------------------------------------------
# SUPABASE-COMPAT green-proof (Task 2.2). Self-driving on RECORDS_PG_ADMIN_DSN: it builds a
# disposable DB, applies 001-044 + adapted 045 then adapted 046 through the NON-super
# applier, and asserts the adapted 046 SUCCEEDS with the correct ownership posture / FORCE
# RLS / owner-role flags / D-A membership isolation / records_reclaim_owner existence. This
# is the green mirror of test_supabase_compat_redproof.py; it is a LOCAL APPROXIMATION
# (records objects are applier-owned locally in the FRESH case, postgres-owned on a real
# Supabase branch - the branch is the fidelity authority, Phase 3). The reclaim RE-UP branch
# is exercised on a real branch; locally the FRESH branch is proven end-to-end.
# --------------------------------------------------------------------------------------
import run_validation as rv  # noqa: E402

_ADMIN = os.environ.get("RECORDS_PG_ADMIN_DSN")

compat = pytest.mark.skipif(
    not _ADMIN, reason="RECORDS_PG_ADMIN_DSN not set - non-super compat green-proof skipped"
)

# Cluster-level roles the compat proof may leave behind (aborted prior run). Drop the
# password-less, orphaned set before/after each module run so the proof is idempotent;
# password-carrying roles are LEFT IN PLACE (DEV-7 safety). records_owner is per-up
# created; records_reclaim_owner is persistent-by-design but disposable in this proof's
# throwaway cluster context, so we clear it too when orphaned + password-less.
_DISPOSABLE_ROLES = ("records_api", "records_intake_writer", "records_owner", "records_reclaim_owner")


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
    """Disposable DB with 001-044 + adapted 045 + adapted 046 applied AS the non-super
    applier; yields the ADMIN child DSN for catalog introspection. The fixture succeeding IS
    the green proof that adapted 046 applies under the non-super applier. Value-silent."""
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
            if num > 46:
                break
            rv._apply_as_applier(fname, apply_dsn)  # 001-044, adapted 045, adapted 046; each succeeds
        yield rv.RedactedDsn(rv.derive_child_dsn(_ADMIN, val))
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_046_applies_under_non_super(compat_child):
    # Reaching here means adapted 046 applied AS the non-super applier without raising.
    assert compat_child


@compat
def test_compat_all_records_objects_owned_by_records_owner(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        n = c.execute(OWNED_NE % ("records_owner", "records_owner", "records_owner")).fetchone()[0]
        assert n == 0, f"{n} records object(s)/schema not owned by records_owner"


@compat
def test_compat_owner_roles_flags(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        for role in ("records_owner", "records_reclaim_owner"):
            sup, byp, login, cdb, crole, crepl = c.execute(
                "select rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, "
                "rolreplication from pg_roles where rolname=%s", (role,)
            ).fetchone()
            assert sup is False, f"{role} must be rolsuper=false"
            assert byp is False, f"{role} must be rolbypassrls=false"
            assert login is False, f"{role} must be NOLOGIN"
            assert not (cdb or crole or crepl), f"{role} holds createdb/createrole/replication"


@compat
def test_compat_reclaim_owner_exists_and_owns_nothing(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        assert c.execute(
            "select count(*) from pg_roles where rolname='records_reclaim_owner'"
        ).fetchone()[0] == 1, "records_reclaim_owner must exist after 046 UP"
        owned = c.execute(OWNED_EQ % (("records_reclaim_owner",) * 3)).fetchone()[0]
        assert owned == 0, f"records_reclaim_owner owns {owned} records object(s) after UP; must own nothing"


@compat
def test_compat_force_rls_on_all_base_tables(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        off = c.execute(
            "select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace "
            "where ns.nspname='records' and c.relkind='r' and not c.relforcerowsecurity"
        ).fetchone()[0]
        assert off == 0, f"{off} records base table(s) not FORCE-RLS"


@compat
def test_compat_membership_isolation_holds(compat_child):
    # D-A (invariant 8, RESTATED): no NON-admin role holds a USABLE (set/inherit) membership
    # path INTO records_owner or records_reclaim_owner. The trusted applier/postgres identity
    # is EXEMPT (member <> postgres); admin-only edges (set=inherit=false) are not flagged.
    with psycopg.connect(compat_child, autocommit=True) as c:
        rows = c.execute(
            "select ow.rolname, m.rolname, am.set_option, am.inherit_option "
            "from pg_auth_members am "
            "join pg_roles ow on ow.oid=am.roleid "
            "join pg_roles m on m.oid=am.member "
            "where ow.rolname in ('records_owner','records_reclaim_owner') "
            "and (am.set_option or am.inherit_option) "
            "and am.member <> 'postgres'::regrole"
        ).fetchall()
        assert rows == [], f"a non-admin role holds a usable membership into an owner role: {rows}"


@compat
def test_compat_owner_is_pure_no_acl_grants(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        n = c.execute(
            "select count(*) from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid "
            "where ro.rolname='records_owner' and sd.deptype='a'"
        ).fetchone()[0]
        assert n == 0, f"records_owner holds {n} ACL grant(s); must be a pure owner"
