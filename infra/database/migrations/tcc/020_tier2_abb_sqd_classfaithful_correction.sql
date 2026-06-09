-- 020_tier2_abb_sqd_classfaithful_correction.sql
-- Tier-2 GF over-model resolution + Square D "Micrologic Full" family accuracy (lvbreakertcc, task #111).
--
-- Resolves the §197 held Tier-2 (6 medium-confidence styles) after an operator-sourced
-- catalog review (Square D SE manual 48040-495-07) and the family-sibling consistency
-- check. Operator: "approved for all measures that make it correct end to end."
--
-- THREE distinct accuracy fixes:
--
-- A. ABB PR331/P + ELT — VESTIGIAL GROUND, drop it (7 styles).
--    Every non-LSIG style in the PR331/P family carries a stray gfpu flag (label derives
--    LIG/LSIG) but ZERO ground curve (gfd_bands=0, gfpu_pickups=0); the clean -LSIG
--    siblings hold the only real ground. So the G is label-only — dropping it loses no
--    curve and makes the label match both the name and the (empty) ground plot.
--    Includes the 3 "-LSI" siblings the ground-token-only §197 audit missed (DURABLE 27).
--      1106 MCCB-LI, 1237 ICCB-LI, 2035 [IEC] MCCB-LI, 1915 ELT-LI  -> LI
--      2095 ICCB-LSI, 2097 MCCB-LSI, 2036 [IEC] MCCB-LSI            -> LSI
--    Correction = flag-flip only (gfpu_calc=-1, gfpu_pickup_max=NULL); no child rows exist.
--
-- B. Square D "Micrologic Full" SE-LI (294) — ORPHAN PHANTOM CURVES, clean to LI.
--    294 derives LI (stpu_calc/gfpu_calc already -1) but carries orphan std_bands(32)+
--    stpu_pickups(64)+gfd_bands(40)+gfpu_pickups(40) -> it draws short-time AND ground
--    curves under an "LI" label (curve gates on band existence, DURABLE 26). Its clean
--    siblings LE-LI(636)/ME-LI(637) are std=0/gfd=0. Fix = delete the orphan S+G child
--    rows so the curve matches the LI label and the family pattern.
--
-- C. Square D SE-LI (815) + ME-LI Series B (2371) — GROUND IS FAITHFUL, keep + rename.
--    The Square D SE manual (48040-495-07, MICROLOGIC Full-function Trip System) shows
--    ground fault is a real, orderable ("ground-fault option"), defeatable ("defeat
--    ground-fault ... jumper") element on these full-function trips. So LIG (long-time +
--    instantaneous + ground active, short-time defeated) is a faithful configuration, NOT
--    an over-model -> KEEP the ground curve. The only inaccuracy is the style NAME suffix
--    "-LI" understating the class; rename "-LI" -> "-LIG" so the stored name matches the
--    modeled/derived class (no curve/flag change). [DURABLE 28]
--
-- Reversible: tcc.tier2_backup_20260608_*. Fail-closed: scope + post-state + END-TO-END
-- (serving-view derived class == intended) assertions roll the whole migration back.

CREATE TEMP TABLE _abb_li(sid int)  ON COMMIT DROP;  -- drop G -> LI
INSERT INTO _abb_li(sid)  VALUES (1106),(1237),(2035),(1915);
CREATE TEMP TABLE _abb_lsi(sid int) ON COMMIT DROP;  -- drop G -> LSI
INSERT INTO _abb_lsi(sid) VALUES (2095),(2097),(2036);

-- 0. Reversibility snapshot -----------------------------------------------------
CREATE TABLE tcc.tier2_backup_20260608_sensors AS
  SELECT * FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _abb_li UNION SELECT sid FROM _abb_lsi UNION SELECT 294);
CREATE TABLE tcc.tier2_backup_20260608_std_bands AS
  SELECT b.* FROM tcc.etu_std_bands b
   WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
CREATE TABLE tcc.tier2_backup_20260608_stpu_pickups AS
  SELECT p.* FROM tcc.etu_stpu_pickups p
   WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
CREATE TABLE tcc.tier2_backup_20260608_gfd_bands AS
  SELECT b.* FROM tcc.etu_gfd_bands b
   WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
CREATE TABLE tcc.tier2_backup_20260608_gfpu_pickups AS
  SELECT p.* FROM tcc.etu_gfpu_pickups p
   WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
CREATE TABLE tcc.tier2_backup_20260608_trip_styles AS
  SELECT * FROM tcc.trip_styles WHERE id IN (815, 2371);

COMMENT ON TABLE tcc.tier2_backup_20260608_sensors IS
  'Pre-change snapshot for Tier-2 ABB/SqD correction (task #111, 2026-06-08). ABB PR331/P+ELT vestigial-G drop (7 styles) + SqD SE-LI 294 orphan-curve cleanup. Reversal: restore etu_sensors gfpu_calc/gfpu_pickup_max by id; re-INSERT the 294 *_std_bands/_stpu_pickups/_gfd_bands/_gfpu_pickups backups; restore trip_styles.style from _trip_styles backup.';

-- A. ABB: drop the vestigial ground label (flag-flip) ---------------------------
UPDATE tcc.etu_sensors
   SET gfpu_calc = -1, gfpu_pickup_max = NULL
 WHERE trip_style_id IN (SELECT sid FROM _abb_li UNION SELECT sid FROM _abb_lsi);
