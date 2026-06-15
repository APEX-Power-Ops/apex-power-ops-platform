-- Down: 002_records_tables.sql
-- Packet: 2026-06-12-records-001
-- Drops in reverse-dependency order. The reciprocal form_submissions→pm_events FK is
-- dropped first so pm_events can be dropped without a circular constraint.
BEGIN;

ALTER TABLE IF EXISTS records.form_submissions DROP CONSTRAINT IF EXISTS fk_form_submissions_pm_event;

DROP TABLE IF EXISTS records.pm_events;
DROP TABLE IF EXISTS records.pm_schedules;
DROP TABLE IF EXISTS records.pm_programs;
DROP TABLE IF EXISTS records.form_field_values;
DROP TABLE IF EXISTS records.form_submissions;
DROP TABLE IF EXISTS records.form_templates;
DROP TABLE IF EXISTS records.assets;
DROP TABLE IF EXISTS records.asset_classes;

COMMIT;
