"""
PM/Work Domain — Project, Work-Package, and Task Write Services
================================================================
Packet: 2026-04-14-pm-schema-011f (project writes)
Packet: 2026-04-14-pm-schema-013 (work-package writes)
Packet: 2026-04-14-pm-schema-013j (work-package response crew/org name enrichment)
Packet: 2026-04-14-pm-schema-014 (task writes — minimal)
Packet: 2026-04-15-pm-schema-015 (assignment writes — minimal)
Packet: 2026-04-15-pm-schema-016 (dependency writes — minimal)
Packet: 2026-04-15-pm-schema-017 (execution-issue writes — minimal)
Packet: 2026-04-15-pm-schema-018 (progress-snapshot writes — minimal)
Packet: 2026-04-16-pm-schema-019 (write-surface consolidation —
        ``_merge_errors`` / ``_raise_if_errors`` helpers, no new surfaces)
Authority: 2026-04-14-pm-schema-011d (FK activation),
           2026-04-14-pm-schema-011e (ORM alignment),
           2026-04-14-pm-schema-012d (identity FK activation),
           2026-04-14-pm-schema-012e (identity ORM alignment),
           2026-04-14-pm-schema-012f (identity-joined read hydration pattern)

Write service functions for work.projects, work.work_packages,
work.tasks, and work.assignments only.

Scope:
  - create_project / update_project: project writes with org FK validation
  - create_work_package / update_work_package: work-package writes with
    org (client, site), identity (crew), and intra-work (project, WBS node)
    FK validation, plus post-commit response enrichment that surfaces
    assigned_crew_name / client_name / site_name using the same
    identity- and org-joined name contracts the read path already exposes
  - create_task / update_task: task writes with merged intra-work FK
    validation for work_package_id (required on create) and
    primary_wbs_node_id (optional) — no new SQL and no broadening of the
    mutation surface into dependencies, issues, or progress snapshots
  - create_assignment / update_assignment: assignment writes with
    merged intra-work FK validation for work_package_id and task_id
    (the DDL check constraint requires at least one parent, enforced
    by the AssignmentCreate Pydantic model on create) plus identity
    FK validation for employee_id and crew_id.  No new SQL and no
    broadening of the mutation surface into issues or progress
    snapshots.
  - create_dependency / update_dependency: dependency writes with
    merged intra-work FK validation for predecessor_task_id and
    successor_task_id (both required NOT NULL by the DDL and enforced
    at the Pydantic layer on create).  The no-self-cycle rule
    (predecessor != successor) is enforced twice: by a Pydantic
    ``model_validator(mode="after")`` on DependencyCreate for full
    payloads, and by a service-layer check on update that evaluates
    the effective (post-patch) pair so partial updates cannot sneak a
    self-referential row past the API boundary.  No new SQL and no
    broadening of the mutation surface into issues or progress
    snapshots.
  - create_execution_issue / update_execution_issue: execution-issue
    writes with merged intra-work FK validation for work_package_id
    and task_id (both individually nullable but constrained by the
    DDL check ``ck_execution_issues_at_least_one_parent`` so at least
    one parent must be present — enforced at the Pydantic layer on
    create).  No new SQL and no broadening of the mutation surface
    into progress snapshots or WBS nodes.
  - create_progress_snapshot / update_progress_snapshot (packet 018):
    progress-snapshot writes with merged 5-FK validation for
    project_id (required), work_package_id, task_id,
    supersedes_snapshot_id (self-reference), and approved_by
    (identity.users).  The DDL period-monotonicity check
    ``ck_progress_snapshots_period`` is mirrored at the Pydantic
    layer on create via a model_validator and at the service layer
    on update via an effective-pair check so partial updates cannot
    sneak an inverted period past the API boundary.  Self-reference
    (a snapshot superseding itself) is blocked at the service layer
    on update via an effective-pair check — mirroring the packet 016
    dependency pattern.  No new SQL and no broadening into WBS-node
    writes.

Reference validation:
  - Org FKs reuse the existing _validate_org_references helper
  - Intra-work FKs (project_id, primary_wbs_node_id) and identity FKs
    (assigned_crew_id) are validated via _validate_work_package_references
  - Task intra-work FKs (work_package_id, primary_wbs_node_id) are
    validated via _validate_task_references
  - Assignment intra-work FKs (work_package_id, task_id) and identity
    FKs (employee_id, crew_id) are validated via
    _validate_assignment_references
  - Dependency intra-work FKs (predecessor_task_id, successor_task_id)
    are validated via _validate_dependency_references
  - Execution-issue intra-work FKs (work_package_id, task_id) are
    validated via _validate_execution_issue_references
  - Progress-snapshot FKs (project_id, work_package_id, task_id,
    supersedes_snapshot_id, approved_by) are validated via
    _validate_progress_snapshot_references
  - All supplied references are looked up with db.get() before persist;
    invalid references produce a clear 422-style error dict

Response enrichment (packet 013j):
  - After a successful create/update, _hydrate_work_package_response
    populates the three optional name fields on the returned ORM
    instance using db.get() lookups.  Identity-map caching means the
    lookups are free when the FKs were just validated.  When an FK is
    null (or its row is absent), the corresponding *_name is None.
  - No new endpoints, no new schema fields, no SQL — only the three
    pre-existing WorkPackageRead optional fields are populated.

Does not contain:
  - WBS-node write logic
  - Background jobs or side effects
  - Schema changes or SQL
"""

