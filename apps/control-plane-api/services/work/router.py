"""
PM/Work Domain — FastAPI Router
================================
Packet: 2026-04-13-pm-schema-010b (original read-only surface)
Updated: 2026-04-14-pm-schema-011f (project write endpoints)
Updated: 2026-04-14-pm-schema-013 (work-package write endpoints — minimal)
Updated: 2026-04-14-pm-schema-014 (task write endpoints — minimal)
Updated: 2026-04-15-pm-schema-015 (assignment write endpoints — minimal)
Updated: 2026-04-15-pm-schema-016 (dependency write endpoints — minimal)
Updated: 2026-04-15-pm-schema-017 (execution-issue write endpoints — minimal)
Updated: 2026-04-15-pm-schema-018 (progress-snapshot write endpoints — minimal)
Updated: 2026-04-16-pm-schema-019 (idempotency seam on 7 POST handlers)
Updated: 2026-04-16-pm-schema-019f (idempotency seam moved to durable DB-backed store)
Authority: 2026-04-13-pm-schema-010a (ORM + schemas),
           2026-04-14-pm-schema-011e (org ORM alignment),
           2026-04-14-pm-schema-011f (project write API),
           2026-04-14-pm-schema-012e (identity ORM alignment),
           2026-04-14-pm-schema-013 (work-package write API),
           2026-04-14-pm-schema-014 (task write API),
           2026-04-15-pm-schema-015 (assignment write API),
           2026-04-15-pm-schema-016 (dependency write API),
           2026-04-15-pm-schema-017 (execution-issue write API),
           2026-04-15-pm-schema-018 (progress-snapshot write API)

Mounts under /api/v1/work/.

Read endpoints (11 GET, all entities):
  GET /api/v1/work/projects                 — list projects
  GET /api/v1/work/projects/{project_id}    — get project
  GET /api/v1/work/wbs-nodes                — list WBS nodes (filterable by project)
  GET /api/v1/work/work-packages            — list work packages (filterable by project)
  GET /api/v1/work/work-packages/{id}       — get work package
  GET /api/v1/work/tasks                    — list tasks (filterable by work package)
  GET /api/v1/work/tasks/{task_id}          — get task
  GET /api/v1/work/dependencies             — list dependencies (filterable)
  GET /api/v1/work/assignments              — list assignments (filterable)
  GET /api/v1/work/execution-issues         — list execution issues (filterable)
  GET /api/v1/work/progress-snapshots       — list progress snapshots (filterable)

Write endpoints (14, projects + work packages + tasks + assignments +
dependencies + execution issues + progress snapshots only):
  POST  /api/v1/work/projects                                  — create project (packet 011f)
  PATCH /api/v1/work/projects/{project_id}                     — update project (packet 011f)
  POST  /api/v1/work/work-packages                             — create work package (packet 013)
  PATCH /api/v1/work/work-packages/{work_package_id}           — update work package (packet 013)
  POST  /api/v1/work/tasks                                     — create task (packet 014)
  PATCH /api/v1/work/tasks/{task_id}                           — update task (packet 014)
  POST  /api/v1/work/assignments                               — create assignment (packet 015)
  PATCH /api/v1/work/assignments/{assignment_id}               — update assignment (packet 015)
  POST  /api/v1/work/dependencies                              — create dependency (packet 016)
  PATCH /api/v1/work/dependencies/{dependency_id}              — update dependency (packet 016)
  POST  /api/v1/work/execution-issues                          — create execution issue (packet 017)
  PATCH /api/v1/work/execution-issues/{execution_issue_id}     — update execution issue (packet 017)
  POST  /api/v1/work/progress-snapshots                        — create progress snapshot (packet 018)
  PATCH /api/v1/work/progress-snapshots/{progress_snapshot_id} — update progress snapshot (packet 018)

Hard constraints:
  - Write endpoints for projects, work packages, tasks, assignments,
    dependencies, execution issues, and progress snapshots only — no
    WBS-node writes
  - Org, identity, and intra-work FK references validated before persist
  - Dependency no-self-cycle rule mirrored at the API boundary on create
    (Pydantic model_validator) and on update (service-layer effective-pair
    check)
  - Execution-issue at-least-one-parent rule mirrored at the API boundary
    on create (Pydantic model_validator) — parity with the assignment
    create contract
  - Progress-snapshot period-monotonicity rule mirrored at the API
    boundary on create (Pydantic model_validator) and on update
    (service-layer effective-pair check); progress-snapshot self-reference
    (superseding itself) is blocked on update via an effective-pair check
    at the service layer
  - No background jobs or write side effects
  - No cross-domain dependency activation
"""

