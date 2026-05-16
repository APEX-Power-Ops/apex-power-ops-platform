from __future__ import annotations

from typing import Any, Dict, List, Mapping

from app.project_import_approval_contract import load_project_import_approval_contract


APPROVAL_STORAGE_PLAN_VERSION = "pm_import_approval_storage_plan_read_only_v1"
STORAGE_DECISION_AUTHORITY = "storage_decision_only_not_admitted"
RECOMMENDED_TABLE = "seam.pm_import_candidate_approvals"
RECOMMENDED_ENTITY_TYPE = "pm_import_candidate_approval"
RECOMMENDED_ROUTE = "/api/v1/mutations/project-import-approvals"


def _contract_identity(contract: Mapping[str, Any]) -> Dict[str, Any]:
    identity = dict(contract.get("candidate_identity") or {})
    expected = contract.get("minimum_expected_values") or {}
    if not identity:
        identity = {
            "candidate_id": expected.get("candidate_id"),
            "candidate_version": expected.get("candidate_version"),
            "source_stat_fingerprint": expected.get("source_stat_fingerprint"),
            "candidate_shape_fingerprint": expected.get("candidate_shape_fingerprint"),
            "idempotency_key": expected.get("idempotency_key"),
        }
    return identity


def _recommended_columns(contract: Mapping[str, Any]) -> List[Dict[str, Any]]:
    permitted_decisions = list(contract.get("permitted_decisions") or [])
    return [
        {
            "name": "approval_record_id",
            "type": "text",
            "required": True,
            "source": "server generated deterministic id from candidate identity and idempotency key",
        },
        {"name": "candidate_id", "type": "text", "required": True, "source": "approval payload"},
        {"name": "candidate_version", "type": "text", "required": True, "source": "approval payload"},
        {"name": "source_stat_fingerprint", "type": "text", "required": True, "source": "approval payload"},
        {"name": "candidate_shape_fingerprint", "type": "text", "required": True, "source": "approval payload"},
        {"name": "idempotency_key", "type": "text", "required": True, "source": "approval payload"},
        {
            "name": "decision",
            "type": "text",
            "required": True,
            "source": "approval payload",
            "allowed_values": permitted_decisions,
        },
        {"name": "approved_by_actor_id", "type": "text", "required": True, "source": "authenticated PM actor"},
        {"name": "approved_at_utc", "type": "timestamptz", "required": True, "source": "server timestamp"},
        {"name": "accepted_warning_codes", "type": "jsonb", "required": True, "source": "approval payload"},
        {"name": "accepted_no_go_overrides", "type": "jsonb", "required": True, "source": "approval payload"},
        {"name": "review_notes", "type": "text", "required": True, "source": "approval payload"},
        {"name": "approval_payload", "type": "jsonb", "required": True, "source": "validated normalized payload"},
        {"name": "validation_result", "type": "jsonb", "required": True, "source": "contract validator result"},
        {"name": "created_at", "type": "timestamptz", "required": True, "source": "server timestamp"},
    ]


def _recommended_constraints(contract: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "constraint_id": "approval-record-primary-key",
            "applies_to": ["approval_record_id"],
            "rule": "primary key; replay with the same idempotency key must return the same stored record",
        },
        {
            "constraint_id": "candidate-identity-required",
            "applies_to": [
                "candidate_id",
                "candidate_version",
                "source_stat_fingerprint",
                "candidate_shape_fingerprint",
                "idempotency_key",
            ],
            "rule": "all candidate identity fields are non-null and must pass the approval contract validator",
        },
        {
            "constraint_id": "decision-is-permitted",
            "applies_to": ["decision"],
            "rule": "decision must be one of the approval contract permitted decisions",
            "allowed_values": list(contract.get("permitted_decisions") or []),
        },
        {
            "constraint_id": "warning-codes-json-array",
            "applies_to": ["accepted_warning_codes"],
            "rule": "value must be a JSON array and must exactly match the current candidate warning-code set",
        },
        {
            "constraint_id": "no-go-overrides-json-array",
            "applies_to": ["accepted_no_go_overrides"],
            "rule": "value must be a JSON array and may only include needs_human_acceptance check ids",
        },
        {
            "constraint_id": "review-note-required",
            "applies_to": ["review_notes"],
            "rule": "review_notes must be non-empty before persistence",
        },
        {
            "constraint_id": "insert-only-record",
            "applies_to": ["approval_record_id"],
            "rule": "canonical approval records are append-only; changed candidates produce a new record, not an update",
        },
    ]


