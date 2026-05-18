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


TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE = "pm_customer_delivery_proof_review"
TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ACTION_TYPE = "persist_temp_power_customer_delivery_proof_review"
TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ROUTE = "/api/v1/mutations/temp-power-customer-delivery-proof-reviews"
TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_ROUTE = "/api/v1/reads/temp-power-customer-delivery-proof-status"
TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_PERSISTENCE_VERSION = "pm_lane_329_customer_delivery_proof_review_v1"
TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_SOURCE = "seam.pm_customer_delivery_proof_reviews"

TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
TEMP_POWER_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
TEMP_POWER_SOURCE_FINGERPRINT = "e111fdbe934bf9de07ed24c1"

ALLOWED_DELIVERY_CHANNELS = {"CONTROLLED_EMAIL", "LATER_APPROVED_PORTAL"}
FOLLOWUP_PM_DELIVERY_APPROVAL_STATUSES = {"PENDING_PM_FOLLOWUP", "REVIEW_ONLY_INCOMPLETE_EVIDENCE"}
BLOCKED_PAYLOAD_KEYWORDS = ("finance", "payroll", "invoice", "accounting", "writeback", "billing", "export")
BLOCKED_PAYLOAD_FIELDS = {
    "finance_export_recorded",
    "source_writeback_recorded",
    "customer_billing_delivery_recorded",
    "finance_authority",
    "source_writeback_authority",
    "customer_billing_delivery_authority",
}


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def _records() -> Any:
    if not hasattr(store, "temp_power_customer_delivery_proof_reviews"):
        store.temp_power_customer_delivery_proof_reviews = {}
    return store.temp_power_customer_delivery_proof_reviews


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value).strip() for value in values if str(value).strip())
    value = str(values).strip()
    return [value] if value else []


def _preview_review_records() -> Dict[str, Any]:
    if not hasattr(store, "temp_power_customer_preview_reviews"):
        return {}
    return store.temp_power_customer_preview_reviews


def _preview_review_row(review_id: str) -> Optional[Dict[str, Any]]:
    rows = _preview_review_records()
    if review_id not in rows:
        return None
    return dict(rows[review_id])


