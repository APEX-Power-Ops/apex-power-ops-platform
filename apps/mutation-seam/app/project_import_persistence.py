from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional
from uuid import uuid4

from app.audit.logger import record_audit_event
from app.auth.jwt import Actor
from app.db.memory_store import store
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.idempotency.store import save_idempotency
from app.project_import_admission_plan import load_project_import_admission_plan
from app.project_import_approval_contract import load_project_import_approval_contract
from app.project_import_approval_persistence import load_project_import_approval_status
from app.project_import_candidate import load_project_import_candidate


IMPORT_ENTITY_TYPE = "pm_import"
IMPORT_ACTION_TYPE = "persist_project_import"
IMPORT_ROUTE = "/api/v1/mutations/project-imports"
IMPORT_PERSISTENCE_VERSION = "pm_import_persistence_v1"
IMPORT_AUTHORITY = "admitted_by_pm_lane_278"
SOURCE_TRACE_STORAGE = "embedded_on_imported_task_and_apparatus_rows"
WARNING_REVIEW_STORAGE = "embedded_on_imported_project_row"

REQUIRED_PAYLOAD_FIELDS = {
    "candidate_id",
    "candidate_version",
    "source_stat_fingerprint",
    "candidate_shape_fingerprint",
    "idempotency_key",
    "approval_record_id",
    "accepted_warning_codes",
    "accepted_no_go_overrides",
}
OPTIONAL_PAYLOAD_FIELDS = {
    "import_notes",
    "operator_attestation",
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def _slug(value: Any, fallback: str = "unknown") -> str:
    text = str(value or fallback).strip()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or fallback


def _candidate_slug(candidate: Mapping[str, Any]) -> str:
    candidate_id = str(candidate.get("candidate_id") or "project-miner")
    return _slug(candidate_id.removeprefix("pm-import-candidate-"))


def build_project_import_id(candidate: Mapping[str, Any]) -> str:
    return f"pm-import-project-{_candidate_slug(candidate)}"


def _sorted_strings(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return sorted(str(value) for value in values)
    return sorted(str(value) for value in [values])


def _warning_codes(candidate: Mapping[str, Any]) -> list[str]:
    return sorted(
        str(warning.get("code"))
        for warning in candidate.get("warnings", [])
        if warning.get("code")
    )


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or "unknown",
        entity_type=IMPORT_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _expected_identity(
    candidate: Mapping[str, Any],
    admission_plan: Mapping[str, Any],
    approval_status: Mapping[str, Any],
) -> Dict[str, Any]:
    contract = load_project_import_approval_contract()
    expected = contract.get("minimum_expected_values") or {}
    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "source_stat_fingerprint": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
        "candidate_shape_fingerprint": admission_plan.get("candidate_shape_fingerprint"),
        "idempotency_key": expected.get("idempotency_key"),
        "approval_record_id": approval_status.get("approval_record_id"),
        "accepted_warning_codes": list(expected.get("accepted_warning_codes") or []),
        "accepted_no_go_overrides": list(expected.get("accepted_no_go_overrides") or []),
    }


def _normalized_import_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = {field: payload.get(field) for field in sorted(REQUIRED_PAYLOAD_FIELDS)}
    normalized["accepted_warning_codes"] = _sorted_strings(normalized.get("accepted_warning_codes"))
    normalized["accepted_no_go_overrides"] = _sorted_strings(normalized.get("accepted_no_go_overrides"))
    if "import_notes" in payload:
        normalized["import_notes"] = str(payload.get("import_notes") or "").strip()
    if "operator_attestation" in payload:
        normalized["operator_attestation"] = str(payload.get("operator_attestation") or "").strip()
    return normalized


def _validate_import_payload(
    *,
    request: MutationRequest,
    payload: Mapping[str, Any],
    candidate: Mapping[str, Any],
    admission_plan: Mapping[str, Any],
    approval_status: Mapping[str, Any],
) -> Optional[MutationResponse]:
    unknown_fields = sorted(set(payload) - REQUIRED_PAYLOAD_FIELDS - OPTIONAL_PAYLOAD_FIELDS)
    if unknown_fields:
        return _invalid_payload_response(
            request,
            "Project import payload contains fields outside the admitted contract.",
            detail={"unknown_fields": unknown_fields},
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return _invalid_payload_response(
            request,
            "Project import payload is missing required fields.",
            detail={"missing_fields": missing_fields},
        )

    expected = _expected_identity(candidate, admission_plan, approval_status)
    mismatches = []
    for field in [
        "candidate_id",
        "candidate_version",
        "source_stat_fingerprint",
        "candidate_shape_fingerprint",
        "idempotency_key",
        "approval_record_id",
    ]:
        if payload.get(field) != expected.get(field):
            mismatches.append(
                {
                    "field": field,
                    "payload_value": payload.get(field),
                    "expected_value": expected.get(field),
                }
            )

    list_fields = ["accepted_warning_codes", "accepted_no_go_overrides"]
    for field in list_fields:
        if _sorted_strings(payload.get(field)) != _sorted_strings(expected.get(field)):
            mismatches.append(
                {
                    "field": field,
                    "payload_value": _sorted_strings(payload.get(field)),
                    "expected_value": _sorted_strings(expected.get(field)),
                }
            )

    if request.idempotency_key != expected.get("idempotency_key"):
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "payload_value": request.idempotency_key,
                "expected_value": expected.get("idempotency_key"),
            }
        )

    if mismatches:
        return _invalid_payload_response(
            request,
            "Project import payload does not match the current approved candidate identity.",
            detail={"mismatches": mismatches},
        )

    return None


