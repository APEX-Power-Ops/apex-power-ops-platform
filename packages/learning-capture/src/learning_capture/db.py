"""learning_dev connection (read-WRITE) for the capture path. DSN pinned so ambient PG env
(which points at prod) cannot redirect us -- mirrors learning-resolver/ops-intake, but withOUT the
read-only session: capture writes."""
import os

import psycopg


def dsn() -> str:
    return os.environ.get("LEARNING_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=learning_dev user=postgres "
        f"password={os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


def connect() -> "psycopg.Connection":
    # autocommit: each INSERT commits immediately; no idle transaction.
    return psycopg.connect(dsn(), autocommit=True)
