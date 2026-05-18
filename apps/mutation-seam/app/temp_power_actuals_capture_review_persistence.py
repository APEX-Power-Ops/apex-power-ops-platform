from __future__ import annotations

import hashlib
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


TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE = "pm_temp_power_actuals_capture_review"
TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE = "persist_temp_power_actuals_capture_review"
TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ROUTE = "/api/v1/mutations/temp-power-actuals-capture-reviews"
TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_ROUTE = "/api/v1/reads/temp-power-actuals-capture-review-status"
TEMP_POWER_ACTUALS_CAPTURE_REVIEW_PERSISTENCE_VERSION = "pm_lane_304_actuals_capture_review_v1"
TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_SOURCE = "seam.pm_actuals_capture_reviews"

TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
TEMP_POWER_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
TEMP_POWER_SOURCE_FINGERPRINT = "e111fdbe934bf9de07ed24c1"

ALLOWED_CORRECTION_MODES = {"ORIGINAL_REVIEW", "VOID_AND_REPLACEMENT"}
FOLLOWUP_PM_REVIEW_STATUSES = {"PENDING_PM_FOLLOWUP", "REVIEW_ONLY_INCOMPLETE_EVIDENCE"}
BLOCKED_PAYLOAD_KEYWORDS = ("finance", "export", "writeback")
BLOCKED_PAYLOAD_FIELDS = {"delivery_complete", "durable_delivery_event", "customer_delivery_authority"}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def _records() -> Any:
    if not hasattr(store, "temp_power_actuals_capture_reviews"):
        store.temp_power_actuals_capture_reviews = {}
    return store.temp_power_actuals_capture_reviews


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value).strip() for value in values if str(value).strip())
    value = str(values).strip()
    return [value] if value else []


