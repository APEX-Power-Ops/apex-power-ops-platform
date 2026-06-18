"""TDD - run-ledger finalize via report() (success + failure paths)."""
from apex_jobs.engine import claim, enqueue, get_job, report, start


def test_report_success(conn_test):
    enqueue(dispatch_id="r-ok", title="x", env_required="host")
    job = claim(as_="cc")
    run_id = start(job["id"], claimed_by="cc", run_env="host")
    status = report(run_id, exit_code=0, result={"ok": True})
    assert status == "succeeded"
    assert get_job("r-ok")["status"] == "succeeded"
    row = conn_test.execute(
        "select status, exit_code, finished_at, result, env "
        "from jobs.run where id=%s",
        (run_id,),
    ).fetchone()
    assert row[0] == "succeeded"
    assert row[1] == 0
    assert row[2] is not None
    assert row[3] == {"ok": True}
    assert row[4] == "host"  # the trust evidence is recorded


def test_report_failure(conn_test):
    enqueue(dispatch_id="r-fail", title="x", env_required="host")
    job = claim(as_="cc")
    run_id = start(job["id"], claimed_by="cc", run_env="host")
    status = report(run_id, exit_code=1, result={"stderr": "boom"})
    assert status == "failed"
    assert get_job("r-fail")["status"] == "failed"
