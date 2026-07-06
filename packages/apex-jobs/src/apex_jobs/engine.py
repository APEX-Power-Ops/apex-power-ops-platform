"""apex-jobs engine - queue + ledger + gate operations over the jobs schema (psycopg3).

Raw SQL (the queue logic is transaction/locking-centric). Each call opens its own
dict-row connection and manages the transaction explicitly.

Gate model:
  * human-approval gate: enqueue() creates pending jobs.gate rows for a job that
    requires_approval / names gate_categories. v_eligible (and claim()) exclude any
    job with an open gate, so it is not claimable until the operator approves -
    enforcing "no execution before approval" at the queue boundary.
  * env gate: start() refuses to open a run unless the claiming worker's run_env
    matches the job's env_required (the sandbox|host trust evidence).
"""
import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager

import psycopg
from psycopg.types.json import Jsonb

from . import db

_log = logging.getLogger(__name__)

# Visibility-timeout for crash recovery. A run whose lease expires (worker died,
# no heartbeat) is reaped and requeued/failed. Generous by default; agent runs
# extend it via heartbeat().
LEASE_TTL_S = int(os.environ.get("APEX_JOBS_LEASE_TTL_S", "1800"))


class GateError(Exception):
    """Raised when an env or human-approval gate blocks a job from running."""


def _conn():
    return psycopg.connect(db.resolve_dsn(), row_factory=psycopg.rows.dict_row)


def enqueue(dispatch_id, title, payload=None, target="any", priority=100,
            predecessor_id=None, authority="gated", requires_approval=False,
            gate_categories=None, env_required="any", created_by=None,
            closeout_path=None, kind="command", max_attempts=1, base_ref=None):
    """Insert (idempotent on dispatch_id) a queue item. On first insert, create
    the matching pending gate rows if approval is required. Returns the job id."""
    payload = payload if payload is not None else {}
    gate_categories = list(gate_categories or [])
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into jobs.job
                  (dispatch_id, title, target, priority, predecessor_id, authority,
                   requires_approval, gate_categories, env_required, payload,
                   created_by, closeout_path, kind, max_attempts, base_ref)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (dispatch_id) do update set title = excluded.title
                returning id, (xmax = 0) as inserted
                """,
                (dispatch_id, title, target, priority, predecessor_id, authority,
                 requires_approval, gate_categories, env_required, Jsonb(payload),
                 created_by, closeout_path, kind, max_attempts, base_ref),
            )
            r = cur.fetchone()
            jid, inserted = r["id"], r["inserted"]
            if inserted:
                gates = list(gate_categories)
                if requires_approval and not gates:
                    gates = ["approval"]
                for gt in gates:
                    cur.execute(
                        "insert into jobs.gate (job_id, gate_type) values (%s, %s)",
                        (jid, gt),
                    )
        conn.commit()
    return jid


def get_job(ident):
    """Fetch a job row (dict) by id (uuid) or dispatch_id. None if absent."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select * from jobs.job where id::text = %s or dispatch_id = %s",
                (str(ident), str(ident)),
            )
            return cur.fetchone()


def claim(as_=None, env=None):
    """Atomically claim the highest-priority eligible job (priority asc, then
    dispatch_id asc) via FOR UPDATE SKIP LOCKED on jobs.job, so concurrent
    claimers never double-claim. Returns the claimed job (dict) or None."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id from jobs.job j
                where j.status = 'pending'
                  and (%(env)s::text is null or j.env_required = 'any'
                       or j.env_required::text = %(env)s::text)
                  and (j.predecessor_id is null
                       or exists (select 1 from jobs.job p
                                  where p.id = j.predecessor_id and p.status = 'succeeded'))
                  and not exists (select 1 from jobs.gate g
                                  where g.job_id = j.id and g.state = 'pending')
                order by j.priority asc, j.dispatch_id asc
                limit 1
                for update skip locked
                """,
                {"env": env},
            )
            row = cur.fetchone()
            if not row:
                conn.commit()
                return None
            cur.execute(
                "update jobs.job set status='claimed', updated_at=now() "
                "where id=%s returning *",
                (row["id"],),
            )
            job = cur.fetchone()
        conn.commit()
    return job