-- defensive (expect 0 rows each): any GF child rows on the ABB styles
DELETE FROM tcc.etu_gfd_bands
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _abb_li UNION SELECT sid FROM _abb_lsi));
DELETE FROM tcc.etu_gfpu_pickups
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _abb_li UNION SELECT sid FROM _abb_lsi));

-- B. SqD 294 SE-LI: delete orphan short-time + ground curves (label already LI) --
DELETE FROM tcc.etu_std_bands     WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_stpu_pickups  WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_std_equations WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_stpu_overrides WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_gfd_bands     WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_gfpu_pickups  WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);
DELETE FROM tcc.etu_gfd_equations WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id = 294);

-- C. SqD 815/2371: keep faithful ground, rename name suffix -LI -> -LIG ----------
UPDATE tcc.trip_styles SET style = 'ICCB SE-LIG'    WHERE id = 815  AND style = 'ICCB SE-LI';
UPDATE tcc.trip_styles SET style = 'ME-LIG Series B' WHERE id = 2371 AND style = 'ME-LI Series B';

-- 1. Fail-closed assertions -----------------------------------------------------
DO $$
DECLARE v_back int; v_abb_g int; v_294_child int; v_815 int; v_2371 int; v_815_gf int; v_2371_gf int;
BEGIN
  SELECT count(*) INTO v_back FROM tcc.tier2_backup_20260608_sensors;
  IF v_back <> 48 THEN RAISE EXCEPTION 'scope drift: backup captured % sensors, expected 48 (39 ABB + 9 SqD-294)', v_back; END IF;

  SELECT count(*) INTO v_abb_g FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _abb_li UNION SELECT sid FROM _abb_lsi)
     AND gfpu_calc IS NOT NULL AND gfpu_calc <> -1;
  IF v_abb_g <> 0 THEN RAISE EXCEPTION 'post: % ABB sensors still carry ground', v_abb_g; END IF;

  SELECT (SELECT count(*) FROM tcc.etu_std_bands  WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=294))
       + (SELECT count(*) FROM tcc.etu_gfd_bands  WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=294))
       + (SELECT count(*) FROM tcc.etu_stpu_pickups WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=294))
       + (SELECT count(*) FROM tcc.etu_gfpu_pickups WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=294))
    INTO v_294_child;
  IF v_294_child <> 0 THEN RAISE EXCEPTION 'post: SqD 294 still has S/G child rows (%)', v_294_child; END IF;

  -- C: names renamed, ground PRESERVED
  SELECT count(*) INTO v_815  FROM tcc.trip_styles WHERE id=815  AND style='ICCB SE-LIG';
  SELECT count(*) INTO v_2371 FROM tcc.trip_styles WHERE id=2371 AND style='ME-LIG Series B';
  IF v_815 <> 1 OR v_2371 <> 1 THEN RAISE EXCEPTION 'post: SqD rename failed (815=%, 2371=%)', v_815, v_2371; END IF;
  SELECT count(*) INTO v_815_gf  FROM tcc.etu_gfd_bands WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=815);
  SELECT count(*) INTO v_2371_gf FROM tcc.etu_gfd_bands WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id=2371);
  IF v_815_gf <> 36 OR v_2371_gf <> 12 THEN RAISE EXCEPTION 'post: SqD ground curve altered (815 gfd=%, 2371 gfd=%; expected 36/12)', v_815_gf, v_2371_gf; END IF;

  RAISE NOTICE 'Tier-2 correction OK: ABB 7 -> LI/LSI; SqD 294 -> clean LI; SqD 815/2371 kept LIG + renamed.';
END $$;

-- 2. END-TO-END: serving-view derived class == intended -------------------------
DO $$
DECLARE v_mismatch int; v_detail text;
BEGIN
  SELECT count(*), string_agg(d.sid || ':' || d.derived || '<>' || e.expected, ', ')
    INTO v_mismatch, v_detail
  FROM (
    SELECT v.trip_style_id AS sid,
           'L' || CASE WHEN bool_or(v.has_stpu) THEN 'S' ELSE '' END
               || CASE WHEN bool_or(v.has_inst) THEN 'I' ELSE '' END
               || CASE WHEN bool_or(v.has_gfpu) THEN 'G' ELSE '' END AS derived
    FROM public.vw_trip_unit_cascade v
    WHERE v.trip_style_id IN (1106,1237,2035,1915, 2095,2097,2036, 294, 815,2371)
    GROUP BY v.trip_style_id
  ) d
  JOIN (VALUES
    (1106,'LI'),(1237,'LI'),(2035,'LI'),(1915,'LI'),
    (2095,'LSI'),(2097,'LSI'),(2036,'LSI'),
    (294,'LI'),
    (815,'LIG'),(2371,'LIG')
  ) e(sid, expected) ON e.sid = d.sid
  WHERE d.derived <> e.expected;

  IF v_mismatch <> 0 THEN
    RAISE EXCEPTION 'end-to-end: % styles derive a class != intended [%]', v_mismatch, v_detail;
  END IF;
  RAISE NOTICE 'end-to-end OK: all 10 Tier-2 styles derive their intended class via vw_trip_unit_cascade.';
END $$;
