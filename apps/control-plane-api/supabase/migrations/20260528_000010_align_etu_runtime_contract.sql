-- ============================================================================
-- ETU Runtime Contract Alignment
-- ============================================================================
-- Purpose:
--   Capture the 2026-05-28 ETU schema drift findings in the canonical forward
--   Supabase lane and add compatibility surfaces for the current runtime path.
--
-- Scope:
--   1. reconcile tcc_etu_plugs with the runtime sensor-scoped lookup contract
--   2. add flat STPU override columns used by the live/runtime ETU path
--   3. annotate and index tcc_etu_sensor_params for flat sensor/section/curve/idx lookups
--   4. define a repo-owned fn_sensor_available_settings() using the same direct
--      ETU sources the FastAPI runtime now trusts
--
-- Important:
--   This migration is additive and guarded for the accepted live baseline.
--   It is not intended to replace the historical bootstrap schema in
--   migrations/001_tcc_schema.sql.
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'sensor_id'
    ) THEN
        ALTER TABLE public.tcc_etu_plugs
            ADD COLUMN sensor_id integer;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'sensor_id'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'trip_style_id'
    ) THEN
        ALTER TABLE public.tcc_etu_plugs
            DROP CONSTRAINT IF EXISTS tcc_etu_plugs_trip_style_id_value_key;

        INSERT INTO public.tcc_etu_plugs (trip_style_id, value, created_at, sensor_id)
        SELECT
            plugs.trip_style_id,
            plugs.value,
            plugs.created_at,
            sensors.id AS sensor_id
        FROM public.tcc_etu_plugs AS plugs
        INNER JOIN public.tcc_etu_sensors AS sensors
            ON sensors.trip_style_id = plugs.trip_style_id
        WHERE plugs.sensor_id IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM public.tcc_etu_plugs AS existing
              WHERE existing.sensor_id = sensors.id
                AND existing.value = plugs.value
          );
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'sensor_id'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND constraint_name = 'tcc_etu_plugs_sensor_id_fkey'
    ) THEN
        ALTER TABLE public.tcc_etu_plugs
            ADD CONSTRAINT tcc_etu_plugs_sensor_id_fkey
            FOREIGN KEY (sensor_id)
            REFERENCES public.tcc_etu_sensors(id)
            ON DELETE CASCADE
            NOT VALID;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tcc_etu_plugs_sensor_id
    ON public.tcc_etu_plugs (sensor_id);

CREATE INDEX IF NOT EXISTS idx_tcc_etu_plugs_sensor_value_lookup
    ON public.tcc_etu_plugs (sensor_id, value)
    WHERE sensor_id IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'trip_style_id'
    ) THEN
        EXECUTE $sql$
            CREATE INDEX IF NOT EXISTS idx_tcc_etu_plugs_legacy_trip_style_value_lookup
                ON public.tcc_etu_plugs (trip_style_id, value)
                WHERE sensor_id IS NULL
        $sql$;
    END IF;
END $$;

