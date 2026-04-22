"""
PM/Work Domain — Shared PATCH Target-Exists Regression Harness
===============================================================
Packet: 2026-04-16-pm-schema-019

A single parametrized test module that standardises the PATCH contract
across all seven PM update endpoints.  Each entity's dedicated write
test already covers rich field-level behaviour; this harness exists to
lock in the three standardised outcomes that MUST hold uniformly across
the surface:

  * ``PATCH /{entity}/{nonexistent_id}`` with any valid body → 404
  * ``PATCH /{entity}/{existing_id}`` with an empty body → 200 (no-op)
  * ``PATCH /{entity}/{existing_id}`` with an invalid FK → 422 (with the
    offending field keyed in the merged ``errors`` payload)

These three assertions form the minimum contract that the seven PATCH
endpoints must all honour; drift from this shape (e.g. a handler
accidentally returning 500 or 400 on an unknown id) would break the
front-end's error surface expectations.

The harness uses per-entity mock databases — no live PostgreSQL — and
the FastAPI dependency override seam already used by every entity-level
unit test.  The entity-level write tests (``test_work_project_write``,
``test_work_work_package_write``, … ``test_work_progress_snapshot_write``)
remain the source of truth for entity-specific validation; this module
asserts only the cross-cutting contract.
"""

from __future__ import annotations

import sys
import os
from unittest.mock import MagicMock
from uuid import UUID

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from config import get_db  # noqa: E402
from main import app  # noqa: E402
from services.work.idempotency import idempotency_cache  # noqa: E402


# ---------------------------------------------------------------------------
# Sentinel UUIDs
# ---------------------------------------------------------------------------

VALID_CLIENT_ID      = UUID("11111111-0000-0000-0000-000000000019")
VALID_SITE_ID        = UUID("22222222-0000-0000-0000-000000000019")
VALID_PROJECT_ID     = UUID("99999999-1111-0000-0000-000000000019")
VALID_WP_ID          = UUID("99999999-2222-0000-0000-000000000019")
VALID_TASK_ID        = UUID("99999999-3333-0000-0000-000000000019")
VALID_PRED_TASK_ID   = UUID("99999999-3333-0000-0000-000000000020")
VALID_SUCC_TASK_ID   = UUID("99999999-3333-0000-0000-000000000021")
VALID_EMPLOYEE_ID    = UUID("99999999-5555-0000-0000-000000000019")
VALID_APPROVER_ID    = UUID("99999999-6666-0000-0000-000000000019")

EXISTING_PROJECT_ID     = UUID("aaaaaaaa-0000-0000-0000-000000000019")
EXISTING_WP_ID          = UUID("aaaaaaaa-0000-0000-0000-000000000119")
EXISTING_TASK_ID        = UUID("aaaaaaaa-0000-0000-0000-000000000219")
EXISTING_DEP_ID         = UUID("aaaaaaaa-0000-0000-0000-000000000319")
EXISTING_ASSIGNMENT_ID  = UUID("aaaaaaaa-0000-0000-0000-000000000419")
EXISTING_ISSUE_ID       = UUID("aaaaaaaa-0000-0000-0000-000000000519")
EXISTING_SNAPSHOT_ID    = UUID("aaaaaaaa-0000-0000-0000-000000000619")

NONEXISTENT_ID = UUID("00000000-0000-0000-0000-000000000099")

