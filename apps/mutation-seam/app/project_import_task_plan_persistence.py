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
from app.idempotency.store import check_idempotency, save_idempotency
from app.project_import_candidate import load_project_import_candidate


TASK_PLAN_ENTITY_TYPE = "pm_import_task_plan"
TASK_PLAN_ACTION_TYPE = "persist_project_import_task_plan"
TASK_PLAN_ROUTE = "/api/v1/mutations/project-import-task-plans"
TASK_PLAN_STATUS_ROUTE = "/api/v1/reads/project-import-task-plan-status"
TASK_PLAN_PERSISTENCE_VERSION = "pm_import_task_plan_persistence_v1"
TASK_PLAN_AUTHORITY = "admitted_by_pm_lane_361_task_plan_persistence"
TASK_PLAN_STORAGE = "seam.projects_workpackages_tasks_apparatus"

REQUIRED_PAYLOAD_FIELDS = {
    "candidate_id",
    "candidate_version",
    "source_stat_fingerprint",
    "idempotency_key",
    "manual_task_shaping",
}
OPTIONAL_PAYLOAD_FIELDS = {
    "review_notes",
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:24]


def _server_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: Any, fallback: str = "unknown") -> str:
    text = str(value or fallback).strip()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or fallback


def _candidate_slug(candidate: Mapping[str, Any]) -> str:
    candidate_id = str(candidate.get("candidate_id") or "project-miner")
    return _slug(candidate_id.removeprefix("pm-import-candidate-"))


def build_project_import_task_plan_id(candidate: Mapping[str, Any]) -> str:
    return f"pm-task-plan-project-{_candidate_slug(candidate)}"


def _invalid_payload_response(
    request: MutationRequest,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    return error_response(
        code=ErrorCode.INVALID_PAYLOAD,
        message=message,
        entity_id=request.entity_id or "unknown",
        entity_type=TASK_PLAN_ENTITY_TYPE,
        action_type=request.action_type,
        detail=detail,
    )


def _expected_identity(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "source_stat_fingerprint": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
    }


def _normalize_manual_task_shaping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}

    groups = []
    for group in value.get("groups") or []:
        if not isinstance(group, Mapping):
            continue
        groups.append(
            {
                "group_id": str(group.get("group_id") or ""),
                "title": str(group.get("title") or "").strip(),
                "designation": str(group.get("designation") or "").strip(),
                "seeded_from_source": bool(group.get("seeded_from_source")),
                "source_task_id": str(group.get("source_task_id") or "").strip() or None,
                "apparatus_count": int(group.get("apparatus_count") or 0),
                "planned_hours": float(group.get("planned_hours") or 0),
                "apparatus_candidate_ids": [str(item) for item in group.get("apparatus_candidate_ids") or [] if item],
            }
        )

    apparatus = []
    for row in value.get("apparatus") or []:
        if not isinstance(row, Mapping):
            continue
        apparatus.append(
            {
                "candidate_id": str(row.get("candidate_id") or "").strip(),
                "local_task_group_id": str(row.get("local_task_group_id") or "").strip(),
                "display_name": str(row.get("display_name") or "").strip(),
                "designation": str(row.get("designation") or "").strip(),
                "source_task_id": str(row.get("source_task_id") or "").strip() or None,
                "source_task_title": str(row.get("source_task_title") or "").strip() or None,
            }
        )

    return {
        "storage": str(value.get("storage") or "local_browser_only"),
        "version": str(value.get("version") or "unknown"),
        "summary": {
            "group_count": int(((value.get("summary") or {}).get("group_count") or 0)),
            "regrouped_apparatus_count": int(((value.get("summary") or {}).get("regrouped_apparatus_count") or 0)),
            "designation_override_count": int(((value.get("summary") or {}).get("designation_override_count") or 0)),
        },
        "groups": groups,
        "apparatus": apparatus,
    }


