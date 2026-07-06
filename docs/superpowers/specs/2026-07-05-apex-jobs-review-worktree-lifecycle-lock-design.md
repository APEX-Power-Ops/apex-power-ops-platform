# apex-jobs review worktree lifecycle lock -- design

- **Lane:** orchestration/review-worktree-lifecycle-lock (deferred C2 follow-on from PR #68 prune + PR #69 auto-clean)
- **Base:** main @ 14f70c7b (PR #69 merged)
- **Worktree (host-canonical):** /home/olares/code/apex/apex-review-wtlock
- **Status:** DRAFT rev 2 -- no implementation has begun (spec only). Rev 2 folds a cross-engine adversarial audit (5 Claude auditors + Codex): see Section 13.
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

Reviews are enqueued with `max_attempts=1`, so this is *not* a reap/lease race. It is a **same-dispatch concurrent-invocation** race: two `review-run --dispatch-id <same>` calls, or a `review-run` racing a worker draining an `enqueue-review` of the same dispatch id.

### 1.2 Minor label race (also closed by this lane)

A `prune --apply` landing in the auto-clean tail window (the run is already `succeeded` but the tree is not yet removed) double-removes the same clean path -> a misleading `remove-failed` / `failed_preserved` label. No data loss, but label-fog.

## 2. Goals / Non-goals

### Goals
- Prevent concurrent review runners from unsafely creating / removing / reusing the same detached review worktree.
- Make the startup `git worktree remove --force` **provably safe** -- reached only when the running process is the proven sole live owner of the path.
- Establish full-attempt **path ownership**: one dispatch, one live owner, one path.
- Preserve prune + auto-clean semantics exactly (labels, exit codes, dirty/currency guards, fail-closed-on-DbUnreachable).
- Value-silent throughout.

### Non-goals / boundary
- No DB schema change / DDL / new column / new table.
- No production DB mutation.
- **The `flock` liveness-fuse (Section 4.3b) is NOT a second coordination substrate.** Postgres remains the authoritative dispatch/worktree coordinator (ownership + queueing + prune-recheck composition). `flock` is a *local process-liveness fuse* consulted only around destructive filesystem operations. It never carries DB/job-status semantics and never replaces the PG lock.
- No advisory lock (PG or flock) on `run_agent_job` in this lane (Section 10 -- named follow-on).
- No rewrite of `engine.start()`'s general contract (the ledger fix is scoped to a new run-only finalizer; Section 4.4).
- No unrelated apex-jobs refactors.

## 3. Threat model

| # | Scenario | Today | With this lane |
| --- | --- | --- | --- |
| T1 | Two `review-run --dispatch-id X` in two processes | B's startup `--force` deletes A's live tree | B fails the PG lock (or the flock fuse) -> B touches no tree; A survives |
| T2 | `review-run X` racing a worker draining `enqueue-review X` | same as T1 | same as T1 |
| T3 | `prune --apply` racing a live review on X | prune's DB recheck largely protects, but the auto-clean tail window can double-remove -> label fog (1.2) | prune fails the flock fuse (a live runner holds it) -> preserve (`contended`); no double-remove |
| T4 | Crashed attempt leaves a dirty tree at path X | requeue-safe `--force` clears it (but `--force` is unconditional -> also a hazard for T1) | crash releases the flock (kernel) + the PG session -> a fresh attempt acquires both -> `--force` reclaims proven-dead residue |
| T5 | **A holds the PG lock, `codex` runs; A's lock CONNECTION drops (idle-session/TCP reset/PG restart) while A's PROCESS lives; B acquires the freed PG lock** | (rev-1 design flaw) B's startup `--force` deletes A's LIVE tree -- a PG session lock proves the *connection* is alive, not the *process* | A still holds the OS `flock` (kernel-released only on real process death). B passes the PG lock but **fails the flock fuse** -> B touches no tree; A's live tree survives |

Safety property (rev 2): **the destructive `--force` (and any worktree removal) is reached only by a process that holds BOTH the PG dispatch lock AND a fresh non-blocking `flock` on `runs/<dispatch_id>.lock`.** The PG lock is cross-process coordination; the `flock` is the process-liveness guarantee that a released lock corresponds to a genuinely dead holder. Neither a stale PG session nor a dropped lock connection can let a competitor delete a live tree.

## 4. Design

### 4.1 Coordinator + fuse

- **Postgres session advisory lock, keyed on `dispatch_id`** -- the authoritative cross-process COORDINATOR (ownership, queueing, prune-recheck composition). Non-blocking `pg_try_advisory_lock`; held for the full review attempt on a dedicated **autocommit** connection.
- **OS `flock` on `runs/<dispatch_id>.lock`** -- a narrow local **process-liveness fuse** (Section 4.3b). Held by the runner PROCESS for the full attempt; the kernel releases it ONLY on fd close / process death. It is *not* a coordinator: it is consulted only to answer "is a live local process still standing on this path?" immediately before a destructive removal.

Why both: a PG session lock is released the instant its *connection's backend* ends -- which can happen (idle-session / idle-in-transaction timeout, TCP reset, PG restart/failover) while the runner PROCESS and its `codex` subprocess keep running and still own the path (threat T5). The `flock` closes that gap because it is bound to the process, not a DB connection. Rejected alternatives: transaction-scoped PG locks at mutation points only (no full-attempt ownership); `flock`-only (loses the DB-centric prune composition and the cross-host-future property); PG-only (T5 unhandled).

### 4.2 PG lock key

Two-int namespaced form:

```
pg_try_advisory_lock(_REVIEW_WT_LOCK_NS, hashtext(dispatch_id))
```

`_REVIEW_WT_LOCK_NS = 0x52565754` (ASCII "RVWT" = review worktree), a fixed module constant so we never collide with any other advisory-lock user on the cluster. **ONE imported constant; no callsite ever transcribes a decimal literal** (rev-1 documented a wrong decimal; dropped -- see Section 13). A unit assertion pins `_REVIEW_WT_LOCK_NS == 0x52565754`. `hashtext` returns int4; a collision between two distinct live dispatch ids manifests only as a *spurious `contended` bail on an unrelated dispatch* (an availability degradation, safe for correctness -- over-exclusion never deletes a tree), not auto-requeued; negligible over the small live-id set.

### 4.3 New engine surface (no schema)

```python
class LockUnavailable(Exception):
    """The advisory-lock connection or acquire query hit a DB transport failure.
    Value-silent: carries NO underlying psycopg text (which can embed host/port/user).
    Callers treat it as 'cannot establish ownership'."""

_REVIEW_WT_LOCK_NS = 0x52565754  # ASCII 'RVWT'; fixed namespace, ONE imported constant

@contextmanager
def review_worktree_lock(dispatch_id):
    """Cross-process COORDINATOR for runs/<dispatch_id>. Dedicated AUTOCOMMIT connection;
    non-blocking session advisory lock. Yields the acquired bool. Value-silent: ANY
    transport failure at connect OR acquire raises LockUnavailable FROM NONE (severs the
    __context__ chain so no logger can print the DSN). The unlock in the finally is
    best-effort (a dropped session already released the lock) and never raises out of exit."""
    try:
        conn = _conn()
        conn.autocommit = True                       # explicit -- no idle-in-transaction hold
        with conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok",
                        (_REVIEW_WT_LOCK_NS, dispatch_id))
            acquired = bool(cur.fetchone()["ok"])
    except (psycopg.OperationalError, psycopg.InterfaceError):
        try: conn.close()
        except Exception: pass
        raise LockUnavailable() from None            # value-silent; no chained psycopg text
    try:
        yield acquired
    finally:
        try:
            if acquired:
                with conn.cursor() as cur:
                    cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                                (_REVIEW_WT_LOCK_NS, dispatch_id))
        except (psycopg.OperationalError, psycopg.InterfaceError):
            pass                                     # dead session already released; never mask a return
        finally:
            conn.close()

def report_run_only(run_id, exit_code, result=None):
    """Finalize ONLY the run row (status/finished_at/exit_code/result); do NOT propagate
    status to jobs.job. Used by the contended / fuse-failed / lock-lost paths so a LOSING
    attempt never last-writer-wins-demotes the real winner's job.status."""
    status = "succeeded" if exit_code == 0 else "failed"
    # UPDATE jobs.run SET status, finished_at=now(), exit_code, result WHERE id=%s   (NO jobs.job UPDATE)
    return status
```

- **autocommit is load-bearing** (rev-1 only commented it): with it, no implicit transaction wraps the multi-minute hold, so `idle_in_transaction_session_timeout` cannot fire. Requires a direct session (the canonical DSN is direct, not a transaction-mode pooler). Defense-in-depth: TCP keepalives + `idle_session_timeout=0` on the lock DSN; the `flock` fuse is the actual guarantee if the session drops anyway.
- The value-silent mapping now wraps the **whole acquire body** (connect + `execute` + `fetchone`), uses `raise ... from None`, and the unlock is guarded so a dead-connection unlock is a harmless no-op that never replaces a clean caller return with a raw leak.

### 4.3b The `flock` liveness fuse (`agent_runner`)

```python
import fcntl

@contextmanager
def _worktree_flock(runs, dispatch_id):
    """Local process-liveness FUSE (NOT a coordinator) for runs/<dispatch_id>. Opens the
    sibling lockfile runs/<dispatch_id>.lock and takes a NON-BLOCKING exclusive flock.
    Yields True if acquired (no live local runner holds the path), False if a live process
    holds it. The kernel releases an flock ONLY on fd close / process death -- so a released
    fuse ALWAYS means the holder is genuinely gone (this is what a PG session lock cannot
    promise). The lockfile is a sibling of the worktree dir (git never touches it) and is
    left in place; an unheld lockfile flocks fine, a stale 0-byte file is inert. Value-silent."""
    path = os.path.join(runs, dispatch_id + ".lock")
    os.makedirs(runs, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            acquired = False
        yield acquired
    finally:
        try:
            if acquired:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
```

- The lockfile basename `review-XXXXXXXX.lock` is not a git worktree and does not match prune's `^review-[0-9a-f]{8}$` worktree-basename filter, so it never interferes with enumeration.
- Lockfiles are **not unlinked** (avoids the classic flock+unlink inode race); a stale 0-byte lockfile flocks cleanly when unheld. Their accumulation in `runs/` is inert; an optional orphaned-lockfile sweep is a possible follow-on, out of scope here. POSIX-only (`fcntl`); apex-jobs + its test suite run on the Linux host.

### 4.4 Runner control flow (`run_review_job`)

Ordering (a single consistent global lock order -> no deadlock): **PG lock (coordinator) -> `flock` (fuse) -> `_WORKTREE_LOCK` (intra-process belt) around the git ops.** The PG lock is acquired after `engine.start()` (so `GateError` propagates unchanged); the `flock` is held for the full attempt (through `codex` + auto-clean).

```python
def run_review_job(job, env, as_="cc", agent_cmd=None):
    repo, runs = _repo(), _runs_dir()
    run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # GateError propagates
    dispatch_id = job["dispatch_id"]
    review_head, base_ref = ...                                     # as today

    def _contended():
        # LOSING attempt: finalize ONLY our own run; NEVER write job.status; touch NO tree.
        try: engine.report_run_only(run_id, _CONTENDED_RC,
                                    {"is_review": True, "contended": True,
                                     "review_head": review_head, "base_ref": base_ref})
        except Exception as e: log.warning("review contended report error: %s", type(e).__name__)
        return {"job": dispatch_id, "run": str(run_id), "status": "failed",
                "review_head": review_head, "findings_len": 0,
                "contended": True, "cleanup_status": "not_attempted"}
    try:
        with engine.review_worktree_lock(dispatch_id) as held:     # PG COORDINATOR
            if not held:
                return _contended()                                # another live owner holds the dispatch
            with _worktree_flock(runs, dispatch_id) as fuse_ok:    # PROCESS-LIVENESS FUSE (whole attempt)
                if not fuse_ok:
                    return _contended()                            # T5: a live local process still owns the path
                # BOTH held -> proven sole live owner -> startup --force reclaims proven-dead residue
                with _WORKTREE_LOCK:
                    _git("worktree","remove","--force", wt, cwd=repo, check=False)   # provably safe here ONLY
                    _git("worktree","add","--detach", wt, review_head, cwd=repo)
                ... heartbeat, codex, result, engine.report(run_id,...),
                    set_run_artifacts (best-effort), auto-clean helper ...           # lock+fuse held throughout
                return {... succeeded/failed summary incl cleanup_status ...}
    except engine.LockUnavailable:
        return _contended()                                        # cannot establish ownership; touch nothing
```

- `_CONTENDED_RC = 75` (EX_TEMPFAIL): `report_run_only` records the run `failed` **without** touching `jobs.job.status`, so a contended loser can never demote a genuinely-succeeded winner (fixes the ledger defect). The `contended: True` result key is the real signal. Not auto-requeued.
- All three losing paths (PG-not-held, fuse-not-ok, `LockUnavailable`) route through `_contended()`, whose `report_run_only` is itself wrapped (type-only log) so a real DB outage cannot re-raise; on a true outage the run is resolved by `reap` (lease + `LEASE_TTL_S`), not by report -- stated honestly (Section 6), since the heartbeat thread is not started on the contended path.

### 4.5 Startup `--force` (ratified F1, tightened by F4)

The startup `git worktree remove --force` is retained but reached **only inside the doubly-guarded branch: PG dispatch lock held AND `flock` fuse acquired.** In that branch the running process is the proven sole live owner, so any tree at the path is dead residue -- forcing its removal is safe reclamation and avoids wedging the dispatch on crashed dirty residue. **Rule: `--force` is permitted only when BOTH locks are held (lock-held startup reclamation) -- never in auto-clean or prune** (those stay plain-remove, no `--force`, unchanged). An in-code comment records the double-guard invariant.

### 4.6 Prune integration (ratified F2)

Each per-item apply requires BOTH the PG lock AND the `flock` fuse before its (plain, no-`--force`) remove:

```python
if apply:
    for w in items:
        if w.classification != "prunable": continue
        try:
            with engine.review_worktree_lock(w.dispatch_id) as held:
                if not held:
                    w.classification, w.action = "contended", "preserved"; continue
                with agent_runner._worktree_flock(runs, w.dispatch_id) as fuse_ok:
                    if not fuse_ok:
                        w.classification, w.action = "contended", "preserved"; continue   # live runner holds it
                    with agent_runner._WORKTREE_LOCK:
                        ... existing recheck-before-remove + plain remove verbatim ...
        except (engine.LockUnavailable, psycopg.OperationalError, psycopg.InterfaceError):
            return _refusal(items, "db-unreachable", applied=True, remove_failed=remove_failed)
```

- New classification **`contended`** (`action=preserved`) -- distinct from `active` (DB `any_running`-derived) and `locked` (git worktree-locked); set only in the apply loop (like `remove-failed`), never by `_classify_one`. Reached when EITHER the PG lock OR the flock fuse is held by a live runner. Value-silent; flows into `_counts` naturally.
- The `except` is broadened to `(LockUnavailable, OperationalError, InterfaceError)` -> the existing `db-unreachable` refusal (belt-and-suspenders even after the 4.3 acquire-path fix), so no psycopg exception can escape the apply loop fail-open.

### 4.7 `--keep-worktree` interaction

Lock + fuse lifetime are independent of keep. `--keep-worktree` still only skips auto-clean (`cleanup_status="kept"`); the attempt releases BOTH the PG lock and the `flock` at terminal handling regardless, and the kept tree remains reclaimable by a later prune (which acquires the now-free PG lock and flock and, if the tree is succeeded+clean+not-active, removes it). B1 semantics preserved.

### 4.8 CLI / JSON surfacing

`review-run` contended -> the run is `failed` (via `report_run_only`), so the existing exit contract yields exit `3`; `--json` gains `"contended": true` so a contended bail is distinguishable from a genuine review failure. No new exit code.

### 4.9 `_WORKTREE_LOCK` retained

Kept as the innermost intra-process belt around the git ops; **not** the safety mechanism.

### 4.10 Lock ordering / no deadlock

Global order is always **PG lock -> flock -> `_WORKTREE_LOCK`**, all acquired non-blocking except the short same-process `_WORKTREE_LOCK`. No two code paths acquire in the opposite order, so no deadlock cycle. Auto-clean and prune both nest `_WORKTREE_LOCK` innermost, consistent with the runner.

## 5. Concurrency posture

Safe for the current single-worker dev deployment AND for multi-process operation. The PG session lock coordinates dispatch ownership; the `flock` fuse guarantees that a released lock corresponds to a genuinely dead holder. Crash: process death releases BOTH (kernel flock + PG session) -> a legitimate later attempt reclaims. Live-but-slow holder: keeps both -> a competitor bails. **Lock-connection loss without process death (T5): PG frees its lock, but the process still holds the flock, so a competitor passes the PG lock yet fails the fuse and touches nothing.** The safety property holds *given the fuse is honored at every destructive op* -- which the design enforces at startup `--force` (4.5) and in prune (4.6). Optional future defense-in-depth (not required for safety, out of scope here): a heartbeat `SELECT 1` on the lock connection to fail the runner's own attempt loudly if it detects lock-connection loss.

## 6. The operator's design questions -- answered

| Question | Answer |
| --- | --- |
| Postgres advisory, file lock, or both? | Both, with distinct roles: PG session lock = cross-process COORDINATOR; `flock` = local process-liveness FUSE around destructive ops. |
| Lock key? | `dispatch_id` for both: `pg_try_advisory_lock(_NS, hashtext(dispatch_id))` and `runs/<dispatch_id>.lock`. |
| Cover checkout / execution / cleanup / prune, or only mutation points? | Full attempt: PG lock + flock held from startup checkout through `codex`, artifact recording, and auto-clean; prune requires both before its remove. |
| Interaction with `--keep-worktree`? | Orthogonal; keep still only skips auto-clean; both locks released at terminal handling (4.7). |
| Lock acquisition fails / times out? | Non-blocking. PG `False` or flock `False` -> `contended` (runner `report_run_only`; prune preserves `contended`). Connect/acquire transport failure -> `LockUnavailable` -> runner contended, prune `db-unreachable` refusal. No timeout. |
| Contended path corrupting the job ledger? | Losing attempts call `report_run_only` (finalize own run, never write `jobs.job.status`), so they cannot demote a succeeded winner. |
| What tests prove stale/concurrent/connection-lost runners cannot remove another active review worktree? | Section 9 (F2/F3 flock fuse incl. `pg_terminate_backend`, R1, P1, ledger test). |

## 7. Ratified forks

- **F1 -- startup `--force`:** keep it, reached only under BOTH the PG lock and the flock fuse (dead-residue reclamation); never in auto-clean or prune.
- **F2 -- prune contention label:** new `contended` classification (`action=preserved`); do not reuse `locked`.
- **F3 -- scope:** review worktrees only this lane; `run_agent_job` parity documented as a named follow-on (Section 10).
- **F4 -- coordinator + fuse (rev 2):** PG session lock is the authoritative coordinator; a narrow `flock` is a local process-liveness fuse around destructive ops only -- not a second coordinator, not a job/status ledger, not a PG replacement, not extended to `run_agent_job`.

## 8. Migration / schema impact

**None.** PG advisory locks and OS `flock` are both transient runtime constructs. No DDL, no new column, no new table, no prod DB mutation. DB surface is `pg_try_advisory_lock` / `pg_advisory_unlock`; fs surface is a per-dispatch `runs/<dispatch_id>.lock` file.

## 9. Test matrix (real `orchestration_test` DB; Linux host for `flock`)

Engine PG lock (`review_worktree_lock`):
- **E1** acquire on a free dispatch -> `held=True`; releases on `with`-exit (second acquire afterward succeeds).
- **E2** two overlapping contexts, same dispatch, **distinct connections** -> first `True`, second `False`.
- **E3** crash-release: acquire on raw conn A, **close A**, acquire on conn B -> `True` (session-drop auto-release).
- **E4** distinct dispatch_ids -> both `True` (distinct keys).
- **E5** value-silence: `_conn()` raising `OperationalError` -> `LockUnavailable`, no text, **no chained `__context__`** (assert `e.__cause__ is None` / `__suppress_context__`).
- **E6** acquire-time (`cur.execute`) `OperationalError` -> `LockUnavailable` (not a raw psycopg escape); conn closed.
- **E7** unlock-time transport failure -> swallowed; the `with`-body's return value is preserved (no mask).
- **E8** `conn.autocommit is True` after acquire (autocommit is coded, not just commented).
- **E9** `_REVIEW_WT_LOCK_NS == 0x52565754` (constant pin).

Flock fuse (`_worktree_flock`):
- **F1** acquire on fd A -> `True`; a second fd -> `False`; **close A's fd** -> a third fd -> `True` (kernel process-death release; the guarantee PG cannot give).
- **F2** runner with a competitor holding the flock (PG lock free) -> `run_review_job` gets the PG lock but fuse `False` -> **touches no tree** (git spy: no `remove`/`add`), `report_run_only` -> `failed`+`contended`, `cleanup_status="not_attempted"`.
- **F3** **`pg_terminate_backend`** of the runner's PG lock session while a competitor holds the flock -> the competitor acquires the PG lock but fails the fuse -> does NOT delete the held tree (the T5 proof).

Runner:
- **R1** contended PG lock (competitor holds the dispatch) -> no tree touched, `report_run_only` failed+contended, `cleanup_status="not_attempted"`.
- **R2** happy path unchanged (no competitor) -> full review runs, worktree created then auto-cleaned, `cleanup_status="cleaned"`.
- **R3** startup `--force` fires **only** inside the both-locks-held branch, never on any contended path (git spy).
- **R4** `LockUnavailable` in the runner -> no tree touched, failed+contended; a subsequent failing `report_run_only` is swallowed (run left for `reap`, bounded by `LEASE_TTL_S`).
- **R5** ledger integrity: a genuine winner A (real run, reports `succeeded`) racing a contended B -> `jobs.job.status` ends `succeeded` **in both report orderings**; B's run row is `failed`+`contended` and does not demote the job.

Prune:
- **P1** `--apply`, PG lock held by a competitor -> `contended`/`preserved`/not removed.
- **P2** `--apply`, flock held by a live runner (PG free) -> `contended`/`preserved`/not removed.
- **P3** after both release -> `removed`.
- **P4** `LockUnavailable` / acquire-time `OperationalError` mid-apply -> `db-unreachable` refusal (not a raw raise; `applied` reflects the partial).
- **P5** dry-run takes no lock/fuse (classification only), unchanged.

Keep + regression:
- **K1** `keep_worktree=True` -> `cleanup_status="kept"` AND both locks released (a same-dispatch re-acquire succeeds) AND a later prune reclaims the kept succeeded+clean tree.
- **G1** full apex-jobs suite green (>= 142 + the new tests); `test_prune.py` **byte-unchanged** (all P1-P5 / contended tests live in a NEW module, e.g. `tests/test_review_worktree_lock.py`, because the uncontended prune path is a true no-op); auto-clean labels + exit codes byte-stable.

## 10. Deferred hardening / named follow-on

**apex-jobs agent-job worktree lifecycle lock lane.** `run_agent_job` has the structurally identical startup `--force` race for `job/<dispatch_id>` worktrees. Not fixed here because agent jobs intentionally **preserve** their worktree for a promotion gate, so the lock+fuse lifetime cannot simply span "until cleanup"; it needs its own design pass. Also deferred: the optional heartbeat `SELECT 1` lock-connection-loss detector (Section 5) and an orphaned-`.lock`-file sweep. Not urgent under the single-worker dev deployment.

Side benefit captured here: the minor prune-vs-auto-clean tail label race (1.2) is closed, because auto-clean holds both locks through cleanup and a concurrent prune fails the fuse -> preserves.

## 11. Success criteria

1. `engine.review_worktree_lock` exists: dispatch-keyed, non-blocking, session-scoped, **explicitly autocommit**, value-silent on connect AND acquire (`raise LockUnavailable() from None`), best-effort unlock, auto-releases on session drop (E1-E9 green).
2. `agent_runner._worktree_flock` exists: dispatch-keyed non-blocking `flock`, held for the full attempt, kernel-released on process death (F1 green).
3. `run_review_job` acquires PG lock then the flock fuse before any worktree op; the startup `--force` is reached only with BOTH held; all losing paths `report_run_only` (never demote `jobs.job.status`) and touch no tree (F2, F3, R1-R5 green).
4. `prune --apply` requires PG lock + flock fuse before its plain remove, preserves a contended dispatch as `contended`, and removes once free (P1-P3); fail-closed broadened (P4).
5. Zero schema change; no prod DB mutation.
6. All existing behavior preserved: `test_prune.py` byte-unchanged (new tests in a new module), auto-clean labels/exit-codes stable, full suite green (G1, K1).
7. `run_agent_job` parity documented as a named follow-on (Section 10).

## 12. Statement

No implementation has begun. This document is the design only. Implementation follows an SDD plan (writing-plans) after the operator's spec-review gate.

## 13. Audit-resolution table (rev 1 -> rev 2)

Cross-engine adversarial audit: 5 independent Claude auditors (lock-liveness, ledger-integrity, failure-injection, value-silence, test-and-semantics) + Codex host review. Both engines independently reached the same four load-bearing defects (raising confidence they are real, not lens artifacts). Verdict rev 1: CHANGES-REQUIRED. Resolutions:

| # | Finding (severity) | Source | Resolution in rev 2 |
| --- | --- | --- | --- |
| 1 | Lock-liveness != process-liveness: a dropped lock CONNECTION frees the PG lock while the PROCESS + `codex` live, letting B `--force`-delete A's live tree (T5). FATAL->BLOCKING (disposable scratch bounds blast radius to a re-runnable review, but it defeats the stated safety property). | all 5 Claude + Codex | **F4:** narrow `flock` process-liveness fuse (4.3b) required alongside the PG lock at every destructive op (4.5/4.6). Kernel-released only on process death -> closes T5. Safety wording weakened to "given the fuse is honored" (Section 5). |
| 2 | Job-ledger corruption: lock acquired after `start()` can't stop B opening attempt N+1; B's contended `report()` last-writer-wins-demotes a succeeded A's `jobs.job.status`. BLOCKING. | ledger-integrity, test-and-semantics, Codex | New `engine.report_run_only` (4.3/4.4): losing attempts finalize ONLY their own run row, never write `jobs.job.status`. Test R5. |
| 3 | Value-silence / fail-closed hole on the acquire path: transport error on `cur.execute` escapes as raw psycopg (leaks DSN, strands run, breaks prune fail-closed); `raise LockUnavailable()` retains `__context__`; unlock-in-finally can mask a clean return. BLOCKING. | lock-liveness, failure-injection, value-silence, test-and-semantics, Codex | 4.3: wrap the whole acquire body -> `LockUnavailable() from None`; guard the unlock; broaden prune's `except` (4.6). Tests E5/E6/E7, P4. |
| 4 | Autocommit gap: spec commented `autocommit=True` but called `_conn()` (autocommit=False) -> idle-in-transaction hold arms `idle_in_transaction_session_timeout` to release the lock mid-run (a trigger for #1). BLOCKING. | lock-liveness, failure-injection, Codex | 4.3: `conn.autocommit = True` explicit + doc (direct session required). Test E8. |
| 5 | NS constant: hex `0x52565754` correct but documented decimal `1381193044` WRONG (=`0x52535554`); a callsite copying the decimal silently loses all mutual exclusion (false-green). IMPORTANT (raised from Codex LOW). | Codex (Claude missed) | 4.2: drop the decimal; ONE imported constant; unit assertion `== 0x52565754`. Test E9. |
| 6 | `superseded_preserved` side effect: contended B bumping attempt -> A's auto-clean returns `superseded_preserved` and leaks its (prune-reclaimable) tree. LOW/PLAUSIBLE. | ledger-integrity, lock-liveness | Documented as accepted (disposable scratch; prune reclaims). Covered by R5 assertions on cleanup_status. |
| 7 | Test-matrix false-greens: no test for connection-death safety, winner-survives-contended, acquire-time failure, keep-path reclaim; `test_prune.py` byte-unchanged vs prune.py-changed tension. | test-and-semantics, Codex | Section 9 expanded (F2/F3, E5-E9, R4/R5, K1); all new tests in a new module so `test_prune.py` stays byte-unchanged. |
| -- | hashtext collision = spurious contended on an unrelated dispatch (availability, not safety). LOW. | lock-liveness, Codex | 4.2 restated as an availability note. |

Confirmed sound by both engines (no change): `pg_try_advisory_lock(int4,int4)`+`hashtext` shape; lock-outside-`_WORKTREE_LOCK` (no deadlock); session locks survive commit; `start()` outside the try (GateError preserved); no schema/DDL/prod mutation; direct-DSN substrate; disposable-scratch bounding.
