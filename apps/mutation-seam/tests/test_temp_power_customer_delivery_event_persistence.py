import base64
import json
from pathlib import Path

from app.db.memory_store import store
from app.temp_power_customer_delivery_event_persistence import (
    REQUIRED_CUSTOMER_DELIVERY_STATUS,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ACTION_TYPE,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
    build_temp_power_customer_delivery_event_id,
    classify_temp_power_customer_delivery_event_record,
    load_temp_power_customer_delivery_event_status,
)
from app.temp_power_customer_delivery_proof_review_persistence import TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ACTION_TYPE
from app.temp_power_customer_delivery_proof_review_persistence import build_temp_power_customer_delivery_proof_review_id
from app.temp_power_customer_preview_review_persistence import build_temp_power_customer_preview_review_id


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "011_pm_lane_347_customer_delivery_events.sql"


def _token(actor_role: str = "pm", project_scope: list[str] | None = None) -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": project_scope or [TEMP_POWER_PROJECT_ID],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _seed_temp_power_scope() -> None:
    store.projects[TEMP_POWER_PROJECT_ID] = {
        "id": TEMP_POWER_PROJECT_ID,
        "name": "Project Miner Temp Power",
    }
    store.tasks["pm-import-project-miner-temp-power-task-0001"] = {
        "id": "pm-import-project-miner-temp-power-task-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "workpackage_id": "pm-import-project-miner-temp-power-wp-001",
        "status": "ready",
    }
    store.apparatus["pm-import-project-miner-temp-power-app-0001"] = {
        "id": "pm-import-project-miner-temp-power-app-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "task_id": "pm-import-project-miner-temp-power-task-0001",
        "status": "ready",
    }
    store.workpackages["pm-import-project-miner-temp-power-wp-001"] = {
        "id": "pm-import-project-miner-temp-power-wp-001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "status": "not_started",
    }


def _seed_customer_preview_review() -> str:
    preview_payload = {
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "customer_preview_id": "pm-import-project-miner-temp-power-preview-0001",
        "coverage_scope_task_ids": ["pm-import-project-miner-temp-power-task-0001"],
        "coverage_scope_apparatus_ids": ["pm-import-project-miner-temp-power-app-0001"],
        "idempotency_key": "pm-lane-315-customer-preview-review:pm-import-project-miner-temp-power:preview-0001",
    }
    review_id = build_temp_power_customer_preview_review_id(preview_payload)
    store.temp_power_customer_preview_reviews = {
        review_id: {
            "review_id": review_id,
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "customer_preview_id": "pm-import-project-miner-temp-power-preview-0001",
            "preview_artifact_refs": ["preview://temp-power/2026-05-18/review-bundle-0001"],
            "pm_reviewed_at": "2026-05-18T23:30:00Z",
        }
    }
    return review_id


def _delivery_proof_payload(customer_preview_review_id: str, **overrides) -> dict:
    payload = {
        "idempotency_key": "pm-lane-329-customer-delivery-proof-review:pm-import-project-miner-temp-power:delivery-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "customer_preview_review_id": customer_preview_review_id,
        "customer_delivery_event_id": "temp-power-delivery-event-0001",
        "preview_artifact_lineage": ["preview://temp-power/2026-05-18/review-bundle-0001"],
        "named_recipient_name": "Jordan Buyer",
        "named_recipient_role": "Operations Manager",
        "delivery_channel": "CONTROLLED_EMAIL",
        "delivery_artifact_refs": ["delivery://temp-power/2026-05-18/email-package-0001"],
        "delivered_at_utc": "2026-05-18T23:45:00Z",
        "delivery_proof_type": "EMAIL_RECEIPT",
        "delivery_proof_ref": "receipt://temp-power/2026-05-18/email-receipt-0001",
        "delivery_proof_recorded": True,
        "pm_delivery_approval_status": "DELIVERY_PROOF_REVIEW_ACCEPTED",
        "pm_delivery_approval_note": "PM accepted customer delivery and durable proof review storage only; finance and source writeback remain blocked.",
        "delivery_note": "Customer delivery review captured for the hosted-green preview lineage only.",
    }
    payload.update(overrides)
    return payload


def _delivery_proof_request(payload: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ACTION_TYPE,
        "entity_id": build_temp_power_customer_delivery_proof_review_id(payload),
        "payload": payload,
        "reason": "Persist admitted Temp Power customer delivery/proof review only; finance, source writeback, and customer billing delivery remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T23:46:00Z",
    }
    request.update(overrides)
    return request


