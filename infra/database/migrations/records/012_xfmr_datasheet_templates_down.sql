-- =============================================================================
-- Records Chip 2b - DOWN: remove the transformer datasheet templates (dry + liquid).
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_dry_xfmr_v1', 'ats_liquid_xfmr_v1');
COMMIT;
