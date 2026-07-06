# apex-jobs review worktree lifecycle lock -- design

- **Lane:** orchestration/review-worktree-lifecycle-lock (deferred C2 follow-on from PR #68 prune + PR #69 auto-clean)
- **Base:** main @ 14f70c7b (PR #69 merged)
- **Worktree (host-canonical):** /home/olares/code/apex/apex-review-wtlock
- **Status:** DRAFT rev 4 -- no implementation has begun (spec only). Three cross-engine review rounds folded (rev 1->2->3->4). See Section 13.
- **Date:** 2026-07-05

## 1. Problem

Every mutation of a review worktree is keyed on one path, `~/.apex-jobs/runs/<dispatch_id>`, and touched at three sites:

| Site | Location | Operation | Guard today |
| --- | --- | --- | --- |
| Startup | `agent_runner.run_review_job` (~L186) | `git worktree remove --force` then `add --detach` | `_WORKTREE_LOCK` (process-local) |
| Auto-clean | `agent_runner._cleanup_review_worktree` (~L157) | plain `git worktree remove` (never `--force`) | `_WORKTREE_LOCK` + currency + dirty guards |
| Prune `--apply` | `prune.prune_review_worktrees` (~L214) | plain `git worktree remove` (never `--force`) | `_WORKTREE_LOCK` + recheck-before-remove |

`_WORKTREE_LOCK` is a `threading.Lock()` -- **process-local**. It serializes those sites only within one OS process (one `run_pool`). Across processes it does nothing.

### 1.1 The reachable defect

`engine.start()` has **no guard against opening a second concurrent run** for a job that already has a live run: it inserts `attempt = max(attempt)+1` and flips the job to `running` unconditionally. Combined with a **reused `dispatch_id`** (`enqueue-review --dispatch-id` is *required*; `review-run --dispatch-id` is accepted), two processes can review into the **same path**. Process B's startup `git worktree remove --force` then **deletes process A's live checkout out from under its running `codex`**. Reviews are `max_attempts=1`, so this is a **same-dispatch concurrent-invocation** race, not a reap/lease race.

### 1.2 Minor label race (also closed by this lane)

A `prune --apply` landing in the auto-clean tail window (run already `succeeded`, tree not yet removed) double-removes the same clean path -> a misleading `remove-failed` / `failed_preserved` label. No data loss, but label-fog.

## 2. Goals / Non-goals

### Goals
- Prevent concurrent review runners from unsafely creating / removing / reusing the same detached review worktree.
- Make the startup `git worktree remove --force` **provably safe** -- reached only when the running process is the proven sole live owner of the path.
- Keep the job/run ledger consistent under contention (a loser never demotes a winner; a contended pool-claimed job is never stranded).
- Preserve prune + auto-clean semantics exactly (labels, exit codes, dirty/currency guards, fail-closed-on-DbUnreachable).
- Value-silent throughout.

### Non-goals / boundary
- No DB schema change / DDL / new column / new table; no production DB mutation.
- **The `flock` liveness-fuse (Section 4.3b) is NOT a second coordination substrate.** Postgres remains the authoritative coordinator; `flock` is a local process-liveness fuse consulted only around destructive filesystem operations. It never carries DB/job-status semantics and never replaces the PG lock.
- No advisory lock (PG or flock) on `run_agent_job` in this lane (Section 10 -- named follow-on).
- **No rewrite of `engine.start()`'s general contract.** The ledger fix is achieved by *where* the runner calls `start()` (inside both locks) plus a value-silent claim-release, not by changing `start()` itself.
- **No fork-in-threaded-pool subprocess supervision in this lane** (the `codex` child is launched via the existing `subprocess.run`; no `preexec_fn`/`PR_SET_PDEATHSIG`). Fork-safe child-lifetime binding is a named follow-on (Section 10).
- No unrelated apex-jobs refactors.

## 3. Threat model

| # | Scenario | Today | With this lane |
| --- | --- | --- | --- |
| T1 | Two `review-run --dispatch-id X` in two processes | B's startup `--force` deletes A's live tree; B's `start()` demotes A's job | B fails the PG lock (or the flock fuse) BEFORE `start()` -> opens no run, touches no tree, never writes job.status; A survives |
| T2 | `review-run X` racing a worker draining `enqueue-review X` | same as T1 | same as T1 |
| T3 | `prune --apply` racing a live review on X | DB recheck mostly protects; tail window can double-remove -> label fog (1.2) | prune fails the flock fuse (a live runner holds it) -> preserve (`contended`); no double-remove |
| T4 | A crashed/normally-dead runner leaves a tree at path X | requeue-safe `--force` clears it (unconditionally -> also a hazard for T1) | runner death releases the flock (O_CLOEXEC fd, not held by any child) + PG session -> a fresh attempt reclaims idle residue. (Orphaned-`codex`-after-SIGKILL: accepted residual, 4.4b.) |
| T5 | A holds the PG lock, `codex` runs; A's lock CONNECTION drops while A's PROCESS lives; B acquires the freed PG lock | (rev-1 flaw) B `--force`-deletes A's LIVE tree | A still holds the OS `flock` (kernel-released only on process death). B passes the PG lock but **fails the flock fuse** -> touches nothing; A's tree survives |
| T6 | B (loser) demotes a succeeded A's job via `engine.start()`; or a contended pool-claimed job is stranded | (rev-2/rev-3 residuals) | B never reaches `start()` (called only inside both locks); a contended pool-claimed job is CAS'd back to `pending` (4.4) so it stays re-claimable |

**Safety property (rev 4):** a destructive worktree removal is reached only by a process holding a fresh **`flock`** on `runs/<dispatch_id>.lock` (the **runner-process**-liveness guarantee); the startup `--force` *additionally* requires the PG dispatch lock (it may target foreign residue). A loser bails before `engine.start()` (so it opens no run and never writes `jobs.job.status`) and releases any pool claim (so it is never stranded). Not protected: an orphaned `codex` child that outlives a SIGKILLed runner (accepted narrow residual, 4.4b -- disposable scratch, nil durable loss).

## 4. Design

### 4.1 Coordinator + fuse

- **Postgres session advisory lock, keyed on `dispatch_id`** -- the authoritative cross-process COORDINATOR (ownership, queueing, prune-recheck composition). Non-blocking `pg_try_advisory_lock`; held for the full attempt on a dedicated **autocommit** connection.
- **OS `flock` on `runs/<dispatch_id>.lock`** -- a narrow local **process-liveness fuse** (Section 4.3b). Held by the runner PROCESS for the full attempt; kernel-released only on fd close / process death.

Why both: a PG session lock is released when its *connection's backend* ends (idle timeout, TCP reset, PG restart) while the runner PROCESS keeps running (T5). The `flock` closes that gap because it is bound to the process, not a DB connection. Rejected: xact-scoped PG locks at mutation points; `flock`-only; PG-only (T5 unhandled).

### 4.2 PG lock key

`pg_try_advisory_lock(_REVIEW_WT_LOCK_NS, hashtext(dispatch_id))`. `_REVIEW_WT_LOCK_NS = 0x52565754` (ASCII "RVWT"), **the ONE namespace constant, imported at every callsite -- no decimal literal transcribed** (rev-1's decimal was wrong; dropped). A unit assertion pins `== 0x52565754`. `hashtext` returns int4; a collision between two distinct live dispatch ids manifests only as a *spurious `contended` bail on an unrelated dispatch* (availability, not a safety issue), not auto-requeued; negligible over the small live-id set.

### 4.3 New engine surface (no schema)

```python
class LockUnavailable(Exception):
    """Cannot establish PG dispatch ownership (connect/acquire/config failed). Value-silent:
    carries NO underlying psycopg/DSN text and NO chained __context__ (raised outside the
    except block, so __context__ is None -- not merely __suppress_context__)."""

_REVIEW_WT_LOCK_NS = 0x52565754  # ASCII 'RVWT'; the ONE namespace constant (imported everywhere)

@contextmanager
def review_worktree_lock(dispatch_id):
    conn = None; acquired = False; failed = False
    try:
        conn = _conn()
        conn.autocommit = True                        # explicit -- no idle-in-transaction hold
        with conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok",
                        (_REVIEW_WT_LOCK_NS, dispatch_id))
            acquired = bool(cur.fetchone()["ok"])
    except (psycopg.Error, OSError, ValueError, KeyError, RuntimeError):   # transport OR resolve_dsn config
        failed = True
    if failed:                                        # raise OUTSIDE the except -> __context__ is None
        if conn is not None:
            try: conn.close()
            except Exception: pass
        raise LockUnavailable()
    try:
        yield acquired
    finally:
        try:
            if acquired:
                with conn.cursor() as cur:
                    cur.execute("select pg_advisory_unlock(%s, hashtext(%s))",
                                (_REVIEW_WT_LOCK_NS, dispatch_id))
        except (psycopg.Error, OSError):
            pass                                      # dead session already released; never mask a return
        finally:
            try: conn.close()
            except Exception: pass                    # guarded: a close-time raise never masks/leaks

def release_claim(job_id):
    """Value-silent CAS: return a still-CLAIMED job to 'pending' so a contended pool-claimed
    review (which opened no run) is never stranded. No-op if a winner already advanced the job
    to running/terminal (WHERE status='claimed'), so it can never overwrite a live/finished run."""
    # UPDATE jobs.job SET status='pending', updated_at=now() WHERE id=%s AND status='claimed'
```

- **autocommit is load-bearing** (rev-1 only commented it): no implicit transaction wraps the multi-minute hold, so `idle_in_transaction_session_timeout` cannot fire. Requires a direct session (the canonical DSN is direct). Defense-in-depth: TCP keepalives + `idle_session_timeout=0`; the flock is the actual guarantee if the session drops anyway.
- **Value-silence is complete:** the acquire body catches transport *and* config failures (incl. `resolve_dsn`'s `RuntimeError` on a missing password env); `LockUnavailable` is raised **outside** the except so `__context__ is None`; the unlock **and** both `conn.close()` sites are guarded so none can mask a clean caller return or leak psycopg text.
- No `report_run_only` (losers open no run, Section 4.4).

### 4.3b The `flock` liveness fuse (`agent_runner`)

```python
import fcntl
_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)

@contextmanager
def _worktree_flock(runs, dispatch_id):
    """Local RUNNER-process-liveness FUSE (NOT a coordinator) for runs/<dispatch_id>. Non-blocking
    exclusive flock on the sibling lockfile. Yields True if acquired (no live local process holds
    the path), False if held OR the fuse cannot be established (fs error -> fail-closed). The fd is
    O_CLOEXEC so it is NOT inherited by the codex child: the flock therefore releases exactly on the
    RUNNER process's death (a child never keeps it held, which would wedge the dispatch). Value-silent."""
    fd = None; acquired = False
    try:
        path = os.path.join(runs, dispatch_id + ".lock")
        os.makedirs(runs, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | _O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            acquired = False                          # held by a live process -> occupied
    except OSError:
        acquired = False                              # fs error establishing the fuse -> fail-closed
    try:
        yield acquired
    finally:
        try:
            if fd is not None:
                if acquired: fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
        except OSError:
            pass
```

- **O_CLOEXEC is load-bearing:** the fd must not be inherited by the `codex` subprocess. If it were, an orphaned child would keep the flock held after the runner dies and permanently wedge the dispatch as `contended` -- strictly worse than the accepted delete-residual. We pass O_CLOEXEC explicitly so a future non-default subprocess call cannot silently regress it (CPython/PEP 446 already defaults to it).
- `os.makedirs`/`os.open` are inside the try, so a filesystem `OSError` yields `False` (fail-closed = treat as occupied, touch nothing), value-silent.
- Lockfiles are **not unlinked** (avoids the flock+unlink inode race); a stale 0-byte lockfile flocks cleanly. POSIX-only (`fcntl`); apex-jobs + tests run on the Linux host. Accumulation is inert; an optional orphaned-lockfile sweep is deferred (Section 10).

### 4.4 Runner control flow (`run_review_job`)

Ordering: **PG lock -> `flock` -> `engine.start()` -> `_WORKTREE_LOCK` -> git ops.** `start()` is called only inside the both-locks-held branch, so a losing attempt (PG-not-held, fuse-not-ok, or `LockUnavailable`) opens **no run** and never writes `jobs.job.status`. A loser also `release_claim`s **its own** pool claim so a pool-claimed job is never stranded. `owns_claim` gates that release: the pool path (`_run_one`, which claimed the job) passes `owns_claim=True`; a synchronous `review-run` caller (`cmd_review_run`, which only `get_job`'d the row) passes `owns_claim=False` and MUST NOT release -- otherwise a contended review-run could demote a concurrent worker's legitimate `claimed` job (duplicate claim/run).

```python
def run_review_job(job, env, as_="cc", agent_cmd=None, owns_claim=False):
    repo, runs = _repo(), _runs_dir()
    dispatch_id = job["dispatch_id"]
    review_head = (job.get("payload") or {}).get("review_head") or "HEAD"

    def _contended():                                   # owns_claim gates the release
        # LOSER: no run opened, no job.status write, no tree touched. Un-strand ONLY a
        # claim THIS invocation acquired (owns_claim -> the pool path). A review-run caller
        # (owns_claim=False) never claimed the job, so it must not demote a concurrent
        # worker's legitimate 'claimed' job (-> duplicate claim/run).
        if owns_claim:
            try: engine.release_claim(job["id"])        # CAS claimed->pending; no-op if a winner advanced it
            except Exception as e: log.warning("review release_claim error: %s", type(e).__name__)
        return {"job": dispatch_id, "run": None, "status": "contended",
                "review_head": review_head, "findings_len": 0,
                "contended": True, "cleanup_status": "not_attempted"}
    try:
        with engine.review_worktree_lock(dispatch_id) as held:      # PG COORDINATOR
            if not held:
                return _contended()
            with _worktree_flock(runs, dispatch_id) as fuse_ok:     # RUNNER-liveness FUSE (whole attempt)
                if not fuse_ok:
                    return _contended()                             # T5 / occupied / fs-error
                run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # winner only; GateError propagates
                base_ref = ...                                      # resolve + set_base_ref, as today
                wt = os.path.join(runs, dispatch_id)
                with _WORKTREE_LOCK:
                    _git("worktree","remove","--force", wt, cwd=repo, check=False)   # BOTH locks held -> proven-idle residue
                    _git("worktree","add","--detach", wt, review_head, cwd=repo)
                ... heartbeat, codex, result, engine.report(run_id,...),
                    set_run_artifacts (best-effort), auto-clean helper ...          # flock held throughout
                return {"job": dispatch_id, "run": str(run_id), "status": status,
                        "review_head": review_head, "findings_len": len(out),
                        "contended": False, "cleanup_status": cleanup_status}
    except engine.LockUnavailable:
        return _contended()
```

- A contended result carries `status="contended"`, `run=None`; `_contended()` releases a pool claim **only when `owns_claim`** (the pool path claimed it) -- a `review-run` caller (`owns_claim=False`) never demotes a concurrent worker's claim. `engine.start()` stays inside the winner branch; its `GateError` propagates out of `run_review_job` exactly as today (the pool records it), releasing both locks on the way out.
- **Re-claim spin:** on persistent contention (a long prune hold, or a persistent fs error such as a full disk), `release_claim` -> `pending` -> the pool may re-claim and re-contend in a tight loop until the condition clears. Accepted at single-worker dev scale (prune per-item is fast; a full disk is an out-of-band operational failure). Bounded backoff is a possible follow-on.

### 4.4b Runner death and the `codex` child (accepted residual)

The `flock` tracks the **runner process**. The `codex` child is launched with the existing `subprocess.run` (no `preexec_fn`/`PR_SET_PDEATHSIG` -- fork-in-threaded-pool supervision is explicitly out of scope, Non-goals). Consequence: if the runner is **SIGKILLed** mid-review, its `codex` child can be reparented and briefly outlive it; the runner's flock fd (O_CLOEXEC, not inherited) releases on the runner's death, so a competitor could `--force`-reclaim the path under the orphaned child.

**Accepted as a narrow residual** because the blast radius is nil on disposable scratch: the orphaned child's parent run is already lost (nothing captures its findings), no durable review data should be trusted from an orphan, and the worst case is a failed/re-runnable review -- never repo or durable-data loss. Fork-safe child-lifetime binding (a supervisor/launcher, NOT `preexec_fn` under the thread pool) is a named follow-on (Section 10).

### 4.5 Destructive-op guards (startup `--force` = ratified F1, tightened)

- **The flock is the runner-process-liveness guarantee for every worktree removal.** Auto-clean removes the runner's OWN tree while it still holds the flock, so no competing live runner can be present -- safe even if the runner has meanwhile lost only its PG lock connection (the flock, not the PG lock, guards the removal).
- **The startup `git worktree remove --force`** additionally requires the PG dispatch lock (it may target residue this attempt did not create). Reached only inside the both-locks-held branch (4.4), so any tree there is idle residue. `--force` is permitted only there -- never in auto-clean or prune (plain remove, flock-guarded, no `--force`). An in-code comment records the invariant.

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
                        w.classification, w.action = "contended", "preserved"; continue
                    with agent_runner._WORKTREE_LOCK:
                        ... existing recheck-before-remove + plain remove verbatim ...
        except (engine.LockUnavailable, psycopg.Error, OSError):
            return _refusal(items, "db-unreachable", applied=True, remove_failed=remove_failed)
```

- New classification **`contended`** (`action=preserved`), set only in the apply loop, reached when EITHER lock is held by a live runner. Value-silent; flows into `_counts`.
- `except` broadened to `(LockUnavailable, psycopg.Error, OSError)` -> the existing `db-unreachable` refusal. Global lock order PG -> flock -> `_WORKTREE_LOCK` matches the runner (no deadlock).

### 4.7 `--keep-worktree` interaction

Lock + fuse lifetime are independent of keep. `--keep-worktree` still only skips auto-clean (`cleanup_status="kept"`); the attempt releases BOTH locks at terminal handling, and the kept tree remains reclaimable by a later prune. B1 semantics preserved.

### 4.8 CLI / JSON surfacing

`review-run` contended -> `status="contended"`, `run=None`. The CLI **must handle `run is None`**: skip the `runs_for(disp)[-1]` findings read (which would `IndexError` on no run, or print a stale prior run's findings), emit empty findings + `"contended": true`, and exit `3` (contended is not `succeeded`). Any pool-summary consumer likewise tolerates `run=None`/`findings_len=0`. No new exit code.

### 4.9 `_WORKTREE_LOCK` retained

Innermost intra-process belt around the git ops; **not** the safety mechanism.

## 5. Concurrency posture

Safe for single-worker dev AND multi-process operation. The PG lock coordinates dispatch ownership; the `flock` (tracking the runner process, fd not inherited) guarantees a released lock means no live RUNNER is using the path. **Normal death / SIGKILL:** the runner dies -> flock + PG session release -> a legit reclaimer safely `--force`-reclaims idle residue (an orphaned `codex` is the accepted residual, 4.4b). **Connection loss without process death (T5):** A keeps the flock -> a competitor passes the PG lock but fails the fuse -> touches nothing. **A that loses only its PG lock but lives:** it keeps the flock and safely finishes/auto-cleans its OWN tree. **Contention:** a loser bails before `engine.start()` (no run, no job.status write) and releases any pool claim -> the winner's ledger stands and the job stays re-claimable (T6). Optional future defense-in-depth (out of scope): a heartbeat `SELECT 1` to fail a runner's own attempt on PG-lock-connection loss.

## 6. The operator's design questions -- answered

| Question | Answer |
| --- | --- |
| Postgres advisory, file lock, or both? | Both, distinct roles: PG session lock = coordinator; `flock` = local runner-process-liveness fuse around destructive ops. |
| Lock key? | `dispatch_id` for both. |
| Cover checkout / execution / cleanup / prune, or only mutation points? | Full attempt: PG lock + flock held from startup through `codex`, artifacts, auto-clean; prune requires both before its remove. |
| Interaction with `--keep-worktree`? | Orthogonal; keep only skips auto-clean; both locks released at terminal handling. |
| Lock acquisition fails / times out? | Non-blocking. PG/flock `False` -> `contended` (no run; pool claim released; prune preserves). Connect/acquire/config failure -> `LockUnavailable` -> runner contended, prune `db-unreachable`. No timeout. |
| Contended path corrupting the job ledger? | Losers bail before `engine.start()` (no run, no job.status write) and `release_claim` (no strand). |
| What proves a stale/concurrent/connection-lost runner cannot remove another live runner's tree? | Section 9: F2/F3 (fuse incl. `pg_terminate_backend`), R1-R6. |

## 7. Ratified forks

- **F1 -- startup `--force`:** keep it, reached only under BOTH locks (idle-residue reclamation); never in auto-clean/prune.
- **F2 -- prune contention label:** new `contended` classification (`action=preserved`); not `locked`.
- **F3 -- scope:** review worktrees only; `run_agent_job` parity is a named follow-on (Section 10).
- **F4 -- coordinator + fuse:** PG lock = coordinator; `flock` = local runner-process-liveness fuse around destructive ops only (not a second coordinator, not a status ledger, not a PG replacement, not extended to `run_agent_job`, no fork-in-threaded-pool child supervision in-lane).

## 8. Migration / schema impact

**None.** PG advisory locks + OS `flock` are transient runtime constructs. No DDL/column/table/prod mutation. DB surface: `pg_try_advisory_lock`/`pg_advisory_unlock` + a `release_claim` UPDATE on the existing `jobs.job`; fs surface: a per-dispatch `runs/<dispatch_id>.lock` file.

## 9. Test matrix (real `orchestration_test` DB; Linux host for `flock`)

PG lock (`review_worktree_lock`):
- **E1** free dispatch -> `held=True`; releases on exit.
- **E2** two contexts, same dispatch, distinct connections -> first `True`, second `False`.
- **E3** crash-release: acquire on conn A, close A, acquire on conn B -> `True`.
- **E4** distinct dispatch_ids -> both `True`.
- **E5** value-silence: `_conn()` `OperationalError` -> `LockUnavailable`; assert `e.__context__ is None` and `e.__cause__ is None` and `str(e)` carries no DSN.
- **E6** acquire-time `cur.execute` `OperationalError`, a `resolve_dsn` `ValueError`, AND a `resolve_dsn` `RuntimeError` (missing-password env) -> `LockUnavailable`, value-silent (`__context__ is None`); conn closed.
- **E7** unlock-time AND close-time transport failure -> swallowed; the `with`-body return preserved.
- **E8** `conn.autocommit is True` after acquire.
- **E9** `_REVIEW_WT_LOCK_NS == 0x52565754`.

Flock fuse (`_worktree_flock`):
- **F1** acquire on fd A -> `True`; a second fd -> `False`; close A -> a third fd -> `True` (kernel process-death release).
- **F1b** the lockfile fd is O_CLOEXEC / not inherited across a subprocess.
- **F2** competitor holds the flock (PG free) -> `run_review_job` gets the PG lock but fuse `False` -> no run opened, no tree touched (git spy), `contended`.
- **F3** `pg_terminate_backend` of the runner's PG lock session while a competitor holds the flock -> the competitor acquires the PG lock but fails the fuse -> does NOT delete the held tree (T5 proof).
- **F4** flock fs-error (`os.open`/`makedirs` `OSError`) -> fuse `False` -> `contended`, no tree, value-silent.

Runner:
- **R1** contended PG lock -> no run opened, no tree touched, `contended`.
- **R2** happy path unchanged -> full review, worktree created then auto-cleaned, `cleanup_status="cleaned"`.
- **R3** startup `--force` fires only inside the both-locks-held branch (git spy), never on a contended path.
- **R4** `LockUnavailable` -> `contended`, no run, no tree.
- **R5** ledger integrity: drive winner A to reported-`succeeded`; a concurrent contended B (bails before `start()`) -> `jobs.job.status` stays `succeeded`; assert no path can leave `jobs.job.status='running'` once every run row is terminal.
- **R6** strand-free contention: a **pool-claimed** job (status pre-set `claimed`) whose runner bails `contended` -> `release_claim` returns it to `pending` (re-claimable); and `release_claim` is a **no-op** when a winner already advanced the job to `running`/terminal (assert both).
- **R7** CLI: `review-run` contended (`run=None`) -> no `IndexError`, empty findings, `contended:true`, exit `3`.

Prune:
- **P1** PG lock held by a competitor -> `contended`/`preserved`/not removed.
- **P2** flock held by a live runner (PG free) -> `contended`/`preserved`/not removed.
- **P3** both released -> `removed`.
- **P4** `LockUnavailable` / acquire-time `OperationalError` mid-apply -> `db-unreachable` refusal (not a raw raise).
- **P5** dry-run takes no lock/fuse, unchanged.

Keep + regression:
- **K1** `keep_worktree=True` -> `cleanup_status="kept"` AND both locks released (same-dispatch re-acquire succeeds) AND a later prune reclaims the kept succeeded+clean tree.
- **G1** full apex-jobs suite green (>= 142 + new tests); `test_prune.py` **byte-unchanged** (all new prune/contended tests live in a NEW module, e.g. `tests/test_review_worktree_lock.py`, since the uncontended path is a true no-op); auto-clean labels + exit codes byte-stable.

## 10. Deferred hardening / named follow-ons

- **apex-jobs agent-job worktree lifecycle lock lane** -- `run_agent_job` has the structurally identical startup `--force` race but preserves its worktree for a promotion gate, so the lock+fuse lifetime needs its own design pass.
- **review child lifecycle binding / subprocess supervisor lane** -- fork-safe binding of the `codex` child to the runner's lifetime (a supervisor/launcher, NOT `preexec_fn` under the thread pool), closing the orphaned-`codex`-after-SIGKILL residual (4.4b) if it is ever judged worth the machinery.
- Also deferred: the optional heartbeat lock-connection-loss detector (Section 5); an orphaned-`.lock` sweep; bounded backoff on repeated re-claim contention (4.4).

Side benefit captured here: the minor prune-vs-auto-clean tail label race (1.2) is closed (auto-clean holds the flock through cleanup; a concurrent prune fails the fuse -> preserves).

## 11. Success criteria

1. `engine.review_worktree_lock`: dispatch-keyed, non-blocking, **explicitly autocommit**, value-silent on connect/acquire/config incl. `resolve_dsn` `RuntimeError` (`LockUnavailable` raised outside the except -> `__context__ is None`), guarded unlock AND close, auto-releases on session drop (E1-E9). `engine.release_claim` is a value-silent CAS.
2. `agent_runner._worktree_flock`: dispatch-keyed non-blocking `flock`, O_CLOEXEC fd, fs-error fail-closed, kernel-released on process death (F1, F1b, F4).
3. `run_review_job`: PG lock -> flock -> `start()` -> git ops; a loser bails before `start()` (no run, no job.status write, no tree) and `release_claim`s; startup `--force` only with both held (F2, F3, R1-R6). CLI tolerates `run=None` (R7).
4. `prune --apply`: PG lock + flock before its plain remove; `contended` preserve; removes once free (P1-P3); fail-closed broadened (P4).
5. Zero schema change; no prod DB mutation.
6. Existing behavior preserved: `test_prune.py` byte-unchanged (new tests in a new module), auto-clean labels/exit-codes stable, full suite green (G1, K1).
7. `run_agent_job` parity and fork-safe child binding documented as named follow-ons (Section 10); orphaned-`codex`-after-SIGKILL accepted as a residual (4.4b).

## 12. Statement

No implementation has begun. This document is the design only. Implementation follows an SDD plan (writing-plans) after the operator's spec-review gate.

## 13. Audit-resolution table

Three cross-engine adversarial rounds. R1 (rev 1): 5 Claude auditors + Codex. R2 (rev 2): 3 Claude re-auditors + Codex. R3 (rev 3): 1 Claude verifier + Codex. Both engines independently reached the load-bearing findings each round.

| # | Finding (severity) | Round | Resolution |
| --- | --- | --- | --- |
| 1 | Lock-liveness != process-liveness (T5). | R1 | `flock` process-liveness fuse (4.3b) at every destructive op. |
| 2 | Ledger corruption via contended `report()`. | R1 | (rev 2) superseded by #6. |
| 3 | Value-silence hole on the acquire path. | R1+R2 | 4.3: whole-body catch, raise outside except (`__context__ is None`), guarded unlock+close. |
| 4 | Autocommit only commented. | R1+R2 | 4.3: `conn.autocommit = True` explicit. |
| 5 | NS-constant decimal wrong. | R1 | 4.2: drop decimal; ONE imported constant; assert E9. |
| 6 | Rev-2 ledger fix incomplete: loser `start()` demotes; reap can't recover. | R2 | 4.4: `start()` INSIDE both locks -> loser opens no run; removed `report_run_only`. R5. |
| 7 | `from None` leaves `__context__` live. | R2 | 4.3: raise outside the except. E5. |
| 8 | Orphaned `codex` outlives a SIGKILLed runner. | R2 | (rev 3 mandated `PR_SET_PDEATHSIG`) **rev 4 reverses:** the mechanism is a fork-in-threaded-pool hazard; ACCEPTED as a narrow residual (4.4b, nil durable loss); keep O_CLOEXEC; fork-safe binding deferred to a named follow-on (Section 10). Operator-ratified. |
| 9 | Unguarded `conn.close()`; too-narrow acquire except (config `ValueError`). | R2 | 4.3: guard close; broaden catch. |
| 10 | `flock` fs `OSError` escaped. | R2 | 4.3b: wrap fs setup -> fuse `False`. F4. |
| 11 | Auto-clean under flock-only after PG-lock loss. | R2 | 4.5: the flock guards removals; only `--force` needs the PG lock too. |
| 12 | **Rev-3 introduced a strand:** a contended **pool-claimed** job (prune/fs-error/DB-blip contention, no runner-winner) is stuck `claimed` (reap ignores it). BLOCKING. | R3, Codex (Claude verifier wrongly ruled it unreachable) | 4.4: `_contended()` calls value-silent `engine.release_claim` (CAS `claimed->pending`, no-op if advanced). R6. |
| 13 | CLI `review-run` `runs_for(disp)[-1]` `IndexError`/stale on `run=None`. | R3, Codex | 4.8: handle `run is None` -> empty findings, exit 3. R7. |
| 14 | Acquire catch missed `resolve_dsn`'s `RuntimeError` (missing-password env). | R3, Codex | 4.3: add `RuntimeError`. E6. |
| -- | lockfile accumulation; hashtext collision; re-claim spin. LOW. | R1-R3 | Documented accepted; sweeps/backoff deferred (Section 10). |

Confirmed sound by both engines (unchanged): `pg_try_advisory_lock(int4,int4)`+`hashtext` shape; lock-outside-`_WORKTREE_LOCK` (no deadlock); session locks survive commit; no schema/DDL/prod mutation; direct-DSN substrate; flock-not-unlinked (no inode race); prune lock ordering; GateError value-silent; disposable-scratch bounding.
