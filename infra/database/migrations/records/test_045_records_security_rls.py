# infra/database/migrations/records/test_045_records_security_rls.py
"""Tier-3 static posture test for migration 045 (records security/RLS).

Introspection only - no mutation - so it is safe inside the forward-incremental
walk and does not move the schema fingerprint. Dynamic denial/escalation proofs
live in run_validation.py Tier 5. Skips loudly when RECORDS_DEV_DSN is absent.
"""
import os
import sys

import psycopg
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dbtest  # noqa: E402

RESERVED = {
    "assets": {"status", "condition"},
    "form_submissions": {"status", "reviewed_by"},
    "pm_events": {"status"},
    "form_field_values": {"assessment"},
    "persons": {"worker_class", "employee_ref", "match_adjudicated_by",
                "match_adjudicated_at", "match_confidence"},
}
NOT_NULL_INVARIANT = [
    ("assets", "asset_tag"), ("assets", "name"),
    ("form_submissions", "template_id"), ("form_submissions", "asset_id"),
    ("form_field_values", "form_submission_id"), ("form_field_values", "field_key"),
    ("pm_schedules", "pm_program_id"), ("pm_schedules", "asset_id"),
    ("pm_events", "pm_schedule_id"), ("pm_events", "asset_id"),
    ("persons", "display_name"),
]
WRITE_PATH = ["assets", "form_submissions", "form_field_values", "pm_schedules", "pm_events", "persons"]
REFERENCE = ["asset_classes", "form_templates", "pm_programs", "neta_procedures",
             "neta_test_items", "neta_tables", "asset_class_neta_procedure", "neta_procedure_xref"]
# The 15 records tables the migration's grant matrix is authoritative over
# (8 reference + 6 write-path + source_links). Same list the migration uses.
ALL_TABLES = REFERENCE + WRITE_PATH + ["neta_table_source_links"]


@pytest.fixture(scope="module")
def conn():
    c = psycopg.connect(_dbtest.dsn(), autocommit=True)
    yield c
    c.close()


def test_rls_enabled_on_all_records_tables(conn):
    rows = conn.execute(
        "select c.relname, c.relrowsecurity from pg_class c "
        "join pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname='records' and c.relkind='r' order by 1"
    ).fetchall()
    off = [r[0] for r in rows if not r[1]]
    assert off == [], f"tables without RLS enabled: {off}"


def test_no_policy_is_public(conn):
    # pg_policies.roles renders as name[] e.g. {records_api,records_intake_writer};
    # a policy with no TO clause (PUBLIC) renders as {public}.
    pub = conn.execute(
        "select tablename, policyname, roles from pg_policies "
        "where schemaname='records' and (roles is null or 'public' = any(roles))"
    ).fetchall()
    assert pub == [], f"records policy granted TO PUBLIC: {pub}"


def test_no_public_execute_on_routines(conn):
    n = conn.execute(
        "select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace, "
        "lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
        "where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE'"
    ).fetchone()[0]
    assert n == 0, "a records routine retains PUBLIC EXECUTE"


def test_no_public_on_tables_or_schema(conn):
    # AC2: zero PUBLIC grants on any records table/view, and no PUBLIC privilege on the schema.
    tv = conn.execute(
        "select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace, "
        "lateral aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a "
        "where n.nspname='records' and c.relkind in ('r','v') and a.grantee=0"
    ).fetchone()[0]
    assert tv == 0, "PUBLIC holds a grant on a records table/view"
    sc = conn.execute(
        "select count(*) from pg_namespace n, "
        "lateral aclexplode(coalesce(n.nspacl, acldefault('n', n.nspowner))) a "
        "where n.nspname='records' and a.grantee=0"
    ).fetchone()[0]
    assert sc == 0, "PUBLIC holds a privilege on schema records"


def test_reader_has_no_write(conn):
    for tbl in WRITE_PATH:
        for priv in ("INSERT", "UPDATE", "DELETE"):
            has = conn.execute(
                "select has_table_privilege('records_api', %s, %s)", (f"records.{tbl}", priv)
            ).fetchone()[0]
            assert not has, f"records_api unexpectedly holds {priv} on {tbl}"


def test_writer_holds_all_not_null_columns(conn):
    for tbl, col in NOT_NULL_INVARIANT:
        has = conn.execute(
            "select has_column_privilege('records_intake_writer', %s, %s, 'INSERT')",
            (f"records.{tbl}", col),
        ).fetchone()[0]
        assert has, f"records_intake_writer missing INSERT({col}) on {tbl} (would break real import)"


