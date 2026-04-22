"""
Ops Router — PM Idempotency By-Route Unit Tests
===============================================
Packet: 2026-04-16-pm-schema-019i
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from services.work.idempotency import PM_POST_ROUTES, idempotency_cache  # noqa: E402


@pytest.fixture
def client():
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
    from main import app

    idempotency_cache.use_in_memory_backend()
    idempotency_cache.clear()
    yield TestClient(app)
    idempotency_cache.clear()


class TestOpsIdempotencyByRouteEndpointMounting:

    def test_endpoint_responds_200(self, client):
        r = client.get("/api/v1/ops/pm-idempotency/by-route")
        assert r.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        r = client.get("/api/v1/work/pm-idempotency/by-route")
        assert r.status_code == 404

    def test_endpoint_is_get_only(self, client):
        r = client.post("/api/v1/ops/pm-idempotency/by-route")
        assert r.status_code == 405


class TestOpsIdempotencyByRouteShape:

    def test_empty_store_returns_all_routes(self, client):
        body = client.get("/api/v1/ops/pm-idempotency/by-route").json()
        assert set(body.keys()) == {"by_route", "backend_kind"}
        assert body["backend_kind"] == "in_memory"
        assert [row["route"] for row in body["by_route"]] == sorted(PM_POST_ROUTES)
        assert all(row["count"] == 0 for row in body["by_route"])

    def test_count_reflects_registered_entries(self, client):
        idempotency_cache.register_request("/projects", "k1", b'{"a":1}')
        idempotency_cache.register_request("/projects", "k2", b'{"a":2}')
        idempotency_cache.register_request("/tasks", "k3", b'{"b":3}')
        body = client.get("/api/v1/ops/pm-idempotency/by-route").json()
        rows = {row["route"]: row for row in body["by_route"]}
        assert rows["/projects"]["count"] == 2
        assert rows["/tasks"]["count"] == 1
        assert rows["/assignments"]["count"] == 0

    def test_repeated_calls_are_stable(self, client):
        first = client.get("/api/v1/ops/pm-idempotency/by-route").json()
        second = client.get("/api/v1/ops/pm-idempotency/by-route").json()
        assert first == second


class TestOpsIdempotencyByRouteScopeGuards:

    def test_non_get_verbs_are_rejected(self, client):
        for method in ("post", "put", "patch", "delete"):
            r = getattr(client, method)("/api/v1/ops/pm-idempotency/by-route")
            assert r.status_code == 405

    def test_work_prefix_variant_does_not_exist(self, client):
        r = client.get("/api/v1/work/pm-idempotency/by-route")
        assert r.status_code == 404
