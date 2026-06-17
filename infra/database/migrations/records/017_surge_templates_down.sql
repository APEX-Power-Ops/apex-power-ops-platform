-- =============================================================================
-- Records Chip 2b - DOWN: remove the Surge-Protection datasheets + reverse the leaf split.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy + 2-backfill intact.
-- Order: templates first (they FK asset_classes), then restore the original acnp wiring,
-- then drop the spd_lv leaf. Safe to run before the up (all DELETEs are no-ops if absent;
-- the restore INSERT is ON CONFLICT DO NOTHING).
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code IN ('ats_lv_spd_v1', 'ats_mvhv_arrester_v1');

-- restore the original surge_arrester -> 7.19.1 link (was non-primary, from backfill 009)
INSERT INTO records.asset_class_neta_procedure (asset_class_id, neta_procedure_id, is_primary)
VALUES (
  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'surge_arrester'),
  (SELECT neta_procedure_id FROM records.neta_procedures WHERE section = '7.19.1'),
  false)
ON CONFLICT (asset_class_id, neta_procedure_id) DO NOTHING;

-- drop the spd_lv leaf's link + the leaf itself
DELETE FROM records.asset_class_neta_procedure
WHERE asset_class_id = (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'spd_lv');
DELETE FROM records.asset_classes WHERE class_code = 'spd_lv';
COMMIT;