ALTER TABLE IF EXISTS public.tcc_etu_stpu_overrides
    ADD COLUMN IF NOT EXISTS ovr_amps numeric,
    ADD COLUMN IF NOT EXISTS ovr_clear_sec numeric,
    ADD COLUMN IF NOT EXISTS ovr_open_sec numeric,
    ADD COLUMN IF NOT EXISTS ovr_toler_high_pct numeric,
    ADD COLUMN IF NOT EXISTS ovr_toler_low_pct numeric;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_stpu_overrides'
          AND column_name = 'type'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_stpu_overrides'
          AND column_name = 'value'
    ) THEN
        WITH aggregated AS (
            SELECT
                sensor_id,
                MAX(CASE WHEN type = 'amps' THEN value END) AS ovr_amps,
                MAX(CASE WHEN type = 'clear_sec' THEN value END) AS ovr_clear_sec,
                MAX(CASE WHEN type = 'open_sec' THEN value END) AS ovr_open_sec,
                MAX(CASE WHEN type = 'tolerance_high' THEN value END) AS ovr_toler_high_pct,
                MAX(CASE WHEN type = 'tolerance_low' THEN value END) AS ovr_toler_low_pct
            FROM public.tcc_etu_stpu_overrides
            GROUP BY sensor_id
        )
        UPDATE public.tcc_etu_stpu_overrides AS target
        SET
            ovr_amps = COALESCE(target.ovr_amps, aggregated.ovr_amps),
            ovr_clear_sec = COALESCE(target.ovr_clear_sec, aggregated.ovr_clear_sec),
            ovr_open_sec = COALESCE(target.ovr_open_sec, aggregated.ovr_open_sec),
            ovr_toler_high_pct = COALESCE(target.ovr_toler_high_pct, aggregated.ovr_toler_high_pct),
            ovr_toler_low_pct = COALESCE(target.ovr_toler_low_pct, aggregated.ovr_toler_low_pct)
        FROM aggregated
        WHERE target.sensor_id = aggregated.sensor_id;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_tcc_etu_sensor_params_runtime_lookup
    ON public.tcc_etu_sensor_params (sensor_id, section, curve_id, idx);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_sensor_params'
          AND column_name = 'id'
    ) THEN
        COMMENT ON COLUMN public.tcc_etu_sensor_params.id IS
            'Legacy surrogate key retained for baseline compatibility; runtime ETU lookups resolve rows by sensor_id, section, curve_id, and idx.';
    END IF;
END $$;

COMMENT ON TABLE public.tcc_etu_stpu_overrides IS
    'ETU STPU override settings. Runtime contract prefers flat ovr_* columns; legacy type/value rows are preserved only for backfill compatibility.';

COMMENT ON TABLE public.tcc_etu_plugs IS
    'ETU plug ratings. Runtime contract prefers sensor-scoped lookup by sensor_id while preserving legacy trip_style_id lineage when present.';

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
    FROM public.tcc_etu_sensors
    WHERE id = p_sensor_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'sensor_id'
    ) THEN
        EXECUTE $sql$
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT value
                FROM public.tcc_etu_plugs
                WHERE sensor_id = $1
                  AND value IS NOT NULL
            ) plugs
        $sql$
        INTO v_plug_values
        USING p_sensor_id;
    ELSIF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tcc_etu_plugs'
          AND column_name = 'trip_style_id'
    ) THEN
        EXECUTE $sql$
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT value
                FROM public.tcc_etu_plugs
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
        FROM public.tcc_etu_ltd_bands
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
                FROM public.tcc_etu_ltpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND ltd_setting IS NOT NULL
            ) src
        ),
        'ltd_settings', COALESCE(v_ltd_settings, '[]'::json),
        'ltd_multipliers', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT ltd_c AS value
                FROM public.tcc_etu_ltpu_multipliers
                WHERE sensor_id = p_sensor_id
                  AND ltd_c IS NOT NULL
            ) src
        ),
        'stpu_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT stp_setting AS value
                FROM public.tcc_etu_stpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND stp_setting IS NOT NULL
            ) src
        ),
        'inst_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT ip_setting AS value
                FROM public.tcc_etu_inst_pickups
                WHERE sensor_id = p_sensor_id
                  AND ip_setting IS NOT NULL
            ) src
        ),
        'gfpu_settings', (
            SELECT COALESCE(json_agg(value ORDER BY value), '[]'::json)
            FROM (
                SELECT DISTINCT gfp_setting AS value
                FROM public.tcc_etu_gfpu_pickups
                WHERE sensor_id = p_sensor_id
                  AND gfp_setting IS NOT NULL
            ) src
        )
    );
END;
$function$;

COMMENT ON FUNCTION public.fn_sensor_available_settings(integer) IS
    'Runtime-aligned ETU settings loader. Returns direct sensor-scoped plug and pickup settings using the live ETU catalog contract and guarded legacy plug fallback when needed.';