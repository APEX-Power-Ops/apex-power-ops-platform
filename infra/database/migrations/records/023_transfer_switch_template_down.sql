-- =============================================================================
-- Records Chip 2c - DOWN: remove the Automatic Transfer Switch datasheet.
-- New leaf-bound datasheet (no dependents in dev) -> a plain delete reverses it.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_transfer_switch_v1';
COMMIT;
