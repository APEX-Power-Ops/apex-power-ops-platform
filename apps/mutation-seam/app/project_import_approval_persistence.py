from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.db.memory_store import store
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.project_import_approval_contract import (
    load_project_import_approval_contract,
    validate_project_import_approval_payload,
)


APPROVAL_ENTITY_TYPE = "pm_import_candidate_approval"
APPROVAL_ACTION_TYPE = "persist_import_approval"
APPROVAL_ROUTE = "/api/v1/mutations/project-import-approvals"
APPROVAL_PERSISTENCE_VERSION = "pm_import_approval_persistence_v1"
APPROVAL_STATUS_SOURCE = "seam.pm_import_candidate_approvals"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def build_project_import_approval_record_id(payload: Mapping[str, Any]) -> str:
    identity = {
        "candidate_id": payload.get("candidate_id"),
        "candidate_version": payload.get("candidate_version"),
        "source_stat_fingerprint": payload.get("source_stat_fingerprint"),
        "candidate_shape_fingerprint": payload.get("candidate_shape_fingerprint"),
        "idempotency_key": payload.get("idempotency_key"),
    }
    return f"pm-import-approval-{_stable_hash(identity)}"


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _approval_records():
    if not hasattr(store, "pm_import_candidate_approvals"):
        store.pm_import_candidate_approvals = {}
    return store.pm_import_candidate_approvals


def _get_existing_record(approval_record_id: str) -> Optional[Dict[str, Any]]:
    records = _approval_records()
    if approval_record_id not in records:
        return None
    return dict(records[approval_record_id])


def _insert_record(record: Dict[str, Any]) -> None:
    records = _approval_records()
    if hasattr(records, "insert"):
        records.insert(record)
    else:
        records[record["approval_record_id"]] = record


def _normalize_payload(
    payload: Mapping[str, Any],
    actor: Actor,
    approved_at_utc: str,
) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["approved_by_actor_id"] = actor.actor_id
    normalized["approved_at_utc"] = approved_at_utc
    normalized["accepted_warning_codes"] = sorted(str(code) for code in normalized.get("accepted_warning_codes") or [])
    normalized["accepted_no_go_overrides"] = sorted(str(check_id) for check_id in normalized.get("accepted_no_go_overrides") or [])
    return normalized


def _payloads_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _stable_json(left) == _stable_json(right)


def _sorted_strings(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value) for value in values)
    return sorted(str(value) for value in [values])


def _current_mismatches(record: Mapping[str, Any], contract: Mapping[str, Any]) -> list[Dict[str, Any]]:
    expected = contract.get("minimum_expected_values") or {}
    checks = [
        "candidate_id",
        "candidate_version",
        "source_stat_fingerprint",
        "candidate_shape_fingerprint",
        "idempotency_key",
    ]
    mismatches = []
    for field in checks:
        if record.get(field) != expected.get(field):
            mismatches.append(
                {
                    "field": field,
                    "record_value": record.get(field),
                    "expected_value": expected.get(field),
                }
            )

    list_checks = [
        "accepted_warning_codes",
        "accepted_no_go_overrides",
    ]
    for field in list_checks:
        if _sorted_strings(record.get(field)) != _sorted_strings(expected.get(field)):
            mismatches.append(
                {
                    "field": field,
                    "record_value": _sorted_strings(record.get(field)),
                    "expected_value": _sorted_strings(expected.get(field)),
                }
            )
    return mismatches


