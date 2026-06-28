-- 031_lvbreakertcc_tmt_contract_view_transition_down.sql
-- =============================================================================
-- DOWN for 031 -- restore the 028 base contract-view definition VERBATIM via
-- CREATE OR REPLACE (re-introduces the Cartesian frame_counts CTE and the
-- d4_tmt_helper_columns_absent_from_projection / d5_inst_override_columns_absent_
-- from_projection flags). The output column list is unchanged, so the two
-- dependent views auto-revert; they are not touched.
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW tcc.vw_lvbreakertcc_tmt_frame_contract AS
WITH frame_base AS (
  SELECT
    f.id AS frame_id,
    UPPER(f.breaker_class::text) AS breaker_class,
    f.breaker_style_id,
    f.size AS frame_size,
    b.manufacturer_id,
    m.mfr_name AS manufacturer_name,
    b.id AS breaker_id,
    b.name AS breaker_name,
    s.frame AS breaker_style_name,
    s.standard,
    true AS style_parent_exists
  FROM tcc.tmt_frames f
  JOIN tcc.brk_mccb_styles s
    ON UPPER(f.breaker_class::text) = 'MCCB'
   AND s.id = f.breaker_style_id
  JOIN tcc.brk_mccb b
    ON b.id = s.breaker_id
  LEFT JOIN tcc.manufacturers m
    ON m.id = b.manufacturer_id

  UNION ALL

  SELECT
    f.id AS frame_id,
    UPPER(f.breaker_class::text) AS breaker_class,
    f.breaker_style_id,
    f.size AS frame_size,
    b.manufacturer_id,
    m.mfr_name AS manufacturer_name,
    b.id AS breaker_id,
    b.name AS breaker_name,
    s.frame AS breaker_style_name,
    s.standard,
    true AS style_parent_exists
  FROM tcc.tmt_frames f
  JOIN tcc.brk_iccb_styles s
    ON UPPER(f.breaker_class::text) = 'ICCB'
   AND s.id = f.breaker_style_id
  JOIN tcc.brk_iccb b
    ON b.id = s.breaker_id
  LEFT JOIN tcc.manufacturers m
    ON m.id = b.manufacturer_id

  UNION ALL

  SELECT
    f.id AS frame_id,
    UPPER(f.breaker_class::text) AS breaker_class,
    f.breaker_style_id,
    f.size AS frame_size,
    b.manufacturer_id,
    m.mfr_name AS manufacturer_name,
    b.id AS breaker_id,
    b.name AS breaker_name,
    s.frame AS breaker_style_name,
    s.standard,
    true AS style_parent_exists
  FROM tcc.tmt_frames f
  JOIN tcc.brk_pcb_styles s
    ON UPPER(f.breaker_class::text) = 'PCB'
   AND s.id = f.breaker_style_id
  JOIN tcc.brk_pcb b
    ON b.id = s.breaker_id
  LEFT JOIN tcc.manufacturers m
    ON m.id = b.manufacturer_id
),
orphans AS (
  SELECT
    f.id AS frame_id,
    UPPER(f.breaker_class::text) AS breaker_class,
    f.breaker_style_id,
    f.size AS frame_size,
    NULL::integer AS manufacturer_id,
    NULL::text AS manufacturer_name,
    NULL::integer AS breaker_id,
    NULL::varchar AS breaker_name,
    NULL::varchar AS breaker_style_name,
    NULL::numeric AS standard,
    false AS style_parent_exists
  FROM tcc.tmt_frames f
  WHERE NOT EXISTS (
    SELECT 1
    FROM frame_base fb
    WHERE fb.frame_id = f.id
  )
),
frame_counts AS (
  SELECT
    f.id AS frame_id,
    count(DISTINCT a.id)::integer AS amp_count,
    count(DISTINCT st.id)::integer AS setting_count,
    count(DISTINCT th.id)::integer AS thermal_adjustment_count,
    count(DISTINCT c.id)::integer AS curve_point_count,
    count(DISTINCT c.class)::integer AS trip_class_count
  FROM tcc.tmt_frames f
  LEFT JOIN tcc.tmt_amps a
    ON a.frame_id = f.id
  LEFT JOIN tcc.tmt_settings st
    ON st.frame_id = f.id
  LEFT JOIN tcc.tmt_thermal_adj th
    ON th.frame_id = f.id
  LEFT JOIN tcc.tmt_curves c
    ON c.frame_id = f.id
  GROUP BY f.id
)
SELECT
  fb.frame_id,
  fb.breaker_class,
  fb.breaker_style_id,
  fb.frame_size,
  fb.manufacturer_id,
  fb.manufacturer_name,
  fb.breaker_id,
  fb.breaker_name,
  fb.breaker_style_name,
  fb.standard,
  fb.style_parent_exists,
  fc.amp_count,
  fc.setting_count,
  fc.thermal_adjustment_count,
  fc.curve_point_count,
  fc.trip_class_count,
  (fc.amp_count > 0) AS has_amp_options,
  (fc.curve_point_count > 0) AS has_curve_points,
  (fb.style_parent_exists AND fc.amp_count > 0 AND fc.curve_point_count > 0) AS is_curve_serving_candidate,
  CASE
    WHEN NOT fb.style_parent_exists THEN 'withhold'
    WHEN fc.amp_count = 0 THEN 'withhold'
    WHEN fc.curve_point_count = 0 THEN 'withhold'
    ELSE 'bounded'
  END AS serving_posture,
  array_remove(ARRAY[
    CASE WHEN NOT fb.style_parent_exists THEN 'missing_style_parent' END,
    CASE WHEN fc.amp_count = 0 THEN 'missing_amp_options' END,
    CASE WHEN fc.curve_point_count = 0 THEN 'missing_curve_points' END,
    CASE WHEN fc.setting_count = 0 THEN 'missing_setting_options' END,
    CASE WHEN fc.thermal_adjustment_count = 0 THEN 'missing_thermal_adjustment_rows' END,
    CASE WHEN fb.breaker_class IN ('ICCB', 'MCCB') THEN 'd4_tmt_helper_columns_absent_from_projection' END,
    'd5_inst_override_columns_absent_from_projection'
  ], NULL)::text[] AS projection_hazards
FROM (
  SELECT * FROM frame_base
  UNION ALL
  SELECT * FROM orphans
) fb
JOIN frame_counts fc
  ON fc.frame_id = fb.frame_id;

COMMENT ON VIEW tcc.vw_lvbreakertcc_tmt_frame_contract IS
  '#79 F-79-02: class-keyed TMT frame contract view with curve-serving posture and projection hazards; does not infer missing Access behavior.';

COMMIT;