from typing import Mapping, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from models.work import (
    Project, WorkPackage, WBSNode, Task, Assignment, Dependency,
    ExecutionIssue, ProgressSnapshot,
)
from models.org import Client, Site, BusinessUnit, Contract
from models.identity import Crew, Employee, User
from .schemas import (
    ProjectCreate,
    ProjectUpdate,
    WorkPackageCreate,
    WorkPackageUpdate,
    TaskCreate,
    TaskUpdate,
    AssignmentCreate,
    AssignmentUpdate,
    DependencyCreate,
    DependencyUpdate,
    ExecutionIssueCreate,
    ExecutionIssueUpdate,
    ProgressSnapshotCreate,
    ProgressSnapshotUpdate,
)


class OrgValidationError(Exception):
    """Raised when org FK references fail validation."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(f"Org validation failed: {errors}")


# ---------------------------------------------------------------------------
# Shared merged-error helpers (packet 019)
# ---------------------------------------------------------------------------

def _merge_errors(
    *error_dicts: Optional[Mapping[str, str]],
) -> dict[str, str]:
    """Merge zero or more FK/validation error mappings into a single dict.

    Empty mappings and ``None`` are skipped.  Later keys overwrite earlier
    keys — which should not occur in practice because each validator owns
    a distinct field-key namespace.  This helper replaces the ad-hoc
    ``{**org_errors, **wp_errors}`` merge pattern used across the seven
    PM mutation services prior to packet 019.
    """
    merged: dict[str, str] = {}
    for d in error_dicts:
        if d:
            merged.update(d)
    return merged


def _raise_if_errors(errors: Optional[Mapping[str, str]]) -> None:
    """Raise ``OrgValidationError`` with the merged dict when non-empty.

    Replaces the repeated ``if errors: raise OrgValidationError(errors)``
    epilogue of every mutation service.  The input is copied into a fresh
    ``dict[str, str]`` so callers may safely keep mutating their local
    error buffer after the helper returns (not raised).
    """
    if errors:
        raise OrgValidationError(dict(errors))


def _validate_org_references(
    db: Session,
    *,
    client_id: Optional[UUID] = None,
    site_id: Optional[UUID] = None,
    business_unit_id: Optional[UUID] = None,
    contract_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate org FK references exist.  Returns a dict of field→error for any that don't."""
    errors: dict[str, str] = {}

    if client_id is not None:
        if db.get(Client, client_id) is None:
            errors["client_id"] = f"Client {client_id} not found in org.clients"

    if site_id is not None:
        if db.get(Site, site_id) is None:
            errors["site_id"] = f"Site {site_id} not found in org.sites"

    if business_unit_id is not None:
        if db.get(BusinessUnit, business_unit_id) is None:
            errors["business_unit_id"] = (
                f"Business unit {business_unit_id} not found in org.business_units"
            )

    if contract_id is not None:
        if db.get(Contract, contract_id) is None:
            errors["contract_id"] = (
                f"Contract {contract_id} not found in org.contracts"
            )

    return errors


