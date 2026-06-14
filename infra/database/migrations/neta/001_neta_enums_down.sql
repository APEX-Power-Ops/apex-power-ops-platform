-- Down: 001_neta_enums.sql
-- Packet: 2026-06-12-neta-records-001
-- Drops the neta enum types and the schema. Run LAST (after 002 tables are dropped),
-- since the tables depend on these types.
BEGIN;

DROP TYPE IF EXISTS neta.pm_event_status_enum;
DROP TYPE IF EXISTS neta.pm_interval_unit_enum;
DROP TYPE IF EXISTS neta.result_value_kind_enum;
DROP TYPE IF EXISTS neta.assessment_result_enum;
DROP TYPE IF EXISTS neta.as_found_as_left_enum;
DROP TYPE IF EXISTS neta.datasheet_status_enum;
DROP TYPE IF EXISTS neta.neta_standard_enum;
DROP TYPE IF EXISTS neta.asset_condition_enum;
DROP TYPE IF EXISTS neta.asset_status_enum;
DROP TYPE IF EXISTS neta.provenance_status_enum;
DROP TYPE IF EXISTS neta.provenance_source_enum;

DROP SCHEMA IF EXISTS neta;

COMMIT;
