CREATE TABLE IF NOT EXISTS seam.pm_customer_delivery_events (
    customer_delivery_event_id          TEXT PRIMARY KEY,
    mutation_id                         TEXT NOT NULL,
    audit_event_id                      TEXT NOT NULL,
    project_id                          TEXT NOT NULL,
    candidate_id                        TEXT NOT NULL,
    source_fingerprint                  TEXT NOT NULL,
    customer_preview_review_id          TEXT NOT NULL,
    customer_delivery_proof_review_id   TEXT NOT NULL,
    named_recipient_name                TEXT NOT NULL,
    named_recipient_role                TEXT NOT NULL,
    delivery_channel                    TEXT NOT NULL CHECK (delivery_channel IN ('CONTROLLED_EMAIL', 'LATER_APPROVED_PORTAL')),
    delivery_artifact_refs_json         JSONB NOT NULL DEFAULT '[]'::jsonb,
    delivered_at_utc                    TIMESTAMPTZ NOT NULL,
    execution_method                    TEXT NOT NULL CHECK (execution_method IN ('CONTROLLED_EMAIL_OPERATOR_SEND', 'LATER_APPROVED_PORTAL_OPERATOR_RELEASE')),
    delivery_proof_type                 TEXT NOT NULL,
    delivery_proof_ref                  TEXT NOT NULL,
    customer_delivery_status            TEXT NOT NULL CHECK (customer_delivery_status = 'DELIVERED_AND_PROOF_ATTACHED'),
    execution_note                      TEXT NOT NULL,
    proof_recorded_at_utc               TIMESTAMPTZ NOT NULL,
    pm_actor                            TEXT NOT NULL,
    pm_timestamp                        TIMESTAMPTZ NOT NULL,
    idempotency_key                     TEXT NOT NULL UNIQUE,
    mutation_class                      TEXT NOT NULL DEFAULT 'C',
    source_route                        TEXT NOT NULL DEFAULT '/api/v1/mutations/temp-power-customer-delivery-events',
    finance_export_recorded             BOOLEAN NOT NULL DEFAULT FALSE,
    source_writeback_recorded           BOOLEAN NOT NULL DEFAULT FALSE,
    customer_billing_delivery_recorded  BOOLEAN NOT NULL DEFAULT FALSE,
    execution_payload                   JSONB NOT NULL DEFAULT '{}'::jsonb,
    data                                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    CONSTRAINT pm_customer_delivery_events_execution_payload_object CHECK (
        jsonb_typeof(execution_payload) = 'object'
    ),
    CONSTRAINT pm_customer_delivery_events_data_object CHECK (
        jsonb_typeof(data) = 'object'
    )
);

CREATE OR REPLACE FUNCTION seam.reject_pm_customer_delivery_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'pm_customer_delivery_events is insert-only';
END;
$$;

DROP TRIGGER IF EXISTS pm_customer_delivery_events_reject_update
ON seam.pm_customer_delivery_events;

CREATE TRIGGER pm_customer_delivery_events_reject_update
BEFORE UPDATE ON seam.pm_customer_delivery_events
FOR EACH ROW
EXECUTE FUNCTION seam.reject_pm_customer_delivery_event_mutation();

DROP TRIGGER IF EXISTS pm_customer_delivery_events_reject_delete
ON seam.pm_customer_delivery_events;

CREATE TRIGGER pm_customer_delivery_events_reject_delete
BEFORE DELETE ON seam.pm_customer_delivery_events
FOR EACH ROW
EXECUTE FUNCTION seam.reject_pm_customer_delivery_event_mutation();

ALTER TABLE seam.pm_customer_delivery_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE seam.pm_customer_delivery_events FROM anon;
REVOKE ALL ON TABLE seam.pm_customer_delivery_events FROM authenticated;