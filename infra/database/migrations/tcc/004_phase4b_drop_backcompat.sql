-- =============================================================================
-- Decision-012 - Phase 4b: terminal back-compat cleanup.
--
-- IRREVERSIBLE: no data DOWN. The back-compat views are trivially
-- re-creatable from tcc.* if ever needed; the orphaned _pre_rebuild/_v2 table
-- data is intentionally retired by this migration.
-- =============================================================================

BEGIN;

CREATE TEMP TABLE phase4b_drop_targets (
  schema_name text NOT NULL,
  object_name text NOT NULL,
  object_kind text NOT NULL CHECK (object_kind IN ('view', 'table')),
  PRIMARY KEY (schema_name, object_name)
) ON COMMIT DROP;

INSERT INTO phase4b_drop_targets (schema_name, object_name, object_kind) VALUES
  ('public','tcc_brk_iccb','view'),
  ('public','tcc_brk_iccb_styles','view'),
  ('public','tcc_brk_mccb','view'),
  ('public','tcc_brk_mccb_styles','view'),
  ('public','tcc_brk_pcb','view'),
  ('public','tcc_brk_pcb_styles','view'),
  ('public','tcc_emt','view'),
  ('public','tcc_emt_band_names','view'),
  ('public','tcc_emt_curves','view'),
  ('public','tcc_emt_frame_amps','view'),
  ('public','tcc_emt_frames','view'),
  ('public','tcc_emt_pickups','view'),
  ('public','tcc_emt_sections','view'),
  ('public','tcc_etu_gfd_bands','view'),
  ('public','tcc_etu_gfd_equations','view'),
  ('public','tcc_etu_gfpu_pickups','view'),
  ('public','tcc_etu_inst_curves','view'),
  ('public','tcc_etu_inst_pickups','view'),
  ('public','tcc_etu_ltd_bands','view'),
  ('public','tcc_etu_ltd_params','view'),
  ('public','tcc_etu_ltpu_multipliers','view'),
  ('public','tcc_etu_ltpu_pickups','view'),
  ('public','tcc_etu_plugs','view'),
  ('public','tcc_etu_sensor_maint','view'),
  ('public','tcc_etu_sensor_params','view'),
  ('public','tcc_etu_sensors','view'),
  ('public','tcc_etu_settings','view'),
  ('public','tcc_etu_std_bands','view'),
  ('public','tcc_etu_std_equations','view'),
  ('public','tcc_etu_stpu_overrides','view'),
  ('public','tcc_etu_stpu_pickups','view'),
  ('public','tcc_manufacturers','view'),
  ('public','tcc_tmt_amps','view'),
  ('public','tcc_tmt_curves','view'),
  ('public','tcc_tmt_frames','view'),
  ('public','tcc_tmt_settings','view'),
  ('public','tcc_tmt_thermal_adj','view'),
  ('public','tcc_trip_styles','view'),
  ('public','tcc_trip_types','view'),
  ('work','tcc_relay_curve_points_tcp','view'),
  ('work','tcc_relay_curve_rows_bsl','view'),
  ('work','tcc_relay_curve_rows_iec','view'),
  ('work','tcc_relay_curve_rows_meq','view'),
  ('work','tcc_relay_curve_rows_pcd','view'),
  ('work','tcc_relay_curve_rows_swz','view'),
  ('work','tcc_relay_curves_bsl','view'),
  ('work','tcc_relay_curves_egc','view'),
  ('work','tcc_relay_curves_iec','view'),
  ('work','tcc_relay_curves_lrm','view'),
  ('work','tcc_relay_curves_meq','view'),
  ('work','tcc_relay_curves_pcd','view'),
  ('work','tcc_relay_curves_rxd','view'),
  ('work','tcc_relay_curves_swz','view'),
  ('work','tcc_relay_curves_tcp','view'),
  ('work','tcc_relay_devices','view'),
  ('work','tcc_relay_discrete_values','view'),
  ('work','tcc_relay_line_sections','view'),
  ('work','tcc_relay_ranges','view'),
  ('work','tcc_relay_td_sections','view'),
  ('work','tcc_relays','view'),
  ('public','tcc_etu_gfd_equations_pre_rebuild','table'),
  ('public','tcc_etu_inst_curves_pre_rebuild','table'),
  ('public','tcc_etu_ltd_params_pre_rebuild','table'),
  ('public','tcc_etu_ltpu_multipliers_pre_rebuild','table'),
  ('public','tcc_etu_plugs_pre_rebuild','table'),
  ('public','tcc_etu_sensor_maint_pre_rebuild','table'),
  ('public','tcc_etu_sensor_params_pre_rebuild','table'),
  ('public','tcc_etu_settings_pre_rebuild','table'),
  ('public','tcc_etu_std_equations_pre_rebuild','table'),
  ('public','tcc_etu_stpu_overrides_pre_rebuild','table'),
  ('public','tcc_etu_sensor_maint_v2','table');

