-- fn_calculate_test_currents (current state after MAINT mode migrations)
--
-- Applied via Supabase migrations:
--   create_fn_calculate_test_currents
--   replace_fn_calculate_test_currents_with_maint_mode
--   fn_calculate_use_maint_capable
--
-- Key MAINT behavior:
--   Uses ctx.maint_capable (derived from data presence) NOT ctx.maint_available (runtime toggle)
--   Returns maint_support_level: 'none' | 'partial_inst_gfpu' | 'full'
--   Applies maint-specific INST/GFPU tolerances and reduction factors

CREATE OR REPLACE FUNCTION public.fn_calculate_test_currents(
    p_sensor_id    integer,
    p_plug_rating  numeric,
    p_ltpu_setting numeric DEFAULT NULL,
    p_ltd_multiplier numeric DEFAULT 3,
    p_stpu_setting numeric DEFAULT NULL,
    p_std_multiplier numeric DEFAULT 1.5,
    p_inst_setting numeric DEFAULT NULL,
    p_gfpu_setting numeric DEFAULT NULL,
    p_gfd_multiplier numeric DEFAULT 1.5,
    p_multiplier_value numeric DEFAULT NULL,
    p_c_factor numeric DEFAULT NULL,
    p_maint_mode   boolean DEFAULT false
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
  eff_inst_delay_opening NUMERIC;
  eff_inst_delay_clearing NUMERIC;
  ltpu_reduction NUMERIC := 1.0;
  stpu_reduction NUMERIC := 1.0;
  ltpu_test_i NUMERIC;
  ltd_test_i NUMERIC;
  stpu_test_i NUMERIC;
  std_test_i NUMERIC;
  inst_test_i NUMERIC;
  gfpu_test_i NUMERIC;
  gfd_test_i NUMERIC;
  maint_capable BOOLEAN := false;
  maint_inst_calc_used INT;
  maint_gfpu_calc_used INT;
  eff_ltpu_calc INT;
  eff_stpu_calc INT;
  eff_inst_calc INT;
  eff_gfpu_calc INT;
  warnings TEXT[] := '{}';
  result JSON;
BEGIN
  SELECT * INTO ctx FROM vw_sensor_calc_context WHERE sensor_id = p_sensor_id;
  IF NOT FOUND THEN
    RETURN json_build_object('error', 'Sensor not found', 'sensor_id', p_sensor_id);
  END IF;

  eff_inst_tol_lo := COALESCE(ctx.inst_ovrtol_min, -10);
  eff_inst_tol_hi := COALESCE(ctx.inst_ovrtol_max, 10);
  eff_gfpu_tol_lo := COALESCE(ctx.gfpu_tol_lo, -10);
  eff_gfpu_tol_hi := COALESCE(ctx.gfpu_tol_hi, 10);
  eff_inst_delay_opening := ctx.inst_delay_opening;
  eff_inst_delay_clearing := ctx.inst_delay_clearing;

  -- MAINT MODE: use maint_capable (derived from data presence), not maint_available (runtime toggle)
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
        eff_inst_delay_opening := COALESCE(ctx.maint_inst_delay_opening, eff_inst_delay_opening);
        eff_inst_delay_clearing := COALESCE(ctx.maint_inst_delay_clearing, eff_inst_delay_clearing);
        maint_inst_calc_used := ctx.maint_inst_calc;
      END IF;

      IF ctx.maint_gfpu_calc IS NOT NULL AND ctx.maint_gfpu_calc != -1 THEN
        eff_gfpu_tol_lo := COALESCE(ctx.maint_gfpu_tol_lo, eff_gfpu_tol_lo);
        eff_gfpu_tol_hi := COALESCE(ctx.maint_gfpu_tol_hi, eff_gfpu_tol_hi);
        maint_gfpu_calc_used := ctx.maint_gfpu_calc;
      END IF;
    END IF;
  END IF;

  eff_ltpu_calc := COALESCE(ctx.ltpu_calc, -1);
  eff_stpu_calc := COALESCE(ctx.stpu_calc, -1);
  eff_inst_calc := COALESCE(maint_inst_calc_used, ctx.inst_calc, -1);
  eff_gfpu_calc := COALESCE(maint_gfpu_calc_used, ctx.gfpu_calc, -1);

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

  -- PICKUP ELEMENTS
  ltpu_test_i := public.fn_calc_etu_pickup_current(
    eff_ltpu_calc, p_ltpu_setting, ctx.rating, p_plug_rating, NULL, NULL, p_multiplier_value, p_c_factor
  );
  IF ltpu_test_i IS NOT NULL THEN
    ltpu_test_i := ltpu_test_i * ltpu_reduction;
  END IF;

  stpu_test_i := public.fn_calc_etu_pickup_current(
    eff_stpu_calc, p_stpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, NULL, p_multiplier_value, p_c_factor
  );
  IF stpu_test_i IS NOT NULL THEN
    stpu_test_i := stpu_test_i * stpu_reduction;
  END IF;

  inst_test_i := public.fn_calc_etu_pickup_current(
    eff_inst_calc, p_inst_setting, ctx.rating, p_plug_rating, ltpu_test_i, stpu_test_i, p_multiplier_value, p_c_factor
  );

  gfpu_test_i := public.fn_calc_etu_pickup_current(
    eff_gfpu_calc, p_gfpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, stpu_test_i, p_multiplier_value, p_c_factor
  );

  -- DELAY ELEMENTS
  IF ltpu_test_i IS NOT NULL AND p_ltd_multiplier IS NOT NULL THEN ltd_test_i := ltpu_test_i * p_ltd_multiplier; END IF;
  IF stpu_test_i IS NOT NULL AND p_std_multiplier IS NOT NULL THEN std_test_i := stpu_test_i * p_std_multiplier; END IF;
  IF gfpu_test_i IS NOT NULL AND p_gfd_multiplier IS NOT NULL THEN gfd_test_i := gfpu_test_i * p_gfd_multiplier; END IF;

  -- BUILD RESULT
  SELECT json_build_object(
    'sensor_id', p_sensor_id,
    'plug_rating', p_plug_rating,
    'manufacturer', ctx.manufacturer_name,
    'trip_type', ctx.trip_type_name,
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

    'ltpu', CASE WHEN ltpu_test_i IS NOT NULL THEN json_build_object(
      'setting', p_ltpu_setting, 'test_current', ROUND(ltpu_test_i, 2), 'test_multiplier', 1,
      'reduction', ltpu_reduction,
      'tol_lo_pct', COALESCE(ctx.ltpu_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.ltpu_tol_hi, 10),
      'limit_low', ROUND(ltpu_test_i * (1 + COALESCE(ctx.ltpu_tol_lo, -10) / 100.0), 2),
      'limit_high', ROUND(ltpu_test_i * (1 + COALESCE(ctx.ltpu_tol_hi, 10) / 100.0), 2),
      'calc_method', eff_ltpu_calc, 'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'ltd', CASE WHEN ltd_test_i IS NOT NULL THEN json_build_object(
      'test_current', ROUND(ltd_test_i, 2), 'test_multiplier', p_ltd_multiplier,
      'tol_lo_pct', COALESCE(ctx.ltd_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.ltd_tol_hi, 10),
      'limit_low', ROUND(ltd_test_i * (1 + COALESCE(ctx.ltd_tol_lo, -10) / 100.0), 2),
      'limit_high', ROUND(ltd_test_i * (1 + COALESCE(ctx.ltd_tol_hi, 10) / 100.0), 2),
      'delay_method', ctx.ltd_func, 'setting_type', ctx.ltd_setting_type,
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'stpu', CASE WHEN stpu_test_i IS NOT NULL THEN json_build_object(
      'setting', p_stpu_setting, 'test_current', ROUND(stpu_test_i, 2), 'test_multiplier', 1,
      'reduction', stpu_reduction,
      'tol_lo_pct', COALESCE(ctx.stpu_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.stpu_tol_hi, 10),
      'limit_low', ROUND(stpu_test_i * (1 + COALESCE(ctx.stpu_tol_lo, -10) / 100.0), 2),
      'limit_high', ROUND(stpu_test_i * (1 + COALESCE(ctx.stpu_tol_hi, 10) / 100.0), 2),
      'calc_method', eff_stpu_calc, 'i2t_enabled', ctx.stpu_i2t,
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'std', CASE WHEN std_test_i IS NOT NULL THEN json_build_object(
      'test_current', ROUND(std_test_i, 2), 'test_multiplier', p_std_multiplier,
      'tol_lo_pct', COALESCE(ctx.stpu_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.stpu_tol_hi, 10),
      'limit_low', ROUND(std_test_i * (1 + COALESCE(ctx.stpu_tol_lo, -10) / 100.0), 2),
      'limit_high', ROUND(std_test_i * (1 + COALESCE(ctx.stpu_tol_hi, 10) / 100.0), 2),
      'i2t_type', ctx.stpu_i2t_type, 'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'inst', CASE WHEN inst_test_i IS NOT NULL THEN json_build_object(
      'setting', p_inst_setting, 'test_current', ROUND(inst_test_i, 2), 'test_multiplier', 1,
      'tol_lo_pct', eff_inst_tol_lo, 'tol_hi_pct', eff_inst_tol_hi,
      'limit_low', ROUND(inst_test_i * (1 + eff_inst_tol_lo / 100.0), 2),
      'limit_high', ROUND(inst_test_i * (1 + eff_inst_tol_hi / 100.0), 2),
      'calc_method', eff_inst_calc,
      'delay_opening', eff_inst_delay_opening, 'delay_clearing', eff_inst_delay_clearing,
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'gfpu', CASE WHEN gfpu_test_i IS NOT NULL THEN json_build_object(
      'setting', p_gfpu_setting, 'test_current', ROUND(gfpu_test_i, 2), 'test_multiplier', 1,
      'tol_lo_pct', eff_gfpu_tol_lo, 'tol_hi_pct', eff_gfpu_tol_hi,
      'limit_low', ROUND(gfpu_test_i * (1 + eff_gfpu_tol_lo / 100.0), 2),
      'limit_high', ROUND(gfpu_test_i * (1 + eff_gfpu_tol_hi / 100.0), 2),
      'calc_method', eff_gfpu_calc,
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'gfd', CASE WHEN gfd_test_i IS NOT NULL THEN json_build_object(
      'test_current', ROUND(gfd_test_i, 2), 'test_multiplier', p_gfd_multiplier,
      'tol_lo_pct', eff_gfpu_tol_lo, 'tol_hi_pct', eff_gfpu_tol_hi,
      'limit_low', ROUND(gfd_test_i * (1 + eff_gfpu_tol_lo / 100.0), 2),
      'limit_high', ROUND(gfd_test_i * (1 + eff_gfpu_tol_hi / 100.0), 2),
      'i2t_type', ctx.gfpu_i2t_type, 'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END
  ) INTO result;

  RETURN result;
END;
$function$;
