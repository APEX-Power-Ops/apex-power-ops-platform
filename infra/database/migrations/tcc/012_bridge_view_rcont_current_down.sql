-- 012_bridge_view_rcont_current_down.sql — restore the migration 006 view (drop r_cont_current column).
-- NOTE: pair with reverting the /etu/bridge-sensors code (it SELECTs r_cont_current).
CREATE OR REPLACE VIEW tcc.vw_breaker_sst_bridge AS
WITH styles AS (
  SELECT 'mccb'::text AS breaker_class, s.id AS breaker_style_id, s.breaker_id, s.frame AS breaker_style_frame,
         s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_mccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'iccb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_iccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'pcb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_pcb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
)
SELECT st.breaker_class, st.breaker_id, st.breaker_style_id, st.breaker_style_frame,
       st.tmt_sst_mfr, st.tmt_sst_type, st.tmt_sst_style,
       ts.id AS trip_style_id, es.id AS sensor_id, es.rating AS sensor_rating, es.description AS sensor_description
FROM styles st
JOIN tcc.manufacturers m ON m.mfr_name = st.tmt_sst_mfr
JOIN tcc.trip_styles ts ON ts.mfg_id = m.id AND ts.type = st.tmt_sst_type AND ts.style = st.tmt_sst_style
JOIN tcc.etu_sensors es ON es.trip_style_id = ts.id;
