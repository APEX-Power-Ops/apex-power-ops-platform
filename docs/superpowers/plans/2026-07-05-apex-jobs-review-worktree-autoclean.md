# apex-jobs Review-Worktree Auto-Clean — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Have `run_review_job` remove its own disposable worktree after a pristine, succeeded, still-current review — stopping the `~/.apex-jobs/runs/review-*` leak at the source without ever deleting what `prune-review-worktrees` protects and without demoting a good review.

**Architecture:** Two new `engine` DB helpers (`run_is_current`, `set_run_cleanup`), one guarded `agent_runner` cleanup helper (`_cleanup_review_worktree`) that owns the filesystem outcome and returns a fixed-vocabulary label, a truth-preserving exception-isolated tail in `run_review_job`, and a `--keep-worktree` opt-out on both CLI review verbs. No DB schema change; disposition is merged into the existing `jobs.run.result` JSONB.

**Tech Stack:** Python 3, `psycopg` (host Postgres `jobs.*`), `git worktree`/`git status`, `pytest`. Source spec: `docs/superpowers/specs/2026-07-05-apex-jobs-review-worktree-autoclean-design.md` (rev 6, committed `8cf59ae5`).

## Global Constraints

- **Host-canonical single-writer.** Author locally on Windows → `scp` each changed file to the worktree `/home/olares/code/apex/apex-review-autoclean` → run/commit host-side over `ssh olares-mesh`. Edit existing files via a single-buffer patch script (never multi-edit-clobber).
- **Branch:** `orchestration/review-worktree-autoclean` (off main `30b4d1c5`). Spec already committed on it.
- **Test command (host-only; conftest skips without DB env):** `export PATH=$HOME/.local/bin:$PATH`; source the **canonical** `infra/.env` (`/home/olares/code/apex/apex-power-ops-platform/infra/.env` — the worktree's is gitignored/absent); then `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest` from `packages/apex-jobs`.
- **ASCII-only** added lines in code files.
- **Value-silence (lane additions):** `cleanup_status` is one of exactly seven labels; the helper discards git stdout/stderr; swallowed exceptions log `type(e).__name__` only. No paths/DSN/env/file-contents in any lane-added output. (Pre-existing `findings` output is out of scope.)
- **`cleanup_status` vocabulary (exact strings, exhaustive):** `cleaned`, `kept`, `dirty_preserved`, `failed_preserved`, `superseded_preserved`, `already_absent`, `not_attempted`.
- **Dirty definition == prune's:** `git status --porcelain --ignored`, non-empty = dirty.
- **Guard order (load-bearing):** `isdir`→`already_absent`, then currency→`superseded_preserved`, then dirtiness→`dirty_preserved`, then plain remove→`cleaned`/`failed_preserved`. Cleanup runs under `agent_runner._WORKTREE_LOCK`. **The cleanup remove never passes `--force`.**
- **Orthogonality:** review success is committed by `engine.report` before the housekeeping tail; nothing in the tail changes run status or process exit. A cleanup/record failure yields a preserve/failed label, never a demotion.
- **Non-goal (explicit):** no Postgres advisory lock / cross-process worktree lock in this lane. **Future lane** (named, not built here): dispatch/worktree-lifecycle advisory lock around *both* startup worktree create/remove and cleanup remove — closes the cross-process stale-attempt race and the pre-existing startup `--force` race.
- **Finish:** after Task 4, run the full apex-jobs suite green + a **whole-branch Codex cross-engine review** on the implementation before finishing-a-development-branch.

---

## File Structure

- **Modify** `packages/apex-jobs/src/apex_jobs/engine.py` — add `run_is_current`, `set_run_cleanup` (Task 1).
- **Modify** `packages/apex-jobs/src/apex_jobs/agent_runner.py` — add module `log`, `_cleanup_review_worktree` (Task 2); restructure `run_review_job` tail (Task 3).
- **Modify** `packages/apex-jobs/src/apex_jobs/cli.py` — `--keep-worktree` on `review-run` + `enqueue-review`, OR-merge payload, `cleanup_status` in `--json` (Task 4).
- **Create** `packages/apex-jobs/tests/test_review_autoclean.py` — the 15-case matrix (Tasks 1–4 each add their rows).
- **Unchanged / regression gate:** `packages/apex-jobs/tests/test_prune.py` must stay green.

**Test harness note (applies to every task):** reuse the existing `tests/test_prune.py` fixtures. It already provisions a throwaway git repo, a `runs` dir, `orchestration_test` env (`APEX_JOBS_REPO`/`APEX_JOBS_DB`), and helpers to enqueue review jobs and seed runs. Read `test_prune.py` first and import/mirror its fixture (e.g. `prune_env`) and seed helpers rather than re-inventing them. The fake review agent is driven by the `APEX_JOBS_AGENT_CMD` JSON-argv seam consumed by `run_review_job(..., agent_cmd=...)`; a fake is a JSON argv run in `cwd=wt`:
- pristine: `["sh","-c","echo FINDINGS; exit 0"]`
- untracked dirt: `["sh","-c","echo x > untracked.txt; echo FINDINGS; exit 0"]`
- ignored dirt: `["sh","-c","mkdir -p __pycache__; echo x > __pycache__/x.pyc; echo FINDINGS; exit 0"]` (ensure the throwaway repo's `.gitignore` ignores `__pycache__/`)
- failure: `["sh","-c","exit 1"]`

---

## Task 1: Engine helpers — `run_is_current` + `set_run_cleanup`

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/engine.py` (append two functions near `set_run_artifacts`)
- Test: `packages/apex-jobs/tests/test_review_autoclean.py` (create)

**Interfaces:**
- Produces: `engine.run_is_current(run_id) -> bool` (True iff `run_id` is the highest-attempt run for its job; False if not found). `engine.set_run_cleanup(run_id, cleanup_status: str) -> None` (merges `cleanup_status` into `jobs.run.result` JSONB; never touches status/finished_at/exit_code).
- Consumes: existing `engine._conn()` (psycopg dict_row + explicit commit), `jobs.run` (columns `id, job_id, attempt, result jsonb`).

- [ ] **Step 0: Test scaffolding (read `test_prune.py` first)**

Read `tests/test_prune.py`. It already provisions `orchestration_test` + a throwaway git repo + a `runs` dir. If its repo/runs/DB fixture is local to that file, **promote it to `tests/conftest.py`** so both test files share it; expose it as `prune_env` with attributes `.repo` (repo path) and `.runs` (runs dir), and ensure `APEX_JOBS_REPO`/`APEX_JOBS_DB`/the runs-dir env are set so `agent_runner._repo()`/`_runs_dir()` resolve to them. The throwaway repo must have at least two commits (so `HEAD` and `HEAD~1` both resolve) and a `.gitignore` containing `__pycache__/`.

Create `tests/test_review_autoclean.py` with these thin helpers (concrete; verified engine/agent_runner APIs):

```python
import json, os, uuid
from apex_jobs import engine, agent_runner, cli   # cli parser entry: see cli.py main/build_parser

def _enqueue_review(dispatch_id, review_head="HEAD", payload=None):
    p = {"review_head": review_head}
    if payload:
        p.update(payload)
    engine.enqueue(dispatch_id=dispatch_id, title="t", payload=p, target="codex",
                   kind="agent", base_ref="HEAD~1", env_required="host",
                   priority=100, created_by=None)
    return engine.get_job(dispatch_id)

def _seed_current_run(dispatch_id):
    """Enqueue a review job + open one run; run_is_current(run_id) is True."""
    job = _enqueue_review(dispatch_id)
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    return job, run_id

def _add_detached_worktree(repo, runs, dispatch_id):
    wt = os.path.join(runs, dispatch_id)
    agent_runner._git("worktree", "add", "--detach", wt, "HEAD", cwd=repo)
    return wt

def _run_review(dispatch_id, fake, payload=None):
    """Enqueue a review job then run it in-process with a fake agent_cmd; return the summary."""
    job = _enqueue_review(dispatch_id, payload=payload)
    return agent_runner.run_review_job(job, env="host", agent_cmd=fake)

def _parse_args(argv):
    """Build the CLI parser (the function in cli.py that wires the subparsers + `fn` defaults)
    and parse argv into an args namespace with `.fn`."""
    return cli.build_parser().parse_args(argv)   # adapt to cli.py's actual parser-builder name
```

- [ ] **Step 1: Write the failing test for `run_is_current`**

Add to `tests/test_review_autoclean.py`:

```python
from apex_jobs import engine

def test_run_is_current_true_for_only_attempt(prune_env):
    job = _enqueue_review(dispatch_id="review-aaaaaaaa", review_head="HEAD")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    assert engine.run_is_current(run_id) is True

def test_run_is_current_false_when_superseded(prune_env):
    job = _enqueue_review(dispatch_id="review-bbbbbbbb", review_head="HEAD")
    r1 = engine.start(job["id"], claimed_by="cc", run_env="host")   # attempt 1
    r2 = engine.start(job["id"], claimed_by="cc", run_env="host")   # attempt 2 (max)
    assert engine.run_is_current(r2) is True
    assert engine.run_is_current(r1) is False

def test_run_is_current_false_for_unknown(prune_env):
    import uuid
    assert engine.run_is_current(uuid.uuid4()) is False
```

- [ ] **Step 2: Run to verify failure**

Run: `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest tests/test_review_autoclean.py -k run_is_current -v`
Expected: FAIL with `AttributeError: module 'apex_jobs.engine' has no attribute 'run_is_current'`.

- [ ] **Step 3: Implement `run_is_current`**

Append to `engine.py`:

```python
def run_is_current(run_id):
    """True if run_id is the highest-attempt run for its job (not superseded by a newer
    attempt). False if not found. Backs the same-process auto-clean currency guard."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select (r.attempt = (select max(attempt) from jobs.run r2 "
                "where r2.job_id = r.job_id)) as is_current "
                "from jobs.run r where r.id = %s", (run_id,))
            row = cur.fetchone()
    return bool(row and row["is_current"])
```

- [ ] **Step 4: Run to verify pass**

Run: same `-k run_is_current` command. Expected: PASS (3 tests).

- [ ] **Step 5: Write the failing test for `set_run_cleanup`**

```python
def test_set_run_cleanup_merges_without_clobbering_findings(prune_env):
    job = _enqueue_review(dispatch_id="review-cccccccc", review_head="HEAD")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    engine.report(run_id, exit_code=0, result={"findings": "F", "is_review": True})
    engine.set_run_cleanup(run_id, "cleaned")
    res = engine.runs_for(job["dispatch_id"])[-1]["result"]
    assert res["cleanup_status"] == "cleaned"
    assert res["findings"] == "F"           # merge preserved the disjoint key
    assert res["is_review"] is True

def test_set_run_cleanup_null_result_safe(prune_env):
    job = _enqueue_review(dispatch_id="review-dddddddd", review_head="HEAD")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    # no report() -> result is NULL; coalesce guard must not error
    engine.set_run_cleanup(run_id, "not_attempted")
    res = engine.runs_for(job["dispatch_id"])[-1]["result"]
    assert res["cleanup_status"] == "not_attempted"
```

- [ ] **Step 6: Run to verify failure**

Run: `... pytest tests/test_review_autoclean.py -k set_run_cleanup -v`
Expected: FAIL (`no attribute 'set_run_cleanup'`).

- [ ] **Step 7: Implement `set_run_cleanup`**

Append to `engine.py`:

```python
def set_run_cleanup(run_id, cleanup_status):
    """Merge cleanup_status into the run's result JSONB (no schema change). ORTHOGONAL to
    run status: never changes status, finished_at, exit_code, or the process exit."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set result = coalesce(result, '{}'::jsonb) "
                "|| jsonb_build_object('cleanup_status', %s::text) where id=%s",
                (cleanup_status, run_id))
        conn.commit()
```

- [ ] **Step 8: Run to verify pass + no regression**

Run: `... pytest tests/test_review_autoclean.py -v` then `... pytest tests/test_prune.py -q`. Expected: all PASS.

- [ ] **Step 9: Commit**

Host-side: `git add src/apex_jobs/engine.py tests/test_review_autoclean.py && git commit -m "feat(apex-jobs): engine.run_is_current + set_run_cleanup for review auto-clean"`

---

## Task 2: `agent_runner._cleanup_review_worktree`

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/agent_runner.py` (add `import logging` + module `log`; add helper after the other module helpers)
- Test: `packages/apex-jobs/tests/test_review_autoclean.py` (add helper-level cases)

**Interfaces:**
- Consumes: `engine.run_is_current` (Task 1), `agent_runner._WORKTREE_LOCK`, `agent_runner._git`, `os.path.isdir`.
- Produces: `agent_runner._cleanup_review_worktree(repo, wt, run_id) -> str` returning exactly one of the seven labels relevant to a succeeded-non-kept path: `already_absent | superseded_preserved | dirty_preserved | cleaned | failed_preserved`. Runs under `_WORKTREE_LOCK`. Value-silent.

- [ ] **Step 1: Write the failing tests (all helper label paths)**

These drive the helper directly against throwaway worktrees created under the `runs` dir (mirror how `test_prune.py` creates worktrees with `git worktree add`). `_seed_current_run` opens a run and returns `(job, run_id)` such that `run_is_current(run_id)` is True.

```python
from apex_jobs import agent_runner

def test_cleanup_pristine_current_returns_cleaned(prune_env):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-11111111")
    wt = _add_detached_worktree(repo, runs, "review-11111111")   # clean tree
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "cleaned"
    assert not os.path.isdir(wt)

def test_cleanup_ignored_dirt_returns_dirty_preserved(prune_env):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-22222222")
    wt = _add_detached_worktree(repo, runs, "review-22222222")
    os.makedirs(os.path.join(wt, "__pycache__"), exist_ok=True)
    open(os.path.join(wt, "__pycache__", "x.pyc"), "w").write("x")   # ignored dirt
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "dirty_preserved"
    assert os.path.isdir(wt)

def test_cleanup_untracked_dirt_returns_dirty_preserved(prune_env):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-33333333")
    wt = _add_detached_worktree(repo, runs, "review-33333333")
    open(os.path.join(wt, "untracked.txt"), "w").write("x")
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "dirty_preserved"
    assert os.path.isdir(wt)

def test_cleanup_absent_returns_already_absent(prune_env):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-44444444")
    wt = os.path.join(runs, "review-44444444")   # never created on disk
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "already_absent"

def test_cleanup_superseded_returns_superseded_and_does_not_touch(prune_env, monkeypatch):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-55555555")
    wt = _add_detached_worktree(repo, runs, "review-55555555")
    monkeypatch.setattr(engine, "run_is_current", lambda rid: False)
    calls = []
    real_git = agent_runner._git
    monkeypatch.setattr(agent_runner, "_git",
                        lambda *a, **k: (calls.append(a) or real_git(*a, **k)))
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "superseded_preserved"
    assert os.path.isdir(wt)
    assert not any(a[:1] == ("status",) for a in calls)             # no git status
    assert not any(a[:2] == ("worktree", "remove") for a in calls)  # no remove

def test_cleanup_absent_beats_superseded(prune_env, monkeypatch):
    job, run_id = _seed_current_run("review-66666666")
    wt = os.path.join(prune_env.runs, "review-66666666")            # absent
    monkeypatch.setattr(engine, "run_is_current", lambda rid: False)
    assert agent_runner._cleanup_review_worktree(prune_env.repo, wt, run_id) == "already_absent"

def test_cleanup_remove_failure_returns_failed_preserved(prune_env, monkeypatch):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-77777777")
    wt = _add_detached_worktree(repo, runs, "review-77777777")      # clean
    real_git = agent_runner._git
    def fake_git(*a, **k):
        if a[:2] == ("worktree", "remove"):
            class R: returncode = 1; stdout = ""; stderr = ""
            return R()
        return real_git(*a, **k)
    monkeypatch.setattr(agent_runner, "_git", fake_git)
    assert agent_runner._cleanup_review_worktree(repo, wt, run_id) == "failed_preserved"

def test_cleanup_never_passes_force(prune_env, monkeypatch):
    repo, runs = prune_env.repo, prune_env.runs
    job, run_id = _seed_current_run("review-88888888")
    wt = _add_detached_worktree(repo, runs, "review-88888888")
    seen = []
    real_git = agent_runner._git
    monkeypatch.setattr(agent_runner, "_git",
                        lambda *a, **k: (seen.append(a) or real_git(*a, **k)))
    agent_runner._cleanup_review_worktree(repo, wt, run_id)
    assert not any("--force" in a for a in seen if a[:2] == ("worktree", "remove"))
```

- [ ] **Step 2: Run to verify failure**

Run: `... pytest tests/test_review_autoclean.py -k cleanup -v`
Expected: FAIL (`no attribute '_cleanup_review_worktree'`).

- [ ] **Step 3: Implement the module logger + helper**

Ensure `import logging` and `import os` are present at the top of `agent_runner.py`; add `log = logging.getLogger(__name__)` at module scope (near `_WORKTREE_LOCK`). Add:

```python
def _cleanup_review_worktree(repo, wt, run_id):
    """Decide + apply cleanup for a SUCCEEDED, non-kept review worktree. Caller has already
    confirmed status=='succeeded' and keep is false. Runs under _WORKTREE_LOCK. OWNS the fs
    mutation and returns the TRUE disposition label. Value-silent: returns a bare label, never
    a path or git stderr. Guard order is load-bearing (filesystem truth first):
      1. absent    -> dir already gone (raced by prune / a newer attempt's teardown) -> 'already_absent'
      2. currency  -> dir present but this run is not the current attempt -> 'superseded_preserved'
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
```

- [ ] **Step 4: Run to verify pass**

Run: `... pytest tests/test_review_autoclean.py -k cleanup -v`. Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

`git add src/apex_jobs/agent_runner.py tests/test_review_autoclean.py && git commit -m "feat(apex-jobs): _cleanup_review_worktree -- guarded, fs-truth-ordered, no --force"`

---

## Task 3: `run_review_job` tail — truth-preserving, orthogonal housekeeping

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/agent_runner.py` (`run_review_job` tail only)
- Test: `packages/apex-jobs/tests/test_review_autoclean.py` (end-to-end via fake agent)

**Interfaces:**
- Consumes: `engine.report`, `engine.set_run_artifacts`, `engine.set_run_cleanup` (Task 1), `_cleanup_review_worktree` (Task 2), `job.payload.keep_worktree`.
- Produces: `run_review_job(...)` summary dict gains `"cleanup_status"`. Behaviour: review status unchanged by housekeeping; a cleanup/record failure never demotes.

- [ ] **Step 1: Write the failing end-to-end tests**

Drive `run_review_job` with fake agents (`agent_cmd=` JSON argv). `_run_review(dispatch_id, fake, payload=None)` enqueues a review job, `get_job`s it, and calls `agent_runner.run_review_job(job, env="host", agent_cmd=fake)`, returning the summary.

```python
FINDINGS_OK = ["sh", "-c", "echo FINDINGS; exit 0"]
DIRTY_UNTRACKED = ["sh", "-c", "echo x > untracked.txt; echo FINDINGS; exit 0"]
DIRTY_IGNORED = ["sh", "-c", "mkdir -p __pycache__; echo x > __pycache__/x.pyc; echo F; exit 0"]
FAIL = ["sh", "-c", "exit 1"]

def test_tail_pristine_success_cleaned(prune_env):
    s = _run_review("review-a1111111", FINDINGS_OK)
    assert s["status"] == "succeeded" and s["cleanup_status"] == "cleaned"
    assert not os.path.isdir(os.path.join(prune_env.runs, "review-a1111111"))

def test_tail_ignored_dirty_preserved(prune_env):
    s = _run_review("review-a2222222", DIRTY_IGNORED)
    assert s["status"] == "succeeded" and s["cleanup_status"] == "dirty_preserved"
    assert os.path.isdir(os.path.join(prune_env.runs, "review-a2222222"))

def test_tail_untracked_dirty_preserved(prune_env):
    s = _run_review("review-a3333333", DIRTY_UNTRACKED)
    assert s["cleanup_status"] == "dirty_preserved"

def test_tail_failed_review_not_attempted(prune_env):
    s = _run_review("review-a4444444", FAIL)
    assert s["status"] == "failed" and s["cleanup_status"] == "not_attempted"
    assert os.path.isdir(os.path.join(prune_env.runs, "review-a4444444"))

def test_tail_keep_worktree_kept(prune_env):
    s = _run_review("review-a5555555", FINDINGS_OK, payload={"keep_worktree": True})
    assert s["cleanup_status"] == "kept"
    assert os.path.isdir(os.path.join(prune_env.runs, "review-a5555555"))

def test_tail_record_failure_does_not_relabel_or_demote(prune_env, monkeypatch):
    monkeypatch.setattr(engine, "set_run_cleanup",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db")))
    s = _run_review("review-a6666666", FINDINGS_OK)
    assert s["status"] == "succeeded"            # not demoted
    assert s["cleanup_status"] == "cleaned"      # true fs outcome, not relabelled
    assert not os.path.isdir(os.path.join(prune_env.runs, "review-a6666666"))

def test_tail_decision_failure_is_failed_preserved_not_demoted(prune_env, monkeypatch):
    monkeypatch.setattr(engine, "run_is_current",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db")))
    s = _run_review("review-a7777777", FINDINGS_OK)
    assert s["status"] == "succeeded"
    assert s["cleanup_status"] == "failed_preserved"

def test_tail_set_run_artifacts_failure_still_cleans(prune_env, monkeypatch):
    monkeypatch.setattr(engine, "set_run_artifacts",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db")))
    s = _run_review("review-a8888888", DIRTY_IGNORED)   # dirty -> preserved candidate
    assert s["status"] == "succeeded" and s["cleanup_status"] == "dirty_preserved"
```

- [ ] **Step 2: Run to verify failure**

Run: `... pytest tests/test_review_autoclean.py -k tail -v`
Expected: FAIL (summary has no `cleanup_status`; cleanup not wired).

- [ ] **Step 3: Replace the `run_review_job` tail**

Locate the existing tail in `run_review_job` (the `result = {...}` / `engine.report(...)` / `engine.set_run_artifacts(...)` / `return {...}` block) and replace it exactly with (use a single-buffer patch script to avoid multi-edit clobber):

```python
    result = {"findings": out[-8000:], "stderr": err[-4000:],
              "review_head": review_head, "base_ref": base_ref, "is_review": True}
    status = engine.report(run_id, exit_code=rc, result=result)   # commits terminal review status

    # (a) record where the run ran -- best-effort; prune keys on dispatch_id, a miss is harmless
    try:
        engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)
    except Exception as e:
        log.warning("review set_run_artifacts error: %s", type(e).__name__)

    # (b) decide + apply worktree disposition; the helper OWNS the fs mutation + true label
    try:
        keep = bool((job.get("payload") or {}).get("keep_worktree"))
        if status != "succeeded":
            cleanup_status = "not_attempted"
        elif keep:
            cleanup_status = "kept"
        else:
            cleanup_status = _cleanup_review_worktree(repo, wt, run_id)
    except Exception as e:
        log.warning("review cleanup error: %s", type(e).__name__)
        cleanup_status = "failed_preserved"

    # (c) record disposition -- best-effort; a record failure NEVER relabels the (b) outcome
    try:
        engine.set_run_cleanup(run_id, cleanup_status)
    except Exception as e:
        log.warning("review set_run_cleanup error: %s", type(e).__name__)

    return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
            "review_head": review_head, "findings_len": len(out),
            "cleanup_status": cleanup_status}
```

- [ ] **Step 4: Run to verify pass + full-suite regression**

Run: `... pytest tests/test_review_autoclean.py -k tail -v`, then the whole suite `... pytest -q` (incl `test_prune.py`). Expected: all PASS.

- [ ] **Step 5: Commit**

`git add src/apex_jobs/agent_runner.py tests/test_review_autoclean.py && git commit -m "feat(apex-jobs): run_review_job auto-clean tail -- orthogonal, truth-preserving"`

---

## Task 4: CLI `--keep-worktree` + JSON surface

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/cli.py` (`cmd_enqueue_review`, `cmd_review_run`, both subparsers)
- Test: `packages/apex-jobs/tests/test_review_autoclean.py` (CLI-level)

**Interfaces:**
- Consumes: the runner honoring `payload.keep_worktree` (Task 3), the summary carrying `cleanup_status`.
- Produces: `--keep-worktree` (store_true) on both verbs; `enqueue-review` OR-merges into `payload`; `review-run --json` includes `cleanup_status`.

- [ ] **Step 1: Write failing tests**

```python
def test_enqueue_review_or_merges_payload_keep(prune_env):
    # flag omitted but payload asks to keep -> keep must survive (OR semantics)
    args = _parse_args(["enqueue-review", "--dispatch-id", "review-b1111111",
                        "--review-head", "HEAD", "--base-ref", "HEAD~1",
                        "--payload", '{"keep_worktree": true}'])
    args.fn(args)
    job = engine.get_job("review-b1111111")
    assert job["payload"].get("keep_worktree") is True

def test_enqueue_review_flag_sets_keep(prune_env):
    args = _parse_args(["enqueue-review", "--dispatch-id", "review-b2222222",
                        "--review-head", "HEAD", "--base-ref", "HEAD~1", "--keep-worktree"])
    args.fn(args)
    assert engine.get_job("review-b2222222")["payload"].get("keep_worktree") is True

def test_enqueue_review_neither_defaults_false(prune_env):
    args = _parse_args(["enqueue-review", "--dispatch-id", "review-b3333333",
                        "--review-head", "HEAD", "--base-ref", "HEAD~1"])
    args.fn(args)
    assert bool(engine.get_job("review-b3333333")["payload"].get("keep_worktree")) is False

def test_review_run_json_includes_cleanup_status(prune_env, capsys, monkeypatch):
    monkeypatch.setenv("APEX_JOBS_AGENT_CMD", json.dumps(FINDINGS_OK))
    args = _parse_args(["review-run", "--review-head", "HEAD", "--base-ref", "HEAD~1", "--json"])
    args.fn(args)
    out = json.loads(capsys.readouterr().out)
    assert out["cleanup_status"] == "cleaned"

def test_review_run_keep_flag_preserves(prune_env, capsys, monkeypatch):
    monkeypatch.setenv("APEX_JOBS_AGENT_CMD", json.dumps(FINDINGS_OK))
    args = _parse_args(["review-run", "--review-head", "HEAD", "--base-ref", "HEAD~1",
                        "--json", "--keep-worktree"])
    args.fn(args)
    assert json.loads(capsys.readouterr().out)["cleanup_status"] == "kept"
```

- [ ] **Step 2: Run to verify failure**

Run: `... pytest tests/test_review_autoclean.py -k "enqueue_review or review_run_json or review_run_keep" -v`
Expected: FAIL (`--keep-worktree` unrecognized; no `cleanup_status` in JSON).

- [ ] **Step 3: Implement the CLI changes**

In `cmd_enqueue_review`, after `payload["review_head"] = a.review_head`, add the OR-merge:
```python
    payload["keep_worktree"] = bool(a.keep_worktree) or bool(payload.get("keep_worktree"))
```
In `cmd_review_run`, change the payload construction to:
```python
    payload = {"review_head": a.review_head, "keep_worktree": bool(a.keep_worktree)}
```
and add `cleanup_status` to the `--json` object:
```python
        print(json.dumps({"dispatch_id": disp, "status": summary["status"],
                          "review_head": a.review_head, "base_ref": a.base_ref,
                          "cleanup_status": summary["cleanup_status"],
                          "findings": res.get("findings", "")}, indent=2))
```
Add to BOTH subparsers (`er` and `rr`):
```python
    er.add_argument("--keep-worktree", action="store_true", dest="keep_worktree",
                    help="opt out of auto-cleanup at review completion (not a permanent hold; "
                         "a later explicit prune may still reclaim a clean worktree)")
```
(and the identical `rr.add_argument(...)`).

- [ ] **Step 4: Run to verify pass + full suite**

Run: `... pytest tests/test_review_autoclean.py -v`, then whole suite `... pytest -q`. Expected: all PASS, `test_prune.py` green.

- [ ] **Step 5: Commit**

`git add src/apex_jobs/cli.py tests/test_review_autoclean.py && git commit -m "feat(apex-jobs): --keep-worktree on review-run + enqueue-review (OR-merge) + cleanup_status in --json"`

---

## Finishing

- [ ] Run the full apex-jobs suite once more, green, 0 skipped (with DB env).
- [ ] **Whole-branch Codex cross-engine review on the implementation:** `codex exec review --dangerously-bypass-approvals-and-sandbox -c model_reasoning_effort=high --base main` in the worktree; fold any P1/P2 findings and re-review to convergence.
- [ ] superpowers:finishing-a-development-branch → push + PR (squash self-merge governance; no admin-bypass); after merge, run one live dry-run of the leak surface if useful, then clean the worktree/branch (OPS_* pattern) and sync durable state.

## Coverage map (spec 15-case matrix → tests)

| Spec case | Test |
|---|---|
| pristine → cleaned | `test_cleanup_pristine_current_returns_cleaned`, `test_tail_pristine_success_cleaned` |
| ignored dirt → dirty_preserved | `test_cleanup_ignored_dirt_...`, `test_tail_ignored_dirty_preserved` |
| untracked dirt → dirty_preserved | `test_cleanup_untracked_dirt_...`, `test_tail_untracked_dirty_preserved` |
| dirty pre-check prevents remove / no --force | `test_cleanup_never_passes_force`, superseded no-touch spy |
| superseded → superseded_preserved (untouched) | `test_cleanup_superseded_...` (spies no status/remove) |
| already-gone → already_absent | `test_cleanup_absent_...`, `test_cleanup_absent_beats_superseded` |
| remove failure → failed_preserved | `test_cleanup_remove_failure_...` |
| record failure no relabel/demote | `test_tail_record_failure_does_not_relabel_or_demote` |
| decision failure → failed_preserved, not demoted | `test_tail_decision_failure_...` |
| set_run_artifacts raises → cleanup still runs | `test_tail_set_run_artifacts_failure_still_cleans` |
| keep → preserved | `test_tail_keep_worktree_kept`, `test_review_run_keep_flag_preserves` |
| enqueue OR-merge / flag / neither | `test_enqueue_review_or_merges_payload_keep` (+ flag/neither) |
| review-run --json cleanup_status | `test_review_run_json_includes_cleanup_status` |
| failed review → not_attempted | `test_tail_failed_review_not_attempted` |
| value-silence + prune regression | JSONB merge test (no clobber) + whole `test_prune.py` green |
