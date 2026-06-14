-- =============================================================================
-- NETA Records Domain — Triggers + Views  (Chip 1)
-- Packet: 2026-06-12-neta-records-001
-- Landing Lane: infra/database/migrations/neta/
-- Requires: 002_neta_tables.sql
--
-- updated_at auto-maintenance on every mutable table, plus two read views that
-- give the surface app its core operator screens without per-call joins:
--   * v_asset_test_history — latest data sheet + assessment per asset
--   * v_pm_due             — PM schedules with a derived due/overdue bucket
-- =============================================================================

-- ---------------------------------------------------------------------------
-- updated_at auto-maintenance (schema-local copy; mirrors work.fn_set_updated_at)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION neta.fn_set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION neta.fn_set_updated_at() IS
    'Sets updated_at = now() on UPDATE. Attached to every mutable neta table.';

CREATE TRIGGER trg_asset_classes_updated_at
    BEFORE UPDATE ON neta.asset_classes
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_assets_updated_at
    BEFORE UPDATE ON neta.assets
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_datasheet_templates_updated_at
    BEFORE UPDATE ON neta.datasheet_templates
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_datasheets_updated_at
    BEFORE UPDATE ON neta.datasheets
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_test_results_updated_at
    BEFORE UPDATE ON neta.test_results
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_pm_programs_updated_at
    BEFORE UPDATE ON neta.pm_programs
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_pm_schedules_updated_at
    BEFORE UPDATE ON neta.pm_schedules
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

CREATE TRIGGER trg_pm_events_updated_at
    BEFORE UPDATE ON neta.pm_events
    FOR EACH ROW EXECUTE FUNCTION neta.fn_set_updated_at();

-- ---------------------------------------------------------------------------
-- neta.v_asset_test_history
--   One row per (asset, data sheet) for the asset detail timeline — the
--   the asset test-history panel. Newest first.
-- ---------------------------------------------------------------------------
CREATE VIEW neta.v_asset_test_history AS
SELECT
    a.asset_id,
    a.asset_tag,
    a.name                    AS asset_name,
    d.datasheet_id,
    t.title                   AS template_title,
    t.neta_standard,
    d.status                  AS datasheet_status,
    d.overall_assessment,
    d.test_date,
    d.technician,
    d.created_at              AS datasheet_created_at
FROM neta.assets a
JOIN neta.datasheets d         ON d.asset_id = a.asset_id
JOIN neta.datasheet_templates t ON t.template_id = d.template_id
ORDER BY a.asset_tag, d.test_date DESC NULLS LAST, d.created_at DESC;

COMMENT ON VIEW neta.v_asset_test_history IS
    'Per-asset test-sheet timeline (the asset test-history panel), newest first.';

-- ---------------------------------------------------------------------------
-- neta.v_pm_due
--   Active PM schedules with a derived due bucket so the dashboard can sort by
--   urgency without recomputing date math per call. Bucket is relative to today.
-- ---------------------------------------------------------------------------
CREATE VIEW neta.v_pm_due AS
SELECT
    s.pm_schedule_id,
    s.asset_id,
    a.asset_tag,
    a.name                    AS asset_name,
    p.pm_program_id,
    p.name                    AS program_name,
    p.interval_value,
    p.interval_unit,
    s.last_performed_at,
    s.next_due_at,
    CASE
        WHEN s.next_due_at IS NULL                       THEN 'unscheduled'
        WHEN s.next_due_at <  current_date               THEN 'overdue'
        WHEN s.next_due_at <= current_date + INTERVAL '90 days' THEN 'due_soon'
        ELSE 'ok'
    END                       AS due_bucket
FROM neta.pm_schedules s
JOIN neta.assets a       ON a.asset_id = s.asset_id
JOIN neta.pm_programs p  ON p.pm_program_id = s.pm_program_id
WHERE s.is_active;

COMMENT ON VIEW neta.v_pm_due IS
    'Active PM schedules with a derived overdue/due_soon/ok/unscheduled bucket '
    'for the maintenance-due dashboard.';
