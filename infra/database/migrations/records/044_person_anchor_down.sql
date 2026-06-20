-- =============================================================================
-- Records migration 044 DOWN -- reverse the person anchor + technician spine FK.
--   Drops the FK + index + column on records.form_submissions first, then
--   records.persons. Touches no form_submissions data beyond the (empty) new
--   nullable column. Idempotent (IF EXISTS) so the test can run it on a clean DB.
-- =============================================================================

BEGIN;
SET client_encoding TO 'UTF8';

ALTER TABLE records.form_submissions
    DROP CONSTRAINT IF EXISTS fk_form_submissions_technician_person;
DROP INDEX IF EXISTS records.ix_form_submissions_technician_person;
ALTER TABLE records.form_submissions
    DROP COLUMN IF EXISTS technician_person_id;

DROP TRIGGER IF EXISTS trg_persons_updated_at ON records.persons;
DROP TABLE IF EXISTS records.persons;

COMMIT;
