"""
PM/Work Domain — Durable Idempotency Store Unit Tests
======================================================
Packet: 2026-04-16-pm-schema-019f

Pins the contract of the SQL-backed ``_DurableBackend`` that replaces
the process-local packet-019 cache for the seven PM POST handlers.

Two lanes live in this module:

  A. Pure-backend tests — exercise ``_DurableBackend`` against a stubbed
     ``session_factory`` that records issued SQL.  These verify the
     INSERT-ON-CONFLICT-RETURNING / SELECT / UPDATE / DELETE shape
     without requiring a live PostgreSQL.

  B. Facade tests — exercise ``IdempotencyCache.use_durable_backend``
     and ``use_in_memory_backend`` to verify the pluggable-backend
     swap, the ``backend_kind()`` introspection, the ``_entries``
     shim returning an empty dict under the durable backend, and
     the ``discard_registration`` delegation.

Real-PG end-to-end coverage lives in
``test_work_idempotency_durable_integration.py`` (skips cleanly when
no PostgreSQL is reachable, mirroring packets 012g / 013i / 014i /
015i / 016i / 017i / 018i / 019-PATCH-harness-integration).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.idempotency import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    IDEMPOTENCY_HEADER,
    IdempotencyCache,
    IdempotencyHit,
    PM_POST_ROUTES,
    _DurableBackend,
    _hash_body,
)


# ===========================================================================
# A. Pure-backend tests via a stub session
# ===========================================================================

@dataclass
class _StubRow:
    body_hash: str
    response_status: Optional[int]
    response_body: Optional[bytes]

    def __iter__(self):
        return iter(
            (self.body_hash, self.response_status, self.response_body)
        )


@dataclass
class _StubResult:
    rows: list[Any] = field(default_factory=list)

    def first(self):
        return self.rows[0] if self.rows else None


class _StubSession:
    """Records SQL statements + parameters issued against a fake session.

    Encodes the minimum behaviour that ``_DurableBackend`` relies on:

      * ``INSERT ... ON CONFLICT DO NOTHING RETURNING`` returns
        either a sentinel row (first-sight) or empty (conflict).
      * A subsequent ``SELECT`` returns the currently-stored row.
      * ``UPDATE`` / ``DELETE`` are recorded but return empty result.
      * ``COMMIT`` is tracked.
    """

    def __init__(self):
        self.store: dict[tuple[str, str], _StubRow] = {}
        self.statements: list[tuple[str, dict]] = []
        self.commits: int = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def _key(self, params):
        return (params["route"], params["key"])

    def execute(self, stmt, params=None):
        text = str(stmt).strip().lower()
        params = params or {}
        self.statements.append((text, params))

        if text.startswith("delete from pm.idempotency_keys where expires_at"):
            return _StubResult()

        if text.startswith("insert into pm.idempotency_keys"):
            k = self._key(params)
            if k in self.store:
                # ON CONFLICT DO NOTHING — no row returned.
                return _StubResult(rows=[])
            self.store[k] = _StubRow(
                body_hash=params["body_hash"],
                response_status=None,
                response_body=None,
            )
            return _StubResult(rows=[("inserted-id",)])

        if text.startswith("select body_hash"):
            row = self.store.get(self._key(params))
            return _StubResult(rows=[row] if row else [])

        if text.startswith("update pm.idempotency_keys"):
            row = self.store.get(self._key(params))
            if row is not None and row.body_hash == params["body_hash"]:
                row.response_status = params["status"]
                row.response_body = params["body"]
            return _StubResult()

        if text.startswith("delete from pm.idempotency_keys"):
            k = self._key(params)
            row = self.store.get(k)
            if row is not None and row.body_hash == params.get("body_hash"):
                # Only when status is NULL
                if row.response_status is None:
                    del self.store[k]
            return _StubResult()

        return _StubResult()

    def commit(self):
        self.commits += 1


def _session_factory_from_stub(stub: _StubSession):
    def factory():
        return stub
    return factory


class TestDurableBackendRegisterRequest:
    """``_DurableBackend.register_request`` — first-sight, replay,
    mismatch, and in-flight paths."""

    def setup_method(self):
        self.stub = _StubSession()
        self.backend = _DurableBackend(
            _session_factory_from_stub(self.stub),
            ttl_seconds=DEFAULT_TTL_SECONDS,
        )

    def test_first_sight_inserts_and_returns_none(self):
        hit = self.backend.register_request("/projects", "k1", b'{"a":1}')
        assert hit is None
        assert ("/projects", "k1") in self.stub.store
        # INSERT was committed
        assert self.stub.commits >= 1

    def test_replay_with_matching_body_returns_cached_response(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        self.backend.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"project_id":"x"}',
        )
        hit = self.backend.register_request("/projects", "k1", b'{"a":1}')
        assert isinstance(hit, IdempotencyHit)
        assert hit.match is True
        assert hit.status == 201
        assert hit.response_body == b'{"project_id":"x"}'

    def test_replay_with_reordered_keys_matches(self):
        self.backend.register_request(
            "/projects", "k1", b'{"a":1,"b":2}',
        )
        self.backend.record_response(
            "/projects", "k1", b'{"a":1,"b":2}', 201, b'{"ok":true}',
        )
        hit = self.backend.register_request(
            "/projects", "k1", b'{"b":2,"a":1}',
        )
        assert hit is not None
        assert hit.match is True
        assert hit.response_body == b'{"ok":true}'

    def test_replay_before_response_recorded_returns_match_no_body(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        # No record_response yet.
        hit = self.backend.register_request("/projects", "k1", b'{"a":1}')
        assert hit is not None
        assert hit.match is True
        assert hit.status is None
        assert hit.response_body is None

    def test_mismatching_body_returns_match_false(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        hit = self.backend.register_request("/projects", "k1", b'{"a":2}')
        assert hit is not None
        assert hit.match is False
        assert hit.status is None

    def test_per_route_namespacing(self):
        h1 = self.backend.register_request("/projects", "k1", b'{"a":1}')
        h2 = self.backend.register_request("/tasks", "k1", b'{"a":1}')
        assert h1 is None
        assert h2 is None
        assert ("/projects", "k1") in self.stub.store
        assert ("/tasks", "k1") in self.stub.store


class TestDurableBackendDiscardRegistration:
    """``_DurableBackend.discard_registration`` — validation-failure
    cleanup gated on ``response_status IS NULL``."""

    def setup_method(self):
        self.stub = _StubSession()
        self.backend = _DurableBackend(
            _session_factory_from_stub(self.stub),
            ttl_seconds=DEFAULT_TTL_SECONDS,
        )

    def test_discards_unrecorded_row(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        assert ("/projects", "k1") in self.stub.store
        self.backend.discard_registration("/projects", "k1", b'{"a":1}')
        assert ("/projects", "k1") not in self.stub.store

    def test_preserves_row_with_recorded_success(self):
        """Once a success response is cached, a later discard MUST NOT
        evict the row — that would defeat the replay contract."""
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        self.backend.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"ok":true}',
        )
        self.backend.discard_registration("/projects", "k1", b'{"a":1}')
        assert ("/projects", "k1") in self.stub.store

    def test_noop_on_missing_row(self):
        # Just shouldn't raise
        self.backend.discard_registration("/projects", "k1", b'{"a":1}')


class TestDurableBackendRecordResponse:

    def setup_method(self):
        self.stub = _StubSession()
        self.backend = _DurableBackend(
            _session_factory_from_stub(self.stub),
            ttl_seconds=DEFAULT_TTL_SECONDS,
        )

    def test_updates_row_with_matching_body_hash(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        self.backend.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"ok":true}',
        )
        row = self.stub.store[("/projects", "k1")]
        assert row.response_status == 201
        assert row.response_body == b'{"ok":true}'

    def test_update_with_mismatching_body_hash_is_noop(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        self.backend.record_response(
            "/projects", "k1", b'{"a":2}', 201, b'{"ok":true}',
        )
        row = self.stub.store[("/projects", "k1")]
        assert row.response_status is None


# ===========================================================================
# B. Facade tests — pluggable backend swap
# ===========================================================================

class TestIdempotencyCacheFacade:

    def test_default_backend_is_in_memory(self):
        cache = IdempotencyCache()
        assert cache.backend_kind() == "in_memory"

    def test_use_durable_backend_reports_durable(self):
        cache = IdempotencyCache()
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        assert cache.backend_kind() == "durable"

    def test_use_in_memory_after_durable_swaps_back(self):
        cache = IdempotencyCache()
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        cache.use_in_memory_backend()
        assert cache.backend_kind() == "in_memory"

    def test_entries_shim_returns_empty_under_durable_backend(self):
        cache = IdempotencyCache()
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        # Shim returns {} so packet-019 code that peeks at
        # ``cache._entries`` doesn't raise under the durable backend.
        assert cache._entries == {}

    def test_entries_shim_returns_dict_under_in_memory_backend(self):
        cache = IdempotencyCache()
        cache.register_request("/projects", "k1", b'{"a":1}')
        assert len(cache._entries) == 1

    def test_register_and_replay_through_facade_on_durable_backend(self):
        cache = IdempotencyCache()
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        assert cache.register_request("/projects", "k1", b'{"a":1}') is None
        cache.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"ok":true}',
        )
        hit = cache.register_request("/projects", "k1", b'{"a":1}')
        assert hit is not None
        assert hit.match is True
        assert hit.response_body == b'{"ok":true}'

    def test_ttl_propagates_to_new_backends(self):
        cache = IdempotencyCache()
        cache.set_ttl(99)
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        cache.register_request("/projects", "k1", b'{"a":1}')
        # TTL param was threaded through
        insert_stmts = [
            (t, p) for t, p in stub.statements
            if t.startswith("insert into pm.idempotency_keys")
        ]
        assert insert_stmts
        _, params = insert_stmts[0]
        assert params["ttl"] == 99

    def test_discard_delegates_to_backend(self):
        cache = IdempotencyCache()
        stub = _StubSession()
        cache.use_durable_backend(_session_factory_from_stub(stub))
        cache.register_request("/projects", "k1", b'{"a":1}')
        assert ("/projects", "k1") in stub.store
        cache.discard_registration("/projects", "k1", b'{"a":1}')
        assert ("/projects", "k1") not in stub.store


class TestPMPostRoutes:
    """The ``PM_POST_ROUTES`` constant pins the seven covered routes."""

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

    def test_no_wbs_nodes_route(self):
        assert "/wbs-nodes" not in PM_POST_ROUTES