def create_project(db: Session, payload: ProjectCreate) -> Project:
    """Create a new work.projects record with org FK validation.

    Raises OrgValidationError if any org FK reference is invalid.
    """
    # Validate required and optional org references
    errors = _validate_org_references(
        db,
        client_id=payload.client_id,
        site_id=payload.site_id,
        business_unit_id=payload.business_unit_id,
        contract_id=payload.contract_id,
    )
    _raise_if_errors(errors)

    project = Project(
        project_code=payload.project_code,
        title=payload.title,
        status=payload.status.value,
        client_id=payload.client_id,
        site_id=payload.site_id,
        business_unit_id=payload.business_unit_id,
        contract_id=payload.contract_id,
        description=payload.description,
        planned_start_at=payload.planned_start_at,
        planned_end_at=payload.planned_end_at,
        project_priority=payload.project_priority,
        created_from_source=payload.created_from_source.value,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session,
    project_id: UUID,
    payload: ProjectUpdate,
) -> Optional[Project]:
    """Update an existing work.projects record with org FK validation.

    Returns the updated Project, or None if project_id not found.
    Raises OrgValidationError if any supplied org FK reference is invalid.
    """
    project = db.get(Project, project_id)
    if project is None:
        return None

    # Extract only the fields that were explicitly set
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return project  # Nothing to update

    # Validate any org FK references that are being changed
    errors = _validate_org_references(
        db,
        client_id=update_data.get("client_id"),
        site_id=update_data.get("site_id"),
        business_unit_id=update_data.get("business_unit_id"),
        contract_id=update_data.get("contract_id"),
    )
    _raise_if_errors(errors)

    # Apply updates
    for field, value in update_data.items():
        # Convert enum values to their string representation for SQLAlchemy
        if hasattr(value, "value"):
            value = value.value
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# Work-Package Write Services (packet 013)
# ---------------------------------------------------------------------------

