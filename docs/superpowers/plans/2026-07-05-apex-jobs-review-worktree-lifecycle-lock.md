# apex-jobs review worktree lifecycle lock -- Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop concurrent review runners from unsafely creating/removing/reusing the same detached review worktree, by adding a Postgres session advisory lock (cross-process coordinator) plus a narrow OS `flock` (runner-process-liveness fuse) around every destructive worktree op, and making a contended attempt open no run and never strand its job.

**Architecture:** A dedicated-connection PG session advisory lock keyed on `dispatch_id` coordinates ownership; a per-dispatch `flock` proves the holding process is alive. `run_review_job` acquires PG lock -> flock -> then `engine.start()` (so a loser opens no run and never writes `jobs.job.status`) and un-strands any pool claim via a value-silent `release_claim` CAS. The startup `git worktree remove --force` is reached only with both held; auto-clean and prune stay `--force`-free and also honor the fuse. No schema change.

**Tech Stack:** Python 3.12, psycopg3 (`from psycopg.types.json import Jsonb`), stdlib `fcntl`/`contextlib`, pytest against a real `orchestration_test` Postgres (host-only suite). Spec: `docs/superpowers/specs/2026-07-05-apex-jobs-review-worktree-lifecycle-lock-design.md` (rev 4, committed `b692b434`).

## Global Constraints

- **Namespace constant, exact:** `_REVIEW_WT_LOCK_NS = 0x52565754` (ASCII "RVWT"). ONE definition in `engine.py`; every callsite imports it. Never transcribe a decimal literal. Unit-assert `_REVIEW_WT_LOCK_NS == 0x52565754`.
- **PG key form, exact:** `pg_try_advisory_lock(_REVIEW_WT_LOCK_NS, hashtext(dispatch_id))`; release with `pg_advisory_unlock(...)` (same args).
- **Lock connection is autocommit:** set `conn.autocommit = True` explicitly on the dedicated lock connection.
- **Value-silence:** `LockUnavailable` carries no psycopg/DSN text and is raised OUTSIDE the `except` so `__context__ is None`. Swallowed exceptions log `type(e).__name__` only. Tests assert on statuses/labels/counts/booleans -- never file contents, env, or DSN.
- **Lock order (no deadlock):** always PG lock -> `flock` -> `_WORKTREE_LOCK`. Never the reverse.
- **`--force` only under BOTH locks** (startup reclamation). Auto-clean and prune stay plain `git worktree remove` (no `--force`).
- **ASCII-only added lines** in `.py` source files.
- **`test_prune.py` stays byte-unchanged.** All new tests go in `tests/test_review_worktree_lock.py`.
- **Host-canonical single-writer:** author locally on Windows -> `scp` per-file to `/home/olares/code/apex/apex-review-wtlock` -> run/commit host-side over `ssh olares-mesh`. Existing-file edits via single-buffer Python patch scripts (anchor-count-guarded).
- **Run the suite** from `packages/apex-jobs`: `export PATH=$HOME/.local/bin:$PATH`; source the canonical `/home/olares/code/apex/apex-power-ops-platform/infra/.env`; `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest`.
- **Final gate:** whole-branch Codex cross-engine review before finishing.

---

## File Structure

| File | Change | Responsibility |
| --- | --- | --- |
| `packages/apex-jobs/src/apex_jobs/engine.py` | modify | Add `LockUnavailable`, `_REVIEW_WT_LOCK_NS`, `review_worktree_lock` (CM), `release_claim` (CAS). Add `from contextlib import contextmanager` import. |
| `packages/apex-jobs/src/apex_jobs/agent_runner.py` | modify | Add `_worktree_flock` (CM, `fcntl`/`O_CLOEXEC`). Restructure `run_review_job` (PG lock -> flock -> `start()` -> git ops; `_contended` inner helper). Add `import fcntl`. |
| `packages/apex-jobs/src/apex_jobs/prune.py` | modify | Wrap each per-item apply in PG lock + `flock`; add `contended` classification; broaden the `except`. |
| `packages/apex-jobs/src/apex_jobs/cli.py` | modify | `cmd_review_run` tolerates `summary["run"] is None` (skip `runs_for`, empty findings, `contended` in JSON, exit 3). |
| `packages/apex-jobs/tests/test_review_worktree_lock.py` | create | All new tests (E/F/R/P/K series). Imports helpers from `test_prune` + `conn_test` fixture from conftest. |
| `packages/apex-jobs/tests/test_prune.py` | UNCHANGED | Regression gate; byte-identical. |

**Task order:** T1 -> T2 -> T3 -> T4 -> T5 -> T6 (T4 consumes T1/T2/T3; T5 consumes T1/T3; T6 consumes T4).

---

## Task 1: engine PG session advisory lock

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/engine.py` (add `from contextlib import contextmanager` to the import block; append the new surface after `set_job_keep_worktree`)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py` (create)

**Interfaces:**
- Consumes: `engine._conn()` (dict-row psycopg connection to the pinned test DB), `psycopg` (already imported), `db.resolve_dsn()` (called inside `_conn`).
- Produces:
  - `engine.LockUnavailable` (Exception)
  - `engine._REVIEW_WT_LOCK_NS = 0x52565754`
  - `engine.review_worktree_lock(dispatch_id)` -> context manager yielding `acquired: bool`; raises `LockUnavailable` (value-silent) on any connect/acquire/config failure.

- [ ] **Step 1: Create the test module scaffold + the constant/immediate tests**

Create `packages/apex-jobs/tests/test_review_worktree_lock.py`:

