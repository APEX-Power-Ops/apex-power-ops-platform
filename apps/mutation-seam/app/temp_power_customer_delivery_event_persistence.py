from __future__ import annotations

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
from app.temp_power_customer_preview_review_persistence import _ensure_customer_preview_review_schema


TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE = "pm_customer_delivery_event"
TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ACTION_TYPE = "persist_temp_power_customer_delivery_event"
TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ROUTE = "/api/v1/mutations/temp-power-customer-delivery-events"
TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_ROUTE = "/api/v1/reads/temp-power-customer-delivery-event-status"
TEMP_POWER_CUSTOMER_DELIVERY_EVENT_PERSISTENCE_VERSION = "pm_lane_347_customer_delivery_event_v1"
TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_SOURCE = "seam.pm_customer_delivery_events"
LANE_347_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "011_pm_lane_347_customer_delivery_events.sql"
)
_SCHEMA_READY = False

TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
TEMP_POWER_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
TEMP_POWER_SOURCE_FINGERPRINT = "e111fdbe934bf9de07ed24c1"

ALLOWED_DELIVERY_CHANNELS = {"CONTROLLED_EMAIL", "LATER_APPROVED_PORTAL"}
ALLOWED_EXECUTION_METHODS = {
    "CONTROLLED_EMAIL_OPERATOR_SEND": "CONTROLLED_EMAIL",
    "LATER_APPROVED_PORTAL_OPERATOR_RELEASE": "LATER_APPROVED_PORTAL",
}
REQUIRED_CUSTOMER_DELIVERY_STATUS = "DELIVERED_AND_PROOF_ATTACHED"
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


def _ensure_customer_delivery_event_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY or os.getenv("SEAM_STORE_BACKEND") == "memory":
        return
    if type(store).__name__ != "SupabaseStore":
        _SCHEMA_READY = True
        return

    from app.db.supabase_store import _conn_get

    with _conn_get().cursor() as cur:
        cur.execute("SELECT to_regclass('seam.pm_customer_delivery_events') IS NOT NULL")
        exists = bool(cur.fetchone()[0])
        if not exists:
            cur.execute(LANE_347_MIGRATION_PATH.read_text(encoding="utf-8"))
    _SCHEMA_READY = True


def _records() -> Any:
    _ensure_customer_delivery_event_schema()
    if not hasattr(store, "temp_power_customer_delivery_events"):
        store.temp_power_customer_delivery_events = {}
    return store.temp_power_customer_delivery_events


def _values(collection: Any) -> list[Dict[str, Any]]:
    return [dict(row) for row in collection.values()]


def _string_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value).strip() for value in values if str(value).strip())
    value = str(values).strip()
    return [value] if value else []


def _preview_review_records() -> Any:
    _ensure_customer_preview_review_schema()
    if not hasattr(store, "temp_power_customer_preview_reviews"):
        return {}
    return store.temp_power_customer_preview_reviews


def _delivery_proof_review_records() -> Any:
    if not hasattr(store, "temp_power_customer_delivery_proof_reviews"):
        return {}
    return store.temp_power_customer_delivery_proof_reviews


def _preview_review_row(review_id: str) -> Optional[Dict[str, Any]]:
    rows = _preview_review_records()
    if review_id not in rows:
        return None
    return dict(rows[review_id])


def _delivery_proof_review_row(review_id: str) -> Optional[Dict[str, Any]]:
    rows = _delivery_proof_review_records()
    if review_id not in rows:
        return None
    return dict(rows[review_id])


def build_temp_power_customer_delivery_event_id(payload: Mapping[str, Any]) -> str:
    return str(payload.get("customer_delivery_event_id") or "").strip()