def _normalized_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_id": payload.get("candidate_id"),
        "candidate_version": payload.get("candidate_version"),
        "source_stat_fingerprint": payload.get("source_stat_fingerprint"),
        "idempotency_key": payload.get("idempotency_key"),
        "review_notes": str(payload.get("review_notes") or "").strip() or None,
        "manual_task_shaping": _normalize_manual_task_shaping(payload.get("manual_task_shaping")),
    }


def _flatten_candidate_apparatus(candidate: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for workpackage in candidate.get("workpackages") or []:
        workpackage_id = workpackage.get("workpackage_id")
        workpackage_title = workpackage.get("title")
        for task in workpackage.get("tasks") or []:
            apparatus_candidates = task.get("apparatus_candidates") or []
            apparatus_count = len(apparatus_candidates) or 1
            task_planned_hours = float(task.get("planned_hours") or 0)
            per_apparatus_hours = task_planned_hours / apparatus_count if apparatus_count else 0
            source_ref = task.get("source_ref") or {}
            for apparatus in apparatus_candidates:
                candidate_id = str(apparatus.get("candidate_id") or "").strip()
                if not candidate_id:
                    continue
                rows[candidate_id] = {
                    "candidate_id": candidate_id,
                    "source_workpackage_id": workpackage_id,
                    "source_workpackage_title": workpackage_title,
                    "source_task_id": task.get("task_id"),
                    "source_task_title": task.get("title"),
                    "source_designation": task.get("designation") or "",
                    "display_name": apparatus.get("display_name") or task.get("title") or candidate_id,
                    "apparatus_type": task.get("apparatus_type"),
                    "drawing_ref": source_ref.get("drawing_ref") or task.get("drawing_ref"),
                    "source_row": apparatus.get("source_row") or source_ref.get("source_row"),
                    "source_line_id": apparatus.get("source_line_id") or source_ref.get("line_id"),
                    "planned_hours": per_apparatus_hours,
                    "source_ref": dict(source_ref),
                }
    return rows


def _validate_payload(
    *,
    request: MutationRequest,
    payload: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> tuple[Optional[MutationResponse], Optional[Dict[str, Any]]]:
    unknown_fields = sorted(set(payload) - REQUIRED_PAYLOAD_FIELDS - OPTIONAL_PAYLOAD_FIELDS)
    if unknown_fields:
        return (
            _invalid_payload_response(
                request,
                "Project import task plan payload contains fields outside the admitted contract.",
                detail={"unknown_fields": unknown_fields},
            ),
            None,
        )

    missing_fields = sorted(field for field in REQUIRED_PAYLOAD_FIELDS if payload.get(field) in (None, ""))
    if missing_fields:
        return (
            _invalid_payload_response(
                request,
                "Project import task plan payload is missing required fields.",
                detail={"missing_fields": missing_fields},
            ),
            None,
        )

    normalized = _normalized_payload(payload)
    expected = _expected_identity(candidate)
    mismatches = []
    for field in ["candidate_id", "candidate_version", "source_stat_fingerprint"]:
      if normalized.get(field) != expected.get(field):
        mismatches.append(
            {
                "field": field,
                "payload_value": normalized.get(field),
                "expected_value": expected.get(field),
            }
        )

    if request.idempotency_key != normalized.get("idempotency_key"):
        mismatches.append(
            {
                "field": "envelope.idempotency_key",
                "payload_value": request.idempotency_key,
                "expected_value": normalized.get("idempotency_key"),
            }
        )

    manual_task_shaping = normalized["manual_task_shaping"]
    groups = manual_task_shaping.get("groups") or []
    apparatus_rows = manual_task_shaping.get("apparatus") or []
    if not groups:
        mismatches.append({"field": "manual_task_shaping.groups", "payload_value": 0, "expected_value": ">=1"})
    if not apparatus_rows:
        mismatches.append({"field": "manual_task_shaping.apparatus", "payload_value": 0, "expected_value": ">=1"})

    current_candidate_apparatus = _flatten_candidate_apparatus(candidate)
    payload_candidate_ids = [row.get("candidate_id") for row in apparatus_rows if row.get("candidate_id")]
    if sorted(payload_candidate_ids) != sorted(current_candidate_apparatus.keys()):
        mismatches.append(
            {
                "field": "manual_task_shaping.apparatus[].candidate_id",
                "payload_value": sorted(payload_candidate_ids),
                "expected_value": sorted(current_candidate_apparatus.keys()),
            }
        )

    group_ids = {row.get("group_id") for row in groups if row.get("group_id")}
    missing_group_refs = sorted(
        {
            row.get("local_task_group_id")
            for row in apparatus_rows
            if row.get("local_task_group_id") and row.get("local_task_group_id") not in group_ids
        }
    )
    if missing_group_refs:
        mismatches.append(
            {
                "field": "manual_task_shaping.apparatus[].local_task_group_id",
                "payload_value": missing_group_refs,
                "expected_value": "known group ids",
            }
        )

    if mismatches:
        return (
            _invalid_payload_response(
                request,
                "Project import task plan payload does not match the current candidate or shaping contract.",
                detail={"mismatches": mismatches},
            ),
            None,
        )

    return None, normalized


def _task_plan_source_trace(group: Mapping[str, Any], candidate_ids: list[str], source_rows: list[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "trace_id": f"pm-task-plan-source-trace-{_stable_hash({'group': group, 'candidate_ids': candidate_ids})}",
        "source_trace_authority": TASK_PLAN_AUTHORITY,
        "manual_group_id": group.get("group_id"),
        "candidate_apparatus_ids": candidate_ids,
        "source_rows": [
            {
                "candidate_id": row.get("candidate_id"),
                "source_task_id": row.get("source_task_id"),
                "source_workpackage_id": row.get("source_workpackage_id"),
                "source_line_id": row.get("source_line_id"),
                "source_row": row.get("source_row"),
                "drawing_ref": row.get("drawing_ref"),
            }
            for row in source_rows
        ],
    }


def _build_rows(
    *,
    candidate: Mapping[str, Any],
    task_plan_payload: Mapping[str, Any],
    actor: Actor,
    persisted_at: str,
) -> Dict[str, Any]:
    project = candidate.get("project") or {}
    project_id = build_project_import_task_plan_id(candidate)
    flattened = _flatten_candidate_apparatus(candidate)
    manual_task_shaping = task_plan_payload["manual_task_shaping"]
    apparatus_by_group: Dict[str, list[Dict[str, Any]]] = {}
    payload_apparatus = {row["candidate_id"]: row for row in manual_task_shaping.get("apparatus") or []}
    for candidate_id, payload_row in payload_apparatus.items():
        source_row = flattened[candidate_id]
        merged = {
            **source_row,
            "display_name": payload_row.get("display_name") or source_row.get("display_name"),
            "designation": payload_row.get("designation") if payload_row.get("designation") is not None else source_row.get("source_designation"),
            "local_task_group_id": payload_row.get("local_task_group_id"),
            "payload_source_task_id": payload_row.get("source_task_id"),
            "payload_source_task_title": payload_row.get("source_task_title"),
        }
        apparatus_by_group.setdefault(str(payload_row.get("local_task_group_id")), []).append(merged)

    persisted_groups = [
        group
        for group in manual_task_shaping.get("groups") or []
        if apparatus_by_group.get(str(group.get("group_id")))
    ]

    workpackage_id = f"{project_id}-wp-001"
    workpackage_row = {
        "id": workpackage_id,
        "project_id": project_id,
        "name": f"{project.get('name') or 'Project Miner'} PM task plan",
        "status": "planned",
        "planned_hours": round(sum(float(group.get("planned_hours") or 0) for group in persisted_groups), 2),
        "percent_complete": 0,
        "task_count": len(persisted_groups),
        "apparatus_count": len(payload_apparatus),
        "source_import_candidate_id": candidate.get("candidate_id"),
        "planning_context_only": True,
        "task_plan_authority": TASK_PLAN_AUTHORITY,
        "task_plan_persistence_version": TASK_PLAN_PERSISTENCE_VERSION,
        "persisted_at": persisted_at,
    }

    task_rows = []
    apparatus_rows = []
    task_ids_by_group: Dict[str, str] = {}
    for group_index, group in enumerate(persisted_groups, start=1):
        group_id = str(group.get("group_id"))
        task_id = f"{project_id}-task-{group_index:04d}"
        task_ids_by_group[group_id] = task_id
        source_rows = apparatus_by_group[group_id]
        candidate_ids = [row["candidate_id"] for row in source_rows]
        task_rows.append(
            {
                "id": task_id,
                "project_id": project_id,
                "workpackage_id": workpackage_id,
                "name": group.get("title") or task_id,
                "title": group.get("title") or task_id,
                "status": "planned",
                "priority": max(0.1, round(1.0 - ((group_index - 1) * 0.03), 2)),
                "planned_hours": round(sum(float(row.get("planned_hours") or 0) for row in source_rows), 2),
                "drawing_ref": next((row.get("drawing_ref") for row in source_rows if row.get("drawing_ref")), None),
                "designation": group.get("designation") or "",
                "source_import_candidate_id": candidate.get("candidate_id"),
                "source_candidate_task_ids": sorted({str(row.get("source_task_id") or "") for row in source_rows if row.get("source_task_id")}),
                "source_workpackage_ids": sorted({str(row.get("source_workpackage_id") or "") for row in source_rows if row.get("source_workpackage_id")}),
                "planning_context_only": True,
                "task_plan_authority": TASK_PLAN_AUTHORITY,
                "task_plan_group_id": group_id,
                "task_plan_seeded_from_source": bool(group.get("seeded_from_source")),
                "task_plan_payload_hash": _stable_hash(task_plan_payload),
                "task_plan_source_trace": _task_plan_source_trace(group, candidate_ids, source_rows),
                "persisted_at": persisted_at,
            }
        )

    apparatus_index = 1
    for group_id, source_rows in apparatus_by_group.items():
        task_id = task_ids_by_group[group_id]
        for row in source_rows:
            apparatus_id = f"{project_id}-app-{apparatus_index:04d}"
            apparatus_index += 1
            apparatus_rows.append(
                {
                    "id": apparatus_id,
                    "project_id": project_id,
                    "task_id": task_id,
                    "name": row.get("display_name") or apparatus_id,
                    "status": "planned",
                    "assigned_to": None,
                    "source_import_candidate_id": candidate.get("candidate_id"),
                    "source_candidate_task_id": row.get("source_task_id"),
                    "source_candidate_apparatus_id": row.get("candidate_id"),
                    "source_apparatus_type": row.get("apparatus_type"),
                    "source_designation": row.get("source_designation"),
                    "planned_designation": row.get("designation") or "",
                    "source_drawing_ref": row.get("drawing_ref"),
                    "source_line_id": row.get("source_line_id"),
                    "source_row": row.get("source_row"),
                    "planned_hours": float(row.get("planned_hours") or 0),
                    "planning_context_only": True,
                    "task_plan_authority": TASK_PLAN_AUTHORITY,
                    "task_plan_group_id": group_id,
                    "persisted_at": persisted_at,
                }
            )

    project_row = {
        "id": project_id,
        "name": project.get("name") or project_id,
        "status": "planned",
        "location": project.get("location"),
        "drawing_package": project.get("drawing_package"),
        "issue_date": project.get("issue_date"),
        "source_format": project.get("source_format"),
        "source_sheet": project.get("source_sheet"),
        "source_import_candidate_id": candidate.get("candidate_id"),
        "source_stat_fingerprint": task_plan_payload.get("source_stat_fingerprint"),
        "task_plan_authority": TASK_PLAN_AUTHORITY,
        "task_plan_persistence_version": TASK_PLAN_PERSISTENCE_VERSION,
        "task_plan_storage": TASK_PLAN_STORAGE,
        "planning_context_only": True,
        "persisted_by_actor_id": actor.actor_id,
        "persisted_at": persisted_at,
        "task_plan_payload_hash": _stable_hash(task_plan_payload),
        "task_plan_payload": dict(task_plan_payload),
        "task_plan_summary": {
            "group_count": len(persisted_groups),
            "apparatus_count": len(apparatus_rows),
            "regrouped_apparatus_count": manual_task_shaping.get("summary", {}).get("regrouped_apparatus_count") or 0,
            "designation_override_count": manual_task_shaping.get("summary", {}).get("designation_override_count") or 0,
        },
        "blocked_downstream": [
            "approval_record_creation",
            "project_import",
            "assignments",
            "schedule_status_mutation",
            "durable_field_records",
            "production_tracking",
            "customer_reporting",
            "billing_payroll_invoice_accounting",
            "source_writeback_or_macros",
        ],
    }

    return {
        "project": project_row,
        "workpackages": [workpackage_row],
        "tasks": task_rows,
        "apparatus": apparatus_rows,
    }


def _persist_rows(rows: Mapping[str, Any]) -> None:
    for row in rows.get("workpackages") or []:
        store.workpackages[row["id"]] = row
    for row in rows.get("tasks") or []:
        store.tasks[row["id"]] = row
    for row in rows.get("apparatus") or []:
        store.apparatus[row["id"]] = row
    store.projects[rows["project"]["id"]] = rows["project"]


def _row_counts(rows: Mapping[str, Any]) -> Dict[str, int]:
    return {
        "projects": 1,
        "workpackages": len(rows.get("workpackages") or []),
        "tasks": len(rows.get("tasks") or []),
        "apparatus": len(rows.get("apparatus") or []),
    }


def _response_state(*, rows: Mapping[str, Any], mutation_id: str, audit_event_id: Optional[str], status: str) -> Dict[str, Any]:
    project = rows["project"]
    return {
        "status": status,
        "route": TASK_PLAN_ROUTE,
        "task_plan_authority": TASK_PLAN_AUTHORITY,
        "task_plan_persistence_version": TASK_PLAN_PERSISTENCE_VERSION,
        "task_plan_storage": TASK_PLAN_STORAGE,
        "project_id": project["id"],
        "candidate_id": project.get("source_import_candidate_id"),
        "mutation_id": mutation_id,
        "audit_event_id": audit_event_id,
        "row_counts": _row_counts(rows),
        "blocked_downstream": list(project.get("blocked_downstream") or []),
        "written_row_ids": {
            "project": project["id"],
            "workpackages": [row["id"] for row in rows.get("workpackages") or []],
            "tasks": [row["id"] for row in rows.get("tasks") or []],
            "apparatus": [row["id"] for row in rows.get("apparatus") or []],
        },
    }


def _existing_project_rows(project_id: str) -> Optional[Dict[str, Any]]:
    if project_id not in store.projects:
        return None
    return dict(store.projects[project_id])


def _existing_task_plan_matches(existing: Mapping[str, Any], task_plan_payload: Mapping[str, Any]) -> bool:
    return (
        existing.get("task_plan_authority") == TASK_PLAN_AUTHORITY
        and existing.get("task_plan_payload_hash") == _stable_hash(task_plan_payload)
    )


def _filter_values(rows: Iterable[Mapping[str, Any]], candidate_id: str, project_id: str) -> list[Dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if row.get("project_id") == project_id and row.get("source_import_candidate_id") == candidate_id
    ]


def load_project_import_task_plan_status() -> Dict[str, Any]:
    candidate = load_project_import_candidate()
    project_id = build_project_import_task_plan_id(candidate)
    expected_apparatus = int((candidate.get("summary") or {}).get("apparatus_candidate_count") or 0)
    if project_id not in store.projects:
        return {
            "classification": "no_task_plan_record",
            "route": TASK_PLAN_STATUS_ROUTE,
            "task_plan_route": TASK_PLAN_ROUTE,
            "task_plan_authority": TASK_PLAN_AUTHORITY,
            "candidate_id": candidate.get("candidate_id"),
            "candidate_version": candidate.get("candidate_version"),
            "project_id": project_id,
            "expected_row_counts": {
                "projects": 1,
                "workpackages": 1,
                "tasks": 0,
                "apparatus": expected_apparatus,
            },
            "persisted_row_counts": {
                "projects": 0,
                "workpackages": 0,
                "tasks": 0,
                "apparatus": 0,
            },
            "current_candidate_match": False,
            "planning_context_only": True,
        }

    project = dict(store.projects[project_id])
    candidate_id = str(candidate.get("candidate_id") or "")
    workpackages = _filter_values(store.workpackages.values(), candidate_id, project_id)
    tasks = _filter_values(store.tasks.values(), candidate_id, project_id)
    apparatus = _filter_values(store.apparatus.values(), candidate_id, project_id)
    persisted_counts = {
        "projects": 1,
        "workpackages": len(workpackages),
        "tasks": len(tasks),
        "apparatus": len(apparatus),
    }
    payload = dict(project.get("task_plan_payload") or {})
    expected_identity = _expected_identity(candidate)
    current_candidate_match = all(payload.get(field) == expected_identity.get(field) for field in expected_identity)
    expected_tasks = int(((payload.get("manual_task_shaping") or {}).get("summary") or {}).get("group_count") or 0)
    if tasks:
        expected_tasks = len({row.get("task_plan_group_id") for row in tasks if row.get("task_plan_group_id")})
    expected_counts = {
        "projects": 1,
        "workpackages": 1,
        "tasks": persisted_counts["tasks"] if persisted_counts["tasks"] else expected_tasks,
        "apparatus": expected_apparatus,
    }

    return {
        "classification": "task_plan_persisted" if current_candidate_match else "task_plan_record_stale",
        "route": TASK_PLAN_STATUS_ROUTE,
        "task_plan_route": TASK_PLAN_ROUTE,
        "task_plan_authority": project.get("task_plan_authority") or TASK_PLAN_AUTHORITY,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "project_id": project_id,
        "mutation_id": project.get("task_plan_mutation_id"),
        "audit_event_id": project.get("task_plan_audit_event_id"),
        "expected_row_counts": expected_counts,
        "persisted_row_counts": persisted_counts,
        "current_candidate_match": current_candidate_match,
        "planning_context_only": bool(project.get("planning_context_only")),
        "blocked_downstream": list(project.get("blocked_downstream") or []),
        "persisted_at": project.get("persisted_at"),
        "review_notes": payload.get("review_notes"),
    }


async def persist_project_import_task_plan(request: MutationRequest, actor: Actor) -> MutationResponse:
    if request.action_type != TASK_PLAN_ACTION_TYPE:
        response = _invalid_payload_response(
            request,
            f"Unknown action type for {TASK_PLAN_ENTITY_TYPE}: {request.action_type}",
        )
        save_idempotency(request.idempotency_key, response)
        return response

    existing_response = check_idempotency(request.idempotency_key)
    if existing_response:
        return MutationResponse(
            status="idempotent_hit",
            mutation_id=existing_response.mutation_id,
            entity_id=existing_response.entity_id,
            entity_type=existing_response.entity_type,
            action_type=existing_response.action_type,
            new_state=existing_response.new_state,
            audit_event_id=existing_response.audit_event_id,
        )

    if request.source == "offline_queue":
        response = error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Project import task plan persistence cannot be queued offline.",
            entity_id=request.entity_id or "unknown",
            entity_type=TASK_PLAN_ENTITY_TYPE,
            action_type=request.action_type,
        )
        save_idempotency(request.idempotency_key, response)
        return response

    if request.mutation_class != "C":
        response = error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message="Project import task plan persistence requires mutation_class C.",
            entity_id=request.entity_id or "unknown",
            entity_type=TASK_PLAN_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"declared_class": request.mutation_class},
        )
        save_idempotency(request.idempotency_key, response)
        return response

    if actor.actor_role != "pm":
        response = error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message="Only PM actors can persist Project Miner task plans.",
            entity_id=request.entity_id or "unknown",
            entity_type=TASK_PLAN_ENTITY_TYPE,
            action_type=request.action_type,
            detail={"actor_role": actor.actor_role},
        )
        save_idempotency(request.idempotency_key, response)
        return response

    candidate = load_project_import_candidate()
    project_id = build_project_import_task_plan_id(candidate)
    if request.entity_id and request.entity_id != project_id:
        response = _invalid_payload_response(
            request,
            "entity_id must match the deterministic Project Miner task-plan project id when provided.",
            detail={"expected_entity_id": project_id, "provided_entity_id": request.entity_id},
        )
        save_idempotency(request.idempotency_key, response)
        return response

    payload_error, normalized_payload = _validate_payload(request=request, payload=request.payload, candidate=candidate)
    if payload_error or normalized_payload is None:
        save_idempotency(request.idempotency_key, payload_error)
        return payload_error

    existing = _existing_project_rows(project_id)
    if existing:
        if not _existing_task_plan_matches(existing, normalized_payload):
            response = error_response(
                code=ErrorCode.IDEMPOTENCY_DUPLICATE,
                message="Existing Project Miner task plan does not match the submitted task-plan payload.",
                entity_id=project_id,
                entity_type=TASK_PLAN_ENTITY_TYPE,
                action_type=request.action_type,
                detail={"project_id": project_id},
            )
            save_idempotency(request.idempotency_key, response)
            return response

        replay_state = {
            "status": "accepted",
            "route": TASK_PLAN_ROUTE,
            "task_plan_authority": existing.get("task_plan_authority") or TASK_PLAN_AUTHORITY,
            "project_id": project_id,
            "candidate_id": candidate.get("candidate_id"),
            "row_counts": load_project_import_task_plan_status().get("persisted_row_counts"),
        }
        response = MutationResponse(
            status="accepted",
            mutation_id=str(existing.get("task_plan_mutation_id") or f"mut-{uuid4()}"),
            entity_id=project_id,
            entity_type=TASK_PLAN_ENTITY_TYPE,
            action_type=request.action_type,
            new_state=replay_state,
            audit_event_id=str(existing.get("task_plan_audit_event_id") or f"audit-{uuid4()}"),
        )
        save_idempotency(request.idempotency_key, response)
        return response

    persisted_at = _server_timestamp()
    rows = _build_rows(candidate=candidate, task_plan_payload=normalized_payload, actor=actor, persisted_at=persisted_at)
    mutation_id = f"mut-{uuid4()}"
    audit_event_id = f"audit-{uuid4()}"
    rows["project"]["task_plan_mutation_id"] = mutation_id
    rows["project"]["task_plan_audit_event_id"] = audit_event_id
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
        entity_type=TASK_PLAN_ENTITY_TYPE,
    )

    response = MutationResponse(
        status="accepted",
        mutation_id=mutation_id,
        entity_id=project_id,
        entity_type=TASK_PLAN_ENTITY_TYPE,
        action_type=request.action_type,
        new_state=response_state,
        audit_event_id=audit_event_id,
    )
    save_idempotency(request.idempotency_key, response)
    return response