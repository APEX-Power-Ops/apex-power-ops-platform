-- 021_bucketc_tier2_gf_overmodel_correction.sql
-- Bucket-C re-sweep (§199-surfaced) Tier-2: label-only GF over-model correction.
--
-- 12 ETU trip styles named "LS/I" or "-LSI" but modeled LSIG with a VESTIGIAL ground
-- flag (gfpu_calc set) and ZERO ground curve rows (gfd_bands = gfpu_pickups =
-- gfd_equations = 0). Each family band-stores real ground on its -LSIG siblings
-- (MIXED_G), so these are vestigial flags, not data gaps. Catalog-confirmed no-ground
-- configs (re-uses the §197 cross-ref, .audit_workspace/catalog_lane/protection_class_audit/):
--   * ABB Ekip Dip catalog 1SDC210100D0205 enumerates LS/I as a DISTINCT variant != LSIG.
--   * Eaton PXR overview MN012007EN: PXR 20/20D/25 ground fault is offered only on LSIG;
--     LSI configs have no G. (2204 independently catalog-locked LSI, task #39.)
--
-- Pure label-only flag-flip (no child rows to delete). Reversible + fail-closed.
--   ABB Ekip Dip:    2397 2398 2399 2400 2401   (XT2/4/5/6/7 LS/I)
--   Eaton PXR20/25:  2204 1864 1868 1873 2024 2029 2475
--                    (PXR2 20D/25 / IZMX16 / IZMX40 H+N / NRX NF+RF / PDG4  -LSI)
-- All LSIG -> LSI (drop the over-modeled G). 63 sensors. HELD (not touched): the
-- C-H/Eaton DT 310 family (§197 ruled GF-REAL) and ABB S3 (no S3-specific catalog).

DO $mig$
DECLARE
  v_sids  int[] := ARRAY[2397,2398,2399,2400,2401,2204,1864,1868,1873,2024,2029,2475];
  v_back  int;
  v_child int;
  v_upd   int;
  v_bad   int;
BEGIN
  -- (1) Backup pre-state for reversibility
  DROP TABLE IF EXISTS tcc.bucketc_backup_20260609_sensors;
  CREATE TABLE tcc.bucketc_backup_20260609_sensors AS
    SELECT s.id, s.trip_style_id, s.gfpu_calc, s.gfpu_pickup_max
    FROM tcc.etu_sensors s
    WHERE s.trip_style_id = ANY(v_sids);
  GET DIAGNOSTICS v_back = ROW_COUNT;
  IF v_back <> 63 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: backup captured % sensors, expected 63', v_back;
  END IF;

  -- (2) Guard: confirm pure label-only (ZERO ground child rows) before any write
  SELECT
      (SELECT count(*) FROM tcc.etu_gfd_bands   b JOIN tcc.etu_sensors s ON s.id=b.sensor_id WHERE s.trip_style_id = ANY(v_sids))
    + (SELECT count(*) FROM tcc.etu_gfpu_pickups p JOIN tcc.etu_sensors s ON s.id=p.sensor_id WHERE s.trip_style_id = ANY(v_sids))
    + (SELECT count(*) FROM tcc.etu_gfd_equations e JOIN tcc.etu_sensors s ON s.id=e.sensor_id WHERE s.trip_style_id = ANY(v_sids))
    INTO v_child;
  IF v_child <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: expected 0 ground child rows (label-only), found % - not a pure flag-flip', v_child;
  END IF;

  -- (3) Flip: drop the vestigial ground flag
  UPDATE tcc.etu_sensors
     SET gfpu_calc = -1, gfpu_pickup_max = NULL
   WHERE trip_style_id = ANY(v_sids);
  GET DIAGNOSTICS v_upd = ROW_COUNT;
  IF v_upd <> 63 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: updated % sensors, expected 63', v_upd;
  END IF;

  -- (4) End-to-end assertion: every style now derives LSI through the LIVE serving view
  SELECT count(*) INTO v_bad FROM (
    SELECT ts.id,
           'L'
           || CASE WHEN bool_or(c.has_stpu) THEN 'S' ELSE '' END
           || CASE WHEN bool_or(c.has_inst) THEN 'I' ELSE '' END
           || CASE WHEN bool_or(c.has_gfpu) THEN 'G' ELSE '' END AS derived
    FROM tcc.trip_styles ts
    JOIN public.vw_trip_unit_cascade c ON c.trip_style_id = ts.id
    WHERE ts.id = ANY(v_sids)
    GROUP BY ts.id
  ) d
  WHERE d.derived <> 'LSI';
  IF v_bad <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % styles did not derive LSI post-flip', v_bad;
  END IF;

  RAISE NOTICE 'Migration 021 OK: 12 styles / 63 sensors LSIG->LSI (label-only); all derive LSI via live view; backup tcc.bucketc_backup_20260609_sensors.';
END $mig$;
