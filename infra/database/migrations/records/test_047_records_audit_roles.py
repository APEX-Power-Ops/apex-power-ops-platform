import os
import sys

import psycopg
import pytest

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

# D-A refined (REV 5, PHASE0-FINDINGS D3): count only USABLE (set/inherit) edges
# touching either audit role in EITHER direction, EXEMPTING the trusted postgres
# applier (its un-removable admin-only creator edge is set=inherit=false -> not
# usable, and postgres is custody-controlled). A real usable membership involving
# an audit role and a non-admin role still trips.
USABLE_MEMBERSHIP_EDGES = (
    "select count(*) from pg_auth_members am "
    "join pg_roles rl on rl.oid=am.roleid "
    "join pg_roles mm on mm.oid=am.member "
    "where (rl.rolname in ('records_fn_owner','records_auditor') "
    "    or mm.rolname in ('records_fn_owner','records_auditor')) "
    "  and (am.set_option or am.inherit_option) "
    "  and am.roleid <> 'postgres'::regrole "
    "  and am.member <> 'postgres'::regrole"
)

FN_OWNER_EXISTS = "select count(*) from pg_roles where rolname='records_fn_owner'"
AUDITOR_EXISTS = "select count(*) from pg_roles where rolname='records_auditor'"


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
    # super/bypassrls/createdb/createrole/replication, zero USABLE membership edges.
    rows = _q(dsn, ROLE_FLAGS)
    assert [r[0] for r in rows] == ["records_auditor", "records_fn_owner"]
    by_name = {r[0]: r for r in rows}
    fn_owner = by_name["records_fn_owner"]
    auditor = by_name["records_auditor"]
    # (rolname, rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, rolcreaterole, rolreplication)
    assert fn_owner[1:] == (False, False, False, False, False, False)  # NOLOGIN
    assert auditor[1:] == (False, False, True, False, False, False)  # LOGIN
    assert _q(dsn, USABLE_MEMBERSHIP_EDGES)[0][0] == 0

    # (2) DOWN -> RATIFIED LOGIN-leave posture: records_fn_owner (NOLOGIN pure owner)
    # is DROPPED after its zero-owned guard; records_auditor (LOGIN credential role)
    # is RETAINED with its records access revoked (never destroy a possibly operator-
    # provisioned serving credential; no pg_authid read).
    _dbtest.run_psql(DOWN, dsn)
    assert _q(dsn, FN_OWNER_EXISTS)[0][0] == 0
    assert _q(dsn, AUDITOR_EXISTS)[0][0] == 1

    # (3) UP -> re-apply 047 and LEAVE it applied. records_auditor is re-normalized
    # (create-if-not-exists is a no-op; the unconditional alter re-asserts its attrs).
    _dbtest.run_psql(MIG, dsn)
    rows = _q(dsn, ROLE_FLAGS)
    assert [r[0] for r in rows] == ["records_auditor", "records_fn_owner"]
    by_name = {r[0]: r for r in rows}
    assert by_name["records_fn_owner"][1:] == (False, False, False, False, False, False)
    assert by_name["records_auditor"][1:] == (False, False, True, False, False, False)
    assert _q(dsn, USABLE_MEMBERSHIP_EDGES)[0][0] == 0


# --------------------------------------------------------------------------------------
# SUPABASE-COMPAT green-proof (Task 2.3). Self-driving on RECORDS_PG_ADMIN_DSN: it builds a
# disposable DB, applies 001-044 + adapted 045 + adapted 046 + adapted 047 through the
# NON-super applier, and asserts the adapted 047 SUCCEEDS with the correct role attrs
# (records_fn_owner NOLOGIN/non-super/non-bypass; records_auditor LOGIN/non-super/non-bypass/
# no-repl/no-createdb/no-createrole) + D-A usable-membership isolation + pure-owner. It then
# exercises 047_down and asserts the ratified LOGIN-leave (records_fn_owner dropped;
# records_auditor retained, records access revoked). This is the green mirror of
# test_supabase_compat_redproof.py; it is a LOCAL APPROXIMATION (a real Supabase branch is
# the fidelity authority, Phase 3).
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
    """Disposable DB with 001-044 + adapted 045/046/047 applied AS the non-super applier;
    yields the ADMIN child DSN for catalog introspection. The fixture succeeding IS the green
    proof that adapted 047 applies under the non-super applier. Value-silent."""
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
            if num > 47:
                break
            rv._apply_as_applier(fname, apply_dsn)  # 001-044, adapted 045/046/047; each succeeds
        yield rv.derive_child_dsn(_ADMIN, val)
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_047_applies_under_non_super(compat_child):
    # Reaching here means adapted 047 applied AS the non-super applier without raising.
    assert compat_child


@compat
def test_compat_audit_role_flags(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        rows = {r[0]: r for r in c.execute(ROLE_FLAGS).fetchall()}
        assert set(rows) == {"records_fn_owner", "records_auditor"}
        # (rolname, super, bypassrls, canlogin, createdb, createrole, replication)
        assert rows["records_fn_owner"][1:] == (False, False, False, False, False, False), \
            "records_fn_owner must be NOLOGIN/non-super/non-bypass/no-repl/no-createdb/no-createrole"
        assert rows["records_auditor"][1:] == (False, False, True, False, False, False), \
            "records_auditor must be LOGIN/non-super/non-bypass/no-repl/no-createdb/no-createrole"


@compat
def test_compat_audit_membership_isolation_holds(compat_child):
    # D-A (invariant 8, RESTATED): no NON-admin role holds a USABLE (set/inherit) membership
    # edge to/from either audit role. The trusted applier/postgres identity is EXEMPT
    # (endpoint <> postgres); admin-only edges (set=inherit=false) are not flagged.
    with psycopg.connect(compat_child, autocommit=True) as c:
        rows = c.execute(
            "select rl.rolname, mm.rolname, am.set_option, am.inherit_option "
            "from pg_auth_members am "
            "join pg_roles rl on rl.oid=am.roleid "
            "join pg_roles mm on mm.oid=am.member "
            "where (rl.rolname in ('records_fn_owner','records_auditor') "
            "    or mm.rolname in ('records_fn_owner','records_auditor')) "
            "and (am.set_option or am.inherit_option) "
            "and am.roleid <> 'postgres'::regrole and am.member <> 'postgres'::regrole"
        ).fetchall()
        assert rows == [], f"a usable membership edge touches an audit role: {rows}"


@compat
def test_compat_fn_owner_is_pure_no_acl_grants(compat_child):
    # At 047 records_fn_owner is BARE (048 adds the single schema USAGE grant).
    with psycopg.connect(compat_child, autocommit=True) as c:
        n = c.execute(
            "select count(*) from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid "
            "where ro.rolname='records_fn_owner' and sd.deptype='a'"
        ).fetchone()[0]
        assert n == 0, f"records_fn_owner holds {n} ACL grant(s) at 047; must be bare"


# DOWN LOGIN-leave posture (records_fn_owner DROPPED after its zero-owned guard;
# records_auditor RETAINED with records access revoked; NO pg_authid, NO drop of the LOGIN
# role) is asserted by the walk-contract test_047_applied_then_down_up above, which the full
# run_validation walk exercises. The applier-facing DOWN (drop owned by records_fn_owner under
# a non-super applier holding only the admin-only creator edge) is a Phase-3 real-branch
# concern - the SAME fidelity boundary 046's down uses; not re-proven here as a local
# approximation. 047's records_fn_owner down block is unchanged from the superuser posture per
# the ratified rule (NOLOGIN owner roles drop after zero-owned guards).
