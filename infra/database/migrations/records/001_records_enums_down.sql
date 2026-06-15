-- Down: 001_records_enums.sql
-- Packet: 2026-06-12-records-001
-- Drops the records enum types and the schema. Run LAST (after 002 tables are dropped),
-- since the tables depend on these types.
BEGIN;

DROP TYPE IF EXISTS records.pm_event_status_enum;
DROP TYPE IF EXISTS records.pm_interval_unit_enum;
DROP TYPE IF EXISTS records.field_value_kind_enum;
DROP TYPE IF EXISTS records.assessment_result_enum;
DROP TYPE IF EXISTS records.as_found_as_left_enum;
DROP TYPE IF EXISTS records.form_type_enum;
DROP TYPE IF EXISTS records.form_status_enum;
DROP TYPE IF EXISTS records.neta_standard_enum;
DROP TYPE IF EXISTS records.asset_condition_enum;
DROP TYPE IF EXISTS records.asset_status_enum;
DROP TYPE IF EXISTS records.provenance_status_enum;
DROP TYPE IF EXISTS records.provenance_source_enum;

DROP SCHEMA IF EXISTS records;

COMMIT;
