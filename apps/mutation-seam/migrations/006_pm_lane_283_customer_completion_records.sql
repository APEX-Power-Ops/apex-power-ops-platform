-- ============================================================================
-- APEX PM Lane 283 - Customer Completion Baseline Persistence Schema
-- Migration: 006_pm_lane_283_customer_completion_records.sql
-- Created:   2026-05-18
-- ============================================================================
-- Adds only the dedicated customer completion baseline table admitted by PM Lane
-- 283. This table is for the Temp Power zero-report and zero-evidence baseline
-- record that follows the PM Lane 282 production tracking baseline.
--
-- Scope
--   * Create seam.customer_completion_records.
--   * Preserve one PM-owned customer/completion readiness baseline plus audit,
--     idempotency, import, field authorization, schedule-status, durable field,
--     and production tracking evidence.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No customer-facing report delivery, completion evidence artifact storage,
--     customer commitment, billing, payroll, invoice, accounting, external
--     finance output, schedule/date write, workpackage status write, workbook
--     writeback, or macro execution.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.customer_completion_records (
    id                            TEXT PRIMARY KEY,
    project_id                    TEXT NOT NULL,
    record_date                   DATE NOT NULL,
    record_kind                   TEXT NOT NULL,
    record_status                 TEXT NOT NULL,
    created_by_actor_id           TEXT NOT NULL,
    created_by_role               TEXT NOT NULL,
    recorded_at_utc               TIMESTAMPTZ NOT NULL,
    source_import_candidate_id    TEXT NOT NULL,
    source_import_fingerprint     TEXT NOT NULL,
    field_authorization_record_id TEXT NOT NULL,
    schedule_status_record_id     TEXT NOT NULL,
    durable_field_record_id       TEXT NOT NULL,
    production_tracking_record_id TEXT NOT NULL,
    production_tracking_authority TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_282_zero_actual_baseline',
    customer_reporting_authority  TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_283_customer_completion_baseline',
    completion_evidence_authority TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_283_zero_evidence_baseline',
    customer_delivery_authority   TEXT NOT NULL DEFAULT 'not_admitted_external_delivery',
    finance_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    billing_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    payroll_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    invoice_authority             TEXT NOT NULL DEFAULT 'not_admitted',
    accounting_authority          TEXT NOT NULL DEFAULT 'not_admitted',
    idempotency_key               TEXT NOT NULL,
    mutation_id                   TEXT NOT NULL,
    audit_event_id                TEXT NOT NULL,
    customer_completion_payload   JSONB NOT NULL DEFAULT '{}'::jsonb,
    precondition_readback         JSONB NOT NULL DEFAULT '{}'::jsonb,
    customer_report_artifacts     JSONB NOT NULL DEFAULT '[]'::jsonb,
    customer_report_count         INTEGER NOT NULL DEFAULT 0,
    completion_evidence_artifacts JSONB NOT NULL DEFAULT '[]'::jsonb,
    completion_evidence_count     INTEGER NOT NULL DEFAULT 0,
    customer_delivery_events      JSONB NOT NULL DEFAULT '[]'::jsonb,
    production_quantity_count     INTEGER NOT NULL DEFAULT 0,
    labor_entry_count             INTEGER NOT NULL DEFAULT 0,
    actual_labor_hours            NUMERIC(12, 2) NOT NULL DEFAULT 0,
    apparatus_progress_count      INTEGER NOT NULL DEFAULT 0,
    progress_update_count         INTEGER NOT NULL DEFAULT 0,
    daily_summary                 TEXT NOT NULL,
    data                          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT customer_completion_kind_valid
        CHECK (record_kind IN ('customer_completion_zero_evidence_baseline')),
    CONSTRAINT customer_completion_status_valid
        CHECK (record_status IN ('recorded')),
    CONSTRAINT customer_completion_created_by_role_valid
        CHECK (created_by_role IN ('pm')),
    CONSTRAINT customer_completion_production_authority_valid
        CHECK (production_tracking_authority = 'admitted_by_pm_lane_282_zero_actual_baseline'),
    CONSTRAINT customer_completion_reporting_authority_valid
        CHECK (customer_reporting_authority = 'admitted_by_pm_lane_283_customer_completion_baseline'),
    CONSTRAINT customer_completion_evidence_authority_valid
        CHECK (completion_evidence_authority = 'admitted_by_pm_lane_283_zero_evidence_baseline'),
    CONSTRAINT customer_completion_delivery_blocked
        CHECK (customer_delivery_authority = 'not_admitted_external_delivery'),
    CONSTRAINT customer_completion_finance_blocked
        CHECK (
            finance_authority = 'not_admitted'
            AND billing_authority = 'not_admitted'
            AND payroll_authority = 'not_admitted'
            AND invoice_authority = 'not_admitted'
            AND accounting_authority = 'not_admitted'
        ),
    CONSTRAINT customer_completion_zero_customer_outputs
        CHECK (customer_report_count = 0 AND completion_evidence_count = 0),
    CONSTRAINT customer_completion_zero_production_outputs
        CHECK (
            production_quantity_count = 0
            AND labor_entry_count = 0
            AND actual_labor_hours = 0
            AND apparatus_progress_count = 0
            AND progress_update_count = 0
        ),
    CONSTRAINT customer_completion_payload_object
        CHECK (jsonb_typeof(customer_completion_payload) = 'object'),
    CONSTRAINT customer_completion_preconditions_object
        CHECK (jsonb_typeof(precondition_readback) = 'object'),
    CONSTRAINT customer_completion_report_artifacts_array
        CHECK (jsonb_typeof(customer_report_artifacts) = 'array'),
    CONSTRAINT customer_completion_evidence_artifacts_array
        CHECK (jsonb_typeof(completion_evidence_artifacts) = 'array'),
    CONSTRAINT customer_completion_delivery_events_array
        CHECK (jsonb_typeof(customer_delivery_events) = 'array'),
    CONSTRAINT customer_completion_data_object
        CHECK (jsonb_typeof(data) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_completion_records_idempotency_key
    ON seam.customer_completion_records (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_completion_records_mutation_id
    ON seam.customer_completion_records (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_completion_records_audit_event_id
    ON seam.customer_completion_records (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_customer_completion_records_project_date
    ON seam.customer_completion_records (project_id, record_date DESC);

CREATE INDEX IF NOT EXISTS idx_customer_completion_records_source_candidate
    ON seam.customer_completion_records (source_import_candidate_id, source_import_fingerprint);

CREATE INDEX IF NOT EXISTS idx_customer_completion_records_production_tracking
    ON seam.customer_completion_records (production_tracking_record_id);

CREATE OR REPLACE FUNCTION seam.reject_customer_completion_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.customer_completion_records is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_customer_completion_records_insert_only_update
    ON seam.customer_completion_records;

CREATE TRIGGER trg_customer_completion_records_insert_only_update
    BEFORE UPDATE ON seam.customer_completion_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_customer_completion_record_mutation();

DROP TRIGGER IF EXISTS trg_customer_completion_records_insert_only_delete
    ON seam.customer_completion_records;

CREATE TRIGGER trg_customer_completion_records_insert_only_delete
    BEFORE DELETE ON seam.customer_completion_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_customer_completion_record_mutation();

ALTER TABLE seam.customer_completion_records ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON TABLE seam.customer_completion_records FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON TABLE seam.customer_completion_records FROM authenticated;
    END IF;
END;
$$;

COMMENT ON TABLE seam.customer_completion_records IS
    'Dedicated insert-only customer completion records. PM Lane 283 admits only a Temp Power zero-report, zero-evidence baseline, not external delivery or finance outputs.';
COMMENT ON COLUMN seam.customer_completion_records.customer_completion_payload IS
    'Validated normalized PM Lane 283 customer completion payload used for strict replay comparison.';
COMMENT ON COLUMN seam.customer_completion_records.data IS
    'Overflow metadata for the application PgDict adapter.';

-- ============================================================================
-- END of 006_pm_lane_283_customer_completion_records.sql
-- ============================================================================
