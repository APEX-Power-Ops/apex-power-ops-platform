-- =============================================================================
-- jobs domain — core tables: job (queue item) / run (ledger) / gate (approvals)
-- Requires 001. job subsumes the ops/agents/inbox frontmatter; run is the
-- run+promotion ledger (env = the sandbox|host trust evidence); gate holds the
-- human-approval records. Dev passwords/IaC stay in gitignored infra/.env.
-- =============================================================================

CREATE TABLE jobs.job (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    dispatch_id       text NOT NULL UNIQUE,
    title             text NOT NULL,
    target            jobs.executor_enum NOT NULL DEFAULT 'any',
    priority          int NOT NULL DEFAULT 100,
    predecessor_id    uuid REFERENCES jobs.job(id),
    authority         jobs.authority_enum NOT NULL DEFAULT 'gated',
    requires_approval boolean NOT NULL DEFAULT false,
    gate_categories   text[] NOT NULL DEFAULT '{}',
    env_required      jobs.env_enum NOT NULL DEFAULT 'any',
    payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
    closeout_path     text,
    status            jobs.job_status_enum NOT NULL DEFAULT 'pending',
    created_by        text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE jobs.run (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      uuid NOT NULL REFERENCES jobs.job(id) ON DELETE CASCADE,
    attempt     int NOT NULL,
    claimed_by  text NOT NULL,
    env         jobs.env_enum NOT NULL,
    status      jobs.run_status_enum NOT NULL DEFAULT 'running',
    claimed_at  timestamptz NOT NULL DEFAULT now(),
    started_at  timestamptz,
    finished_at timestamptz,
    exit_code   int,
    result      jsonb,
    log_ref     text,
    CONSTRAINT run_env_concrete CHECK (env IN ('sandbox', 'host')),
    UNIQUE (job_id, attempt)
);

CREATE TABLE jobs.gate (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id       uuid NOT NULL REFERENCES jobs.job(id) ON DELETE CASCADE,
    gate_type    text NOT NULL,
    state        jobs.gate_state_enum NOT NULL DEFAULT 'pending',
    requested_at timestamptz NOT NULL DEFAULT now(),
    decided_at   timestamptz,
    decided_by   text,
    note         text
);
