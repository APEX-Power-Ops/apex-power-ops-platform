-- Down: 003_records_indexes.sql
-- Packet: 2026-06-12-records-001
BEGIN;

DROP INDEX IF EXISTS records.ix_pm_events_form_submission;
DROP INDEX IF EXISTS records.ix_pm_events_status;
DROP INDEX IF EXISTS records.ix_pm_events_asset;
DROP INDEX IF EXISTS records.ix_pm_events_schedule;
DROP INDEX IF EXISTS records.ix_pm_schedules_due;
DROP INDEX IF EXISTS records.ix_pm_schedules_program;
DROP INDEX IF EXISTS records.ix_pm_schedules_asset;
DROP INDEX IF EXISTS records.ix_pm_programs_class;

DROP INDEX IF EXISTS records.ix_form_field_values_group;
DROP INDEX IF EXISTS records.ix_form_field_values_assessment;
DROP INDEX IF EXISTS records.ix_form_field_values_form_submission;

DROP INDEX IF EXISTS records.uq_form_templates_current;
DROP INDEX IF EXISTS records.ix_form_templates_class;
DROP INDEX IF EXISTS records.ix_form_submissions_job_number;
DROP INDEX IF EXISTS records.ix_form_submissions_pm_event;
DROP INDEX IF EXISTS records.ix_form_submissions_status;
DROP INDEX IF EXISTS records.ix_form_submissions_project;
DROP INDEX IF EXISTS records.ix_form_submissions_template;
DROP INDEX IF EXISTS records.ix_form_submissions_asset;

DROP INDEX IF EXISTS records.ix_asset_classes_parent;
DROP INDEX IF EXISTS records.ix_assets_legacy_src;
DROP INDEX IF EXISTS records.ix_assets_status;
DROP INDEX IF EXISTS records.ix_assets_site_ref;
DROP INDEX IF EXISTS records.ix_assets_parent;
DROP INDEX IF EXISTS records.ix_assets_class;

COMMIT;
