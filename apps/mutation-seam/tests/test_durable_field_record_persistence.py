import base64
import json

from app.db.memory_store import store
from app.durable_field_record_persistence import (
    LANE_279_FIELD_AUTH_RECORD_ID,
    LANE_280_STATUS_RECORD_ID,
    LANE_281_FIELD_RECORD_ID,
    LANE_281_IDEMPOTENCY_KEY,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
    load_durable_field_record_status,
)


def _token(actor_role: str = "lead", project_scope: list[str] | None = None) -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": project_scope or [TEMP_POWER_PROJECT_ID],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _seed_temp_power_ready_rows() -> None:
    store.projects[TEMP_POWER_PROJECT_ID] = {
        "id": TEMP_POWER_PROJECT_ID,
        "name": "Project Miner Temp Power",
    }
    for index in range(1, 8):
        store.workpackages[f"pm-import-project-miner-temp-power-wp-{index:03d}"] = {
            "id": f"pm-import-project-miner-temp-power-wp-{index:03d}",
            "project_id": TEMP_POWER_PROJECT_ID,
            "status": "not_started",
        }
    for index in range(1, 16):
        store.tasks[f"pm-import-project-miner-temp-power-task-{index:04d}"] = {
            "id": f"pm-import-project-miner-temp-power-task-{index:04d}",
            "project_id": TEMP_POWER_PROJECT_ID,
            "workpackage_id": f"pm-import-project-miner-temp-power-wp-{min(7, ((index - 1) // 3) + 1):03d}",
            "status": "ready",
        }
    for index in range(1, 185):
        task_index = min(15, ((index - 1) // 13) + 1)
        app_id = f"pm-import-project-miner-temp-power-app-{index:04d}"
        task_id = f"pm-import-project-miner-temp-power-task-{task_index:04d}"
        store.apparatus[app_id] = {
            "id": app_id,
            "project_id": TEMP_POWER_PROJECT_ID,
            "task_id": task_id,
            "status": "ready",
        }
        store.assignments[f"assignment-{index:04d}"] = {
            "id": f"assignment-{index:04d}",
            "project_id": TEMP_POWER_PROJECT_ID,
            "task_id": task_id,
            "apparatus_id": app_id,
            "assigned_to": f"tech-{((index - 1) % 3) + 1:03d}",
            "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        }


def _payload(**overrides):
    payload = {
        "field_record_id": LANE_281_FIELD_RECORD_ID,
        "idempotency_key": LANE_281_IDEMPOTENCY_KEY,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "field_record_kind": "field_start_readiness",
        "record_status": "recorded",
        "record_scope": "daily_readiness_no_production_quantities",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "workpackage_count": 7,
        "task_ready_count": 15,
        "apparatus_ready_count": 184,
        "assignment_count": 184,
        "unique_assignment_apparatus_count": 184,
        "issue_count": 0,
        "daily_summary": "Field-start readiness captured for imported Temp Power work; no production quantities recorded.",
        "field_evidence_attachments": [],
        "production_quantity_count": 0,
        "field_evidence_authority": "not_admitted_attachment_write",
        "production_tracking_authority": "not_admitted",
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "readiness_evidence": {
            "task_ready_count": 15,
            "apparatus_ready_count": 184,
            "assignment_count": 184,
        },
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides):
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "B",
        "action_type": "create_daily_field_record",
        "entity_id": payload["field_record_id"],
        "payload": payload,
        "reason": "Persist PM Lane 281 field-start readiness record only; production, customer, and finance remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T03:30:00Z",
    }
    request.update(overrides)
    return request


def test_durable_field_record_route_persists_one_bounded_record_and_readback(client):
    _seed_temp_power_ready_rows()
    before_status = load_durable_field_record_status()
    assert before_status["classification"] == "no_durable_field_record"

    response = client.post(
        "/api/v1/mutations/durable-field-records",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "durable_field_record"
    assert data["action_type"] == "create_daily_field_record"
    assert data["entity_id"] == LANE_281_FIELD_RECORD_ID
    assert data["new_state"]["production_tracking_authority"] == "not_admitted"
    assert data["new_state"]["customer_reporting_authority"] == "not_admitted"
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["field_evidence_attachments"] == []
    assert data["new_state"]["production_quantity_count"] == 0
    assert len(store.durable_field_records) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "durable_field_record"

    status = client.get("/api/v1/reads/durable-field-record-status", headers=_token()).json()
    assert status["classification"] == "durable_field_recorded"
    assert status["field_record_id"] == LANE_281_FIELD_RECORD_ID
    assert status["production_tracking_authority"] == "not_admitted"
    assert status["preconditions"]["counts"]["task_ready_count"] == 15
    assert status["preconditions"]["counts"]["apparatus_ready_count"] == 184


def test_durable_field_record_route_replays_identical_payload_without_second_insert(client):
    _seed_temp_power_ready_rows()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/durable-field-records", json=request, headers=_token())
    second = client.post("/api/v1/mutations/durable-field-records", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.durable_field_records) == 1
    assert len(store.audit_log) == 1


def test_durable_field_record_route_rejects_replay_mismatch(client):
    _seed_temp_power_ready_rows()
    first = client.post("/api/v1/mutations/durable-field-records", json=_request(_payload()), headers=_token())
    changed = _payload(daily_summary="Changed replay summary.")

    second = client.post("/api/v1/mutations/durable-field-records", json=_request(changed), headers=_token())

    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"
    assert len(store.durable_field_records) == 1


def test_durable_field_record_route_rejects_missing_schedule_status_readiness(client):
    _seed_temp_power_ready_rows()
    task = store.tasks["pm-import-project-miner-temp-power-task-0001"].copy()
    task["status"] = "not_started"
    store.tasks[task["id"]] = task

    response = client.post(
        "/api/v1/mutations/durable-field-records",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"
    assert len(store.durable_field_records) == 0


def test_durable_field_record_route_rejects_downstream_authority_widening(client):
    _seed_temp_power_ready_rows()

    response = client.post(
        "/api/v1/mutations/durable-field-records",
        json=_request(_payload(production_tracking_authority="admitted")),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"
    assert len(store.durable_field_records) == 0
