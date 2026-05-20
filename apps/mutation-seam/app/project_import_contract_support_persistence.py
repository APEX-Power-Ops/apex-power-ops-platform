from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from typing import Any, Mapping

from fastapi import HTTPException, status

from app.auth.jwt import Actor
from app.contract_support_response_fixtures import (
    CONTRACT_SUPPORT_RESPONSE_CONFLICT_DUPLICATE_BUSINESS_PAYLOAD,
    CONTRACT_SUPPORT_RESPONSE_IDEMPOTENT_HIT,
    CONTRACT_SUPPORT_RESPONSE_READBACK_COUNTS_MISMATCH,
    CONTRACT_SUPPORT_RESPONSE_READBACK_MISSING,
    CONTRACT_SUPPORT_RESPONSE_READBACK_READY,
    CONTRACT_SUPPORT_RESPONSE_READBACK_STALE_CANDIDATE,
    CONTRACT_SUPPORT_RESPONSE_READBACK_UNAVAILABLE,
    CONTRACT_SUPPORT_RESPONSE_ROLLBACK_APPARATUS_FINANCIAL_VALIDATION_FAILED,
    CONTRACT_SUPPORT_RESPONSE_ROLLBACK_AUDIT_WRITE_UNAVAILABLE,
    CONTRACT_SUPPORT_RESPONSE_ROLLBACK_IDEMPOTENCY_WRITE_UNAVAILABLE,
    CONTRACT_SUPPORT_RESPONSE_ROLLBACK_SCOPE_DETAIL_CONFLICT,
    CONTRACT_SUPPORT_RESPONSE_SUCCESS_FIRST_WRITE,
)
from app.project_import_contract_support_models import ProjectImportContractSupportReadbackQuery


CONTRACT_SUPPORT_ENTITY_TYPE = "pm_project_import_contract_support"
CONTRACT_SUPPORT_ACTION_TYPE = "persist_project_import_contract_support"
CONTRACT_SUPPORT_WRITE_ROUTE = "/api/v1/mutations/project-import-contract-support"
CONTRACT_SUPPORT_READ_ROUTE = "/api/v1/reads/project-import-contract-support-status"
CONTRACT_SUPPORT_ALLOWED_ROLES = {"pm", "operations"}
CONTRACT_SUPPORT_FLAG = "LANE_412_DRY_RUN_ENABLED"
CONTRACT_SUPPORT_RUNTIME_FIELD_ROLE = "task_lead"

_FORCE_FAILURE_FIXTURES = {
    "scope_detail_conflict": CONTRACT_SUPPORT_RESPONSE_ROLLBACK_SCOPE_DETAIL_CONFLICT,
    "apparatus_financial_validation_failed": CONTRACT_SUPPORT_RESPONSE_ROLLBACK_APPARATUS_FINANCIAL_VALIDATION_FAILED,
    "audit_write_unavailable": CONTRACT_SUPPORT_RESPONSE_ROLLBACK_AUDIT_WRITE_UNAVAILABLE,
    "idempotency_write_unavailable": CONTRACT_SUPPORT_RESPONSE_ROLLBACK_IDEMPOTENCY_WRITE_UNAVAILABLE,
}

_READBACK_FIXTURES = {
    "missing": CONTRACT_SUPPORT_RESPONSE_READBACK_MISSING,
    "ready": CONTRACT_SUPPORT_RESPONSE_READBACK_READY,
    "stale_candidate": CONTRACT_SUPPORT_RESPONSE_READBACK_STALE_CANDIDATE,
    "counts_mismatch": CONTRACT_SUPPORT_RESPONSE_READBACK_COUNTS_MISMATCH,
    "unavailable": CONTRACT_SUPPORT_RESPONSE_READBACK_UNAVAILABLE,
}

_STATE: dict[str, dict[str, Any]] = {}


def reset_project_import_contract_support_state() -> None:
    _STATE.clear()


def _is_flag_enabled() -> bool:
    return os.getenv(CONTRACT_SUPPORT_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _ordered_scope_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(row) for row in rows), key=lambda row: (str(row.get("scope_id") or ""), str(row.get("scope_name") or "")))


