-- =============================================================================
-- Decision-012 - Phase 4a: repoint final DB object bodies to tcc.*.
-- Reversible CREATE OR REPLACE only. No drops, no table changes.
-- =============================================================================

BEGIN;

DO $$
DECLARE
  missing text[] := ARRAY[]::text[];
BEGIN
  IF to_regprocedure('public.fn_calculate_test_currents(integer,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,boolean)') IS NULL THEN
    missing := missing || 'public.fn_calculate_test_currents';
  END IF;
  IF to_regprocedure('public.fn_sensor_available_settings(integer)') IS NULL THEN
    missing := missing || 'public.fn_sensor_available_settings';
  END IF;
  IF to_regclass('public.vw_trip_unit_cascade') IS NULL THEN
    missing := missing || 'public.vw_trip_unit_cascade';
  END IF;
  IF to_regclass('tcc.etu_stpu_overrides') IS NULL THEN missing := missing || 'tcc.etu_stpu_overrides'; END IF;
  IF to_regclass('tcc.etu_sensors') IS NULL THEN missing := missing || 'tcc.etu_sensors'; END IF;
  IF to_regclass('tcc.etu_plugs') IS NULL THEN missing := missing || 'tcc.etu_plugs'; END IF;
  IF to_regclass('tcc.etu_ltd_bands') IS NULL THEN missing := missing || 'tcc.etu_ltd_bands'; END IF;
  IF to_regclass('tcc.etu_ltpu_pickups') IS NULL THEN missing := missing || 'tcc.etu_ltpu_pickups'; END IF;
  IF to_regclass('tcc.etu_ltpu_multipliers') IS NULL THEN missing := missing || 'tcc.etu_ltpu_multipliers'; END IF;
  IF to_regclass('tcc.etu_stpu_pickups') IS NULL THEN missing := missing || 'tcc.etu_stpu_pickups'; END IF;
  IF to_regclass('tcc.etu_inst_pickups') IS NULL THEN missing := missing || 'tcc.etu_inst_pickups'; END IF;
  IF to_regclass('tcc.etu_gfpu_pickups') IS NULL THEN missing := missing || 'tcc.etu_gfpu_pickups'; END IF;
  IF to_regclass('tcc.trip_types') IS NULL THEN missing := missing || 'tcc.trip_types'; END IF;

  IF array_length(missing, 1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: missing required Phase 4a object(s): %', array_to_string(missing, ', ');
  END IF;
END $$;

CREATE OR REPLACE FUNCTION public.fn_calculate_test_currents(p_sensor_id integer, p_plug_rating numeric, p_ltpu_setting numeric DEFAULT NULL::numeric, p_ltd_multiplier numeric DEFAULT 3, p_stpu_setting numeric DEFAULT NULL::numeric, p_std_multiplier numeric DEFAULT 1.5, p_inst_setting numeric DEFAULT NULL::numeric, p_gfpu_setting numeric DEFAULT NULL::numeric, p_gfd_multiplier numeric DEFAULT 1.5, p_multiplier_value numeric DEFAULT NULL::numeric, p_c_factor numeric DEFAULT NULL::numeric, p_maint_mode boolean DEFAULT false)
 RETURNS json
 LANGUAGE plpgsql
 STABLE
AS $function$
DECLARE
  ctx RECORD;
  ovr RECORD;
  override_applied BOOLEAN := false;
  override_amps NUMERIC;
  override_tol_lo NUMERIC;
  override_tol_hi NUMERIC;
  override_open_sec NUMERIC;
  override_clear_sec NUMERIC;
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
  std_supported BOOLEAN;
  gfd_supported BOOLEAN;
  warnings TEXT[] := '{}';
  result JSON;
BEGIN
  SELECT * INTO ctx FROM vw_sensor_calc_context WHERE sensor_id = p_sensor_id;
  IF NOT FOUND THEN
    RETURN json_build_object('error', 'Sensor not found', 'sensor_id', p_sensor_id);
  END IF;

  -- Load STPU override (post-Step-3B flat shape; one row per override-bearing
  -- sensor with non-NULL ovr_amps). On no-row, ovr fields are NULL and the
  -- override branch stays inactive.
  SELECT
      o.ovr_amps, o.ovr_clear_sec, o.ovr_open_sec,
      o.ovr_toler_high_pct, o.ovr_toler_low_pct
    INTO ovr
    FROM tcc.etu_stpu_overrides o
   WHERE o.sensor_id = p_sensor_id;
  override_applied := (ovr.ovr_amps IS NOT NULL);
  IF override_applied THEN
    override_amps     := ovr.ovr_amps;
    override_tol_lo   := ovr.ovr_toler_low_pct;
    override_tol_hi   := ovr.ovr_toler_high_pct;
    override_open_sec := ovr.ovr_open_sec;
    override_clear_sec:= ovr.ovr_clear_sec;
  END IF;

  -- Normal-mode INST band reads DS4_TOL_LOW/HIGH (inst_tol_lo/hi), matching the Python calc engine.
  -- The former ovrtol_min/max columns are INST-override tolerance and must not be used as the
  -- normal-mode band source. MAINT override branch below preserves its existing precedence.
  eff_inst_tol_lo := COALESCE(ctx.inst_tol_lo, -10);
  eff_inst_tol_hi := COALESCE(ctx.inst_tol_hi, 10);
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

  -- Delay-routing dispatch support: NONE (0), I2X (1), and INVEQ (2) are
  -- supported. TUSTD (3) and TUG (4) remain unsupported in the SQL payload.
  std_supported := (ctx.stpu_delay_calc_code IS NULL) OR (ctx.stpu_delay_calc_code IN (0, 1, 2));
  gfd_supported := (ctx.ground_delay_calc_code IS NULL) OR (ctx.ground_delay_calc_code IN (0, 1, 2));

  IF NOT std_supported THEN
    warnings := array_append(
      warnings,
      format(
        'STD delay routing code %s (%s) is stored on this sensor but has no solver path in this build; SQL output reports the stored code without dispatching to its solver',
        ctx.stpu_delay_calc_code, fn_etu_delay_calc_name(ctx.stpu_delay_calc_code)
      )
    );
  END IF;
  IF NOT gfd_supported THEN
    warnings := array_append(
      warnings,
      format(
        'GFD delay routing code %s (%s) is stored on this sensor but has no solver path in this build; SQL output reports the stored code without dispatching to its solver',
        ctx.ground_delay_calc_code, fn_etu_delay_calc_name(ctx.ground_delay_calc_code)
      )
    );
  END IF;

  -- PICKUP ELEMENTS
  ltpu_test_i := public.fn_calc_etu_pickup_current(
    eff_ltpu_calc, p_ltpu_setting, ctx.rating, p_plug_rating, NULL, NULL, p_multiplier_value, p_c_factor
  );
  IF ltpu_test_i IS NOT NULL THEN
    ltpu_test_i := ltpu_test_i * ltpu_reduction;
  END IF;

  IF override_applied THEN
    -- DLL CBreakerOverride Constant-mode: fixed amps from DatSection3STOvr.
    -- Override bypasses the normal stpu_calc path AND the MAINT reduction
    -- factor (mirrors ETUPickupCalculator.calculate / _build_override_stpu_result).
    stpu_test_i := override_amps;
    IF p_maint_mode AND maint_capable AND ctx.maint_stpu_reduction IS NOT NULL THEN
      warnings := array_append(
        warnings,
        'STPU override active — MAINT reduction factor not applied to override amps'
      );
    END IF;
  ELSE
    stpu_test_i := public.fn_calc_etu_pickup_current(
      eff_stpu_calc, p_stpu_setting, ctx.rating, p_plug_rating, ltpu_test_i, NULL, p_multiplier_value, p_c_factor
    );
    IF stpu_test_i IS NOT NULL THEN
      stpu_test_i := stpu_test_i * stpu_reduction;
    END IF;
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

    'stpu', CASE WHEN stpu_test_i IS NOT NULL THEN
      CASE WHEN override_applied THEN
        json_build_object(
          'setting', p_stpu_setting, 'test_current', ROUND(stpu_test_i, 2), 'test_multiplier', 1,
          'reduction', 1,
          'tol_lo_pct', COALESCE(override_tol_lo, 0), 'tol_hi_pct', COALESCE(override_tol_hi, 0),
          'limit_low',  ROUND(stpu_test_i * (1 + COALESCE(override_tol_lo, 0) / 100.0), 2),
          'limit_high', ROUND(stpu_test_i * (1 + COALESCE(override_tol_hi, 0) / 100.0), 2),
          'calc_method', 7,
          'method_name', 'OVERRIDE',
          'delay_calc_code', ctx.stpu_delay_calc_code,
          'delay_calc_name', fn_etu_delay_calc_name(ctx.stpu_delay_calc_code),
          'maint_mode', p_maint_mode AND maint_capable AND ctx.maint_stpu_reduction IS NOT NULL,
          'override_applied', true,
          'override_amps', override_amps,
          'override_open_time', override_open_sec,
          'override_clear_time', override_clear_sec
        )
      ELSE
        json_build_object(
          'setting', p_stpu_setting, 'test_current', ROUND(stpu_test_i, 2), 'test_multiplier', 1,
          'reduction', stpu_reduction,
          'tol_lo_pct', COALESCE(ctx.stpu_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.stpu_tol_hi, 10),
          'limit_low',  ROUND(stpu_test_i * (1 + COALESCE(ctx.stpu_tol_lo, -10) / 100.0), 2),
          'limit_high', ROUND(stpu_test_i * (1 + COALESCE(ctx.stpu_tol_hi,  10) / 100.0), 2),
          'calc_method', eff_stpu_calc,
          'delay_calc_code', ctx.stpu_delay_calc_code,
          'delay_calc_name', fn_etu_delay_calc_name(ctx.stpu_delay_calc_code),
          'maint_mode', p_maint_mode AND maint_capable,
          'override_applied', false
        )
      END
    ELSE NULL END,

    'std', CASE WHEN std_test_i IS NOT NULL THEN json_build_object(
      'test_current', ROUND(std_test_i, 2), 'test_multiplier', p_std_multiplier,
      'tol_lo_pct', COALESCE(ctx.stpu_tol_lo, -10), 'tol_hi_pct', COALESCE(ctx.stpu_tol_hi, 10),
      'limit_low', ROUND(std_test_i * (1 + COALESCE(ctx.stpu_tol_lo, -10) / 100.0), 2),
      'limit_high', ROUND(std_test_i * (1 + COALESCE(ctx.stpu_tol_hi, 10) / 100.0), 2),
      'delay_calc_code', ctx.stpu_delay_calc_code,
      'delay_calc_name', fn_etu_delay_calc_name(ctx.stpu_delay_calc_code),
      'delay_variant_code', ctx.stpu_i2t_type,
      'delay_setting_value', ctx.stpu_i2t_val,
      'delay_supported', std_supported,
      'maint_mode', p_maint_mode AND maint_capable
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
      'delay_calc_code', ctx.ground_delay_calc_code,
      'delay_calc_name', fn_etu_delay_calc_name(ctx.ground_delay_calc_code),
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END,

    'gfd', CASE WHEN gfd_test_i IS NOT NULL THEN json_build_object(
      'test_current', ROUND(gfd_test_i, 2), 'test_multiplier', p_gfd_multiplier,
      'tol_lo_pct', eff_gfpu_tol_lo, 'tol_hi_pct', eff_gfpu_tol_hi,
      'limit_low', ROUND(gfd_test_i * (1 + eff_gfpu_tol_lo / 100.0), 2),
      'limit_high', ROUND(gfd_test_i * (1 + eff_gfpu_tol_hi / 100.0), 2),
      'delay_calc_code', ctx.ground_delay_calc_code,
      'delay_calc_name', fn_etu_delay_calc_name(ctx.ground_delay_calc_code),
      'delay_variant_code', ctx.gfpu_i2t_type,
      'delay_setting_value', ctx.gfpu_i2t_val,
      'delay_supported', gfd_supported,
      'maint_mode', p_maint_mode AND maint_capable
    ) ELSE NULL END
  ) INTO result;

  RETURN result;
END;
$function$;

CREATE OR REPLACE FUNCTION public.fn_sensor_available_settings(p_sensor_id integer)
 RETURNS json
 LANGUAGE plpgsql
 STABLE
AS $function$
DECLARE
    v_trip_style_id integer;
    v_plug_values json := '[]'::json;
    v_ltd_settings json := '[]'::json;
BEGIN
    SELECT trip_style_id
    INTO v_trip_style_id
    FROM tcc.etu_sensors
    WHERE id = p_sensor_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'tcc'
          AND table_name = 'etu_plugs'
          AND column_name = 'sensor_id'
    ) THEN
        EXECUTE $sql$
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT value
                FROM tcc.etu_plugs
                WHERE sensor_id = $1
                  AND value IS NOT NULL
            ) plugs
        $sql$
        INTO v_plug_values
        USING p_sensor_id;
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'tcc'
          AND table_name = 'etu_plugs'
          AND column_name = 'trip_style_id'
    ) THEN
        EXECUTE $sql$
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT value
                FROM tcc.etu_plugs
                WHERE trip_style_id = $1
                  AND value IS NOT NULL
            ) plugs
        $sql$
        INTO v_plug_values
        USING v_trip_style_id;
    END IF;

    SELECT COALESCE(
        json_agg(
            json_build_object(
                'band', band,
                'label', label,
                'open_time', open_time,
                'clear_time', clear_time,
                'is_default', false
            )
            ORDER BY open_time
        ),
        '[]'::json
    )
    INTO v_ltd_settings
    FROM (
        SELECT DISTINCT
            COALESCE(ltd_desc, ltd_setting::text) AS band,
            COALESCE(ltd_desc, ltd_setting::text) AS label,
            ltd_setting::numeric AS open_time,
            NULL::numeric AS clear_time
        FROM tcc.etu_ltd_bands
        WHERE sensor_id = p_sensor_id
          AND ltd_setting IS NOT NULL
    ) ltd;

    RETURN json_build_object(
        'sensor_id', p_sensor_id,
        'plug_values', COALESCE(v_plug_values, '[]'::json),
        'ltpu_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT ltd_setting AS value
                FROM tcc.etu_ltpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND ltd_setting IS NOT NULL
            ) src
        ),
        'ltd_settings', COALESCE(v_ltd_settings, '[]'::json),
        'ltd_multipliers', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT ltd_c AS value
                FROM tcc.etu_ltpu_multipliers
                WHERE sensor_id = p_sensor_id
                  AND ltd_c IS NOT NULL
            ) src
        ),
        'stpu_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT stp_setting AS value
                FROM tcc.etu_stpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND stp_setting IS NOT NULL
            ) src
        ),
        'inst_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT ip_setting AS value
                FROM tcc.etu_inst_pickups
                WHERE sensor_id = p_sensor_id
                  AND ip_setting IS NOT NULL
            ) src
        ),
        'gfpu_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT gfp_setting AS value
                FROM tcc.etu_gfpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND gfp_setting IS NOT NULL
            ) src
        )
    );