def request_gate(job_id, gate_type, note=None):
    """Create a pending human-approval gate on a job. Returns the gate id."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into jobs.gate (job_id, gate_type, note) "
                "values (%s, %s, %s) returning id",
                (job_id, gate_type, note),
            )
            gid = cur.fetchone()["id"]
        conn.commit()
    return gid


def _decide_gate(gate_id, state, by, note):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.gate set state=%s, decided_at=now(), decided_by=%s, "
                "note=coalesce(%s, note) where id=%s returning id",
                (state, by, note, gate_id),
            )
            r = cur.fetchone()
        conn.commit()
    if r is None:
        raise ValueError(f"gate {gate_id} not found")
    return r["id"]


def approve(gate_id, by, note=None):
    gid = _decide_gate(gate_id, "approved", by, note)
    # Lifecycle closure: a job parked 'awaiting_approval' becomes claimable again
    # once it has no remaining open gate. awaiting_promotion is left untouched - it
    # flows to promote(), not back to pending.
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update jobs.job j set status='pending', updated_at=now()
                from jobs.gate g
                where g.id=%s and j.id=g.job_id and j.status='awaiting_approval'
                  and not exists (select 1 from jobs.gate g2
                                  where g2.job_id=j.id and g2.state='pending')
                """,
                (gate_id,),
            )
        conn.commit()
    return gid


def reject(gate_id, by, note=None):
    return _decide_gate(gate_id, "rejected", by, note)


def unblock(ident):
    """Return a blocked job to pending (re-claimable). Returns the job id or None."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.job set status='pending', updated_at=now() "
                "where (id::text=%s or dispatch_id=%s) and status='blocked' returning id",
                (str(ident), str(ident)),
            )
            r = cur.fetchone()
        conn.commit()
    return r["id"] if r else None


def start(job_id, claimed_by, run_env):
    """Open a run for a claimed job, enforcing the env + human-approval gates.
    Raises GateError (parking the job 'blocked'/'awaiting_approval') if a gate is
    unsatisfied. Returns the new run id."""
    if run_env not in ("sandbox", "host"):
        raise ValueError("run_env must be 'sandbox' or 'host'")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("select * from jobs.job where id=%s for update", (job_id,))
            job = cur.fetchone()
            if job is None:
                raise ValueError(f"job {job_id} not found")
            if job["env_required"] != "any" and run_env != job["env_required"]:
                cur.execute("update jobs.job set status='blocked', updated_at=now() "
                            "where id=%s", (job_id,))
                conn.commit()
                raise GateError(
                    f"env gate: job requires env={job['env_required']}, worker env={run_env}")
            cur.execute("select count(*) as n from jobs.gate "
                        "where job_id=%s and state='pending'", (job_id,))
            if cur.fetchone()["n"] > 0:
                cur.execute("update jobs.job set status='awaiting_approval', "
                            "updated_at=now() where id=%s", (job_id,))
                conn.commit()
                raise GateError("human gate: open approval gate(s) pending")
            cur.execute("select coalesce(max(attempt), 0) + 1 as a "
                        "from jobs.run where job_id=%s", (job_id,))
            attempt = cur.fetchone()["a"]
            cur.execute(
                "insert into jobs.run (job_id, attempt, claimed_by, env, status, "
                "started_at, lease_expires_at, heartbeat_at) "
                "values (%s, %s, %s, %s, 'running', now(), "
                "now() + (%s || ' seconds')::interval, now()) returning id",
                (job_id, attempt, claimed_by, run_env, str(LEASE_TTL_S)),
            )
            run_id = cur.fetchone()["id"]
            cur.execute("update jobs.job set status='running', updated_at=now() "
                        "where id=%s", (job_id,))
        conn.commit()
    return run_id


def report(run_id, exit_code, result=None, log_ref=None):
    """Finalize a run: set its terminal status from the exit code, stamp
    finished_at + result, and propagate the status to the owning job. Returns
    the terminal status ('succeeded' | 'failed')."""
    status = "succeeded" if exit_code == 0 else "failed"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set status=%s, finished_at=now(), exit_code=%s, "
                "result=%s, log_ref=coalesce(%s, log_ref) where id=%s returning job_id",
                (status, exit_code, Jsonb(result) if result is not None else None,
                 log_ref, run_id),
            )
            r = cur.fetchone()
            if r is None:
                raise ValueError(f"run {run_id} not found")
            cur.execute("update jobs.job set status=%s, updated_at=now() where id=%s",
                        (status, r["job_id"]))
        conn.commit()
    return status


def heartbeat(run_id, lease_ttl_s=LEASE_TTL_S):
    """Extend a running run's lease (called periodically during long agent runs)."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set heartbeat_at=now(), "
                "lease_expires_at = now() + (%s || ' seconds')::interval "
                "where id=%s and status='running'",
                (str(lease_ttl_s), run_id),
            )
        conn.commit()


