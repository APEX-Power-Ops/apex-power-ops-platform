import base64
import json
from pathlib import Path

from app.db.memory_store import store
from app.temp_power_customer_preview_review_persistence import (
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ACTION_TYPE,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
    build_temp_power_customer_preview_review_id,
    classify_temp_power_customer_preview_review_record,
    load_temp_power_customer_preview_review_status,
)


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "009_pm_lane_315_customer_preview_reviews.sql"


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


def _payload(**overrides) -> dict:
    payload = {
        "idempotency_key": "pm-lane-315-customer-preview-review:pm-import-project-miner-temp-power:preview-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "customer_preview_id": "pm-import-project-miner-temp-power-preview-0001",
        "coverage_scope_task_ids": ["pm-import-project-miner-temp-power-task-0001"],
        "coverage_scope_apparatus_ids": ["pm-import-project-miner-temp-power-app-0001"],
        "preview_summary": "Preview-only customer review bundle for one Temp Power apparatus; no delivery or finance output admitted.",
        "preview_artifact_refs": ["preview://temp-power/2026-05-18/review-bundle-0001"],
        "named_recipient_name": "Jordan Buyer",
        "named_recipient_role": "Operations Manager",
        "delivery_channel": "CONTROLLED_EMAIL",
        "future_delivery_proof_requirements": ["EMAIL_RECEIPT", "SIGNED_TRANSMITTAL"],
        "durable_delivery_event": False,
        "delivery_proof_recorded": False,
        "delivery_block_reason": "DELIVERY_REQUIRES_SEPARATE_ADMISSION",
        "pm_review_status": "REVIEW_ONLY_READY_FOR_PM_REVIEW",
        "pm_review_note": "PM accepted preview review storage only; no customer delivery, finance, or source writeback admitted.",
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ACTION_TYPE,
        "entity_id": build_temp_power_customer_preview_review_id(payload),
        "payload": payload,
        "reason": "Persist admitted Temp Power customer preview review only; delivery, finance, and source writeback remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T23:30:00Z",
    }
    request.update(overrides)
    return request


def _domain_counts() -> dict[str, int]:
    return {
        "projects": len(store.projects),
        "workpackages": len(store.workpackages),
        "tasks": len(store.tasks),
        "apparatus": len(store.apparatus),
        "assignments": len(store.assignments),
        "hours": len(store.hours),
        "issues": len(store.issues),
    }


def test_temp_power_customer_preview_review_route_persists_one_insert_only_review_and_readback(client):
    _seed_temp_power_scope()
    before_counts = _domain_counts()

    missing = load_temp_power_customer_preview_review_status()
    assert missing["status"] == "no_customer_preview_review_record"
    assert missing["storage_route_registered"] is True

    response = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "pm_temp_power_customer_preview_review"
    assert data["action_type"] == TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ACTION_TYPE
    assert data["new_state"]["pm_actor"] == "pm-001"
    assert data["new_state"]["review_storage_status"] == "accepted_for_review_storage"
    assert data["new_state"]["customer_delivery_authority"] == "not_admitted"
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["source_writeback_authority"] == "not_admitted"
    assert data["new_state"]["durable_delivery_event"] is False
    assert data["new_state"]["delivery_proof_recorded"] is False
    assert data["new_state"]["mutation_id"] == data["mutation_id"]
    assert data["new_state"]["audit_event_id"] == data["audit_event_id"]
    assert data["entity_id"] in store.temp_power_customer_preview_reviews
    assert len(store.temp_power_customer_preview_reviews) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "pm_temp_power_customer_preview_review"
    assert _domain_counts() == before_counts

    status = client.get("/api/v1/reads/temp-power-customer-preview-status", headers=_token()).json()
    assert status["status"] == "customer_preview_delivery_blocked"
    assert status["latest_customer_preview_review_id"] == data["entity_id"]
    assert status["record_count"] == 1
    assert status["current_candidate_match"] is True
    assert status["current_source_fingerprint_match"] is True
    assert status["preview_artifact_count"] == 1
    assert status["storage_source"] == "seam.pm_customer_preview_reviews"
    assert status["durable_delivery_event"] is False
    assert status["delivery_proof_recorded"] is False