def _ordered_apparatus_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (dict(row) for row in rows),
        key=lambda row: (
            str(row.get("scope_id") or ""),
            str(row.get("apparatus_id") or ""),
            str(row.get("apparatus_name") or ""),
        ),
    )


def compute_project_import_contract_support_digest(payload: Mapping[str, Any]) -> str:
    canonical_parts = [
        str(payload.get("project_id") or ""),
        str(payload.get("candidate_id") or ""),
        str(payload.get("source_fingerprint") or ""),
        str(payload.get("snapshot_kind") or ""),
        str(payload.get("contract_value") or ""),
        str(payload.get("total_quoted_hours") or ""),
        _stable_json(_ordered_scope_rows(list(payload.get("scope_labor_details") or []))),
        _stable_json(_ordered_apparatus_rows(list(payload.get("apparatus_financials") or []))),
    ]
    return hashlib.sha256("|".join(canonical_parts).encode("utf-8")).hexdigest()


def build_project_import_contract_support_entity_id(payload: Mapping[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "snapshot_kind": payload.get("snapshot_kind"),
        "idempotency_key": payload.get("idempotency_key"),
    }
    digest = hashlib.sha256(_stable_json(identity).encode("utf-8")).hexdigest()[:24]
    return f"project-import-contract-support-{digest}"


def _reject_unauthorized_role(actor: Actor) -> None:
    if actor.actor_role not in CONTRACT_SUPPORT_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "UNAUTHORIZED_ROLE",
                "actor_role": actor.actor_role,
                "allowed_roles": sorted(CONTRACT_SUPPORT_ALLOWED_ROLES),
            },
        )


