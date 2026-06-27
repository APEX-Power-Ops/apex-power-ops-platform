-- 030_d5_native_overrides_sidetable_down.sql
-- =============================================================================
-- DOWN for 030 - drop the D5 native_bounded raw-override side table.
-- =============================================================================

BEGIN;

DROP TABLE IF EXISTS tcc.brk_style_native_overrides;

COMMIT;
