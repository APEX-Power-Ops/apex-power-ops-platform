import uuid
import psycopg, pytest
from ops_intake import recognition as rec

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return str(c.execute("insert into ops.persons (display_name) values ('PM') returning person_id").fetchone()[0])

def _eligible(dsn, status="In Progress"):
    with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
        cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                    " values (%s,'P','Active','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
        pid=cur.fetchone()[0]
        cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                    " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
        sid=cur.fetchone()[0]
        cur.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
                    "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())",(sid,))
        cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                    "quoted_hours,quoted_revenue,source) values (%s,'A',%s,'approved',10,1500,'ops-intake') returning id",
                    (sid,status))
        return str(cur.fetchone()[0])

def test_attest_then_recognize_then_reverse_then_revoke(clean_ops, admin_dsn, api_dsn):
    who=_person(admin_dsn); aid=_eligible(admin_dsn)
    att=rec.attest_complete(api_dsn, aid, who, "tested ok"); assert isinstance(att,str)
    ev=rec.recognize(api_dsn, aid, who, "not_applicable", None, "not_applicable", None); assert isinstance(ev,str)
    rv=rec.reverse(api_dsn, ev, who, "correction"); assert isinstance(rv,str)
    out=rec.revoke(api_dsn, att, who, "superseded"); assert out==att

def test_second_active_attest_raises_conflict_value_free(clean_ops, admin_dsn, api_dsn):
    who=_person(admin_dsn); aid=_eligible(admin_dsn)
    rec.attest_complete(api_dsn, aid, who, "x")
    with pytest.raises(rec.RecognitionConflict) as ei:
        rec.attest_complete(api_dsn, aid, who, "y")
    assert "$" not in str(ei.value) and "1500" not in str(ei.value)

def test_unknown_actor_raises_input_error_value_free(clean_ops, admin_dsn, api_dsn):
    aid=_eligible(admin_dsn)
    with pytest.raises(rec.RecognitionInputError) as ei:
        rec.attest_complete(api_dsn, aid, str(uuid.uuid4()), "x")
    assert "$" not in str(ei.value)

def test_blank_reason_raises_input_error(clean_ops, admin_dsn, api_dsn):
    who=_person(admin_dsn); aid=_eligible(admin_dsn)
    with pytest.raises(rec.RecognitionInputError):
        rec.attest_complete(api_dsn, aid, who, "   ")

def test_revoke_open_recognition_raises_conflict(clean_ops, admin_dsn, api_dsn):
    who=_person(admin_dsn); aid=_eligible(admin_dsn)
    att=rec.attest_complete(api_dsn, aid, who, "x")
    rec.recognize(api_dsn, aid, who, "not_applicable", None, "not_applicable", None)
    with pytest.raises(rec.RecognitionConflict):
        rec.revoke(api_dsn, att, who, "nope")

def test_recognize_without_attestation_raises_state_error(clean_ops, admin_dsn, api_dsn):
    who=_person(admin_dsn); aid=_eligible(admin_dsn)
    # Force apparatus to Complete via the ctx bypass (inside a transaction so SET LOCAL persists
    # through the UPDATE in the same txn) WITHOUT inserting a completion_attestation row.
    # This exercises the approve_and_recognize gate that rejects a Complete apparatus that
    # has no active attestation (009 firewall: 'no active completion attestation').
    # Setup DML - the sanctioned superuser tier (admin_dsn), NOT the writer/api login roles.
    with psycopg.connect(admin_dsn, autocommit=False) as c, c.cursor() as cur:
        cur.execute("set local ops.completion_ctx='1'")
        cur.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        c.commit()
    with pytest.raises(rec.RecognitionStateError):
        rec.recognize(api_dsn, aid, who, "not_applicable", None, "not_applicable", None)

def test_intake_apparatus_insert_still_succeeds_under_completion_guard(clean_ops, admin_dsn):
    """REGRESSION (Chip-5 intake must not break under the T2 apparatus_completion_guard):
    the merged ops-intake approve_run materialization inserts apparatus at status='Not Started'
    (insert_apparatus in load.py) and approve.py later stamps provenance_status='approved'.
    Neither the 'Not Started' insert NOR the post-approve 'approved' state is governed-complete
    (g := status='Complete' AND provenance_status='approved'), so the T2 guard MUST NOT fire and
    the apparatus row MUST exist. This pins that 009 does not regress intake. We drive a direct
    INSERT mirroring approve.py's post-approval apparatus state (provenance_status='approved',
    status='Not Started') after 009 is applied, with NO completion ctx set.

    This is a guard-behavior probe (explicit status= literal), not the writer-path equivalent -
    the writer-path insert_apparatus (no status column) is proven in test_012's positive pipeline.
    Runs on admin_dsn."""
    with psycopg.connect(admin_dsn, autocommit=True) as c, c.cursor() as cur:
        cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                    " values (%s,'P','Active','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
        pid=cur.fetchone()[0]
        cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                    " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
        sid=cur.fetchone()[0]
        # mirrors approve.py's post-approval apparatus row: approved + NOT governed-complete.
        # NO ops.completion_ctx is set -> the guard must allow this because it is not entering g.
        cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                    "quoted_hours,quoted_revenue,source) values (%s,'A-1','Not Started','approved',10,1500,'ops-intake')"
                    " returning id",(sid,))
        aid=cur.fetchone()[0]
        cur.execute("select status, provenance_status from ops.apparatus where id=%s",(aid,))
        assert cur.fetchone()==("Not Started","approved"), "intake-style approved/Not-Started insert was blocked by the guard"


# ---------------------------------------------------------------------------
# Task 9: real-login SET ROLE denials + package-tier forge-closure proof
# ---------------------------------------------------------------------------

def test_login_roles_cannot_set_role_fn_owner(writer_dsn, api_dsn):
    """Proof (h): a REAL login session (session_user = the role) cannot SET ROLE
    ops_fn_owner. (test_012 can only assert pg_has_role - SET ROLE permission is
    checked against session_user, which stays postgres there.)"""
    for d in (writer_dsn, api_dsn):
        with psycopg.connect(d) as c, c.cursor() as cur:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                cur.execute("set role ops_fn_owner")


def test_writer_cannot_recognize_forge_closure(clean_ops, admin_dsn, writer_dsn):
    """Forge-closure at the package tier: the writer identity cannot attest, even via
    the wrappers. The wrapper may translate the error - the contract is: the call FAILS
    and no attestation row exists."""
    who = _person(admin_dsn)
    aid = _eligible(admin_dsn)
    with pytest.raises(Exception):
        rec.attest_complete(writer_dsn, aid, who, "forged")
    with psycopg.connect(admin_dsn, autocommit=True) as c:
        n = c.execute(
            "select count(*) from ops.completion_attestation where apparatus_id=%s", (aid,)
        ).fetchone()[0]
        assert n == 0, "a forged attestation row landed"
