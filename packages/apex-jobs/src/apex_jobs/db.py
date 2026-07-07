"""DSN resolution + connection helper for apex-jobs.

Defaults to orchestration_dev on the host dev-pg (127.0.0.1:5432) as the
`orchestration` role. Override the database via APEX_JOBS_DB (tests use
orchestration_test) or the whole DSN via APEX_JOBS_DSN. The orchestration role
password is APEX_JOBS_PGPASSWORD, injected from Infisical (dev) -- e.g. via
infra/infisical/apex-jobs.sh; never committed to this PUBLIC repo.
"""
import os

import psycopg
from psycopg.rows import dict_row


def resolve_dsn() -> str:
    dsn = os.environ.get("APEX_JOBS_DSN")
    if dsn:
        return dsn
    db = os.environ.get("APEX_JOBS_DB", "orchestration_dev")
    pw = os.environ.get("APEX_JOBS_PGPASSWORD")
    if not pw:
        raise RuntimeError(
            "set APEX_JOBS_PGPASSWORD before running apex-jobs (or APEX_JOBS_DSN to "
            "override the whole DSN) -- inject it from Infisical, e.g. "
            "`infra/infisical/apex-jobs.sh <verb>`. DEV_PG_PASSWORD is the postgres "
            "superuser password and does NOT authenticate as the orchestration role."
        )
    host = os.environ.get("APEX_JOBS_HOST", "127.0.0.1")
    port = os.environ.get("APEX_JOBS_PORT", "5432")
    user = os.environ.get("APEX_JOBS_USER", "orchestration")
    return f"host={host} port={port} dbname={db} user={user} password={pw} sslmode=disable"


def connect():
    """A dict-row connection (autocommit off; callers manage the transaction)."""
    return psycopg.connect(resolve_dsn(), row_factory=dict_row)