def _validate_current_gate(
    *,
    request: MutationRequest,
    candidate: Mapping[str, Any],
    admission_plan: Mapping[str, Any],
    approval_status: Mapping[str, Any],
) -> Optional[MutationResponse]:
    if approval_status.get("classification") != "approved_for_import_packet":
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import requires a current approved import-candidate approval record.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"approval_status": approval_status},
        )

    if approval_status.get("current_candidate_match") is not True:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import approval record is stale against the current candidate.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"approval_status": approval_status},
        )

    if int(approval_status.get("approval_record_count_for_candidate") or 0) != 1:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import requires exactly one current approval record for the candidate.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"approval_status": approval_status},
        )

    summary = candidate.get("summary") or {}
    if int(summary.get("blocker_count") or 0) != 0:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import cannot run while candidate blocker warnings remain.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"blocker_count": summary.get("blocker_count")},
        )

    if int(summary.get("task_count") or 0) <= 0:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import requires at least one task row in the current candidate.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"summary": summary},
        )

    source_freshness = candidate.get("source_freshness") or {}
    if not source_freshness.get("aggregate_fingerprint"):
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import requires a current source fingerprint.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"source_freshness": source_freshness},
        )

    non_admission_no_go = [
        check
        for check in admission_plan.get("no_go_checks", [])
        if check.get("status") == "no_go"
        and check.get("check_id") not in {"mutation-path-not-admitted"}
    ]
    if non_admission_no_go:
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Project import cannot run because non-admission no-go checks remain.",
            entity_id=request.entity_id or build_project_import_id(candidate),
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"no_go_checks": non_admission_no_go},
        )

    return None


def _trace_payload(entity_type: str, source_ref: Mapping[str, Any], extra: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "trace_id": f"pm-import-source-trace-{_stable_hash({'entity_type': entity_type, 'source_ref': source_ref, 'extra': extra})}",
        "entity_type": entity_type,
        "source_ref": dict(source_ref),
        "source_trace_authority": IMPORT_AUTHORITY,
        **dict(extra),
    }