def _seed_customer_delivery_proof_review(client, customer_preview_review_id: str) -> str:
    response = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-proof-reviews",
        json=_delivery_proof_request(_delivery_proof_payload(customer_preview_review_id)),
        headers=_token(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    return data["entity_id"]


def _payload(customer_preview_review_id: str, customer_delivery_proof_review_id: str, **overrides) -> dict:
    payload = {
        "idempotency_key": "pm-lane-347-customer-delivery-event:pm-import-project-miner-temp-power:event-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "customer_preview_review_id": customer_preview_review_id,
        "customer_delivery_proof_review_id": customer_delivery_proof_review_id,
        "customer_delivery_event_id": "temp-power-delivery-event-0001",
        "named_recipient_name": "Jordan Buyer",
        "named_recipient_role": "Operations Manager",
        "delivery_channel": "CONTROLLED_EMAIL",
        "delivery_artifact_refs": ["delivery://temp-power/2026-05-18/email-package-0001"],
        "delivered_at_utc": "2026-05-18T23:45:00Z",
        "execution_method": "CONTROLLED_EMAIL_OPERATOR_SEND",
        "delivery_proof_type": "EMAIL_RECEIPT",
        "delivery_proof_ref": "receipt://temp-power/2026-05-18/email-receipt-0001",
        "customer_delivery_status": REQUIRED_CUSTOMER_DELIVERY_STATUS,
        "execution_note": "PM executed the admitted customer-facing delivery event only; downstream finance and writeback remain blocked.",
        "proof_recorded_at_utc": "2026-05-18T23:45:00Z",
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ACTION_TYPE,
        "entity_id": build_temp_power_customer_delivery_event_id(payload),
        "payload": payload,
        "reason": "Persist admitted Temp Power customer-facing delivery execution event only; finance, source writeback, and customer billing delivery remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T23:47:00Z",
    }
    request.update(overrides)
    return request


def test_temp_power_customer_delivery_event_route_persists_one_insert_only_event_and_readback(client):
    _seed_temp_power_scope()
    preview_review_id = _seed_customer_preview_review()
    delivery_proof_review_id = _seed_customer_delivery_proof_review(client, preview_review_id)

    missing = load_temp_power_customer_delivery_event_status()
    assert missing["status"] == "no_customer_delivery_event_record"
    assert missing["storage_route_registered"] is True

    response = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id)),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "pm_customer_delivery_event"
    assert data["action_type"] == TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ACTION_TYPE
    assert data["entity_id"] == "temp-power-delivery-event-0001"
    assert data["new_state"]["execution_storage_status"] == "accepted_for_customer_delivery_event_storage"
    assert data["new_state"]["customer_delivery_status"] == REQUIRED_CUSTOMER_DELIVERY_STATUS
    assert data["new_state"]["delivery_channel"] == "CONTROLLED_EMAIL"
    assert data["new_state"]["execution_method"] == "CONTROLLED_EMAIL_OPERATOR_SEND"
    assert data["new_state"]["finance_export_recorded"] is False
    assert data["new_state"]["source_writeback_recorded"] is False
    assert data["new_state"]["customer_billing_delivery_recorded"] is False
    assert data["new_state"]["mutation_id"] == data["mutation_id"]
    assert data["new_state"]["audit_event_id"] == data["audit_event_id"]
    assert data["entity_id"] in store.temp_power_customer_delivery_events
    assert len(store.temp_power_customer_delivery_events) == 1
    assert len(store.audit_log) == 2

    status = client.get("/api/v1/reads/temp-power-customer-delivery-event-status", headers=_token()).json()
    assert status["status"] == "customer_delivery_event_recorded_current_match"
    assert status["latest_customer_delivery_event_id"] == data["entity_id"]
    assert status["record_count"] == 1
    assert status["customer_preview_review_id"] == preview_review_id
    assert status["customer_delivery_proof_review_id"] == delivery_proof_review_id
    assert status["current_candidate_match"] is True
    assert status["current_source_fingerprint_match"] is True
    assert status["preview_review_lineage_match"] is True
    assert status["delivery_proof_review_lineage_match"] is True
    assert status["latest_delivery_proof_type"] == "EMAIL_RECEIPT"
    assert status["latest_delivery_proof_ref"] == "receipt://temp-power/2026-05-18/email-receipt-0001"
    assert status["finance_authority"] == "not_admitted"
    assert status["source_writeback_authority"] == "not_admitted"
    assert status["customer_billing_delivery_authority"] == "not_admitted"


def test_temp_power_customer_delivery_event_route_replays_identical_payload_without_second_insert(client):
    _seed_temp_power_scope()
    preview_review_id = _seed_customer_preview_review()
    delivery_proof_review_id = _seed_customer_delivery_proof_review(client, preview_review_id)
    request = _request(_payload(preview_review_id, delivery_proof_review_id))

    first = client.post("/api/v1/mutations/temp-power-customer-delivery-events", json=request, headers=_token())
    second = client.post("/api/v1/mutations/temp-power-customer-delivery-events", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["entity_id"] == first.json()["entity_id"]
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.temp_power_customer_delivery_events) == 1