INVALID_CLIENT_ID = UUID("eeeeeeee-1111-0000-0000-000000000099")
INVALID_WP_ID     = UUID("eeeeeeee-2222-0000-0000-000000000099")
INVALID_TASK_ID   = UUID("eeeeeeee-3333-0000-0000-000000000099")
INVALID_PROJECT_ID = UUID("eeeeeeee-4444-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Shared mock DB
# ---------------------------------------------------------------------------

def _make_mock(**overrides):
    mock = MagicMock()
    for k, v in overrides.items():
        setattr(mock, k, v)
    return mock


def _mock_project():
    from datetime import datetime, timezone
    return _make_mock(
        project_id=EXISTING_PROJECT_ID,
        project_code="PATCH-HARNESS-PROJ",
        title="Patch Harness Project",
        status="draft",
        client_id=VALID_CLIENT_ID,
        site_id=VALID_SITE_ID,
        business_unit_id=None,
        contract_id=None,
        description=None,
        client_name=None,
        site_name=None,
        business_unit_name=None,
        contract_title=None,
        planned_start_at=None,
        planned_end_at=None,
        actual_start_at=None,
        actual_end_at=None,
        project_priority=None,
        created_from_source="manual",
        provenance_status="curated",
        p6_project_id=None,
        p6_short_name=None,
        p6_data_date=None,
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_wp():
    from datetime import datetime, timezone
    return _make_mock(
        work_package_id=EXISTING_WP_ID,
        project_id=VALID_PROJECT_ID,
        work_package_code="PATCH-HARNESS-WP",
        title="Patch Harness WP",
        work_type="testing",
        lifecycle_state="planned",
        priority="normal",
        primary_wbs_node_id=None,
        client_id=VALID_CLIENT_ID,
        site_id=VALID_SITE_ID,
        client_name=None,
        site_name=None,
        scope_source_ref=None,
        asset_class_id=None,
        apparatus_cluster_ref=None,
        assigned_crew_id=None,
        assigned_crew_name=None,
        scheduled_start_at=None,
        scheduled_end_at=None,
        actual_start_at=None,
        actual_end_at=None,
        progress_percent=None,
        billing_state=None,
        execution_summary=None,
        created_from_source="manual",
        provenance_status="curated",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_task():
    from datetime import datetime, timezone
    return _make_mock(
        task_id=EXISTING_TASK_ID,
        work_package_id=VALID_WP_ID,
        task_code="PATCH-HARNESS-TASK",
        title="Patch Harness Task",
        task_type="task",
        lifecycle_state="not_started",
        planned_start_at=None,
        planned_end_at=None,
        actual_start_at=None,
        actual_end_at=None,
        early_start_at=None,
        early_end_at=None,
        late_start_at=None,
        late_end_at=None,
        duration_hours=None,
        remaining_duration_hours=None,
        estimated_labor_hours=None,
        actual_labor_hours=None,
        total_float_hours=None,
        schedule_priority_override=None,
        primary_wbs_node_id=None,
        p6_task_id=None,
        p6_activity_id=None,
        p6_calendar_id=None,
        created_from_source="manual",
        provenance_status="curated",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_dependency():
    from datetime import datetime, timezone
    return _make_mock(
        dependency_id=EXISTING_DEP_ID,
        predecessor_task_id=VALID_PRED_TASK_ID,
        successor_task_id=VALID_SUCC_TASK_ID,
        relationship_type="FS",
        lag_hours=None,
        source_system="manual",
        p6_relationship_id=None,
        is_active=True,
        created_from_source="manual",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_assignment():
    from datetime import datetime, timezone
    return _make_mock(
        assignment_id=EXISTING_ASSIGNMENT_ID,
        work_package_id=VALID_WP_ID,
        task_id=None,
        employee_id=VALID_EMPLOYEE_ID,
        crew_id=None,
        employee_name=None,
        crew_name=None,
        assignment_role="lead",
        planned_hours=None,
        actual_hours=None,
        start_at=None,
        end_at=None,
        p6_task_resource_id=None,
        p6_resource_id=None,
        is_actual_participation=False,
        created_from_source="manual",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_issue():
    from datetime import datetime, timezone
    return _make_mock(
        execution_issue_id=EXISTING_ISSUE_ID,
        work_package_id=VALID_WP_ID,
        task_id=None,
        apparatus_ref=None,
        issue_type="other",
        severity="minor",
        status="open",
        blocks_completion=False,
        summary="Patch Harness Issue",
        details=None,
        reported_by=None,
        assigned_to=None,
        reported_by_name=None,
        assigned_to_name=None,
        resolution_type=None,
        opened_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        resolved_at=None,
        closed_at=None,
        created_from_source="manual",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _mock_snapshot():
    from datetime import date, datetime, timezone
    return _make_mock(
        progress_snapshot_id=EXISTING_SNAPSHOT_ID,
        project_id=VALID_PROJECT_ID,
        work_package_id=None,
        task_id=None,
        snapshot_period_start=date(2026, 4, 1),
        snapshot_period_end=date(2026, 4, 14),
        snapshot_status="draft",
        completed_apparatus_count=None,
        total_apparatus_count=None,
        percent_complete=None,
        actual_labor_hours=None,
        billable_amount=None,
        billing_reference=None,
        approved_by=None,
        approved_by_name=None,
        approved_at=None,
        supersedes_snapshot_id=None,
        source_data_date=None,
        created_from_source="manual",
        created_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        updated_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
    )


def _harness_db():
    """A shared mock DB that recognises every entity the PATCH harness
    touches plus the FK lookups needed for the 422 lane."""
    from models.org import Client, Site, BusinessUnit, Contract
    from models.work import (
        Project, WorkPackage, Task, Dependency,
        Assignment, ExecutionIssue, ProgressSnapshot,
    )
    from models.identity import User

    mock_db = MagicMock()

    def mock_get(model_class, pk):
        if model_class is Client:
            if pk == VALID_CLIENT_ID:
                return _make_mock(client_id=pk, name="Patch Harness Client")
            return None
        if model_class is Site:
            if pk == VALID_SITE_ID:
                return _make_mock(site_id=pk, name="Patch Harness Site")
            return None
        if model_class is BusinessUnit or model_class is Contract:
            return None
        if model_class is Project:
            if pk == EXISTING_PROJECT_ID or pk == VALID_PROJECT_ID:
                return _mock_project()
            return None
        if model_class is WorkPackage:
            if pk == EXISTING_WP_ID or pk == VALID_WP_ID:
                return _mock_wp()
            return None
        if model_class is Task:
            if pk in (
                EXISTING_TASK_ID, VALID_TASK_ID,
                VALID_PRED_TASK_ID, VALID_SUCC_TASK_ID,
            ):
                return _mock_task()
            return None
        if model_class is Dependency:
            if pk == EXISTING_DEP_ID:
                return _mock_dependency()
            return None
        if model_class is Assignment:
            if pk == EXISTING_ASSIGNMENT_ID:
                return _mock_assignment()
            return None
        if model_class is ExecutionIssue:
            if pk == EXISTING_ISSUE_ID:
                return _mock_issue()
            return None
        if model_class is ProgressSnapshot:
            if pk == EXISTING_SNAPSHOT_ID:
                return _mock_snapshot()
            return None
        if model_class is User:
            if pk == VALID_EMPLOYEE_ID or pk == VALID_APPROVER_ID:
                return _make_mock(user_id=pk, display_name="Patch Harness User")
            return None
        return None

    mock_db.get = mock_get
    mock_db.add = lambda _: None
    mock_db.commit = lambda: None
    mock_db.refresh = lambda _: None

    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.one_or_none.return_value = None
    mock_db.query.return_value = mock_query

    return mock_db


@pytest.fixture
def harness_client():
    mock_db = _harness_db()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    idempotency_cache.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    idempotency_cache.clear()


# ---------------------------------------------------------------------------
# Per-entity PATCH contract descriptors
# ---------------------------------------------------------------------------
#
# Each tuple describes one PATCH endpoint's standardised contract inputs:
#   (entity_path, existing_id, invalid_fk_patch, invalid_fk_field)
#
# ``invalid_fk_patch`` is a body that is valid shape-wise but references
# an unknown FK so the mutation service rejects with 422.  ``invalid_fk_field``
# is the name expected to appear under ``errors`` in the 422 payload.

PATCH_CASES = [
    (
        "/api/v1/work/projects",
        EXISTING_PROJECT_ID,
        {"client_id": str(INVALID_CLIENT_ID)},
        "client_id",
    ),
    (
        "/api/v1/work/work-packages",
        EXISTING_WP_ID,
        {"project_id": str(INVALID_PROJECT_ID)},
        "project_id",
    ),
    (
        "/api/v1/work/tasks",
        EXISTING_TASK_ID,
        {"work_package_id": str(INVALID_WP_ID)},
        "work_package_id",
    ),
    (
        "/api/v1/work/dependencies",
        EXISTING_DEP_ID,
        {"predecessor_task_id": str(INVALID_TASK_ID)},
        "predecessor_task_id",
    ),
    (
        "/api/v1/work/assignments",
        EXISTING_ASSIGNMENT_ID,
        {"work_package_id": str(INVALID_WP_ID)},
        "work_package_id",
    ),
    (
        "/api/v1/work/execution-issues",
        EXISTING_ISSUE_ID,
        {"work_package_id": str(INVALID_WP_ID)},
        "work_package_id",
    ),
    (
        "/api/v1/work/progress-snapshots",
        EXISTING_SNAPSHOT_ID,
        {"project_id": str(INVALID_PROJECT_ID)},
        "project_id",
    ),
]


# ---------------------------------------------------------------------------
# Standardised 200 / 404 / 422 lane
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entity_path,existing_id,_invalid_patch,_invalid_field",
    PATCH_CASES,
    ids=[c[0] for c in PATCH_CASES],
)
def test_patch_empty_body_returns_200(
    harness_client, entity_path, existing_id, _invalid_patch, _invalid_field,
):
    resp = harness_client.patch(f"{entity_path}/{existing_id}", json={})
    assert resp.status_code == 200, (
        f"{entity_path}: expected 200 on empty-body PATCH, got "
        f"{resp.status_code} — body: {resp.text[:200]}"
    )


@pytest.mark.parametrize(
    "entity_path,_existing_id,_invalid_patch,_invalid_field",
    PATCH_CASES,
    ids=[c[0] for c in PATCH_CASES],
)
def test_patch_nonexistent_id_returns_404(
    harness_client, entity_path, _existing_id, _invalid_patch, _invalid_field,
):
    resp = harness_client.patch(
        f"{entity_path}/{NONEXISTENT_ID}", json={},
    )
    assert resp.status_code == 404, (
        f"{entity_path}: expected 404 on nonexistent id, got "
        f"{resp.status_code} — body: {resp.text[:200]}"
    )


@pytest.mark.parametrize(
    "entity_path,existing_id,invalid_patch,invalid_field",
    PATCH_CASES,
    ids=[c[0] for c in PATCH_CASES],
)
def test_patch_invalid_fk_returns_422_with_merged_error(
    harness_client, entity_path, existing_id, invalid_patch, invalid_field,
):
    resp = harness_client.patch(
        f"{entity_path}/{existing_id}", json=invalid_patch,
    )
    assert resp.status_code == 422, (
        f"{entity_path}: expected 422 on invalid FK, got "
        f"{resp.status_code} — body: {resp.text[:200]}"
    )
    body = resp.json()
    assert "errors" in body, (
        f"{entity_path}: 422 payload missing ``errors`` key — {body}"
    )
    assert invalid_field in body["errors"], (
        f"{entity_path}: expected field {invalid_field!r} in errors, got "
        f"{list(body['errors'].keys())}"
    )
