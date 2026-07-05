# apex-jobs review-worktree prune — design (rev 2)

**Status:** rev 2 — folds the IRP + Codex cross-engine audit (2026-07-05). Operator-ratified design + four leans + age-visibility; rev 2 forks (cross-process safety = recheck-before-remove; remove-failed = exit 2; --include-failed = documented-irreversible, opt-in, no refs) all ratified.
**Lane:** `orchestration/prune-review-worktrees` (host worktree `/home/olares/code/apex/apex-review-prune` off main `3168f922`)
**Package:** `packages/apex-jobs` (host-canonical — lives on Olares)

## Rev 2 changes (why this differs from rev 1)

A lean audit-mode IRP (3 grounded Claude probes + adversarial pass) and a Codex
cross-engine pass found one fatal design defect and a cluster of must-fixes in
rev 1. Three host-decisive checks then resolved the latent-vs-active question:

- **`jobs.job` has `job_dispatch_id_key` UNIQUE(dispatch_id)** (verified) — one
  dispatch_id ↔ one job_id. Because `worktree_path = runs/<dispatch_id>` is a
  pure function of dispatch_id, a path can never be shared across distinct
  job_ids. This **structurally precludes** the cross-job "max-attempt picks the
  wrong row / stale-succeeded authorizes delete" exploit.
- `~/.apex-jobs/runs` has **no symlinked component**, and all **6/6** live
  worktrees' porcelain paths **exactly** match their stored `jobs.run.worktree_path`
  — so the path-normalization defect is latent today (fixed defensively anyway).

**The fatal defect (rev 1):** the `active` guard keyed on `worktree_path`, which
is **NULL for a running review** until `set_run_artifacts` fires *after* the
codex subprocess returns (`agent_runner.py:189`). So a live review's own run row
was never returned by the path-keyed lookup; the guard was unreachable, and live
reviews were preserved only *accidentally* by the `orphan` (no-DB-row)
fall-through — which would invert to a live-tree delete the instant anyone
persisted `worktree_path` earlier.

**The linchpin fix (rev 2):** re-key the entire classifier from `worktree_path`
→ **`dispatch_id` (= the worktree basename, by construction)**. The unique
constraint makes basename → `jobs.job` → `jobs.run` exact. This makes the active
guard reachable (F1), dissolves the max-attempt/stale-row defects (one job per
dispatch_id), and lets `active` = *any* running run (fixes the NULL-lease
fail-open). All other must-fixes (value-silence, normalization, git-status
hardening, ignored files, frozen snapshot + recheck, exit codes, tests) are
folded below.

## Problem (root cause, grounded)

`agent_runner.run_review_job()` creates a detached git worktree at
`~/.apex-jobs/runs/<dispatch_id>` (dispatch_id = `review-<hex8>`), runs
`codex exec review`, records the findings to `jobs.run`, and — unlike the
agent/promotion path (`run_agent_job` → `open_promotion`) — **never removes the
worktree and opens no gate**. Nothing reaps it, so review worktrees accumulate.
Host 2026-07-05: **6 on disk** under `~/.apex-jobs/runs/review-*`, all
`succeeded` + lease-expired; `jobs.run` holds ~40+ historical review rows but
only 6 exist on disk. **Enumeration is therefore from git/disk, never the DB.**

## Goals

- A safe, explicit `apex-jobs prune-review-worktrees` verb: dry-run by default,
  `--apply` to mutate, `--include-failed` and `--json` optional.
- Prune only review worktrees provably safe: the worktree's dispatch_id maps to a
  real codex-review job whose latest terminal run `succeeded`, with no running
  run, clean tree, not locked.
- Never touch unrelated (lane) worktrees.
- Fail closed: if the DB can't be reached to verify active-ness, refuse.
- Value-silent: names, paths, classifications, counts, ISO timestamps only —
  never file contents, env/DSN/secret values, or psycopg exception strings.
- Age *visibility* in report output (never a pruning criterion).

## Non-goals (explicitly out of scope this lane)

- No `--force` removal — plain `git worktree remove` only.
- No orphan pruning (a review-* worktree with no matching `jobs.job` row is
  preserved; no override flag).
- No age-based eligibility. Eligibility is safety-state only; timestamps are
  displayed for operator judgment, never acted on.
