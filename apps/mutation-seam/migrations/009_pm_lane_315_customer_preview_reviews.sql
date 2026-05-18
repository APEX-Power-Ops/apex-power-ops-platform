CREATE SCHEMA IF NOT EXISTS seam;

CREATE TABLE IF NOT EXISTS seam.pm_customer_preview_reviews (
    review_id                    TEXT PRIMARY KEY,
    mutation_id                  TEXT NOT NULL,
    audit_event_id               TEXT NOT NULL,
    project_id                   TEXT NOT NULL,
    candidate_id                 TEXT NOT NULL,
    source_fingerprint           TEXT NOT NULL,
    customer_preview_id          TEXT NOT NULL,
    coverage_scope_task_ids      JSONB NOT NULL DEFAULT '[]'::jsonb,
    coverage_scope_apparatus_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    preview_summary              TEXT NOT NULL,
    preview_artifact_refs        JSONB NOT NULL DEFAULT '[]'::jsonb,
    named_recipient_name         TEXT NOT NULL,
    named_recipient_role         TEXT NOT NULL,
    delivery_channel             TEXT NOT NULL CHECK (delivery_channel IN ('CONTROLLED_EMAIL', 'LATER_APPROVED_PORTAL')),
    future_delivery_proof_requirements JSONB NOT NULL DEFAULT '[]'::jsonb,
    durable_delivery_event       BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_proof_recorded      BOOLEAN NOT NULL DEFAULT FALSE,
    delivery_block_reason        TEXT NOT NULL,
    pm_review_status             TEXT NOT NULL,
    pm_review_note               TEXT NOT NULL,
    pm_actor                     TEXT NOT NULL,
    approver_role                TEXT NOT NULL,
    pm_reviewed_at               TIMESTAMPTZ NOT NULL,
    idempotency_key              TEXT NOT NULL,
    customer_delivery_authority  TEXT NOT NULL DEFAULT 'not_admitted',
    finance_authority            TEXT NOT NULL DEFAULT 'not_admitted',
    source_writeback_authority   TEXT NOT NULL DEFAULT 'not_admitted',
    route                        TEXT NOT NULL,
    status_route                 TEXT NOT NULL,
    storage_source               TEXT NOT NULL,
    persistence_version          TEXT NOT NULL,
    review_payload               JSONB NOT NULL,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT pm_customer_preview_reviews_durable_delivery_false CHECK (durable_delivery_event = FALSE),
    CONSTRAINT pm_customer_preview_reviews_delivery_proof_false CHECK (delivery_proof_recorded = FALSE)
);

CREATE OR REPLACE FUNCTION seam.reject_pm_customer_preview_review_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'pm_customer_preview_reviews is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_reject_pm_customer_preview_review_update ON seam.pm_customer_preview_reviews;
CREATE TRIGGER trg_reject_pm_customer_preview_review_update
BEFORE UPDATE ON seam.pm_customer_preview_reviews
FOR EACH ROW EXECUTE FUNCTION seam.reject_pm_customer_preview_review_mutation();

DROP TRIGGER IF EXISTS trg_reject_pm_customer_preview_review_delete ON seam.pm_customer_preview_reviews;
CREATE TRIGGER trg_reject_pm_customer_preview_review_delete
BEFORE DELETE ON seam.pm_customer_preview_reviews
FOR EACH ROW EXECUTE FUNCTION seam.reject_pm_customer_preview_review_mutation();

ALTER TABLE seam.pm_customer_preview_reviews ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE seam.pm_customer_preview_reviews FROM anon;
REVOKE ALL ON TABLE seam.pm_customer_preview_reviews FROM authenticated;