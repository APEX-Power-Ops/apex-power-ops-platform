"""
PM/Work Domain — Org-Joined Read Surface Tests
===============================================
Packet: 2026-04-14-pm-schema-012h

Verifies the org-joined read surface wires the six active org
relationships onto the existing project and work-package read paths,
populating the optional `*_name` / `*_title` fields authored by
packet 011e:

  * Project       → client_name, site_name, business_unit_name, contract_title
  * WorkPackage   → client_name, site_name

The tests exercise the private hydration helpers and the Pydantic
serialization layer directly, mirroring the packet 012f pattern for
identity.  They do not require a live PostgreSQL connection —
stub ORM-shaped objects validate both the populated-relationship
path and the null-FK path.

Identity-joined fields added in packet 012f remain covered by
``test_work_identity_joined_read.py``; this module targets only the
org-backed hydration added in packet 012h.
"""

import os
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.work.queries import (
    _hydrate_project,
    _hydrate_work_package,
)
from services.work.schemas import (
    ProjectRead,
    WorkPackageRead,
)


# ---------------------------------------------------------------------------
# _hydrate_project — populated relationship path
# ---------------------------------------------------------------------------


class TestHydrateProjectPopulated:
    def test_populates_all_four_org_name_fields(self):
        p = SimpleNamespace(
            client_id=uuid4(),
            site_id=uuid4(),
            business_unit_id=uuid4(),
            contract_id=uuid4(),
            client=SimpleNamespace(name="Stack DC Client"),
            site=SimpleNamespace(name="Stack DC — Hillsboro Phase 1"),
            business_unit=SimpleNamespace(name="Western Region"),
            contract=SimpleNamespace(title="Stack DC MSA 2026"),
        )
        result = _hydrate_project(p)
        assert result is p
        assert result.client_name == "Stack DC Client"
        assert result.site_name == "Stack DC — Hillsboro Phase 1"
        assert result.business_unit_name == "Western Region"
        assert result.contract_title == "Stack DC MSA 2026"

    def test_populates_required_fk_fields_with_nullable_fks_null(self):
        # client_id and site_id are NOT NULL in DDL; business_unit_id and
        # contract_id are nullable.  Hydrator must fill the first two and
        # leave the last two as None when their FKs are null.
        p = SimpleNamespace(
            client_id=uuid4(),
            site_id=uuid4(),
            business_unit_id=None,
            contract_id=None,
            client=SimpleNamespace(name="Acme Power"),
            site=SimpleNamespace(name="Plant 3"),
            business_unit=None,
            contract=None,
        )
        result = _hydrate_project(p)
        assert result.client_name == "Acme Power"
        assert result.site_name == "Plant 3"
        assert result.business_unit_name is None
        assert result.contract_title is None


class TestHydrateProjectNullOrMissing:
    def test_returns_none_for_none_input(self):
        assert _hydrate_project(None) is None

    def test_all_names_none_when_all_fks_null(self):
        p = SimpleNamespace(
            client_id=None,
            site_id=None,
            business_unit_id=None,
            contract_id=None,
            client=None,
            site=None,
            business_unit=None,
            contract=None,
        )
        result = _hydrate_project(p)
        assert result.client_name is None
        assert result.site_name is None
        assert result.business_unit_name is None
        assert result.contract_title is None

    def test_names_none_when_fk_set_but_relationship_missing(self):
        # FK populated but the related row was not joined / was deleted.
        p = SimpleNamespace(
            client_id=uuid4(),
            site_id=uuid4(),
            business_unit_id=uuid4(),
            contract_id=uuid4(),
            client=None,
            site=None,
            business_unit=None,
            contract=None,
        )
        result = _hydrate_project(p)
        assert result.client_name is None
        assert result.site_name is None
        assert result.business_unit_name is None
        assert result.contract_title is None

    def test_contract_title_none_when_contract_title_is_null(self):
        # Contract.title is nullable in DDL; `getattr(contract, 'title', None)`
        # must propagate None without raising.
        p = SimpleNamespace(
            client_id=uuid4(),
            site_id=uuid4(),
            business_unit_id=None,
            contract_id=uuid4(),
            client=SimpleNamespace(name="Client X"),
            site=SimpleNamespace(name="Site Y"),
            business_unit=None,
            contract=SimpleNamespace(title=None),
        )
        result = _hydrate_project(p)
        assert result.contract_title is None


