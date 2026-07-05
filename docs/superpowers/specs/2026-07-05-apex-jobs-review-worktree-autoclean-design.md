# apex-jobs Review-Worktree Auto-Clean Design

**Status:** rev 2 (cross-engine audit-hardened; forks A1 + B1 operator-ratified 2026-07-05). Rev 1 was found "not safe as written" by a dual-engine audit (Codex on host + IRP grounded probes); this rev folds all six required fixes. Not final until the rev-2 cross-engine pass is clean and the operator approves.

**Goal:** Stop `apex-jobs` review-runs from leaking detached worktrees at the source, by having `run_review_job` remove its own disposable worktree after a **pristine, succeeded, still-current** review — while never demoting a good review because housekeeping hiccuped, never deleting anything `prune-review-worktrees` would preserve, and leaving that verb as the durable backstop.

**Architecture:** A single, guarded, in-process cleanup step at the tail of `run_review_job`, gated on run success + a per-job opt-out (`payload.keep_worktree`) + an attempt-currency guard + a dirtiness pre-check whose definition is byte-identical to prune's. No DB schema change; no early `worktree_path` persistence. Disposition is recorded as an orthogonal, fixed-vocabulary label merged into the existing `jobs.run.result` JSONB.

**Tech stack:** Python 3, `psycopg` (host Postgres `jobs.*`), `git worktree` / `git status`, existing `agent_runner`/`engine`/`cli` modules in `packages/apex-jobs`.

---

## Context — the leak (grounded)

`run_review_job` (agent_runner.py:145) checks out `payload.review_head` **detached** at `~/.apex-jobs/runs/<dispatch_id>`, runs `codex exec review`, records findings to `jobs.run.result`, calls `engine.set_run_artifacts`, and returns. It is read-only (no commit, no diff, no promotion gate). Unlike `run_agent_job` (which opens a promotion gate whose resolution reclaims the worktree), a review opens no gate — so nothing ever reclaims its worktree and it accumulates under `~/.apex-jobs/runs/review-*`. The findings — the review's entire value — are durable in the run row; the worktree is disposable scratch. Both entry paths funnel through `run_review_job`: `review-run` (synchronous, cli.py:173) and `enqueue-review` (async → `run_pool → _run_one → run_review_job`, cli.py:157). Fixing the one function fixes both.

## Non-goals

- No DB schema change (`cleanup_status` merges into existing `jobs.run.result` JSONB).
- No early `worktree_path` persistence (prune keys on `dispatch_id`; the runner holds the path in-process).
- **No `--force`, ever.** Dirtiness is decided by an explicit pre-check, not by git's implicit refusal.
- No auto-clean of failed/timeout/errored reviews (preserved for diagnosis; reachable via `prune --include-failed`).
- No change to the merged `prune-review-worktrees` verb (Fork B1: `--keep-worktree` is not a prune-proof hold).
- The crash window is accepted; `prune-review-worktrees` is the durable backstop.

## Approved scope (rev-2 contract, verbatim)

1. Add explicit `git status --porcelain --ignored` pre-check before cleanup: empty -> plain `git worktree remove`; non-empty -> preserve as dirty; never use `--force`.
2. Add attempt-currency guard under `_WORKTREE_LOCK`: if a newer attempt exists for the same dispatch/job, skip cleanup as superseded; never remove a path that could belong to a newer live attempt.
3. Exception-isolate post-report cleanup: cleanup failure must not demote a successful review; record/report `cleanup_status` value-silently.
4. `--keep-worktree` plumbing on both `review-run` and `enqueue-review`; runner honors `payload.keep_worktree`; enqueue merge is **OR** semantics (the CLI flag can only add keep, never erase a payload keep).
5. Scope wording: the prune-backstop guarantee applies to default `review-<hex8>` dispatch IDs; custom/manual dispatch IDs are documented out of prune-backstop scope unless separately handled. In-process auto-clean may still use the exact path it created, subject to the same dirty/currency checks.
6. Test matrix (see below).

