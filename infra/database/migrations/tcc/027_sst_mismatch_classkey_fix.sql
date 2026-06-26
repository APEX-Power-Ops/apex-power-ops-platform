-- 027_sst_mismatch_classkey_fix.sql
-- =============================================================================
-- F-79-01 (HIGH) — #79 lvbreakertcc contract audit promotion.
-- PROD-BOUND, OPERATOR-GATED. Apply against governed Supabase tcc via the MCP
-- apply_migration, then this file is the version-controlled record (matches the
-- 026 convention).
--
-- BUG: tcc.vw_breaker_sst_mismatch partitions the resolves_exact window by the
-- BARE breaker_style_id. Per the TCC Master Reference a breaker style id is
-- unique only WITHIN a breaker_class (style ids collide across classes), so the
-- canonical key is (breaker_class, breaker_style_id). With the bare key, an
-- exact-rating match in ANOTHER class can mark a row resolves_exact and suppress
-- a genuine mismatch — hiding rows from the diagnostic.
--
-- SOURCE: codex #79 sandbox audit finding F-79-01, CC-verified independently on
-- the read-only sandbox viewer (the live view IS bare-keyed; pre-fix count = 8).
-- This packet is the MINIMAL-DIFF promotion: the live view definition verbatim
-- with ONLY the PARTITION BY clause changed (bare -> class+style). The sandbox
-- self-check's hardcoded "= 53" is NOT promoted; counts are observed live below.
--
-- PREFLIGHT (run read-only FIRST and record the number for the change log):
--   SELECT count(*) AS before_bare_key FROM tcc.vw_breaker_sst_mismatch;
--
-- GUARD: class-keying makes the partition strictly finer, so the mismatch count
-- can only stay equal or rise. The migration aborts (RAISE EXCEPTION) if the
-- post-count drops below the pre-count — a count-free logical invariant, not a
-- hardcoded snapshot value.
--
-- REVERSIBLE: 027_sst_mismatch_classkey_fix_down.sql restores the bare-key view.
-- =============================================================================

BEGIN;

-- Capture the live pre-fix (bare-key) count before replacing the view.
CREATE TEMP TABLE _f79_01_before ON COMMIT DROP AS
  SELECT count(*)::int AS cnt FROM tcc.vw_breaker_sst_mismatch;

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
            bool_or(vw_breaker_sst_bridge.sensor_rating::numeric = vw_breaker_sst_bridge.r_cont_current) OVER (PARTITION BY vw_breaker_sst_bridge.breaker_class, vw_breaker_sst_bridge.breaker_style_id) AS resolves_exact
           FROM tcc.vw_breaker_sst_bridge) z
  WHERE NOT resolves_exact AND COALESCE(tmt_sst_mfr, ''::text) !~* 'eaton|cutler'::text AND NOT (EXISTS ( SELECT 1
           FROM tcc.bridge_nonsst n
          WHERE n.tmt_sst_mfr = z.tmt_sst_mfr AND n.tmt_sst_type = z.tmt_sst_type AND n.tmt_sst_style = z.tmt_sst_style))
  GROUP BY breaker_class, breaker_style_id, tmt_sst_mfr, tmt_sst_type, tmt_sst_style, r_cont_current;

DO $$
DECLARE v_before integer; v_after integer;
BEGIN
  SELECT cnt INTO v_before FROM _f79_01_before;
  SELECT count(*) INTO v_after FROM tcc.vw_breaker_sst_mismatch;
  RAISE NOTICE 'F-79-01 vw_breaker_sst_mismatch: before(bare-key)=%, after(class-key)=%, delta=%',
    v_before, v_after, v_after - v_before;
  IF v_after < v_before THEN
    RAISE EXCEPTION 'F-79-01 monotonicity violated: class-keyed count % < bare-key count % — investigate before applying', v_after, v_before;
  END IF;
END $$;

COMMIT;