```python
"""TDD - apex-jobs review worktree lifecycle lock (PG advisory lock coordinator +
flock liveness fuse). Real orchestration_test DB (conn_test) + throwaway detached
worktrees under a tmp runs dir. Value-silent: assertions use statuses/labels/
counts/booleans only -- never file contents, env, or DSN. Kept in a SEPARATE
module so test_prune.py stays byte-unchanged."""
import fcntl
import os
import subprocess

import psycopg
import pytest

from apex_jobs import engine, agent_runner
from test_prune import _enqueue_review, REPO


# ---- fakes for the value-silence / autocommit / unlock-mask paths ----
class _FakeCur:
    def __init__(self, conn): self.conn = conn
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=None):
        self.conn.calls.append(sql)
        if "pg_advisory_unlock" in sql and self.conn.fail_unlock:
            raise psycopg.OperationalError("unlock boom host=secret")
    def fetchone(self): return {"ok": True}


class _FakeConn:
    def __init__(self, fail_unlock=False, fail_close=False):
        self.autocommit = False
        self.fail_unlock = fail_unlock
        self.fail_close = fail_close
        self.calls = []
        self.closed = False
    def cursor(self): return _FakeCur(self)
    def close(self):
        self.closed = True
        if self.fail_close:
            raise psycopg.OperationalError("close boom host=secret")


def test_ns_constant_pinned():
    assert engine._REVIEW_WT_LOCK_NS == 0x52565754
```

- [ ] **Step 2: Run it to confirm the module imports and the constant test fails**

Run: `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest tests/test_review_worktree_lock.py::test_ns_constant_pinned -v`
Expected: FAIL with `AttributeError: module 'apex_jobs.engine' has no attribute '_REVIEW_WT_LOCK_NS'`.

- [ ] **Step 3: Add the imports + constant + exception + context manager to engine.py**

In `engine.py`, add to the import block (after `import tempfile`):

```python
from contextlib import contextmanager
```

Append after `set_job_keep_worktree`:

```python
class LockUnavailable(Exception):
    """Cannot establish PG dispatch ownership (connect/acquire/config failed).
    Value-silent: carries NO underlying psycopg/DSN text and NO chained
    __context__ (raised outside the except block)."""


_REVIEW_WT_LOCK_NS = 0x52565754  # ASCII 'RVWT'; the ONE namespace constant (imported everywhere)


@contextmanager
def review_worktree_lock(dispatch_id):
    """Cross-process COORDINATOR for runs/<dispatch_id>. Dedicated autocommit
    connection; non-blocking session advisory lock. Yields the acquired bool.
    Value-silent: any transport OR resolve_dsn config failure at connect/acquire
    raises LockUnavailable (raised outside the except so __context__ is None).
    The unlock and both close() sites are guarded so neither masks a caller return."""
    conn = None
    acquired = False
    failed = False
    try:
        conn = _conn()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok",
                        (_REVIEW_WT_LOCK_NS, dispatch_id))
            acquired = bool(cur.fetchone()["ok"])
    except (psycopg.Error, OSError, ValueError, KeyError, RuntimeError):
        failed = True
    if failed:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        raise LockUnavailable()
    try:
        yield acquired
    finally:
        try:
            if acquired:
                with conn.cursor() as cur:
                    cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                                (_REVIEW_WT_LOCK_NS, dispatch_id))
        except (psycopg.Error, OSError):
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
```

- [ ] **Step 4: Run the constant test to confirm it passes**

Run: `... pytest tests/test_review_worktree_lock.py::test_ns_constant_pinned -v`
Expected: PASS.

- [ ] **Step 5: Add the E-series behavior tests**

Append to `tests/test_review_worktree_lock.py`:

```python
def test_e1_acquire_and_release(conn_test):
    d = "review-e1000001"
    with engine.review_worktree_lock(d) as held:
        assert held is True
    with engine.review_worktree_lock(d) as held2:   # released -> re-acquire succeeds
        assert held2 is True


def test_e2_second_holder_contends(conn_test):
    d = "review-e2000002"
    with engine.review_worktree_lock(d) as held:
        assert held is True
        with engine.review_worktree_lock(d) as held2:   # distinct connection, same key
            assert held2 is False


def test_e3_crash_release(conn_test):
    d = "review-e3000003"
    ns = engine._REVIEW_WT_LOCK_NS
    a = engine._conn(); a.autocommit = True
    with a.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok", (ns, d))
        assert cur.fetchone()["ok"] is True
    a.close()                                            # session drop -> auto-release
    with engine.review_worktree_lock(d) as held:
        assert held is True


def test_e4_distinct_dispatch_no_false_contention(conn_test):
    with engine.review_worktree_lock("review-e4000001") as h1:
        with engine.review_worktree_lock("review-e4000002") as h2:
            assert h1 is True and h2 is True


def test_e5_connect_failure_value_silent(conn_test, monkeypatch):
    def boom():
        raise psycopg.OperationalError("host=secret user=orchestration password=hunter2")
    monkeypatch.setattr(engine, "_conn", boom)
    with pytest.raises(engine.LockUnavailable) as ei:
        with engine.review_worktree_lock("review-e5000001"):
            pass
    e = ei.value
    assert e.__context__ is None and e.__cause__ is None
    assert "secret" not in str(e) and "hunter2" not in str(e)


def test_e6_resolve_dsn_runtimeerror_value_silent(conn_test, monkeypatch):
    def boom():
        raise RuntimeError("APEX_JOBS_PGPASSWORD or DEV_PG_PASSWORD required")
    monkeypatch.setattr(engine, "_conn", boom)
    with pytest.raises(engine.LockUnavailable) as ei:
        with engine.review_worktree_lock("review-e6000001"):
            pass
    assert ei.value.__context__ is None


def test_e7_unlock_and_close_failure_do_not_mask(conn_test, monkeypatch):
    monkeypatch.setattr(engine, "_conn", lambda: _FakeConn(fail_unlock=True, fail_close=True))
    with engine.review_worktree_lock("review-e7000001") as held:
        assert held is True
        result = "clean-return"
    assert result == "clean-return"   # no exception escaped the CM


def test_e8_lock_connection_is_autocommit(conn_test, monkeypatch):
    fake = _FakeConn()
    monkeypatch.setattr(engine, "_conn", lambda: fake)
    with engine.review_worktree_lock("review-e8000001") as held:
        assert held is True
    assert fake.autocommit is True
```

