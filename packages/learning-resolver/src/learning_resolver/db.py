"""learning_dev connection (read-only). DSN pinned so ambient PG env (which points at
prod) cannot redirect us -- mirrors the ops-intake pattern."""
import os

import psycopg


def dsn() -> str:
    return os.environ.get("LEARNING_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=learning_dev user=postgres "
        f"password={os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


def connect() -> "psycopg.Connection":
    # read-only enforced at the session level; autocommit avoids idle transactions.
    conn = psycopg.connect(dsn(), autocommit=True)
    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    return conn
