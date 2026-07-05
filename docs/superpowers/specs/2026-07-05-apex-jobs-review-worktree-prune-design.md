# apex-jobs review-worktree prune — design

**Status:** ratified design (operator go, four leans + age-visibility requirement, 2026-07-05)
**Lane:** `orchestration/prune-review-worktrees` (host worktree `/home/olares/code/apex/apex-review-prune` off main `3168f922`)
**Package:** `packages/apex-jobs` (host-canonical — lives on Olares)

## Problem (root cause, grounded)

`agent_runner.run_review_job()` creates a detached git worktree at
`~/.apex-jobs/runs/<dispatch_id>` (dispatch_id = `review-<hex8>`), runs
`codex exec review`, records the findings + `worktree_path` to `jobs.run`, and —
unlike the agent/promotion path (`run_agent_job` → `open_promotion`) — **never
removes the worktree and opens no gate**. Nothing reaps it afterward, so review
worktrees accumulate.

Observed on the host 2026-07-05: **6 worktrees on disk** under
`~/.apex-jobs/runs/review-*`, every one `status='succeeded'` with an expired
lease. The `jobs.run` table holds ~40+ historical review rows but only 6 exist
on disk — most were removed by some other means while their DB rows persist.
That asymmetry drives the central design fact: **enumeration is from git/disk,
never from the DB.**

## Goals

- A safe, explicit `apex-jobs prune-review-worktrees` verb: dry-run by default,
  `--apply` to mutate, `--include-failed` and `--json` optional.
- Prune only review worktrees that are provably safe (succeeded + clean +
  not-active). Never touch unrelated (lane) worktrees.
- Fail closed: if the DB cannot be reached to verify active-ness, refuse.
- Value-silent: names, paths, classifications, counts, and run timestamps only —
  never file contents, never env/DSN/secret values.
- Age *visibility* in report output (not a pruning criterion).

## Non-goals (explicitly out of scope this lane)

- No `--force` removal.
- No orphan pruning (worktree with no `jobs.run` row is preserved; no override
  flag).
- No age-based eligibility. Eligibility is safety-state only; timestamps are
  displayed for operator judgment, never acted on.
- No auto-clean of successful review-runs — deferred to a later lane (see
  Recommendation). This lane is the explicit command only.
