-- ============================================================================
-- Control-Plane RLS Bootstrap
-- ============================================================================
-- Purpose:
--   Enable row-level security for the remote control-plane tables and align
--   policy shape with the existing Supabase auth pattern used by the runtime
--   test-plan surfaces.
--
-- Policy posture:
--   - service_role keeps full access for backend and operator workflows
--   - authenticated users may read shared packet / priority / artifact surfaces
--   - authenticated users may create review decisions only as themselves
--   - authenticated users may create and view only their own queued jobs
--   - job-run rows are readable only when tied to a queued job they requested
-- ============================================================================

ALTER TABLE public.mcp_task_packets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_review_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_local_action_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_job_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_validation_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_lane_priorities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS mcp_task_packets_auth_read ON public.mcp_task_packets;
DROP POLICY IF EXISTS mcp_task_packets_service_all ON public.mcp_task_packets;
CREATE POLICY mcp_task_packets_auth_read
    ON public.mcp_task_packets
    FOR SELECT
    USING (auth.role() IN ('authenticated', 'service_role'));
CREATE POLICY mcp_task_packets_service_all
    ON public.mcp_task_packets
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS mcp_review_decisions_auth_read ON public.mcp_review_decisions;
DROP POLICY IF EXISTS mcp_review_decisions_auth_insert_self ON public.mcp_review_decisions;
DROP POLICY IF EXISTS mcp_review_decisions_service_all ON public.mcp_review_decisions;
CREATE POLICY mcp_review_decisions_auth_read
    ON public.mcp_review_decisions
    FOR SELECT
    USING (auth.role() IN ('authenticated', 'service_role'));
CREATE POLICY mcp_review_decisions_auth_insert_self
    ON public.mcp_review_decisions
    FOR INSERT
    WITH CHECK (
        auth.role() = 'service_role'
        OR actor_id = auth.uid()::text
    );
CREATE POLICY mcp_review_decisions_service_all
    ON public.mcp_review_decisions
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS mcp_local_action_queue_auth_read_own ON public.mcp_local_action_queue;
DROP POLICY IF EXISTS mcp_local_action_queue_auth_insert_own ON public.mcp_local_action_queue;
DROP POLICY IF EXISTS mcp_local_action_queue_service_all ON public.mcp_local_action_queue;
CREATE POLICY mcp_local_action_queue_auth_read_own
    ON public.mcp_local_action_queue
    FOR SELECT
    USING (
        auth.role() = 'service_role'
        OR requested_by = auth.uid()::text
    );
CREATE POLICY mcp_local_action_queue_auth_insert_own
    ON public.mcp_local_action_queue
    FOR INSERT
    WITH CHECK (
        auth.role() = 'service_role'
        OR requested_by = auth.uid()::text
    );
CREATE POLICY mcp_local_action_queue_service_all
    ON public.mcp_local_action_queue
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS mcp_job_runs_auth_read_requested ON public.mcp_job_runs;
DROP POLICY IF EXISTS mcp_job_runs_service_all ON public.mcp_job_runs;
CREATE POLICY mcp_job_runs_auth_read_requested
    ON public.mcp_job_runs
    FOR SELECT
    USING (
        auth.role() = 'service_role'
        OR EXISTS (
            SELECT 1
            FROM public.mcp_local_action_queue q
            WHERE q.job_id = mcp_job_runs.job_id
              AND q.requested_by = auth.uid()::text
        )
    );
CREATE POLICY mcp_job_runs_service_all
    ON public.mcp_job_runs
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS mcp_validation_artifacts_auth_read ON public.mcp_validation_artifacts;
DROP POLICY IF EXISTS mcp_validation_artifacts_service_all ON public.mcp_validation_artifacts;
CREATE POLICY mcp_validation_artifacts_auth_read
    ON public.mcp_validation_artifacts
    FOR SELECT
    USING (auth.role() IN ('authenticated', 'service_role'));
CREATE POLICY mcp_validation_artifacts_service_all
    ON public.mcp_validation_artifacts
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS mcp_lane_priorities_auth_read ON public.mcp_lane_priorities;
DROP POLICY IF EXISTS mcp_lane_priorities_service_all ON public.mcp_lane_priorities;
CREATE POLICY mcp_lane_priorities_auth_read
    ON public.mcp_lane_priorities
    FOR SELECT
    USING (auth.role() IN ('authenticated', 'service_role'));
CREATE POLICY mcp_lane_priorities_service_all
    ON public.mcp_lane_priorities
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

COMMENT ON TABLE public.mcp_task_packets IS
    'Remote control-plane packet mirror with RLS-enabled authenticated read and service-role write access.';

COMMENT ON TABLE public.mcp_review_decisions IS
    'Append-only authority decisions with authenticated self-write and service-role full access.';

COMMENT ON TABLE public.mcp_local_action_queue IS
    'Privileged local action queue with authenticated self-scoped request visibility and service-role execution access.';

COMMENT ON TABLE public.mcp_job_runs IS
    'Execution results for local action queue items, readable by request owner or service role.';

COMMENT ON TABLE public.mcp_validation_artifacts IS
    'Durable control-plane evidence records with authenticated read access and service-role write access.';

COMMENT ON TABLE public.mcp_lane_priorities IS
    'Normalized lane-priority read model with authenticated read access and service-role maintenance access.';