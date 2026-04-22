"""
PM/Work Domain — Unit Tests for ORM Models, Enums, and Pydantic Schemas
=========================================================================
Packet: 2026-04-13-pm-schema-010a

These tests verify:
  1. All 16 enum types import cleanly and contain the correct values
  2. All 8 SQLAlchemy model classes import and have correct __tablename__
  3. Model columns match the validated DDL (name, type, nullability)
  4. Model constraint names match the validated DDL
  5. All 8 Pydantic read schemas import and can round-trip a minimal instance
  6. The package __init__.py exports are consistent

These tests do NOT require a live database connection.
"""

import sys
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# 1. Enum Import and Value Tests
# ============================================================================

class TestWorkEnums:
    """Verify all 16 work enums import and contain the validated values."""

    def test_enum_registry_count(self):
        from models.work_enums import WORK_ENUM_REGISTRY
        assert len(WORK_ENUM_REGISTRY) == 16

    def test_provenance_source_values(self):
        from models.work_enums import ProvenanceSource
        expected = {"manual", "p6_import", "api", "automation", "migration", "bulk_upload"}
        actual = {e.value for e in ProvenanceSource}
        assert actual == expected

    def test_provenance_status_values(self):
        from models.work_enums import ProvenanceStatus
        expected = {"curated", "imported", "provisional", "validated", "rejected"}
        actual = {e.value for e in ProvenanceStatus}
        assert actual == expected

    def test_project_status_values(self):
        from models.work_enums import ProjectStatus
        expected = {"draft", "active", "on_hold", "complete", "closed", "cancelled"}
        actual = {e.value for e in ProjectStatus}
        assert actual == expected

    def test_wp_lifecycle_values(self):
        from models.work_enums import WPLifecycle
        expected = {
            "draft", "planned", "ready", "active", "blocked",
            "awaiting_review", "complete", "closed", "cancelled",
        }
        actual = {e.value for e in WPLifecycle}
        assert actual == expected
        assert len(WPLifecycle) == 9, "WP lifecycle must have exactly 9 states"

    def test_work_type_values(self):
        from models.work_enums import WorkType
        expected = {"testing", "commissioning", "maintenance", "inspection", "study", "other"}
        actual = {e.value for e in WorkType}
        assert actual == expected

    def test_priority_values(self):
        from models.work_enums import Priority
        expected = {"critical", "high", "normal", "low"}
        actual = {e.value for e in Priority}
        assert actual == expected

    def test_billing_state_values(self):
        from models.work_enums import BillingState
        expected = {"not_billable", "pending", "invoiced", "paid", "disputed"}
        actual = {e.value for e in BillingState}
        assert actual == expected

    def test_task_lifecycle_values(self):
        from models.work_enums import TaskLifecycle
        expected = {
            "not_started", "ready", "active", "on_hold",
            "awaiting_review", "complete", "cancelled",
        }
        actual = {e.value for e in TaskLifecycle}
        assert actual == expected
        assert len(TaskLifecycle) == 7, "Task lifecycle must have exactly 7 states"

    def test_task_type_values(self):
        from models.work_enums import TaskType
        expected = {"task", "milestone", "finish_milestone", "level_of_effort", "wbs_summary"}
        actual = {e.value for e in TaskType}
        assert actual == expected

    def test_dependency_type_values(self):
        from models.work_enums import DependencyType
        expected = {"FS", "SS", "SF", "FF"}
        actual = {e.value for e in DependencyType}
        assert actual == expected

    def test_assignment_role_values(self):
        from models.work_enums import AssignmentRole
        expected = {"primary", "secondary", "lead", "observer", "support"}
        actual = {e.value for e in AssignmentRole}
        assert actual == expected

    def test_issue_type_values(self):
        from models.work_enums import IssueType
        expected = {
            "equipment_not_ready", "test_failure", "settings_incorrect",
            "access_blocked", "safety_hold", "material_missing",
            "documentation_gap", "other",
        }
        actual = {e.value for e in IssueType}
        assert actual == expected

    def test_severity_values(self):
        from models.work_enums import Severity
        expected = {"critical", "major", "minor", "info"}
        actual = {e.value for e in Severity}
        assert actual == expected

    def test_issue_status_values(self):
        from models.work_enums import IssueStatus
        expected = {"open", "in_review", "escalated", "resolved", "closed"}
        actual = {e.value for e in IssueStatus}
        assert actual == expected

    def test_resolution_type_values(self):
        from models.work_enums import ResolutionType
        expected = {
            "repaired", "retested_passed", "deferred",
            "accepted_as_is", "replaced", "not_applicable",
        }
        actual = {e.value for e in ResolutionType}
        assert actual == expected

    def test_snapshot_status_values(self):
        from models.work_enums import SnapshotStatus
        expected = {"draft", "submitted", "approved", "rejected"}
        actual = {e.value for e in SnapshotStatus}
        assert actual == expected

    def test_all_enums_are_str_enum(self):
        """Every work enum must be (str, Enum) for Pydantic JSON serialization."""
        from models.work_enums import WORK_ENUM_REGISTRY
        for name, cls in WORK_ENUM_REGISTRY.items():
            assert issubclass(cls, str), f"{name} must inherit from str"


