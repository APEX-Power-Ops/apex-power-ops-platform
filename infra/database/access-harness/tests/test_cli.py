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


from access_harness import config as _config


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


def test_cli_parser_accepts_governed_flag():
    """The parser exposes a --governed boolean defaulting to False."""
    parser = cli.build_parser()
    args = parser.parse_args(["--governed", "run-all"])
    assert args.governed is True
    args2 = parser.parse_args(["run-all"])
    assert args2.governed is False


def test_pg_dsn_for_routes_governed(monkeypatch):
    """_pg_dsn_for returns the governed DSN when args.governed, else the base."""
    base = "postgresql://u:pw@127.0.0.1:5432/postgres"
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)

    class _A:
        governed = True
    class _B:
        governed = False

    assert cli._pg_dsn_for(_A()).endswith("/tcc_fidelity_governed")
    assert cli._pg_dsn_for(_B()).endswith("/postgres")


def test_fence_governed_refuses_wrong_db():
    """_fence_governed raises when --governed but connected to the wrong DB, and
    is a no-op when --governed is not set (even on a non-governed DB)."""
    from tests.test_config import _StubConn  # reuse the stub

    class _Gov:
        governed = True
    class _Plain:
        governed = False

    # --governed on the wrong db -> refuse.
    with pytest.raises(RuntimeError):
        cli._fence_governed(_StubConn("tcc_fidelity_test"), _Gov())
    # --governed on the right db -> ok.
    cli._fence_governed(_StubConn("tcc_fidelity_governed"), _Gov())
    # not --governed -> no fence, even on a non-governed db.
    cli._fence_governed(_StubConn("postgres"), _Plain())


def test_governed_command_paths_fence_before_write(monkeypatch):
    """AC-2: load / inventory / run-all with --governed resolving to a NON-governed
    DB must raise the fence error BEFORE any write (record_extraction_run and
    _load_slice never run). Access-dependent steps are monkeypatched to no-ops so
    the test is fast + independent of the Windows Access path; the fence is the
    thing under test."""
    from access_harness import cli, config, extract, freeze as freeze_mod

    base = _base_dsn()
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)
    # --governed resolves to tcc_fidelity_test (a NON-governed db) -> fence fires.
    monkeypatch.setattr(config, "governed_pg_dsn", config.test_pg_dsn)

    class _FS:
        frozen_path = "X:/frozen.accdb"
        source_sha256 = "00" * 32
    monkeypatch.setattr(freeze_mod, "freeze", lambda *a, **k: _FS())
    monkeypatch.setattr(cli, "driver_preflight", lambda *a, **k: ("drv", "ver", 1))
    monkeypatch.setattr(extract, "connect_data", lambda *a, **k: object())
    monkeypatch.setattr(extract, "connect_ace", lambda *a, **k: object())

    def _boom_record(*a, **k):
        raise AssertionError("record_extraction_run ran BEFORE the fence")
    def _boom_load(*a, **k):
        raise AssertionError("_load_slice ran BEFORE the fence")
    def _boom_snapshot(*a, **k):
        raise AssertionError("snapshot_tcc ran BEFORE the fence")
    def _boom_validate(*a, **k):
        raise AssertionError("_run_validation ran BEFORE the fence")
    monkeypatch.setattr(freeze_mod, "record_extraction_run", _boom_record)
    monkeypatch.setattr(cli, "_load_slice", _boom_load)
    monkeypatch.setattr(cli, "snapshot_tcc", _boom_snapshot)
    monkeypatch.setattr(cli, "_run_validation", _boom_validate)

    class _Args:
        governed = True
        with_curves = False
        accdb = None
        frozen_dir = None
        run_id = "x"
        snapshot_id = "x"

    for cmd in (
        cli.cmd_load,
        cli.cmd_inventory,
        cli.cmd_run_all,
        cli.cmd_extract,
        cli.cmd_snapshot_tcc,
        cli.cmd_validate,
    ):
        with pytest.raises(RuntimeError, match="FENCE VIOLATION"):
            cmd(_Args())
