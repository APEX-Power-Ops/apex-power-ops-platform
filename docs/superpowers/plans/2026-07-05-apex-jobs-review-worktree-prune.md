# apex-jobs prune-review-worktrees Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, explicit `apex-jobs prune-review-worktrees` verb that removes only provably-safe leaked codex-review worktrees under `~/.apex-jobs/runs/review-*`.

**Architecture:** Enumerate candidate worktrees from `git worktree list --porcelain` (never the DB); key every safety decision on the worktree basename = `dispatch_id` (unique in `jobs.job`); classify via one frozen DB snapshot (`engine.review_dispatch_statuses`) plus git dirty/locked/exists facts; under `--apply` remove only `prunable` (succeeded + clean + not-active + not-locked) with a per-item recheck-before-remove and plain `git worktree remove` (no `--force`). Fail closed on DB-unreachable; value-silent throughout.

**Tech Stack:** Python 3.12, `psycopg` (v3, dict-row) on host Postgres `orchestration_test` (tests) / `orchestration_dev` (runtime), `argparse` CLI, `git worktree` plumbing, `uv` for the venv, `pytest`.

**Spec:** `docs/superpowers/specs/2026-07-05-apex-jobs-review-worktree-prune-design.md` (rev 2, committed `ad45a0e3`). Read it first.

## Global Constraints

- Host-canonical single-writer: author locally on Windows -> `scp` per-file to the `apex-review-prune` worktree -> run/commit host-side over `ssh olares-mesh`. PULL-first before editing an existing host file.
- ASCII-only added lines in code files: `git diff --cached -- '*.py' '*.sh' '*.yml' '*.yaml' '*.json' | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]'` must be empty.
- Value-silent: output/logs carry names, paths, classification labels, actions, integer counts, ISO timestamps ONLY. Never a DSN/password/env value, an environment dict, or a psycopg exception string.
- No `--force`; plain `git worktree remove` only. No orphan pruning. No git refs created/retained. No `jobs.run` mutation.
- Fail-closed on DB-unreachable (catch ONLY `psycopg.OperationalError`/`psycopg.InterfaceError`); every other exception propagates.
- Exit codes: `0` clean (dry-run or apply with no removal failures); `2` any `remove-failed` under `--apply`; `3` db-unreachable refusal.
- No production mutation: tests target `orchestration_test` ONLY (conftest refuses `orchestration_dev`/`APEX_JOBS_DSN` with `pytest.exit rc=4`).
- TDD, bite-sized commits; commit trailer `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Merge governance: squash self-merge after green host-side suite + whole-branch Codex cross-engine review; no admin-bypass, no local-merge.

## Working directory & commands (host)

All commands run over `ssh olares-mesh` inside the worktree. **Canonical run
recipe** (verified): `uv` lives at `~/.local/bin` (not on the non-interactive
PATH); the DB env comes from the **canonical** repo's `infra/.env` (the
worktree's `infra/.env` is gitignored / not checked out); test deps come from
uv's ephemeral env via `--with` (there is no synced dev venv). Every
`uv run ... pytest` in this plan means exactly this form:
```
export PATH=$HOME/.local/bin:$PATH
cd /home/olares/code/apex/apex-review-prune/packages/apex-jobs
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest tests/test_prune.py -v
```
The full suite: same, ending `pytest -q`. Baseline (pre-change) is green.

## File Structure

- **Modify** `packages/apex-jobs/src/apex_jobs/engine.py` — add `review_dispatch_statuses(dispatch_ids)` (the only new DB access; all DB stays in engine).
- **Create** `packages/apex-jobs/src/apex_jobs/prune.py` — enumeration + classification + apply/removal + `ReviewWorktree` + `DbUnreachable`. Reuses `agent_runner._git/_repo/_runs_dir/_WORKTREE_LOCK` and imports `engine`.
- **Modify** `packages/apex-jobs/src/apex_jobs/cli.py` — `cmd_prune_review_worktrees` + subparser + verb-list docstring.
- **Create** `packages/apex-jobs/tests/test_prune.py` — the full value-silent test matrix (real `orchestration_test` + throwaway worktrees).

**CI note (verified):** no GitHub workflow runs the apex-jobs pytest suite (it needs a live Postgres; `conftest.py` skips the whole suite without DB env). The verification gate for this lane is therefore the **host-side** suite, not GitHub CI. Do NOT invent a CI step. (This corrects the spec's CI-wiring aside; flagged to the operator.)

---

### Task 1: `engine.review_dispatch_statuses(dispatch_ids)`

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/engine.py` (add one function near `list_promotions`, ~line 632)
- Test: `packages/apex-jobs/tests/test_prune.py` (new file; Task 1 adds the engine tests + shared seed helpers)