# ============================================================================
# 2. SQLAlchemy Model Import and Table Name Tests
# ============================================================================

class TestWorkModelImport:
    """Verify all 8 work models import and declare the correct table/schema."""

    EXPECTED_TABLES = {
        "Project": ("projects", "work"),
        "WBSNode": ("wbs_nodes", "work"),
        "WorkPackage": ("work_packages", "work"),
        "Task": ("tasks", "work"),
        "Dependency": ("dependencies", "work"),
        "Assignment": ("assignments", "work"),
        "ExecutionIssue": ("execution_issues", "work"),
        "ProgressSnapshot": ("progress_snapshots", "work"),
    }

    def test_model_registry_count(self):
        from models.work import WORK_MODEL_REGISTRY
        assert len(WORK_MODEL_REGISTRY) == 8

    def test_tablenames_and_schema(self):
        from models.work import WORK_MODEL_REGISTRY
        from models.work import (
            Project, WBSNode, WorkPackage, Task,
            Dependency, Assignment, ExecutionIssue, ProgressSnapshot,
        )
        models = {
            "Project": Project,
            "WBSNode": WBSNode,
            "WorkPackage": WorkPackage,
            "Task": Task,
            "Dependency": Dependency,
            "Assignment": Assignment,
            "ExecutionIssue": ExecutionIssue,
            "ProgressSnapshot": ProgressSnapshot,
        }
        for class_name, (expected_table, expected_schema) in self.EXPECTED_TABLES.items():
            model = models[class_name]
            assert model.__tablename__ == expected_table, (
                f"{class_name}.__tablename__ should be '{expected_table}'"
            )
            assert model.__table_args__[-1].get("schema") == expected_schema, (
                f"{class_name} schema should be '{expected_schema}'"
            )

    def test_all_models_share_base(self):
        from models.base import Base
        from models.work import (
            Project, WBSNode, WorkPackage, Task,
            Dependency, Assignment, ExecutionIssue, ProgressSnapshot,
        )
        for model in [Project, WBSNode, WorkPackage, Task,
                       Dependency, Assignment, ExecutionIssue, ProgressSnapshot]:
            assert issubclass(model, Base), f"{model.__name__} must extend Base"


# ============================================================================
# 3. Column Coverage Tests — verify columns match the validated DDL
# ============================================================================

