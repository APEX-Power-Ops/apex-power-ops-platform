-- ROLLBACK for A1 (01b-core). OPERATOR-GATED. Run as postgres (grantor fidelity). Never auto-runs.
-- Restores the pre-state anon grants (anon = ALL / arwdDxtm). PUBLIC had no direct grant, so none restored.
BEGIN;
DO $$ BEGIN IF current_user <> 'postgres' THEN RAISE EXCEPTION 'run rollback as postgres (grantor fidelity)'; END IF; END $$;

GRANT ALL ON
    public.mcp_job_runs,
    public.mcp_lane_priorities,
    public.mcp_local_action_queue,
    public.mcp_review_decisions,
    public.mcp_task_packets,
    public.mcp_validation_artifacts,
    public.mcp_job_run_summary_v,
    public.mcp_task_packet_summary_v
TO anon;

DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        EXECUTE 'GRANT ALL ON public.mcp_external_action_audits TO anon';
    END IF;
END $$;

COMMIT;