def build_temp_power_customer_delivery_proof_review_id(payload: Mapping[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "customer_preview_review_id": payload.get("customer_preview_review_id"),
        "customer_delivery_event_id": payload.get("customer_delivery_event_id"),
        "preview_artifact_lineage": _string_list(payload.get("preview_artifact_lineage")),
        "idempotency_key": payload.get("idempotency_key"),
    }
    return f"temp-power-customer-delivery-proof-review-{_stable_hash(identity)}"


def _normalize_payload(payload: Mapping[str, Any], actor: Actor, reviewed_at: str, proof_recorded_at: Optional[str]) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["project_id"] = str(normalized.get("project_id") or "").strip()
    normalized["candidate_id"] = str(normalized.get("candidate_id") or "").strip()
    normalized["source_fingerprint"] = str(normalized.get("source_fingerprint") or "").strip()
    normalized["customer_preview_review_id"] = str(normalized.get("customer_preview_review_id") or "").strip()
    normalized["customer_delivery_event_id"] = str(normalized.get("customer_delivery_event_id") or "").strip()
    normalized["preview_artifact_lineage"] = _string_list(normalized.get("preview_artifact_lineage"))
    normalized["named_recipient_name"] = str(normalized.get("named_recipient_name") or "").strip()
    normalized["named_recipient_role"] = str(normalized.get("named_recipient_role") or "").strip()
    normalized["delivery_channel"] = str(normalized.get("delivery_channel") or "").strip()
    normalized["delivery_artifact_refs"] = _string_list(normalized.get("delivery_artifact_refs"))
    normalized["delivered_at_utc"] = str(normalized.get("delivered_at_utc") or "").strip()
    normalized["delivery_proof_type"] = str(normalized.get("delivery_proof_type") or "").strip()
    normalized["delivery_proof_ref"] = str(normalized.get("delivery_proof_ref") or "").strip()
    normalized["delivery_proof_recorded"] = bool(normalized.get("delivery_proof_recorded"))
    normalized["pm_delivery_approval_status"] = str(normalized.get("pm_delivery_approval_status") or "").strip()
    normalized["pm_delivery_approval_note"] = str(normalized.get("pm_delivery_approval_note") or "").strip()
    normalized["delivery_note"] = str(normalized.get("delivery_note") or "").strip()
    normalized["idempotency_key"] = str(normalized.get("idempotency_key") or "").strip()
    normalized["pm_actor"] = actor.actor_id
    normalized["pm_actor_role"] = actor.actor_role
    normalized["pm_reviewed_at"] = reviewed_at
    normalized["proof_recorded_at_utc"] = proof_recorded_at
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
        entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
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


def _lineage_matches_preview_review(
    preview_review_id: str,
    preview_artifact_lineage: list[str],
) -> tuple[bool, Optional[Dict[str, Any]]]:
    preview_review = _preview_review_row(preview_review_id)
    if not preview_review:
        return False, None
    preview_artifact_refs = _string_list(preview_review.get("preview_artifact_refs"))
    return preview_artifact_lineage == preview_artifact_refs, preview_review


def _validate_payload(request: MutationRequest) -> Optional[MutationResponse]:
    payload = request.payload or {}
    required_fields = {
        "idempotency_key",
        "project_id",
        "candidate_id",
        "source_fingerprint",
        "customer_preview_review_id",
        "customer_delivery_event_id",
        "preview_artifact_lineage",
        "named_recipient_name",
        "named_recipient_role",
        "delivery_channel",
        "delivery_artifact_refs",
        "delivered_at_utc",
        "delivery_proof_type",
        "delivery_proof_ref",
        "delivery_proof_recorded",
        "pm_delivery_approval_status",
        "pm_delivery_approval_note",
        "delivery_note",
    }
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        return _invalid_payload_response(
            request,
            "Customer delivery/proof review payload is missing required fields.",
            detail={"missing_fields": missing},
        )

    blocked_fields = _blocked_payload_fields(payload)
    if blocked_fields:
        return _invalid_payload_response(
            request,
            "Customer delivery/proof review payload may not widen finance, source-writeback, or customer-billing-delivery boundaries.",
            detail={"blocked_fields": blocked_fields},
        )

    if str(payload.get("project_id") or "").strip() != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "Customer delivery/proof review is admitted only for the current Temp Power project.",
            detail={"expected_project_id": TEMP_POWER_PROJECT_ID, "project_id": payload.get("project_id")},
        )

    if str(payload.get("candidate_id") or "").strip() != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "Customer delivery/proof review is admitted only for the current Temp Power import candidate.",
            detail={"expected_candidate_id": TEMP_POWER_CANDIDATE_ID, "candidate_id": payload.get("candidate_id")},
        )

    if str(payload.get("source_fingerprint") or "").strip() != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "Customer delivery/proof review source_fingerprint must match the current admitted Temp Power source.",
            detail={
                "expected_source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
                "source_fingerprint": payload.get("source_fingerprint"),
            },
        )

    preview_review_id = str(payload.get("customer_preview_review_id") or "").strip()
    if not preview_review_id:
        return _invalid_payload_response(request, "customer_preview_review_id is required.")

    preview_artifact_lineage = payload.get("preview_artifact_lineage")
    if not isinstance(preview_artifact_lineage, list):
        return _invalid_payload_response(request, "preview_artifact_lineage must be an array.")
    normalized_lineage = _string_list(preview_artifact_lineage)
    if not normalized_lineage:
        return _invalid_payload_response(request, "preview_artifact_lineage must contain at least one preview artifact ref.")

    lineage_matches, preview_review = _lineage_matches_preview_review(preview_review_id, normalized_lineage)
    if preview_review is None:
        return error_response(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="customer_preview_review_id must reference an existing Temp Power customer preview review.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"customer_preview_review_id": preview_review_id},
        )

    if not lineage_matches:
        return _invalid_payload_response(
            request,
            "preview_artifact_lineage must match the canonical preview-review lineage.",
            detail={
                "customer_preview_review_id": preview_review_id,
                "expected_preview_artifact_lineage": _string_list(preview_review.get("preview_artifact_refs")),
                "preview_artifact_lineage": normalized_lineage,
            },
        )

    if str(preview_review.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "customer_preview_review_id must belong to the current Temp Power project.",
            detail={"customer_preview_review_id": preview_review_id, "preview_review_project_id": preview_review.get("project_id")},
        )

    if str(preview_review.get("candidate_id") or "") != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "customer_preview_review_id must belong to the current Temp Power import candidate.",
            detail={"customer_preview_review_id": preview_review_id, "preview_review_candidate_id": preview_review.get("candidate_id")},
        )

    if str(preview_review.get("source_fingerprint") or "") != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "customer_preview_review_id must reference the current admitted Temp Power source fingerprint.",
            detail={"customer_preview_review_id": preview_review_id, "preview_review_source_fingerprint": preview_review.get("source_fingerprint")},
        )

    customer_delivery_event_id = str(payload.get("customer_delivery_event_id") or "").strip()
    if not customer_delivery_event_id:
        return _invalid_payload_response(request, "customer_delivery_event_id is required.")

    if not str(payload.get("named_recipient_name") or "").strip():
        return _invalid_payload_response(request, "named_recipient_name is required.")
    if not str(payload.get("named_recipient_role") or "").strip():
        return _invalid_payload_response(request, "named_recipient_role is required.")

    delivery_channel = str(payload.get("delivery_channel") or "").strip()
    if delivery_channel not in ALLOWED_DELIVERY_CHANNELS:
        return _invalid_payload_response(
            request,
            "delivery_channel must be one of the admitted delivery/proof review values.",
            detail={"allowed_values": sorted(ALLOWED_DELIVERY_CHANNELS), "delivery_channel": delivery_channel},
        )

    delivery_artifact_refs = payload.get("delivery_artifact_refs")
    if not isinstance(delivery_artifact_refs, list):
        return _invalid_payload_response(request, "delivery_artifact_refs must be an array.")
    if not _string_list(delivery_artifact_refs):
        return _invalid_payload_response(request, "delivery_artifact_refs must contain at least one delivery artifact ref.")

    if not str(payload.get("delivered_at_utc") or "").strip():
        return _invalid_payload_response(request, "delivered_at_utc is required.")

    delivery_proof_recorded = bool(payload.get("delivery_proof_recorded"))
    delivery_proof_type = str(payload.get("delivery_proof_type") or "").strip()
    delivery_proof_ref = str(payload.get("delivery_proof_ref") or "").strip()
    if delivery_proof_recorded and (not delivery_proof_type or not delivery_proof_ref):
        return _invalid_payload_response(
            request,
            "delivery_proof_recorded may be true only when delivery_proof_type and delivery_proof_ref are present.",
        )

    if not str(payload.get("pm_delivery_approval_status") or "").strip():
        return _invalid_payload_response(request, "pm_delivery_approval_status is required.")
    if not str(payload.get("pm_delivery_approval_note") or "").strip():
        return _invalid_payload_response(request, "pm_delivery_approval_note is required.")
    if not str(payload.get("delivery_note") or "").strip():
        return _invalid_payload_response(request, "delivery_note is required.")

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
        entity_id=str(record["customer_delivery_proof_review_id"]),
        entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
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
        "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
        "entity_id": record["customer_delivery_proof_review_id"],
        "action_type": request.action_type,
        "from_state": {},
        "to_state": dict(record),
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": record["created_at"],
    }


