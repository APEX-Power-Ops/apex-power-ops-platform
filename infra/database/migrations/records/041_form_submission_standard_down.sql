-- =============================================================================
-- DOWN for 041_form_submission_standard.sql — drop form_submissions.neta_standard.
-- =============================================================================
BEGIN;
SET client_encoding TO 'UTF8';

ALTER TABLE records.form_submissions DROP COLUMN IF EXISTS neta_standard;

COMMIT;