**Interfaces:**
- Consumes: `engine._conn()` (dict-row psycopg connection); schema `jobs.job(id, dispatch_id UNIQUE, kind, payload jsonb)` + `jobs.run(job_id, attempt, status, claimed_at, finished_at, worktree_path)`.
- Produces: `review_dispatch_statuses(dispatch_ids: list[str]) -> dict[str, dict]`. Each present key maps to `{"is_review": bool, "any_running": bool, "status": str|None, "claimed_at": datetime|None, "finished_at": datetime|None}`. dispatch_ids with no `jobs.job` row are ABSENT from the result. Raises `psycopg.OperationalError`/`InterfaceError` on connection failure (uncaught here).

- [ ] **Step 1: Write the failing tests + shared helpers**

Create `packages/apex-jobs/tests/test_prune.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `set -a; . /home/olares/code/apex/apex-review-prune/infra/.env; set +a; APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v`
Expected: FAIL with `AttributeError: module 'apex_jobs.engine' has no attribute 'review_dispatch_statuses'`.

- [ ] **Step 3: Implement `review_dispatch_statuses`**

Add to `engine.py` (after `list_promotions`):

```python
def review_dispatch_statuses(dispatch_ids):
    """Per-dispatch DB status for prune classification, keyed on dispatch_id
    (UNIQUE in jobs.job). Returns {dispatch_id: {is_review, any_running, status,
    claimed_at, finished_at}} for every input id that HAS a jobs.job row; ids
    with no job row are absent (-> orphan). is_review = codex-review job
    (kind='agent' AND payload.review_head set). any_running = any run for the job
    is status='running' (regardless of lease). status/claimed_at/finished_at come
    from the LATEST run by (claimed_at DESC, attempt DESC). One query. Raises
    psycopg.OperationalError/InterfaceError on connection failure."""
    if not dispatch_ids:
        return {}
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select j.dispatch_id, "
            "       (j.kind = 'agent' and (j.payload ->> 'review_head') is not null) as is_review, "
            "       exists (select 1 from jobs.run r "
            "               where r.job_id = j.id and r.status = 'running') as any_running, "
            "       lr.status, lr.claimed_at, lr.finished_at "
            "from jobs.job j "
            "left join lateral (select status, claimed_at, finished_at from jobs.run "
            "                   where job_id = j.id "
            "                   order by claimed_at desc, attempt desc limit 1) lr on true "
            "where j.dispatch_id = any(%s)",
            (list(dispatch_ids),),
        )
        return {r["dispatch_id"]: {
            "is_review": r["is_review"],
            "any_running": r["any_running"],
            "status": r["status"],
            "claimed_at": r["claimed_at"],
            "finished_at": r["finished_at"],
        } for r in cur.fetchall()}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v` (with DB env loaded)
Expected: 3 passed.

- [ ] **Step 5: ASCII-check and commit (host-side)**

```bash
cd /home/olares/code/apex/apex-review-prune
git add packages/apex-jobs/src/apex_jobs/engine.py packages/apex-jobs/tests/test_prune.py
git diff --cached -- '*.py' | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]' && echo NONASCII || echo ASCII-CLEAN
git -c user.email=apex-jobs@local -c user.name=apex-jobs commit -m "feat(apex-jobs): engine.review_dispatch_statuses for prune classification

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `prune.py` enumeration + classification (dry-run)

**Files:**
- Create: `packages/apex-jobs/src/apex_jobs/prune.py`
- Test: `packages/apex-jobs/tests/test_prune.py` (add classification tests + the `prune_env` fixture)

