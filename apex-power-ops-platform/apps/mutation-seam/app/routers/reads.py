"""
Read-only endpoints for prototype data access.
In production, reads go through Supabase directly via RLS.
For the prototype, we expose the in-memory store.
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict, List

from app.auth.jwt import Actor, get_current_actor
from app.db.memory_store import store

router = APIRouter(prefix="/api/v1/reads", tags=["reads"])


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
    """List available crew members (prototype seed data)."""
    return [
        {"id": "tech-001", "name": "Alex Rivera", "role": "field_tech"},
        {"id": "tech-002", "name": "Sam Chen", "role": "field_tech"},
        {"id": "tech-003", "name": "Jordan Bell", "role": "field_tech"},
    ]


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
async def get_decision_history(actor: Actor = Depends(get_current_actor)) -> List[Dict[str, Any]]:
    """
    PM decision history: audit trail of Class C approval/rejection/escalation actions.
    """
    pm_actions = {"approve", "reject", "escalate_review", "resolve_escalated", "re_escalate", "return_to_lead"}
    history = [
        e for e in store.audit_log
        if e.get("action_type") in pm_actions or e.get("actor_role") == "pm"
    ]
    return sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)


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
