# prune-review-worktrees Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, single-writer over mesh). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add richer reporting (buckets + orphan-lock enumeration) and two guarded cleanup modes (`--force-succeeded-dirty`, `--prune-orphan-locks`) to `apex-jobs prune-review-worktrees`, additive-only, without changing any default behavior or existing JSON key.

**Architecture:** Extend `prune.py` with orphan-lock enumeration (`list_orphan_locks`/`classify_orphan_locks`/`OrphanLock`), a `_lock_held` flock probe, additive summary fields, a post-classify force label, an extracted `_guarded_remove_worktree` choreography helper (behavior-preserving refactor of the existing apply loop), and an orphan-lock removal branch with a 4-proof recheck. `classify_review_worktrees` + `_classify_one` stay byte-unchanged. CLI gains two flags. New tests in `test_prune_hardening.py` reuse `test_prune`'s fixtures via import.

**Tech Stack:** Python 3 (psycopg3, fcntl flock), pytest, uv, git worktrees, Infisical injection.

**Spec:** `docs/superpowers/specs/2026-07-07-prune-worktrees-hardening-design.md`

## Global Constraints

- **Additive only.** Never reclassify; never remove/rename an existing summary key (`items`, `counts`, `applied`, `remove_failed`, `refused`, `refused_reason`); flags OFF => byte-identical behavior + output keys.
- **Default cleanup unchanged:** dry-run default; `--apply` removes only clean `prunable`; `--include-failed` stays failed-only.
- **`--force-succeeded-dirty`:** only classification==`dirty` AND status==`succeeded` AND not active; removal REQUIRES `--apply`; NEVER implies `--include-failed`.
- **`--prune-orphan-locks`:** remove a `review-*.lock` only after ALL 4 proofs (basename `^review-[0-9a-f]{8}\.lock$`; no registered worktree; DB no active run OR no row; non-blocking flock acquired); any failure => preserve + `preserve_reason`; removal REQUIRES `--apply`.
- **No real-artifact deletion:** all apply-path testing on throwaway tmp dirs/locks; never `--apply` against the live runs dir in this lane.
- **`test_prune.py` stays byte-unchanged.** New tests live in `test_prune_hardening.py`, importing `prune_env, _add_wt, _seed_run, _enqueue_review, _enqueue_nonreview, REPO` from `test_prune`.
- Value-silent (names/paths/labels/counts/booleans/ISO only); ASCII-only added lines; host-canonical single-writer over mesh; suites via `inject.sh dev` (APEX_JOBS_PGPASSWORD, `APEX_JOBS_DB=orchestration_test`) with `DEV_PG_PASSWORD` unset in-child; merge governance: squash, self-merge after green CI + Codex, no admin-bypass.
- Mesh conventions: `SSH`=`ssh olares-mesh`; `REPO_DIR`=`/home/olares/code/apex/apex-power-ops-platform`; `PATHX`=`export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH`.
- **Injected test runner** (used every test step): `SSH 'cd REPO_DIR && PATHX && infra/infisical/inject.sh dev -- bash -c "unset DEV_PG_PASSWORD; cd packages/apex-jobs && APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest <ARGS>; echo RC=\$?"' 2>&1 | grep -viE "release of infisical|To update|Injecting" | tail -25`

---

## Task 1: orphan-lock enumeration + classification (read-only)

**Files:** Modify `packages/apex-jobs/src/apex_jobs/prune.py`; Create `packages/apex-jobs/tests/test_prune_hardening.py`.

**Produces:** `prune.list_orphan_locks(runs_dir, registered_ids) -> list[dict]`; `prune._lock_held(runs_dir, dispatch_id) -> bool`; `prune.classify_orphan_locks(registered_ids) -> list[OrphanLock]`; `prune.OrphanLock` dataclass `(basename, dispatch_id, held, has_active_run, has_registered_worktree, action, preserve_reason)`.

- [ ] **Step 1: Failing tests** -- create `test_prune_hardening.py`:

```python
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


def _orphans():
    return {o.dispatch_id: o for o in prune.classify_orphan_locks(_registered())}


def _registered():
    return [w.dispatch_id for w in prune.classify_review_worktrees()]


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
```