**Interfaces:**
- Consumes: `engine.review_dispatch_statuses` (Task 1); `agent_runner._git(*args, cwd, check=True)`, `agent_runner._repo()`, `agent_runner._runs_dir()`.
- Produces:
  - `class DbUnreachable(Exception)` (carries no exception text).
  - `@dataclass ReviewWorktree: path, dispatch_id, classification, action, status, claimed_at, finished_at, active`.
  - `RE_REVIEW = re.compile(r"^review-[0-9a-f]{8}$")`.
  - `list_review_worktrees(repo, runs_dir) -> list[dict]` — candidates `{path, dispatch_id, locked, exists, git_ok, dirty}` (git/fs facts only; realpath-canonical parent-dir match; basename matches `RE_REVIEW`).
  - `classify_review_worktrees(include_failed=False) -> list[ReviewWorktree]` — one frozen `review_dispatch_statuses` snapshot; assigns classification/action/timestamps; raises `DbUnreachable` on `OperationalError`/`InterfaceError`.

- [ ] **Step 1: Write the failing classification tests + fixture**

Append to `tests/test_prune.py`:

```python
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
    assert _classify_map()[d] == "prunable"


def test_dirty_tracked_modification_preserved(prune_env):
    conn, runs, created = prune_env
    d = "review-5555eeee"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    # modify a tracked file so `git status --porcelain` is non-empty
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
    # .venv is gitignored at packages/apex-jobs/.gitignore; a top-level ignored
    # path here: create a file matching a repo .gitignore entry.
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
    # force the per-worktree flags probe to report a git failure
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'apex_jobs.prune'` (or `AttributeError` on `prune._worktree_flags`).

- [ ] **Step 3: Implement `prune.py` (enumeration + classification only)**

Create `packages/apex-jobs/src/apex_jobs/prune.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v`
Expected: all Task 1 + Task 2 tests pass. If `test_ignored_file_counts_dirty` fails because `node_modules` is not ignored at that path, switch the ignored path to one listed in the repo root `.gitignore` (confirm with `git -C <wt> check-ignore -v node_modules` returning a match; otherwise use `.venv`).

- [ ] **Step 5: ASCII-check and commit (host-side)**

```bash
cd /home/olares/code/apex/apex-review-prune
git add packages/apex-jobs/src/apex_jobs/prune.py packages/apex-jobs/tests/test_prune.py
git diff --cached -- '*.py' | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]' && echo NONASCII || echo ASCII-CLEAN
git -c user.email=apex-jobs@local -c user.name=apex-jobs commit -m "feat(apex-jobs): prune.py enumeration + dispatch-keyed classification

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `prune.py` apply/removal + recheck-before-remove + exit contract

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/prune.py` (add `prune_review_worktrees`)
- Test: `packages/apex-jobs/tests/test_prune.py` (add apply tests)

**Interfaces:**
- Consumes: `classify_review_worktrees` (Task 2), `agent_runner._WORKTREE_LOCK`, `agent_runner._git`, `engine.review_dispatch_statuses` (for the per-item recheck).
- Produces: `prune_review_worktrees(apply=False, include_failed=False) -> dict` with keys `items` (list of `ReviewWorktree` as dicts), `counts` (dict of classification -> int), `applied` (bool), `remove_failed` (int), `refused` (bool).

- [ ] **Step 1: Write the failing apply tests**

Append to `tests/test_prune.py`:

