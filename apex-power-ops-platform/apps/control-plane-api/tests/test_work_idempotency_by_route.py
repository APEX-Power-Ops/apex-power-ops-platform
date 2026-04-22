"""
PM/Work Domain — Idempotency By-Route Stats Unit Tests
======================================================
Packet: 2026-04-16-pm-schema-019i
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.idempotency import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    IdempotencyCache,
    PM_POST_ROUTES,
    _DurableBackend,
    _InMemoryBackend,
)


class TestInMemoryBackendByRouteStats:

    def setup_method(self):
        self.backend = _InMemoryBackend(ttl_seconds=DEFAULT_TTL_SECONDS)

    def test_empty_store_returns_no_populated_rows(self):
        assert self.backend.stats_by_route() == []

    def test_counts_and_oldest_reflect_registered_entries(self):
        from services.work.idempotency import _Entry, _hash_body

        self.backend.register_request("/projects", "p1", b'{"a":1}')
        self.backend.register_request("/projects", "p2", b'{"a":2}')
        past = time.time() - 120
        self.backend._entries[("/tasks", "t-old")] = _Entry(
            body_hash=_hash_body(b'{"x":1}'),
            expires_at=past,
        )

        rows = {row["route"]: row for row in self.backend.stats_by_route()}
        assert rows["/projects"]["count"] == 2
        assert rows["/projects"]["expired_count"] == 0
        assert isinstance(rows["/projects"]["oldest_expires_at"], datetime)
        assert rows["/tasks"]["count"] == 1
        assert rows["/tasks"]["expired_count"] == 1
        assert rows["/tasks"]["oldest_expires_at"] == datetime.fromtimestamp(past)


@dataclass
class _StubResult:
    rows: list[Any] = field(default_factory=list)

    def all(self):
        return self.rows


class _ByRouteStubSession:

    def __init__(self, by_route_rows=None) -> None:
        self.statements: list[str] = []
        self.commits = 0
        self._by_route_rows = by_route_rows or []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, stmt, params=None):
        sql = str(stmt).strip().lower()
        self.statements.append(sql)
        if sql.startswith("select") and "group by route" in sql:
            return _StubResult(rows=self._by_route_rows)
        return _StubResult()

    def commit(self):
        self.commits += 1


def _factory(stub: _ByRouteStubSession):
    def f():
        return stub
    return f


class TestDurableBackendByRouteStats:

    def test_empty_store_returns_no_populated_rows(self):
        stub = _ByRouteStubSession([])
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        assert backend.stats_by_route() == []
        assert stub.commits == 0

    def test_grouped_rows_are_returned(self):
        dt = datetime(2026, 4, 16, 12, 0, 0)
        stub = _ByRouteStubSession([
            ("/projects", 3, 1, dt),
            ("/tasks", 2, 0, dt),
        ])
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        rows = {row["route"]: row for row in backend.stats_by_route()}
        assert rows["/projects"] == {
            "route": "/projects",
            "count": 3,
            "expired_count": 1,
            "oldest_expires_at": dt,
        }
        assert rows["/tasks"] == {
            "route": "/tasks",
            "count": 2,
            "expired_count": 0,
            "oldest_expires_at": dt,
        }

    def test_stats_issue_single_grouped_select_and_no_writes(self):
        stub = _ByRouteStubSession([])
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        backend.stats_by_route()
        assert any(
            stmt.startswith("select")
            and "from pm.idempotency_keys" in stmt
            and "where route in" in stmt
            and "group by route" in stmt
            and "order by route" in stmt
            for stmt in stub.statements
        )
        assert not any(stmt.startswith("insert") for stmt in stub.statements)
        assert not any(stmt.startswith("update") for stmt in stub.statements)
        assert not any(stmt.startswith("delete") for stmt in stub.statements)
        assert stub.commits == 0


class TestFacadeByRouteStats:

    def test_in_memory_payload_has_exact_keys_and_all_routes(self):
        cache = IdempotencyCache()
        payload = cache.stats_by_route()
        assert set(payload.keys()) == {"by_route", "backend_kind"}
        assert payload["backend_kind"] == "in_memory"
        assert [row["route"] for row in payload["by_route"]] == sorted(PM_POST_ROUTES)
        assert all(row["count"] == 0 for row in payload["by_route"])

    def test_durable_payload_has_exact_keys_and_all_routes(self):
        cache = IdempotencyCache()
        cache.use_durable_backend(_factory(_ByRouteStubSession([])))
        payload = cache.stats_by_route()
        assert set(payload.keys()) == {"by_route", "backend_kind"}
        assert payload["backend_kind"] == "durable"
        assert [row["route"] for row in payload["by_route"]] == sorted(PM_POST_ROUTES)

    def test_facade_pads_missing_routes(self):
        cache = IdempotencyCache()
        dt = datetime(2026, 4, 16, 10, 30, 0)
        cache.use_durable_backend(_factory(_ByRouteStubSession([
            ("/dependencies", 4, 2, dt),
        ])))
        rows = {row["route"]: row for row in cache.stats_by_route()["by_route"]}
        assert rows["/dependencies"]["count"] == 4
        assert rows["/projects"]["count"] == 0
