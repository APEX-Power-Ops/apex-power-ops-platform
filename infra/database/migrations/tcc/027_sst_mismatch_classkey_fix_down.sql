-- 027_sst_mismatch_classkey_fix_down.sql
-- =============================================================================
-- DOWN for 027 — restore the original BARE breaker_style_id partition.
-- This is the live pre-027 definition verbatim (captured via pg_get_viewdef).
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW tcc.vw_breaker_sst_mismatch AS
 SELECT breaker_class,
    breaker_style_id,
    tmt_sst_mfr,
    tmt_sst_type,
    tmt_sst_style,
    r_cont_current
   FROM ( SELECT vw_breaker_sst_bridge.breaker_class,
            vw_breaker_sst_bridge.breaker_style_id,
            vw_breaker_sst_bridge.tmt_sst_mfr,
            vw_breaker_sst_bridge.tmt_sst_type,
            vw_breaker_sst_bridge.tmt_sst_style,
            vw_breaker_sst_bridge.r_cont_current,
            bool_or(vw_breaker_sst_bridge.sensor_rating::numeric = vw_breaker_sst_bridge.r_cont_current) OVER (PARTITION BY vw_breaker_sst_bridge.breaker_style_id) AS resolves_exact
           FROM tcc.vw_breaker_sst_bridge) z
  WHERE NOT resolves_exact AND COALESCE(tmt_sst_mfr, ''::text) !~* 'eaton|cutler'::text AND NOT (EXISTS ( SELECT 1
           FROM tcc.bridge_nonsst n
          WHERE n.tmt_sst_mfr = z.tmt_sst_mfr AND n.tmt_sst_type = z.tmt_sst_type AND n.tmt_sst_style = z.tmt_sst_style))
  GROUP BY breaker_class, breaker_style_id, tmt_sst_mfr, tmt_sst_type, tmt_sst_style, r_cont_current;

COMMIT;
