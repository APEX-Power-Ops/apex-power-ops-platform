-- =============================================================================
-- NETA Records Domain — Indexes  (PowerDB replacement, Chip 1)
-- Packet: 2026-06-12-neta-records-001
-- Landing Lane: infra/database/migrations/neta/
-- Requires: 002_neta_tables.sql
--
-- Lookup + traversal indexes for the asset → datasheet → results and
-- asset → PM schedule → events access paths. Unique constraints already cover
-- the natural keys; these target the high-traffic foreign-key joins and the
-- "what's due / what failed" filters.
-- =============================================================================

-- Asset register --------------------------------------------------------------
CREATE INDEX ix_assets_class       ON neta.assets (asset_class_id);
CREATE INDEX ix_assets_parent      ON neta.assets (parent_asset_id);
CREATE INDEX ix_assets_site_ref    ON neta.assets (site_ref);
CREATE INDEX ix_assets_status      ON neta.assets (status);
CREATE INDEX ix_assets_powerdb_src ON neta.assets (powerdb_source_id);

CREATE INDEX ix_asset_classes_parent ON neta.asset_classes (parent_class_id);

-- Data sheets -----------------------------------------------------------------
CREATE INDEX ix_datasheets_asset     ON neta.datasheets (asset_id);
CREATE INDEX ix_datasheets_template  ON neta.datasheets (template_id);
CREATE INDEX ix_datasheets_project   ON neta.datasheets (project_ref);
CREATE INDEX ix_datasheets_status    ON neta.datasheets (status);
CREATE INDEX ix_datasheets_pm_event  ON neta.datasheets (pm_event_id);
CREATE INDEX ix_datasheets_job_number ON neta.datasheets (job_number);  -- PowerDB universal join key

CREATE INDEX ix_datasheet_templates_class ON neta.datasheet_templates (asset_class_id);
-- One current version per template_code.
CREATE UNIQUE INDEX uq_datasheet_templates_current
    ON neta.datasheet_templates (template_code)
    WHERE is_current;

-- Test results ----------------------------------------------------------------
CREATE INDEX ix_test_results_datasheet  ON neta.test_results (datasheet_id);
CREATE INDEX ix_test_results_assessment ON neta.test_results (assessment);
CREATE INDEX ix_test_results_group      ON neta.test_results (test_group);

-- PM tracking -----------------------------------------------------------------
CREATE INDEX ix_pm_programs_class    ON neta.pm_programs (asset_class_id);
CREATE INDEX ix_pm_schedules_asset   ON neta.pm_schedules (asset_id);
CREATE INDEX ix_pm_schedules_program ON neta.pm_schedules (pm_program_id);
-- Drives the "what's coming due" dashboard.
CREATE INDEX ix_pm_schedules_due     ON neta.pm_schedules (next_due_at) WHERE is_active;
CREATE INDEX ix_pm_events_schedule   ON neta.pm_events (pm_schedule_id);
CREATE INDEX ix_pm_events_asset      ON neta.pm_events (asset_id);
CREATE INDEX ix_pm_events_status     ON neta.pm_events (status);
CREATE INDEX ix_pm_events_datasheet  ON neta.pm_events (datasheet_id);
