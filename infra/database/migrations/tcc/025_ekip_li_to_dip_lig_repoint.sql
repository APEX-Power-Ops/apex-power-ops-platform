-- 025_ekip_li_to_dip_lig_repoint.sql
-- Repoint the EP-shorthand "Ekip LI" type (trip_types id 10) into the canonical
-- "Ekip Dip" type (id 4) as the LIG variant, completing the Tmax XT Dip lineup
-- (LS/I, LIG, LSI, LSIG) to ABB's actual four power-distribution variants.
--
-- Triangulated identification ([VENDOR-DOC], cited in CATALOG-INDEX):
--   * 860995673-Ekip-Dip.pdf (ABB Ekip Dip overview, 1SDC210100D0203 family):
--     the XT Dip lineup is LS/I + LIG + LSI + LSIG — there is NO "LI" variant;
--     LIG = L + I + G (no short-time), G real-adjustable (I4 Off-1xIn, t4 0.1-0.8s).
--   * 1SDC210200D0206 (2024 UL Tmax XT catalog): zero "Dip LI" occurrences.
--   * ABB-ZEAEDLI-Ekip-Dip-LI-Datasheet.pdf (1SDA074194R1): the genuine
--     "Ekip Dip LI" is an Emax 2 (E1.2..E6.2) ACB accessory — a DIFFERENT product,
--     already modeled faithfully as style 1527 "LVPCB LI" (L+I, no G).
--   * Styles 1501/1503 match the XT LIG column empirically: LTPU step 0.04
--     (the LS/I-and-LIG-generation step; LSI/LSIG use 0.02), no S, analytic G.
-- The G stays (sec.197 GF-REAL, reconfirmed) — this is a naming repoint only.
-- "trip_styles.type = trip_types.name" is the cascade join key (sec.195), so the
-- repoint pairs the style update with the orphaned type-row delete atomically.
-- Alias tables are trip_style_id-keyed — unaffected.

DO $mig$
DECLARE
  v_cnt int;
  v_mfg_type bigint;
  v_mfg_styles int;
BEGIN
  -- (1) Guards: expected rows exist, exactly 2 styles ride type 10, no name collisions
  SELECT count(*) INTO v_cnt FROM tcc.trip_types WHERE id = 4 AND name = 'Ekip Dip';
  IF v_cnt <> 1 THEN RAISE EXCEPTION 'FAIL-CLOSED: trip_types id 4 is not ''Ekip Dip'''; END IF;
  SELECT count(*) INTO v_cnt FROM tcc.trip_types WHERE id = 10 AND name = 'Ekip LI';
  IF v_cnt <> 1 THEN RAISE EXCEPTION 'FAIL-CLOSED: trip_types id 10 is not ''Ekip LI'''; END IF;
  SELECT count(*) INTO v_cnt FROM tcc.trip_styles WHERE type = 'Ekip LI';
  IF v_cnt <> 2 THEN RAISE EXCEPTION 'FAIL-CLOSED: % styles on type ''Ekip LI'', expected 2 (1501,1503)', v_cnt; END IF;
  SELECT count(*) INTO v_cnt FROM tcc.trip_styles WHERE style IN ('XT2 LIG','XT4 LIG');
  IF v_cnt <> 0 THEN RAISE EXCEPTION 'FAIL-CLOSED: style name collision on XT2/XT4 LIG'; END IF;

  -- (2) Guard: manufacturer consistency between target type and the styles
  SELECT manufacturer_id INTO v_mfg_type FROM tcc.trip_types WHERE id = 4;
  SELECT count(DISTINCT mfg_id) INTO v_mfg_styles FROM tcc.trip_styles WHERE id IN (1501,1503);
  IF v_mfg_styles <> 1 OR (SELECT DISTINCT mfg_id FROM tcc.trip_styles WHERE id IN (1501,1503)) <> v_mfg_type THEN
    RAISE EXCEPTION 'FAIL-CLOSED: manufacturer mismatch between trip_types id 4 (%) and styles 1501/1503', v_mfg_type;
  END IF;

  -- (3) Backup for reversibility
  DROP TABLE IF EXISTS tcc.ekip_li_repoint_backup_20260609;
  CREATE TABLE tcc.ekip_li_repoint_backup_20260609 AS
    SELECT id, type, style FROM tcc.trip_styles WHERE id IN (1501,1503);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 2 THEN RAISE EXCEPTION 'FAIL-CLOSED: backup captured %, expected 2', v_cnt; END IF;

  -- (4) Repoint + class-faithful style rename
  UPDATE tcc.trip_styles ts SET type = 'Ekip Dip', style = v.newstyle
  FROM (VALUES (1501, 'XT2 LIG'), (1503, 'XT4 LIG')) AS v(id, newstyle)
  WHERE ts.id = v.id;
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 2 THEN RAISE EXCEPTION 'FAIL-CLOSED: repointed %, expected 2', v_cnt; END IF;

  -- (5) Delete the orphaned type row (guard: truly orphaned first)
  SELECT count(*) INTO v_cnt FROM tcc.trip_styles WHERE type = 'Ekip LI';
  IF v_cnt <> 0 THEN RAISE EXCEPTION 'FAIL-CLOSED: % styles still reference ''Ekip LI''', v_cnt; END IF;
  DELETE FROM tcc.trip_types WHERE id = 10 AND name = 'Ekip LI';
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  IF v_cnt <> 1 THEN RAISE EXCEPTION 'FAIL-CLOSED: deleted % type rows, expected 1', v_cnt; END IF;

  -- (6) E2E assert: both styles still resolve through the cascade and derive LIG
  SELECT count(*) INTO v_cnt FROM (
    SELECT c.trip_style_id,
           'L'
           || CASE WHEN bool_or(c.has_stpu) THEN 'S' ELSE '' END
           || CASE WHEN bool_or(c.has_inst) THEN 'I' ELSE '' END
           || CASE WHEN bool_or(c.has_gfpu) THEN 'G' ELSE '' END AS derived
    FROM public.vw_trip_unit_cascade c
    WHERE c.trip_style_id IN (1501,1503)
    GROUP BY c.trip_style_id
  ) d
  WHERE d.derived = 'LIG';
  IF v_cnt <> 2 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: cascade post-repoint resolves %/2 styles as LIG', v_cnt;
  END IF;

  RAISE NOTICE 'Migration 025 OK: 1501/1503 repointed to Ekip Dip as XT2 LIG / XT4 LIG; orphaned ''Ekip LI'' type deleted; backup tcc.ekip_li_repoint_backup_20260609.';
END $mig$;
