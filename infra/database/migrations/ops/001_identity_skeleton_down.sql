-- ============================================================================
-- DOWN — ops Chip 1 identity skeleton.
-- Drops the whole ops namespace (tables, enums, the scope-immutability trigger +
-- function, indexes). Idempotent (IF EXISTS) so the test can run it on a clean DB.
-- ============================================================================
drop schema if exists ops cascade;
