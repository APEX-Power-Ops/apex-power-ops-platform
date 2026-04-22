-- ============================================================================
-- Remote Control-Plane Bootstrap
-- ============================================================================
-- Purpose:
--   Create the first bounded control-plane tables and views required for the
--   remote packet / review / queue / job / artifact workflow.
--
-- Scope:
--   This migration intentionally excludes image-specific summary views because
--   the current backend baseline does not yet carry the image workflow tables.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'update_updated_at'
          AND pg_function_is_visible(oid)
    ) THEN
        EXECUTE $fn$
        CREATE FUNCTION public.update_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $body$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $body$;
        $fn$;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.mcp_task_packets (
    task_id              text PRIMARY KEY,
    title                text NOT NULL,
    lane                 text NOT NULL,
    primary_repo         text NOT NULL,
    status               text NOT NULL,
    action_type          text NOT NULL,
    risk_level           text NOT NULL,
    preferred_model_tier text,
    review_gate          text,
    briefing_path        text,
    packet_json          jsonb NOT NULL,
    claimed_by           text,
    created_at           timestamptz NOT NULL DEFAULT NOW(),
    updated_at           timestamptz NOT NULL DEFAULT NOW(),
    last_reviewed_at     timestamptz
);

CREATE INDEX IF NOT EXISTS idx_mcp_task_packets_lane_status
    ON public.mcp_task_packets (lane, status);

CREATE INDEX IF NOT EXISTS idx_mcp_task_packets_primary_repo
    ON public.mcp_task_packets (primary_repo);

DROP TRIGGER IF EXISTS mcp_task_packets_updated_at ON public.mcp_task_packets;
CREATE TRIGGER mcp_task_packets_updated_at
    BEFORE UPDATE ON public.mcp_task_packets
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();

CREATE TABLE IF NOT EXISTS public.mcp_review_decisions (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_type         text NOT NULL,
    subject_id           text NOT NULL,
    decision             text NOT NULL,
    reasoning_summary    text NOT NULL,
    required_next_action text,
    actor_id             text NOT NULL,
    source_tool          text NOT NULL,
    evidence_links       jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcp_review_decisions_subject
    ON public.mcp_review_decisions (subject_type, subject_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.mcp_local_action_queue (
    job_id          text PRIMARY KEY,
    action_type     text NOT NULL,
    status          text NOT NULL DEFAULT 'queued',
    priority        text NOT NULL DEFAULT 'normal',
    task_id         text,
    subject_type    text NOT NULL,
    subject_id      text NOT NULL,
    requested_by    text NOT NULL,
    request_payload jsonb NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT NOW(),
    claimed_at      timestamptz,
    claimed_by      text,
    completed_at    timestamptz,
    CONSTRAINT mcp_local_action_queue_status_ck
        CHECK (status IN ('queued', 'claimed', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT mcp_local_action_queue_priority_ck
        CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX IF NOT EXISTS idx_mcp_local_action_queue_status_created
    ON public.mcp_local_action_queue (status, created_at);

CREATE INDEX IF NOT EXISTS idx_mcp_local_action_queue_subject
    ON public.mcp_local_action_queue (subject_type, subject_id);

CREATE TABLE IF NOT EXISTS public.mcp_job_runs (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id             text NOT NULL REFERENCES public.mcp_local_action_queue(job_id) ON DELETE CASCADE,
    status             text NOT NULL,
    result_summary     text,
    result_json        jsonb,
    evidence_artifacts jsonb NOT NULL DEFAULT '[]'::jsonb,
    runner_id          text,
    started_at         timestamptz,
    completed_at       timestamptz
);

CREATE INDEX IF NOT EXISTS idx_mcp_job_runs_job_status
    ON public.mcp_job_runs (job_id, status);

CREATE TABLE IF NOT EXISTS public.mcp_validation_artifacts (
    artifact_id    text PRIMARY KEY,
    artifact_type  text NOT NULL,
    subject_type   text NOT NULL,
    subject_id     text NOT NULL,
    title          text NOT NULL,
    summary        text,
    artifact_path  text,
    artifact_uri   text,
    artifact_json  jsonb,
    created_by     text,
    created_at     timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mcp_validation_artifacts_subject
    ON public.mcp_validation_artifacts (subject_type, subject_id, created_at DESC);

CREATE TABLE IF NOT EXISTS public.mcp_lane_priorities (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lane           text NOT NULL,
    priority_rank  integer NOT NULL,
    item_id        text NOT NULL,
    title          text NOT NULL,
    status         text NOT NULL,
    source_surface text NOT NULL,
    notes          text,
    updated_at     timestamptz NOT NULL DEFAULT NOW(),
    UNIQUE (lane, priority_rank, item_id)
);

CREATE INDEX IF NOT EXISTS idx_mcp_lane_priorities_lane_rank
    ON public.mcp_lane_priorities (lane, priority_rank);

DROP TRIGGER IF EXISTS mcp_lane_priorities_updated_at ON public.mcp_lane_priorities;
CREATE TRIGGER mcp_lane_priorities_updated_at
    BEFORE UPDATE ON public.mcp_lane_priorities
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE VIEW public.mcp_task_packet_summary_v AS
SELECT
    task_id,
    title,
    lane,
    status,
    risk_level,
    preferred_model_tier,
    review_gate,
    updated_at
FROM public.mcp_task_packets;

CREATE OR REPLACE VIEW public.mcp_job_run_summary_v AS
SELECT
    q.job_id,
    q.action_type,
    q.status,
    q.subject_type,
    q.subject_id,
    q.created_at,
    q.completed_at,
    r.result_summary
FROM public.mcp_local_action_queue q
LEFT JOIN LATERAL (
    SELECT result_summary
    FROM public.mcp_job_runs r
    WHERE r.job_id = q.job_id
    ORDER BY COALESCE(r.completed_at, r.started_at) DESC NULLS LAST
    LIMIT 1
) r ON TRUE;

COMMENT ON TABLE public.mcp_task_packets IS
    'Remote control-plane packet mirror for bounded task routing and status updates.';

COMMENT ON TABLE public.mcp_review_decisions IS
    'Append-only authority decisions emitted through the control-plane surface.';

COMMENT ON TABLE public.mcp_local_action_queue IS
    'Queue of privileged local actions requested indirectly through the remote control plane.';

COMMENT ON TABLE public.mcp_job_runs IS
    'Execution results for local action queue items.';

COMMENT ON TABLE public.mcp_validation_artifacts IS
    'Durable evidence records retrievable by remote control-plane clients.';

COMMENT ON TABLE public.mcp_lane_priorities IS
    'Normalized lane-priority read model for remote queue review.';