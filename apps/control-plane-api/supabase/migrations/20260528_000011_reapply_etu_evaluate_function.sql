-- ============================================================================
-- Reapply ETU Evaluate SQL Function
-- ============================================================================
-- Purpose:
--   Replace any stale live fn_evaluate_test_results() variant with the
--   repo-owned factor-contract implementation already captured in
--   20260323_000006_extend_etu_factor_contract.sql.
--
-- Scope:
--   This migration updates only fn_evaluate_test_results(). The active
--   runtime still evaluates pickup pass/fail in Python, but this reapply keeps
--   the live SQL surface aligned for direct validation and future cutback.
-- ============================================================================

CREATE OR REPLACE FUNCTION public.fn_evaluate_test_results(
    p_sensor_id     integer,
    p_plug_rating   numeric,
    p_ltpu_setting  numeric DEFAULT NULL,
    p_stpu_setting  numeric DEFAULT NULL,
    p_inst_setting  numeric DEFAULT NULL,
    p_gfpu_setting  numeric DEFAULT NULL,
    p_multiplier_value numeric DEFAULT NULL,
    p_c_factor numeric DEFAULT NULL,
    p_ltpu_measured numeric DEFAULT NULL,
    p_stpu_measured numeric DEFAULT NULL,
    p_inst_measured numeric DEFAULT NULL,
    p_gfpu_measured numeric DEFAULT NULL,
    p_ltd_trip_time numeric DEFAULT NULL,
    p_std_trip_time numeric DEFAULT NULL,
    p_gfd_trip_time numeric DEFAULT NULL,
    p_maint_mode    boolean DEFAULT false
)
RETURNS json
LANGUAGE plpgsql
STABLE
AS $function$
DECLARE
  ctx RECORD;
  eff_inst_tol_lo NUMERIC;
  eff_inst_tol_hi NUMERIC;
  eff_gfpu_tol_lo NUMERIC;
  eff_gfpu_tol_hi NUMERIC;
  ltpu_reduction NUMERIC := 1.0;
  stpu_reduction NUMERIC := 1.0;
  ltpu_test_i NUMERIC;
  stpu_test_i NUMERIC;
  inst_test_i NUMERIC;
  gfpu_test_i NUMERIC;
  ltpu_lo NUMERIC; ltpu_hi NUMERIC;
  stpu_lo NUMERIC; stpu_hi NUMERIC;
  inst_lo NUMERIC; inst_hi NUMERIC;
  gfpu_lo NUMERIC; gfpu_hi NUMERIC;
  maint_capable BOOLEAN := false;
  eff_ltpu_calc INT;
  eff_stpu_calc INT;
  eff_inst_calc INT;
  eff_gfpu_calc INT;
  warnings TEXT[] := '{}';
  result JSON;
