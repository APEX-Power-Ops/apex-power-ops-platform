"""TDD - env gate (at start) + human-approval gate (at the queue boundary)."""
import pytest

from apex_jobs.engine import GateError, approve, claim, enqueue, get_job, start


def _open_gate_id(conn, dispatch_id):
    return conn.execute(
        "select g.id from jobs.gate g join jobs.job j on j.id=g.job_id "
        "where j.dispatch_id=%s and g.state='pending'",
        (dispatch_id,),
    ).fetchone()[0]


def test_env_gate_refuses_wrong_env(conn_test):
    enqueue(dispatch_id="g-env", title="x", env_required="host")
    job = claim(as_="cc")  # claimable: no approval gate
    assert job["dispatch_id"] == "g-env"
    with pytest.raises(GateError):
        start(job["id"], claimed_by="cc", run_env="sandbox")
    assert get_job("g-env")["status"] == "blocked"
    run_id = start(job["id"], claimed_by="cc", run_env="host")
    assert run_id is not None
    assert get_job("g-env")["status"] == "running"


def test_human_gate_blocks_until_approved(conn_test):
    enqueue(dispatch_id="g-appr", title="x", requires_approval=True, gate_categories=["schema"])
    assert claim(as_="cc") is None  # open gate -> not claimable
    approve(_open_gate_id(conn_test, "g-appr"), by="operator")
    job = claim(as_="cc")
    assert job is not None and job["dispatch_id"] == "g-appr"
    run_id = start(job["id"], claimed_by="cc", run_env="host")
    assert run_id is not None
    assert get_job("g-appr")["status"] == "running"