def classify_temp_power_customer_delivery_proof_review_record(
    record: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not record:
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "customer_preview_review_id": None,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "preview_review_lineage_match": False,
            "status": "no_customer_delivery_proof_review_record",
            "record_count": 0,
            "latest_customer_delivery_proof_review_id": None,
            "latest_reviewed_at": None,
            "customer_delivery_event_id": None,
            "delivery_channel": None,
            "delivery_artifact_count": 0,
            "delivered_at_utc": None,
            "named_recipient_name": None,
            "named_recipient_role": None,
            "delivery_proof_type": None,
            "delivery_proof_ref": None,
            "delivery_proof_recorded": False,
            "proof_recorded_at_utc": None,
            "pm_delivery_approval_status": None,
            "pm_actor": None,
            "pm_reviewed_at": None,
            "storage_route_registered": True,
            "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            "finance_export_recorded": False,
            "source_writeback_recorded": False,
            "customer_billing_delivery_recorded": False,
        }

    current_candidate_match = (
        str(record.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(record.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
    )
    current_source_fingerprint_match = str(record.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
    preview_review_lineage_match, _ = _lineage_matches_preview_review(
        str(record.get("customer_preview_review_id") or "").strip(),
        _string_list(record.get("preview_artifact_lineage")),
    )
    pm_delivery_approval_status = str(record.get("pm_delivery_approval_status") or "")

    if not current_candidate_match or not current_source_fingerprint_match:
        status = "customer_delivery_proof_review_recorded_stale_source"
    elif not preview_review_lineage_match:
        status = "customer_delivery_proof_review_lineage_mismatch"
    elif pm_delivery_approval_status in FOLLOWUP_PM_DELIVERY_APPROVAL_STATUSES:
        status = "customer_delivery_proof_pending_pm_followup"
    else:
        status = "customer_delivery_proof_review_recorded_current_match"

    return {
        "project_id": record.get("project_id"),
        "candidate_id": record.get("candidate_id"),
        "source_fingerprint": record.get("source_fingerprint"),
        "customer_preview_review_id": record.get("customer_preview_review_id"),
        "current_candidate_match": current_candidate_match,
        "current_source_fingerprint_match": current_source_fingerprint_match,
        "preview_review_lineage_match": preview_review_lineage_match,
        "status": status,
        "record_count": 0,
        "latest_customer_delivery_proof_review_id": record.get("customer_delivery_proof_review_id"),
        "latest_reviewed_at": record.get("pm_reviewed_at"),
        "customer_delivery_event_id": record.get("customer_delivery_event_id"),
        "delivery_channel": record.get("delivery_channel"),
        "delivery_artifact_count": len(_string_list(record.get("delivery_artifact_refs"))),
        "delivered_at_utc": record.get("delivered_at_utc"),
        "named_recipient_name": record.get("named_recipient_name"),
        "named_recipient_role": record.get("named_recipient_role"),
        "delivery_proof_type": record.get("delivery_proof_type"),
        "delivery_proof_ref": record.get("delivery_proof_ref"),
        "delivery_proof_recorded": bool(record.get("delivery_proof_recorded")),
        "proof_recorded_at_utc": record.get("proof_recorded_at_utc"),
        "pm_delivery_approval_status": record.get("pm_delivery_approval_status"),
        "pm_actor": record.get("pm_actor"),
        "pm_reviewed_at": record.get("pm_reviewed_at"),
        "storage_route_registered": True,
        "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_SOURCE,
        "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
        "finance_export_recorded": False,
        "source_writeback_recorded": False,
        "customer_billing_delivery_recorded": False,
    }


def load_temp_power_customer_delivery_proof_review_status() -> Dict[str, Any]:
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
            "customer_preview_review_id": None,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "preview_review_lineage_match": False,
            "status": "customer_delivery_proof_review_storage_unavailable",
            "record_count": 0,
            "latest_customer_delivery_proof_review_id": None,
            "latest_reviewed_at": None,
            "storage_route_registered": False,
            "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            "storage_available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "finance_export_recorded": False,
            "source_writeback_recorded": False,
            "customer_billing_delivery_recorded": False,
            "delivery_proof_recorded": False,
            "proof_recorded_at_utc": None,
        }

    rows.sort(key=lambda row: str(row.get("pm_reviewed_at") or row.get("created_at") or ""), reverse=True)
    current = rows[0] if rows else None
    status = classify_temp_power_customer_delivery_proof_review_record(current)
    status["record_count"] = len(rows)
    status["storage_available"] = True
    return status


async def persist_temp_power_customer_delivery_proof_review(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown customer delivery/proof review action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Temp Power customer delivery/proof review persistence cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Temp Power customer delivery/proof review persistence requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Temp Power customer delivery/proof review records.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the current Temp Power project.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Customer delivery/proof review payload is required.")

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

    review_id = build_temp_power_customer_delivery_proof_review_id(request.payload)
    if request.entity_id and request.entity_id != review_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the deterministic customer delivery/proof review id when provided.",
            detail={"expected_entity_id": review_id, "provided_entity_id": request.entity_id},
        )

    payload_error = _validate_payload(request)
    if payload_error:
        return payload_error

    records = _records()
    existing = dict(records.get(review_id)) if review_id in records else None
    reviewed_at = str(existing.get("pm_reviewed_at")) if existing else _server_timestamp()
    proof_recorded_at = None
    if bool(request.payload.get("delivery_proof_recorded")):
        proof_recorded_at = str(existing.get("proof_recorded_at_utc")) if existing else reviewed_at
    normalized_payload = _normalize_payload(request.payload, actor, reviewed_at, proof_recorded_at)

    if existing:
        existing_payload = existing.get("review_payload") or {}
        if not _payloads_match(normalized_payload, existing_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Idempotent replay payload does not match the stored customer delivery/proof review record.",
                entity_id=review_id,
                entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"customer_delivery_proof_review_id": review_id},
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
        "customer_delivery_proof_review_id": review_id,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "project_id": normalized_payload["project_id"],
        "candidate_id": normalized_payload["candidate_id"],
        "source_fingerprint": normalized_payload["source_fingerprint"],
        "customer_preview_review_id": normalized_payload["customer_preview_review_id"],
        "customer_delivery_event_id": normalized_payload["customer_delivery_event_id"],
        "preview_artifact_lineage": list(normalized_payload["preview_artifact_lineage"]),
        "named_recipient_name": normalized_payload["named_recipient_name"],
        "named_recipient_role": normalized_payload["named_recipient_role"],
        "delivery_channel": normalized_payload["delivery_channel"],
        "delivery_artifact_refs": list(normalized_payload["delivery_artifact_refs"]),
        "delivered_at_utc": normalized_payload["delivered_at_utc"],
        "delivery_note": normalized_payload["delivery_note"],
        "delivery_proof_type": normalized_payload["delivery_proof_type"],
        "delivery_proof_ref": normalized_payload["delivery_proof_ref"],
        "delivery_proof_recorded": bool(normalized_payload["delivery_proof_recorded"]),
        "proof_recorded_at_utc": normalized_payload["proof_recorded_at_utc"],
        "pm_delivery_approval_status": normalized_payload["pm_delivery_approval_status"],
        "pm_delivery_approval_note": normalized_payload["pm_delivery_approval_note"],
        "pm_actor": actor.actor_id,
        "pm_actor_role": actor.actor_role,
        "pm_reviewed_at": reviewed_at,
        "review_storage_status": "accepted_for_review_storage",
        "idempotency_key": normalized_payload["idempotency_key"],
        "finance_export_recorded": False,
        "source_writeback_recorded": False,
        "customer_billing_delivery_recorded": False,
        "route": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ROUTE,
        "status_route": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_ROUTE,
        "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_STATUS_SOURCE,
        "persistence_version": TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_PERSISTENCE_VERSION,
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
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_PROOF_REVIEW_ENTITY_TYPE,
        )

    return _response(
        status="accepted",
        mutation_id=mutation_id,
        record=record,
        action_type=request.action_type,
        audit_event_id=audit_event_id,
    )