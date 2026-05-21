-- ============================================================================
-- APEX PM Lane 421 — Schema Architecture Correction
-- Migration: 015_seam_scopes_addition_and_fk_retarget.sql
-- Created:   2026-05-21
-- ============================================================================
-- Corrects the inherited Dataverse-era public.scopes assumption by creating
-- seam.scopes as the operational scope anchor and retargeting the seam-side
-- financial scope foreign keys to that TEXT-based table.
--
-- Scope
--   * Create seam.scopes with TEXT ids aligned to seam.projects/apparatus.
--   * Preserve insert-only discipline on the new seam.scopes table.
--   * Retarget seam.scope_labor_details.scope_id from public.scopes to seam.scopes.
--   * Retarget seam.apparatus_revenue_events.scope_id from public.scopes to seam.scopes.
--   * Preserve RLS and public-role deny posture.
--   * Extend the PM/Operations SELECT+INSERT grant contract to seam.scopes.
--
-- Out of scope
--   * No route or persistence-module change.
--   * No business-row insert or backfill.
--   * No public.* mutation.
-- ============================================================================

CREATE TABLE seam.scopes (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES seam.projects(id),
    name            TEXT NOT NULL,
    scope_type      TEXT NOT NULL,
    total_hours     NUMERIC NOT NULL,
    quoted_amount   NUMERIC NOT NULL,
    multiplier      NUMERIC NOT NULL DEFAULT 1.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_seam_scopes_insert_only_update
    ON seam.scopes;
CREATE TRIGGER trg_seam_scopes_insert_only_update
    BEFORE UPDATE ON seam.scopes
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

DROP TRIGGER IF EXISTS trg_seam_scopes_insert_only_delete
    ON seam.scopes;
CREATE TRIGGER trg_seam_scopes_insert_only_delete
    BEFORE DELETE ON seam.scopes
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_lane_411_financial_table_mutation();

ALTER TABLE seam.scopes ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE seam.scopes FROM anon;
REVOKE ALL ON TABLE seam.scopes FROM authenticated;

GRANT SELECT, INSERT ON TABLE seam.scopes TO pm, operations;

DO $$
DECLARE
    role_name TEXT;
BEGIN
    FOREACH role_name IN ARRAY ARRAY['field_tech', 'field_lead', 'task_lead']
    LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
            EXECUTE format('REVOKE ALL ON TABLE seam.scopes FROM %I', role_name);
        END IF;
    END LOOP;
END;
$$;

ALTER TABLE seam.scope_labor_details
    DROP CONSTRAINT IF EXISTS scope_labor_details_scope_id_fkey;

ALTER TABLE seam.scope_labor_details
    ALTER COLUMN scope_id TYPE TEXT USING scope_id::text;

ALTER TABLE seam.scope_labor_details
    ADD CONSTRAINT scope_labor_details_scope_id_fkey
    FOREIGN KEY (scope_id) REFERENCES seam.scopes(id);

ALTER TABLE seam.apparatus_revenue_events
    DROP CONSTRAINT IF EXISTS apparatus_revenue_events_scope_id_fkey;

ALTER TABLE seam.apparatus_revenue_events
    ALTER COLUMN scope_id TYPE TEXT USING scope_id::text;

ALTER TABLE seam.apparatus_revenue_events
    ADD CONSTRAINT apparatus_revenue_events_scope_id_fkey
    FOREIGN KEY (scope_id) REFERENCES seam.scopes(id);

COMMENT ON TABLE seam.scopes IS
    'Operational scope anchor table introduced by PM Lane 421 schema architecture correction.';