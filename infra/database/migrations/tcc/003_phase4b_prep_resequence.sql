-- =============================================================================
-- Decision-012 - Phase 4b PREP: reassign shared sequence ownership.
-- Reversible sequence metadata only. No drops, no row changes.
-- =============================================================================

BEGIN;

DO $$
DECLARE
  seq_oid oid;
BEGIN
  SELECT to_regclass('public.tcc_etu_sensor_maint_id_seq') INTO seq_oid;

  IF seq_oid IS NULL THEN
    RAISE EXCEPTION 'ABORT: expected sequence public.tcc_etu_sensor_maint_id_seq was not found.';
  END IF;

  IF to_regclass('tcc.etu_sensor_maint_id_seq') IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: target sequence tcc.etu_sensor_maint_id_seq already exists.';
  END IF;

  IF to_regclass('tcc.tcc_etu_sensor_maint_id_seq') IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: intermediate sequence tcc.tcc_etu_sensor_maint_id_seq already exists.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_depend d
      JOIN pg_class owner_rel ON owner_rel.oid = d.refobjid
      JOIN pg_namespace owner_ns ON owner_ns.oid = owner_rel.relnamespace
      JOIN pg_attribute owner_att
        ON owner_att.attrelid = owner_rel.oid
       AND owner_att.attnum = d.refobjsubid
     WHERE d.classid = 'pg_class'::regclass
       AND d.refclassid = 'pg_class'::regclass
       AND d.objid = seq_oid
       AND d.deptype = 'a'
       AND owner_ns.nspname = 'public'
       AND owner_rel.relname = 'tcc_etu_sensor_maint_pre_rebuild'
       AND owner_att.attname = 'id'
  ) THEN
    RAISE EXCEPTION 'ABORT: public.tcc_etu_sensor_maint_id_seq is not owned by public.tcc_etu_sensor_maint_pre_rebuild.id.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_attrdef ad
      JOIN pg_depend d
        ON d.classid = 'pg_attrdef'::regclass
       AND d.objid = ad.oid
       AND d.refclassid = 'pg_class'::regclass
       AND d.refobjid = seq_oid
      JOIN pg_class rel ON rel.oid = ad.adrelid
      JOIN pg_namespace rel_ns ON rel_ns.oid = rel.relnamespace
      JOIN pg_attribute att
        ON att.attrelid = rel.oid
       AND att.attnum = ad.adnum
     WHERE rel_ns.nspname = 'tcc'
       AND rel.relname = 'etu_sensor_maint'
       AND att.attname = 'id'
  ) THEN
    RAISE EXCEPTION 'ABORT: tcc.etu_sensor_maint.id default does not depend on public.tcc_etu_sensor_maint_id_seq.';
  END IF;
END $$;

ALTER SEQUENCE public.tcc_etu_sensor_maint_id_seq OWNED BY NONE;
ALTER SEQUENCE public.tcc_etu_sensor_maint_id_seq SET SCHEMA tcc;
ALTER SEQUENCE tcc.tcc_etu_sensor_maint_id_seq RENAME TO etu_sensor_maint_id_seq;
ALTER SEQUENCE tcc.etu_sensor_maint_id_seq OWNED BY tcc.etu_sensor_maint.id;

DO $$
DECLARE
  seq_oid oid;
BEGIN
  SELECT to_regclass('tcc.etu_sensor_maint_id_seq') INTO seq_oid;

  IF seq_oid IS NULL THEN
    RAISE EXCEPTION 'ABORT: expected sequence tcc.etu_sensor_maint_id_seq was not found after resequence.';
  END IF;

  IF to_regclass('public.tcc_etu_sensor_maint_id_seq') IS NOT NULL THEN
    RAISE EXCEPTION 'ABORT: public.tcc_etu_sensor_maint_id_seq still exists after resequence.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_depend d
      JOIN pg_class owner_rel ON owner_rel.oid = d.refobjid
      JOIN pg_namespace owner_ns ON owner_ns.oid = owner_rel.relnamespace
      JOIN pg_attribute owner_att
        ON owner_att.attrelid = owner_rel.oid
       AND owner_att.attnum = d.refobjsubid
     WHERE d.classid = 'pg_class'::regclass
       AND d.refclassid = 'pg_class'::regclass
       AND d.objid = seq_oid
       AND d.deptype = 'a'
       AND owner_ns.nspname = 'tcc'
       AND owner_rel.relname = 'etu_sensor_maint'
       AND owner_att.attname = 'id'
  ) THEN
    RAISE EXCEPTION 'ABORT: tcc.etu_sensor_maint_id_seq is not owned by tcc.etu_sensor_maint.id.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_attrdef ad
      JOIN pg_depend d
        ON d.classid = 'pg_attrdef'::regclass
       AND d.objid = ad.oid
       AND d.refclassid = 'pg_class'::regclass
       AND d.refobjid = seq_oid
      JOIN pg_class rel ON rel.oid = ad.adrelid
      JOIN pg_namespace rel_ns ON rel_ns.oid = rel.relnamespace
      JOIN pg_attribute att
        ON att.attrelid = rel.oid
       AND att.attnum = ad.adnum
     WHERE rel_ns.nspname = 'tcc'
       AND rel.relname = 'etu_sensor_maint'
       AND att.attname = 'id'
  ) THEN
    RAISE EXCEPTION 'ABORT: tcc.etu_sensor_maint.id default lost its sequence dependency.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_attrdef ad
      JOIN pg_depend d
        ON d.classid = 'pg_attrdef'::regclass
       AND d.objid = ad.oid
       AND d.refclassid = 'pg_class'::regclass
       AND d.refobjid = seq_oid
      JOIN pg_class rel ON rel.oid = ad.adrelid
      JOIN pg_namespace rel_ns ON rel_ns.oid = rel.relnamespace
      JOIN pg_attribute att
        ON att.attrelid = rel.oid
       AND att.attnum = ad.adnum
     WHERE rel_ns.nspname = 'public'
       AND rel.relname = 'tcc_etu_sensor_maint_pre_rebuild'
       AND att.attname = 'id'
  ) THEN
    RAISE EXCEPTION 'ABORT: public.tcc_etu_sensor_maint_pre_rebuild.id default lost its sequence dependency.';
  END IF;
END $$;

COMMIT;
