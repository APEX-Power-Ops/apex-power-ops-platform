"""Tests for access_harness.cli connection plumbing.

Codex P2 (fix 2): every CLI subcommand connects via _pg_dsn_from_env(), but that
helper passed the RAW ACCESS_HARNESS_SUPERUSER_DSN straight to psycopg.connect.
config.pg_dsn() strips a SQLAlchemy-style postgresql+psycopg:// / +asyncpg://
driver prefix; psycopg.connect does NOT understand that prefix.  So with a
+driver DSN every CLI subcommand failed to connect while the tests (which go
through config.pg_dsn()/test_pg_dsn()) worked.  The CLI must normalise identically.
"""
import os

import psycopg
import pytest

from access_harness import cli
from access_harness import config


def _base_dsn() -> str:
    raw = os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN")
    if not raw:
        pytest.skip("ACCESS_HARNESS_SUPERUSER_DSN unset")
    # Normalise to a clean postgresql:// base regardless of how it is exported.
    return config.pg_dsn()


def test_cli_dsn_strips_driver_prefix(monkeypatch):
    """A postgresql+psycopg:// env value must yield a prefix-free DSN through the
    CLI's own connection path (the same normalisation config.pg_dsn() applies)."""
    base = _base_dsn()  # clean postgresql://user:pw@host/db
    plus_dsn = base.replace("postgresql://", "postgresql+psycopg://", 1)
    assert plus_dsn.startswith("postgresql+psycopg://")

    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", plus_dsn)

    resolved = cli._pg_dsn_from_env()
    assert not resolved.startswith("postgresql+psycopg://"), (
        f"CLI DSN must strip the +driver prefix, got {resolved!r}"
    )
    assert resolved.startswith("postgresql://"), (
        f"CLI DSN must normalise to postgresql://, got {resolved!r}"
    )


def test_cli_dsn_is_psycopg_connectable_through_cli_path(monkeypatch):
    """With a +driver env value, the CLI's connection helper must produce a DSN
    that psycopg.connect actually accepts (it would raise on the raw +driver)."""
    base = _base_dsn()
    plus_dsn = base.replace("postgresql://", "postgresql+asyncpg://", 1)
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", plus_dsn)

    # Drive a real connection through the CLI's own helpers -- this is the path
    # every subcommand uses.  A raw +asyncpg DSN would make psycopg.connect raise.
    dsn = cli._pg_dsn_from_env()
    conn = cli._connect_pg(dsn, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            (one,) = cur.fetchone()
        assert one == 1
    finally:
        conn.close()