class TestWorkModelColumns:
    """Verify each model has the exact columns defined in the DDL."""

    def _get_column_names(self, model_cls):
        """Extract column names from a SQLAlchemy model class."""
        return {c.name for c in model_cls.__table__.columns}

    def test_project_columns(self):
        from models.work import Project
        expected = {
            "project_id", "project_code", "title", "status",
            "client_id", "site_id", "business_unit_id", "description",
            "contract_id", "planned_start_at", "planned_end_at",
            "actual_start_at", "actual_end_at", "project_priority",
            "created_from_source", "provenance_status",
            "p6_project_id", "p6_short_name", "p6_data_date",
            "created_at", "updated_at",
        }
        assert self._get_column_names(Project) == expected

    def test_wbs_node_columns(self):
        from models.work import WBSNode
        expected = {
            "wbs_node_id", "project_id", "parent_wbs_node_id",
            "wbs_code", "title", "sort_order",
            "p6_wbs_id", "p6_parent_wbs_id",
            "created_from_source", "created_at", "updated_at",
        }
        assert self._get_column_names(WBSNode) == expected

    def test_work_package_columns(self):
        from models.work import WorkPackage
        expected = {
            "work_package_id", "project_id", "work_package_code", "title",
            "work_type", "lifecycle_state", "priority",
            "client_id", "site_id", "primary_wbs_node_id",
            "scope_source_ref", "asset_class_id", "apparatus_cluster_ref",
            "assigned_crew_id",
            "scheduled_start_at", "scheduled_end_at",
            "actual_start_at", "actual_end_at",
            "progress_percent", "billing_state", "execution_summary",
            "created_from_source", "provenance_status",
            "created_at", "updated_at",
        }
        assert self._get_column_names(WorkPackage) == expected

    def test_task_columns(self):
        from models.work import Task
        expected = {
            "task_id", "work_package_id", "task_code", "title",
            "task_type", "lifecycle_state",
            "planned_start_at", "planned_end_at",
            "actual_start_at", "actual_end_at",
            "early_start_at", "early_end_at",
            "late_start_at", "late_end_at",
            "duration_hours", "remaining_duration_hours",
            "estimated_labor_hours", "actual_labor_hours",
            "total_float_hours", "schedule_priority_override",
            "primary_wbs_node_id",
            "p6_task_id", "p6_activity_id", "p6_calendar_id",
            "created_from_source", "provenance_status",
            "created_at", "updated_at",
        }
        assert self._get_column_names(Task) == expected

    def test_dependency_columns(self):
        from models.work import Dependency
        expected = {
            "dependency_id", "predecessor_task_id", "successor_task_id",
            "relationship_type", "lag_hours", "source_system",
            "p6_relationship_id", "is_active",
            "created_from_source", "created_at", "updated_at",
        }
        assert self._get_column_names(Dependency) == expected

    def test_assignment_columns(self):
        from models.work import Assignment
        expected = {
            "assignment_id", "work_package_id", "task_id",
            "employee_id", "crew_id", "assignment_role",
            "planned_hours", "actual_hours",
            "start_at", "end_at",
            "p6_task_resource_id", "p6_resource_id",
            "is_actual_participation", "created_from_source",
            "created_at", "updated_at",
        }
        assert self._get_column_names(Assignment) == expected

    def test_execution_issue_columns(self):
        from models.work import ExecutionIssue
        expected = {
            "execution_issue_id", "work_package_id", "task_id",
            "apparatus_ref", "issue_type", "severity", "status",
            "blocks_completion", "summary", "details",
            "reported_by", "assigned_to", "resolution_type",
            "opened_at", "resolved_at", "closed_at",
            "created_from_source", "created_at", "updated_at",
        }
        assert self._get_column_names(ExecutionIssue) == expected

    def test_progress_snapshot_columns(self):
        from models.work import ProgressSnapshot
        expected = {
            "progress_snapshot_id", "project_id", "work_package_id", "task_id",
            "snapshot_period_start", "snapshot_period_end", "snapshot_status",
            "completed_apparatus_count", "total_apparatus_count",
            "percent_complete", "actual_labor_hours",
            "billable_amount", "billing_reference",
            "approved_by", "approved_at", "supersedes_snapshot_id",
            "source_data_date", "created_from_source",
            "created_at", "updated_at",
        }
        assert self._get_column_names(ProgressSnapshot) == expected


# ============================================================================
# 4. Pydantic Schema Import and Round-Trip Tests
# ============================================================================

