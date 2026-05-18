from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.auth.role_guard import check_scope
from app.db.memory_store import store
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse


TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE = "pm_temp_power_customer_preview_review"
TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ACTION_TYPE = "persist_temp_power_customer_preview_review"
TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ROUTE = "/api/v1/mutations/temp-power-customer-preview-reviews"
TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_ROUTE = "/api/v1/reads/temp-power-customer-preview-status"
TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_PERSISTENCE_VERSION = "pm_lane_315_customer_preview_review_v1"
TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_SOURCE = "seam.pm_customer_preview_reviews"
LANE_315_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "009_pm_lane_315_customer_preview_reviews.sql"
)
_SCHEMA_READY = False

TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
TEMP_POWER_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
TEMP_POWER_SOURCE_FINGERPRINT = "e111fdbe934bf9de07ed24c1"

ALLOWED_DELIVERY_CHANNELS = {"CONTROLLED_EMAIL", "LATER_APPROVED_PORTAL"}
FOLLOWUP_PM_REVIEW_STATUSES = {"PENDING_PM_FOLLOWUP", "REVIEW_ONLY_INCOMPLETE_EVIDENCE"}
BLOCKED_PAYLOAD_KEYWORDS = ("finance", "payroll", "invoice", "accounting", "writeback")
BLOCKED_PAYLOAD_FIELDS = {"finance_authority", "source_writeback_authority", "customer_delivery_authority"}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def _ensure_customer_preview_review_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY or os.getenv("SEAM_STORE_BACKEND") == "memory":
        return
    if type(store).__name__ != "SupabaseStore":
        _SCHEMA_READY = True
        return

    from app.db.supabase_store import _conn_get

    with _conn_get().cursor() as cur:
        cur.execute("SELECT to_regclass('seam.pm_customer_preview_reviews') IS NOT NULL")
        exists = bool(cur.fetchone()[0])
        if not exists:
            cur.execute(LANE_315_MIGRATION_PATH.read_text(encoding="utf-8"))
    _SCHEMA_READY = True


def _records() -> Any:
    _ensure_customer_preview_review_schema()
    if not hasattr(store, "temp_power_customer_preview_reviews"):
        store.temp_power_customer_preview_reviews = {}
    return store.temp_power_customer_preview_reviews


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value).strip() for value in values if str(value).strip())
    value = str(values).strip()
    return [value] if value else []


