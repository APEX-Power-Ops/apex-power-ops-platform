# prune-review-worktrees Hardening -- Design

**Date:** 2026-07-07
**Lane:** `orchestration/prune-worktrees-hardening`
**Status:** design (operator-approved with constraints; pre-plan)
**Chip:** `task_cf2ab656`
**Predecessors:** prune utility (#68), auto-clean at source (#69), advisory-lock/fuse (#70)

## Goal

Make `apex-jobs prune-review-worktrees` (a) report clearly which review artifacts exist and why
each is preserved, and (b) offer two EXPLICIT, guarded cleanup modes -- force-remove
succeeded+inactive+dirty review worktrees, and remove stale orphan `.lock` sidecars -- WITHOUT
changing any default behavior. Today the tool sees only git-registered worktrees, classifies
dirty+succeeded as `dirty`/preserved, and never enumerates the `runs/<dispatch_id>.lock` files that
`_worktree_flock` creates-but-never-unlinks (hence they accumulate).

## Guiding principle: ADDITIVE ONLY

The classifications (`prunable/active/dirty/locked/orphan/failed/unknown/remove-failed/contended`)
are a locked test contract (e.g. `test_missing_dir_is_unknown` pins missing->`unknown`;
`test_dirty_tracked_modification_preserved` pins dirty). So this lane adds **new flags + new action
labels + new summary fields**; it never reclassifies, never removes/renames an existing JSON key,
and never changes a default removal decision. New flags OFF => byte-identical behavior + output keys.

## Behavior contract

### Default (no new flags) -- UNCHANGED
- Dry-run by default; `--apply` removes ONLY clean `prunable` (succeeded+clean+not-active+not-locked).
- `--include-failed` remains scoped to FAILED review worktrees only (unchanged).
- The full coordinator-PG-lock -> flock-fuse -> `_WORKTREE_LOCK` -> recheck-before-remove ->
  plain `git worktree remove` choreography is untouched.

### Reporting -- ADDITIVE (always on)
Do NOT remove or rename existing keys (`items`, `counts`, `applied`, `remove_failed`, `refused`,
`refused_reason`). Add:
- `items[*].exists: bool` (additive per-item field) -- lets "registered-missing" be seen without
  reclassifying (a missing dir stays classification `unknown`).
- `orphan_locks: [ {basename, dispatch_id, held, has_active_run, has_registered_worktree, action,
  preserve_reason} ]` -- the new orphan-lock bucket.
- `lock_remove_failed: int` -- orphan-lock removal failures (separate from `remove_failed`).
- `buckets: {registered, dirty_succeeded, orphan_locks, registered_missing}` -- explicit COUNTS for
  the four buckets the operator named:
  - `registered` = len(items),
  - `dirty_succeeded` = items where classification==`dirty` AND status==`succeeded` AND not active,
  - `orphan_locks` = len(orphan_locks),
  - `registered_missing` = items where `exists` is False.

### `--force-succeeded-dirty` (NEW, guarded)
- Targets ONLY review worktrees that are classification==`dirty` AND status==`succeeded` AND not active.
- MUST require `--apply` to remove (dry-run just reports `would-remove-force`). MUST NEVER imply
  `--include-failed` (independent flags; a failed dirty tree is never force-removed by this flag).
- Removal reuses the EXACT existing choreography (coordinator PG-lock -> flock fuse -> `_WORKTREE_LOCK`
  -> recheck-before-remove that re-confirms review+succeeded+inactive+dirty+exists) then
  `git worktree remove **--force**`. New action labels `would-remove-force` / `removed-force`.
  Classification stays `dirty`. Never touches active/locked/contended/failed/unknown/orphan/prunable.

### `--prune-orphan-locks` (NEW, guarded) -- remove a stale orphan `review-*.lock` sidecar only after
ALL FOUR proofs hold (any failure => preserve + report the reason):
1. basename matches `^review-[0-9a-f]{8}\.lock$`,
2. NO registered worktree candidate exists for that dispatch (`has_registered_worktree` False),
3. the DB says NO active review run for that dispatch, OR no row exists (`has_active_run` False),
4. a non-blocking `flock(LOCK_EX|LOCK_NB)` acquisition SUCCEEDS (`held` False).
Then `os.remove` the lock file (safe to unlink while holding the flock). MUST require `--apply`.
`preserve_reason` in {`has-registered-worktree`, `active-run`, `held`, `flock-error`, `remove-failed`}.
Action labels `would-remove-lock` / `removed-lock` / `preserved`. Non-matching `.lock` files (check 1)
are simply not enumerated. DbUnreachable/GitUnavailable => whole-op refusal (exit 3), never fail-open.

## New public surface

`prune.prune_review_worktrees(apply=False, include_failed=False, force_succeeded_dirty=False,
prune_orphan_locks=False)` -- two new kwargs, default False.
New helper `prune.list_orphan_locks(runs_dir, registered_ids)` -> candidate orphan-lock dicts
(regex-filtered, registered-excluded) with git/fs facts; the DB active-run check + flock probe are
applied in classify/apply so the single frozen DB snapshot rule is preserved.

## Safety / error handling (unchanged posture)
Value-silent throughout (names/paths/labels/counts/booleans/ISO-timestamps only). `DbUnreachable`
(psycopg Operational/Interface) and `GitUnavailable` -> refusal summary (exit 3). Any lock/DB/fs
error mid-apply -> partial-apply refusal (`applied=True`), never a raw traceback, never fail-open.
Orphan-lock removal recheck is fresh at apply time (re-run all 4 proofs before `os.remove`).

## CLI

`prune-review-worktrees` gains `--force-succeeded-dirty` and `--prune-orphan-locks` (both
`action="store_true"`, both no-op without `--apply` for the destructive part; `--json` unchanged).
Human-readable output gains a sectioned report: registered worktrees (classification incl.
dirty/missing), then orphan locks (held / active-run / reason), then the `buckets` summary line.
Exit codes: 0 clean; 2 if `remove_failed` or `lock_remove_failed` > 0; 3 on refusal.

## Testing (TDD, fake dirs/locks; real orchestration_test DB)

New module `packages/apex-jobs/tests/test_prune_hardening.py`. Shared setup (`prune_env` fixture +
the worktree/lock/db helper functions it needs) moves to `packages/apex-jobs/tests/conftest.py` so
`test_prune.py`'s TEST FUNCTIONS stay byte-unchanged and the new module reuses them. New tests
(value-silent -- classifications/labels/counts/booleans only):
- orphan-lock enumeration: stale (no worktree, unheld, no active run) -> would-remove-lock; held ->
  preserved+held; active-run -> preserved+active-run; has-registered-worktree -> excluded/preserved;
  non-matching basename -> not enumerated.
- `--force-succeeded-dirty`: dirty+succeeded+inactive -> would-remove-force (dry-run) and removed-force
  (apply); dirty+failed and dirty+active and locked -> never force-removed; requires --apply.
- `--prune-orphan-locks`: stale lock removed (apply); held/active-run/registered -> preserved+reason;
  requires --apply; DbUnreachable -> refusal.
- Default-unchanged guards: with no new flags, a dirty+succeeded worktree stays preserved and orphan
  locks are reported but not removed; existing summary keys present + unchanged in shape.

## Out of scope
- Deleting any CURRENT real review artifact (the live `runs/review-*` dirty worktrees + `.lock`
  sidecars). All apply-path testing is on throwaway tmp dirs/locks. The real artifacts are cleaned by
  the operator later using these new modes, not by this lane.
- Dropping stale git worktree registrations via `git worktree prune` (the tool uses `git worktree
  remove`; git-registration GC is a separate concern).

## Execution model
Host-canonical single-writer over mesh; lane branch in the MAIN worktree (caches + DB present);
value-silent; ASCII-only added lines; the apex-jobs suites run via injection (`inject.sh dev`,
`APEX_JOBS_PGPASSWORD`) against `orchestration_test`. Cross-engine Codex review via
`apex-jobs review-run` at the end (Codex is offline ~45 min -> the review lands last; the PR holds at
the CI/review gate until the Codex pass is clean). Merge governance: squash, author self-merge after
green CI + Codex, NO admin-bypass; restore `main` after merge.