def _patch_common_response_fields(response: dict[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    response["action_type"] = CONTRACT_SUPPORT_ACTION_TYPE
    response["entity_id"] = build_project_import_contract_support_entity_id(payload)
    response["entity_type"] = CONTRACT_SUPPORT_ENTITY_TYPE
    response["apparatus_financial_row_count"] = len(list(payload.get("apparatus_financials") or []))
    response["current_candidate_match"] = True
    response["scope_labor_detail_row_count"] = len(list(payload.get("scope_labor_details") or []))
    response.setdefault("http_status", 200)
    response.setdefault("new_state", {})
    response["new_state"]["apparatus_financial_row_count"] = response["apparatus_financial_row_count"]
    response["new_state"]["candidate_id"] = payload.get("candidate_id")
    response["new_state"]["counts_match"] = response["new_state"].get("counts_match", True)
    response["new_state"]["current_candidate_match"] = response["current_candidate_match"]
    response["new_state"]["project_id"] = payload.get("project_id")
    response["new_state"]["route"] = CONTRACT_SUPPORT_WRITE_ROUTE
    response["new_state"]["scope_labor_detail_row_count"] = response["scope_labor_detail_row_count"]
    response["new_state"]["snapshot_kind"] = payload.get("snapshot_kind")
    response["new_state"]["source_fingerprint"] = payload.get("source_fingerprint")
    response["new_state"]["status_route"] = CONTRACT_SUPPORT_READ_ROUTE
    return response


def _success_response(payload: Mapping[str, Any]) -> dict[str, Any]:
    response = deepcopy(CONTRACT_SUPPORT_RESPONSE_SUCCESS_FIRST_WRITE)
    return _patch_common_response_fields(response, payload)


def _idempotent_response(payload: Mapping[str, Any], stored: Mapping[str, Any]) -> dict[str, Any]:
    response = deepcopy(CONTRACT_SUPPORT_RESPONSE_IDEMPOTENT_HIT)
    response["audit_event_id"] = stored["response"].get("audit_event_id")
    response["mutation_id"] = stored["mutation_id"]
    response["project_contract_snapshot_id"] = stored["response"].get("project_contract_snapshot_id")
    patched = _patch_common_response_fields(response, payload)
    patched["new_state"]["audit_event_id"] = stored["response"].get("audit_event_id")
    patched["new_state"]["mutation_id"] = stored["mutation_id"]
    return patched


def _conflict_response(payload: Mapping[str, Any], stored: Mapping[str, Any]) -> dict[str, Any]:
    response = deepcopy(CONTRACT_SUPPORT_RESPONSE_CONFLICT_DUPLICATE_BUSINESS_PAYLOAD)
    response["mutation_id"] = payload.get("mutation_id")
    response["conflict"]["queued_action"]["incoming_mutation_id"] = payload.get("mutation_id")
    response["conflict"]["server_state"]["existing_mutation_id"] = stored["mutation_id"]
    patched = _patch_common_response_fields(response, payload)
    patched["new_state"]["mutation_id"] = payload.get("mutation_id")
    return patched


def _forced_failure_response(payload: Mapping[str, Any], force_failure: str) -> dict[str, Any]:
    return deepcopy(_FORCE_FAILURE_FIXTURES[force_failure])


def persist_project_import_contract_support(
    request: Mapping[str, Any],
    actor: Actor,
) -> dict[str, Any]:
    _reject_unauthorized_role(actor)

    if request.get("action_type") != CONTRACT_SUPPORT_ACTION_TYPE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_PAYLOAD", "field": "action_type"})
    if request.get("mutation_class") != "C":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_MUTATION_CLASS"})
    if request.get("source") == "offline_queue":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "OFFLINE_CLASS_C_REJECTED"})

    payload = dict(request.get("payload") or {})
    digest = compute_project_import_contract_support_digest(payload)
    if request.get("idempotency_key") != digest or payload.get("idempotency_key") != digest:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PAYLOAD",
                "detail": {
                    "computed_business_payload_digest": digest,
                    "envelope_idempotency_key": request.get("idempotency_key"),
                    "payload_idempotency_key": payload.get("idempotency_key"),
                },
            },
        )

    expected_entity_id = build_project_import_contract_support_entity_id(payload)
    if request.get("entity_id") != expected_entity_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PAYLOAD",
                "detail": {
                    "expected_entity_id": expected_entity_id,
                    "provided_entity_id": request.get("entity_id"),
                },
            },
        )

    flag_enabled = _is_flag_enabled()
    force_failure = request.get("force_failure") if flag_enabled else None
    dry_run = bool(request.get("dry_run")) if flag_enabled else False

    if force_failure:
        if force_failure not in _FORCE_FAILURE_FIXTURES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_PAYLOAD", "field": "force_failure"})
        return _forced_failure_response(payload, force_failure)

    existing = _STATE.get(digest)
    if existing is not None:
        if existing["mutation_id"] == payload.get("mutation_id"):
            return _idempotent_response(payload, existing)
        return _conflict_response(payload, existing)

    response = _success_response(payload)
    response["mutation_id"] = payload.get("mutation_id")
    response["new_state"]["mutation_id"] = payload.get("mutation_id")

    if not dry_run:
        _STATE[digest] = {
            "candidate_id": payload.get("candidate_id"),
            "mutation_id": payload.get("mutation_id"),
            "payload": deepcopy(payload),
            "project_id": payload.get("project_id"),
            "response": deepcopy(response),
            "source_fingerprint": payload.get("source_fingerprint"),
        }

    return response


def load_project_import_contract_support_status(
    query: ProjectImportContractSupportReadbackQuery,
    actor: Actor,
) -> dict[str, Any]:
    _reject_unauthorized_role(actor)

    if not _STATE:
        return deepcopy(_READBACK_FIXTURES["missing"])

    latest = next(reversed(_STATE.values()))
    if latest["candidate_id"] != query.candidate_id or latest["source_fingerprint"] != query.source_fingerprint:
        response = deepcopy(_READBACK_FIXTURES["stale_candidate"])
        response["candidate_id"] = query.candidate_id
        response["current_candidate_match"] = False
        response["project_id"] = query.project_id
        response["source_fingerprint"] = query.source_fingerprint
        return response

    response = deepcopy(_READBACK_FIXTURES["ready"])
    response["candidate_id"] = query.candidate_id
    response["project_id"] = query.project_id
    response["source_fingerprint"] = query.source_fingerprint
    return response
