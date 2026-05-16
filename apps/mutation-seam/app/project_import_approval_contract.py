from __future__ import annotations

from typing import Any, Dict, List, Mapping

from app.project_import_admission_plan import load_project_import_admission_plan


APPROVAL_CONTRACT_VERSION = "pm_import_approval_persistence_contract_read_only_v1"
PERSISTENCE_AUTHORITY = "design_only_not_admitted"


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _sorted_strings(values: Any) -> List[str]:
    return sorted(str(value) for value in _as_list(values) if str(value))


def _check_ids_by_status(admission_plan: Mapping[str, Any], statuses: set[str]) -> List[str]:
    return sorted(
        str(check.get("check_id"))
        for check in admission_plan.get("no_go_checks", [])
        if check.get("status") in statuses and check.get("check_id")
    )


def _minimum_expected_values(admission_plan: Mapping[str, Any]) -> Dict[str, Any]:
    approval_contract = admission_plan.get("approval_record_contract") or {}
    expected = dict(approval_contract.get("minimum_expected_values") or {})
    expected["idempotency_key"] = (admission_plan.get("idempotency_plan") or {}).get("sample_key")
    expected["accepted_no_go_overrides"] = _check_ids_by_status(admission_plan, {"needs_human_acceptance"})
    return expected


def build_project_import_approval_contract(admission_plan: Mapping[str, Any]) -> Dict[str, Any]:
    approval_contract = admission_plan.get("approval_record_contract") or {}
    expected = _minimum_expected_values(admission_plan)
    human_acceptance_check_ids = expected["accepted_no_go_overrides"]
    non_overridable_check_ids = _check_ids_by_status(admission_plan, {"no_go", "pending_future_admission"})

    return {
        "approval_contract_id": f"{admission_plan.get('candidate_id')}-approval-persistence-contract",
        "approval_contract_version": APPROVAL_CONTRACT_VERSION,
        "candidate_id": admission_plan.get("candidate_id"),
        "candidate_version": admission_plan.get("candidate_version"),
        "readiness_status": admission_plan.get("readiness_status"),
        "mutation_authority": admission_plan.get("mutation_authority") or "not_admitted",
        "persistence_authority": PERSISTENCE_AUTHORITY,
        "storage_decision": "pending_future_packet",
        "approval_record_contract": approval_contract,
        "required_fields": list(approval_contract.get("required_fields") or []),
        "permitted_decisions": list(approval_contract.get("permitted_decisions") or []),
        "minimum_expected_values": expected,
        "candidate_identity": {
            "candidate_id": expected.get("candidate_id"),
            "candidate_version": expected.get("candidate_version"),
            "source_stat_fingerprint": expected.get("source_stat_fingerprint"),
            "candidate_shape_fingerprint": expected.get("candidate_shape_fingerprint"),
            "idempotency_key": expected.get("idempotency_key"),
        },
        "human_acceptance_policy": {
            "accepted_no_go_overrides_field": "accepted_no_go_overrides",
            "required_human_acceptance_check_ids": human_acceptance_check_ids,
            "non_overridable_check_ids": non_overridable_check_ids,
            "policy": "PM may acknowledge needs_human_acceptance checks; no_go and pending_future_admission checks remain blocked until a later packet changes authority.",
        },
        "decision_payload_template": {
            "candidate_id": expected.get("candidate_id"),
            "candidate_version": expected.get("candidate_version"),
            "source_stat_fingerprint": expected.get("source_stat_fingerprint"),
            "candidate_shape_fingerprint": expected.get("candidate_shape_fingerprint"),
            "idempotency_key": expected.get("idempotency_key"),
            "decision": "approve_for_import_packet",
            "approved_by_actor_id": "<pm actor id>",
            "approved_at_utc": "<server timestamp in future admitted mutation>",
            "accepted_warning_codes": list(expected.get("accepted_warning_codes") or []),
            "accepted_no_go_overrides": human_acceptance_check_ids,
            "review_notes": "<PM review note required before persistence>",
        },
        "validation_matrix": [
            {
                "check_id": "required-fields-present",
                "fields": list(approval_contract.get("required_fields") or []),
                "failure_action": "reject approval packet before persistence",
            },
            {
                "check_id": "decision-is-permitted",
                "permitted_decisions": list(approval_contract.get("permitted_decisions") or []),
                "failure_action": "reject approval packet before persistence",
            },
            {
                "check_id": "candidate-identity-matches-current-plan",
                "fields": [
                    "candidate_id",
                    "candidate_version",
                    "source_stat_fingerprint",
                    "candidate_shape_fingerprint",
                    "idempotency_key",
                ],
                "failure_action": "stop import and regenerate PM review packet",
            },
            {
                "check_id": "warning-codes-accepted-exactly",
                "fields": ["accepted_warning_codes"],
                "failure_action": "stop import and get renewed PM warning acceptance",
            },
            {
                "check_id": "only-human-acceptance-checks-acknowledged",
                "fields": ["accepted_no_go_overrides"],
                "failure_action": "stop import and resolve or re-authorize no-go conditions",
            },
            {
                "check_id": "review-note-is-nonempty",
                "fields": ["review_notes"],
                "failure_action": "reject approval packet before persistence",
            },
        ],
        "future_mutation_contract": {
            "proposed_entity_type": "pm_import_candidate_approval",
            "proposed_action": "persist_import_approval",
            "proposed_route": "/api/v1/mutations/project-import-approvals",
            "current_authority": "not_admitted",
            "idempotency_policy": (admission_plan.get("idempotency_plan") or {}).get("collision_policy"),
        },
        "not_allowed_now": [
            "persist_approval_record",
            "write_supabase",
            "run_workbook_macros",
            "write_workbooks",
            "import_project_rows",
            "assign_work",
            "mutate_schedule",
            "change_status",
            "autonomous_ai_business_state_mutation",
        ],
    }


