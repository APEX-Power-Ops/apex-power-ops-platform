"""
PM/Work Domain — Identity-Joined Read Surface Tests
====================================================
Packet: 2026-04-14-pm-schema-012f

Verifies the identity-joined read surface wires the six active identity
relationships onto the existing work-package, assignment,
execution-issue, and progress-snapshot read paths, populating the
optional `*_name` fields authored by packet 012e.

These tests exercise the private hydration helpers and the Pydantic
serialization layer directly.  They do not require a live PostgreSQL
connection — stub ORM-shaped objects validate both the populated
identity relationship path and the null-FK path.
"""

import os
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.queries import (
    _employee_display_name,
    _hydrate_assignment,
    _hydrate_execution_issue,
    _hydrate_progress_snapshot,
    _hydrate_work_package,
)
from services.work.schemas import (
    AssignmentRead,
    ExecutionIssueRead,
    ProgressSnapshotRead,
    WorkPackageRead,
)


# ---------------------------------------------------------------------------
# Identity-name hydration helpers
# ---------------------------------------------------------------------------

class TestEmployeeDisplayName:
    def test_returns_none_for_missing_employee(self):
        assert _employee_display_name(None) is None

    def test_joins_first_and_last(self):
        emp = SimpleNamespace(first_name="Ada", last_name="Lovelace")
        assert _employee_display_name(emp) == "Ada Lovelace"

    def test_trims_extra_whitespace(self):
        emp = SimpleNamespace(first_name="  Ada ", last_name=" Lovelace  ")
        assert _employee_display_name(emp) == "Ada Lovelace"

    def test_returns_none_when_both_blank(self):
        emp = SimpleNamespace(first_name="", last_name="")
        assert _employee_display_name(emp) is None


class TestHydrateWorkPackage:
    def test_populates_assigned_crew_name_when_present(self):
        crew = SimpleNamespace(name="Crew Alpha")
        wp = SimpleNamespace(
            assigned_crew_id=uuid4(),
            assigned_crew=crew,
        )
        result = _hydrate_work_package(wp)
        assert result.assigned_crew_name == "Crew Alpha"

    def test_name_is_none_when_fk_is_null(self):
        wp = SimpleNamespace(
            assigned_crew_id=None,
            assigned_crew=None,
        )
        result = _hydrate_work_package(wp)
        assert result.assigned_crew_name is None

    def test_name_is_none_when_relationship_missing(self):
        # FK populated but related row not loaded / deleted
        wp = SimpleNamespace(
            assigned_crew_id=uuid4(),
            assigned_crew=None,
        )
        result = _hydrate_work_package(wp)
        assert result.assigned_crew_name is None

    def test_none_row_returns_none(self):
        assert _hydrate_work_package(None) is None


class TestHydrateAssignment:
    def test_populates_both_names_when_present(self):
        emp = SimpleNamespace(first_name="Grace", last_name="Hopper")
        crew = SimpleNamespace(name="Crew Beta")
        a = SimpleNamespace(
            employee_id=uuid4(),
            employee=emp,
            crew_id=uuid4(),
            crew=crew,
        )
        result = _hydrate_assignment(a)
        assert result.employee_name == "Grace Hopper"
        assert result.crew_name == "Crew Beta"

    def test_both_names_none_when_both_fks_null(self):
        a = SimpleNamespace(
            employee_id=None,
            employee=None,
            crew_id=None,
            crew=None,
        )
        result = _hydrate_assignment(a)
        assert result.employee_name is None
        assert result.crew_name is None

    def test_mixed_fks_hydrate_independently(self):
        crew = SimpleNamespace(name="Crew Gamma")
        a = SimpleNamespace(
            employee_id=None,
            employee=None,
            crew_id=uuid4(),
            crew=crew,
        )
        result = _hydrate_assignment(a)
        assert result.employee_name is None
        assert result.crew_name == "Crew Gamma"


