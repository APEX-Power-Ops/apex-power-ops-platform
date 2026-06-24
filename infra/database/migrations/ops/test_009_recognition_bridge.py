# test_009_recognition_bridge.py — MIRRORS test_008's DSN/guard/fixture idiom; runs on ops_test ONLY.
import os, pathlib, uuid
import psycopg, pytest
from psycopg.conninfo import conninfo_to_dict
HERE = pathlib.Path(__file__).parent
DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "009 migration tests run on ops_test ONLY"
DOWN1 = HERE / "001_identity_skeleton_down.sql"
CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
         "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql",
         "007_intake_envelope.sql","008_core_equipment_models.sql","009_recognition_bridge.sql"]
UP   = HERE / "009_recognition_bridge.sql"
DOWN = HERE / "009_recognition_bridge_down.sql"

def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))

def _clean_slate():
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("drop schema if exists core cascade")
    _exec(DOWN1)

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with psycopg.connect(DSN) as c, c.cursor() as cur:        # hard runtime guard
        cur.execute("select current_database()")
        assert cur.fetchone()[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN: _exec(HERE / f)                           # applies 001..009
    yield
    _clean_slate()

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

# ---- helpers: seed an eligible (approved, frozen, positive-basis) apparatus ----
def _seed_person(cur, name="PM"):
    cur.execute("insert into ops.persons (display_name) values (%s) returning person_id", (name,))
    return cur.fetchone()[0]

def _seed_eligible_apparatus(cur, *, status="Not Started", provenance="approved",
                             scope_status="In Progress", project_status="Active",
                             is_active=True, scope_active=True, project_active=True,
                             frozen=True, quoted_hours=10, quoted_revenue=1500):
    """Seed project->scope->scope_quote(frozen)->apparatus; returns apparatus_id.
    blended_rate is GENERATED (P4); onsite_labor + total_quoted_hours make it positive."""
    cur.execute("insert into ops.projects (project_number, project_name, status, provenance_status, is_active)"
                " values (%s,'P',%s,'approved',%s) returning id",
                (f"P-{uuid.uuid4().hex[:8]}", project_status, project_active))
    pid = cur.fetchone()[0]
    cur.execute("insert into ops.scopes (project_id, scope_name, status, provenance_status, is_active, source)"
                " values (%s,'S',%s,'approved',%s,'ops-intake') returning id",
                (pid, scope_status, scope_active))
    sid = cur.fetchone()[0]
    cur.execute("insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust,"
                " total_quoted_hours, is_frozen, frozen_at)"
                " values (%s,1500,1,1,%s,%s, case when %s then now() else null end)",
                (sid, quoted_hours, frozen, frozen))
    cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status,"
                " is_active, quoted_hours, quoted_revenue, source)"
                " values (%s,'A-1',%s,%s,%s,%s,%s,'ops-intake') returning id",
                (sid, status, provenance, is_active, quoted_hours, quoted_revenue))
    return cur.fetchone()[0]

def test_db_is_ops_test(conn):
    with conn.cursor() as cur:
        cur.execute("select current_database()"); assert cur.fetchone()[0] == "ops_test"

def test_chain_applies_through_009_table_and_index_present(conn):
    with conn.cursor() as cur:
        cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
        assert cur.fetchone()
        cur.execute("select 1 from pg_indexes where schemaname='ops' and indexname='uq_completion_attestation_active'")
        assert cur.fetchone()
        cur.execute("select obj_description('ops.completion_attestation'::regclass)")
        assert 'FOR RECOGNITION' in (cur.fetchone()[0] or '')

def test_active_unique_one_per_apparatus(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        who = _seed_person(cur)
        aid = _seed_eligible_apparatus(cur)
        cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                    " values (%s,%s,'r','Not Started')", (aid, who))
        try:
            cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                        " values (%s,%s,'r2','Not Started')", (aid, who))
            assert False, "second active attestation accepted — partial-unique index missing"
        except psycopg.errors.UniqueViolation:
            pass
        cur.execute("rollback to savepoint s")

def test_down_then_reup_idempotent():
    _exec(DOWN)
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
        assert cur.fetchone() is None, "009 down did not drop completion_attestation"
        cur.execute("select count(*) from ops.apparatus")   # 001-008 survive
    _exec(UP)
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
        assert cur.fetchone(), "009 re-up did not recreate the table"

