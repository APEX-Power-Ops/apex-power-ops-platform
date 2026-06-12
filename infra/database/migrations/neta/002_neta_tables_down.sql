-- Down: 002_neta_tables.sql
-- Packet: 2026-06-12-neta-records-001
-- Drops in reverse-dependency order. The reciprocal datasheets→pm_events FK is
-- dropped first so pm_events can be dropped without a circular constraint.
BEGIN;

ALTER TABLE IF EXISTS neta.datasheets DROP CONSTRAINT IF EXISTS fk_datasheets_pm_event;

DROP TABLE IF EXISTS neta.pm_events;
DROP TABLE IF EXISTS neta.pm_schedules;
DROP TABLE IF EXISTS neta.pm_programs;
DROP TABLE IF EXISTS neta.test_results;
DROP TABLE IF EXISTS neta.datasheets;
DROP TABLE IF EXISTS neta.datasheet_templates;
DROP TABLE IF EXISTS neta.assets;
DROP TABLE IF EXISTS neta.asset_classes;

COMMIT;
