"""
PM/Work Domain — Idempotency Seam
==================================
Packet: 2026-04-16-pm-schema-019  (process-local in-memory cache)
Packet: 2026-04-16-pm-schema-019f (durable DB-backed store)
Packet: 2026-04-16-pm-schema-019g (explicit sweep + minimal ops stats)
Packet: 2026-04-16-pm-schema-019i (per-route ops breakdown)

Backs the ``Idempotency-Key`` HTTP header contract on the seven PM POST
handlers (projects, work_packages, tasks, assignments, dependencies,
execution_issues, progress_snapshots).  The seam activates only when
the caller supplies ``Idempotency-Key``; otherwise handlers behave
exactly as they did before packet 019.

Header-driven contract (unchanged from packet 019):

  * Cache key: ``(route, Idempotency-Key)``.  Route namespacing permits
    the same Idempotency-Key to be reused across different POST routes
    without collision.
  * Body integrity: SHA-256 over canonical-JSON form of the request
    body so logically-equivalent payloads (reordered keys, whitespace
    differences) hash identically.
  * Match + body same: the cached ``(status, body)`` is replayed
    byte-for-byte.
  * Match + body differs: 422 with
    ``{"detail": "Idempotency-Key reused with different payload",
       "errors": {"idempotency_key": "..."}}`` — shape mirrors the
    existing FK merged-error payload.
  * Match + response not yet recorded: handler runs again (in-flight
    or prior-error recovery).
  * Only successful responses (2xx) are cached.  422 validation
    failures are explicitly NOT persisted — the runtime deletes
    pre-registered rows on validation failure so callers can retry the
    same key with a corrected payload.

Pluggable backends (packet 019f):

  * ``_InMemoryBackend`` — process-local ``dict``; the packet-019
    behaviour.  Used by mock-DB unit tests and as the default so app
    startup order (router import before DB config) stays safe.
  * ``_DurableBackend`` — SQL-backed; rows stored in
    ``pm.idempotency_keys`` via a caller-supplied ``session_factory``.
    Durable across process restarts and coordinates across multi-
    instance deployments via the ``UNIQUE (route, idempotency_key)``
    constraint + ``ON CONFLICT DO NOTHING`` insert semantics.

Production wiring (``main.py``) swaps to ``_DurableBackend`` at app
init; tests that want the packet-019 in-memory behaviour call
``idempotency_cache.use_in_memory_backend()`` in their fixture setup,
and tests that want to exercise durable behaviour call
``use_durable_backend(factory)`` with a real PostgreSQL-bound
sessionmaker.

Packet 019g additions (runtime + observability only; no DDL):

  * ``IdempotencyCache.sweep_expired()`` — delete every row whose
    ``expires_at`` has passed.  Bounded to the durable table (under
    the durable backend) or the in-memory dict (under the in-memory
    backend).  Returns the number of rows deleted so callers can log
    / alert / emit metrics.  Intended to be driven on a schedule
    (cron, k8s CronJob) or on-demand.
  * ``IdempotencyCache.stats()`` — minimal operator-facing payload
    ``{count, expired_count, oldest_expires_at, backend_kind}``.  The
    operator-facing read surface at ``GET /api/v1/ops/pm-idempotency/
    stats`` (packet 019g) serialises this dict directly.

Packet 019i additions (runtime observability only; no DDL, no write
surface, no new sweep path):

  * ``IdempotencyCache.stats_by_route()`` — per-route inventory and
    expiry pressure, bounded strictly to the seven PM POST routes in
    ``PM_POST_ROUTES``.  Response shape:
    ``{by_route: [{route, count, expired_count, oldest_expires_at},
    ...], backend_kind}``.  Always returns exactly seven rows, sorted
    by route, with zero-padded counts for routes that currently have
    no idempotency rows — this guarantees deterministic payload shape
    regardless of backend state and avoids inventing new route
    buckets.  The operator-facing read surface at
    ``GET /api/v1/ops/pm-idempotency/by-route`` (packet 019i)
    serialises this dict directly.

Public surface:

  * ``IdempotencyCache`` — the facade used by the router.  Pluggable
    backend selected via ``use_in_memory_backend()`` /
    ``use_durable_backend()``.  Ops-maintenance methods
    ``sweep_expired()`` and ``stats()`` added in packet 019g.
  * ``idempotency_cache`` — module singleton.
  * ``IdempotencyHit`` — sentinel returned by ``register_request``
    when a cached response should be served (or 422 mismatch raised).
  * ``IDEMPOTENCY_HEADER`` — the header name constant (Stripe-style).
  * ``DEFAULT_TTL_SECONDS`` — 24 h default TTL.
  * ``_hash_body(body_bytes)`` — canonical SHA-256 hex digest.
  * ``PM_POST_ROUTES`` — the seven route identifiers covered.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 24 h TTL by default.  Kept deliberately short so bounded-size cache /
# table growth stays manageable without a dedicated sweeper.
DEFAULT_TTL_SECONDS: int = 24 * 60 * 60

# Header name — Stripe-style.  Single authority so tests and follow-on
# packets reference one constant rather than re-typing the string.
IDEMPOTENCY_HEADER: str = "Idempotency-Key"

# The seven PM POST routes covered by the idempotency seam.  Pinned
# here so the durable-backend CHECK constraint on ``pm.idempotency_keys``
# has a single authoritative source.  Any expansion of the seam to new
# routes MUST ship alongside a migration that widens the CHECK.
PM_POST_ROUTES: frozenset[str] = frozenset({
    "/projects",
    "/work-packages",
    "/tasks",
    "/assignments",
    "/dependencies",
    "/execution-issues",
    "/progress-snapshots",
})


# ---------------------------------------------------------------------------
# Body hashing
# ---------------------------------------------------------------------------

def _hash_body(body_bytes: bytes) -> str:
    """SHA-256 hex digest over the canonical-JSON form of the request body.

    Bytes are parsed + re-serialised with ``sort_keys=True`` so logically-
    equivalent payloads hash to the same digest.  Empty or non-JSON bodies
    fall back to raw SHA-256 of the bytes (preserves the packet-019
    contract on non-JSON payloads).
    """
    if not body_bytes:
        return hashlib.sha256(b"").hexdigest()
    try:
        parsed = json.loads(body_bytes)
    except (ValueError, TypeError):
        return hashlib.sha256(body_bytes).hexdigest()
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Sentinels
# ---------------------------------------------------------------------------

@dataclass
class IdempotencyHit:
    """Sentinel returned by ``register_request`` when the key has been
    seen before.

    ``match`` is ``True`` when the replayed body hash matches the
    originally-recorded body hash.  In that case ``status`` and
    ``response_body`` carry the previously-returned success response (or
    ``None`` if the original request is still in-flight — the response
    hasn't been recorded yet).

    When ``match`` is ``False`` the caller should produce a ``422``
    response indicating that the key has been reused with a different
    payload.
    """

    match: bool
    status: Optional[int] = None
    response_body: Optional[bytes] = None


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------

class _Backend(Protocol):
    """Storage backend interface.

    Kept intentionally narrow so swapping in a different durable store
    (e.g. Redis in a future packet) is a one-class change.
    """

    def register_request(
        self, route: str, key: str, body_bytes: bytes,
    ) -> Optional[IdempotencyHit]: ...
    def record_response(
        self, route: str, key: str, body_bytes: bytes,
        status: int, response_body: bytes,
    ) -> None: ...
    def discard_registration(
        self, route: str, key: str, body_bytes: bytes,
    ) -> None: ...
    def clear(self) -> None: ...
    def set_ttl(self, seconds: int) -> None: ...

    # Packet 019g — explicit maintenance + observability hooks.
    def sweep_expired(self) -> int: ...
    def stats(self) -> dict: ...

    # Packet 019i — per-route observability breakdown.  Returns raw
    # per-route rows for routes with at least one entry; the facade
    # reconciles against ``PM_POST_ROUTES`` and pads zero-rows for any
    # missing route so the API-level payload always carries exactly
    # seven rows in deterministic order.
    def stats_by_route(self) -> list[dict]: ...


# ---------------------------------------------------------------------------
# In-memory backend (process-local; packet 019 behaviour)
# ---------------------------------------------------------------------------

@dataclass
class _Entry:
    body_hash: str
    status: Optional[int] = None
    response_body: Optional[bytes] = None
    expires_at: float = 0.0


class _InMemoryBackend:
    """Process-local in-memory backend.  Mirrors packet-019 semantics.

    Thread-safe via a coarse-grained mutex; expected QPS for PM writes
    is small enough that finer-grained locking is not justified.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._entries: dict[tuple[str, str], _Entry] = {}

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def set_ttl(self, seconds: int) -> None:
        with self._lock:
            self._ttl = seconds

    def _prune_expired_locked(self, now: float) -> None:
        expired = [k for k, e in self._entries.items() if e.expires_at <= now]
        for k in expired:
            del self._entries[k]

    def register_request(
        self, route: str, key: str, body_bytes: bytes,
    ) -> Optional[IdempotencyHit]:
        body_hash = _hash_body(body_bytes)
        cache_key = (route, key)
        now = time.time()
        with self._lock:
            self._prune_expired_locked(now)
            existing = self._entries.get(cache_key)
            if existing is not None:
                if existing.body_hash == body_hash:
                    return IdempotencyHit(
                        match=True,
                        status=existing.status,
                        response_body=existing.response_body,
                    )
                return IdempotencyHit(match=False)
            self._entries[cache_key] = _Entry(
                body_hash=body_hash,
                expires_at=now + self._ttl,
            )
        return None

    def record_response(
        self, route: str, key: str, body_bytes: bytes,
        status: int, response_body: bytes,
    ) -> None:
        body_hash = _hash_body(body_bytes)
        cache_key = (route, key)
        now = time.time()
        with self._lock:
            existing = self._entries.get(cache_key)
            if existing is None or existing.body_hash != body_hash:
                return
            existing.status = status
            existing.response_body = response_body
            existing.expires_at = now + self._ttl

    def discard_registration(
        self, route: str, key: str, body_bytes: bytes,
    ) -> None:
        """Remove a pre-registered entry whose response was never
        recorded (e.g. validation-failure 422 path).  No-ops if the
        entry already carries a recorded success response — those MUST
        survive for replay parity with packet 019 semantics."""
        body_hash = _hash_body(body_bytes)
        cache_key = (route, key)
        with self._lock:
            existing = self._entries.get(cache_key)
            if existing is None:
                return
            if existing.body_hash != body_hash:
                return
            if existing.status is not None:
                # A success response has already been recorded; do NOT
                # evict — that would defeat the replay contract.
                return
            del self._entries[cache_key]

    # ------------------------------------------------------------------
    # Packet 019g — sweep + stats
    # ------------------------------------------------------------------

    def sweep_expired(self) -> int:
        """Drop every expired entry.  Returns the number deleted.

        Bounded to `expires_at <= now()` so in-flight and replay-ready
        rows are untouched until their own TTL lapses.
        """
        now = time.time()
        with self._lock:
            expired_keys = [
                k for k, e in self._entries.items() if e.expires_at <= now
            ]
            for k in expired_keys:
                del self._entries[k]
            return len(expired_keys)

    def stats(self) -> dict:
        """Minimal observability payload for the in-memory backend.

        Mirrors the durable-backend stats shape so the ops endpoint
        produces the same keys regardless of which backend is active.
        """
        now = time.time()
        with self._lock:
            count = len(self._entries)
            expired_count = sum(
                1 for e in self._entries.values() if e.expires_at <= now
            )
            oldest: Optional[datetime] = None
            if self._entries:
                earliest_ts = min(e.expires_at for e in self._entries.values())
                oldest = datetime.fromtimestamp(earliest_ts)
        return {
            "count": count,
            "expired_count": expired_count,
            "oldest_expires_at": oldest,
        }

    def stats_by_route(self) -> list[dict]:
        """Per-route inventory for the in-memory backend.

        Returns one row per route that currently has at least one
        entry — the facade later pads zero-rows for routes absent
        from this result so the API payload always carries exactly
        the seven ``PM_POST_ROUTES`` entries.  Values: ``count``,
        ``expired_count``, ``oldest_expires_at``.
        """
        now = time.time()
        with self._lock:
            per: dict[str, dict] = {}
            for (route, _key), entry in self._entries.items():
                bucket = per.setdefault(
                    route,
                    {
                        "count": 0,
                        "expired_count": 0,
                        "_oldest_ts": None,
                    },
                )
                bucket["count"] += 1
                if entry.expires_at <= now:
                    bucket["expired_count"] += 1
                if (
                    bucket["_oldest_ts"] is None
                    or entry.expires_at < bucket["_oldest_ts"]
                ):
                    bucket["_oldest_ts"] = entry.expires_at
        out: list[dict] = []
        for route, bucket in per.items():
            oldest_ts = bucket["_oldest_ts"]
            out.append({
                "route": route,
                "count": bucket["count"],
                "expired_count": bucket["expired_count"],
                "oldest_expires_at": (
                    datetime.fromtimestamp(oldest_ts)
                    if oldest_ts is not None else None
                ),
            })
        return out


# ---------------------------------------------------------------------------
# Durable backend (SQL-backed; packet 019f)
# ---------------------------------------------------------------------------

class _DurableBackend:
    """Durable backend backed by ``pm.idempotency_keys``.

    Uses a caller-supplied ``session_factory`` (typically
    ``SessionLocal`` from ``config.py``) so each idempotency op runs in
    its own short-lived transaction, independent of the request session.
    This decouples idempotency-commit semantics from the domain-mutation
    transaction: a validation-failure 422 can delete the pre-registered
    row without disturbing the request session, and a concurrent replay
    can observe the committed idempotency row without waiting on the
    caller's long-running transaction.

    Concurrency coordination across multi-instance deployments falls out
    of the ``UNIQUE (route, idempotency_key)`` constraint + the
    ``INSERT ... ON CONFLICT DO NOTHING RETURNING`` pattern: only one
    writer wins the insert; every other writer observes the committed
    row via a follow-up ``SELECT``.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self._session_factory = session_factory
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Admin (test helpers)
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """DELETE FROM pm.idempotency_keys.  Intended for tests."""
        with self._session_factory() as db:
            db.execute(text("DELETE FROM pm.idempotency_keys"))
            db.commit()

    def set_ttl(self, seconds: int) -> None:
        with self._lock:
            self._ttl = seconds

    def _ttl_seconds(self) -> int:
        with self._lock:
            return self._ttl

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def register_request(
        self, route: str, key: str, body_bytes: bytes,
    ) -> Optional[IdempotencyHit]:
        body_hash = _hash_body(body_bytes)
        ttl = self._ttl_seconds()
        with self._session_factory() as db:
            # Opportunistic prune of expired rows — keeps table growth
            # bounded without a dedicated sweeper (see 019f follow-on
            # recommendations for the durable sweeper packet).
            db.execute(text(
                "DELETE FROM pm.idempotency_keys WHERE expires_at <= now()"
            ))

            result = db.execute(
                text("""
                    INSERT INTO pm.idempotency_keys
                        (route, idempotency_key, body_hash, expires_at)
                    VALUES
                        (:route, :key, :body_hash,
                         now() + make_interval(secs => :ttl))
                    ON CONFLICT (route, idempotency_key) DO NOTHING
                    RETURNING idempotency_key_id
                """),
                dict(route=route, key=key, body_hash=body_hash, ttl=ttl),
            )
            inserted = result.first()
            if inserted is not None:
                db.commit()
                return None

            # Conflict — another concurrent writer won the insert.
            # Fetch the committed row to compare body_hash and replay
            # the cached response if available.
            row = db.execute(
                text("""
                    SELECT body_hash, response_status, response_body
                      FROM pm.idempotency_keys
                     WHERE route = :route AND idempotency_key = :key
                """),
                dict(route=route, key=key),
            ).first()
            db.commit()

            if row is None:
                # Race window: row evicted between our INSERT attempt
                # and the SELECT.  Treat as first-sight — caller will
                # proceed and try to re-register on the next op.
                return None

            existing_hash, status, resp_bytes = row
            if existing_hash != body_hash:
                return IdempotencyHit(match=False)

            return IdempotencyHit(
                match=True,
                status=status,
                response_body=(
                    bytes(resp_bytes) if resp_bytes is not None else None
                ),
            )

    def record_response(
        self, route: str, key: str, body_bytes: bytes,
        status: int, response_body: bytes,
    ) -> None:
        body_hash = _hash_body(body_bytes)
        ttl = self._ttl_seconds()
        with self._session_factory() as db:
            db.execute(
                text("""
                    UPDATE pm.idempotency_keys
                       SET response_status = :status,
                           response_body   = :body,
                           expires_at      = now() + make_interval(secs => :ttl)
                     WHERE route = :route
                       AND idempotency_key = :key
                       AND body_hash = :body_hash
                """),
                dict(
                    route=route, key=key, body_hash=body_hash,
                    status=status, body=response_body, ttl=ttl,
                ),
            )
            db.commit()

    def discard_registration(
        self, route: str, key: str, body_bytes: bytes,
    ) -> None:
        """Delete a pre-registered row whose response was never recorded.

        Gated on ``response_status IS NULL`` so a row whose success
        response was already cached is NEVER deleted — the replay
        contract MUST survive concurrent validation-failure retries.

        Gated on matching ``body_hash`` so a validation-failure retry on
        one payload cannot evict a separately-registered row from a
        different in-flight payload.  (In practice these paths collide
        only under transient test interleaving; the guard is
        defence-in-depth.)
        """
        body_hash = _hash_body(body_bytes)
        with self._session_factory() as db:
            db.execute(
                text("""
                    DELETE FROM pm.idempotency_keys
                     WHERE route = :route
                       AND idempotency_key = :key
                       AND body_hash = :body_hash
                       AND response_status IS NULL
                """),
                dict(route=route, key=key, body_hash=body_hash),
            )
            db.commit()

    # ------------------------------------------------------------------
    # Packet 019g — explicit sweep + minimal ops stats
    # ------------------------------------------------------------------

    def sweep_expired(self) -> int:
        """Delete expired rows from ``pm.idempotency_keys``.

        Bounded SQL: ``DELETE ... WHERE expires_at <= now()``.  Returns
        the number of rows deleted.  No DDL changes; no touching of
        in-flight or replay-ready rows whose ``expires_at`` is still in
        the future.  Intended for scheduled / cron-driven invocation;
        also available through the minimal ops surface.
        """
        with self._session_factory() as db:
            result = db.execute(text(
                "DELETE FROM pm.idempotency_keys "
                "WHERE expires_at <= now()"
            ))
            deleted = result.rowcount or 0
            db.commit()
        return int(deleted)

    def stats(self) -> dict:
        """Return minimal observability payload against the durable store.

        Exactly ``{count, expired_count, oldest_expires_at}`` — the facade
        wraps this in ``{..., backend_kind}``.  No join, no route-
        partitioning, no write.  Single round-trip with two aggregates.
        """
        with self._session_factory() as db:
            row = db.execute(text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE expires_at <= now()) AS expired,
                    MIN(expires_at) AS oldest
                FROM pm.idempotency_keys
            """)).first()
        if row is None:
            return {
                "count": 0,
                "expired_count": 0,
                "oldest_expires_at": None,
            }
        total, expired, oldest = row
        return {
            "count": int(total or 0),
            "expired_count": int(expired or 0),
            "oldest_expires_at": oldest,
        }

    # ------------------------------------------------------------------
    # Packet 019i — per-route observability breakdown
    # ------------------------------------------------------------------

    def stats_by_route(self) -> list[dict]:
        """Per-route inventory against the durable store.

        Single aggregate ``GROUP BY route`` round-trip.  Returns one
        dict per route that currently has at least one row; the facade
        pads zero-rows for any of the seven ``PM_POST_ROUTES`` absent
        from this result.  No write; no DDL; no touching of the
        ``pm.idempotency_keys`` shape.
        """
        route_literals = ", ".join(
            f"'{route}'" for route in sorted(PM_POST_ROUTES)
        )
        with self._session_factory() as db:
            rows = db.execute(text(f"""
                SELECT
                    route,
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE expires_at <= now()) AS expired,
                    MIN(expires_at) AS oldest
                FROM pm.idempotency_keys
                WHERE route IN ({route_literals})
                GROUP BY route
                ORDER BY route
            """)).all()
        out: list[dict] = []
        for row in rows:
            route, total, expired, oldest = row
            out.append({
                "route": route,
                "count": int(total or 0),
                "expired_count": int(expired or 0),
                "oldest_expires_at": oldest,
            })
        return out


