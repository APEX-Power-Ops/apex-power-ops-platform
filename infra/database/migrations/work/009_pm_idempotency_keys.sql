-- =============================================================================
-- PM Runtime — Durable Idempotency Store
-- Packet: 2026-04-16-pm-schema-019f
-- Authority: 2026-04-16-pm-schema-019 (process-local cache), §6 follow-on 019f
--
-- Adds the minimum shared-infra table needed to back the existing PM POST
-- idempotency seam for the seven PM write endpoints (projects,
-- work_packages, tasks, assignments, dependencies, execution_issues,
-- progress_snapshots).  Scope invariants preserved by this migration:
--
--   * New schema `pm` is introduced specifically for PM runtime shared
--     infra (idempotency now, possibly audit/outbox later).  The `work`
--     schema is NOT touched — its registry size remains 22.
--   * No changes to any work.* table, view, enum, function, or trigger.
--   * No cross-schema FK from `pm.*` to `work.*`: idempotency rows are
--     intentionally decoupled from domain rows so a rolled-back domain
--     transaction doesn't orphan an idempotency key and vice-versa.
--   * Route scoping (Stripe-style per-endpoint semantics) is enforced by
--     the UNIQUE (route, idempotency_key) constraint.
--   * Only success responses populate response_status + response_body.
--     The runtime (services/work/idempotency.py) is responsible for
--     deleting pre-registered rows on validation-failure 422 so callers
--     can retry the same key with a corrected payload.
--
-- Deferred (packet 019f does NOT author these):
--   * Background sweeper job for expired entries — the runtime prunes
--     expired rows opportunistically at register_request time.
--   * Cross-instance lock contention handling — we rely on the UNIQUE
--     constraint + ON CONFLICT DO NOTHING for coordination.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS pm;

-- ---------------------------------------------------------------------------
-- pm.idempotency_keys
-- ---------------------------------------------------------------------------
--
-- Durable backing store for the ``Idempotency-Key`` header contract first
-- introduced in packet 019 as a process-local cache.  One row per
-- (route, idempotency_key) pair; route is the logical POST path
-- ("/projects", "/work-packages", "/tasks", "/assignments",
--  "/dependencies", "/execution-issues", "/progress-snapshots").

CREATE TABLE IF NOT EXISTS pm.idempotency_keys (
    idempotency_key_id   uuid         NOT NULL DEFAULT gen_random_uuid(),
    route                text         NOT NULL,
    idempotency_key      text         NOT NULL,
    body_hash            text         NOT NULL,
    response_status      integer      NULL,
    response_body        bytea        NULL,
    created_at           timestamptz  NOT NULL DEFAULT now(),
    expires_at           timestamptz  NOT NULL,

    CONSTRAINT pk_pm_idempotency_keys
        PRIMARY KEY (idempotency_key_id),

    CONSTRAINT uq_pm_idempotency_keys_route_key
        UNIQUE (route, idempotency_key),

    -- Response status is only populated for successful responses
    -- (2xx).  422 validation failures MUST NOT be persisted; the runtime
    -- achieves that by deleting the pre-registered row on validation
    -- failure, so by construction any row whose response_status IS NOT
    -- NULL carries a successful replay body.  This CHECK pins that
    -- invariant at the DDL level as defence-in-depth.
    CONSTRAINT chk_pm_idempotency_keys_response_status
        CHECK (
            response_status IS NULL
            OR (response_status >= 200 AND response_status < 300)
        ),

    -- response_status and response_body are either both NULL (pre-record
    -- / in-flight) or both populated (replay-ready).
    CONSTRAINT chk_pm_idempotency_keys_response_paired
        CHECK (
            (response_status IS NULL AND response_body IS NULL)
            OR (response_status IS NOT NULL AND response_body IS NOT NULL)
        ),

    -- Route scoping pins the seven PM POST routes explicitly.  Any
    -- future expansion of the idempotency seam to additional routes
    -- MUST ship alongside a schema evolution of this CHECK — which
    -- forces an explicit packet boundary rather than silent scope creep.
    CONSTRAINT chk_pm_idempotency_keys_route
        CHECK (route IN (
            '/projects',
            '/work-packages',
            '/tasks',
            '/assignments',
            '/dependencies',
            '/execution-issues',
            '/progress-snapshots'
        ))
);

-- Sweep index: a background sweeper (out-of-scope for 019f) or the
-- runtime's opportunistic pruning at register_request time uses
-- expires_at <= now() to evict TTL-expired rows.  The partial index
-- keeps the hot path small.
CREATE INDEX IF NOT EXISTS idx_pm_idempotency_keys_expires_at
    ON pm.idempotency_keys (expires_at);

-- Replay-path index: register_request's SELECT on conflict hits
-- (route, idempotency_key) which is already backed by the UNIQUE
-- constraint; no additional index needed for the lookup path.

COMMENT ON TABLE  pm.idempotency_keys IS
    'Durable backing store for the PM POST Idempotency-Key seam '
    '(packet 019f). One row per (route, idempotency_key) pair.';
COMMENT ON COLUMN pm.idempotency_keys.route IS
    'Logical POST route, e.g. "/projects". Route-scoped so the same '
    'idempotency_key can be reused across different POST endpoints.';
COMMENT ON COLUMN pm.idempotency_keys.idempotency_key IS
    'Value of the incoming Idempotency-Key HTTP header.';
COMMENT ON COLUMN pm.idempotency_keys.body_hash IS
    'Hex SHA-256 of the canonical-JSON form of the request body. '
    'Logically-equivalent payloads with reordered keys hash identically.';
COMMENT ON COLUMN pm.idempotency_keys.response_status IS
    'HTTP status of the originally-served response. NULL while the '
    'original request is in-flight or failed before recording.';
COMMENT ON COLUMN pm.idempotency_keys.response_body IS
    'Raw bytes of the originally-served response body. Replayed '
    'verbatim on subsequent requests with the matching key+body_hash.';
COMMENT ON COLUMN pm.idempotency_keys.expires_at IS
    'Wall-clock expiry. Rows past this time are eligible for eviction '
    'by the runtime or a future sweep job.';
