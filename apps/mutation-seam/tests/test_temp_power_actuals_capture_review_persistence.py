import base64
import json
from pathlib import Path

from app.db.memory_store import store
from app.temp_power_actuals_capture_review_persistence import (
    TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
    build_temp_power_actuals_capture_review_id,
    classify_temp_power_actuals_capture_review_record,
    load_temp_power_actuals_capture_review_status,
)


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "008_pm_lane_304_actuals_capture_reviews.sql"


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
        "idempotency_key": "pm-lane-304-actuals-review:pm-import-project-miner-temp-power:task-0001:app-0001:2026-05-18",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "task_id": "pm-import-project-miner-temp-power-task-0001",
        "apparatus_id": "pm-import-project-miner-temp-power-app-0001",
        "task_day_fallback_reason": None,
        "work_date": "2026-05-18",
        "recorder_role": "field_tech",
        "actual_labor_hours_preview": 6.5,
        "work_summary_note": "Preview actual labor for one Temp Power apparatus only; no customer or finance output admitted.",
        "primary_evidence_type": "field_ticket",
        "primary_evidence_ref": "ticket://temp-power/2026-05-18/app-0001",
        "supporting_evidence_refs": ["photo://temp-power/app-0001/2026-05-18"],
        "correction_mode": "ORIGINAL_REVIEW",
        "supersedes_review_id": None,
        "replacement_reason": None,
        "pm_review_status": "REVIEW_ONLY_READY_FOR_PM_REVIEW",
        "pm_review_note": "PM accepted bounded capture-review storage only; customer preview and downstream outputs remain blocked.",
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE,
        "entity_id": build_temp_power_actuals_capture_review_id(payload),
        "payload": payload,
        "reason": "Persist admitted Temp Power actuals-capture review only; customer delivery, finance, and source writeback remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T22:40:00Z",
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


def test_temp_power_actuals_capture_review_route_persists_one_insert_only_review_and_readback(client):
    _seed_temp_power_scope()
    before_counts = _domain_counts()

    missing = load_temp_power_actuals_capture_review_status()
    assert missing["status"] == "no_actuals_capture_review_record"
    assert missing["storage_route_registered"] is True

    response = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "pm_temp_power_actuals_capture_review"
    assert data["action_type"] == TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE
    assert data["new_state"]["pm_actor"] == "pm-001"
    assert data["new_state"]["customer_delivery_authority"] == "not_admitted"
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["source_writeback_authority"] == "not_admitted"
    assert data["new_state"]["durable_delivery_event"] is False
    assert data["new_state"]["mutation_id"] == data["mutation_id"]
    assert data["new_state"]["audit_event_id"] == data["audit_event_id"]
    assert data["entity_id"] in store.temp_power_actuals_capture_reviews
    assert len(store.temp_power_actuals_capture_reviews) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "pm_temp_power_actuals_capture_review"
    assert _domain_counts() == before_counts

    status = client.get("/api/v1/reads/temp-power-actuals-capture-review-status", headers=_token()).json()
    assert status["status"] == "actuals_capture_review_recorded_current_match"
    assert status["latest_review_id"] == data["entity_id"]
    assert status["record_count"] == 1
    assert status["current_candidate_match"] is True
    assert status["current_source_fingerprint_match"] is True
    assert status["supporting_evidence_count"] == 1
    assert status["storage_source"] == "seam.pm_actuals_capture_reviews"
    assert status["durable_delivery_event"] is False


def test_temp_power_actuals_capture_review_route_replays_identical_payload_without_second_insert(client):
    _seed_temp_power_scope()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/temp-power-actuals-capture-reviews", json=request, headers=_token())
    second = client.post("/api/v1/mutations/temp-power-actuals-capture-reviews", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["entity_id"] == first.json()["entity_id"]
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.temp_power_actuals_capture_reviews) == 1
    assert len(store.audit_log) == 1


def test_temp_power_actuals_capture_review_readback_classifies_stale_and_replacement_records_without_audit_dependency(client):
    _seed_temp_power_scope()
    response = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=_request(_payload()),
        headers=_token(),
    )
    accepted = response.json()

    stale_record = dict(store.temp_power_actuals_capture_reviews[accepted["entity_id"]])
    stale_record["source_fingerprint"] = "stale-source-fingerprint"
    stale = classify_temp_power_actuals_capture_review_record(stale_record)
    assert stale["status"] == "actuals_capture_review_recorded_stale_source"
    assert stale["current_candidate_match"] is True
    assert stale["current_source_fingerprint_match"] is False

    replacement_record = dict(store.temp_power_actuals_capture_reviews[accepted["entity_id"]])
    replacement_record["correction_mode"] = "VOID_AND_REPLACEMENT"
    replacement_record["supersedes_review_id"] = accepted["entity_id"]
    replacement = classify_temp_power_actuals_capture_review_record(replacement_record)
    assert replacement["status"] == "actuals_capture_review_replacement_chain_present"
    assert replacement["replacement_chain_present"] is True


def test_temp_power_actuals_capture_review_route_rejects_blocked_fields_and_invalid_request_context(client):
    _seed_temp_power_scope()

    blocked = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=_request(_payload(finance_authority="admitted")),
        headers=_token(),
    )
    wrong_role = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=_request(_payload()),
        headers=_token(actor_role="lead"),
    )
    wrong_scope = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=_request(_payload()),
        headers=_token(project_scope=["another-project"]),
    )
    stale_source = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
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
    assert not hasattr(store, "temp_power_actuals_capture_reviews") or len(store.temp_power_actuals_capture_reviews) == 0


def test_temp_power_actuals_capture_review_status_read_classifies_storage_unavailable(monkeypatch):
    class BrokenActualsCaptureReviewStore:
        def values(self):
            raise RuntimeError("actuals capture review table missing")

    monkeypatch.setattr(store, "temp_power_actuals_capture_reviews", BrokenActualsCaptureReviewStore())

    status = load_temp_power_actuals_capture_review_status()

    assert status["status"] == "actuals_capture_review_storage_unavailable"
    assert status["storage_available"] is False
    assert status["storage_route_registered"] is False
    assert status["error_type"] == "RuntimeError"


def test_temp_power_actuals_capture_review_migration_preserves_insert_only_boundary():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS seam.pm_actuals_capture_reviews" in sql
    assert "review_id                    TEXT PRIMARY KEY" in sql
    assert "mutation_id                  TEXT NOT NULL" in sql
    assert "audit_event_id               TEXT NOT NULL" in sql
    assert "customer_delivery_authority  TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "finance_authority            TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "source_writeback_authority   TEXT NOT NULL DEFAULT 'not_admitted'" in sql
    assert "durable_delivery_event       BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "FUNCTION seam.reject_pm_actuals_capture_review_mutation()" in sql
    assert "BEFORE UPDATE ON seam.pm_actuals_capture_reviews" in sql
    assert "BEFORE DELETE ON seam.pm_actuals_capture_reviews" in sql
    assert "correction_mode IN ('ORIGINAL_REVIEW', 'VOID_AND_REPLACEMENT')" in sql
    assert "ALTER TABLE seam.pm_actuals_capture_reviews ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON TABLE seam.pm_actuals_capture_reviews FROM anon" in sql
    assert "REVOKE ALL ON TABLE seam.pm_actuals_capture_reviews FROM authenticated" in sql
    assert "CREATE TABLE IF NOT EXISTS seam.projects" not in sql
    assert "CREATE TABLE IF NOT EXISTS seam.tasks" not in sql
    assert "CREATE TABLE IF NOT EXISTS seam.apparatus" not in sql