- [ ] **Step 2: Run, verify FAIL.**
Run (injected): `... pytest tests/test_prune_hardening.py -q`
Expected: FAIL / collection error (`prune.classify_orphan_locks` / `list_orphan_locks` not defined).

- [ ] **Step 3: Implement in `prune.py`.** Add near the top (after `RE_REVIEW`):

```python
RE_LOCK = re.compile(r"^review-[0-9a-f]{8}\.lock$")
```

Add the dataclass (after `ReviewWorktree`):

```python
@dataclass
class OrphanLock:
    basename: str
    dispatch_id: str
    held: bool                   # a live process holds the flock (check 4 failed)
    has_active_run: bool         # DB says a review run is running (check 3 failed)
    has_registered_worktree: bool
    action: str = "preserved"    # would-remove-lock|removed-lock|preserved
    preserve_reason: object = None
```

Add the functions (after `list_review_worktrees`):

```python
def list_orphan_locks(runs_dir, registered_ids):
    """review-<8hex>.lock files under runs_dir whose dispatch_id is NOT a registered
    review worktree. Regex-gated (check 1) + registered-excluded (check 2). Returns
    dicts {basename, dispatch_id}. DB active-run (3) + flock (4) applied by caller."""
    reg = set(registered_ids)
    try:
        names = os.listdir(runs_dir)
    except OSError:
        return []
    out = []
    for name in sorted(names):
        if not RE_LOCK.match(name):
            continue
        did = name[: -len(".lock")]
        if did in reg:
            continue
        out.append({"basename": name, "dispatch_id": did})
    return out


def _lock_held(runs_dir, dispatch_id):
    """True if a live process holds the flock (non-blocking acquire fails), False if
    acquirable (=> not held). Fail-CLOSED to True on any fs/lock error."""
    try:
        with agent_runner._worktree_flock(runs_dir, dispatch_id) as acquired:
            return not acquired
    except OSError:
        return True


def classify_orphan_locks(registered_ids):
    """Orphan-lock candidates with git/DB/fs facts, one frozen DB snapshot for their
    ids. Raises DbUnreachable on psycopg Operational/Interface error."""
    runs = agent_runner._runs_dir()
    cands = list_orphan_locks(runs, registered_ids)
    ids = [c["dispatch_id"] for c in cands]
    try:
        snap = engine.review_dispatch_statuses(ids)
    except (psycopg.OperationalError, psycopg.InterfaceError):
        raise DbUnreachable()
    out = []
    for c in cands:
        db = snap.get(c["dispatch_id"])
        out.append(OrphanLock(
            basename=c["basename"], dispatch_id=c["dispatch_id"],
            held=_lock_held(runs, c["dispatch_id"]),
            has_active_run=bool(db and db["any_running"]),
            has_registered_worktree=False))
    return out
```

Add `from . import engine` is already imported (line 15). Confirm `import re`, `os` present (they are).

- [ ] **Step 4: Run, verify PASS.**
Run (injected): `... pytest tests/test_prune_hardening.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit.**
`git add packages/apex-jobs/src/apex_jobs/prune.py packages/apex-jobs/tests/test_prune_hardening.py && git commit -m "feat(prune): orphan-lock enumeration + classification (read-only)"` (+ Co-Authored-By trailer).

---

## Task 2: additive summary -- orphan_locks, buckets, exists, lock_remove_failed

**Files:** Modify `prune.py` (summary builders + `prune_review_worktrees` signature/report).

**Consumes:** T1 `classify_orphan_locks`, `OrphanLock`.
**Produces:** `prune_review_worktrees(apply=False, include_failed=False, force_succeeded_dirty=False, prune_orphan_locks=False)`; summary gains `items[*].exists`, `orphan_locks`, `buckets`, `lock_remove_failed` (existing keys unchanged).

- [ ] **Step 1: Failing tests** -- append to `test_prune_hardening.py`:

```python
def test_summary_has_additive_buckets_and_keys(prune_env):
    conn, runs, created = prune_env
    # one clean prunable worktree + one stale orphan lock
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
```

- [ ] **Step 2: Run, verify FAIL** (`orphan_locks`/`buckets` KeyError).

- [ ] **Step 3: Implement.** In `prune.py`:

Extend `_item_dict` to add `exists` (additive; the candidate's exists flag must be carried). Since `ReviewWorktree` lacks `exists`, add an `exists: bool = True` field to the dataclass and set it in `classify_review_worktrees` from the candidate `c["exists"]` (additive dataclass field; `_classify_one` unchanged). Then:

```python
def _item_dict(w):
    return {"basename": w.dispatch_id, "dispatch_id": w.dispatch_id,
            "classification": w.classification, "action": w.action,
            "status": w.status,
            "claimed_at": w.claimed_at.isoformat() if w.claimed_at else None,
            "finished_at": w.finished_at.isoformat() if w.finished_at else None,
            "active": w.active, "exists": w.exists}