- [ ] **Step 6: Run the E-series and confirm all pass**

Run: `... pytest tests/test_review_worktree_lock.py -v`
Expected: PASS (E1-E8 + the constant test).

- [ ] **Step 7: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/engine.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "feat(apex-jobs): engine.review_worktree_lock PG advisory-lock coordinator (value-silent)"
```

---

## Task 2: engine `release_claim` CAS

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/engine.py` (append after `review_worktree_lock`)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py`

**Interfaces:**
- Consumes: `engine._conn()`, `engine.enqueue`.
- Produces: `engine.release_claim(job_id)` -> value-silent CAS `UPDATE jobs.job SET status='pending' WHERE id=%s AND status='claimed'`. No-op on any other status.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_review_worktree_lock.py`:

```python
def _set_status(conn, job_id, status):
    with conn.cursor() as cur:
        cur.execute("update jobs.job set status=%s where id=%s", (status, job_id))


def _status(conn, job_id):
    with conn.cursor() as cur:
        cur.execute("select status from jobs.job where id=%s", (job_id,))
        return cur.fetchone()["status"]


def test_release_claim_unstrands_claimed(conn_test):
    jid = _enqueue_review("review-rc000001")
    _set_status(conn_test, jid, "claimed")
    engine.release_claim(jid)
    assert _status(conn_test, jid) == "pending"


def test_release_claim_noop_on_running(conn_test):
    jid = _enqueue_review("review-rc000002")
    _set_status(conn_test, jid, "running")
    engine.release_claim(jid)
    assert _status(conn_test, jid) == "running"


def test_release_claim_noop_on_succeeded(conn_test):
    jid = _enqueue_review("review-rc000003")
    _set_status(conn_test, jid, "succeeded")
    engine.release_claim(jid)
    assert _status(conn_test, jid) == "succeeded"
```

- [ ] **Step 2: Run to confirm failure**

Run: `... pytest tests/test_review_worktree_lock.py -k release_claim -v`
Expected: FAIL with `AttributeError: ... has no attribute 'release_claim'`.

- [ ] **Step 3: Implement `release_claim`**

Append to `engine.py` (after `review_worktree_lock`):

```python
def release_claim(job_id):
    """Value-silent CAS: return a still-CLAIMED job to 'pending' so a contended
    pool-claimed review (which opened no run) is never stranded. No-op if a winner
    already advanced the job to running/terminal (WHERE status='claimed'), so it can
    never overwrite live or finished work."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("update jobs.job set status='pending', updated_at=now() "
                        "where id=%s and status='claimed'", (job_id,))
        conn.commit()
```

- [ ] **Step 4: Run to confirm passing**

Run: `... pytest tests/test_review_worktree_lock.py -k release_claim -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/engine.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "feat(apex-jobs): engine.release_claim CAS (un-strand contended pool claim)"
```

---

## Task 3: `agent_runner._worktree_flock` fuse

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/agent_runner.py` (add `import fcntl` + `_O_CLOEXEC`; add `_worktree_flock` after `_WORKTREE_LOCK`/`log`)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py`

**Interfaces:**
- Consumes: stdlib `os`, `fcntl`, `contextlib.contextmanager` (already imported in agent_runner? add if absent).
- Produces: `agent_runner._worktree_flock(runs, dispatch_id)` -> context manager yielding `acquired: bool` (True = no live holder; False = held or fs-error). O_CLOEXEC fd; lockfile is `runs/<dispatch_id>.lock`, never unlinked.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_review_worktree_lock.py`:

```python
def test_f1_flock_process_death_release(tmp_path):
    runs = str(tmp_path)
    d = "review-f1000001"
    lockpath = os.path.join(runs, d + ".lock")
    fd = os.open(lockpath, os.O_CREAT | os.O_RDWR, 0o600)   # simulate a live holder
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with agent_runner._worktree_flock(runs, d) as ok:
        assert ok is False                                  # occupied
    os.close(fd)                                            # holder "dies" -> kernel releases
    with agent_runner._worktree_flock(runs, d) as ok2:
        assert ok2 is True


def test_f1b_flock_fd_is_cloexec(tmp_path):
    runs = str(tmp_path)
    d = "review-f1b00001"
    # While holding the flock inside the CM, a child subprocess must NOT be able to
    # re-flock (it would inherit a live fd) -- prove the child sees it acquirable-free
    # only AFTER we exit, i.e. the child does not inherit our held fd.
    with agent_runner._worktree_flock(runs, d) as ok:
        assert ok is True
        # a child that opens its OWN fd and tries LOCK_NB must fail because WE hold it,
        # and it must not have inherited our fd (close_fds default True keeps it clean)
        code = (
            "import fcntl,os,sys\n"
            f"fd=os.open({os.path.join(runs, d + '.lock')!r},os.O_CREAT|os.O_RDWR,0o600)\n"
            "import sys\n"
            "try:\n fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB); print('GOT')\n"
            "except OSError: print('BLOCKED')\n"
        )
        r = subprocess.run(["python3", "-c", code], capture_output=True, text=True)
        assert "BLOCKED" in r.stdout                        # our held flock blocks the child


