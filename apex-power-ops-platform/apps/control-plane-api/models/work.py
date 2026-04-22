"""
PM/Work Domain — SQLAlchemy ORM Models
=======================================
Packet: 2026-04-13-pm-schema-010a (original)
Updated: 2026-04-14-pm-schema-011e (org FK alignment)
Authority: infra/database/migrations/work/002_work_tables.sql
           infra/database/migrations/work/007_work_org_fk_activation.sql

8 models for the validated work.* tables:
  1. Project           — work.projects
  2. WBSNode           — work.wbs_nodes
  3. WorkPackage        — work.work_packages
  4. Task              — work.tasks
  5. Dependency         — work.dependencies
  6. Assignment         — work.assignments
  7. ExecutionIssue     — work.execution_issues
  8. ProgressSnapshot   — work.progress_snapshots

Column names, types, nullability, defaults, and constraints match the
validated DDL exactly.

Org-domain FKs (6 total) are now represented as SQLAlchemy ForeignKey
columns with relationship() declarations, aligned to the constraints
activated by packet 011d.  Remaining cross-domain FKs (identity.*,
asset.*) are still bare UUID columns — those constraints will be added
when the target domains are available.

Do not add FastAPI routes, service-layer logic, or background jobs in
this file.
"""

from sqlalchemy import (
    Column, String, Text, Integer, Numeric, Boolean, Date,
    ForeignKey, CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from .base import Base
from .work_enums import (
    ProvenanceSource, ProvenanceStatus, ProjectStatus,
    WPLifecycle, WorkType, Priority, BillingState,
    TaskLifecycle, TaskType, DependencyType, AssignmentRole,
    IssueType, Severity, IssueStatus, ResolutionType,
    SnapshotStatus,
)


# ---------------------------------------------------------------------------
# Helper: create a PostgreSQL ENUM bound to the work schema
# ---------------------------------------------------------------------------

def _pg_enum(py_enum, name: str) -> ENUM:
    """Build a PostgreSQL ENUM type referencing an existing work.* enum."""
    return ENUM(
        py_enum,
        name=name,
        schema="work",
        create_type=False,   # enum already exists in the DB
    )


# ---------------------------------------------------------------------------
# 4.1 projects
# ---------------------------------------------------------------------------

class Project(Base):
    """Top-level project container (work.projects)."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("project_code", name="uq_projects_project_code"),
        CheckConstraint(
            "planned_end_at IS NULL OR planned_start_at IS NULL "
            "OR planned_end_at > planned_start_at",
            name="ck_projects_planned_dates",
        ),
        {"schema": "work"},
    )

    project_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_code = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    status = Column(
        _pg_enum(ProjectStatus, "project_status_enum"),
        nullable=False, server_default="draft",
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.clients.client_id"),
        nullable=False,
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.sites.site_id"),
        nullable=False,
    )
    business_unit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.business_units.business_unit_id"),
        nullable=True,
    )
    description = Column(Text, nullable=True)
    contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.contracts.contract_id"),
        nullable=True,
    )
    planned_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    planned_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    project_priority = Column(Text, nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    provenance_status = Column(
        _pg_enum(ProvenanceStatus, "provenance_status_enum"),
        nullable=False, server_default="curated",
    )
    p6_project_id = Column(Text, nullable=True)
    p6_short_name = Column(Text, nullable=True)
    p6_data_date = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — org domain (packet 011e)
    client = relationship(
        "Client", back_populates="projects",
        foreign_keys=[client_id],
    )
    site = relationship(
        "Site", back_populates="projects",
        foreign_keys=[site_id],
    )
    business_unit = relationship(
        "BusinessUnit", back_populates="projects",
        foreign_keys=[business_unit_id],
    )
    contract = relationship(
        "Contract", back_populates="projects",
        foreign_keys=[contract_id],
    )

    # Relationships — within work schema
    wbs_nodes = relationship("WBSNode", back_populates="project")
    work_packages = relationship("WorkPackage", back_populates="project")
    progress_snapshots = relationship("ProgressSnapshot", back_populates="project")


# ---------------------------------------------------------------------------
# 4.4 wbs_nodes
# ---------------------------------------------------------------------------

class WBSNode(Base):
    """N-level work breakdown structure hierarchy (work.wbs_nodes)."""

    __tablename__ = "wbs_nodes"
    __table_args__ = (
        UniqueConstraint("project_id", "wbs_code", name="uq_wbs_nodes_project_code"),
        {"schema": "work"},
    )

    wbs_node_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.projects.project_id"),
        nullable=False,
    )
    parent_wbs_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.wbs_nodes.wbs_node_id"),
        nullable=True,
    )
    wbs_code = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=True)
    p6_wbs_id = Column(Text, nullable=True)
    p6_parent_wbs_id = Column(Text, nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project = relationship("Project", back_populates="wbs_nodes")
    parent = relationship("WBSNode", remote_side=[wbs_node_id], backref="children")
    work_packages = relationship(
        "WorkPackage", back_populates="primary_wbs_node",
        foreign_keys="WorkPackage.primary_wbs_node_id",
    )
    tasks = relationship(
        "Task", back_populates="primary_wbs_node",
        foreign_keys="Task.primary_wbs_node_id",
    )


# ---------------------------------------------------------------------------
# 4.2 work_packages
# ---------------------------------------------------------------------------

class WorkPackage(Base):
    """Primary operating object of the PM/work domain (work.work_packages)."""

    __tablename__ = "work_packages"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "work_package_code",
            name="uq_work_packages_project_code",
        ),
        CheckConstraint(
            "scheduled_end_at IS NULL OR scheduled_start_at IS NULL "
            "OR scheduled_end_at > scheduled_start_at",
            name="ck_work_packages_scheduled_dates",
        ),
        CheckConstraint(
            "progress_percent IS NULL OR "
            "(progress_percent >= 0 AND progress_percent <= 100)",
            name="ck_work_packages_progress",
        ),
        {"schema": "work"},
    )

    work_package_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.projects.project_id"),
        nullable=False,
    )
    work_package_code = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    work_type = Column(
        _pg_enum(WorkType, "work_type_enum"), nullable=False,
    )
    lifecycle_state = Column(
        _pg_enum(WPLifecycle, "wp_lifecycle_enum"),
        nullable=False, server_default="draft",
    )
    priority = Column(
        _pg_enum(Priority, "priority_enum"),
        nullable=False, server_default="normal",
    )
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.clients.client_id"),
        nullable=False,
    )
    site_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org.sites.site_id"),
        nullable=False,
    )
    primary_wbs_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.wbs_nodes.wbs_node_id"),
        nullable=True,
    )
    scope_source_ref = Column(UUID(as_uuid=True), nullable=True)    # legacy traceability
    asset_class_id = Column(UUID(as_uuid=True), nullable=True)      # DEFERRED FK → asset.asset_classes
    apparatus_cluster_ref = Column(Text, nullable=True)
    assigned_crew_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.crews.crew_id"),
        nullable=True,
    )
    scheduled_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    scheduled_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    progress_percent = Column(Numeric(5, 2), nullable=True)
    billing_state = Column(
        _pg_enum(BillingState, "billing_state_enum"), nullable=True,
    )
    execution_summary = Column(Text, nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    provenance_status = Column(
        _pg_enum(ProvenanceStatus, "provenance_status_enum"),
        nullable=False, server_default="curated",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships — org domain (packet 011e)
    client = relationship(
        "Client", back_populates="work_packages",
        foreign_keys=[client_id],
    )
    site = relationship(
        "Site", back_populates="work_packages",
        foreign_keys=[site_id],
    )

    # Relationships — identity domain (packet 012e)
    assigned_crew = relationship(
        "Crew", back_populates="assigned_work_packages",
        foreign_keys=[assigned_crew_id],
    )

    # Relationships — within work schema
    project = relationship("Project", back_populates="work_packages")
    primary_wbs_node = relationship(
        "WBSNode", back_populates="work_packages",
        foreign_keys=[primary_wbs_node_id],
    )
    tasks = relationship("Task", back_populates="work_package")
    assignments = relationship(
        "Assignment", back_populates="work_package",
        foreign_keys="Assignment.work_package_id",
    )
    execution_issues = relationship(
        "ExecutionIssue", back_populates="work_package",
        foreign_keys="ExecutionIssue.work_package_id",
    )
    progress_snapshots = relationship(
        "ProgressSnapshot", back_populates="work_package",
        foreign_keys="ProgressSnapshot.work_package_id",
    )


# ---------------------------------------------------------------------------
# 4.3 tasks
# ---------------------------------------------------------------------------

class Task(Base):
    """Schedulable unit of work within a work package (work.tasks)."""

    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("work_package_id", "task_code", name="uq_tasks_wp_code"),
        CheckConstraint(
            "planned_end_at IS NULL OR planned_start_at IS NULL "
            "OR planned_end_at > planned_start_at",
            name="ck_tasks_planned_dates",
        ),
        {"schema": "work"},
    )

    task_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    work_package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.work_packages.work_package_id"),
        nullable=False,
    )
    task_code = Column(Text, nullable=True)
    title = Column(Text, nullable=False)
    task_type = Column(
        _pg_enum(TaskType, "task_type_enum"),
        nullable=False, server_default="task",
    )
    lifecycle_state = Column(
        _pg_enum(TaskLifecycle, "task_lifecycle_enum"),
        nullable=False, server_default="not_started",
    )
    planned_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    planned_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    actual_end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    early_start_at = Column(TIMESTAMP(timezone=True), nullable=True)    # P6 planning truth
    early_end_at = Column(TIMESTAMP(timezone=True), nullable=True)      # P6 planning truth
    late_start_at = Column(TIMESTAMP(timezone=True), nullable=True)     # P6 planning truth
    late_end_at = Column(TIMESTAMP(timezone=True), nullable=True)       # P6 planning truth
    duration_hours = Column(Numeric(10, 2), nullable=True)
    remaining_duration_hours = Column(Numeric(10, 2), nullable=True)
    estimated_labor_hours = Column(Numeric(10, 2), nullable=True)
    actual_labor_hours = Column(Numeric(10, 2), nullable=True)
    total_float_hours = Column(Numeric(10, 2), nullable=True)
    schedule_priority_override = Column(
        _pg_enum(Priority, "priority_enum"), nullable=True,
    )
    primary_wbs_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.wbs_nodes.wbs_node_id"),
        nullable=True,
    )
    p6_task_id = Column(Text, nullable=True)
    p6_activity_id = Column(Text, nullable=True)
    p6_calendar_id = Column(Text, nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    provenance_status = Column(
        _pg_enum(ProvenanceStatus, "provenance_status_enum"),
        nullable=False, server_default="curated",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    work_package = relationship("WorkPackage", back_populates="tasks")
    primary_wbs_node = relationship(
        "WBSNode", back_populates="tasks",
        foreign_keys=[primary_wbs_node_id],
    )
    predecessor_dependencies = relationship(
        "Dependency", back_populates="successor_task",
        foreign_keys="Dependency.successor_task_id",
    )
    successor_dependencies = relationship(
        "Dependency", back_populates="predecessor_task",
        foreign_keys="Dependency.predecessor_task_id",
    )
    assignments = relationship(
        "Assignment", back_populates="task",
        foreign_keys="Assignment.task_id",
    )
    execution_issues = relationship(
        "ExecutionIssue", back_populates="task",
        foreign_keys="ExecutionIssue.task_id",
    )
    progress_snapshots = relationship(
        "ProgressSnapshot", back_populates="task",
        foreign_keys="ProgressSnapshot.task_id",
    )


# ---------------------------------------------------------------------------
# 4.5 dependencies
# ---------------------------------------------------------------------------

class Dependency(Base):
    """Task-to-task schedule relationship (work.dependencies)."""

    __tablename__ = "dependencies"
    __table_args__ = (
        UniqueConstraint(
            "predecessor_task_id", "successor_task_id", "relationship_type",
            name="uq_dependencies_relationship",
        ),
        {"schema": "work"},
    )

    dependency_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    predecessor_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.tasks.task_id"),
        nullable=False,
    )
    successor_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.tasks.task_id"),
        nullable=False,
    )
    relationship_type = Column(
        _pg_enum(DependencyType, "dependency_type_enum"),
        nullable=False, server_default="FS",
    )
    lag_hours = Column(Numeric(10, 2), nullable=True, server_default=text("0"))
    source_system = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    p6_relationship_id = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    predecessor_task = relationship(
        "Task", back_populates="successor_dependencies",
        foreign_keys=[predecessor_task_id],
    )
    successor_task = relationship(
        "Task", back_populates="predecessor_dependencies",
        foreign_keys=[successor_task_id],
    )


# ---------------------------------------------------------------------------
# 4.6 assignments
# ---------------------------------------------------------------------------

class Assignment(Base):
    """Resource assignment at work-package or task level (work.assignments)."""

    __tablename__ = "assignments"
    __table_args__ = (
        CheckConstraint(
            "work_package_id IS NOT NULL OR task_id IS NOT NULL",
            name="ck_assignments_at_least_one_parent",
        ),
        {"schema": "work"},
    )

    assignment_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    work_package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.work_packages.work_package_id"),
        nullable=True,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.tasks.task_id"),
        nullable=True,
    )
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.employees.employee_id"),
        nullable=True,
    )
    crew_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.crews.crew_id"),
        nullable=True,
    )
    assignment_role = Column(
        _pg_enum(AssignmentRole, "assignment_role_enum"),
        nullable=False, server_default="primary",
    )
    planned_hours = Column(Numeric(10, 2), nullable=True)
    actual_hours = Column(Numeric(10, 2), nullable=True)
    start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    p6_task_resource_id = Column(Text, nullable=True)
    p6_resource_id = Column(Text, nullable=True)
    is_actual_participation = Column(
        Boolean, nullable=False, server_default=text("false"),
    )
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    work_package = relationship(
        "WorkPackage", back_populates="assignments",
        foreign_keys=[work_package_id],
    )
    task = relationship(
        "Task", back_populates="assignments",
        foreign_keys=[task_id],
    )

    # Relationships — identity domain (packet 012e)
    employee = relationship(
        "Employee", back_populates="assignments",
        foreign_keys=[employee_id],
    )
    crew = relationship(
        "Crew", back_populates="assignments",
        foreign_keys=[crew_id],
    )


# ---------------------------------------------------------------------------
# 4.7 execution_issues
# ---------------------------------------------------------------------------

class ExecutionIssue(Base):
    """Field execution issue record (work.execution_issues)."""

    __tablename__ = "execution_issues"
    __table_args__ = (
        {"schema": "work"},
    )

    execution_issue_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    work_package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.work_packages.work_package_id"),
        nullable=True,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.tasks.task_id"),
        nullable=True,
    )
    apparatus_ref = Column(UUID(as_uuid=True), nullable=True)       # asset-side linkage (not FK)
    issue_type = Column(
        _pg_enum(IssueType, "issue_type_enum"), nullable=False,
    )
    severity = Column(
        _pg_enum(Severity, "severity_enum"), nullable=False,
    )
    status = Column(
        _pg_enum(IssueStatus, "issue_status_enum"),
        nullable=False, server_default="open",
    )
    blocks_completion = Column(Boolean, nullable=False, server_default=text("false"))
    summary = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    reported_by = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.user_id"),
        nullable=True,
    )
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.user_id"),
        nullable=True,
    )
    resolution_type = Column(
        _pg_enum(ResolutionType, "resolution_type_enum"), nullable=True,
    )
    opened_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    closed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    work_package = relationship(
        "WorkPackage", back_populates="execution_issues",
        foreign_keys=[work_package_id],
    )
    task = relationship(
        "Task", back_populates="execution_issues",
        foreign_keys=[task_id],
    )

    # Relationships — identity domain (packet 012e)
    reporter = relationship(
        "User", back_populates="reported_issues",
        foreign_keys=[reported_by],
    )
    assignee = relationship(
        "User", back_populates="assigned_issues",
        foreign_keys=[assigned_to],
    )


# ---------------------------------------------------------------------------
# 4.8 progress_snapshots
# ---------------------------------------------------------------------------

class ProgressSnapshot(Base):
    """Period-truth progress reporting with approval workflow (work.progress_snapshots)."""

    __tablename__ = "progress_snapshots"
    __table_args__ = (
        CheckConstraint(
            "snapshot_period_end >= snapshot_period_start",
            name="ck_progress_snapshots_period",
        ),
        CheckConstraint(
            "percent_complete IS NULL OR "
            "(percent_complete >= 0 AND percent_complete <= 100)",
            name="ck_progress_snapshots_percent",
        ),
        CheckConstraint(
            "(completed_apparatus_count IS NULL OR completed_apparatus_count >= 0) "
            "AND (total_apparatus_count IS NULL OR total_apparatus_count >= 0)",
            name="ck_progress_snapshots_apparatus_counts",
        ),
        {"schema": "work"},
    )

    progress_snapshot_id = Column(
        UUID(as_uuid=True), primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.projects.project_id"),
        nullable=False,
    )
    work_package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.work_packages.work_package_id"),
        nullable=True,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.tasks.task_id"),
        nullable=True,
    )
    snapshot_period_start = Column(Date, nullable=False)
    snapshot_period_end = Column(Date, nullable=False)
    snapshot_status = Column(
        _pg_enum(SnapshotStatus, "snapshot_status_enum"),
        nullable=False, server_default="draft",
    )
    completed_apparatus_count = Column(Integer, nullable=True)
    total_apparatus_count = Column(Integer, nullable=True)
    percent_complete = Column(Numeric(5, 2), nullable=True)
    actual_labor_hours = Column(Numeric(10, 2), nullable=True)
    billable_amount = Column(Numeric(12, 2), nullable=True)
    billing_reference = Column(Text, nullable=True)
    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.user_id"),
        nullable=True,
    )
    approved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    supersedes_snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work.progress_snapshots.progress_snapshot_id"),
        nullable=True,
    )
    source_data_date = Column(TIMESTAMP(timezone=True), nullable=True)
    created_from_source = Column(
        _pg_enum(ProvenanceSource, "provenance_source_enum"),
        nullable=False, server_default="manual",
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project = relationship("Project", back_populates="progress_snapshots")
    work_package = relationship(
        "WorkPackage", back_populates="progress_snapshots",
        foreign_keys=[work_package_id],
    )
    task = relationship(
        "Task", back_populates="progress_snapshots",
        foreign_keys=[task_id],
    )
    supersedes = relationship(
        "ProgressSnapshot", remote_side=[progress_snapshot_id],
        backref="superseded_by",
    )

    # Relationships — identity domain (packet 012e)
    approver = relationship(
        "User", back_populates="approved_snapshots",
        foreign_keys=[approved_by],
    )


# ---------------------------------------------------------------------------
# Model registry — maps SQL table name to ORM class
# ---------------------------------------------------------------------------

WORK_MODEL_REGISTRY = {
    "projects": Project,
    "wbs_nodes": WBSNode,
    "work_packages": WorkPackage,
    "tasks": Task,
    "dependencies": Dependency,
    "assignments": Assignment,
    "execution_issues": ExecutionIssue,
    "progress_snapshots": ProgressSnapshot,
}

assert len(WORK_MODEL_REGISTRY) == 8, (
    f"Expected 8 work models, got {len(WORK_MODEL_REGISTRY)}"
)
