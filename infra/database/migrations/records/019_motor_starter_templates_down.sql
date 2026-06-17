-- =============================================================================
-- Records Chip 2b - DOWN: remove the Motor-Starter datasheet templates.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- (The MCC leaves were never given sheets - pure crossref, composed at the asset tree.)
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates
WHERE template_code IN ('ats_lv_motor_starter_v1', 'ats_mv_motor_starter_v1');
COMMIT;