import json as _json
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from config import get_db
from .idempotency import (
    IDEMPOTENCY_HEADER,
    idempotency_cache,
)
from .queries import (
    list_projects, get_project,
    list_wbs_nodes,
    list_work_packages, get_work_package,
    list_tasks, get_task,
    list_dependencies,
    list_assignments,
    list_execution_issues,
    list_progress_snapshots,
)
from .mutations import (
    create_project as svc_create_project,
    update_project as svc_update_project,
    create_work_package as svc_create_work_package,
    update_work_package as svc_update_work_package,
    create_task as svc_create_task,
    update_task as svc_update_task,
    create_assignment as svc_create_assignment,
    update_assignment as svc_update_assignment,
    create_dependency as svc_create_dependency,
    update_dependency as svc_update_dependency,
    create_execution_issue as svc_create_execution_issue,
    update_execution_issue as svc_update_execution_issue,
    create_progress_snapshot as svc_create_progress_snapshot,
    update_progress_snapshot as svc_update_progress_snapshot,
    OrgValidationError,
)
from .schemas import (
    ProjectRead, ProjectCreate, ProjectUpdate,
    WBSNodeRead,
    WorkPackageRead, WorkPackageCreate, WorkPackageUpdate,
    TaskRead, TaskCreate, TaskUpdate,
    DependencyRead, DependencyCreate, DependencyUpdate,
    AssignmentRead, AssignmentCreate, AssignmentUpdate,
    ExecutionIssueRead, ExecutionIssueCreate, ExecutionIssueUpdate,
    ProgressSnapshotRead, ProgressSnapshotCreate, ProgressSnapshotUpdate,
)


router = APIRouter(prefix="/api/v1/work", tags=["work"])


# ---------------------------------------------------------------------------
# Idempotency seam (packet 019; packet 019f made it durable)
# ---------------------------------------------------------------------------
#
# A shared pre/post/discard triple wraps each of the seven PM POST
# handlers.  The seam activates only when the caller supplies an
# ``Idempotency-Key`` header; otherwise each handler behaves exactly as
# before.  The cache backing (in-memory vs. durable ``pm.idempotency_keys``)
# is selected at app init — see ``services.work.idempotency``.  Validation-
# failure 422s are explicitly NOT persisted: ``_idempotency_discard``
# removes the pre-registered row so callers can retry the same key with
# a corrected payload.
#
# Cache-key namespace uses the logical route path (e.g. ``"/projects"``,
# ``"/work-packages"``) so the same Idempotency-Key can be reused across
# different POST endpoints without collision — parity with Stripe-style
# per-endpoint semantics.

_IDEMPOTENCY_MISMATCH_BODY = {
    "detail": "Idempotency-Key reused with different payload",
    "errors": {
        "idempotency_key": (
            "Idempotency-Key reused with different payload"
        ),
    },
}


async def _idempotency_precheck(
    route: str, request: Request,
) -> tuple[Optional[Response], Optional[str], bytes]:
    """Register an incoming POST with the idempotency cache.

    Returns a ``(early_response, key, body_bytes)`` triple:

      * ``early_response`` is non-None when the caller should return
        immediately — either a cached replay (same status + JSON body as
        the original success response) or a ``422`` mismatch response
        when the key has been seen with a different payload.
      * ``key`` is the ``Idempotency-Key`` header value when present, or
        ``None`` when the caller omitted it.  Passed back through to
        ``_idempotency_record`` so the record-side can no-op cheaply.
      * ``body_bytes`` is the raw request body (cached by Starlette), or
        ``b""`` when no key was supplied.  Also passed back through to
        ``_idempotency_record`` so the recorded body hash matches the
        registered body hash.
    """
    key = request.headers.get(IDEMPOTENCY_HEADER)
    if not key:
        return (None, None, b"")
    body_bytes = await request.body()
    hit = idempotency_cache.register_request(route, key, body_bytes)
    if hit is None:
        return (None, key, body_bytes)
    if not hit.match:
        return (
            JSONResponse(
                status_code=422, content=_IDEMPOTENCY_MISMATCH_BODY,
            ),
            key,
            body_bytes,
        )
    if hit.status is not None and hit.response_body is not None:
        return (
            Response(
                content=hit.response_body,
                status_code=hit.status,
                media_type="application/json",
            ),
            key,
            body_bytes,
        )
    # Key seen but response not yet recorded (in-flight or prior error);
    # let the handler run and rely on record_response overwriting.
    return (None, key, body_bytes)


