-- =============================================================================
-- jobs domain — schema + enum types  (Chip 3 / D-ARCH-3: the apex-jobs task bus)
-- Landing Lane: infra/database/migrations/jobs/
-- The DB-backed upgrade of ops/agents/inbox: a durable queue + run/promotion
-- ledger + env & human-approval gates. Applied to orchestration_dev (PG17).
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS jobs;

CREATE TYPE jobs.executor_enum   AS ENUM ('cc', 'codex', 'cowork', 'any');
CREATE TYPE jobs.authority_enum  AS ENUM ('gated', 'autonomous_safe');
CREATE TYPE jobs.env_enum        AS ENUM ('sandbox', 'host', 'any');
CREATE TYPE jobs.job_status_enum AS ENUM
    ('pending', 'claimed', 'running', 'blocked', 'awaiting_approval',
     'succeeded', 'failed', 'cancelled');
CREATE TYPE jobs.run_status_enum AS ENUM ('running', 'succeeded', 'failed', 'cancelled');
CREATE TYPE jobs.gate_state_enum AS ENUM ('pending', 'approved', 'rejected');