def test_down_is_idempotent_double_down():
    """Running the 009 DOWN migration TWICE in a row (after a full 001..009 up) must be a
    clean no-op the second time — proving the IF-EXISTS / create-or-replace idempotency of
    every down block (T6 drop view if exists; T5 create or replace + alter ... drop column
    if exists; T4/T3 drop function if exists; T2/T1 drop trigger if exists + drop function
    if exists; T0 drop table if exists). A double-down must raise NOTHING. Restores the
    full 001..009 session state afterward so later tests are unaffected."""
    _exec(DOWN)            # first down: tears 009 back to the 001..008 baseline
    _exec(DOWN)            # second down on the already-torn-down state: MUST be a clean no-op
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
        assert cur.fetchone() is None, "table present after double-down"
        cur.execute("select count(*) from ops.apparatus")   # 001-008 still intact
    _exec(UP)             # restore the 001..009 session post-state for the remaining tests
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
        assert cur.fetchone(), "009 re-up after double-down did not recreate the table"

def _seed_attestation(cur, who, aid, reason="r"):
    cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                " values (%s,%s,%s,'Not Started') returning id", (aid, who, reason))
    return cur.fetchone()[0]

def test_immutable_core_field_update_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
        att=_seed_attestation(cur, who, aid)
        try:
            cur.execute("update ops.completion_attestation set reason='changed' where id=%s",(att,))
            assert False, "core-field UPDATE accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_immutable_delete_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
        att=_seed_attestation(cur, who, aid)
        try:
            cur.execute("delete from ops.completion_attestation where id=%s",(att,))
            assert False, "DELETE accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_immutable_partial_revoke_fails_missing_revoked_at(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
        att=_seed_attestation(cur, who, aid)
        try:
            cur.execute("update ops.completion_attestation set revoked_by=%s where id=%s",(who,att))
            assert False, "partial revoke (revoked_by w/o revoked_at) accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_immutable_blank_revoke_reason_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
        att=_seed_attestation(cur, who, aid)
        try:
            cur.execute("update ops.completion_attestation set revoked_at=now(), revoked_by=%s, revoke_reason='  '"
                        " where id=%s",(who,att))
            assert False, "blank revoke_reason accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_immutable_wellformed_revoke_succeeds_then_double_revoke_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
        att=_seed_attestation(cur, who, aid)
        cur.execute("update ops.completion_attestation set revoked_at=now(), revoked_by=%s, revoke_reason='superseded'"
                    " where id=%s",(who,att))
        cur.execute("select revoked_at is not null from ops.completion_attestation where id=%s",(att,))
        assert cur.fetchone()[0] is True
        try:
            cur.execute("update ops.completion_attestation set revoke_reason='again' where id=%s",(att,))
            assert False, "double-revoke / post-revoke mutation accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_guard_insert_as_governed_complete_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        # build chain manually so we can attempt the bypass INSERT directly on apparatus
        cur.execute("insert into ops.projects (project_number, project_name, provenance_status)"
                    " values (%s,'P','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
        pid=cur.fetchone()[0]
        cur.execute("insert into ops.scopes (project_id, scope_name, provenance_status) values (%s,'S','approved') returning id",(pid,))
        sid=cur.fetchone()[0]
        try:
            cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status)"
                        " values (%s,'X','Complete','approved')",(sid,))
            assert False, "INSERT as governed-complete (no ctx) accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_guard_draft_complete_then_flip_provenance_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        cur.execute("insert into ops.projects (project_number, project_name, provenance_status)"
                    " values (%s,'P','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
        pid=cur.fetchone()[0]
        cur.execute("insert into ops.scopes (project_id, scope_name, provenance_status) values (%s,'S','approved') returning id",(pid,))
        sid=cur.fetchone()[0]
        # INSERT status=Complete, provenance=draft is NOT g -> allowed
        cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status)"
                    " values (%s,'X','Complete','draft') returning id",(sid,))
        aid=cur.fetchone()[0]
        # flipping provenance to 'approved' ENTERS g without ctx -> must fail on the 2nd stmt
        try:
            cur.execute("update ops.apparatus set provenance_status='approved' where id=%s",(aid,))
            assert False, "draft-Complete -> flip-provenance bypass accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_guard_normal_intake_insert_succeeds(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        aid=_seed_eligible_apparatus(cur, status="Not Started", provenance="approved")  # not g -> allowed
        cur.execute("select status, provenance_status from ops.apparatus where id=%s",(aid,))
        assert cur.fetchone()==("Not Started","approved")
        cur.execute("rollback to savepoint s")

def test_guard_direct_update_status_complete_fails(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        aid=_seed_eligible_apparatus(cur, status="In Progress", provenance="approved")
        try:
            cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
            assert False, "direct UPDATE status=Complete (no ctx) accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_guard_ctx_path_update_succeeds(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        aid=_seed_eligible_apparatus(cur, status="In Progress", provenance="approved")
        cur.execute("select set_config('ops.completion_ctx','1', true)")  # txn-local, mimics attest fn
        cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
        cur.execute("select status from ops.apparatus where id=%s",(aid,))
        assert cur.fetchone()[0]=="Complete"
        cur.execute("rollback to savepoint s")
