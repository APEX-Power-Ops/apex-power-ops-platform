-- =============================================================================
-- Records Chip 2b - DOWN: remove the MV/HV circuit-breaker datasheet template.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_mvhv_cb_v1';
COMMIT;
