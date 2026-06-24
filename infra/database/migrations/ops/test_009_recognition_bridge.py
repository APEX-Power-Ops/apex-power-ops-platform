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

def test_attest_success_sets_complete_and_captures_prior(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'tested ok')",(aid,who))
        att=cur.fetchone()[0]
        cur.execute("select status from ops.apparatus where id=%s",(aid,)); assert cur.fetchone()[0]=="Complete"
        cur.execute("select prior_status, attested_by, reason from ops.completion_attestation where id=%s",(att,))
        ps, ab, r = cur.fetchone(); assert ps=="In Progress" and ab==who and r=="tested ok"
        cur.execute("rollback to savepoint s")

def test_attest_rejects_unapproved_provenance(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, provenance="draft")
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_cancelled_chain(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, scope_status="Cancelled")
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_inactive(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, is_active=False)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_already_complete(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who))   # now Complete + active attestation
        # revoke nothing; a second attest must fail (status already Complete AND unique index)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'y')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_unfrozen_basis(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, frozen=False)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_nonpositive_basis(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, quoted_revenue=0)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_unknown_actor(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s")
        aid=_seed_eligible_apparatus(cur)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,str(uuid.uuid4()))); assert False
        except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
        cur.execute("rollback to savepoint s")

def test_attest_rejects_blank_reason(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur)
        try:
            cur.execute("select ops.attest_apparatus_complete(%s,%s,'   ')",(aid,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_revoke_blocked_when_net_positive(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        try:
            cur.execute("select ops.revoke_completion_attestation(%s,%s,'oops')",(att,who))
            assert False, "revoke with open recognition accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_revoke_after_reverse_restores_prior_and_marks_revoked(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        ev=cur.fetchone()[0]
        cur.execute("select ops.reverse_recognition(%s,%s,'correction')",(ev,who))   # net back to 0
        cur.execute("select ops.revoke_completion_attestation(%s,%s,'superseded')",(att,who))
        cur.execute("select status from ops.apparatus where id=%s",(aid,)); assert cur.fetchone()[0]=="In Progress"
        cur.execute("select revoked_at is not null, revoked_by, revoke_reason from ops.completion_attestation where id=%s",(att,))
        ra, rb, rr = cur.fetchone(); assert ra is True and rb==who and rr=="superseded"
        cur.execute("rollback to savepoint s")

def test_revoke_unknown_actor_rejected(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        try:
            cur.execute("select ops.revoke_completion_attestation(%s,%s,'x')",(att,str(uuid.uuid4()))); assert False
        except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
        cur.execute("rollback to savepoint s")

def test_revoke_blank_reason_rejected(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        try:
            cur.execute("select ops.revoke_completion_attestation(%s,%s,'  ')",(att,who)); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def _recognize(cur, who, *, status="In Progress"):
    aid=_seed_eligible_apparatus(cur, status=status)
    cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
    cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
    ev=cur.fetchone()[0]
    return aid, att, ev

def test_recognize_populates_completion_attestation_id(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid, att, ev=_recognize(cur, who)
        cur.execute("select completion_attestation_id from ops.revenue_recognition_event where id=%s",(ev,))
        assert cur.fetchone()[0]==att
        cur.execute("rollback to savepoint s")

def test_approve_and_recognize_rejects_when_no_active_attestation(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select set_config('ops.completion_ctx','1', true)")   # flip to Complete WITHOUT an attestation
        cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
        try:
            cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
            assert False, "recognize with no active attestation accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def _direct_recognized_insert(cur, aid, sid, pid, amount, qh, br, frozen_at, att_id):
    cur.execute("insert into ops.revenue_recognition_event"
                " (apparatus_id, scope_id, project_id, event_type, recognized_amount, quoted_hours,"
                "  blended_rate, basis_frozen_at, actor_person_id, datasheet_clearance, cx_clearance,"
                "  completion_attestation_id)"
                " select %s,%s,%s,'recognized',%s,%s,%s,%s, (select person_id from ops.persons limit 1),"
                " 'not_applicable','not_applicable',%s",
                (aid, sid, pid, amount, qh, br, frozen_at, att_id))

def _chain_ids(cur, aid):
    cur.execute("select a.scope_id, s.project_id, a.quoted_revenue, a.quoted_hours, sq.blended_rate, sq.frozen_at"
                " from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                " join ops.scope_quote sq on sq.scope_id=a.scope_id where a.id=%s",(aid,))
    return cur.fetchone()

def test_integrity_rejects_recognized_with_null_attestation(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))   # Complete + active att
        sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, None); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_integrity_rejects_recognized_with_foreign_attestation(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))
        sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, str(uuid.uuid4())); assert False
        except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
        cur.execute("rollback to savepoint s")

def test_integrity_rejects_recognized_with_revoked_attestation(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        # revoke it (net 0, no recognition yet) -> now revoked; status restored to prior
        cur.execute("select ops.revoke_completion_attestation(%s,%s,'r')",(att,who))
        # re-flip to Complete via ctx so the integrity trigger's status check is not the blocker
        cur.execute("select set_config('ops.completion_ctx','1', true)")
        cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
        sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, att); assert False, "revoked attestation accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

def test_integrity_rejects_recognized_with_cross_apparatus_attestation(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid1=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'a1')",(aid1,who)); att1=cur.fetchone()[0]
        aid2=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'a2')",(aid2,who))   # aid2 Complete + own att
        sid,pid,rev,qh,br,fa=_chain_ids(cur,aid2)
        try:
            _direct_recognized_insert(cur, aid2, sid, pid, rev, qh, br, fa, att1)   # att1 belongs to aid1
            assert False, "cross-apparatus attestation accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint s")

# ---- FIREWALL REGRESSION: every original 005 recognized-integrity check still raises ----
def test_firewall_regression_005_checks_still_raise(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
        # (a) lineage: wrong scope_id
        cur.execute("savepoint c")
        try:
            _direct_recognized_insert(cur, aid, str(uuid.uuid4()), pid, rev, qh, br, fa, att); assert False
        except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
        cur.execute("rollback to savepoint c")
        # (b) recognized_amount distinct-from quoted_revenue
        cur.execute("savepoint c")
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev+1, qh, br, fa, att); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint c")
        # (c) basis-snapshot mismatch (wrong quoted_hours)
        cur.execute("savepoint c")
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev, qh+1, br, fa, att); assert False
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint c")
        # (d) status not Complete (revoke restores prior, leaving an active... so test on a non-complete app)
        aid2=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid2,who)); att2=cur.fetchone()[0]
        cur.execute("select ops.revoke_completion_attestation(%s,%s,'r')",(att2,who))  # status back to In Progress, att2 revoked
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'y')",(aid2,who)); att2b=cur.fetchone()[0]  # Complete again
        cur.execute("select set_config('ops.completion_ctx','1', true)")
        cur.execute("update ops.apparatus set status='Pending Review' where id=%s",(aid2,))  # leave g via ctx
        s2,p2,r2,h2,b2,f2=_chain_ids(cur,aid2)
        cur.execute("savepoint c")
        try:
            _direct_recognized_insert(cur, aid2, s2, p2, r2, h2, b2, f2, att2b); assert False, "non-complete accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint c")
        # (e) open-net idempotency: a real recognize, then a second direct recognized insert
        cur.execute("savepoint c")
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        try:
            _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, att); assert False, "double-recognize accepted"
        except psycopg.errors.RaiseException: pass
        cur.execute("rollback to savepoint c")
        cur.execute("rollback to savepoint s")

