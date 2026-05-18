from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.auth.role_guard import check_scope
from app.db.memory_store import store
from app.durable_field_record_persistence import (
    LANE_279_FIELD_AUTH_RECORD_ID,
    LANE_280_STATUS_RECORD_ID,
    LANE_281_FIELD_RECORD_ID,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
)
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.idempotency.store import save_idempotency
from app.production_tracking_persistence import (
    LANE_282_PRODUCTION_TRACKING_RECORD_ID,
    PRODUCTION_TRACKING_AUTHORITY,
    load_production_tracking_status,
)


CUSTOMER_COMPLETION_ENTITY_TYPE = "customer_completion_record"
CUSTOMER_COMPLETION_ACTION_TYPE = "create_customer_completion_baseline"
CUSTOMER_COMPLETION_ROUTE = "/api/v1/mutations/customer-completion"
CUSTOMER_COMPLETION_STATUS_ROUTE = "/api/v1/reads/customer-completion-status"
CUSTOMER_COMPLETION_PERSISTENCE_VERSION = "pm_lane_283_customer_completion_v1"
CUSTOMER_REPORTING_AUTHORITY = "admitted_by_pm_lane_283_customer_completion_baseline"
COMPLETION_EVIDENCE_AUTHORITY = "admitted_by_pm_lane_283_zero_evidence_baseline"
CUSTOMER_DELIVERY_AUTHORITY = "not_admitted_external_delivery"
FINANCE_AUTHORITY = "not_admitted"

LANE_283_CUSTOMER_COMPLETION_RECORD_ID = "pm-lane-283-customer-completion-temp-power-2026-05-18"
LANE_283_IDEMPOTENCY_KEY = "pm-lane-283-customer-completion:pm-import-project-miner-temp-power:2026-05-18"
LANE_283_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "006_pm_lane_283_customer_completion_records.sql"
)
_SCHEMA_READY = False

EXPECTED_COUNTS = {
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
    "customer_report_count": 0,
    "completion_evidence_count": 0,
}

REQUIRED_PAYLOAD_FIELDS = {
    "customer_completion_record_id",
    "idempotency_key",
    "project_id",
    "record_date",
    "record_kind",
    "record_status",
    "record_scope",
    "source_import_candidate_id",
    "source_import_fingerprint",
    "field_authorization_record_id",
    "schedule_status_record_id",
    "durable_field_record_id",
    "production_tracking_record_id",
    "workpackage_count",
    "task_ready_count",
    "apparatus_ready_count",
    "assignment_count",
    "unique_assignment_apparatus_count",
    "issue_count",
    "durable_field_record_count",
    "production_tracking_record_count",
    "production_quantity_count",
    "labor_entry_count",
    "actual_labor_hours",
    "apparatus_progress_count",
    "progress_update_count",
    "customer_report_artifacts",
    "customer_report_count",
    "completion_evidence_artifacts",
    "completion_evidence_count",
    "customer_delivery_events",
    "production_tracking_authority",
    "customer_reporting_authority",
    "completion_evidence_authority",
    "customer_delivery_authority",
    "finance_authority",
    "billing_authority",
    "payroll_authority",
    "invoice_authority",
    "accounting_authority",
    "daily_summary",
}

OPTIONAL_PAYLOAD_FIELDS = {
    "customer_readiness_evidence",
    "field_notes",
    "pm_review_notes",
}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def _ensure_customer_completion_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY or os.getenv("SEAM_STORE_BACKEND") == "memory":
        return
    if type(store).__name__ != "SupabaseStore":
        _SCHEMA_READY = True
        return

    from app.db.supabase_store import _conn_get

    with _conn_get().cursor() as cur:
        cur.execute("SELECT to_regclass('seam.customer_completion_records') IS NOT NULL")
        exists = bool(cur.fetchone()[0])
        if not exists:
            cur.execute(LANE_283_MIGRATION_PATH.read_text(encoding="utf-8"))
    _SCHEMA_READY = True


