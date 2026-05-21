-- ============================================================================
-- APEX PM Lane 500 / Migration 016 — Structural Supplement
-- Migration: 016_seam_apparatus_scope_id_and_operational_grants.sql
-- Created:   2026-05-21
-- ============================================================================
-- Adds the missing relational seam.apparatus.scope_id anchor and extends the
-- operational grant posture needed for future no-live onboarding work.
--
-- Scope
--   * Add seam.apparatus.scope_id as a nullable TEXT foreign key to seam.scopes.
--   * Add an index on seam.apparatus.scope_id.
--   * Grant pm and operations SELECT, INSERT, UPDATE on seam.projects,
--     seam.tasks, and seam.apparatus.
--   * Revoke anon and authenticated access on the same three tables.
--
-- Out of scope
--   * No business-row insert, update, or backfill.
--   * No JSONB normalization.
--   * No route, auth-role-definition, or persistence-module change.
-- ============================================================================

ALTER TABLE seam.apparatus
    ADD COLUMN IF NOT EXISTS scope_id TEXT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'seam.apparatus'::regclass
          AND conname = 'apparatus_scope_id_fkey'
    ) THEN
        ALTER TABLE seam.apparatus
            ADD CONSTRAINT apparatus_scope_id_fkey
            FOREIGN KEY (scope_id) REFERENCES seam.scopes(id);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS apparatus_scope_id_idx
    ON seam.apparatus(scope_id);

GRANT SELECT, INSERT, UPDATE ON TABLE seam.projects TO pm, operations;
GRANT SELECT, INSERT, UPDATE ON TABLE seam.tasks TO pm, operations;
GRANT SELECT, INSERT, UPDATE ON TABLE seam.apparatus TO pm, operations;

REVOKE ALL ON TABLE seam.projects FROM anon;
REVOKE ALL ON TABLE seam.projects FROM authenticated;
REVOKE ALL ON TABLE seam.tasks FROM anon;
REVOKE ALL ON TABLE seam.tasks FROM authenticated;
REVOKE ALL ON TABLE seam.apparatus FROM anon;
REVOKE ALL ON TABLE seam.apparatus FROM authenticated;

COMMENT ON COLUMN seam.apparatus.scope_id IS
    'Nullable seam scope anchor introduced by PM Lane 500 migration 016 structural supplement.';