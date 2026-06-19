-- =============================================================================
-- DOWN for 042 - remove the Network Protector datasheet, link, and leaf; re-deactivate parent.
-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy intact. Safe before the up
-- (DELETEs are no-ops if absent). Order: template (FK), then link, then leaf, then parent flag.
-- =============================================================================
BEGIN;
DELETE FROM records.form_templates WHERE template_code = 'ats_network_protector_v1';
DELETE FROM records.asset_class_neta_procedure
  WHERE asset_class_id = (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'network_protector');
DELETE FROM records.asset_classes WHERE class_code = 'network_protector';
-- restore the parent to its shell-seeded inactive state (007 marked it future/inactive).
UPDATE records.asset_classes SET is_active = false, updated_at = now()
  WHERE class_code = 'network_protectors';
COMMIT;
