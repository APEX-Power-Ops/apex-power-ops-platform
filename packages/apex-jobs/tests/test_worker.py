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


def test_worker_skips_mismatched_env(conn_test):
    # env-filtered claim: a sandbox worker does NOT claim a host-only job; it stays
    # pending for a host worker (the old claim-then-block path is gone by design).
    enqueue(dispatch_id="w-gate", title="x", env_required="host",
            payload={"command": "true"})
    assert run_once(as_="cc", env="sandbox") is None       # not claimed (env filtered)
    assert get_job("w-gate")["status"] == "pending"        # stays claimable
    r = run_once(as_="cc", env="host")                     # a host worker runs it
    assert r is not None and r["status"] == "succeeded"