def classify_project_import_approval_record(
    record: Optional[Mapping[str, Any]],
    contract: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    active_contract = contract or load_project_import_approval_contract()
    if not record:
        return {
            "classification": "no_approval_record",
            "current_candidate_match": False,
            "candidate_id": active_contract.get("candidate_id"),
            "candidate_version": active_contract.get("candidate_version"),
            "source": APPROVAL_STATUS_SOURCE,
            "audit_log_used_for_current_status": False,
            "import_authority": "not_admitted",
        }

    mismatches = _current_mismatches(record, active_contract)
    decision = str(record.get("decision") or "")
    if mismatches:
        classification = "stale_approval_record"
    elif decision == "approve_for_import_packet":
        classification = "approved_for_import_packet"
    elif decision == "return_for_revision":
        classification = "returned_for_revision"
    elif decision == "reject_candidate":
        classification = "rejected_candidate"
    else:
        classification = "unsupported_decision"

    return {
        "classification": classification,
        "current_candidate_match": not mismatches,
        "candidate_id": record.get("candidate_id"),
        "candidate_version": record.get("candidate_version"),
        "approval_record_id": record.get("approval_record_id"),
        "decision": decision,
        "mutation_id": record.get("mutation_id"),
        "audit_event_id": record.get("audit_event_id"),
        "stale_fields": [mismatch["field"] for mismatch in mismatches],
        "mismatches": mismatches,
        "source": APPROVAL_STATUS_SOURCE,
        "audit_log_used_for_current_status": False,
        "import_authority": record.get("import_authority") or "not_admitted",
    }


def load_project_import_approval_status() -> Dict[str, Any]:
    contract = load_project_import_approval_contract()
    expected = contract.get("minimum_expected_values") or {}
    records = [
        dict(record)
        for record in _approval_records().values()
        if record.get("candidate_id") == expected.get("candidate_id")
    ]
    records.sort(key=lambda record: str(record.get("created_at") or ""), reverse=True)
    selected = records[0] if records else None
    status = classify_project_import_approval_record(selected, contract)
    status["approval_record_count_for_candidate"] = len(records)
    return status


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or "unknown",
        entity_type=APPROVAL_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _approval_response(
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
        entity_id=str(record["approval_record_id"]),
        entity_type=APPROVAL_ENTITY_TYPE,
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
        "entity_type": APPROVAL_ENTITY_TYPE,
        "entity_id": record["approval_record_id"],
        "action_type": request.action_type,
        "from_state": {},
        "to_state": dict(record),
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": record["created_at"],
    }


async def persist_project_import_approval(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != APPROVAL_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown action type for {APPROVAL_ENTITY_TYPE}: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Project import approval persistence cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=APPROVAL_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Project import approval persistence requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=APPROVAL_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Project Miner import approval records.",
            entity_id=request.entity_id or "unknown",
            entity_type=APPROVAL_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Approval persistence payload is required.")

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

    approval_record_id = build_project_import_approval_record_id(request.payload)
    if request.entity_id and request.entity_id != approval_record_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the deterministic approval_record_id when provided.",
            detail={"expected_entity_id": approval_record_id, "provided_entity_id": request.entity_id},
        )

    contract = load_project_import_approval_contract()
    existing = _get_existing_record(approval_record_id)
    approved_at_utc = str(existing.get("approved_at_utc")) if existing else _server_timestamp()
    normalized_payload = _normalize_payload(request.payload, actor, approved_at_utc)
    validation_result = validate_project_import_approval_payload(normalized_payload, contract)
    if not validation_result["valid"]:
        return _invalid_payload_response(
            request,
            "Approval persistence payload failed validation.",
            detail={"validation_result": validation_result},
        )

    if existing:
        existing_payload = existing.get("approval_payload") or {}
        if not _payloads_match(normalized_payload, existing_payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Idempotent replay payload does not match the stored approval record.",
                entity_id=approval_record_id,
                entity_type=APPROVAL_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"approval_record_id": approval_record_id},
            )
        return _approval_response(
            status="idempotent_hit",
            mutation_id=str(existing.get("mutation_id") or f"mut-{uuid4()}"),
            record=existing,
            action_type=request.action_type,
            audit_event_id=str(existing.get("audit_event_id") or "") or None,
        )

    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    record = {
        "approval_record_id": approval_record_id,
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "candidate_id": normalized_payload["candidate_id"],
        "candidate_version": normalized_payload["candidate_version"],
        "source_stat_fingerprint": normalized_payload["source_stat_fingerprint"],
        "candidate_shape_fingerprint": normalized_payload["candidate_shape_fingerprint"],
        "idempotency_key": normalized_payload["idempotency_key"],
        "decision": normalized_payload["decision"],
        "approved_by_actor_id": normalized_payload["approved_by_actor_id"],
        "approved_at_utc": normalized_payload["approved_at_utc"],
        "accepted_warning_codes": list(normalized_payload["accepted_warning_codes"]),
        "accepted_no_go_overrides": list(normalized_payload["accepted_no_go_overrides"]),
        "review_notes": str(normalized_payload["review_notes"]).strip(),
        "approval_payload": normalized_payload,
        "validation_result": validation_result,
        "created_at": approved_at_utc,
        "persistence_version": APPROVAL_PERSISTENCE_VERSION,
        "route": APPROVAL_ROUTE,
        "import_authority": "not_admitted",
    }
    audit_request = request.model_copy(update={"entity_id": approval_record_id, "payload": record})
    audit_event = _build_audit_event(
        actor=actor,
        request=audit_request,
        record=record,
        mutation_id=mutation_id,
        audit_event_id=audit_event_id,
    )
    records = _approval_records()
    if hasattr(records, "insert_with_audit"):
        records.insert_with_audit(record, audit_event)
    else:
        _insert_record(record)
        record_audit_event(
            actor=actor,
            request=audit_request,
            from_state={},
            to_state=record,
            mutation_id=mutation_id,
            event_id=audit_event_id,
            entity_type=APPROVAL_ENTITY_TYPE,
        )
        records[approval_record_id] = record

    return _approval_response(
        status="accepted",
        mutation_id=mutation_id,
        record=record,
        action_type=request.action_type,
        audit_event_id=audit_event_id,
    )