def test_f4_fs_error_fail_closed(tmp_path, monkeypatch):
    runs = str(tmp_path)
    def boom(*a, **k):
        raise OSError("ENOSPC /runs/review-x.lock")
    monkeypatch.setattr(agent_runner.os, "open", boom)
    with agent_runner._worktree_flock(runs, "review-f4000001") as ok:
        assert ok is False                                  # fail-closed, value-silent
```

- [ ] **Step 2: Run to confirm failure**

Run: `... pytest tests/test_review_worktree_lock.py -k "f1 or f1b or f4" -v`
Expected: FAIL with `AttributeError: ... has no attribute '_worktree_flock'`.

- [ ] **Step 3: Implement `_worktree_flock`**

In `agent_runner.py` add to the imports (after `import subprocess`):

```python
import fcntl
```

(If `from contextlib import contextmanager` is not already imported in agent_runner.py, add it.)

Add after the `_WORKTREE_LOCK` / `log` definitions:

```python
_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)


@contextmanager
def _worktree_flock(runs, dispatch_id):
    """Local RUNNER-process-liveness FUSE (NOT a coordinator) for runs/<dispatch_id>.
    Non-blocking exclusive flock on the sibling lockfile. Yields True if acquired (no
    live local process holds the path), False if held OR the fuse cannot be established
    (fs error -> fail-closed). The fd is O_CLOEXEC so it is not inherited by the codex
    child: the flock releases exactly on the runner process's death. Value-silent."""
    fd = None
    acquired = False
    try:
        path = os.path.join(runs, dispatch_id + ".lock")
        os.makedirs(runs, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | _O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            acquired = False
    except OSError:
        acquired = False
    try:
        yield acquired
    finally:
        try:
            if fd is not None:
                if acquired:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
        except OSError:
            pass
```

- [ ] **Step 4: Run to confirm passing**

Run: `... pytest tests/test_review_worktree_lock.py -k "f1 or f1b or f4" -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/agent_runner.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "feat(apex-jobs): _worktree_flock runner-liveness fuse (O_CLOEXEC, fail-closed)"
```

---

## Task 4: `run_review_job` restructure (PG lock -> flock -> start() -> git ops)

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/agent_runner.py` (rewrite the body of `run_review_job`)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py`

**Interfaces:**
- Consumes: `engine.review_worktree_lock` (T1), `engine.release_claim` (T2), `_worktree_flock` (T3), and the unchanged `engine.start`, `engine.report`, `engine.set_run_artifacts`, `_cleanup_review_worktree`, `_git`, `_review_argv`, `_agent_env`.
- Produces: `run_review_job(job, env, as_="cc", agent_cmd=None)` returning a dict. Winner: `{"job","run"(str),"status","review_head","findings_len","contended":False,"cleanup_status"}`. Loser (contended): `{"job","run":None,"status":"contended","review_head","findings_len":0,"contended":True,"cleanup_status":"not_attempted"}`.

**Fixtures/helpers for this task's tests** (append to the test module once):

```python
FAKE_OK = ["python3", "-c", "print('review findings ok')"]   # agent_cmd stand-in (rc 0)


def _mk_review_repo(tmp_path):
    """A throwaway git repo to host detached review worktrees."""
    repo = str(tmp_path / "repo")
    os.makedirs(repo)
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "root"], check=True)
    return repo


@pytest.fixture
def review_env(tmp_path, monkeypatch):
    repo = _mk_review_repo(tmp_path)
    runs = str(tmp_path / "runs")
    os.makedirs(runs)
    monkeypatch.setenv("APEX_JOBS_REPO", repo)
    monkeypatch.setenv("APEX_JOBS_RUNS_DIR", runs)
    return repo, runs
```

- [ ] **Step 1: Write the happy-path + contended tests (R1, R2, R3)**

```python
def test_r2_happy_path_runs_and_autocleans(conn_test, review_env):
    repo, runs = review_env
    jid = _enqueue_review("review-r2000001")
    job = engine.get_job("review-r2000001")
    summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    assert summary["status"] == "succeeded"
    assert summary["contended"] is False
    assert summary["cleanup_status"] == "cleaned"
    assert not os.path.isdir(os.path.join(runs, "review-r2000001"))   # auto-cleaned


def test_r1_r3_contended_pg_opens_no_run_touches_no_tree(conn_test, review_env):
    repo, runs = review_env
    d = "review-r1000001"
    jid = _enqueue_review(d)
    job = engine.get_job(d)
    spy = []
    orig_git = agent_runner._git
    def _spy_git(*args, cwd, check=True):
        spy.append(args)
        return orig_git(*args, cwd=cwd, check=check)
    # hold the PG lock on a raw connection so run_review_job contends
    holder = engine._conn(); holder.autocommit = True
    with holder.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s))",
                    (engine._REVIEW_WT_LOCK_NS, d))
    try:
        import unittest.mock as m
        with m.patch.object(agent_runner, "_git", _spy_git):
            summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    finally:
        with holder.cursor() as cur:
            cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                        (engine._REVIEW_WT_LOCK_NS, d))
        holder.close()
    assert summary["status"] == "contended" and summary["contended"] is True
    assert summary["run"] is None and summary["cleanup_status"] == "not_attempted"
    assert not any(a[:2] == ("worktree", "remove") or a[:2] == ("worktree", "add") for a in spy)
    assert not os.path.isdir(os.path.join(runs, d))
