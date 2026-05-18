from __future__ import annotations

import json
from datetime import datetime, timezone
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


PRODUCTION_TRACKING_ENTITY_TYPE = "production_tracking_record"
PRODUCTION_TRACKING_ACTION_TYPE = "create_daily_production_baseline"
PRODUCTION_TRACKING_ROUTE = "/api/v1/mutations/production-tracking"
PRODUCTION_TRACKING_STATUS_ROUTE = "/api/v1/reads/production-tracking-status"
PRODUCTION_TRACKING_PERSISTENCE_VERSION = "pm_lane_282_production_tracking_v1"
PRODUCTION_TRACKING_AUTHORITY = "admitted_by_pm_lane_282_zero_actual_baseline"

LANE_282_PRODUCTION_TRACKING_RECORD_ID = "pm-lane-282-production-tracking-temp-power-2026-05-18"
LANE_282_IDEMPOTENCY_KEY = "pm-lane-282-production-tracking:pm-import-project-miner-temp-power:2026-05-18"

EXPECTED_COUNTS = {
    "workpackage_count": 7,
    "task_ready_count": 15,
    "apparatus_ready_count": 184,
    "assignment_count": 184,
    "unique_assignment_apparatus_count": 184,
    "issue_count": 0,
    "durable_field_record_count": 1,
    "production_quantity_count": 0,
    "labor_entry_count": 0,
    "actual_labor_hours": 0.0,
    "apparatus_progress_count": 0,
    "progress_update_count": 0,
}

REQUIRED_PAYLOAD_FIELDS = {
    "production_tracking_record_id",
    "idempotency_key",
    "project_id",
    "record_date",
    "tracking_kind",
    "record_status",
    "record_scope",
    "source_import_candidate_id",
    "source_import_fingerprint",
    "field_authorization_record_id",
    "schedule_status_record_id",
    "durable_field_record_id",
    "workpackage_count",
    "task_ready_count",
    "apparatus_ready_count",
    "assignment_count",
    "unique_assignment_apparatus_count",
    "issue_count",
    "durable_field_record_count",
    "production_quantities",
    "production_quantity_count",
    "labor_entries",
    "labor_entry_count",
    "actual_labor_hours",
    "apparatus_progress",
    "apparatus_progress_count",
    "progress_updates",
    "progress_update_count",
    "daily_summary",
    "production_tracking_authority",
    "customer_reporting_authority",
    "finance_authority",
}