def _orphan_dict(o):
    return {"basename": o.basename, "dispatch_id": o.dispatch_id, "held": o.held,
            "has_active_run": o.has_active_run,
            "has_registered_worktree": o.has_registered_worktree,
            "action": o.action, "preserve_reason": o.preserve_reason}


def _buckets(items, orphan_locks):
    return {
        "registered": len(items),
        "dirty_succeeded": sum(1 for w in items if w.classification == "dirty"
                               and w.status == "succeeded" and not w.active),
        "orphan_locks": len(orphan_locks),
        "registered_missing": sum(1 for w in items if not w.exists),
    }
```

Set `w.exists` in `classify_review_worktrees` result construction: add `exists=c["exists"]` to the `ReviewWorktree(...)` call. (`_classify_one` and its call site otherwise unchanged.)

Update `_refusal` to carry orphan_locks (default empty), and update the final summary return. Change `prune_review_worktrees` signature to add the two kwargs (default False) and compute + include the additive fields. The dry-run (no-apply) return becomes:

```python
    locks = []
    try:
        items = classify_review_worktrees(include_failed=include_failed)
        registered_ids = [w.dispatch_id for w in items]
        locks = classify_orphan_locks(registered_ids)
    except DbUnreachable:
        return _refusal(None, "db-unreachable", applied=False, orphan_locks=locks)
    except GitUnavailable:
        return _refusal(None, "git-unavailable", applied=False, orphan_locks=locks)
    # ... (apply branches added in Tasks 3 & 4) ...
    return {"items": [_item_dict(w) for w in items], "counts": _counts(items),
            "buckets": _buckets(items, locks),
            "orphan_locks": [_orphan_dict(o) for o in locks],
            "applied": apply, "remove_failed": remove_failed,
            "lock_remove_failed": lock_remove_failed,
            "refused": False, "refused_reason": None}
```

Extend `_refusal(items, reason, applied, remove_failed=0, orphan_locks=None, lock_remove_failed=0)` to include `"orphan_locks": [_orphan_dict(o) for o in (orphan_locks or [])]`, `"buckets": _buckets(items or [], orphan_locks or [])`, and `"lock_remove_failed": lock_remove_failed`. Initialize `lock_remove_failed = 0` near `remove_failed = 0`.

- [ ] **Step 4: Run new + existing prune tests, verify PASS.**
Run (injected): `... pytest tests/test_prune.py tests/test_prune_hardening.py -q`
Expected: all pass (existing `test_prune.py` unchanged + green; the additive `exists`/`buckets`/`orphan_locks` keys do not break its per-key assertions).

- [ ] **Step 5: Commit.** `feat(prune): additive summary buckets + orphan_locks + exists`.

---

## Task 3: --force-succeeded-dirty (guarded force removal)

**Files:** Modify `prune.py` (post-classify label + extracted `_guarded_remove_worktree` + apply branch).

**Consumes:** T2 summary. **Produces:** `--force-succeeded-dirty` behavior; action labels `would-remove-force`/`removed-force`.

- [ ] **Step 1: Failing tests** -- append:

```python
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
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement.** In `prune.py`:

