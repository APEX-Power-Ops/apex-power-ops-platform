-- =============================================================================
-- Records Chip 2b - DOWN: remove the switchgear + panelboard datasheet templates.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_switchgear_v1', 'ats_panelboard_v1');
COMMIT;
