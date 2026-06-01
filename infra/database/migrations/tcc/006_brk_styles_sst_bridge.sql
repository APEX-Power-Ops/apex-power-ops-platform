-- =============================================================================
-- D1 — Recover the breaker -> ETU SST bridge on tcc.brk_*_styles.
--
-- Root cause (G1 D1): the 4 SST-bridge columns (TMT_Use_SST + TMT_SST_{Mfr,Type,
-- Style}) were dropped at the Access->Supabase load (a loader expecting a numeric
-- Manufacturers.ID discarded the name-key). Live-confirmed missing 2026-06-01.
-- Also: 325 MCCB style rows were orphaned from day one — the original load preserved
-- a row-ordered surrogate id (rank=id, PROVEN), but the too-narrow parent unique key
-- (manufacturer_id, name) dropped 41 AC/DC & ANSI/IEC twins (re-inserted by migration
-- 005 at new ids), leaving those styles pointing at dead parent surrogates.
--
-- Approach (lean A — minimal, in-place; router.py depends on brk_*_styles.id as
-- breaker_style_id, so ids are PRESERVED, not renumbered):
--   1. ADD source_id + tmt_use_sst(bool) + tmt_sst_{mfr,type,style}(text)  [this file]
--   2. Carry the SST data from Access keyed on rank=id            [_d1_loader staging]
--   3. Repoint the 325 orphan styles to the migration-005 twins   [_d1_loader staging]
--   4. Build the BG-4 bridge view                                 [this file]
--
-- rank=id mapping PROVEN: Supabase brk_*_styles.id == position of the Access
-- Breaker*Styles row ordered by ID ascending (46/46 spot matches across the full
-- range + per-class style/SST/orphan integrity md5s).
--
-- Bulk staging data is loaded from the generated, integrity-checked SQL in
-- infra/database/migrations/tcc/_d1_loader/ (see _d1_loader/RUN_ORDER.md). It is not
-- inlined here (5,412 SST assignments + 325 orphan rows). Apply order:
--   (A) this DDL  ->  (B) _d1_loader/d1_04_triples_*.sql + d1_05_sst_*.sql +
--   d1_06_orphan.sql into transient tcc._stg_d1_*  ->  (C) the UPDATEs below  ->
--   (D) the bridge view  ->  drop the _stg_d1_* tables.
--
-- tmt_use_sst boolean = (Access TMT_Use_SST <> 0): mccb 1704 / iccb 515 / pcb 3193.
-- (1680x value=1 + 2x value=2 + 22x value=255 [=-1 byte-wrapped True]; 725 NULL=false.)
-- source_id population is DEFERRED — ready, un-applied, in _d1_loader/d1_90_srcid_*.sql.
-- =============================================================================

-- (A) DDL — additive, reversible (DROP COLUMN ...).
ALTER TABLE tcc.brk_mccb_styles
  ADD COLUMN IF NOT EXISTS source_id integer,
  ADD COLUMN IF NOT EXISTS tmt_use_sst boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tmt_sst_mfr text,
  ADD COLUMN IF NOT EXISTS tmt_sst_type text,
  ADD COLUMN IF NOT EXISTS tmt_sst_style text;
ALTER TABLE tcc.brk_iccb_styles
  ADD COLUMN IF NOT EXISTS source_id integer,
  ADD COLUMN IF NOT EXISTS tmt_use_sst boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tmt_sst_mfr text,
  ADD COLUMN IF NOT EXISTS tmt_sst_type text,
  ADD COLUMN IF NOT EXISTS tmt_sst_style text;
ALTER TABLE tcc.brk_pcb_styles
  ADD COLUMN IF NOT EXISTS source_id integer,
  ADD COLUMN IF NOT EXISTS tmt_use_sst boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tmt_sst_mfr text,
  ADD COLUMN IF NOT EXISTS tmt_sst_type text,
  ADD COLUMN IF NOT EXISTS tmt_sst_style text;