# ---- DOWN SOURCE-DIFF: after 009-down, both 005 fns equal the 005-up defs (normalized) ----
def _functiondef(dsn, signature):
    with psycopg.connect(dsn) as c, c.cursor() as cur:
        cur.execute("select pg_get_functiondef(%s::regprocedure)", (signature,))
        return cur.fetchone()[0]

def _normalize(sql):
    import re
    return re.sub(r"\s+", " ", sql).strip()

def test_down_restores_005_function_bodies_byte_for_byte():
    AR = "ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)"
    II = "ops.trg_revrec_insert_integrity()"
    # capture the 009-up (modified) defs, then run 009-down, then capture the restored defs
    _exec(DOWN)
    restored_ar = _normalize(_functiondef(DSN, AR))
    restored_ii = _normalize(_functiondef(DSN, II))
    # rebuild a pristine 005-only baseline in a savepoint-free way: drop ops, apply 001..005,
    # read those defs, then restore the full 001..009 session state.
    _clean_slate()
    for f in ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
              "004_person_anchor.sql","005_recognition_ledger.sql"]:
        _exec(HERE / f)
    baseline_ar = _normalize(_functiondef(DSN, AR))
    baseline_ii = _normalize(_functiondef(DSN, II))
    # restore the session post-state (001..009) for the remaining tests
    _clean_slate()
    for f in CHAIN: _exec(HERE / f)
    assert restored_ar == baseline_ar, "approve_and_recognize down-restore != 005-up definition"
    assert restored_ii == baseline_ii, "trg_revrec_insert_integrity down-restore != 005-up definition"