def _records() -> Any:
    _ensure_customer_completion_schema()
    return store.customer_completion_records


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _readiness_counts() -> Dict[str, int]:
    tasks = [
        row for row in _values(store.tasks)
        if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-task-")
    ]
    apparatus = [
        row for row in _values(store.apparatus)
        if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-app-")
    ]
    workpackages = [
        row for row in _values(store.workpackages)
        if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-wp-")
    ]
    assignments = [
        row for row in _values(store.assignments)
        if str(row.get("apparatus_id") or "").startswith("pm-import-project-miner-temp-power-app-")
    ]
    issues = [
        row for row in _values(store.issues)
        if str(row.get("apparatus_id") or "").startswith("pm-import-project-miner-temp-power-app-")
        or str(row.get("task_id") or "").startswith("pm-import-project-miner-temp-power-task-")
    ]
    durable_records = [
        row for row in _values(store.durable_field_records)
        if row.get("id") == LANE_281_FIELD_RECORD_ID
        and row.get("project_id") == TEMP_POWER_PROJECT_ID
        and row.get("record_status") == "recorded"
    ]

    ready_tasks = [row for row in tasks if row.get("status") == "ready"]
    ready_apparatus = [row for row in apparatus if row.get("status") == "ready"]
    not_started_workpackages = [row for row in workpackages if row.get("status") == "not_started"]
    unique_assignment_apparatus = {
        str(row.get("apparatus_id"))
        for row in assignments
        if row.get("apparatus_id")
    }

    return {
        "workpackage_count": len(workpackages),
        "workpackage_not_started_count": len(not_started_workpackages),
        "task_count": len(tasks),
        "task_ready_count": len(ready_tasks),
        "apparatus_count": len(apparatus),
        "apparatus_ready_count": len(ready_apparatus),
        "assignment_count": len(assignments),
        "unique_assignment_apparatus_count": len(unique_assignment_apparatus),
        "issue_count": len(issues),
        "durable_field_record_count": len(durable_records),
    }


def _production_tracking_readback() -> tuple[Dict[str, Any], list[Dict[str, Any]]]:
    production_status = load_production_tracking_status()
    production_records = [
        row for row in _values(store.production_tracking_records)
        if row.get("id") == LANE_282_PRODUCTION_TRACKING_RECORD_ID
        and row.get("project_id") == TEMP_POWER_PROJECT_ID
        and row.get("record_status") == "recorded"
    ]
    return production_status, production_records


def _temp_power_preconditions() -> Dict[str, Any]:
    counts: Dict[str, Any] = _readiness_counts()
    production_status, production_records = _production_tracking_readback()
    current_production = production_records[0] if production_records else {}
    counts.update(
        {
            "production_tracking_record_count": len(production_records),
            "production_quantity_count": current_production.get("production_quantity_count"),
            "labor_entry_count": current_production.get("labor_entry_count"),
            "actual_labor_hours": current_production.get("actual_labor_hours"),
            "apparatus_progress_count": current_production.get("apparatus_progress_count"),
            "progress_update_count": current_production.get("progress_update_count"),
            "customer_report_count": 0,
            "completion_evidence_count": 0,
        }
    )

    mismatches = []
    for field, expected in EXPECTED_COUNTS.items():
        if counts.get(field) != expected:
            mismatches.append({"field": field, "expected": expected, "actual": counts.get(field)})
    if counts["workpackage_not_started_count"] != EXPECTED_COUNTS["workpackage_count"]:
        mismatches.append(
            {
                "field": "workpackage_not_started_count",
                "expected": EXPECTED_COUNTS["workpackage_count"],
                "actual": counts["workpackage_not_started_count"],
            }
        )

    if production_status.get("classification") != "production_tracking_baseline_recorded":
        mismatches.append(
            {
                "field": "production_tracking_status",
                "expected": "production_tracking_baseline_recorded",
                "actual": production_status.get("classification"),
            }
        )

    if current_production:
        expected_production_values = {
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": "not_admitted",
            "finance_authority": "not_admitted",
        }
        for field, expected in expected_production_values.items():
            if current_production.get(field) != expected:
                mismatches.append({"field": f"production.{field}", "expected": expected, "actual": current_production.get(field)})

    return {
        "valid": not mismatches,
        "counts": counts,
        "mismatches": mismatches,
        "production_tracking_status": production_status,
        "production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
    }


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _normalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = {field: payload.get(field) for field in sorted(REQUIRED_PAYLOAD_FIELDS)}
    for field in sorted(OPTIONAL_PAYLOAD_FIELDS):
        if field in payload:
            normalized[field] = payload.get(field)
    for field in ["customer_report_artifacts", "completion_evidence_artifacts", "customer_delivery_events"]:
        if normalized.get(field) is None:
            normalized[field] = []
    if normalized.get("customer_readiness_evidence") is None:
        normalized["customer_readiness_evidence"] = {}
    normalized["daily_summary"] = str(normalized.get("daily_summary") or "").strip()
    for field in ["field_notes", "pm_review_notes"]:
        if field in normalized:
            normalized[field] = str(normalized.get(field) or "").strip()
    return normalized


