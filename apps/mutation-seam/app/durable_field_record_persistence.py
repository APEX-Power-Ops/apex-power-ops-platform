from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.auth.role_guard import check_scope
from app.db.memory_store import store
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.idempotency.store import save_idempotency


DURABLE_FIELD_RECORD_ENTITY_TYPE = "durable_field_record"
DURABLE_FIELD_RECORD_ACTION_TYPE = "create_daily_field_record"
DURABLE_FIELD_RECORD_ROUTE = "/api/v1/mutations/durable-field-records"
DURABLE_FIELD_RECORD_STATUS_ROUTE = "/api/v1/reads/durable-field-record-status"
DURABLE_FIELD_RECORD_PERSISTENCE_VERSION = "pm_lane_281_durable_field_record_v1"

TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
TEMP_POWER_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
TEMP_POWER_SOURCE_FINGERPRINT = "e111fdbe934bf9de07ed24c1"
LANE_279_FIELD_AUTH_RECORD_ID = "pm-lane-279-field-auth-temp-power-2026-05-18"
LANE_280_STATUS_RECORD_ID = "pm-lane-280-status-readiness-temp-power-2026-05-18"
LANE_281_FIELD_RECORD_ID = "pm-lane-281-durable-field-record-temp-power-2026-05-18"
LANE_281_IDEMPOTENCY_KEY = "pm-lane-281-durable-field-record:pm-import-project-miner-temp-power:2026-05-18"

EXPECTED_COUNTS = {
    "workpackage_count": 7,
    "task_ready_count": 15,
    "apparatus_ready_count": 184,
    "assignment_count": 184,
    "unique_assignment_apparatus_count": 184,
    "issue_count": 0,
    "production_quantity_count": 0,
}

REQUIRED_PAYLOAD_FIELDS = {
    "field_record_id",
    "idempotency_key",
    "project_id",
    "record_date",
    "field_record_kind",
    "record_status",
    "record_scope",
    "source_import_candidate_id",
    "source_import_fingerprint",
    "field_authorization_record_id",
    "schedule_status_record_id",
    "workpackage_count",
    "task_ready_count",
    "apparatus_ready_count",
    "assignment_count",
    "unique_assignment_apparatus_count",
    "issue_count",
    "daily_summary",
    "field_evidence_attachments",
    "production_quantity_count",
    "field_evidence_authority",
    "production_tracking_authority",
    "customer_reporting_authority",
    "finance_authority",
}

OPTIONAL_PAYLOAD_FIELDS = {
    "readiness_evidence",
    "field_notes",
}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _records() -> Any:
    return store.durable_field_records


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _temp_power_preconditions() -> Dict[str, Any]:
    tasks = [row for row in _values(store.tasks) if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-task-")]
    apparatus = [row for row in _values(store.apparatus) if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-app-")]
    workpackages = [row for row in _values(store.workpackages) if str(row.get("id") or "").startswith("pm-import-project-miner-temp-power-wp-")]
    assignments = [
        row for row in _values(store.assignments)
        if str(row.get("apparatus_id") or "").startswith("pm-import-project-miner-temp-power-app-")
    ]
    issues = [
        row for row in _values(store.issues)
        if str(row.get("apparatus_id") or "").startswith("pm-import-project-miner-temp-power-app-")
        or str(row.get("task_id") or "").startswith("pm-import-project-miner-temp-power-task-")
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
    }
    mismatches = []
    for field, expected in EXPECTED_COUNTS.items():
        if field == "production_quantity_count":
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
    }


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
        entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _normalize_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = {field: payload.get(field) for field in sorted(REQUIRED_PAYLOAD_FIELDS)}
    for field in sorted(OPTIONAL_PAYLOAD_FIELDS):
        if field in payload:
            normalized[field] = payload.get(field)
    if normalized.get("field_evidence_attachments") is None:
        normalized["field_evidence_attachments"] = []
    if normalized.get("readiness_evidence") is None:
        normalized["readiness_evidence"] = {}
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
            "Durable field record payload contains fields outside the admitted PM Lane 281 contract.",
            detail={"unknown_fields": unknown_fields},
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return _invalid_payload_response(
            request,
            "Durable field record payload is missing required fields.",
            detail={"missing_fields": missing_fields},
        )

    expected_values = {
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
        "field_evidence_authority": "not_admitted_attachment_write",
        "production_tracking_authority": "not_admitted",
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        **EXPECTED_COUNTS,
    }
    mismatches = []
    for field, expected in expected_values.items():
        actual = payload.get(field)
        if actual != expected:
            mismatches.append({"field": field, "expected": expected, "actual": actual})

    if request.idempotency_key != LANE_281_IDEMPOTENCY_KEY:
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "expected": LANE_281_IDEMPOTENCY_KEY,
                "actual": request.idempotency_key,
            }
        )
    if request.entity_id and request.entity_id != LANE_281_FIELD_RECORD_ID:
        mismatches.append(
            {
                "field": "envelope.entity_id",
                "expected": LANE_281_FIELD_RECORD_ID,
                "actual": request.entity_id,
            }
        )
    if payload.get("field_evidence_attachments") != []:
        mismatches.append(
            {
                "field": "field_evidence_attachments",
                "expected": [],
                "actual": payload.get("field_evidence_attachments"),
            }
        )
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
            "Durable field record payload does not match the admitted PM Lane 281 contract.",
            detail={"mismatches": mismatches},
        )
    return None


def _record_matches(record: Mapping[str, Any], normalized_payload: Mapping[str, Any]) -> bool:
    return _stable_json(record.get("field_record_payload") or {}) == _stable_json(normalized_payload)


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
        entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
        action_type=action_type,
        new_state=dict(record),
        audit_event_id=audit_event_id,
    )


