"""
PM/Work Domain — Read-Only Query Services
==========================================
Packet: 2026-04-13-pm-schema-010b (original read-only surface)
Updated: 2026-04-14-pm-schema-012f (identity-joined read surface)
Updated: 2026-04-14-pm-schema-012h (org-joined read surface)
Authority: 2026-04-13-pm-schema-010a (ORM models + Pydantic schemas),
           2026-04-14-pm-schema-011e (org ORM alignment),
           2026-04-14-pm-schema-012e (identity ORM alignment)

Minimal query helpers for the read-only PM/work API surface.
Each function accepts a SQLAlchemy Session and returns ORM model
instances.  No write operations, mutations, or side effects.

Query scope:
  - projects: list, get-by-id
  - work_packages: list (filterable by project_id), get-by-id
  - tasks: list (filterable by work_package_id), get-by-id
  - assignments: list (filterable by work_package_id or task_id)
  - wbs_nodes: list (filterable by project_id)
  - execution_issues: list (filterable by work_package_id or task_id)
  - progress_snapshots: list (filterable by project_id)
  - dependencies: list (filterable by predecessor or successor task_id)

Identity-joined read surface (packet 012f):
  The five query helpers covering work_packages, assignments,
  execution_issues, and progress_snapshots eager-load the six
  active identity relationships (assigned_crew, employee, crew,
  reporter, assignee, approver) with `joinedload` and populate
  the optional `*_name` fields authored by packet 012e.
  `*_name` attributes remain `None` when the underlying FK is NULL
  or when the related row is missing.

Org-joined read surface (packet 012h):
  The project and work-package query helpers additionally
  eager-load the six active org relationships (Project.client,
  Project.site, Project.business_unit, Project.contract,
  WorkPackage.client, WorkPackage.site) with `joinedload` and
  populate the optional org `*_name` / `*_title` fields authored
  by packet 011e (ProjectRead: client_name, site_name,
  business_unit_name, contract_title; WorkPackageRead: client_name,
  site_name).  These attributes remain `None` when the FK is NULL
  or the related row / attribute is missing.
"""

from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from models.work import (
    Project, WBSNode, WorkPackage, Task,
    Dependency, Assignment, ExecutionIssue, ProgressSnapshot,
)


# ---------------------------------------------------------------------------
# Identity-name hydration helpers (packet 012f)
# ---------------------------------------------------------------------------
#
# Each helper attaches scalar `*_name` attributes to the ORM instance so
# that Pydantic's `from_attributes=True` serialization resolves the
# display-name fields authored by packet 012e.  Non-mapped Python
# attributes on SQLAlchemy instances are stored in instance __dict__ and
# do not participate in the ORM write path.


def _employee_display_name(employee) -> Optional[str]:
    """Return `first_name last_name` for an Employee, or None."""
    if employee is None:
        return None
    first = (employee.first_name or "").strip()
    last = (employee.last_name or "").strip()
    combined = f"{first} {last}".strip()
    return combined or None


def _hydrate_work_package(wp: Optional[WorkPackage]) -> Optional[WorkPackage]:
    if wp is None:
        return None
    # Identity-joined hydration (packet 012f)
    wp.assigned_crew_name = (
        wp.assigned_crew.name if wp.assigned_crew_id and wp.assigned_crew else None
    )
    # Org-joined hydration (packet 012h).  `getattr` tolerates stub-shaped
    # test objects authored before packet 012h that do not carry the
    # client / site attributes; real WorkPackage ORM instances always
    # expose them via the relationship() declarations from packet 011e.
    client_id = getattr(wp, "client_id", None)
    client = getattr(wp, "client", None)
    wp.client_name = client.name if client_id and client else None
    site_id = getattr(wp, "site_id", None)
    site = getattr(wp, "site", None)
    wp.site_name = site.name if site_id and site else None
    return wp