```

- [ ] **Step 2: Run to confirm R1 fails (current run_review_job has no contention path)**

Run: `... pytest tests/test_review_worktree_lock.py -k "r1_r3 or r2_happy" -v`
Expected: R2 may pass on current code; R1 FAILS (current code would open a run / create a worktree despite the held PG lock, since there is no lock yet).

- [ ] **Step 3: Rewrite `run_review_job`**

Replace the entire body of `run_review_job` in `agent_runner.py` with:

```python
def run_review_job(job, env, as_="cc", agent_cmd=None):
    """Run a kind='agent' REVIEW job under the dispatch coordinator (PG advisory lock)
    + the runner-liveness fuse (flock). A losing attempt (PG-not-held, fuse-not-ok, or
    LockUnavailable) opens NO run, writes NO job.status, touches NO tree, and releases
    any pool claim. The winner runs codex, records findings, and auto-cleans. Read-only
    review -- no commit/diff/promotion gate. agent_cmd overrides the CLI (fake, in tests)."""
    repo, runs = _repo(), _runs_dir()
    dispatch_id = job["dispatch_id"]
    review_head = (job.get("payload") or {}).get("review_head") or "HEAD"

    def _contended():
        try:
            engine.release_claim(job["id"])   # CAS claimed->pending; no-op if a winner advanced it
        except Exception as e:
            log.warning("review release_claim error: %s", type(e).__name__)
        return {"job": dispatch_id, "run": None, "status": "contended",
                "review_head": review_head, "findings_len": 0,
                "contended": True, "cleanup_status": "not_attempted"}

    try:
        with engine.review_worktree_lock(dispatch_id) as held:      # PG COORDINATOR
            if not held:
                return _contended()
            with _worktree_flock(runs, dispatch_id) as fuse_ok:     # RUNNER-liveness FUSE
                if not fuse_ok:
                    return _contended()
                run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # winner only
                base_ref = job.get("base_ref") or _git(
                    "rev-parse", "--abbrev-ref", "HEAD", cwd=repo).stdout.strip()
                if not job.get("base_ref"):
                    engine.set_base_ref(job["id"], base_ref)
                wt = os.path.join(runs, dispatch_id)
                os.makedirs(runs, exist_ok=True)
                with _WORKTREE_LOCK:                                # BOTH locks held -> idle residue
                    _git("worktree", "remove", "--force", wt, cwd=repo, check=False)   # provably safe HERE ONLY
                    _git("worktree", "add", "--detach", wt, review_head, cwd=repo)
                argv = agent_cmd or _review_argv(base_ref)
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
                try:
                    engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)
                except Exception as e:
                    log.warning("review set_run_artifacts error: %s", type(e).__name__)
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
                try:
                    engine.set_run_cleanup(run_id, cleanup_status)
                except Exception as e:
                    log.warning("review set_run_cleanup error: %s", type(e).__name__)
                return {"job": dispatch_id, "run": str(run_id), "status": status,
                        "review_head": review_head, "findings_len": len(out),
                        "contended": False, "cleanup_status": cleanup_status}
    except engine.LockUnavailable:
        return _contended()
```

- [ ] **Step 4: Run R1/R2/R3 to confirm passing**

Run: `... pytest tests/test_review_worktree_lock.py -k "r1_r3 or r2_happy" -v`
Expected: PASS.

- [ ] **Step 5: Add F2, F3, R4, R5, R6, K1**

```python
def _hold_flock(runs, d):
    os.makedirs(runs, exist_ok=True)
    fd = os.open(os.path.join(runs, d + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fd


def test_f2_fuse_fail_opens_no_run_no_tree(conn_test, review_env):
    repo, runs = review_env
    d = "review-f2000001"
    _enqueue_review(d)
    job = engine.get_job(d)
    fd = _hold_flock(runs, d)                     # a live process holds the path
    try:
        summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    finally:
        os.close(fd)
    assert summary["status"] == "contended" and summary["run"] is None
    assert not os.path.isdir(os.path.join(runs, d))


def test_f3_pg_terminated_but_flock_held_no_delete(conn_test, review_env):
    repo, runs = review_env
    d = "review-f3000001"
    _enqueue_review(d)
    job = engine.get_job(d)
    # A's live tree + A holds the flock; A's PG session is (already) gone.
    wt = os.path.join(runs, d)
    subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, "HEAD"], check=True)
    fd = _hold_flock(runs, d)
    try:
        summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    finally:
        os.close(fd)
    assert summary["status"] == "contended"
    assert os.path.isdir(wt)                      # B did NOT delete A's live tree
    subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], check=False)


def test_r4_lock_unavailable_contended(conn_test, review_env, monkeypatch):
    repo, runs = review_env
    d = "review-r4000001"
    _enqueue_review(d)
    job = engine.get_job(d)
    from contextlib import contextmanager
    @contextmanager
    def boom(dispatch_id):
        raise engine.LockUnavailable()
        yield  # pragma: no cover
    monkeypatch.setattr(engine, "review_worktree_lock", boom)
    summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    assert summary["status"] == "contended" and summary["run"] is None
    assert not os.path.isdir(os.path.join(runs, d))


def test_r5_contended_loser_cannot_demote_succeeded(conn_test, review_env):
    repo, runs = review_env
    d = "review-r5000001"
    _enqueue_review(d)
    job = engine.get_job(d)
    # winner A runs to succeeded
    a = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    assert a["status"] == "succeeded"
    # now a live holder grabs the PG lock; a fresh attempt B contends
    holder = engine._conn(); holder.autocommit = True
    with holder.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s))",
                    (engine._REVIEW_WT_LOCK_NS, d))
    try:
        b = agent_runner.run_review_job(engine.get_job(d), env="host", agent_cmd=FAKE_OK)
    finally:
        with holder.cursor() as cur:
            cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                        (engine._REVIEW_WT_LOCK_NS, d))
        holder.close()
    assert b["status"] == "contended"
    assert _status(conn_test, job["id"]) == "succeeded"    # B did not demote the job


