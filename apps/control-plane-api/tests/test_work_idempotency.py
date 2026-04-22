"""
PM/Work Domain — Idempotency Seam Unit Tests
=============================================
Packet: 2026-04-16-pm-schema-019

Exercises the zero-DDL idempotency seam introduced in packet 019 at two
levels:

  A. ``IdempotencyCache`` — the process-local in-memory store that
     backs ``services.work.idempotency.idempotency_cache``.  Verifies
     first-sight, matching-replay, mismatching-body, TTL eviction, body
     hash canonicalisation, and per-route namespacing semantics.

  B. End-to-end over one representative POST route (``/projects``) via
     the FastAPI TestClient — proves the header-driven replay and 422
     mismatch surface end-to-end without coupling to per-entity fixture
     scaffolding.

The TestClient exercise uses the same mock-DB pattern used by the
per-entity write tests so the idempotency behaviour is observed without
a live Postgres; see ``test_work_project_write.py`` for the underlying
pattern.
"""

import sys
import os
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from services.work.idempotency import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    IDEMPOTENCY_HEADER,
    IdempotencyCache,
    IdempotencyHit,
    _hash_body,
    idempotency_cache,
)


# ===========================================================================
# A. IdempotencyCache unit tests
# ===========================================================================

class TestHashBody:
    """Tests for ``_hash_body``."""

    def test_empty_bytes_is_stable(self):
        assert _hash_body(b"") == _hash_body(b"")

    def test_different_bytes_produce_different_hashes(self):
        a = b'{"title": "A"}'
        b = b'{"title": "B"}'
        assert _hash_body(a) != _hash_body(b)

    def test_reordered_keys_hash_identically(self):
        """Canonical JSON form: ``{"a":1,"b":2}`` == ``{"b":2,"a":1}``."""
        a = b'{"title": "proj", "client_id": "c1"}'
        b = b'{"client_id": "c1", "title": "proj"}'
        assert _hash_body(a) == _hash_body(b)

    def test_whitespace_differences_hash_identically(self):
        a = b'{"title": "proj"}'
        b = b'{"title":"proj"}'
        assert _hash_body(a) == _hash_body(b)

    def test_non_json_bytes_fall_back_to_raw_sha(self):
        """Non-JSON bodies fall through to a raw SHA-256 of the bytes."""
        digest_a = _hash_body(b"<xml/>")
        digest_b = _hash_body(b"<xml/>")
        digest_c = _hash_body(b"<html/>")
        assert digest_a == digest_b
        assert digest_a != digest_c


