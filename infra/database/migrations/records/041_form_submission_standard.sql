-- =============================================================================
-- Records MTS-accommodation Chip C1 — form_submissions.neta_standard.
-- The test EVENT's standard: ats (acceptance/commissioning) | mts (maintenance).
-- A given apparatus is tested under ATS at commissioning and MTS at each maintenance
-- interval, using the SAME standard-aware template (migs 038-040). This column records
-- which standard a submission ran under; the render/validate layer (Chip C2, serving)
-- resolves coverage + acceptance against it. Idempotent; reversible in _down.
-- =============================================================================
BEGIN;
SET client_encoding TO 'UTF8';

ALTER TABLE records.form_submissions
    ADD COLUMN IF NOT EXISTS neta_standard records.neta_standard_enum NOT NULL DEFAULT 'ats';

COMMENT ON COLUMN records.form_submissions.neta_standard IS
    'The NETA standard this test event runs under: ats (acceptance/commissioning) | mts '
    '(maintenance). The submission renders + validates against this standard''s coverage and '
    'acceptance from the standard-aware template (field_schema.neta_standards / neta_covers, '
    'migs 039-040) + the standard-keyed neta_tables (mig 038). Distinct from '
    'form_templates.neta_standard (the template''s native/primary standard).';

COMMIT;