def _hydrate_project(p: Optional[Project]) -> Optional[Project]:
    """Populate the four org-backed *_name/_title fields on a Project.

    Mirrors the packet 012f identity-hydration pattern for the four
    active Project → org relationships authored by packet 011e:
      - client_name         ← Project.client.name         (NOT NULL FK)
      - site_name           ← Project.site.name           (NOT NULL FK)
      - business_unit_name  ← Project.business_unit.name  (nullable FK)
      - contract_title      ← Project.contract.title      (nullable FK; title nullable)

    Returns ``None`` for any *_name / *_title whose FK is NULL, whose
    relationship target is missing, or (for contract_title) whose
    underlying column is NULL.
    """
    if p is None:
        return None
    p.client_name = (
        p.client.name if p.client_id and p.client else None
    )
    p.site_name = (
        p.site.name if p.site_id and p.site else None
    )
    p.business_unit_name = (
        p.business_unit.name
        if p.business_unit_id and p.business_unit
        else None
    )
    p.contract_title = (
        p.contract.title
        if p.contract_id and p.contract
        else None
    )
    return p


def _hydrate_assignment(a: Optional[Assignment]) -> Optional[Assignment]:
    if a is None:
        return None
    a.employee_name = (
        _employee_display_name(a.employee) if a.employee_id else None
    )
    a.crew_name = (
        a.crew.name if a.crew_id and a.crew else None
    )
    return a


def _hydrate_execution_issue(ei: Optional[ExecutionIssue]) -> Optional[ExecutionIssue]:
    if ei is None:
        return None
    ei.reported_by_name = (
        ei.reporter.display_name if ei.reported_by and ei.reporter else None
    )
    ei.assigned_to_name = (
        ei.assignee.display_name if ei.assigned_to and ei.assignee else None
    )
    return ei


def _hydrate_progress_snapshot(ps: Optional[ProgressSnapshot]) -> Optional[ProgressSnapshot]:
    if ps is None:
        return None
    ps.approved_by_name = (
        ps.approver.display_name if ps.approved_by and ps.approver else None
    )
    return ps


def _hydrate_many(rows: Iterable, hydrator):
    return [hydrator(r) for r in rows]


# ---------------------------------------------------------------------------
# Projects (org-joined — packet 012h)
# ---------------------------------------------------------------------------

