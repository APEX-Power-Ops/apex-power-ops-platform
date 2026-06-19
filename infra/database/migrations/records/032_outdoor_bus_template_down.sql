-- =============================================================================
-- Records Chip 2c - DOWN: remove the Outdoor Bus Structure datasheet.
-- New leaf-bound datasheet (no dependents in dev) -> a plain delete reverses it.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_outdoor_bus_v1';
COMMIT;