class TestIdempotencyCacheCore:
    """Tests for the ``IdempotencyCache`` store directly."""

    def setup_method(self):
        self.cache = IdempotencyCache(ttl_seconds=DEFAULT_TTL_SECONDS)

    def test_first_sight_returns_none(self):
        hit = self.cache.register_request("/projects", "k1", b'{"a":1}')
        assert hit is None

    def test_matching_replay_returns_hit_with_recorded_response(self):
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        self.cache.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"project_id":"x"}',
        )
        hit = self.cache.register_request("/projects", "k1", b'{"a":1}')
        assert isinstance(hit, IdempotencyHit)
        assert hit.match is True
        assert hit.status == 201
        assert hit.response_body == b'{"project_id":"x"}'

    def test_matching_replay_before_response_recorded(self):
        """Same key + same body, but the original response hasn't landed
        yet — the replayed request should still be allowed to proceed."""
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        hit = self.cache.register_request("/projects", "k1", b'{"a":1}')
        assert hit is not None
        assert hit.match is True
        assert hit.status is None
        assert hit.response_body is None

    def test_mismatching_body_returns_match_false(self):
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        hit = self.cache.register_request("/projects", "k1", b'{"a":2}')
        assert hit is not None
        assert hit.match is False
        assert hit.status is None
        assert hit.response_body is None

    def test_canonicalised_body_matches(self):
        """Key-reordered bodies are treated as identical."""
        self.cache.register_request(
            "/projects", "k1", b'{"a": 1, "b": 2}',
        )
        self.cache.record_response(
            "/projects", "k1", b'{"a": 1, "b": 2}', 201, b'{"ok": true}',
        )
        hit = self.cache.register_request(
            "/projects", "k1", b'{"b": 2, "a": 1}',
        )
        assert hit is not None
        assert hit.match is True
        assert hit.response_body == b'{"ok": true}'

    def test_per_route_namespacing(self):
        """The same key is allowed on two different routes without collision."""
        h1 = self.cache.register_request("/projects", "k1", b'{"a":1}')
        h2 = self.cache.register_request("/tasks", "k1", b'{"a":1}')
        assert h1 is None
        assert h2 is None

    def test_record_response_noop_on_wrong_body_hash(self):
        """A successful response for a body different from the registered
        one must not overwrite the original entry — otherwise a hostile
        later call could hijack the replay."""
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        # Simulate a stale record-call referencing a different body
        self.cache.record_response(
            "/projects", "k1", b'{"a":2}', 201, b'{"ok":true}',
        )
        hit = self.cache.register_request("/projects", "k1", b'{"a":1}')
        # Entry is still the pre-record sentinel (match True, no body)
        assert hit is not None
        assert hit.match is True
        assert hit.response_body is None

    def test_record_response_noop_after_eviction(self):
        """Record on an evicted entry silently no-ops."""
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        self.cache.clear()
        self.cache.record_response(
            "/projects", "k1", b'{"a":1}', 201, b'{"ok":true}',
        )
        hit = self.cache.register_request("/projects", "k1", b'{"a":1}')
        # Post-clear + post-no-op-record, the new register is a first-sight
        assert hit is None

    def test_ttl_expiry_evicts_entries(self):
        cache = IdempotencyCache(ttl_seconds=0)
        cache.register_request("/projects", "k1", b'{"a":1}')
        # Next call prunes expired entries, so the prior registration is
        # gone and this is again a first-sight.
        hit = cache.register_request("/projects", "k1", b'{"a":2}')
        assert hit is None

    def test_clear_wipes_all_entries(self):
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        self.cache.register_request("/tasks", "k2", b'{"a":2}')
        self.cache.clear()
        assert (
            self.cache.register_request("/projects", "k1", b'{"a":1}') is None
        )
        assert (
            self.cache.register_request("/tasks", "k2", b'{"a":2}') is None
        )

    def test_set_ttl_applies_to_new_entries(self):
        self.cache.set_ttl(0)
        self.cache.register_request("/projects", "k1", b'{"a":1}')
        hit = self.cache.register_request("/projects", "k1", b'{"a":2}')
        # Previous entry expired, so this is a first-sight registration.
        assert hit is None


# ===========================================================================
# B. End-to-end over POST /projects via TestClient
# ===========================================================================

VALID_CLIENT_ID = UUID("11111111-1111-0000-0000-000000000001")
VALID_SITE_ID = UUID("22222222-2222-0000-0000-000000000001")


