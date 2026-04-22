"""
PM/Work Domain — Durable Idempotency Store Integration Smoke
=============================================================
Packet: 2026-04-16-pm-schema-019f

Real-PostgreSQL variant of the unit lanes in
``test_work_idempotency_durable``.  Exercises ``_DurableBackend`` against
the live ``pm.idempotency_keys`` table and end-to-end through the
FastAPI TestClient over POST ``/api/v1/work/projects`` with the
idempotency seam swapped to the durable backend.

Coverage:

  * First-sight registration inserts a row with response_status=NULL.
  * Record-response updates the row with (2xx, body).
  * Replay with matching (route, key, body_hash) returns the cached
    (status, body) bytes.
  * Replay with mismatching body hash surfaces as ``match=False``.
  * ``discard_registration`` removes an unrecorded row (422 validation-
    failure discard path).  A recorded-success row is NEVER evicted.
  * End-to-end via POST ``/api/v1/work/projects``: first request inserts
    a pm row with response_status=201, replay returns byte-for-byte same
    response, 422 mismatch payload shape, and validation-failure 422 does
    NOT persist a pm row (discard path wired by the router).
  * Cross-instance simulation: a second session_factory observes the
    committed row from the first and replays its cached response.

Skip-guards:
  * ``APEX_INTEGRATION_DATABASE_URL`` (or ``DATABASE_URL``) must be set.
  * The URL's host:port must be TCP-reachable from this executor.
  * The ``pm.idempotency_keys`` table must exist (i.e. migration 009 has
    been applied to the target DB).

Mirrors the skip-guard patterns used by packets 012g / 012i / 013i /
014i / 015i / 016i / 017i / 018i / 019-PATCH-harness-integration.

Sentinels: code prefix ``SMK19F-``, UUID prefix ``019f0xxx-...``.
Cleanup deletes only rows keyed by these sentinels, leaving the rest of
the staging DB untouched.
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------

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
        "Durable idempotency integration skipped: set "
        "APEX_INTEGRATION_DATABASE_URL to a PostgreSQL URL hosting the "
        "pm + work + org schemas (migration 009_pm_idempotency_keys "
        "applied)."
    ),
)

if _DB_URL is not None and not _db_is_reachable(_DB_URL):
    pytestmark = pytest.mark.skip(
        reason=(
            f"Durable idempotency integration skipped: PostgreSQL at "
            f"{_DB_URL!s} is not reachable from this executor."
        )
    )


# ---------------------------------------------------------------------------
# Deferred imports — module-level only when the DB URL resolved.
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if _DB_URL is not None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import ProgrammingError
    from sqlalchemy.orm import sessionmaker

    from config import get_db  # type: ignore
    from fastapi.testclient import TestClient
    from main import app  # type: ignore

    from services.work.idempotency import (  # type: ignore
        IDEMPOTENCY_HEADER,
        PM_POST_ROUTES,
        IdempotencyHit,
        _DurableBackend,
        _hash_body,
        idempotency_cache,
    )

    # Additional skip: the pm.idempotency_keys table must exist.
    _probe_engine = create_engine(_DB_URL, future=True)
    try:
        with _probe_engine.connect() as _conn:
            _conn.execute(text(
                "SELECT 1 FROM pm.idempotency_keys WHERE false"
            ))
    except ProgrammingError:
        pytestmark = pytest.mark.skip(
            reason=(
                "Durable idempotency integration skipped: "
                "pm.idempotency_keys table not found — apply "
                "migration 009_pm_idempotency_keys.sql."
            )
        )
    except Exception as _exc:  # pragma: no cover - defensive
        pytestmark = pytest.mark.skip(
            reason=(
                "Durable idempotency integration skipped: probe of "
                f"pm.idempotency_keys raised {_exc!r}."
            )
        )
    finally:
        _probe_engine.dispose()


# ---------------------------------------------------------------------------
# Sentinels
# ---------------------------------------------------------------------------

CLIENT_ID  = "019f0001-0000-4000-8000-000000000001"
SITE_ID    = "019f0002-0000-4000-8000-000000000001"

# Sentinel idempotency key prefixes.  ``SMK19F-`` is the cleanup anchor.
IKEY_FIRST_SIGHT         = "SMK19F-first-sight"
IKEY_REPLAY              = "SMK19F-replay"
IKEY_MISMATCH            = "SMK19F-mismatch"
IKEY_DISCARD             = "SMK19F-discard"
IKEY_DISCARD_PRESERVES   = "SMK19F-discard-preserves"
IKEY_VALIDATION_FAILURE  = "SMK19F-validation-failure"
IKEY_CROSS_INSTANCE      = "SMK19F-cross-instance"
IKEY_E2E_REPLAY          = "SMK19F-e2e-replay"
IKEY_E2E_MISMATCH        = "SMK19F-e2e-mismatch"

ALL_SENTINEL_KEYS = [
    IKEY_FIRST_SIGHT,
    IKEY_REPLAY,
    IKEY_MISMATCH,
    IKEY_DISCARD,
    IKEY_DISCARD_PRESERVES,
    IKEY_VALIDATION_FAILURE,
    IKEY_CROSS_INSTANCE,
    IKEY_E2E_REPLAY,
    IKEY_E2E_MISMATCH,
]


# ---------------------------------------------------------------------------
# Seed / teardown helpers
# ---------------------------------------------------------------------------

def _seed_org(conn):
    """Seed one client + site so POST /projects has valid FKs."""
    conn.execute(text("""
        INSERT INTO org.clients (client_id, client_code, name, is_active)
        VALUES (:cid, 'SMK19F-CLIENT', 'Smoke Client 19f', true)
        ON CONFLICT (client_id) DO NOTHING
    """), dict(cid=CLIENT_ID))
    conn.execute(text("""
        INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
        VALUES (:sid, :cid, 'SMK19F-SITE', 'Smoke Site 19f', true)
        ON CONFLICT (site_id) DO NOTHING
    """), dict(sid=SITE_ID, cid=CLIENT_ID))


def _teardown(conn):
    # pm.idempotency_keys — remove every sentinel key across every route.
    conn.execute(text("""
        DELETE FROM pm.idempotency_keys
         WHERE idempotency_key = ANY(:keys)
    """), dict(keys=ALL_SENTINEL_KEYS))

    # work.projects — anything created by the e2e POST calls is keyed by
    # project_code starting with "SMK19F-".  Capture the IDs first so
    # any downstream rows (none in 019f scope but defensive) are safe.
    conn.execute(text("""
        DELETE FROM work.projects
         WHERE project_code LIKE 'SMK19F-%'
    """))

    conn.execute(
        text("DELETE FROM org.sites WHERE site_id = :v"), dict(v=SITE_ID),
    )
    conn.execute(
        text("DELETE FROM org.clients WHERE client_id = :v"),
        dict(v=CLIENT_ID),
    )


# ---------------------------------------------------------------------------
# Engine / session_factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    eng = create_engine(_DB_URL, future=True)
    with eng.begin() as conn:
        _seed_org(conn)
    yield eng
    with eng.begin() as conn:
        _teardown(conn)
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# A. Pure-backend smoke — _DurableBackend against live PG
# ---------------------------------------------------------------------------

class TestDurableBackendLivePG:

    def test_first_sight_inserts_row_with_null_response(
        self, session_factory, engine,
    ):
        backend = _DurableBackend(session_factory)
        hit = backend.register_request(
            "/projects", IKEY_FIRST_SIGHT, b'{"a":1}',
        )
        assert hit is None
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT body_hash, response_status, response_body
                  FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(r="/projects", k=IKEY_FIRST_SIGHT)).first()
        assert row is not None
        assert row[0] == _hash_body(b'{"a":1}')
        assert row[1] is None
        assert row[2] is None

    def test_record_response_updates_row(self, session_factory, engine):
        backend = _DurableBackend(session_factory)
        backend.register_request(
            "/projects", IKEY_REPLAY, b'{"a":1}',
        )
        backend.record_response(
            "/projects", IKEY_REPLAY, b'{"a":1}', 201, b'{"ok":true}',
        )
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT response_status, response_body
                  FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(r="/projects", k=IKEY_REPLAY)).first()
        assert row is not None
        assert row[0] == 201
        assert bytes(row[1]) == b'{"ok":true}'

    def test_replay_with_matching_body_returns_cached(
        self, session_factory,
    ):
        backend = _DurableBackend(session_factory)
        backend.register_request(
            "/projects", IKEY_REPLAY, b'{"a":1}',
        )
        backend.record_response(
            "/projects", IKEY_REPLAY, b'{"a":1}', 201, b'{"ok":true}',
        )
        hit = backend.register_request(
            "/projects", IKEY_REPLAY, b'{"a":1}',
        )
        assert isinstance(hit, IdempotencyHit)
        assert hit.match is True
        assert hit.status == 201
        assert hit.response_body == b'{"ok":true}'

    def test_replay_with_mismatching_body_returns_match_false(
        self, session_factory,
    ):
        backend = _DurableBackend(session_factory)
        backend.register_request(
            "/projects", IKEY_MISMATCH, b'{"a":1}',
        )
        hit = backend.register_request(
            "/projects", IKEY_MISMATCH, b'{"a":2}',
        )
        assert hit is not None
        assert hit.match is False

    def test_discard_removes_unrecorded_row(
        self, session_factory, engine,
    ):
        backend = _DurableBackend(session_factory)
        backend.register_request(
            "/projects", IKEY_DISCARD, b'{"a":1}',
        )
        backend.discard_registration(
            "/projects", IKEY_DISCARD, b'{"a":1}',
        )
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT 1 FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(r="/projects", k=IKEY_DISCARD)).first()
        assert row is None

    def test_discard_preserves_row_with_recorded_success(
        self, session_factory, engine,
    ):
        """A recorded-success row MUST survive a later discard — the
        replay contract depends on it."""
        backend = _DurableBackend(session_factory)
        backend.register_request(
            "/projects", IKEY_DISCARD_PRESERVES, b'{"a":1}',
        )
        backend.record_response(
            "/projects", IKEY_DISCARD_PRESERVES,
            b'{"a":1}', 201, b'{"ok":true}',
        )
        backend.discard_registration(
            "/projects", IKEY_DISCARD_PRESERVES, b'{"a":1}',
        )
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT response_status, response_body
                  FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(r="/projects", k=IKEY_DISCARD_PRESERVES)).first()
        assert row is not None
        assert row[0] == 201
        assert bytes(row[1]) == b'{"ok":true}'

    def test_cross_instance_second_factory_observes_committed_row(
        self, engine,
    ):
        """Two different session_factories bound to the same DB see the
        same committed row — simulates multi-instance coordination."""
        factory_a = sessionmaker(
            bind=engine, autoflush=False, autocommit=False,
        )
        factory_b = sessionmaker(
            bind=engine, autoflush=False, autocommit=False,
        )
        backend_a = _DurableBackend(factory_a)
        backend_b = _DurableBackend(factory_b)

        assert backend_a.register_request(
            "/projects", IKEY_CROSS_INSTANCE, b'{"a":1}',
        ) is None
        backend_a.record_response(
            "/projects", IKEY_CROSS_INSTANCE,
            b'{"a":1}', 201, b'{"from":"a"}',
        )

        hit = backend_b.register_request(
            "/projects", IKEY_CROSS_INSTANCE, b'{"a":1}',
        )
        assert hit is not None
        assert hit.match is True
        assert hit.status == 201
        assert hit.response_body == b'{"from":"a"}'


# ---------------------------------------------------------------------------
# B. End-to-end — POST /api/v1/work/projects with durable seam live
# ---------------------------------------------------------------------------

MINIMAL_PROJECT_PAYLOAD_BASE = {
    "project_code": "SMK19F-PRJ",
    "title": "Durable idempotency smoke",
    "client_id": CLIENT_ID,
    "site_id": SITE_ID,
}


@pytest.fixture
def client(engine, session_factory):
    """TestClient with the durable backend swapped to the integration DB.

    This fixture deliberately rebinds ``idempotency_cache`` to the
    integration test's own session_factory so the seam writes rows to
    the same database the TestClient's POST handlers are writing
    projects to (both routed through the same ``engine``).  After the
    test, we reset the singleton to the in-memory backend so no other
    module inherits the rebound durable connection.
    """
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


class TestE2EOverPostProjectsDurable:

    def test_first_request_with_key_inserts_pm_row_and_returns_201(
        self, client, engine,
    ):
        payload = {
            **MINIMAL_PROJECT_PAYLOAD_BASE,
            "project_code": "SMK19F-FIRST",
        }
        resp = client.post(
            "/api/v1/work/projects",
            json=payload,
            headers={IDEMPOTENCY_HEADER: IKEY_E2E_REPLAY},
        )
        assert resp.status_code == 201, resp.text
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT response_status
                  FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(r="/projects", k=IKEY_E2E_REPLAY)).first()
        assert row is not None
        assert row[0] == 201

    def test_replay_returns_byte_for_byte_same_body(
        self, client, engine,
    ):
        payload = {
            **MINIMAL_PROJECT_PAYLOAD_BASE,
            "project_code": "SMK19F-REPLAY",
        }
        first = client.post(
            "/api/v1/work/projects",
            json=payload,
            headers={IDEMPOTENCY_HEADER: IKEY_E2E_REPLAY + "-byte"},
        )
        second = client.post(
            "/api/v1/work/projects",
            json=payload,
            headers={IDEMPOTENCY_HEADER: IKEY_E2E_REPLAY + "-byte"},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.content == second.content
        # Only one work.projects row created despite two POSTs.
        with engine.begin() as conn:
            count = conn.execute(text("""
                SELECT COUNT(*) FROM work.projects
                 WHERE project_code = :pc
            """), dict(pc="SMK19F-REPLAY")).scalar()
        assert count == 1

    def test_replay_with_different_body_returns_422_mismatch(self, client):
        first = client.post(
            "/api/v1/work/projects",
            json={
                **MINIMAL_PROJECT_PAYLOAD_BASE,
                "project_code": "SMK19F-MISMATCH-A",
            },
            headers={IDEMPOTENCY_HEADER: IKEY_E2E_MISMATCH},
        )
        assert first.status_code == 201
        second = client.post(
            "/api/v1/work/projects",
            json={
                **MINIMAL_PROJECT_PAYLOAD_BASE,
                "project_code": "SMK19F-MISMATCH-B",
                "title": "A different title",
            },
            headers={IDEMPOTENCY_HEADER: IKEY_E2E_MISMATCH},
        )
        assert second.status_code == 422
        body = second.json()
        assert body["detail"] == (
            "Idempotency-Key reused with different payload"
        )
        assert "errors" in body and "idempotency_key" in body["errors"]

    def test_validation_failure_does_not_persist_pm_row(
        self, client, engine,
    ):
        """A POST that fails org FK validation returns 422 and MUST NOT
        leave a pm.idempotency_keys row behind — otherwise the caller
        can never retry this key with a corrected payload."""
        resp = client.post(
            "/api/v1/work/projects",
            json={
                **MINIMAL_PROJECT_PAYLOAD_BASE,
                "project_code": "SMK19F-VAL-FAIL",
                # Unknown client_id — org FK validation will 422.
                "client_id": "019f0099-0000-4000-8000-000000000099",
            },
            headers={IDEMPOTENCY_HEADER: IKEY_VALIDATION_FAILURE},
        )
        assert resp.status_code == 422
        with engine.begin() as conn:
            row = conn.execute(text("""
                SELECT 1 FROM pm.idempotency_keys
                 WHERE route = :r AND idempotency_key = :k
            """), dict(
                r="/projects", k=IKEY_VALIDATION_FAILURE,
            )).first()
        assert row is None, (
            "Validation-failure 422 must not persist the pre-registered "
            "row — the retry-with-corrected-payload contract relies on "
            "the discard path."
        )


# ---------------------------------------------------------------------------
# C. Scope pins
# ---------------------------------------------------------------------------

class TestPMPostRoutesPinnedLive:
    """Even under the live backend, ``PM_POST_ROUTES`` remains the seven
    routes (the DDL CHECK constraint pins the same list)."""

    def test_exact_seven_routes(self):
        assert PM_POST_ROUTES == frozenset({
            "/projects",
            "/work-packages",
            "/tasks",
            "/assignments",
            "/dependencies",
            "/execution-issues",
            "/progress-snapshots",
        })
