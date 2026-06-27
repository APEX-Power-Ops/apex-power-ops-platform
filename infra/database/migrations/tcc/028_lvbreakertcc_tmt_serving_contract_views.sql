-- 028_lvbreakertcc_tmt_serving_contract_views.sql
-- =============================================================================
-- APPLIED to prod (governed Supabase fxoyniqnrlkxfligbxmg, PG 17.6) via MCP
-- apply_migration on 2026-06-27 (name f79_02_lvbreakertcc_tmt_serving_contract_views).
-- Preflight: tmt_frames=42069, target views=0, deps=11/11.
-- Post: views=3, total=42069, serving=40125, hazards=1944, curveless=1923,
-- orphans=0, partition_ok=true; matches sandbox snapshot exactly. Down available.
-- Authorization: operator "28 tcc proceed". See 028_APPLY_TRANSCRIPT.md.
-- =============================================================================
-- =============================================================================
-- F-79-02 (HIGH) — #79 lvbreakertcc contract audit promotion.
-- *** APPLIED 2026-06-27 (after 027) - see the applied-stamp header above + 028_APPLY_TRANSCRIPT.md. ***
-- PROD-BOUND. Was applied against governed Supabase tcc via apply_migration (operator-gated; now LIVE).
--
-- WHAT: additive, diagnostic-only TMT serving-contract views. They SEPARATE the
-- TMT frames that can satisfy the current lvbreakertcc nominal-curve serving
-- contract from those that cannot (curveless / no amp options / no style parent),
-- so serving can be bounded WITHOUT inventing curves. Purely additive: three new
-- views, no data change, no existing object altered. Nothing reads them yet, so
-- creating them does not change what lvbreakertcc serves.
--
-- BEHAVIORAL DEFERRAL (Access authority): whether the withheld frames are
-- suppressed or backfilled, and WIRING lvbreakertcc serving to these views, is a
-- separate calc-engine ruling (Access TCC_NEW.accdb). This packet only exposes
-- the contract boundary; it does not decide it.
--
-- SOURCE: codex #79 sandbox candidate-patches/002, de-hardcoded for prod — the
-- sandbox self-check's snapshot counts (42069 / 40125 / 1944 / 1923) are NOT
-- promoted; the migration RAISE NOTICEs the LIVE counts instead (prod differs
-- from the sandbox by the F-79-03 row-count deltas, which remain a triangulation
-- task, not actioned here).
--
-- PREFLIGHT (read-only, record for the change log):
--   SELECT count(*) FROM tcc.tmt_frames;
--
-- REVERSIBLE: 028_..._down.sql drops the three views.
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

CREATE OR REPLACE VIEW tcc.vw_lvbreakertcc_tmt_serving_frames AS
SELECT *
FROM tcc.vw_lvbreakertcc_tmt_frame_contract
WHERE is_curve_serving_candidate;

COMMENT ON VIEW tcc.vw_lvbreakertcc_tmt_serving_frames IS
  '#79 F-79-02: TMT frames safe for current lvbreakertcc nominal curve serving; excludes curveless frames instead of inventing curves.';

CREATE OR REPLACE VIEW tcc.vw_lvbreakertcc_tmt_projection_hazards AS
SELECT *
FROM tcc.vw_lvbreakertcc_tmt_frame_contract
WHERE NOT is_curve_serving_candidate;

COMMENT ON VIEW tcc.vw_lvbreakertcc_tmt_projection_hazards IS
  '#79 F-79-02: actionable TMT projection hazards for the current serving contract; curveless rows require a suppress-or-backfill (Access) decision.';

-- Live counts for the change log (no hardcoded snapshot assertions; prod differs
-- from the sandbox by the F-79-03 deltas).
DO $$
DECLARE v_total integer; v_serving integer; v_hazard integer; v_curveless integer; v_orphan integer;
BEGIN
  SELECT count(*) INTO v_total    FROM tcc.vw_lvbreakertcc_tmt_frame_contract;
  SELECT count(*) INTO v_serving  FROM tcc.vw_lvbreakertcc_tmt_serving_frames;
  SELECT count(*) INTO v_hazard   FROM tcc.vw_lvbreakertcc_tmt_projection_hazards;
  SELECT count(*) INTO v_curveless FROM tcc.vw_lvbreakertcc_tmt_frame_contract WHERE NOT has_curve_points;
  SELECT count(*) INTO v_orphan   FROM tcc.vw_lvbreakertcc_tmt_frame_contract WHERE NOT style_parent_exists;
  RAISE NOTICE 'F-79-02 TMT contract (LIVE): frames=%, serving=%, hazards=%, curveless=%, orphans=%',
    v_total, v_serving, v_hazard, v_curveless, v_orphan;
  -- Count-free logical invariants: the three views must partition the contract.
  IF v_serving + v_hazard <> v_total THEN
    RAISE EXCEPTION 'F-79-02 partition invariant violated: serving(%) + hazards(%) <> total(%)', v_serving, v_hazard, v_total;
  END IF;
  IF v_orphan <> 0 THEN
    RAISE NOTICE 'F-79-02 WARNING: % orphan frame(s) with no style parent present in prod (sandbox had 0)', v_orphan;
  END IF;
END $$;

COMMIT;