END;
$function$;

CREATE OR REPLACE VIEW public.vw_trip_unit_cascade AS
 SELECT m.id AS manufacturer_id,
    m.mfr_name AS manufacturer_name,
    tt.id AS trip_type_id,
    tt.name AS trip_type_name,
    ts.id AS trip_style_id,
    ts.style AS trip_style_name,
    ts.tcc_no AS tcc_number,
    s.id AS sensor_id,
    s.rating AS sensor_rating,
    s.description AS sensor_desc,
    s.sensor_idx,
    s.ltpu_calc IS NOT NULL AND s.ltpu_calc <> '-1'::integer AS has_ltpu,
    s.stpu_calc IS NOT NULL AND s.stpu_calc <> '-1'::integer AS has_stpu,
    s.inst_calc IS NOT NULL AND s.inst_calc <> '-1'::integer AS has_inst,
    s.gfpu_calc IS NOT NULL AND s.gfpu_calc <> '-1'::integer AS has_gfpu,
    s.ltpu_calc,
    s.stpu_calc,
    s.inst_calc,
    s.gfpu_calc
   FROM tcc.manufacturers m
     JOIN tcc.trip_styles ts ON ts.mfg_id = m.id
     JOIN tcc.etu_sensors s ON s.trip_style_id = ts.id
     LEFT JOIN tcc.trip_types tt ON tt.manufacturer_id = m.id AND tt.name::text = ts.type::text;

