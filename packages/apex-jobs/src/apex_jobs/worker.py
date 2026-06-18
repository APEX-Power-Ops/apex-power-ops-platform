"""apex-jobs worker - claim an eligible job, run its payload.command in a
subprocess tagged with the worker's env, and record the run in the ledger.

The env + human-approval gates are enforced by engine.start(): a job whose
env_required doesn't match this worker's env is parked 'blocked' (GateError),
and a job with open approval gates is never eligible to claim in the first place.
"""
import os
import subprocess
import time

from . import engine


def run_once(as_, env):
    """Claim and run one eligible job end-to-end. Returns a summary dict, None if
    nothing was eligible, or {'job', 'gated'} if a gate refused it after claim."""
    job = engine.claim(as_=as_, env=env)
    if job is None:
        return None
    try:
        run_id = engine.start(job["id"], claimed_by=as_, run_env=env)
    except engine.GateError as e:
        return {"job": job["dispatch_id"], "gated": str(e)}
    command = (job.get("payload") or {}).get("command", "true")
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        env={**os.environ, "APEX_JOB_ENV": env},
    )
    status = engine.report(
        run_id, exit_code=proc.returncode,
        result={"stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]},
    )
    return {"job": job["dispatch_id"], "run": str(run_id),
            "status": status, "exit_code": proc.returncode}


def run_forever(as_, env, poll_s=5.0):
    """Drain eligible jobs forever; sleep poll_s when the queue is empty."""
    while True:
        if run_once(as_, env) is None:
            time.sleep(poll_s)