CREATE TEMP TABLE phase4b_must_keep (
  schema_name text NOT NULL,
  object_name text NOT NULL,
  PRIMARY KEY (schema_name, object_name)
) ON COMMIT DROP;

INSERT INTO phase4b_must_keep (schema_name, object_name) VALUES
  ('public','tcc_etu_gfd_bands_pre_rebuild'),
  ('public','tcc_etu_gfpu_pickups_pre_rebuild'),
  ('public','tcc_etu_inst_pickups_pre_rebuild'),
  ('public','tcc_etu_ltd_bands_pre_rebuild'),
  ('public','tcc_etu_ltpu_pickups_pre_rebuild'),
  ('public','tcc_etu_sensors_pre_rebuild'),
  ('public','tcc_etu_std_bands_pre_rebuild'),
  ('public','tcc_etu_stpu_pickups_pre_rebuild'),
  ('public','tcc_trip_styles_pre_rebuild'),
  ('public','tcc_manufacturers_pre_rebuild'),
  ('public','sops_v2'),
  ('public','tcc_test_plans'),
  ('public','tcc_test_results'),
  ('tcc','etu_sensor_maint_id_seq'),
  ('tcc','etu_sensor_maint'),
  ('tcc','manufacturers'),
  ('tcc','relay_devices'),
  ('tcc','relays');

DO $$
DECLARE
  missing text[] := ARRAY[]::text[];
  view_count integer;
  table_count integer;
  body_ref_count integer;
  external_dep_count integer;
  sequence_coupling_count integer;
  canonical_sequence_owner text;
