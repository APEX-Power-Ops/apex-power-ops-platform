-- 012_bridge_view_rcont_current.sql
-- =============================================================================
-- Surface the breaker-style continuous rating (r_cont_current, carried in migr 011)
-- through tcc.vw_breaker_sst_bridge so /etu/bridge-sensors can rating-narrow the
-- bridged sensor set to the ONE sensor matching the breaker (#75, STATE §145).
-- Additive (one extra column); existing consumers (cross-filter SELECTs) unaffected.
-- =============================================================================

CREATE OR REPLACE VIEW tcc.vw_breaker_sst_bridge AS
WITH styles AS (
  SELECT 'mccb'::text AS breaker_class, s.id AS breaker_style_id, s.breaker_id, s.frame AS breaker_style_frame,
         s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
  FROM tcc.brk_mccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'iccb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
  FROM tcc.brk_iccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'pcb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style, s.r_cont_current
  FROM tcc.brk_pcb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
)
-- NOTE: r_cont_current MUST be appended last — CREATE OR REPLACE VIEW forbids
-- reordering/renaming existing columns (006 column order preserved verbatim).
SELECT st.breaker_class, st.breaker_id, st.breaker_style_id, st.breaker_style_frame,
       st.tmt_sst_mfr, st.tmt_sst_type, st.tmt_sst_style,
       ts.id AS trip_style_id, es.id AS sensor_id, es.rating AS sensor_rating, es.description AS sensor_description,
       st.r_cont_current
FROM styles st
JOIN tcc.manufacturers m ON m.mfr_name = st.tmt_sst_mfr
JOIN tcc.trip_styles ts ON ts.mfg_id = m.id AND ts.type = st.tmt_sst_type AND ts.style = st.tmt_sst_style
JOIN tcc.etu_sensors es ON es.trip_style_id = ts.id;
