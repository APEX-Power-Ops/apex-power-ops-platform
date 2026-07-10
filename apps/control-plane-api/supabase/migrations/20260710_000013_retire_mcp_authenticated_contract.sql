-- 20260710_000013_retire_mcp_authenticated_contract.sql
-- Schema-Placement Packet 01 / ACTION A2 (01b-auth): RETIRE the authenticated Data-API contract (operator-declared).
-- APPLY: raw `psql -v ON_ERROR_STOP=1 -f <this file>` ONLY, one action per invocation, in the SAME window as A1.
-- REVOKE authenticated + DROP the 8 authenticated policies + record retirement in the 6 table comments, atomically.
-- service_role_all policies + RLS stay ON. Post-state: authenticated -> 42501. Idempotent; re-run safe.
-- Rollback: 20260710_000013_retire_mcp_authenticated_contract.rollback.sql (operator-gated, run as postgres).
BEGIN;

REVOKE ALL ON
    public.mcp_job_runs,
    public.mcp_lane_priorities,
    public.mcp_local_action_queue,
    public.mcp_review_decisions,
    public.mcp_task_packets,
    public.mcp_validation_artifacts,
    public.mcp_job_run_summary_v,
    public.mcp_task_packet_summary_v
FROM authenticated;

DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        EXECUTE 'REVOKE ALL ON public.mcp_external_action_audits FROM authenticated';
    END IF;
END $$;

DROP POLICY IF EXISTS mcp_task_packets_auth_read              ON public.mcp_task_packets;
DROP POLICY IF EXISTS mcp_review_decisions_auth_read          ON public.mcp_review_decisions;
DROP POLICY IF EXISTS mcp_review_decisions_auth_insert_self   ON public.mcp_review_decisions;
DROP POLICY IF EXISTS mcp_local_action_queue_auth_read_own    ON public.mcp_local_action_queue;
DROP POLICY IF EXISTS mcp_local_action_queue_auth_insert_own  ON public.mcp_local_action_queue;
DROP POLICY IF EXISTS mcp_job_runs_auth_read_requested        ON public.mcp_job_runs;
DROP POLICY IF EXISTS mcp_validation_artifacts_auth_read      ON public.mcp_validation_artifacts;
DROP POLICY IF EXISTS mcp_lane_priorities_auth_read           ON public.mcp_lane_priorities;

COMMENT ON TABLE public.mcp_job_runs            IS 'Control-plane job runs. Authenticated Data-API read contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';
COMMENT ON TABLE public.mcp_lane_priorities     IS 'Control-plane lane priorities. Authenticated Data-API read contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';
COMMENT ON TABLE public.mcp_local_action_queue  IS 'Control-plane local action queue. Authenticated Data-API self-scoped read/insert contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';
COMMENT ON TABLE public.mcp_review_decisions    IS 'Control-plane review decisions. Authenticated Data-API read + self-insert contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';
COMMENT ON TABLE public.mcp_task_packets        IS 'Control-plane task packets. Authenticated Data-API read contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';
COMMENT ON TABLE public.mcp_validation_artifacts IS 'Control-plane validation artifacts. Authenticated Data-API read contract RETIRED 2026-07-10 (schema-placement 01b-auth); privileged/service_role connection only. RLS + service_role-all retained.';

-- Assert: authenticated holds NO effective privilege (all verbs, incl guarded 7th) AND none of the 8 policies remain.
DO $$
DECLARE
    obj  text;
    objs text[] := ARRAY[
        'public.mcp_job_runs','public.mcp_lane_priorities','public.mcp_local_action_queue',
        'public.mcp_review_decisions','public.mcp_task_packets','public.mcp_validation_artifacts',
        'public.mcp_job_run_summary_v','public.mcp_task_packet_summary_v'];
    bad  text[] := '{}';
    priv text;
    pol_cnt int;
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        objs := objs || 'public.mcp_external_action_audits'::text;
    END IF;
    FOREACH obj IN ARRAY objs LOOP
        FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE'] LOOP
            IF has_table_privilege('authenticated', obj, priv) THEN bad := bad || (obj||':'||priv); END IF;
        END LOOP;
    END LOOP;
    SELECT count(*) INTO pol_cnt
    FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND p.polname IN (
        'mcp_task_packets_auth_read','mcp_review_decisions_auth_read','mcp_review_decisions_auth_insert_self',
        'mcp_local_action_queue_auth_read_own','mcp_local_action_queue_auth_insert_own',
        'mcp_job_runs_auth_read_requested','mcp_validation_artifacts_auth_read','mcp_lane_priorities_auth_read');
    IF array_length(bad,1) IS NOT NULL THEN
        RAISE EXCEPTION '01b-auth FAILED: authenticated retains privilege on %', bad;
    END IF;
    IF pol_cnt <> 0 THEN
        RAISE EXCEPTION '01b-auth FAILED: % retired authenticated policies still present', pol_cnt;
    END IF;
END $$;

COMMIT;
