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


def _run_command_job(job, env, as_):
    """Run an already-claimed kind='command' job: open a run (enforcing the env +
    approval gates), execute payload.command in a subprocess tagged with the worker
    env, and record the ledger. Returns a summary dict, or {'job','gated'} if a gate
    refused it at start(). Shared by run_once and the agent pool's _run_one."""
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


def run_once(as_, env):
    """Claim and run one eligible job end-to-end, dispatching by kind: an 'agent'
    job goes to the worktree-isolating agent_runner, a 'command' job runs its
    payload.command. Returns a summary dict, None if nothing was eligible, or
    {'job', 'gated'} if a gate refused a command job after claim."""
    job = engine.claim(as_=as_, env=env)
    if job is None:
        return None
    if job.get("kind") == "agent":
        from . import agent_runner          # lazy import: avoid the worker<->agent_runner cycle
        return agent_runner.run_agent_job(job, env, as_=as_)
    return _run_command_job(job, env, as_)


def run_forever(as_, env, poll_s=5.0):
    """Drain eligible jobs forever; reap lease-expired runs and sleep poll_s when
    the queue is empty (opportunistic crash recovery on the idle path)."""
    while True:
        if run_once(as_, env) is None:
            engine.reap()
            time.sleep(poll_s)