BEGIN
  SELECT
      COALESCE(
        array_agg(format('%I.%I', schema_name, object_name) ORDER BY object_kind, schema_name, object_name)
          FILTER (WHERE to_regclass(format('%I.%I', schema_name, object_name)) IS NULL),
        ARRAY[]::text[]
      ),
      count(*) FILTER (WHERE object_kind = 'view'),
      count(*) FILTER (WHERE object_kind = 'table')
    INTO missing, view_count, table_count
    FROM phase4b_drop_targets;

  IF array_length(missing, 1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: missing Phase 4b drop target(s): %', array_to_string(missing, ', ');
  END IF;

  IF view_count <> 60 OR table_count <> 11 THEN
    RAISE EXCEPTION 'ABORT: expected 60 views and 11 tables, found % views and % tables.', view_count, table_count;
  END IF;

  WITH existing AS (
    SELECT t.*, c.oid
      FROM phase4b_drop_targets t
      JOIN pg_namespace n ON n.nspname = t.schema_name
      JOIN pg_class c ON c.relnamespace = n.oid AND c.relname = t.object_name
  ), tokens AS (
    SELECT schema_name, object_name, object_kind, oid, schema_name || '.' || object_name AS token FROM existing
    UNION ALL
    SELECT schema_name, object_name, object_kind, oid, object_name AS token FROM existing
  ), functions AS (
    SELECT p.oid AS objid,
           format('%I.%I(%s)', n.nspname, p.proname, pg_get_function_identity_arguments(p.oid)) AS object_name,
           pg_get_functiondef(p.oid) AS body
      FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE p.prokind IN ('f','p')
  ), views AS (
    SELECT c.oid AS objid,
           format('%I.%I', n.nspname, c.relname) AS object_name,
           pg_get_viewdef(c.oid, true) AS body
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE c.relkind IN ('v','m')
  ), rules AS (
    SELECT r.oid AS objid,
           format('%I.%I:%I', n.nspname, c.relname, r.rulename) AS object_name,
           pg_get_ruledef(r.oid, true) AS body,
           c.oid AS rel_oid
      FROM pg_rewrite r
      JOIN pg_class c ON c.oid = r.ev_class
      JOIN pg_namespace n ON n.oid = c.relnamespace
  ), triggers AS (
    SELECT t.oid AS objid,
           format('%I.%I:%I', n.nspname, c.relname, t.tgname) AS object_name,
           pg_get_triggerdef(t.oid, true) AS body
      FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE NOT t.tgisinternal
  ), bodies AS (
    SELECT 'function' AS object_type, objid, object_name, body, NULL::oid AS rel_oid FROM functions
    UNION ALL SELECT 'view', objid, object_name, body, objid FROM views
    UNION ALL SELECT 'rule', objid, object_name, body, rel_oid FROM rules
    UNION ALL SELECT 'trigger', objid, object_name, body, NULL::oid FROM triggers
  ), body_refs AS (
    SELECT b.object_type, b.object_name, tok.schema_name || '.' || tok.object_name AS referenced_object, tok.token
      FROM bodies b
      JOIN tokens tok ON tok.oid IS NOT NULL
       AND b.body ~ ('(^|[^[:alnum:]_])' || replace(tok.token, '.', '[.]') || '([^[:alnum:]_]|$)')
     WHERE COALESCE(b.rel_oid, 0) <> tok.oid
  )
  SELECT count(*) INTO body_ref_count FROM body_refs;

  IF body_ref_count <> 0 THEN
    RAISE EXCEPTION 'ABORT: % DB object body reference(s) still point at the Phase 4b drop-set.', body_ref_count;
  END IF;

  WITH existing AS (
    SELECT t.*, c.oid
      FROM phase4b_drop_targets t
      JOIN pg_namespace n ON n.nspname = t.schema_name
      JOIN pg_class c ON c.relnamespace = n.oid AND c.relname = t.object_name
  ), external_deps AS (
    SELECT DISTINCT dep.classid, dep.objid, dep.deptype, e.schema_name, e.object_name
      FROM existing e
      JOIN pg_depend dep ON dep.refclassid = 'pg_class'::regclass AND dep.refobjid = e.oid
     WHERE dep.deptype NOT IN ('i','a')
       AND NOT (
         dep.classid = 'pg_rewrite'::regclass
         AND dep.objid IN (SELECT oid FROM pg_rewrite WHERE ev_class = e.oid)
       )
  )
  SELECT count(*) INTO external_dep_count FROM external_deps;

  IF external_dep_count <> 0 THEN
    RAISE EXCEPTION 'ABORT: % external catalog dependency reference(s) still point at the Phase 4b drop-set.', external_dep_count;
  END IF;

  WITH safe_tables AS (
    SELECT schema_name, object_name
      FROM phase4b_drop_targets
     WHERE object_kind = 'table'
  ), safe_owned_sequences AS (
    SELECT seq.oid AS seq_oid,
           format('%I.%I', seq_ns.nspname, seq.relname) AS sequence_fqn,
           format('%I.%I.%I', owner_ns.nspname, owner.relname, owner_att.attname) AS owned_by
      FROM safe_tables st
      JOIN pg_namespace owner_ns ON owner_ns.nspname = st.schema_name
      JOIN pg_class owner ON owner.relnamespace = owner_ns.oid AND owner.relname = st.object_name
      JOIN pg_depend dep ON dep.refobjid = owner.oid AND dep.refobjsubid > 0 AND dep.deptype = 'a'
      JOIN pg_class seq ON seq.oid = dep.objid AND seq.relkind = 'S'
      JOIN pg_namespace seq_ns ON seq_ns.oid = seq.relnamespace
      JOIN pg_attribute owner_att ON owner_att.attrelid = owner.oid AND owner_att.attnum = dep.refobjsubid
  ), default_deps AS (
    SELECT seq.oid AS seq_oid,
           def_ns.nspname AS default_schema,
           defrel.relname AS default_table,
           format('%I.%I.%I', def_ns.nspname, defrel.relname, defatt.attname) AS default_fqn
      FROM pg_attrdef ad
      JOIN pg_depend dep
        ON dep.classid = 'pg_attrdef'::regclass
       AND dep.objid = ad.oid
       AND dep.refclassid = 'pg_class'::regclass
      JOIN pg_class seq ON seq.oid = dep.refobjid AND seq.relkind = 'S'
      JOIN pg_class defrel ON defrel.oid = ad.adrelid
      JOIN pg_namespace def_ns ON def_ns.oid = defrel.relnamespace
      JOIN pg_attribute defatt ON defatt.attrelid = defrel.oid AND defatt.attnum = ad.adnum
  ), sequence_couplings AS (
    SELECT sos.sequence_fqn, sos.owned_by, dd.default_fqn AS kept_dependent
      FROM safe_owned_sequences sos
      JOIN default_deps dd ON dd.seq_oid = sos.seq_oid
     WHERE NOT EXISTS (
       SELECT 1
         FROM safe_tables st
        WHERE st.schema_name = dd.default_schema
          AND st.object_name = dd.default_table
     )
  )
  SELECT count(*) INTO sequence_coupling_count FROM sequence_couplings;

  IF sequence_coupling_count <> 0 THEN
    RAISE EXCEPTION 'ABORT: % safe-to-drop table-owned sequence coupling(s) still have kept dependents.', sequence_coupling_count;
  END IF;

  SELECT format('%I.%I.%I', owner_ns.nspname, owner.relname, owner_att.attname)
    INTO canonical_sequence_owner
    FROM pg_depend dep
    JOIN pg_class seq ON seq.oid = dep.objid
    JOIN pg_class owner ON owner.oid = dep.refobjid
    JOIN pg_namespace owner_ns ON owner_ns.oid = owner.relnamespace
    JOIN pg_attribute owner_att ON owner_att.attrelid = owner.oid AND owner_att.attnum = dep.refobjsubid
   WHERE dep.classid = 'pg_class'::regclass
     AND dep.refclassid = 'pg_class'::regclass
     AND dep.deptype = 'a'
     AND seq.oid = to_regclass('tcc.etu_sensor_maint_id_seq');

  IF canonical_sequence_owner IS DISTINCT FROM 'tcc.etu_sensor_maint.id' THEN
    RAISE EXCEPTION 'ABORT: tcc.etu_sensor_maint_id_seq owner is %, expected tcc.etu_sensor_maint.id.', canonical_sequence_owner;
  END IF;
END $$;

DROP VIEW public.tcc_brk_iccb RESTRICT;
DROP VIEW public.tcc_brk_iccb_styles RESTRICT;
DROP VIEW public.tcc_brk_mccb RESTRICT;
DROP VIEW public.tcc_brk_mccb_styles RESTRICT;
DROP VIEW public.tcc_brk_pcb RESTRICT;
DROP VIEW public.tcc_brk_pcb_styles RESTRICT;
DROP VIEW public.tcc_emt RESTRICT;
DROP VIEW public.tcc_emt_band_names RESTRICT;
DROP VIEW public.tcc_emt_curves RESTRICT;
DROP VIEW public.tcc_emt_frame_amps RESTRICT;
DROP VIEW public.tcc_emt_frames RESTRICT;
DROP VIEW public.tcc_emt_pickups RESTRICT;
DROP VIEW public.tcc_emt_sections RESTRICT;
DROP VIEW public.tcc_etu_gfd_bands RESTRICT;
DROP VIEW public.tcc_etu_gfd_equations RESTRICT;
DROP VIEW public.tcc_etu_gfpu_pickups RESTRICT;
DROP VIEW public.tcc_etu_inst_curves RESTRICT;
DROP VIEW public.tcc_etu_inst_pickups RESTRICT;
DROP VIEW public.tcc_etu_ltd_bands RESTRICT;
DROP VIEW public.tcc_etu_ltd_params RESTRICT;
DROP VIEW public.tcc_etu_ltpu_multipliers RESTRICT;
DROP VIEW public.tcc_etu_ltpu_pickups RESTRICT;
DROP VIEW public.tcc_etu_plugs RESTRICT;
DROP VIEW public.tcc_etu_sensor_maint RESTRICT;
DROP VIEW public.tcc_etu_sensor_params RESTRICT;
DROP VIEW public.tcc_etu_sensors RESTRICT;
DROP VIEW public.tcc_etu_settings RESTRICT;
DROP VIEW public.tcc_etu_std_bands RESTRICT;
DROP VIEW public.tcc_etu_std_equations RESTRICT;
DROP VIEW public.tcc_etu_stpu_overrides RESTRICT;
DROP VIEW public.tcc_etu_stpu_pickups RESTRICT;
DROP VIEW public.tcc_manufacturers RESTRICT;
DROP VIEW public.tcc_tmt_amps RESTRICT;
DROP VIEW public.tcc_tmt_curves RESTRICT;
DROP VIEW public.tcc_tmt_frames RESTRICT;
DROP VIEW public.tcc_tmt_settings RESTRICT;
DROP VIEW public.tcc_tmt_thermal_adj RESTRICT;
DROP VIEW public.tcc_trip_styles RESTRICT;
DROP VIEW public.tcc_trip_types RESTRICT;
DROP VIEW work.tcc_relay_curve_points_tcp RESTRICT;
DROP VIEW work.tcc_relay_curve_rows_bsl RESTRICT;
DROP VIEW work.tcc_relay_curve_rows_iec RESTRICT;
DROP VIEW work.tcc_relay_curve_rows_meq RESTRICT;
DROP VIEW work.tcc_relay_curve_rows_pcd RESTRICT;
DROP VIEW work.tcc_relay_curve_rows_swz RESTRICT;
DROP VIEW work.tcc_relay_curves_bsl RESTRICT;
DROP VIEW work.tcc_relay_curves_egc RESTRICT;
DROP VIEW work.tcc_relay_curves_iec RESTRICT;
DROP VIEW work.tcc_relay_curves_lrm RESTRICT;
DROP VIEW work.tcc_relay_curves_meq RESTRICT;
DROP VIEW work.tcc_relay_curves_pcd RESTRICT;
DROP VIEW work.tcc_relay_curves_rxd RESTRICT;
DROP VIEW work.tcc_relay_curves_swz RESTRICT;
DROP VIEW work.tcc_relay_curves_tcp RESTRICT;
DROP VIEW work.tcc_relay_devices RESTRICT;
DROP VIEW work.tcc_relay_discrete_values RESTRICT;
DROP VIEW work.tcc_relay_line_sections RESTRICT;
DROP VIEW work.tcc_relay_ranges RESTRICT;
DROP VIEW work.tcc_relay_td_sections RESTRICT;
DROP VIEW work.tcc_relays RESTRICT;

DROP TABLE public.tcc_etu_gfd_equations_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_inst_curves_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_ltd_params_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_ltpu_multipliers_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_plugs_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_sensor_maint_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_sensor_params_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_settings_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_std_equations_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_stpu_overrides_pre_rebuild RESTRICT;
DROP TABLE public.tcc_etu_sensor_maint_v2 RESTRICT;

DO $$
DECLARE
  still_present text[] := ARRAY[]::text[];
  missing_must_keep text[] := ARRAY[]::text[];
  tcc_base_tables integer;
BEGIN
  SELECT COALESCE(
      array_agg(format('%I.%I', schema_name, object_name) ORDER BY object_kind, schema_name, object_name)
        FILTER (WHERE to_regclass(format('%I.%I', schema_name, object_name)) IS NOT NULL),
      ARRAY[]::text[]
    )
    INTO still_present
    FROM phase4b_drop_targets;

  SELECT COALESCE(
      array_agg(format('%I.%I', schema_name, object_name) ORDER BY schema_name, object_name)
        FILTER (WHERE to_regclass(format('%I.%I', schema_name, object_name)) IS NULL),
      ARRAY[]::text[]
    )
    INTO missing_must_keep
    FROM phase4b_must_keep;

  SELECT count(*)
    INTO tcc_base_tables
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'tcc'
     AND c.relkind IN ('r','p');

  IF array_length(still_present, 1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: Phase 4b dropped object(s) still present: %', array_to_string(still_present, ', ');
  END IF;

  IF array_length(missing_must_keep, 1) IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: Phase 4b must-keep object(s) missing: %', array_to_string(missing_must_keep, ', ');
  END IF;

  IF tcc_base_tables <> 60 THEN
    RAISE EXCEPTION 'ABORT: expected 60 tcc base tables after Phase 4b, found %.', tcc_base_tables;
  END IF;
END $$;

COMMIT;
