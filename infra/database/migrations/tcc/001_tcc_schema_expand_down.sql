-- =============================================================================
-- Decision-012 — Phase 2 (EXPAND) ROLLBACK / DOWN.
-- Reverses 001_tcc_schema_expand.sql: returns the 60 catalog tables to
-- public.tcc_* / work.tcc_relay_*, restores the _pre_rebuild manufacturer FK
-- targets (reverses the name-based remap), drops the tcc schema.
-- Single transaction; any guard failure -> ROLLBACK. Use only while the back-compat
-- views still exist (i.e. before Phase 4 drops them / before route repoint relies on tcc.*).
-- =============================================================================

BEGIN;

-- mirror carry-set (new tcc.* name = old minus 'tcc_')
CREATE TEMP TABLE _d012_carry (src_schema text, tbl text) ON COMMIT DROP;
INSERT INTO _d012_carry (src_schema, tbl) VALUES
  ('public','tcc_brk_iccb'),('public','tcc_brk_iccb_styles'),
  ('public','tcc_brk_mccb'),('public','tcc_brk_mccb_styles'),
  ('public','tcc_brk_pcb'),('public','tcc_brk_pcb_styles'),
  ('public','tcc_emt'),('public','tcc_emt_band_names'),('public','tcc_emt_curves'),
  ('public','tcc_emt_frame_amps'),('public','tcc_emt_frames'),('public','tcc_emt_pickups'),
  ('public','tcc_emt_sections'),
  ('public','tcc_etu_gfd_bands'),('public','tcc_etu_gfd_equations'),
  ('public','tcc_etu_gfpu_pickups'),('public','tcc_etu_inst_curves'),
  ('public','tcc_etu_inst_pickups'),('public','tcc_etu_ltd_bands'),
  ('public','tcc_etu_ltd_params'),('public','tcc_etu_ltpu_multipliers'),
  ('public','tcc_etu_ltpu_pickups'),('public','tcc_etu_plugs'),
  ('public','tcc_etu_sensor_maint'),('public','tcc_etu_sensor_params'),
  ('public','tcc_etu_sensors'),('public','tcc_etu_settings'),
  ('public','tcc_etu_std_bands'),('public','tcc_etu_std_equations'),
  ('public','tcc_etu_stpu_overrides'),('public','tcc_etu_stpu_pickups'),
  ('public','tcc_manufacturers'),
  ('public','tcc_tmt_amps'),('public','tcc_tmt_curves'),('public','tcc_tmt_frames'),
  ('public','tcc_tmt_settings'),('public','tcc_tmt_thermal_adj'),
  ('public','tcc_trip_styles'),('public','tcc_trip_types'),
  ('work','tcc_relays'),('work','tcc_relay_devices'),('work','tcc_relay_line_sections'),
  ('work','tcc_relay_td_sections'),('work','tcc_relay_ranges'),('work','tcc_relay_discrete_values'),
  ('work','tcc_relay_curves_iec'),('work','tcc_relay_curves_swz'),('work','tcc_relay_curves_bsl'),
  ('work','tcc_relay_curves_meq'),('work','tcc_relay_curves_pcd'),('work','tcc_relay_curves_lrm'),
  ('work','tcc_relay_curves_rxd'),('work','tcc_relay_curves_egc'),('work','tcc_relay_curves_tcp'),
  ('work','tcc_relay_curve_rows_iec'),('work','tcc_relay_curve_rows_swz'),
  ('work','tcc_relay_curve_rows_bsl'),('work','tcc_relay_curve_rows_meq'),
  ('work','tcc_relay_curve_rows_pcd'),('work','tcc_relay_curve_points_tcp');

-- 1. Drop back-compat views (free the old names before moving tables back)
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT src_schema, tbl FROM _d012_carry LOOP
    EXECUTE format('DROP VIEW IF EXISTS %I.%I', r.src_schema, r.tbl);
  END LOOP;
END $$;

-- 2. Move tables back to source schema + restore tcc_ prefix
DO $$
DECLARE r record; newname text;
BEGIN
  FOR r IN SELECT src_schema, tbl FROM _d012_carry LOOP
    newname := substr(r.tbl, 5);
    EXECUTE format('ALTER TABLE tcc.%I SET SCHEMA %I', newname, r.src_schema);
    EXECUTE format('ALTER TABLE %I.%I RENAME TO %I', r.src_schema, newname, r.tbl);
  END LOOP;
