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

def test_attest_then_recognize_then_reverse_then_revoke(clean_ops):
    dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
    att=rec.attest_complete(dsn, aid, who, "tested ok"); assert isinstance(att,str)
    ev=rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None); assert isinstance(ev,str)
    rv=rec.reverse(dsn, ev, who, "correction"); assert isinstance(rv,str)
    out=rec.revoke(dsn, att, who, "superseded"); assert out==att

def test_second_active_attest_raises_conflict_value_free(clean_ops):
    dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
    rec.attest_complete(dsn, aid, who, "x")
    with pytest.raises(rec.RecognitionConflict) as ei:
        rec.attest_complete(dsn, aid, who, "y")
    assert "$" not in str(ei.value) and "1500" not in str(ei.value)

def test_unknown_actor_raises_input_error_value_free(clean_ops):
    dsn=clean_ops; aid=_eligible(dsn)
    with pytest.raises(rec.RecognitionInputError) as ei:
        rec.attest_complete(dsn, aid, str(uuid.uuid4()), "x")
    assert "$" not in str(ei.value)

def test_blank_reason_raises_input_error(clean_ops):
    dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
    with pytest.raises(rec.RecognitionInputError):
        rec.attest_complete(dsn, aid, who, "   ")

def test_revoke_open_recognition_raises_conflict(clean_ops):
    dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
    att=rec.attest_complete(dsn, aid, who, "x")
    rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None)
    with pytest.raises(rec.RecognitionConflict):
        rec.revoke(dsn, att, who, "nope")

def test_recognize_without_attestation_raises_state_error(clean_ops):
    dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
    # Force apparatus to Complete via the ctx bypass (inside a transaction so SET LOCAL persists
    # through the UPDATE in the same txn) WITHOUT inserting a completion_attestation row.
    # This exercises the approve_and_recognize gate that rejects a Complete apparatus that
    # has no active attestation (009 firewall: 'no active completion attestation').
    with psycopg.connect(dsn, autocommit=False) as c, c.cursor() as cur:
        cur.execute("set local ops.completion_ctx='1'")
        cur.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        c.commit()
    with pytest.raises(rec.RecognitionStateError):
        rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None)

def test_intake_apparatus_insert_still_succeeds_under_completion_guard(clean_ops):
    """REGRESSION (Chip-5 intake must not break under the T2 apparatus_completion_guard):
    the merged ops-intake approve_run materialization inserts apparatus at status='Not Started'
    (insert_apparatus in load.py) and approve.py later stamps provenance_status='approved'.
    Neither the 'Not Started' insert NOR the post-approve 'approved' state is governed-complete
    (g := status='Complete' AND provenance_status='approved'), so the T2 guard MUST NOT fire and
    the apparatus row MUST exist. This pins that 009 does not regress intake. We drive a direct
    INSERT mirroring approve.py's post-approval apparatus state (provenance_status='approved',
    status='Not Started') after 009 is applied, with NO completion ctx set."""
    dsn=clean_ops
    with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
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
