"""apex-jobs agent-runner — execute a kind='agent' job in an isolated git
worktree via a headless agent CLI; capture the branch diff + structured result;
open a promotion gate on success. Offline-testable by injecting agent_cmd (the
fake agent), so the whole runner is exercised without claude / tokens / OAuth.

REPO + RUNS_DIR are resolved at call time from the env so tests can redirect them.
run_pool() fans execution out across threads, bounded by `concurrency`.
"""
import logging
import os
import subprocess
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from . import engine
from . import _env

DEFAULT_REPO = os.path.expanduser("~/code/apex/apex-orch-lane")
DEFAULT_RUNS_DIR = os.path.expanduser("~/.apex-jobs/runs")
TIMEOUT_S = int(os.environ.get("APEX_JOBS_AGENT_TIMEOUT_S", "3600"))

# Serialize the git worktree-admin plumbing (remove / branch -D / worktree add)
# across pool threads: `git worktree add` and ref deletes briefly lock the shared
# repo, so concurrent setup would race on index.lock / packed-refs. The agent
# subprocess — the part we actually want to run in parallel — runs OUTSIDE this
# lock, as do per-worktree `add`/`commit` (distinct index + distinct ref) and the
# read-only diff.
_WORKTREE_LOCK = threading.Lock()
log = logging.getLogger(__name__)

