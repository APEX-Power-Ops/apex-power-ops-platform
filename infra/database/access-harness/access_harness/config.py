"""Config module for the Access Fidelity Harness.

Provides connection DSNs and helpers. Never prints or logs the password.
"""
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from psycopg import sql


def _normalize_dsn(dsn: str) -> str:
    """Strip driver prefix (postgresql+driver://) -> postgresql://."""
    return re.sub(r"^postgres(?:ql)?\+\w+://", "postgresql://", dsn)


def _with_db(dsn: str, dbname: str) -> str:
    """Return a new DSN with only the database path swapped. Netloc kept byte-identical."""
    p = urlparse(dsn)
    return urlunparse(p._replace(path="/" + dbname))


def pg_dsn() -> str:
    """Return the staging DSN (normalized from ACCESS_HARNESS_SUPERUSER_DSN)."""
    raw = os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN")
    if not raw:
        raise RuntimeError(
            "ACCESS_HARNESS_SUPERUSER_DSN is not set. "
            "Export a postgres superuser DSN before running."
        )
    return _normalize_dsn(raw)


def test_pg_dsn() -> str:
    """Return a DSN pointing at tcc_fidelity_test (derived from pg_dsn())."""
    return _with_db(pg_dsn(), "tcc_fidelity_test")


def frozen_dir() -> Path:
    """Return the path to the frozen Access copies directory."""
    env_val = os.environ.get("ACCESS_HARNESS_FROZEN_DIR")
    if env_val:
        return Path(env_val)
    return Path(r"D:\_access_frozen")


def apply_sql(conn, path: Path) -> None:
    """Execute a SQL file against an open psycopg connection (autocommit must be on)."""
    sql_text = Path(path).read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql_text)


GOVERNED_DB = "tcc_fidelity_governed"


def governed_pg_dsn() -> str:
    """Return a DSN pointing at tcc_fidelity_governed (derived from pg_dsn()).

    Mirrors test_pg_dsn(): only the database path is swapped; the netloc
    (user / host / port) stays byte-identical to the base DSN.
    """
    return _with_db(pg_dsn(), GOVERNED_DB)


def assert_current_database(conn, expected: str) -> None:
    """Raise RuntimeError unless conn.current_database() == expected.

    The fail-closed fence for governed runs: a governed command must refuse to
    do any work unless it is actually connected to `expected`.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        (current,) = cur.fetchone()
    if current != expected:
        raise RuntimeError(
            f"DATABASE FENCE VIOLATION: connected to '{current}' but this "
            f"operation requires '{expected}'. Refusing to proceed."
        )


def ensure_database(admin_conn, dbname: str) -> bool:
    """CREATE DATABASE dbname if it does not exist. Idempotent; never drops.

    admin_conn must be an AUTOCOMMIT psycopg connection to a DIFFERENT database
    (CREATE DATABASE cannot run inside a transaction block). Returns True if it
    created the database, False if it already existed. The dbname is embedded via
    psycopg.sql.Identifier (never an f-string) so it is safely quoted.
    """
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is not None:
            return False
        cur.execute(
            sql.SQL("CREATE DATABASE {db}").format(db=sql.Identifier(dbname))
        )
    return True
