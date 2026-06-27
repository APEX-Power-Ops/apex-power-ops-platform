-- 029_d4_tmt_helper_recarry.sql
-- =============================================================================
-- F-79-04 D4 re-carry (source_faithful). PROD-BOUND, OPERATOR-GATED.
-- *** QUEUED: apply ONLY after the operator gives a separate go (027/028 discipline). ***
--
-- Lane-2 data-carry: re-carry the six TMT_* helper columns from Access into
-- tcc.brk_iccb_styles / tcc.brk_mccb_styles, keyed on source_id (= Access Breaker*Styles.ID,
-- NOT NULL + UNIQUE per mig 007). Source-faithful, name-faithful (D1 precedent: no FK coercion).
-- lower_snake_case target columns; the verbatim Access name + decode live in COMMENT ON COLUMN.
-- NOT wired to serving - the serving cut-line is a separate operator decision (G1 sec 5 D4).
--
-- THIS FILE = the SCHEMA (ALTER + COMMENT), self-contained + idempotent. The DATA population is a
-- separate harness-driven gated step (prod cannot reach D:\TCC_NEW.accdb): read the six columns
-- row-level from Access keyed by ID (pyodbc; memo TMT_Notes read row-level, NEVER via CSV), then
-- UPDATE tcc.brk_<class>_styles SET tmt_* = <access value> WHERE source_id = <Access ID>. Dry-run on
-- the breaker sandbox (verify 608 ICCB / 10335 MCCB + a source_id<->ID checksum), apply on the gate.
-- See reference/tcc/VOCABULARY_MAP.md (Lane-2) + G1 sec 5 D4 / sec 3.1.
--
-- REVERSIBLE: 029_d4_tmt_helper_recarry_down.sql drops the six columns.
-- =============================================================================

BEGIN;

ALTER TABLE tcc.brk_iccb_styles
  ADD COLUMN IF NOT EXISTS tmt_tcc_number       text,
  ADD COLUMN IF NOT EXISTS tmt_notes            text,
  ADD COLUMN IF NOT EXISTS tmt_trip_plug        smallint,
  ADD COLUMN IF NOT EXISTS tmt_breaker_type     smallint,
  ADD COLUMN IF NOT EXISTS tmt_thermal_magnetic smallint,
  ADD COLUMN IF NOT EXISTS tmt_thermal          smallint;

ALTER TABLE tcc.brk_mccb_styles
  ADD COLUMN IF NOT EXISTS tmt_tcc_number       text,
  ADD COLUMN IF NOT EXISTS tmt_notes            text,
  ADD COLUMN IF NOT EXISTS tmt_trip_plug        smallint,
  ADD COLUMN IF NOT EXISTS tmt_breaker_type     smallint,
  ADD COLUMN IF NOT EXISTS tmt_thermal_magnetic smallint,
  ADD COLUMN IF NOT EXISTS tmt_thermal          smallint;

-- COMMENTs preserve the verbatim Access source name + decode (the canonical UI label is
-- VOCABULARY_MAP.canonical_term, NOT the physical column name).
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_tcc_number       IS 'Access BreakerICCBStyles.TMT_TCCNumber: free-text vendor-doc curve-set reference (~99% empty); NOT an FK. Source-faithful raw carry: non-null may be empty/whitespace - trim/decode before treating as present (do not test non-null alone; decode at 031/UI). [VERIFIED-LIVE 2026-06-27]';
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_notes            IS 'Access BreakerICCBStyles.TMT_Notes: human curve-provenance memo. Source-faithful raw carry: non-null may be empty/default - trim/decode before treating as present (do not test non-null alone; decode at 031/UI). [VERIFIED-LIVE]';
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_trip_plug        IS 'Access BreakerICCBStyles.TMT_TripPlug: 0=Trip, 1=Plug. Metadata, not read by the serving cascade. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_breaker_type     IS 'Access BreakerICCBStyles.TMT_BreakerType: 0=Thermal Magnetic, 1=Motor Circuit Protector. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_thermal_magnetic IS 'Access BreakerICCBStyles.TMT_ThermalMagnetic: 0=With Adjustable Instantaneous, 1=Without. Vestigial on ICCB (all 0); the engine reads tmt_thermal here. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_iccb_styles.tmt_thermal          IS 'Access BreakerICCBStyles.TMT_Thermal: the ICCB-class inst-gate flag (== MCCB TMT_ThermalMagnetic): 0=With Adjustable Instantaneous, 1=Without. Engine-consumed (gates the inst-settings list). [DLL G1 3.1 split]';

COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_tcc_number       IS 'Access BreakerMCCBStyles.TMT_TCCNumber: free-text vendor-doc curve-set reference; NOT an FK. Source-faithful raw carry: non-null may be empty/whitespace - trim/decode before treating as present (do not test non-null alone; decode at 031/UI). [VERIFIED-LIVE 2026-06-27]';
COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_notes            IS 'Access BreakerMCCBStyles.TMT_Notes: human curve-provenance memo. Source-faithful raw carry: non-null may be empty/default - trim/decode before treating as present (do not test non-null alone; decode at 031/UI). [VERIFIED-LIVE]';
COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_trip_plug        IS 'Access BreakerMCCBStyles.TMT_TripPlug: 0=Trip, 1=Plug. Metadata, not read by the serving cascade. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_breaker_type     IS 'Access BreakerMCCBStyles.TMT_BreakerType: 0=Thermal Magnetic, 1=Motor Circuit Protector. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_thermal_magnetic IS 'Access BreakerMCCBStyles.TMT_ThermalMagnetic: the MCCB-class inst-gate flag: 0=With Adjustable Instantaneous, 1=Without. Engine-consumed. [DVL-DB G1 3.1]';
COMMENT ON COLUMN tcc.brk_mccb_styles.tmt_thermal          IS 'Access BreakerMCCBStyles.TMT_Thermal: present but vestigial on MCCB (engine reads tmt_thermal_magnetic). [DLL G1 3.1 split]';

-- Preflight (read-only, record for the change log): SELECT count(*) FROM tcc.brk_iccb_styles;  -- 608
--                                                   SELECT count(*) FROM tcc.brk_mccb_styles;  -- 10335

-- Exact-shape guard (fail closed): ADD COLUMN IF NOT EXISTS silently skips a pre-existing column of the
-- WRONG type, so assert the six columns exist with the expected types on both tables before COMMIT.
DO $$
DECLARE
  v_tbl text; v_pair text; v_col text; v_typ text; v_actual text;
  expected text[] := ARRAY['tmt_tcc_number=text','tmt_notes=text','tmt_trip_plug=smallint',
                           'tmt_breaker_type=smallint','tmt_thermal_magnetic=smallint','tmt_thermal=smallint'];
BEGIN
  FOREACH v_tbl IN ARRAY ARRAY['brk_iccb_styles','brk_mccb_styles'] LOOP
    FOREACH v_pair IN ARRAY expected LOOP
      v_col := split_part(v_pair,'=',1); v_typ := split_part(v_pair,'=',2);
      SELECT data_type INTO v_actual FROM information_schema.columns
        WHERE table_schema='tcc' AND table_name=v_tbl AND column_name=v_col;
      IF v_actual IS NULL THEN RAISE EXCEPTION '029 shape: tcc.%.% missing', v_tbl, v_col; END IF;
      IF v_actual <> v_typ THEN RAISE EXCEPTION '029 shape: tcc.%.% is % (expected %)', v_tbl, v_col, v_actual, v_typ; END IF;
    END LOOP;
  END LOOP;
  RAISE NOTICE '029 shape OK: 6 D4 cols x 2 tables, types match';
END $$;

COMMIT;
