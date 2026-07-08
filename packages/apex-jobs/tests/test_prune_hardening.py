"""TDD - prune-review-worktrees hardening: orphan-lock enumeration, buckets,
--force-succeeded-dirty, --prune-orphan-locks. Reuses test_prune's fixtures +
helpers (test_prune.py stays byte-unchanged). Value-silent: labels/counts/booleans
only. Fake review dirs + .lock files under a tmp runs dir; real orchestration_test."""
import os

import psycopg
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


def test_summary_has_additive_buckets_and_keys(prune_env):
    conn, runs, created = prune_env
    d1 = "review-5e5e5e5e"; jid = _enqueue_review(d1)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    _add_wt(runs, created, d1)
    _touch_lock(runs, "review-6f6f6f6f")
    res = prune.prune_review_worktrees()               # dry-run, no new flags
    for k in ("items", "counts", "applied", "remove_failed", "refused", "refused_reason"):
        assert k in res                                # existing keys preserved
    for k in ("orphan_locks", "buckets", "lock_remove_failed"):
        assert k in res                                # additive keys present
    assert set(res["buckets"]) == {"registered", "dirty_succeeded",
                                   "orphan_locks", "registered_missing"}
    assert res["buckets"]["orphan_locks"] == 1
    assert all("exists" in i for i in res["items"])
    assert res["applied"] is False                     # default still dry-run


def test_dirty_succeeded_bucket_counts(prune_env):
    conn, runs, created = prune_env
    d = "review-7a7a7a7a"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d)
    open(os.path.join(p, "dirty.txt"), "w").close()    # untracked -> dirty
    res = prune.prune_review_worktrees()
    assert res["buckets"]["dirty_succeeded"] == 1
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["classification"] == "dirty" and item["action"] == "preserved"  # default: preserved


def test_force_dirty_dry_run_labels_would_remove_force(prune_env):
    conn, runs, created = prune_env
    d = "review-8b8b8b8b"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d); open(os.path.join(p, "x.txt"), "w").close()
    res = prune.prune_review_worktrees(force_succeeded_dirty=True)     # no --apply
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "would-remove-force" and item["classification"] == "dirty"
    assert os.path.isdir(p)                                            # dry-run: not removed


def test_force_dirty_apply_removes(prune_env):
    conn, runs, created = prune_env
    d = "review-9c9c9c9c"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d); open(os.path.join(p, "x.txt"), "w").close()
    res = prune.prune_review_worktrees(apply=True, force_succeeded_dirty=True)
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "removed-force" and not os.path.isdir(p)


def test_force_dirty_never_touches_failed_or_active(prune_env):
    conn, runs, created = prune_env
    df = "review-a1a1a1a1"; jf = _enqueue_review(df)
    _seed_run(conn, jf, status="failed", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    pf = _add_wt(runs, created, df); open(os.path.join(pf, "x.txt"), "w").close()
    da = "review-b2b2b2b2"; ja = _enqueue_review(da)
    _seed_run(conn, ja, status="running", attempt=1)
    pa = _add_wt(runs, created, da); open(os.path.join(pa, "x.txt"), "w").close()
    prune.prune_review_worktrees(apply=True, force_succeeded_dirty=True)
    assert os.path.isdir(pf) and os.path.isdir(pa)      # neither force-removed


def _lockpath(runs, did):
    return os.path.join(runs, did + ".lock")


def test_prune_orphan_locks_removes_stale(prune_env):
    conn, runs, created = prune_env
    d = "review-c3c3c3c3"; _touch_lock(runs, d)        # no worktree, no run, unheld
    res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    o = [x for x in res["orphan_locks"] if x["dispatch_id"] == d][0]
    assert o["action"] == "removed-lock" and not os.path.exists(_lockpath(runs, d))


def test_prune_orphan_locks_dry_run_labels_only(prune_env):
    conn, runs, created = prune_env
    d = "review-d4d4d4d4"; _touch_lock(runs, d)
    res = prune.prune_review_worktrees(prune_orphan_locks=True)   # no --apply
    o = [x for x in res["orphan_locks"] if x["dispatch_id"] == d][0]
    assert o["action"] == "would-remove-lock" and os.path.exists(_lockpath(runs, d))


def test_prune_orphan_locks_preserves_active_run(prune_env):
    conn, runs, created = prune_env
    d = "review-e5e5e5e5"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="running", attempt=1)
    _touch_lock(runs, d)
    res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    o = [x for x in res["orphan_locks"] if x["dispatch_id"] == d][0]
    assert o["action"] == "preserved" and o["preserve_reason"] == "active-run"
    assert os.path.exists(_lockpath(runs, d))


