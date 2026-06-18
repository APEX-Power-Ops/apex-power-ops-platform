"""TDD - the worker loop: claim -> gate-check -> subprocess -> report."""
from apex_jobs.engine import enqueue, get_job
from apex_jobs.worker import run_once


def test_worker_runs_noop_success(conn_test):
    enqueue(dispatch_id="w-ok", title="x", env_required="host",
            payload={"command": "echo hi"})
    r = run_once(as_="cc", env="host")
    assert r is not None
    assert r["status"] == "succeeded"
    assert r["exit_code"] == 0
    assert get_job("w-ok")["status"] == "succeeded"


def test_worker_reports_failure(conn_test):
    enqueue(dispatch_id="w-fail", title="x", env_required="host",
            payload={"command": "exit 1"})
    r = run_once(as_="cc", env="host")
    assert r["status"] == "failed"
    assert r["exit_code"] == 1
    assert get_job("w-fail")["status"] == "failed"


def test_worker_no_eligible_returns_none(conn_test):
    assert run_once(as_="cc", env="host") is None


def test_worker_respects_env_gate(conn_test):
    enqueue(dispatch_id="w-gate", title="x", env_required="host",
            payload={"command": "true"})
    r = run_once(as_="cc", env="sandbox")  # wrong env
    assert r is not None and "gated" in r
    assert get_job("w-gate")["status"] == "blocked"