def _mock_db_for_project_writes():
    from models.org import Client, Site, BusinessUnit, Contract
    from models.work import Project

    mock_db = MagicMock()
    created = [None]

    def mock_get(model_class, pk):
        if model_class is Client and pk == VALID_CLIENT_ID:
            m = MagicMock()
            m.client_id = pk
            m.name = "Mock Client"
            return m
        if model_class is Site and pk == VALID_SITE_ID:
            m = MagicMock()
            m.site_id = pk
            m.name = "Mock Site"
            return m
        if model_class is BusinessUnit:
            return None
        if model_class is Contract:
            return None
        if model_class is Project:
            return None
        return None

    def mock_add(obj):
        created[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created[0] is not None:
            # Deterministic project_id so cached response bytes match
            # across replays — real servers would mint a new UUID, but
            # for the idempotency contract the replay returns the
            # originally-captured bytes, so we don't care about uniqueness
            # across test methods as long as the cache is cleared between.
            if getattr(created[0], "project_id", None) is None:
                created[0].project_id = UUID(
                    "cccccccc-0000-0000-0000-000000000042",
                )
            if getattr(created[0], "created_at", None) is None:
                created[0].created_at = datetime(
                    2026, 4, 16, tzinfo=timezone.utc,
                )
            if getattr(created[0], "updated_at", None) is None:
                created[0].updated_at = datetime(
                    2026, 4, 16, tzinfo=timezone.utc,
                )
            if getattr(created[0], "provenance_status", None) is None:
                created[0].provenance_status = "curated"
            for attr in [
                "client_name", "site_name", "business_unit_name",
                "contract_title", "p6_project_id", "p6_short_name",
                "p6_data_date", "actual_start_at", "actual_end_at",
            ]:
                if not hasattr(created[0], attr):
                    setattr(created[0], attr, None)

    def mock_refresh(obj):
        pass

    mock_db.get = mock_get
    mock_db.add = mock_add
    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.one_or_none.return_value = None
    mock_db.query.return_value = mock_query

    return mock_db


@pytest.fixture
def client_write():
    from config import get_db
    from main import app

    mock_db = _mock_db_for_project_writes()

    def override_get_db():
        yield mock_db

    # ``main.py`` swaps the singleton to the durable DB-backed backend at
    # app init (packet 019f); this in-memory test lane explicitly opts
    # back to the process-local backend so the mocked DB session isn't
    # asked to execute SQL against ``pm.idempotency_keys``.
    idempotency_cache.use_in_memory_backend()

    app.dependency_overrides[get_db] = override_get_db
    # Reset the singleton between tests to avoid cross-test contamination.
    idempotency_cache.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    idempotency_cache.clear()


MINIMAL_PROJECT_PAYLOAD = {
    "project_code": "IDEMP-019",
    "title": "Idempotency Test Project",
    "client_id": str(VALID_CLIENT_ID),
    "site_id": str(VALID_SITE_ID),
}


class TestIdempotencyOverPostProjects:
    """End-to-end idempotency behaviour via POST /api/v1/work/projects."""

    def test_no_header_runs_as_before(self, client_write):
        """Absence of the header is a no-op — handler runs normally."""
        resp = client_write.post(
            "/api/v1/work/projects", json=MINIMAL_PROJECT_PAYLOAD,
        )
        assert resp.status_code == 201
        # Nothing recorded under no key.
        assert len(idempotency_cache._entries) == 0

    def test_first_request_with_key_runs_and_caches(self, client_write):
        resp = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        assert resp.status_code == 201
        assert len(idempotency_cache._entries) == 1

    def test_replay_with_matching_key_and_body_returns_cached_response(
        self, client_write,
    ):
        first = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        second = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        # Byte-for-byte identical body (same project_id, same timestamps).
        assert first.content == second.content

    def test_replay_with_reordered_keys_returns_same_cached_response(
        self, client_write,
    ):
        first = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        reordered = {
            "title": MINIMAL_PROJECT_PAYLOAD["title"],
            "site_id": MINIMAL_PROJECT_PAYLOAD["site_id"],
            "project_code": MINIMAL_PROJECT_PAYLOAD["project_code"],
            "client_id": MINIMAL_PROJECT_PAYLOAD["client_id"],
        }
        second = client_write.post(
            "/api/v1/work/projects",
            json=reordered,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.content == second.content

    def test_replay_with_different_body_returns_422_mismatch(
        self, client_write,
    ):
        first = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        assert first.status_code == 201

        # Same key, different payload.
        second = client_write.post(
            "/api/v1/work/projects",
            json={
                **MINIMAL_PROJECT_PAYLOAD,
                "title": "A different title",
            },
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        assert second.status_code == 422
        body = second.json()
        assert body["detail"] == (
            "Idempotency-Key reused with different payload"
        )
        assert "errors" in body
        assert "idempotency_key" in body["errors"]

    def test_different_keys_do_not_replay(self, client_write):
        first = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "abc-123"},
        )
        second = client_write.post(
            "/api/v1/work/projects",
            json=MINIMAL_PROJECT_PAYLOAD,
            headers={IDEMPOTENCY_HEADER: "xyz-789"},
        )
        assert first.status_code == 201
        assert second.status_code == 201
        # Distinct fresh runs — cache now has 2 entries.
        assert len(idempotency_cache._entries) == 2
