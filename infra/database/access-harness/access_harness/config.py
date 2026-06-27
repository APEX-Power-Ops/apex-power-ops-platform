"""Config module for the Access Fidelity Harness.

Provides connection DSNs and helpers. Never prints or logs the password.
"""
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse


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
