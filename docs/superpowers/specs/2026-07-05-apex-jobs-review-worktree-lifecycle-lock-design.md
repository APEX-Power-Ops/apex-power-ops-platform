# apex-jobs review worktree lifecycle lock -- design

- **Lane:** orchestration/review-worktree-lifecycle-lock (deferred C2 follow-on from PR #68 prune + PR #69 auto-clean)
- **Base:** main @ 14f70c7b (PR #69 merged)
- **Worktree (host-canonical):** /home/olares/code/apex/apex-review-wtlock
- **Status:** DRAFT rev 3 -- no implementation has begun (spec only). Rev 2 folded a cross-engine audit; rev 3 folds a cross-engine RE-audit (3 Claude re-auditors + Codex) that found the rev-2 ledger fix incomplete. See Section 13.
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

`engine.start()` has **no guard against opening a second concurrent run** for a job that already has a live run: it inserts `attempt = max(attempt)+1` and flips the job to `running` unconditionally. Combined with a **reused `dispatch_id`** (`enqueue-review --dispatch-id` is *required*; `review-run --dispatch-id` is accepted), two processes can review into the **same path**. Process B's startup `git worktree remove --force` then **deletes process A's live checkout out from under its running `codex`**. The `--force` is what makes the collision destructive. Reviews are `max_attempts=1`, so this is a **same-dispatch concurrent-invocation** race, not a reap/lease race.

### 1.2 Minor label race (also closed by this lane)

A `prune --apply` landing in the auto-clean tail window (run already `succeeded`, tree not yet removed) double-removes the same clean path -> a misleading `remove-failed` / `failed_preserved` label. No data loss, but label-fog.

## 2. Goals / Non-goals

### Goals
- Prevent concurrent review runners from unsafely creating / removing / reusing the same detached review worktree.
- Make the startup `git worktree remove --force` **provably safe** -- reached only when the running process is the proven sole live owner of the path.
- Keep the job/run ledger consistent under contention (a losing attempt never demotes a succeeded winner).
- Preserve prune + auto-clean semantics exactly (labels, exit codes, dirty/currency guards, fail-closed-on-DbUnreachable).
- Value-silent throughout.

### Non-goals / boundary
- No DB schema change / DDL / new column / new table; no production DB mutation.
- **The `flock` liveness-fuse (Section 4.3b) is NOT a second coordination substrate.** Postgres remains the authoritative dispatch/worktree coordinator (ownership + queueing + prune-recheck composition). `flock` is a *local process-liveness fuse* consulted only around destructive filesystem operations. It never carries DB/job-status semantics and never replaces the PG lock.
- No advisory lock (PG or flock) on `run_agent_job` in this lane (Section 10 -- named follow-on).
- **No rewrite of `engine.start()`'s general contract.** The ledger fix is achieved by *where* the runner calls `start()` (inside both locks), not by changing `start()` itself; `start()` is unmodified.
- No unrelated apex-jobs refactors.

## 3. Threat model

| # | Scenario | Today | With this lane |
| --- | --- | --- | --- |
| T1 | Two `review-run --dispatch-id X` in two processes | B's startup `--force` deletes A's live tree; B's `start()` demotes A's job | B fails the PG lock (or the flock fuse) BEFORE `start()` -> B opens no run, touches no tree, never writes job.status; A survives |
| T2 | `review-run X` racing a worker draining `enqueue-review X` | same as T1 | same as T1 |
| T3 | `prune --apply` racing a live review on X | DB recheck mostly protects; tail window can double-remove -> label fog (1.2) | prune fails the flock fuse (a live runner holds it) -> preserve (`contended`); no double-remove |
| T4 | Crashed / SIGKILLed runner leaves a tree at path X | requeue-safe `--force` clears it (unconditionally -> also a hazard for T1) | runner death kills its `codex` child (4.4b) and releases the flock (O_CLOEXEC fd) + PG session -> a fresh attempt reclaims proven-idle residue |
| T5 | A holds the PG lock, `codex` runs; A's lock CONNECTION drops while A's PROCESS lives; B acquires the freed PG lock | (rev-1 flaw) B `--force`-deletes A's LIVE tree | A still holds the OS `flock` (kernel-released only on process death). B passes the PG lock but **fails the flock fuse** -> touches nothing; A's tree survives |
| T6 | B (loser) demotes a succeeded A's job ledger via `engine.start()` | (rev-2 residual) B's `start()` flips job `succeeded`->`running`; `reap` cannot recover it (no running run) | B never reaches `start()` -- it is called only inside the both-locks-held branch, after B has already bailed `contended` (4.4) |

**Safety property (rev 3):** a destructive worktree removal is reached only by a process holding a fresh **`flock`** on `runs/<dispatch_id>.lock` (the process-liveness guarantee); the startup `--force` *additionally* requires the PG dispatch lock (it may target residue this attempt did not create). The `codex` child is bound to the runner's lifetime and the flock fd is not inherited, so a released flock corresponds exactly to "no live process is using the path." A losing attempt bails before `engine.start()`, so it never opens a run or writes `jobs.job.status`.

## 4. Design

### 4.1 Coordinator + fuse

- **Postgres session advisory lock, keyed on `dispatch_id`** -- the authoritative cross-process COORDINATOR (ownership, queueing, prune-recheck composition). Non-blocking `pg_try_advisory_lock`; held for the full attempt on a dedicated **autocommit** connection.
- **OS `flock` on `runs/<dispatch_id>.lock`** -- a narrow local **process-liveness fuse** (Section 4.3b). Held by the runner PROCESS for the full attempt; kernel-released only on fd close / process death.

Why both: a PG session lock is released when its *connection's backend* ends -- which can happen (idle-session/idle-in-transaction timeout, TCP reset, PG restart) while the runner PROCESS and its `codex` keep running (T5). The `flock` closes that gap because it is bound to the process, not a DB connection. Rejected: xact-scoped PG locks at mutation points (no full-attempt ownership); `flock`-only (loses DB-centric prune composition + cross-host-future); PG-only (T5 unhandled).

### 4.2 PG lock key

`pg_try_advisory_lock(_REVIEW_WT_LOCK_NS, hashtext(dispatch_id))`. `_REVIEW_WT_LOCK_NS = 0x52565754` (ASCII "RVWT"), **the ONE namespace constant, imported at every callsite -- no callsite transcribes a decimal literal** (rev-1 documented a wrong decimal; dropped). A unit assertion pins `_REVIEW_WT_LOCK_NS == 0x52565754`. `hashtext` returns int4; a collision between two distinct live dispatch ids manifests only as a *spurious `contended` bail on an unrelated dispatch* (an availability degradation, safe for correctness), not auto-requeued; negligible over the small live-id set.

### 4.3 New engine surface (no schema)

```python
class LockUnavailable(Exception):
    """Cannot establish PG dispatch ownership (connect/acquire failed). Value-silent:
    carries NO underlying psycopg/DSN text and NO chained __context__ (raised outside
    the except block, so __context__ is None -- not merely __suppress_context__)."""

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
    except (psycopg.Error, OSError, ValueError, KeyError):   # transport OR resolve_dsn config failure
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
```

- **autocommit is load-bearing** (rev-1 only commented it): no implicit transaction wraps the multi-minute hold, so `idle_in_transaction_session_timeout` cannot fire. Requires a direct session (the canonical DSN is direct). Defense-in-depth: TCP keepalives + `idle_session_timeout=0` on the lock DSN; the `flock` fuse is the actual guarantee if the session drops anyway.
- **Value-silence is complete:** the acquire body catches transport *and* config (`resolve_dsn`) failures; `LockUnavailable` is raised **outside** the except so `__context__ is None` (not merely `__suppress_context__`); the unlock **and** the `conn.close()` are both guarded so neither can mask a clean caller return or leak psycopg text.
- **No `report_run_only`** (removed vs rev 2): losing attempts open no run at all (Section 4.4), so there is nothing to finalize.

### 4.3b The `flock` liveness fuse (`agent_runner`)

```python
import fcntl
_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)

@contextmanager
def _worktree_flock(runs, dispatch_id):
    """Local process-liveness FUSE (NOT a coordinator) for runs/<dispatch_id>. Non-blocking
    exclusive flock on the sibling lockfile. Yields True if acquired (no live local process
    holds the path), False if a live process holds it OR the fuse itself cannot be established
    (fs error -> fail-closed). The fd is O_CLOEXEC so it is NOT inherited by the codex child ->
    the kernel releases the flock exactly on the RUNNER process's death. Value-silent."""
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

- **O_CLOEXEC is load-bearing:** the fd must not be inherited by the `codex` subprocess, or a lingering child would keep the flock held after the runner dies (wedging the dispatch). CPython (PEP 446) sets O_CLOEXEC by default; we pass it explicitly so a future non-default subprocess call cannot silently regress it.
- `os.makedirs` / `os.open` are inside the try, so a filesystem `OSError` (ENOSPC/EACCES) yields `False` (fail-closed = treat as occupied, touch nothing), value-silent (no path leak).
- The lockfile basename `review-XXXXXXXX.lock` is not a git worktree and does not match prune's worktree-basename filter. Lockfiles are **not unlinked** (avoids the flock+unlink inode race); a stale 0-byte lockfile flocks cleanly. POSIX-only (`fcntl`); apex-jobs + its tests run on the Linux host. Accumulation is inert; an optional orphaned-lockfile sweep is deferred (Section 10).

### 4.4 Runner control flow (`run_review_job`)

Ordering: **PG lock (coordinator) -> `flock` (fuse) -> `engine.start()` -> `_WORKTREE_LOCK` -> git ops.** `start()` is called **only inside the both-locks-held branch**, so a losing attempt (PG-not-held, fuse-not-ok, or `LockUnavailable`) opens **no run** and never writes `jobs.job.status` -- the winner always resolves the job.

```python
def run_review_job(job, env, as_="cc", agent_cmd=None):
    repo, runs = _repo(), _runs_dir()
    dispatch_id = job["dispatch_id"]
    review_head = (job.get("payload") or {}).get("review_head") or "HEAD"

    def _contended():
        # LOSER: no run opened, no job.status write, no tree touched. Winner resolves the job.
        return {"job": dispatch_id, "run": None, "status": "contended",
                "review_head": review_head, "findings_len": 0,
                "contended": True, "cleanup_status": "not_attempted"}
    try:
        with engine.review_worktree_lock(dispatch_id) as held:      # PG COORDINATOR
            if not held:
                return _contended()
            with _worktree_flock(runs, dispatch_id) as fuse_ok:     # PROCESS-LIVENESS FUSE (whole attempt)
                if not fuse_ok:
                    return _contended()                             # T5 / occupied / fs-error
                run_id = engine.start(job["id"], claimed_by=as_, run_env=env)   # winner only; GateError propagates
                base_ref = ...                                      # resolve + set_base_ref, as today
                wt = os.path.join(runs, dispatch_id)
                with _WORKTREE_LOCK:
                    _git("worktree","remove","--force", wt, cwd=repo, check=False)   # BOTH locks held -> proven-dead residue
                    _git("worktree","add","--detach", wt, review_head, cwd=repo)
                ... heartbeat, codex (bound to runner lifetime, 4.4b), result, engine.report(run_id,...),
                    set_run_artifacts (best-effort), auto-clean helper ...          # flock held throughout
                return {"job": dispatch_id, "run": str(run_id), "status": status,
                        "review_head": review_head, "findings_len": len(out),
                        "contended": False, "cleanup_status": cleanup_status}
    except engine.LockUnavailable:
        return _contended()
```

- A contended result carries `status="contended"`, `run=None`. `engine.start()` stays inside the winner branch; its `GateError` propagates out of `run_review_job` exactly as today (the pool records it), releasing both locks on the way out.
- The heartbeat thread is started only on the winner path (after `start()`), so no contended path leaves a run for `reap`.

### 4.4b Review subprocess lifetime bound to the runner

The `codex` subprocess is launched so it **cannot outlive the runner process**: on Linux via `preexec_fn` setting `PR_SET_PDEATHSIG = SIGKILL` (belt: a new session + a process-group kill on runner exit). So runner death (even SIGKILL) kills `codex`, which -- with the O_CLOEXEC flock fd (4.3b) -- means a released flock corresponds to a genuinely-idle tree (no orphaned child still using it). This makes the "flock released == holder genuinely gone" guarantee true, closing the orphaned-`codex` gap.

### 4.5 Destructive-op guards (startup `--force` = ratified F1, tightened)

- **The flock is the process-liveness guarantee for every worktree removal.** Auto-clean removes the runner's OWN tree while it still holds the flock, so no competitor can be present -- safe even if the runner has meanwhile lost only its PG lock connection (the flock, not the PG lock, guards the removal).
- **The startup `git worktree remove --force`** additionally requires the PG dispatch lock, because it may target residue this attempt did not create. It is reached only inside the both-locks-held branch (4.4), so any tree there is proven-dead residue. **`--force` is permitted only there -- never in auto-clean or prune** (those stay plain-remove, flock-guarded, no `--force`). An in-code comment records the invariant.

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

- New classification **`contended`** (`action=preserved`), set only in the apply loop (like `remove-failed`), reached when EITHER the PG lock OR the flock fuse is held by a live runner. Value-silent; flows into `_counts`.
- The `except` is broadened to `(LockUnavailable, psycopg.Error, OSError)` -> the existing `db-unreachable` refusal, so no exception escapes the apply loop fail-open. Global lock order PG -> flock -> `_WORKTREE_LOCK` matches the runner (no deadlock).

### 4.7 `--keep-worktree` interaction

Lock + fuse lifetime are independent of keep. `--keep-worktree` still only skips auto-clean (`cleanup_status="kept"`); the attempt releases BOTH the PG lock and the `flock` at terminal handling, and the kept tree remains reclaimable by a later prune. B1 semantics preserved.

### 4.8 CLI / JSON surfacing

`review-run` contended -> `status="contended"` (no run opened), which is not `succeeded`, so the existing exit contract yields exit `3`; `--json` gains `"contended": true`. No new exit code.

### 4.9 `_WORKTREE_LOCK` retained

Innermost intra-process belt around the git ops; **not** the safety mechanism.

## 5. Concurrency posture

Safe for single-worker dev AND multi-process operation. The PG lock coordinates dispatch ownership; the `flock` (tracking the runner process, with `codex` bound to the runner's lifetime and the fd not inherited) guarantees a released lock means no live process is using the path. **Crash / SIGKILL:** the runner dies -> `codex` dies (4.4b) -> flock + PG session release on an idle tree -> a legit reclaimer safely `--force`-reclaims. **Connection loss without process death (T5):** A keeps the flock -> a competitor passes the PG lock but fails the fuse -> touches nothing. **A that loses only its PG lock but lives:** it keeps the flock and safely finishes/auto-cleans its OWN tree (the flock guards the removal). **Contention:** a loser bails before `engine.start()` -> opens no run, never writes job.status -> the winner's ledger stands (T6). Optional future defense-in-depth (out of scope): a heartbeat `SELECT 1` to fail a runner's own attempt loudly on PG-lock-connection loss.

## 6. The operator's design questions -- answered

| Question | Answer |
| --- | --- |
| Postgres advisory, file lock, or both? | Both, distinct roles: PG session lock = cross-process COORDINATOR; `flock` = local process-liveness FUSE around destructive ops. |
| Lock key? | `dispatch_id` for both. |
| Cover checkout / execution / cleanup / prune, or only mutation points? | Full attempt: PG lock + flock held from startup through `codex`, artifacts, auto-clean; prune requires both before its remove. |
| Interaction with `--keep-worktree`? | Orthogonal; keep only skips auto-clean; both locks released at terminal handling. |
| Lock acquisition fails / times out? | Non-blocking. PG `False` / flock `False` -> `contended` (runner opens no run; prune preserves `contended`). Connect/acquire/config failure -> `LockUnavailable` -> runner contended, prune `db-unreachable` refusal. No timeout. |
| Contended path corrupting the job ledger? | Losers bail before `engine.start()` -> no run, no `jobs.job.status` write. |
| What proves a stale/concurrent/connection-lost/crashed runner cannot remove another active tree? | Section 9: F2/F3 (fuse incl. `pg_terminate_backend`), R6 (child dies with runner), R1-R5. |

## 7. Ratified forks

- **F1 -- startup `--force`:** keep it, reached only under BOTH locks (dead-residue reclamation); never in auto-clean/prune.
- **F2 -- prune contention label:** new `contended` classification (`action=preserved`); not `locked`.
- **F3 -- scope:** review worktrees only; `run_agent_job` parity is a named follow-on (Section 10).
- **F4 -- coordinator + fuse:** PG session lock = authoritative coordinator; a narrow `flock` = local process-liveness fuse around destructive ops only (not a second coordinator, not a status ledger, not a PG replacement, not extended to `run_agent_job`).

## 8. Migration / schema impact

**None.** PG advisory locks + OS `flock` are transient runtime constructs. No DDL/column/table/prod mutation. DB surface: `pg_try_advisory_lock`/`pg_advisory_unlock`; fs surface: a per-dispatch `runs/<dispatch_id>.lock` file.

## 9. Test matrix (real `orchestration_test` DB; Linux host for `flock`)

PG lock (`review_worktree_lock`):
- **E1** free dispatch -> `held=True`; releases on exit (second acquire succeeds).
- **E2** two contexts, same dispatch, distinct connections -> first `True`, second `False`.
- **E3** crash-release: acquire on conn A, close A, acquire on conn B -> `True`.
- **E4** distinct dispatch_ids -> both `True`.
- **E5** value-silence: `_conn()` `OperationalError` -> `LockUnavailable`; assert **`e.__context__ is None` and `e.__cause__ is None`** (raised outside the except) and `str(e)` carries no DSN.
- **E6** acquire-time `cur.execute` `OperationalError` AND a non-transport `resolve_dsn` `ValueError` -> `LockUnavailable`, value-silent (`__context__ is None`); conn closed.
- **E7** unlock-time AND close-time transport failure -> swallowed; the `with`-body return value is preserved (no mask, no leak).
- **E8** `conn.autocommit is True` after acquire.
- **E9** `_REVIEW_WT_LOCK_NS == 0x52565754`.

Flock fuse (`_worktree_flock`):
- **F1** acquire on fd A -> `True`; a second fd -> `False`; close A -> a third fd -> `True` (kernel process-death release).
- **F1b** the lockfile fd is O_CLOEXEC / not inherited across a subprocess (assert the child cannot see/hold it).
- **F2** competitor holds the flock (PG free) -> `run_review_job` gets the PG lock but fuse `False` -> **no run opened**, **no tree touched** (git spy), returns `contended`.
- **F3** `pg_terminate_backend` of the runner's PG lock session while a competitor holds the flock -> the competitor acquires the PG lock but fails the fuse -> does NOT delete the held tree (T5 proof).
- **F4** flock fs-error (`os.open`/`makedirs` raises `OSError`) -> fuse `False` -> `contended`, no tree, value-silent.

Runner:
- **R1** contended PG lock -> no run opened, no tree touched, `contended`.
- **R2** happy path unchanged -> full review, worktree created then auto-cleaned, `cleanup_status="cleaned"`.
- **R3** startup `--force` fires **only** inside the both-locks-held branch (git spy), never on a contended path.
- **R4** `LockUnavailable` -> `contended`, no run, no tree.
- **R5** ledger integrity (rewritten): drive winner A to reported-`succeeded`; then a concurrent contended B (bails before `start()`) -> `jobs.job.status` stays `succeeded`; assert **no code path can leave `jobs.job.status='running'` once every run row for the job is terminal** (proves B never opens a demoting run).
- **R6** the review subprocess dies when the runner process dies (child-lifetime binding, 4.4b): spawn a fake long child under a runner stand-in, kill the runner, assert the child is gone.

Prune:
- **P1** PG lock held by a competitor -> `contended`/`preserved`/not removed.
- **P2** flock held by a live runner (PG free) -> `contended`/`preserved`/not removed.
- **P3** both released -> `removed`.
- **P4** `LockUnavailable` / acquire-time `OperationalError` mid-apply -> `db-unreachable` refusal (not a raw raise).
- **P5** dry-run takes no lock/fuse, unchanged.

Keep + regression:
- **K1** `keep_worktree=True` -> `cleanup_status="kept"` AND both locks released (same-dispatch re-acquire succeeds) AND a later prune reclaims the kept succeeded+clean tree.
- **G1** full apex-jobs suite green (>= 142 + new tests); `test_prune.py` **byte-unchanged** (all new prune/contended tests live in a NEW module, e.g. `tests/test_review_worktree_lock.py`, since the uncontended path is a true no-op); auto-clean labels + exit codes byte-stable.

## 10. Deferred hardening / named follow-on

**apex-jobs agent-job worktree lifecycle lock lane** -- `run_agent_job` has the structurally identical startup `--force` race but preserves its worktree for a promotion gate, so the lock+fuse lifetime needs its own design pass. Also deferred: the optional heartbeat lock-connection-loss detector (Section 5) and an orphaned-`.lock` sweep. Not urgent under the single-worker dev deployment. Side benefit captured here: the minor prune-vs-auto-clean tail label race (1.2) is closed (auto-clean holds the flock through cleanup; a concurrent prune fails the fuse -> preserves).

## 11. Success criteria

1. `engine.review_worktree_lock`: dispatch-keyed, non-blocking, **explicitly autocommit**, value-silent on connect/acquire/config (`LockUnavailable` raised outside the except -> `__context__ is None`), guarded unlock AND close, auto-releases on session drop (E1-E9).
2. `agent_runner._worktree_flock`: dispatch-keyed non-blocking `flock`, O_CLOEXEC fd, fs-error fail-closed, kernel-released on process death (F1, F1b, F4).
3. `run_review_job`: PG lock -> flock -> `start()` -> git ops; a loser bails before `start()` (no run, no job.status write, no tree); startup `--force` only with both held; `codex` bound to the runner's lifetime (F2, F3, R1-R6).
4. `prune --apply`: PG lock + flock before its plain remove; `contended` preserve; removes once free (P1-P3); fail-closed broadened (P4).
5. Zero schema change; no prod DB mutation.
6. Existing behavior preserved: `test_prune.py` byte-unchanged (new tests in a new module), auto-clean labels/exit-codes stable, full suite green (G1, K1).
7. `run_agent_job` parity documented as a named follow-on (Section 10).

## 12. Statement

No implementation has begun. This document is the design only. Implementation follows an SDD plan (writing-plans) after the operator's spec-review gate.

## 13. Audit-resolution table

Cross-engine adversarial audit across two rounds. Round 1 (rev 1): 5 Claude auditors + Codex -> four blocking defects -> rev 2. Round 2 (rev 2): 3 Claude re-auditors + Codex -> the rev-2 ledger fix was incomplete + value-silence residuals + an orphaned-child gap -> rev 3. Both engines independently reached the round-2 blocking findings.

| # | Finding (severity) | Round / source | Resolution |
| --- | --- | --- | --- |
| 1 | Lock-liveness != process-liveness (T5): a dropped lock CONNECTION frees the PG lock while the PROCESS+`codex` live -> competitor `--force`-deletes a live tree. | R1, all 5 Claude + Codex | Narrow `flock` process-liveness fuse (4.3b) required at every destructive op (4.5/4.6); kernel-released on process death. |
| 2 | Ledger corruption via contended `report()` last-writer-wins. | R1 | (rev 2) `report_run_only`; superseded in rev 3 by #6. |
| 3 | Value-silence hole on the acquire path (raw psycopg escape). | R1 + R2 | 4.3: whole-acquire-body catch (transport + config), `LockUnavailable` raised outside the except (`__context__ is None`), guarded unlock AND close. Tests E5-E7. |
| 4 | Autocommit only commented. | R1 + R2 | 4.3: `conn.autocommit = True` explicit. Test E8. |
| 5 | NS-constant decimal wrong (false-green). | R1 Codex | 4.2: drop the decimal; ONE imported constant; assert E9. |
| 6 | **Rev-2 ledger fix INCOMPLETE:** a loser's `engine.start()` (before the lock) still demotes a succeeded job `running`, and `reap` cannot recover it (no running run). BLOCKING. | R2, Codex + Claude ledger | 4.4: move `engine.start()` INSIDE both locks -> a loser opens no run, never writes job.status; removes `report_run_only`. Test R5 rewritten. |
| 7 | `raise ... from None` sets `__suppress_context__` but leaves `__context__` live -> introspecting logger can leak the DSN. BLOCKING. | R2, Codex (+ Claude E5 precision) | 4.3: raise `LockUnavailable` OUTSIDE the except so `__context__ is None`; E5 asserts it. |
| 8 | Orphaned `codex` outlives a SIGKILLed runner -> flock releases (fd not inherited) but the child still uses the tree -> competitor deletes a live tree. BLOCKING. | R2, Codex (+ Claude O_CLOEXEC complement) | 4.4b: bind the `codex` child to the runner's lifetime (`PR_SET_PDEATHSIG`); 4.3b: explicit O_CLOEXEC fd. Test R6/F1b. |
| 9 | Unguarded `conn.close()` can mask a clean return + leak; acquire `except` too narrow (config `ValueError` escapes). IMPORTANT. | R2, Claude value-silence | 4.3: guard `close()`; broaden the acquire catch to `(psycopg.Error, OSError, ValueError, KeyError)`. Tests E6/E7. |
| 10 | `flock` `os.makedirs`/`os.open` `OSError` escaped raw + stranded the run. IMPORTANT. | R2, Codex + Claude | 4.3b: wrap fs setup -> fuse `False` (fail-closed, value-silent); moot after `start()` reorder. Test F4. |
| 11 | A continuing after PG-lock-loss auto-cleans its own tree without "both locks." IMPORTANT. | R2, Codex | 4.5: the flock (held) guards a removal; only startup `--force` additionally needs the PG lock (may target foreign residue). |
| -- | lockfile accumulation; hashtext collision = availability. LOW. | R1/R2 | Documented accepted (4.3b / 4.2); optional sweep deferred (Section 10). |

Confirmed sound by both engines (unchanged): `pg_try_advisory_lock(int4,int4)`+`hashtext` shape; lock-outside-`_WORKTREE_LOCK` (no deadlock); session locks survive commit; no schema/DDL/prod mutation; direct-DSN substrate; flock-not-unlinked (no inode race); prune lock ordering; disposable-scratch bounding.
