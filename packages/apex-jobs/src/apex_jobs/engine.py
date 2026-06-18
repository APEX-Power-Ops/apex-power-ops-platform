"""apex-jobs engine - the queue + ledger + gate operations over the jobs schema.

psycopg3, raw SQL (the queue logic is transaction/locking-centric). Each call
opens its own dict-row connection and manages the transaction explicitly.
"""
import psycopg
from psycopg.types.json import Jsonb

from . import db


def _conn():
    return psycopg.connect(db.resolve_dsn(), row_factory=psycopg.rows.dict_row)


def enqueue(dispatch_id, title, payload=None, target="any", priority=100,
            predecessor_id=None, authority="gated", requires_approval=False,
            gate_categories=None, env_required="any", created_by=None,
            closeout_path=None):
    """Insert (or idempotently no-op on dispatch_id) a queue item. Returns its id."""
    payload = payload if payload is not None else {}
    gate_categories = gate_categories or []
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
                returning id
                """,
                (dispatch_id, title, target, priority, predecessor_id, authority,
                 requires_approval, gate_categories, env_required, Jsonb(payload),
                 created_by, closeout_path),
            )
            jid = cur.fetchone()["id"]
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