def _normalize_payload(payload: Mapping[str, Any], actor: Actor, pm_timestamp: str) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["project_id"] = str(normalized.get("project_id") or "").strip()
    normalized["candidate_id"] = str(normalized.get("candidate_id") or "").strip()
    normalized["source_fingerprint"] = str(normalized.get("source_fingerprint") or "").strip()
    normalized["customer_preview_review_id"] = str(normalized.get("customer_preview_review_id") or "").strip()
    normalized["customer_delivery_proof_review_id"] = str(normalized.get("customer_delivery_proof_review_id") or "").strip()
    normalized["customer_delivery_event_id"] = str(normalized.get("customer_delivery_event_id") or "").strip()
    normalized["named_recipient_name"] = str(normalized.get("named_recipient_name") or "").strip()
    normalized["named_recipient_role"] = str(normalized.get("named_recipient_role") or "").strip()
    normalized["delivery_channel"] = str(normalized.get("delivery_channel") or "").strip()
    normalized["delivery_artifact_refs"] = _string_list(normalized.get("delivery_artifact_refs"))
    normalized["delivered_at_utc"] = str(normalized.get("delivered_at_utc") or "").strip()
    normalized["execution_method"] = str(normalized.get("execution_method") or "").strip()
    normalized["delivery_proof_type"] = str(normalized.get("delivery_proof_type") or "").strip()
    normalized["delivery_proof_ref"] = str(normalized.get("delivery_proof_ref") or "").strip()
    normalized["customer_delivery_status"] = str(normalized.get("customer_delivery_status") or "").strip()
    normalized["execution_note"] = str(normalized.get("execution_note") or "").strip()
    normalized["proof_recorded_at_utc"] = str(normalized.get("proof_recorded_at_utc") or "").strip()
    normalized["idempotency_key"] = str(normalized.get("idempotency_key") or "").strip()
    normalized["pm_actor"] = actor.actor_id
    normalized["pm_actor_role"] = actor.actor_role
    normalized["pm_timestamp"] = pm_timestamp
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
        entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
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


