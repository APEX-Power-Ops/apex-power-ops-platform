-- 022_gfreal_keeper_classfaithful_rename.sql
-- Cosmetic, name-only rename of the §197 GF-REAL keeper styles so the stored
-- trip-style NAME matches the (already-correct, catalog-confirmed) modeled class.
-- The ground (and short-time) elements are GENUINE here (GF-REAL, kept by §197/§199),
-- so this only renames the "-LI" suffix to the derived class. NO flag/curve change;
-- `trip_styles.style` is display-only (not a join key). The §199 precedent
-- (815/2371 "-LI"->"-LIG") generalized.
--
--   5    GE MVT-4     ICCB-LI        -> ICCB-LIG        (LIG)
--   7    GE MVT-4     MCCB-LI        -> MCCB-LIG        (LIG)
--   23   GE SelecTrip MCCB TKR-LI    -> MCCB TKR-LIG    (LIG)
--   24   GE SelecTrip TPR-LI         -> TPR-LIG         (LIG)
--   2458 West DT 700  SPB-LI         -> SPB-LIG         (LIG)
--   1656 Eaton DT 310 E2N/E2NM - LI  -> E2N/E2NM - LSIG (LSIG)
--   1610 FP HSSA      HSSA1 - LI     -> HSSA1 - LSIG    (LSIG)
--
-- HELD (not renamed): ABB Ekip LI (1501,1503) — the "LI" lives in `trip_styles.type`
-- ("Ekip LI"), which is a JOIN key to `trip_types.name` (§195); renaming needs a
-- paired model rename, out of scope for a cosmetic style rename.

DO $mig$
DECLARE
  v_back int;
  v_upd  int;
  v_bad  int;
BEGIN
  -- (1) Backup the old names for reversibility
  DROP TABLE IF EXISTS tcc.gfreal_rename_backup_20260609;
  CREATE TABLE tcc.gfreal_rename_backup_20260609 AS
    SELECT id, style AS old_style FROM tcc.trip_styles
    WHERE id IN (5,7,23,24,2458,1656,1610);
  GET DIAGNOSTICS v_back = ROW_COUNT;
  IF v_back <> 7 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: backup captured % styles, expected 7', v_back;
  END IF;

  -- (2) Rename (explicit per-id, no regex)
  UPDATE tcc.trip_styles ts SET style = v.newname
  FROM (VALUES
    (5,    'ICCB-LIG'),
    (7,    'MCCB-LIG'),
    (23,   'MCCB TKR-LIG'),
    (24,   'TPR-LIG'),
    (2458, 'SPB-LIG'),
    (1656, 'E2N/E2NM - LSIG'),
    (1610, 'HSSA1 - LSIG')
  ) AS v(id, newname)
  WHERE ts.id = v.id;
  GET DIAGNOSTICS v_upd = ROW_COUNT;
  IF v_upd <> 7 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: renamed % styles, expected 7', v_upd;
  END IF;

  -- (3) Assert each renamed name now ENDS WITH its derived class (class-faithful)
  SELECT count(*) INTO v_bad FROM (
    SELECT ts.id, ts.style,
           'L'
           || CASE WHEN bool_or(c.has_stpu) THEN 'S' ELSE '' END
           || CASE WHEN bool_or(c.has_inst) THEN 'I' ELSE '' END
           || CASE WHEN bool_or(c.has_gfpu) THEN 'G' ELSE '' END AS derived
    FROM tcc.trip_styles ts
    JOIN public.vw_trip_unit_cascade c ON c.trip_style_id = ts.id
    WHERE ts.id IN (5,7,23,24,2458,1656,1610)
    GROUP BY ts.id, ts.style
  ) d
  WHERE d.style NOT LIKE '%' || d.derived;
  IF v_bad <> 0 THEN
    RAISE EXCEPTION 'FAIL-CLOSED: % renamed styles do not end with their derived class', v_bad;
  END IF;

  RAISE NOTICE 'Migration 022 OK: 7 GF-REAL keeper styles renamed class-faithful (LIG x5, LSIG x2); backup tcc.gfreal_rename_backup_20260609.';
END $mig$;