BEGIN
  SELECT * INTO ctx
  FROM vw_sensor_calc_context
  WHERE sensor_id = p_sensor_id;

  IF NOT FOUND THEN
    RETURN json_build_object('error', 'Sensor not found');
  END IF;

  -- Pickup tolerances are per-device manufacturer data (DS4_TOL_LOW/HIGH ->
  -- inst_tol_lo/hi, DS1GF_TOL_LOW/HIGH -> gfpu_tol_lo/hi). Per NETA the general
  -- +/-10% applies ONLY in the absence of manufacturer data; we have that data,
  -- so the band is read straight from the tables with NO numeric default.
  -- Invariant (verified across the full 17,831-row DatSensor catalog): a present
  -- element always carries its tolerance -- tolerance is NULL only where
  -- PICKUP_CALC = -1 (element absent), which the calc gate below skips entirely.
  -- inst_ovrtol_min/max remain the separate override-only band, not used here.
  eff_inst_tol_lo := ctx.inst_tol_lo;
  eff_inst_tol_hi := ctx.inst_tol_hi;
  eff_gfpu_tol_lo := ctx.gfpu_tol_lo;
  eff_gfpu_tol_hi := ctx.gfpu_tol_hi;

  IF p_maint_mode THEN
    maint_capable := COALESCE(ctx.maint_capable, false);

    IF NOT maint_capable THEN
      warnings := array_append(warnings, 'Sensor does not have maintenance mode data — using normal calculations');
    ELSE
      ltpu_reduction := COALESCE(ctx.maint_ltpu_reduction, 1.0);
      stpu_reduction := COALESCE(ctx.maint_stpu_reduction, 1.0);
      IF ctx.maint_ltpu_reduction IS NULL AND ctx.maint_stpu_reduction IS NULL THEN
        warnings := array_append(warnings, 'LTPU/STPU reduction factors not available — defaulting to 1.0 (partial MAINT support: INST/GFPU only)');
      END IF;

      IF ctx.maint_inst_calc IS NOT NULL AND ctx.maint_inst_calc != -1 THEN
        eff_inst_tol_lo := COALESCE(ctx.maint_inst_tol_lo, eff_inst_tol_lo);
        eff_inst_tol_hi := COALESCE(ctx.maint_inst_tol_hi, eff_inst_tol_hi);
      END IF;

      IF ctx.maint_gfpu_calc IS NOT NULL AND ctx.maint_gfpu_calc != -1 THEN
        eff_gfpu_tol_lo := COALESCE(ctx.maint_gfpu_tol_lo, eff_gfpu_tol_lo);
        eff_gfpu_tol_hi := COALESCE(ctx.maint_gfpu_tol_hi, eff_gfpu_tol_hi);
      END IF;
    END IF;
  END IF;

  eff_ltpu_calc := COALESCE(ctx.ltpu_calc, -1);
  eff_stpu_calc := COALESCE(ctx.stpu_calc, -1);
  eff_inst_calc := COALESCE(ctx.maint_inst_calc, ctx.inst_calc, -1);
  eff_gfpu_calc := COALESCE(ctx.maint_gfpu_calc, ctx.gfpu_calc, -1);

  IF p_ltpu_setting IS NOT NULL AND eff_ltpu_calc = 8 THEN
    warnings := array_append(warnings, 'LTPU calc method 8 requires a GFPU cascade source that is not represented in the SQL RPC contract');
  END IF;
  IF p_stpu_setting IS NOT NULL AND eff_stpu_calc = 8 THEN
    warnings := array_append(warnings, 'STPU calc method 8 requires a GFPU cascade source that is not represented in the SQL RPC contract');
  END IF;
  IF p_inst_setting IS NOT NULL AND eff_inst_calc = 8 THEN
    warnings := array_append(warnings, 'INST calc method 8 requires a GFPU cascade source that is not represented in the SQL RPC contract');
  END IF;
  IF p_gfpu_setting IS NOT NULL AND eff_gfpu_calc = 8 THEN
    warnings := array_append(warnings, 'GFPU calc method 8 requires a GFPU cascade source that is not represented in the SQL RPC contract');
  END IF;

  ltpu_test_i := public.fn_calc_etu_pickup_current(
    eff_ltpu_calc, p_ltpu_setting, ctx.rating, p_plug_rating, NULL, NULL, p_multiplier_value, p_c_factor
  );
  IF ltpu_test_i IS NOT NULL THEN
    ltpu_test_i := ltpu_test_i * ltpu_reduction;
    ltpu_lo := ltpu_test_i * (1 + COALESCE(ctx.ltpu_tol_lo, -10) / 100.0);
    ltpu_hi := ltpu_test_i * (1 + COALESCE(ctx.ltpu_tol_hi, 10) / 100.0);
  END IF;

  stpu_test_i := public.fn_calc_etu_pickup_current(
    eff_stpu_calc, p_stpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, NULL, p_multiplier_value, p_c_factor
  );
  IF stpu_test_i IS NOT NULL THEN
    stpu_test_i := stpu_test_i * stpu_reduction;
    stpu_lo := stpu_test_i * (1 + COALESCE(ctx.stpu_tol_lo, -10) / 100.0);
    stpu_hi := stpu_test_i * (1 + COALESCE(ctx.stpu_tol_hi, 10) / 100.0);
  END IF;

  inst_test_i := public.fn_calc_etu_pickup_current(
    eff_inst_calc, p_inst_setting, ctx.rating, p_plug_rating, ltpu_test_i, stpu_test_i, p_multiplier_value, p_c_factor
  );
  IF inst_test_i IS NOT NULL THEN
    IF eff_inst_tol_lo IS NULL OR eff_inst_tol_hi IS NULL THEN
      warnings := array_append(warnings, 'INST element is active but carries no manufacturer tolerance in source data (band indeterminate; no default applied)');
    END IF;
    inst_lo := inst_test_i * (1 + eff_inst_tol_lo / 100.0);
    inst_hi := inst_test_i * (1 + eff_inst_tol_hi / 100.0);
  END IF;

  gfpu_test_i := public.fn_calc_etu_pickup_current(
    eff_gfpu_calc, p_gfpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, stpu_test_i, p_multiplier_value, p_c_factor
  );
  IF gfpu_test_i IS NOT NULL THEN
    IF eff_gfpu_tol_lo IS NULL OR eff_gfpu_tol_hi IS NULL THEN
      warnings := array_append(warnings, 'GFPU element is active but carries no manufacturer tolerance in source data (band indeterminate; no default applied)');
    END IF;
    gfpu_lo := gfpu_test_i * (1 + eff_gfpu_tol_lo / 100.0);
    gfpu_hi := gfpu_test_i * (1 + eff_gfpu_tol_hi / 100.0);
  END IF;

  SELECT json_build_object(
    'sensor_id', p_sensor_id,
    'manufacturer', ctx.manufacturer_name,
    'trip_style', ctx.trip_style_name,
    'sensor_desc', ctx.sensor_desc,
    'maint_mode', p_maint_mode,
    'maint_capable', maint_capable,
    'maint_support_level', CASE
      WHEN NOT maint_capable THEN 'none'
      WHEN ctx.maint_ltpu_reduction IS NULL THEN 'partial_inst_gfpu'
      ELSE 'full'
    END,
    'warnings', to_json(warnings),

    'ltpu', CASE WHEN p_ltpu_measured IS NOT NULL AND ltpu_test_i IS NOT NULL THEN json_build_object(
      'expected', ROUND(ltpu_test_i, 2),
      'measured', p_ltpu_measured,
      'limit_low', ROUND(ltpu_lo, 2),
      'limit_high', ROUND(ltpu_hi, 2),
      'pass', (p_ltpu_measured >= ltpu_lo AND p_ltpu_measured <= ltpu_hi),
      'deviation_pct', ROUND((p_ltpu_measured - ltpu_test_i) / ltpu_test_i * 100, 2)
    ) ELSE NULL END,

    'stpu', CASE WHEN p_stpu_measured IS NOT NULL AND stpu_test_i IS NOT NULL THEN json_build_object(
      'expected', ROUND(stpu_test_i, 2),
      'measured', p_stpu_measured,
      'limit_low', ROUND(stpu_lo, 2),
      'limit_high', ROUND(stpu_hi, 2),
      'pass', (p_stpu_measured >= stpu_lo AND p_stpu_measured <= stpu_hi),
      'deviation_pct', ROUND((p_stpu_measured - stpu_test_i) / stpu_test_i * 100, 2)
    ) ELSE NULL END,

    'inst', CASE WHEN p_inst_measured IS NOT NULL AND inst_test_i IS NOT NULL THEN json_build_object(
      'expected', ROUND(inst_test_i, 2),
      'measured', p_inst_measured,
      'limit_low', ROUND(inst_lo, 2),
      'limit_high', ROUND(inst_hi, 2),
      'pass', (p_inst_measured >= inst_lo AND p_inst_measured <= inst_hi),
      'deviation_pct', ROUND((p_inst_measured - inst_test_i) / inst_test_i * 100, 2)
    ) ELSE NULL END,

    'gfpu', CASE WHEN p_gfpu_measured IS NOT NULL AND gfpu_test_i IS NOT NULL THEN json_build_object(
      'expected', ROUND(gfpu_test_i, 2),
      'measured', p_gfpu_measured,
      'limit_low', ROUND(gfpu_lo, 2),
      'limit_high', ROUND(gfpu_hi, 2),
      'pass', (p_gfpu_measured >= gfpu_lo AND p_gfpu_measured <= gfpu_hi),
      'deviation_pct', ROUND((p_gfpu_measured - gfpu_test_i) / gfpu_test_i * 100, 2)
    ) ELSE NULL END,

    'overall_pass', (
      (p_ltpu_measured IS NULL OR (p_ltpu_measured >= ltpu_lo AND p_ltpu_measured <= ltpu_hi)) AND
      (p_stpu_measured IS NULL OR (p_stpu_measured >= stpu_lo AND p_stpu_measured <= stpu_hi)) AND
      (p_inst_measured IS NULL OR (p_inst_measured >= inst_lo AND p_inst_measured <= inst_hi)) AND
      (p_gfpu_measured IS NULL OR (p_gfpu_measured >= gfpu_lo AND p_gfpu_measured <= gfpu_hi))
    )
  ) INTO result;

  RETURN result;
END;
$function$;

COMMENT ON FUNCTION public.fn_evaluate_test_results(integer, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, boolean)
IS 'ETU evaluate SQL RPC aligned to the factor-contract implementation in the tracked Supabase migration lane.';