(a) After `items = classify_review_worktrees(...)`, apply the force LABEL (dry-run report) BEFORE the apply loop:

```python
    if force_succeeded_dirty:
        for w in items:
            if (w.classification == "dirty" and w.status == "succeeded"
                    and not w.active and w.exists):
                w.action = "would-remove-force"
```

(b) Extract the existing per-item removal choreography (current lines ~211-265, the `if w.classification != "prunable": continue` loop body) into a helper WITHOUT behavior change for the prunable path:

```python
def _guarded_remove_worktree(w, repo, runs, include_failed, force):
    """PG-lock -> flock fuse -> _WORKTREE_LOCK -> recheck-before-remove -> git worktree
    remove [--force]. `force` (dirty+succeeded) removes with --force and rechecks for
    that shape; else rechecks for still-prunable. Mutates w in place. Returns
    (remove_failed_delta:int, refusal:dict|None)."""
    try:
        with engine.review_worktree_lock(w.dispatch_id) as held:
            if not held:
                w.classification, w.action = "contended", "preserved"; return 0, None
            with agent_runner._worktree_flock(runs, w.dispatch_id) as fuse_ok:
                if not fuse_ok:
                    w.classification, w.action = "contended", "preserved"; return 0, None
                with agent_runner._WORKTREE_LOCK:
                    try:
                        snap = engine.review_dispatch_statuses([w.dispatch_id])
                        cand = _fresh_candidate(repo, runs, w.dispatch_id)
                    except (psycopg.OperationalError, psycopg.InterfaceError):
                        return 0, "db-unreachable"
                    except GitUnavailable:
                        return 0, "git-unavailable"
                    db = snap.get(w.dispatch_id)
                    if cand is None:
                        w.classification, w.action = "unknown", "preserved"; return 0, None
                    cls, _act, status, claimed_at, finished_at, active = _classify_one(
                        cand, db, include_failed)
                    if force:
                        removable = (cls == "dirty" and status == "succeeded" and not active)
                        label = "removed-force"
                    else:
                        removable = (cls == "prunable")
                        label = "removed"
                    if not removable:
                        w.classification, w.action = cls, "preserved"
                        w.status, w.claimed_at, w.finished_at, w.active = (
                            status, claimed_at, finished_at, active)
                        return 0, None
                    args = ["worktree", "remove", w.path]
                    if force:
                        args.insert(2, "--force")
                    r = agent_runner._git(*args, cwd=repo, check=False)
                    if r.returncode == 0:
                        w.action = label; return 0, None
                    w.classification, w.action = "remove-failed", "preserved"
                    return 1, None
    except (engine.LockUnavailable, psycopg.Error, OSError):
        return 0, "db-unreachable"
```

(c) Rewrite the apply loop to call the helper for BOTH prunable (unchanged) and would-remove-force items:

```python
    if apply:
        for w in items:
            if w.classification == "prunable":
                dec, refusal = _guarded_remove_worktree(w, repo, runs, include_failed, force=False)
            elif force_succeeded_dirty and w.action == "would-remove-force":
                dec, refusal = _guarded_remove_worktree(w, repo, runs, include_failed, force=True)
            else:
                continue
            remove_failed += dec
            if refusal:
                return _refusal(items, refusal, applied=True, remove_failed=remove_failed,
                                orphan_locks=locks, lock_remove_failed=lock_remove_failed)
```

NOTE: The `_guarded_remove_worktree(..., force=False)` path is a verbatim behavior-preserving extraction of the current loop body -- existing `test_prune.py` (apply-removes-clean, recheck-skips-now-active, remove-failed-count, dry-run-noop) MUST stay green.

- [ ] **Step 4: Run existing + new, verify PASS.**
Run (injected): `... pytest tests/test_prune.py tests/test_prune_hardening.py -q`
Expected: all pass (existing prunable behavior intact; force-dirty removes only dirty+succeeded+inactive).

- [ ] **Step 5: Commit.** `feat(prune): --force-succeeded-dirty guarded force removal`.

---

## Task 4: --prune-orphan-locks (4-proof gated lock removal)

**Files:** Modify `prune.py` (orphan-lock apply branch).

