-- 029_d4_tmt_helper_recarry_down.sql
-- =============================================================================
-- DOWN for 029 - drop the six re-carried D4 TMT_* helper columns from both style tables.
-- =============================================================================

BEGIN;

ALTER TABLE tcc.brk_iccb_styles
  DROP COLUMN IF EXISTS tmt_tcc_number,
  DROP COLUMN IF EXISTS tmt_notes,
  DROP COLUMN IF EXISTS tmt_trip_plug,
  DROP COLUMN IF EXISTS tmt_breaker_type,
  DROP COLUMN IF EXISTS tmt_thermal_magnetic,
  DROP COLUMN IF EXISTS tmt_thermal;

ALTER TABLE tcc.brk_mccb_styles
  DROP COLUMN IF EXISTS tmt_tcc_number,
  DROP COLUMN IF EXISTS tmt_notes,
  DROP COLUMN IF EXISTS tmt_trip_plug,
  DROP COLUMN IF EXISTS tmt_breaker_type,
  DROP COLUMN IF EXISTS tmt_thermal_magnetic,
  DROP COLUMN IF EXISTS tmt_thermal;

COMMIT;
