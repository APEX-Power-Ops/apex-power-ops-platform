"""apex-jobs prune-review-worktrees -- safe cleanup of leaked codex-review
worktrees under the runs dir. Enumeration is from git/disk (never the DB); every
safety decision is keyed on the worktree basename = dispatch_id (UNIQUE in
jobs.job). Value-silent: emits names/paths/labels/counts/ISO-timestamps only.

This module implements enumeration + classification (dry-run) and the --apply
removal path with a per-item recheck-before-remove. No --force; fail-closed on
DB-unreachable."""
import os
import re
from dataclasses import dataclass

import psycopg

from . import engine
from . import agent_runner

RE_REVIEW = re.compile(r"^review-[0-9a-f]{8}$")
RE_LOCK = re.compile(r"^review-[0-9a-f]{8}\.lock$")


class DbUnreachable(Exception):
    """DB connection/transport failure during classification. Carries NO
    underlying-exception text (value-silence: the psycopg string can embed
    host/port/user)."""


class GitUnavailable(Exception):
    """git worktree enumeration itself failed (non-zero exit) -- we cannot see the
    real worktree set, so an empty listing must NOT be read as authoritative.
    Value-silent (carries no git stderr)."""


@dataclass
class ReviewWorktree:
    path: str
    dispatch_id: str
    classification: str          # prunable|active|dirty|locked|orphan|failed|unknown|remove-failed|contended
    action: str                  # would-remove|removed|preserved|refused
    status: object               # latest run status or None
    claimed_at: object           # datetime or None
    finished_at: object          # datetime or None
    active: bool                 # job has a running run


@dataclass
class OrphanLock:
    basename: str
    dispatch_id: str
    held: bool                   # a live process holds the flock (check 4 failed)
    has_active_run: bool         # DB says a review run is running (check 3 failed)
    has_registered_worktree: bool
    action: str = "preserved"    # would-remove-lock|removed-lock|preserved
    preserve_reason: object = None


def _norm(path):
    return os.path.realpath(path.rstrip("/"))


def _porcelain_worktrees(repo):
    """Parse `git worktree list --porcelain` -> list of {path, locked}. Raises
    GitUnavailable on a non-zero git exit -- an empty stdout from a FAILED git
    command (bad/unset APEX_JOBS_REPO, non-git path) must not read as 'no
    worktrees', which would make --apply a silent exit-0 no-op."""
    r = agent_runner._git("worktree", "list", "--porcelain", cwd=repo, check=False)
    if r.returncode != 0:
        raise GitUnavailable()
    out = r.stdout
    entries, cur = [], None
    for line in out.splitlines():
        if line.startswith("worktree "):
            cur = {"path": line[len("worktree "):], "locked": False}
            entries.append(cur)
        elif line.strip() == "locked" or line.startswith("locked "):
            if cur is not None:
                cur["locked"] = True
    return entries


def _worktree_flags(path, locked):
    """git/fs facts for one worktree: {exists, git_ok, dirty, locked}. dirty uses
    --ignored so ignored files (silently deleted by `worktree remove`) count."""
    exists = os.path.isdir(path)
    if not exists:
        return {"exists": False, "git_ok": False, "dirty": False, "locked": locked}
    r = agent_runner._git("status", "--porcelain", "--ignored", cwd=path, check=False)
    git_ok = r.returncode == 0
    dirty = git_ok and bool(r.stdout.strip())
    return {"exists": True, "git_ok": git_ok, "dirty": dirty, "locked": locked}


def list_review_worktrees(repo, runs_dir):
    """Candidate review worktrees: parent-dir realpath == runs_dir realpath AND
    basename matches ^review-[0-9a-f]{8}$. Returns dicts with git/fs facts only."""
    runs_real = _norm(runs_dir)
    out = []
    for e in _porcelain_worktrees(repo):
        path = e["path"]
        base = os.path.basename(path.rstrip("/"))
        if not RE_REVIEW.match(base):
            continue
        if _norm(os.path.dirname(path.rstrip("/"))) != runs_real:
            continue
        flags = _worktree_flags(path, e["locked"])
        out.append({"path": path, "dispatch_id": base, **flags})
    return out


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


def _fresh_candidate(repo, runs_dir, dispatch_id):
    """Re-enumerate ONE review worktree with fresh git/fs facts (for the per-item
    recheck-before-remove). Returns the candidate dict, or None if it is no longer
    a candidate (registration/dir gone, basename or parent-dir no longer matches)."""
    runs_real = _norm(runs_dir)
    for e in _porcelain_worktrees(repo):
        path = e["path"]
        base = os.path.basename(path.rstrip("/"))
        if base != dispatch_id:
            continue
        if not RE_REVIEW.match(base):
            return None
        if _norm(os.path.dirname(path.rstrip("/"))) != runs_real:
            return None
        return {"path": path, "dispatch_id": base, **_worktree_flags(path, e["locked"])}
    return None


