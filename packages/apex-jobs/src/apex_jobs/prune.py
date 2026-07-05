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


class DbUnreachable(Exception):
    """DB connection/transport failure during classification. Carries NO
    underlying-exception text (value-silence: the psycopg string can embed
    host/port/user)."""


@dataclass
class ReviewWorktree:
    path: str
    dispatch_id: str
    classification: str          # prunable|active|dirty|locked|orphan|failed|unknown|remove-failed
    action: str                  # would-remove|removed|preserved|refused
    status: object               # latest run status or None
    claimed_at: object           # datetime or None
    finished_at: object          # datetime or None
    active: bool                 # job has a running run


def _norm(path):
    return os.path.realpath(path.rstrip("/"))


def _porcelain_worktrees(repo):
    """Parse `git worktree list --porcelain` -> list of {path, locked}."""
    out = agent_runner._git("worktree", "list", "--porcelain", cwd=repo,
                            check=False).stdout
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


def prune_review_worktrees(apply=False, include_failed=False):
    """Classify (frozen snapshot); under apply, remove each prunable with a
    per-item recheck-before-remove (the ONLY DB call in the loop) and plain
    `git worktree remove` (no --force). Returns a value-silent summary. On
    DbUnreachable, returns a refusal summary (caller maps to exit 3)."""
    repo = agent_runner._repo()
    try:
        items = classify_review_worktrees(include_failed=include_failed)
    except DbUnreachable:
        return {"items": [], "counts": {}, "applied": False,
                "remove_failed": 0, "refused": True}
    remove_failed = 0
    if apply:
        for w in items:
            if w.classification != "prunable":
                continue
            with agent_runner._WORKTREE_LOCK:
                # recheck-before-remove: re-query THIS dispatch + re-check git flags
                try:
                    snap = engine.review_dispatch_statuses([w.dispatch_id])
                except (psycopg.OperationalError, psycopg.InterfaceError):
                    return {"items": [_item_dict(x) for x in items],
                            "counts": _counts(items), "applied": False,
                            "remove_failed": remove_failed, "refused": True}
                db = snap.get(w.dispatch_id)
                flags = _worktree_flags(w.path, w.classification == "locked")
                if db and db["any_running"]:
                    w.classification, w.action, w.active = "active", "preserved", True
                    continue
                if (not flags["exists"]) or (not flags["git_ok"]):
                    w.classification, w.action = "unknown", "preserved"
                    continue
                if flags["dirty"]:
                    w.classification, w.action = "dirty", "preserved"
                    continue
                if flags["locked"]:
                    w.classification, w.action = "locked", "preserved"
                    continue
                r = agent_runner._git("worktree", "remove", w.path, cwd=repo, check=False)
                if r.returncode == 0:
                    w.action = "removed"
                else:
                    w.classification, w.action = "remove-failed", "preserved"
                    remove_failed += 1
    return {"items": [_item_dict(w) for w in items], "counts": _counts(items),
            "applied": apply, "remove_failed": remove_failed, "refused": False}