def _validate_payload(
    request: MutationRequest,
    preconditions: Mapping[str, Any],
) -> Optional[MutationResponse]:
    payload = request.payload or {}
    unknown_fields = sorted(set(payload) - REQUIRED_PAYLOAD_FIELDS - OPTIONAL_PAYLOAD_FIELDS)
    if unknown_fields:
        return _invalid_payload_response(
            request,
            "Customer completion payload contains fields outside the admitted PM Lane 283 contract.",
            detail={"unknown_fields": unknown_fields},
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return _invalid_payload_response(
            request,
            "Customer completion payload is missing required fields.",
            detail={"missing_fields": missing_fields},
        )

    expected_values = {
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
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
        "finance_authority": FINANCE_AUTHORITY,
        "billing_authority": FINANCE_AUTHORITY,
        "payroll_authority": FINANCE_AUTHORITY,
        "invoice_authority": FINANCE_AUTHORITY,
        "accounting_authority": FINANCE_AUTHORITY,
        **EXPECTED_COUNTS,
    }
    mismatches = []
    for field, expected in expected_values.items():
        actual = payload.get(field)
        if actual != expected:
            mismatches.append({"field": field, "expected": expected, "actual": actual})

    if request.idempotency_key != LANE_283_IDEMPOTENCY_KEY:
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "expected": LANE_283_IDEMPOTENCY_KEY,
                "actual": request.idempotency_key,
            }
        )
    if request.entity_id and request.entity_id != LANE_283_CUSTOMER_COMPLETION_RECORD_ID:
        mismatches.append(
            {
                "field": "envelope.entity_id",
                "expected": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
                "actual": request.entity_id,
            }
        )

    for field in ["customer_report_artifacts", "completion_evidence_artifacts", "customer_delivery_events"]:
        if payload.get(field) != []:
            mismatches.append({"field": field, "expected": [], "actual": payload.get(field)})

    if not str(payload.get("daily_summary") or "").strip():
        mismatches.append({"field": "daily_summary", "expected": "non-empty", "actual": payload.get("daily_summary")})

    precondition_counts = dict(preconditions.get("counts") or {})
    for field in EXPECTED_COUNTS:
        if payload.get(field) != precondition_counts.get(field):
            mismatches.append(
                {
                    "field": f"payload.{field}_vs_readback",
                    "expected": precondition_counts.get(field),
                    "actual": payload.get(field),
                }
            )

    if mismatches:
        return _invalid_payload_response(
            request,
            "Customer completion payload does not match the admitted PM Lane 283 contract.",
            detail={"mismatches": mismatches},
        )
    return None


def _record_matches(record: Mapping[str, Any], normalized_payload: Mapping[str, Any]) -> bool:
    return _stable_json(record.get("customer_completion_payload") or {}) == _stable_json(normalized_payload)


