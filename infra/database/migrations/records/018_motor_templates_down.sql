-- =============================================================================
-- Records Chip 2b - DOWN: remove the Rotating-Machinery datasheet templates.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates
WHERE template_code IN ('ats_induction_motor_v1', 'ats_synchronous_machine_v1', 'ats_dc_machine_v1');
COMMIT;
