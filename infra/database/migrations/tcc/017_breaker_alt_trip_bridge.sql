-- 017_breaker_alt_trip_bridge
-- Additive "alternate/retrofit compatible trip" bridge. A breaker style's native
-- tmt_sst_* columns are SINGLE-VALUED (one compatible trip per style); this table lets a
-- style carry ADDITIONAL compatible trips, UNION'd into vw_breaker_sst_bridge.
--
-- First use (operator-directed 2026-06-08): GE WavePro (PCB, breaker_id 18, all 15 frames)
-- gains EntelliGuard TU as a compatible model. The original MicroVersaTrip (EPIC/RMS9/MVT+/MVT-PM)
-- trips have a direct GE EntelliGuard TU retrofit -- [VENDOR-DOC] "EntelliGuard TU Trip Unit
-- Conversion/upgrade kits" 1SDC200139L0201 ("WavePro - All Frames -> EntelliGuard TU") + DET167C
-- WavePro Guide. Bridges to the purpose-built EntelliGuard-TU-for-WavePro trips already modeled:
--   1073 = GE / Entelliguard TU / WavePro     (LSIG; sensors 150..5000, exact WavePro ladder)
--   1566 = GE / Entelliguard TU / Wavepro LI  (LI config; same ladder)

CREATE TABLE IF NOT EXISTS tcc.breaker_alt_trip_bridge (
  breaker_class    text    NOT NULL CHECK (breaker_class IN ('pcb','mccb','iccb')),
  breaker_style_id integer NOT NULL,
  trip_style_id    integer NOT NULL REFERENCES tcc.trip_styles(id),
  relation         text    NOT NULL DEFAULT 'retrofit',
  source           text,
  provenance       text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT breaker_alt_trip_bridge_pk UNIQUE (breaker_class, breaker_style_id, trip_style_id)
);

COMMENT ON TABLE tcc.breaker_alt_trip_bridge IS
  'Additive alternate/retrofit compatible trips per breaker style (beyond the single native tmt_sst_*); UNION-ed into vw_breaker_sst_bridge. Cite the kit/source in source/provenance.';

-- Seed: WavePro all frames -> EntelliGuard TU (LSIG 1073 + LI 1566)
INSERT INTO tcc.breaker_alt_trip_bridge (breaker_class, breaker_style_id, trip_style_id, relation, source, provenance)
SELECT 'pcb', s.id, t.tsid, 'retrofit',
       'GE/ABB EntelliGuard TU Trip Unit Conversion/upgrade kits (1SDC200139L0201); WavePro all-frames MVT->EntelliGuard TU',
       '[VENDOR-DOC] 1SDC200139L0201 + DET167C WavePro Guide; operator-directed 2026-06-08'
FROM tcc.brk_pcb_styles s
CROSS JOIN (VALUES (1073),(1566)) AS t(tsid)
WHERE s.breaker_id = 18
ON CONFLICT (breaker_class, breaker_style_id, trip_style_id) DO NOTHING;

-- Extend the bridge view: native (single tmt_sst_*) UNION ALL the alt-trip bridge.
CREATE OR REPLACE VIEW tcc.vw_breaker_sst_bridge AS
WITH styles AS (
         SELECT 'mccb'::text AS breaker_class, s.id AS breaker_style_id, s.breaker_id,
            s.frame AS breaker_style_frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
           FROM tcc.brk_mccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
        UNION ALL
         SELECT 'iccb'::text, s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
           FROM tcc.brk_iccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
        UNION ALL
         SELECT 'pcb'::text, s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
           FROM tcc.brk_pcb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
        ),
     all_styles AS (
         SELECT 'mccb'::text AS breaker_class, s.id AS breaker_style_id, s.breaker_id, s.frame AS breaker_style_frame, s.r_cont_current FROM tcc.brk_mccb_styles s
        UNION ALL SELECT 'iccb'::text, s.id, s.breaker_id, s.frame, s.r_cont_current FROM tcc.brk_iccb_styles s
        UNION ALL SELECT 'pcb'::text,  s.id, s.breaker_id, s.frame, s.r_cont_current FROM tcc.brk_pcb_styles s
        )
 SELECT st.breaker_class, st.breaker_id, st.breaker_style_id, st.breaker_style_frame,
    st.tmt_sst_mfr, st.tmt_sst_type, st.tmt_sst_style,
    ts.id AS trip_style_id, es.id AS sensor_id, es.rating AS sensor_rating, es.description AS sensor_description, st.r_cont_current
   FROM styles st
     JOIN tcc.manufacturers m ON m.mfr_name::text = st.tmt_sst_mfr
     JOIN tcc.trip_styles ts ON ts.mfg_id = m.id AND ts.type::text = st.tmt_sst_type AND ts.style::text = st.tmt_sst_style
     JOIN tcc.etu_sensors es ON es.trip_style_id = ts.id
 UNION ALL
 SELECT a.breaker_class, st.breaker_id, st.breaker_style_id, st.breaker_style_frame,
    m.mfr_name::text, ts.type::text, ts.style::text,
    ts.id, es.id, es.rating, es.description, st.r_cont_current
   FROM tcc.breaker_alt_trip_bridge a
     JOIN all_styles st ON st.breaker_class = a.breaker_class AND st.breaker_style_id = a.breaker_style_id
     JOIN tcc.trip_styles ts ON ts.id = a.trip_style_id
     JOIN tcc.manufacturers m ON m.id = ts.mfg_id
     JOIN tcc.etu_sensors es ON es.trip_style_id = ts.id;

-- Fail-closed verification
DO $$
DECLARE v_seed int; v_native int; v_alt int;
BEGIN
  SELECT COUNT(*) INTO v_seed FROM tcc.breaker_alt_trip_bridge
   WHERE breaker_class='pcb' AND trip_style_id IN (1073,1566)
     AND breaker_style_id IN (SELECT id FROM tcc.brk_pcb_styles WHERE breaker_id=18);
  IF v_seed <> 30 THEN RAISE EXCEPTION 'seed expected 30 WavePro alt-trip rows, got %', v_seed; END IF;

  SELECT COUNT(*) INTO v_native FROM tcc.vw_breaker_sst_bridge
   WHERE breaker_class='pcb' AND breaker_id=18 AND trip_style_id=251;
  IF v_native = 0 THEN RAISE EXCEPTION 'native WavePro (trip 251) rows missing from view'; END IF;

  SELECT COUNT(DISTINCT trip_style_id) INTO v_alt FROM tcc.vw_breaker_sst_bridge
   WHERE breaker_class='pcb' AND breaker_id=18 AND trip_style_id IN (1073,1566);
  IF v_alt <> 2 THEN RAISE EXCEPTION 'expected 2 EntelliGuard TU trips in view for WavePro, got %', v_alt; END IF;
END $$;