**Consumes:** T2/T3. **Produces:** `--prune-orphan-locks` behavior; orphan action labels `would-remove-lock`/`removed-lock`, preserve reasons.

- [ ] **Step 1: Failing tests** -- append:

```python
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
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement.** Add the orphan-lock apply branch in `prune_review_worktrees`, AFTER the worktree apply loop and BEFORE the final return. Label in dry-run, remove under apply with a fresh 4-proof recheck:

```python
    runs_real = agent_runner._runs_dir()
    reg_now = None
    for o in locks:
        # dry-run labelling + apply removal, both gated by the 4 proofs (fresh recheck).
        if o.has_registered_worktree:
            o.action, o.preserve_reason = "preserved", "has-registered-worktree"; continue
        if o.has_active_run:
            o.action, o.preserve_reason = "preserved", "active-run"; continue
        if o.held:
            o.action, o.preserve_reason = "preserved", "held"; continue
        if not (apply and prune_orphan_locks):
            o.action = "would-remove-lock"; continue
        # apply: fresh recheck of all 4 proofs, then remove while holding the flock.
        if reg_now is None:
            reg_now = set(w.dispatch_id for w in items)
        if o.dispatch_id in reg_now:
            o.action, o.preserve_reason = "preserved", "has-registered-worktree"; continue
        try:
            snap = engine.review_dispatch_statuses([o.dispatch_id])
        except (psycopg.OperationalError, psycopg.InterfaceError):
            return _refusal(items, "db-unreachable", applied=True, remove_failed=remove_failed,
                            orphan_locks=locks, lock_remove_failed=lock_remove_failed)
        db = snap.get(o.dispatch_id)
        if db and db["any_running"]:
            o.action, o.preserve_reason = "preserved", "active-run"; continue
        lp = os.path.join(runs_real, o.basename)
        try:
            with agent_runner._worktree_flock(runs_real, o.dispatch_id) as ok:
                if not ok:
                    o.action, o.preserve_reason = "preserved", "held"; continue
                try:
                    if os.path.exists(lp):
                        os.remove(lp)
                    o.action = "removed-lock"
                except OSError:
                    o.action, o.preserve_reason = "preserved", "remove-failed"
                    lock_remove_failed += 1
        except OSError:
            o.action, o.preserve_reason = "preserved", "flock-error"
```

(Confirm `import os` present -- yes.)

- [ ] **Step 4: Run existing + new, verify PASS.**
Run (injected): `... pytest tests/test_prune.py tests/test_prune_hardening.py -q`
Expected: all pass.

- [ ] **Step 5: Commit.** `feat(prune): --prune-orphan-locks with 4-proof gate`.

---

## Task 5: CLI flags + rendering

**Files:** Modify `packages/apex-jobs/src/apex_jobs/cli.py`.

- [ ] **Step 1: Failing test** -- append to `test_prune_hardening.py`:

```python
def test_cli_parser_accepts_new_flags():
    from apex_jobs import cli
    a = cli.build_parser().parse_args(
        ["prune-review-worktrees", "--apply", "--force-succeeded-dirty", "--prune-orphan-locks"])
    assert a.force_succeeded_dirty is True and a.prune_orphan_locks is True and a.apply is True
    b = cli.build_parser().parse_args(["prune-review-worktrees"])
    assert b.force_succeeded_dirty is False and b.prune_orphan_locks is False
```

- [ ] **Step 2: Run, verify FAIL** (unrecognized arguments).

- [ ] **Step 3: Implement.** In `cli.py`, add to the `prune-review-worktrees` parser (after `--include-failed`):

```python
    pw.add_argument("--force-succeeded-dirty", action="store_true", dest="force_succeeded_dirty",
                    help="also remove succeeded+inactive+DIRTY review worktrees (requires --apply; "
                         "uses git worktree remove --force; does NOT imply --include-failed)")
    pw.add_argument("--prune-orphan-locks", action="store_true", dest="prune_orphan_locks",
                    help="also remove stale orphan review-*.lock sidecars (requires --apply) after "
                         "proving: no registered worktree, no active DB run, non-blocking flock free")