def build_temp_power_customer_preview_review_id(payload: Mapping[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "customer_preview_id": payload.get("customer_preview_id"),
        "coverage_scope_task_ids": _string_list(payload.get("coverage_scope_task_ids")),
        "coverage_scope_apparatus_ids": _string_list(payload.get("coverage_scope_apparatus_ids")),
        "idempotency_key": payload.get("idempotency_key"),
    }
    return f"temp-power-customer-preview-review-{_stable_hash(identity)}"


def _normalize_payload(payload: Mapping[str, Any], actor: Actor, reviewed_at: str) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["project_id"] = str(normalized.get("project_id") or "").strip()
    normalized["candidate_id"] = str(normalized.get("candidate_id") or "").strip()
    normalized["source_fingerprint"] = str(normalized.get("source_fingerprint") or "").strip()
    normalized["customer_preview_id"] = str(normalized.get("customer_preview_id") or "").strip()
    normalized["coverage_scope_task_ids"] = _string_list(normalized.get("coverage_scope_task_ids"))
    normalized["coverage_scope_apparatus_ids"] = _string_list(normalized.get("coverage_scope_apparatus_ids"))
    normalized["preview_summary"] = str(normalized.get("preview_summary") or "").strip()
    normalized["preview_artifact_refs"] = _string_list(normalized.get("preview_artifact_refs"))
    normalized["named_recipient_name"] = str(normalized.get("named_recipient_name") or "").strip()
    normalized["named_recipient_role"] = str(normalized.get("named_recipient_role") or "").strip()
    normalized["delivery_channel"] = str(normalized.get("delivery_channel") or "").strip()
    normalized["future_delivery_proof_requirements"] = _string_list(
        normalized.get("future_delivery_proof_requirements")
    )
    normalized["durable_delivery_event"] = bool(normalized.get("durable_delivery_event"))
    normalized["delivery_proof_recorded"] = bool(normalized.get("delivery_proof_recorded"))
    normalized["delivery_block_reason"] = str(normalized.get("delivery_block_reason") or "").strip()
    normalized["pm_review_status"] = str(normalized.get("pm_review_status") or "").strip()
    normalized["pm_review_note"] = str(normalized.get("pm_review_note") or "").strip()
    normalized["idempotency_key"] = str(normalized.get("idempotency_key") or "").strip()
    normalized["pm_actor"] = actor.actor_id
    normalized["approver_role"] = actor.actor_role
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
        entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
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
        "customer_preview_id",
        "coverage_scope_task_ids",
        "coverage_scope_apparatus_ids",
        "preview_summary",
        "preview_artifact_refs",
        "named_recipient_name",
        "named_recipient_role",
        "delivery_channel",
        "future_delivery_proof_requirements",
        "durable_delivery_event",
        "delivery_proof_recorded",
        "delivery_block_reason",
        "pm_review_status",
        "pm_review_note",
    }
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        return _invalid_payload_response(
            request,
            "Customer preview review payload is missing required fields.",
            detail={"missing_fields": missing},
        )

    blocked_fields = _blocked_payload_fields(payload)
    if blocked_fields:
        return _invalid_payload_response(
            request,
            "Customer preview review payload may not widen finance, delivery authority, or source-writeback boundaries.",
            detail={"blocked_fields": blocked_fields},
        )

    if str(payload.get("project_id") or "").strip() != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "Customer preview review is admitted only for the current Temp Power project.",
            detail={"expected_project_id": TEMP_POWER_PROJECT_ID, "project_id": payload.get("project_id")},
        )

    if str(payload.get("candidate_id") or "").strip() != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "Customer preview review is admitted only for the current Temp Power import candidate.",
            detail={"expected_candidate_id": TEMP_POWER_CANDIDATE_ID, "candidate_id": payload.get("candidate_id")},
        )

    if str(payload.get("source_fingerprint") or "").strip() != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "Customer preview review source_fingerprint must match the current admitted Temp Power source.",
            detail={
                "expected_source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
                "source_fingerprint": payload.get("source_fingerprint"),
            },
        )

    customer_preview_id = str(payload.get("customer_preview_id") or "").strip()
    if not customer_preview_id:
        return _invalid_payload_response(request, "customer_preview_id is required.")

    coverage_scope_task_ids = payload.get("coverage_scope_task_ids")
    if not isinstance(coverage_scope_task_ids, list):
        return _invalid_payload_response(request, "coverage_scope_task_ids must be an array.")
    normalized_task_ids = _string_list(coverage_scope_task_ids)
    if not normalized_task_ids:
        return _invalid_payload_response(request, "coverage_scope_task_ids must contain at least one task_id.")
    for task_id in normalized_task_ids:
        task = _task_row(task_id)
        if not task:
            return error_response(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="coverage_scope_task_ids must reference existing Temp Power tasks.",
                entity_id=request.entity_id or "unknown",
                entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"task_id": task_id},
            )
        if str(task.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
            return _invalid_payload_response(
                request,
                "coverage_scope_task_ids must belong to the current Temp Power project.",
                detail={"task_id": task_id, "task_project_id": task.get("project_id")},
            )

    coverage_scope_apparatus_ids = payload.get("coverage_scope_apparatus_ids")
    if not isinstance(coverage_scope_apparatus_ids, list):
        return _invalid_payload_response(request, "coverage_scope_apparatus_ids must be an array.")
    for apparatus_id in _string_list(coverage_scope_apparatus_ids):
        apparatus = _apparatus_row(apparatus_id)
        if not apparatus:
            return error_response(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message="coverage_scope_apparatus_ids must reference existing Temp Power apparatus.",
                entity_id=request.entity_id or "unknown",
                entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"apparatus_id": apparatus_id},
            )
        if str(apparatus.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
            return _invalid_payload_response(
                request,
                "coverage_scope_apparatus_ids must belong to the current Temp Power project.",
                detail={"apparatus_id": apparatus_id, "apparatus_project_id": apparatus.get("project_id")},
            )
        if str(apparatus.get("task_id") or "") not in normalized_task_ids:
            return _invalid_payload_response(
                request,
                "coverage_scope_apparatus_ids must belong to the supplied coverage_scope_task_ids.",
                detail={"apparatus_id": apparatus_id, "apparatus_task_id": apparatus.get("task_id")},
            )

    if not str(payload.get("preview_summary") or "").strip():
        return _invalid_payload_response(request, "preview_summary is required.")
    if not isinstance(payload.get("preview_artifact_refs"), list):
        return _invalid_payload_response(request, "preview_artifact_refs must be an array.")
    if not _string_list(payload.get("preview_artifact_refs")):
        return _invalid_payload_response(request, "preview_artifact_refs must contain at least one preview artifact ref.")
    if not str(payload.get("named_recipient_name") or "").strip():
        return _invalid_payload_response(request, "named_recipient_name is required.")
    if not str(payload.get("named_recipient_role") or "").strip():
        return _invalid_payload_response(request, "named_recipient_role is required.")

    delivery_channel = str(payload.get("delivery_channel") or "").strip()
    if delivery_channel not in ALLOWED_DELIVERY_CHANNELS:
        return _invalid_payload_response(
            request,
            "delivery_channel must be one of the admitted preview-only values.",
            detail={"allowed_values": sorted(ALLOWED_DELIVERY_CHANNELS), "delivery_channel": delivery_channel},
        )

    if not isinstance(payload.get("future_delivery_proof_requirements"), list):
        return _invalid_payload_response(request, "future_delivery_proof_requirements must be an array.")
    if not _string_list(payload.get("future_delivery_proof_requirements")):
        return _invalid_payload_response(
            request,
            "future_delivery_proof_requirements must record at least one future proof requirement.",
        )

    if bool(payload.get("durable_delivery_event")):
        return _invalid_payload_response(
            request,
            "durable_delivery_event must remain false in the customer preview review slice.",
        )
    if bool(payload.get("delivery_proof_recorded")):
        return _invalid_payload_response(
            request,
            "delivery_proof_recorded must remain false in the customer preview review slice.",
        )
    if not str(payload.get("delivery_block_reason") or "").strip():
        return _invalid_payload_response(request, "delivery_block_reason is required.")
    if not str(payload.get("pm_review_status") or "").strip():
        return _invalid_payload_response(request, "pm_review_status is required.")
    if not str(payload.get("pm_review_note") or "").strip():
        return _invalid_payload_response(request, "pm_review_note is required.")

    return None


def _response(
    *,
    status: str,
    mutation_id: str,
    record: Mapping[str, Any],
    action_type: str,
    audit_event_id: Optional[str],
) -> MutationResponse:
    new_state = dict(record)
    new_state.setdefault("review_storage_status", "accepted_for_review_storage")
    return MutationResponse(
        status=status,
        mutation_id=mutation_id,
        entity_id=str(record["review_id"]),
        entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
        action_type=action_type,
        new_state=new_state,
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
        "entity_type": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
        "entity_id": record["review_id"],
        "action_type": request.action_type,
        "from_state": {},
        "to_state": dict(record),
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": record["created_at"],
    }


def classify_temp_power_customer_preview_review_record(
    record: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not record:
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "status": "no_customer_preview_review_record",
            "record_count": 0,
            "latest_customer_preview_review_id": None,
            "latest_reviewed_at": None,
            "customer_preview_id": None,
            "preview_summary": None,
            "preview_artifact_count": 0,
            "named_recipient_name": None,
            "named_recipient_role": None,
            "delivery_channel": None,
            "pm_review_status": None,
            "pm_actor": None,
            "approver_role": None,
            "durable_delivery_event": False,
            "delivery_block_reason": None,
            "delivery_proof_recorded": False,
            "storage_route_registered": True,
            "storage_source": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            "customer_delivery_authority": "not_admitted",
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
        }

    current_candidate_match = (
        str(record.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(record.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
    )
    current_source_fingerprint_match = str(record.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
    pm_review_status = str(record.get("pm_review_status") or "")
    delivery_block_reason = str(record.get("delivery_block_reason") or "").strip()

    if not current_candidate_match or not current_source_fingerprint_match:
        status = "customer_preview_review_recorded_stale_source"
    elif pm_review_status in FOLLOWUP_PM_REVIEW_STATUSES:
        status = "customer_preview_pending_pm_followup"
    elif delivery_block_reason:
        status = "customer_preview_delivery_blocked"
    else:
        status = "customer_preview_review_recorded_current_match"

    return {
        "project_id": record.get("project_id"),
        "candidate_id": record.get("candidate_id"),
        "source_fingerprint": record.get("source_fingerprint"),
        "current_candidate_match": current_candidate_match,
        "current_source_fingerprint_match": current_source_fingerprint_match,
        "status": status,
        "record_count": 0,
        "latest_customer_preview_review_id": record.get("review_id"),
        "latest_reviewed_at": record.get("pm_reviewed_at"),
        "customer_preview_id": record.get("customer_preview_id"),
        "preview_summary": record.get("preview_summary"),
        "preview_artifact_count": len(_string_list(record.get("preview_artifact_refs"))),
        "named_recipient_name": record.get("named_recipient_name"),
        "named_recipient_role": record.get("named_recipient_role"),
        "delivery_channel": record.get("delivery_channel"),
        "pm_review_status": record.get("pm_review_status"),
        "pm_actor": record.get("pm_actor"),
        "approver_role": record.get("approver_role"),
        "durable_delivery_event": bool(record.get("durable_delivery_event")),
        "delivery_block_reason": record.get("delivery_block_reason"),
        "delivery_proof_recorded": bool(record.get("delivery_proof_recorded")),
        "storage_route_registered": True,
        "storage_source": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_SOURCE,
        "entity_type": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
        "customer_delivery_authority": record.get("customer_delivery_authority") or "not_admitted",
        "finance_authority": record.get("finance_authority") or "not_admitted",
        "source_writeback_authority": record.get("source_writeback_authority") or "not_admitted",
    }


def load_temp_power_customer_preview_review_status() -> Dict[str, Any]:
    try:
        rows = [
            row
            for row in _values(_records())
            if str(row.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        ]
    except Exception as exc:  # pragma: no cover
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "status": "customer_preview_review_storage_unavailable",
            "record_count": 0,
            "latest_customer_preview_review_id": None,
            "latest_reviewed_at": None,
            "storage_route_registered": False,
            "storage_source": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            "storage_available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "customer_delivery_authority": "not_admitted",
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
            "durable_delivery_event": False,
            "delivery_proof_recorded": False,
        }

    rows.sort(key=lambda row: str(row.get("pm_reviewed_at") or row.get("created_at") or ""), reverse=True)
    current = rows[0] if rows else None
    status = classify_temp_power_customer_preview_review_record(current)
    status["record_count"] = len(rows)
    status["storage_available"] = True
    return status


async def persist_temp_power_customer_preview_review(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown customer preview review action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Temp Power customer preview review persistence cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Temp Power customer preview review persistence requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Temp Power customer preview review records.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the current Temp Power project.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Customer preview review payload is required.")

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

    review_id = build_temp_power_customer_preview_review_id(request.payload)
    if request.entity_id and request.entity_id != review_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the deterministic customer preview review id when provided.",
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
                message="Idempotent replay payload does not match the stored customer preview review record.",
                entity_id=review_id,
                entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
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
        "customer_preview_id": normalized_payload["customer_preview_id"],
        "coverage_scope_task_ids": list(normalized_payload["coverage_scope_task_ids"]),
        "coverage_scope_apparatus_ids": list(normalized_payload["coverage_scope_apparatus_ids"]),
        "preview_summary": normalized_payload["preview_summary"],
        "preview_artifact_refs": list(normalized_payload["preview_artifact_refs"]),
        "named_recipient_name": normalized_payload["named_recipient_name"],
        "named_recipient_role": normalized_payload["named_recipient_role"],
        "delivery_channel": normalized_payload["delivery_channel"],
        "future_delivery_proof_requirements": list(normalized_payload["future_delivery_proof_requirements"]),
        "durable_delivery_event": False,
        "delivery_proof_recorded": False,
        "delivery_block_reason": normalized_payload["delivery_block_reason"],
        "pm_review_status": normalized_payload["pm_review_status"],
        "pm_review_note": normalized_payload["pm_review_note"],
        "pm_actor": actor.actor_id,
        "approver_role": actor.actor_role,
        "pm_reviewed_at": reviewed_at,
        "idempotency_key": normalized_payload["idempotency_key"],
        "customer_delivery_authority": "not_admitted",
        "finance_authority": "not_admitted",
        "source_writeback_authority": "not_admitted",
        "route": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ROUTE,
        "status_route": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_ROUTE,
        "storage_source": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_STATUS_SOURCE,
        "persistence_version": TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_PERSISTENCE_VERSION,
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
            entity_type=TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_ENTITY_TYPE,
        )

    return _response(
        status="accepted",
        mutation_id=mutation_id,
        record=record,
        action_type=request.action_type,
        audit_event_id=audit_event_id,
    )