def _idempotency_record(
    route: str,
    key: Optional[str],
    body_bytes: bytes,
    model_cls: Any,
    orm_obj: Any,
    status: int = 201,
) -> Response:
    """Serialize a success response via ``model_cls`` and cache the bytes.

    Returns a ``Response`` whose body is byte-for-byte identical to the
    bytes recorded in the cache, so subsequent replays (via the pre-check
    above) return the same payload.  When ``key`` is ``None`` the cache
    is not touched — the Response is still returned so the handler can
    uniformly return a single shape in both the idempotent and
    non-idempotent code paths.
    """
    validated = model_cls.model_validate(orm_obj)
    encoded = jsonable_encoder(validated)
    response_bytes = _json.dumps(encoded).encode("utf-8")
    if key is not None:
        idempotency_cache.record_response(
            route, key, body_bytes, status, response_bytes,
        )
    return Response(
        content=response_bytes,
        status_code=status,
        media_type="application/json",
    )


def _idempotency_discard(
    route: str, key: Optional[str], body_bytes: bytes,
) -> None:
    """Remove a pre-registered idempotency row when the handler produced
    a validation-failure 422.

    Called from the ``except OrgValidationError`` branch of every POST
    handler before the 422 response is returned.  No-ops when ``key`` is
    ``None`` (caller never set the header) so uniform call sites remain
    cheap in the non-idempotent path.  The backend's discard
    implementation is gated on ``response_status IS NULL`` so an
    already-committed success replay row is never evicted.
    """
    if key is None:
        return
    idempotency_cache.discard_registration(route, key, body_bytes)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.get("/projects", response_model=list[ProjectRead])
