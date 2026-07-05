# apex-jobs Review-Worktree Auto-Clean Design

**Status:** rev 6 — **CONVERGED** (five Codex re-review rounds; forks A1 + B1 + C2 operator-ratified 2026-07-05). Rev 1 → rev 2 fixed a convergent fatal (no-force remove semantics) + a stale-attempt race; rev 2 → rev 3 folded label-truth + narrowed exception isolation + `already_absent` + C2; rev 3 → rev 4 reordered the guard (`already_absent` before `superseded`) + corrected reachability wording; rev 4 → rev 5 corrected the same-process safety decomposition (both `_WORKTREE_LOCK` **and** the currency-check-under-lock are load-bearing) + label wording + test spies; rev 5 → rev 6 folds two LOW wording nits (helper-comment/table consistency; value-silence scoped to this lane's additions). **Codex rev-5 verdict: core design logic sound, holistic consistency pass clean, no regressions** — only those two LOW wording items remained, now fixed. Convergence bounded at 5 Codex rounds (severity trajectory fatal → fatal → blocking → important → low). Awaiting operator approval to write the plan.

**Goal:** Stop `apex-jobs` review-runs from leaking detached worktrees at the source, by having `run_review_job` remove its own disposable worktree after a **pristine, succeeded, still-current** review — never demoting a good review because housekeeping hiccuped, never deleting anything `prune-review-worktrees` would preserve, and leaving that verb as the durable backstop.

**Architecture:** A single, guarded, in-process cleanup step at the tail of `run_review_job`, gated on run success + a per-job opt-out (`payload.keep_worktree`) + an attempt-currency guard + a dirtiness pre-check whose definition is byte-identical to prune's. No DB schema change; no early `worktree_path` persistence. The cleanup helper owns the filesystem outcome and returns the true disposition as a fixed-vocabulary label; recording is separate best-effort and never relabels.

**Tech stack:** Python 3, `psycopg` (host Postgres `jobs.*`), `git worktree` / `git status`, existing `agent_runner`/`engine`/`cli` modules in `packages/apex-jobs`.

---

## Context — the leak (grounded)

`run_review_job` (agent_runner.py:145) checks out `payload.review_head` **detached** at `~/.apex-jobs/runs/<dispatch_id>`, runs `codex exec review`, records findings to `jobs.run.result`, calls `engine.set_run_artifacts`, and returns. It is read-only (no commit, no diff, no promotion gate). Unlike `run_agent_job` (which opens a promotion gate whose resolution reclaims the worktree), a review opens no gate — so nothing ever reclaims its worktree and it accumulates under `~/.apex-jobs/runs/review-*`. The findings — the review's entire value — are durable in the run row; the worktree is disposable scratch. Both entry paths funnel through `run_review_job`: `review-run` (synchronous, cli.py:173) and `enqueue-review` (async → `run_pool → _run_one → run_review_job`, cli.py:157). Auto-clean is enabled for **both** paths under the current single-worker deployment (see Concurrency posture).

## Non-goals

- No DB schema change (`cleanup_status` merges into existing `jobs.run.result` JSONB).
- No early `worktree_path` persistence (prune keys on `dispatch_id`; the runner holds the path in-process).
- **The cleanup path never uses `--force`.** Dirtiness is decided by an explicit pre-check, not by git's implicit refusal. (The pre-existing start-time `git worktree remove --force` in `run_review_job`/`run_agent_job` is unchanged and out of scope — see Deferred hardening.)
- No auto-clean of failed/timeout/errored reviews (preserved for diagnosis; reachable via `prune --include-failed`).
- No change to the merged `prune-review-worktrees` verb (Fork B1: `--keep-worktree` is not a prune-proof hold).
- **No cross-process worktree locking in this lane** (Fork C2). The crash window and the cross-process stale-attempt race are accepted as deferred hardening; `prune-review-worktrees` is the durable backstop.

## Approved scope (rev-3 contract)

1. Explicit `git status --porcelain --ignored` pre-check before cleanup: empty → plain `git worktree remove`; non-empty → `dirty_preserved`; the cleanup path never uses `--force`.
2. Attempt-currency guard under `_WORKTREE_LOCK`: if a newer attempt exists for the same dispatch/job, skip cleanup as `superseded_preserved`; never remove a path that could belong to a newer live attempt (same-process guarantee — see Concurrency posture for the cross-process residual).
3. Exception isolation with **truth-preserving** structure: the cleanup helper owns the filesystem disposition and returns the true label; `set_run_artifacts` and `set_run_cleanup` are independent best-effort writes that log exception **class names** value-silently and never relabel the true cleanup outcome. Cleanup failure never demotes a successful review.
4. `--keep-worktree` on both `review-run` and `enqueue-review`; runner honors `payload.keep_worktree`; enqueue merge is **OR** semantics (the flag can only add keep, never erase a payload keep).
5. Scope wording: the prune-backstop guarantee applies to default `review-<hex8>` dispatch IDs; custom/manual dispatch IDs are out of prune-backstop scope. In-process auto-clean may still use the exact path it created, subject to the same dirty/currency guards.
6. Test matrix (below).

**Fork decisions:** A1 — preserve ignored-cache dirty trees (dirtiness definition identical to prune's). B1 — `--keep-worktree` is auto-clean opt-out only, not permanent prune immunity. **C2 — same-process currency guard now; the cross-process stale-attempt race is deferred hardening (not reachable in the current single-worker deployment); auto-clean stays enabled for both sync and async paths.**

**Load-bearing principle:** `cleanup_status` is **orthogonal** to run status. A cleanup/DB hiccup never demotes a good review; the review stays `succeeded`, carrying a preserve/absent label so any leftover is visible and prune reclaims it.

---

## Concurrency posture (guardrail wording)

This design is **safe for normal single-worker, unique-dispatch-id operation; cross-process stale-attempt hardening is deferred.** It is *not* claimed safe under arbitrary multi-process concurrency. Precisely:

- **Same-process (one `run_pool` worker, N threads):** filesystem-safe via **two** load-bearing mechanisms, both required. (1) The module `_WORKTREE_LOCK` serializes every attempt's setup `worktree add`/`remove` against the cleanup `worktree remove` — they cannot interleave. (2) The `run_is_current` currency check, performed **under that lock**, prevents a stale cleanup from acting on a newer attempt that has *already* completed its `worktree add`: without it, a stale cleanup that acquires the lock *after* the newer attempt's add finished could `git status`/`remove` the newer live tree. The lock alone does not prevent that (add and remove are serialized but both still run); the currency check is what makes the stale cleanup a no-op (`superseded_preserved`). Together they guarantee a stale cleanup never touches a newer attempt's worktree. A stale run whose currency check still passes (its own tree; no newer attempt committed yet) cleans only its own pristine tree — honest and harmless.
- **Cross-process (two processes creating attempts for the same job):** a residual stale-attempt race remains — process A's committed-DB currency check can pass microseconds before process B commits a new attempt and re-creates the shared `runs/<dispatch_id>` path, after which A's plain remove could delete B's live worktree. `_WORKTREE_LOCK` is a `threading.Lock` (in-process only) and cannot serialize this. Reachable only when two processes create attempts for the **same job** concurrently: (i) multiple queue-draining worker processes (not the current dev-only single-worker deployment), or (ii) deliberate concurrent reuse of the **same explicit `--dispatch-id`** across two `review-run`/`enqueue-review` invocations. Normal `review-run` auto-generates a unique `review-<hex8>` per call, so normal single-invocation use never hits this. Accepted as deferred hardening.

## Deferred hardening

A future **dispatch/worktree-lifecycle advisory-lock lane** is the correct home for the cross-process fix: a Postgres advisory lock keyed on `dispatch_id`, held around **both** the start-time worktree create/remove (in `run_review_job` *and* `run_agent_job`) **and** the cleanup remove. That lane closes all cross-process cases at once: (i) multiple queue-draining workers, and (ii) concurrent same-`--dispatch-id` reuse. It also owns the **pre-existing** cross-process hazard this lane does not touch: the start-time `git worktree remove --force` can already delete a concurrent attempt's live tree across processes today, independent of auto-clean. Bundling both into one lifecycle-lock spec keeps the fix coherent; splitting a partial advisory lock into this lane would half-solve it and leave the startup race open.

## Design

### `cleanup_status` vocabulary (fixed; the only allowed values)

Recorded on **every** review run, merged into `jobs.run.result`. Exactly one of:

| `cleanup_status` | Meaning | Worktree | Run status |
|---|---|---|---|
| `not_attempted` | review not `succeeded` (failed / timeout / error) — cleanup never attempted | preserved | `failed` |
| `kept` | succeeded + `payload.keep_worktree` true (opt-out) | preserved | `succeeded` |
| `already_absent` | succeeded, not kept, but the worktree dir was **already gone** at cleanup time (raced by an explicit prune or a newer attempt's teardown) — benign, no action | already gone | `succeeded` |
| `superseded_preserved` | succeeded, not kept, dir **present**, but this run is **not the current attempt** (a newer attempt exists) — cleanup took no action, left the path untouched (no `git status`, no `remove`) | untouched | `succeeded` |
| `dirty_preserved` | succeeded, not kept, current, but `git status --porcelain --ignored` **non-empty** | preserved | `succeeded` |
| `cleaned` | succeeded, not kept, current, **pristine**, plain `git worktree remove` returned 0 | removed | `succeeded` |
| `failed_preserved` | succeeded, not kept, current, pristine attempt, but `git worktree remove` returned non-zero, **or** `git status` errored, **or** the decision block raised | preserved | `succeeded` |

All seven are bare labels — value-silent, no paths/stderr/secrets. Only `cleaned` removes a tree; `already_absent` observes it was already gone; every other outcome preserves (or the review failed). `failed_preserved` now means strictly "cleanup was attempted and could not complete cleanly" — the benign already-gone case is `already_absent`, not a failure. This is the complete, exhaustive disposition set; tests and operator output assert against exactly these strings.

### Decision flow — `run_review_job` tail (proposed; truth-preserving)

Review success is committed by `report` **before** this block. The helper owns the filesystem outcome and returns the true label; the two recording writes are independent best-effort and never relabel it:

```python
result = {"findings": out[-8000:], "stderr": err[-4000:],
          "review_head": review_head, "base_ref": base_ref, "is_review": True}
status = engine.report(run_id, exit_code=rc, result=result)   # commits terminal review status; nothing below changes it

# (a) record where the run ran -- best-effort; prune keys on dispatch_id, so a miss is harmless
try:
    engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)
except Exception as e:
    log.warning("review set_run_artifacts error: %s", type(e).__name__)   # value-silent: class name only

# (b) decide + apply worktree disposition. _cleanup_review_worktree OWNS the fs mutation and returns
#     the TRUE label. A raise HERE means the disposition is genuinely uncertain -> failed_preserved.
try:
    keep = bool((job.get("payload") or {}).get("keep_worktree"))
    if status != "succeeded":
        cleanup_status = "not_attempted"
    elif keep:
        cleanup_status = "kept"
    else:
        cleanup_status = _cleanup_review_worktree(repo, wt, run_id)
except Exception as e:
    log.warning("review cleanup error: %s", type(e).__name__)
    cleanup_status = "failed_preserved"

# (c) record the disposition -- best-effort; a recording failure NEVER relabels the true outcome in (b)
try:
    engine.set_run_cleanup(run_id, cleanup_status)
except Exception as e:
    log.warning("review set_run_cleanup error: %s", type(e).__name__)

return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
        "review_head": review_head, "findings_len": len(out),
        "cleanup_status": cleanup_status}
```

`log = logging.getLogger(__name__)` at module scope. If `_cleanup_review_worktree` returns `cleaned` (dir removed) and `set_run_cleanup` then raises, `cleanup_status` stays `cleaned` — the summary is accurate; the DB row merely lacks the key (indistinguishable from the crash window, which prune no-ops on since the dir is gone). No lie. Each `except` logs only `type(e).__name__` — never the message, args, path, or SQL — so a real bug (bad SQL, helper error) is observable without leaking values.

### The cleanup helper (agent_runner) — guarded, no `--force`, owns the fs outcome

```python
def _cleanup_review_worktree(repo, wt, run_id):
    """Decide + apply cleanup for a SUCCEEDED, non-kept review worktree. Caller has already
    confirmed status=='succeeded' and keep is false. Runs under _WORKTREE_LOCK. OWNS the fs
    mutation and returns the TRUE disposition label. Value-silent: returns a bare label, never a
    path or git stderr. Guard order is load-bearing (filesystem truth first):
      1. absent    -> dir already gone (raced by prune / a newer attempt's teardown) -> 'already_absent'
      2. currency  -> dir present but this run is not the current attempt -> 'superseded_preserved' (touch nothing)
      3. dirtiness -> git status --porcelain --ignored non-empty -> 'dirty_preserved' (never remove)
      4. remove    -> plain `git worktree remove` (NEVER --force): rc 0 -> 'cleaned', else 'failed_preserved'
    """
    with _WORKTREE_LOCK:
        if not os.path.isdir(wt):
            return "already_absent"                    # fs truth first: nothing to clean or preserve
        if not engine.run_is_current(run_id):
            return "superseded_preserved"              # present, but not the current attempt -> touch nothing
        st = _git("status", "--porcelain", "--ignored", cwd=wt, check=False)
        if st.returncode != 0:
            return "failed_preserved"                 # git error -> preserve, do not guess
        if st.stdout.strip():
            return "dirty_preserved"                  # ANY tracked/untracked/IGNORED content
        r = _git("worktree", "remove", wt, cwd=repo, check=False)   # plain, NEVER --force
        return "cleaned" if r.returncode == 0 else "failed_preserved"
```

- **Filesystem truth first, then currency:** `already_absent` (dir gone) takes priority over `superseded_preserved`, so the label is the true fs disposition. If the dir is present but this run is not the current attempt, cleanup takes no action (`superseded_preserved`) — it does not run `git status` or `remove`. Same-process safety comes from **both** `_WORKTREE_LOCK` (serializes setup vs cleanup) **and** the currency check under that lock (prevents a stale cleanup from acting on a newer attempt's already-created worktree). The cross-process residual is deferred (see Concurrency posture).
- **Dirtiness = prune's definition** (Fork A1): `git status --porcelain --ignored`, identical to `prune._worktree_flags`. Non-empty (including ignored caches like `.pytest_cache/`, `__pycache__/`) → `dirty_preserved`; the code path never reaches `remove` on a dirty tree, so git's `--force`-off ignored-file deletion can never fire.
- Only `returncode`/emptiness drive labels; git stdout/stderr are never surfaced.

### `engine.run_is_current` (new — the currency guard)

```python
def run_is_current(run_id):
    """True if run_id is the highest-attempt run for its job (not superseded by a newer attempt).
    False if not found. Backs the same-process auto-clean currency guard."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select (r.attempt = (select max(attempt) from jobs.run r2 "
                "where r2.job_id = r.job_id)) as is_current "
                "from jobs.run r where r.id = %s", (run_id,))
            row = cur.fetchone()
    return bool(row and row["is_current"])
```

### `engine.set_run_cleanup` (new — no schema change)

Mirrors the existing `engine.reap()` JSONB-merge idiom:

```python
def set_run_cleanup(run_id, cleanup_status):
    """Merge cleanup_status into the run's result JSONB (no schema change). ORTHOGONAL to run
    status: never changes status, finished_at, exit_code, or the process exit."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set result = coalesce(result, '{}'::jsonb) "
                "|| jsonb_build_object('cleanup_status', %s::text) where id=%s",
                (cleanup_status, run_id))
        conn.commit()
```

`jobs.run.result` is JSONB (`002_jobs_tables.sql:38`). The shallow `||` merge replaces only `cleanup_status`, preserving `findings`/`stderr`/`review_head`/`base_ref`/`is_review`. `report` commits terminal status before this runs, so `reap` (targets only `status='running'`) can never race it.

### CLI — `--keep-worktree` on both entrypoints (Fix 4)

One signal, `payload.keep_worktree`; the runner reads only the payload.

- **`enqueue-review`**: add `--keep-worktree (store_true)`; **OR-merge** so the flag can only add keep, never erase an operator `--payload` opt-out:
  `payload["keep_worktree"] = bool(a.keep_worktree) or bool(payload.get("keep_worktree"))`.
  **Caveat (documented):** the flag applies when a *new* dispatch id is enqueued. Re-enqueuing an existing dispatch id updates title only (`engine.enqueue` conflict behavior), so `--keep-worktree` does not retrofit an existing job row. `review-run` auto-generates a fresh `review-<hex8>` per call, so this edge affects only explicit `enqueue-review --dispatch-id` reuse.
- **`review-run`**: add `--keep-worktree (store_true)`; build `payload = {"review_head": a.review_head, "keep_worktree": bool(a.keep_worktree)}`; add `"cleanup_status": summary["cleanup_status"]` to `--json`.
- Help on both: `--keep-worktree  opt out of auto-cleanup at review completion (not a permanent hold; a later explicit prune may still reclaim a clean worktree)`.

---

## Spec must-answer

1. **Where recorded** — `jobs.run.result` JSONB under `cleanup_status` (via `engine.set_run_cleanup`, reap idiom; no column). Also in the `run_review_job` summary and `review-run --json`.
2. **Exit/status impact** — none. `report` commits status before the housekeeping; the helper owns the fs outcome; the two recording writes are best-effort and never relabel. `review-run` exits 0 on a succeeded review regardless of `cleanup_status`.
3. **In JSON/result** — the `cleanup_status` label (one of seven) in the summary, `review-run --json`, and `jobs.run.result`.
4. **Both entrypoints** — `--keep-worktree (store_true)` on both; `enqueue-review` OR-merges into `--payload`; `review-run` writes its literal payload; runner reads `(job.get('payload') or {}).get('keep_worktree')`.
5. **No-force / dirty proof** — an explicit `git status --porcelain --ignored` pre-check preserves on any dirt (incl ignored) and the code path never reaches `remove` on a dirty tree; a spy test asserts the **cleanup remove** call is not invoked when the pre-check is non-empty and that the cleanup remove never carries `--force`.

## Fork decisions (ratified)

- **A1** — ignored-cache dirt is `dirty_preserved`. Auto-clean's dirtiness definition equals prune's. Pristine successes are cleaned; cache-dirty successes fall to the explicit prune/cache-clean path. The leak is *reduced*, not eliminated; no worktree prune would protect is ever auto-deleted.
- **B1** — `--keep-worktree` opts out of auto-clean at review completion only. A `kept` worktree is clean, so a later *explicit* prune may still reclaim it. Documented; permanent holds are a future prune-lane extension.
- **C2** — same-process currency guard now; cross-process stale-attempt race deferred (not reachable in the current single-worker deployment); auto-clean enabled on both sync and async paths. See Concurrency posture + Deferred hardening.

## Scope wording — prune-backstop coverage

The prune backstop guarantee (a leaked/preserved worktree is later reclaimable) applies to **default `review-<hex8>` dispatch IDs** — what `review-run` generates and what the leak produces. `prune-review-worktrees` enumerates only basenames matching `^review-[0-9a-f]{8}$` whose parent is the runs dir. Operator-supplied custom dispatch IDs (e.g. `enqueue-review --dispatch-id rv-1`) are **out of prune-backstop scope**; auto-clean still applies to them in-process (same guards), but a preserved/`kept`/`dirty_preserved` leftover under a non-`review-<hex8>` id will not be enumerated by prune. Documented, not silently assumed.

## Test plan (host-only, `orchestration_test`, fake-agent seam)

Tests use `APEX_JOBS_AGENT_CMD` against real `orchestration_test` with throwaway worktrees, same harness as `test_prune.py`. The default review fake writes into cwd → dirty tree — the `cleaned` case needs an explicit pristine fake; dirty cases inject the relevant file. Fakes run in `cwd=wt`:
- pristine: `["sh","-c","echo FINDINGS; exit 0"]`
- untracked dirt: `["sh","-c","echo x > untracked.txt; echo FINDINGS; exit 0"]`
- ignored dirt: `["sh","-c","mkdir -p __pycache__; echo x > __pycache__/x.pyc; echo FINDINGS; exit 0"]`
- failure: `["sh","-c","exit 1"]`

| # | Test | Assert |
|---|---|---|
| 1 | pristine success → cleaned | `cleaned`; dir gone; absent from `git worktree list --porcelain` |
| 2 | ignored-only dirt → preserved | `dirty_preserved`; dir present; status `succeeded` |
| 3 | untracked non-ignored dirt → preserved | `dirty_preserved`; dir present; status `succeeded` |
| 4 | dirty pre-check prevents the remove call | spy on `agent_runner._git`: when `status --porcelain --ignored` non-empty, no `("worktree","remove",...)` call; the cleanup remove never contains `"--force"` |
| 5 | superseded attempt → preserved, untouched | seed a newer run (higher attempt) → `run_is_current` False → `superseded_preserved`; dir present; **spy on `agent_runner._git` asserts neither `("status",...)` nor `("worktree","remove",...)` is called** once the currency check fails |
| 6 | already-gone → already_absent | remove the dir after report but before cleanup → `already_absent`; status `succeeded` |
| 6b | already-gone **+ newer attempt** → already_absent | dir gone AND a newer attempt exists (seed higher-attempt run) → helper returns `already_absent` (fs-truth-first ordering, **not** `superseded_preserved`) |
| 7 | record failure never relabels | monkeypatch `engine.set_run_cleanup` to raise on a pristine success → summary `cleaned` (dir gone), run `succeeded`, `review-run` exits 0 |
| 8 | decision-block failure → failed_preserved + not demoted | monkeypatch `engine.run_is_current` to raise → `failed_preserved`; run `succeeded`; exit 0 |
| 8b | set_run_artifacts raises → cleanup still runs | monkeypatch `engine.set_run_artifacts` to raise on a **dirty** review → cleanup proceeds → `dirty_preserved`, `worktree_path` unset, run `succeeded`; prune still classifies the **preserved** tree by dispatch_id (worktree_path NULL) |
| 9 | `--keep-worktree` → preserved | succeeded + keep → `kept`; dir present |
| 10 | keep OR-merge (enqueue-review) | `--payload '{"keep_worktree":true}'` **without** the flag → `payload.keep_worktree==True` → `kept`; flag-without-payload also `kept`; neither → cleanup runs |
| 11 | failed review → not_attempted | `not_attempted`; dir present; run `failed` |
| 12 | CLI flag on both entrypoints | argparse parses `--keep-worktree` for `review-run` and `enqueue-review`; `review-run --json` includes `cleanup_status` |
| 13 | concurrent/pool path | two reviews cleaning under `_WORKTREE_LOCK` via `run_pool` → both terminate with valid labels; no `index.lock`/registry race |
| 13b | same-dispatch-id concurrency (labels) | seed a second run for the same job (simulates concurrent same-`--dispatch-id` review-run) → `run_is_current`/`already_absent` labels correct; **note in the test** that the true cross-process delete race is the deferred lifecycle-lock lane, not unit-testable here |
| 14 | value-silence (lane additions) | the `cleanup_status` additions emit labels/counts only — no worktree paths beyond the pre-existing `worktree_path`, no git stderr, no file contents; swallowed-exception logs carry class names only. (Pre-existing review `findings` output is unchanged and out of scope.) |
| 15 | existing prune tests still pass | `test_prune.py` unchanged and green (regression) |

## Value-silence

Scoped to **this lane's additions** (the review `findings` output — the review's intended product, stored in `result.findings` and printed by `review-run` — is pre-existing and unchanged; this lane introduces no new value output). `cleanup_status` is one of seven fixed labels. The helper inspects only `returncode`/emptiness and discards git stdout/stderr. Swallowed exceptions log `type(e).__name__` only. `set_run_cleanup` binds a bare label. The new `cleanup_status` surfaces (summary, `--json`, `result`) carry labels only — no paths, git stderr, DSN, env, or file contents.

## Backstop relationship to prune-review-worktrees

Auto-clean removes only the pristine-success case; prune remains the durable backstop for what this lane preserves — `dirty_preserved` (incl ignored caches, A1), `kept` (B1), `superseded_preserved`, `failed_preserved`, `not_attempted`, the crash window, and (per C2) any cross-process leftover — all under `review-<hex8>` ids. No change to the prune verb; its dirtiness definition and auto-clean's are identical, so the two never disagree about what is safe to remove.

## Audit resolution (two dual-engine rounds)

**Round 1 (rev 1 → rev 2):**
| Finding (sev) | Engine | Resolution |
|---|---|---|
| no-force remove silently deletes ignored-only trees / refuses on untracked (FATAL, convergent) | Codex + IRP | Fix 1: explicit `--ignored` pre-check == prune's; `dirty_preserved` (A1) |
| stale attempt removes a newer live attempt's worktree (FATAL) | Codex | Fix 2: currency guard; `superseded_preserved` |
| post-report cleanup/DB failure demotes review at process layer | Codex + IRP | Fix 3: exception isolation |
| `enqueue-review` flag overwrites operator `--payload` keep | Codex + IRP | Fix 4: OR-merge |
| prune regex misses custom dispatch ids | Codex | Fix 5: narrow backstop guarantee to `review-<hex8>` |
| `--keep-worktree` not durable vs later prune | IRP | Fork B1: documented |
| happy-path test unachievable w/ writing fake; missing dirty/pool cases | IRP | Fix 6: rebuilt matrix |
| "prune verb does not exist" (HIGH) | IRP | Discounted — stale-local-tree grounding artifact; Codex (host) confirmed prune merged |

**Round 2 (rev 2 → rev 3):**
| Finding (sev) | Resolution |
|---|---|
| cross-process stale-attempt race still open (FATAL/blocking) | **Fork C2**: same-process currency guard now; cross-process deferred to a worktree-lifecycle advisory-lock lane; documented + not reachable in single-worker deployment |
| `cleanup_status` could lie after a real removal | Nit 1: helper owns fs disposition; recording is separate best-effort, never relabels |
| over-broad `except` hides bugs | Nit 2: narrowed boundaries + value-silent class-name logging |
| benign already-gone mislabeled `failed_preserved` | Nit 3: new `already_absent` label |
| "No `--force`, ever" over-claims (startup still force-removes) | Nit 4: narrowed to the cleanup path; startup force-remove documented pre-existing/out-of-scope |
| `--keep-worktree` won't retrofit an existing dispatch row | Documented caveat (enqueue conflict updates title only) |
| currency-guard DB read inside `_WORKTREE_LOCK` | Considered; not a defect (sub-second independent read, no deadlock) |

**Round 3 (rev 3 → rev 4):**
| Finding (sev) | Resolution |
|---|---|
| `already_absent + superseded` mislabeled by currency-before-isdir order (label-truth) | Reordered helper: `isdir`→`already_absent` **before** currency→`superseded_preserved`; fs truth first |
| "not reachable in single-worker" overclaims — reachable via concurrent same-`--dispatch-id` `review-run` reuse | Corrected Concurrency posture wording; reachable only via multi-worker **or** deliberate same-explicit-id reuse (normal review-run uses unique ids); both closed by the deferred lane |
| same-process guarantee mis-attributed to the currency check | Reworded: the safety barrier is `_WORKTREE_LOCK`; the currency check is a best-effort early-out |
| test matrix not exhaustive (set_run_artifacts-raise, already_absent+superseded, same-dispatch-id) | Added cases 6b, 8b, 13b |
| no-force wording; value-silence of class-name logging | **Confirmed closed** — cleanup remove is plain, test 4 scoped to cleanup; logs carry `type(e).__name__` only |

**Round 4 (rev 4 → rev 5):** Codex verdict — no fatal helper-order defect; guard reorder correct; cross-process scoping accurate; no regressions on any prior fix. Remaining (wording/test only):
| Finding (sev) | Resolution |
|---|---|
| rev-4 over-corrected: called the currency check "best-effort", not safety-critical | Reworded: same-process safety requires **both** `_WORKTREE_LOCK` (serializes) **and** the currency check under the lock (stops a stale cleanup acting on a newer already-added worktree) |
| `superseded_preserved` label wording asserted "newer attempt owns the path" (untrue when the newer attempt is blocked on the lock) | Reworded to "not the current attempt → left untouched (no status, no remove)" |
| test 5 didn't falsify the "superseded tree gets status/remove" regression | Added a `_git` spy asserting neither `status` nor `worktree remove` runs once superseded |
| test 8b would leave no prune candidate if the fake is pristine | 8b now uses a dirty (preserved) review |

## Verification

Host-only suite: `export PATH=$HOME/.local/bin:$PATH`; source canonical `infra/.env`; `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest`. Whole suite green (prune tests included) + new `test_review_autoclean.py`. The **spec-level Codex cross-engine gate is satisfied** (5 rounds, converged; rev-5 verdict: logic sound + holistic-clean). A fresh whole-branch Codex review runs on the **implementation** after the SDD build, per the prune-lane pattern.