# ---------------------------------------------------------------------------
# _hydrate_work_package — org fields (identity fields covered by 012f tests)
# ---------------------------------------------------------------------------


class TestHydrateWorkPackageOrg:
    def test_populates_client_and_site_name_when_present(self):
        wp = SimpleNamespace(
            assigned_crew_id=None,
            assigned_crew=None,
            client_id=uuid4(),
            site_id=uuid4(),
            client=SimpleNamespace(name="Stack DC Client"),
            site=SimpleNamespace(name="Stack DC — Hillsboro"),
        )
        result = _hydrate_work_package(wp)
        assert result.client_name == "Stack DC Client"
        assert result.site_name == "Stack DC — Hillsboro"

    def test_org_names_none_when_fks_null(self):
        # WorkPackage.client_id / site_id are NOT NULL in DDL, but the
        # hydrator should still short-circuit cleanly if something
        # constructs a stub with null FKs (e.g., unit-test seams).
        wp = SimpleNamespace(
            assigned_crew_id=None,
            assigned_crew=None,
            client_id=None,
            site_id=None,
            client=None,
            site=None,
        )
        result = _hydrate_work_package(wp)
        assert result.client_name is None
        assert result.site_name is None

    def test_org_names_none_when_relationships_missing(self):
        wp = SimpleNamespace(
            assigned_crew_id=None,
            assigned_crew=None,
            client_id=uuid4(),
            site_id=uuid4(),
            client=None,
            site=None,
        )
        result = _hydrate_work_package(wp)
        assert result.client_name is None
        assert result.site_name is None

    def test_identity_and_org_hydration_coexist(self):
        wp = SimpleNamespace(
            assigned_crew_id=uuid4(),
            assigned_crew=SimpleNamespace(name="Crew Alpha"),
            client_id=uuid4(),
            site_id=uuid4(),
            client=SimpleNamespace(name="Client A"),
            site=SimpleNamespace(name="Site A"),
        )
        result = _hydrate_work_package(wp)
        assert result.assigned_crew_name == "Crew Alpha"
        assert result.client_name == "Client A"
        assert result.site_name == "Site A"


# ---------------------------------------------------------------------------
# Pydantic serialization — hydrated instances flow through org `*_name`
# ---------------------------------------------------------------------------


def _base_project_payload():
    return {
        "project_id": uuid4(),
        "project_code": "PRJ-012H-001",
        "title": "Org-Joined Read Surface Demo",
        "status": "draft",
        "client_id": uuid4(),
        "site_id": uuid4(),
        "business_unit_id": uuid4(),
        "description": None,
        "contract_id": uuid4(),
        "planned_start_at": None,
        "planned_end_at": None,
        "actual_start_at": None,
        "actual_end_at": None,
        "project_priority": None,
        "created_from_source": "manual",
        "provenance_status": "curated",
        "p6_project_id": None,
        "p6_short_name": None,
        "p6_data_date": None,
        "created_at": "2026-04-14T00:00:00+00:00",
        "updated_at": "2026-04-14T00:00:00+00:00",
    }


