-- Shared helper for current-state SQL RPC artifacts.
-- Exact routing for methods -1,0,1,2,3,4,5,6,7,9,10.
-- Method 8 remains reserved or unsupported until a GFPU cascade source is
-- explicitly carried in the request contract.

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