def _validate_work_package_references(
    db: Session,
    *,
    project_id: Optional[UUID] = None,
    primary_wbs_node_id: Optional[UUID] = None,
    assigned_crew_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate intra-work and identity FK references for work packages.

    Org FKs (client_id, site_id) are NOT validated here — callers should
    reuse _validate_org_references for those and merge the error dicts.

    Returns a dict of field→error for any supplied reference that does not
    resolve in its owning domain.
    """
    errors: dict[str, str] = {}

    if project_id is not None:
        if db.get(Project, project_id) is None:
            errors["project_id"] = (
                f"Project {project_id} not found in work.projects"
            )

    if primary_wbs_node_id is not None:
        if db.get(WBSNode, primary_wbs_node_id) is None:
            errors["primary_wbs_node_id"] = (
                f"WBS node {primary_wbs_node_id} not found in work.wbs_nodes"
            )

    if assigned_crew_id is not None:
        if db.get(Crew, assigned_crew_id) is None:
            errors["assigned_crew_id"] = (
                f"Crew {assigned_crew_id} not found in identity.crews"
            )

    return errors


def _hydrate_work_package_response(db: Session, wp: WorkPackage) -> WorkPackage:
    """Populate the three optional *_name fields on a work-package ORM
    instance so create/update responses match the read-path shape.

    Packet: 2026-04-14-pm-schema-013j

    The three fields are already declared on WorkPackageRead (packet
    012e / 012h) and are populated on the read path by
    services.work.queries._hydrate_work_package via relationship
    traversal.  On the write path we use db.get() lookups rather than
    relationship traversal so the helper is robust against detached
    instances and mock-session test doubles.  All three lookups hit the
    SQLAlchemy identity map when the FKs were already validated during
    _validate_org_references / _validate_work_package_references, so
    they cost nothing extra against a live session.

    When an FK is null (or the row cannot be resolved) the corresponding
    *_name field is set to None to match the read-path contract.
    """
    # Identity-backed crew name (nullable FK — packet 012e)
    if getattr(wp, "assigned_crew_id", None) is not None:
        crew = db.get(Crew, wp.assigned_crew_id)
        wp.assigned_crew_name = crew.name if crew is not None else None
    else:
        wp.assigned_crew_name = None

    # Org-backed client and site names (both NOT NULL FKs — packet 011e / 012h)
    client_id = getattr(wp, "client_id", None)
    if client_id is not None:
        client = db.get(Client, client_id)
        wp.client_name = client.name if client is not None else None
    else:
        wp.client_name = None

    site_id = getattr(wp, "site_id", None)
    if site_id is not None:
        site = db.get(Site, site_id)
        wp.site_name = site.name if site is not None else None
    else:
        wp.site_name = None

    return wp


def create_work_package(db: Session, payload: WorkPackageCreate) -> WorkPackage:
    """Create a new work.work_packages record with full FK validation.

    Validates:
      - org FKs: client_id, site_id (required)
      - intra-work FKs: project_id (required), primary_wbs_node_id (optional)
      - identity FKs: assigned_crew_id (optional)

    Raises OrgValidationError with a merged error dict if any reference
    fails validation.
    """
    org_errors = _validate_org_references(
        db,
        client_id=payload.client_id,
        site_id=payload.site_id,
    )
    wp_errors = _validate_work_package_references(
        db,
        project_id=payload.project_id,
        primary_wbs_node_id=payload.primary_wbs_node_id,
        assigned_crew_id=payload.assigned_crew_id,
    )
    errors = _merge_errors(org_errors, wp_errors)
    _raise_if_errors(errors)

    work_package = WorkPackage(
        project_id=payload.project_id,
        work_package_code=payload.work_package_code,
        title=payload.title,
        work_type=payload.work_type.value,
        lifecycle_state=payload.lifecycle_state.value,
        priority=payload.priority.value,
        client_id=payload.client_id,
        site_id=payload.site_id,
        primary_wbs_node_id=payload.primary_wbs_node_id,
        scope_source_ref=payload.scope_source_ref,
        asset_class_id=payload.asset_class_id,
        apparatus_cluster_ref=payload.apparatus_cluster_ref,
        assigned_crew_id=payload.assigned_crew_id,
        scheduled_start_at=payload.scheduled_start_at,
        scheduled_end_at=payload.scheduled_end_at,
        progress_percent=payload.progress_percent,
        billing_state=(
            payload.billing_state.value if payload.billing_state is not None else None
        ),
        execution_summary=payload.execution_summary,
        created_from_source=payload.created_from_source.value,
    )
    db.add(work_package)
    db.commit()
    db.refresh(work_package)
    return _hydrate_work_package_response(db, work_package)


def update_work_package(
    db: Session,
    work_package_id: UUID,
    payload: WorkPackageUpdate,
) -> Optional[WorkPackage]:
    """Partial-update an existing work.work_packages record with FK validation.

    Returns the updated WorkPackage, or None if work_package_id not found.
    Raises OrgValidationError with a merged error dict if any supplied
    reference (org, intra-work, or identity) is invalid.
    """
    work_package = db.get(WorkPackage, work_package_id)
    if work_package is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        # Nothing to update — still enrich response so the contract
        # matches the non-empty-update and create paths.
        return _hydrate_work_package_response(db, work_package)

    org_errors = _validate_org_references(
        db,
        client_id=update_data.get("client_id"),
        site_id=update_data.get("site_id"),
    )
    wp_errors = _validate_work_package_references(
        db,
        project_id=update_data.get("project_id"),
        primary_wbs_node_id=update_data.get("primary_wbs_node_id"),
        assigned_crew_id=update_data.get("assigned_crew_id"),
    )
    errors = _merge_errors(org_errors, wp_errors)
    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(work_package, field, value)

    db.commit()
    db.refresh(work_package)
    return _hydrate_work_package_response(db, work_package)


# ---------------------------------------------------------------------------
# Task Write Services (packet 014)
# ---------------------------------------------------------------------------

def _validate_task_references(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    primary_wbs_node_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate intra-work FK references for tasks.

    Returns a dict of field→error for any supplied reference that does
    not resolve in work.work_packages / work.wbs_nodes.  Tasks have no
    direct org or identity FKs at this level — those are inherited
    transitively through the parent work package.
    """
    errors: dict[str, str] = {}

    if work_package_id is not None:
        if db.get(WorkPackage, work_package_id) is None:
            errors["work_package_id"] = (
                f"Work package {work_package_id} not found in work.work_packages"
            )

    if primary_wbs_node_id is not None:
        if db.get(WBSNode, primary_wbs_node_id) is None:
            errors["primary_wbs_node_id"] = (
                f"WBS node {primary_wbs_node_id} not found in work.wbs_nodes"
            )

    return errors


def create_task(db: Session, payload: TaskCreate) -> Task:
    """Create a new work.tasks record with intra-work FK validation.

    Validates:
      - intra-work FKs: work_package_id (required), primary_wbs_node_id (optional)

    Raises OrgValidationError (reusing the shared validation-error type) if
    any reference fails validation.  The error dict is keyed by the offending
    field name, matching the work-package write contract.
    """
    errors = _validate_task_references(
        db,
        work_package_id=payload.work_package_id,
        primary_wbs_node_id=payload.primary_wbs_node_id,
    )
    _raise_if_errors(errors)

    task = Task(
        work_package_id=payload.work_package_id,
        task_code=payload.task_code,
        title=payload.title,
        task_type=payload.task_type.value,
        lifecycle_state=payload.lifecycle_state.value,
        planned_start_at=payload.planned_start_at,
        planned_end_at=payload.planned_end_at,
        duration_hours=payload.duration_hours,
        remaining_duration_hours=payload.remaining_duration_hours,
        estimated_labor_hours=payload.estimated_labor_hours,
        schedule_priority_override=(
            payload.schedule_priority_override.value
            if payload.schedule_priority_override is not None
            else None
        ),
        primary_wbs_node_id=payload.primary_wbs_node_id,
        created_from_source=payload.created_from_source.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task_id: UUID,
    payload: TaskUpdate,
) -> Optional[Task]:
    """Partial-update an existing work.tasks record with FK validation.

    Returns the updated Task, or None if task_id not found.
    Raises OrgValidationError if any supplied intra-work FK reference is
    invalid (work_package_id or primary_wbs_node_id).
    """
    task = db.get(Task, task_id)
    if task is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return task  # Nothing to update

    errors = _validate_task_references(
        db,
        work_package_id=update_data.get("work_package_id"),
        primary_wbs_node_id=update_data.get("primary_wbs_node_id"),
    )
    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Assignment Write Services (packet 015)
# ---------------------------------------------------------------------------

def _validate_assignment_references(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    employee_id: Optional[UUID] = None,
    crew_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate intra-work and identity FK references for assignments.

    The DDL constraint ``work_package_id IS NOT NULL OR task_id IS NOT
    NULL`` (ck_assignments_at_least_one_parent) is enforced at the
    Pydantic boundary on create via AssignmentCreate's model_validator,
    so this helper only validates that any supplied FK resolves in its
    owning domain.

    Returns a dict of field→error for any supplied reference that does
    not resolve.
    """
    errors: dict[str, str] = {}

    if work_package_id is not None:
        if db.get(WorkPackage, work_package_id) is None:
            errors["work_package_id"] = (
                f"Work package {work_package_id} not found in work.work_packages"
            )

    if task_id is not None:
        if db.get(Task, task_id) is None:
            errors["task_id"] = (
                f"Task {task_id} not found in work.tasks"
            )

    if employee_id is not None:
        if db.get(Employee, employee_id) is None:
            errors["employee_id"] = (
                f"Employee {employee_id} not found in identity.employees"
            )

    if crew_id is not None:
        if db.get(Crew, crew_id) is None:
            errors["crew_id"] = (
                f"Crew {crew_id} not found in identity.crews"
            )

    return errors


def create_assignment(db: Session, payload: AssignmentCreate) -> Assignment:
    """Create a new work.assignments record with merged FK validation.

    Validates:
      - intra-work FKs: work_package_id, task_id (at least one required
        by the AssignmentCreate model_validator before we reach this
        helper)
      - identity FKs: employee_id, crew_id (optional)

    Raises OrgValidationError with a merged error dict if any supplied
    reference fails validation.
    """
    errors = _validate_assignment_references(
        db,
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
        employee_id=payload.employee_id,
        crew_id=payload.crew_id,
    )
    _raise_if_errors(errors)

    assignment = Assignment(
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
        employee_id=payload.employee_id,
        crew_id=payload.crew_id,
        assignment_role=payload.assignment_role.value,
        planned_hours=payload.planned_hours,
        actual_hours=payload.actual_hours,
        start_at=payload.start_at,
        end_at=payload.end_at,
        is_actual_participation=payload.is_actual_participation,
        created_from_source=payload.created_from_source.value,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def update_assignment(
    db: Session,
    assignment_id: UUID,
    payload: AssignmentUpdate,
) -> Optional[Assignment]:
    """Partial-update an existing work.assignments record with FK validation.

    Returns the updated Assignment, or None if assignment_id not found.
    Raises OrgValidationError if any supplied FK reference is invalid
    (work_package_id, task_id, employee_id, crew_id).
    """
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return assignment  # Nothing to update

    errors = _validate_assignment_references(
        db,
        work_package_id=update_data.get("work_package_id"),
        task_id=update_data.get("task_id"),
        employee_id=update_data.get("employee_id"),
        crew_id=update_data.get("crew_id"),
    )
    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


# ---------------------------------------------------------------------------
# Dependency Write Services (packet 016)
# ---------------------------------------------------------------------------

def _validate_dependency_references(
    db: Session,
    *,
    predecessor_task_id: Optional[UUID] = None,
    successor_task_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate intra-work FK references for dependencies.

    Both references target ``work.tasks``.  The no-self-cycle rule
    (predecessor != successor) is NOT checked here — callers enforce it
    at the Pydantic boundary on create and against the effective pair on
    update.  Returns a dict of field→error for any supplied reference
    that does not resolve in work.tasks.
    """
    errors: dict[str, str] = {}

    if predecessor_task_id is not None:
        if db.get(Task, predecessor_task_id) is None:
            errors["predecessor_task_id"] = (
                f"Task {predecessor_task_id} not found in work.tasks"
            )

    if successor_task_id is not None:
        if db.get(Task, successor_task_id) is None:
            errors["successor_task_id"] = (
                f"Task {successor_task_id} not found in work.tasks"
            )

    return errors


def create_dependency(db: Session, payload: DependencyCreate) -> Dependency:
    """Create a new work.dependencies record with merged FK validation.

    Validates:
      - intra-work FKs: predecessor_task_id, successor_task_id (both
        required and required to be distinct by the DependencyCreate
        Pydantic contract — the model_validator raises 422 before this
        helper is reached for self-referential payloads)

    Raises OrgValidationError with a merged error dict if either task
    reference fails validation.
    """
    errors = _validate_dependency_references(
        db,
        predecessor_task_id=payload.predecessor_task_id,
        successor_task_id=payload.successor_task_id,
    )
    _raise_if_errors(errors)

    dependency = Dependency(
        predecessor_task_id=payload.predecessor_task_id,
        successor_task_id=payload.successor_task_id,
        relationship_type=payload.relationship_type.value,
        lag_hours=payload.lag_hours,
        source_system=payload.source_system.value,
        is_active=payload.is_active,
        created_from_source=payload.created_from_source.value,
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    return dependency


def update_dependency(
    db: Session,
    dependency_id: UUID,
    payload: DependencyUpdate,
) -> Optional[Dependency]:
    """Partial-update an existing work.dependencies record with FK validation.

    Returns the updated Dependency, or None if dependency_id not found.
    Raises OrgValidationError if any supplied FK reference is invalid
    (predecessor_task_id or successor_task_id), or if the effective
    (post-patch) predecessor/successor pair would collapse to a self-
    referential row.  The self-cycle check is evaluated at the service
    layer rather than on DependencyUpdate because a partial payload
    cannot see the stored counterparty — the merged evaluation is what
    mirrors the DDL intent.
    """
    dependency = db.get(Dependency, dependency_id)
    if dependency is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return dependency  # Nothing to update

    errors = _validate_dependency_references(
        db,
        predecessor_task_id=update_data.get("predecessor_task_id"),
        successor_task_id=update_data.get("successor_task_id"),
    )

    # Merged no-self-cycle check against the effective (post-patch) pair.
    # Packet 019 consolidates this into the same merged errors dict so
    # callers see every violation at once rather than short-circuiting on
    # the FK error.  Parity with the packet 018 progress-snapshot update
    # accumulator pattern.
    effective_predecessor = update_data.get(
        "predecessor_task_id", dependency.predecessor_task_id
    )
    effective_successor = update_data.get(
        "successor_task_id", dependency.successor_task_id
    )
    if effective_predecessor == effective_successor:
        cycle_msg = (
            "predecessor_task_id and successor_task_id must be"
            " different tasks"
        )
        errors = _merge_errors(
            errors,
            {
                "predecessor_task_id": cycle_msg,
                "successor_task_id": cycle_msg,
            },
        )

    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(dependency, field, value)

    db.commit()
    db.refresh(dependency)
    return dependency


# ---------------------------------------------------------------------------
# Execution-Issue Write Services (packet 017)
# ---------------------------------------------------------------------------

def _validate_execution_issue_references(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate intra-work FK references for execution issues.

    The DDL constraint ``work_package_id IS NOT NULL OR task_id IS NOT
    NULL`` (ck_execution_issues_at_least_one_parent) is enforced at the
    Pydantic boundary on create via ExecutionIssueCreate's
    model_validator, so this helper only validates that any supplied FK
    resolves in its owning domain.

    Returns a dict of field→error for any supplied reference that does
    not resolve.
    """
    errors: dict[str, str] = {}

    if work_package_id is not None:
        if db.get(WorkPackage, work_package_id) is None:
            errors["work_package_id"] = (
                f"Work package {work_package_id} not found in work.work_packages"
            )

    if task_id is not None:
        if db.get(Task, task_id) is None:
            errors["task_id"] = (
                f"Task {task_id} not found in work.tasks"
            )

    return errors


def create_execution_issue(
    db: Session, payload: ExecutionIssueCreate,
) -> ExecutionIssue:
    """Create a new work.execution_issues record with merged FK validation.

    Validates:
      - intra-work FKs: work_package_id, task_id (at least one required
        by the ExecutionIssueCreate model_validator before we reach this
        helper; each supplied FK is then resolved against its owning
        work entity)

    Raises OrgValidationError with a merged error dict if any supplied
    reference fails validation.
    """
    errors = _validate_execution_issue_references(
        db,
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
    )
    _raise_if_errors(errors)

    issue = ExecutionIssue(
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
        apparatus_ref=payload.apparatus_ref,
        issue_type=payload.issue_type.value,
        severity=payload.severity.value,
        status=payload.status.value,
        blocks_completion=payload.blocks_completion,
        summary=payload.summary,
        details=payload.details,
        reported_by=payload.reported_by,
        assigned_to=payload.assigned_to,
        resolution_type=(
            payload.resolution_type.value
            if payload.resolution_type is not None
            else None
        ),
        resolved_at=payload.resolved_at,
        closed_at=payload.closed_at,
        created_from_source=payload.created_from_source.value,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


def update_execution_issue(
    db: Session,
    execution_issue_id: UUID,
    payload: ExecutionIssueUpdate,
) -> Optional[ExecutionIssue]:
    """Partial-update an existing work.execution_issues record.

    Returns the updated ExecutionIssue, or None if execution_issue_id not
    found.  Raises OrgValidationError if any supplied intra-work FK
    reference is invalid (work_package_id or task_id).
    """
    issue = db.get(ExecutionIssue, execution_issue_id)
    if issue is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return issue  # Nothing to update

    errors = _validate_execution_issue_references(
        db,
        work_package_id=update_data.get("work_package_id"),
        task_id=update_data.get("task_id"),
    )
    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue


# ---------------------------------------------------------------------------
# Progress-Snapshot Write Services (packet 018)
# ---------------------------------------------------------------------------

def _validate_progress_snapshot_references(
    db: Session,
    *,
    project_id: Optional[UUID] = None,
    work_package_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    supersedes_snapshot_id: Optional[UUID] = None,
    approved_by: Optional[UUID] = None,
) -> dict[str, str]:
    """Validate FK references for progress snapshots.

    Returns a dict of field→error for any supplied reference that does
    not resolve in its owning domain.  Mirrors the merged-validation
    posture established by packet 015 (assignments, 4 FKs) and extended
    by packet 016 (dependencies, 2 FKs) and packet 017 (execution issues,
    2 FKs).  Progress snapshots carry 5 FKs spanning three domains:

      * work.projects                  — project_id
      * work.work_packages             — work_package_id
      * work.tasks                     — task_id
      * work.progress_snapshots (self) — supersedes_snapshot_id
      * identity.users                 — approved_by
    """
    errors: dict[str, str] = {}

    if project_id is not None:
        if db.get(Project, project_id) is None:
            errors["project_id"] = (
                f"Project {project_id} not found in work.projects"
            )

    if work_package_id is not None:
        if db.get(WorkPackage, work_package_id) is None:
            errors["work_package_id"] = (
                f"Work package {work_package_id} not found in work.work_packages"
            )

    if task_id is not None:
        if db.get(Task, task_id) is None:
            errors["task_id"] = (
                f"Task {task_id} not found in work.tasks"
            )

    if supersedes_snapshot_id is not None:
        if db.get(ProgressSnapshot, supersedes_snapshot_id) is None:
            errors["supersedes_snapshot_id"] = (
                f"Progress snapshot {supersedes_snapshot_id} not found "
                f"in work.progress_snapshots"
            )

    if approved_by is not None:
        if db.get(User, approved_by) is None:
            errors["approved_by"] = (
                f"User {approved_by} not found in identity.users"
            )

    return errors


def create_progress_snapshot(
    db: Session, payload: ProgressSnapshotCreate,
) -> ProgressSnapshot:
    """Create a new work.progress_snapshots record with merged FK validation.

    Validates:
      - project_id (required, work.projects)
      - work_package_id (optional, work.work_packages)
      - task_id (optional, work.tasks)
      - supersedes_snapshot_id (optional, work.progress_snapshots self-ref)
      - approved_by (optional, identity.users)

    The ``snapshot_period_end >= snapshot_period_start`` rule is enforced
    by the ProgressSnapshotCreate model_validator at the Pydantic layer
    before we reach this helper; this service does not re-check it.

    No self-cycle is possible at create time because progress_snapshot_id
    is assigned server-side on INSERT.

    Raises OrgValidationError with a merged error dict if any supplied
    reference fails validation.
    """
    errors = _validate_progress_snapshot_references(
        db,
        project_id=payload.project_id,
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
        supersedes_snapshot_id=payload.supersedes_snapshot_id,
        approved_by=payload.approved_by,
    )
    _raise_if_errors(errors)

    snapshot = ProgressSnapshot(
        project_id=payload.project_id,
        work_package_id=payload.work_package_id,
        task_id=payload.task_id,
        snapshot_period_start=payload.snapshot_period_start,
        snapshot_period_end=payload.snapshot_period_end,
        snapshot_status=payload.snapshot_status.value,
        completed_apparatus_count=payload.completed_apparatus_count,
        total_apparatus_count=payload.total_apparatus_count,
        percent_complete=payload.percent_complete,
        actual_labor_hours=payload.actual_labor_hours,
        billable_amount=payload.billable_amount,
        billing_reference=payload.billing_reference,
        approved_by=payload.approved_by,
        approved_at=payload.approved_at,
        supersedes_snapshot_id=payload.supersedes_snapshot_id,
        source_data_date=payload.source_data_date,
        created_from_source=payload.created_from_source.value,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def update_progress_snapshot(
    db: Session,
    progress_snapshot_id: UUID,
    payload: ProgressSnapshotUpdate,
) -> Optional[ProgressSnapshot]:
    """Partial-update an existing work.progress_snapshots record.

    Returns the updated ProgressSnapshot, or None if progress_snapshot_id
    is not found.  Raises OrgValidationError if any supplied FK reference
    is invalid (project_id, work_package_id, task_id,
    supersedes_snapshot_id, approved_by).

    Applies the following service-layer guards in parity with packet 016
    (dependency update effective-pair self-cycle check):

      * Self-reference guard: ``supersedes_snapshot_id`` must not equal
        ``progress_snapshot_id`` (a snapshot cannot supersede itself).
        This is checked against the effective pair (target id, supplied
        value) before persist.
      * Period monotonicity: if either ``snapshot_period_start`` or
        ``snapshot_period_end`` is supplied, the effective pair (using
        the existing row's bound for the unsupplied end) must satisfy
        ``end >= start`` — mirroring the DDL
        ``ck_progress_snapshots_period`` check constraint at the API
        boundary so callers receive a 422 instead of a database error.
    """
    snapshot = db.get(ProgressSnapshot, progress_snapshot_id)
    if snapshot is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return snapshot  # Nothing to update

    errors = _validate_progress_snapshot_references(
        db,
        project_id=update_data.get("project_id"),
        work_package_id=update_data.get("work_package_id"),
        task_id=update_data.get("task_id"),
        supersedes_snapshot_id=update_data.get("supersedes_snapshot_id"),
        approved_by=update_data.get("approved_by"),
    )

    # Effective-pair self-reference guard (packet 016 pattern)
    if "supersedes_snapshot_id" in update_data:
        supplied = update_data["supersedes_snapshot_id"]
        if supplied is not None and supplied == progress_snapshot_id:
            errors["supersedes_snapshot_id"] = (
                "A progress snapshot cannot supersede itself"
            )

    # Effective-pair period monotonicity guard
    if (
        "snapshot_period_start" in update_data
        or "snapshot_period_end" in update_data
    ):
        effective_start = update_data.get(
            "snapshot_period_start", snapshot.snapshot_period_start,
        )
        effective_end = update_data.get(
            "snapshot_period_end", snapshot.snapshot_period_end,
        )
        if (
            effective_start is not None
            and effective_end is not None
            and effective_end < effective_start
        ):
            errors["snapshot_period_end"] = (
                "snapshot_period_end must be on or after snapshot_period_start"
            )

    _raise_if_errors(errors)

    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(snapshot, field, value)

    db.commit()
    db.refresh(snapshot)
    return snapshot
