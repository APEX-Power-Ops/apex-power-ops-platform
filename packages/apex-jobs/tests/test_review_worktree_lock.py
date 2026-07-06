"""TDD - apex-jobs review worktree lifecycle lock (PG advisory lock coordinator +
flock liveness fuse). Real orchestration_test DB (conn_test) + throwaway detached
worktrees under a tmp runs dir. Value-silent: assertions use statuses/labels/
counts/booleans only -- never file contents, env, or DSN. Kept in a SEPARATE
module so test_prune.py stays byte-unchanged."""
import fcntl
import os
import subprocess
import sys

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


# ---- Task 2: release_claim CAS (conn_test yields TUPLE rows -> positional [0]) ----
def _set_status(conn, job_id, status):
    with conn.cursor() as cur:
        cur.execute("update jobs.job set status=%s where id=%s", (status, job_id))


def _status(conn, job_id):
    with conn.cursor() as cur:
        cur.execute("select status from jobs.job where id=%s", (job_id,))
        return cur.fetchone()[0]


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


# ---- Task 3: _worktree_flock runner-liveness fuse ----
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
    # While holding the flock inside the CM, a child subprocess opening its OWN fd
    # must be BLOCKED (we hold LOCK_EX) and must not have inherited our fd.
    with agent_runner._worktree_flock(runs, d) as ok:
        assert ok is True
        code = (
            "import fcntl,os,sys\n"
            f"fd=os.open({os.path.join(runs, d + '.lock')!r},os.O_CREAT|os.O_RDWR,0o600)\n"
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


# ---- Task 4: run_review_job restructure (PG lock -> flock -> start() -> git ops) ----
# absolute interpreter path (matches test_agent_runner idiom): the review agent runs
# under _agent_env's sanitized PATH, so a bare "python3" would be PATH-fragile.
FAKE_OK = [sys.executable, "-c", "print('review findings ok')"]


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
