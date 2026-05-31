-- =============================================================================
-- Decision-012 — Phase 2 (EXPAND): unify breaker (public.tcc_*) + relay
-- (work.tcc_relay_*) catalogs into one tcc.* schema. NON-DESTRUCTIVE + REVERSIBLE.
--
-- Authority: ARCHITECTURE Decision 012 / 010 / 003; plan
--   apex-ops-substrate/.claude/PLATFORM/DECISION_012_TCC_SCHEMA_UNIFICATION_PLAN_2026-05-30.md
-- Decisions locked: A=drop `tcc_` prefix; B=documented-deferred apparatus anchor;
--   D1=test_plans/test_results stay in public (NOT carried);
--   D2=name-based manufacturer remap (live-verified: 189-mfr renumber, 0 orphan/0 ambiguous).
--
-- SAFETY MODEL:
--   * Runs in ONE transaction. Any guard failure -> RAISE -> full ROLLBACK (prod untouched).
--   * SET SCHEMA / RENAME are metadata-only (no table rewrite) -> fast even for 1.5M-row tables.
--   * Back-compat VIEWS preserve public.tcc_* and work.tcc_relay_* names, so the running app,
--     views (vw_sensor_calc_context, vw_trip_unit_cascade) and functions
--     (fn_sensor_available_settings, fn_calculate_test_currents, fn_evaluate_test_results)
--     keep working with NO route change. Route repoint is Phase 3; view drop is Phase 4.
--   * RUN ON A SUPABASE TEST BRANCH FIRST, run parity probes against it, THEN prod.
--
-- NOT in this phase: route SQL repoint (Phase 3); _pre_rebuild/_v2 + back-compat-view
--   drop (Phase 4); relay-specific enum relocation (deferred, cross-schema ref is valid);
--   relay manufacturer_source_id -> tcc.manufacturers wiring (Decision-010-B deferred).
-- =============================================================================

BEGIN;

-- ── 0. Preconditions ────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'tcc') THEN
    RAISE EXCEPTION 'ABORT: schema "tcc" already exists (Phase 2 expects it absent).';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema='public' AND table_name='tcc_manufacturers') THEN
    RAISE EXCEPTION 'ABORT: public.tcc_manufacturers (canonical) not found.';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema='public' AND table_name='tcc_manufacturers_pre_rebuild') THEN
    RAISE EXCEPTION 'ABORT: public.tcc_manufacturers_pre_rebuild not found (needed for the name-based remap).';
  END IF;
END $$;

-- carry-set (60 tables): 39 base breaker (public) + 21 relay (work).
-- new name = old name minus the leading `tcc_`. test_plans/test_results NOT listed (D1).
CREATE TEMP TABLE _d012_carry (src_schema text, tbl text) ON COMMIT DROP;
INSERT INTO _d012_carry (src_schema, tbl) VALUES
  -- breaker (public)
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
  -- relay (work)
  ('work','tcc_relays'),('work','tcc_relay_devices'),('work','tcc_relay_line_sections'),
  ('work','tcc_relay_td_sections'),('work','tcc_relay_ranges'),('work','tcc_relay_discrete_values'),
  ('work','tcc_relay_curves_iec'),('work','tcc_relay_curves_swz'),('work','tcc_relay_curves_bsl'),
  ('work','tcc_relay_curves_meq'),('work','tcc_relay_curves_pcd'),('work','tcc_relay_curves_lrm'),
  ('work','tcc_relay_curves_rxd'),('work','tcc_relay_curves_egc'),('work','tcc_relay_curves_tcp'),
  ('work','tcc_relay_curve_rows_iec'),('work','tcc_relay_curve_rows_swz'),
  ('work','tcc_relay_curve_rows_bsl'),('work','tcc_relay_curve_rows_meq'),
  ('work','tcc_relay_curve_rows_pcd'),('work','tcc_relay_curve_points_tcp');

DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM _d012_carry;
  IF n <> 60 THEN RAISE EXCEPTION 'ABORT: carry-set has % tables, expected 60.', n; END IF;
  -- every carry table must exist in its stated source schema
  SELECT count(*) INTO n FROM _d012_carry c
   WHERE NOT EXISTS (SELECT 1 FROM information_schema.tables t
                     WHERE t.table_schema=c.src_schema AND t.table_name=c.tbl AND t.table_type='BASE TABLE');
  IF n > 0 THEN RAISE EXCEPTION 'ABORT: % carry table(s) not found as base tables in their source schema.', n; END IF;
END $$;

-- ── 1. Manufacturer name-based remap (D2, live-verified) ─────────────────────
-- The 5 tables whose manufacturer_id FK targets _pre_rebuild (old id-space).
-- Drop the old FK, translate id by NAME to canonical id-space, then (FK re-added post-move).
ALTER TABLE public.tcc_brk_iccb   DROP CONSTRAINT tcc_brk_iccb_manufacturer_id_fkey;
ALTER TABLE public.tcc_brk_mccb   DROP CONSTRAINT tcc_brk_mccb_manufacturer_id_fkey;
ALTER TABLE public.tcc_brk_pcb    DROP CONSTRAINT tcc_brk_pcb_manufacturer_id_fkey;
ALTER TABLE public.tcc_emt        DROP CONSTRAINT tcc_emt_manufacturer_id_fkey;
ALTER TABLE public.tcc_trip_types DROP CONSTRAINT tcc_trip_types_manufacturer_id_fkey;