class TestHydrateExecutionIssue:
    def test_populates_both_names_when_present(self):
        reporter = SimpleNamespace(display_name="Alice Reporter")
        assignee = SimpleNamespace(display_name="Bob Assignee")
        ei = SimpleNamespace(
            reported_by=uuid4(),
            reporter=reporter,
            assigned_to=uuid4(),
            assignee=assignee,
        )
        result = _hydrate_execution_issue(ei)
        assert result.reported_by_name == "Alice Reporter"
        assert result.assigned_to_name == "Bob Assignee"

    def test_both_names_none_when_both_fks_null(self):
        ei = SimpleNamespace(
            reported_by=None,
            reporter=None,
            assigned_to=None,
            assignee=None,
        )
        result = _hydrate_execution_issue(ei)
        assert result.reported_by_name is None
        assert result.assigned_to_name is None

    def test_reporter_only(self):
        reporter = SimpleNamespace(display_name="Alice Reporter")
        ei = SimpleNamespace(
            reported_by=uuid4(),
            reporter=reporter,
            assigned_to=None,
            assignee=None,
        )
        result = _hydrate_execution_issue(ei)
        assert result.reported_by_name == "Alice Reporter"
        assert result.assigned_to_name is None


class TestHydrateProgressSnapshot:
    def test_populates_approved_by_name_when_present(self):
        approver = SimpleNamespace(display_name="Carol Approver")
        ps = SimpleNamespace(
            approved_by=uuid4(),
            approver=approver,
        )
        result = _hydrate_progress_snapshot(ps)
        assert result.approved_by_name == "Carol Approver"

    def test_name_is_none_when_fk_is_null(self):
        ps = SimpleNamespace(
            approved_by=None,
            approver=None,
        )
        result = _hydrate_progress_snapshot(ps)
        assert result.approved_by_name is None


# ---------------------------------------------------------------------------
# Pydantic serialization — hydrated instances flow through `*_name`
# ---------------------------------------------------------------------------

def _base_work_package_payload():
    return {
        "work_package_id": uuid4(),
        "project_id": uuid4(),
        "work_package_code": "WP-001",
        "title": "Demo work package",
        "work_type": "testing",
        "lifecycle_state": "planned",
        "priority": "normal",
        "client_id": uuid4(),
        "site_id": uuid4(),
        "primary_wbs_node_id": None,
        "scope_source_ref": None,
        "asset_class_id": None,
        "apparatus_cluster_ref": None,
        "assigned_crew_id": uuid4(),
        "scheduled_start_at": None,
        "scheduled_end_at": None,
        "actual_start_at": None,
        "actual_end_at": None,
        "progress_percent": None,
        "billing_state": None,
        "execution_summary": None,
        "created_from_source": "manual",
        "provenance_status": "curated",
        "created_at": "2026-04-14T00:00:00+00:00",
        "updated_at": "2026-04-14T00:00:00+00:00",
    }


