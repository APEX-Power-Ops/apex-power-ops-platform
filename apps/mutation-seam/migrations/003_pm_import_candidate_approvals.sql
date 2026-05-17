-- ============================================================================
-- APEX PM Lane 136 — Import Candidate Approval Persistence Schema
-- Migration: 003_pm_import_candidate_approvals.sql
-- Created:   2026-05-16
-- ============================================================================
-- Adds only the dedicated insert-only approval record table admitted by PM
-- Lane 049 and implemented by PM Lane 136.
--
-- Scope
--   * Create seam.pm_import_candidate_approvals.
--   * Preserve candidate/source/shape/idempotency evidence for later import
--     packet diffing.
--   * Enable RLS as defense in depth per Supabase guidance.
--
-- Out of scope
--   * No project, workpackage, task, apparatus, issue, assignment, schedule,
--     status, field record, production tracking, workbook, or import rows.
--   * No generic mutation-pipeline table.
--   * No update/delete runtime path.
--
-- Re-runnability
--   * CREATE statements use IF NOT EXISTS.
--   * Constraint/index creation is guarded by names or IF NOT EXISTS.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.pm_import_candidate_approvals (
    approval_record_id           TEXT PRIMARY KEY,
    mutation_id                  TEXT NOT NULL,
    audit_event_id               TEXT NOT NULL,
    candidate_id                 TEXT NOT NULL,
    candidate_version            TEXT NOT NULL,
    source_stat_fingerprint      TEXT NOT NULL,
    candidate_shape_fingerprint  TEXT NOT NULL,
    idempotency_key              TEXT NOT NULL,
    decision                     TEXT NOT NULL,
    approved_by_actor_id         TEXT NOT NULL,
    approved_at_utc              TIMESTAMPTZ NOT NULL,
    accepted_warning_codes       JSONB NOT NULL DEFAULT '[]'::jsonb,
    accepted_no_go_overrides     JSONB NOT NULL DEFAULT '[]'::jsonb,
    review_notes                 TEXT NOT NULL,
    approval_payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_result            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pm_import_candidate_approvals_decision_valid
        CHECK (decision IN ('approve_for_import_packet', 'return_for_revision', 'reject_candidate')),
    CONSTRAINT pm_import_candidate_approvals_warning_codes_array
        CHECK (jsonb_typeof(accepted_warning_codes) = 'array'),
    CONSTRAINT pm_import_candidate_approvals_no_go_overrides_array
        CHECK (jsonb_typeof(accepted_no_go_overrides) = 'array'),
    CONSTRAINT pm_import_candidate_approvals_payload_object
        CHECK (jsonb_typeof(approval_payload) = 'object'),
    CONSTRAINT pm_import_candidate_approvals_validation_object
        CHECK (jsonb_typeof(validation_result) = 'object'),
    CONSTRAINT pm_import_candidate_approvals_review_notes_nonempty
        CHECK (length(btrim(review_notes)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_identity_idempotency
    ON seam.pm_import_candidate_approvals (
        candidate_id,
        candidate_version,
        source_stat_fingerprint,
        candidate_shape_fingerprint,
        idempotency_key
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_mutation_id
    ON seam.pm_import_candidate_approvals (mutation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_audit_event_id
    ON seam.pm_import_candidate_approvals (audit_event_id);

CREATE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_candidate
    ON seam.pm_import_candidate_approvals (candidate_id, candidate_version, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_decision
    ON seam.pm_import_candidate_approvals (decision);

CREATE OR REPLACE FUNCTION seam.reject_pm_import_candidate_approval_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'seam.pm_import_candidate_approvals is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_pm_import_candidate_approvals_insert_only_update
    ON seam.pm_import_candidate_approvals;

CREATE TRIGGER trg_pm_import_candidate_approvals_insert_only_update
    BEFORE UPDATE ON seam.pm_import_candidate_approvals
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_pm_import_candidate_approval_mutation();

DROP TRIGGER IF EXISTS trg_pm_import_candidate_approvals_insert_only_delete
    ON seam.pm_import_candidate_approvals;

CREATE TRIGGER trg_pm_import_candidate_approvals_insert_only_delete
    BEFORE DELETE ON seam.pm_import_candidate_approvals
    FOR EACH ROW
    EXECUTE FUNCTION seam.reject_pm_import_candidate_approval_mutation();

ALTER TABLE seam.pm_import_candidate_approvals ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE seam.pm_import_candidate_approvals FROM anon;
REVOKE ALL ON TABLE seam.pm_import_candidate_approvals FROM authenticated;

COMMENT ON TABLE seam.pm_import_candidate_approvals IS
    'Dedicated insert-only Project Miner import-candidate approval records. Does not import project/work rows.';
COMMENT ON COLUMN seam.pm_import_candidate_approvals.approval_record_id IS
    'Deterministic id from candidate identity plus idempotency key.';
COMMENT ON COLUMN seam.pm_import_candidate_approvals.mutation_id IS
    'Server mutation id returned for the initial accepted approval persistence request and idempotent replays.';
COMMENT ON COLUMN seam.pm_import_candidate_approvals.audit_event_id IS
    'Audit event id appended with the approval record insert.';
COMMENT ON COLUMN seam.pm_import_candidate_approvals.approval_payload IS
    'Validated normalized approval payload. Used for strict idempotent replay comparison.';
COMMENT ON COLUMN seam.pm_import_candidate_approvals.validation_result IS
    'Result from validate_project_import_approval_payload at persistence time.';

-- ============================================================================
-- END of 003_pm_import_candidate_approvals.sql
-- ============================================================================
