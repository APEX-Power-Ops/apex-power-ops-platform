import base64
import json

from app.db.memory_store import store
from app.durable_field_record_persistence import (
    LANE_279_FIELD_AUTH_RECORD_ID,
    LANE_280_STATUS_RECORD_ID,
    LANE_281_FIELD_RECORD_ID,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
)
from app.production_tracking_persistence import (
    LANE_282_IDEMPOTENCY_KEY,
    LANE_282_PRODUCTION_TRACKING_RECORD_ID,
    PRODUCTION_TRACKING_AUTHORITY,
    load_production_tracking_status,
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


def _seed_durable_field_record() -> None:
    store.durable_field_records[LANE_281_FIELD_RECORD_ID] = {
        "id": LANE_281_FIELD_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "field_record_kind": "field_start_readiness",
        "record_status": "recorded",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "production_tracking_authority": "not_admitted",
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "production_quantity_count": 0,
    }


def _seed_preconditions() -> None:
    _seed_temp_power_ready_rows()
    _seed_durable_field_record()


def _payload(**overrides):
    payload = {
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "idempotency_key": LANE_282_IDEMPOTENCY_KEY,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "tracking_kind": "field_start_zero_actual_baseline",
        "record_status": "recorded",
        "record_scope": "production_tracking_baseline_no_customer_or_finance",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "workpackage_count": 7,
        "task_ready_count": 15,
        "apparatus_ready_count": 184,
        "assignment_count": 184,
        "unique_assignment_apparatus_count": 184,
        "issue_count": 0,
        "durable_field_record_count": 1,
        "production_quantities": [],
        "production_quantity_count": 0,
        "labor_entries": [],
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress": [],
        "apparatus_progress_count": 0,
        "progress_updates": [],
        "progress_update_count": 0,
        "daily_summary": "Production tracking baseline recorded with zero actual quantities, labor, and progress updates.",
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "production_evidence": {
            "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
            "zero_actual_baseline": True,
        },
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides):
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "B",
        "action_type": "create_daily_production_baseline",
        "entity_id": payload["production_tracking_record_id"],
        "payload": payload,
        "reason": "Persist PM Lane 282 production tracking zero-actual baseline; customer and finance remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T04:15:00Z",
    }
    request.update(overrides)
    return request


def test_production_tracking_route_persists_zero_actual_baseline_and_readback(client):
    _seed_preconditions()
    before_status = load_production_tracking_status()
    assert before_status["classification"] == "no_production_tracking_record"

    response = client.post(
        "/api/v1/mutations/production-tracking",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "production_tracking_record"
    assert data["action_type"] == "create_daily_production_baseline"
    assert data["entity_id"] == LANE_282_PRODUCTION_TRACKING_RECORD_ID
    assert data["new_state"]["production_tracking_authority"] == PRODUCTION_TRACKING_AUTHORITY
    assert data["new_state"]["customer_reporting_authority"] == "not_admitted"
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["production_quantities"] == []
    assert data["new_state"]["production_quantity_count"] == 0
    assert data["new_state"]["labor_entries"] == []
    assert data["new_state"]["labor_entry_count"] == 0
    assert data["new_state"]["actual_labor_hours"] == 0.0
    assert len(store.production_tracking_records) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "production_tracking_record"

    status = client.get("/api/v1/reads/production-tracking-status", headers=_token()).json()
    assert status["classification"] == "production_tracking_baseline_recorded"
    assert status["production_tracking_record_id"] == LANE_282_PRODUCTION_TRACKING_RECORD_ID
    assert status["production_tracking_authority"] == PRODUCTION_TRACKING_AUTHORITY
    assert status["customer_reporting_authority"] == "not_admitted"
    assert status["finance_authority"] == "not_admitted"
    assert status["preconditions"]["counts"]["durable_field_record_count"] == 1


def test_production_tracking_route_replays_identical_payload_without_second_insert(client):
    _seed_preconditions()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/production-tracking", json=request, headers=_token())
    second = client.post("/api/v1/mutations/production-tracking", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.production_tracking_records) == 1
    assert len(store.audit_log) == 1


def test_production_tracking_route_rejects_replay_mismatch(client):
    _seed_preconditions()
    first = client.post("/api/v1/mutations/production-tracking", json=_request(_payload()), headers=_token())
    changed = _payload(daily_summary="Changed replay summary.")

    second = client.post("/api/v1/mutations/production-tracking", json=_request(changed), headers=_token())

    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"
    assert len(store.production_tracking_records) == 1


def test_production_tracking_route_rejects_missing_durable_field_record(client):
    _seed_temp_power_ready_rows()

    response = client.post(
        "/api/v1/mutations/production-tracking",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"
    assert len(store.production_tracking_records) == 0


def test_production_tracking_route_rejects_actual_quantity_or_downstream_widening(client):
    _seed_preconditions()

    quantity_response = client.post(
        "/api/v1/mutations/production-tracking",
        json=_request(_payload(production_quantity_count=1, production_quantities=[{"quantity": 1}])),
        headers=_token(),
    )
    finance_response = client.post(
        "/api/v1/mutations/production-tracking",
        json=_request(_payload(finance_authority="admitted")),
        headers=_token(),
    )

    assert quantity_response.status_code == 200
    assert quantity_response.json()["status"] == "rejected"
    assert quantity_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert finance_response.status_code == 200
    assert finance_response.json()["status"] == "rejected"
    assert finance_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert len(store.production_tracking_records) == 0


def test_production_tracking_route_requires_lead_role(client):
    _seed_preconditions()

    response = client.post(
        "/api/v1/mutations/production-tracking",
        json=_request(_payload()),
        headers=_token(actor_role="pm"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert len(store.production_tracking_records) == 0
