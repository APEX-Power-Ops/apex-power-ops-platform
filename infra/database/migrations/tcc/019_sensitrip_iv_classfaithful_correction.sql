-- 019_sensitrip_iv_classfaithful_correction.sql
-- Siemens (ITE/Sentron) Sensitrip IV protection-class over-model correction (lvbreakertcc, task #110).
--
-- BACKGROUND. The §196 audit left "Siemens Sensitrip IV (5)" UNCERTAIN, pending the
-- Sentron Series catalog. The operator supplied the Sentron Sensitrip IV datasheets
-- (SJD 200-400A frame + SND 1200A frame + family manual). Both frames define FOUR
-- distinct ETU models with explicit adjustable-function lists:
--     LI   = Ir (long-time) + tld (LT delay) + Ii (instantaneous)         -> L + I
--     LIG  = LI + Ig/tg (ground)                                          -> L + I + G
--     LSI  = LI + Isd/tsd (short-time)                                    -> L + S + I
--     LSIG = + short-time AND ground                                      -> full
-- i.e. a Sensitrip IV "-LI" trip is Long-time + Instantaneous ONLY (no short-time,
-- no ground); "-LIG" has no short-time; "-LSI" has no ground.
--
-- DEFECT. EasyPower stamped the ENTIRE Sensitrip IV family with the LSIG envelope
-- regardless of the ordered class. 15 of 21 styles carry a label richer than their name.
-- The one already-fixed sibling (PD-LSI, 2076: ground flag off) proves the rest are
-- unfixed over-models, not intentional. Two sub-cases:
--   * Most over-models are LABEL-ONLY: the spurious element's calc flag is set
--     (stpu_calc/gfpu_calc <> -1, so the protection_class derives the extra letter)
--     but there are ZERO child band/pickup rows, so the plotted curve is already
--     correct. -> pure flag-flip.
--   * Two "-LSI" styles (MD 2068, ND 2072) plus the PD-LSI orphan (2076) carry REAL
--     ground child rows (21 gfd_bands + 21 gfpu_pickups total) -> a phantom ground
--     curve renders (the curve gates on etu_gfd_bands existence, DURABLE 26).
--     -> flag-flip + delete the GF child rows (the migration-018 GF-suppress).
--
-- CORRECTION (symmetric S-drop / G-drop, by name class):
--   S-drop (name lacks short-time: LI + LIG, 10 styles) -> stpu_calc=-1 + delete any
--           etu_std_bands/etu_stpu_pickups/etu_std_equations/etu_stpu_overrides (expect 0).
--   G-drop (name lacks ground:     LI + LSI, 10 styles) -> gfpu_calc=-1, gfpu_pickup_max=NULL
--           + delete etu_gfd_bands/etu_gfpu_pickups/etu_gfd_equations (21/21/0).
--   (LI styles are in BOTH sets -> drop S and G.)
-- vw_trip_unit_cascade derives has_stpu = (stpu_calc IS NOT NULL AND <> -1) and
-- has_gfpu = (gfpu_calc IS NOT NULL AND <> -1); the §196 protection_class is
-- 'L' || S? || I? || G? bool_or'd per style. So the flag-flip is what re-labels each
-- style to its name class. Untouched (already correct): LSIG 2061/2065/2069/2073/2077,
-- LSIGA 2423.
--
-- Reversible: full pre-change rows snapshotted into tcc.sensitrip4_backup_20260608_*.
-- Fail-closed: scope + post-state + END-TO-END (serving-view derived class == name) assertions.

CREATE TEMP TABLE _s_styles(sid int) ON COMMIT DROP;   -- name lacks short-time: LI + LIG
INSERT INTO _s_styles(sid) VALUES
  (2058),(2059),(2062),(2063),(2066),(2067),(2070),(2071),(2074),(2075);

CREATE TEMP TABLE _g_styles(sid int) ON COMMIT DROP;   -- name lacks ground: LI + LSI
INSERT INTO _g_styles(sid) VALUES
  (2058),(2060),(2062),(2064),(2066),(2068),(2070),(2072),(2074),(2076);

-- 0. Reversibility snapshot (full rows) ---------------------------------------
CREATE TABLE tcc.sensitrip4_backup_20260608_sensors AS
  SELECT * FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _s_styles UNION SELECT sid FROM _g_styles);
CREATE TABLE tcc.sensitrip4_backup_20260608_gfd_bands AS
  SELECT b.* FROM tcc.etu_gfd_bands b
   WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));
CREATE TABLE tcc.sensitrip4_backup_20260608_gfpu_pickups AS
  SELECT p.* FROM tcc.etu_gfpu_pickups p
   WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));
CREATE TABLE tcc.sensitrip4_backup_20260608_gfd_equations AS
  SELECT e.* FROM tcc.etu_gfd_equations e
   WHERE e.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));
CREATE TABLE tcc.sensitrip4_backup_20260608_std_bands AS
  SELECT b.* FROM tcc.etu_std_bands b
   WHERE b.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));
CREATE TABLE tcc.sensitrip4_backup_20260608_stpu_pickups AS
  SELECT p.* FROM tcc.etu_stpu_pickups p
   WHERE p.sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));