def _rejected_storage_options() -> List[Dict[str, str]]:
    return [
        {
            "option": "audit_log_only",
            "reason": "Audit rows are evidence of actions, not the canonical approval object an import packet should diff against.",
        },
        {
            "option": "reuse_issue_task_or_workpackage",
            "reason": "Import candidate approval is pre-import project state and must not be smuggled into existing production work entities.",
        },
        {
            "option": "browser_local_storage",
            "reason": "Local drafts help review, but they are not durable governed approval evidence.",
        },
        {
            "option": "generic_pgdict_upsert_without_adapter",
            "reason": "The generic store upserts by id; canonical approvals should be insert-only or strict idempotent replay.",
        },
        {
            "option": "direct_supabase_from_excel_or_ui",
            "reason": "Production writes must go through the governed Render mutation seam and authenticated PM actor context.",
        },
    ]


def build_project_import_approval_storage_plan(contract: Mapping[str, Any]) -> Dict[str, Any]:
    identity = _contract_identity(contract)
    return {
        "storage_plan_id": f"{contract.get('candidate_id')}-approval-storage-plan",
        "storage_plan_version": APPROVAL_STORAGE_PLAN_VERSION,
        "candidate_id": contract.get("candidate_id"),
        "candidate_version": contract.get("candidate_version"),
        "mutation_authority": contract.get("mutation_authority") or "not_admitted",
        "persistence_authority": STORAGE_DECISION_AUTHORITY,
        "selected_storage_decision": "dedicated_insert_only_import_candidate_approval_table",
        "recommended_schema": "seam",
        "recommended_table": RECOMMENDED_TABLE,
        "recommended_entity_type": RECOMMENDED_ENTITY_TYPE,
        "recommended_route": RECOMMENDED_ROUTE,
        "contract_dependency": {
            "approval_contract_id": contract.get("approval_contract_id"),
            "approval_contract_version": contract.get("approval_contract_version"),
            "candidate_identity": identity,
        },
        "record_lifecycle": {
            "write_model": "insert_once_with_idempotent_replay",
            "update_policy": "do_not_update_canonical_records; changed source or candidate shape produces a new approval record",
            "delete_policy": "no delete path in the PM runtime",
            "audit_policy": "record a separate audit event after the approval record insert succeeds",
            "import_policy": "import packet may consume an approved current record, but this storage plan does not import rows",
        },
        "recommended_columns": _recommended_columns(contract),
        "recommended_constraints": _recommended_constraints(contract),
        "adapter_requirements": [
            "Use an explicit approval adapter or repository instead of the generic mutation_pipeline apply step.",
            "Validate with validate_project_import_approval_payload before any insert.",
            "Reject stale candidate identity, source fingerprint, shape fingerprint, idempotency key, warning-code set, or non-overridable no-go acknowledgement.",
            "Use authenticated PM actor context for approved_by_actor_id and server time for approved_at_utc.",
            "Return idempotent replay only when approval_record_id and normalized payload match the stored record.",
            "Do not create project, workpackage, task, apparatus, assignment, schedule, issue, or status rows in this adapter.",
        ],
        "readback_requirements": [
            "Read current approval status by candidate id and current candidate identity.",
            "Expose whether the latest approval is current, stale, returned for revision, rejected, or approved for a later import packet.",
            "Do not treat audit history alone as current approval state.",
        ],
        "rejected_storage_options": _rejected_storage_options(),
        "future_admission_sequence": [
            "Approve this storage decision as a packet.",
            "Add a narrow schema migration for the dedicated approval table.",
            "Add an explicit insert-only approval adapter with idempotent replay.",
            "Add a Class C PM-only POST route for approval persistence.",
            "Add readback for current approval status.",
            "Add PM UI approval controls only after backend persistence is proven.",
            "Admit import mutation in a later packet after approval persistence is green.",
        ],
        "not_allowed_now": [
            "persist_approval_record",
            "write_supabase",
            "create_schema",
            "run_schema_migration",
            "run_workbook_macros",
            "write_workbooks",
            "import_project_rows",
            "assign_work",
            "mutate_schedule",
            "change_status",
            "autonomous_ai_business_state_mutation",
        ],
    }


def load_project_import_approval_storage_plan() -> Dict[str, Any]:
    return build_project_import_approval_storage_plan(load_project_import_approval_contract())
