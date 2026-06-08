-- 018_gf_overmodel_tier1_correction.sql
-- Tier-1 ground-fault over-model correction (lvbreakertcc protection-class audit, task #109).
--
-- The §196 audit found ETU trip styles NAMED "LI" (long-time + instantaneous) that
-- EasyPower modeled WITH a ground-fault element (derived LIG/LSIG). A 3-agent vendor-
-- catalog cross-reference (task #108) disproved the ground on 46 high-confidence styles:
--   - Siemens 3VA/3VL ETUs — ETU numbering encodes the class (320/820 = LI, 330/830 = LIG;
--     3VL ETU10 = LI vs ETU12 = LIG); a "LI"-class ETU has no ground element.
--   - Eaton — PXR 10 (S/G "Not available"; GF is PXR 20/25); Digitrip 210+ (LI/LSI only,
--     GF is 310+); Digitrip 520 (G only on LSIG/LSIA).
--   - Square-D Micrologic — "2.0"/PE-LI/SE-LI = basic UL (LI); ground only on the 6.0 unit.
-- Full per-type basis + citations: .audit_workspace/.../protection_class_audit/MASTER_VERDICTS.csv.
--
-- Correction = the §176 GF-suppress: set gfpu_calc=-1 + gfpu_pickup_max=NULL (drops the class
-- via vw_trip_unit_cascade) AND delete the GF child rows etu_gfd_bands / etu_gfpu_pickups /
-- etu_gfd_equations (the curve is gated on gfd_bands existence by _available_delay_elements,
-- and Screen-2 settings on gfpu_pickups — flag-flip alone would leave a spurious GF curve).
-- Tier-2 (ABB PR331/ELT, SqD Micrologic-Full — medium confidence) is intentionally NOT touched.
--
-- Reversible: full pre-change rows are snapshotted into tcc.gf_overmodel_backup_20260608_*.
-- Fail-closed: scope + post-state assertions roll the whole migration back on any mismatch.

CREATE TEMP TABLE _t1_styles(sid int) ON COMMIT DROP;
INSERT INTO _t1_styles(sid) VALUES
  (434),(440),(446),(451),(916),(948),(1706),(1708),(1746),(1748),
  (1780),(1781),(1782),(1783),(1784),(1819),(1824),(1826),(1827),(1828),
  (1829),(1830),(1831),(1832),(1833),(1978),(1979),(1980),(1981),(1982),
  (1983),(1984),(1985),(2018),(2038),(2119),(2257),(2260),(2290),(2291),
  (2296),(2297),(2358),(2450),(2552),(2553);

-- 0. Reversibility snapshot (full rows) ---------------------------------------
CREATE TABLE tcc.gf_overmodel_backup_20260608_sensors AS
  SELECT * FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles);
CREATE TABLE tcc.gf_overmodel_backup_20260608_gfd_bands AS
  SELECT b.* FROM tcc.etu_gfd_bands b
  WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
CREATE TABLE tcc.gf_overmodel_backup_20260608_gfpu_pickups AS
  SELECT p.* FROM tcc.etu_gfpu_pickups p
  WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
CREATE TABLE tcc.gf_overmodel_backup_20260608_gfd_equations AS
  SELECT e.* FROM tcc.etu_gfd_equations e
  WHERE e.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));

COMMENT ON TABLE tcc.gf_overmodel_backup_20260608_sensors IS
  'Pre-change snapshot for Tier-1 GF over-model correction (task #109, 2026-06-08). 46 ETU styles, name=LI but EasyPower-modeled ground; catalog-disproven. Reversal: UPDATE etu_sensors SET gfpu_calc/gfpu_pickup_max FROM here by id, then re-INSERT the *_gfd_bands/*_gfpu_pickups/*_gfd_equations backups.';

-- 1. Drop the class via the per-sensor gate (vw_trip_unit_cascade reads gfpu_calc) --
UPDATE tcc.etu_sensors
   SET gfpu_calc = -1, gfpu_pickup_max = NULL
 WHERE trip_style_id IN (SELECT sid FROM _t1_styles);

-- 2. Remove the GF child rows (curve + settings gates) --------------------------
DELETE FROM tcc.etu_gfd_bands
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
DELETE FROM tcc.etu_gfpu_pickups
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
DELETE FROM tcc.etu_gfd_equations
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));

-- 3. Fail-closed assertions -----------------------------------------------------
DO $$
DECLARE v_back int; v_gf int; v_bands int; v_pick int; v_eq int;
BEGIN
  SELECT count(*) INTO v_back FROM tcc.gf_overmodel_backup_20260608_sensors;
  IF v_back <> 134 THEN
    RAISE EXCEPTION 'scope drift: backup captured % sensors across the 46 styles, expected 134', v_back;
  END IF;

  SELECT count(*) INTO v_gf FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _t1_styles)
     AND gfpu_calc IS NOT NULL AND gfpu_calc <> -1;
  IF v_gf <> 0 THEN RAISE EXCEPTION 'post-state: % sensors still carry a ground element', v_gf; END IF;

  SELECT count(*) INTO v_bands FROM tcc.etu_gfd_bands b
   WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
  SELECT count(*) INTO v_pick FROM tcc.etu_gfpu_pickups p
   WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
  SELECT count(*) INTO v_eq FROM tcc.etu_gfd_equations e
   WHERE e.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _t1_styles));
  IF (v_bands + v_pick + v_eq) <> 0 THEN
    RAISE EXCEPTION 'post-state: GF child rows remain (gfd_bands=%, gfpu_pickups=%, gfd_equations=%)', v_bands, v_pick, v_eq;
  END IF;

  RAISE NOTICE 'Tier-1 GF over-model correction OK: 46 styles / % sensors suppressed; backups gfd_bands=%, gfpu_pickups=%.',
    v_back,
    (SELECT count(*) FROM tcc.gf_overmodel_backup_20260608_gfd_bands),
    (SELECT count(*) FROM tcc.gf_overmodel_backup_20260608_gfpu_pickups);
END $$;