def build_temp_power_actuals_capture_review_id(payload: Mapping[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "task_id": payload.get("task_id"),
        "apparatus_id": payload.get("apparatus_id"),
        "task_day_fallback_reason": payload.get("task_day_fallback_reason"),
        "work_date": payload.get("work_date"),
        "idempotency_key": payload.get("idempotency_key"),
    }
    return f"temp-power-actuals-capture-review-{_stable_hash(identity)}"


def _normalize_payload(payload: Mapping[str, Any], actor: Actor, reviewed_at: str) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["project_id"] = str(normalized.get("project_id") or "").strip()
    normalized["candidate_id"] = str(normalized.get("candidate_id") or "").strip()
    normalized["source_fingerprint"] = str(normalized.get("source_fingerprint") or "").strip()
    normalized["task_id"] = str(normalized.get("task_id") or "").strip()
    normalized["apparatus_id"] = str(normalized.get("apparatus_id") or "").strip() or None
    normalized["task_day_fallback_reason"] = str(normalized.get("task_day_fallback_reason") or "").strip() or None
    normalized["work_date"] = str(normalized.get("work_date") or "").strip()
    normalized["recorder_role"] = str(normalized.get("recorder_role") or "").strip()
    normalized["actual_labor_hours_preview"] = float(normalized.get("actual_labor_hours_preview"))
    normalized["work_summary_note"] = str(normalized.get("work_summary_note") or "").strip()
    normalized["primary_evidence_type"] = str(normalized.get("primary_evidence_type") or "").strip()
    normalized["primary_evidence_ref"] = str(normalized.get("primary_evidence_ref") or "").strip()
    normalized["supporting_evidence_refs"] = _string_list(normalized.get("supporting_evidence_refs"))
    normalized["correction_mode"] = str(normalized.get("correction_mode") or "").strip()
    normalized["supersedes_review_id"] = str(normalized.get("supersedes_review_id") or "").strip() or None
    normalized["replacement_reason"] = str(normalized.get("replacement_reason") or "").strip() or None
    normalized["pm_review_status"] = str(normalized.get("pm_review_status") or "").strip()
    normalized["pm_review_note"] = str(normalized.get("pm_review_note") or "").strip()
    normalized["idempotency_key"] = str(normalized.get("idempotency_key") or "").strip()
    normalized["pm_actor"] = actor.actor_id
    normalized["pm_actor_role"] = actor.actor_role
    normalized["pm_reviewed_at"] = reviewed_at
    return normalized


def _payloads_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _stable_json(left) == _stable_json(right)


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or "unknown",
        entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _blocked_payload_fields(payload: Mapping[str, Any]) -> list[str]:
    blocked = []
    for key in payload.keys():
        normalized = str(key).strip().lower()
        if normalized in BLOCKED_PAYLOAD_FIELDS:
            blocked.append(str(key))
            continue
        if normalized.startswith("delivery_"):
            blocked.append(str(key))
            continue
        if any(keyword in normalized for keyword in BLOCKED_PAYLOAD_KEYWORDS):
            blocked.append(str(key))
    return sorted(set(blocked))


def _task_row(task_id: str) -> Optional[Dict[str, Any]]:
    task = store.tasks.get(task_id)
    if not task:
        return None
    return dict(task)


def _apparatus_row(apparatus_id: str) -> Optional[Dict[str, Any]]:
    apparatus = store.apparatus.get(apparatus_id)
    if not apparatus:
        return None
    return dict(apparatus)


def _validate_payload(request: MutationRequest) -> Optional[MutationResponse]:
    payload = request.payload or {}
    required_fields = {
        "idempotency_key",
        "project_id",
        "candidate_id",
        "source_fingerprint",
        "task_id",
        "work_date",
        "recorder_role",
        "actual_labor_hours_preview",
        "work_summary_note",
        "primary_evidence_type",
        "primary_evidence_ref",
        "supporting_evidence_refs",
        "correction_mode",
        "pm_review_status",
        "pm_review_note",
    }
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        return _invalid_payload_response(
            request,
            "Actuals capture review payload is missing required fields.",
            detail={"missing_fields": missing},
        )

    blocked_fields = _blocked_payload_fields(payload)
    if blocked_fields:
        return _invalid_payload_response(
            request,
            "Actuals capture review payload may not widen finance, export, delivery, or source-writeback boundaries.",
            detail={"blocked_fields": blocked_fields},
        )

    try:
        normalized_hours = float(payload.get("actual_labor_hours_preview"))
    except (TypeError, ValueError):
        return _invalid_payload_response(
            request,
            "actual_labor_hours_preview must be numeric.",
        )

    if normalized_hours < 0:
        return _invalid_payload_response(
            request,
            "actual_labor_hours_preview must be nonnegative.",
            detail={"actual_labor_hours_preview": payload.get("actual_labor_hours_preview")},
        )

    if str(payload.get("project_id") or "").strip() != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "Actuals capture review is admitted only for the current Temp Power project.",
            detail={"expected_project_id": TEMP_POWER_PROJECT_ID, "project_id": payload.get("project_id")},
        )

    if str(payload.get("candidate_id") or "").strip() != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "Actuals capture review is admitted only for the current Temp Power import candidate.",
            detail={"expected_candidate_id": TEMP_POWER_CANDIDATE_ID, "candidate_id": payload.get("candidate_id")},
        )

    if str(payload.get("source_fingerprint") or "").strip() != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "Actuals capture review source_fingerprint must match the current admitted Temp Power source.",
            detail={
                "expected_source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
                "source_fingerprint": payload.get("source_fingerprint"),
            },
        )

    task_id = str(payload.get("task_id") or "").strip()
    task = _task_row(task_id)
    if not task:
        return error_response(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="task_id must reference an existing Temp Power task.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"task_id": task_id},
        )
    if str(task.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "task_id must belong to the current Temp Power project.",
            detail={"task_id": task_id, "task_project_id": task.get("project_id")},
        )

    apparatus_id = str(payload.get("apparatus_id") or "").strip()
    fallback_reason = str(payload.get("task_day_fallback_reason") or "").strip()
    if not apparatus_id and not fallback_reason:
        return _invalid_payload_response(
            request,
            "apparatus_id is required unless task_day_fallback_reason is supplied.",
        )

    if apparatus_id:
        apparatus = _apparatus_row(apparatus_id)
        if not apparatus:
            return error_response(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="apparatus_id must reference an existing Temp Power apparatus.",
                entity_id=request.entity_id or "unknown",
                entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"apparatus_id": apparatus_id},
            )
        if str(apparatus.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
            return _invalid_payload_response(
                request,
                "apparatus_id must belong to the current Temp Power project.",
                detail={"apparatus_id": apparatus_id, "apparatus_project_id": apparatus.get("project_id")},
            )
        if str(apparatus.get("task_id") or "") != task_id:
            return _invalid_payload_response(
                request,
                "apparatus_id must belong to the supplied task_id.",
                detail={"apparatus_id": apparatus_id, "task_id": task_id, "apparatus_task_id": apparatus.get("task_id")},
            )

    if not str(payload.get("work_date") or "").strip():
        return _invalid_payload_response(request, "work_date is required.")
    if not str(payload.get("recorder_role") or "").strip():
        return _invalid_payload_response(request, "recorder_role is required.")
    if not str(payload.get("work_summary_note") or "").strip():
        return _invalid_payload_response(request, "work_summary_note is required.")
    if not str(payload.get("primary_evidence_type") or "").strip():
        return _invalid_payload_response(request, "primary_evidence_type is required.")
    if not str(payload.get("primary_evidence_ref") or "").strip():
        return _invalid_payload_response(request, "primary_evidence_ref is required.")
    if not isinstance(payload.get("supporting_evidence_refs"), list):
        return _invalid_payload_response(request, "supporting_evidence_refs must be an array.")
    if not str(payload.get("pm_review_status") or "").strip():
        return _invalid_payload_response(request, "pm_review_status is required.")
    if not str(payload.get("pm_review_note") or "").strip():
        return _invalid_payload_response(request, "pm_review_note is required.")

    correction_mode = str(payload.get("correction_mode") or "").strip()
    if correction_mode not in ALLOWED_CORRECTION_MODES:
        return _invalid_payload_response(
            request,
            "correction_mode must be one of the admitted actuals-review values.",
            detail={"allowed_values": sorted(ALLOWED_CORRECTION_MODES), "correction_mode": correction_mode},
        )
    if correction_mode == "VOID_AND_REPLACEMENT":
        if not str(payload.get("supersedes_review_id") or "").strip():
            return _invalid_payload_response(request, "VOID_AND_REPLACEMENT requires supersedes_review_id.")
        if not str(payload.get("replacement_reason") or "").strip():
            return _invalid_payload_response(request, "VOID_AND_REPLACEMENT requires replacement_reason.")

    if normalized_hours > 0 and (
        not str(payload.get("primary_evidence_type") or "").strip()
        or not str(payload.get("primary_evidence_ref") or "").strip()
    ):
        return _invalid_payload_response(
            request,
            "Nonzero actual_labor_hours_preview requires primary evidence.",
        )

    return None


def _response(
    *,
    status: str,
    mutation_id: str,
    record: Mapping[str, Any],
    action_type: str,
    audit_event_id: Optional[str],
) -> MutationResponse:
    return MutationResponse(
        status=status,
        mutation_id=mutation_id,
        entity_id=str(record["review_id"]),
        entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
        action_type=action_type,
        new_state=dict(record),
        audit_event_id=audit_event_id,
    )


def _build_audit_event(
    *,
    actor: Actor,
    request: MutationRequest,
    record: Mapping[str, Any],
    mutation_id: str,
    audit_event_id: str,
) -> Dict[str, Any]:
    return {
        "id": audit_event_id,
        "mutation_id": mutation_id,
        "actor_id": actor.actor_id,
        "actor_role": actor.actor_role,
        "entity_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
        "entity_id": record["review_id"],
        "action_type": request.action_type,
        "from_state": {},
        "to_state": dict(record),
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": record["created_at"],
    }


def classify_temp_power_actuals_capture_review_record(
    record: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not record:
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "status": "no_actuals_capture_review_record",
            "record_count": 0,
            "latest_review_id": None,
            "latest_reviewed_at": None,
            "task_id": None,
            "apparatus_id": None,
            "task_day_fallback_reason": None,
            "work_date": None,
            "pm_review_status": None,
            "pm_actor": None,
            "recorder_role": None,
            "actual_labor_hours_preview": None,
            "primary_evidence_type": None,
            "primary_evidence_ref": None,
            "supporting_evidence_count": 0,
            "correction_mode": None,
            "replacement_chain_present": False,
            "supersedes_review_id": None,
            "storage_route_registered": True,
            "storage_source": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            "customer_delivery_authority": "not_admitted",
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
            "durable_delivery_event": False,
        }

    current_candidate_match = (
        str(record.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(record.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
    )
    current_source_fingerprint_match = str(record.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
    replacement_chain_present = bool(record.get("supersedes_review_id")) or str(record.get("correction_mode") or "") == "VOID_AND_REPLACEMENT"
    pm_review_status = str(record.get("pm_review_status") or "")

    if not current_candidate_match or not current_source_fingerprint_match:
        status = "actuals_capture_review_recorded_stale_source"
    elif replacement_chain_present:
        status = "actuals_capture_review_replacement_chain_present"
    elif pm_review_status in FOLLOWUP_PM_REVIEW_STATUSES:
        status = "actuals_capture_review_pending_pm_followup"
    else:
        status = "actuals_capture_review_recorded_current_match"

    return {
        "project_id": record.get("project_id"),
        "candidate_id": record.get("candidate_id"),
        "source_fingerprint": record.get("source_fingerprint"),
        "current_candidate_match": current_candidate_match,
        "current_source_fingerprint_match": current_source_fingerprint_match,
        "status": status,
        "record_count": 0,
        "latest_review_id": record.get("review_id"),
        "latest_reviewed_at": record.get("pm_reviewed_at"),
        "task_id": record.get("task_id"),
        "apparatus_id": record.get("apparatus_id"),
        "task_day_fallback_reason": record.get("task_day_fallback_reason"),
        "work_date": record.get("work_date"),
        "pm_review_status": record.get("pm_review_status"),
        "pm_actor": record.get("pm_actor"),
        "recorder_role": record.get("recorder_role"),
        "actual_labor_hours_preview": record.get("actual_labor_hours_preview"),
        "primary_evidence_type": record.get("primary_evidence_type"),
        "primary_evidence_ref": record.get("primary_evidence_ref"),
        "supporting_evidence_count": len(_string_list(record.get("supporting_evidence_refs"))),
        "correction_mode": record.get("correction_mode"),
        "replacement_chain_present": replacement_chain_present,
        "supersedes_review_id": record.get("supersedes_review_id"),
        "storage_route_registered": True,
        "storage_source": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_SOURCE,
        "entity_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
        "customer_delivery_authority": record.get("customer_delivery_authority") or "not_admitted",
        "finance_authority": record.get("finance_authority") or "not_admitted",
        "source_writeback_authority": record.get("source_writeback_authority") or "not_admitted",
        "durable_delivery_event": bool(record.get("durable_delivery_event")),
    }


def load_temp_power_actuals_capture_review_status() -> Dict[str, Any]:
    try:
        rows = [
            row
            for row in _values(_records())
            if str(row.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover - exercised through broken-store tests if needed.
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "status": "actuals_capture_review_storage_unavailable",
            "record_count": 0,
            "latest_review_id": None,
            "latest_reviewed_at": None,
            "storage_route_registered": False,
            "storage_source": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            "storage_available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "customer_delivery_authority": "not_admitted",
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
            "durable_delivery_event": False,
        }

    rows.sort(key=lambda row: str(row.get("pm_reviewed_at") or row.get("created_at") or ""), reverse=True)
    current = rows[0] if rows else None
    status = classify_temp_power_actuals_capture_review_record(current)
    status["record_count"] = len(rows)
    status["storage_available"] = True
    return status


async def persist_temp_power_actuals_capture_review(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown actuals capture review action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Temp Power actuals capture review persistence cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Temp Power actuals capture review persistence requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Temp Power actuals capture review records.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the current Temp Power project.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Actuals capture review payload is required.")

    payload_idempotency_key = str(request.payload.get("idempotency_key") or "")
    if request.idempotency_key != payload_idempotency_key:
        return _invalid_payload_response(
            request,
            "Envelope idempotency_key must match payload.idempotency_key.",
            detail={
                "envelope_idempotency_key": request.idempotency_key,
                "payload_idempotency_key": payload_idempotency_key,
            },
        )

    review_id = build_temp_power_actuals_capture_review_id(request.payload)
    if request.entity_id and request.entity_id != review_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the deterministic actuals capture review id when provided.",
            detail={"expected_entity_id": review_id, "provided_entity_id": request.entity_id},
        )

    payload_error = _validate_payload(request)
    if payload_error:
        return payload_error

    records = _records()
    existing = dict(records.get(review_id)) if review_id in records else None
    reviewed_at = str(existing.get("pm_reviewed_at")) if existing else _server_timestamp()
    normalized_payload = _normalize_payload(request.payload, actor, reviewed_at)

    if existing:
        existing_payload = existing.get("review_payload") or {}
        if not _payloads_match(normalized_payload, existing_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Idempotent replay payload does not match the stored actuals capture review record.",
                entity_id=review_id,
                entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"review_id": review_id},
            )
        return _response(
            status="idempotent_hit",
            mutation_id=str(existing.get("mutation_id") or f"mut-{uuid4()}"),
            record=existing,
            action_type=request.action_type,
            audit_event_id=str(existing.get("audit_event_id") or "") or None,
        )

    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    record = {
        "review_id": review_id,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "project_id": normalized_payload["project_id"],
        "candidate_id": normalized_payload["candidate_id"],
        "source_fingerprint": normalized_payload["source_fingerprint"],
        "task_id": normalized_payload["task_id"],
        "apparatus_id": normalized_payload["apparatus_id"],
        "task_day_fallback_reason": normalized_payload["task_day_fallback_reason"],
        "work_date": normalized_payload["work_date"],
        "recorder_role": normalized_payload["recorder_role"],
        "actual_labor_hours_preview": normalized_payload["actual_labor_hours_preview"],
        "work_summary_note": normalized_payload["work_summary_note"],
        "primary_evidence_type": normalized_payload["primary_evidence_type"],
        "primary_evidence_ref": normalized_payload["primary_evidence_ref"],
        "supporting_evidence_refs": list(normalized_payload["supporting_evidence_refs"]),
        "correction_mode": normalized_payload["correction_mode"],
        "supersedes_review_id": normalized_payload["supersedes_review_id"],
        "replacement_reason": normalized_payload["replacement_reason"],
        "pm_review_status": normalized_payload["pm_review_status"],
        "pm_review_note": normalized_payload["pm_review_note"],
        "pm_actor": actor.actor_id,
        "pm_actor_role": actor.actor_role,
        "pm_reviewed_at": reviewed_at,
        "idempotency_key": normalized_payload["idempotency_key"],
        "customer_delivery_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "source_writeback_authority": "not_admitted",
        "durable_delivery_event": False,
        "route": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ROUTE,
        "status_route": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_ROUTE,
        "storage_source": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_STATUS_SOURCE,
        "persistence_version": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_PERSISTENCE_VERSION,
        "review_payload": normalized_payload,
        "created_at": reviewed_at,
    }
    audit_request = request.model_copy(update={"entity_id": review_id, "payload": record})
    audit_event = _build_audit_event(
        actor=actor,
        request=audit_request,
        record=record,
        mutation_id=mutation_id,
        audit_event_id=audit_event_id,
    )
    if hasattr(records, "insert_with_audit"):
        records.insert_with_audit(record, audit_event)
    else:
        records[review_id] = record
        record_audit_event(
            actor=actor,
            request=audit_request,
            from_state={},
            to_state=record,
            mutation_id=mutation_id,
            event_id=audit_event_id,
            entity_type=TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ENTITY_TYPE,
        )

    return _response(
        status="accepted",
        mutation_id=mutation_id,
        record=record,
        action_type=request.action_type,
        audit_event_id=audit_event_id,
    )