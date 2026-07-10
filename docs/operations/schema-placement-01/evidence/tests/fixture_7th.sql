-- fixture.sql -- faithful mini-prod of the mcp_* Data-API surface on a BLANK database.
-- Mirrors prod pre-state that Actions A1/A2/A3 harden. Run as postgres (grantor fidelity).
-- Value-silent: throwaway dev DB, no secrets.
BEGIN;

-- ---------------------------------------------------------------------------
-- Roles (cluster-global; guarded so re-use across disposable DBs is safe).
-- ---------------------------------------------------------------------------
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN
        CREATE ROLE service_role NOLOGIN BYPASSRLS;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='apex_tcc_runtime') THEN
        CREATE ROLE apex_tcc_runtime LOGIN;
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Stub `auth` schema (Supabase-shaped) so RLS policy predicates compile.
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS auth;

CREATE OR REPLACE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$ SELECT current_setting('request.jwt.claim.role', true) $$;

CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$ SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;

-- ---------------------------------------------------------------------------
-- 6 mcp_* tables.
-- ---------------------------------------------------------------------------
CREATE TABLE public.mcp_local_action_queue (
    job_id       text PRIMARY KEY,
    requested_by text
);
CREATE TABLE public.mcp_job_runs (
    id     bigserial PRIMARY KEY,
    job_id text REFERENCES public.mcp_local_action_queue(job_id)
);
CREATE TABLE public.mcp_review_decisions (
    id       bigserial PRIMARY KEY,
    actor_id text
);
CREATE TABLE public.mcp_task_packets (
    id bigserial PRIMARY KEY
);
CREATE TABLE public.mcp_validation_artifacts (
    id bigserial PRIMARY KEY
);
CREATE TABLE public.mcp_lane_priorities (
    id bigserial PRIMARY KEY
);

-- ---------------------------------------------------------------------------
-- RLS ON for all 6.
-- ---------------------------------------------------------------------------
ALTER TABLE public.mcp_local_action_queue  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_job_runs            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_review_decisions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_task_packets        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_validation_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_lane_priorities     ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 14 policies (verbatim). 8 authenticated-facing + 6 *_service_all.
-- ---------------------------------------------------------------------------
CREATE POLICY mcp_task_packets_auth_read ON public.mcp_task_packets FOR SELECT USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_task_packets_service_all ON public.mcp_task_packets FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY mcp_review_decisions_auth_read ON public.mcp_review_decisions FOR SELECT USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_review_decisions_auth_insert_self ON public.mcp_review_decisions FOR INSERT WITH CHECK (auth.role() = 'service_role' OR actor_id = auth.uid()::text);
CREATE POLICY mcp_review_decisions_service_all ON public.mcp_review_decisions FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY mcp_local_action_queue_auth_read_own ON public.mcp_local_action_queue FOR SELECT USING (auth.role() = 'service_role' OR requested_by = auth.uid()::text);
CREATE POLICY mcp_local_action_queue_auth_insert_own ON public.mcp_local_action_queue FOR INSERT WITH CHECK (auth.role() = 'service_role' OR requested_by = auth.uid()::text);
CREATE POLICY mcp_local_action_queue_service_all ON public.mcp_local_action_queue FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY mcp_job_runs_auth_read_requested ON public.mcp_job_runs FOR SELECT USING (auth.role() = 'service_role' OR EXISTS (SELECT 1 FROM public.mcp_local_action_queue q WHERE q.job_id = mcp_job_runs.job_id AND q.requested_by = auth.uid()::text));
CREATE POLICY mcp_job_runs_service_all ON public.mcp_job_runs FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY mcp_validation_artifacts_auth_read ON public.mcp_validation_artifacts FOR SELECT USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_validation_artifacts_service_all ON public.mcp_validation_artifacts FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY mcp_lane_priorities_auth_read ON public.mcp_lane_priorities FOR SELECT USING (auth.role() IN ('authenticated','service_role'));
CREATE POLICY mcp_lane_priorities_service_all ON public.mcp_lane_priorities FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- ---------------------------------------------------------------------------
-- 2 SECURITY DEFINER views (plain CREATE VIEW = definer by default).
-- ---------------------------------------------------------------------------
CREATE VIEW public.mcp_job_run_summary_v AS SELECT jr.id, jr.job_id FROM public.mcp_job_runs jr JOIN public.mcp_local_action_queue q ON q.job_id = jr.job_id;
CREATE VIEW public.mcp_task_packet_summary_v AS SELECT id FROM public.mcp_task_packets;

-- ---------------------------------------------------------------------------
-- Grants matching prod.
-- ---------------------------------------------------------------------------
GRANT ALL ON
    public.mcp_job_runs,
    public.mcp_lane_priorities,
    public.mcp_local_action_queue,
    public.mcp_review_decisions,
    public.mcp_task_packets,
    public.mcp_validation_artifacts,
    public.mcp_job_run_summary_v,
    public.mcp_task_packet_summary_v
TO anon, authenticated, service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.mcp_job_runs,
    public.mcp_lane_priorities,
    public.mcp_local_action_queue,
    public.mcp_review_decisions,
    public.mcp_task_packets,
    public.mcp_validation_artifacts,
    public.mcp_job_run_summary_v,
    public.mcp_task_packet_summary_v
TO apex_tcc_runtime;

-- ---------------------------------------------------------------------------
-- 6 ORIGINAL comments (verbatim; A2 rewrites these to RETIRED, rollback restores).
-- ---------------------------------------------------------------------------
COMMENT ON TABLE public.mcp_task_packets IS 'Remote control-plane packet mirror with RLS-enabled authenticated read and service-role write access.';
COMMENT ON TABLE public.mcp_review_decisions IS 'Append-only authority decisions with authenticated self-write and service-role full access.';
COMMENT ON TABLE public.mcp_local_action_queue IS 'Privileged local action queue with authenticated self-scoped request visibility and service-role execution access.';
COMMENT ON TABLE public.mcp_job_runs IS 'Execution results for local action queue items, readable by request owner or service role.';
COMMENT ON TABLE public.mcp_validation_artifacts IS 'Durable control-plane evidence records with authenticated read access and service-role write access.';
COMMENT ON TABLE public.mcp_lane_priorities IS 'Normalized lane-priority read model with authenticated read access and service-role maintenance access.';

-- ---------------------------------------------------------------------------
-- 2 scratch tables (RLS OFF) that A3 relocates into schema `archive`.
-- ---------------------------------------------------------------------------
CREATE TABLE public._009_rollback_snapshot (id bigserial PRIMARY KEY);
CREATE TABLE public._phase3_load_manifest (id bigserial PRIMARY KEY);
GRANT ALL ON public._009_rollback_snapshot, public._phase3_load_manifest TO anon, authenticated;

COMMIT;

-- ===========================================================================
-- fixture_7th.sql extension: the guarded 7th table mcp_external_action_audits.
-- Mirrors 000009 leaving it BORN-EXPOSED (anon+authenticated hold ALL). A1/A2's
-- guarded to_regclass branches harden it; the rollbacks restore it.
-- (This file = the full contents of fixture.sql above PLUS this block, so CASE 2
--  loads ONLY this file to obtain the 7-table mini-prod without duplicate DDL.)
-- ===========================================================================
BEGIN;

CREATE TABLE public.mcp_external_action_audits (audit_id text PRIMARY KEY);
ALTER TABLE public.mcp_external_action_audits ENABLE ROW LEVEL SECURITY;
CREATE POLICY mcp_external_action_audits_service_all ON public.mcp_external_action_audits FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
GRANT ALL ON public.mcp_external_action_audits TO anon, authenticated;

COMMIT;