def _build_rows(
    *,
    candidate: Mapping[str, Any],
    admission_plan: Mapping[str, Any],
    approval_status: Mapping[str, Any],
    import_payload: Mapping[str, Any],
    actor: Actor,
    imported_at: str,
) -> Dict[str, Any]:
    project_id = build_project_import_id(candidate)
    project = candidate.get("project") or {}
    summary = candidate.get("summary") or {}
    candidate_slug = _candidate_slug(candidate)
    source_identity = {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "source_stat_fingerprint": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
        "candidate_shape_fingerprint": admission_plan.get("candidate_shape_fingerprint"),
        "idempotency_key": import_payload.get("idempotency_key"),
        "approval_record_id": approval_status.get("approval_record_id"),
    }
    warning_review_rows = [
        {
            "warning_review_id": f"pm-import-warning-review-{index:03d}",
            "candidate_id": candidate.get("candidate_id"),
            "approval_record_id": approval_status.get("approval_record_id"),
            "warning_code": warning.get("code"),
            "warning_severity": warning.get("severity"),
            "review_status": "accepted_for_import",
            "message": warning.get("message"),
            "review_action": warning.get("review_action"),
        }
        for index, warning in enumerate(candidate.get("warnings", []), start=1)
    ]

    workpackage_rows = []
    task_rows = []
    apparatus_rows = []
    task_id_by_candidate: Dict[str, str] = {}

    for wp_index, workpackage in enumerate(candidate.get("workpackages", []), start=1):
        workpackage_id = f"{project_id}-wp-{wp_index:03d}"
        workpackage_rows.append(
            {
                "id": workpackage_id,
                "project_id": project_id,
                "name": workpackage.get("title") or workpackage_id,
                "status": "not_started",
                "planned_hours": workpackage.get("planned_hours") or 0,
                "percent_complete": 0,
                "task_count": workpackage.get("task_count") or 0,
                "apparatus_count": workpackage.get("apparatus_candidate_count") or 0,
                "source_import_candidate_id": candidate.get("candidate_id"),
                "source_candidate_workpackage_id": workpackage.get("workpackage_id"),
                "source_section": workpackage.get("source_section"),
                "source_scope_sheet": workpackage.get("source_scope_sheet"),
                "source_drawing_refs": list(workpackage.get("drawing_refs") or []),
                "import_identity": source_identity,
                "import_authority": IMPORT_AUTHORITY,
                "imported_at": imported_at,
            }
        )

        for task_index, task in enumerate(workpackage.get("tasks", []), start=len(task_rows) + 1):
            task_id = f"{project_id}-task-{task_index:04d}"
            task_id_by_candidate[str(task.get("task_id"))] = task_id
            source_ref = task.get("source_ref") or {}
            task_rows.append(
                {
                    "id": task_id,
                    "project_id": project_id,
                    "workpackage_id": workpackage_id,
                    "name": task.get("title") or task_id,
                    "title": task.get("title") or task_id,
                    "status": "not_started",
                    "priority": max(0.1, round(1.0 - ((task_index - 1) * 0.02), 2)),
                    "planned_hours": task.get("planned_hours") or 0,
                    "drawing_ref": task.get("drawing_ref"),
                    "source_import_candidate_id": candidate.get("candidate_id"),
                    "source_candidate_task_id": task.get("task_id"),
                    "source_line_id": task.get("source_line_id"),
                    "source_apparatus_type": task.get("apparatus_type"),
                    "source_designation": task.get("designation"),
                    "source_trace": _trace_payload(
                        "task",
                        source_ref,
                        {
                            "candidate_task_id": task.get("task_id"),
                            "source_line_id": task.get("source_line_id"),
                        },
                    ),
                    "apparatus_candidate_count": len(task.get("apparatus_candidates", [])),
                    "import_identity": source_identity,
                    "import_authority": IMPORT_AUTHORITY,
                    "imported_at": imported_at,
                }
            )

            for apparatus_index, apparatus in enumerate(task.get("apparatus_candidates", []), start=len(apparatus_rows) + 1):
                apparatus_id = f"{project_id}-app-{apparatus_index:04d}"
                apparatus_source_ref = {
                    **source_ref,
                    "source_line_id": apparatus.get("source_line_id"),
                    "source_row": apparatus.get("source_row"),
                    "scope_sheet": apparatus.get("scope_sheet"),
                    "drawing_ref": apparatus.get("drawing_ref"),
                }
                apparatus_rows.append(
                    {
                        "id": apparatus_id,
                        "project_id": project_id,
                        "task_id": task_id,
                        "name": apparatus.get("display_name") or apparatus.get("apparatus_type") or apparatus_id,
                        "status": "not_started",
                        "assigned_to": None,
                        "source_import_candidate_id": candidate.get("candidate_id"),
                        "source_candidate_task_id": task.get("task_id"),
                        "source_candidate_apparatus_id": apparatus.get("candidate_id"),
                        "source_apparatus_type": apparatus.get("apparatus_type"),
                        "source_designation": apparatus.get("designation"),
                        "source_drawing_ref": apparatus.get("drawing_ref"),
                        "source_line_id": apparatus.get("source_line_id"),
                        "source_row": apparatus.get("source_row"),
                        "source_scope_sheet": apparatus.get("scope_sheet"),
                        "planned_hours": apparatus.get("planned_hours") or 0,
                        "source_trace": _trace_payload(
                            "apparatus",
                            apparatus_source_ref,
                            {
                                "candidate_apparatus_id": apparatus.get("candidate_id"),
                                "candidate_task_id": task.get("task_id"),
                            },
                        ),
                        "import_identity": source_identity,
                        "import_authority": IMPORT_AUTHORITY,
                        "imported_at": imported_at,
                    }
                )

    project_row = {
        "id": project_id,
        "name": project.get("name") or project_id,
        "status": "not_started",
        "location": project.get("location"),
        "drawing_package": project.get("drawing_package"),
        "issue_date": project.get("issue_date"),
        "source_format": project.get("source_format"),
        "source_sheet": project.get("source_sheet"),
        "scope_sheets": list(project.get("scope_sheets") or []),
        "source_import_candidate_id": candidate.get("candidate_id"),
        "source_stat_fingerprint": source_identity["source_stat_fingerprint"],
        "candidate_shape_fingerprint": source_identity["candidate_shape_fingerprint"],
        "approval_record_id": approval_status.get("approval_record_id"),
        "approval_mutation_id": approval_status.get("mutation_id"),
        "approval_audit_event_id": approval_status.get("audit_event_id"),
        "import_authority": IMPORT_AUTHORITY,
        "import_persistence_version": IMPORT_PERSISTENCE_VERSION,
        "imported_by_actor_id": actor.actor_id,
        "imported_at": imported_at,
        "import_payload_hash": _stable_hash(_normalized_import_payload(import_payload)),
        "import_payload": _normalized_import_payload(import_payload),
        "import_identity": source_identity,
        "import_summary": {
            "workpackage_count": summary.get("workpackage_count"),
            "task_count": summary.get("task_count"),
            "apparatus_candidate_count": summary.get("apparatus_candidate_count"),
            "warning_count": summary.get("warning_count"),
            "source_trace_rows": len(task_rows) + len(apparatus_rows),
            "warning_review_rows": len(warning_review_rows),
        },
        "source_bundle": candidate.get("source_bundle") or {},
        "source_freshness": candidate.get("source_freshness") or {},
        "warning_review_rows": warning_review_rows,
        "warning_review_storage": WARNING_REVIEW_STORAGE,
        "source_trace_storage": SOURCE_TRACE_STORAGE,
    }

    return {
        "project": project_row,
        "workpackages": workpackage_rows,
        "tasks": task_rows,
        "apparatus": apparatus_rows,
        "task_id_by_candidate": task_id_by_candidate,
        "warning_review_rows": warning_review_rows,
    }