def reap():
    """Fail lease-expired running runs; requeue the owning job to pending if it has
    attempts left (run count < max_attempts), else mark it failed. Idempotent.
    Returns the number of runs reaped."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select r.id as run_id, r.job_id, j.max_attempts,
                       (select count(*) from jobs.run r2 where r2.job_id = j.id) as attempts
                from jobs.run r join jobs.job j on j.id = r.job_id
                where r.status = 'running' and r.lease_expires_at is not null
                  and r.lease_expires_at < now()
                for update skip locked
                """
            )
            rows = cur.fetchall()
            for row in rows:
                cur.execute(
                    "update jobs.run set status='failed', finished_at=now(), "
                    "result = coalesce(result, '{}'::jsonb) "
                    "|| jsonb_build_object('reaped', 'lease_expired') where id=%s",
                    (row["run_id"],),
                )
                new_status = "pending" if row["attempts"] < row["max_attempts"] else "failed"
                cur.execute("update jobs.job set status=%s, updated_at=now() where id=%s",
                            (new_status, row["job_id"]))
        conn.commit()
    return len(rows)


def set_base_ref(job_id, base_ref):
    """Persist the resolved base_ref when a job was enqueued without one (promote needs it)."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("update jobs.job set base_ref=%s, updated_at=now() "
                        "where id=%s and base_ref is null", (base_ref, job_id))
        conn.commit()


def set_run_artifacts(run_id, worktree_path=None, branch=None, diff_stat=None):
    """Record an agent run's worktree/branch/diff_stat on the run row."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set worktree_path=coalesce(%s, worktree_path), "
                "branch=coalesce(%s, branch), diff_stat=coalesce(%s, diff_stat) where id=%s",
                (worktree_path, branch, diff_stat, run_id),
            )
        conn.commit()


def run_is_current(run_id):
    """True if run_id is the highest-attempt run for its job (not superseded by a newer
    attempt). False if not found. Backs the same-process auto-clean currency guard."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select (r.attempt = (select max(attempt) from jobs.run r2 "
                "where r2.job_id = r.job_id)) as is_current "
                "from jobs.run r where r.id = %s", (run_id,))
            row = cur.fetchone()
    return bool(row and row["is_current"])


def set_run_cleanup(run_id, cleanup_status):
    """Merge cleanup_status into the run's result JSONB (no schema change). ORTHOGONAL to
    run status: never changes status, finished_at, exit_code, or the process exit."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.run set result = coalesce(result, '{}'::jsonb) "
                "|| jsonb_build_object('cleanup_status', %s::text) where id=%s",
                (cleanup_status, run_id))
        conn.commit()


def set_job_keep_worktree(job_id):
    """Monotonically set payload.keep_worktree=true on a job: OR-merges the flag into the
    existing payload JSONB (never clears it, never clobbers other payload keys). Called only
    when an explicit --keep-worktree is passed, so a keep request is honored even when
    enqueue() took the existing-dispatch conflict path (which updates title only)."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update jobs.job set payload = coalesce(payload, '{}'::jsonb) "
                "|| jsonb_build_object('keep_worktree', true), updated_at=now() where id=%s",
                (job_id,))
        conn.commit()


def open_promotion(job_id):
    """Create a pending promotion gate + move the job to awaiting_promotion. Returns gate id."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("insert into jobs.gate (job_id, gate_type) values (%s, 'promotion') "
                        "returning id", (job_id,))
            gid = cur.fetchone()["id"]
            cur.execute("update jobs.job set status='awaiting_promotion', updated_at=now() "
                        "where id=%s", (job_id,))
        conn.commit()
    return gid


