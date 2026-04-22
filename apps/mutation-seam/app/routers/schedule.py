"""
Read-only schedule-context router — packet UI-002a.

This router exposes P6-derived planning context (imported by
`app.schedule.loader`) to PM-facing surfaces.

Posture (see Source-Of-Truth memo §3 + packet UI-002a):
    * GET-only. No POST/PUT/PATCH/DELETE here. A defensive
      `default_transaction_read_only = on` is also set by the underlying
      query helpers.
    * Reads `schedule.*` exclusively. Joined reads against `seam.*` are
      LEFT joins so seam rows are never required and never mutated.
    * Mounted at `/api/v1/schedule` so it is linearly separable from the
      governed mutation paths under `/api/v1/mutations/*`.
    * Authentication reuses the same `get_current_actor` dependency as
      the other read endpoints — no elevated authority is granted.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.jwt import Actor, get_current_actor
from app.schedule import queries as sched_q


router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])


def _safe_call(fn, *args, **kwargs):
    """Call a query helper, converting RuntimeError (missing DSN, missing
    psycopg2, etc.) into a 503 so the frontend surfaces 'bridge not
    configured' rather than a generic 500."""
    try:
        return fn(*args, **kwargs)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/projects")
async def list_projects(
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """List all imported P6 projects."""
    return _safe_call(sched_q.list_projects)


@router.get("/projects/{schedule_project_id}")
async def get_project(
    schedule_project_id: str,
    actor: Actor = Depends(get_current_actor),
) -> Dict[str, Any]:
    """Return a single imported P6 project by schedule id."""
    row = _safe_call(sched_q.get_project, schedule_project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="schedule_project_not_found")
    return row


@router.get("/projects/{schedule_project_id}/wbs")
async def list_wbs(
    schedule_project_id: str,
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """Return the WBS hierarchy for a schedule project."""
    return _safe_call(sched_q.list_wbs, schedule_project_id)


@router.get("/tasks")
async def list_tasks(
    schedule_project_id: Optional[str] = Query(None, alias="project_id"),
    critical_only: bool = Query(False),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """List schedule tasks. Filter by project and/or critical-only."""
    return _safe_call(
        sched_q.list_tasks,
        schedule_project_id=schedule_project_id,
        critical_only=critical_only,
    )


@router.get("/tasks-with-scope")
async def list_tasks_with_scope(
    schedule_project_id: Optional[str] = Query(None, alias="project_id"),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """Joined read: schedule.tasks LEFT JOIN seam.tasks. Seam rows are read-only."""
    return _safe_call(
        sched_q.list_tasks_with_scope,
        schedule_project_id=schedule_project_id,
    )


@router.get("/relationships")
async def list_relationships(
    schedule_project_id: Optional[str] = Query(None, alias="project_id"),
    task_id: Optional[str] = Query(None),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """List P6 FS/SS/FF/SF relationships with lag."""
    return _safe_call(
        sched_q.list_relationships,
        schedule_project_id=schedule_project_id,
        task_id=task_id,
    )


@router.get("/drivers")
async def list_drivers(
    schedule_project_id: Optional[str] = Query(None, alias="project_id"),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """List critical-path driving edges (packet UI-002e first slice).

    An edge is "driving" when the predecessor sits on the critical path.
    Read-only; derived from persisted ``schedule.relationships`` +
    ``schedule.tasks``; does NOT fabricate dependency semantics client-side
    and does NOT expose the full TASKPRED graph.
    """
    return _safe_call(
        sched_q.list_driver_edges,
        schedule_project_id=schedule_project_id,
    )


@router.get("/tracer")
async def list_tracer(
    task_id: str = Query(..., description="Selected schedule task id to trace upstream from"),
    max_depth: int = Query(10, ge=1, le=25),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """Return the bounded upstream predecessor chain for a selected task
    (packet UI-002f first slice — bounded ancestor chain).

    Walks `schedule.relationships` recursively from the selected task
    backwards. Read-only; depth is capped (router enforces `<= 25`, the
    helper enforces its own hard cap). Does NOT fabricate graph semantics
    client-side; every edge comes from persisted schedule data.
    """
    return _safe_call(
        sched_q.list_tracer_chain,
        task_id=task_id,
        max_depth=max_depth,
    )


@router.get("/variance")
async def list_variance(
    schedule_project_id: Optional[str] = Query(None, alias="project_id"),
    with_baseline_only: bool = Query(
        False,
        description="If true, omit tasks with no persisted baseline pair",
    ),
    only_slipping: bool = Query(
        False,
        description=(
            "If true, return only tasks whose current planned finish is "
            "strictly after their persisted baseline end"
        ),
    ),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """Return per-task current-vs-baseline variance rows
    (packet UI-002g first slice — comparative schedule analytics).

    Every variance field is derived from persisted schedule data:
    ``planned_start`` / ``planned_finish`` on the current task row vs
    ``baseline_start_at`` / ``baseline_end_at`` carried by the same row.
    NULL baselines pass through as NULL variance — the client MUST render
    nothing in that case. Read-only; no fabrication; no reliance on any
    degraded third-party delta export.
    """
    return _safe_call(
        sched_q.list_variance_rows,
        schedule_project_id=schedule_project_id,
        with_baseline_only=with_baseline_only,
        only_slipping=only_slipping,
    )


@router.get("/sync-log")
async def list_sync_log(
    limit: int = Query(20, ge=1, le=200),
    actor: Actor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """Return the most recent sync_log entries (integration ledger, display-only)."""
    return _safe_call(sched_q.list_sync_log, limit)