def _row_counts(rows: Mapping[str, Any]) -> Dict[str, int]:
    return {
        "projects": 1,
        "workpackages": len(rows.get("workpackages") or []),
        "tasks": len(rows.get("tasks") or []),
        "apparatus": len(rows.get("apparatus") or []),
        "source_trace_rows": len(rows.get("tasks") or []) + len(rows.get("apparatus") or []),
        "warning_review_rows": len(rows.get("warning_review_rows") or []),
        "assignments": 0,
        "snapshots": 0,
        "issues": 0,
        "hours": 0,
    }


def _response_state(
    *,
    rows: Mapping[str, Any],
    mutation_id: str,
    audit_event_id: Optional[str],
    status: str,
) -> Dict[str, Any]:
    project = rows["project"]
    return {
        "status": status,
        "route": IMPORT_ROUTE,
        "import_authority": IMPORT_AUTHORITY,
        "import_persistence_version": IMPORT_PERSISTENCE_VERSION,
        "project_id": project["id"],
        "candidate_id": project.get("source_import_candidate_id"),
        "approval_record_id": project.get("approval_record_id"),
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "row_counts": _row_counts(rows),
        "source_trace_storage": SOURCE_TRACE_STORAGE,
        "warning_review_storage": WARNING_REVIEW_STORAGE,
        "written_row_ids": {
            "project": project["id"],
            "workpackages": [row["id"] for row in rows.get("workpackages") or []],
            "tasks": [row["id"] for row in rows.get("tasks") or []],
            "apparatus": [row["id"] for row in rows.get("apparatus") or []],
        },
        "blocked_downstream": [
            "assignments",
            "field_authorization",
            "lead_crew_selection",
            "schedule_status_mutation",
            "durable_field_records",
            "production_tracking",
            "customer_reporting",
            "billing_payroll_invoice_accounting",
            "workbook_writeback_or_macros",
        ],
    }


