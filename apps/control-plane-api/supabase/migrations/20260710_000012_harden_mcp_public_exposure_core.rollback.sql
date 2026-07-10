-- ROLLBACK for A1 (01b-core). OPERATOR-GATED. Run as postgres (grantor fidelity). Never auto-runs.
-- Restores the pre-state anon grants (anon = ALL / arwdDxtm) on the 6 tables + 2 views the forward
-- migration revoked. PUBLIC had no direct grant, so none restored.
-- SCOPE (F3): this rollback restores ONLY the objects A1 actually revoked on the verified prod shape
-- (mcp_external_action_audits is ABSENT on prod, so A1's guarded 7th-table revoke is a no-op there and
-- has nothing to restore). It deliberately does NOT re-grant the 7th table: a blanket re-grant keyed on
-- "table exists at rollback time" could re-open exposure on a substrate where 000009 landed AFTER apply
-- (the born-exposed 7th is a bug, not a state worth faithfully restoring). If a future environment
-- applies A1 while the 7th table exists, regenerate that environment's rollback from its captured pre-ACL.
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

-- 7th table: FAIL-CLOSED (review F3). Forward A1 only revokes the 7th table if it EXISTS AT APPLY; a re-GRANT
-- keyed on existence AT ROLLBACK could add anon=ALL on a table born later (000009) that the pre-state never
-- exposed. Leave it hardened; restore its exact pre-apply ACL from the captured snapshot ONLY if it was
-- anon-exposed before this packet applied.
DO $$
BEGIN
    IF to_regclass('public.mcp_external_action_audits') IS NOT NULL THEN
        RAISE NOTICE 'A1 rollback: mcp_external_action_audits left HARDENED (fail-closed, review F3). Restore its pre-apply anon ACL from the captured snapshot ONLY if it was exposed before this packet applied.';
    END IF;
END $$;

COMMIT;