COMMENT ON TABLE tcc.sensitrip4_backup_20260608_sensors IS
  'Pre-change snapshot for Sensitrip IV class-faithful correction (task #110, 2026-06-08). 42 sensors / 15 styles, name-class < modeled LSIG; catalog-disproven (Sentron Sensitrip IV LI/LIG/LSI/LSIG models). Reversal: UPDATE etu_sensors SET stpu_calc/gfpu_calc/gfpu_pickup_max FROM here by id, then re-INSERT the *_gfd_bands/*_gfpu_pickups/*_gfd_equations (and *_std_bands/*_stpu_pickups) backups.';

-- 1. Drop short-time label (name lacks S) -------------------------------------
UPDATE tcc.etu_sensors
   SET stpu_calc = -1
 WHERE trip_style_id IN (SELECT sid FROM _s_styles);

-- 2. Drop ground label (name lacks G) -----------------------------------------
UPDATE tcc.etu_sensors
   SET gfpu_calc = -1, gfpu_pickup_max = NULL
 WHERE trip_style_id IN (SELECT sid FROM _g_styles);

-- 3. Remove short-time child rows for S-drop (defensive; expect 0) -------------
DELETE FROM tcc.etu_std_bands
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));
DELETE FROM tcc.etu_stpu_pickups
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));
DELETE FROM tcc.etu_std_equations
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));
DELETE FROM tcc.etu_stpu_overrides
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles));

-- 4. Remove ground child rows for G-drop (curve + Screen-2 settings) -----------
DELETE FROM tcc.etu_gfd_bands
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));
DELETE FROM tcc.etu_gfpu_pickups
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));
DELETE FROM tcc.etu_gfd_equations
 WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles));

-- 5. Fail-closed assertions ----------------------------------------------------
DO $$
DECLARE v_back int; v_s_has int; v_g_has int; v_g_child int; v_s_child int;
BEGIN
  SELECT count(*) INTO v_back FROM tcc.sensitrip4_backup_20260608_sensors;
  IF v_back <> 42 THEN
    RAISE EXCEPTION 'scope drift: backup captured % sensors, expected 42', v_back;
  END IF;

  SELECT count(*) INTO v_s_has FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _s_styles) AND stpu_calc IS NOT NULL AND stpu_calc <> -1;
  IF v_s_has <> 0 THEN RAISE EXCEPTION 'post: % S-drop sensors still carry short-time', v_s_has; END IF;

  SELECT count(*) INTO v_g_has FROM tcc.etu_sensors
   WHERE trip_style_id IN (SELECT sid FROM _g_styles) AND gfpu_calc IS NOT NULL AND gfpu_calc <> -1;
  IF v_g_has <> 0 THEN RAISE EXCEPTION 'post: % G-drop sensors still carry ground', v_g_has; END IF;

  SELECT (SELECT count(*) FROM tcc.etu_gfd_bands    WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles)))
       + (SELECT count(*) FROM tcc.etu_gfpu_pickups WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles)))
       + (SELECT count(*) FROM tcc.etu_gfd_equations WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _g_styles)))
    INTO v_g_child;
  IF v_g_child <> 0 THEN RAISE EXCEPTION 'post: G child rows remain on G-drop styles (%)', v_g_child; END IF;

  SELECT (SELECT count(*) FROM tcc.etu_std_bands    WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles)))
       + (SELECT count(*) FROM tcc.etu_stpu_pickups WHERE sensor_id IN (SELECT id FROM tcc.etu_sensors WHERE trip_style_id IN (SELECT sid FROM _s_styles)))
    INTO v_s_child;
  IF v_s_child <> 0 THEN RAISE EXCEPTION 'post: S child rows remain on S-drop styles (%)', v_s_child; END IF;

  RAISE NOTICE 'Sensitrip IV correction OK: 42 sensors; backup gfd_bands=%, gfpu_pickups=%.',
    (SELECT count(*) FROM tcc.sensitrip4_backup_20260608_gfd_bands),
    (SELECT count(*) FROM tcc.sensitrip4_backup_20260608_gfpu_pickups);
END $$;

-- 6. END-TO-END: serving-view derived protection_class == name class -----------
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
    WHERE v.trip_style_id IN (2058,2059,2060,2062,2063,2064,2066,2067,2068,
                              2070,2071,2072,2074,2075,2076)
    GROUP BY v.trip_style_id
  ) d
  JOIN (VALUES
    (2058,'LI'),(2062,'LI'),(2066,'LI'),(2070,'LI'),(2074,'LI'),
    (2059,'LIG'),(2063,'LIG'),(2067,'LIG'),(2071,'LIG'),(2075,'LIG'),
    (2060,'LSI'),(2064,'LSI'),(2068,'LSI'),(2072,'LSI'),(2076,'LSI')
  ) e(sid, expected) ON e.sid = d.sid
  WHERE d.derived <> e.expected;

  IF v_mismatch <> 0 THEN
    RAISE EXCEPTION 'end-to-end: % Sensitrip IV styles derive a class != their name [%]', v_mismatch, v_detail;
  END IF;
  RAISE NOTICE 'end-to-end OK: all 15 touched Sensitrip IV styles derive their name class via vw_trip_unit_cascade.';
END $$;
