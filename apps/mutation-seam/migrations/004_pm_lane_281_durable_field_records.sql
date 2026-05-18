-- ============================================================================
-- APEX PM Lane 281 - Durable Field Record Persistence Schema
-- Migration: 004_pm_lane_281_durable_field_records.sql
-- Created:   2026-05-18
-- ============================================================================
-- Adds only the dedicated durable field record table admitted by PM Lane 281.
--
-- Scope
--   * Create seam.durable_field_records.
--   * Preserve the first Temp Power field-start readiness record plus audit,
--     idempotency, import, field authorization, and schedule-status evidence.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No production quantities, customer reports, billing, payroll, invoice,
--     accounting, external finance output, evidence attachment storage, direct
--     schedule/date writes, workbook writeback, or macro execution.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.durable_field_records (
    id                            TEXT PRIMARY KEY,
    project_id                    TEXT NOT NULL,
    record_date                   DATE NOT NULL,
    field_record_kind             TEXT NOT NULL,
    record_status                 TEXT NOT NULL,
    created_by_actor_id           TEXT NOT NULL,
    created_by_role               TEXT NOT NULL,
    recorded_at_utc               TIMESTAMPTZ NOT NULL,
    source_import_candidate_id    TEXT NOT NULL,
    source_import_fingerprint     TEXT NOT NULL,
    field_authorization_record_id TEXT NOT NULL,
    schedule_status_record_id     TEXT NOT NULL,
    production_tracking_authority TEXT NOT NULL DEFAULT 'not_admitted',
    customer_reporting_authority  TEXT NOT NULL DEFAULT 'not_admitted',
    finance_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    idempotency_key               TEXT NOT NULL,
    mutation_id                   TEXT NOT NULL,
    audit_event_id                TEXT NOT NULL,
    field_record_payload          JSONB NOT NULL DEFAULT '{}'::jsonb,
    data                          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT durable_field_records_kind_valid
        CHECK (field_record_kind IN ('field_start_readiness')),
    CONSTRAINT durable_field_records_status_valid
        CHECK (record_status IN ('recorded')),
    CONSTRAINT durable_field_records_created_by_role_valid
        CHECK (created_by_role IN ('lead')),
    CONSTRAINT durable_field_records_production_blocked
        CHECK (production_tracking_authority = 'not_admitted'),
    CONSTRAINT durable_field_records_customer_blocked
        CHECK (customer_reporting_authority = 'not_admitted'),
    CONSTRAINT durable_field_records_finance_blocked
        CHECK (finance_authority = 'not_admitted'),
    CONSTRAINT durable_field_records_payload_object
        CHECK (jsonb_typeof(field_record_payload) = 'object'),
    CONSTRAINT durable_field_records_data_object
        CHECK (jsonb_typeof(data) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_durable_field_records_idempotency_key
    ON seam.durable_field_records (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_durable_field_records_mutation_id
    ON seam.durable_field_records (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_durable_field_records_audit_event_id
    ON seam.durable_field_records (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_durable_field_records_project_date
    ON seam.durable_field_records (project_id, record_date DESC);

CREATE INDEX IF NOT EXISTS idx_durable_field_records_source_candidate
    ON seam.durable_field_records (source_import_candidate_id, source_import_fingerprint);

CREATE OR REPLACE FUNCTION seam.reject_durable_field_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.durable_field_records is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_durable_field_records_insert_only_update
    ON seam.durable_field_records;

CREATE TRIGGER trg_durable_field_records_insert_only_update
    BEFORE UPDATE ON seam.durable_field_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_durable_field_record_mutation();

DROP TRIGGER IF EXISTS trg_durable_field_records_insert_only_delete
    ON seam.durable_field_records;

CREATE TRIGGER trg_durable_field_records_insert_only_delete
    BEFORE DELETE ON seam.durable_field_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_durable_field_record_mutation();

ALTER TABLE seam.durable_field_records ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON TABLE seam.durable_field_records FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON TABLE seam.durable_field_records FROM authenticated;
    END IF;
END;
$$;

COMMENT ON TABLE seam.durable_field_records IS
    'Dedicated insert-only durable field records for admitted PM field lanes. PM Lane 281 admits only a Temp Power readiness record, not production/customer/finance outputs.';
COMMENT ON COLUMN seam.durable_field_records.field_record_payload IS
    'Validated normalized PM Lane 281 field record payload used for strict replay comparison.';
COMMENT ON COLUMN seam.durable_field_records.data IS
    'Overflow metadata for the application PgDict adapter.';

-- ============================================================================
-- END of 004_pm_lane_281_durable_field_records.sql
-- ============================================================================