def persist_durable_field_record(request: MutationRequest, actor: Actor) -> MutationResponse:
    if request.action_type != DURABLE_FIELD_RECORD_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown durable field record action type: {request.action_type}",
        )

    if request.source != "online":
        return error_response(
            code=ErrorCode.INVALID_PAYLOAD,
            message="Durable field record persistence must originate from online source.",
            entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
            entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "B":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Durable field record persistence requires mutation_class B.",
            entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
            entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "lead":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only lead actors can persist this PM Lane 281 durable field record.",
            entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
            entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the Temp Power project.",
            entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
            entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    preconditions = _temp_power_preconditions()
    if not preconditions["valid"]:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Durable field record requires imported assignments plus schedule/status readiness readback.",
            entity_id=request.entity_id or LANE_281_FIELD_RECORD_ID,
            entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
            action_type=request.action_type,
            detail=preconditions,
        )

    payload_error = _validate_payload(request, preconditions)
    if payload_error:
        return payload_error

    normalized_payload = _normalize_payload(request.payload)
    records = _records()
    existing = records.get(LANE_281_FIELD_RECORD_ID)
    if existing:
        if not _record_matches(existing, normalized_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing durable field record does not match the submitted replay payload.",
                entity_id=LANE_281_FIELD_RECORD_ID,
                entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"field_record_id": LANE_281_FIELD_RECORD_ID},
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
        "id": LANE_281_FIELD_RECORD_ID,
        "project_id": TEMP_POWER_PROJECT_ID,
        "record_date": normalized_payload["record_date"],
        "field_record_kind": normalized_payload["field_record_kind"],
        "record_status": normalized_payload["record_status"],
        "created_by_actor_id": actor.actor_id,
        "created_by_role": actor.actor_role,
        "recorded_at_utc": recorded_at,
        "source_import_candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_import_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "field_authorization_record_id": LANE_279_FIELD_AUTH_RECORD_ID,
        "schedule_status_record_id": LANE_280_STATUS_RECORD_ID,
        "production_tracking_authority": "not_admitted",
        "customer_reporting_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "idempotency_key": LANE_281_IDEMPOTENCY_KEY,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "persistence_version": DURABLE_FIELD_RECORD_PERSISTENCE_VERSION,
        "route": DURABLE_FIELD_RECORD_ROUTE,
        "status_route": DURABLE_FIELD_RECORD_STATUS_ROUTE,
        "field_record_payload": normalized_payload,
        "precondition_readback": preconditions,
        "field_evidence_authority": "not_admitted_attachment_write",
        "field_evidence_attachments": [],
        "production_quantity_count": 0,
        "daily_summary": normalized_payload["daily_summary"],
        "readiness_evidence": normalized_payload.get("readiness_evidence") or {},
    }
    if normalized_payload.get("field_notes"):
        record["field_notes"] = normalized_payload["field_notes"]

    records[LANE_281_FIELD_RECORD_ID] = record
    audit_request = request.model_copy(update={"entity_id": LANE_281_FIELD_RECORD_ID, "payload": record})
    record_audit_event(
        actor=actor,
        request=audit_request,
        from_state={},
        to_state=record,
        mutation_id=mutation_id,
        event_id=audit_event_id,
        entity_type=DURABLE_FIELD_RECORD_ENTITY_TYPE,
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


def load_durable_field_record_status() -> Dict[str, Any]:
    try:
        rows = [
            row for row in _values(_records())
            if row.get("project_id") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover - exercised through broken-store tests if needed.
        return {
            "classification": "durable_field_record_storage_unavailable",
            "storage_available": False,
            "route": DURABLE_FIELD_RECORD_STATUS_ROUTE,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "production_tracking_authority": "not_admitted",
            "customer_reporting_authority": "not_admitted",
            "finance_authority": "not_admitted",
        }

    preconditions = _temp_power_preconditions()
    latest = sorted(rows, key=lambda row: str(row.get("recorded_at_utc") or row.get("created_at") or ""), reverse=True)
    current = next((row for row in latest if row.get("id") == LANE_281_FIELD_RECORD_ID), None)
    if not current:
        return {
            "classification": "no_durable_field_record",
            "storage_available": True,
            "route": DURABLE_FIELD_RECORD_STATUS_ROUTE,
            "expected_field_record_id": LANE_281_FIELD_RECORD_ID,
            "record_count": len(rows),
            "preconditions": preconditions,
            "production_tracking_authority": "not_admitted",
            "customer_reporting_authority": "not_admitted",
            "finance_authority": "not_admitted",
        }

    return {
        "classification": "durable_field_recorded",
        "storage_available": True,
        "route": DURABLE_FIELD_RECORD_STATUS_ROUTE,
        "field_record_id": current.get("id"),
        "record_count": len(rows),
        "record_date": current.get("record_date"),
        "field_record_kind": current.get("field_record_kind"),
        "record_status": current.get("record_status"),
        "mutation_id": current.get("mutation_id"),
        "audit_event_id": current.get("audit_event_id"),
        "source_import_candidate_id": current.get("source_import_candidate_id"),
        "source_import_fingerprint": current.get("source_import_fingerprint"),
        "field_authorization_record_id": current.get("field_authorization_record_id"),
        "schedule_status_record_id": current.get("schedule_status_record_id"),
        "preconditions": preconditions,
        "production_tracking_authority": current.get("production_tracking_authority") or "not_admitted",
        "customer_reporting_authority": current.get("customer_reporting_authority") or "not_admitted",
        "finance_authority": current.get("finance_authority") or "not_admitted",
        "field_evidence_authority": current.get("field_evidence_authority") or "not_admitted_attachment_write",
        "production_quantity_count": current.get("production_quantity_count"),
    }
