-- F-79-03 frame-deficit style-bucket localization (the sec-6 evidence, reproducible).
--
-- Question: can the CLEAN style hop localize the tmt_frames -169 count delta to
-- specific styles (clustered vs diffuse)?  Key = Access StyleID == tcc source_id
-- (verified clean 1:1 by style_provenance_antijoin).  The count delta is class-FREE
-- (class is annotation only).  Run against tcc_fidelity_governed (access_raw is the
-- governed Access mirror; tcc_snapshot.tmt_frames verified == prod: mccb 30809 / pcb
-- 11260 = 42069).
--
-- RESULT (2026-06-28, cross-engine verified): the style hop does NOT localize -169.
-- It reveals a frame-load TRANSFORMATION -- tcc MCCB frames are Access-faithful
-- (30809/30809 on matched styles; corr 0.97 on the 6001 shared styles), but ~10412
-- tcc PCB frames are DERIVED onto styles no Access frame references, while ~9629
-- Access frames on MCCB-only styles have no tcc frame.  net -169 = -10191 (access-only)
-- +10412 (derived PCB) -390 (shared drift).  NOT a 169-row truncation.  See the packet.
--
-- psql "$GOV_DSN" -f F-79-03-frame-style-localization.sql   ( GOV_DSN -> tcc_fidelity_governed )
\pset pager off
\set ON_ERROR_STOP on

CREATE TEMP VIEW _acc AS
  SELECT "StyleID"::int AS sid, count(*) AS acc_n
  FROM access_raw."Breaker_TMTFrameSizes" GROUP BY "StyleID";

-- class-correct join: breaker_style_id -> brk_<class>_styles.id (the surrogate; gives
-- 100% frame coverage), then that row's source_id (== the Access style ID).
CREATE TEMP VIEW _tccf AS
  SELECT 'mccb' AS cls, s.source_id AS sid
    FROM tcc_snapshot.tmt_frames f
    JOIN tcc_snapshot.brk_mccb_styles s ON lower(f.breaker_class)='mccb' AND f.breaker_style_id=s.id
  UNION ALL
  SELECT 'pcb', s.source_id
    FROM tcc_snapshot.tmt_frames f
    JOIN tcc_snapshot.brk_pcb_styles s ON lower(f.breaker_class)='pcb' AND f.breaker_style_id=s.id;

CREATE TEMP VIEW _tcc AS SELECT sid, count(*) AS tcc_n FROM _tccf GROUP BY sid;

CREATE TEMP VIEW _mem AS
  SELECT id AS sid, max((cls='MCCB')::int) in_mccb, max((cls='ICCB')::int) in_iccb, max((cls='PCB')::int) in_pcb
  FROM (SELECT "ID"::int id,'MCCB' cls FROM access_raw."BreakerMCCBStyles"
        UNION ALL SELECT "ID"::int,'ICCB' FROM access_raw."BreakerICCBStyles"
        UNION ALL SELECT "ID"::int,'PCB'  FROM access_raw."BreakerPCBStyles") u GROUP BY id;

CREATE TEMP VIEW _j AS
  SELECT coalesce(a.sid,t.sid) sid, coalesce(a.acc_n,0) acc_n, coalesce(t.tcc_n,0) tcc_n
  FROM _acc a FULL OUTER JOIN _tcc t ON a.sid=t.sid;

\echo '== GATE: totals (acc 42238 / tcc 42069 / delta +169) =='
SELECT sum(acc_n) acc_total, sum(tcc_n) tcc_total, sum(acc_n-tcc_n) delta_total FROM _j;

\echo '== overlap: both / access-only / tcc-only, and frames in the non-overlap =='
SELECT count(*) FILTER (WHERE acc_n>0 AND tcc_n>0) both,
       count(*) FILTER (WHERE acc_n>0 AND tcc_n=0) access_only,
       count(*) FILTER (WHERE acc_n=0 AND tcc_n>0) tcc_only,
       sum(acc_n) FILTER (WHERE acc_n>0 AND tcc_n=0) acc_frames_access_only,
       sum(tcc_n) FILTER (WHERE acc_n=0 AND tcc_n>0) tcc_frames_tcc_only
FROM _j;

\echo '== among BOTH-present styles: faithfulness (exact-match / abs-delta / corr) =='
SELECT count(*) both_styles, sum((acc_n=tcc_n)::int) exact_match,
       sum(abs(acc_n-tcc_n)) total_abs_delta, corr(acc_n::float8,tcc_n::float8) pearson_corr
FROM _j WHERE acc_n>0 AND tcc_n>0;

\echo '== tcc frames by class: matched (source_id HAS Access frames) vs derived =='
SELECT t.cls, count(*) tcc_frames,
       count(*) FILTER (WHERE a.acc_n IS NOT NULL) on_access_styles,
       count(*) FILTER (WHERE a.acc_n IS NULL)     derived
FROM _tccf t LEFT JOIN _acc a ON a.sid=t.sid GROUP BY t.cls ORDER BY t.cls;
