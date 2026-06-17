-- =============================================================================
-- Records Chip 2b - DOWN: remove the Instrument-Transformer datasheet templates.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_ct_v1', 'ats_vt_v1', 'ats_cvt_v1');
COMMIT;