OPTIONAL_PAYLOAD_FIELDS = {
    "production_evidence",
    "field_notes",
}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _records() -> Any:
    return store.production_tracking_records


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _temp_power_preconditions() -> Dict[str, Any]:
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

    counts = {
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
    mismatches = []
    for field, expected in EXPECTED_COUNTS.items():
        if field in {
            "production_quantity_count",
            "labor_entry_count",
            "actual_labor_hours",
            "apparatus_progress_count",
            "progress_update_count",
        }:
            continue
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

    return {
        "valid": not mismatches,
        "counts": counts,
        "mismatches": mismatches,
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
        entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _normalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = {field: payload.get(field) for field in sorted(REQUIRED_PAYLOAD_FIELDS)}
    for field in sorted(OPTIONAL_PAYLOAD_FIELDS):
        if field in payload:
            normalized[field] = payload.get(field)
    for field in ["production_quantities", "labor_entries", "apparatus_progress", "progress_updates"]:
        if normalized.get(field) is None:
            normalized[field] = []
    if normalized.get("production_evidence") is None:
        normalized["production_evidence"] = {}
    normalized["daily_summary"] = str(normalized.get("daily_summary") or "").strip()
    if "field_notes" in normalized:
        normalized["field_notes"] = str(normalized.get("field_notes") or "").strip()
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
            "Production tracking payload contains fields outside the admitted PM Lane 282 contract.",
            detail={"unknown_fields": unknown_fields},
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return _invalid_payload_response(
            request,
            "Production tracking payload is missing required fields.",
            detail={"missing_fields": missing_fields},
        )

    expected_values = {
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
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        **EXPECTED_COUNTS,
    }
    mismatches = []
    for field, expected in expected_values.items():
        actual = payload.get(field)
        if actual != expected:
            mismatches.append({"field": field, "expected": expected, "actual": actual})

    if request.idempotency_key != LANE_282_IDEMPOTENCY_KEY:
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "expected": LANE_282_IDEMPOTENCY_KEY,
                "actual": request.idempotency_key,
            }
        )
    if request.entity_id and request.entity_id != LANE_282_PRODUCTION_TRACKING_RECORD_ID:
        mismatches.append(
            {
                "field": "envelope.entity_id",
                "expected": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
                "actual": request.entity_id,
            }
        )

    empty_list_fields = ["production_quantities", "labor_entries", "apparatus_progress", "progress_updates"]
    for field in empty_list_fields:
        if payload.get(field) != []:
            mismatches.append({"field": field, "expected": [], "actual": payload.get(field)})

    if not str(payload.get("daily_summary") or "").strip():
        mismatches.append({"field": "daily_summary", "expected": "non-empty", "actual": payload.get("daily_summary")})

    precondition_counts = dict(preconditions.get("counts") or {})
    for field in [
        "workpackage_count",
        "task_ready_count",
        "apparatus_ready_count",
        "assignment_count",
        "unique_assignment_apparatus_count",
        "issue_count",
        "durable_field_record_count",
    ]:
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
            "Production tracking payload does not match the admitted PM Lane 282 contract.",
            detail={"mismatches": mismatches},
        )
    return None


def _record_matches(record: Mapping[str, Any], normalized_payload: Mapping[str, Any]) -> bool:
    return _stable_json(record.get("production_tracking_payload") or {}) == _stable_json(normalized_payload)


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
        entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
        action_type=action_type,
        new_state=dict(record),
        audit_event_id=audit_event_id,
    )