def _classify_one(c, db, include_failed):
    """c = candidate dict from list_review_worktrees; db = its status dict or None.
    Returns (classification, action, status, claimed_at, finished_at, active)."""
    status = db["status"] if db else None
    claimed_at = db["claimed_at"] if db else None
    finished_at = db["finished_at"] if db else None
    active = bool(db and db["any_running"])
    # precedence: active > unknown > orphan > dirty > locked > failed > prunable
    if db and db["is_review"] and db["any_running"]:
        cls = "active"
    elif (not c["exists"]) or (not c["git_ok"]) or (db and not db["is_review"]) \
            or (db and db["is_review"] and db["status"] is None):
        cls = "unknown"
    elif db is None:
        cls = "orphan"
    elif c["dirty"]:
        cls = "dirty"
    elif c["locked"]:
        cls = "locked"
    elif db["status"] == "succeeded":
        cls = "prunable"
    elif db["status"] == "failed":
        cls = "prunable" if include_failed else "failed"
    else:
        cls = "unknown"
    action = "would-remove" if cls == "prunable" else "preserved"
    return cls, action, status, claimed_at, finished_at, active


def classify_review_worktrees(include_failed=False):
    """One frozen DB snapshot -> classified candidates. Raises DbUnreachable ONLY
    on psycopg.OperationalError/InterfaceError; any other exception propagates."""
    repo, runs = agent_runner._repo(), agent_runner._runs_dir()
    cands = list_review_worktrees(repo, runs)
    ids = [c["dispatch_id"] for c in cands]
    try:
        snap = engine.review_dispatch_statuses(ids)
    except (psycopg.OperationalError, psycopg.InterfaceError):
        raise DbUnreachable()
    result = []
    for c in cands:
        cls, action, status, claimed_at, finished_at, active = _classify_one(
            c, snap.get(c["dispatch_id"]), include_failed)
        result.append(ReviewWorktree(
            path=c["path"], dispatch_id=c["dispatch_id"], classification=cls,
            action=action, status=status, claimed_at=claimed_at,
            finished_at=finished_at, active=active))
    return result


def _counts(items):
    c = {}
    for i in items:
        c[i.classification] = c.get(i.classification, 0) + 1
    return c


def _item_dict(w):
    return {"basename": w.dispatch_id, "dispatch_id": w.dispatch_id,
            "classification": w.classification, "action": w.action,
            "status": w.status,
            "claimed_at": w.claimed_at.isoformat() if w.claimed_at else None,
            "finished_at": w.finished_at.isoformat() if w.finished_at else None,
            "active": w.active}


def _refusal(items, reason, applied, remove_failed=0):
    """Value-silent refusal summary. `applied` is True when apply mode already
    mutated worktrees before the refusal (a PARTIAL apply -- not a dry-run). Any
    still-'would-remove' candidate (prunable but NOT reached before the abort) is
    relabeled action='refused', so an unprocessed worktree is never reported as
    removed."""
    src = items or []
    for w in src:
        if w.action == "would-remove":
            w.action = "refused"
    return {"items": [_item_dict(x) for x in src], "counts": _counts(src),
            "applied": applied, "remove_failed": remove_failed,
            "refused": True, "refused_reason": reason}


def prune_review_worktrees(apply=False, include_failed=False):
    """Classify (frozen snapshot); under apply, remove each prunable with a
    per-item recheck-before-remove (the ONLY DB call in the loop) and plain
    `git worktree remove` (no --force). Returns a value-silent summary. On
    DbUnreachable, returns a refusal summary (caller maps to exit 3)."""
    repo, runs = agent_runner._repo(), agent_runner._runs_dir()
    try:
        items = classify_review_worktrees(include_failed=include_failed)
    except DbUnreachable:
        return _refusal(None, "db-unreachable", applied=False)
    except GitUnavailable:
        return _refusal(None, "git-unavailable", applied=False)
    remove_failed = 0
    if apply:
        for w in items:
            if w.classification != "prunable":
                continue
            # Coordinator + fuse guard the destructive remove: a live-held dispatch (PG
            # lock held by a runner, or its flock still held by a living process) is
            # classified 'contended'/'preserved' and never removed. A LockUnavailable or
            # transport error is fail-closed to a partial-apply refusal (never fail-open).
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
                            # recheck-before-remove: re-query THIS dispatch and re-enumerate its
                            # git/fs facts, then FULLY re-classify -- remove only if it is STILL
                            # prunable (still a review, allowed terminal status, not-active,
                            # clean, not-locked, exists). This is the only DB call in the loop.
                            # A refusal HERE is a PARTIAL apply (earlier items already removed)
                            # -> applied=True so the summary never reads as a dry-run.
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
            except (engine.LockUnavailable, psycopg.Error, OSError):
                # Fail-CLOSED on ANY lock/DB/fs error during a destructive apply (spec 4.6):
                # a non-transport psycopg.Error (e.g. InsufficientPrivilege) or an OSError
                # (e.g. git binary missing) becomes a db-unreachable refusal, never a raw
                # traceback and never a fail-open remove.
                return _refusal(items, "db-unreachable", applied=True, remove_failed=remove_failed)
    return {"items": [_item_dict(w) for w in items], "counts": _counts(items),
            "applied": apply, "remove_failed": remove_failed, "refused": False,
            "refused_reason": None}
