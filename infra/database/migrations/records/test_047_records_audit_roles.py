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
# ALSO drives 047_records_audit_roles_down.sql through the SAME non-super applier (Task 2.3
# review fix's RED/GREEN proof) and asserts the ratified LOGIN-leave (records_fn_owner
# dropped; records_auditor retained, records access revoked). This is the green mirror of
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
    yields (admin_child_dsn, applier_apply_dsn): the ADMIN child DSN for catalog
    introspection, and the non-super APPLIER's own apply DSN so a test can drive further
    SQL (e.g. 047_down) through the SAME non-super identity that applied 047 UP - the
    identity whose limited membership edge on records_fn_owner is exactly what Task 2.3's
    review fix addresses. The fixture succeeding IS the green proof that adapted 047
    applies under the non-super applier. Value-silent."""
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
        yield rv.derive_child_dsn(_ADMIN, val), apply_dsn
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_047_applies_under_non_super(compat_child):
    # Reaching here means adapted 047 applied AS the non-super applier without raising.
    admin_dsn, apply_dsn = compat_child
    assert admin_dsn and apply_dsn


@compat
def test_compat_audit_role_flags(compat_child):
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
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
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
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
    admin_dsn, _apply_dsn = compat_child
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        n = c.execute(
            "select count(*) from pg_shdepend sd join pg_roles ro on ro.oid=sd.refobjid "
            "where ro.rolname='records_fn_owner' and sd.deptype='a'"
        ).fetchone()[0]
        assert n == 0, f"records_fn_owner holds {n} ACL grant(s) at 047; must be bare"


# The records_fn_owner teardown block is EXTRACTED (not duplicated) from the committed
# 047_records_audit_roles_down.sql on disk, so this proof is genuinely coupled to the real
# file - a future accidental revert of the fix in the .sql is what turns this test RED, not a
# hand-copied literal that could silently drift from the committed source. Extracted between
# two stable markers already present in the file: starts right after `SET client_encoding`
# (the BEGIN preamble), ends right before the `-- records_auditor:` block comment. Applied as
# its OWN transaction (wrapped here, not in the source file) so it can be proven in isolation
# from the records_auditor block that follows it in the committed file. Isolation is required
# because the committed file is a single BEGIN...COMMIT: a failure anywhere in the file rolls
# back the ENTIRE file, including an already-successful fn_owner drop, so a whole-file apply
# cannot isolate the fn_owner mechanism from an unrelated failure later in the same file (see
# the records_auditor defect noted below).
_DOWN_SQL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DOWN)
_START_MARKER = "SET client_encoding TO 'UTF8';"
_END_MARKER = "-- records_auditor:"


def _extract_fn_owner_teardown_sql():
    with open(_DOWN_SQL_PATH, encoding="utf-8") as fh:
        text = fh.read()
    start = text.index(_START_MARKER) + len(_START_MARKER)
    end = text.index(_END_MARKER, start)
    block = text[start:end]
    assert "records_fn_owner" in block, (
        f"{DOWN} marker extraction found no records_fn_owner text between the "
        "SET client_encoding preamble and the records_auditor comment; markers drifted"
    )
    return "begin;\n" + block + "\ncommit;\n"


@compat
def test_compat_047_down_fn_owner_teardown_applies_under_non_super(compat_child):
    # Task 2.3 review fix RED/GREEN proof, isolated to the records_fn_owner mechanism:
    # without the transient INHERIT grant in 047_down, `drop owned by records_fn_owner`
    # 42501s here (RED) because the non-super applier holds only the admin-only creator edge
    # (set_option=inherit_option=false) on records_fn_owner, which does NOT confer
    # has_privs_of_role. With the fix, applying the SAME statements AS THE SAME NON-SUPER
    # APPLIER that applied 047 UP succeeds (GREEN): records_fn_owner is dropped.
    #
    # Applies the EXTRACTED fn_owner block (see _extract_fn_owner_teardown_sql above; sourced
    # from the real committed file, wrapped in its own begin/commit) directly via psycopg on
    # apply_dsn (the applier's own DSN), rather than the whole committed
    # 047_records_audit_roles_down.sql file. Reason: the committed file also contains an
    # UNRELATED, pre-existing, out-of-scope defect in its
    # records_auditor block (`revoke usage on schema records from records_auditor` 42501s
    # under the non-super applier for a DIFFERENT reason - REVOKE on a schema requires
    # ownership/GRANT OPTION on that schema, which the applier does not hold at this point in
    # the stack; the same unprotected-REVOKE shape also exists in 048_records_audit_log_down.sql).
    # Because the whole file is one BEGIN...COMMIT, that later failure would roll back the
    # fn_owner drop this test targets too, making a whole-file apply unable to isolate the
    # fix under review. Flagged separately (out of scope for Task 2.3's records_fn_owner
    # defect); NOT re-proven or fixed here. This isolated proof mirrors
    # test_supabase_compat_redproof.py's test_unadapted_045_fails_at_alter_role_42501 pattern
    # (raw statements against the applier DSN) rather than rv._apply_as_applier, which only
    # applies whole files from disk.
    admin_dsn, apply_dsn = compat_child
    sql = _extract_fn_owner_teardown_sql()
    with psycopg.connect(apply_dsn, autocommit=True) as c:
        c.execute(sql)  # raises on a 42501 regression (e.g. the transient grant reverted)
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        assert c.execute(FN_OWNER_EXISTS).fetchone()[0] == 0, \
            "records_fn_owner must be dropped by its 047_down teardown under the non-super applier"


# DOWN LOGIN-leave posture (records_fn_owner DROPPED after its zero-owned guard;
# records_auditor RETAINED with records access revoked; NO pg_authid, NO drop of the LOGIN
# role) is asserted end-to-end by the walk-contract test_047_applied_then_down_up above (which
# runs under the trusted walk DSN, not the non-super applier), which the full run_validation
# walk exercises. The records_fn_owner DROP OWNED mechanism specifically - the Task 2.3 review
# fix's target - is ADDITIONALLY proven under the non-super applier, in isolation, by
# test_compat_047_down_fn_owner_teardown_applies_under_non_super above: 047_down now mirrors
# 046_down's [d0] transient WITH SET + INHERIT TRUE grant treatment, so `drop owned by
# records_fn_owner` succeeds under the non-super applier holding only the admin-only creator
# edge. This is NOT an unfixed fidelity boundary that 046_down "also carries" - 046_down fixed
# the identical problem for records_owner, and 047_down now applies the same fix for
# records_fn_owner. The COMMITTED FILE'S FULL end-to-end apply under the non-super applier
# remains unproven locally, because of the separate, out-of-scope records_auditor
# schema-usage-revoke defect documented above (also present in 048_down) - that is a Phase-3
# real-branch / follow-up-task concern, not a regression introduced by this fix. A real
# Supabase branch (Phase 3) remains the ultimate fidelity authority for either proof.