# ---------------------------------------------------------------------------
# Facade — pluggable backend
# ---------------------------------------------------------------------------

class IdempotencyCache:
    """Facade over a pluggable backend.

    Default backend is the process-local in-memory store so module
    import order is safe (the router imports this singleton before
    ``main.py`` has wired any DB).  Production wiring calls
    ``use_durable_backend(session_factory)`` at app init; tests that
    want the packet-019 in-memory behaviour call
    ``use_in_memory_backend()`` in their fixture setup.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._backend: _Backend = _InMemoryBackend(ttl_seconds)

    # ------------------------------------------------------------------
    # Backend selection
    # ------------------------------------------------------------------

    def use_durable_backend(
        self, session_factory: Callable[[], Session],
    ) -> None:
        """Swap to the SQL-backed durable backend."""
        self._backend = _DurableBackend(session_factory, self._ttl)

    def use_in_memory_backend(self) -> None:
        """Swap to the process-local in-memory backend.  For tests."""
        self._backend = _InMemoryBackend(self._ttl)

    def backend_kind(self) -> str:
        """Identify the currently-active backend — used by observability
        and by tests that want to pin the expected lane."""
        if isinstance(self._backend, _DurableBackend):
            return "durable"
        return "in_memory"

    # ------------------------------------------------------------------
    # Public API — forwarded to the active backend
    # ------------------------------------------------------------------

    def clear(self) -> None:
        self._backend.clear()

    def set_ttl(self, seconds: int) -> None:
        self._ttl = seconds
        self._backend.set_ttl(seconds)

    def register_request(
        self, route: str, key: str, body_bytes: bytes,
    ) -> Optional[IdempotencyHit]:
        return self._backend.register_request(route, key, body_bytes)

    def record_response(
        self, route: str, key: str, body_bytes: bytes,
        status: int, response_body: bytes,
    ) -> None:
        self._backend.record_response(
            route, key, body_bytes, status, response_body,
        )

    def discard_registration(
        self, route: str, key: str, body_bytes: bytes,
    ) -> None:
        self._backend.discard_registration(route, key, body_bytes)

    # ------------------------------------------------------------------
    # Packet 019g — explicit sweep + minimal ops stats
    # ------------------------------------------------------------------

    def sweep_expired(self) -> int:
        """Delegate explicit expiry sweep to the active backend.

        Returns the number of rows deleted.  Safe to call on either
        backend; under the in-memory backend this sweeps the dict, under
        the durable backend this issues ``DELETE ... WHERE expires_at
        <= now()`` against ``pm.idempotency_keys``.
        """
        return self._backend.sweep_expired()

    def stats(self) -> dict:
        """Return the minimal operator-facing stats payload.

        Always includes ``backend_kind`` so operators can tell which
        lane a given deployment is on.  The remaining keys come from
        the active backend: ``count`` (total rows), ``expired_count``
        (rows with ``expires_at <= now()``), and ``oldest_expires_at``
        (earliest ``expires_at`` across all rows, or ``None`` when
        the store is empty).
        """
        backend_stats = self._backend.stats()
        return {
            "count": backend_stats.get("count", 0),
            "expired_count": backend_stats.get("expired_count", 0),
            "oldest_expires_at": backend_stats.get("oldest_expires_at"),
            "backend_kind": self.backend_kind(),
        }

    def stats_by_route(self) -> dict:
        """Return the operator-facing per-route stats payload.

        The backend returns only populated rows; this facade pads the
        result so operators always receive exactly the seven pinned PM
        POST routes in deterministic order.
        """
        rows = {
            row["route"]: {
                "route": row["route"],
                "count": row.get("count", 0),
                "expired_count": row.get("expired_count", 0),
                "oldest_expires_at": row.get("oldest_expires_at"),
            }
            for row in self._backend.stats_by_route()
            if row.get("route") in PM_POST_ROUTES
        }
        padded = []
        for route in sorted(PM_POST_ROUTES):
            padded.append(rows.get(route, {
                "route": route,
                "count": 0,
                "expired_count": 0,
                "oldest_expires_at": None,
            }))
        return {
            "by_route": padded,
            "backend_kind": self.backend_kind(),
        }

    # ------------------------------------------------------------------
    # Packet 019i — per-route observability breakdown
    # ------------------------------------------------------------------

    def stats_by_route(self) -> dict:
        """Return per-route idempotency inventory bounded to the seven
        PM POST routes.

        Payload shape::

            {
              "by_route": [
                {"route", "count", "expired_count", "oldest_expires_at"},
                ... (exactly 7 rows, sorted by route)
              ],
              "backend_kind": "in_memory" | "durable",
            }

        The facade *reconciles* the backend's raw per-route rows against
        ``PM_POST_ROUTES`` so:

          * any of the seven pinned routes absent from the backend
            result is zero-padded (count=0, expired_count=0,
            oldest_expires_at=None), and
          * any backend row whose ``route`` is NOT in ``PM_POST_ROUTES``
            is dropped defensively — the durable-store CHECK constraint
            already prevents those, but this keeps the payload strictly
            bounded to the seven-route contract even under an unexpected
            store state (e.g. a legacy row from a dropped route).

        Rows are sorted by ``route`` (lexicographic) so consumers get a
        stable deterministic order regardless of backend or iteration.
        """
        raw = self._backend.stats_by_route()
        by_route_map: dict[str, dict] = {}
        for row in raw:
            route = row.get("route")
            if route not in PM_POST_ROUTES:
                # Defensive: drop any row that is not one of the seven
                # pinned PM POST routes.
                continue
            by_route_map[route] = {
                "route": route,
                "count": int(row.get("count", 0) or 0),
                "expired_count": int(row.get("expired_count", 0) or 0),
                "oldest_expires_at": row.get("oldest_expires_at"),
            }
        # Zero-pad the missing routes and sort deterministically.
        reconciled: list[dict] = []
        for route in sorted(PM_POST_ROUTES):
            if route in by_route_map:
                reconciled.append(by_route_map[route])
            else:
                reconciled.append({
                    "route": route,
                    "count": 0,
                    "expired_count": 0,
                    "oldest_expires_at": None,
                })
        return {
            "by_route": reconciled,
            "backend_kind": self.backend_kind(),
        }

    # ------------------------------------------------------------------
    # Packet-019 test-introspection compatibility
    # ------------------------------------------------------------------

    @property
    def _entries(self) -> dict:
        """Expose the in-memory backend's internal dict for packet-019
        tests that peek at cache size.  Only meaningful when the
        in-memory backend is active; returns an empty dict under the
        durable backend so the attribute never raises."""
        if isinstance(self._backend, _InMemoryBackend):
            return self._backend._entries
        return {}


# Module singleton — imported by the router and by tests that reset
# state between runs.  Starts on the in-memory backend; ``main.py``
# upgrades to durable at app init.
idempotency_cache: IdempotencyCache = IdempotencyCache()
