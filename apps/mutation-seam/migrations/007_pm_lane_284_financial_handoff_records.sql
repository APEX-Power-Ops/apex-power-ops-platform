-- ============================================================================
-- APEX PM Lane 284 - Financial Handoff Baseline Persistence Schema
-- Migration: 007_pm_lane_284_financial_handoff_records.sql
-- Created:   2026-05-18
-- ============================================================================
-- Adds only the dedicated financial handoff baseline table admitted by PM Lane
-- 284. This table is for the Temp Power zero-billing, zero-payroll, zero-invoice,
-- zero-accounting baseline record that follows the PM Lane 283 customer
-- completion baseline.
--
-- Scope
--   * Create seam.financial_handoff_records.
--   * Preserve one PM-owned financial handoff readiness baseline plus audit,
--     idempotency, import, field authorization, schedule-status, durable field,
--     production tracking, and customer completion evidence.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No billing export, payroll export, invoice, payroll record, accounting
--     record, customer billing delivery, external finance-system sync, workbook
--     writeback, or macro execution.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.financial_handoff_records (
    id                                  TEXT PRIMARY KEY,
    project_id                          TEXT NOT NULL,
    record_date                         DATE NOT NULL,
    record_kind                         TEXT NOT NULL,
    record_status                       TEXT NOT NULL,
    created_by_actor_id                 TEXT NOT NULL,
    created_by_role                     TEXT NOT NULL,
    recorded_at_utc                     TIMESTAMPTZ NOT NULL,
    source_import_candidate_id          TEXT NOT NULL,
    source_import_fingerprint           TEXT NOT NULL,
    field_authorization_record_id       TEXT NOT NULL,
    schedule_status_record_id           TEXT NOT NULL,
    durable_field_record_id             TEXT NOT NULL,
    production_tracking_record_id       TEXT NOT NULL,
    customer_completion_record_id       TEXT NOT NULL,
    production_tracking_authority       TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_282_zero_actual_baseline',
    customer_reporting_authority        TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_283_customer_completion_baseline',
    completion_evidence_authority       TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_283_zero_evidence_baseline',
    customer_delivery_authority         TEXT NOT NULL DEFAULT 'not_admitted_external_delivery',
    financial_handoff_authority         TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_284_zero_finance_handoff_baseline',
    labor_reconciliation_authority      TEXT NOT NULL DEFAULT 'admitted_by_pm_lane_284_zero_labor_reconciliation_baseline',
    finance_authority                   TEXT NOT NULL DEFAULT 'not_admitted',
    billing_export_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    payroll_export_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    invoice_authority                   TEXT NOT NULL DEFAULT 'not_admitted',
    accounting_authority                TEXT NOT NULL DEFAULT 'not_admitted',
    external_finance_sync_authority     TEXT NOT NULL DEFAULT 'not_admitted',
    customer_billing_delivery_authority TEXT NOT NULL DEFAULT 'not_admitted',
    idempotency_key                     TEXT NOT NULL,
    mutation_id                         TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    financial_handoff_payload           JSONB NOT NULL DEFAULT '{}'::jsonb,
    precondition_readback               JSONB NOT NULL DEFAULT '{}'::jsonb,
    billing_export_artifacts            JSONB NOT NULL DEFAULT '[]'::jsonb,
    billing_export_count                INTEGER NOT NULL DEFAULT 0,
    payroll_export_artifacts            JSONB NOT NULL DEFAULT '[]'::jsonb,
    payroll_export_count                INTEGER NOT NULL DEFAULT 0,
    invoice_records                     JSONB NOT NULL DEFAULT '[]'::jsonb,
    invoice_record_count                INTEGER NOT NULL DEFAULT 0,
    payroll_records                     JSONB NOT NULL DEFAULT '[]'::jsonb,
    payroll_record_count                INTEGER NOT NULL DEFAULT 0,
    accounting_records                  JSONB NOT NULL DEFAULT '[]'::jsonb,
    accounting_record_count             INTEGER NOT NULL DEFAULT 0,
    labor_reconciliation_entries        JSONB NOT NULL DEFAULT '[]'::jsonb,
    labor_reconciliation_entry_count    INTEGER NOT NULL DEFAULT 0,
    external_finance_sync_events        JSONB NOT NULL DEFAULT '[]'::jsonb,
    external_finance_sync_count         INTEGER NOT NULL DEFAULT 0,
    customer_billing_delivery_events    JSONB NOT NULL DEFAULT '[]'::jsonb,
    customer_billing_delivery_count     INTEGER NOT NULL DEFAULT 0,
    billable_amount_total               NUMERIC(12, 2) NOT NULL DEFAULT 0,
    payroll_amount_total                NUMERIC(12, 2) NOT NULL DEFAULT 0,
    production_quantity_count           INTEGER NOT NULL DEFAULT 0,
    labor_entry_count                   INTEGER NOT NULL DEFAULT 0,
    actual_labor_hours                  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    apparatus_progress_count            INTEGER NOT NULL DEFAULT 0,
    progress_update_count               INTEGER NOT NULL DEFAULT 0,
    customer_report_count               INTEGER NOT NULL DEFAULT 0,
    completion_evidence_count           INTEGER NOT NULL DEFAULT 0,
    daily_summary                       TEXT NOT NULL,
    data                                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT financial_handoff_kind_valid
        CHECK (record_kind IN ('financial_handoff_zero_output_baseline')),
    CONSTRAINT financial_handoff_status_valid
        CHECK (record_status IN ('recorded')),
    CONSTRAINT financial_handoff_created_by_role_valid
        CHECK (created_by_role IN ('pm')),
    CONSTRAINT financial_handoff_production_authority_valid
        CHECK (production_tracking_authority = 'admitted_by_pm_lane_282_zero_actual_baseline'),
    CONSTRAINT financial_handoff_customer_authority_valid
        CHECK (
            customer_reporting_authority = 'admitted_by_pm_lane_283_customer_completion_baseline'
            AND completion_evidence_authority = 'admitted_by_pm_lane_283_zero_evidence_baseline'
            AND customer_delivery_authority = 'not_admitted_external_delivery'
        ),
    CONSTRAINT financial_handoff_authority_valid
        CHECK (financial_handoff_authority = 'admitted_by_pm_lane_284_zero_finance_handoff_baseline'),
    CONSTRAINT financial_handoff_labor_reconciliation_authority_valid
        CHECK (labor_reconciliation_authority = 'admitted_by_pm_lane_284_zero_labor_reconciliation_baseline'),
    CONSTRAINT financial_handoff_outputs_blocked
        CHECK (
            finance_authority = 'not_admitted'
            AND billing_export_authority = 'not_admitted'
            AND payroll_export_authority = 'not_admitted'
            AND invoice_authority = 'not_admitted'
            AND accounting_authority = 'not_admitted'
            AND external_finance_sync_authority = 'not_admitted'
            AND customer_billing_delivery_authority = 'not_admitted'
        ),
    CONSTRAINT financial_handoff_zero_finance_outputs
        CHECK (
            billing_export_count = 0
            AND payroll_export_count = 0
            AND invoice_record_count = 0
            AND payroll_record_count = 0
            AND accounting_record_count = 0
            AND labor_reconciliation_entry_count = 0
            AND external_finance_sync_count = 0
            AND customer_billing_delivery_count = 0
            AND billable_amount_total = 0
            AND payroll_amount_total = 0
        ),
    CONSTRAINT financial_handoff_zero_upstream_outputs
        CHECK (
            production_quantity_count = 0
            AND labor_entry_count = 0
            AND actual_labor_hours = 0
            AND apparatus_progress_count = 0
            AND progress_update_count = 0
            AND customer_report_count = 0
            AND completion_evidence_count = 0
        ),
    CONSTRAINT financial_handoff_payload_object
        CHECK (jsonb_typeof(financial_handoff_payload) = 'object'),
    CONSTRAINT financial_handoff_preconditions_object
        CHECK (jsonb_typeof(precondition_readback) = 'object'),
    CONSTRAINT financial_handoff_billing_exports_array
        CHECK (jsonb_typeof(billing_export_artifacts) = 'array'),
    CONSTRAINT financial_handoff_payroll_exports_array
        CHECK (jsonb_typeof(payroll_export_artifacts) = 'array'),
    CONSTRAINT financial_handoff_invoice_records_array
        CHECK (jsonb_typeof(invoice_records) = 'array'),
    CONSTRAINT financial_handoff_payroll_records_array
        CHECK (jsonb_typeof(payroll_records) = 'array'),
    CONSTRAINT financial_handoff_accounting_records_array
        CHECK (jsonb_typeof(accounting_records) = 'array'),
    CONSTRAINT financial_handoff_labor_reconciliation_array
        CHECK (jsonb_typeof(labor_reconciliation_entries) = 'array'),
    CONSTRAINT financial_handoff_external_sync_array
        CHECK (jsonb_typeof(external_finance_sync_events) = 'array'),
    CONSTRAINT financial_handoff_customer_billing_delivery_array
        CHECK (jsonb_typeof(customer_billing_delivery_events) = 'array'),
    CONSTRAINT financial_handoff_data_object
        CHECK (jsonb_typeof(data) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_financial_handoff_records_idempotency_key
    ON seam.financial_handoff_records (idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_financial_handoff_records_mutation_id
    ON seam.financial_handoff_records (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_financial_handoff_records_audit_event_id
    ON seam.financial_handoff_records (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_financial_handoff_records_project_date
    ON seam.financial_handoff_records (project_id, record_date DESC);

CREATE INDEX IF NOT EXISTS idx_financial_handoff_records_source_candidate
    ON seam.financial_handoff_records (source_import_candidate_id, source_import_fingerprint);

CREATE INDEX IF NOT EXISTS idx_financial_handoff_records_customer_completion
    ON seam.financial_handoff_records (customer_completion_record_id);

CREATE OR REPLACE FUNCTION seam.reject_financial_handoff_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.financial_handoff_records is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_financial_handoff_records_insert_only_update
    ON seam.financial_handoff_records;

CREATE TRIGGER trg_financial_handoff_records_insert_only_update
    BEFORE UPDATE ON seam.financial_handoff_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_financial_handoff_record_mutation();

DROP TRIGGER IF EXISTS trg_financial_handoff_records_insert_only_delete
    ON seam.financial_handoff_records;

CREATE TRIGGER trg_financial_handoff_records_insert_only_delete
    BEFORE DELETE ON seam.financial_handoff_records
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_financial_handoff_record_mutation();

ALTER TABLE seam.financial_handoff_records ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON TABLE seam.financial_handoff_records FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON TABLE seam.financial_handoff_records FROM authenticated;
    END IF;
END;
$$;

COMMENT ON TABLE seam.financial_handoff_records IS
    'Dedicated insert-only financial handoff records. PM Lane 284 admits only a Temp Power zero-finance-output baseline, not billing/payroll/invoice/accounting or external sync.';
COMMENT ON COLUMN seam.financial_handoff_records.financial_handoff_payload IS
    'Validated normalized PM Lane 284 financial handoff payload used for strict replay comparison.';
COMMENT ON COLUMN seam.financial_handoff_records.data IS
    'Overflow metadata for the application PgDict adapter.';

-- ============================================================================
-- END of 007_pm_lane_284_financial_handoff_records.sql
-- ============================================================================
