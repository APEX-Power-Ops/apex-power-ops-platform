-- ============================================================================
-- ops migration 004 DOWN -- drop ops.persons ONLY. NEVER drops the ops schema: the
-- active ops.* lane + the 5,344 Miner apparatus live there. Reverses 004_person_anchor.sql.
-- ============================================================================
drop table if exists ops.persons;
