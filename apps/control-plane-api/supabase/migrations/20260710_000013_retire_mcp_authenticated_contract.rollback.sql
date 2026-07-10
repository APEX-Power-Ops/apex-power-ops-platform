-- ROLLBACK for A2 (01b-auth). OPERATOR-GATED. Run as postgres (grantor fidelity). Never auto-runs.
-- Restores authenticated grants (ALL / arwdDxtm) on the 6 tables + 2 views A2 revoked, recreates the 8
-- authenticated policies verbatim (from 000008), and restores the 6 original table comments. The 6
-- *_service_all policies were never dropped.
-- SCOPE (F3): restores ONLY objects A2 revoked on the verified prod shape. mcp_external_action_audits is
-- ABSENT on prod (A2's guarded 7th-table revoke is a no-op there). This rollback deliberately does NOT
-- re-grant the 7th table -- a blanket "exists at rollback time" re-grant could re-open exposure on a
-- substrate where 000009 landed after apply. Regenerate from captured pre-ACL if applied where it exists.
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

-- 7th table: FAIL-CLOSED (review F3). Same reasoning as A1's rollback -- forward A2 only revokes the 7th table
-- if it EXISTS AT APPLY, so a re-GRANT keyed on existence AT ROLLBACK could add authenticated=ALL on a table born
-- later (000009) that the pre-state never exposed. Leave it hardened; restore from the captured pre-state ACL
-- snapshot only if it was authenticated-exposed before this packet applied.
DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        RAISE NOTICE 'A2 rollback: mcp_external_action_audits left HARDENED (fail-closed, review F3). Restore its pre-apply authenticated ACL from the captured snapshot ONLY if it was exposed before this packet applied.';
    END IF;
END $$;

COMMIT;