END $$;

-- 3. Drop the canonical manufacturer FKs (added by the up migration)
ALTER TABLE public.tcc_brk_iccb   DROP CONSTRAINT brk_iccb_manufacturer_id_fkey;
ALTER TABLE public.tcc_brk_mccb   DROP CONSTRAINT brk_mccb_manufacturer_id_fkey;
ALTER TABLE public.tcc_brk_pcb    DROP CONSTRAINT brk_pcb_manufacturer_id_fkey;
ALTER TABLE public.tcc_emt        DROP CONSTRAINT emt_manufacturer_id_fkey;
ALTER TABLE public.tcc_trip_types DROP CONSTRAINT trip_types_manufacturer_id_fkey;

-- 4. Reverse the name-based remap (canonical id-space -> _pre_rebuild id-space, by name)
-- TWO-PHASE reverse-remap (same UNIQUE(manufacturer_id,name) collision avoidance as UP).
DO $$
DECLARE tbl text; n1 int; n2 int;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['tcc_brk_iccb','tcc_brk_mccb','tcc_brk_pcb','tcc_emt','tcc_trip_types'] LOOP
    EXECUTE format($f$
      UPDATE public.%I b
         SET manufacturer_id = p.id + 100000
        FROM public.tcc_manufacturers c
        JOIN public.tcc_manufacturers_pre_rebuild p ON p.name = c.mfr_name
       WHERE c.id = b.manufacturer_id
    $f$, tbl);
    GET DIAGNOSTICS n1 = ROW_COUNT;
    EXECUTE format('UPDATE public.%I SET manufacturer_id = manufacturer_id - 100000 WHERE manufacturer_id > 100000', tbl);
    GET DIAGNOSTICS n2 = ROW_COUNT;
    IF n1 <> n2 THEN
      RAISE EXCEPTION 'reverse-remap %: phase A % rows, phase B % (temp-space leak).', tbl, n1, n2;
    END IF;
    RAISE NOTICE 'reverse-remap %: % row(s) translated via temp space', tbl, n1;
  END LOOP;
END $$;

-- GUARD: every manufacturer_id must resolve in _pre_rebuild again
DO $$
DECLARE bad int;
BEGIN
  SELECT count(*) INTO bad FROM (
    SELECT manufacturer_id FROM public.tcc_brk_iccb
    UNION ALL SELECT manufacturer_id FROM public.tcc_brk_mccb
    UNION ALL SELECT manufacturer_id FROM public.tcc_brk_pcb
    UNION ALL SELECT manufacturer_id FROM public.tcc_emt
    UNION ALL SELECT manufacturer_id FROM public.tcc_trip_types
  ) x
  WHERE manufacturer_id IS NOT NULL
    AND manufacturer_id NOT IN (SELECT id FROM public.tcc_manufacturers_pre_rebuild);
  IF bad > 0 THEN
    RAISE EXCEPTION 'ABORT: reverse-remap left % manufacturer_id(s) unresolved in _pre_rebuild.', bad;
  END IF;
END $$;

-- 5. Restore original _pre_rebuild FKs (original constraint names)
ALTER TABLE public.tcc_brk_iccb   ADD CONSTRAINT tcc_brk_iccb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES public.tcc_manufacturers_pre_rebuild (id) ON DELETE CASCADE;
ALTER TABLE public.tcc_brk_mccb   ADD CONSTRAINT tcc_brk_mccb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES public.tcc_manufacturers_pre_rebuild (id) ON DELETE CASCADE;
ALTER TABLE public.tcc_brk_pcb    ADD CONSTRAINT tcc_brk_pcb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES public.tcc_manufacturers_pre_rebuild (id) ON DELETE CASCADE;
ALTER TABLE public.tcc_emt        ADD CONSTRAINT tcc_emt_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES public.tcc_manufacturers_pre_rebuild (id) ON DELETE CASCADE;
ALTER TABLE public.tcc_trip_types ADD CONSTRAINT tcc_trip_types_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES public.tcc_manufacturers_pre_rebuild (id) ON DELETE CASCADE;

-- 6. Drop the now-empty tcc schema
DROP SCHEMA tcc RESTRICT;

COMMIT;
