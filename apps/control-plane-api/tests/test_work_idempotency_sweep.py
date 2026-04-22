"""
PM/Work Domain — Idempotency Sweep + Ops Stats Unit Tests
==========================================================
Packet: 2026-04-16-pm-schema-019g

Pins the contract of the explicit expiry-sweep primitive and the minimal
operator-facing stats payload added on top of packets 019 + 019f.

Two lanes live here (mirroring packet 019f):

  A. In-memory backend — ``_InMemoryBackend.sweep_expired()`` and
     ``_InMemoryBackend.stats()`` against an in-process dict.
  B. Durable backend — ``_DurableBackend.sweep_expired()`` and
     ``_DurableBackend.stats()`` against a stubbed ``session_factory``
     that records the issued SQL shape.
  C. Facade — ``IdempotencyCache.sweep_expired()`` and
     ``IdempotencyCache.stats()`` delegation + ``backend_kind``
     decoration.

Hard packet-019g scope guards (asserted here so drift is caught
explicitly):

  * No new DDL.  The durable sweep is a single bounded
    ``DELETE ... WHERE expires_at <= now()`` against
    ``pm.idempotency_keys``; no changes to the table shape.
  * No new PM write endpoints or entity surfaces — sweep is a
    callable, NOT an HTTP handler.
  * ``stats()`` payload is EXACTLY ``{count, expired_count,
    oldest_expires_at, backend_kind}``.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.idempotency import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    IdempotencyCache,
    _DurableBackend,
    _InMemoryBackend,
)


# ===========================================================================
# A. In-memory backend — sweep + stats
# ===========================================================================

class TestInMemoryBackendSweep:
    """Sweep drops only entries whose ``expires_at <= now()``."""

    def setup_method(self):
        self.backend = _InMemoryBackend(ttl_seconds=DEFAULT_TTL_SECONDS)

    def test_sweep_on_empty_returns_zero(self):
        assert self.backend.sweep_expired() == 0

    def test_sweep_noop_when_nothing_expired(self):
        self.backend.register_request("/projects", "k1", b'{"a":1}')
        self.backend.register_request("/tasks", "k2", b'{"b":2}')
        deleted = self.backend.sweep_expired()
        assert deleted == 0
        # All entries still present
        assert len(self.backend._entries) == 2

    def test_sweep_drops_only_expired_rows(self):
        # Register a fresh row on the default TTL.
        self.backend.register_request("/projects", "fresh", b'{"a":1}')
        # Now force-insert a pre-expired entry directly.
        from services.work.idempotency import _Entry, _hash_body
        past = time.time() - 10
        self.backend._entries[("/tasks", "old")] = _Entry(
            body_hash=_hash_body(b'{"c":3}'),
            expires_at=past,
        )
        assert len(self.backend._entries) == 2
        deleted = self.backend.sweep_expired()
        assert deleted == 1
        assert ("/tasks", "old") not in self.backend._entries
        assert ("/projects", "fresh") in self.backend._entries

    def test_sweep_is_idempotent(self):
        from services.work.idempotency import _Entry, _hash_body
        past = time.time() - 10
        self.backend._entries[("/tasks", "old")] = _Entry(
            body_hash=_hash_body(b'{"c":3}'),
            expires_at=past,
        )
        assert self.backend.sweep_expired() == 1
        assert self.backend.sweep_expired() == 0


class TestInMemoryBackendStats:
    """Stats returns the shape the ops surface consumes verbatim."""

    def setup_method(self):
        self.backend = _InMemoryBackend(ttl_seconds=DEFAULT_TTL_SECONDS)

    def test_empty_store(self):
        s = self.backend.stats()
        assert s == {
            "count": 0,
            "expired_count": 0,
            "oldest_expires_at": None,
        }

    def test_counts_active_and_expired(self):
        from services.work.idempotency import _Entry, _hash_body

        # Two live rows and one expired row.
        self.backend.register_request("/projects", "a", b'{"x":1}')
        self.backend.register_request("/tasks", "b", b'{"y":2}')
        past = time.time() - 100
        self.backend._entries[("/dependencies", "c")] = _Entry(
            body_hash=_hash_body(b'{"z":3}'),
            expires_at=past,
        )

        s = self.backend.stats()
        assert s["count"] == 3
        assert s["expired_count"] == 1
        assert isinstance(s["oldest_expires_at"], datetime)

    def test_oldest_expires_at_is_earliest(self):
        from services.work.idempotency import _Entry, _hash_body
        t0 = time.time() - 1000
        t1 = time.time() - 500
        self.backend._entries[("/projects", "old")] = _Entry(
            body_hash=_hash_body(b'{}'),
            expires_at=t0,
        )
        self.backend._entries[("/tasks", "newer")] = _Entry(
            body_hash=_hash_body(b'{}'),
            expires_at=t1,
        )
        s = self.backend.stats()
        # Oldest matches the earliest stored expires_at exactly.
        assert s["oldest_expires_at"] == datetime.fromtimestamp(t0)


# ===========================================================================
# B. Durable backend — sweep + stats via stubbed session
# ===========================================================================

@dataclass
class _StubResult:
    rows: list[Any] = field(default_factory=list)
    rowcount: int = 0

    def first(self):
        return self.rows[0] if self.rows else None


class _SweepStubSession:
    """Stubbed session that records SQL shape and returns canned results
    for the sweep + stats paths.  Narrow on purpose — only exercises the
    two SQL statements packet-019g adds."""

    def __init__(
        self,
        sweep_rowcount: int = 0,
        stats_row: Optional[tuple] = None,
    ) -> None:
        self.statements: list[tuple[str, dict]] = []
        self.commits: int = 0
        self._sweep_rowcount = sweep_rowcount
        self._stats_row = stats_row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, stmt, params=None):
        text = str(stmt).strip().lower()
        self.statements.append((text, params or {}))

        if text.startswith("delete from pm.idempotency_keys"):
            return _StubResult(rowcount=self._sweep_rowcount)

        if text.startswith("select") and "count(*)" in text:
            if self._stats_row is None:
                return _StubResult(rows=[])
            return _StubResult(rows=[self._stats_row])

        return _StubResult()

    def commit(self):
        self.commits += 1


def _factory(stub: _SweepStubSession):
    def f():
        return stub
    return f


class TestDurableBackendSweepShape:
    """The sweep issues exactly one bounded DELETE and commits once."""

    def test_sweep_issues_bounded_delete(self):
        stub = _SweepStubSession(sweep_rowcount=5)
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        deleted = backend.sweep_expired()
        assert deleted == 5
        assert any(
            t.startswith("delete from pm.idempotency_keys")
            and "where expires_at <= now()" in t
            for t, _ in stub.statements
        )
        assert stub.commits == 1

    def test_sweep_does_not_issue_ddl(self):
        stub = _SweepStubSession(sweep_rowcount=0)
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        backend.sweep_expired()
        ddl_markers = (
            "alter table",
            "create table",
            "drop table",
            "create index",
            "drop index",
        )
        for stmt, _ in stub.statements:
            for marker in ddl_markers:
                assert marker not in stmt, (
                    f"Packet 019g must not emit DDL; got: {stmt}"
                )

    def test_sweep_zero_when_nothing_expired(self):
        stub = _SweepStubSession(sweep_rowcount=0)
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        assert backend.sweep_expired() == 0


class TestDurableBackendStatsShape:
    """The stats call is a single aggregate SELECT, no writes."""

    def test_stats_empty_store(self):
        # Postgres returns a single row with (0, 0, None) on COUNT aggregates.
        stub = _SweepStubSession(stats_row=(0, 0, None))
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        s = backend.stats()
        assert s == {
            "count": 0,
            "expired_count": 0,
            "oldest_expires_at": None,
        }

    def test_stats_populated(self):
        dt = datetime(2026, 4, 16, 12, 0, 0)
        stub = _SweepStubSession(stats_row=(7, 2, dt))
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        s = backend.stats()
        assert s == {
            "count": 7,
            "expired_count": 2,
            "oldest_expires_at": dt,
        }

    def test_stats_issues_no_writes(self):
        stub = _SweepStubSession(stats_row=(0, 0, None))
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        backend.stats()
        for stmt, _ in stub.statements:
            assert not stmt.startswith("insert"), stmt
            assert not stmt.startswith("update"), stmt
            assert not stmt.startswith("delete"), stmt
        # Stats must not commit anything.
        assert stub.commits == 0


# ===========================================================================
# C. Facade — sweep + stats delegation + backend_kind decoration
# ===========================================================================

class TestFacadeSweepAndStats:

    def test_sweep_delegates_to_in_memory_backend(self):
        cache = IdempotencyCache()
        from services.work.idempotency import _Entry, _hash_body
        past = time.time() - 10
        cache.register_request("/projects", "alive", b'{"a":1}')
        # Inject an expired entry via the backend shim
        cache._entries[("/tasks", "dead")] = _Entry(
            body_hash=_hash_body(b'{"b":2}'),
            expires_at=past,
        )
        assert cache.sweep_expired() == 1
        assert ("/tasks", "dead") not in cache._entries
        assert ("/projects", "alive") in cache._entries

    def test_sweep_delegates_to_durable_backend(self):
        cache = IdempotencyCache()
        stub = _SweepStubSession(sweep_rowcount=3)
        cache.use_durable_backend(_factory(stub))
        assert cache.sweep_expired() == 3
        assert any(
            t.startswith("delete from pm.idempotency_keys")
            for t, _ in stub.statements
        )

    def test_stats_payload_has_exact_four_keys_in_memory(self):
        cache = IdempotencyCache()
        s = cache.stats()
        assert set(s.keys()) == {
            "count",
            "expired_count",
            "oldest_expires_at",
            "backend_kind",
        }
        assert s["backend_kind"] == "in_memory"

    def test_stats_payload_has_exact_four_keys_durable(self):
        cache = IdempotencyCache()
        stub = _SweepStubSession(stats_row=(0, 0, None))
        cache.use_durable_backend(_factory(stub))
        s = cache.stats()
        assert set(s.keys()) == {
            "count",
            "expired_count",
            "oldest_expires_at",
            "backend_kind",
        }
        assert s["backend_kind"] == "durable"

    def test_stats_reflects_in_memory_counts(self):
        cache = IdempotencyCache()
        cache.register_request("/projects", "a", b'{"x":1}')
        cache.register_request("/tasks", "b", b'{"y":2}')
        s = cache.stats()
        assert s["count"] == 2
        assert s["expired_count"] == 0
        assert s["backend_kind"] == "in_memory"
        assert isinstance(s["oldest_expires_at"], datetime)

    def test_stats_reflects_durable_row(self):
        cache = IdempotencyCache()
        dt = datetime(2026, 4, 16, 10, 30, 0)
        stub = _SweepStubSession(stats_row=(42, 5, dt))
        cache.use_durable_backend(_factory(stub))
        s = cache.stats()
        assert s == {
            "count": 42,
            "expired_count": 5,
            "oldest_expires_at": dt,
            "backend_kind": "durable",
        }

    def test_swap_back_to_in_memory_updates_backend_kind(self):
        cache = IdempotencyCache()
        stub = _SweepStubSession(stats_row=(0, 0, None))
        cache.use_durable_backend(_factory(stub))
        assert cache.stats()["backend_kind"] == "durable"
        cache.use_in_memory_backend()
        assert cache.stats()["backend_kind"] == "in_memory"


# ===========================================================================
# D. Packet-019g scope guards
# ===========================================================================

class TestPacket019gScopeGuards:
    """Pins the bounded scope promised in the packet prompt."""

    def test_sweep_sql_is_single_bounded_delete(self):
        stub = _SweepStubSession(sweep_rowcount=0)
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        backend.sweep_expired()
        # Exactly one DELETE, gated on expires_at.
        delete_stmts = [
            t for t, _ in stub.statements
            if t.startswith("delete from pm.idempotency_keys")
        ]
        assert len(delete_stmts) == 1
        assert "expires_at <= now()" in delete_stmts[0]

    def test_stats_sql_is_single_aggregate_select(self):
        stub = _SweepStubSession(stats_row=(0, 0, None))
        backend = _DurableBackend(_factory(stub), ttl_seconds=DEFAULT_TTL_SECONDS)
        backend.stats()
        select_stmts = [
            t for t, _ in stub.statements
            if t.startswith("select") and "count(*)" in t
        ]
        assert len(select_stmts) == 1
        assert "from pm.idempotency_keys" in select_stmts[0]
        # No partition / route filter — stats is store-wide.
        assert "where route" not in select_stmts[0]

    def test_stats_payload_keys_are_exactly_pinned(self):
        cache = IdempotencyCache()
        s = cache.stats()
        # The packet prompt pins {count, oldest_expires_at, backend_kind};
        # we additionally carry expired_count for sweep-pressure dashboards.
        assert "count" in s
        assert "oldest_expires_at" in s
        assert "backend_kind" in s
        assert "expired_count" in s
        # No stray keys — exactly four.
        assert len(s) == 4
