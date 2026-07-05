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