def _existing_project_rows(project_id: str) -> Optional[Dict[str, Any]]:
    if project_id not in store.projects:
        return None
    return dict(store.projects[project_id])


def _existing_import_matches(existing: Mapping[str, Any], import_payload: Mapping[str, Any]) -> bool:
    expected_hash = _stable_hash(_normalized_import_payload(import_payload))
    return (
        existing.get("import_authority") == IMPORT_AUTHORITY
        and existing.get("import_payload_hash") == expected_hash
    )


def _persist_rows(rows: Mapping[str, Any]) -> None:
    for row in rows.get("workpackages") or []:
        store.workpackages[row["id"]] = row
    for row in rows.get("tasks") or []:
        store.tasks[row["id"]] = row
    for row in rows.get("apparatus") or []:
        store.apparatus[row["id"]] = row
    project = rows["project"]
    store.projects[project["id"]] = project


def _filter_values(rows: Iterable[Mapping[str, Any]], candidate_id: str, project_id: str) -> list[Dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if row.get("project_id") == project_id
        and row.get("source_import_candidate_id") == candidate_id
    ]


def load_project_import_status() -> Dict[str, Any]:
    candidate = load_project_import_candidate()
    admission_plan = load_project_import_admission_plan()
    approval_status = load_project_import_approval_status()
    project_id = build_project_import_id(candidate)
    expected_counts = {
        "projects": 1,
        "workpackages": int((candidate.get("summary") or {}).get("workpackage_count") or 0),
        "tasks": int((candidate.get("summary") or {}).get("task_count") or 0),
        "apparatus": int((candidate.get("summary") or {}).get("apparatus_candidate_count") or 0),
        "source_trace_rows": int((candidate.get("summary") or {}).get("task_count") or 0)
        + int((candidate.get("summary") or {}).get("apparatus_candidate_count") or 0),
        "warning_review_rows": int((candidate.get("summary") or {}).get("warning_count") or 0),
    }

    if project_id not in store.projects:
        return {
            "classification": "no_import_record",
            "route": "/api/v1/reads/project-import-status",
            "import_route": IMPORT_ROUTE,
            "import_authority": IMPORT_AUTHORITY,
            "candidate_id": candidate.get("candidate_id"),
            "candidate_version": candidate.get("candidate_version"),
            "project_id": project_id,
            "expected_row_counts": expected_counts,
            "imported_row_counts": {
                "projects": 0,
                "workpackages": 0,
                "tasks": 0,
                "apparatus": 0,
                "source_trace_rows": 0,
                "warning_review_rows": 0,
            },
            "approval_status": approval_status,
            "current_candidate_match": False,
        }

    project = dict(store.projects[project_id])
    candidate_id = str(candidate.get("candidate_id") or "")
    workpackages = _filter_values(store.workpackages.values(), candidate_id, project_id)
    tasks = _filter_values(store.tasks.values(), candidate_id, project_id)
    apparatus = _filter_values(store.apparatus.values(), candidate_id, project_id)
    source_trace_count = sum(1 for row in tasks + apparatus if row.get("source_trace"))
    warning_review_count = len(project.get("warning_review_rows") or [])
    imported_counts = {
        "projects": 1,
        "workpackages": len(workpackages),
        "tasks": len(tasks),
        "apparatus": len(apparatus),
        "source_trace_rows": source_trace_count,
        "warning_review_rows": warning_review_count,
    }
    current_identity = _expected_identity(candidate, admission_plan, approval_status)
    stored_identity = dict(project.get("import_identity") or {})
    identity_match = all(
        stored_identity.get(field) == current_identity.get(field)
        for field in [
            "candidate_id",
            "candidate_version",
            "source_stat_fingerprint",
            "candidate_shape_fingerprint",
            "idempotency_key",
            "approval_record_id",
        ]
    )
    counts_match = imported_counts == expected_counts

    return {
        "classification": "imported" if identity_match and counts_match else "import_record_mismatch",
        "route": "/api/v1/reads/project-import-status",
        "import_route": IMPORT_ROUTE,
        "import_authority": project.get("import_authority") or IMPORT_AUTHORITY,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "project_id": project_id,
        "approval_record_id": project.get("approval_record_id"),
        "mutation_id": project.get("import_mutation_id"),
        "audit_event_id": project.get("import_audit_event_id"),
        "expected_row_counts": expected_counts,
        "imported_row_counts": imported_counts,
        "target_row_plan": admission_plan.get("target_row_plan"),
        "approval_status": approval_status,
        "current_candidate_match": identity_match,
        "counts_match": counts_match,
        "source_trace_storage": project.get("source_trace_storage") or SOURCE_TRACE_STORAGE,
        "warning_review_storage": project.get("warning_review_storage") or WARNING_REVIEW_STORAGE,
    }


