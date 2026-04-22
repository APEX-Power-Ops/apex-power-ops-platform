"""
PM/Work Domain — Python Enum Definitions
=========================================
Packet: 2026-04-13-pm-schema-010a
Authority: infra/database/migrations/work/001_work_enums.sql

These Python enums mirror the validated work.*_enum types exactly.
Values and ordering match the DDL.  Do not modify without a
corresponding SQL migration.

16 enums total:
  Provenance (2): ProvenanceSource, ProvenanceStatus
  Project (1):    ProjectStatus
  Work Package (4): WPLifecycle, WorkType, Priority, BillingState
  Task (2):       TaskLifecycle, TaskType
  Dependency (1): DependencyType
  Assignment (1): AssignmentRole
  Execution Issue (4): IssueType, Severity, IssueStatus, ResolutionType
  Progress Snapshot (1): SnapshotStatus
"""

import enum


# ---------------------------------------------------------------------------
# 5.1 Provenance Enums
# ---------------------------------------------------------------------------

class ProvenanceSource(str, enum.Enum):
    """Origin system for a record (work.provenance_source_enum)."""
    MANUAL = "manual"
    P6_IMPORT = "p6_import"
    API = "api"
    AUTOMATION = "automation"
    MIGRATION = "migration"
    BULK_UPLOAD = "bulk_upload"


class ProvenanceStatus(str, enum.Enum):
    """Quality/trust level of a record (work.provenance_status_enum)."""
    CURATED = "curated"
    IMPORTED = "imported"
    PROVISIONAL = "provisional"
    VALIDATED = "validated"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# 4.1 Project Enums
# ---------------------------------------------------------------------------

class ProjectStatus(str, enum.Enum):
    """Project lifecycle states (work.project_status_enum)."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETE = "complete"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# 4.2 Work Package Enums
# ---------------------------------------------------------------------------

class WPLifecycle(str, enum.Enum):
    """Work-package 9-state lifecycle model (work.wp_lifecycle_enum)."""
    DRAFT = "draft"
    PLANNED = "planned"
    READY = "ready"
    ACTIVE = "active"
    BLOCKED = "blocked"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETE = "complete"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class WorkType(str, enum.Enum):
    """Execution classification for a work package (work.work_type_enum)."""
    TESTING = "testing"
    COMMISSIONING = "commissioning"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    STUDY = "study"
    OTHER = "other"


class Priority(str, enum.Enum):
    """Business priority level (work.priority_enum)."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class BillingState(str, enum.Enum):
    """Financial workflow state for a work package (work.billing_state_enum)."""
    NOT_BILLABLE = "not_billable"
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"
    DISPUTED = "disputed"


# ---------------------------------------------------------------------------
# 4.3 Task Enums
# ---------------------------------------------------------------------------

class TaskLifecycle(str, enum.Enum):
    """Task 7-state lifecycle model (work.task_lifecycle_enum)."""
    NOT_STARTED = "not_started"
    READY = "ready"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Task type classification, aligned with P6 activity types (work.task_type_enum)."""
    TASK = "task"
    MILESTONE = "milestone"
    FINISH_MILESTONE = "finish_milestone"
    LEVEL_OF_EFFORT = "level_of_effort"
    WBS_SUMMARY = "wbs_summary"


# ---------------------------------------------------------------------------
# 4.5 Dependency Enums
# ---------------------------------------------------------------------------

class DependencyType(str, enum.Enum):
    """Schedule relationship types (work.dependency_type_enum)."""
    FS = "FS"
    SS = "SS"
    SF = "SF"
    FF = "FF"


# ---------------------------------------------------------------------------
# 4.6 Assignment Enums
# ---------------------------------------------------------------------------

class AssignmentRole(str, enum.Enum):
    """Role classification for resource assignments (work.assignment_role_enum)."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    LEAD = "lead"
    OBSERVER = "observer"
    SUPPORT = "support"


# ---------------------------------------------------------------------------
# 4.7 Execution Issue Enums
# ---------------------------------------------------------------------------

class IssueType(str, enum.Enum):
    """Classification of execution issues (work.issue_type_enum)."""
    EQUIPMENT_NOT_READY = "equipment_not_ready"
    TEST_FAILURE = "test_failure"
    SETTINGS_INCORRECT = "settings_incorrect"
    ACCESS_BLOCKED = "access_blocked"
    SAFETY_HOLD = "safety_hold"
    MATERIAL_MISSING = "material_missing"
    DOCUMENTATION_GAP = "documentation_gap"
    OTHER = "other"


class Severity(str, enum.Enum):
    """Issue severity level (work.severity_enum)."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class IssueStatus(str, enum.Enum):
    """Execution issue 5-state model (work.issue_status_enum)."""
    OPEN = "open"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ResolutionType(str, enum.Enum):
    """Disposition of a resolved execution issue (work.resolution_type_enum)."""
    REPAIRED = "repaired"
    RETESTED_PASSED = "retested_passed"
    DEFERRED = "deferred"
    ACCEPTED_AS_IS = "accepted_as_is"
    REPLACED = "replaced"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# 4.8 Progress Snapshot Enums
# ---------------------------------------------------------------------------

class SnapshotStatus(str, enum.Enum):
    """Progress snapshot 4-state approval model (work.snapshot_status_enum)."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Enum registry — maps SQL enum type name to Python class
# ---------------------------------------------------------------------------

WORK_ENUM_REGISTRY = {
    "provenance_source_enum": ProvenanceSource,
    "provenance_status_enum": ProvenanceStatus,
    "project_status_enum": ProjectStatus,
    "wp_lifecycle_enum": WPLifecycle,
    "work_type_enum": WorkType,
    "priority_enum": Priority,
    "billing_state_enum": BillingState,
    "task_lifecycle_enum": TaskLifecycle,
    "task_type_enum": TaskType,
    "dependency_type_enum": DependencyType,
    "assignment_role_enum": AssignmentRole,
    "issue_type_enum": IssueType,
    "severity_enum": Severity,
    "issue_status_enum": IssueStatus,
    "resolution_type_enum": ResolutionType,
    "snapshot_status_enum": SnapshotStatus,
}

assert len(WORK_ENUM_REGISTRY) == 16, (
    f"Expected 16 work enums, got {len(WORK_ENUM_REGISTRY)}"
)