- No cross-process lock (Postgres advisory / file lock) — deferred to future
  hardening (this is an operator-run explicit command, not a scheduled reaper).
  In scope: a per-item **recheck-before-remove** (below).
- No auto-clean of successful review-runs — deferred to a later lane (see
  Recommendation). This lane is the explicit command only.
- No mutation of `jobs.run` rows and no creation/retention of git refs.

## Design

### 1. Enumeration (git, filtered, realpath-canonical)

Parse `git worktree list --porcelain` from the canonical repo. A **candidate**
is a worktree where:

- `os.path.realpath(parent-dir-of-worktree) == os.path.realpath(_runs_dir())`
  (both sides canonicalized; trailing slashes stripped), **and**
- `basename` matches the strict regex **`^review-[0-9a-f]{8}$`** (the exact
  `run_review_job` auto-generated form). A `runs/review-not-a-generated-run`,
  or any lane worktree under `code/apex/apex-*`, fails one of these and is never
  a candidate — never enumerated, classified, or removed.

The porcelain block also yields `locked` and `detached` per worktree. The
candidate's `dispatch_id` **is** its basename.

### 2. Per-worktree safety classification

Precedence — **first match wins** (deterministic, stable reason):

| # | Classification | Condition | Action |
|---|---|---|---|
| 1 | `active` | is_review AND any run `status='running'` (any lease, incl NULL) | **preserve** |
| 2 | `unknown` | dir missing, OR `git status` non-zero exit, OR job exists but is **not** a review job, OR is_review but has no runs | **preserve** |
| 3 | `orphan` | no `jobs.job` row for this dispatch_id | **preserve** |
| 4 | `dirty` | `git -C wt status --porcelain --ignored` non-empty | **preserve** |
| 5 | `locked` | porcelain `locked` flag | **preserve** |
| 6 | `failed` | latest terminal run `failed` | **preserve** unless `--include-failed` |
| 7 | `prunable` | latest terminal run `succeeded` (or `failed` + `--include-failed`), AND not-active, AND clean, AND not-locked | **prune** (under `--apply`) |

Key points vs rev 1:
- **`active` = *any* running run** (regardless of lease). This fixes the NULL-lease
  fail-open: `engine.reap()` never reaps a `running` row with NULL
  `lease_expires_at`, so a lease-comparison predicate would wrongly call it
  not-active. Any `status='running'` row means in-flight → preserve.
- **`active` is reachable** because the lookup is keyed on dispatch_id, so a
  running review (whose `worktree_path` is still NULL) is found via its job row.
- **`dirty` includes ignored files** (`--ignored`): `git status --porcelain`
  omits ignored files, but `git worktree remove` would silently delete them.
- **`git status` non-zero exit ⇒ `unknown` ⇒ preserve** (never read a failed
  status as "empty output = clean").
- **latest terminal run** is chosen within the single job by
  `ORDER BY claimed_at DESC, attempt DESC LIMIT 1` — never `max(attempt)` across
  paths (correct because dispatch_id is unique ⇒ one job per path).

### 3. Fail-closed on DB-unreachable (value-silent, narrow catch)

Classification issues **one** DB query up front (`engine.review_dispatch_statuses`,
§Components). If that query raises **`psycopg.OperationalError`** or
**`psycopg.InterfaceError`** (connection/transport failures), the whole command
**refuses**: preserves everything, prints the fixed value-silent line
`db-unreachable: refusing to prune (cannot verify active runs)`, returns exit
**3**. Rules:

- The `DbUnreachable` exception carries **no** underlying-exception text; **no**
  code path logs/echoes the psycopg string (it can embed host/port/user).
- Only `OperationalError`/`InterfaceError` become the refusal. **Every other
  exception propagates** (a `ProgrammingError`/schema drift, or the
  `db.resolve_dsn()` `RuntimeError` on absent env, crashes loudly rather than
  masquerading as a transient outage). Because the classification query runs
  **before** any removal, a propagated exception leaves **zero** worktrees
  removed — still fail-safe.

### 4. Removal — frozen snapshot + per-item recheck (no `--force`)

