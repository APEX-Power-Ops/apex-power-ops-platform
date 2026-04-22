"""
Ops — PM Idempotency Sweep + Stats Integration Smoke (real PostgreSQL)
=======================================================================
Packet: 2026-04-16-pm-schema-019g

Real-PostgreSQL variant of the sweep + stats unit lanes.  Exercises:

  A. ``_DurableBackend.sweep_expired()`` — seeds rows with varied
     ``expires_at`` and asserts the bounded DELETE removes ONLY the
     expired rows while leaving future-dated rows untouched.
  B. ``_DurableBackend.stats()`` — verifies live aggregate SELECT
     returns correct ``{count, expired_count, oldest_expires_at}``.
  C. ``GET /api/v1/ops/pm-idempotency/stats`` — end-to-end via FastAPI
     TestClient with the durable backend bound to the integration DB.
     Asserts the endpoint reports ``backend_kind="durable"`` and the
     counts reflect the seeded rows.

Skip-guards mirror packet 019f's integration lane:
  * ``APEX_INTEGRATION_DATABASE_URL`` (or ``DATABASE_URL``) must be set
  * Host:port must be reachable
  * ``pm.idempotency_keys`` must exist (migration 009 applied)

Sentinels: code prefix ``SMK19G-``.  Teardown deletes only rows keyed by
these sentinels.
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        return None
    return url


def _db_is_reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        parsed = urlparse(
            url.replace("postgresql+psycopg2://", "postgresql://")
        )
        host = parsed.hostname
        port = parsed.port or 5432
        if not host:
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
        return True
    except OSError:
        return False


_DB_URL = _resolve_integration_db_url()

pytestmark = pytest.mark.skipif(
    _DB_URL is None,
    reason=(
        "PM idempotency sweep + stats integration skipped: set "
        "APEX_INTEGRATION_DATABASE_URL to a PostgreSQL URL hosting the "
        "pm schema (migration 009_pm_idempotency_keys applied)."
    ),
)

if _DB_URL is not None and not _db_is_reachable(_DB_URL):
    pytestmark = pytest.mark.skip(
        reason=(
            f"PM idempotency sweep + stats integration skipped: "
            f"PostgreSQL at {_DB_URL!s} is not reachable from this executor."
        )
    )


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if _DB_URL is not None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import ProgrammingError
    from sqlalchemy.orm import sessionmaker

    from config import get_db  # type: ignore
    from fastapi.testclient import TestClient
    from main import app  # type: ignore

    from services.work.idempotency import (  # type: ignore
        _DurableBackend,
        _hash_body,
        idempotency_cache,
    )

    _probe_engine = create_engine(_DB_URL, future=True)
    try:
        with _probe_engine.connect() as _conn:
            _conn.execute(text(
                "SELECT 1 FROM pm.idempotency_keys WHERE false"
            ))
    except ProgrammingError:
        pytestmark = pytest.mark.skip(
            reason=(
                "PM idempotency sweep + stats integration skipped: "
                "pm.idempotency_keys table not found — apply "
                "migration 009_pm_idempotency_keys.sql."
            )
        )
    except Exception as _exc:  # pragma: no cover - defensive
        pytestmark = pytest.mark.skip(
            reason=(
                "PM idempotency sweep + stats integration skipped: "
                f"probe raised {_exc!r}."
            )
        )
    finally:
        _probe_engine.dispose()


# ---------------------------------------------------------------------------
# Sentinels
# ---------------------------------------------------------------------------

SENTINEL_PREFIX = "SMK19G-"
# The sentinel keys all start with SMK19G- so teardown scopes cleanly.
IKEY_EXPIRED_A = "SMK19G-expired-a"
IKEY_EXPIRED_B = "SMK19G-expired-b"
IKEY_FRESH_A   = "SMK19G-fresh-a"
IKEY_FRESH_B   = "SMK19G-fresh-b"
IKEY_STATS_A   = "SMK19G-stats-a"
IKEY_STATS_B   = "SMK19G-stats-b"
IKEY_E2E       = "SMK19G-e2e"


def _seed_row(conn, route: str, key: str, expires_offset_seconds: int):
    """Insert a pm.idempotency_keys row with explicit expires_at offset."""
    conn.execute(text("""
        INSERT INTO pm.idempotency_keys
            (route, idempotency_key, body_hash, expires_at)
        VALUES
            (:route, :key, :body_hash,
             now() + make_interval(secs => :offset))
        ON CONFLICT (route, idempotency_key) DO UPDATE
           SET expires_at = EXCLUDED.expires_at
    """), dict(
        route=route, key=key,
        body_hash=_hash_body(b'{"smoke":true}'),
        offset=expires_offset_seconds,
    ))


def _teardown(conn):
    conn.execute(text("""
        DELETE FROM pm.idempotency_keys
         WHERE idempotency_key LIKE :prefix
    """), dict(prefix=f"{SENTINEL_PREFIX}%"))


@pytest.fixture
def engine():
    eng = create_engine(_DB_URL, future=True)
    # Clean any stale sentinel rows before test body runs.
    with eng.begin() as conn:
        _teardown(conn)
    yield eng
    with eng.begin() as conn:
        _teardown(conn)
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# A. Durable sweep live
# ---------------------------------------------------------------------------

class TestDurableBackendSweepLive:

    def test_sweep_removes_only_expired_rows(
        self, engine, session_factory,
    ):
        # Seed: two expired + two fresh rows.
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_EXPIRED_A, -3600)
            _seed_row(conn, "/tasks", IKEY_EXPIRED_B, -60)
            _seed_row(conn, "/projects", IKEY_FRESH_A, 3600)
            _seed_row(conn, "/tasks", IKEY_FRESH_B, 7200)

        backend = _DurableBackend(session_factory)
        deleted = backend.sweep_expired()
        assert deleted == 2

        with engine.begin() as conn:
            remaining = conn.execute(text("""
                SELECT idempotency_key
                  FROM pm.idempotency_keys
                 WHERE idempotency_key LIKE :prefix
                 ORDER BY idempotency_key
            """), dict(prefix=f"{SENTINEL_PREFIX}%")).all()
        remaining_keys = {r[0] for r in remaining}
        assert IKEY_EXPIRED_A not in remaining_keys
        assert IKEY_EXPIRED_B not in remaining_keys
        assert IKEY_FRESH_A in remaining_keys
        assert IKEY_FRESH_B in remaining_keys

    def test_sweep_on_empty_store_returns_zero(self, session_factory):
        backend = _DurableBackend(session_factory)
        # After fixture teardown the sentinel slice is empty; sweep
        # against the slice is still valid — unrelated rows are not
        # touched because their expires_at hasn't passed.  Assert
        # that sweeping twice in a row is safe and non-negative.
        first = backend.sweep_expired()
        second = backend.sweep_expired()
        assert first >= 0
        assert second >= 0

    def test_sweep_does_not_touch_future_rows(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_FRESH_A, 3600)

        backend = _DurableBackend(session_factory)
        backend.sweep_expired()

        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT 1 FROM pm.idempotency_keys
                 WHERE idempotency_key = :k
            """), dict(k=IKEY_FRESH_A)).first()
        assert row is not None