```python
def test_dry_run_is_noop(prune_env):
    conn, runs, created = prune_env
    d = "review-abcd0001"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    res = prune.prune_review_worktrees(apply=False)
    assert res["applied"] is False
    assert os.path.isdir(p)                          # nothing removed
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "would-remove"


def test_apply_removes_succeeded_clean(prune_env):
    conn, runs, created = prune_env
    d = "review-abcd0002"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    res = prune.prune_review_worktrees(apply=True)
    assert res["applied"] is True and res["remove_failed"] == 0
    assert not os.path.isdir(p)                      # removed
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "removed"


def test_apply_preserves_unrelated_lane_worktrees(prune_env):
    """Only review-* under the runs dir are candidates; the canonical repo and
    lane worktrees are never enumerated."""
    conn, runs, created = prune_env
    d = "review-abcd0003"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    before = subprocess.run(["git", "-C", REPO, "worktree", "list"],
                            capture_output=True, text=True).stdout
    assert "/code/apex/apex-power-ops-platform" in before or REPO in before
    prune.prune_review_worktrees(apply=True)
    after = subprocess.run(["git", "-C", REPO, "worktree", "list"],
                           capture_output=True, text=True).stdout
    # the canonical repo line survives; only the runs/review-* line went away
    assert d not in after


def test_recheck_before_remove_skips_now_active(prune_env, monkeypatch):
    """Classified prunable, but the per-item recheck reports running -> skipped."""
    conn, runs, created = prune_env
    d = "review-abcd0004"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    real = engine.review_dispatch_statuses
    calls = {"n": 0}
    def flip(ids):
        calls["n"] += 1
        out = real(ids)
        # call 1 = the frozen-snapshot classify (sees prunable); call 2+ = the
        # per-item recheck (flip to running so remove is skipped).
        if calls["n"] >= 2 and d in out:
            out[d] = {**out[d], "any_running": True}
        return out
    monkeypatch.setattr(engine, "review_dispatch_statuses", flip)
    res = prune.prune_review_worktrees(apply=True)
    assert os.path.isdir(p)                          # NOT removed
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["action"] == "preserved" and item["classification"] == "active"


def test_remove_failed_sets_count(prune_env, monkeypatch):
    """A prunable candidate whose `git worktree remove` refuses -> remove-failed."""
    conn, runs, created = prune_env
    d = "review-abcd0005"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    real_git = agent_runner._git
    def refuse(*args, cwd, check=True):
        if args[:2] == ("worktree", "remove"):
            class R: returncode = 128; stdout = ""; stderr = "fatal: ..."
            if check:
                raise subprocess.CalledProcessError(128, "git")
            return R()
        return real_git(*args, cwd=cwd, check=check)
    monkeypatch.setattr(agent_runner, "_git", refuse)
    res = prune.prune_review_worktrees(apply=True)
    assert res["remove_failed"] == 1
    item = [i for i in res["items"] if i["dispatch_id"] == d][0]
    assert item["classification"] == "remove-failed" and item["action"] == "preserved"
    assert os.path.isdir(p)                          # still there


def test_prune_refusal_summary_on_db_unreachable(prune_env, monkeypatch):
    conn, runs, created = prune_env
    d = "review-abcd0006"
    _enqueue_review(d)
    _add_wt(runs, created, d)
    def raise_op(_ids):
        raise psycopg.OperationalError("nope")
    monkeypatch.setattr(engine, "review_dispatch_statuses", raise_op)
    res = prune.prune_review_worktrees(apply=True)
    assert res["refused"] is True and res["applied"] is False
    assert all(i["action"] == "refused" for i in res["items"]) or res["items"] == []
```

- [ ] **Step 2: Run to verify failure**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -k apply -v` (plus `recheck`, `remove_failed`, `refusal`, `dry_run`)
Expected: FAIL with `AttributeError: module 'apex_jobs.prune' has no attribute 'prune_review_worktrees'`.

- [ ] **Step 3: Implement `prune_review_worktrees`**

Append to `prune.py`:

```python
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
                    return {"items": [_item_dict(x) for x in items], "counts": _counts(items),
                            "applied": False, "remove_failed": remove_failed, "refused": True}
                db = snap.get(w.dispatch_id)
                flags = _worktree_flags(w.path, w.classification == "locked")
                # re-derive: any change from prunable -> preserve with the new reason
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
```

- [ ] **Step 4: Run to verify pass**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v`
Expected: all Task 1-3 tests pass.

- [ ] **Step 5: ASCII-check and commit (host-side)**

```bash
cd /home/olares/code/apex/apex-review-prune
git add packages/apex-jobs/src/apex_jobs/prune.py packages/apex-jobs/tests/test_prune.py
git diff --cached -- '*.py' | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]' && echo NONASCII || echo ASCII-CLEAN
git -c user.email=apex-jobs@local -c user.name=apex-jobs commit -m "feat(apex-jobs): prune apply path + recheck-before-remove + remove-failed

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: CLI verb + exit codes + `--json` + `--include-failed` help + docstring

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/cli.py` (add `cmd_prune_review_worktrees`, subparser, docstring verb-list)
- Test: `packages/apex-jobs/tests/test_prune.py` (add CLI tests)