DO $$
DECLARE
  old_ref_count integer;
  restored_count integer;
BEGIN
  SELECT count(*) INTO old_ref_count
  FROM (
    SELECT pg_get_functiondef('public.fn_calculate_test_currents(integer,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,boolean)'::regprocedure) AS body
    UNION ALL
    SELECT pg_get_functiondef('public.fn_sensor_available_settings(integer)'::regprocedure)
    UNION ALL
    SELECT pg_get_viewdef('public.vw_trip_unit_cascade'::regclass, true)
  ) bodies
  WHERE body LIKE '%public.tcc\_etu\_%' ESCAPE '\'
     OR body LIKE '%tcc\_etu\_plugs%' ESCAPE '\'
     OR body LIKE '%tcc\_manufacturers\_pre\_rebuild%' ESCAPE '\';

  IF old_ref_count <> 0 THEN
    RAISE EXCEPTION 'ABORT: Phase 4a repoint guard found % old reference-bearing object(s).', old_ref_count;
  END IF;

  SELECT count(*) INTO restored_count
  FROM public.vw_trip_unit_cascade
  WHERE sensor_id = 29442
    AND trip_type_id = 531
    AND trip_type_name = 'NA';

  IF restored_count <> 1 THEN
    RAISE EXCEPTION 'ABORT: expected sensor 29442 to resolve trip type 531 / NA, found % row(s).', restored_count;
  END IF;
END $$;

COMMIT;