def _response(
    *,
    status: str,
    mutation_id: str,
    action_type: str,
    record: Mapping[str, Any],
    audit_event_id: Optional[str],
) -> MutationResponse:
    return MutationResponse(
        status=status,
        mutation_id=mutation_id,
        entity_id=str(record["id"]),
        entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
        action_type=action_type,
        new_state=dict(record),
        audit_event_id=audit_event_id,
    )


def persist_customer_completion_record(request: MutationRequest, actor: Actor) -> MutationResponse:
    if request.action_type != CUSTOMER_COMPLETION_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown customer completion action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Customer completion baseline persistence cannot be queued offline.",
            entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Customer completion baseline persistence requires mutation_class C.",
            entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist this PM Lane 283 customer completion baseline.",
            entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the Temp Power project.",
            entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    preconditions = _temp_power_preconditions()
    if not preconditions["valid"]:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Customer completion baseline requires the PM Lane 282 zero-actual production tracking record.",
            entity_id=request.entity_id or LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
            action_type=request.action_type,
            detail=preconditions,
        )

    payload_error = _validate_payload(request, preconditions)
    if payload_error:
        return payload_error

    normalized_payload = _normalize_payload(request.payload)
    records = _records()
    existing = records.get(LANE_283_CUSTOMER_COMPLETION_RECORD_ID)
    if existing:
        if not _record_matches(existing, normalized_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing customer completion baseline does not match the submitted replay payload.",
                entity_id=LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
                entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID},
            )
        return _response(
            status="idempotent_hit",
            mutation_id=str(existing.get("mutation_id") or f"mut-{uuid4()}"),
            action_type=request.action_type,
            record=existing,
            audit_event_id=str(existing.get("audit_event_id") or "") or None,
        )

    recorded_at = _server_timestamp()
    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    record = {
        "id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": normalized_payload["record_date"],
        "record_kind": normalized_payload["record_kind"],
        "record_status": normalized_payload["record_status"],
        "created_by_actor_id": actor.actor_id,
        "created_by_role": actor.actor_role,
        "recorded_at_utc": recorded_at,
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
        "finance_authority": FINANCE_AUTHORITY,
        "billing_authority": FINANCE_AUTHORITY,
        "payroll_authority": FINANCE_AUTHORITY,
        "invoice_authority": FINANCE_AUTHORITY,
        "accounting_authority": FINANCE_AUTHORITY,
        "idempotency_key": LANE_283_IDEMPOTENCY_KEY,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "persistence_version": CUSTOMER_COMPLETION_PERSISTENCE_VERSION,
        "route": CUSTOMER_COMPLETION_ROUTE,
        "status_route": CUSTOMER_COMPLETION_STATUS_ROUTE,
        "customer_completion_payload": normalized_payload,
        "precondition_readback": _json_safe(preconditions),
        "customer_report_artifacts": [],
        "customer_report_count": 0,
        "completion_evidence_artifacts": [],
        "completion_evidence_count": 0,
        "customer_delivery_events": [],
        "production_quantity_count": 0,
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress_count": 0,
        "progress_update_count": 0,
        "daily_summary": normalized_payload["daily_summary"],
        "customer_readiness_evidence": normalized_payload.get("customer_readiness_evidence") or {},
    }
    for field in ["field_notes", "pm_review_notes"]:
        if normalized_payload.get(field):
            record[field] = normalized_payload[field]

    records[LANE_283_CUSTOMER_COMPLETION_RECORD_ID] = record
    audit_request = request.model_copy(update={"entity_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID, "payload": record})
    record_audit_event(
        actor=actor,
        request=audit_request,
        from_state={},
        to_state=record,
        mutation_id=mutation_id,
        event_id=audit_event_id,
        entity_type=CUSTOMER_COMPLETION_ENTITY_TYPE,
    )
    response = _response(
        status="accepted",
        mutation_id=mutation_id,
        action_type=request.action_type,
        record=record,
        audit_event_id=audit_event_id,
    )
    save_idempotency(request.idempotency_key, response)
    return response


def load_customer_completion_status() -> Dict[str, Any]:
    try:
        rows = [
            row for row in _values(_records())
            if row.get("project_id") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover - exercised through broken-store tests if needed.
        return {
            "classification": "customer_completion_storage_unavailable",
            "storage_available": False,
            "route": CUSTOMER_COMPLETION_STATUS_ROUTE,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
            "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
            "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
            "finance_authority": FINANCE_AUTHORITY,
            "billing_authority": FINANCE_AUTHORITY,
            "payroll_authority": FINANCE_AUTHORITY,
            "invoice_authority": FINANCE_AUTHORITY,
            "accounting_authority": FINANCE_AUTHORITY,
        }

    preconditions = _temp_power_preconditions()
    latest = sorted(rows, key=lambda row: str(row.get("recorded_at_utc") or row.get("created_at") or ""), reverse=True)
    current = next((row for row in latest if row.get("id") == LANE_283_CUSTOMER_COMPLETION_RECORD_ID), None)
    if not current:
        return {
            "classification": "no_customer_completion_record",
            "storage_available": True,
            "route": CUSTOMER_COMPLETION_STATUS_ROUTE,
            "expected_customer_completion_record_id": LANE_283_CUSTOMER_COMPLETION_RECORD_ID,
            "record_count": len(rows),
            "preconditions": preconditions,
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": CUSTOMER_REPORTING_AUTHORITY,
            "completion_evidence_authority": COMPLETION_EVIDENCE_AUTHORITY,
            "customer_delivery_authority": CUSTOMER_DELIVERY_AUTHORITY,
            "finance_authority": FINANCE_AUTHORITY,
            "billing_authority": FINANCE_AUTHORITY,
            "payroll_authority": FINANCE_AUTHORITY,
            "invoice_authority": FINANCE_AUTHORITY,
            "accounting_authority": FINANCE_AUTHORITY,
        }

    return {
        "classification": "customer_completion_baseline_recorded",
        "storage_available": True,
        "route": CUSTOMER_COMPLETION_STATUS_ROUTE,
        "customer_completion_record_id": current.get("id"),
        "record_count": len(rows),
        "record_date": current.get("record_date"),
        "record_kind": current.get("record_kind"),
        "record_status": current.get("record_status"),
        "mutation_id": current.get("mutation_id"),
        "audit_event_id": current.get("audit_event_id"),
        "source_import_candidate_id": current.get("source_import_candidate_id"),
        "source_import_fingerprint": current.get("source_import_fingerprint"),
        "field_authorization_record_id": current.get("field_authorization_record_id"),
        "schedule_status_record_id": current.get("schedule_status_record_id"),
        "durable_field_record_id": current.get("durable_field_record_id"),
        "production_tracking_record_id": current.get("production_tracking_record_id"),
        "preconditions": preconditions,
        "production_tracking_authority": current.get("production_tracking_authority") or PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": current.get("customer_reporting_authority") or CUSTOMER_REPORTING_AUTHORITY,
        "completion_evidence_authority": current.get("completion_evidence_authority") or COMPLETION_EVIDENCE_AUTHORITY,
        "customer_delivery_authority": current.get("customer_delivery_authority") or CUSTOMER_DELIVERY_AUTHORITY,
        "finance_authority": current.get("finance_authority") or FINANCE_AUTHORITY,
        "billing_authority": current.get("billing_authority") or FINANCE_AUTHORITY,
        "payroll_authority": current.get("payroll_authority") or FINANCE_AUTHORITY,
        "invoice_authority": current.get("invoice_authority") or FINANCE_AUTHORITY,
        "accounting_authority": current.get("accounting_authority") or FINANCE_AUTHORITY,
        "customer_report_count": current.get("customer_report_count"),
        "completion_evidence_count": current.get("completion_evidence_count"),
        "production_quantity_count": current.get("production_quantity_count"),
        "labor_entry_count": current.get("labor_entry_count"),
        "actual_labor_hours": current.get("actual_labor_hours"),
        "apparatus_progress_count": current.get("apparatus_progress_count"),
        "progress_update_count": current.get("progress_update_count"),
    }