- No mutation of `jobs.run` rows (they remain the historical record; a pruned
  worktree's row keeps its now-stale `worktree_path`).

## Design

### 1. Enumeration (git, filtered)

Parse `git worktree list --porcelain` from the canonical repo. A candidate is a
worktree whose path's parent directory is exactly the runs dir
(`agent_runner._runs_dir()`, i.e. `$APEX_JOBS_RUNS_DIR` or `~/.apex-jobs/runs`)
**and** whose basename starts with `review-`. The porcelain block also yields
the `locked` flag and `detached` state per worktree. The ~20 sibling lane
worktrees under `code/apex/apex-*` are never candidates — they fail the
parent-dir test — so they cannot be enumerated, classified, or removed.

### 2. Per-worktree safety classification

A candidate is pruned only if it clears **every** gate below. First matching
preserve-reason wins; precedence is deterministic — `active`, then `unknown`
(missing dir / git-status error), then `dirty`, `locked`, `orphan`, `failed` —
so the reported reason is stable when several apply. `active` is checked first
because it is the strongest "do not touch"; `active` and `orphan` are mutually
exclusive (active needs a DB row, orphan means none).

| Signal | Source | Result |
|---|---|---|
| Directory missing / `git status` errors | filesystem / git | **preserve** (`unknown`) |
| Active / in-progress | DB: latest `jobs.run` for this `worktree_path` is `status='running'` **and** `lease_expires_at > now()` | **preserve** (`active`) |
| Dirty | `git -C <wt> status --porcelain` non-empty | **preserve** (`dirty`) |
| Locked | git porcelain `locked` flag | **preserve** (`locked`) |
| No DB row (orphan) | DB lookup misses this `worktree_path` | **preserve** (`orphan`) |
| Latest run `failed` | DB status | **preserve** (`failed`) unless `--include-failed` |
| `succeeded` + clean + not-active (or `failed` + `--include-failed`) | — | **prune** |

### 3. Fail-closed on DB-unreachable

The active/status classification requires the DB. If `engine.review_run_statuses()`
raises a connection error, the whole command **refuses**: it preserves
everything, prints a value-silent reason (`"db-unreachable: refusing to prune
(cannot verify active runs)"`), and returns a nonzero exit code. It never
falls back to a git-only heuristic — an unverifiable worktree is never deleted.

### 4. Removal mechanism

Under `--apply`, for each prunable worktree: `git worktree remove <path>`
(**no `--force`**), serialized under `agent_runner._WORKTREE_LOCK` (the same lock
the runner uses for worktree-admin plumbing, so a concurrent `review-run` adding
a worktree cannot race on `index.lock`/`packed-refs`). `git worktree remove`
unregisters and deletes the directory atomically — no separate `git worktree
prune` is run (avoids touching unrelated stale registrations). If git refuses
(e.g. a dirty/locked worktree that slipped past the check via TOCTOU), the
failure is caught and reported as `preserve (remove-failed)` — git is the second
safety net behind the classifier. DB rows are never mutated.

### 5. Report / output fields (age visibility)

Each candidate is reported (dry-run and `--apply`) with:

- `basename` — the `review-<hex8>` dispatch id
- `classification` — `prunable` | `active` | `dirty` | `locked` | `orphan` |
  `failed` | `unknown` | `remove-failed`
- `action` — `would-remove` (dry-run, prunable) | `removed` (`--apply`, done) |
  `preserved` (with reason) | `refused` (db-unreachable)
- `status` — latest `jobs.run` status (`succeeded` | `failed` | `running` |
  `null` for orphan)
- `claimed_at` — latest run `claimed_at`, the run-created anchor (non-null in
  the DB; ISO-8601). Used as the age timestamp because `started_at` is nullable.
- `finished_at` — latest run `finished_at` (ISO-8601 or `null` while running)
- `active` — the running+live-lease boolean

Text mode prints an aligned table plus a summary line
(`<n> candidates: <p> prunable, <k> preserved (<reasons>)`); `--json` prints the
same as a structured list plus counts. Timestamps are shown for operator
judgment; **they are never a pruning input.**

### 6. Value-silence

Output is limited to the fields above (basenames, classification labels,
actions, statuses, ISO timestamps, integer counts). The command never reads or
prints worktree file contents, never prints the DSN/password/env, and never
dumps an environment dict. The DB connection is opened via the engine's normal
resolver; connection details are never echoed.

## Components & interfaces

### `engine.review_run_statuses(worktree_paths: list[str]) -> dict[str, dict]`

New function in `engine.py` (all DB access stays in the engine). One query.
Returns a dict keyed by `worktree_path` for every path in the input that has at
least one `jobs.run` row; the value is the **latest** run (highest `attempt`)
for that path:

```python
{
  "/home/olares/.apex-jobs/runs/review-0b620661": {
      "status": "succeeded",           # latest run status
      "active": False,                 # status=='running' and lease_expires_at > now()
      "claimed_at": "2026-07-05T05:09:00+00:00",   # non-null run-created anchor
      "finished_at": "2026-07-05T05:12:00+00:00",  # or None while running
  },
  ...
}
```

Paths absent from the result have no run row (→ orphan). Raises on DB
connection failure (caller turns that into fail-closed refusal). The query
filters `worktree_path = any(%s)` and picks the max-attempt row per path via a
window/lateral, so it is a single round-trip regardless of candidate count.

### `apex_jobs/prune.py` (new, focused module)

Reuses `agent_runner._git`, `agent_runner._repo`, `agent_runner._runs_dir`, and
`agent_runner._WORKTREE_LOCK`; imports `engine` for the DB lookup.

- `list_review_worktrees(repo, runs_dir) -> list[dict]` — parse
  `git worktree list --porcelain`; return candidates with `path`, `dispatch_id`,
  `locked`, `exists`, `dirty` (each dict is pure git/fs facts, no DB).
- `classify_review_worktrees(include_failed=False) -> list[ReviewWorktree]` —
  enumerate candidates, batch the DB lookup via
  `engine.review_run_statuses([c.path ...])`, and assign
  `classification`/`action`/timestamps per §2/§5. On DB error, raise
  `DbUnreachable`.
- `prune_review_worktrees(apply=False, include_failed=False) -> dict` —
  orchestrate: classify; under `apply`, `git worktree remove` each `prunable`
  (no `--force`, under the lock), updating each item's `action` to `removed` or
  `preserved (remove-failed)`; return `{"items": [...], "counts": {...},
  "applied": apply}`. On `DbUnreachable`, return a refusal summary
  (`applied=False`, everything `refused`) — the CLI maps this to a nonzero exit.

`ReviewWorktree` is a small dataclass carrying the §5 fields plus `path`.

### `cli.py`

- `cmd_prune_review_worktrees(a)` — thin wrapper: call
  `prune.prune_review_worktrees(apply=a.apply, include_failed=a.include_failed)`;
  render text or `--json`; return `0` normally, `3` on db-unreachable refusal.
- Subparser `prune-review-worktrees` with `--apply` (store_true),
  `--include-failed` (store_true), `--json` (store_true). Registered in the
  verb list in the module docstring.

## CLI interface

```
apex-jobs prune-review-worktrees                    # dry-run: classify + report, mutate nothing
apex-jobs prune-review-worktrees --apply            # remove succeeded+clean+not-active review worktrees
apex-jobs prune-review-worktrees --include-failed   # also treat failed reviews as prunable
apex-jobs prune-review-worktrees --json             # structured output (composable with the above)
```

Exit codes: `0` normal (dry-run or applied); `3` db-unreachable refusal.

## Testing strategy

Real `orchestration_test` DB via the existing `conn_test` fixture + throwaway
git worktrees created under a tmp runs dir (following `test_agent_runner.py`:
`APEX_JOBS_REPO` = the lane repo, `APEX_JOBS_RUNS_DIR` redirected to
`tmp_path/runs`; seed `jobs.run` rows with explicit status/lease/timestamps; the
fixture removes every worktree/branch it creates and prunes). All assertions are
value-silent (statuses, classifications, counts, booleans — never file
contents/env).

Cases (each its own test):

1. **succeeded + clean → pruned** under `--apply`; dir gone, `git worktree list`
   no longer lists it; unrelated worktrees still present.
2. **active (running + live lease) → preserved**, even under `--apply`.
3. **dirty (uncommitted file) → preserved** under `--apply`.
4. **locked (`git worktree lock`) → preserved** under `--apply`.
5. **failed → preserved** by default; **failed + `--include-failed` → pruned**.
6. **orphan (worktree, no `jobs.run` row) → preserved** (`orphan`); no override.
7. **unrelated lane-style worktree** (under a different dir, not `review-*`) →
   never enumerated, untouched.
8. **dry-run → no-op**: classifications reported, `would-remove` for prunable,
   nothing removed from disk.
9. **db-unreachable → fail-closed**: `prune_review_worktrees` returns refusal /
   CLI exit `3`, nothing removed. (Simulated by pointing the engine DSN at a
   dead target or monkeypatching `engine.review_run_statuses` to raise.)
10. **report fields present**: a dry-run item carries `basename`,
    `classification`, `action`, `status`, `claimed_at`/`finished_at`, `active`.

CI: add a `run: <venv> -m pytest tests/test_prune.py` (or fold into the existing
apex-jobs suite step) beside the current apex-jobs test invocation in the
records/jobs CI workflow, matching how the suite is already wired.

## Recommendation (deliverable 5): auto-clean on successful review-runs

A later lane should auto-clean the worktree at the end of a **successful**
`run_review_job`, behind a `--keep-worktree` escape hatch, because:

- A review is read-only and opens no promotion gate — unlike the agent path,
  there is nothing to inspect-and-merge afterward.
- The findings are already durable in `jobs.run.result` (`cmd_review` /
  `review-run --json` read them from the DB, not the worktree), so a clean
  detached review worktree is redundant once the run succeeds.
- Failed/timed-out reviews should still retain the worktree for diagnosis
  (mirrors the agent path's `test_agent_job_failure` retention).

This explicit `prune-review-worktrees` command remains valuable regardless: it
cleans the backlog that predates auto-clean, and sweeps failed/kept worktrees on
operator demand. Recommend implementing auto-clean only after this command has
soaked, so the safety classification is proven before it runs unattended.

## Global constraints

- **Host-canonical single-writer:** author locally on Windows → scp per-file to
  the `apex-review-prune` worktree → run/commit host-side over `ssh olares-mesh`.
  PULL-first before editing an existing host file.
- **ASCII-only added lines:** `git diff --cached | grep '^+' | LC_ALL=C grep -P
  '[^\x00-\x7F]'` must be empty.
- **Value-silent** throughout (names/paths/labels/counts/ISO-timestamps only).
- **No `--force`; no orphan pruning; fail-closed on DB-unreachable.**
- **No production mutation** (orchestration_dev is dev; tests use
  orchestration_test only — never orchestration_dev).
- **TDD**, bite-sized commits; commit trailer
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Merge governance: squash self-merge after green CI + whole-branch Codex
  cross-engine review; no admin-bypass, no local-merge.
