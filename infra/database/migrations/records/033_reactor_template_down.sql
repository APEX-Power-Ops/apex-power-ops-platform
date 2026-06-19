-- =============================================================================
-- Records Chip 2c - DOWN: remove the Dry-Type Reactor datasheet.
-- New leaf-bound datasheet (no dependents in dev) -> a plain delete reverses it.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_reactor_v1';
COMMIT;
