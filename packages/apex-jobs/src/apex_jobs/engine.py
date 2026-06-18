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
import psycopg
from psycopg.types.json import Jsonb

from . import db


class GateError(Exception):
    """Raised when an env or human-approval gate blocks a job from running."""


def _conn():
    return psycopg.connect(db.resolve_dsn(), row_factory=psycopg.rows.dict_row)


def enqueue(dispatch_id, title, payload=None, target="any", priority=100,
            predecessor_id=None, authority="gated", requires_approval=False,
            gate_categories=None, env_required="any", created_by=None,
            closeout_path=None):
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
                   created_by, closeout_path)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (dispatch_id) do update set title = excluded.title
                returning id, (xmax = 0) as inserted
                """,
                (dispatch_id, title, target, priority, predecessor_id, authority,
                 requires_approval, gate_categories, env_required, Jsonb(payload),
                 created_by, closeout_path),
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
                  and (j.predecessor_id is null
                       or exists (select 1 from jobs.job p
                                  where p.id = j.predecessor_id and p.status = 'succeeded'))
                  and not exists (select 1 from jobs.gate g
                                  where g.job_id = j.id and g.state = 'pending')
                order by j.priority asc, j.dispatch_id asc
                limit 1
                for update skip locked
                """
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
    return _decide_gate(gate_id, "approved", by, note)


def reject(gate_id, by, note=None):
    return _decide_gate(gate_id, "rejected", by, note)


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
                "insert into jobs.run (job_id, attempt, claimed_by, env, status, started_at) "
                "values (%s, %s, %s, %s, 'running', now()) returning id",
                (job_id, attempt, claimed_by, run_env),
            )
            run_id = cur.fetchone()["id"]
            cur.execute("update jobs.job set status='running', updated_at=now() "
                        "where id=%s", (job_id,))
        conn.commit()
    return run_id