def test_prune_orphan_locks_preserves_held(prune_env):
    conn, runs, created = prune_env
    d = "review-f6f6f6f6"; _touch_lock(runs, d)
    with agent_runner._worktree_flock(runs, d) as ok:
        assert ok is True
        res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    o = [x for x in res["orphan_locks"] if x["dispatch_id"] == d][0]
    assert o["action"] == "preserved" and o["preserve_reason"] == "held"


def test_cli_parser_accepts_new_flags():
    from apex_jobs import cli
    a = cli.build_parser().parse_args(
        ["prune-review-worktrees", "--apply", "--force-succeeded-dirty", "--prune-orphan-locks"])
    assert a.force_succeeded_dirty is True and a.prune_orphan_locks is True and a.apply is True
    b = cli.build_parser().parse_args(["prune-review-worktrees"])
    assert b.force_succeeded_dirty is False and b.prune_orphan_locks is False


def test_force_dirty_preserves_locked(prune_env):
    import subprocess as _sp
    conn, runs, created = prune_env
    d = "review-c7c7c7c7"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d)
    open(os.path.join(p, "x.txt"), "w").close()                      # dirty
    _sp.run(["git", "-C", REPO, "worktree", "lock", p], check=True, capture_output=True)
    try:
        res = prune.prune_review_worktrees(apply=True, force_succeeded_dirty=True)
        assert os.path.isdir(p)                                       # locked -> not removed
        assert res["remove_failed"] == 0                             # not attempted (no spurious fail)
        item = [i for i in res["items"] if i["dispatch_id"] == d][0]
        assert item["action"] == "preserved" and item["classification"] != "remove-failed"
    finally:
        _sp.run(["git", "-C", REPO, "worktree", "unlock", p], capture_output=True)


