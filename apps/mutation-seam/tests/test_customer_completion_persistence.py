import base64
import json
from decimal import Decimal

from app.customer_completion_persistence import (
    COMPLETION_EVIDENCE_AUTHORITY,
    CUSTOMER_COMPLETION_ACTION_TYPE,
    CUSTOMER_DELIVERY_AUTHORITY,
    CUSTOMER_REPORTING_AUTHORITY,
    LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
    LANE_283_IDEMPOTENCY_KEY,
    load_customer_completion_status,
)
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
)


def _token(actor_role: str = "pm", project_scope: list[str] | None = None) -> dict[str, str]:
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


def _seed_production_tracking_record() -> None:
    store.production_tracking_records[LANE_282_PRODUCTION_TRACKING_RECORD_ID] = {
        "id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "tracking_kind": "field_start_zero_actual_baseline",
        "record_status": "recorded",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "idempotency_key": LANE_282_IDEMPOTENCY_KEY,
        "mutation_id": "mut-existing-production-tracking",
        "audit_event_id": "audit-existing-production-tracking",
        "recorded_at_utc": "2026-05-18T04:30:00Z",
        "production_quantity_count": 0,
        "labor_entry_count": 0,
        "actual_labor_hours": Decimal("0.00"),
        "apparatus_progress_count": 0,
        "progress_update_count": 0,
    }


def _seed_preconditions() -> None:
    _seed_temp_power_ready_rows()
    _seed_durable_field_record()
    _seed_production_tracking_record()


def _payload(**overrides):
    payload = {
        "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "idempotency_key": LANE_283_IDEMPOTENCY_KEY,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "record_kind": "customer_completion_zero_evidence_baseline",
        "record_status": "recorded",
        "record_scope": "customer_completion_baseline_no_external_delivery_or_finance",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "workpackage_count": 7,
        "task_ready_count": 15,
        "apparatus_ready_count": 184,
        "assignment_count": 184,
        "unique_assignment_apparatus_count": 184,
        "issue_count": 0,
        "durable_field_record_count": 1,
        "production_tracking_record_count": 1,
        "production_quantity_count": 0,
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress_count": 0,
        "progress_update_count": 0,
        "customer_report_artifacts": [],
        "customer_report_count": 0,
        "completion_evidence_artifacts": [],
        "completion_evidence_count": 0,
        "customer_delivery_events": [],
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "finance_authority": "not_admitted",
        "billing_authority": "not_admitted",
        "payroll_authority": "not_admitted",
        "invoice_authority": "not_admitted",
        "accounting_authority": "not_admitted",
        "daily_summary": "Customer completion baseline recorded with no customer report, evidence artifact, delivery, or finance output.",
        "customer_readiness_evidence": {
            "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            "zero_actual_baseline": True,
        },
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides):
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": CUSTOMER_COMPLETION_ACTION_TYPE,
        "entity_id": payload["customer_completion_record_id"],
        "payload": payload,
        "reason": "Persist PM Lane 283 customer completion baseline; delivery and finance remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T05:15:00Z",
    }
    request.update(overrides)
    return request


def test_customer_completion_route_persists_zero_output_baseline_and_readback(client):
    _seed_preconditions()
    before_status = load_customer_completion_status()
    assert before_status["classification"] == "no_customer_completion_record"
    assert before_status["preconditions"]["counts"]["production_tracking_record_count"] == 1

    response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "customer_completion_record"
    assert data["action_type"] == CUSTOMER_COMPLETION_ACTION_TYPE
    assert data["entity_id"] == LANE_283_CUSTOMER_COMPLETION_RECORD_ID
    assert data["new_state"]["customer_reporting_authority"] == CUSTOMER_REPORTING_AUTHORITY
    assert data["new_state"]["completion_evidence_authority"] == COMPLETION_EVIDENCE_AUTHORITY
    assert data["new_state"]["customer_delivery_authority"] == CUSTOMER_DELIVERY_AUTHORITY
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["billing_authority"] == "not_admitted"
    assert data["new_state"]["customer_report_artifacts"] == []
    assert data["new_state"]["completion_evidence_artifacts"] == []
    assert data["new_state"]["customer_report_count"] == 0
    assert data["new_state"]["completion_evidence_count"] == 0
    assert len(store.customer_completion_records) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "customer_completion_record"
    json.dumps(store.customer_completion_records[LANE_283_CUSTOMER_COMPLETION_RECORD_ID]["precondition_readback"])

    status = client.get("/api/v1/reads/customer-completion-status", headers=_token()).json()
    assert status["classification"] == "customer_completion_baseline_recorded"
    assert status["customer_completion_record_id"] == LANE_283_CUSTOMER_COMPLETION_RECORD_ID
    assert status["customer_reporting_authority"] == CUSTOMER_REPORTING_AUTHORITY
    assert status["completion_evidence_authority"] == COMPLETION_EVIDENCE_AUTHORITY
    assert status["customer_delivery_authority"] == CUSTOMER_DELIVERY_AUTHORITY
    assert status["finance_authority"] == "not_admitted"
    assert status["customer_report_count"] == 0
    assert status["completion_evidence_count"] == 0


def test_customer_completion_route_replays_identical_payload_without_second_insert(client):
    _seed_preconditions()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/customer-completion", json=request, headers=_token())
    second = client.post("/api/v1/mutations/customer-completion", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.customer_completion_records) == 1
    assert len(store.audit_log) == 1


def test_customer_completion_route_rejects_replay_mismatch(client):
    _seed_preconditions()
    first = client.post("/api/v1/mutations/customer-completion", json=_request(_payload()), headers=_token())
    changed = _payload(daily_summary="Changed replay summary.")

    second = client.post("/api/v1/mutations/customer-completion", json=_request(changed), headers=_token())

    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"
    assert len(store.customer_completion_records) == 1


def test_customer_completion_route_rejects_missing_production_tracking_record(client):
    _seed_temp_power_ready_rows()
    _seed_durable_field_record()

    response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"
    assert len(store.customer_completion_records) == 0


def test_customer_completion_route_rejects_customer_delivery_or_finance_widening(client):
    _seed_preconditions()

    report_response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload(customer_report_count=1, customer_report_artifacts=[{"name": "report.pdf"}])),
        headers=_token(),
    )
    delivery_response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload(customer_delivery_authority="admitted")),
        headers=_token(),
    )
    finance_response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload(finance_authority="admitted")),
        headers=_token(),
    )

    assert report_response.status_code == 200
    assert report_response.json()["status"] == "rejected"
    assert report_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert delivery_response.status_code == 200
    assert delivery_response.json()["status"] == "rejected"
    assert delivery_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert finance_response.status_code == 200
    assert finance_response.json()["status"] == "rejected"
    assert finance_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert len(store.customer_completion_records) == 0


def test_customer_completion_route_requires_pm_role(client):
    _seed_preconditions()

    response = client.post(
        "/api/v1/mutations/customer-completion",
        json=_request(_payload()),
        headers=_token(actor_role="lead"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert len(store.customer_completion_records) == 0
