-- 030_d5_native_overrides_sidetable.sql
-- =============================================================================
-- F-79-04 D5 raw-carry (native_bounded). PROD-BOUND, OPERATOR-GATED.
-- *** QUEUED: apply ONLY after the operator gives a separate go (027/028 discipline). ***
--
-- Lane-2 data-carry: a side table that preserves the raw D5 override / timing / rating columns
-- (InstOvr*, NInstOvr*, BrkTimes*50/60, r_int_*, r_iec_*, and any Breaker_OvrCurves points) as
-- native_bounded REFERENCE data. Keyed (breaker_class, source_id) - source_id collides across
-- breaker classes (G1 sec 2B per-class id overlap), so a shared side table MUST carry breaker_class.
--
-- native_bounded = the raw values are readable, but the override APPLICATION + the curve/char
-- byte-enum legends + the curve math are native (DvlEng input layout only; recalc in TccBase,
-- symbol-stripped) - see G1 sec 3.4 / sec 5 D5. So this carries the raw block WITHOUT claiming
-- behavior and WITHOUT wiring it to serving. The raw block is JSONB keyed by the verbatim Access
-- column name (max fidelity, no 66-column enumeration, class-heterogeneity tolerated as missing keys);
-- promote to explicit typed columns only if a future consumer needs to JOIN/filter on them.
--
-- THIS FILE = the SCHEMA (CREATE TABLE + COMMENT), self-contained + idempotent. The DATA population
-- is the separate harness-driven gated step (read the override blocks row-level from D:\TCC_NEW.accdb
-- per class -> INSERT rows). N defaults to the base block where the Access N columns are absent
-- (engine behavior, DvlEng -Module-.cs:12172) - preserve that as-read, do not synthesize.
--
-- REVERSIBLE: 030_d5_native_overrides_sidetable_down.sql drops the table.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS tcc.brk_style_native_overrides (
  breaker_class  text     NOT NULL,   -- 'ICCB' | 'MCCB' | 'PCB' (uppercased)
  source_id      integer  NOT NULL,   -- = Access Breaker*Styles.ID (per-class; matches brk_<class>_styles.source_id)
  inst_override  jsonb,               -- raw InstOvr* block (16 Access cols, verbatim names + values)
  ninst_override jsonb,               -- raw NInstOvr* block (15 cols; Non-Instantaneous variant; = base where Access N cols absent)
  brk_times      jsonb,               -- raw BrkTimes*50/60 (mechanism timing)
  r_int          jsonb,               -- raw r_int_inst_* / r_int_series_* / r_int_ninst_* (ANSI interrupt ratings; ninst PCB-only)
  r_iec          jsonb,               -- raw r_iec_inst_* / r_iec_ninst_* (IEC interrupt ratings; ninst PCB-only)
  ovr_curves     jsonb,               -- raw Breaker_OvrCurves points by StyleID (currently empty in Access; reserved)
  CONSTRAINT brk_style_native_overrides_class_chk     CHECK (breaker_class IN ('ICCB','MCCB','PCB')),
  CONSTRAINT brk_style_native_overrides_source_id_chk CHECK (source_id > 0),
  PRIMARY KEY (breaker_class, source_id)
);

COMMENT ON TABLE tcc.brk_style_native_overrides IS
  'F-79-04 D5 native_bounded raw-carry: the breaker-style inst-override / timing / interrupt-rating block from Access (InstOvr*/NInstOvr*/BrkTimes*/r_int_*/r_iec_*/Breaker_OvrCurves), preserved as reference. NOT wired to serving; behavior un-claimed (override application + curve/char enum legends + curve math are native/bounded - G1 sec 3.4). N = Non-Instantaneous (inst defeated). [NATIVE-BOUNDED] [VERIFIED-LIVE 2026-06-27]';
COMMENT ON COLUMN tcc.brk_style_native_overrides.breaker_class  IS 'Part of the PK with source_id - source_id collides across classes (G1 sec 2B).';
COMMENT ON COLUMN tcc.brk_style_native_overrides.source_id      IS 'Access Breaker*Styles.ID; joins tcc.brk_<breaker_class>_styles.source_id (per-class, not a declared FK).';
COMMENT ON COLUMN tcc.brk_style_native_overrides.inst_override  IS 'Raw InstOvr* (amps/min+max tolerance/clr+opn delay+radius/notetext/clearing+opening curve sets). Verbatim Access column names as JSONB keys.';
COMMENT ON COLUMN tcc.brk_style_native_overrides.ninst_override IS 'Raw NInstOvr* = the Non-Instantaneous variant (= inst_override where the Access N columns are absent, per DvlEng fallback).';
COMMENT ON COLUMN tcc.brk_style_native_overrides.r_int          IS 'Raw ANSI interrupt ratings (kA) at 240/480/600 V: inst / series / ninst (ninst = PCB-only, getter CTccCurveBase.GetIntKaNonInst).';
COMMENT ON COLUMN tcc.brk_style_native_overrides.r_iec          IS 'Raw IEC interrupt ratings (kA) at 220-1000 V: inst / ninst (ninst = PCB-only).';

