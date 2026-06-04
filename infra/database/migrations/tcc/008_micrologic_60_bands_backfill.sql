-- 008_micrologic_60_bands_backfill.sql
-- =============================================================================
-- Backfill STD/GFD delay bands for the band-LESS Micrologic 6.0 trip styles.
--
-- WHY (STATE §138, 2026-06-04; verified vs raw Access TCC_NEW.accdb):
--   EasyPower's own source genuinely carries NO DatSection3STD / DatSection1GfGFD
--   rows for the Micrologic 6.0 styles 238 / 1919 / 1920 / 1921 / 1922 / 2173
--   (Compact NS + Masterpact NW 6.0A/E/H/P) — a GENUINE source gap, not a load
--   defect. Only styles 246 (SQD Compact NS 6.0A, 9 sensors) + 366 (MG Masterpact
--   NW 6.0, 12 sensors) carry the bands. The S/G delay bands are RATING-INDEPENDENT
--   (identical across every 6.0 frame — verified: all 9 style-246 sensors carry an
--   identical band set), so the same record serves every 6.0 sensor.
--
-- WHAT: propagate EasyPower's OWN style-246 band rows (verbatim, datasheet
--   cross-checked — `reference/tcc/MICROLOGIC-6.0A.md` [VENDOR-DOC]) to the 593
--   band-less 6.0 sensors. This is a faithful EXTENSION using EasyPower's own
--   same-device data, codified at `services/neta/micrologic_curves.py`
--   (CANONICAL_STD_BANDS / CANONICAL_GFD_BANDS). The runtime serving layer already
--   renders these at runtime (STATE §137 fallback); this persists them so the data
--   is self-describing and the fallback becomes dormant.
--
-- IDEMPOTENT: NOT EXISTS guard per (sensor, table) — re-running is a no-op.
-- PROVENANCE: [VENDOR-DOC] (tcc style 246 verbatim + Schneider micrologic_20_70a_eng).
--   Operator-authorized persist (2026-06-04).
-- =============================================================================

BEGIN;

-- ---- STD (4 bands per sensor; i_open = 10·Ir, i2x = 2) ----------------------
WITH canon_std(ordinal, std_desc, std_open, std_clear, t_open, t_clear, i_open, i_clear, i2x) AS (
  VALUES
    (0, '0.1', 0.08::real, 0.14::real, 0.08::real, 0.10::real, 10::real, 10::real, 2::smallint),
    (1, '0.2', 0.14::real, 0.20::real, 0.16::real, 0.20::real, 10::real, 10::real, 2::smallint),
    (2, '0.3', 0.23::real, 0.32::real, 0.24::real, 0.30::real, 10::real, 10::real, 2::smallint),
    (3, '0.4', 0.35::real, 0.50::real, 0.32::real, 0.40::real, 10::real, 10::real, 2::smallint)
),
targets AS (
  SELECT s.id AS sensor_id
  FROM tcc.etu_sensors s
  WHERE s.trip_style_id IN (238, 1919, 1920, 1921, 1922, 2173)
    AND NOT EXISTS (SELECT 1 FROM tcc.etu_std_bands b WHERE b.sensor_id = s.id)
)
INSERT INTO tcc.etu_std_bands (sensor_id, ordinal, std_desc, std_open, std_clear, t_open, t_clear, i_open, i_clear, i2x)
SELECT t.sensor_id, c.ordinal, c.std_desc, c.std_open, c.std_clear, c.t_open, c.t_clear, c.i_open, c.i_clear, c.i2x
FROM targets t CROSS JOIN canon_std c;

-- ---- GFD (5 bands per sensor; ordinal 1 "Off" flat, then i_open = 1·In, i2x = 2)
WITH canon_gfd(ordinal, gfd_desc, gfd_open, gfd_clear, t_open, t_clear, i_open, i_clear, i2x) AS (
  VALUES
    (1, 'Off', 0.02::real, 0.08::real, NULL::real, NULL::real, NULL::real, NULL::real, NULL::smallint),
    (2, '0.1', 0.08::real, 0.14::real, 0.08::real, 0.10::real, 1::real, 1::real, 2::smallint),
    (3, '0.2', 0.14::real, 0.20::real, 0.16::real, 0.20::real, 1::real, 1::real, 2::smallint),
    (4, '0.3', 0.23::real, 0.32::real, 0.24::real, 0.30::real, 1::real, 1::real, 2::smallint),
    (5, '0.4', 0.35::real, 0.50::real, 0.32::real, 0.40::real, 1::real, 1::real, 2::smallint)
),
targets AS (
  SELECT s.id AS sensor_id
  FROM tcc.etu_sensors s
  WHERE s.trip_style_id IN (238, 1919, 1920, 1921, 1922, 2173)
    AND NOT EXISTS (SELECT 1 FROM tcc.etu_gfd_bands g WHERE g.sensor_id = s.id)
)
INSERT INTO tcc.etu_gfd_bands (sensor_id, ordinal, gfd_desc, gfd_open, gfd_clear, t_open, t_clear, i_open, i_clear, i2x)
SELECT t.sensor_id, c.ordinal, c.gfd_desc, c.gfd_open, c.gfd_clear, c.t_open, c.t_clear, c.i_open, c.i_clear, c.i2x
FROM targets t CROSS JOIN canon_gfd c;

-- ---- post-asserts: every band-less 6.0 sensor now carries exactly 4 STD + 5 GFD
DO $$
DECLARE
  n_sensors int;
  bad_std int;
  bad_gfd int;
BEGIN
  SELECT count(*) INTO n_sensors FROM tcc.etu_sensors WHERE trip_style_id IN (238,1919,1920,1921,1922,2173);
  SELECT count(*) INTO bad_std FROM tcc.etu_sensors s
    WHERE s.trip_style_id IN (238,1919,1920,1921,1922,2173)
      AND (SELECT count(*) FROM tcc.etu_std_bands b WHERE b.sensor_id = s.id) <> 4;
  SELECT count(*) INTO bad_gfd FROM tcc.etu_sensors s
    WHERE s.trip_style_id IN (238,1919,1920,1921,1922,2173)
      AND (SELECT count(*) FROM tcc.etu_gfd_bands g WHERE g.sensor_id = s.id) <> 5;
  IF bad_std <> 0 OR bad_gfd <> 0 THEN
    RAISE EXCEPTION 'micrologic 6.0 band backfill assert FAILED: sensors=%, bad_std(<>4)=%, bad_gfd(<>5)=%',
      n_sensors, bad_std, bad_gfd;
  END IF;
  RAISE NOTICE 'micrologic 6.0 band backfill OK: % sensors, all carry 4 STD + 5 GFD bands', n_sensors;
END $$;

COMMIT;
