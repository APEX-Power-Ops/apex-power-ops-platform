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