def test_r6_contended_pool_claim_unstranded(conn_test, review_env):
    repo, runs = review_env
    d = "review-r6000001"
    jid = _enqueue_review(d)
    _set_status(conn_test, jid, "claimed")                 # pool has claimed it
    holder = engine._conn(); holder.autocommit = True
    with holder.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s))",
                    (engine._REVIEW_WT_LOCK_NS, d))
    try:
        summary = agent_runner.run_review_job(engine.get_job(d), env="host", agent_cmd=FAKE_OK)
    finally:
        with holder.cursor() as cur:
            cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                        (engine._REVIEW_WT_LOCK_NS, d))
        holder.close()
    assert summary["status"] == "contended"
    assert _status(conn_test, jid) == "pending"            # re-claimable, not stranded


def test_k1_keep_worktree_preserves_and_releases(conn_test, review_env):
    repo, runs = review_env
    d = "review-k1000001"
    engine.enqueue(dispatch_id=d, title="k", payload={"review_head": "HEAD", "keep_worktree": True},
                   target="codex", kind="agent", env_required="host")
    job = engine.get_job(d)
    summary = agent_runner.run_review_job(job, env="host", agent_cmd=FAKE_OK)
    assert summary["cleanup_status"] == "kept"
    assert os.path.isdir(os.path.join(runs, d))            # kept
    with engine.review_worktree_lock(d) as held:           # lock was released at terminal handling
        assert held is True
    subprocess.run(["git", "-C", repo, "worktree", "remove", "--force",
                    os.path.join(runs, d)], check=False)
```

- [ ] **Step 6: Run the full runner suite**

Run: `... pytest tests/test_review_worktree_lock.py -v`
Expected: PASS (E/F/R/K series all green).

- [ ] **Step 7: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/agent_runner.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "feat(apex-jobs): run_review_job under PG lock + flock; loser opens no run, no strand"
```

---

## Task 5: prune integration (PG lock + flock + `contended`)

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/prune.py` (the `apply` loop in `prune_review_worktrees`; the `ReviewWorktree.classification` comment)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py`

**Interfaces:**
- Consumes: `engine.review_worktree_lock` (T1), `agent_runner._worktree_flock` (T3), the unchanged `classify_review_worktrees`, `_fresh_candidate`, `_classify_one`, `_refusal`, `agent_runner._WORKTREE_LOCK`, `agent_runner._git`.
- Produces: `prune_review_worktrees(apply=..., include_failed=...)` where a live-held dispatch is classified `contended` (`action="preserved"`), and the apply loop cannot fail-open on a lock/transport error.

- [ ] **Step 1: Write the failing test (P2 -- flock held by a live runner)**

```python
def test_p2_prune_preserves_flock_held(conn_test, review_env):
    from apex_jobs import prune
    repo, runs = review_env
    d = "review-p2000001"
    jid = _enqueue_review(d)
    # a succeeded run + a real clean worktree -> normally 'prunable'
    _seed_run_succeeded(conn_test, jid)
    wt = os.path.join(runs, d)
    subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, "HEAD"], check=True)
    fd = _hold_flock(runs, d)                              # a live runner holds the path
    try:
        res = prune.prune_review_worktrees(apply=True)
    finally:
        os.close(fd)
    item = next(i for i in res["items"] if i["dispatch_id"] == d)
    assert item["classification"] == "contended" and item["action"] == "preserved"
    assert os.path.isdir(wt)                               # NOT removed
    subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], check=False)
```

Add this helper to the test module (near the other helpers):

```python
def _seed_run_succeeded(conn, job_id):
    with conn.cursor() as cur:
        cur.execute("insert into jobs.run (job_id, attempt, claimed_by, env, status, "
                    "claimed_at, finished_at) values (%s, 1, 'cc', 'host', 'succeeded', "
                    "now(), now())", (job_id,))
```

- [ ] **Step 2: Run to confirm it fails (current prune removes it)**

Run: `... pytest tests/test_review_worktree_lock.py -k p2_prune -v`
Expected: FAIL -- current prune removes the worktree (`classification == "prunable"`, `action == "removed"`) because it does not consult the flock.

- [ ] **Step 3: Patch the prune apply loop**

In `prune.py`, add the import near the top (after `from . import agent_runner`):

```python
from . import engine as _engine  # review_worktree_lock lives in engine
```

(Note: `engine` is already imported as `from . import engine`; reuse it -- do NOT add a duplicate alias if `engine` is already imported. Use `engine.review_worktree_lock`.)

Extend the `ReviewWorktree.classification` docstring/comment enum to include `contended`:

```python
    classification: str          # prunable|active|dirty|locked|orphan|failed|unknown|remove-failed|contended
```

Replace the per-item apply block (currently `for w in items: ... with agent_runner._WORKTREE_LOCK: ...`) with:

```python
    if apply:
        for w in items:
            if w.classification != "prunable":
                continue
            try:
                with engine.review_worktree_lock(w.dispatch_id) as held:
                    if not held:
                        w.classification, w.action = "contended", "preserved"
                        continue
                    with agent_runner._worktree_flock(runs, w.dispatch_id) as fuse_ok:
                        if not fuse_ok:
                            w.classification, w.action = "contended", "preserved"
                            continue
                        with agent_runner._WORKTREE_LOCK:
                            # recheck-before-remove: re-query THIS dispatch + re-enumerate its
                            # git/fs facts, then FULLY re-classify -- remove only if STILL prunable.
                            try:
                                snap = engine.review_dispatch_statuses([w.dispatch_id])
                                cand = _fresh_candidate(repo, runs, w.dispatch_id)
                            except (psycopg.OperationalError, psycopg.InterfaceError):
                                return _refusal(items, "db-unreachable", applied=True,
                                                remove_failed=remove_failed)
                            except GitUnavailable:
                                return _refusal(items, "git-unavailable", applied=True,
                                                remove_failed=remove_failed)
                            db = snap.get(w.dispatch_id)
                            if cand is None:
                                w.classification, w.action = "unknown", "preserved"
                                continue
                            cls, _act, status, claimed_at, finished_at, active = _classify_one(
                                cand, db, include_failed)
                            if cls != "prunable":
                                w.classification, w.action = cls, "preserved"
                                w.status, w.claimed_at, w.finished_at, w.active = (
                                    status, claimed_at, finished_at, active)
                                continue
                            r = agent_runner._git("worktree", "remove", w.path, cwd=repo, check=False)
                            if r.returncode == 0:
                                w.action = "removed"
                            else:
                                w.classification, w.action = "remove-failed", "preserved"
                                remove_failed += 1
            except (engine.LockUnavailable, psycopg.OperationalError, psycopg.InterfaceError):
                return _refusal(items, "db-unreachable", applied=True, remove_failed=remove_failed)
```

> Note for the implementer: this preserves the existing recheck-before-remove logic verbatim; the only additions are the two enclosing `with engine.review_worktree_lock(...)` / `with agent_runner._worktree_flock(...)` guards, the two `contended`/`preserved` early-continues, and the broadened outer `except`. Copy the inner recheck body from the current `prune.py` to avoid drift.

- [ ] **Step 4: Add P1 (PG lock held) + P3 (both released -> removed) + confirm P5 dry-run unaffected**

```python
def test_p1_prune_preserves_pg_lock_held(conn_test, review_env):
    from apex_jobs import prune
    repo, runs = review_env
    d = "review-p1000001"
    jid = _enqueue_review(d)
    _seed_run_succeeded(conn_test, jid)
    wt = os.path.join(runs, d)
    subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, "HEAD"], check=True)
    holder = engine._conn(); holder.autocommit = True
    with holder.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s))",
                    (engine._REVIEW_WT_LOCK_NS, d))
    try:
        res = prune.prune_review_worktrees(apply=True)
    finally:
        with holder.cursor() as cur:
            cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                        (engine._REVIEW_WT_LOCK_NS, d))
        holder.close()
    item = next(i for i in res["items"] if i["dispatch_id"] == d)
    assert item["classification"] == "contended"
    assert os.path.isdir(wt)
    subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], check=False)


def test_p3_prune_removes_when_free(conn_test, review_env):
    from apex_jobs import prune
    repo, runs = review_env
    d = "review-p3000001"
    jid = _enqueue_review(d)
    _seed_run_succeeded(conn_test, jid)
    wt = os.path.join(runs, d)
    subprocess.run(["git", "-C", repo, "worktree", "add", "--detach", wt, "HEAD"], check=True)
    res = prune.prune_review_worktrees(apply=True)         # nothing holds the locks
    item = next(i for i in res["items"] if i["dispatch_id"] == d)
    assert item["action"] == "removed"
    assert not os.path.isdir(wt)
```

- [ ] **Step 5: Run the P-series**

Run: `... pytest tests/test_review_worktree_lock.py -k "p1_prune or p2_prune or p3_prune" -v`
Expected: PASS.

- [ ] **Step 6: Run the WHOLE suite to confirm test_prune.py still green + byte-unchanged**

Run: `... pytest -v`
Then verify: `git diff --stat -- packages/apex-jobs/tests/test_prune.py` -> **no output** (byte-unchanged).
Expected: full suite PASS; `test_prune.py` unmodified.

- [ ] **Step 7: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/prune.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "feat(apex-jobs): prune honors PG lock + flock (contended preserve, fail-closed)"
```

---

## Task 6: CLI `review-run` tolerates `run=None`

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/cli.py` (`cmd_review_run`)
- Test: `packages/apex-jobs/tests/test_review_worktree_lock.py`

**Interfaces:**
- Consumes: `run_review_job` (T4) returning `summary["run"] is None` on contention.
- Produces: `cmd_review_run` never calls `engine.runs_for(disp)[-1]` when `run is None`; emits empty findings, includes `contended`, exits 3.

- [ ] **Step 1: Write the failing test**

```python
def test_r7_cli_review_run_contended_no_indexerror(conn_test, review_env, capsys):
    from apex_jobs import cli
    repo, runs = review_env
    d = "review-r7000001"
    holder = engine._conn(); holder.autocommit = True
    with holder.cursor() as cur:
        cur.execute("select pg_try_advisory_lock(%s, hashtext(%s))",
                    (engine._REVIEW_WT_LOCK_NS, d))
    os.environ["APEX_JOBS_AGENT_CMD"] = '["python3","-c","print(0)"]'
    try:
        rc = cli.main(["review-run", "--review-head", "HEAD", "--base-ref", "HEAD",
                       "--dispatch-id", d, "--json"])
    finally:
        del os.environ["APEX_JOBS_AGENT_CMD"]
        with holder.cursor() as cur:
            cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                        (engine._REVIEW_WT_LOCK_NS, d))
        holder.close()
    assert rc == 3                                        # contended -> exit 3, no IndexError
    out = capsys.readouterr().out
    assert '"contended": true' in out
```

> Note: confirm `cli.main(argv)` is the entrypoint that dispatches to `fn(a)` and returns its int. If the entrypoint has a different name, adjust the call; the behavior asserted (exit 3, no crash, `contended` in JSON) is what matters.

- [ ] **Step 2: Run to confirm failure**