def test_temp_power_customer_delivery_event_readback_classifies_stale_and_lineage_mismatch_records(client):
    _seed_temp_power_scope()
    preview_review_id = _seed_customer_preview_review()
    delivery_proof_review_id = _seed_customer_delivery_proof_review(client, preview_review_id)
    response = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id)),
        headers=_token(),
    )
    accepted = response.json()

    stale_record = dict(store.temp_power_customer_delivery_events[accepted["entity_id"]])
    stale_record["source_fingerprint"] = "stale-source-fingerprint"
    stale = classify_temp_power_customer_delivery_event_record(stale_record)
    assert stale["status"] == "customer_delivery_event_recorded_stale_source"

    preview_mismatch_record = dict(store.temp_power_customer_delivery_events[accepted["entity_id"]])
    preview_mismatch_record["customer_preview_review_id"] = "missing-preview-review"
    preview_mismatch = classify_temp_power_customer_delivery_event_record(preview_mismatch_record)
    assert preview_mismatch["status"] == "customer_delivery_event_preview_review_lineage_mismatch"

    proof_mismatch_record = dict(store.temp_power_customer_delivery_events[accepted["entity_id"]])
    proof_mismatch_record["customer_delivery_proof_review_id"] = "missing-proof-review"
    proof_mismatch = classify_temp_power_customer_delivery_event_record(proof_mismatch_record)
    assert proof_mismatch["status"] == "customer_delivery_event_delivery_proof_review_lineage_mismatch"


def test_temp_power_customer_delivery_event_route_rejects_blocked_fields_invalid_context_and_lineage(client):
    _seed_temp_power_scope()
    preview_review_id = _seed_customer_preview_review()
    delivery_proof_review_id = _seed_customer_delivery_proof_review(client, preview_review_id)

    blocked = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id, finance_export_recorded=True)),
        headers=_token(),
    )
    wrong_role = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id)),
        headers=_token(actor_role="lead"),
    )
    wrong_scope = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id)),
        headers=_token(project_scope=["another-project"]),
    )
    stale_source = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id, source_fingerprint="stale-source-fingerprint")),
        headers=_token(),
    )
    wrong_event_id = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id, customer_delivery_event_id="temp-power-delivery-event-9999")),
        headers=_token(),
    )
    wrong_method = client.post(
        "/api/v1/mutations/temp-power-customer-delivery-events",
        json=_request(_payload(preview_review_id, delivery_proof_review_id, execution_method="LATER_APPROVED_PORTAL_OPERATOR_RELEASE")),
        headers=_token(),
    )

    assert blocked.json()["status"] == "rejected"
    assert blocked.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert wrong_role.json()["status"] == "rejected"
    assert wrong_role.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert wrong_scope.json()["status"] == "rejected"
    assert wrong_scope.json()["error"]["code"] == "UNAUTHORIZED_SCOPE"
    assert stale_source.json()["status"] == "rejected"
    assert stale_source.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert wrong_event_id.json()["status"] == "rejected"
    assert wrong_event_id.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert wrong_method.json()["status"] == "rejected"
    assert wrong_method.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert not hasattr(store, "temp_power_customer_delivery_events") or len(store.temp_power_customer_delivery_events) == 0


def test_temp_power_customer_delivery_event_status_read_classifies_storage_unavailable(monkeypatch):
    class BrokenCustomerDeliveryEventStore:
        def values(self):
            raise RuntimeError("customer delivery event table missing")

    monkeypatch.setattr(store, "temp_power_customer_delivery_events", BrokenCustomerDeliveryEventStore())

    status = load_temp_power_customer_delivery_event_status()

    assert status["status"] == "customer_delivery_event_storage_unavailable"
    assert status["storage_available"] is False
    assert status["storage_route_registered"] is True
    assert status["finance_authority"] == "not_admitted"
    assert status["source_writeback_authority"] == "not_admitted"
    assert status["customer_billing_delivery_authority"] == "not_admitted"
    assert status["error_type"] == "RuntimeError"


def test_temp_power_customer_delivery_event_migration_preserves_insert_only_boundary():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS seam.pm_customer_delivery_events" in sql
    assert "customer_delivery_event_id          TEXT PRIMARY KEY" in sql
    assert "execution_method                    TEXT NOT NULL" in sql
    assert "customer_delivery_status            TEXT NOT NULL CHECK (customer_delivery_status = 'DELIVERED_AND_PROOF_ATTACHED')" in sql
    assert "proof_recorded_at_utc               TIMESTAMPTZ NOT NULL" in sql
    assert "FUNCTION seam.reject_pm_customer_delivery_event_mutation()" in sql
    assert "BEFORE UPDATE ON seam.pm_customer_delivery_events" in sql
    assert "BEFORE DELETE ON seam.pm_customer_delivery_events" in sql
    assert "ALTER TABLE seam.pm_customer_delivery_events ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON TABLE seam.pm_customer_delivery_events FROM anon" in sql
    assert "REVOKE ALL ON TABLE seam.pm_customer_delivery_events FROM authenticated" in sql