def list_eligible():
    """Claimable jobs in claim order (priority asc, dispatch_id asc)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("select dispatch_id, title, priority, target from jobs.v_eligible")
        return cur.fetchall()


def runs_for(ident):
    """All runs for a job (by id or dispatch_id), oldest attempt first."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select r.* from jobs.run r join jobs.job j on j.id = r.job_id "
            "where j.id::text = %s or j.dispatch_id = %s order by r.attempt",
            (str(ident), str(ident)),
        )
        return cur.fetchall()


def gates_for(ident):
    """All gates for a job (by id or dispatch_id), oldest first."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select g.id, g.gate_type, g.state from jobs.gate g "
            "join jobs.job j on j.id = g.job_id "
            "where j.id::text = %s or j.dispatch_id = %s order by g.requested_at",
            (str(ident), str(ident)),
        )
        return cur.fetchall()


def get_gate(gate_id):
    """Fetch a single gate row (id, job_id, gate_type, state) by id. None if absent."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, job_id, gate_type, state from jobs.gate where id::text = %s",
            (str(gate_id),),
        )
        return cur.fetchone()


# ---------------------------------------------------------------------------
# Promotion — the operator-gated firewall that merges (or discards) a reviewed
# agent branch into its base_ref. Hardened per the T6 adversarial design review:
# protected-ref + checked-out + null/existence guards, an atomic status
# precondition (row lock), a no-ff merge in a throwaway DETACHED worktree, a
# compare-and-swap base advance, promotion-gate closure, and DB-as-commit-point
# ordering so the irreversible branch delete only runs after the DB is durable.
# NEVER advances main/master. Git plumbing shares agent_runner._WORKTREE_LOCK so
# it cannot race the concurrent run_pool.
# ---------------------------------------------------------------------------
_DEFAULT_REPO = os.path.expanduser("~/code/apex/apex-orch-lane")


class PromoteError(Exception):
    """Base class for promotion failures."""


class PromoteRefused(PromoteError):
    """A precondition guard refused the promotion; base + branch are untouched and
    the job stays awaiting_promotion (the gate stays pending)."""


class PromoteConflict(PromoteError):
    """The merge could not be applied (conflict) or base moved concurrently
    (compare-and-swap failed); base is untouched, the job branch is retained for
    fixup, the job stays awaiting_promotion."""


class PromoteNoChanges(PromoteError):
    """The job branch has nothing to merge into base (already up to date); the
    branch is preserved and the job stays awaiting_promotion."""


def _resolve_repo(repo):
    return repo or os.environ.get("APEX_JOBS_REPO", _DEFAULT_REPO)


def _protected_refs():
    extra = {r.strip() for r in os.environ.get("APEX_JOBS_PROTECTED_REFS", "").split(",") if r.strip()}
    return {"main", "master"} | extra


def _git(*args, cwd, check=True):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, check=check)


def _ref_sha(repo, ref):
    """Sha of a ref, or None if it does not resolve."""
    r = _git("rev-parse", "--verify", "--quiet", ref, cwd=repo, check=False)
    return r.stdout.strip() or None


def _branch_checked_out(repo, branch):
    """True if refs/heads/<branch> is the checked-out branch of any worktree."""
    want = f"branch refs/heads/{branch}"
    out = _git("worktree", "list", "--porcelain", cwd=repo, check=False).stdout
    return any(line.strip() == want for line in out.splitlines())


def _worktree_path_for_branch(repo, branch):
    """Filesystem path of the worktree whose HEAD is refs/heads/<branch>, or None."""
    want = f"branch refs/heads/{branch}"
    path = None
    for line in _git("worktree", "list", "--porcelain", cwd=repo, check=False).stdout.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.strip() == want:
            return path
    return None


def _advance_base_ref(repo, base, newsha, oldsha):
    """Compare-and-swap advance of refs/heads/<base> from oldsha to newsha. Returns
    the CompletedProcess; returncode != 0 means base no longer pointed at oldsha
    (a concurrent advance) and the ref was NOT moved. Factored out as a seam so a
    test can simulate a racing advance."""
    return _git("update-ref", f"refs/heads/{base}", newsha, oldsha, cwd=repo, check=False)


