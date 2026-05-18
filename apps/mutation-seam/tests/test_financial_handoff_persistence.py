import base64
import json
from decimal import Decimal

from app.customer_completion_persistence import (
    COMPLETION_EVIDENCE_AUTHORITY,
    CUSTOMER_DELIVERY_AUTHORITY,
    CUSTOMER_REPORTING_AUTHORITY,
    LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
    LANE_283_IDEMPOTENCY_KEY,
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
from app.financial_handoff_persistence import (
    FINANCIAL_HANDOFF_ACTION_TYPE,
    FINANCIAL_HANDOFF_AUTHORITY,
    LABOR_RECONCILIATION_AUTHORITY,
    LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
    LANE_284_IDEMPOTENCY_KEY,
    load_financial_handoff_status,
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


def _seed_customer_completion_record() -> None:
    store.customer_completion_records[LANE_283_CUSTOMER_COMPLETION_RECORD_ID] = {
        "id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "record_kind": "customer_completion_zero_evidence_baseline",
        "record_status": "recorded",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "finance_authority": "not_admitted",
        "billing_authority": "not_admitted",
        "payroll_authority": "not_admitted",
        "invoice_authority": "not_admitted",
        "accounting_authority": "not_admitted",
        "idempotency_key": LANE_283_IDEMPOTENCY_KEY,
        "mutation_id": "mut-existing-customer-completion",
        "audit_event_id": "audit-existing-customer-completion",
        "recorded_at_utc": "2026-05-18T05:30:00Z",
        "customer_report_artifacts": [],
        "customer_report_count": 0,
        "completion_evidence_artifacts": [],
        "completion_evidence_count": 0,
        "customer_delivery_events": [],
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
    _seed_customer_completion_record()


def _payload(**overrides):
    payload = {
        "financial_handoff_record_id": LANE_284_FINANCIAL_HANDOFF_RECORD_ID,
        "idempotency_key": LANE_284_IDEMPOTENCY_KEY,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": "2026-05-18",
        "record_kind": "financial_handoff_zero_output_baseline",
        "record_status": "recorded",
        "record_scope": "financial_handoff_baseline_no_billing_payroll_invoice_accounting_or_sync",
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "workpackage_count": 7,
        "task_ready_count": 15,
        "apparatus_ready_count": 184,
        "assignment_count": 184,
        "unique_assignment_apparatus_count": 184,
        "issue_count": 0,
        "durable_field_record_count": 1,
        "production_tracking_record_count": 1,
        "customer_completion_record_count": 1,
        "production_quantity_count": 0,
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress_count": 0,
        "progress_update_count": 0,
        "customer_report_count": 0,
        "completion_evidence_count": 0,
        "customer_delivery_event_count": 0,
        "billing_export_artifacts": [],
        "billing_export_count": 0,
        "payroll_export_artifacts": [],
        "payroll_export_count": 0,
        "invoice_records": [],
        "invoice_record_count": 0,
        "payroll_records": [],
        "payroll_record_count": 0,
        "accounting_records": [],
        "accounting_record_count": 0,
        "labor_reconciliation_entries": [],
        "labor_reconciliation_entry_count": 0,
        "external_finance_sync_events": [],
        "external_finance_sync_count": 0,
        "customer_billing_delivery_events": [],
        "customer_billing_delivery_count": 0,
        "billable_amount_total": 0.0,
        "payroll_amount_total": 0.0,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "financial_handoff_authority": FINANCIAL_HANDOFF_AUTHORITY,
        "labor_reconciliation_authority": LABOR_RECONCILIATION_AUTHORITY,
        "finance_authority": "not_admitted",
        "billing_export_authority": "not_admitted",
        "payroll_export_authority": "not_admitted",
        "invoice_authority": "not_admitted",
        "accounting_authority": "not_admitted",
        "external_finance_sync_authority": "not_admitted",
        "customer_billing_delivery_authority": "not_admitted",
        "daily_summary": "Financial handoff baseline recorded with no billing export, payroll export, invoice, accounting record, or external finance sync.",
        "financial_handoff_evidence": {
            "customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            "zero_finance_output_baseline": True,
        },
    }
    payload.update(overrides)
    return payload


def _request(payload: dict, **overrides):
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": FINANCIAL_HANDOFF_ACTION_TYPE,
        "entity_id": payload["financial_handoff_record_id"],
        "payload": payload,
        "reason": "Persist PM Lane 284 financial handoff baseline; finance outputs remain blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T06:15:00Z",
    }
    request.update(overrides)
    return request


def test_financial_handoff_route_persists_zero_finance_output_baseline_and_readback(client):
    _seed_preconditions()
    before_status = load_financial_handoff_status()
    assert before_status["classification"] == "no_financial_handoff_record"
    assert before_status["preconditions"]["counts"]["customer_completion_record_count"] == 1

    response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "financial_handoff_record"
    assert data["action_type"] == FINANCIAL_HANDOFF_ACTION_TYPE
    assert data["entity_id"] == LANE_284_FINANCIAL_HANDOFF_RECORD_ID
    assert data["new_state"]["financial_handoff_authority"] == FINANCIAL_HANDOFF_AUTHORITY
    assert data["new_state"]["labor_reconciliation_authority"] == LABOR_RECONCILIATION_AUTHORITY
    assert data["new_state"]["finance_authority"] == "not_admitted"
    assert data["new_state"]["billing_export_artifacts"] == []
    assert data["new_state"]["payroll_export_artifacts"] == []
    assert data["new_state"]["invoice_records"] == []
    assert data["new_state"]["accounting_records"] == []
    assert data["new_state"]["billing_export_count"] == 0
    assert data["new_state"]["payroll_export_count"] == 0
    assert data["new_state"]["invoice_record_count"] == 0
    assert data["new_state"]["accounting_record_count"] == 0
    assert len(store.financial_handoff_records) == 1
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["entity_type"] == "financial_handoff_record"
    json.dumps(store.financial_handoff_records[LANE_284_FINANCIAL_HANDOFF_RECORD_ID]["precondition_readback"])

    status = client.get("/api/v1/reads/financial-handoff-status", headers=_token()).json()
    assert status["classification"] == "financial_handoff_baseline_recorded"
    assert status["financial_handoff_record_id"] == LANE_284_FINANCIAL_HANDOFF_RECORD_ID
    assert status["financial_handoff_authority"] == FINANCIAL_HANDOFF_AUTHORITY
    assert status["labor_reconciliation_authority"] == LABOR_RECONCILIATION_AUTHORITY
    assert status["finance_authority"] == "not_admitted"
    assert status["billing_export_count"] == 0
    assert status["invoice_record_count"] == 0
    assert status["external_finance_sync_count"] == 0


def test_financial_handoff_route_replays_identical_payload_without_second_insert(client):
    _seed_preconditions()
    request = _request(_payload())

    first = client.post("/api/v1/mutations/financial-handoff", json=request, headers=_token())
    second = client.post("/api/v1/mutations/financial-handoff", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.financial_handoff_records) == 1
    assert len(store.audit_log) == 1


def test_financial_handoff_route_rejects_replay_mismatch(client):
    _seed_preconditions()
    first = client.post("/api/v1/mutations/financial-handoff", json=_request(_payload()), headers=_token())
    changed = _payload(daily_summary="Changed replay summary.")

    second = client.post("/api/v1/mutations/financial-handoff", json=_request(changed), headers=_token())

    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"
    assert len(store.financial_handoff_records) == 1


def test_financial_handoff_route_rejects_missing_customer_completion_record(client):
    _seed_temp_power_ready_rows()
    _seed_durable_field_record()
    _seed_production_tracking_record()

    response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload()),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"
    assert len(store.financial_handoff_records) == 0


def test_financial_handoff_route_rejects_finance_output_widening(client):
    _seed_preconditions()

    billing_response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload(billing_export_count=1, billing_export_artifacts=[{"name": "billing.csv"}])),
        headers=_token(),
    )
    invoice_response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload(invoice_authority="admitted")),
        headers=_token(),
    )
    sync_response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload(external_finance_sync_count=1, external_finance_sync_events=[{"sync": "queued"}])),
        headers=_token(),
    )

    assert billing_response.status_code == 200
    assert billing_response.json()["status"] == "rejected"
    assert billing_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert invoice_response.status_code == 200
    assert invoice_response.json()["status"] == "rejected"
    assert invoice_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert sync_response.status_code == 200
    assert sync_response.json()["status"] == "rejected"
    assert sync_response.json()["error"]["code"] == "INVALID_PAYLOAD"
    assert len(store.financial_handoff_records) == 0


def test_financial_handoff_route_requires_pm_role(client):
    _seed_preconditions()

    response = client.post(
        "/api/v1/mutations/financial-handoff",
        json=_request(_payload()),
        headers=_token(actor_role="lead"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert len(store.financial_handoff_records) == 0
