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
    import uuid
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
