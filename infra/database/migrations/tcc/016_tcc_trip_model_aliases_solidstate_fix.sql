-- 016_tcc_trip_model_aliases_solidstate_fix.sql
-- =============================================================================
-- RECORD ONLY: already applied to prod by CC via governed migration
-- `tcc_trip_model_aliases_solidstate_fix_seed` on 2026-06-07.
--
-- Do not re-run this file against prod as a normal app migration.
--
-- Purpose: capture the +10 additive trip model alias rows from the v2 Star
-- Library family-inference fix. The generator no longer routes "static trip"
-- to EMT, and legacy la/od cues are word-boundary anchored so GE VersaTrip
-- MOD2 no longer false-hits "od2".
-- =============================================================================

INSERT INTO tcc.trip_model_aliases (
  trip_style_id,
  etap_model,
  tier,
  provenance,
  created_at
) VALUES
  (39, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (40, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (41, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (42, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (43, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (44, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (45, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (140, 'FB600', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (141, 'FB600', 'core', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00'),
  (2444, 'VersaTrip(MOD2)', 'exact', '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)', '2026-06-07 21:11:21.419675+00');
