-- 031_lvbreakertcc_tmt_contract_view_transition.sql
-- =============================================================================
-- F-79-04 D4/D5 contract-view transition. PROD-BOUND, OPERATOR-GATED.
-- *** QUEUED: apply ONLY after the operator gives a separate go, and ONLY after
--     029 (D4 cols + recarry) and 030 (D5 side table + rows) are applied. ***
--
-- WHAT: a single CREATE OR REPLACE of the 028 base contract view
-- (tcc.vw_lvbreakertcc_tmt_frame_contract) that transitions the now-stale hazard
-- surface after the D4/D5 data carry, and fixes a latent perf defect. Three changes,
-- nothing else -- no serving change, no `served` flag flips (Decision 1 RATIFIED:
-- wire nothing new in this lane; the Access/engine authority stays operator-side):
--
--   1. DROP the d4_tmt_helper_columns_absent_from_projection flag. 029 carried the
--      six TMT_* helper columns into brk_iccb_styles / brk_mccb_styles and the
--      recarry populated them, so the "absent" annotation is no longer true.
--   2. RELABEL d5_inst_override_columns_absent_from_projection ->
--      d5_inst_override_carried_reference_only. 030 carried the InstOvr*/NInstOvr*/
--      timing/rating block into tcc.brk_style_native_overrides as native_bounded
--      REFERENCE data. It is carried, not projected, and NOT wired to serving --
--      the relabel says exactly that (behavior remains un-claimed).
--   3. FIX the frame_counts child-count Cartesian product (Codex review-2dd99030 P2).
--      The 028 frame_counts CTE LEFT JOINs tmt_amps x tmt_settings x tmt_thermal_adj
--      x tmt_curves (~1.1M curve rows) before COUNT(DISTINCT ...), multiplying each
--      frame's children before de-duping. 031 aggregates EACH child per-frame in its
--      own CTE, then LEFT JOINs the per-frame counts onto tmt_frames (COALESCE 0 for
--      childless frames). This is value-equivalent to the COUNT(DISTINCT child.id) it
--      replaces -- each child id is a PK, so per-frame count(*) == count(DISTINCT id),
--      and a frame with no child rows yields 0 either way -- so every count / posture
--      / partition column is byte-identical to 028; only projection_hazards changes.
--
-- FAIL-CLOSED GUARD: the leading DO block RAISEs unless 029 (D4 populated) AND 030
-- (D5 side table populated) are in place, so the hazard labels can never flip ahead
-- of the data they assert. The trailing DO block re-checks the serving+hazards=total
-- partition invariant and asserts that NEITHER stale flag survives the transition.
--
-- DEPENDENTS: vw_lvbreakertcc_tmt_serving_frames and
-- vw_lvbreakertcc_tmt_projection_hazards are SELECT * over this view; the output
-- column list is unchanged (projection_hazards keeps its name + text[] type), so
-- CREATE OR REPLACE is permitted and the dependents auto-reflect the new definition.
-- They are intentionally NOT re-created (minimal change; no drop/recreate of
-- unaffected objects).
--
-- VALUE-PARITY ANCHOR (captured from prod fxoyniqnrlkxfligbxmg 2026-06-28, pre-031):
--   total=42069, serving=40125, hazards=1944, curveless=1923, orphans=0;
--   parity_hash_excl_hazards = 58cc15fe36e5dabf131e154e730c1833.
-- The 031 view MUST reproduce these exactly (perf-fix is value-neutral).
--
-- REVERSIBLE: 031_..._down.sql re-creates the 028 base-view definition verbatim.
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- Fail-closed precondition guard: refuse to flip the hazard labels unless the
-- D4 (029) and D5 (030) data they now assert is actually present.
-- ---------------------------------------------------------------------------
DO $$
DECLARE v_d4 bigint; v_d5 bigint;
BEGIN
  IF to_regclass('tcc.brk_style_native_overrides') IS NULL THEN
    RAISE EXCEPTION '031 precondition: tcc.brk_style_native_overrides missing -- apply 030 DDL before 031';
  END IF;

  SELECT count(*) INTO v_d5 FROM tcc.brk_style_native_overrides;
  IF v_d5 = 0 THEN
    RAISE EXCEPTION '031 precondition: tcc.brk_style_native_overrides is empty -- apply 030 data before 031 (refusing to relabel D5 carried_reference_only)';
  END IF;

  -- tmt_breaker_type is a smallint enum (0/1); non-null is a clean "029 data ran"
  -- sentinel (the text helper cols can be empty-string non-null, so they are NOT used).
  SELECT (SELECT count(*) FROM tcc.brk_iccb_styles WHERE tmt_breaker_type IS NOT NULL)
       + (SELECT count(*) FROM tcc.brk_mccb_styles WHERE tmt_breaker_type IS NOT NULL)
    INTO v_d4;
  IF v_d4 = 0 THEN
    RAISE EXCEPTION '031 precondition: D4 tmt helper columns are unpopulated -- apply 029 data before 031 (refusing to drop the d4-absent hazard flag)';
  END IF;

  RAISE NOTICE '031 precondition OK: D4 populated rows=%, D5 side rows=%', v_d4, v_d5;
END $$;