def _validate_payload(request: MutationRequest) -> Optional[MutationResponse]:
    payload = request.payload or {}
    required_fields = {
        "idempotency_key",
        "project_id",
        "candidate_id",
        "source_fingerprint",
        "customer_preview_review_id",
        "customer_delivery_proof_review_id",
        "customer_delivery_event_id",
        "named_recipient_name",
        "named_recipient_role",
        "delivery_channel",
        "delivery_artifact_refs",
        "delivered_at_utc",
        "execution_method",
        "delivery_proof_type",
        "delivery_proof_ref",
        "customer_delivery_status",
        "execution_note",
        "proof_recorded_at_utc",
    }
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        return _invalid_payload_response(
            request,
            "Customer-facing delivery execution payload is missing required fields.",
            detail={"missing_fields": missing},
        )

    blocked_fields = _blocked_payload_fields(payload)
    if blocked_fields:
        return _invalid_payload_response(
            request,
            "Customer-facing delivery execution payload may not widen finance, source-writeback, or customer-billing-delivery boundaries.",
            detail={"blocked_fields": blocked_fields},
        )

    if str(payload.get("project_id") or "").strip() != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "Customer-facing delivery execution is admitted only for the current Temp Power project.",
            detail={"expected_project_id": TEMP_POWER_PROJECT_ID, "project_id": payload.get("project_id")},
        )

    if str(payload.get("candidate_id") or "").strip() != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "Customer-facing delivery execution is admitted only for the current Temp Power import candidate.",
            detail={"expected_candidate_id": TEMP_POWER_CANDIDATE_ID, "candidate_id": payload.get("candidate_id")},
        )

    if str(payload.get("source_fingerprint") or "").strip() != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "Customer-facing delivery execution source_fingerprint must match the current admitted Temp Power source.",
            detail={
                "expected_source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
                "source_fingerprint": payload.get("source_fingerprint"),
            },
        )

    preview_review_id = str(payload.get("customer_preview_review_id") or "").strip()
    if not preview_review_id:
        return _invalid_payload_response(request, "customer_preview_review_id is required.")

    proof_review_id = str(payload.get("customer_delivery_proof_review_id") or "").strip()
    if not proof_review_id:
        return _invalid_payload_response(request, "customer_delivery_proof_review_id is required.")

    event_id = str(payload.get("customer_delivery_event_id") or "").strip()
    if not event_id:
        return _invalid_payload_response(request, "customer_delivery_event_id is required.")

    preview_review = _preview_review_row(preview_review_id)
    if preview_review is None:
        return error_response(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="customer_preview_review_id must reference an existing Temp Power customer preview review.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"customer_preview_review_id": preview_review_id},
        )

    proof_review = _delivery_proof_review_row(proof_review_id)
    if proof_review is None:
        return error_response(
            code=ErrorCode.ENTITY_NOT_FOUND,
            message="customer_delivery_proof_review_id must reference an existing Temp Power delivery/proof review record.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"customer_delivery_proof_review_id": proof_review_id},
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

    if str(proof_review.get("project_id") or "") != TEMP_POWER_PROJECT_ID:
        return _invalid_payload_response(
            request,
            "customer_delivery_proof_review_id must belong to the current Temp Power project.",
            detail={
                "customer_delivery_proof_review_id": proof_review_id,
                "delivery_proof_review_project_id": proof_review.get("project_id"),
            },
        )

    if str(proof_review.get("candidate_id") or "") != TEMP_POWER_CANDIDATE_ID:
        return _invalid_payload_response(
            request,
            "customer_delivery_proof_review_id must belong to the current Temp Power import candidate.",
            detail={
                "customer_delivery_proof_review_id": proof_review_id,
                "delivery_proof_review_candidate_id": proof_review.get("candidate_id"),
            },
        )

    if str(proof_review.get("source_fingerprint") or "") != TEMP_POWER_SOURCE_FINGERPRINT:
        return _invalid_payload_response(
            request,
            "customer_delivery_proof_review_id must reference the current admitted Temp Power source fingerprint.",
            detail={
                "customer_delivery_proof_review_id": proof_review_id,
                "delivery_proof_review_source_fingerprint": proof_review.get("source_fingerprint"),
            },
        )

    if str(proof_review.get("customer_preview_review_id") or "") != preview_review_id:
        return _invalid_payload_response(
            request,
            "customer_delivery_proof_review_id must reference the same canonical customer preview review.",
            detail={
                "customer_preview_review_id": preview_review_id,
                "delivery_proof_review_customer_preview_review_id": proof_review.get("customer_preview_review_id"),
            },
        )

    if str(proof_review.get("customer_delivery_event_id") or "") != event_id:
        return _invalid_payload_response(
            request,
            "customer_delivery_event_id must match the reviewed event identity from the delivery/proof review row.",
            detail={
                "customer_delivery_event_id": event_id,
                "reviewed_customer_delivery_event_id": proof_review.get("customer_delivery_event_id"),
            },
        )

    if str(payload.get("named_recipient_name") or "").strip() != str(proof_review.get("named_recipient_name") or "").strip():
        return _invalid_payload_response(
            request,
            "named_recipient_name must match the linked delivery/proof review.",
        )

    if str(payload.get("named_recipient_role") or "").strip() != str(proof_review.get("named_recipient_role") or "").strip():
        return _invalid_payload_response(
            request,
            "named_recipient_role must match the linked delivery/proof review.",
        )

    delivery_channel = str(payload.get("delivery_channel") or "").strip()
    if delivery_channel not in ALLOWED_DELIVERY_CHANNELS:
        return _invalid_payload_response(
            request,
            "delivery_channel must be one of the admitted customer-facing delivery values.",
            detail={"allowed_values": sorted(ALLOWED_DELIVERY_CHANNELS), "delivery_channel": delivery_channel},
        )

    execution_method = str(payload.get("execution_method") or "").strip()
    if execution_method not in ALLOWED_EXECUTION_METHODS:
        return _invalid_payload_response(
            request,
            "execution_method must be one of the admitted orchestration execution methods.",
            detail={"allowed_values": sorted(ALLOWED_EXECUTION_METHODS), "execution_method": execution_method},
        )

    if ALLOWED_EXECUTION_METHODS[execution_method] != delivery_channel:
        return _invalid_payload_response(
            request,
            "execution_method must be compatible with the selected delivery_channel.",
            detail={"execution_method": execution_method, "delivery_channel": delivery_channel},
        )

    if str(proof_review.get("delivery_channel") or "").strip() != delivery_channel:
        return _invalid_payload_response(
            request,
            "delivery_channel must match the linked delivery/proof review.",
        )

    delivery_artifact_refs = payload.get("delivery_artifact_refs")
    if not isinstance(delivery_artifact_refs, list):
        return _invalid_payload_response(request, "delivery_artifact_refs must be an array.")
    normalized_artifact_refs = _string_list(delivery_artifact_refs)
    if not normalized_artifact_refs:
        return _invalid_payload_response(request, "delivery_artifact_refs must contain at least one delivery artifact ref.")
    if normalized_artifact_refs != _string_list(proof_review.get("delivery_artifact_refs")):
        return _invalid_payload_response(
            request,
            "delivery_artifact_refs must match the linked delivery/proof review.",
        )

    if not str(payload.get("delivered_at_utc") or "").strip():
        return _invalid_payload_response(request, "delivered_at_utc is required.")

    delivery_proof_type = str(payload.get("delivery_proof_type") or "").strip()
    if not delivery_proof_type:
        return _invalid_payload_response(request, "delivery_proof_type is required.")
    if delivery_proof_type != str(proof_review.get("delivery_proof_type") or "").strip():
        return _invalid_payload_response(
            request,
            "delivery_proof_type must match the linked delivery/proof review.",
        )

    delivery_proof_ref = str(payload.get("delivery_proof_ref") or "").strip()
    if not delivery_proof_ref:
        return _invalid_payload_response(request, "delivery_proof_ref is required.")
    if delivery_proof_ref != str(proof_review.get("delivery_proof_ref") or "").strip():
        return _invalid_payload_response(
            request,
            "delivery_proof_ref must match the linked delivery/proof review.",
        )

    customer_delivery_status = str(payload.get("customer_delivery_status") or "").strip()
    if customer_delivery_status != REQUIRED_CUSTOMER_DELIVERY_STATUS:
        return _invalid_payload_response(
            request,
            "customer_delivery_status must stay within the admitted bounded execution value.",
            detail={"required_status": REQUIRED_CUSTOMER_DELIVERY_STATUS, "customer_delivery_status": customer_delivery_status},
        )

    if not str(payload.get("execution_note") or "").strip():
        return _invalid_payload_response(request, "execution_note is required.")

    if not str(payload.get("proof_recorded_at_utc") or "").strip():
        return _invalid_payload_response(
            request,
            "proof_recorded_at_utc is required when customer delivery execution is claimed.",
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
        entity_id=str(record["customer_delivery_event_id"]),
        entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
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
        "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
        "entity_id": record["customer_delivery_event_id"],
        "action_type": request.action_type,
        "from_state": {},
        "to_state": dict(record),
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": record["created_at"],
    }


def classify_temp_power_customer_delivery_event_record(
    record: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not record:
        return {
            "project_id": TEMP_POWER_PROJECT_ID,
            "candidate_id": TEMP_POWER_CANDIDATE_ID,
            "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
            "customer_preview_review_id": None,
            "customer_delivery_proof_review_id": None,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "preview_review_lineage_match": False,
            "delivery_proof_review_lineage_match": False,
            "status": "no_customer_delivery_event_record",
            "record_count": 0,
            "latest_customer_delivery_event_id": None,
            "latest_delivered_at_utc": None,
            "latest_delivery_proof_type": None,
            "latest_delivery_proof_ref": None,
            "delivery_channel": None,
            "execution_method": None,
            "customer_delivery_status": None,
            "named_recipient_name": None,
            "named_recipient_role": None,
            "storage_route_registered": True,
            "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
            "customer_billing_delivery_authority": "not_admitted",
            "finance_export_recorded": False,
            "source_writeback_recorded": False,
            "customer_billing_delivery_recorded": False,
        }

    preview_review = _preview_review_row(str(record.get("customer_preview_review_id") or "").strip())
    proof_review = _delivery_proof_review_row(str(record.get("customer_delivery_proof_review_id") or "").strip())
    current_candidate_match = (
        str(record.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(record.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
    )
    current_source_fingerprint_match = str(record.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
    preview_review_lineage_match = bool(
        preview_review
        and str(preview_review.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(preview_review.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
        and str(preview_review.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
    )
    delivery_proof_review_lineage_match = bool(
        proof_review
        and str(proof_review.get("project_id") or "") == TEMP_POWER_PROJECT_ID
        and str(proof_review.get("candidate_id") or "") == TEMP_POWER_CANDIDATE_ID
        and str(proof_review.get("source_fingerprint") or "") == TEMP_POWER_SOURCE_FINGERPRINT
        and str(proof_review.get("customer_preview_review_id") or "") == str(record.get("customer_preview_review_id") or "")
        and str(proof_review.get("customer_delivery_event_id") or "") == str(record.get("customer_delivery_event_id") or "")
    )

    if not current_candidate_match or not current_source_fingerprint_match:
        status = "customer_delivery_event_recorded_stale_source"
    elif not preview_review_lineage_match:
        status = "customer_delivery_event_preview_review_lineage_mismatch"
    elif not delivery_proof_review_lineage_match:
        status = "customer_delivery_event_delivery_proof_review_lineage_mismatch"
    else:
        status = "customer_delivery_event_recorded_current_match"

    return {
        "project_id": record.get("project_id"),
        "candidate_id": record.get("candidate_id"),
        "source_fingerprint": record.get("source_fingerprint"),
        "customer_preview_review_id": record.get("customer_preview_review_id"),
        "customer_delivery_proof_review_id": record.get("customer_delivery_proof_review_id"),
        "current_candidate_match": current_candidate_match,
        "current_source_fingerprint_match": current_source_fingerprint_match,
        "preview_review_lineage_match": preview_review_lineage_match,
        "delivery_proof_review_lineage_match": delivery_proof_review_lineage_match,
        "status": status,
        "record_count": 0,
        "latest_customer_delivery_event_id": record.get("customer_delivery_event_id"),
        "latest_delivered_at_utc": record.get("delivered_at_utc"),
        "latest_delivery_proof_type": record.get("delivery_proof_type"),
        "latest_delivery_proof_ref": record.get("delivery_proof_ref"),
        "delivery_channel": record.get("delivery_channel"),
        "execution_method": record.get("execution_method"),
        "customer_delivery_status": record.get("customer_delivery_status"),
        "named_recipient_name": record.get("named_recipient_name"),
        "named_recipient_role": record.get("named_recipient_role"),
        "storage_route_registered": True,
        "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_SOURCE,
        "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
        "finance_authority": record.get("finance_authority") or "not_admitted",
        "source_writeback_authority": record.get("source_writeback_authority") or "not_admitted",
        "customer_billing_delivery_authority": record.get("customer_billing_delivery_authority") or "not_admitted",
        "finance_export_recorded": False,
        "source_writeback_recorded": False,
        "customer_billing_delivery_recorded": False,
    }


def load_temp_power_customer_delivery_event_status() -> Dict[str, Any]:
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
            "customer_delivery_proof_review_id": None,
            "current_candidate_match": False,
            "current_source_fingerprint_match": False,
            "preview_review_lineage_match": False,
            "delivery_proof_review_lineage_match": False,
            "status": "customer_delivery_event_storage_unavailable",
            "record_count": 0,
            "latest_customer_delivery_event_id": None,
            "latest_delivered_at_utc": None,
            "storage_route_registered": True,
            "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_SOURCE,
            "entity_type": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            "storage_available": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "finance_authority": "not_admitted",
            "source_writeback_authority": "not_admitted",
            "customer_billing_delivery_authority": "not_admitted",
            "finance_export_recorded": False,
            "source_writeback_recorded": False,
            "customer_billing_delivery_recorded": False,
        }

    rows.sort(key=lambda row: str(row.get("pm_timestamp") or row.get("created_at") or ""), reverse=True)
    current = rows[0] if rows else None
    status = classify_temp_power_customer_delivery_event_record(current)
    status["record_count"] = len(rows)
    status["storage_available"] = True
    return status


async def persist_temp_power_customer_delivery_event(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown customer-facing delivery execution action type: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Temp Power customer-facing delivery execution cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Temp Power customer-facing delivery execution requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Temp Power customer-facing delivery execution records.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not check_scope(actor, TEMP_POWER_PROJECT_ID):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include the current Temp Power project.",
            entity_id=request.entity_id or "unknown",
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"project_id": TEMP_POWER_PROJECT_ID, "actor_scope": actor.project_scope},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Customer-facing delivery execution payload is required.")

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

    event_id = build_temp_power_customer_delivery_event_id(request.payload)
    if request.entity_id and request.entity_id != event_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the canonical customer_delivery_event_id when provided.",
            detail={"expected_entity_id": event_id, "provided_entity_id": request.entity_id},
        )

    payload_error = _validate_payload(request)
    if payload_error:
        return payload_error

    records = _records()
    existing = dict(records.get(event_id)) if event_id in records else None
    pm_timestamp = str(existing.get("pm_timestamp")) if existing else _server_timestamp()
    normalized_payload = _normalize_payload(request.payload, actor, pm_timestamp)

    if existing:
        existing_payload = existing.get("execution_payload") or {}
        if not _payloads_match(normalized_payload, existing_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Idempotent replay payload does not match the stored customer-facing delivery execution record.",
                entity_id=event_id,
                entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"customer_delivery_event_id": event_id},
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
        "customer_delivery_event_id": event_id,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "project_id": normalized_payload["project_id"],
        "candidate_id": normalized_payload["candidate_id"],
        "source_fingerprint": normalized_payload["source_fingerprint"],
        "customer_preview_review_id": normalized_payload["customer_preview_review_id"],
        "customer_delivery_proof_review_id": normalized_payload["customer_delivery_proof_review_id"],
        "named_recipient_name": normalized_payload["named_recipient_name"],
        "named_recipient_role": normalized_payload["named_recipient_role"],
        "delivery_channel": normalized_payload["delivery_channel"],
        "delivery_artifact_refs": list(normalized_payload["delivery_artifact_refs"]),
        "delivered_at_utc": normalized_payload["delivered_at_utc"],
        "execution_method": normalized_payload["execution_method"],
        "delivery_proof_type": normalized_payload["delivery_proof_type"],
        "delivery_proof_ref": normalized_payload["delivery_proof_ref"],
        "customer_delivery_status": normalized_payload["customer_delivery_status"],
        "execution_note": normalized_payload["execution_note"],
        "proof_recorded_at_utc": normalized_payload["proof_recorded_at_utc"],
        "pm_actor": actor.actor_id,
        "pm_actor_role": actor.actor_role,
        "pm_timestamp": pm_timestamp,
        "execution_storage_status": "accepted_for_customer_delivery_event_storage",
        "idempotency_key": normalized_payload["idempotency_key"],
        "finance_export_recorded": False,
        "source_writeback_recorded": False,
        "customer_billing_delivery_recorded": False,
        "route": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ROUTE,
        "status_route": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_ROUTE,
        "storage_source": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_STATUS_SOURCE,
        "persistence_version": TEMP_POWER_CUSTOMER_DELIVERY_EVENT_PERSISTENCE_VERSION,
        "execution_payload": normalized_payload,
        "created_at": pm_timestamp,
    }
    audit_request = request.model_copy(update={"entity_id": event_id, "payload": record})
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
        records[event_id] = record
        record_audit_event(
            actor=actor,
            request=audit_request,
            from_state={},
            to_state=record,
            mutation_id=mutation_id,
            event_id=audit_event_id,
            entity_type=TEMP_POWER_CUSTOMER_DELIVERY_EVENT_ENTITY_TYPE,
        )

    return _response(
        status="accepted",
        mutation_id=mutation_id,
        record=record,
        action_type=request.action_type,
        audit_event_id=audit_event_id,
    )