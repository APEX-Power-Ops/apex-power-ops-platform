"""TDD - apex-jobs prune-review-worktrees: engine query, classification, apply,
CLI. Real orchestration_test DB (conn_test) + throwaway detached worktrees under
a tmp runs dir. Value-silent: assertions use statuses/labels/counts/booleans
only -- never file contents or env."""
import os
import subprocess
import sys

import psycopg
from psycopg.types.json import Json
import pytest

from apex_jobs import engine

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # lane repo root


def _enqueue_review(dispatch_id, kind="agent", review_head="HEAD"):
    """Create a codex-review jobs.job (kind='agent', payload.review_head set).
    Returns job id. Uses engine.enqueue so all NOT NULL/default columns are set."""
    payload = {"review_head": review_head} if review_head is not None else {}
    return engine.enqueue(dispatch_id=dispatch_id, title=f"codex review {dispatch_id}",
                          payload=payload, target="codex", kind=kind, env_required="host")


def _enqueue_nonreview(dispatch_id):
    """A non-review job at a review-* dispatch_id (kind='agent', NO review_head)."""
    return engine.enqueue(dispatch_id=dispatch_id, title="not a review",
                          payload={"prompt": "x"}, target="cc", kind="agent",
                          env_required="host")


def _seed_run(conn, job_id, *, status, attempt, claimed_at=None,
              finished_at=None, worktree_path=None):
    """Insert one jobs.run row with explicit status/attempt/timestamps.
    claimed_at/finished_at are SQL-castable strings (ISO) or None (-> now()/NULL)."""
    with conn.cursor() as cur:
        cur.execute(
            "insert into jobs.run "
            "(job_id, attempt, claimed_by, env, status, claimed_at, finished_at, worktree_path) "
            "values (%s, %s, 'cc', 'host', %s, coalesce(%s::timestamptz, now()), "
            "%s::timestamptz, %s)",
            (job_id, attempt, status, claimed_at, finished_at, worktree_path))


def test_review_dispatch_statuses_shape_and_latest(conn_test):
    d = "review-aaaa1111"
    jid = _enqueue_review(d)
    # two runs; the newer (by claimed_at) is the succeeded one
    _seed_run(conn_test, jid, status="failed", attempt=1,
              claimed_at="2026-07-05T00:00:00+00:00")
    _seed_run(conn_test, jid, status="succeeded", attempt=2,
              claimed_at="2026-07-05T01:00:00+00:00",
              finished_at="2026-07-05T01:05:00+00:00")
    out = engine.review_dispatch_statuses([d, "review-doesnotex"])
    assert set(out.keys()) == {d}                     # absent dispatch -> not a key
    row = out[d]
    assert row["is_review"] is True
    assert row["any_running"] is False
    assert row["status"] == "succeeded"               # latest by claimed_at DESC
    assert row["claimed_at"].isoformat().startswith("2026-07-05T01:00:00")
    assert row["finished_at"] is not None


def test_review_dispatch_statuses_any_running_true(conn_test):
    d = "review-bbbb2222"
    jid = _enqueue_review(d)
    _seed_run(conn_test, jid, status="succeeded", attempt=1)
    _seed_run(conn_test, jid, status="running", attempt=2, worktree_path=None)
    out = engine.review_dispatch_statuses([d])
    assert out[d]["any_running"] is True              # a running row anywhere -> True


def test_review_dispatch_statuses_non_review(conn_test):
    d = "review-cccc3333"
    jid = _enqueue_nonreview(d)
    _seed_run(conn_test, jid, status="succeeded", attempt=1)
    assert engine.review_dispatch_statuses([d])[d]["is_review"] is False


# ------------------------- Task 2: classification (dry-run) -------------------

from apex_jobs import prune, agent_runner


@pytest.fixture
def prune_env(conn_test, tmp_path, monkeypatch):
    """Isolated runs dir + REPO; removes any review worktree it creates."""
    runs = str(tmp_path / "runs")
    os.makedirs(runs, exist_ok=True)
    monkeypatch.setenv("APEX_JOBS_REPO", REPO)
    monkeypatch.setenv("APEX_JOBS_RUNS_DIR", runs)
    created = []
    yield conn_test, runs, created
    for name in created:
        subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force",
                        os.path.join(runs, name)], capture_output=True)
    subprocess.run(["git", "-C", REPO, "worktree", "prune"], capture_output=True)


def _add_wt(runs, created, name, ref="HEAD"):
    """Create a detached worktree runs/<name> on disk. Returns its path."""
    created.append(name)
    p = os.path.join(runs, name)
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", p, ref],
                   check=True, capture_output=True)
    return p


def _classify_map(include_failed=False):
    """{dispatch_id: classification} for the current runs dir."""
    return {w.dispatch_id: w.classification
            for w in prune.classify_review_worktrees(include_failed=include_failed)}