def test_worklist_flags_across_states(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        # (1) fresh eligible -> can_attest only
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        assert cur.fetchone()==(True, False, False, False)
        # (2) attested -> can_recognize + can_revoke
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
        cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        assert cur.fetchone()==(False, True, True, False)
        # (3) recognized -> can_reverse only
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        ev=cur.fetchone()[0]
        cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        assert cur.fetchone()==(False, False, False, True)
        # (4) reversed -> re-recognize + revoke again
        cur.execute("select ops.reverse_recognition(%s,%s,'corr')",(ev,who))
        cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        assert cur.fetchone()==(False, True, True, False)
        cur.execute("rollback to savepoint s")

def test_worklist_carries_project_number_and_basis(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); _seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress", quoted_revenue=1500, quoted_hours=10)
        cur.execute("select project_number, status, quoted_hours, quoted_revenue, net_recognized, is_recognized"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        pn, st, qh, qr, net, isr = cur.fetchone()
        assert pn is not None and st=="In Progress" and float(qr)==1500 and isr is False
        cur.execute("rollback to savepoint s")

def test_worklist_exposes_attestation_and_recognition_columns(conn):
    """The worklist must surface the attestation identity (attested_by/attested_at/
    attest_reason) and the recognition trace (recognized_event_id) correctly:
      - fresh eligible  -> all four NULL
      - after attest    -> attested_by=actor, attested_at set, attest_reason=reason; event still NULL
      - after recognize -> recognized_event_id non-null
      - after reverse   -> recognized_event_id NULL again (v_apparatus_recognition nulls it)."""
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress")
        # (1) fresh eligible: no active attestation, no recognition.
        cur.execute("select attested_by, attested_at, attest_reason, recognized_event_id"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        ab, at_, ar_, rev = cur.fetchone()
        assert ab is None and at_ is None and ar_ is None and rev is None
        # (2) after attest: attestation columns populated; recognition still empty.
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'tested ok')",(aid,who))
        cur.execute("select attested_by, attested_at, attest_reason, recognized_event_id"
                    " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        ab, at_, ar_, rev = cur.fetchone()
        assert ab==who and at_ is not None and ar_=="tested ok" and rev is None
        # (3) after recognize: recognized_event_id is non-null.
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        ev=cur.fetchone()[0]
        cur.execute("select recognized_event_id from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        assert cur.fetchone()[0]==ev, "recognized_event_id not exposed after recognize"
        # (4) after reverse: recognized_event_id goes NULL (per v_apparatus_recognition).
        cur.execute("select ops.reverse_recognition(%s,%s,'corr')",(ev,who))
        cur.execute("select recognized_event_id, attested_by from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        rev2, ab2 = cur.fetchone()
        assert rev2 is None and ab2==who, "recognized_event_id not cleared on reverse / attestation lost"
        cur.execute("rollback to savepoint s")

def test_rollup_sums_recognized_and_resolves_project_number(conn):
    with conn.cursor() as cur:
        cur.execute("savepoint s"); who=_seed_person(cur)
        aid=_seed_eligible_apparatus(cur, status="In Progress", quoted_revenue=1500)
        cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
        pn=cur.fetchone()[0]
        cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))
        cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
        cur.execute("select project_number, recognized_total, recognized_count"
                    " from ops.v_completion_recognition_rollup where project_number=%s",(pn,))
        rpn, rtot, rcnt = cur.fetchone()
        assert rpn==pn and float(rtot)==1500 and rcnt==1
        cur.execute("rollback to savepoint s")

def test_rollup_eligible_count_uses_full_worklist_predicate(conn):
    """eligible_count must use the SAME eligibility predicate as the worklist:
    provenance_status='approved' AND a.is_active AND active non-cancelled scope/project
    chain AND sq.is_frozen. An unfrozen-basis or cancelled-scope apparatus must NOT be
    counted as eligible (and must not appear in the rollup row scope at all)."""
    with conn.cursor() as cur:
        cur.execute("savepoint s"); _seed_person(cur)
        # (1) one fully-eligible apparatus -> eligible_count == 1, and it appears in the worklist.
        aid_ok=_seed_eligible_apparatus(cur, status="In Progress")
        cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_ok,))
        pn=cur.fetchone()[0]
        cur.execute("select eligible_count from ops.v_completion_recognition_rollup where project_number=%s",(pn,))
        assert cur.fetchone()[0]==1, "fully-eligible apparatus not counted in eligible_count"
        # (2) an UNFROZEN-basis apparatus is NOT eligible -> excluded from eligible_count.
        aid_unfrozen=_seed_eligible_apparatus(cur, status="In Progress", frozen=False)
        cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_unfrozen,))
        assert cur.fetchone() is None, "unfrozen-basis apparatus leaked into the worklist"
        cur.execute("select coalesce(max(eligible_count),0) from ops.v_completion_recognition_rollup"
                    " where scope_id=(select scope_id from ops.apparatus where id=%s)",(aid_unfrozen,))
        assert cur.fetchone()[0]==0, "unfrozen-basis apparatus counted as eligible"
        # (3) a CANCELLED-scope apparatus is NOT eligible -> excluded from eligible_count.
        aid_cancelled=_seed_eligible_apparatus(cur, status="In Progress", scope_status="Cancelled")
        cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_cancelled,))
        assert cur.fetchone() is None, "cancelled-scope apparatus leaked into the worklist"
        cur.execute("select coalesce(max(eligible_count),0) from ops.v_completion_recognition_rollup"
                    " where scope_id=(select scope_id from ops.apparatus where id=%s)",(aid_cancelled,))
        assert cur.fetchone()[0]==0, "cancelled-scope apparatus counted as eligible"
        cur.execute("rollback to savepoint s")
