-- Down: 004_records_triggers_and_views.sql
-- Packet: 2026-06-12-records-001
BEGIN;

DROP VIEW IF EXISTS records.v_pm_due;
DROP VIEW IF EXISTS records.v_asset_test_history;

DROP TRIGGER IF EXISTS trg_pm_events_updated_at         ON records.pm_events;
DROP TRIGGER IF EXISTS trg_pm_schedules_updated_at      ON records.pm_schedules;
DROP TRIGGER IF EXISTS trg_pm_programs_updated_at       ON records.pm_programs;
DROP TRIGGER IF EXISTS trg_form_field_values_updated_at      ON records.form_field_values;
DROP TRIGGER IF EXISTS trg_form_submissions_updated_at        ON records.form_submissions;
DROP TRIGGER IF EXISTS trg_form_templates_updated_at ON records.form_templates;
DROP TRIGGER IF EXISTS trg_assets_updated_at            ON records.assets;
DROP TRIGGER IF EXISTS trg_asset_classes_updated_at     ON records.asset_classes;

DROP FUNCTION IF EXISTS records.fn_set_updated_at();

COMMIT;