**Fork decisions:** A1 — preserve ignored-cache dirty trees (auto-clean's dirtiness definition is identical to prune's). B1 — `--keep-worktree` documents opt-out from auto-clean only, not permanent prune immunity.

**Load-bearing principle:** `cleanup_status` is **orthogonal** to run status. A cleanup/DB hiccup never demotes a good review; the review stays `succeeded`, carrying a `*_preserved` label so the leftover is visible and prune reclaims it.

---

## Design

### `cleanup_status` vocabulary (fixed; the only allowed values)

Recorded on **every** review run, merged into `jobs.run.result`. Exactly one of:

| `cleanup_status` | Meaning | Worktree | Run status |
|---|---|---|---|
| `not_attempted` | review not `succeeded` (failed / timeout / error) — cleanup never attempted | preserved | `failed` |
| `kept` | succeeded + `payload.keep_worktree` true (opt-out) | preserved | `succeeded` |
| `superseded_preserved` | succeeded, not kept, but a **newer attempt** owns the shared path (currency guard) | preserved | `succeeded` |
| `dirty_preserved` | succeeded, not kept, current, but `git status --porcelain --ignored` **non-empty** | preserved | `succeeded` |
| `cleaned` | succeeded, not kept, current, **pristine**, plain `git worktree remove` returned 0 | removed | `succeeded` |
| `failed_preserved` | succeeded, not kept, current, pristine, but remove returned non-zero **or** the tail raised / the dir was already gone (e.g. raced by an explicit prune) | preserved (or already gone) | `succeeded` |

All six are bare labels — value-silent, no paths/stderr/secrets. Only `cleaned` removes; every other outcome preserves (or the review failed). This is the complete, exhaustive disposition set; tests and operator output assert against exactly these strings.

### Decision flow — `run_review_job` tail (proposed)

The existing tail (`... = engine.report(...)` then `engine.set_run_artifacts(...)`) is replaced by an **exception-isolated** housekeeping block. Review success is committed by `report` **before** this block; nothing here can change it:

```python
result = {"findings": out[-8000:], "stderr": err[-4000:],
          "review_head": review_head, "base_ref": base_ref, "is_review": True}
status = engine.report(run_id, exit_code=rc, result=result)   # commits succeeded/failed + finished_at

# --- post-report housekeeping: ORTHOGONAL to review status; never demotes a good review ---
cleanup_status = "not_attempted"
try:
    engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)   # record where it ran, FIRST
    keep = bool((job.get("payload") or {}).get("keep_worktree"))
    if status != "succeeded":
        cleanup_status = "not_attempted"
    elif keep:
        cleanup_status = "kept"
    else:
        cleanup_status = _cleanup_review_worktree(repo, wt, run_id)   # guarded; see helper
    engine.set_run_cleanup(run_id, cleanup_status)
except Exception:
    # Housekeeping must NEVER demote a succeeded review. Swallow value-silently; best-effort
    # record 'failed_preserved'; the prune backstop reclaims any leftover.
    cleanup_status = "failed_preserved"
    try:
        engine.set_run_cleanup(run_id, "failed_preserved")
    except Exception:
        pass   # even the record failed; the run stays succeeded (report already committed)

return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
        "review_head": review_head, "findings_len": len(out),
        "cleanup_status": cleanup_status}
```

### The cleanup helper (agent_runner) — guarded, no `--force`

```python
def _cleanup_review_worktree(repo, wt, run_id):
    """Decide + apply cleanup for a SUCCEEDED, non-kept review worktree. Caller has already
    confirmed status=='succeeded' and keep is false. Runs under _WORKTREE_LOCK. Value-silent:
    returns a bare label, never a path or git stderr. Ordering of guards is load-bearing:
      1. currency  -> a newer attempt owns this shared path -> 'superseded_preserved' (touch nothing)
      2. dirtiness -> git status --porcelain --ignored non-empty -> 'dirty_preserved' (never remove)
      3. remove    -> plain `git worktree remove` (NEVER --force): rc 0 -> 'cleaned', else 'failed_preserved'
    """
    with _WORKTREE_LOCK:
        if not engine.run_is_current(run_id):
            return "superseded_preserved"
        if not os.path.isdir(wt):
            return "failed_preserved"                 # already gone (e.g. raced by explicit prune)
        st = _git("status", "--porcelain", "--ignored", cwd=wt, check=False)
        if st.returncode != 0:
            return "failed_preserved"                 # git error -> preserve, do not guess
        if st.stdout.strip():
            return "dirty_preserved"                  # ANY tracked/untracked/IGNORED content
        r = _git("worktree", "remove", wt, cwd=repo, check=False)   # plain, NEVER --force
        return "cleaned" if r.returncode == 0 else "failed_preserved"
```

