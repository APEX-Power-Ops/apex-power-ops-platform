-- 20260710_000012_harden_mcp_public_exposure_core.sql
-- Schema-Placement Packet 01 / ACTION A1 (01b-core): close the anon Data-API surface on mcp_*.
-- APPLY: raw `psql -v ON_ERROR_STOP=1 -f <this file>` ONLY (one action per invocation). Do NOT route through the
--   Supabase CLI runner or MCP apply_migration (the embedded BEGIN/COMMIT must own the transaction).
-- Pure REVOKE (PUBLIC, anon); views stay SECURITY DEFINER; postgres/service_role/apex_tcc_runtime untouched.
-- Post-state: anon -> PostgREST 42501 (HTTP 401/403); authenticated UNCHANGED (see A2). Idempotent; re-run safe.
-- Rollback: 20260710_000012_harden_mcp_public_exposure_core.rollback.sql (operator-gated, run as postgres).
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
FROM PUBLIC, anon;

DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        EXECUTE 'REVOKE ALL ON public.mcp_external_action_audits FROM PUBLIC, anon';
    END IF;
END $$;

-- Assert: anon holds NO effective privilege (all verbs) on any hardened object.
DO $$
DECLARE
    obj  text;
    objs text[] := ARRAY[
        'public.mcp_job_runs','public.mcp_lane_priorities','public.mcp_local_action_queue',
        'public.mcp_review_decisions','public.mcp_task_packets','public.mcp_validation_artifacts',
        'public.mcp_job_run_summary_v','public.mcp_task_packet_summary_v'];
    bad  text[] := '{}';
    priv text;
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        objs := objs || 'public.mcp_external_action_audits'::text;
    END IF;
    FOREACH obj IN ARRAY objs LOOP
        FOREACH priv IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE'] LOOP
            IF has_table_privilege('anon', obj, priv) THEN bad := bad || (obj||':'||priv); END IF;
        END LOOP;
    END LOOP;
    IF array_length(bad,1) IS NOT NULL THEN
        RAISE EXCEPTION '01b-core FAILED: anon retains privilege on %', bad;
    END IF;
END $$;

-- Assert (narrow): the 2 named mcp summary views are in an expected security-mode state - still DEFINER (count=2)
-- or already flipped to invoker by the deferred 6b (count=0). A count of 1 = inconsistent partial-6b state, aborts.
-- Project-wide "no NEW definer view / no renewed anon reach" is the P2 advisor oracle's job, not in-txn.
DO $$
DECLARE definer_named int;
BEGIN
    SELECT count(*) INTO definer_named
    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind='v'
      AND c.relname IN ('mcp_job_run_summary_v','mcp_task_packet_summary_v')
      AND COALESCE((SELECT option_value FROM pg_options_to_table(c.reloptions)
                    WHERE option_name='security_invoker'),'false')::bool = false;
    IF definer_named NOT IN (0,2) THEN
        RAISE EXCEPTION '01b-core FAILED: named mcp summary views in inconsistent security-mode state (definer count=%)', definer_named;
    END IF;
END $$;

COMMIT;