**Interfaces:**
- Consumes: `prune.prune_review_worktrees(apply, include_failed) -> dict` (Task 3).
- Produces: CLI verb `apex-jobs prune-review-worktrees [--apply] [--include-failed] [--json]`; `cli.main([...]) -> int` (0 clean, 2 any remove-failed, 3 db-unreachable refusal).

- [ ] **Step 1: Write the failing CLI tests**

Append to `tests/test_prune.py`:

```python
from apex_jobs import cli


def test_cli_dryrun_exit0_and_reports(prune_env, capsys):
    conn, runs, created = prune_env
    d = "review-c11d0001"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    assert cli.main(["prune-review-worktrees"]) == 0
    out = capsys.readouterr().out
    assert d in out and "prunable" in out


def test_cli_json_shape(prune_env, capsys):
    conn, runs, created = prune_env
    d = "review-c11d0002"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    assert cli.main(["prune-review-worktrees", "--json"]) == 0
    import json
    payload = json.loads(capsys.readouterr().out)
    item = [i for i in payload["items"] if i["dispatch_id"] == d][0]
    assert set(item) >= {"basename", "classification", "action", "status",
                         "claimed_at", "finished_at", "active"}


def test_cli_apply_exit0(prune_env, capsys):
    conn, runs, created = prune_env
    d = "review-c11d0003"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    p = _add_wt(runs, created, d)
    assert cli.main(["prune-review-worktrees", "--apply"]) == 0
    assert not os.path.isdir(p)


def test_cli_remove_failed_exit2(prune_env, monkeypatch, capsys):
    conn, runs, created = prune_env
    d = "review-c11d0004"
    jid = _enqueue_review(d)
    _seed_run(conn, jid, status="succeeded", attempt=1)
    _add_wt(runs, created, d)
    real_git = agent_runner._git
    def refuse(*args, cwd, check=True):
        if args[:2] == ("worktree", "remove"):
            class R: returncode = 128; stdout = ""; stderr = ""
            return R()
        return real_git(*args, cwd=cwd, check=check)
    monkeypatch.setattr(agent_runner, "_git", refuse)
    assert cli.main(["prune-review-worktrees", "--apply"]) == 2


def test_cli_db_unreachable_exit3_valuesilent(prune_env, monkeypatch, capsys):
    conn, runs, created = prune_env
    d = "review-c11d0005"
    _enqueue_review(d)
    _add_wt(runs, created, d)
    def raise_op(_ids):
        raise psycopg.OperationalError("password authentication failed for user secret")
    monkeypatch.setattr(engine, "review_dispatch_statuses", raise_op)
    assert cli.main(["prune-review-worktrees", "--apply"]) == 3
    out = capsys.readouterr().out
    assert "db-unreachable" in out
    assert "password" not in out and "secret" not in out       # value-silent


def test_cli_include_failed_help_warns_irreversible(capsys):
    with pytest.raises(SystemExit):
        cli.main(["prune-review-worktrees", "--help"])
    out = capsys.readouterr().out
    assert "gc-unrecoverable" in out or "gc unrecoverable" in out
```

- [ ] **Step 2: Run to verify failure**

Run: `APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -k cli -v`
Expected: FAIL with argparse `invalid choice: 'prune-review-worktrees'`.

- [ ] **Step 3: Implement the CLI verb**

Add `cmd_prune_review_worktrees` to `cli.py` (near `cmd_review`):

```python
def cmd_prune_review_worktrees(a):
    """Safely prune leaked codex-review worktrees under the runs dir. Dry-run by
    default; --apply removes succeeded+clean+not-active+not-locked review
    worktrees. Value-silent. Exit 0 clean, 2 if any remove-failed, 3 on
    db-unreachable refusal."""
    from . import prune
    res = prune.prune_review_worktrees(apply=a.apply, include_failed=a.include_failed)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        if res["refused"]:
            print("db-unreachable: refusing to prune (cannot verify active runs)")
        for i in res["items"]:
            print(f"{i['basename']}  {i['classification']:<12}  {i['action']:<12}  "
                  f"status={i['status']}  active={i['active']}  "
                  f"claimed={i['claimed_at']}  finished={i['finished_at']}")
        c = res["counts"]
        prunable = c.get("prunable", 0)
        preserved = sum(v for k, v in c.items() if k != "prunable")
        verb = "removed" if res["applied"] else "would-remove"
        print(f"{len(res['items'])} candidates: {prunable} {verb}, {preserved} preserved  "
              f"[{', '.join(f'{k}={v}' for k, v in sorted(c.items()))}]")
    if res["refused"]:
        return 3
    if res["remove_failed"] > 0:
        return 2
    return 0
```

