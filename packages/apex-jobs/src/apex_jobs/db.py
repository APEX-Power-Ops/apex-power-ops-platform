"""DSN resolution + connection helper for apex-jobs.

Defaults to orchestration_dev on the host dev-pg (127.0.0.1:5432) as the
`orchestration` role. Override the database via APEX_JOBS_DB (tests use
orchestration_test) or the whole DSN via APEX_JOBS_DSN. The dev password lives
in the gitignored infra/.env (DEV_PG_PASSWORD); never committed to this PUBLIC repo.
"""
import os

import psycopg
from psycopg.rows import dict_row


def resolve_dsn() -> str:
    dsn = os.environ.get("APEX_JOBS_DSN")
    if dsn:
        return dsn
    db = os.environ.get("APEX_JOBS_DB", "orchestration_dev")
    pw = os.environ.get("APEX_JOBS_PGPASSWORD") or os.environ.get("DEV_PG_PASSWORD")
    if not pw:
        raise RuntimeError(
            "set DEV_PG_PASSWORD (or APEX_JOBS_PGPASSWORD) before running apex-jobs "
            "-- e.g. `set -a; . infra/.env; set +a`. No hardcoded fallback (committed-secret hazard)."
        )
    host = os.environ.get("APEX_JOBS_HOST", "127.0.0.1")
    port = os.environ.get("APEX_JOBS_PORT", "5432")
    user = os.environ.get("APEX_JOBS_USER", "orchestration")
    return f"host={host} port={port} dbname={db} user={user} password={pw} sslmode=disable"


def connect():
    """A dict-row connection (autocommit off; callers manage the transaction)."""
    return psycopg.connect(resolve_dsn(), row_factory=dict_row)
