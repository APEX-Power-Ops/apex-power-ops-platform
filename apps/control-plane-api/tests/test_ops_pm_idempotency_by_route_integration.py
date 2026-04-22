"""
Ops — PM Idempotency By-Route Integration Smoke (real PostgreSQL)
==================================================================
Packet: 2026-04-16-pm-schema-019i

Real-PostgreSQL variant of the per-route stats unit lane.  Exercises:

  A. ``_DurableBackend.stats_by_route()`` — seeds rows across multiple
     pinned PM POST routes with varied ``expires_at`` and asserts the
     GROUP BY query returns correct per-route counts, expired counts,
     and oldest-expires-at timestamps.
  B. ``GET /api/v1/ops/pm-idempotency/by-route`` — end-to-end via
     FastAPI TestClient with the durable backend bound to the
     integration DB.  Asserts the endpoint reports
     ``backend_kind="durable"``, the payload carries exactly seven
     rows pinned to ``PM_POST_ROUTES``, and per-route counts reflect
     the seeded sentinel rows.

Skip-guards mirror packets 019f / 019g integration lanes:
  * ``APEX_INTEGRATION_DATABASE_URL`` (or ``DATABASE_URL``) must be set
  * Host:port must be reachable
  * ``pm.idempotency_keys`` must exist (migration 009 applied)

Sentinels: code prefix ``SMK19I-``.  Teardown deletes only rows keyed
by these sentinels so other tests' rows survive.
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
        "PM idempotency by-route integration skipped: set "
        "APEX_INTEGRATION_DATABASE_URL to a PostgreSQL URL hosting the "
        "pm schema (migration 009_pm_idempotency_keys applied)."
    ),
)

if _DB_URL is not None and not _db_is_reachable(_DB_URL):
    pytestmark = pytest.mark.skip(
        reason=(
            f"PM idempotency by-route integration skipped: "
            f"PostgreSQL at {_DB_URL!s} is not reachable from this "
            f"executor."
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
        PM_POST_ROUTES,
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
                "PM idempotency by-route integration skipped: "
                "pm.idempotency_keys table not found — apply "
                "migration 009_pm_idempotency_keys.sql."
            )
        )
    except Exception as _exc:  # pragma: no cover - defensive
        pytestmark = pytest.mark.skip(
            reason=(
                "PM idempotency by-route integration skipped: "
                f"probe raised {_exc!r}."
            )
        )
    finally:
        _probe_engine.dispose()


# ---------------------------------------------------------------------------
# Sentinels
# ---------------------------------------------------------------------------

SENTINEL_PREFIX = "SMK19I-"
IKEY_PROJ_FRESH_A    = "SMK19I-proj-fresh-a"
IKEY_PROJ_FRESH_B    = "SMK19I-proj-fresh-b"
IKEY_TASKS_FRESH     = "SMK19I-tasks-fresh"
IKEY_ASSIGN_FRESH    = "SMK19I-assign-fresh"
IKEY_ASSIGN_EXPIRED  = "SMK19I-assign-expired"
IKEY_DEPS_FRESH      = "SMK19I-deps-fresh"
IKEY_E2E_A           = "SMK19I-e2e-a"
IKEY_E2E_B           = "SMK19I-e2e-b"


def _seed_row(conn, route: str, key: str, expires_offset_seconds: int):
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
# A. Durable stats-by-route live
# ---------------------------------------------------------------------------

class TestDurableBackendStatsByRouteLive:

    def test_stats_by_route_returns_rows_for_seeded_routes(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_PROJ_FRESH_A, 3600)
            _seed_row(conn, "/projects", IKEY_PROJ_FRESH_B, 7200)
            _seed_row(conn, "/tasks",    IKEY_TASKS_FRESH, 3600)

        backend = _DurableBackend(session_factory)
        rows = backend.stats_by_route()
        by_route = {r["route"]: r for r in rows}

        # The sentinel slice guarantees ≥2 for /projects and ≥1 for
        # /tasks.  Other unrelated test rows may raise these bounds.
        assert "/projects" in by_route
        assert "/tasks" in by_route
        assert by_route["/projects"]["count"] >= 2
        assert by_route["/tasks"]["count"] >= 1

    def test_stats_by_route_tracks_expired_per_route(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/assignments", IKEY_ASSIGN_FRESH, 3600)
            _seed_row(conn, "/assignments", IKEY_ASSIGN_EXPIRED, -60)

        backend = _DurableBackend(session_factory)
        rows = backend.stats_by_route()
        by_route = {r["route"]: r for r in rows}

        assert "/assignments" in by_route
        assert by_route["/assignments"]["count"] >= 2
        assert by_route["/assignments"]["expired_count"] >= 1

    def test_stats_by_route_oldest_per_route(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/dependencies", IKEY_DEPS_FRESH, 1800)

        backend = _DurableBackend(session_factory)
        rows = backend.stats_by_route()
        by_route = {r["route"]: r for r in rows}

        assert "/dependencies" in by_route
        assert by_route["/dependencies"]["oldest_expires_at"] is not None

    def test_stats_by_route_issues_no_writes_live(
        self, engine, session_factory,
    ):
        with engine.begin() as conn:
            before = conn.execute(text("""
                SELECT COUNT(*) FROM pm.idempotency_keys
            """)).scalar() or 0

        backend = _DurableBackend(session_factory)
        backend.stats_by_route()

        with engine.begin() as conn:
            after = conn.execute(text("""
                SELECT COUNT(*) FROM pm.idempotency_keys
            """)).scalar() or 0

        # Per-route stats is a pure SELECT; total row count must
        # be unchanged.
        assert after == before


# ---------------------------------------------------------------------------
# B. End-to-end: GET /api/v1/ops/pm-idempotency/by-route on live durable
#    backend
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


class TestOpsByRouteEndpointLive:

    def test_endpoint_reports_durable_backend(self, client):
        resp = client.get("/api/v1/ops/pm-idempotency/by-route")
        assert resp.status_code == 200
        body = resp.json()
        assert body["backend_kind"] == "durable"
        assert set(body.keys()) == {"by_route", "backend_kind"}

    def test_endpoint_always_returns_seven_rows(self, client):
        resp = client.get("/api/v1/ops/pm-idempotency/by-route")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["by_route"]) == 7
        routes_seen = {r["route"] for r in body["by_route"]}
        assert routes_seen == set(PM_POST_ROUTES)

    def test_endpoint_counts_reflect_seeded_rows(
        self, client, engine,
    ):
        with engine.begin() as conn:
            _seed_row(conn, "/projects", IKEY_E2E_A, 3600)
            _seed_row(conn, "/projects", IKEY_E2E_B, 7200)

        resp = client.get("/api/v1/ops/pm-idempotency/by-route")
        assert resp.status_code == 200
        body = resp.json()
        by_route = {r["route"]: r for r in body["by_route"]}
        # DB may include other-test rows; assert lower bound on
        # /projects.
        assert by_route["/projects"]["count"] >= 2
        assert by_route["/projects"]["oldest_expires_at"] is not None

    def test_endpoint_is_read_only_live(self, client):
        for method in ("post", "put", "patch", "delete"):
            r = getattr(client, method)(
                "/api/v1/ops/pm-idempotency/by-route"
            )
            assert r.status_code == 405

    def test_endpoint_total_matches_stats_endpoint_live(self, client):
        by_route_resp = client.get(
            "/api/v1/ops/pm-idempotency/by-route"
        ).json()
        stats_resp = client.get("/api/v1/ops/pm-idempotency/stats").json()

        by_route_total = sum(r["count"] for r in by_route_resp["by_route"])
        # On the live DB the by-route total MUST equal the aggregate
        # stats endpoint count — this is the invariant that ties the
        # two ops endpoints into a coherent pair.
        assert by_route_total == stats_resp["count"]