def test_prune_orphan_locks_db_error_refuses(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-d8d8d8d8"; _touch_lock(runs, d)
    real = engine.review_dispatch_statuses
    seen = {"n": 0}
    def flaky(ids):
        if list(ids) == [d]:
            seen["n"] += 1
            if seen["n"] >= 2:               # classify ok; fail the apply-time recheck
                raise psycopg.errors.InsufficientPrivilege("boom")
        return real(ids)
    monkeypatch.setattr(engine, "review_dispatch_statuses", flaky)
    res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    assert res["refused"] is True and res["applied"] is True         # value-silent refusal, no traceback
    assert os.path.exists(_lockpath(runs, d))                        # not removed


def test_orphan_lock_db_fail_preserves_items(prune_env, monkeypatch):
    conn, runs, created = prune_env
    dw = "review-e9e9e9e9"; jid = _enqueue_review(dw)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    _add_wt(runs, created, dw)                        # a registered worktree
    dl = "review-fafafafa"; _touch_lock(runs, dl)     # + an orphan lock whose status query fails
    real = engine.review_dispatch_statuses
    def flaky(ids):
        if list(ids) == [dl]:
            raise psycopg.OperationalError("dropped")
        return real(ids)
    monkeypatch.setattr(engine, "review_dispatch_statuses", flaky)
    res = prune.prune_review_worktrees()             # dry-run
    assert res["refused"] is True
    assert any(i["dispatch_id"] == dw for i in res["items"])   # classified worktrees NOT dropped


def test_force_dirty_partial_refusal_relabels_would_remove_force(prune_env, monkeypatch):
    conn, runs, created = prune_env
    for name in ("review-ab010101", "review-ab020202"):
        jid = _enqueue_review(name)
        _seed_run(conn, jid, status="succeeded", attempt=1,
                  finished_at="2026-07-05T00:00:00+00:00")
        pp = _add_wt(runs, created, name)
        open(os.path.join(pp, "x.txt"), "w").close()             # dirty+succeeded
    real = engine.review_dispatch_statuses
    calls = {"n": 0}
    def flaky(ids):
        calls["n"] += 1                              # classify(1) + recheck-removes(2) + recheck-drops(3)
        if calls["n"] >= 3:
            raise psycopg.OperationalError("dropped")
        return real(ids)
    monkeypatch.setattr(engine, "review_dispatch_statuses", flaky)
    res = prune.prune_review_worktrees(apply=True, force_succeeded_dirty=True)
    assert res["refused"] is True and res["applied"] is True
    assert not any(i["action"] == "would-remove-force" for i in res["items"])   # relabeled
    assert any(i["action"] == "refused" for i in res["items"])


def test_orphan_lock_active_run_appears_after_classify(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-cd010101"; _touch_lock(runs, d)      # stale at classify (no job row)
    real = engine.review_dispatch_statuses
    calls = {"n": 0}
    def flaky(ids):
        if list(ids) == [d]:
            calls["n"] += 1
            if calls["n"] >= 2:                      # after classify, before apply recheck: activate
                jid = _enqueue_review(d)
                _seed_run(conn, jid, status="running", attempt=1)
        return real(ids)
    monkeypatch.setattr(engine, "review_dispatch_statuses", flaky)
    res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    o = [x for x in res["orphan_locks"] if x["dispatch_id"] == d][0]
    assert o["preserve_reason"] == "active-run" and o["has_active_run"] is True   # consistent booleans
    assert os.path.exists(_lockpath(runs, d))


def test_orphan_lock_recheck_oserror_refuses(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-de010101"; _touch_lock(runs, d)
    def boom(*a, **k):
        raise OSError("cannot spawn git")            # _fresh_candidate git spawn failure
    monkeypatch.setattr(prune, "_fresh_candidate", boom)
    res = prune.prune_review_worktrees(apply=True, prune_orphan_locks=True)
    assert res["refused"] is True and res["applied"] is True   # value-silent refusal, no traceback
    assert os.path.exists(_lockpath(runs, d))


def test_force_dirty_marked_before_orphan_lock_refusal(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-df010101"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d); open(os.path.join(p, "x.txt"), "w").close()   # dirty+succeeded
    dl = "review-df020202"; _touch_lock(runs, dl)                                # + orphan lock
    real = engine.review_dispatch_statuses
    def flaky(ids):
        if list(ids) == [dl]:
            raise psycopg.OperationalError("dropped")     # fail the orphan status query
        return real(ids)
    monkeypatch.setattr(engine, "review_dispatch_statuses", flaky)
    res = prune.prune_review_worktrees(apply=True, force_succeeded_dirty=True)
    assert res["refused"] is True
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "refused"    # marked would-remove-force then relabeled, not "preserved"


def test_cli_footer_counts_force_actions(prune_env, capsys):
    conn, runs, created = prune_env
    d = "review-e0010101"; jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1,
              finished_at="2026-07-05T00:00:00+00:00")
    p = _add_wt(runs, created, d); open(os.path.join(p, "x.txt"), "w").close()
    from apex_jobs import cli
    args = cli.build_parser().parse_args(
        ["prune-review-worktrees", "--apply", "--force-succeeded-dirty"])
    cli.cmd_prune_review_worktrees(args)
    out = capsys.readouterr().out
    assert "candidates: none" not in out              # force removal not misreported as none
    assert "removed-force" in out
