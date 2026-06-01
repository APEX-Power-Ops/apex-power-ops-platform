-- =============================================================================
-- D1 follow-on — populate + constrain brk_*_styles.source_id (the stable source key).
--
-- The source_id COLUMN was added by 006; this step fills it (deferred there) and
-- locks it as an alternate key. source_id = Access Breaker*Styles.ID, carried via
-- the PROVEN rank=id mapping (Supabase brk_*_styles.id == Access row position by ID
-- asc). Population SQL (the per-class Access-ID arrays, integrity-md5-verified) lives in
-- infra/database/migrations/tcc/_d1_loader/:
--   d1_90_srcid_iccb.sql                         (608 ids,  1 statement)
--   d1_90_srcid_pcb.sql                          (3,279 ids, 1 statement)
--   d1_90_srcid_mccb_p1..p4.sql                  (10,335 ids, 4 rank-offset chunks)
-- (mccb is chunked only because one 10,335-int array exceeds tool surfacing limits;
--  d1_90_srcid_mccb.sql is the equivalent single statement.)
--
-- Verified per class: count(source_id)=count(*); md5(string_agg(source_id::text,',' order by id)):
--   iccb 26e21a93b9dae545d24d2c960a80ab0d · pcb f6b00f029979a9aa3ed4724ab56cc62f
--   mccb 67a8c051024cab0a44f1c44a0078e337
--
-- Apply order: 006 (cols+bridge) -> the d1_90_srcid_*.sql loads -> this file.
-- =============================================================================

-- ... load _d1_loader/d1_90_srcid_{iccb,pcb}.sql + d1_90_srcid_mccb_p1..p4.sql here ...

ALTER TABLE tcc.brk_mccb_styles ALTER COLUMN source_id SET NOT NULL;
ALTER TABLE tcc.brk_iccb_styles ALTER COLUMN source_id SET NOT NULL;
ALTER TABLE tcc.brk_pcb_styles  ALTER COLUMN source_id SET NOT NULL;

ALTER TABLE tcc.brk_mccb_styles ADD CONSTRAINT tcc_brk_mccb_styles_source_id_key UNIQUE (source_id);
ALTER TABLE tcc.brk_iccb_styles ADD CONSTRAINT tcc_brk_iccb_styles_source_id_key UNIQUE (source_id);
ALTER TABLE tcc.brk_pcb_styles  ADD CONSTRAINT tcc_brk_pcb_styles_source_id_key  UNIQUE (source_id);

COMMENT ON COLUMN tcc.brk_mccb_styles.source_id IS 'Access BreakerMCCBStyles.ID (stable source key; carried via the proven rank=id mapping, D1 2026-06-01).';
COMMENT ON COLUMN tcc.brk_iccb_styles.source_id IS 'Access BreakerICCBStyles.ID (stable source key; D1 2026-06-01).';
COMMENT ON COLUMN tcc.brk_pcb_styles.source_id  IS 'Access BreakerPCBStyles.ID (stable source key; D1 2026-06-01).';