DO $$
DECLARE
  tbl   text;
  updated int;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['tcc_brk_iccb','tcc_brk_mccb','tcc_brk_pcb','tcc_emt','tcc_trip_types'] LOOP
    EXECUTE format($f$
      UPDATE public.%I b
         SET manufacturer_id = c.id
        FROM public.tcc_manufacturers_pre_rebuild p
        JOIN public.tcc_manufacturers c ON c.mfr_name = p.name
       WHERE p.id = b.manufacturer_id
         AND c.id <> b.manufacturer_id
    $f$, tbl);
    GET DIAGNOSTICS updated = ROW_COUNT;
    RAISE NOTICE 'remap %: % row(s) retargeted', tbl, updated;
  END LOOP;
END $$;

-- GUARD: every manufacturer_id in the 5 tables must now resolve in canonical tcc_manufacturers.
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
    AND manufacturer_id NOT IN (SELECT id FROM public.tcc_manufacturers);
  IF bad > 0 THEN
    RAISE EXCEPTION 'ABORT: % breaker/trip-type row(s) have a manufacturer_id absent from canonical tcc_manufacturers after remap.', bad;
  END IF;
END $$;

-- ── 2. CREATE SCHEMA + move/rename (drop `tcc_` prefix) ──────────────────────
CREATE SCHEMA tcc;

DO $$
DECLARE r record; newname text;
BEGIN
  FOR r IN SELECT src_schema, tbl FROM _d012_carry LOOP
    newname := substr(r.tbl, 5);   -- strip leading 'tcc_'
    EXECUTE format('ALTER TABLE %I.%I SET SCHEMA tcc', r.src_schema, r.tbl);
    EXECUTE format('ALTER TABLE tcc.%I RENAME TO %I', r.tbl, newname);
  END LOOP;
END $$;

-- ── 3. Re-add manufacturer FKs -> canonical tcc.manufacturers ────────────────
ALTER TABLE tcc.brk_iccb   ADD CONSTRAINT brk_iccb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES tcc.manufacturers (id);
ALTER TABLE tcc.brk_mccb   ADD CONSTRAINT brk_mccb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES tcc.manufacturers (id);
ALTER TABLE tcc.brk_pcb    ADD CONSTRAINT brk_pcb_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES tcc.manufacturers (id);
ALTER TABLE tcc.emt        ADD CONSTRAINT emt_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES tcc.manufacturers (id);
ALTER TABLE tcc.trip_types ADD CONSTRAINT trip_types_manufacturer_id_fkey
  FOREIGN KEY (manufacturer_id) REFERENCES tcc.manufacturers (id);

-- ── 4. Back-compat VIEWS: recreate old names in old schema over the moved tcc.* ─
-- Keeps routes (unqualified public.* / qualified work.*), views, and functions working
-- unchanged. Catalog is read-only in the app, so simple SELECT * views are sufficient.
DO $$
DECLARE r record; newname text;
BEGIN
  FOR r IN SELECT src_schema, tbl FROM _d012_carry LOOP
    newname := substr(r.tbl, 5);
    EXECUTE format('CREATE VIEW %I.%I AS SELECT * FROM tcc.%I', r.src_schema, r.tbl, newname);
  END LOOP;
END $$;

-- ── 5. Final guards ──────────────────────────────────────────────────────────
DO $$
DECLARE missing int;
BEGIN
  -- every carried table now lives in tcc (base table) AND a back-compat view exists at the old name
  SELECT count(*) INTO missing FROM _d012_carry c
   WHERE NOT EXISTS (SELECT 1 FROM information_schema.tables t
                     WHERE t.table_schema='tcc' AND t.table_name=substr(c.tbl,5) AND t.table_type='BASE TABLE');
  IF missing > 0 THEN RAISE EXCEPTION 'ABORT: % carried table(s) missing from tcc.', missing; END IF;

  SELECT count(*) INTO missing FROM _d012_carry c
   WHERE NOT EXISTS (SELECT 1 FROM information_schema.views v
                     WHERE v.table_schema=c.src_schema AND v.table_name=c.tbl);
  IF missing > 0 THEN RAISE EXCEPTION 'ABORT: % back-compat view(s) missing.', missing; END IF;

  -- relay 503-guard surface must still resolve in work (now as views)
  SELECT count(*) INTO missing FROM (VALUES
    ('tcc_relays'),('tcc_relay_devices'),('tcc_relay_line_sections'),('tcc_relay_td_sections'),
    ('tcc_relay_ranges'),('tcc_relay_curves_iec'),('tcc_relay_curve_rows_iec'),
    ('tcc_relay_curves_tcp'),('tcc_relay_curve_points_tcp')
  ) g(name)
  WHERE NOT EXISTS (SELECT 1 FROM information_schema.tables t
                    WHERE t.table_schema='work' AND t.table_name=g.name);
  IF missing > 0 THEN RAISE EXCEPTION 'ABORT: % relay-guard name(s) not resolvable in work.', missing; END IF;
END $$;

-- Manufacturers row-count parity sanity (move is metadata-only; this just confirms).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM tcc.manufacturers;
  IF n <> 450 THEN RAISE EXCEPTION 'ABORT: tcc.manufacturers has % rows, expected 450.', n; END IF;
END $$;

COMMIT;

-- Post-conditions (informational): public.tcc_* + work.tcc_relay_* now resolve to
-- back-compat views over tcc.*; the app, views, and functions are unchanged.
-- Next: Phase 3 repoints route/probe/test SQL to tcc.* and parity-gates; Phase 4 drops
-- the back-compat views + _pre_rebuild/_v2 after soak.
