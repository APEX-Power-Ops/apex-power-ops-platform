-- 024_megatiker_li_inert_st_clear.sql
-- Clear the inert short-time placeholder on the 7 bticino Megatiker "M..E LI"
-- styles (1569-1575) so they derive clean LI matching their name (operator-ratified
-- option (a), 2026-06-09).
--
-- Basis: every short-time band on these styles is std_desc='Fixed' with ALL
-- t_open/t_clear/i_open/i_clear NULL (degenerate placeholder rendering no curve),
-- while the M..E LSI siblings carry real adjustable ladders (Tsd 0.1/0.2/0.3s,
-- 12xIr, I2t). Catalog (AD-EXMT22C): the electronic Megatiker is "Lsi or Lsig
-- only" — the LI tier has no selective short-time. Runs AFTER 023 (ground already
-- dropped), so post-state derives exactly LI.
--
-- 7 styles / 14 sensors / 14 inert band rows.

DO $mig$
DECLARE
  v_cnt int;
BEGIN
  -- (1) Backup sensors (flag) + bands (full rows) for reversibility
  DROP TABLE IF EXISTS tcc.megatiker_li_sclear_backup_20260609_sensors;
  CREATE TABLE tcc.megatiker_li_sclear_backup_20260609_sensors AS
    SELECT id, trip_style_id, stpu_calc
    FROM tcc.etu_sensors
    WHERE trip_style_id = ANY(ARRAY[1569,1570,1571,1572,1573,1574,1575]);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 14 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: sensor backup captured %, expected 14', v_cnt;
  END IF;

  DROP TABLE IF EXISTS tcc.megatiker_li_sclear_backup_20260609_bands;
  CREATE TABLE tcc.megatiker_li_sclear_backup_20260609_bands AS
    SELECT b.*
    FROM tcc.etu_std_bands b
    JOIN tcc.megatiker_li_sclear_backup_20260609_sensors t ON t.id = b.sensor_id;
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 14 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: band backup captured %, expected 14', v_cnt;
  END IF;

  -- (2) Guard: every target band is the inert placeholder (Fixed + null curve)
  SELECT count(*) INTO v_cnt
  FROM tcc.megatiker_li_sclear_backup_20260609_bands
  WHERE NOT (std_desc = 'Fixed' AND t_open IS NULL AND t_clear IS NULL
             AND i_open IS NULL AND i_clear IS NULL);
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % target bands are not inert placeholders — aborting', v_cnt;
  END IF;

  -- (3) Delete the placeholder bands
  DELETE FROM tcc.etu_std_bands b
  USING tcc.megatiker_li_sclear_backup_20260609_sensors t
  WHERE b.sensor_id = t.id;
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 14 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: deleted % bands, expected 14', v_cnt;
  END IF;

  -- (4) Clear the short-time flag
  UPDATE tcc.etu_sensors
  SET stpu_calc = -1
  WHERE id IN (SELECT id FROM tcc.megatiker_li_sclear_backup_20260609_sensors);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 14 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: updated % sensors, expected 14', v_cnt;
  END IF;

  -- (5) E2E assert: each of the 7 styles now derives exactly LI
  SELECT count(*) INTO v_cnt FROM (
    SELECT c.trip_style_id,
           'L'
           || CASE WHEN bool_or(c.has_stpu) THEN 'S' ELSE '' END
           || CASE WHEN bool_or(c.has_inst) THEN 'I' ELSE '' END
           || CASE WHEN bool_or(c.has_gfpu) THEN 'G' ELSE '' END AS derived
    FROM public.vw_trip_unit_cascade c
    WHERE c.trip_style_id = ANY(ARRAY[1569,1570,1571,1572,1573,1574,1575])
    GROUP BY c.trip_style_id
  ) d
  WHERE d.derived <> 'LI';
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % styles do not derive LI post-clear', v_cnt;
  END IF;

  -- (6) Regression guard: the M..E LSI siblings keep their real short-time
  SELECT count(*) INTO v_cnt FROM (
    SELECT c.trip_style_id
    FROM public.vw_trip_unit_cascade c
    WHERE c.trip_style_id = ANY(ARRAY[1576,1577,1578,1579,1581,1582,1583])
    GROUP BY c.trip_style_id
    HAVING NOT bool_or(c.has_stpu)
  ) d;
  IF v_cnt <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % LSI siblings lost short-time — over-sweep', v_cnt;
  END IF;

  RAISE NOTICE 'Migration 024 OK: inert short-time cleared on 7 Megatiker M..E LI styles (14 sensors, 14 placeholder bands); backups tcc.megatiker_li_sclear_backup_20260609_*.';
END $mig$;
