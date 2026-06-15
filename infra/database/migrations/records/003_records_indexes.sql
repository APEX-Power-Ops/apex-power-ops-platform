-- =============================================================================
-- Records Domain — Indexes  (Chip 1)
-- Packet: 2026-06-12-records-001
-- Landing Lane: infra/database/migrations/records/
-- Requires: 002_records_tables.sql
--
-- Lookup + traversal indexes for the asset → form_submission → results and
-- asset → PM schedule → events access paths. Unique constraints already cover
-- the natural keys; these target the high-traffic foreign-key joins and the
-- "what's due / what failed" filters.
-- =============================================================================

-- Asset register --------------------------------------------------------------
CREATE INDEX ix_assets_class       ON records.assets (asset_class_id);
CREATE INDEX ix_assets_parent      ON records.assets (parent_asset_id);
CREATE INDEX ix_assets_site_ref    ON records.assets (site_ref);
CREATE INDEX ix_assets_status      ON records.assets (status);
CREATE INDEX ix_assets_legacy_src  ON records.assets (legacy_source_id);

CREATE INDEX ix_asset_classes_parent ON records.asset_classes (parent_class_id);

-- Data sheets -----------------------------------------------------------------
CREATE INDEX ix_form_submissions_asset     ON records.form_submissions (asset_id);
CREATE INDEX ix_form_submissions_template  ON records.form_submissions (template_id);
CREATE INDEX ix_form_submissions_project   ON records.form_submissions (project_ref);
CREATE INDEX ix_form_submissions_status    ON records.form_submissions (status);
CREATE INDEX ix_form_submissions_pm_event  ON records.form_submissions (pm_event_id);
CREATE INDEX ix_form_submissions_job_number ON records.form_submissions (job_number);  -- external/legacy join key

CREATE INDEX ix_form_templates_class ON records.form_templates (asset_class_id);
-- One current version per template_code.
CREATE UNIQUE INDEX uq_form_templates_current
    ON records.form_templates (template_code)
    WHERE is_current;

-- Test results ----------------------------------------------------------------
CREATE INDEX ix_form_field_values_form_submission  ON records.form_field_values (form_submission_id);
CREATE INDEX ix_form_field_values_assessment ON records.form_field_values (assessment);
CREATE INDEX ix_form_field_values_group      ON records.form_field_values (test_group);

-- PM tracking -----------------------------------------------------------------
CREATE INDEX ix_pm_programs_class    ON records.pm_programs (asset_class_id);
CREATE INDEX ix_pm_schedules_asset   ON records.pm_schedules (asset_id);
CREATE INDEX ix_pm_schedules_program ON records.pm_schedules (pm_program_id);
-- Drives the "what's coming due" dashboard.
CREATE INDEX ix_pm_schedules_due     ON records.pm_schedules (next_due_at) WHERE is_active;
CREATE INDEX ix_pm_events_schedule   ON records.pm_events (pm_schedule_id);
CREATE INDEX ix_pm_events_asset      ON records.pm_events (asset_id);
CREATE INDEX ix_pm_events_status     ON records.pm_events (status);
CREATE INDEX ix_pm_events_form_submission  ON records.pm_events (form_submission_id);