Under `--apply`, the classification result is a **single frozen snapshot** (one
up-front DB query; the apply loop makes **no** DB calls **except** the per-item
recheck below). For each `prunable` candidate, in order, under
`agent_runner._WORKTREE_LOCK` (serializes the git plumbing against a concurrent
`run_pool`'s worktree add/remove/branch-D on `index.lock`/`packed-refs`):

1. **Recheck-before-remove** (closes the classify→remove window): re-query this
   one dispatch's running state (`engine.review_dispatch_statuses([dispatch_id])`)
   and re-run the git `dirty`/`locked`/exists checks. If it is now active, dirty,
   locked, or unknown → **skip**, relabel `preserve` with the new reason. This is
   the only DB access inside the apply loop; a recheck query raising
   `OperationalError`/`InterfaceError` aborts the loop into the refusal path
   (exit 3), having removed only already-completed items.
2. `git worktree remove <path>` (**no `--force`**). git itself is the second
   safety net: it refuses a dirty tree (`exit 128`, "modified or untracked
   files") and a locked tree (needs *double* `-f`), so a TOCTOU slip cannot be
   force-deleted. A refusal is caught → relabel `remove-failed` (preserve).

`git worktree remove` unregisters + deletes atomically; **no** separate
`git worktree prune` is run (avoids touching unrelated stale registrations).
`jobs.run` rows are never mutated; no refs are created or retained.

A cross-*process* race (a separate worker process starting a review between the
recheck and the remove) is narrowed to a single git command by the recheck and
is accepted as residual risk for this operator-run command; a Postgres advisory
or file lock is deferred hardening (Non-goals).

### 5. Report / output fields (age visibility)

Each candidate is reported (dry-run and `--apply`):

- `basename` — the `review-<hex8>` dispatch id
- `classification` — `prunable` | `active` | `dirty` | `locked` | `orphan` |
  `failed` | `unknown` | `remove-failed`
- `action` — `would-remove` (dry-run, prunable) | `removed` (`--apply`, done) |
  `preserved` (with reason) | `refused` (db-unreachable)
- `status` — latest `jobs.run` status for the job (`running` | `succeeded` |
  `failed` | `null`)
- `claimed_at` — latest run `claimed_at` (non-null run-created anchor; ISO-8601;
  `started_at` is nullable so `claimed_at` is the age anchor)
- `finished_at` — latest run `finished_at` (ISO-8601 or `null` while running)
- `active` — bool: the job has a running run

Text mode prints an aligned table + a summary line
(`<n> candidates: <p> prunable, <k> preserved (<reasons>)`); `--json` prints the
same as a structured list + counts. Timestamps are shown for judgment only,
**never a pruning input**.

### 6. Value-silence

Output = the fields above only (basenames, classification labels, actions,
statuses, ISO timestamps, integer counts). The command never reads/prints
worktree file contents, the DSN/password/env, an environment dict, or any
psycopg exception string. The DB connection is opened via the engine's normal
resolver; connection details are never echoed.

### 7. Exit codes

- **0** — dry-run, or `--apply` completing with no removal failures.
- **2** — `--apply` where **any** prunable candidate hit `remove-failed`.
- **3** — db-unreachable refusal (nothing removed).

## Components & interfaces

### `engine.review_dispatch_statuses(dispatch_ids: list[str]) -> dict[str, dict]`

New function in `engine.py` (all DB access stays in the engine). **One** query,
keyed on dispatch_id (unique). Returns a dict keyed by dispatch_id for every id
in the input that has a `jobs.job` row:

```python
{
  "review-0b620661": {
      "is_review": True,       # kind='agent' AND payload->>'review_head' IS NOT NULL
      "any_running": False,    # EXISTS a jobs.run for the job with status='running'
      "status": "succeeded",   # latest run: ORDER BY claimed_at DESC, attempt DESC LIMIT 1
      "claimed_at": "2026-07-05T05:09:00+00:00",   # non-null anchor
      "finished_at": "2026-07-05T05:12:00+00:00",  # or None while running
  },
  ...
}
```

SQL (parameterized; `= ANY(%s)` binds the Python list as a `text[]` — no
interpolation, injection-safe):

```sql
SELECT j.dispatch_id,
       (j.kind = 'agent' AND (j.payload ->> 'review_head') IS NOT NULL) AS is_review,
       EXISTS (SELECT 1 FROM jobs.run r
               WHERE r.job_id = j.id AND r.status = 'running')          AS any_running,
       lr.status, lr.claimed_at, lr.finished_at
FROM jobs.job j
LEFT JOIN LATERAL (
    SELECT status, claimed_at, finished_at
    FROM jobs.run
    WHERE job_id = j.id
    ORDER BY claimed_at DESC, attempt DESC
    LIMIT 1
) lr ON TRUE
WHERE j.dispatch_id = ANY(%s);
```

dispatch_ids absent from the result have no job row (→ `orphan`). The function
opens the connection via `engine._conn()`; a `psycopg.OperationalError` /
`InterfaceError` propagates to the caller (→ fail-closed refusal). It is called
with the full candidate list once (frozen snapshot) and again with a single-id
list for each per-item recheck.

### `apex_jobs/prune.py` (new, focused module)

Reuses `agent_runner._git`, `agent_runner._repo`, `agent_runner._runs_dir`, and
`agent_runner._WORKTREE_LOCK`; imports `engine` for the DB lookup. Defines
`class DbUnreachable(Exception)` (carries no exception text).

- `list_review_worktrees(repo, runs_dir) -> list[dict]` — parse
  `git worktree list --porcelain`; realpath-canonicalize both sides; keep only
  candidates matching `^review-[0-9a-f]{8}$` under the runs dir; return
  `{path, dispatch_id, locked, exists, dirty, git_ok}` (pure git/fs facts, no
  DB; `dirty` from `git status --porcelain --ignored`; `git_ok=False` on a
  non-zero status exit).
- `classify_review_worktrees(include_failed=False) -> list[ReviewWorktree]` —
  enumerate; batch `engine.review_dispatch_statuses([dispatch_ids])` **once**;
  assign classification/action/timestamps per §2/§5. Catches only
  `psycopg.OperationalError`/`InterfaceError` → raise `DbUnreachable`; other
  exceptions propagate.
- `prune_review_worktrees(apply=False, include_failed=False) -> dict` —
  orchestrate: classify (frozen snapshot); under `apply`, for each `prunable`,
  under the lock: recheck (single-id DB query + git re-check) → skip/relabel if
  changed, else `git worktree remove` (no `--force`) → `removed` or
  `remove-failed`. Returns `{"items": [...], "counts": {...}, "applied": apply,
  "remove_failed": <int>}`. On `DbUnreachable`, returns a refusal summary
  (`applied=False`, everything `refused`). Never mutates `jobs.run`.

`ReviewWorktree` is a small dataclass: `path, dispatch_id, classification,
action, status, claimed_at, finished_at, active`.

### `cli.py`

- `cmd_prune_review_worktrees(a)` — thin wrapper: call
  `prune.prune_review_worktrees(apply=a.apply, include_failed=a.include_failed)`;
  render text or `--json`; return **3** on db-unreachable refusal, **2** if any
  `remove-failed`, else **0**.
- Subparser `prune-review-worktrees` with `--apply`, `--include-failed`, `--json`
  (all `store_true`). The `--include-failed` help text **documents that failed
  review worktrees are detached (no ref) and their removal may be
  gc-unrecoverable**. Add the verb to the module docstring's verb list.

## CLI interface

```
apex-jobs prune-review-worktrees                    # dry-run: classify + report, mutate nothing
apex-jobs prune-review-worktrees --apply            # remove succeeded+clean+not-active+not-locked review worktrees
apex-jobs prune-review-worktrees --include-failed   # also treat failed reviews as prunable (see --help: irreversible)
apex-jobs prune-review-worktrees --json             # structured output (composable)
```

Exit codes: `0` clean · `2` some remove-failed under `--apply` · `3`
db-unreachable refusal.

## Testing strategy

Real `orchestration_test` DB via `conn_test` + throwaway git worktrees under a
tmp runs dir (following `test_agent_runner.py`: `APEX_JOBS_REPO` = lane repo,
`APEX_JOBS_RUNS_DIR` → `tmp_path/runs`; seed `jobs.job` + `jobs.run` rows with
explicit kind/payload/status/lease/attempt/claimed_at; the fixture removes every
worktree/branch it creates and prunes). `conftest.py` already refuses
`orchestration_dev`/`APEX_JOBS_DSN` (`pytest.exit rc=4`). All assertions are
value-silent (statuses, classifications, counts, booleans — never file
contents/env).

Cases (each its own test):

1. **succeeded + clean → pruned** (`--apply`): dir gone; `git worktree list` no
   longer lists it; unrelated worktrees still present.
2. **in-flight running review, `worktree_path` NULL, tree on disk → preserved
   (`active`)** — seed a review `jobs.job` + a `running` `jobs.run` with
   `worktree_path` NULL; create the worktree on disk; classify finds it via
   dispatch_id (not path); `--apply` preserves it. *(The F1 fix.)*
3. **path reuse within one dispatch/job → preserved** — one job: attempt 1
   `succeeded` (worktree_path set) + attempt 2 `running` (worktree_path NULL)
   sharing the path → `any_running` → `active` → preserved.
4. **latest terminal chosen by `claimed_at`/attempt** — one job with an older
   `failed` and a newer `succeeded` → latest terminal = `succeeded` → prunable;
   inverted timestamps select correctly (locks in `claimed_at DESC`).
5. **dirty (tracked modification) → preserved.**
6. **ignored file present → counts dirty → preserved** (`--ignored`).
7. **`git status` non-zero exit → `unknown` → preserved** (inject a git failure,
   e.g. remove the worktree's `.git` file / point at a broken tree).
8. **locked → preserved.**
9. **failed → preserved**; **failed + `--include-failed` → pruned.**
10. **orphan (valid `review-<hex8>` on disk, no `jobs.job` row) → preserved.**
11. **non-candidate basename** (`runs/review-notgenerated`, or a lane-style
    worktree outside the runs dir) → never enumerated / untouched.
12. **dry-run → no-op**: `would-remove` reported for prunable; nothing removed.
13. **db-unreachable → exit 3 fail-closed**: monkeypatch
    `engine.review_dispatch_statuses` to raise `psycopg.OperationalError`; assert
    exit 3, the fixed value-silent message, no removals, no leaked exception text.
14. **remove-failed → exit 2**: a prunable candidate made dirty/locked right
    before remove (TOCTOU sim) → git refuses → `remove-failed` (preserved) →
    exit 2.
15. **recheck-before-remove**: classify says prunable, but the per-item recheck
    reports `running` (monkeypatched) → skipped/preserved, not removed.
16. **report fields present**: a dry-run item carries `basename`,
    `classification`, `action`, `status`, `claimed_at`/`finished_at`, `active`.
17. **`--include-failed` help text present**: `--help` output contains the
    irreversibility warning.

CI: add a `run: <venv> -m pytest tests/test_prune.py` step beside the existing
apex-jobs suite invocation in the records/jobs CI workflow, matching the wiring
of the current suite.

## Recommendation (deliverable 5): auto-clean on successful review-runs

A later lane should auto-clean the worktree at the end of a **successful**
`run_review_job`, behind a `--keep-worktree` escape hatch, because:

- A review is read-only and opens no promotion gate — nothing to
  inspect-and-merge afterward.
- The findings are already durable in `jobs.run.result` (`cmd_review` /
  `review-run --json` read them from the DB, not the worktree).
- Failed/timed-out reviews should still retain the worktree for diagnosis.

That lane is also the right place for the **durable substrate fix** the audit
surfaced: persist `worktree_path` at run creation (`engine.start`) so a running
review's row carries its path, and (with the reachable dispatch_id-keyed guard)
retire the accidental orphan-shield permanently. This explicit
`prune-review-worktrees` command remains valuable regardless (it clears the
pre-auto-clean backlog and sweeps failed/kept worktrees on operator demand).
Implement auto-clean only after this command has soaked, so the classification is
proven before it runs unattended.

## Global constraints

- **Host-canonical single-writer:** author locally on Windows → scp per-file to
  the `apex-review-prune` worktree → run/commit host-side over `ssh olares-mesh`.
  PULL-first before editing an existing host file.
- **ASCII-only added lines in code files** (`.py`/`.sh`/`.yml`/`.json`):
  `git diff --cached -- '*.py' '*.sh' '*.yml' '*.yaml' '*.json' | grep '^+' |
  LC_ALL=C grep -P '[^\x00-\x7F]'` must be empty. (Markdown prose is exempt.)
- **Value-silent** throughout (names/paths/labels/counts/ISO-timestamps only;
  never a DSN/password/env value or a psycopg exception string).
- **No `--force`; no orphan pruning; no refs; fail-closed on DB-unreachable.**
- **No production mutation** — tests use `orchestration_test` only, never
  `orchestration_dev`.
- **TDD**, bite-sized commits; commit trailer
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Merge governance: squash self-merge after green CI + whole-branch Codex
  cross-engine review; no admin-bypass, no local-merge.