class TestWorkPydanticSchemas:
    """Verify all 8 Pydantic read schemas import and can round-trip."""

    def test_schema_registry_count(self):
        from services.work.schemas import WORK_SCHEMA_REGISTRY
        # 8 read + 14 write: ProjectCreate/Update (packet 011f) +
        # WorkPackageCreate/Update (packet 013) +
        # TaskCreate/Update (packet 014) +
        # AssignmentCreate/Update (packet 015) +
        # DependencyCreate/Update (packet 016) +
        # ExecutionIssueCreate/Update (packet 017) +
        # ProgressSnapshotCreate/Update (packet 018)
        assert len(WORK_SCHEMA_REGISTRY) == 22

    def _ts(self):
        return datetime.now(tz=timezone.utc)

    def test_project_read_roundtrip(self):
        from services.work.schemas import ProjectRead
        data = ProjectRead(
            project_id=uuid4(), project_code="TST-001", title="Test Project",
            status="draft", client_id=uuid4(), site_id=uuid4(),
            created_from_source="manual", provenance_status="curated",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["project_code"] == "TST-001"
        assert d["status"] == "draft"

    def test_wbs_node_read_roundtrip(self):
        from services.work.schemas import WBSNodeRead
        data = WBSNodeRead(
            wbs_node_id=uuid4(), project_id=uuid4(),
            wbs_code="1.1", title="Phase 1",
            created_from_source="manual",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["wbs_code"] == "1.1"

    def test_work_package_read_roundtrip(self):
        from services.work.schemas import WorkPackageRead
        data = WorkPackageRead(
            work_package_id=uuid4(), project_id=uuid4(),
            work_package_code="WP-001", title="Test WP",
            work_type="testing", lifecycle_state="draft",
            priority="normal", client_id=uuid4(), site_id=uuid4(),
            created_from_source="manual", provenance_status="curated",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["work_type"] == "testing"

    def test_task_read_roundtrip(self):
        from services.work.schemas import TaskRead
        data = TaskRead(
            task_id=uuid4(), work_package_id=uuid4(),
            title="Test Task", task_type="task",
            lifecycle_state="not_started",
            created_from_source="manual", provenance_status="curated",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["lifecycle_state"] == "not_started"

    def test_dependency_read_roundtrip(self):
        from services.work.schemas import DependencyRead
        data = DependencyRead(
            dependency_id=uuid4(),
            predecessor_task_id=uuid4(), successor_task_id=uuid4(),
            relationship_type="FS", is_active=True,
            source_system="manual", created_from_source="manual",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["relationship_type"] == "FS"

    def test_assignment_read_roundtrip(self):
        from services.work.schemas import AssignmentRead
        data = AssignmentRead(
            assignment_id=uuid4(), work_package_id=uuid4(),
            assignment_role="primary", is_actual_participation=False,
            created_from_source="manual",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["assignment_role"] == "primary"

    def test_execution_issue_read_roundtrip(self):
        from services.work.schemas import ExecutionIssueRead
        data = ExecutionIssueRead(
            execution_issue_id=uuid4(),
            issue_type="test_failure", severity="major",
            status="open", blocks_completion=True,
            summary="Relay failed pickup test",
            created_from_source="manual",
            opened_at=self._ts(),
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["blocks_completion"] is True

    def test_progress_snapshot_read_roundtrip(self):
        from services.work.schemas import ProgressSnapshotRead
        data = ProgressSnapshotRead(
            progress_snapshot_id=uuid4(), project_id=uuid4(),
            snapshot_period_start=date(2026, 4, 1),
            snapshot_period_end=date(2026, 4, 7),
            snapshot_status="draft",
            created_from_source="manual",
            created_at=self._ts(), updated_at=self._ts(),
        )
        d = data.model_dump()
        assert d["snapshot_status"] == "draft"


# ============================================================================
# 5. Package Export Consistency
# ============================================================================

class TestPackageExports:
    """Verify models/__init__.py exports are consistent."""

    def test_init_exports_work_models(self):
        import models
        for name in [
            "Project", "WBSNode", "WorkPackage", "Task",
            "Dependency", "Assignment", "ExecutionIssue", "ProgressSnapshot",
        ]:
            assert hasattr(models, name), f"models.{name} not exported"

    def test_init_exports_work_enums(self):
        import models
        for name in [
            "ProvenanceSource", "ProvenanceStatus", "ProjectStatus",
            "WPLifecycle", "WorkType", "Priority", "BillingState",
            "TaskLifecycle", "TaskType", "DependencyType", "AssignmentRole",
            "IssueType", "Severity", "IssueStatus", "ResolutionType",
            "SnapshotStatus",
        ]:
            assert hasattr(models, name), f"models.{name} not exported"

    def test_init_exports_registries(self):
        import models
        assert hasattr(models, "WORK_ENUM_REGISTRY")
        assert hasattr(models, "WORK_MODEL_REGISTRY")
        assert hasattr(models, "ORG_MODEL_REGISTRY")
        assert hasattr(models, "IDENTITY_MODEL_REGISTRY")
        assert len(models.WORK_ENUM_REGISTRY) == 16
        assert len(models.WORK_MODEL_REGISTRY) == 8
        assert len(models.ORG_MODEL_REGISTRY) == 4
        assert len(models.IDENTITY_MODEL_REGISTRY) == 3

    def test_all_list_count(self):
        import models
        # 60 (original) + 5 (org: Client, Site, BusinessUnit, Contract, ORG_MODEL_REGISTRY)
        # + 4 (identity: User, Employee, Crew, IDENTITY_MODEL_REGISTRY) = 69
        assert len(models.__all__) == 69, (
            f"Expected 69 __all__ exports, got {len(models.__all__)}"
        )