class TestSerialization:
    def test_work_package_read_picks_up_hydrated_crew_name(self):
        payload = _base_work_package_payload()
        wp_stub = SimpleNamespace(**payload)
        wp_stub.assigned_crew = SimpleNamespace(name="Crew Delta")
        _hydrate_work_package(wp_stub)
        read = WorkPackageRead.model_validate(wp_stub)
        assert read.assigned_crew_name == "Crew Delta"

    def test_work_package_read_name_none_when_fk_null(self):
        payload = _base_work_package_payload()
        payload["assigned_crew_id"] = None
        wp_stub = SimpleNamespace(**payload)
        wp_stub.assigned_crew = None
        _hydrate_work_package(wp_stub)
        read = WorkPackageRead.model_validate(wp_stub)
        assert read.assigned_crew_name is None

    def test_assignment_read_picks_up_hydrated_names(self):
        a_stub = SimpleNamespace(
            assignment_id=uuid4(),
            work_package_id=uuid4(),
            task_id=None,
            employee_id=uuid4(),
            crew_id=uuid4(),
            assignment_role="primary",
            planned_hours=None,
            actual_hours=None,
            start_at=None,
            end_at=None,
            p6_task_resource_id=None,
            p6_resource_id=None,
            is_actual_participation=False,
            created_from_source="manual",
            created_at="2026-04-14T00:00:00+00:00",
            updated_at="2026-04-14T00:00:00+00:00",
            employee=SimpleNamespace(first_name="Grace", last_name="Hopper"),
            crew=SimpleNamespace(name="Crew Beta"),
        )
        _hydrate_assignment(a_stub)
        read = AssignmentRead.model_validate(a_stub)
        assert read.employee_name == "Grace Hopper"
        assert read.crew_name == "Crew Beta"

    def test_assignment_read_names_none_when_fks_null(self):
        a_stub = SimpleNamespace(
            assignment_id=uuid4(),
            work_package_id=uuid4(),
            task_id=None,
            employee_id=None,
            crew_id=None,
            assignment_role="primary",
            planned_hours=None,
            actual_hours=None,
            start_at=None,
            end_at=None,
            p6_task_resource_id=None,
            p6_resource_id=None,
            is_actual_participation=False,
            created_from_source="manual",
            created_at="2026-04-14T00:00:00+00:00",
            updated_at="2026-04-14T00:00:00+00:00",
            employee=None,
            crew=None,
        )
        _hydrate_assignment(a_stub)
        read = AssignmentRead.model_validate(a_stub)
        assert read.employee_name is None
        assert read.crew_name is None

    def test_execution_issue_read_picks_up_hydrated_names(self):
        ei_stub = SimpleNamespace(
            execution_issue_id=uuid4(),
            work_package_id=uuid4(),
            task_id=None,
            apparatus_ref=None,
            issue_type="safety_hold",
            severity="major",
            status="open",
            blocks_completion=False,
            summary="Safety stand-down",
            details=None,
            reported_by=uuid4(),
            assigned_to=uuid4(),
            resolution_type=None,
            opened_at="2026-04-14T00:00:00+00:00",
            resolved_at=None,
            closed_at=None,
            created_from_source="manual",
            created_at="2026-04-14T00:00:00+00:00",
            updated_at="2026-04-14T00:00:00+00:00",
            reporter=SimpleNamespace(display_name="Alice Reporter"),
            assignee=SimpleNamespace(display_name="Bob Assignee"),
        )
        _hydrate_execution_issue(ei_stub)
        read = ExecutionIssueRead.model_validate(ei_stub)
        assert read.reported_by_name == "Alice Reporter"
        assert read.assigned_to_name == "Bob Assignee"

    def test_progress_snapshot_read_picks_up_hydrated_name(self):
        ps_stub = SimpleNamespace(
            progress_snapshot_id=uuid4(),
            project_id=uuid4(),
            work_package_id=None,
            task_id=None,
            snapshot_period_start="2026-04-01",
            snapshot_period_end="2026-04-14",
            snapshot_status="approved",
            completed_apparatus_count=None,
            total_apparatus_count=None,
            percent_complete=None,
            actual_labor_hours=None,
            billable_amount=None,
            billing_reference=None,
            approved_by=uuid4(),
            approved_at="2026-04-14T00:00:00+00:00",
            supersedes_snapshot_id=None,
            source_data_date=None,
            created_from_source="manual",
            created_at="2026-04-14T00:00:00+00:00",
            updated_at="2026-04-14T00:00:00+00:00",
            approver=SimpleNamespace(display_name="Carol Approver"),
        )
        _hydrate_progress_snapshot(ps_stub)
        read = ProgressSnapshotRead.model_validate(ps_stub)
        assert read.approved_by_name == "Carol Approver"


# ---------------------------------------------------------------------------
# Boundary confirmation — no new endpoints, schemas, or write-surface
# ---------------------------------------------------------------------------

class TestBoundaryConfirmation:
    def test_work_schema_registry_size_unchanged(self):
        from services.work.schemas import WORK_SCHEMA_REGISTRY
        # Packet 013 added WorkPackageCreate/Update → 12
        # Packet 014 added TaskCreate/Update → 14
        # Packet 015 added AssignmentCreate/Update → 16
        # Packet 016 added DependencyCreate/Update → 18
        # Packet 017 added ExecutionIssueCreate/Update → 20
        # Packet 018 added ProgressSnapshotCreate/Update → 22 (8 read + 14 write)
        assert len(WORK_SCHEMA_REGISTRY) == 22

    def test_no_new_endpoints_beyond_existing_surface(self):
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        from config import get_db
        from main import app

        # Empty mock so route listing is deterministic
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            client = TestClient(app)
            resp = client.get("/openapi.json")
            assert resp.status_code == 200
            paths = resp.json()["paths"]
            work_paths = sorted(p for p in paths if p.startswith("/api/v1/work"))
            # 010b read surface (11 paths) + packet 015 adds
            # PATCH /assignments/{assignment_id} (→ 12) + packet 016 adds
            # PATCH /dependencies/{dependency_id} (→ 13) + packet 017 adds
            # PATCH /execution-issues/{execution_issue_id} (→ 14) +
            # packet 018 adds PATCH /progress-snapshots/{progress_snapshot_id}
            # only — the POST /progress-snapshots handler reuses the path
            # already present from the 010b GET, so the overall path count
            # increments by exactly one (→ 15).
            assert len(work_paths) == 15, (
                f"Expected exactly 15 /api/v1/work paths after packet 018, "
                f"got {len(work_paths)}: {work_paths}"
            )
        finally:
            app.dependency_overrides.clear()