def _base_work_package_payload():
    return {
        "work_package_id": uuid4(),
        "project_id": uuid4(),
        "work_package_code": "WP-012H-001",
        "title": "Org-Joined WP Demo",
        "work_type": "testing",
        "lifecycle_state": "planned",
        "priority": "normal",
        "client_id": uuid4(),
        "site_id": uuid4(),
        "primary_wbs_node_id": None,
        "scope_source_ref": None,
        "asset_class_id": None,
        "apparatus_cluster_ref": None,
        "assigned_crew_id": None,
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


class TestProjectReadSerialization:
    def test_project_read_picks_up_all_four_org_names(self):
        payload = _base_project_payload()
        p_stub = SimpleNamespace(**payload)
        p_stub.client = SimpleNamespace(name="Big Client")
        p_stub.site = SimpleNamespace(name="Big Site")
        p_stub.business_unit = SimpleNamespace(name="Western BU")
        p_stub.contract = SimpleNamespace(title="MSA-2026")
        _hydrate_project(p_stub)
        read = ProjectRead.model_validate(p_stub)
        assert read.client_name == "Big Client"
        assert read.site_name == "Big Site"
        assert read.business_unit_name == "Western BU"
        assert read.contract_title == "MSA-2026"

    def test_project_read_optional_org_names_none_when_fks_null(self):
        payload = _base_project_payload()
        payload["business_unit_id"] = None
        payload["contract_id"] = None
        p_stub = SimpleNamespace(**payload)
        p_stub.client = SimpleNamespace(name="Only Client")
        p_stub.site = SimpleNamespace(name="Only Site")
        p_stub.business_unit = None
        p_stub.contract = None
        _hydrate_project(p_stub)
        read = ProjectRead.model_validate(p_stub)
        assert read.client_name == "Only Client"
        assert read.site_name == "Only Site"
        assert read.business_unit_name is None
        assert read.contract_title is None


class TestWorkPackageReadSerialization:
    def test_work_package_read_picks_up_org_names(self):
        payload = _base_work_package_payload()
        wp_stub = SimpleNamespace(**payload)
        wp_stub.assigned_crew = None
        wp_stub.client = SimpleNamespace(name="WP Client")
        wp_stub.site = SimpleNamespace(name="WP Site")
        _hydrate_work_package(wp_stub)
        read = WorkPackageRead.model_validate(wp_stub)
        assert read.client_name == "WP Client"
        assert read.site_name == "WP Site"

    def test_work_package_read_picks_up_org_and_crew_names(self):
        payload = _base_work_package_payload()
        payload["assigned_crew_id"] = uuid4()
        wp_stub = SimpleNamespace(**payload)
        wp_stub.assigned_crew = SimpleNamespace(name="Crew Delta")
        wp_stub.client = SimpleNamespace(name="WP Client")
        wp_stub.site = SimpleNamespace(name="WP Site")
        _hydrate_work_package(wp_stub)
        read = WorkPackageRead.model_validate(wp_stub)
        assert read.assigned_crew_name == "Crew Delta"
        assert read.client_name == "WP Client"
        assert read.site_name == "WP Site"


# ---------------------------------------------------------------------------
# Boundary confirmation — no new endpoints / schemas / write paths
# ---------------------------------------------------------------------------


class TestBoundaryConfirmation:
    def test_work_schema_registry_size_unchanged(self):
        from services.work.schemas import WORK_SCHEMA_REGISTRY
        # 8 read + 14 write (packet 011f ProjectCreate/Update + packet 013
        # WorkPackageCreate/Update + packet 014 TaskCreate/Update +
        # packet 015 AssignmentCreate/Update + packet 016
        # DependencyCreate/Update + packet 017 ExecutionIssueCreate/Update +
        # packet 018 ProgressSnapshotCreate/Update)
        assert len(WORK_SCHEMA_REGISTRY) == 22

    def test_project_read_retains_four_org_name_fields(self):
        fields = ProjectRead.model_fields
        assert "client_name" in fields
        assert "site_name" in fields
        assert "business_unit_name" in fields
        assert "contract_title" in fields

    def test_work_package_read_retains_two_org_name_fields(self):
        fields = WorkPackageRead.model_fields
        assert "client_name" in fields
        assert "site_name" in fields

    def test_no_new_work_endpoints_introduced(self):
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        from config import get_db
        from main import app

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
