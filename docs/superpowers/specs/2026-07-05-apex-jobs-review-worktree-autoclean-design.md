# apex-jobs Review-Worktree Auto-Clean Design

**Status:** approved design (operator-ratified narrowed scope 2026-07-05); this document is the spec.

**Goal:** Stop `apex-jobs` review-runs from leaking detached worktrees at the source, by having `run_review_job` remove its own disposable worktree after a successful, clean review — while never demoting a good review because housekeeping hiccuped, and leaving the `prune-review-worktrees` verb as the durable backstop.

**Architecture:** A single in-process cleanup step inside `run_review_job`, gated on run success and a per-job opt-out (`payload.keep_worktree`). No DB schema change; no early `worktree_path` persistence (prune classification is keyed on `dispatch_id`, so a running review no longer needs its path in the DB). Cleanup status is recorded as an orthogonal label merged into the existing `jobs.run.result` JSONB.

**Tech stack:** Python 3, `psycopg` (host Postgres `jobs.*` schema), `git worktree`, existing `agent_runner`/`engine`/`cli` modules in `packages/apex-jobs`.

---

## Context — the leak (grounded)

`agent_runner.run_review_job` (packages/apex-jobs/src/apex_jobs/agent_runner.py:145) checks out `payload.review_head` **detached** at `~/.apex-jobs/runs/<dispatch_id>`, runs `codex exec review --base <base_ref>`, records findings to `jobs.run.result`, calls `engine.set_run_artifacts`, and returns. It is read-only: **no commit, no diff, no promotion gate.**

Contrast `run_agent_job` (agent_runner.py:86): on success it calls `engine.open_promotion(job_id)`, deliberately leaving its worktree intact — the promotion gate's later resolution is what reclaims that worktree. A review has nothing to merge, so it opens no gate — and therefore **nothing ever reclaims its worktree.** It accumulates under `~/.apex-jobs/runs/review-*` forever. That is the entire leak. The review's value (the findings) is already durable in the `jobs.run` row; the worktree is pure disposable detached scratch the moment findings are recorded.

Both entry paths funnel through `run_review_job`:
- `review-run` (cli.py:173, `cmd_review_run`) — synchronous IRP front door; enqueues then runs in-process.
- `enqueue-review` (cli.py:157, `cmd_enqueue_review`) — async; a worker drains it later via `run_pool → _run_one → run_review_job`.

Fixing `run_review_job` fixes both.

## Non-goals