def read_projects(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all projects, ordered by most recently created."""
    return list_projects(db, limit=limit, offset=offset)


@router.get("/projects/{project_id}", response_model=ProjectRead)
def read_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get a single project by ID."""
    row = get_project(db, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


@router.post("/projects", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new project.

    Validates org FK references (client_id, site_id, and optional
    business_unit_id, contract_id) against the org domain before persist.
    Returns 422 with field-level error details if any org reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).  When
    present, a repeat request with the same key + payload returns the
    cached response verbatim; a repeat with the same key but different
    payload returns 422.
    """
    early, key, body_bytes = await _idempotency_precheck("/projects", request)
    if early is not None:
        return early
    try:
        project = svc_create_project(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/projects", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid org references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/projects", key, body_bytes, ProjectRead, project,
        )
    return project


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a project.

    Only fields present in the request body are applied.
    Validates any org FK references that are being changed.
    Returns 404 if the project does not exist.
    Returns 422 with field-level error details if any org reference is invalid.
    """
    try:
        project = svc_update_project(db, project_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid org references", "errors": e.errors},
        )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# WBS Nodes
# ---------------------------------------------------------------------------

@router.get("/wbs-nodes", response_model=list[WBSNodeRead])
def read_wbs_nodes(
    project_id: Optional[UUID] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List WBS nodes, optionally filtered by project."""
    return list_wbs_nodes(db, project_id=project_id, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Work Packages
# ---------------------------------------------------------------------------

@router.get("/work-packages", response_model=list[WorkPackageRead])
def read_work_packages(
    project_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List work packages, optionally filtered by project."""
    return list_work_packages(db, project_id=project_id, limit=limit, offset=offset)


@router.get("/work-packages/{work_package_id}", response_model=WorkPackageRead)
def read_work_package(work_package_id: UUID, db: Session = Depends(get_db)):
    """Get a single work package by ID."""
    row = get_work_package(db, work_package_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    return row


@router.post("/work-packages", response_model=WorkPackageRead, status_code=201)
async def create_work_package(
    payload: WorkPackageCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new work package.

    Validates references before persist:
      - org FKs: client_id, site_id (required)
      - intra-work FKs: project_id (required), primary_wbs_node_id (optional)
      - identity FKs: assigned_crew_id (optional)
    Returns 422 with field-level error details if any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck(
        "/work-packages", request,
    )
    if early is not None:
        return early
    try:
        work_package = svc_create_work_package(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/work-packages", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/work-packages", key, body_bytes, WorkPackageRead, work_package,
        )
    return work_package


@router.patch("/work-packages/{work_package_id}", response_model=WorkPackageRead)
def update_work_package(
    work_package_id: UUID,
    payload: WorkPackageUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a work package.

    Only fields present in the request body are applied.
    Validates any supplied org, intra-work, or identity FK references.
    Returns 404 if the work package does not exist.
    Returns 422 with field-level error details if any reference is invalid.
    """
    try:
        work_package = svc_update_work_package(db, work_package_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if work_package is None:
        raise HTTPException(status_code=404, detail="Work package not found")
    return work_package


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.get("/tasks", response_model=list[TaskRead])
def read_tasks(
    work_package_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List tasks, optionally filtered by work package."""
    return list_tasks(db, work_package_id=work_package_id, limit=limit, offset=offset)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    row = get_task(db, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@router.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new task.

    Validates intra-work FK references before persist:
      - work_package_id (required)
      - primary_wbs_node_id (optional)
    Returns 422 with field-level error details if any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck("/tasks", request)
    if early is not None:
        return early
    try:
        task = svc_create_task(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/tasks", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/tasks", key, body_bytes, TaskRead, task,
        )
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a task.

    Only fields present in the request body are applied.
    Validates any supplied intra-work FK references
    (work_package_id, primary_wbs_node_id).
    Returns 404 if the task does not exist.
    Returns 422 with field-level error details if any reference is invalid.
    """
    try:
        task = svc_update_task(db, task_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

@router.get("/dependencies", response_model=list[DependencyRead])
def read_dependencies(
    predecessor_task_id: Optional[UUID] = Query(None),
    successor_task_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List task dependencies, optionally filtered by predecessor or successor."""
    return list_dependencies(
        db,
        predecessor_task_id=predecessor_task_id,
        successor_task_id=successor_task_id,
        limit=limit, offset=offset,
    )


@router.post("/dependencies", response_model=DependencyRead, status_code=201)
async def create_dependency(
    payload: DependencyCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new task dependency.

    Validates intra-work FK references before persist:
      - predecessor_task_id (required)
      - successor_task_id (required)
    The DependencyCreate Pydantic contract also rejects self-referential
    requests (predecessor_task_id == successor_task_id) at the API
    boundary, mirroring the DDL intent.
    Returns 422 with field-level error details if any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck(
        "/dependencies", request,
    )
    if early is not None:
        return early
    try:
        dependency = svc_create_dependency(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/dependencies", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/dependencies", key, body_bytes, DependencyRead, dependency,
        )
    return dependency


@router.patch("/dependencies/{dependency_id}", response_model=DependencyRead)
def update_dependency(
    dependency_id: UUID,
    payload: DependencyUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a task dependency.

    Only fields present in the request body are applied.
    Validates any supplied intra-work FK references (predecessor_task_id,
    successor_task_id) and re-checks the no-self-cycle rule against the
    effective (post-patch) predecessor/successor pair.
    Returns 404 if the dependency does not exist.
    Returns 422 with field-level error details if any reference is invalid
    or the effective pair collapses to a self-cycle.
    """
    try:
        dependency = svc_update_dependency(db, dependency_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if dependency is None:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return dependency


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------

@router.get("/assignments", response_model=list[AssignmentRead])
def read_assignments(
    work_package_id: Optional[UUID] = Query(None),
    task_id: Optional[UUID] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List assignments, optionally filtered by work package or task."""
    return list_assignments(
        db,
        work_package_id=work_package_id,
        task_id=task_id,
        limit=limit, offset=offset,
    )


@router.post("/assignments", response_model=AssignmentRead, status_code=201)
async def create_assignment(
    payload: AssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new assignment.

    Validates references before persist:
      - intra-work FKs: work_package_id and task_id (at least one required
        by the AssignmentCreate Pydantic contract — mirrors the DDL
        ``ck_assignments_at_least_one_parent`` check constraint)
      - identity FKs: employee_id, crew_id (optional)
    Returns 422 with field-level error details if any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck(
        "/assignments", request,
    )
    if early is not None:
        return early
    try:
        assignment = svc_create_assignment(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/assignments", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/assignments", key, body_bytes, AssignmentRead, assignment,
        )
    return assignment


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an assignment.

    Only fields present in the request body are applied.
    Validates any supplied intra-work (work_package_id, task_id) and
    identity (employee_id, crew_id) FK references.
    Returns 404 if the assignment does not exist.
    Returns 422 with field-level error details if any reference is invalid.
    """
    try:
        assignment = svc_update_assignment(db, assignment_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


# ---------------------------------------------------------------------------
# Execution Issues
# ---------------------------------------------------------------------------

@router.get("/execution-issues", response_model=list[ExecutionIssueRead])
def read_execution_issues(
    work_package_id: Optional[UUID] = Query(None),
    task_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List execution issues, optionally filtered by work package or task."""
    return list_execution_issues(
        db,
        work_package_id=work_package_id,
        task_id=task_id,
        limit=limit, offset=offset,
    )


@router.post(
    "/execution-issues", response_model=ExecutionIssueRead, status_code=201,
)
async def create_execution_issue(
    payload: ExecutionIssueCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new execution issue.

    Validates references before persist:
      - intra-work FKs: work_package_id and task_id (at least one required
        by the ExecutionIssueCreate Pydantic contract — mirrors the DDL
        ``ck_execution_issues_at_least_one_parent`` check constraint)
    Returns 422 with field-level error details if any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck(
        "/execution-issues", request,
    )
    if early is not None:
        return early
    try:
        issue = svc_create_execution_issue(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/execution-issues", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/execution-issues", key, body_bytes, ExecutionIssueRead, issue,
        )
    return issue


@router.patch(
    "/execution-issues/{execution_issue_id}",
    response_model=ExecutionIssueRead,
)
def update_execution_issue(
    execution_issue_id: UUID,
    payload: ExecutionIssueUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an execution issue.

    Only fields present in the request body are applied.
    Validates any supplied intra-work (work_package_id, task_id) FK
    references.
    Returns 404 if the execution issue does not exist.
    Returns 422 with field-level error details if any reference is invalid.
    """
    try:
        issue = svc_update_execution_issue(db, execution_issue_id, payload)
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if issue is None:
        raise HTTPException(status_code=404, detail="Execution issue not found")
    return issue


# ---------------------------------------------------------------------------
# Progress Snapshots
# ---------------------------------------------------------------------------

@router.get("/progress-snapshots", response_model=list[ProgressSnapshotRead])
def read_progress_snapshots(
    project_id: Optional[UUID] = Query(None),
    work_package_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List progress snapshots, optionally filtered by project or work package."""
    return list_progress_snapshots(
        db,
        project_id=project_id,
        work_package_id=work_package_id,
        limit=limit, offset=offset,
    )


@router.post(
    "/progress-snapshots", response_model=ProgressSnapshotRead, status_code=201,
)
async def create_progress_snapshot(
    payload: ProgressSnapshotCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new progress snapshot.

    Validates references before persist:
      - project_id (required, work.projects)
      - work_package_id (optional, work.work_packages)
      - task_id (optional, work.tasks)
      - supersedes_snapshot_id (optional, work.progress_snapshots self-ref)
      - approved_by (optional, identity.users)

    The period-monotonicity rule ``snapshot_period_end >=
    snapshot_period_start`` is enforced by the ProgressSnapshotCreate
    Pydantic contract at the API boundary (mirrors the DDL
    ``ck_progress_snapshots_period`` check constraint) so callers get a
    422 before persist.  Returns 422 with field-level error details if
    any reference is invalid.

    Accepts an optional ``Idempotency-Key`` header (packet 019).
    """
    early, key, body_bytes = await _idempotency_precheck(
        "/progress-snapshots", request,
    )
    if early is not None:
        return early
    try:
        snapshot = svc_create_progress_snapshot(db, payload)
    except OrgValidationError as e:
        _idempotency_discard("/progress-snapshots", key, body_bytes)
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if key is not None:
        return _idempotency_record(
            "/progress-snapshots",
            key, body_bytes, ProgressSnapshotRead, snapshot,
        )
    return snapshot


@router.patch(
    "/progress-snapshots/{progress_snapshot_id}",
    response_model=ProgressSnapshotRead,
)
def update_progress_snapshot(
    progress_snapshot_id: UUID,
    payload: ProgressSnapshotUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a progress snapshot.

    Only fields present in the request body are applied.
    Validates any supplied FK references (project_id, work_package_id,
    task_id, supersedes_snapshot_id, approved_by) and enforces the
    service-layer self-reference guard (a snapshot cannot supersede
    itself) and period-monotonicity guard (effective end >= effective
    start, using the existing row's bound for an unsupplied end).
    Returns 404 if the progress snapshot does not exist.
    Returns 422 with field-level error details if any reference or rule
    is violated.
    """
    try:
        snapshot = svc_update_progress_snapshot(
            db, progress_snapshot_id, payload,
        )
    except OrgValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid references", "errors": e.errors},
        )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Progress snapshot not found")
    return snapshot
