"""apex-jobs agent-runner — execute a kind='agent' job in an isolated git
worktree via a headless agent CLI; capture the branch diff + structured result;
open a promotion gate on success. Offline-testable by injecting agent_cmd (the
fake agent), so the whole runner is exercised without claude / tokens / OAuth.

REPO + RUNS_DIR are resolved at call time from the env so tests can redirect them.
"""
import os
import subprocess
import threading

from . import engine

DEFAULT_REPO = os.path.expanduser("~/code/apex/apex-orch-lane")
DEFAULT_RUNS_DIR = os.path.expanduser("~/.apex-jobs/runs")
TIMEOUT_S = int(os.environ.get("APEX_JOBS_AGENT_TIMEOUT_S", "3600"))

# Per-target headless agent command templates; {prompt} is substituted. Exact
# claude flags are pinned in Task 0 Step 4 before the live path is trusted.
AGENT_CMD = {
    "cc": ["claude", "-p", "{prompt}", "--output-format", "json"],
    "codex": ["codex", "exec", "{prompt}"],
}


def _repo():
    return os.environ.get("APEX_JOBS_REPO", DEFAULT_REPO)


def _runs_dir():
    return os.environ.get("APEX_JOBS_RUNS_DIR", DEFAULT_RUNS_DIR)


def _git(*args, cwd, check=True):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=check)


def _agent_argv(target, prompt):
    tmpl = AGENT_CMD.get(target if target in AGENT_CMD else "cc")
    return [a.replace("{prompt}", prompt) for a in tmpl]


def run_agent_job(job, env, as_="cc", agent_cmd=None):
    """Run a kind='agent' job in an isolated worktree; capture diff + result; on
    success open a promotion gate (leaving the worktree intact for review).
    agent_cmd overrides the agent CLI (the fake agent, in tests)."""
    repo, runs = _repo(), _runs_dir()
    run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # raises GateError if gated

    base_ref = job.get("base_ref") or _git("rev-parse", "--abbrev-ref", "HEAD",
                                            cwd=repo).stdout.strip()
    if not job.get("base_ref"):
        engine.set_base_ref(job["id"], base_ref)
    branch = f"job/{job['dispatch_id']}"
    wt = os.path.join(runs, job["dispatch_id"])
    os.makedirs(runs, exist_ok=True)
    _git("worktree", "remove", "--force", wt, cwd=repo, check=False)   # idempotent (requeue-safe)
    _git("branch", "-D", branch, cwd=repo, check=False)
    _git("worktree", "add", "-b", branch, wt, base_ref, cwd=repo)

    prompt = (job.get("payload") or {}).get("prompt", "")
    argv = agent_cmd or _agent_argv(job.get("target", "cc"), prompt)

    # Heartbeat the lease during long runs; harmless for fast (fake) runs.
    stop = threading.Event()

    def _hb():
        while not stop.wait(max(1, engine.LEASE_TTL_S // 3)):
            try:
                engine.heartbeat(run_id)
            except Exception:
                pass

    threading.Thread(target=_hb, daemon=True).start()
    try:
        proc = subprocess.run(argv, cwd=wt, env={**os.environ, "APEX_JOB_ENV": env},
                              capture_output=True, text=True, timeout=TIMEOUT_S)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 124, (e.stdout or ""), f"timeout after {TIMEOUT_S}s"
    finally:
        stop.set()

    # Capture work: commit anything the agent left, then diff the branch vs base.
    _git("add", "-A", cwd=wt, check=False)
    _git("-c", "user.email=apex-jobs@local", "-c", "user.name=apex-jobs",
         "commit", "-m", f"agent:{job['dispatch_id']}", "--allow-empty", cwd=wt, check=False)
    diff_stat = _git("diff", "--stat", f"{base_ref}...{branch}", cwd=wt, check=False).stdout
    diff = _git("diff", f"{base_ref}...{branch}", cwd=wt, check=False).stdout
    result = {"stdout": out[-4000:], "stderr": err[-4000:],
              "diff": diff[-8000:], "no_changes": diff.strip() == ""}

    status = engine.report(run_id, exit_code=rc, result=result)
    engine.set_run_artifacts(run_id, worktree_path=wt, branch=branch, diff_stat=diff_stat)
    if status == "succeeded":
        engine.open_promotion(job["id"])
    return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
            "no_changes": result["no_changes"]}