def test_temp_power_customer_preview_review_route_replays_identical_payload_without_second_insert(client):
    _seed_temp_power_scope()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/temp-power-customer-preview-reviews", json=request, headers=_token())
    second = client.post("/api/v1/mutations/temp-power-customer-preview-reviews", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["entity_id"] == first.json()["entity_id"]
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.temp_power_customer_preview_reviews) == 1
    assert len(store.audit_log) == 1


def test_temp_power_customer_preview_review_readback_classifies_stale_and_followup_records_without_audit_dependency(client):
    _seed_temp_power_scope()
    response = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload()),
        headers=_token(),
    )
    accepted = response.json()

    stale_record = dict(store.temp_power_customer_preview_reviews[accepted["entity_id"]])
    stale_record["source_fingerprint"] = "stale-source-fingerprint"
    stale = classify_temp_power_customer_preview_review_record(stale_record)
    assert stale["status"] == "customer_preview_review_recorded_stale_source"
    assert stale["current_candidate_match"] is True
    assert stale["current_source_fingerprint_match"] is False

    followup_record = dict(store.temp_power_customer_preview_reviews[accepted["entity_id"]])
    followup_record["pm_review_status"] = "PENDING_PM_FOLLOWUP"
    followup_record["delivery_block_reason"] = ""
    followup = classify_temp_power_customer_preview_review_record(followup_record)
    assert followup["status"] == "customer_preview_pending_pm_followup"


def test_temp_power_customer_preview_review_route_rejects_blocked_fields_and_invalid_request_context(client):
    _seed_temp_power_scope()

    blocked = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload(finance_authority="admitted")),
        headers=_token(),
    )
    wrong_role = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload()),
        headers=_token(actor_role="lead"),
    )
    wrong_scope = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload()),
        headers=_token(project_scope=["another-project"]),
    )
    stale_source = client.post(
        "/api/v1/mutations/temp-power-customer-preview-reviews",
        json=_request(_payload(source_fingerprint="stale-source-fingerprint")),
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
    assert not hasattr(store, "temp_power_customer_preview_reviews") or len(store.temp_power_customer_preview_reviews) == 0


def test_temp_power_customer_preview_review_status_read_classifies_storage_unavailable(monkeypatch):
    class BrokenCustomerPreviewReviewStore:
        def values(self):
            raise RuntimeError("customer preview review table missing")

    monkeypatch.setattr(store, "temp_power_customer_preview_reviews", BrokenCustomerPreviewReviewStore())

    status = load_temp_power_customer_preview_review_status()

    assert status["status"] == "customer_preview_review_storage_unavailable"
    assert status["storage_available"] is False
    assert status["storage_route_registered"] is False
    assert status["error_type"] == "RuntimeError"


def test_temp_power_customer_preview_review_migration_preserves_insert_only_boundary():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS seam.pm_customer_preview_reviews" in sql
    assert "review_id                    TEXT PRIMARY KEY" in sql
    assert "mutation_id                  TEXT NOT NULL" in sql
    assert "audit_event_id               TEXT NOT NULL" in sql
    assert "customer_delivery_authority  TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "finance_authority            TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "source_writeback_authority   TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "durable_delivery_event       BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "delivery_proof_recorded      BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "FUNCTION seam.reject_pm_customer_preview_review_mutation()" in sql
    assert "BEFORE UPDATE ON seam.pm_customer_preview_reviews" in sql
    assert "BEFORE DELETE ON seam.pm_customer_preview_reviews" in sql
    assert "delivery_channel IN ('CONTROLLED_EMAIL', 'LATER_APPROVED_PORTAL')" in sql
    assert "ALTER TABLE seam.pm_customer_preview_reviews ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON TABLE seam.pm_customer_preview_reviews FROM anon" in sql
    assert "REVOKE ALL ON TABLE seam.pm_customer_preview_reviews FROM authenticated" in sql
    assert "CREATE TABLE IF NOT EXISTS seam.projects" not in sql