def _commit_promotion(conn, cur, job_id, by):
    """Record a successful promotion (job succeeded + promotion gate approved) and
    commit. Factored out as a seam so a test can inject a post-CAS DB failure and
    verify that promote() rolls the base ref back."""
    cur.execute("update jobs.job set status='succeeded', updated_at=now() where id=%s", (job_id,))
    cur.execute("update jobs.gate set state='approved', decided_at=now(), decided_by=%s "
                "where job_id=%s and gate_type='promotion' and state='pending'", (by, job_id))
    conn.commit()


def _is_prior_promote_merge(repo, base, branch, dispatch_id):
    """True if base's tip is the merge a PRIOR promote() of this job created (second
    parent == the job branch tip, subject == the promote marker). Signals that base
    was advanced but the DB commit never landed (a hard crash between the CAS and
    the commit), so a re-promote should finish the DB side idempotently rather than
    wedging the job at awaiting_promotion. Migration-free crash recovery."""
    branch_sha = _ref_sha(repo, f"refs/heads/{branch}")
    if branch_sha is None:
        return False
    if _ref_sha(repo, f"refs/heads/{base}^2") != branch_sha:
        return False
    subject = _git("log", "-1", "--format=%s", f"refs/heads/{base}", cwd=repo, check=False).stdout.strip()
    return subject == f"promote {dispatch_id}"


def promote(ident, by="operator", repo=None):
    """Merge the reviewed agent branch job/<dispatch_id> into its base_ref via a
    --no-ff merge built in a throwaway detached worktree, then advance base with a
    compare-and-swap. Operator-gated firewall: refuses null / protected (main,
    master, $APEX_JOBS_PROTECTED_REFS) / checked-out bases and any job not in
    awaiting_promotion. On success: base advanced, promotion gate approved, job
    succeeded, the job worktree + branch removed. Raises PromoteRefused /
    PromoteConflict / PromoteNoChanges (each leaves base + branch intact). Returns
    the new base sha."""
    from . import agent_runner   # lazy: agent_runner imports engine, so avoid a top-level cycle
    repo = _resolve_repo(repo)
    job = get_job(ident)
    if job is None:
        raise PromoteRefused(f"no such job: {ident}")
    base = (job.get("base_ref") or "").strip()
    if base.startswith("refs/heads/"):
        base = base[len("refs/heads/"):]
    branch = f"job/{job['dispatch_id']}"

    # --- pre-flight guards (no mutation; firewall lives here, in CODE not docs) ---
    if not base:
        raise PromoteRefused("job has no base_ref")
    if base in _protected_refs():
        raise PromoteRefused(f"refusing to promote to protected ref {base!r} "
                             "(main/master is gated by a separate operator step)")
    if _ref_sha(repo, f"refs/heads/{base}") is None:
        raise PromoteRefused(f"base ref does not exist: {base}")
    if _branch_checked_out(repo, base):
        raise PromoteRefused(f"{base} is checked out in a worktree; "
                             "base_ref must be a non-checked-out branch")
    if _ref_sha(repo, f"refs/heads/{branch}") is None:
        raise PromoteRefused(f"no agent branch to promote: {branch} "
                             "(already promoted/discarded, or the run produced none)")

    lock = agent_runner._WORKTREE_LOCK
    with _conn() as conn, conn.cursor() as cur:
        # Atomic precondition: claim the awaiting_promotion job under a row lock, so
        # a second/concurrent promote sees a non-awaiting status and refuses.
        cur.execute("select status from jobs.job where id=%s for update", (job["id"],))
        row = cur.fetchone()
        if row is None or row["status"] != "awaiting_promotion":
            conn.rollback()
            raise PromoteRefused(
                f"job not in awaiting_promotion (status={row['status'] if row else None})")

        oldsha = _ref_sha(repo, f"refs/heads/{base}")
        tmp = tempfile.mkdtemp(prefix="apex-promote-")
        newsha = None
        try:
            with lock:
                _git("worktree", "add", "--detach", tmp, oldsha, cwd=repo)
            # merge runs in the isolated tmp worktree -> safe to run UNLOCKED (it
            # touches only tmp's index, never the real base or any live worktree).
            m = _git("merge", "--no-ff", "-m", f"promote {job['dispatch_id']}",
                     branch, cwd=tmp, check=False)
            after = _git("rev-parse", "HEAD", cwd=tmp, check=False).stdout.strip()
            if m.returncode != 0:
                _git("merge", "--abort", cwd=tmp, check=False)
                conn.rollback()
                raise PromoteConflict(
                    f"merge of {branch} into {base} failed: "
                    f"{(m.stdout + m.stderr).strip()[:500]}")
            if after != oldsha:
                # a real merge commit was created -> advance base. Re-check the
                # not-checked-out guard here (inside the tx) to close the TOCTOU on
                # the entry-time guard, then compare-and-swap.
                if _branch_checked_out(repo, base):
                    conn.rollback()
                    raise PromoteRefused(f"{base} became checked out during promote")
                newsha = after
                with lock:
                    cas = _advance_base_ref(repo, base, newsha, oldsha)
                if cas.returncode != 0:
                    conn.rollback()
                    raise PromoteConflict(
                        f"{base} advanced concurrently; re-promote against the new base: "
                        f"{cas.stderr.strip()[:300]}")
            elif _is_prior_promote_merge(repo, base, branch, job["dispatch_id"]):
                # crash recovery: a prior promote already advanced base with this
                # job's merge but the DB commit never landed -> finish the DB side
                # idempotently (base is already at the merge; do NOT advance again).
                newsha = oldsha
            else:
                conn.rollback()
                raise PromoteNoChanges(f"{branch} has nothing to merge into {base}")
        finally:
            with lock:
                _git("worktree", "remove", "--force", tmp, cwd=repo, check=False)
            shutil.rmtree(tmp, ignore_errors=True)

        # base advanced -> record success atomically (DB commit is the commit point).
        try:
            _commit_promotion(conn, cur, job["id"], by)
        except Exception:
            with lock:                      # undo the irreversible base advance on a record-keeping failure
                rb = _advance_base_ref(repo, base, oldsha, newsha)
            if rb.returncode != 0:          # could not restore base -> needs operator attention
                _log.error("promote: base rollback failed for %s (base may be advanced "
                           "without a succeeded job): %s", base, rb.stderr.strip())
            conn.rollback()
            raise

    # DB is durable -> best-effort cleanup (a crash here leaves a recoverable orphan branch).
    with lock:
        wt = _worktree_path_for_branch(repo, branch)
        if wt:
            _git("worktree", "remove", "--force", wt, cwd=repo, check=False)
        _git("branch", "-D", branch, cwd=repo, check=False)
    return newsha