-- Transient staging (populated from _d1_loader/*.sql — see RUN_ORDER.md).
CREATE TABLE IF NOT EXISTS tcc._stg_d1_triples (class text, triple_id int, mfr text, type text, style text);
CREATE TABLE IF NOT EXISTS tcc._stg_d1_sst     (class text, style_id int, triple_id int);
CREATE TABLE IF NOT EXISTS tcc._stg_d1_orphan  (style_id int, src_breaker_id int, mfr_id int, type text, standard numeric, acdc smallint, src_style text);

-- ... load _d1_loader/d1_04_triples_{iccb,pcb,mccb}.sql, d1_05_sst_{iccb,mccb,pcb}.sql,
--     d1_06_orphan.sql here (431 triples / 5,412 assignments / 325 orphans) ...

-- (C) SST carry (source-faithful, via rank=id).
UPDATE tcc.brk_mccb_styles t
SET tmt_use_sst = true, tmt_sst_mfr = tr.mfr, tmt_sst_type = tr.type, tmt_sst_style = tr.style
FROM tcc._stg_d1_sst a JOIN tcc._stg_d1_triples tr ON tr.class = a.class AND tr.triple_id = a.triple_id
WHERE a.class = 'mccb' AND t.id = a.style_id;
UPDATE tcc.brk_iccb_styles t
SET tmt_use_sst = true, tmt_sst_mfr = tr.mfr, tmt_sst_type = tr.type, tmt_sst_style = tr.style
FROM tcc._stg_d1_sst a JOIN tcc._stg_d1_triples tr ON tr.class = a.class AND tr.triple_id = a.triple_id
WHERE a.class = 'iccb' AND t.id = a.style_id;
UPDATE tcc.brk_pcb_styles t
SET tmt_use_sst = true, tmt_sst_mfr = tr.mfr, tmt_sst_type = tr.type, tmt_sst_style = tr.style
FROM tcc._stg_d1_sst a JOIN tcc._stg_d1_triples tr ON tr.class = a.class AND tr.triple_id = a.triple_id
WHERE a.class = 'pcb' AND t.id = a.style_id;

-- Orphan repoint -> migration-005 twins (frame-guarded, normalized).
UPDATE tcc.brk_mccb_styles t
SET breaker_id = b.id
FROM tcc._stg_d1_orphan o
JOIN tcc.brk_mccb b
  ON b.manufacturer_id = o.mfr_id AND b.name = o.type
  AND b.standard IS NOT DISTINCT FROM o.standard
  AND b.ac_dc_code IS NOT DISTINCT FROM o.acdc
WHERE t.id = o.style_id
  AND regexp_replace(upper(o.src_style),'[^A-Z0-9]','','g')
    = regexp_replace(upper(coalesce(t.frame,'')),'[^A-Z0-9]','','g');

DO $$
DECLARE v int;
BEGIN
  SELECT count(*) INTO v FROM tcc.brk_mccb_styles WHERE tmt_use_sst;
  IF v <> 1704 THEN RAISE EXCEPTION 'mccb tmt_use_sst expected 1704 got %', v; END IF;
  SELECT count(*) INTO v FROM tcc.brk_iccb_styles WHERE tmt_use_sst;
  IF v <> 515 THEN RAISE EXCEPTION 'iccb tmt_use_sst expected 515 got %', v; END IF;
  SELECT count(*) INTO v FROM tcc.brk_pcb_styles WHERE tmt_use_sst;
  IF v <> 3193 THEN RAISE EXCEPTION 'pcb tmt_use_sst expected 3193 got %', v; END IF;
  SELECT count(*) INTO v FROM tcc.brk_mccb_styles s LEFT JOIN tcc.brk_mccb p ON p.id=s.breaker_id WHERE p.id IS NULL;
  IF v <> 0 THEN RAISE EXCEPTION 'mccb orphan styles expected 0 got %', v; END IF;
END $$;

-- (D) BG-4 bridge surface.
CREATE OR REPLACE VIEW tcc.vw_breaker_sst_bridge AS
WITH styles AS (
  SELECT 'mccb'::text AS breaker_class, s.id AS breaker_style_id, s.breaker_id, s.frame AS breaker_style_frame,
         s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_mccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'iccb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_iccb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
  UNION ALL
  SELECT 'pcb', s.id, s.breaker_id, s.frame, s.tmt_sst_mfr, s.tmt_sst_type, s.tmt_sst_style
  FROM tcc.brk_pcb_styles s WHERE s.tmt_use_sst AND s.tmt_sst_type IS NOT NULL
)
SELECT st.breaker_class, st.breaker_id, st.breaker_style_id, st.breaker_style_frame,
       st.tmt_sst_mfr, st.tmt_sst_type, st.tmt_sst_style,
       ts.id AS trip_style_id, es.id AS sensor_id, es.rating AS sensor_rating, es.description AS sensor_description
FROM styles st
JOIN tcc.manufacturers m ON m.mfr_name = st.tmt_sst_mfr
JOIN tcc.trip_styles ts ON ts.mfg_id = m.id AND ts.type = st.tmt_sst_type AND ts.style = st.tmt_sst_style
JOIN tcc.etu_sensors es ON es.trip_style_id = ts.id;

-- cleanup
DROP TABLE IF EXISTS tcc._stg_d1_triples;
DROP TABLE IF EXISTS tcc._stg_d1_sst;
DROP TABLE IF EXISTS tcc._stg_d1_orphan;
