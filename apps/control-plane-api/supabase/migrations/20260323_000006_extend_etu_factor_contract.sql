-- Extend the ETU SQL RPC contract with explicit factor inputs so methods
-- 2/3/5/6 can be reconstructed exactly instead of falling back to base scaling.
--
-- Exact support after this migration:
--   -1 NONE
--    0 SENSORFRAME
--    1 PLUGTAP
--    2 SENSORFRAME_MULT
--    3 PLUGTAP_MULT
--    4 LTPU cascade
--    5 SENSORFRAME_C
--    6 PLUGTAP_C
--    7 AMPS
--    9 MULTWTH (current Python semantics: sensorframe-equivalent)
--   10 STPU cascade
--
-- Remaining unsupported method:
--    8 GFPU reserved cascade source is still not represented in the request contract.

DROP FUNCTION IF EXISTS public.fn_calc_etu_pickup_current(integer, numeric, numeric, numeric, numeric, numeric);
DROP FUNCTION IF EXISTS public.fn_calculate_test_currents(integer, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, boolean);
DROP FUNCTION IF EXISTS public.fn_evaluate_test_results(integer, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, numeric, boolean);

CREATE OR REPLACE FUNCTION public.fn_calc_etu_pickup_current(
    p_calc_method integer,
    p_setting numeric,
    p_sensor_rating numeric,
    p_plug_rating numeric,
    p_ltpu_current numeric DEFAULT NULL,
    p_stpu_current numeric DEFAULT NULL,
    p_multiplier_value numeric DEFAULT NULL,
    p_c_factor numeric DEFAULT NULL
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $function$
    SELECT CASE
        WHEN p_setting IS NULL OR p_calc_method IS NULL OR p_calc_method = -1 THEN NULL
        WHEN p_calc_method = 0 THEN p_setting * p_sensor_rating
        WHEN p_calc_method = 1 THEN p_setting * p_plug_rating
        WHEN p_calc_method = 2 THEN p_setting * p_sensor_rating * COALESCE(p_multiplier_value, 1)
        WHEN p_calc_method = 3 THEN p_setting * p_plug_rating * COALESCE(p_multiplier_value, 1)
        WHEN p_calc_method = 4 THEN CASE
            WHEN p_ltpu_current IS NULL THEN NULL
            ELSE p_setting * p_ltpu_current
        END
        WHEN p_calc_method = 5 THEN p_setting * p_sensor_rating * COALESCE(p_c_factor, 1)
        WHEN p_calc_method = 6 THEN p_setting * p_plug_rating * COALESCE(p_c_factor, 1)
        WHEN p_calc_method = 7 THEN p_setting
        WHEN p_calc_method = 8 THEN NULL
        WHEN p_calc_method = 9 THEN p_setting * p_sensor_rating
        WHEN p_calc_method = 10 THEN CASE
            WHEN p_stpu_current IS NULL THEN NULL
            ELSE p_setting * p_stpu_current
        END
        ELSE p_setting * p_plug_rating
    END
$function$;

COMMENT ON FUNCTION public.fn_calc_etu_pickup_current(integer, numeric, numeric, numeric, numeric, numeric, numeric, numeric)
IS 'Method-aware ETU pickup routing helper for SQL RPC functions. Exact for methods -1,0,1,2,3,4,5,6,7,9,10; method 8 remains reserved or unsupported.';

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

  IF ltpu_test_i IS NOT NULL AND p_ltd_multiplier IS NOT NULL THEN ltd_test_i := ltpu_test_i * p_ltd_multiplier; END IF;
  IF stpu_test_i IS NOT NULL AND p_std_multiplier IS NOT NULL THEN std_test_i := stpu_test_i * p_std_multiplier; END IF;
  IF gfpu_test_i IS NOT NULL AND p_gfd_multiplier IS NOT NULL THEN gfd_test_i := gfpu_test_i * p_gfd_multiplier; END IF;

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

  eff_inst_tol_lo := COALESCE(ctx.inst_ovrtol_min, -10);
  eff_inst_tol_hi := COALESCE(ctx.inst_ovrtol_max, 10);
  eff_gfpu_tol_lo := COALESCE(ctx.gfpu_tol_lo, -10);
  eff_gfpu_tol_hi := COALESCE(ctx.gfpu_tol_hi, 10);

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
    inst_lo := inst_test_i * (1 + eff_inst_tol_lo / 100.0);
    inst_hi := inst_test_i * (1 + eff_inst_tol_hi / 100.0);
  END IF;

  gfpu_test_i := public.fn_calc_etu_pickup_current(
    eff_gfpu_calc, p_gfpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, stpu_test_i, p_multiplier_value, p_c_factor
  );
  IF gfpu_test_i IS NOT NULL THEN
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