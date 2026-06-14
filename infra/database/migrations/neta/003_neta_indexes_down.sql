-- Down: 003_neta_indexes.sql
-- Packet: 2026-06-12-neta-records-001
BEGIN;

DROP INDEX IF EXISTS neta.ix_pm_events_datasheet;
DROP INDEX IF EXISTS neta.ix_pm_events_status;
DROP INDEX IF EXISTS neta.ix_pm_events_asset;
DROP INDEX IF EXISTS neta.ix_pm_events_schedule;
DROP INDEX IF EXISTS neta.ix_pm_schedules_due;
DROP INDEX IF EXISTS neta.ix_pm_schedules_program;
DROP INDEX IF EXISTS neta.ix_pm_schedules_asset;
DROP INDEX IF EXISTS neta.ix_pm_programs_class;

DROP INDEX IF EXISTS neta.ix_test_results_group;
DROP INDEX IF EXISTS neta.ix_test_results_assessment;
DROP INDEX IF EXISTS neta.ix_test_results_datasheet;

DROP INDEX IF EXISTS neta.uq_datasheet_templates_current;
DROP INDEX IF EXISTS neta.ix_datasheet_templates_class;
DROP INDEX IF EXISTS neta.ix_datasheets_job_number;
DROP INDEX IF EXISTS neta.ix_datasheets_pm_event;
DROP INDEX IF EXISTS neta.ix_datasheets_status;
DROP INDEX IF EXISTS neta.ix_datasheets_project;
DROP INDEX IF EXISTS neta.ix_datasheets_template;
DROP INDEX IF EXISTS neta.ix_datasheets_asset;

DROP INDEX IF EXISTS neta.ix_asset_classes_parent;
DROP INDEX IF EXISTS neta.ix_assets_powerdb_src;
DROP INDEX IF EXISTS neta.ix_assets_status;
DROP INDEX IF EXISTS neta.ix_assets_site_ref;
DROP INDEX IF EXISTS neta.ix_assets_parent;
DROP INDEX IF EXISTS neta.ix_assets_class;

COMMIT;
