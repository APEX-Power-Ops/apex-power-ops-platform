-- ============================================================================
-- APEX PM Lane 282 - Production Tracking Baseline Persistence Schema
-- Migration: 005_pm_lane_282_production_tracking_records.sql
-- Created:   2026-05-18
-- ============================================================================
-- Adds only the dedicated production tracking record table admitted by PM Lane
-- 282. This table is for the Temp Power zero-actual baseline record that follows
-- the PM Lane 281 durable field record.
--
-- Scope
--   * Create seam.production_tracking_records.
--   * Preserve one zero-actual production baseline plus audit, idempotency,
--     import, field authorization, schedule-status, and durable field evidence.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No customer report, billing, payroll, invoice, accounting, external
--     finance output, evidence attachment storage, schedule/date write,
--     workpackage status write, workbook writeback, or macro execution.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.production_tracking_records (
    id                            TEXT PRIMARY KEY,
    project_id                    TEXT NOT NULL,
    record_date                   DATE NOT NULL,
    tracking_kind                 TEXT NOT NULL,
    record_status                 TEXT NOT NULL,
    created_by_actor_id           TEXT NOT NULL,
    created_by_role               TEXT NOT NULL,
    recorded_at_utc               TIMESTAMPTZ NOT NULL,
    source_import_candidate_id    TEXT NOT NULL,
    source_import_fingerprint     TEXT NOT NULL,
    field_authorization_record_id TEXT NOT NULL,
    schedule_status_record_id     TEXT NOT NULL,
    durable_field_record_id       TEXT NOT NULL,
    production_tracking_authority TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_282_zero_actual_baseline',
    customer_reporting_authority  TEXT NOT NULL DEFAULT 'not_admitted',
    finance_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    idempotency_key               TEXT NOT NULL,
    mutation_id                   TEXT NOT NULL,
    audit_event_id                TEXT NOT NULL,
    production_tracking_payload   JSONB NOT NULL DEFAULT '{}'::jsonb,
    precondition_readback         JSONB NOT NULL DEFAULT '{}'::jsonb,
    production_quantities         JSONB NOT NULL DEFAULT '[]'::jsonb,
    production_quantity_count     INTEGER NOT NULL DEFAULT 0,
    labor_entries                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    labor_entry_count             INTEGER NOT NULL DEFAULT 0,
    actual_labor_hours            NUMERIC(12, 2) NOT NULL DEFAULT 0,
    apparatus_progress            JSONB NOT NULL DEFAULT '[]'::jsonb,
    apparatus_progress_count      INTEGER NOT NULL DEFAULT 0,
    progress_updates              JSONB NOT NULL DEFAULT '[]'::jsonb,
    progress_update_count         INTEGER NOT NULL DEFAULT 0,
    daily_summary                 TEXT NOT NULL,
    data                          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT production_tracking_kind_valid
        CHECK (tracking_kind IN ('field_start_zero_actual_baseline')),
    CONSTRAINT production_tracking_status_valid
        CHECK (record_status IN ('recorded')),
    CONSTRAINT production_tracking_created_by_role_valid
        CHECK (created_by_role IN ('lead')),
    CONSTRAINT production_tracking_authority_valid
        CHECK (production_tracking_authority = 'admitted_by_pm_lane_282_zero_actual_baseline'),
    CONSTRAINT production_tracking_customer_blocked
        CHECK (customer_reporting_authority = 'not_admitted'),
    CONSTRAINT production_tracking_finance_blocked
        CHECK (finance_authority = 'not_admitted'),
    CONSTRAINT production_tracking_zero_quantities
        CHECK (production_quantity_count = 0),
    CONSTRAINT production_tracking_zero_labor
        CHECK (labor_entry_count = 0 AND actual_labor_hours = 0),
    CONSTRAINT production_tracking_zero_progress
        CHECK (apparatus_progress_count = 0 AND progress_update_count = 0),
    CONSTRAINT production_tracking_payload_object
        CHECK (jsonb_typeof(production_tracking_payload) = 'object'),
    CONSTRAINT production_tracking_preconditions_object
        CHECK (jsonb_typeof(precondition_readback) = 'object'),
    CONSTRAINT production_tracking_quantities_array
        CHECK (jsonb_typeof(production_quantities) = 'array'),
    CONSTRAINT production_tracking_labor_entries_array
        CHECK (jsonb_typeof(labor_entries) = 'array'),
    CONSTRAINT production_tracking_apparatus_progress_array
        CHECK (jsonb_typeof(apparatus_progress) = 'array'),
    CONSTRAINT production_tracking_progress_updates_array
        CHECK (jsonb_typeof(progress_updates) = 'array'),
    CONSTRAINT production_tracking_data_object
        CHECK (jsonb_typeof(data) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_production_tracking_records_idempotency_key
    ON seam.production_tracking_records (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_production_tracking_records_mutation_id
    ON seam.production_tracking_records (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_production_tracking_records_audit_event_id
    ON seam.production_tracking_records (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_production_tracking_records_project_date
    ON seam.production_tracking_records (project_id, record_date DESC);

CREATE INDEX IF NOT EXISTS idx_production_tracking_records_source_candidate
    ON seam.production_tracking_records (source_import_candidate_id, source_import_fingerprint);

CREATE INDEX IF NOT EXISTS idx_production_tracking_records_durable_field
    ON seam.production_tracking_records (durable_field_record_id);

CREATE OR REPLACE FUNCTION seam.reject_production_tracking_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.production_tracking_records is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_production_tracking_records_insert_only_update
    ON seam.production_tracking_records;

CREATE TRIGGER trg_production_tracking_records_insert_only_update
    BEFORE UPDATE ON seam.production_tracking_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_production_tracking_record_mutation();

DROP TRIGGER IF EXISTS trg_production_tracking_records_insert_only_delete
    ON seam.production_tracking_records;

CREATE TRIGGER trg_production_tracking_records_insert_only_delete
    BEFORE DELETE ON seam.production_tracking_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_production_tracking_record_mutation();

ALTER TABLE seam.production_tracking_records ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON TABLE seam.production_tracking_records FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON TABLE seam.production_tracking_records FROM authenticated;
    END IF;
END;
$$;

COMMENT ON TABLE seam.production_tracking_records IS
    'Dedicated insert-only production tracking records. PM Lane 282 admits only a Temp Power zero-actual baseline, not customer or finance outputs.';
COMMENT ON COLUMN seam.production_tracking_records.production_tracking_payload IS
    'Validated normalized PM Lane 282 production tracking payload used for strict replay comparison.';
COMMENT ON COLUMN seam.production_tracking_records.data IS
    'Overflow metadata for the application PgDict adapter.';

-- ============================================================================
-- END of 005_pm_lane_282_production_tracking_records.sql
-- ============================================================================
