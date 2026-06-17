-- =============================================================================
-- Records Chip 2b - DOWN: remove the LV circuit-breaker datasheet template.
-- Reversible; leaves the 2a NETA reference + 2-shell/backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_lv_cb_v1';
COMMIT;