Register the subparser in `build_parser()` (near the `review` subparser):

```python
    pw = sub.add_parser("prune-review-worktrees",
                        help="safely remove leaked codex-review worktrees under the runs dir")
    pw.add_argument("--apply", action="store_true",
                    help="actually remove prunable worktrees (default: dry-run)")
    pw.add_argument("--include-failed", action="store_true", dest="include_failed",
                    help="also prune FAILED review worktrees. WARNING: a failed review "
                         "tree is detached (no branch ref); removal may be gc-unrecoverable")
    pw.add_argument("--json", action="store_true")
    pw.set_defaults(fn=cmd_prune_review_worktrees)
```

Add `prune-review-worktrees` to the verb list in the module docstring (line 3-4):

```python
Verbs: enqueue, enqueue-review, review-run, queue, claim, start, report, request-gate, approve, reject,
gates, status, ledger, reap, promotions, review, prune-review-worktrees, unblock. Returns an int exit
code (3 = gated/refused).
```

- [ ] **Step 4: Run to verify pass, then the FULL suite**

```
APEX_JOBS_DB=orchestration_test uv run pytest tests/test_prune.py -v
APEX_JOBS_DB=orchestration_test uv run pytest -q          # full apex-jobs suite must stay green
```
Expected: all prune tests pass; full suite green (0 failures; pre-existing count + the new tests).

- [ ] **Step 5: ASCII-check and commit (host-side)**

```bash
cd /home/olares/code/apex/apex-review-prune
git add packages/apex-jobs/src/apex_jobs/cli.py packages/apex-jobs/tests/test_prune.py
git diff --cached -- '*.py' | grep '^+' | LC_ALL=C grep -P '[^\x00-\x7F]' && echo NONASCII || echo ASCII-CLEAN
git -c user.email=apex-jobs@local -c user.name=apex-jobs commit -m "feat(apex-jobs): prune-review-worktrees CLI verb (exit 0/2/3, --json, --include-failed)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## After all tasks

1. **Whole-branch Codex cross-engine review** (IRP): `apex-jobs review-run --review-head orchestration/prune-review-worktrees --base-ref main --json` (or the direct `codex exec review --dangerously-bypass-approvals-and-sandbox --base main` fallback). Fold findings.
2. **Real-world dry-run verification** (value-silent, no `--apply`): run `apex-jobs prune-review-worktrees` against the live host and confirm it classifies the 6 real leaked worktrees as `prunable` and touches nothing.
3. **finishing-a-development-branch**: full suite green -> push -> PR -> squash self-merge after green + Codex.
4. Write the deliverable-5 auto-clean recommendation into the PR/handoff.

## Self-Review (done)

- **Spec coverage:** enumeration+realpath (T2), dispatch-keyed classification incl active/unknown/orphan/dirty/locked/failed/prunable + precedence (T2), `--ignored` dirty + git-nonzero->unknown (T2), `review_dispatch_statuses` + any_running + latest-by-claimed_at (T1), fail-closed narrow-catch value-silent (T2/T3/T4), frozen snapshot + recheck-before-remove + no-force (T3), exit 0/2/3 (T4), `--json` + report fields + `--include-failed` help (T4), all 17 spec tests mapped. CI: corrected to host-side (flagged).
- **Placeholder scan:** none; every code step carries full code.
- **Type consistency:** `review_dispatch_statuses` keys/fields, `ReviewWorktree` fields, `_worktree_flags` keys (`exists/git_ok/dirty/locked`), and the summary dict keys (`items/counts/applied/remove_failed/refused`) are consistent across T1-T4.
