"""TDD - apex-jobs review-worktree auto-clean.

Reuses test_prune.py's prune_env fixture + helpers by IMPORT (kept there so the
test_prune regression gate stays byte-unchanged; promoting the shared fixture to
conftest.py is a trivial future cleanup). Real orchestration_test DB + throwaway
detached worktrees under a tmp runs dir. Value-silent: assertions use
statuses/labels/counts/booleans only -- never file contents or env.
"""
import json
import os
import subprocess
import uuid

import pytest

from apex_jobs import engine, agent_runner, cli
# Import-reuse (documented above): prune_env is an imported fixture; _add_wt /
# _enqueue_review / REPO are helpers shared with test_prune.py.
from test_prune import prune_env, _add_wt, _enqueue_review, REPO  # noqa: F401


# --------------------------- shared helpers -----------------------------------

def _job(dispatch_id, review_head="HEAD", **payload_extra):
    """Enqueue a review job (kind='agent', payload.review_head) and return the job dict."""
    payload = {"review_head": review_head}
    payload.update(payload_extra)
    engine.enqueue(dispatch_id=dispatch_id, title=f"codex review {dispatch_id}",
                   payload=payload, target="codex", kind="agent", env_required="host")
    return engine.get_job(dispatch_id)


def _current_run(dispatch_id, review_head="HEAD"):
    """A review job + one open run; run_is_current(run_id) is True."""
    job = _job(dispatch_id, review_head)
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    return job, run_id


def _spy_git(monkeypatch):
    """Record positional args of every agent_runner._git call; passthrough to the real impl."""
    calls = []
    real_git = agent_runner._git
    monkeypatch.setattr(agent_runner, "_git",
                        lambda *a, **k: (calls.append(a), real_git(*a, **k))[1])
    return calls


# =============================== Task 1: engine ================================

def test_run_is_current_true_for_only_attempt(prune_env):
    job = _job("review-aaaa0001")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    assert engine.run_is_current(run_id) is True


def test_run_is_current_false_when_superseded(prune_env):
    job = _job("review-aaaa0002")
    r1 = engine.start(job["id"], claimed_by="cc", run_env="host")
    r2 = engine.start(job["id"], claimed_by="cc", run_env="host")
    assert engine.run_is_current(r2) is True
    assert engine.run_is_current(r1) is False


def test_run_is_current_false_for_unknown(prune_env):
    assert engine.run_is_current(uuid.uuid4()) is False


def test_set_run_cleanup_merges_without_clobbering(prune_env):
    job = _job("review-aaaa0003")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    engine.report(run_id, exit_code=0, result={"findings": "F", "is_review": True})
    engine.set_run_cleanup(run_id, "cleaned")
    res = engine.runs_for("review-aaaa0003")[-1]["result"]
    assert res["cleanup_status"] == "cleaned"
    assert res["findings"] == "F"
    assert res["is_review"] is True


def test_set_run_cleanup_null_result_safe(prune_env):
    job = _job("review-aaaa0004")
    run_id = engine.start(job["id"], claimed_by="cc", run_env="host")
    engine.set_run_cleanup(run_id, "not_attempted")
    res = engine.runs_for("review-aaaa0004")[-1]["result"]
    assert res["cleanup_status"] == "not_attempted"


# =========================== Task 2: cleanup helper ===========================

def test_cleanup_pristine_current_returns_cleaned(prune_env):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000001")
    wt = _add_wt(runs, created, "review-b0000001")
    assert agent_runner._cleanup_review_worktree(REPO, wt, run_id) == "cleaned"
    assert not os.path.isdir(wt)


def test_cleanup_ignored_dirt_returns_dirty_preserved(prune_env):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000002")
    wt = _add_wt(runs, created, "review-b0000002")
    os.makedirs(os.path.join(wt, "__pycache__"), exist_ok=True)
    with open(os.path.join(wt, "__pycache__", "x.pyc"), "w") as f:
        f.write("x")
    assert agent_runner._cleanup_review_worktree(REPO, wt, run_id) == "dirty_preserved"
    assert os.path.isdir(wt)


def test_cleanup_untracked_dirt_returns_dirty_preserved(prune_env):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000003")
    wt = _add_wt(runs, created, "review-b0000003")
    with open(os.path.join(wt, "untracked.txt"), "w") as f:
        f.write("x")
    assert agent_runner._cleanup_review_worktree(REPO, wt, run_id) == "dirty_preserved"
    assert os.path.isdir(wt)


def test_cleanup_absent_returns_already_absent(prune_env):
    conn, runs, created = prune_env
    wt = os.path.join(runs, "review-b0000004")   # never created on disk
    assert agent_runner._cleanup_review_worktree(REPO, wt, uuid.uuid4()) == "already_absent"


def test_cleanup_superseded_returns_superseded_and_does_not_touch(prune_env, monkeypatch):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000005")
    wt = _add_wt(runs, created, "review-b0000005")
    monkeypatch.setattr(engine, "run_is_current", lambda rid: False)
    calls = _spy_git(monkeypatch)
    assert agent_runner._cleanup_review_worktree(REPO, wt, run_id) == "superseded_preserved"
    assert os.path.isdir(wt)
    assert not any(a[:1] == ("status",) for a in calls)
    assert not any(a[:2] == ("worktree", "remove") for a in calls)


def test_cleanup_absent_beats_superseded(prune_env, monkeypatch):
    conn, runs, created = prune_env
    wt = os.path.join(runs, "review-b0000006")   # absent
    monkeypatch.setattr(engine, "run_is_current", lambda rid: False)
    assert agent_runner._cleanup_review_worktree(REPO, wt, uuid.uuid4()) == "already_absent"


def test_cleanup_remove_failure_returns_failed_preserved(prune_env, monkeypatch):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000007")
    wt = _add_wt(runs, created, "review-b0000007")

    real_git = agent_runner._git

    class _R:
        returncode = 1
        stdout = ""
        stderr = ""

    def fake_git(*a, **k):
        if a[:2] == ("worktree", "remove"):
            return _R()
        return real_git(*a, **k)

    monkeypatch.setattr(agent_runner, "_git", fake_git)
    assert agent_runner._cleanup_review_worktree(REPO, wt, run_id) == "failed_preserved"
    assert os.path.isdir(wt)


def test_cleanup_never_passes_force(prune_env, monkeypatch):
    conn, runs, created = prune_env
    job, run_id = _current_run("review-b0000008")
    wt = _add_wt(runs, created, "review-b0000008")
    seen = _spy_git(monkeypatch)
    agent_runner._cleanup_review_worktree(REPO, wt, run_id)
    removes = [a for a in seen if a[:2] == ("worktree", "remove")]
    assert removes, "expected a worktree remove on a clean tree"
    assert not any("--force" in a for a in removes)
