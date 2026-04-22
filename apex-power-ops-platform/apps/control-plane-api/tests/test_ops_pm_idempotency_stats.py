"""
Ops Router — PM Idempotency Stats Unit Tests
=============================================
Packet: 2026-04-16-pm-schema-019g

Covers the ``GET /api/v1/ops/pm-idempotency/stats`` surface at the
FastAPI TestClient level without requiring a live PostgreSQL.  The
idempotency cache is pinned to the in-memory backend for these tests
so the stats endpoint reports on an inspectable in-process dict.

Assertions enforce:

  * The endpoint is mounted under ``/api/v1/ops/*`` (NOT under
    ``/api/v1/work/*``, preserving the packet-019f path-count
    invariant of 15).
  * Response shape is exactly ``{count, expired_count,
    oldest_expires_at, backend_kind}``.
  * ``backend_kind`` reports ``"in_memory"`` when the singleton is on
    the in-memory backend.
  * Repeated calls against an empty store return stable empty payloads.
  * Registering PM idempotency entries moves ``count`` upward without
    any other widening of PM write surfaces.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from services.work.idempotency import idempotency_cache  # noqa: E402


@pytest.fixture
def client():
    """Bring the FastAPI app up and pin idempotency to in-memory."""
    from main import app

    idempotency_cache.use_in_memory_backend()
    idempotency_cache.clear()
    yield TestClient(app)
    idempotency_cache.clear()


class TestOpsIdempotencyStatsEndpointMounting:
    """Endpoint is mounted at ``/api/v1/ops/pm-idempotency/stats``."""

    def test_endpoint_responds_200(self, client):
        r = client.get("/api/v1/ops/pm-idempotency/stats")
        assert r.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        # Pin: stats MUST NOT be at /api/v1/work/* — that path count
        # stays at 15 across packet 019g.
        r = client.get("/api/v1/work/pm-idempotency/stats")
        assert r.status_code == 404

    def test_endpoint_is_get_only(self, client):
        r = client.post("/api/v1/ops/pm-idempotency/stats")
        assert r.status_code == 405  # Method Not Allowed


class TestOpsIdempotencyStatsShape:
    """Response is exactly {count, expired_count, oldest_expires_at,
    backend_kind}."""

    def test_empty_store_returns_zero_counts(self, client):
        r = client.get("/api/v1/ops/pm-idempotency/stats")
        body = r.json()
        assert body["count"] == 0
        assert body["expired_count"] == 0
        assert body["oldest_expires_at"] is None
        assert body["backend_kind"] == "in_memory"

    def test_response_keys_are_exactly_four(self, client):
        r = client.get("/api/v1/ops/pm-idempotency/stats")
        body = r.json()
        assert set(body.keys()) == {
            "count",
            "expired_count",
            "oldest_expires_at",
            "backend_kind",
        }

    def test_count_reflects_registered_entries(self, client):
        idempotency_cache.register_request("/projects", "k1", b'{"a":1}')
        idempotency_cache.register_request("/tasks", "k2", b'{"b":2}')

        r = client.get("/api/v1/ops/pm-idempotency/stats")
        body = r.json()
        assert body["count"] == 2
        assert body["expired_count"] == 0
        assert body["backend_kind"] == "in_memory"
        # oldest_expires_at is ISO-8601 datetime when populated
        assert body["oldest_expires_at"] is not None

    def test_backend_kind_reports_active_backend(self, client):
        # Default fixture pin is in_memory
        r = client.get("/api/v1/ops/pm-idempotency/stats")
        assert r.json()["backend_kind"] == "in_memory"


class TestOpsIdempotencyStatsIdempotent:
    """Scraping the endpoint is side-effect-free."""

    def test_repeated_calls_return_stable_payload_when_empty(self, client):
        first = client.get("/api/v1/ops/pm-idempotency/stats").json()
        second = client.get("/api/v1/ops/pm-idempotency/stats").json()
        assert first == second

    def test_repeated_calls_do_not_mutate_count(self, client):
        idempotency_cache.register_request("/projects", "k1", b'{"a":1}')
        first = client.get("/api/v1/ops/pm-idempotency/stats").json()
        second = client.get("/api/v1/ops/pm-idempotency/stats").json()
        third = client.get("/api/v1/ops/pm-idempotency/stats").json()
        assert first["count"] == 1
        assert second["count"] == 1
        assert third["count"] == 1


class TestOpsIdempotencyStatsScopeGuards:
    """Packet 019g scope guards — no new PM writes, no work widening."""

    def test_no_new_post_under_ops_stats(self, client):
        # GET is the only verb; POST/PUT/PATCH/DELETE must all 405.
        for method in ("post", "put", "patch", "delete"):
            call = getattr(client, method)
            r = call("/api/v1/ops/pm-idempotency/stats")
            assert r.status_code == 405, f"{method.upper()} should be 405"

    def test_work_pm_idempotency_stats_path_does_not_exist(self, client):
        # The surface lives under /api/v1/ops only; /api/v1/work stays
        # at 15 paths.
        r = client.get("/api/v1/work/pm-idempotency/stats")
        assert r.status_code == 404