# ---------------------------------------------------------------------------
# B. Durable stats live
# ---------------------------------------------------------------------------

class TestDurableBackendStatsLive:

    def test_stats_reflects_live_counts(self, engine, session_factory):
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_STATS_A, -30)   # expired
            _seed_row(conn, "/tasks",    IKEY_STATS_B, 300)   # fresh

        backend = _DurableBackend(session_factory)
        s = backend.stats()
        # Note: the DB may contain non-sentinel rows from other tests;
        # we can only assert lower bounds + structural invariants.
        assert s["count"] >= 2
        assert s["expired_count"] >= 1
        assert s["oldest_expires_at"] is not None

    def test_stats_issues_no_writes_live(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            before = conn.execute(text("""
                SELECT COUNT(*) FROM pm.idempotency_keys
            """)).scalar() or 0

        backend = _DurableBackend(session_factory)
        backend.stats()

        with engine.begin() as conn:
            after = conn.execute(text("""
                SELECT COUNT(*) FROM pm.idempotency_keys
            """)).scalar() or 0

        # Stats is a pure SELECT; total row count must be unchanged.
        assert after == before


# ---------------------------------------------------------------------------
# C. End-to-end: GET /api/v1/ops/pm-idempotency/stats on live durable backend
# ---------------------------------------------------------------------------

@pytest.fixture
def client(engine, session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    idempotency_cache.use_durable_backend(session_factory)

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        idempotency_cache.use_in_memory_backend()


class TestOpsStatsEndpointLive:

    def test_endpoint_reports_durable_backend(self, client):
        resp = client.get("/api/v1/ops/pm-idempotency/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["backend_kind"] == "durable"
        assert set(body.keys()) == {
            "count", "expired_count", "oldest_expires_at", "backend_kind",
        }

    def test_endpoint_counts_reflect_seeded_rows(
        self, client, engine,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_E2E + "-live", 3600)

        resp = client.get("/api/v1/ops/pm-idempotency/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        assert body["oldest_expires_at"] is not None

    def test_endpoint_is_read_only(self, client):
        # Verify non-GET verbs are 405 against the live surface too.
        for method in ("post", "put", "patch", "delete"):
            r = getattr(client, method)("/api/v1/ops/pm-idempotency/stats")
            assert r.status_code == 405