- **No DB schema change.** `cleanup_status` merges into the existing `jobs.run.result` JSONB.
- **No early `worktree_path` persistence.** The runner already holds the path in-process; prune keys on `dispatch_id`; adding an early write surfaces state with no consumer.
- **No `--force`, ever.** A clean review leaves a clean tree; if a tree is somehow dirty/locked, we preserve it and let prune/operator handle it.
- **No auto-clean of failed/timeout/errored reviews.** Failed artifacts are preserved for inspection (consistent with the prune lane's default) and remain reachable via `prune-review-worktrees --include-failed`.
- **The crash window is accepted.** A crash between `report` and the removal leaks one worktree; `prune-review-worktrees` is the durable backstop (a succeeded-clean-not-active review classifies prunable).

## Approved scope (verbatim contract)

- No DB schema change. No early `worktree_path` persistence. Implement in-process cleanup only inside `run_review_job`.
- Add `--keep-worktree` to both `review-run` and `enqueue-review`, stored as `payload.keep_worktree`. The runner honors exactly that one payload flag.
- On `status == "succeeded"` and `keep_worktree` false: call `set_run_artifacts` first, then remove the detached review worktree; plain `git worktree remove`; never `--force`; hold `_WORKTREE_LOCK` for removal.
- On failed/timeout/error: preserve the worktree.
- On dirty/locked/remove-failed: preserve the worktree; report cleanup failure honestly in the run result; do **not** turn the review into succeeded-clean if cleanup failed silently.
- Crash window accepted; `prune-review-worktrees` remains the durable backstop.

**Load-bearing principle (operator caution):** cleanup status is **orthogonal** to review status. A cleanup failure must never demote a good review. The review stays `succeeded`; it carries `cleanup_status=failed` so the failure is visible and prune can catch the leftover later.

---

## Design

### cleanup_status semantics

A single label recorded on every review run, merged into `jobs.run.result`. Four values, precedence top-to-bottom:

| `cleanup_status` | When | Worktree | Run status |
|---|---|---|---|
| `skipped` | review not `succeeded` (failed / timeout / error) | preserved | `failed` |
| `kept`    | succeeded **and** `payload.keep_worktree` true | preserved | `succeeded` |
| `cleaned` | succeeded, not kept, `git worktree remove` returned 0 | removed | `succeeded` |
| `failed`  | succeeded, not kept, removal returned non-zero (dirty/locked/any error) | preserved | `succeeded` |

`keep_worktree` only matters on success; a failed review is always `skipped` (preserved for inspection regardless of the flag). All four values are bare labels — value-silent, no paths or git stderr.

### run_review_job — end-of-function sequence (modified)

The existing tail:

```python
result = {"findings": out[-8000:], "stderr": err[-4000:],
          "review_head": review_head, "base_ref": base_ref, "is_review": True}
status = engine.report(run_id, exit_code=rc, result=result)
engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)
```

becomes:

```python
result = {"findings": out[-8000:], "stderr": err[-4000:],
          "review_head": review_head, "base_ref": base_ref, "is_review": True}
status = engine.report(run_id, exit_code=rc, result=result)
engine.set_run_artifacts(run_id, worktree_path=wt, branch=review_head)   # record where it ran, FIRST

keep = bool((job.get("payload") or {}).get("keep_worktree"))
if status != "succeeded":
    cleanup_status = "skipped"                       # preserve failed artifact for inspection
elif keep:
    cleanup_status = "kept"                           # operator opted out of cleanup
else:
    cleanup_status = _cleanup_review_worktree(repo, wt)   # "cleaned" | "failed"
engine.set_run_cleanup(run_id, cleanup_status)

return {"job": job["dispatch_id"], "run": str(run_id), "status": status,
        "review_head": review_head, "findings_len": len(out),
        "cleanup_status": cleanup_status}
```

`set_run_artifacts` still records the worktree path (historical: where the run ran) even when the directory is then removed — the run row stays accurate about what happened.

### The cleanup helper (agent_runner)

```python
def _cleanup_review_worktree(repo, wt):
    """Remove a succeeded review's detached worktree with plain `git worktree remove`
    (never --force). Returns "cleaned" if git removed it, "failed" otherwise (dirty,
    locked, or any non-zero) -- in which case the worktree is left in place for
    `prune-review-worktrees` to catch later. Value-silent: returns a bare label,
    never a path or git stderr. Acquires _WORKTREE_LOCK (non-reentrant; the worktree
    add earlier in run_review_job has already released it)."""
    with _WORKTREE_LOCK:
        r = _git("worktree", "remove", wt, cwd=repo, check=False)
    return "cleaned" if r.returncode == 0 else "failed"
```

- Plain `git worktree remove` — **no `--force`**. Git refuses on a dirty tree or one with untracked files, which is exactly the safety we want: a hiccup preserves the tree.
- Non-zero → `"failed"`; the git stderr is discarded (never surfaced) to stay value-silent.
- `_WORKTREE_LOCK` is the same lock `run_agent_job`/`run_review_job` use for worktree add; the add-block released it before the subprocess ran, so re-acquiring here does not deadlock.

### engine.set_run_cleanup (new — no schema change)

Mirrors the existing `engine.reap()` JSONB-merge idiom (`result = coalesce(result,'{}'::jsonb) || jsonb_build_object('reaped', ...)`):

```python
def set_run_cleanup(run_id, cleanup_status):
    """Merge cleanup_status into the run's result JSONB (no schema change). Records
    whether the review's disposable worktree was cleaned/kept/skipped/failed --
    ORTHOGONAL to the review's own succeeded/failed status; this never changes the
    run's status or the process exit code."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set result = coalesce(result, '{}'::jsonb) "
                "|| jsonb_build_object('cleanup_status', %s::text) where id=%s",
                (cleanup_status, run_id),
            )
        conn.commit()
```

`jobs.run.result` is JSONB (proven by `Jsonb(result)` in `engine.report` and the `|| jsonb_build_object` merge in `engine.reap`). The merge is order-independent with the `findings` written by `report`.

### CLI — `--keep-worktree` on both entrypoints

One signal, `payload.keep_worktree`; the sync/async distinction disappears because the runner reads only the payload.

**`enqueue-review`** (`cmd_enqueue_review`, cli.py:157): add `er.add_argument("--keep-worktree", action="store_true", dest="keep_worktree")`; set `payload["keep_worktree"] = a.keep_worktree`. The flag persists on the enqueued job row; the worker honors it at drain time.

**`review-run`** (`cmd_review_run`, cli.py:173): add `rr.add_argument("--keep-worktree", action="store_true", dest="keep_worktree")`; build `payload = {"review_head": a.review_head, "keep_worktree": a.keep_worktree}`; enqueue with that payload, then run in-process (the same run_review_job reads the same payload).

Help text on both: `--keep-worktree  preserve the review worktree instead of auto-removing it on success`.

**JSON / result output (Q3).** Three surfaces carry `cleanup_status`, all bare labels:
- `run_review_job` return summary dict → `cleanup_status`.
- `cmd_review_run --json` → add `"cleanup_status": summary["cleanup_status"]` to the printed object.
- `jobs.run.result` JSONB → `cleanup_status` (so `apex-jobs review <id>`, which prints `result=`, shows it with no code change).

The `keep` intent is fully encoded by `cleanup_status == "kept"`; no separate flag echo is needed.

---

## Spec must-answer (explicit)

1. **Where cleanup status is recorded.** In `jobs.run.result` JSONB under key `cleanup_status`, merged via `engine.set_run_cleanup` (same idiom as `engine.reap`'s `reaped` key). No new column. Also surfaced in the `run_review_job` return summary and `review-run --json`.
2. **Does cleanup failure change process exit / run status?** **No.** It changes only `cleanup_status`. Run status stays `succeeded`; `review-run` still exits 0 on a succeeded review even if `cleanup_status=failed`. `report` (which sets run status + exit-derived status) runs before cleanup and is never revisited by cleanup. Rationale: review success == findings produced; housekeeping is orthogonal; the leftover is visible via `cleanup_status` and reclaimable via prune.
3. **How `--keep-worktree` appears in JSON/result.** As `cleanup_status` (`kept` when set) in: the `run_review_job` summary, `review-run --json`, and `jobs.run.result`. Bare label; value-silent.
4. **How sync and async both set `payload.keep_worktree`.** Both CLI verbs expose `--keep-worktree (store_true)` and write `payload["keep_worktree"]`. `review-run` sets it on the payload it enqueues-then-runs; `enqueue-review` sets it on the payload it persists for the worker. `run_review_job` reads exactly `(job.get("payload") or {}).get("keep_worktree")` — one place, both paths.
5. **How tests prove no `--force` and dirty preservation.** A succeeded-but-dirty review (fake agent writes an untracked file, exits 0) → plain `git worktree remove` refuses → `cleanup_status=failed`, directory still present. Had we used `--force`, the dirty tree would be removed; its preservation *is* the proof. Belt: a direct assertion that the removal argv contains no `"--force"`.

---

## Test plan (host-only, `orchestration_test`, fake-agent seam)

All tests use `APEX_JOBS_AGENT_CMD` (a JSON argv seam) so no real codex runs, against real `orchestration_test`, with throwaway worktrees — same harness as `test_prune.py`. Fake commands run in `cwd=wt`:
- clean success: `["sh","-c","echo FINDINGS; exit 0"]` (writes nothing → tree clean)
- dirty success: `["sh","-c","echo dirt > untracked.txt; exit 0"]` (untracked file → remove refuses)
- failure: `["sh","-c","exit 1"]`

| # | Test | Assert |
|---|---|---|
| 1 | succeeded clean review → removed | `cleanup_status=="cleaned"`; worktree dir gone; not in `git worktree list --porcelain` |
| 2 | succeeded + `keep_worktree` → preserved | `cleanup_status=="kept"`; dir present |
| 3 | failed review → preserved | `cleanup_status=="skipped"`; dir present; run status `failed` |
| 4 | dirty successful review → preserved, no force | `cleanup_status=="failed"`; dir present; run status stays `succeeded` |
| 5 | generic remove-failure → preserved + reported | monkeypatch `agent_runner._git` so `("worktree","remove",...)` returns rc=1; `cleanup_status=="failed"`; dir present; status `succeeded` |
| 6 | CLI flag on both entrypoints | argparse parses `--keep-worktree` for `review-run` and `enqueue-review`; each sets `payload["keep_worktree"]=True` |
| 7 | `keep_worktree` false/missing → cleanup | payload without the key, and with `False`, both → `cleanup_status=="cleaned"`, dir gone |
| 8 | cleanup failure does not demote run | run status `succeeded` and exit path unchanged while `cleanup_status=="failed"` (folds into #4/#5 asserts) |
| 9 | no-force belt | removal `_git` call args never contain `"--force"` |
| 10 | async path honors keep | `enqueue-review --keep-worktree` → payload persisted → drained via `run_pool`/`_run_one` → `cleanup_status=="kept"`, dir present |
| 11 | summary + `--json` carry cleanup_status | `run_review_job` return dict and `review-run --json` include `cleanup_status` |
| 12 | value-silent output | printed/JSON output contains only basenames/status/labels/counts — no worktree paths, no file contents, no git stderr |
| 13 | existing prune tests still pass | `test_prune.py` unchanged and green (regression) |

## Value-silence

`cleanup_status` is one of four fixed labels. The cleanup helper discards git stderr. No worktree path, file content, DSN, env, or psycopg string is ever printed or stored by this lane. `review-run`/`enqueue-review` output remains basenames/labels/counts only.

## Backstop relationship to prune-review-worktrees

Auto-clean handles the happy path (succeeded + clean, ~99%). `prune-review-worktrees` remains the durable backstop for exactly the residue this lane deliberately leaves: the crash window (removal never reached), `--keep-worktree` runs the operator later abandons, and `cleanup_status=failed` leftovers. Those all classify `prunable` (succeeded, clean, not-active) or are preserved (dirty/failed) under the existing safety rules — no change to the prune verb.

## Verification

Host-only suite (no GitHub CI): `export PATH=$HOME/.local/bin:$PATH`; source canonical `infra/.env`; `APEX_JOBS_DB=orchestration_test uv run --with 'psycopg[binary]' --with pytest --with-editable . pytest`. Whole suite must stay green (prune tests included) plus the new `test_review_autoclean.py`. Cross-engine Codex whole-branch review before finishing, per the prune-lane pattern.