# Per-target headless agent command templates; {prompt} is substituted. Exact
# claude flags are pinned in Task 0 Step 4 before the live path is trusted.
AGENT_CMD = {
    "cc": ["claude", "-p", "{prompt}", "--output-format", "json", "--permission-mode", "acceptEdits"],
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



# A cross-engine (Codex) review: the worktree is checked out (detached) at the ref
# under review, so `codex exec review --base <base_ref>` diffs review_head against
# base_ref and prints findings to stdout (the review subcommand has no --json/-o).
REVIEW_CMD = ["codex", "exec", "review", "--base", "{base}"]


def _review_argv(base_ref):
    # NB: codex `exec review --base` is mutually exclusive with a [PROMPT] positional
    # ("--base cannot be used with [PROMPT]"), so a base-diff review carries no prompt;
    # review focus is applied by the IRP synthesis layer, not the codex invocation.
    return [a.replace("{base}", base_ref) for a in REVIEW_CMD]


_DEFAULT_AGENT_PATH = os.pathsep.join([
    "/home/olares/.local/share/fnm/node-versions/v22.22.2/installation/bin",  # claude (fnm)
    "/home/olares/.nvm/versions/node/v20.20.2/bin",                            # codex (nvm v20)
])


def _agent_env(job_env):
    """Subprocess env for the agent/review CLI: the shared default-deny allowlist
    (_env.sanitized_env -- exact names plus the LC_/XDG_ prefixes) plus the
    APEX_JOB_ENV marker, with the agent bin dir(s) prepended to PATH so `claude` /
    `codex` (and their node) resolve under the non-interactive worker (neither is on
    the login PATH). The worker's ambient secrets (DB passwords, DSNs, tokens) are
    NOT inherited. APEX_JOBS_AGENT_PATH is read only to compute the PATH prepend; it
    is not exported. Override the bins via APEX_JOBS_AGENT_PATH."""
    extra = os.environ.get("APEX_JOBS_AGENT_PATH", _DEFAULT_AGENT_PATH)
    return _env.sanitized_env(job_env, extra_path=extra)


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
    with _WORKTREE_LOCK:                                            # serialize repo-admin plumbing
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
        proc = subprocess.run(argv, cwd=wt, env=_agent_env(env),
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


def _cleanup_review_worktree(repo, wt, run_id):
    """Decide + apply cleanup for a SUCCEEDED, non-kept review worktree. Caller has
    already confirmed status=='succeeded' and keep is false. Runs under _WORKTREE_LOCK.
    OWNS the fs mutation and returns the TRUE disposition label. Value-silent: returns a
    bare label, never a path or git stderr. Guard order is load-bearing (fs truth first):
      1. absent    -> dir already gone -> 'already_absent'
      2. currency  -> present but not the current attempt -> 'superseded_preserved' (touch nothing)
      3. dirtiness -> git status --porcelain --ignored non-empty -> 'dirty_preserved' (never remove)
      4. remove    -> plain `git worktree remove` (NEVER --force): rc 0 -> 'cleaned', else 'failed_preserved'
    """
    with _WORKTREE_LOCK:
        if not os.path.isdir(wt):
            return "already_absent"
        if not engine.run_is_current(run_id):
            return "superseded_preserved"
        st = _git("status", "--porcelain", "--ignored", cwd=wt, check=False)
        if st.returncode != 0:
            return "failed_preserved"
        if st.stdout.strip():
            return "dirty_preserved"
        r = _git("worktree", "remove", wt, cwd=repo, check=False)   # plain, NEVER --force
        return "cleaned" if r.returncode == 0 else "failed_preserved"

def run_review_job(job, env, as_="cc", agent_cmd=None):
    """Run a kind='agent' REVIEW job: check out the ref under review
    (payload.review_head, DETACHED) in an isolated worktree, run
    `codex exec review --base <base_ref>`, and capture the findings (stdout) as the
    run result. Read-only — NO commit, NO diff, and NO promotion gate: a review only
    reports, there is nothing to merge. agent_cmd overrides the CLI (fake, in tests)."""
    repo, runs = _repo(), _runs_dir()
    run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # raises GateError if gated

    base_ref = job.get("base_ref") or _git("rev-parse", "--abbrev-ref", "HEAD",
                                            cwd=repo).stdout.strip()
    if not job.get("base_ref"):
        engine.set_base_ref(job["id"], base_ref)
    review_head = (job.get("payload") or {}).get("review_head") or "HEAD"
    wt = os.path.join(runs, job["dispatch_id"])
    os.makedirs(runs, exist_ok=True)
    with _WORKTREE_LOCK:                                            # serialize repo-admin plumbing
        _git("worktree", "remove", "--force", wt, cwd=repo, check=False)   # idempotent (requeue-safe)
        _git("worktree", "add", "--detach", wt, review_head, cwd=repo)

    argv = agent_cmd or _review_argv(base_ref)

    # Heartbeat the lease during long reviews; harmless for fast (fake) runs.
    stop = threading.Event()

    def _hb():
        while not stop.wait(max(1, engine.LEASE_TTL_S // 3)):
            try:
                engine.heartbeat(run_id)
            except Exception:
                pass

    threading.Thread(target=_hb, daemon=True).start()
    try:
        proc = subprocess.run(argv, cwd=wt, env=_agent_env(env),
                              capture_output=True, text=True, timeout=TIMEOUT_S)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 124, (e.stdout or ""), f"timeout after {TIMEOUT_S}s"
    finally:
        stop.set()

    result = {"findings": out[-8000:], "stderr": err[-4000:],
              "review_head": review_head, "base_ref": base_ref, "is_review": True}
    status = engine.report(run_id, exit_code=rc, result=result)
    engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)
    # NO open_promotion: a review reports findings; there is nothing to merge.
    return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
            "review_head": review_head, "findings_len": len(out)}


def _run_one(job, env, as_, agent_cmd):
    """Dispatch one already-claimed job: agent → the runner, command → the worker
    (lazy import avoids an import cycle — worker imports engine, agent_runner does too)."""
    if job.get("kind") == "agent":
        if (job.get("payload") or {}).get("review_head"):
            return run_review_job(job, env, as_=as_, agent_cmd=agent_cmd)
        return run_agent_job(job, env, as_=as_, agent_cmd=agent_cmd)
    from .worker import _run_command_job
    return _run_command_job(job, env, as_)


def run_pool(as_, env, concurrency=4, agent_cmd=None, max_jobs=None):
    """Drain eligible jobs, at most `concurrency` executing at once, until the queue
    is empty and every in-flight job finishes (or `max_jobs` have completed). Claims
    run serially on this thread — FOR UPDATE SKIP LOCKED already makes concurrent
    claiming safe, but serial claiming keeps ordering deterministic; only execution
    fans out. Returns the list of per-job summaries (claim order is not guaranteed)."""
    results, in_flight = [], set()
    submitted = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        while True:
            engine.reap()                                   # opportunistic crash recovery
            while len(in_flight) < concurrency and (max_jobs is None or submitted < max_jobs):
                job = engine.claim(as_=as_, env=env)
                if job is None:
                    break
                in_flight.add(ex.submit(_run_one, job, env, as_, agent_cmd))
                submitted += 1
            if not in_flight:
                break                                       # queue drained, nothing running
            done, in_flight = wait(in_flight, return_when=FIRST_COMPLETED)
            for fut in done:
                try:
                    results.append(fut.result())
                except Exception as exc:    # isolate one job's failure; its run is left for the reaper
                    results.append({"error": str(exc)})
            if max_jobs is not None and len(results) >= max_jobs:
                break
    return results
