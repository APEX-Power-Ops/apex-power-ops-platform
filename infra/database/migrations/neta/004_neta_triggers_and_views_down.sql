-- Down: 004_neta_triggers_and_views.sql
-- Packet: 2026-06-12-neta-records-001
BEGIN;

DROP VIEW IF EXISTS neta.v_pm_due;
DROP VIEW IF EXISTS neta.v_asset_test_history;

DROP TRIGGER IF EXISTS trg_pm_events_updated_at         ON neta.pm_events;
DROP TRIGGER IF EXISTS trg_pm_schedules_updated_at      ON neta.pm_schedules;
DROP TRIGGER IF EXISTS trg_pm_programs_updated_at       ON neta.pm_programs;
DROP TRIGGER IF EXISTS trg_test_results_updated_at      ON neta.test_results;
DROP TRIGGER IF EXISTS trg_datasheets_updated_at        ON neta.datasheets;
DROP TRIGGER IF EXISTS trg_datasheet_templates_updated_at ON neta.datasheet_templates;
DROP TRIGGER IF EXISTS trg_assets_updated_at            ON neta.assets;
DROP TRIGGER IF EXISTS trg_asset_classes_updated_at     ON neta.asset_classes;

DROP FUNCTION IF EXISTS neta.fn_set_updated_at();

COMMIT;
