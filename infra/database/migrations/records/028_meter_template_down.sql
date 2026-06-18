-- =============================================================================
-- Records Chip 2c - DOWN: remove the Metering Device datasheet.
-- New leaf-bound datasheet (no dependents in dev) -> a plain delete reverses it.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_meter_v1';
COMMIT;