-- Exact-shape guard (fail closed): CREATE TABLE IF NOT EXISTS skips a pre-existing table of the wrong
-- shape, so assert the table, key types, jsonb blocks, PK, and the two CHECK constraints before COMMIT.
DO $$
DECLARE v_actual text; v_jsonb int; v_pk int; v_chk int;
BEGIN
  SELECT data_type INTO v_actual FROM information_schema.columns
    WHERE table_schema='tcc' AND table_name='brk_style_native_overrides' AND column_name='breaker_class';
  IF v_actual IS NULL THEN RAISE EXCEPTION '030 shape: table/breaker_class missing'; END IF;
  IF v_actual <> 'text' THEN RAISE EXCEPTION '030 shape: breaker_class is % (expected text)', v_actual; END IF;
  SELECT data_type INTO v_actual FROM information_schema.columns
    WHERE table_schema='tcc' AND table_name='brk_style_native_overrides' AND column_name='source_id';
  IF v_actual <> 'integer' THEN RAISE EXCEPTION '030 shape: source_id is % (expected integer)', v_actual; END IF;
  SELECT count(*) INTO v_jsonb FROM information_schema.columns
    WHERE table_schema='tcc' AND table_name='brk_style_native_overrides' AND data_type='jsonb';
  IF v_jsonb <> 6 THEN RAISE EXCEPTION '030 shape: expected 6 jsonb blocks (found %)', v_jsonb; END IF;
  -- PK must be EXACTLY (breaker_class, source_id): a source_id-only PK would pass a bare "has a PK"
  -- check but defeat the cross-class collision guard this table exists for (Codex review-c0e624b6).
  SELECT count(*) INTO v_pk
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON kcu.constraint_schema=tc.constraint_schema AND kcu.constraint_name=tc.constraint_name
    WHERE tc.table_schema='tcc' AND tc.table_name='brk_style_native_overrides' AND tc.constraint_type='PRIMARY KEY';
  IF v_pk <> 2 THEN RAISE EXCEPTION '030 shape: PK has % column(s), expected exactly 2 (breaker_class, source_id)', v_pk; END IF;
  IF (SELECT count(*) FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_schema=tc.constraint_schema AND kcu.constraint_name=tc.constraint_name
        WHERE tc.table_schema='tcc' AND tc.table_name='brk_style_native_overrides'
          AND tc.constraint_type='PRIMARY KEY' AND kcu.column_name IN ('breaker_class','source_id')) <> 2
    THEN RAISE EXCEPTION '030 shape: PK columns are not exactly (breaker_class, source_id)'; END IF;
  SELECT count(*) INTO v_chk FROM information_schema.table_constraints
    WHERE table_schema='tcc' AND table_name='brk_style_native_overrides' AND constraint_type='CHECK'
      AND constraint_name IN ('brk_style_native_overrides_class_chk','brk_style_native_overrides_source_id_chk');
  IF v_chk <> 2 THEN RAISE EXCEPTION '030 shape: expected 2 named CHECK constraints (found %)', v_chk; END IF;
  RAISE NOTICE '030 shape OK: table + key types + 6 jsonb + PK + 2 CHECKs';
END $$;

COMMIT;

-- DATA POPULATION (separate gated step, harness-driven): per class, read the override/timing/rating
-- columns row-level from D:\TCC_NEW.accdb, build the JSONB blocks (verbatim Access keys), and
-- INSERT (breaker_class, source_id, inst_override, ninst_override, brk_times, r_int, r_iec) for ANY
-- style with at least one non-null D5 block (override OR BrkTimes OR r_int OR r_iec - these exist
-- INDEPENDENTLY of an override; e.g. PCB carries r_int_* on ~1616 styles but InstOvrAmps>0 on only
-- ~317, so an override-only filter would silently drop ~1300 rating-only rows). Leave a per-block
-- JSONB NULL where that block is absent. Dry-run on the breaker sandbox; apply on the gate.
