CREATE TABLE IF NOT EXISTS seam.pm_customer_delivery_proof_reviews (
    customer_delivery_proof_review_id   TEXT PRIMARY KEY,
    mutation_id                         TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    project_id                          TEXT NOT NULL,
    candidate_id                        TEXT NOT NULL,
    source_fingerprint                  TEXT NOT NULL,
    customer_preview_review_id          TEXT NOT NULL,
    customer_delivery_event_id          TEXT NOT NULL,
    preview_artifact_lineage_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    named_recipient_name                TEXT NOT NULL,
    named_recipient_role                TEXT NOT NULL,
    delivery_channel                    TEXT NOT NULL CHECK (delivery_channel IN ('CONTROLLED_EMAIL', 'LATER_APPROVED_PORTAL')),
    delivery_artifact_refs_json         JSONB NOT NULL DEFAULT '[]'::jsonb,
    delivered_at_utc                    TIMESTAMPTZ NOT NULL,
    delivery_note                       TEXT NOT NULL,
    delivery_proof_type                 TEXT NOT NULL,
    delivery_proof_ref                  TEXT NOT NULL,
    delivery_proof_recorded             BOOLEAN NOT NULL DEFAULT FALSE,
    proof_recorded_at_utc               TIMESTAMPTZ,
    pm_delivery_approval_status         TEXT NOT NULL,
    pm_delivery_approval_note           TEXT NOT NULL,
    pm_actor                            TEXT NOT NULL,
    pm_reviewed_at                      TIMESTAMPTZ NOT NULL,
    idempotency_key                     TEXT NOT NULL UNIQUE,
    mutation_class                      TEXT NOT NULL DEFAULT 'C',
    source_route                        TEXT NOT NULL DEFAULT '/api/v1/mutations/temp-power-customer-delivery-proof-reviews',
    finance_export_recorded             BOOLEAN NOT NULL DEFAULT FALSE,
    source_writeback_recorded           BOOLEAN NOT NULL DEFAULT FALSE,
    customer_billing_delivery_recorded  BOOLEAN NOT NULL DEFAULT FALSE,
    review_payload                      JSONB NOT NULL DEFAULT '{}'::jsonb,
    data                                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT pm_customer_delivery_proof_reviews_proof_gate CHECK (
        delivery_proof_recorded = FALSE
        OR (
            length(trim(delivery_proof_type)) > 0
            AND length(trim(delivery_proof_ref)) > 0
            AND proof_recorded_at_utc IS NOT NULL
        )
    ),
    CONSTRAINT pm_customer_delivery_proof_reviews_review_payload_object CHECK (
        jsonb_typeof(review_payload) = 'object'
    ),
    CONSTRAINT pm_customer_delivery_proof_reviews_data_object CHECK (
        jsonb_typeof(data) = 'object'
    )
);

CREATE OR REPLACE FUNCTION seam.reject_pm_customer_delivery_proof_review_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'pm_customer_delivery_proof_reviews is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS pm_customer_delivery_proof_reviews_reject_update
ON seam.pm_customer_delivery_proof_reviews;

CREATE TRIGGER pm_customer_delivery_proof_reviews_reject_update
BEFORE UPDATE ON seam.pm_customer_delivery_proof_reviews
FOR EACH ROW
EXECUTE FUNCTION seam.reject_pm_customer_delivery_proof_review_mutation();

DROP TRIGGER IF EXISTS pm_customer_delivery_proof_reviews_reject_delete
ON seam.pm_customer_delivery_proof_reviews;

CREATE TRIGGER pm_customer_delivery_proof_reviews_reject_delete
BEFORE DELETE ON seam.pm_customer_delivery_proof_reviews
FOR EACH ROW
EXECUTE FUNCTION seam.reject_pm_customer_delivery_proof_review_mutation();

ALTER TABLE seam.pm_customer_delivery_proof_reviews ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE seam.pm_customer_delivery_proof_reviews FROM anon;
REVOKE ALL ON TABLE seam.pm_customer_delivery_proof_reviews FROM authenticated;