def discard_promotion(ident, by="operator", repo=None):
    """Reject a reviewed agent branch: snapshot its tip to refs/discarded/<id>
    (recoverable), mark the job cancelled + the promotion gate rejected (DB commit
    point), then remove the worktree + force-delete the branch. base_ref is never
    touched. Raises PromoteRefused if the job is not awaiting_promotion. Returns
    the saved tip sha (or None)."""
    from . import agent_runner   # lazy: avoid the engine<->agent_runner cycle
    repo = _resolve_repo(repo)
    job = get_job(ident)
    if job is None:
        raise PromoteRefused(f"no such job: {ident}")
    branch = f"job/{job['dispatch_id']}"
    lock = agent_runner._WORKTREE_LOCK
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("select status from jobs.job where id=%s for update", (job["id"],))
        row = cur.fetchone()
        if row is None or row["status"] != "awaiting_promotion":
            conn.rollback()
            raise PromoteRefused(
                f"job not in awaiting_promotion (status={row['status'] if row else None})")
        # snapshot the tip BEFORE any destructive op so a mistaken discard is recoverable
        tip = _ref_sha(repo, f"refs/heads/{branch}")
        if tip:
            with lock:
                _git("update-ref", f"refs/discarded/{job['dispatch_id']}", tip, cwd=repo, check=False)
        cur.execute("update jobs.job set status='cancelled', updated_at=now() where id=%s",
                    (job["id"],))
        cur.execute("update jobs.gate set state='rejected', decided_at=now(), decided_by=%s "
                    "where job_id=%s and gate_type='promotion' and state='pending'",
                    (by, job["id"]))
        conn.commit()
    # DB durable -> now the irreversible removals (crash here = recoverable orphan + the snapshot ref).
    with lock:
        wt = _worktree_path_for_branch(repo, branch)
        if wt:
            _git("worktree", "remove", "--force", wt, cwd=repo, check=False)
        _git("branch", "-D", branch, cwd=repo, check=False)
    return tip


