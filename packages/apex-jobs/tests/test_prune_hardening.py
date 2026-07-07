"""TDD - prune-review-worktrees hardening: orphan-lock enumeration, buckets,
--force-succeeded-dirty, --prune-orphan-locks. Reuses test_prune's fixtures +
helpers (test_prune.py stays byte-unchanged). Value-silent: labels/counts/booleans
only. Fake review dirs + .lock files under a tmp runs dir; real orchestration_test."""
import os

import pytest

from apex_jobs import prune, agent_runner, engine
from test_prune import prune_env, _add_wt, _seed_run, _enqueue_review, _enqueue_nonreview, REPO  # noqa: F401


def _touch_lock(runs, dispatch_id):
    """Create runs/<dispatch_id>.lock (an UNHELD sidecar: no process holds it)."""
    os.makedirs(runs, exist_ok=True)
    p = os.path.join(runs, dispatch_id + ".lock")
    open(p, "a").close()
    return p


def _registered():
    return [w.dispatch_id for w in prune.classify_review_worktrees()]


def _orphans():
    return {o.dispatch_id: o for o in prune.classify_orphan_locks(_registered())}


def test_orphan_lock_stale_enumerated(prune_env):
    conn, runs, created = prune_env
    d = "review-1a1a1a1a"
    _touch_lock(runs, d)                     # lock, no worktree, no job row
    o = _orphans()[d]
    assert o.has_registered_worktree is False
    assert o.has_active_run is False
    assert o.held is False                   # unheld sidecar


def test_orphan_lock_with_registered_worktree_excluded(prune_env):
    conn, runs, created = prune_env
    d = "review-2b2b2b2b"
    _add_wt(runs, created, d)                # registered worktree
    _touch_lock(runs, d)
    assert d not in _orphans()               # not orphan: excluded (check 2)


def test_orphan_lock_active_run_flagged(prune_env):
    conn, runs, created = prune_env
    d = "review-3c3c3c3c"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="running", attempt=1)
    _touch_lock(runs, d)
    assert _orphans()[d].has_active_run is True   # check 3


def test_orphan_lock_held_flagged(prune_env):
    conn, runs, created = prune_env
    d = "review-4d4d4d4d"
    _touch_lock(runs, d)
    with agent_runner._worktree_flock(runs, d) as ok:
        assert ok is True                    # we hold it now
        assert _orphans()[d].held is True    # check 4: probe sees it held


def test_nonmatching_lock_not_enumerated(prune_env):
    conn, runs, created = prune_env
    os.makedirs(runs, exist_ok=True)
    open(os.path.join(runs, "review-notgen.lock"), "a").close()   # bad basename (check 1)
    open(os.path.join(runs, "other.lock"), "a").close()
    assert prune.list_orphan_locks(runs, []) == []