def test_writer_denied_reserved_columns(conn):
    for tbl, cols in RESERVED.items():
        for col in cols:
            for priv in ("INSERT", "UPDATE"):
                has = conn.execute(
                    "select has_column_privilege('records_intake_writer', %s, %s, %s)",
                    (f"records.{tbl}", col, priv),
                ).fetchone()[0]
                assert not has, f"records_intake_writer holds {priv}({col}) on {tbl} - reserved"


def test_views_are_security_invoker(conn):
    for v in ("v_asset_test_history", "v_pm_due"):
        opts = conn.execute(
            "select reloptions from pg_class c join pg_namespace n on n.oid=c.relnamespace "
            "where n.nspname='records' and c.relname=%s", (v,)
        ).fetchone()[0]
        assert opts and any("security_invoker=" in o and o.split("=")[1] in ("true", "on", "1")
                            for o in opts), f"{v} is not security_invoker"


def test_source_links_restricted(conn):
    # D10 owner-only: NEITHER app role holds ANY privilege on source_links,
    # not just SELECT (a stale INSERT/UPDATE/DELETE grant must not survive 045).
    for role in ("records_api", "records_intake_writer"):
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            has = conn.execute(
                "select has_table_privilege(%s, 'records.neta_table_source_links', %s)",
                (role, priv),
            ).fetchone()[0]
            assert not has, f"{role} holds {priv} on neta_table_source_links (D10 restricts it)"


def test_writer_no_delete_anywhere(conn):
    # Authoritative matrix: records_intake_writer never holds DELETE on any records
    # table (a stale DELETE grant must be cleared by 045's revoke-first).
    for tbl in ALL_TABLES:
        has = conn.execute(
            "select has_table_privilege('records_intake_writer', %s, 'DELETE')",
            (f"records.{tbl}",),
        ).fetchone()[0]
        assert not has, f"records_intake_writer unexpectedly holds DELETE on {tbl}"


def test_reader_no_write_anywhere(conn):
    # records_api is read-only across ALL 15 records tables (broad reader-no-write;
    # extends test_reader_has_no_write from the 6 write-path tables to all 15).
    for tbl in ALL_TABLES:
        for priv in ("INSERT", "UPDATE", "DELETE"):
            has = conn.execute(
                "select has_table_privilege('records_api', %s, %s)", (f"records.{tbl}", priv)
            ).fetchone()[0]
            assert not has, f"records_api unexpectedly holds {priv} on {tbl}"


# --------------------------------------------------------------------------------------
# SUPABASE-COMPAT green-proof (Task 2.1). Self-driving on RECORDS_PG_ADMIN_DSN: it builds
# a disposable DB, applies 001-044 then the ADAPTED 045 through the NON-super applier, and
# asserts the adapted 045 SUCCEEDS with the correct role posture / policy binding / D-A
# membership isolation. This is the green mirror of test_supabase_compat_redproof.py; it is
# a LOCAL APPROXIMATION (records objects are applier-owned locally, postgres-owned on a real
# Supabase branch - the branch is the fidelity authority, Phase 3).
# --------------------------------------------------------------------------------------
import run_validation as rv  # noqa: E402

_ADMIN = os.environ.get("RECORDS_PG_ADMIN_DSN")

def compat(fn):
    """Stacked marks: apply the registered `compat` marker (so run_validation tier-3
    selects the isolated compat pass via `-m compat` and the per-migration walk deselects
    via `-m "not compat"`) AND skip when RECORDS_PG_ADMIN_DSN is absent (no local Postgres
    to build the non-super applier)."""
    return pytest.mark.compat(
        pytest.mark.skipif(
            not _ADMIN,
            reason="RECORDS_PG_ADMIN_DSN not set - non-super compat green-proof skipped",
        )(fn)
    )


# The records app roles are CLUSTER-level, so a per-DB disposable does not isolate them.
# On a clean target the applier creates + owns them (holds ADMIN); a leaked, orphaned pair
# (from an aborted prior run whose applier was dropped) has no admin edge and blocks the
# next applier's ALTER with 42501. Drop the disposable, password-less pair before/after each
# module run so the proof is idempotent. Password-carrying roles are LEFT IN PLACE (safety).
_APP_ROLES = ("records_api", "records_intake_writer")


