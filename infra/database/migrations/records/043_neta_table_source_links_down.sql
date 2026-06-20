-- =============================================================================
-- Records migration 043 DOWN -- drop records.neta_table_source_links.
--   Reverses 043_neta_table_source_links.sql. The bespoke vocab is CHECK-constrained
--   text (no companion enum types), so this is trigger + table only. Does not touch
--   records.neta_tables or any seed data.
-- =============================================================================

BEGIN;
SET client_encoding TO 'UTF8';
SET standard_conforming_strings TO on;

DROP TRIGGER IF EXISTS trg_neta_table_source_links_updated_at
    ON records.neta_table_source_links;

DROP TABLE IF EXISTS records.neta_table_source_links;

COMMIT;
