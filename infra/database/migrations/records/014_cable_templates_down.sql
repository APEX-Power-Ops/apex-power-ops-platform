-- =============================================================================
-- Records Chip 2b - DOWN: remove the cable datasheet templates (LV + MV/HV).
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_lv_cable_v1', 'ats_mvhv_cable_v1');
COMMIT;
