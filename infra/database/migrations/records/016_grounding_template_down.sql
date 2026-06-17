-- =============================================================================
-- Records Chip 2b - DOWN: remove the Grounding-System datasheet template.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_grounding_v1');
COMMIT;
