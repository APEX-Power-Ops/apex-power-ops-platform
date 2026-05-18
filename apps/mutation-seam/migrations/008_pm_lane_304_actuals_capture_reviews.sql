-- ============================================================================
-- APEX PM Lane 304 - Temp Power Actuals Capture Review Persistence Schema
-- Migration: 008_pm_lane_304_actuals_capture_reviews.sql
-- Created:   2026-05-18
-- ============================================================================
-- Adds only the dedicated insert-only actuals capture review table admitted by
-- PM Lane 304 for the current Project Miner Temp Power candidate.
--
-- Scope
--   * Create seam.pm_actuals_capture_reviews.
--   * Preserve PM review identity, evidence, correction lineage, idempotency,
--     and audit references for the admitted actuals-capture review route.
--   * Keep customer delivery, finance, and source-writeback boundaries blocked.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No customer preview rows.
--   * No customer delivery, durable delivery event, billing, payroll, invoice,
--     accounting, finance export, or source workbook writeback.
--   * No generic mutation-pipeline table.
--   * No update/delete runtime path.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.pm_actuals_capture_reviews (
    review_id                    TEXT PRIMARY KEY,
    mutation_id                  TEXT NOT NULL,
    audit_event_id               TEXT NOT NULL,
    project_id                   TEXT NOT NULL,
    candidate_id                 TEXT NOT NULL,
    source_fingerprint           TEXT NOT NULL,
    task_id                      TEXT NOT NULL,
    apparatus_id                 TEXT,
    task_day_fallback_reason     TEXT,
    work_date                    DATE NOT NULL,
    recorder_role                TEXT NOT NULL,
    actual_labor_hours_preview   DOUBLE PRECISION NOT NULL,
    work_summary_note            TEXT NOT NULL,
    primary_evidence_type        TEXT NOT NULL,
    primary_evidence_ref         TEXT NOT NULL,
    supporting_evidence_refs     JSONB NOT NULL DEFAULT '[]'::jsonb,
    correction_mode              TEXT NOT NULL,
    supersedes_review_id         TEXT,
    replacement_reason           TEXT,
    pm_review_status             TEXT NOT NULL,
    pm_review_note               TEXT NOT NULL,
    pm_actor                     TEXT NOT NULL,
    pm_actor_role                TEXT NOT NULL,
    pm_reviewed_at_utc           TIMESTAMPTZ NOT NULL,
    idempotency_key              TEXT NOT NULL,
    customer_delivery_authority  TEXT NOT NULL DEFAULT 'not_admitted',
    finance_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    source_writeback_authority   TEXT NOT NULL DEFAULT 'not_admitted',
    durable_delivery_event       BOOLEAN NOT NULL DEFAULT FALSE,
    review_payload               JSONB NOT NULL DEFAULT '{}'::jsonb,
    data                         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pm_actuals_capture_reviews_hours_nonnegative
        CHECK (actual_labor_hours_preview >= 0),
    CONSTRAINT pm_actuals_capture_reviews_supporting_evidence_array
        CHECK (jsonb_typeof(supporting_evidence_refs) = 'array'),
    CONSTRAINT pm_actuals_capture_reviews_review_payload_object
        CHECK (jsonb_typeof(review_payload) = 'object'),
    CONSTRAINT pm_actuals_capture_reviews_data_object
        CHECK (jsonb_typeof(data) = 'object'),
    CONSTRAINT pm_actuals_capture_reviews_correction_mode_valid
        CHECK (correction_mode IN ('ORIGINAL_REVIEW', 'VOID_AND_REPLACEMENT')),
    CONSTRAINT pm_actuals_capture_reviews_pm_actor_role_valid
        CHECK (pm_actor_role IN ('pm')),
    CONSTRAINT pm_actuals_capture_reviews_customer_delivery_blocked
        CHECK (customer_delivery_authority = 'not_admitted'),
    CONSTRAINT pm_actuals_capture_reviews_finance_blocked
        CHECK (finance_authority = 'not_admitted'),
    CONSTRAINT pm_actuals_capture_reviews_source_writeback_blocked
        CHECK (source_writeback_authority = 'not_admitted'),
    CONSTRAINT pm_actuals_capture_reviews_durable_delivery_blocked
        CHECK (durable_delivery_event = FALSE),
    CONSTRAINT pm_actuals_capture_reviews_work_summary_nonempty
        CHECK (length(btrim(work_summary_note)) > 0),
    CONSTRAINT pm_actuals_capture_reviews_pm_review_note_nonempty
        CHECK (length(btrim(pm_review_note)) > 0),
    CONSTRAINT pm_actuals_capture_reviews_pm_review_status_nonempty
        CHECK (length(btrim(pm_review_status)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_actuals_capture_reviews_idempotency
    ON seam.pm_actuals_capture_reviews (project_id, candidate_id, source_fingerprint, idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_actuals_capture_reviews_mutation_id
    ON seam.pm_actuals_capture_reviews (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_actuals_capture_reviews_audit_event_id
    ON seam.pm_actuals_capture_reviews (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_pm_actuals_capture_reviews_project_work_date
    ON seam.pm_actuals_capture_reviews (project_id, work_date DESC);

CREATE INDEX IF NOT EXISTS idx_pm_actuals_capture_reviews_task_apparatus
    ON seam.pm_actuals_capture_reviews (task_id, apparatus_id, created_at DESC);

CREATE OR REPLACE FUNCTION seam.reject_pm_actuals_capture_review_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.pm_actuals_capture_reviews is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_pm_actuals_capture_reviews_insert_only_update
    ON seam.pm_actuals_capture_reviews;

CREATE TRIGGER trg_pm_actuals_capture_reviews_insert_only_update
    BEFORE UPDATE ON seam.pm_actuals_capture_reviews
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_pm_actuals_capture_review_mutation();

DROP TRIGGER IF EXISTS trg_pm_actuals_capture_reviews_insert_only_delete
    ON seam.pm_actuals_capture_reviews;

CREATE TRIGGER trg_pm_actuals_capture_reviews_insert_only_delete
    BEFORE DELETE ON seam.pm_actuals_capture_reviews
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_pm_actuals_capture_review_mutation();

ALTER TABLE seam.pm_actuals_capture_reviews ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON TABLE seam.pm_actuals_capture_reviews FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON TABLE seam.pm_actuals_capture_reviews FROM authenticated;
    END IF;
END;
$$;

COMMENT ON TABLE seam.pm_actuals_capture_reviews IS
    'Dedicated insert-only Temp Power actuals capture review records. Customer delivery, finance, and source writeback remain blocked.';
COMMENT ON COLUMN seam.pm_actuals_capture_reviews.review_payload IS
    'Validated PM Lane 304 actuals capture review payload used for strict replay comparison.';
COMMENT ON COLUMN seam.pm_actuals_capture_reviews.data IS
    'Overflow metadata for the application PgDict adapter.';

-- ============================================================================
-- END of 008_pm_lane_304_actuals_capture_reviews.sql
-- ============================================================================