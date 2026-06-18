-- =============================================================================
-- Records Chip 2c - DOWN: remove the Metal-Enclosed Busway datasheet.
-- New leaf-bound datasheet (no dependents in dev) -> a plain delete reverses it.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_busway_v1';
COMMIT;
