-- 011_brk_rcont_current_backfill_down.sql
ALTER TABLE tcc.brk_mccb_styles DROP COLUMN IF EXISTS r_cont_current;
ALTER TABLE tcc.brk_pcb_styles DROP COLUMN IF EXISTS r_cont_current;
ALTER TABLE tcc.brk_iccb_styles DROP COLUMN IF EXISTS r_cont_current;