```

Pass them through in `cmd_prune_review_worktrees`:

```python
    res = prune.prune_review_worktrees(apply=a.apply, include_failed=a.include_failed,
                                       force_succeeded_dirty=a.force_succeeded_dirty,
                                       prune_orphan_locks=a.prune_orphan_locks)
```

Extend the human-readable block to render orphan locks + the buckets line (after the existing items loop, before the counts line):

```python
        for o in res.get("orphan_locks", []):
            print(f"{o['basename']}  {o['action']:<16}  held={o['held']}  "
                  f"active_run={o['has_active_run']}  reason={o['preserve_reason']}")
        b = res.get("buckets", {})
        print(f"buckets: registered={b.get('registered', 0)} "
              f"dirty_succeeded={b.get('dirty_succeeded', 0)} "
              f"orphan_locks={b.get('orphan_locks', 0)} "
              f"registered_missing={b.get('registered_missing', 0)}")
```

Update the exit-code logic to also treat `lock_remove_failed` as exit 2:

```python
    if res["remove_failed"] > 0 or res.get("lock_remove_failed", 0) > 0:
        return 2
```

- [ ] **Step 4: Run, verify PASS.** `... pytest tests/test_prune_hardening.py::test_cli_parser_accepts_new_flags -q`.

- [ ] **Step 5: Commit.** `feat(prune): CLI --force-succeeded-dirty + --prune-orphan-locks + report rendering`.

---

## Task 6: full suite via injection + Codex + finish

- [ ] **Step 1: Full apex-jobs suite via injection (DEV_PG_PASSWORD unset in-child).**
Run: `SSH 'cd REPO_DIR && PATHX && infra/infisical/inject.sh dev -- bash -c "unset DEV_PG_PASSWORD; cd packages/apex-jobs && APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest -q; echo RC=\$?"' 2>&1 | grep -viE "release of infisical|To update|Injecting" | tail -20`
Expected: all pass (existing + new); `RC=0`.

- [ ] **Step 2: ASCII check (added lines) + shellcheck (none -- no shell edited).**
Run: `SSH 'cd REPO_DIR && git --no-pager diff main -- packages/apex-jobs | grep "^+" | grep -v "^+++" | LC_ALL=C grep -nP "[^\x00-\x7F]" && echo NON_ASCII_ADDED || echo ADDED_LINES_ASCII_CLEAN'`

- [ ] **Step 3: Whole-branch Codex review** (Codex offline ~45 min -> run when back).
Run: `SSH 'cd REPO_DIR && PATHX && infra/infisical/apex-jobs.sh review-run --review-head orchestration/prune-worktrees-hardening --base-ref main --json' 2>&1 | grep -viE "release of infisical|To update|Injecting"`
Adjudicate findings value-silently; fix; re-run until clean.

- [ ] **Step 4: Finish** -- push + open PR (body: additive report buckets, two guarded modes with their exact gates, no default-behavior change, test evidence, Codex record). STOP for CI/review; on green squash-merge (no admin-bypass), restore main, doc reconcile + dismiss chip `task_cf2ab656`.

## Self-Review (authoring)

- **Spec coverage:** orphan-lock enumeration (T1) / additive buckets+exists+orphan_locks+lock_remove_failed, existing keys preserved (T2) / --force-succeeded-dirty succeeded+inactive+dirty, requires --apply, never --include-failed (T3) / --prune-orphan-locks 4-proof gate + reasons (T4) / CLI flags+render (T5) / default unchanged (T2/T3 guards + existing test_prune.py green) / value-silent + no real-artifact deletion (Global; tmp-only tests) / Codex last (T6). All mapped.
- **Type consistency:** `OrphanLock` fields, `classify_orphan_locks`, `_guarded_remove_worktree(w, repo, runs, include_failed, force)`, summary keys, and CLI dests (`force_succeeded_dirty`, `prune_orphan_locks`) are consistent across tasks.
- **No placeholders:** all new code + representative tests are complete; the `_guarded_remove_worktree(force=False)` path is an explicit verbatim extraction guarded by existing tests.
