"""
Read-only endpoints for prototype data access.
In production, reads go through Supabase directly via RLS.
For the prototype, we expose the in-memory store.
"""
from fastapi import APIRouter, Depends, Query
from typing import Any, Dict, List

from app.auth.jwt import Actor, get_current_actor
from app.db.memory_store import store
from app.pm_workfront_read_model import build_pm_workfront_read_model
from app.project_import_admission_plan import load_project_import_admission_plan
from app.project_import_approval_contract import load_project_import_approval_contract
from app.project_import_approval_persistence import load_project_import_approval_status
from app.project_import_approval_storage_plan import load_project_import_approval_storage_plan
from app.project_import_candidate import load_project_import_candidate
from app.project_seed_sources import load_project_seed_sources
from app.seed_workbooks import load_seed_data

router = APIRouter(prefix="/api/v1/reads", tags=["reads"])


PM_DECISION_ACTIONS = {"approve", "reject", "escalate_review", "resolve_escalated", "re_escalate", "return_to_lead"}
DECISION_HISTORY_LIMIT_MAX = 100


def _audit_event_timestamp(event: Dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("server_timestamp") or event.get("client_timestamp") or "")


def _decision_history_row(event: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(event)
    row["timestamp"] = _audit_event_timestamp(row)
    return row


@router.get("/apparatus")
async def list_apparatus(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all apparatus in the store."""
    return list(store.apparatus.values())


@router.get("/apparatus/{apparatus_id}")
async def get_apparatus(apparatus_id: str, actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Get a single apparatus by ID."""
    if apparatus_id not in store.apparatus:
        return {"error": "not_found"}
    return store.apparatus[apparatus_id]


@router.get("/assignments")
async def list_assignments(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all assignments."""
    return list(store.assignments.values())


@router.get("/tasks")
async def list_tasks(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all tasks."""
    return list(store.tasks.values())


@router.get("/workpackages")
async def list_workpackages(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all workpackages."""
    return list(store.workpackages.values())


@router.get("/issues")
async def list_issues(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all issues."""
    return list(store.issues.values())


@router.get("/checklist/{apparatus_id}")
async def list_checklist_for_apparatus(apparatus_id: str, actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List checklist items for an apparatus."""
    return [item for item in store.checklist_items.values() if item.get("apparatus_id") == apparatus_id]


@router.get("/hours")
async def list_hours(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all hours entries."""
    return list(store.hours.values())


@router.get("/crew")
async def list_crew(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List available crew members from the workbook-backed field seed when present."""
    return load_seed_data()["crew"]


@router.get("/equipment-inventory")
async def list_equipment_inventory(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List workbook-backed equipment inventory rows for field seed hydration."""
    return load_seed_data()["equipment_inventory"]


@router.get("/tech-capabilities")
async def list_tech_capabilities(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """List workbook-backed technician capability rows and score scale."""
    seed = load_seed_data()
    return {
        "crew": seed["crew"],
        "score_scale": seed["capability_score_scale"],
        "capabilities": seed["tech_capabilities"],
    }


@router.get("/project-apparatus-plan")
async def get_project_apparatus_plan(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return the workbook-backed project apparatus plan plus SLD-derived topology labels."""
    return load_project_seed_sources()


@router.get("/project-import-candidate")
async def get_project_import_candidate(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return a read-only Project Miner import candidate for PM review before any import mutation."""
    return load_project_import_candidate()


@router.get("/project-import-admission-plan")
async def get_project_import_admission_plan(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return a read-only import-admission plan for PM approval and future idempotent import design."""
    return load_project_import_admission_plan()


@router.get("/project-import-approval-contract")
async def get_project_import_approval_contract(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return a read-only approval-persistence contract for a future PM import approval."""
    return load_project_import_approval_contract()


@router.get("/project-import-approval-storage-plan")
async def get_project_import_approval_storage_plan(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return a read-only storage decision plan for future PM import approval persistence."""
    return load_project_import_approval_storage_plan()


@router.get("/project-import-approval-status")
async def get_project_import_approval_status(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return read-only approval persistence status for the current Project Miner import candidate."""
    return load_project_import_approval_status()


@router.get("/pm-workfront")
async def get_pm_workfront(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """Return a read-only PM workfront projection for apparatus readiness triage."""
    return build_pm_workfront_read_model(
        apparatus_rows=list(store.apparatus.values()),
        assignment_rows=list(store.assignments.values()),
        task_rows=list(store.tasks.values()),
        workpackage_rows=list(store.workpackages.values()),
        issue_rows=list(store.issues.values()),
        checklist_rows=list(store.checklist_items.values()),
        audit_rows=list(store.audit_log),
    )


@router.get("/snapshots")
async def list_snapshots(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """List all progress snapshots."""
    return list(store.snapshots.values())


@router.get("/approval-queue")
async def get_approval_queue(actor: Actor = Depends(get_current_actor)) -> Dict[str, Any]:
    """
    PM approval queue: all entities awaiting PM review.
    """
    awaiting_tasks = [t for t in store.tasks.values() if t.get("status") == "awaiting_review"]
    awaiting_wps = [w for w in store.workpackages.values() if w.get("status") == "awaiting_review"]
    submitted_snapshots = [s for s in store.snapshots.values() if s.get("status") == "submitted"]
    escalated_issues = [i for i in store.issues.values() if i.get("status") == "escalated"]
    return {
        "tasks": awaiting_tasks,
        "workpackages": awaiting_wps,
        "snapshots": submitted_snapshots,
        "escalated_issues": escalated_issues,
        "total_count": len(awaiting_tasks) + len(awaiting_wps) + len(submitted_snapshots) + len(escalated_issues),
    }


@router.get("/decision-history")
async def get_decision_history(
    actor: Actor = Depends(get_current_actor),
    entity_id: List[str] | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1),
) -> List[Dict[str, Any]]:
    """
    PM decision history: audit trail of Class C approval/rejection/escalation actions.
    """
    entity_ids = {str(value) for value in entity_id or [] if value}
    history = [
        _decision_history_row(e) for e in store.audit_log
        if (e.get("action_type") in PM_DECISION_ACTIONS or e.get("actor_role") == "pm")
        and (not entity_ids or str(e.get("entity_id") or "") in entity_ids)
    ]
    sorted_history = sorted(history, key=_audit_event_timestamp, reverse=True)
    if limit is not None:
        return sorted_history[:min(limit, DECISION_HISTORY_LIMIT_MAX)]
    return sorted_history


@router.get("/blocking-issues/{entity_type}/{entity_id}")
async def get_blocking_issues(entity_type: str, entity_id: str, actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """Get unresolved blocking issues for a task or workpackage."""
    blocking = []
    if entity_type == "task":
        for issue in store.issues.values():
            if issue.get("blocks_completion") and issue.get("status") not in ("resolved", "closed"):
                app = store.apparatus.get(issue.get("apparatus_id", ""))
                if app and app.get("task_id") == entity_id:
                    blocking.append(issue)
    elif entity_type == "workpackage":
        wp_task_ids = {t["id"] for t in store.tasks.values() if t.get("workpackage_id") == entity_id}
        for issue in store.issues.values():
            if issue.get("blocks_completion") and issue.get("status") not in ("resolved", "closed"):
                app = store.apparatus.get(issue.get("apparatus_id", ""))
                if app and app.get("task_id") in wp_task_ids:
                    blocking.append(issue)
    return blocking