def _missing_required_fields(payload: Mapping[str, Any], required_fields: List[str]) -> List[str]:
    missing = []
    for field in required_fields:
        value = payload.get(field)
        if value is None or value == "":
            missing.append(field)
    return missing


def _add_error(errors: List[Dict[str, str]], field: str, code: str, message: str) -> None:
    errors.append({"field": field, "code": code, "message": message})


def validate_project_import_approval_payload(
    payload: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    expected = contract.get("minimum_expected_values") or {}
    required_fields = list(contract.get("required_fields") or [])
    permitted_decisions = set(contract.get("permitted_decisions") or [])
    human_policy = contract.get("human_acceptance_policy") or {}
    required_human_acceptance = _sorted_strings(human_policy.get("required_human_acceptance_check_ids"))
    non_overridable = set(_sorted_strings(human_policy.get("non_overridable_check_ids")))
    errors: List[Dict[str, str]] = []

    for field in _missing_required_fields(payload, required_fields):
        _add_error(errors, field, "missing_required_field", f"{field} is required by the approval contract.")

    decision = payload.get("decision")
    if decision not in permitted_decisions:
        _add_error(errors, "decision", "unsupported_decision", f"{decision!r} is not a permitted import approval decision.")

    identity_fields = [
        "candidate_id",
        "candidate_version",
        "source_stat_fingerprint",
        "candidate_shape_fingerprint",
        "idempotency_key",
    ]
    for field in identity_fields:
        if payload.get(field) != expected.get(field):
            _add_error(errors, field, f"stale_{field}", f"{field} does not match the current admission plan.")

    warning_codes = _sorted_strings(payload.get("accepted_warning_codes"))
    expected_warning_codes = _sorted_strings(expected.get("accepted_warning_codes"))
    if warning_codes != expected_warning_codes:
        _add_error(
            errors,
            "accepted_warning_codes",
            "warning_code_set_mismatch",
            "accepted_warning_codes must exactly match the current candidate warning-code set.",
        )

    accepted_overrides = _sorted_strings(payload.get("accepted_no_go_overrides"))
    if accepted_overrides != required_human_acceptance:
        _add_error(
            errors,
            "accepted_no_go_overrides",
            "human_acceptance_set_mismatch",
            "accepted_no_go_overrides must exactly match needs_human_acceptance checks.",
        )
    blocked_overrides = sorted(set(accepted_overrides).intersection(non_overridable))
    if blocked_overrides:
        _add_error(
            errors,
            "accepted_no_go_overrides",
            "non_overridable_check_acknowledged",
            f"These checks cannot be overridden by an approval packet: {', '.join(blocked_overrides)}.",
        )

    review_notes = str(payload.get("review_notes") or "").strip()
    if not review_notes or review_notes.startswith("<"):
        _add_error(errors, "review_notes", "review_notes_required", "review_notes must contain a PM review note.")

    approved_by = str(payload.get("approved_by_actor_id") or "").strip()
    if not approved_by or approved_by.startswith("<"):
        _add_error(
            errors,
            "approved_by_actor_id",
            "approved_by_actor_required",
            "approved_by_actor_id must identify the PM actor for the approval packet.",
        )

    approved_at = str(payload.get("approved_at_utc") or "").strip()
    if not approved_at or approved_at.startswith("<"):
        _add_error(
            errors,
            "approved_at_utc",
            "approved_timestamp_required",
            "approved_at_utc must be populated before approval persistence.",
        )

    return {
        "valid": not errors,
        "approval_contract_id": contract.get("approval_contract_id"),
        "approval_contract_version": contract.get("approval_contract_version"),
        "candidate_id": contract.get("candidate_id"),
        "candidate_version": contract.get("candidate_version"),
        "mutation_authority": contract.get("mutation_authority"),
        "persistence_authority": contract.get("persistence_authority"),
        "errors": errors,
        "accepted_warning_codes": warning_codes,
        "accepted_no_go_overrides": accepted_overrides,
    }


def load_project_import_approval_contract() -> Dict[str, Any]:
    return build_project_import_approval_contract(load_project_import_admission_plan())