- **Currency guard first** (Fix 2): if superseded, the path now hosts a newer attempt's checkout — we must not inspect-to-remove it. `_WORKTREE_LOCK` serializes in-process git plumbing; `run_is_current` is a committed-DB read, so it is correct across processes too (a newer attempt's `engine.start` has committed its run row). The pre-existing start-time `git worktree remove --force` that every attempt runs is unchanged and out of scope; this lane only guarantees a *stale* attempt's cleanup never removes a *newer* attempt's worktree.
- **Dirtiness = prune's definition** (Fix 1, Fork A1): `git status --porcelain --ignored` — identical to `prune._worktree_flags`. Non-empty (including ignored caches like `.pytest_cache/`, `__pycache__/`) -> preserve; we never call `remove` on a dirty tree, so git's `--force`-off ignored-file deletion can never fire. This closes the audit's convergent fatal (plain remove silently deletes ignored-only trees).
- **`git status` stderr/stdout paths are never surfaced** — only `returncode` and a `.strip()` emptiness test drive the label.

### `engine.run_is_current` (new — the currency guard)

```python
def run_is_current(run_id):
    """True if run_id is the highest-attempt run for its job (not superseded by a newer attempt).
    False if not found. Backs the auto-clean currency guard so a stale attempt never removes a
    newer live attempt's shared worktree path."""
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

Mirrors the existing `engine.reap()` JSONB-merge idiom (`result = coalesce(result,'{}'::jsonb) || jsonb_build_object('reaped', ...)`):

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

`jobs.run.result` is JSONB (confirmed: `002_jobs_tables.sql:38`; `Jsonb(result)` in `report`; `||` merge in `reap`). The shallow `||` merge replaces only the `cleanup_status` key and preserves `findings`/`stderr`/`review_head`/`base_ref`/`is_review` verbatim. `report` commits terminal status before this runs, so `reap` (which targets only `status='running'`) can never race it; even a hypothetical interleave merges disjoint keys.

### CLI — `--keep-worktree` on both entrypoints (Fix 4)

One signal, `payload.keep_worktree`; the runner reads only the payload, so sync/async collapse.

- **`enqueue-review`** (`cmd_enqueue_review`): add `--keep-worktree (store_true)`. **OR-merge** so the flag can only add keep, never erase an operator `--payload` opt-out:
  ```python
  payload["keep_worktree"] = bool(a.keep_worktree) or bool(payload.get("keep_worktree"))
  ```
- **`review-run`** (`cmd_review_run`): add `--keep-worktree (store_true)`; build `payload = {"review_head": a.review_head, "keep_worktree": bool(a.keep_worktree)}` (no `--payload` on this verb → no merge). Add `"cleanup_status": summary["cleanup_status"]` to the `--json` object.
- Help on both: `--keep-worktree  opt out of auto-cleanup at review completion (not a permanent hold; a later explicit prune may still reclaim a clean worktree)`.

---

## Spec must-answer (updated)

1. **Where recorded** — `jobs.run.result` JSONB under `cleanup_status` (via `engine.set_run_cleanup`, reap idiom; no column). Also in the `run_review_job` summary and `review-run --json`.
2. **Exit/status impact** — none. `report` commits status before the isolated housekeeping block; cleanup only writes `cleanup_status`. `review-run` still exits 0 on a succeeded review even if cleanup preserved/failed. Fix 3 guarantees this at the *process* layer: any exception in the tail is swallowed value-silently.
3. **In JSON/result** — the `cleanup_status` label (one of the six) in the summary, `review-run --json`, and `jobs.run.result`.
4. **Both entrypoints** — `--keep-worktree (store_true)` on both; `enqueue-review` OR-merges into `--payload`; `review-run` writes its literal payload; runner reads `(job.get('payload') or {}).get('keep_worktree')`.
5. **No-force / dirty proof** — an explicit `git status --porcelain --ignored` pre-check preserves on any dirt (tracked, untracked, **or ignored**) and the code path never reaches `remove` on a dirty tree; a spy test asserts `git worktree remove` is not invoked when the pre-check is non-empty, and no code path ever passes `--force`.

## Fork decisions (ratified)

- **A1** — ignored-cache dirt is preserved. Auto-clean's dirtiness definition equals prune's (`git status --porcelain --ignored`). Consequence: pristine successes are cleaned; cache-dirty successes (~2/6 observed on real worktrees) are `dirty_preserved` and fall to the explicit prune/cache-clean path. Accepted: the leak is *reduced*, not eliminated, and no worktree prune would protect is ever auto-deleted.
- **B1** — `--keep-worktree` opts out of auto-clean at review completion only. A `kept` worktree is clean, so a later *explicit* `prune-review-worktrees` may still reclaim it (prune has no visibility into `cleanup_status='kept'`). Documented in `--help`. Permanent holds, if ever needed, are a future prune-lane extension; this lane does not reopen prune.

## Scope wording — prune-backstop coverage (Fix 5)

The prune backstop guarantee (a leaked/kept/failed-preserved worktree is later reclaimable) applies to **default `review-<hex8>` dispatch IDs** — what `review-run` generates and what the leak actually produces. `prune-review-worktrees` enumerates only basenames matching `^review-[0-9a-f]{8}$`. Operator-supplied custom dispatch IDs (e.g. `enqueue-review --dispatch-id rv-1`) are **out of prune-backstop scope** unless separately handled; auto-clean still applies to them in-process (subject to the same dirty/currency guards), but a `dirty_preserved`/`kept`/`failed_preserved` leftover under a non-`review-<hex8>` id will not be enumerated by prune. Documented, not silently assumed.

## Test plan (host-only, `orchestration_test`, fake-agent seam)

Tests use `APEX_JOBS_AGENT_CMD` (JSON argv seam) against real `orchestration_test` with throwaway worktrees, same harness as `test_prune.py`. **Note:** the default review fake writes into cwd, so it naturally yields a *dirty* tree — the `cleaned` case needs an explicit pristine fake (writes nothing); the `dirty_preserved` cases inject the relevant file. Fakes run in `cwd=wt`:
- pristine: `["sh","-c","echo FINDINGS; exit 0"]`
- untracked dirt: `["sh","-c","echo x > untracked.txt; echo FINDINGS; exit 0"]`
- ignored dirt: `["sh","-c","mkdir -p __pycache__; echo x > __pycache__/x.pyc; echo FINDINGS; exit 0"]` (matches repo `.gitignore`)
- failure: `["sh","-c","exit 1"]`

| # | Test | Assert |
|---|---|---|
| 1 | pristine success -> cleaned | `cleanup_status=="cleaned"`; dir gone; absent from `git worktree list --porcelain` |
| 2 | ignored-only dirt -> preserved | `cleanup_status=="dirty_preserved"`; dir present; status `succeeded` |
| 3 | untracked non-ignored dirt -> preserved | `cleanup_status=="dirty_preserved"`; dir present; status `succeeded` |
| 4 | dirty pre-check prevents the remove call | spy on `agent_runner._git`: when `status --porcelain --ignored` is non-empty, no `("worktree","remove",...)` invocation occurs; no call ever contains `"--force"` |
| 5 | superseded attempt -> preserved | seed a newer run (higher attempt) for the job so `run_is_current` is False -> `cleanup_status=="superseded_preserved"`; dir present |
| 6 | cleanup DB/record failure -> review still succeeds | monkeypatch `engine.set_run_cleanup` to raise -> `run_review_job` returns status `succeeded`, `cleanup_status=="failed_preserved"`; `review-run` exits 0 |
| 7 | `--keep-worktree` -> preserved | succeeded + keep -> `cleanup_status=="kept"`; dir present |
| 8 | keep OR-merge (enqueue-review) | `--payload '{"keep_worktree":true}'` **without** the flag still yields `payload.keep_worktree==True` -> `kept`; flag-without-payload also `kept`; neither -> cleanup runs |
| 9 | failed review -> not_attempted | `cleanup_status=="not_attempted"`; dir present; run status `failed` |
| 10 | CLI flag on both entrypoints | argparse parses `--keep-worktree` for `review-run` and `enqueue-review`; `review-run --json` includes `cleanup_status` |
| 11 | concurrent/pool path | two reviews cleaning under `_WORKTREE_LOCK` via `run_pool` -> both terminate with valid labels; no `index.lock`/registry race |
| 12 | value-silence | printed/JSON/stored output is basenames/labels/counts only — no worktree paths beyond the pre-existing `worktree_path`, no file contents, no git stderr |
| 13 | existing prune tests still pass | `test_prune.py` unchanged and green (regression) |

## Value-silence

`cleanup_status` is one of six fixed labels. The helper inspects only `returncode`/emptiness and discards git stdout/stderr. `set_run_cleanup` binds a bare label. `review-run`/`enqueue-review` emit labels/counts/basenames only.

## Backstop relationship to prune-review-worktrees

Auto-clean removes only the pristine-success case; prune remains the durable backstop for exactly what this lane deliberately preserves — `dirty_preserved` (incl ignored caches, per A1), `kept` (per B1), `superseded_preserved`, `failed_preserved`, `not_attempted`, and the crash window — all under `review-<hex8>` ids. No change to the prune verb; its dirtiness definition and auto-clean's are now identical, so the two never disagree about what is safe to remove.

## Rev-2 audit resolution (dual-engine: Codex host + IRP grounded probes)

| Finding (severity) | Engine | Resolution |
|---|---|---|
| no-force remove silently deletes ignored-only trees / refuses on untracked -> goal defeated or inconsistent (FATAL, convergent) | Codex + 2 IRP probes | Fix 1: explicit `--ignored` pre-check == prune's; never remove a dirty tree; `dirty_preserved` label (A1) |
| stale attempt's cleanup removes a newer live attempt's shared worktree (FATAL) | Codex | Fix 2: currency guard (`run_is_current`) under lock; `superseded_preserved` |
| post-report cleanup/DB failure demotes review at the process/summary layer (important) | Codex + IRP | Fix 3: exception-isolate the whole post-report housekeeping block; review status from `report` only |
| `enqueue-review` flag overwrites an operator `--payload` keep=true (important) | Codex + IRP | Fix 4: OR-merge |
| prune regex `^review-[0-9a-f]{8}$` misses custom dispatch ids -> backstop gap (important) | Codex | Fix 5: narrow the backstop guarantee to `review-<hex8>`; document custom ids out of scope |
| `--keep-worktree` not durable vs a later prune (medium) | IRP | Fork B1: documented as auto-clean opt-out only |
| happy-path/`cleaned` test unachievable with the default (writing) fake; missing dirty/pool cases (medium) | IRP | Fix 6: rebuilt matrix — pristine fake for `cleaned`, injected files for `dirty_preserved`, pool + superseded + DB-fail cases |
| "prune verb does not exist" (HIGH) | IRP | **Discounted** — grounding artifact: those probes read stale *local* apex-jobs mirrors (pre-#68); Codex, on the host canonical off `30b4d1c5`, correctly grounded on the merged `prune.py`. (Process note, not a spec change: host-canonical IRP should run agents on the host.) |
| JSONB merge / lock non-reentrance / NULL-result / value-silence | both | **Confirmed safe** — no change needed |

## Verification

Host-only suite: `export PATH=$HOME/.local/bin:$PATH`; source canonical `infra/.env`; `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest`. Whole suite green (prune tests included) + new `test_review_autoclean.py`. **Rerun the cross-engine review on rev 2 before writing the plan** (operator-required).
