"""Tests for access_harness.config governed-target helpers.

The governed DSN derivation is pure-string (no DB).  assert_current_database is
proven with BOTH a real fixture connection AND a stub connection parametrized
over the DB names the --governed fence must refuse (postgres / tcc_fidelity_test
/ arbitrary) -- so the refusal logic is proven for every name without the suite
ever touching tcc_fidelity_governed.
"""
import os
from contextlib import contextmanager

import pytest

from access_harness import config


def _base_dsn() -> str:
    if not os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN"):
        pytest.skip("ACCESS_HARNESS_SUPERUSER_DSN unset")
    return config.pg_dsn()


def test_governed_pg_dsn_swaps_db_only(monkeypatch):
    """governed_pg_dsn() swaps ONLY the db path to tcc_fidelity_governed; the
    netloc (user/host/port) is byte-identical to the base DSN."""
    base = "postgresql://u:pw@127.0.0.1:5432/postgres"
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)
    gov = config.governed_pg_dsn()
    assert gov == "postgresql://u:pw@127.0.0.1:5432/tcc_fidelity_governed"
    # netloc identical to test_pg_dsn (which targets tcc_fidelity_test)
    assert config.test_pg_dsn().rsplit("/", 1)[0] == gov.rsplit("/", 1)[0]
    assert config.GOVERNED_DB == "tcc_fidelity_governed"


class _StubConn:
    """Minimal psycopg-conn stand-in: cursor() -> ctx mgr; execute/fetchone
    return a fixed current_database() value."""
    def __init__(self, db):
        self._db = db
    @contextmanager
    def cursor(self):
        outer = self
        class _Cur:
            def execute(self, *_a, **_k):
                pass
            def fetchone(self):
                return (outer._db,)
        yield _Cur()


@pytest.mark.parametrize("wrong_db", ["postgres", "tcc_fidelity_test", "whatever_db"])
def test_assert_current_database_refuses_wrong_db(wrong_db):
    """assert_current_database raises for any DB that is not the expected one."""
    with pytest.raises(RuntimeError):
        config.assert_current_database(_StubConn(wrong_db), "tcc_fidelity_governed")


def test_assert_current_database_passes_on_match():
    """assert_current_database is a no-op when the connected DB matches."""
    config.assert_current_database(_StubConn("tcc_fidelity_governed"),
                                   "tcc_fidelity_governed")  # must not raise


def test_assert_current_database_real_conn(pg):
    """With the real fixture conn (tcc_fidelity_test): passes for its own name,
    raises for the governed name."""
    config.assert_current_database(pg, "tcc_fidelity_test")  # no raise
    with pytest.raises(RuntimeError):
        config.assert_current_database(pg, "tcc_fidelity_governed")


import psycopg


def test_ensure_database_idempotent(pg):
    """ensure_database creates a missing DB (True), is a no-op if present (False),
    and never raises on an existing DB.  Uses a uniquely-named throwaway probe DB
    -- NEVER tcc_fidelity_governed -- and drops it afterward.

    OPT-IN (AC-1): cluster-mutating (creates/drops a probe db), so it is SKIPPED
    unless ACCESS_HARNESS_ALLOW_DB_CREATE=1 -- a default suite run never mutates
    the cluster."""
    if os.environ.get("ACCESS_HARNESS_ALLOW_DB_CREATE") != "1":
        pytest.skip("opt-in only: set ACCESS_HARNESS_ALLOW_DB_CREATE=1 (AC-1)")
    base = _base_dsn()  # connect to the base DB (postgres); ensure a DIFFERENT db
    probe = "tcc_fidelity_ensure_probe_t1"
    admin = psycopg.connect(base, autocommit=True)
    try:
        # Clean slate: drop the probe if a prior run left it.
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {probe}")

        created = config.ensure_database(admin, probe)
        assert created is True, "first ensure must CREATE the probe db"

        # It now exists.
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (probe,))
            assert cur.fetchone() is not None

        again = config.ensure_database(admin, probe)
        assert again is False, "second ensure must be a no-op (already exists)"
    finally:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {probe}")
        admin.close()