def list_promotions():
    """Jobs parked at awaiting_promotion, with their latest run's diff_stat /
    worktree_path for operator review (newest first)."""
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select j.dispatch_id, j.title, j.base_ref, "
            "       r.branch, r.worktree_path, r.diff_stat "
            "from jobs.job j "
            "left join lateral (select branch, worktree_path, diff_stat from jobs.run "
            "                   where job_id=j.id order by attempt desc limit 1) r on true "
            "where j.status='awaiting_promotion' order by j.updated_at desc")
        return cur.fetchall()


def review_dispatch_statuses(dispatch_ids):
    """Per-dispatch DB status for prune classification, keyed on dispatch_id
    (UNIQUE in jobs.job). Returns {dispatch_id: {is_review, any_running, status,
    claimed_at, finished_at}} for every input id that HAS a jobs.job row; ids
    with no job row are absent (-> orphan). is_review = codex-review job
    (kind='agent' AND payload.review_head is a non-empty JSON string, matching
    the runner's truthiness routing). any_running = any run for the job
    is status='running' (regardless of lease). status/claimed_at/finished_at come
    from the LATEST run by (claimed_at DESC, attempt DESC). One query. Raises
    psycopg.OperationalError/InterfaceError on connection failure."""
    if not dispatch_ids:
        return {}
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select j.dispatch_id, "
            "       coalesce(j.kind = 'agent' and jsonb_typeof(j.payload -> 'review_head') = 'string' "
            "                and (j.payload ->> 'review_head') <> '', false) as is_review, "
            "       exists (select 1 from jobs.run r "
            "               where r.job_id = j.id and r.status = 'running') as any_running, "
            "       lr.status, lr.claimed_at, lr.finished_at "
            "from jobs.job j "
            "left join lateral (select status, claimed_at, finished_at from jobs.run "
            "                   where job_id = j.id "
            "                   order by claimed_at desc, attempt desc limit 1) lr on true "
            "where j.dispatch_id = any(%s)",
            (list(dispatch_ids),),
        )
        return {r["dispatch_id"]: {
            "is_review": r["is_review"],
            "any_running": r["any_running"],
            "status": r["status"],
            "claimed_at": r["claimed_at"],
            "finished_at": r["finished_at"],
        } for r in cur.fetchall()}


class LockUnavailable(Exception):
    """Cannot establish PG dispatch ownership (connect/acquire/config failed).
    Value-silent: carries NO underlying psycopg/DSN text and NO chained
    __context__ (raised outside the except block)."""


_REVIEW_WT_LOCK_NS = 0x52565754  # ASCII 'RVWT'; the ONE namespace constant (imported everywhere)


@contextmanager
def review_worktree_lock(dispatch_id):
    """Cross-process COORDINATOR for runs/<dispatch_id>. Dedicated autocommit
    connection; non-blocking session advisory lock. Yields the acquired bool.
    Value-silent: any transport OR resolve_dsn config failure at connect/acquire
    raises LockUnavailable (raised outside the except so __context__ is None).
    The unlock and both close() sites are guarded so neither masks a caller return."""
    conn = None
    acquired = False
    failed = False
    try:
        conn = _conn()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s, hashtext(%s)) as ok",
                        (_REVIEW_WT_LOCK_NS, dispatch_id))
            acquired = bool(cur.fetchone()["ok"])
    except (psycopg.Error, OSError, ValueError, KeyError, RuntimeError):
        failed = True
    if failed:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
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
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


def release_claim(job_id):
    """Value-silent CAS: return a still-CLAIMED job to 'pending' so a contended
    pool-claimed review (which opened no run) is never stranded. No-op if a winner
    already advanced the job to running/terminal (WHERE status='claimed'), so it can
    never overwrite live or finished work."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("update jobs.job set status='pending', updated_at=now() "
                        "where id=%s and status='claimed'", (job_id,))
        conn.commit()