def _drop_disposable_app_roles():
    with psycopg.connect(_ADMIN, autocommit=True) as c:
        for role in _APP_ROLES:
            if not c.execute("select 1 from pg_roles where rolname=%s", (role,)).fetchone():
                continue
            haspw = c.execute(
                "select rolpassword is not null from pg_authid where rolname=%s", (role,)
            ).fetchone()[0]
            if haspw:
                continue  # out-of-band password: never drop (DEV-7 discipline)
            try:
                c.execute(f'drop role "{role}"')
            except psycopg.errors.DependentObjectsStillExist:
                pass  # cross-DB dependency: leave in place


@pytest.fixture(scope="module")
def compat_child():
    """Disposable DB with 001-044 + the ADAPTED 045 applied AS the non-super applier;
    yields the ADMIN child DSN for catalog introspection. The fixture succeeding IS the
    green proof that adapted 045 applies under the non-super applier. Value-silent."""
    if not _ADMIN:
        pytest.skip("RECORDS_PG_ADMIN_DSN not set")
    rv.check_admin_dsn(_ADMIN)
    _drop_disposable_app_roles()  # clean any orphaned cluster-level pair before applying
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
            if num > 45:
                break
            rv._apply_as_applier(fname, apply_dsn)  # 001-044 then adapted 045; each must succeed
        yield rv.RedactedDsn(rv.derive_child_dsn(_ADMIN, val))
    finally:
        with psycopg.connect(_ADMIN, autocommit=True) as c:
            c.execute(f'drop database if exists "{val}" with (force)')
            c.execute(applier.drop_sql)
        _drop_disposable_app_roles()  # do not leave orphaned cluster-level roles behind


@compat
def test_compat_adapted_045_applies_under_non_super(compat_child):
    # Reaching here means adapted 045 applied AS the non-super applier without raising.
    assert compat_child


@compat
def test_compat_app_role_flags(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        for role in ("records_api", "records_intake_writer"):
            sup, byp, login = c.execute(
                "select rolsuper, rolbypassrls, rolcanlogin from pg_roles where rolname=%s",
                (role,),
            ).fetchone()
            assert sup is False, f"{role} must be rolsuper=false"
            assert byp is False, f"{role} must be rolbypassrls=false"
            assert login is True, f"{role} must be rolcanlogin=true"


@compat
def test_compat_reader_no_write_writer_no_delete(compat_child):
    with psycopg.connect(compat_child, autocommit=True) as c:
        for tbl in ALL_TABLES:
            for priv in ("INSERT", "UPDATE", "DELETE"):
                has = c.execute(
                    "select has_table_privilege('records_api', %s, %s)",
                    (f"records.{tbl}", priv),
                ).fetchone()[0]
                assert not has, f"records_api holds {priv} on {tbl}"
            hasdel = c.execute(
                "select has_table_privilege('records_intake_writer', %s, 'DELETE')",
                (f"records.{tbl}",),
            ).fetchone()[0]
            assert not hasdel, f"records_intake_writer holds DELETE on {tbl}"


@compat
def test_compat_policies_bound_to_custom_roles(compat_child):
    # Gate B: policies target the custom app roles directly, never PUBLIC.
    with psycopg.connect(compat_child, autocommit=True) as c:
        pub = c.execute(
            "select tablename, policyname from pg_policies where schemaname='records' "
            "and (roles is null or 'public' = any(roles))"
        ).fetchall()
        assert pub == [], f"records policy TO PUBLIC: {pub}"
        bound = c.execute(
            "select count(*) from pg_policies where schemaname='records' "
            "and roles && array['records_api','records_intake_writer']::name[]"
        ).fetchone()[0]
        assert bound > 0, "no records policy is bound TO the custom app roles"


@compat
def test_compat_membership_isolation_holds(compat_child):
    # D-A: no USABLE (set/inherit) membership edge from/to an app role by a NON-admin role.
    with psycopg.connect(compat_child, autocommit=True) as c:
        rows = c.execute(
            "select a.rolname, b.rolname, am.set_option, am.inherit_option "
            "from pg_auth_members am "
            "join pg_roles a on a.oid=am.roleid join pg_roles b on b.oid=am.member "
            "where (a.rolname in ('records_api','records_intake_writer') "
            "    or b.rolname in ('records_api','records_intake_writer')) "
            "and (am.set_option or am.inherit_option) "
            "and am.member <> 'postgres'::regrole"
        ).fetchall()
        assert rows == [], f"app role holds a usable membership edge: {rows}"
