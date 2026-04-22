"""
PM/Work Domain — Pydantic Schemas
===================================
Packet: 2026-04-13-pm-schema-010a (original read schemas)
Updated: 2026-04-14-pm-schema-011e (org relationship names)
Updated: 2026-04-14-pm-schema-011f (project create/update schemas)
Updated: 2026-04-14-pm-schema-013 (work-package create/update schemas)
Updated: 2026-04-14-pm-schema-014 (task create/update schemas)
Updated: 2026-04-15-pm-schema-015 (assignment create/update schemas)
Updated: 2026-04-15-pm-schema-016 (dependency create/update schemas)
Updated: 2026-04-15-pm-schema-017 (execution-issue create/update schemas)
Updated: 2026-04-15-pm-schema-018 (progress-snapshot create/update schemas)
Authority: infra/database/migrations/work/002_work_tables.sql
           infra/database/migrations/work/007_work_org_fk_activation.sql

Read schemas (8):
  ProjectRead, WBSNodeRead, WorkPackageRead, TaskRead,
  DependencyRead, AssignmentRead, ExecutionIssueRead,
  ProgressSnapshotRead

Write schemas — projects only (2, packet 011f):
  ProjectCreate, ProjectUpdate

Write schemas — work packages only (2, packet 013):
  WorkPackageCreate, WorkPackageUpdate

Write schemas — tasks only (2, packet 014):
  TaskCreate, TaskUpdate

Write schemas — assignments only (2, packet 015):
  AssignmentCreate, AssignmentUpdate

Write schemas — dependencies only (2, packet 016):
  DependencyCreate, DependencyUpdate

Write schemas — execution issues only (2, packet 017):
  ExecutionIssueCreate, ExecutionIssueUpdate

Write schemas — progress snapshots only (2, packet 018):
  ProgressSnapshotCreate, ProgressSnapshotUpdate

Org entity name fields (client_name, site_name, business_unit_name,
contract_title) are optional on ProjectRead and WorkPackageRead.
They resolve via SQLAlchemy relationship traversal when the ORM
instance is loaded with joined org data.  When loaded without joins
(e.g., direct query), these fields default to None.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from models.work_enums import (
    ProvenanceSource, ProvenanceStatus, ProjectStatus,
    WPLifecycle, WorkType, Priority, BillingState,
    TaskLifecycle, TaskType, DependencyType, AssignmentRole,
    IssueType, Severity, IssueStatus, ResolutionType,
    SnapshotStatus,
)


# ---------------------------------------------------------------------------
# 4.1 ProjectRead
# ---------------------------------------------------------------------------

class ProjectRead(BaseModel):
    """Read schema for work.projects."""

    project_id: UUID
    project_code: str
    title: str
    status: ProjectStatus
    client_id: UUID
    site_id: UUID
    business_unit_id: Optional[UUID] = None
    description: Optional[str] = None
    contract_id: Optional[UUID] = None
    # Org entity names — resolved via relationship when joined (packet 011e)
    client_name: Optional[str] = None
    site_name: Optional[str] = None
    business_unit_name: Optional[str] = None
    contract_title: Optional[str] = None
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    project_priority: Optional[str] = None
    created_from_source: ProvenanceSource
    provenance_status: ProvenanceStatus
    p6_project_id: Optional[str] = None
    p6_short_name: Optional[str] = None
    p6_data_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.1b ProjectCreate (packet 011f)
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    """Request schema for creating a work.projects record.

    Required fields match the NOT NULL DDL contract:
      - project_code, title: mandatory text fields
      - client_id, site_id: mandatory org FK references (validated before persist)

    Optional fields have server defaults or are nullable in DDL.
    Fields not exposed on create (server-managed):
      - project_id, created_at, updated_at (auto-generated)
      - provenance_status (defaults to 'curated')
      - p6_* fields (P6 integration — not settable via manual create)
    """

    project_code: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    client_id: UUID
    site_id: UUID
    status: ProjectStatus = ProjectStatus.DRAFT
    business_unit_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    description: Optional[str] = None
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    project_priority: Optional[str] = None
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL


# ---------------------------------------------------------------------------
# 4.1c ProjectUpdate (packet 011f)
# ---------------------------------------------------------------------------

class ProjectUpdate(BaseModel):
    """Request schema for updating a work.projects record.

    All fields are optional — only supplied fields are applied.
    Org FK fields (client_id, site_id, business_unit_id, contract_id)
    are validated against the org domain when supplied.
    Server-managed fields (project_id, created_at, updated_at, p6_*)
    are not exposed for update.
    """

    project_code: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[ProjectStatus] = None
    client_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    business_unit_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    description: Optional[str] = None
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    project_priority: Optional[str] = None
    provenance_status: Optional[ProvenanceStatus] = None


# ---------------------------------------------------------------------------
# 4.4 WBSNodeRead
# ---------------------------------------------------------------------------

class WBSNodeRead(BaseModel):
    """Read schema for work.wbs_nodes."""

    wbs_node_id: UUID
    project_id: UUID
    parent_wbs_node_id: Optional[UUID] = None
    wbs_code: str
    title: str
    sort_order: Optional[int] = None
    p6_wbs_id: Optional[str] = None
    p6_parent_wbs_id: Optional[str] = None
    created_from_source: ProvenanceSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.2 WorkPackageRead
# ---------------------------------------------------------------------------

class WorkPackageRead(BaseModel):
    """Read schema for work.work_packages."""

    work_package_id: UUID
    project_id: UUID
    work_package_code: str
    title: str
    work_type: WorkType
    lifecycle_state: WPLifecycle
    priority: Priority
    client_id: UUID
    site_id: UUID
    # Org entity names — resolved via relationship when joined (packet 011e)
    client_name: Optional[str] = None
    site_name: Optional[str] = None
    primary_wbs_node_id: Optional[UUID] = None
    scope_source_ref: Optional[UUID] = None
    asset_class_id: Optional[UUID] = None
    apparatus_cluster_ref: Optional[str] = None
    assigned_crew_id: Optional[UUID] = None
    # Identity entity name — resolved via relationship when joined (packet 012e)
    assigned_crew_name: Optional[str] = None
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    progress_percent: Optional[Decimal] = None
    billing_state: Optional[BillingState] = None
    execution_summary: Optional[str] = None
    created_from_source: ProvenanceSource
    provenance_status: ProvenanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.2b WorkPackageCreate (packet 013)
# ---------------------------------------------------------------------------

class WorkPackageCreate(BaseModel):
    """Request schema for creating a work.work_packages record.

    Required fields match the NOT NULL DDL contract:
      - project_id: intra-work FK (parent project; validated before persist)
      - work_package_code, title: mandatory text fields
      - work_type: mandatory enum
      - client_id, site_id: mandatory org FK references (validated before persist)

    Optional fields have server defaults or are nullable in DDL.
    Optional FK references (primary_wbs_node_id, assigned_crew_id) are
    validated against their owning domain (work / identity) when supplied.
    Fields not exposed on create (server-managed):
      - work_package_id, created_at, updated_at (auto-generated)
      - provenance_status (defaults to 'curated')
      - actual_start_at, actual_end_at (populated via execution, not manual)
    """

    project_id: UUID
    work_package_code: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    work_type: WorkType
    client_id: UUID
    site_id: UUID
    lifecycle_state: WPLifecycle = WPLifecycle.DRAFT
    priority: Priority = Priority.NORMAL
    primary_wbs_node_id: Optional[UUID] = None
    scope_source_ref: Optional[UUID] = None
    asset_class_id: Optional[UUID] = None
    apparatus_cluster_ref: Optional[str] = Field(None, max_length=200)
    assigned_crew_id: Optional[UUID] = None
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    progress_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    billing_state: Optional[BillingState] = None
    execution_summary: Optional[str] = None
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL


# ---------------------------------------------------------------------------
# 4.2c WorkPackageUpdate (packet 013)
# ---------------------------------------------------------------------------

class WorkPackageUpdate(BaseModel):
    """Request schema for updating a work.work_packages record.

    All fields are optional — only supplied fields are applied.
    FK fields (project_id intra-work; client_id, site_id org; assigned_crew_id
    identity; primary_wbs_node_id intra-work) are validated against their
    owning domain when supplied.
    Server-managed fields (work_package_id, created_at, updated_at) are not
    exposed for update.
    """

    project_id: Optional[UUID] = None
    work_package_code: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    work_type: Optional[WorkType] = None
    lifecycle_state: Optional[WPLifecycle] = None
    priority: Optional[Priority] = None
    client_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    primary_wbs_node_id: Optional[UUID] = None
    scope_source_ref: Optional[UUID] = None
    asset_class_id: Optional[UUID] = None
    apparatus_cluster_ref: Optional[str] = Field(None, max_length=200)
    assigned_crew_id: Optional[UUID] = None
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    progress_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    billing_state: Optional[BillingState] = None
    execution_summary: Optional[str] = None
    provenance_status: Optional[ProvenanceStatus] = None


# ---------------------------------------------------------------------------
# 4.3 TaskRead
# ---------------------------------------------------------------------------

class TaskRead(BaseModel):
    """Read schema for work.tasks."""

    task_id: UUID
    work_package_id: UUID
    task_code: Optional[str] = None
    title: str
    task_type: TaskType
    lifecycle_state: TaskLifecycle
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    early_start_at: Optional[datetime] = None
    early_end_at: Optional[datetime] = None
    late_start_at: Optional[datetime] = None
    late_end_at: Optional[datetime] = None
    duration_hours: Optional[Decimal] = None
    remaining_duration_hours: Optional[Decimal] = None
    estimated_labor_hours: Optional[Decimal] = None
    actual_labor_hours: Optional[Decimal] = None
    total_float_hours: Optional[Decimal] = None
    schedule_priority_override: Optional[Priority] = None
    primary_wbs_node_id: Optional[UUID] = None
    p6_task_id: Optional[str] = None
    p6_activity_id: Optional[str] = None
    p6_calendar_id: Optional[str] = None
    created_from_source: ProvenanceSource
    provenance_status: ProvenanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.3b TaskCreate (packet 014)
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    """Request schema for creating a work.tasks record.

    Required fields match the NOT NULL DDL contract:
      - work_package_id: intra-work FK (parent work package; validated before persist)
      - title: mandatory text field
      - task_type: mandatory enum (defaults to TASK)
      - lifecycle_state: mandatory enum (defaults to NOT_STARTED)

    Optional FK references (primary_wbs_node_id) are validated against
    their owning domain when supplied.

    Fields not exposed on create (server-managed):
      - task_id, created_at, updated_at (auto-generated)
      - provenance_status (defaults to 'curated')
      - actual_start_at / actual_end_at (populated via execution, not manual)
      - early_*_at / late_*_at (populated by P6 sync, not manual)
      - p6_* fields (P6 integration — not settable via manual create)
    """

    work_package_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    task_type: TaskType = TaskType.TASK
    lifecycle_state: TaskLifecycle = TaskLifecycle.NOT_STARTED
    task_code: Optional[str] = Field(None, min_length=1, max_length=100)
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0)
    remaining_duration_hours: Optional[Decimal] = Field(None, ge=0)
    estimated_labor_hours: Optional[Decimal] = Field(None, ge=0)
    schedule_priority_override: Optional[Priority] = None
    primary_wbs_node_id: Optional[UUID] = None
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL


# ---------------------------------------------------------------------------
# 4.3c TaskUpdate (packet 014)
# ---------------------------------------------------------------------------

class TaskUpdate(BaseModel):
    """Request schema for updating a work.tasks record.

    All fields are optional — only supplied fields are applied.
    FK fields (work_package_id intra-work; primary_wbs_node_id intra-work)
    are validated against their owning domain when supplied.
    Server-managed fields (task_id, created_at, updated_at, p6_*,
    early_*_at, late_*_at) are not exposed for update.
    """

    work_package_id: Optional[UUID] = None
    task_code: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    task_type: Optional[TaskType] = None
    lifecycle_state: Optional[TaskLifecycle] = None
    planned_start_at: Optional[datetime] = None
    planned_end_at: Optional[datetime] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    duration_hours: Optional[Decimal] = Field(None, ge=0)
    remaining_duration_hours: Optional[Decimal] = Field(None, ge=0)
    estimated_labor_hours: Optional[Decimal] = Field(None, ge=0)
    actual_labor_hours: Optional[Decimal] = Field(None, ge=0)
    total_float_hours: Optional[Decimal] = None
    schedule_priority_override: Optional[Priority] = None
    primary_wbs_node_id: Optional[UUID] = None
    provenance_status: Optional[ProvenanceStatus] = None


# ---------------------------------------------------------------------------
# 4.5 DependencyRead
# ---------------------------------------------------------------------------

class DependencyRead(BaseModel):
    """Read schema for work.dependencies."""

    dependency_id: UUID
    predecessor_task_id: UUID
    successor_task_id: UUID
    relationship_type: DependencyType
    lag_hours: Optional[Decimal] = None
    source_system: ProvenanceSource
    p6_relationship_id: Optional[str] = None
    is_active: bool
    created_from_source: ProvenanceSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.5b DependencyCreate (packet 016)
# ---------------------------------------------------------------------------

class DependencyCreate(BaseModel):
    """Request schema for creating a work.dependencies record.

    DDL contract: ``predecessor_task_id`` and ``successor_task_id`` are
    both NOT NULL FKs into work.tasks, and the natural key
    ``(predecessor_task_id, successor_task_id, relationship_type)`` is
    enforced by the ``uq_dependencies_relationship`` unique constraint.
    The no-self-cycle rule (``predecessor_task_id != successor_task_id``)
    is surfaced at the Pydantic layer via a ``@model_validator(mode=
    "after")`` so that a self-referential request raises 422 before any
    database round-trip.

    Required-on-create fields (runtime-enforced):
      - predecessor_task_id, successor_task_id: both mandatory intra-work
        FK references, validated against work.tasks before persist and
        required to be distinct

    Server-managed fields not exposed on create:
      - dependency_id, created_at, updated_at (auto-generated)
      - p6_relationship_id (populated via P6 sync, not manual)
    """

    predecessor_task_id: UUID
    successor_task_id: UUID
    relationship_type: DependencyType = DependencyType.FS
    lag_hours: Optional[Decimal] = Field(Decimal("0"))
    source_system: ProvenanceSource = ProvenanceSource.MANUAL
    is_active: bool = True
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL

    @model_validator(mode="after")
    def _reject_self_cycle(self) -> "DependencyCreate":
        """Mirror the DDL no-self-cycle intent at the API boundary."""
        if self.predecessor_task_id == self.successor_task_id:
            raise ValueError(
                "predecessor_task_id and successor_task_id must be different tasks"
            )
        return self


# ---------------------------------------------------------------------------
# 4.5c DependencyUpdate (packet 016)
# ---------------------------------------------------------------------------

class DependencyUpdate(BaseModel):
    """Request schema for updating a work.dependencies record.

    All fields are optional — only supplied fields are applied.  FK fields
    (predecessor_task_id, successor_task_id) are validated against
    work.tasks when supplied.  Server-managed fields (dependency_id,
    created_at, updated_at, p6_relationship_id) are not exposed for
    update.

    The no-self-cycle rule is re-asserted in the mutation service against
    the effective (post-update) predecessor/successor pair so that a
    partial update which swaps one side into equality with the stored
    other side still raises 422 before commit.  The Pydantic layer can
    only see the fields in the request body, so a PATCH-scoped
    model_validator would under-enforce the rule — the merged check
    lives in the service layer instead.
    """

    predecessor_task_id: Optional[UUID] = None
    successor_task_id: Optional[UUID] = None
    relationship_type: Optional[DependencyType] = None
    lag_hours: Optional[Decimal] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# 4.6 AssignmentRead
# ---------------------------------------------------------------------------


class AssignmentRead(BaseModel):
    """Read schema for work.assignments."""

    assignment_id: UUID
    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    crew_id: Optional[UUID] = None
    # Identity entity names — resolved via relationship when joined (packet 012e)
    employee_name: Optional[str] = None
    crew_name: Optional[str] = None
    assignment_role: AssignmentRole
    planned_hours: Optional[Decimal] = None
    actual_hours: Optional[Decimal] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    p6_task_resource_id: Optional[str] = None
    p6_resource_id: Optional[str] = None
    is_actual_participation: bool
    created_from_source: ProvenanceSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.6b AssignmentCreate (packet 015)
# ---------------------------------------------------------------------------

class AssignmentCreate(BaseModel):
    """Request schema for creating a work.assignments record.

    DDL contract: all four FK references (work_package_id, task_id,
    employee_id, crew_id) are individually nullable, but the assignments
    table enforces ``work_package_id IS NOT NULL OR task_id IS NOT NULL``
    via the ``ck_assignments_at_least_one_parent`` check constraint.  The
    parent-required rule is surfaced to API callers at the Pydantic layer
    so it raises a 422 before touching the database.

    Required-on-create fields (runtime-enforced):
      - At least one of work_package_id / task_id must be supplied
      - All other FKs (employee_id, crew_id) remain optional and are
        validated against identity when supplied

    Server-managed fields not exposed on create:
      - assignment_id, created_at, updated_at (auto-generated)
      - p6_task_resource_id, p6_resource_id (populated via P6 sync, not
        manual)
    """

    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    crew_id: Optional[UUID] = None
    assignment_role: AssignmentRole = AssignmentRole.PRIMARY
    planned_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_actual_participation: bool = False
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL

    @model_validator(mode="after")
    def _require_at_least_one_parent(self) -> "AssignmentCreate":
        """Mirror the DDL check constraint at the API boundary."""
        if self.work_package_id is None and self.task_id is None:
            raise ValueError(
                "At least one of work_package_id or task_id must be supplied"
            )
        return self


# ---------------------------------------------------------------------------
# 4.6c AssignmentUpdate (packet 015)
# ---------------------------------------------------------------------------

class AssignmentUpdate(BaseModel):
    """Request schema for updating a work.assignments record.

    All fields are optional — only supplied fields are applied.
    FK fields (work_package_id intra-work; task_id intra-work;
    employee_id and crew_id identity) are validated against their
    owning domain when supplied.
    Server-managed fields (assignment_id, created_at, updated_at,
    p6_task_resource_id, p6_resource_id) are not exposed for update.

    Note: the DDL ``ck_assignments_at_least_one_parent`` constraint is
    not re-checked at the Pydantic layer on update because the existing
    row already satisfies it and PATCH does not require both parents to
    be re-specified.  A partial update that explicitly null-outs both
    work_package_id and task_id would be caught by the database
    constraint at commit time — that scenario is not exercised by
    packet 015 and no additional API-layer handling is added.
    """

    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    employee_id: Optional[UUID] = None
    crew_id: Optional[UUID] = None
    assignment_role: Optional[AssignmentRole] = None
    planned_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_actual_participation: Optional[bool] = None


# ---------------------------------------------------------------------------
# 4.7 ExecutionIssueRead
# ---------------------------------------------------------------------------

class ExecutionIssueRead(BaseModel):
    """Read schema for work.execution_issues."""

    execution_issue_id: UUID
    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    apparatus_ref: Optional[UUID] = None
    issue_type: IssueType
    severity: Severity
    status: IssueStatus
    blocks_completion: bool
    summary: str
    details: Optional[str] = None
    reported_by: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    # Identity entity names — resolved via relationship when joined (packet 012e)
    reported_by_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_from_source: ProvenanceSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.7b ExecutionIssueCreate (packet 017)
# ---------------------------------------------------------------------------

class ExecutionIssueCreate(BaseModel):
    """Request schema for creating a work.execution_issues record.

    DDL contract: ``work_package_id`` and ``task_id`` are both individually
    nullable, but the execution_issues table enforces ``work_package_id IS
    NOT NULL OR task_id IS NOT NULL`` via the
    ``ck_execution_issues_at_least_one_parent`` check constraint.  The
    parent-required rule is surfaced to API callers at the Pydantic layer
    so it raises a 422 before touching the database.

    Required-on-create fields (runtime-enforced):
      - ``summary`` is NOT NULL in DDL
      - ``issue_type`` and ``severity`` are NOT NULL enum columns
      - At least one of ``work_package_id`` / ``task_id`` must be supplied;
        when supplied, each FK is validated against its owning work
        entity before persist

    Server-managed fields not exposed on create:
      - execution_issue_id, opened_at (server defaults), created_at,
        updated_at (auto-generated)

    Apparatus-side linkage (``apparatus_ref``) is accepted but is not
    validated against an FK because the asset domain is not wired in at
    this lane.
    """

    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    apparatus_ref: Optional[UUID] = None
    issue_type: IssueType
    severity: Severity
    status: IssueStatus = IssueStatus.OPEN
    blocks_completion: bool = False
    summary: str = Field(..., min_length=1)
    details: Optional[str] = None
    reported_by: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    resolution_type: Optional[ResolutionType] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL

    @model_validator(mode="after")
    def _require_at_least_one_parent(self) -> "ExecutionIssueCreate":
        """Mirror the DDL check constraint at the API boundary."""
        if self.work_package_id is None and self.task_id is None:
            raise ValueError(
                "At least one of work_package_id or task_id must be supplied"
            )
        return self


# ---------------------------------------------------------------------------
# 4.7c ExecutionIssueUpdate (packet 017)
# ---------------------------------------------------------------------------

class ExecutionIssueUpdate(BaseModel):
    """Request schema for updating a work.execution_issues record.

    All fields are optional — only supplied fields are applied.  FK fields
    (work_package_id, task_id) are validated against work.work_packages and
    work.tasks respectively when supplied.  Server-managed fields
    (execution_issue_id, opened_at, created_at, updated_at) are not
    exposed for update.

    Note: the DDL ``ck_execution_issues_at_least_one_parent`` constraint
    is not re-checked at the Pydantic layer on update because the
    existing row already satisfies it and PATCH does not require both
    parents to be re-specified.  A partial update that explicitly
    null-outs both work_package_id and task_id would be caught by the
    database constraint at commit time — that scenario is not exercised
    by packet 017 and no additional API-layer handling is added, mirroring
    the packet 015 (assignment update) approach.
    """

    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    apparatus_ref: Optional[UUID] = None
    issue_type: Optional[IssueType] = None
    severity: Optional[Severity] = None
    status: Optional[IssueStatus] = None
    blocks_completion: Optional[bool] = None
    summary: Optional[str] = Field(None, min_length=1)
    details: Optional[str] = None
    reported_by: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    resolution_type: Optional[ResolutionType] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# 4.8 ProgressSnapshotRead
# ---------------------------------------------------------------------------

class ProgressSnapshotRead(BaseModel):
    """Read schema for work.progress_snapshots."""

    progress_snapshot_id: UUID
    project_id: UUID
    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    snapshot_period_start: date
    snapshot_period_end: date
    snapshot_status: SnapshotStatus
    completed_apparatus_count: Optional[int] = None
    total_apparatus_count: Optional[int] = None
    percent_complete: Optional[Decimal] = None
    actual_labor_hours: Optional[Decimal] = None
    billable_amount: Optional[Decimal] = None
    billing_reference: Optional[str] = None
    approved_by: Optional[UUID] = None
    # Identity entity name — resolved via relationship when joined (packet 012e)
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    supersedes_snapshot_id: Optional[UUID] = None
    source_data_date: Optional[datetime] = None
    created_from_source: ProvenanceSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 4.8b ProgressSnapshotCreate (packet 018)
# ---------------------------------------------------------------------------

class ProgressSnapshotCreate(BaseModel):
    """Request schema for creating a work.progress_snapshots record.

    DDL contract (infra/database/migrations/work/002_work_tables.sql):
      - ``project_id`` NOT NULL — references work.projects(project_id)
      - ``work_package_id`` NULLABLE — references work.work_packages
      - ``task_id`` NULLABLE — references work.tasks
      - ``approved_by`` NULLABLE — references identity.users(user_id)
      - ``supersedes_snapshot_id`` NULLABLE — self-reference to
        work.progress_snapshots(progress_snapshot_id)
      - ``snapshot_period_start``, ``snapshot_period_end`` NOT NULL
      - ``snapshot_status`` NOT NULL with server default ``'draft'``
      - ``created_from_source`` NOT NULL with server default ``'manual'``
      - ck_progress_snapshots_period: snapshot_period_end >=
        snapshot_period_start
      - ck_progress_snapshots_percent: percent_complete BETWEEN 0 AND 100
        (or NULL)
      - ck_progress_snapshots_apparatus_counts: completed/total >= 0

    The ``period_end >= period_start`` rule is mirrored at the Pydantic
    layer via a model_validator so it raises a 422 before touching the
    database, in parity with the packet 015 AssignmentCreate and packet
    017 ExecutionIssueCreate DDL-constraint mirroring pattern.  The
    percent-complete and apparatus-count ranges are mirrored via
    Field-level ge/le constraints.

    Required-on-create fields (runtime-enforced):
      - ``project_id`` is NOT NULL in DDL
      - ``snapshot_period_start`` / ``snapshot_period_end`` are NOT NULL
      - ``snapshot_status`` defaults to ``draft`` via the enum default
      - ``created_from_source`` defaults to ``manual`` via the enum default

    Server-managed fields not exposed on create:
      - progress_snapshot_id (server default), created_at, updated_at
        (auto-generated)

    Self-reference (supersedes_snapshot_id) must not equal the target
    record on create.  Because progress_snapshot_id is assigned server-side
    on INSERT, no self-cycle is possible at create time; the self-reference
    rule is enforced only on update via the mutation service.
    """

    project_id: UUID
    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    snapshot_period_start: date
    snapshot_period_end: date
    snapshot_status: SnapshotStatus = SnapshotStatus.DRAFT
    completed_apparatus_count: Optional[int] = Field(None, ge=0)
    total_apparatus_count: Optional[int] = Field(None, ge=0)
    percent_complete: Optional[Decimal] = Field(None, ge=0, le=100)
    actual_labor_hours: Optional[Decimal] = Field(None, ge=0)
    billable_amount: Optional[Decimal] = Field(None, ge=0)
    billing_reference: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    supersedes_snapshot_id: Optional[UUID] = None
    source_data_date: Optional[datetime] = None
    created_from_source: ProvenanceSource = ProvenanceSource.MANUAL

    @model_validator(mode="after")
    def _require_period_monotonic(self) -> "ProgressSnapshotCreate":
        """Mirror the DDL ``ck_progress_snapshots_period`` constraint."""
        if self.snapshot_period_end < self.snapshot_period_start:
            raise ValueError(
                "snapshot_period_end must be on or after snapshot_period_start"
            )
        return self


# ---------------------------------------------------------------------------
# 4.8c ProgressSnapshotUpdate (packet 018)
# ---------------------------------------------------------------------------

class ProgressSnapshotUpdate(BaseModel):
    """Request schema for updating a work.progress_snapshots record.

    All fields are optional — only supplied fields are applied.  FK fields
    (project_id, work_package_id, task_id, supersedes_snapshot_id,
    approved_by) are validated against their owning domains when supplied.
    Server-managed fields (progress_snapshot_id, created_at, updated_at)
    are not exposed for update.

    Self-reference rule: a progress snapshot cannot supersede itself.
    Because partial updates can change either the target id (implicitly,
    via PATCH target) or ``supersedes_snapshot_id`` explicitly, the
    self-cycle guard is applied at the mutation-service layer where the
    effective pair (target id, supplied supersedes id) is known —
    mirroring the packet 016 dependency update pattern.

    Period monotonicity is re-checked at the service layer when either
    end of the period is supplied, using the existing row's period bound
    when only one end is changed.
    """

    project_id: Optional[UUID] = None
    work_package_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    snapshot_period_start: Optional[date] = None
    snapshot_period_end: Optional[date] = None
    snapshot_status: Optional[SnapshotStatus] = None
    completed_apparatus_count: Optional[int] = Field(None, ge=0)
    total_apparatus_count: Optional[int] = Field(None, ge=0)
    percent_complete: Optional[Decimal] = Field(None, ge=0, le=100)
    actual_labor_hours: Optional[Decimal] = Field(None, ge=0)
    billable_amount: Optional[Decimal] = Field(None, ge=0)
    billing_reference: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    supersedes_snapshot_id: Optional[UUID] = None
    source_data_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

WORK_SCHEMA_REGISTRY = {
    "ProjectRead": ProjectRead,
    "ProjectCreate": ProjectCreate,
    "ProjectUpdate": ProjectUpdate,
    "WBSNodeRead": WBSNodeRead,
    "WorkPackageRead": WorkPackageRead,
    "WorkPackageCreate": WorkPackageCreate,
    "WorkPackageUpdate": WorkPackageUpdate,
    "TaskRead": TaskRead,
    "TaskCreate": TaskCreate,
    "TaskUpdate": TaskUpdate,
    "DependencyRead": DependencyRead,
    "DependencyCreate": DependencyCreate,
    "DependencyUpdate": DependencyUpdate,
    "AssignmentRead": AssignmentRead,
    "AssignmentCreate": AssignmentCreate,
    "AssignmentUpdate": AssignmentUpdate,
    "ExecutionIssueRead": ExecutionIssueRead,
    "ExecutionIssueCreate": ExecutionIssueCreate,
    "ExecutionIssueUpdate": ExecutionIssueUpdate,
    "ProgressSnapshotRead": ProgressSnapshotRead,
    "ProgressSnapshotCreate": ProgressSnapshotCreate,
    "ProgressSnapshotUpdate": ProgressSnapshotUpdate,
}

assert len(WORK_SCHEMA_REGISTRY) == 22, (
    f"Expected 22 work schemas (8 read + 14 write), got {len(WORK_SCHEMA_REGISTRY)}"
)