async def persist_project_import(
    request: MutationRequest,
    actor: Actor,
) -> MutationResponse:
    if request.action_type != IMPORT_ACTION_TYPE:
        return _invalid_payload_response(
            request,
            f"Unknown action type for {IMPORT_ENTITY_TYPE}: {request.action_type}",
        )

    if request.source == "offline_queue":
        return error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Project import cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
        )

    if request.mutation_class != "C":
        return error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Project import requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )

    if actor.actor_role != "pm":
        return error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Project Miner imports.",
            entity_id=request.entity_id or "unknown",
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )

    if not request.payload:
        return _invalid_payload_response(request, "Project import payload is required.")

    candidate = load_project_import_candidate()
    admission_plan = load_project_import_admission_plan()
    approval_status = load_project_import_approval_status()
    project_id = build_project_import_id(candidate)

    if request.entity_id and request.entity_id != project_id:
        return _invalid_payload_response(
            request,
            "entity_id must match the deterministic Project Miner import project id when provided.",
            detail={"expected_entity_id": project_id, "provided_entity_id": request.entity_id},
        )

    gate_error = _validate_current_gate(
        request=request,
        candidate=candidate,
        admission_plan=admission_plan,
        approval_status=approval_status,
    )
    if gate_error:
        return gate_error

    payload_error = _validate_import_payload(
        request=request,
        payload=request.payload,
        candidate=candidate,
        admission_plan=admission_plan,
        approval_status=approval_status,
    )
    if payload_error:
        return payload_error

    existing = _existing_project_rows(project_id)
    if existing:
        if not _existing_import_matches(existing, request.payload):
            return error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing Project Miner import record does not match the submitted import payload.",
                entity_id=project_id,
                entity_type=IMPORT_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"project_id": project_id},
            )
        rows = _build_rows(
            candidate=candidate,
            admission_plan=admission_plan,
            approval_status=approval_status,
            import_payload=request.payload,
            actor=actor,
            imported_at=str(existing.get("imported_at") or _server_timestamp()),
        )
        rows["project"].update(existing)
        mutation_id = str(existing.get("import_mutation_id") or existing.get("mutation_id") or f"mut-{uuid4()}")
        audit_event_id = str(existing.get("import_audit_event_id") or existing.get("audit_event_id") or "") or None
        return MutationResponse(
            status="idempotent_hit",
            mutation_id=mutation_id,
            entity_id=project_id,
            entity_type=IMPORT_ENTITY_TYPE,
            action_type=request.action_type,
            new_state=_response_state(
                rows=rows,
                mutation_id=mutation_id,
                audit_event_id=audit_event_id,
                status="idempotent_hit",
            ),
            audit_event_id=audit_event_id,
        )

    imported_at = _server_timestamp()
    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    rows = _build_rows(
        candidate=candidate,
        admission_plan=admission_plan,
        approval_status=approval_status,
        import_payload=request.payload,
        actor=actor,
        imported_at=imported_at,
    )
    rows["project"]["import_mutation_id"] = mutation_id
    rows["project"]["import_audit_event_id"] = audit_event_id
    _persist_rows(rows)
    response_state = _response_state(
        rows=rows,
        mutation_id=mutation_id,
        audit_event_id=audit_event_id,
        status="accepted",
    )

    audit_request = request.model_copy(update={"entity_id": project_id, "payload": response_state})
    record_audit_event(
        actor=actor,
        request=audit_request,
        from_state={},
        to_state=response_state,
        mutation_id=mutation_id,
        event_id=audit_event_id,
        entity_type=IMPORT_ENTITY_TYPE,
    )

    response = MutationResponse(
        status="accepted",
        mutation_id=mutation_id,
        entity_id=project_id,
        entity_type=IMPORT_ENTITY_TYPE,
        action_type=request.action_type,
        new_state=response_state,
        audit_event_id=audit_event_id,
    )
    save_idempotency(request.idempotency_key, response)
    return response
