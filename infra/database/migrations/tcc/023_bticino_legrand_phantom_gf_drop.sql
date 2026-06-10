-- 023_bticino_legrand_phantom_gf_drop.sql
-- Family-wide phantom-G drop for the bticino Megatiker / Megabreaker + Legrand DMX3
-- families (resolves the audit's UNCERTAIN-9 + DURABLE-27 siblings).
--
-- Catalog basis ([VENDOR-DOC], read-only per sec.146 — cited in CATALOG-INDEX, not committed):
--   * 30808e.pdf (MP4-Megabreaker protection-unit manual): "earth fault protection
--     (only for version MP4 LSIg and MP6 LSIg)" — ground is confined to the -LSIg SKUs.
--     The MP4/MP6 protection unit is shared by bticino Megabreaker and Legrand DMX3.
--   * AD-EXMT22C Megatiker catalogue: electronic releases are "Lsi or Lsig only";
--     Lsi = Ir/tr + Isd/Tsd + Ii (NO earth fault); Lsig adds Ig/tg.
--   * 80178E / megatiker_mamhml_6301250 (MA-MH-ML manual): "S and T versions" —
--     T (terra/earth) is a distinct orderable version.
-- Internal basis: every non-LSIG style below carries gfpu_calc set with ZERO
-- etu_gfd_bands / gfd_equations / gfpu_pickups (pure phantom flag), while the
-- -LSIG siblings band-store the only real ground (identical signature to the
-- sec.111 PR331/P + sec.202 bucket-C corrections; DURABLE 31 triple satisfied).
--
-- 18 styles / 62 sensors (pure flag-flip; no child rows exist to delete):
--   bticino Megabreaker: 1591 MP4 LI, 1592 MP4 LSI
--   Legrand DMX3:        1523 MP4 LI
--   bticino Megatiker:   1568 M2250; 1569-1575 (M..E LI x7);
--                        1576,1577,1578,1579,1581,1582,1583 (M..E LSI x7)
-- Real-G keepers (regression-guarded below, NOT touched): Megatiker LSIG 1584-1590,
-- Megabreaker LSIG 1593/1594/2437, DMX3 MP4 LSI/G 1524, DMX-E MP 2G 1525.

DO $mig$
DECLARE
  v_cnt int;
BEGIN
  -- (1) Backup for reversibility
  DROP TABLE IF EXISTS tcc.bticino_legrand_gdrop_backup_20260609;
  CREATE TABLE tcc.bticino_legrand_gdrop_backup_20260609 AS
    SELECT id, trip_style_id, gfpu_calc, gfpu_pickup_max
    FROM tcc.etu_sensors
    WHERE trip_style_id = ANY(ARRAY[1591,1592,1523,1568,1569,1570,1571,1572,1573,1574,1575,1576,1577,1578,1579,1581,1582,1583]);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 62 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: backup captured % sensors, expected 62', v_cnt;
  END IF;

  -- (2) Guard: pure phantom — zero ground child rows on the targets
  SELECT count(*) INTO v_cnt FROM (
    SELECT b.sensor_id FROM tcc.etu_gfd_bands b
    JOIN tcc.bticino_legrand_gdrop_backup_20260609 t ON t.id = b.sensor_id
    UNION ALL
    SELECT e.sensor_id FROM tcc.etu_gfd_equations e
    JOIN tcc.bticino_legrand_gdrop_backup_20260609 t ON t.id = e.sensor_id
    UNION ALL
    SELECT p.sensor_id FROM tcc.etu_gfpu_pickups p
    JOIN tcc.bticino_legrand_gdrop_backup_20260609 t ON t.id = p.sensor_id
  ) x;
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % ground child rows exist on targets — not a pure flag-flip, aborting', v_cnt;
  END IF;

  -- (3) Flag-flip (GF-suppress, sec.176 mechanism)
  UPDATE tcc.etu_sensors
  SET gfpu_calc = -1, gfpu_pickup_max = NULL
  WHERE id IN (SELECT id FROM tcc.bticino_legrand_gdrop_backup_20260609);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 62 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: updated % sensors, expected 62', v_cnt;
  END IF;

  -- (4) E2E assert: none of the 18 corrected styles still derives a G class
  SELECT count(*) INTO v_cnt FROM (
    SELECT c.trip_style_id
    FROM public.vw_trip_unit_cascade c
    WHERE c.trip_style_id = ANY(ARRAY[1591,1592,1523,1568,1569,1570,1571,1572,1573,1574,1575,1576,1577,1578,1579,1581,1582,1583])
    GROUP BY c.trip_style_id
    HAVING bool_or(c.has_gfpu)
  ) d;
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % corrected styles still derive ground', v_cnt;
  END IF;

  -- (5) Regression guard: every real-G sibling still derives G
  SELECT count(*) INTO v_cnt FROM (
    SELECT c.trip_style_id
    FROM public.vw_trip_unit_cascade c
    WHERE c.trip_style_id = ANY(ARRAY[1584,1585,1586,1587,1588,1589,1590,1593,1594,2437,1524,1525])
    GROUP BY c.trip_style_id
    HAVING NOT bool_or(c.has_gfpu)
  ) d;
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % real-G sibling styles lost ground — over-sweep', v_cnt;
  END IF;

  RAISE NOTICE 'Migration 023 OK: phantom-G dropped on 18 bticino/Legrand styles (62 sensors); backup tcc.bticino_legrand_gdrop_backup_20260609.';
END $mig$;
