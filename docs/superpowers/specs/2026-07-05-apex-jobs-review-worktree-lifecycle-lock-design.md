# apex-jobs review worktree lifecycle advisory-lock -- design

- **Lane:** orchestration/review-worktree-lifecycle-lock (deferred C2 follow-on from PR #68 prune + PR #69 auto-clean)
- **Base:** main @ 14f70c7b (PR #69 merged)
- **Worktree (host-canonical):** /home/olares/code/apex/apex-review-wtlock
- **Status:** DRAFT rev 1 -- no implementation has begun (spec only)
- **Date:** 2026-07-05

## 1. Problem

Every mutation of a review worktree is keyed on one path, `~/.apex-jobs/runs/<dispatch_id>`, and touched at three sites:

| Site | Location | Operation | Guard today |
| --- | --- | --- | --- |
| Startup | `agent_runner.run_review_job` (~L186) | `git worktree remove --force` then `add --detach` | `_WORKTREE_LOCK` (process-local) |
| Auto-clean | `agent_runner._cleanup_review_worktree` (~L157) | plain `git worktree remove` (never `--force`) | `_WORKTREE_LOCK` + currency + dirty guards |
| Prune `--apply` | `prune.prune_review_worktrees` (~L214) | plain `git worktree remove` (never `--force`) | `_WORKTREE_LOCK` + recheck-before-remove |

`_WORKTREE_LOCK` is a `threading.Lock()` -- **process-local**. It fully serializes those three sites only within one OS process (one `run_pool`). Across processes it does nothing.

### 1.1 The reachable defect

`engine.start()` has **no guard against opening a second concurrent run** for a job that already has a live run: it inserts `attempt = max(attempt)+1` and flips the job to `running` unconditionally. Combined with a **reused `dispatch_id`** (`enqueue-review --dispatch-id` is *required*; `review-run --dispatch-id` is accepted), two processes can review into the **same path**. Process B's startup `git worktree remove --force` then **deletes process A's live checkout out from under its running `codex`**. The `--force` is what makes the collision destructive (it deletes even a dirty tree).

Reviews are enqueued with `max_attempts=1`, so this is *not* a reap/lease race (reap marks a `max_attempts=1` job `failed`, never `pending`, so there is no reclaim). It is a **same-dispatch concurrent-invocation** race: two `review-run --dispatch-id <same>` calls, or a `review-run` racing a worker draining an `enqueue-review` of the same dispatch id.

### 1.2 Minor label race (also closed by this lane)

A `prune --apply` landing in the auto-clean tail window (the run is already `succeeded` but the tree is not yet removed) double-removes the same clean path -> a misleading `remove-failed` / `failed_preserved` label. No data loss, but label-fog.

## 2. Goals / Non-goals

### Goals
- Prevent concurrent review runners from unsafely creating / removing / reusing the same detached review worktree.
- Close the pre-existing startup `git worktree remove --force` cross-process race (make `--force` provably safe rather than removing it).
- Establish full-attempt **path ownership**: one dispatch, one live owner, one path.
- Preserve prune + auto-clean semantics exactly (labels, exit codes, dirty/currency guards, fail-closed-on-DbUnreachable).
- Value-silent throughout.

### Non-goals
- No DB schema change / DDL / new column / new table (advisory locks are transient runtime state).
- No production DB mutation.
- No advisory lock on `run_agent_job` in this lane (see Section 10 -- named follow-on).
- No rewrite of `engine.start()`'s general contract (the lock is the scoped remedy; hardening start() is out of scope).
- No unrelated apex-jobs refactors.

## 3. Threat model

| # | Scenario | Today | With this lane |
| --- | --- | --- | --- |
| T1 | Two `review-run --dispatch-id X` in two processes | B's startup `--force` deletes A's live tree | B's `try_lock` fails -> B touches no tree; A survives |
| T2 | `review-run X` racing a worker draining `enqueue-review X` | same as T1 | same as T1 |
| T3 | `prune --apply` racing a live review on X | prune's DB recheck largely protects, but the auto-clean tail window can double-remove -> label fog (1.2) | prune's per-item `try_lock` fails -> preserve (`contended`); no double-remove |
| T4 | Crashed attempt leaves a dirty tree at path X | requeue-safe `--force` clears it (but `--force` is unconditional -> also a hazard for T1) | held lock proves the tree is dead residue -> `--force` is safe reclamation only |

Safety property established: **at most one live process may create/remove/rely-on the worktree at `runs/<dispatch_id>` at any time.** A process-local mutex cannot express cross-process mutual exclusion; a Postgres session advisory lock keyed on `dispatch_id` can.

## 4. Design

### 4.1 Lock spine (ratified)

A **Postgres session advisory lock, keyed on `dispatch_id`, held for the full review attempt.** Acquired non-blocking at startup before any worktree op; held through checkout, `codex` execution, artifact recording, and auto-clean; released after terminal handling. A dedicated connection makes the session-lock lifetime explicit. Crash / kill drops the session and Postgres auto-releases the lock -- so safety does **not** depend on lease timing. Rejected alternatives (documented for the record): transaction-scoped locks at mutation points only (do not establish full-attempt ownership; lean on DB-row/lease interpretation) and OS `flock` (a second coordination substrate that composes worse with the DB-backed job model).

### 4.2 Lock key

Two-int namespaced form:

```
pg_try_advisory_lock(_NS, hashtext(dispatch_id))
```

`_NS` is a fixed module constant namespace so we never collide with any other advisory-lock user on the cluster. Recommended value: `_REVIEW_WT_LOCK_NS = 0x52565754` (1381193044, ASCII "RVWT" = review worktree), documented in code. `hashtext` returns int4; collisions across the small set of live `review-XXXXXXXX` ids are negligible, and a collision only produces a *spurious contention* (safe-fail, never an unsafe removal).

### 4.3 New engine surface (no schema)

```python
class LockUnavailable(Exception):
    """The advisory-lock connection could not be established (DB transport
    failure). Value-silent: carries NO underlying psycopg text (which can embed
    host/port/user). Callers treat it as 'cannot establish ownership'."""

_REVIEW_WT_LOCK_NS = 0x52565754  # ASCII 'RVWT'; fixed namespace, documented provenance

@contextmanager
def review_worktree_lock(dispatch_id):
    """Cross-process ownership of runs/<dispatch_id>. Opens a DEDICATED
    autocommit connection and takes a SESSION advisory lock
    pg_try_advisory_lock(_REVIEW_WT_LOCK_NS, hashtext(dispatch_id)) (non-blocking).
    Yields the acquired bool. On exit: pg_advisory_unlock (if acquired) then close.
    Crash/kill drops the session -> Postgres auto-releases (safety independent of
    lease timing). Autocommit so no idle-in-transaction connection lingers across a
    long review. Value-silent: a connect/transport failure raises LockUnavailable
    (no DSN/stderr); it does NOT leak as a generic exception string."""
    try:
        conn = _conn()            # autocommit=True on this connection
    except (psycopg.OperationalError, psycopg.InterfaceError):
        raise LockUnavailable()
    acquired = False
    try:
        with conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok",
                        (_REVIEW_WT_LOCK_NS, dispatch_id))
            acquired = bool(cur.fetchone()["ok"])
        yield acquired
    finally:
        try:
            if acquired:
                with conn.cursor() as cur:
                    cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                                (_REVIEW_WT_LOCK_NS, dispatch_id))
        finally:
            conn.close()
```

Session (not transaction) advisory locks are not released by commit/rollback -- only by explicit `pg_advisory_unlock` or session end. The dedicated connection is autocommit so nothing holds an open transaction across the review.

### 4.4 Runner control flow (`run_review_job`)

The lock is acquired **immediately after `engine.start()`** (which opens the run and enforces the env/approval gates) and **before any worktree op**. This ordering guarantees a contended attempt always resolves its run to a terminal state (no stranded `claimed`/`running` job) while still never touching a tree.

```python
def run_review_job(job, env, as_="cc", agent_cmd=None):
    repo, runs = _repo(), _runs_dir()
    run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # GateError propagates unchanged
    dispatch_id = job["dispatch_id"]
    review_head = (job.get("payload") or {}).get("review_head") or "HEAD"
    base_ref = ...   # as today
    try:
        with engine.review_worktree_lock(dispatch_id) as held:
            if not held:
                # another LIVE process owns runs/<dispatch_id>; touch NO tree
                engine.report(run_id, exit_code=_CONTENDED_RC, result={
                    "review_head": review_head, "base_ref": base_ref,
                    "is_review": True, "contended": True})
                return {"job": dispatch_id, "run": str(run_id), "status": "failed",
                        "review_head": review_head, "findings_len": 0,
                        "contended": True, "cleanup_status": "not_attempted"}
            # HELD: sole live owner -> startup --force reclaims dead residue safely
            #   ... existing body verbatim: worktree remove --force + add --detach,
            #       heartbeat, codex subprocess, result, engine.report,
            #       set_run_artifacts (best-effort), auto-clean helper ...
            return {... existing succeeded/failed summary incl cleanup_status ...}
    except engine.LockUnavailable:
        # cannot establish ownership (DB transport blip) -> do NOT touch the tree
        engine.report(run_id, exit_code=_CONTENDED_RC, result={
            "review_head": review_head, "base_ref": base_ref,
            "is_review": True, "contended": True})
        return {"job": dispatch_id, "run": str(run_id), "status": "failed",
                "review_head": review_head, "findings_len": 0,
                "contended": True, "cleanup_status": "not_attempted"}
```

- `_CONTENDED_RC = 75` (EX_TEMPFAIL -- a non-zero exit so `engine.report` records `failed`; the `contended: True` result key is the real signal). A contended attempt is **not** auto-requeued (avoids spin; the other live attempt is the real one).
- `engine.start()` stays **outside** the `try`, so a `GateError` (env/approval) propagates exactly as today (the worker maps it to `gated`), and no lock is taken.

### 4.5 Startup `--force` (ratified F1)

The existing startup `git worktree remove --force` is **retained but reached only while holding the dispatch lock.** Once the lock is held, no live process can own that path, so any tree there is dead residue from a terminated prior attempt; forcing its removal is safe reclamation and avoids wedging the dispatch forever on crashed dirty residue. **Rule: `--force` is permitted only for lock-held startup reclamation -- never in auto-clean or prune** (those stay plain-remove, no `--force`, unchanged). The code line does not change; its safety invariant is now established by the enclosing lock. An in-code comment records the invariant.

### 4.6 Prune integration (ratified F2)

Each per-item apply wraps its recheck+remove in the dispatch lock:

```python
if apply:
    for w in items:
        if w.classification != "prunable":
            continue
        try:
            with engine.review_worktree_lock(w.dispatch_id) as held:
                if not held:
                    w.classification, w.action = "contended", "preserved"
                    continue
                with agent_runner._WORKTREE_LOCK:
                    ... existing recheck-before-remove + plain remove verbatim ...
        except engine.LockUnavailable:
            return _refusal(items, "db-unreachable", applied=True,
                            remove_failed=remove_failed)
```

- New classification **`contended`** (`action=preserved`) -- distinct from `active` (DB `any_running`-derived) and `locked` (git worktree-locked). It means "a live review currently owns this dispatch." Added to the `ReviewWorktree.classification` comment enum; set only in the apply loop (like the existing `remove-failed`), never by `_classify_one` (which stays pure DB+fs). It flows into `_counts` naturally and is value-silent.
- `LockUnavailable` maps to the existing `db-unreachable` refusal (partial-apply -> `applied=True`), consistent with prune's current fail-closed posture.
- The dispatch advisory lock is taken **outside** the process-local `_WORKTREE_LOCK` belt.
- Dry-run takes no lock (classification only), unchanged.

### 4.7 `--keep-worktree` interaction

Lock lifetime is independent of keep. `--keep-worktree` still only skips auto-clean (`cleanup_status="kept"`); the attempt releases the lock at terminal handling regardless, and the kept tree remains reclaimable by a later prune (which acquires the now-free lock and, if the tree is succeeded+clean+not-active, removes it). B1 semantics ("keep = auto-clean opt-out only") are preserved.

### 4.8 CLI / JSON surfacing

`review-run` contended -> the run is `failed`, so the existing exit contract yields exit `3`; `--json` gains `"contended": true` so a contended bail is distinguishable from a genuine review failure. No new exit code (keeps the CLI contract stable).

### 4.9 `_WORKTREE_LOCK` retained

The process-local `_WORKTREE_LOCK` stays as an intra-process belt (cheap, prevents same-process thread interleave), but it is **not** the safety mechanism. The dispatch advisory lock is.

## 5. Concurrency posture

Safe for the current single-worker dev deployment **and** for multi-process operation: the dispatch-keyed session advisory lock is a true cross-process mutual exclusion. Crash semantics are correct by construction -- a dead holder's session drops and Postgres releases the lock, so a legitimate later attempt proceeds; a live-but-slow holder keeps the lock, so a competitor safely bails. This is strictly stronger than the lease/reap heuristic and does not replace it (the lease still governs crash-recovery of the run ledger via `reap`).

## 6. The operator's design questions -- answered

| Question | Answer |
| --- | --- |
| Postgres advisory, file lock, or both? | Postgres session advisory lock. (flock rejected: second substrate, composes worse.) |
| Lock key? | `dispatch_id` (the worktree identity), via `pg_try_advisory_lock(_NS, hashtext(dispatch_id))`. |
| Cover checkout / execution / cleanup / prune, or only mutation points? | Full attempt: startup checkout through codex execution, artifact recording, and auto-clean; prune wraps its per-item recheck+remove. |
| Interaction with `--keep-worktree`? | Orthogonal; keep still only skips auto-clean; lock released at terminal handling either way (4.7). |
| Lock acquisition fails / times out? | Non-blocking `try_lock`; clean `False` -> contended (runner bails / prune preserves as `contended`); connect failure -> `LockUnavailable` -> runner bails, prune maps to `db-unreachable` refusal. No timeout (non-blocking). |
| What tests prove stale/concurrent runners cannot remove/overwrite another active review worktree? | Section 9 (R1, P1, E2, E3 in particular). |

## 7. Ratified forks

- **F1 -- startup `--force`:** keep it, permitted only while holding the dispatch lock (dead-residue reclamation); never in auto-clean or prune.
- **F2 -- prune contention label:** new `contended` classification (`action=preserved`); do not reuse `locked`.
- **F3 -- scope:** review worktrees only this lane; `run_agent_job` parity documented as a named follow-on (Section 10).

## 8. Migration / schema impact

**None.** Advisory locks are transient runtime constructs. No DDL, no new column, no new table, no prod DB mutation. The only DB surface is `pg_try_advisory_lock` / `pg_advisory_unlock` calls.

## 9. Test matrix (real `orchestration_test` DB)

Engine (`review_worktree_lock`):
- **E1** acquire on a free dispatch -> `held=True`; releases on `with`-exit (a second acquire afterward succeeds).
- **E2** two overlapping contexts, same dispatch, **distinct connections** -> first `True`, second `False` (exercises the real advisory lock).
- **E3** crash-release: acquire on raw conn A, **close A**, then acquire on conn B -> `True` (proves session-drop auto-release; the core safety guarantee).
- **E4** distinct dispatch_ids -> both `True` concurrently (distinct keys, no false contention).
- **E5** value-silence: `_conn()` raising `OperationalError` -> `LockUnavailable` with no underlying text.

Runner (`run_review_job`):
- **R1** contended startup (competitor holds the same dispatch) -> touches **no** tree (git spy asserts no `worktree remove`/`add`), opens the run, reports `failed` + `contended:true`, returns `cleanup_status="not_attempted"`.
- **R2** happy path unchanged (no competitor) -> full review runs, worktree created then auto-cleaned, `cleanup_status="cleaned"` (lock transparent; existing behavior preserved).
- **R3** startup `--force` fires **only** under the held lock, and never on the contended path (spy on the `--force` remove).
- **R4** `LockUnavailable` in the runner -> no tree touched, run reported `failed` + `contended:true`.

Prune:
- **P1** `--apply` on a prunable dispatch whose lock is **held** by a competitor -> classification `contended`, action `preserved`, **not** removed.
- **P2** same, after the competitor releases -> `removed`.
- **P3** `LockUnavailable` mid-apply -> `db-unreachable` refusal (`applied` reflects the partial).
- **P4** dry-run takes no lock (classification only), unaffected.

Regression:
- **G1** full apex-jobs suite green (>= 142); `test_prune.py` byte-unchanged; auto-clean labels + exit codes byte-stable.

## 10. Deferred hardening / named follow-on

**apex-jobs agent-job worktree lifecycle lock lane.** `run_agent_job` has the structurally identical startup `--force` race for `job/<dispatch_id>` worktrees (same missing `start()` guard, same reused-path exposure). It is **not** fixed here because agent jobs intentionally **preserve** their worktree for a promotion gate -- so the lock boundary cannot simply span "until cleanup" as it does for reviews; the held-until-promoted (or held-until-discarded) lifetime needs its own design pass. Tracked as a named future lane, not urgent under the single-worker dev deployment.

Side benefit already captured here: the minor prune-vs-auto-clean tail label race (1.2) is closed, because auto-clean holds the dispatch lock through cleanup and a concurrent prune's per-item `try_lock` contends -> preserves.

## 11. Success criteria

1. `engine.review_worktree_lock` exists, is dispatch-keyed, non-blocking, session-scoped, autocommit, value-silent, and auto-releases on session drop (E1-E5 green).
2. `run_review_job` acquires after `start()` and before any worktree op, bails value-silently on contention/`LockUnavailable` without touching the tree, and holds the lock through auto-clean (R1-R4 green).
3. Startup `--force` is reached only under the held lock; auto-clean and prune remain `--force`-free (R3 green).
4. `prune --apply` preserves a lock-contended dispatch as `contended` and removes it once free (P1-P2 green); fail-closed unchanged (P3).
5. Zero schema change; no prod DB mutation.
6. All existing behavior preserved: `test_prune.py` byte-unchanged, auto-clean labels/exit-codes stable, full suite green (G1).
7. `run_agent_job` parity documented as a named follow-on (Section 10).

## 12. Statement

No implementation has begun. This document is the design only. Implementation follows an SDD plan (writing-plans) after this spec passes an IRP grounded-audit + mandatory Codex cross-engine review and the operator's spec-review gate.
