-- Down record for 016_tcc_trip_model_aliases_solidstate_fix.sql.
-- Deletes only the 10 already-applied solid-state family-inference fix rows.

DELETE FROM tcc.trip_model_aliases
WHERE trip_style_id IN (39, 40, 41, 42, 43, 44, 45, 140, 141, 2444)
  AND provenance = '[ETAP Star Library List - published help docs] names-only crosswalk (v2 family-inference fix: static-trip/MOD2 re-match to ETU/LVSST)';