def test_succeeded_clean_is_prunable(prune_env):
    conn, runs, created = prune_env
    d = "review-1111aaaa"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    assert _classify_map()[d] == "prunable"


def test_inflight_running_null_worktree_path_preserved(prune_env):
    """The F1 fix: a running review whose run row has worktree_path=NULL is found
    by dispatch_id (not path) and preserved as active."""
    conn, runs, created = prune_env
    d = "review-2222bbbb"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="running", attempt=1, worktree_path=None)
    _add_wt(runs, created, d)
    w = {x.dispatch_id: x for x in prune.classify_review_worktrees()}[d]
    assert w.classification == "active" and w.active is True


def test_path_reuse_within_job_preserved(prune_env):
    """Succeeded attempt N + running attempt N+1 on one job -> any_running -> active."""
    conn, runs, created = prune_env
    d = "review-3333cccc"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              claimed_at="2026-07-05T00:00:00+00:00")
    _seed_run(conn, jid, status="running", attempt=2,
              claimed_at="2026-07-05T02:00:00+00:00", worktree_path=None)
    _add_wt(runs, created, d)
    assert _classify_map()[d] == "active"


def test_latest_terminal_by_claimed_at(prune_env):
    """Older failed + newer succeeded -> latest terminal = succeeded -> prunable."""
    conn, runs, created = prune_env
    d = "review-4444dddd"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="failed", attempt=1,
              claimed_at="2026-07-05T00:00:00+00:00")
    _seed_run(conn, jid, status="succeeded", attempt=2,
              claimed_at="2026-07-05T03:00:00+00:00")
    _add_wt(runs, created, d)
    assert _classify_map()[d] == "prunable"


def test_dirty_tracked_modification_preserved(prune_env):
    conn, runs, created = prune_env
    d = "review-5555eeee"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    with open(os.path.join(p, "README.md"), "a") as f:
        f.write("dirty\n")
    assert _classify_map()[d] == "dirty"


def test_ignored_file_counts_dirty(prune_env):
    """git status --porcelain --ignored surfaces ignored files -> dirty."""
    conn, runs, created = prune_env
    d = "review-6666ffff"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    os.makedirs(os.path.join(p, "node_modules"), exist_ok=True)
    with open(os.path.join(p, "node_modules", "x"), "w") as f:
        f.write("junk\n")
    assert _classify_map()[d] == "dirty"


def test_locked_preserved(prune_env):
    conn, runs, created = prune_env
    d = "review-7777aaaa"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    subprocess.run(["git", "-C", REPO, "worktree", "lock", p], check=True,
                   capture_output=True)
    try:
        assert _classify_map()[d] == "locked"
    finally:
        subprocess.run(["git", "-C", REPO, "worktree", "unlock", p],
                       capture_output=True)


def test_failed_preserved_then_pruned_with_include_failed(prune_env):
    conn, runs, created = prune_env
    d = "review-8888bbbb"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="failed", attempt=1)
    _add_wt(runs, created, d)
    assert _classify_map(include_failed=False)[d] == "failed"
    assert _classify_map(include_failed=True)[d] == "prunable"


def test_orphan_no_job_row_preserved(prune_env):
    conn, runs, created = prune_env
    d = "review-9999cccc"          # valid basename, NO jobs.job row
    _add_wt(runs, created, d)
    assert _classify_map()[d] == "orphan"


def test_non_review_job_is_unknown(prune_env):
    conn, runs, created = prune_env
    d = "review-aaaadddd"
    jid = _enqueue_nonreview(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    assert _classify_map()[d] == "unknown"


def test_noncandidate_basename_not_enumerated(prune_env):
    conn, runs, created = prune_env
    _add_wt(runs, created, "review-notgen")     # fails ^review-[0-9a-f]{8}$
    assert "review-notgen" not in _classify_map()


def test_missing_dir_is_unknown(prune_env):
    conn, runs, created = prune_env
    d = "review-eeee1111"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    import shutil
    shutil.rmtree(p)               # registration remains, dir gone
    assert _classify_map()[d] == "unknown"


def test_git_status_nonzero_is_unknown(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-ffff2222"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    real = prune._worktree_flags
    def boom(path, locked):
        f = real(path, locked)
        f["git_ok"] = False
        return f
    monkeypatch.setattr(prune, "_worktree_flags", boom)
    assert _classify_map()[d] == "unknown"


def test_db_unreachable_raises(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-11112222"
    _enqueue_review(d)
    _add_wt(runs, created, d)
    def raise_op(_ids):
        raise psycopg.OperationalError("connection refused")
    monkeypatch.setattr(engine, "review_dispatch_statuses", raise_op)
    with pytest.raises(prune.DbUnreachable):
        prune.classify_review_worktrees()