-- ---------------------------------------------------------------------------
-- Transitioned contract view. frame_base + orphans are VERBATIM from 028; only
-- frame_counts (per-child aggregation, no Cartesian) and the projection_hazards
-- array (d4 dropped, d5 relabeled) change.
-- ---------------------------------------------------------------------------
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
-- Per-child aggregation (031 perf-fix): each child counted once per frame, with
-- NO cross-join multiplication. count(*) == the 028 count(DISTINCT child.id) since
-- each child id is a PK; childless frames fall to 0 via the COALESCE below.
amp_counts AS (
  SELECT a.frame_id, count(*)::integer AS amp_count
  FROM tcc.tmt_amps a
  GROUP BY a.frame_id
),
setting_counts AS (
  SELECT st.frame_id, count(*)::integer AS setting_count
  FROM tcc.tmt_settings st
  GROUP BY st.frame_id
),
thermal_counts AS (
  SELECT th.frame_id, count(*)::integer AS thermal_adjustment_count
  FROM tcc.tmt_thermal_adj th
  GROUP BY th.frame_id
),
curve_counts AS (
  SELECT c.frame_id,
         count(*)::integer AS curve_point_count,
         count(DISTINCT c.class)::integer AS trip_class_count
  FROM tcc.tmt_curves c
  GROUP BY c.frame_id
),
frame_counts AS (
  SELECT
    f.id AS frame_id,
    COALESCE(ac.amp_count, 0) AS amp_count,
    COALESCE(sc.setting_count, 0) AS setting_count,
    COALESCE(tc.thermal_adjustment_count, 0) AS thermal_adjustment_count,
    COALESCE(cc.curve_point_count, 0) AS curve_point_count,
    COALESCE(cc.trip_class_count, 0) AS trip_class_count
  FROM tcc.tmt_frames f
  LEFT JOIN amp_counts ac
    ON ac.frame_id = f.id
  LEFT JOIN setting_counts sc
    ON sc.frame_id = f.id
  LEFT JOIN thermal_counts tc
    ON tc.frame_id = f.id
  LEFT JOIN curve_counts cc
    ON cc.frame_id = f.id
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
    -- 031: the d4_tmt_helper_columns_absent_from_projection flag is removed
    -- (029 carried + populated the six TMT_* helper columns).
    -- 031: D5 inst-override block carried as native_bounded reference (030),
    -- NOT projected and NOT wired to serving.
    'd5_inst_override_carried_reference_only'
  ], NULL)::text[] AS projection_hazards
FROM (
  SELECT * FROM frame_base
  UNION ALL
  SELECT * FROM orphans
) fb
JOIN frame_counts fc
  ON fc.frame_id = fb.frame_id;

COMMENT ON VIEW tcc.vw_lvbreakertcc_tmt_frame_contract IS
  '#79 F-79-02/04: class-keyed TMT frame contract view with curve-serving posture and projection hazards. 031 transition: d4-absent flag dropped (029 carried the six TMT_* helper cols); d5 relabeled to d5_inst_override_carried_reference_only (030 native_bounded reference, NOT served); frame child-counts via per-frame aggregation CTEs (no Cartesian). No serving change; does not infer Access behavior.';

-- ---------------------------------------------------------------------------
-- Post-transition invariants for the change log: the three views still partition
-- the contract, and NEITHER stale flag survives.
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  v_total integer; v_serving integer; v_hazard integer; v_curveless integer; v_orphan integer;
  v_d4flag integer; v_d5old integer; v_d5new integer;
BEGIN
  SELECT count(*) INTO v_total     FROM tcc.vw_lvbreakertcc_tmt_frame_contract;
  SELECT count(*) INTO v_serving   FROM tcc.vw_lvbreakertcc_tmt_serving_frames;
  SELECT count(*) INTO v_hazard    FROM tcc.vw_lvbreakertcc_tmt_projection_hazards;
  SELECT count(*) INTO v_curveless FROM tcc.vw_lvbreakertcc_tmt_frame_contract WHERE NOT has_curve_points;
  SELECT count(*) INTO v_orphan    FROM tcc.vw_lvbreakertcc_tmt_frame_contract WHERE NOT style_parent_exists;
  SELECT count(*) INTO v_d4flag    FROM tcc.vw_lvbreakertcc_tmt_frame_contract
    WHERE 'd4_tmt_helper_columns_absent_from_projection' = ANY (projection_hazards);
  SELECT count(*) INTO v_d5old     FROM tcc.vw_lvbreakertcc_tmt_frame_contract
    WHERE 'd5_inst_override_columns_absent_from_projection' = ANY (projection_hazards);
  SELECT count(*) INTO v_d5new     FROM tcc.vw_lvbreakertcc_tmt_frame_contract
    WHERE 'd5_inst_override_carried_reference_only' = ANY (projection_hazards);

  RAISE NOTICE '031 TMT contract (LIVE): frames=%, serving=%, hazards=%, curveless=%, orphans=%, d5_carried=%',
    v_total, v_serving, v_hazard, v_curveless, v_orphan, v_d5new;

  IF v_serving + v_hazard <> v_total THEN
    RAISE EXCEPTION '031 partition invariant violated: serving(%) + hazards(%) <> total(%)', v_serving, v_hazard, v_total;
  END IF;
  IF v_d4flag <> 0 THEN
    RAISE EXCEPTION '031 transition incomplete: % row(s) still carry the d4-absent flag', v_d4flag;
  END IF;
  IF v_d5old <> 0 THEN
    RAISE EXCEPTION '031 transition incomplete: % row(s) still carry the old d5-absent flag', v_d5old;
  END IF;
  IF v_orphan <> 0 THEN
    RAISE NOTICE '031 WARNING: % orphan frame(s) with no style parent present (sandbox/prod baseline had 0)', v_orphan;
  END IF;
END $$;

COMMIT;