def list_projects(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Project]:
    """Return projects with the four org `*_name`/`*_title` fields hydrated."""
    rows = (
        db.query(Project)
        .options(
            joinedload(Project.client),
            joinedload(Project.site),
            joinedload(Project.business_unit),
            joinedload(Project.contract),
        )
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return _hydrate_many(rows, _hydrate_project)


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    """Return a single project with org `*_name`/`*_title` fields hydrated."""
    p = (
        db.query(Project)
        .options(
            joinedload(Project.client),
            joinedload(Project.site),
            joinedload(Project.business_unit),
            joinedload(Project.contract),
        )
        .filter(Project.project_id == project_id)
        .one_or_none()
    )
    return _hydrate_project(p)


# ---------------------------------------------------------------------------
# WBS Nodes
# ---------------------------------------------------------------------------

def list_wbs_nodes(
    db: Session,
    *,
    project_id: Optional[UUID] = None,
    limit: int = 200,
    offset: int = 0,
) -> list[WBSNode]:
    """Return WBS nodes, optionally filtered by project_id."""
    q = db.query(WBSNode)
    if project_id is not None:
        q = q.filter(WBSNode.project_id == project_id)
    return q.order_by(WBSNode.sort_order, WBSNode.wbs_code).offset(offset).limit(limit).all()


# ---------------------------------------------------------------------------
# Work Packages (identity-joined — packet 012f; org-joined — packet 012h)
# ---------------------------------------------------------------------------

def list_work_packages(
    db: Session,
    *,
    project_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[WorkPackage]:
    """Return work packages with identity + org `*_name` fields hydrated."""
    q = db.query(WorkPackage).options(
        joinedload(WorkPackage.assigned_crew),
        joinedload(WorkPackage.client),
        joinedload(WorkPackage.site),
    )
    if project_id is not None:
        q = q.filter(WorkPackage.project_id == project_id)
    rows = q.order_by(WorkPackage.created_at.desc()).offset(offset).limit(limit).all()
    return _hydrate_many(rows, _hydrate_work_package)


def get_work_package(db: Session, work_package_id: UUID) -> Optional[WorkPackage]:
    """Return a single work package with identity + org `*_name` fields hydrated."""
    wp = (
        db.query(WorkPackage)
        .options(
            joinedload(WorkPackage.assigned_crew),
            joinedload(WorkPackage.client),
            joinedload(WorkPackage.site),
        )
        .filter(WorkPackage.work_package_id == work_package_id)
        .one_or_none()
    )
    return _hydrate_work_package(wp)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def list_tasks(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Task]:
    """Return tasks, optionally filtered by work_package_id."""
    q = db.query(Task)
    if work_package_id is not None:
        q = q.filter(Task.work_package_id == work_package_id)
    return q.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()


def get_task(db: Session, task_id: UUID) -> Optional[Task]:
    """Return a single task by primary key, or None."""
    return db.get(Task, task_id)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def list_dependencies(
    db: Session,
    *,
    predecessor_task_id: Optional[UUID] = None,
    successor_task_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Dependency]:
    """Return dependencies, optionally filtered by predecessor or successor."""
    q = db.query(Dependency)
    if predecessor_task_id is not None:
        q = q.filter(Dependency.predecessor_task_id == predecessor_task_id)
    if successor_task_id is not None:
        q = q.filter(Dependency.successor_task_id == successor_task_id)
    return q.order_by(Dependency.created_at.desc()).offset(offset).limit(limit).all()


# ---------------------------------------------------------------------------
# Assignments (identity-joined — packet 012f)
# ---------------------------------------------------------------------------

def list_assignments(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Assignment]:
    """Return assignments with `employee_name` and `crew_name` hydrated."""
    q = db.query(Assignment).options(
        joinedload(Assignment.employee),
        joinedload(Assignment.crew),
    )
    if work_package_id is not None:
        q = q.filter(Assignment.work_package_id == work_package_id)
    if task_id is not None:
        q = q.filter(Assignment.task_id == task_id)
    rows = q.order_by(Assignment.created_at.desc()).offset(offset).limit(limit).all()
    return _hydrate_many(rows, _hydrate_assignment)


# ---------------------------------------------------------------------------
# Execution Issues (identity-joined — packet 012f)
# ---------------------------------------------------------------------------

def list_execution_issues(
    db: Session,
    *,
    work_package_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ExecutionIssue]:
    """Return execution issues with reporter/assignee display names hydrated."""
    q = db.query(ExecutionIssue).options(
        joinedload(ExecutionIssue.reporter),
        joinedload(ExecutionIssue.assignee),
    )
    if work_package_id is not None:
        q = q.filter(ExecutionIssue.work_package_id == work_package_id)
    if task_id is not None:
        q = q.filter(ExecutionIssue.task_id == task_id)
    rows = q.order_by(ExecutionIssue.opened_at.desc()).offset(offset).limit(limit).all()
    return _hydrate_many(rows, _hydrate_execution_issue)


# ---------------------------------------------------------------------------
# Progress Snapshots (identity-joined — packet 012f)
# ---------------------------------------------------------------------------

def list_progress_snapshots(
    db: Session,
    *,
    project_id: Optional[UUID] = None,
    work_package_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ProgressSnapshot]:
    """Return progress snapshots with `approved_by_name` hydrated."""
    q = db.query(ProgressSnapshot).options(
        joinedload(ProgressSnapshot.approver),
    )
    if project_id is not None:
        q = q.filter(ProgressSnapshot.project_id == project_id)
    if work_package_id is not None:
        q = q.filter(ProgressSnapshot.work_package_id == work_package_id)
    rows = q.order_by(ProgressSnapshot.created_at.desc()).offset(offset).limit(limit).all()
    return _hydrate_many(rows, _hydrate_progress_snapshot)