def persist_production_tracking_record(request: MutationRequest, actor: Actor) -> MutationResponse:
    if request.action_type != PRODUCTION_TRACKING_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown production tracking action type: {request.action_type}",
        )

    if request.source != "online":
        return error_response(
            code=ErrorCode.INVALID_PAYLOAD,
            message="Production tracking baseline persistence must originate from online source.",
            entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "B":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Production tracking baseline persistence requires mutation_class B.",
            entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "lead":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only lead actors can persist this PM Lane 282 production tracking baseline.",
            entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the Temp Power project.",
            entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    preconditions = _temp_power_preconditions()
    if not preconditions["valid"]:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Production tracking baseline requires imported readiness plus the PM Lane 281 durable field record.",
            entity_id=request.entity_id or LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
            action_type=request.action_type,
            detail=preconditions,
        )

    payload_error = _validate_payload(request, preconditions)
    if payload_error:
        return payload_error

    normalized_payload = _normalize_payload(request.payload)
    records = _records()
    existing = records.get(LANE_282_PRODUCTION_TRACKING_RECORD_ID)
    if existing:
        if not _record_matches(existing, normalized_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing production tracking baseline does not match the submitted replay payload.",
                entity_id=LANE_282_PRODUCTION_TRACKING_RECORD_ID,
                entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID},
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
        "id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": normalized_payload["record_date"],
        "tracking_kind": normalized_payload["tracking_kind"],
        "record_status": normalized_payload["record_status"],
        "created_by_actor_id": actor.actor_id,
        "created_by_role": actor.actor_role,
        "recorded_at_utc": recorded_at,
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "durable_field_record_id": LANE_281_FIELD_RECORD_ID,
        "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "idempotency_key": LANE_282_IDEMPOTENCY_KEY,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "persistence_version": PRODUCTION_TRACKING_PERSISTENCE_VERSION,
        "route": PRODUCTION_TRACKING_ROUTE,
        "status_route": PRODUCTION_TRACKING_STATUS_ROUTE,
        "production_tracking_payload": normalized_payload,
        "precondition_readback": preconditions,
        "production_quantities": [],
        "production_quantity_count": 0,
        "labor_entries": [],
        "labor_entry_count": 0,
        "actual_labor_hours": 0.0,
        "apparatus_progress": [],
        "apparatus_progress_count": 0,
        "progress_updates": [],
        "progress_update_count": 0,
        "daily_summary": normalized_payload["daily_summary"],
        "production_evidence": normalized_payload.get("production_evidence") or {},
    }
    if normalized_payload.get("field_notes"):
        record["field_notes"] = normalized_payload["field_notes"]

    records[LANE_282_PRODUCTION_TRACKING_RECORD_ID] = record
    audit_request = request.model_copy(update={"entity_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID, "payload": record})
    record_audit_event(
        actor=actor,
        request=audit_request,
        from_state={},
        to_state=record,
        mutation_id=mutation_id,
        event_id=audit_event_id,
        entity_type=PRODUCTION_TRACKING_ENTITY_TYPE,
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


def load_production_tracking_status() -> Dict[str, Any]:
    try:
        rows = [
            row for row in _values(_records())
            if row.get("project_id") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover - exercised through broken-store tests if needed.
        return {
            "classification": "production_tracking_storage_unavailable",
            "storage_available": False,
            "route": PRODUCTION_TRACKING_STATUS_ROUTE,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": "not_admitted",
            "finance_authority": "not_admitted",
        }

    preconditions = _temp_power_preconditions()
    latest = sorted(rows, key=lambda row: str(row.get("recorded_at_utc") or row.get("created_at") or ""), reverse=True)
    current = next((row for row in latest if row.get("id") == LANE_282_PRODUCTION_TRACKING_RECORD_ID), None)
    if not current:
        return {
            "classification": "no_production_tracking_record",
            "storage_available": True,
            "route": PRODUCTION_TRACKING_STATUS_ROUTE,
            "expected_production_tracking_record_id": LANE_282_PRODUCTION_TRACKING_RECORD_ID,
            "record_count": len(rows),
            "preconditions": preconditions,
            "production_tracking_authority": PRODUCTION_TRACKING_AUTHORITY,
            "customer_reporting_authority": "not_admitted",
            "finance_authority": "not_admitted",
        }

    return {
        "classification": "production_tracking_baseline_recorded",
        "storage_available": True,
        "route": PRODUCTION_TRACKING_STATUS_ROUTE,
        "production_tracking_record_id": current.get("id"),
        "record_count": len(rows),
        "record_date": current.get("record_date"),
        "tracking_kind": current.get("tracking_kind"),
        "record_status": current.get("record_status"),
        "mutation_id": current.get("mutation_id"),
        "audit_event_id": current.get("audit_event_id"),
        "source_import_candidate_id": current.get("source_import_candidate_id"),
        "source_import_fingerprint": current.get("source_import_fingerprint"),
        "field_authorization_record_id": current.get("field_authorization_record_id"),
        "schedule_status_record_id": current.get("schedule_status_record_id"),
        "durable_field_record_id": current.get("durable_field_record_id"),
        "preconditions": preconditions,
        "production_tracking_authority": current.get("production_tracking_authority") or PRODUCTION_TRACKING_AUTHORITY,
        "customer_reporting_authority": current.get("customer_reporting_authority") or "not_admitted",
        "finance_authority": current.get("finance_authority") or "not_admitted",
        "production_quantity_count": current.get("production_quantity_count"),
        "labor_entry_count": current.get("labor_entry_count"),
        "actual_labor_hours": current.get("actual_labor_hours"),
        "apparatus_progress_count": current.get("apparatus_progress_count"),
        "progress_update_count": current.get("progress_update_count"),
    }
