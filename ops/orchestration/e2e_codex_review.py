"""Live `codex exec review` e2e (Cycles 2-3 capstone). Sets up a small diff, enqueues
a kind='agent' REVIEW job (target=codex), and runs run_review_job with REAL codex (no
fake agent). Proves: real codex runs via the runner, findings are captured in the run
result, and NO promotion gate is opened (a review only reports). Runs against
orchestration_dev; driven DIRECTLY (not run_pool) so it never claims another pending
job. Cleans up its git branches/worktrees at the end, leaving the job row as audit."""
import os
import subprocess

from apex_jobs import engine, agent_runner

REPO = os.environ["APEX_JOBS_REPO"]
RUNS = os.environ["APEX_JOBS_RUNS_DIR"]
DISP = "codex-review-e2e"
BASE = "e2e-review-base"
HEAD = "e2e-review-head"


def sh(*args, check=False):
    return subprocess.run(args, capture_output=True, text=True, check=check)


def cleanup_git():
    sh("git", "-C", REPO, "worktree", "remove", "--force", os.path.join(RUNS, DISP))
    sh("git", "-C", REPO, "worktree", "remove", "--force", os.path.join(RUNS, "_e2e_setup"))
    sh("git", "-C", REPO, "worktree", "prune")
    sh("git", "-C", REPO, "branch", "-D", HEAD)
    sh("git", "-C", REPO, "branch", "-D", BASE)


def cleanup_db():
    with engine._conn() as c:
        with c.cursor() as cur:
            cur.execute("select id from jobs.job where dispatch_id=%s", (DISP,))
            for r in cur.fetchall():
                jid = r["id"]
                cur.execute("delete from jobs.gate where job_id=%s", (jid,))
                cur.execute("delete from jobs.run where job_id=%s", (jid,))
                cur.execute("delete from jobs.job where id=%s", (jid,))
        c.commit()


# ---- fresh setup ----
cleanup_git()
cleanup_db()
os.makedirs(RUNS, exist_ok=True)
sh("git", "-C", REPO, "branch", BASE, "HEAD", check=True)
tmpwt = os.path.join(RUNS, "_e2e_setup")
sh("git", "-C", REPO, "worktree", "add", "-b", HEAD, tmpwt, BASE, check=True)
with open(os.path.join(tmpwt, "REVIEW_ME.py"), "w") as f:
    f.write("def add(a, b):\n    # BUG: subtracts instead of adding\n    return a - b\n")
sh("git", "-C", tmpwt, "add", "-A", check=True)
sh("git", "-C", tmpwt, "-c", "user.email=apex-jobs@local", "-c", "user.name=apex-jobs",
   "commit", "-m", "e2e review target: intentional add/sub bug", check=True)
sh("git", "-C", REPO, "worktree", "remove", "--force", tmpwt)

# ---- enqueue ----
jid = engine.enqueue(dispatch_id=DISP, title="codex review e2e", env_required="host",
                     payload={"review_head": HEAD})
with engine._conn() as c:
    with c.cursor() as cur:
        cur.execute("update jobs.job set kind='agent', target='codex', base_ref=%s where id=%s",
                    (BASE, jid))
    c.commit()

# ---- run REAL codex ----
job = engine.get_job(DISP)
print("RUNNING run_review_job with REAL codex (base=%s head=%s) ..." % (BASE, HEAD), flush=True)
summary = agent_runner.run_review_job(job, env="host")
print("SUMMARY:", summary, flush=True)

# ---- assert ----
run = engine.runs_for(DISP)[-1]
res = run["result"] or {}
findings = res.get("findings", "") or ""
print("RUN STATUS:", run["status"])
print("IS_REVIEW:", res.get("is_review"), "BASE:", res.get("base_ref"), "HEAD:", res.get("review_head"))
print("RUN BRANCH (recorded):", run.get("branch"))
print("FINDINGS LEN:", len(findings))
print("---- FINDINGS (first 2500) ----", flush=True)
print(findings[:2500], flush=True)
print("---- STDERR (first 600) ----", flush=True)
print((res.get("stderr") or "")[:600], flush=True)

gates = engine.gates_for(DISP)
assert not any(g["gate_type"] == "promotion" for g in gates), "FAIL: review opened a promotion gate"
assert res.get("is_review") is True, "FAIL: result not tagged is_review"
assert run["status"] in ("succeeded", "failed")
print("ASSERTS OK: no promotion gate; is_review=True; job status=%s" % engine.get_job(DISP)["status"])
print("E2E DONE")

cleanup_git()
print("GIT CLEANED")