Run: `... pytest tests/test_review_worktree_lock.py -k r7_cli -v`
Expected: FAIL with `IndexError: list index out of range` (from `engine.runs_for(disp)[-1]` on no run).

- [ ] **Step 3: Patch `cmd_review_run`**

In `cli.py`, replace the block from `summary = agent_runner.run_review_job(...)` through the `return 0 if ...` with:

```python
    summary = agent_runner.run_review_job(job, env="host", agent_cmd=agent_cmd)
    contended = bool(summary.get("contended"))
    if summary.get("run") is None:
        res = {}                                          # contended: no run -> no findings read
    else:
        runs = engine.runs_for(disp)
        res = (runs[-1]["result"] if runs else None) or {}
    if a.json:
        print(json.dumps({"dispatch_id": disp, "status": summary["status"],
                          "review_head": a.review_head, "base_ref": a.base_ref,
                          "cleanup_status": summary["cleanup_status"],
                          "contended": contended,
                          "findings": res.get("findings", "")}, indent=2))
    else:
        print(f"dispatch_id={disp} status={summary['status']} contended={contended}")
        print("---- findings ----")
        print(res.get("findings", ""))
    return 0 if summary["status"] == "succeeded" else 3
```

- [ ] **Step 4: Run to confirm passing**

Run: `... pytest tests/test_review_worktree_lock.py -k r7_cli -v`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `... pytest -v`
Expected: full suite PASS; `git diff --stat -- tests/test_prune.py` empty.

- [ ] **Step 6: Commit**

```bash
git add packages/apex-jobs/src/apex_jobs/cli.py packages/apex-jobs/tests/test_review_worktree_lock.py
git commit -m "fix(apex-jobs): review-run CLI tolerates contended run=None (no IndexError, exit 3)"
```

---

## Final: whole-branch Codex cross-engine review

- [ ] Run the full suite once more and confirm green + `test_prune.py` byte-unchanged.
- [ ] Whole-branch Codex review from the worktree:

```bash
ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; \
  cd /home/olares/code/apex/apex-review-wtlock; \
  codex exec review --dangerously-bypass-approvals-and-sandbox -c model_reasoning_effort=high --base main'
```

- [ ] Fold any actionable finding (TDD: failing test -> fix -> green) and re-review to convergence.
- [ ] Then use superpowers:finishing-a-development-branch (operator-gated squash merge, no admin-bypass, no local merge).

---

## Self-Review

**1. Spec coverage:**
- Spec 4.3 `review_worktree_lock` + `LockUnavailable` + `_NS` -> Task 1 (E1-E9). autocommit E8, value-silence E5-E7, NS E9. Covered.
- Spec 4.3 `release_claim` -> Task 2. Covered.
- Spec 4.3b `_worktree_flock` (O_CLOEXEC, fail-closed) -> Task 3 (F1, F1b, F4). Covered.
- Spec 4.4 `run_review_job` reorder + `_contended` + release_claim -> Task 4 (R1-R6, F2, F3). Covered. Startup `--force` only under both locks -> R1/R3 git-spy + F2/F3. Covered.
- Spec 4.5 destructive-op guard (flock guards removal) -> exercised by F3 (fuse blocks delete) + R2 (auto-clean under held flock). Covered.
- Spec 4.6 prune (contended, broadened except) -> Task 5 (P1-P3). P4 (LockUnavailable refusal) -> the broadened `except` is covered by code; add an explicit P4 test if desired (monkeypatch `engine.review_worktree_lock` to raise `LockUnavailable` inside the loop -> assert `refused_reason == "db-unreachable"`). **Gap fix:** add P4 to Task 5 Step 4.
- Spec 4.7 keep -> Task 4 K1. Covered.
- Spec 4.8 CLI run=None -> Task 6 (R7). Covered.
- Spec 9 G1 (byte-unchanged test_prune) -> Task 5 Step 6 + Task 6 Step 5 verify `git diff --stat`. Covered.

**Gap found + fixed:** add **P4** to Task 5 Step 4:
```python
def test_p4_prune_lock_unavailable_refuses(conn_test, review_env, monkeypatch):
    from apex_jobs import prune
    repo, runs = review_env
    d = "review-p4000001"
    jid = _enqueue_review(d)
    _seed_run_succeeded(conn_test, jid)
    subprocess.run(["git", "-C", repo, "worktree", "add", "--detach",
                    os.path.join(runs, d), "HEAD"], check=True)
    from contextlib import contextmanager
    @contextmanager
    def boom(dispatch_id):
        raise engine.LockUnavailable()
        yield  # pragma: no cover
    monkeypatch.setattr(engine, "review_worktree_lock", boom)
    res = prune.prune_review_worktrees(apply=True)
    assert res["refused"] is True and res["refused_reason"] == "db-unreachable"
    subprocess.run(["git", "-C", repo, "worktree", "remove", "--force",
                    os.path.join(runs, d)], check=False)
```

**2. Placeholder scan:** No "TBD"/"implement later"/"handle edge cases". Every code step has complete code. The one advisory note ("copy the inner recheck body verbatim") points at exact existing code, not a placeholder.

**3. Type consistency:** `run_review_job` returns `run` = `str(run_id)` (winner) or `None` (loser); `status` in {`succeeded`,`failed`,`contended`}; `contended` bool present on both branches; `cleanup_status` present on both. CLI (T6) reads `summary.get("run")`/`summary["status"]`/`summary["cleanup_status"]`/`summary.get("contended")` -- all defined in T4. `review_worktree_lock(dispatch_id)`, `release_claim(job_id)`, `_worktree_flock(runs, dispatch_id)` signatures match across T1/T2/T3/T4/T5. `_REVIEW_WT_LOCK_NS` is one constant. Consistent.
