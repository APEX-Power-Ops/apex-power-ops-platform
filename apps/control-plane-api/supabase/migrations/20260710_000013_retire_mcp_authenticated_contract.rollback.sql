-- ROLLBACK for A2 (01b-auth). OPERATOR-GATED. Run as postgres (grantor fidelity). Never auto-runs.
-- Restores authenticated grants (ALL / arwdDxtm), recreates the 8 authenticated policies verbatim (from 000008),
-- and restores the 6 original table comments. The 6 *_service_all policies were never dropped.
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
TO authenticated;

DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        EXECUTE 'GRANT ALL ON public.mcp_external_action_audits TO authenticated';
    END IF;
END $$;

CREATE POLICY mcp_task_packets_auth_read ON public.mcp_task_packets FOR SELECT
    USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_review_decisions_auth_read ON public.mcp_review_decisions FOR SELECT
    USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_review_decisions_auth_insert_self ON public.mcp_review_decisions FOR INSERT
    WITH CHECK (auth.role() = 'service_role' OR actor_id = auth.uid()::text);
CREATE POLICY mcp_local_action_queue_auth_read_own ON public.mcp_local_action_queue FOR SELECT
    USING (auth.role() = 'service_role' OR requested_by = auth.uid()::text);
CREATE POLICY mcp_local_action_queue_auth_insert_own ON public.mcp_local_action_queue FOR INSERT
    WITH CHECK (auth.role() = 'service_role' OR requested_by = auth.uid()::text);
CREATE POLICY mcp_job_runs_auth_read_requested ON public.mcp_job_runs FOR SELECT
    USING (auth.role() = 'service_role' OR EXISTS (SELECT 1 FROM public.mcp_local_action_queue q
           WHERE q.job_id = mcp_job_runs.job_id AND q.requested_by = auth.uid()::text));
CREATE POLICY mcp_validation_artifacts_auth_read ON public.mcp_validation_artifacts FOR SELECT
    USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_lane_priorities_auth_read ON public.mcp_lane_priorities FOR SELECT
    USING (auth.role() IN ('authenticated','service_role'));

COMMENT ON TABLE public.mcp_task_packets IS 'Remote control-plane packet mirror with RLS-enabled authenticated read and service-role write access.';
COMMENT ON TABLE public.mcp_review_decisions IS 'Append-only authority decisions with authenticated self-write and service-role full access.';
COMMENT ON TABLE public.mcp_local_action_queue IS 'Privileged local action queue with authenticated self-scoped request visibility and service-role execution access.';
COMMENT ON TABLE public.mcp_job_runs IS 'Execution results for local action queue items, readable by request owner or service role.';
COMMENT ON TABLE public.mcp_validation_artifacts IS 'Durable control-plane evidence records with authenticated read access and service-role write access.';
COMMENT ON TABLE public.mcp_lane_priorities IS 'Normalized lane-priority read model with authenticated read access and service-role maintenance access.';

COMMIT;
