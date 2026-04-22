"""
PM/Work Domain — Assignment Write Surface Integration Smoke
============================================================
Packet: 2026-04-15-pm-schema-015i

Locks in the real-PostgreSQL runtime behavior of the assignment POST
and PATCH surface wired by packet 015.  Exercises the existing write
handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST /api/v1/work/assignments              (packet 015)
       → PATCH /api/v1/work/assignments/{id}        (packet 015)
          → routes.py handler
             → services.work.mutations
                (_validate_assignment_references: work_package_id +
                 task_id intra-work FKs, employee_id + crew_id
                 identity FKs)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with valid work_package_id only returns 201 and a
    materialized AssignmentRead whose id is the inserted row.
  * POST with valid task_id only returns 201 (alternative parent
    shape per ck_assignments_at_least_one_parent).
  * POST with both parent + employee + crew persists every reference.
  * POST with neither work_package_id nor task_id returns 422 from the
    Pydantic @model_validator (mirrors DDL
    ck_assignments_at_least_one_parent).
  * POST with an unknown work_package_id returns 422 with a merged-
    field error dict containing work_package_id.
  * POST with an unknown task_id returns 422 with task_id in errors.
  * POST with an unknown employee_id returns 422 with employee_id in
    errors.
  * POST with an unknown crew_id returns 422 with crew_id in errors.
  * POST with all four FKs bad returns 422 with all four fields in
    the merged error dict (merged-error behavior inherited from packet
    015's _validate_assignment_references helper).
  * PATCH with valid fields returns 200 and the updated row.
  * PATCH role swap returns 200.
  * PATCH employee swap returns 200.
  * PATCH with an unknown employee_id returns 422.
  * PATCH against a random non-existent assignment_id returns 404.
  * PATCH with empty body returns 200 (idempotent no-op).
  * Non-assignment read-only PM-write endpoints (dependencies,
    execution issues, progress snapshots) remain 405 on POST/PATCH
    (sanity boundary).

Design constraints (packet 015i hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 015's assignment-only
    scope — seed supporting rows (client, site, project, work_package,
    task, crew, employee) are inserted directly via SQLAlchemy
    ``text()`` statements, not through the write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or
    `DATABASE_URL`) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g, 012i,
    013i, and 014i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK15I-`` and sentinel
    UUID prefix ``015b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``015b`` is used in its place, matching the convention
    established by packets 012i / 013i / 014i).
  - Teardown deletes only the fixture rows (including any assignment
    rows created by the POST calls), leaving existing staging data
    untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_assignment_write_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packets 012g, 012i, 013i, 014i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Assignment write surface depends on PostgreSQL ENUMs; skip sqlite.
        return None
    return url


def _db_is_reachable(url: str, timeout: float = 2.0) -> bool:
    """TCP-level reachability probe. Avoids authentication noise."""
    try:
        parsed = urlparse(url.replace("postgresql+psycopg2://", "postgresql://"))
        host = parsed.hostname
        port = parsed.port or 5432
        if not host:
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
        return True
    except OSError:
        return False


_DB_URL = _resolve_integration_db_url()

pytestmark = pytest.mark.skipif(
    _DB_URL is None,
    reason=(
        "Integration smoke skipped: set APEX_INTEGRATION_DATABASE_URL to a "
        "PostgreSQL URL hosting the work+org+identity schemas "
        "(e.g. apex_pm_stage)."
    ),
)

if _DB_URL is not None and not _db_is_reachable(_DB_URL):
    pytestmark = pytest.mark.skip(
        reason=(
            f"Integration smoke skipped: PostgreSQL at {_DB_URL!s} "
            "is not reachable from this executor."
        )
    )


# ---------------------------------------------------------------------------
# Module-scope imports — deferred so a missing DB URL doesn't explode
# module import during collection.
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if _DB_URL is not None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from config import get_db  # type: ignore
    from fastapi.testclient import TestClient
    from main import app  # type: ignore


# ---------------------------------------------------------------------------
# Sentinel UUIDs + codes so fixtures are easy to clean up.
#
# NOTE: "i" is not a valid hex character, so packet 015i adopts the
# "015b" prefix convention matching packets 012i / 013i / 014i.  All
# fixture IDs live in the 015b0xxx range, distinct from 014b0xxx used
# by packet 014i's task integration smoke.
# ---------------------------------------------------------------------------

CLIENT_ID        = "015b0001-0000-4000-8000-000000000001"
SITE_ID          = "015b0002-0000-4000-8000-000000000001"
PROJECT_ID       = "015b0003-0000-4000-8000-000000000001"
WORK_PACKAGE_ID  = "015b0004-0000-4000-8000-000000000001"
TASK_ID          = "015b0005-0000-4000-8000-000000000001"
CREW_ID          = "015b0006-0000-4000-8000-000000000001"
EMPLOYEE_ID      = "015b0007-0000-4000-8000-000000000001"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_ASSIGNMENT_ID = "015b0099-0000-4000-8000-000000000099"
NONEXISTENT_WP_ID         = "015b0098-0000-4000-8000-000000000099"
NONEXISTENT_TASK_ID       = "015b0097-0000-4000-8000-000000000099"
NONEXISTENT_EMPLOYEE_ID   = "015b0096-0000-4000-8000-000000000099"
NONEXISTENT_CREW_ID       = "015b0095-0000-4000-8000-000000000099"

CLIENT_NAME    = "Smoke Client 015i"
SITE_NAME      = "Smoke Site 015i"
PROJECT_CODE   = "SMK15I-PRJ-1"
PROJECT_TITLE  = "Smoke Project 015i"
WP_CODE        = "SMK15I-WP-1"
WP_TITLE       = "Smoke WP 015i"
TASK_CODE      = "SMK15I-TASK-1"
TASK_TITLE     = "Smoke Task 015i"
CREW_CODE      = "SMK15I-CREW-1"
CREW_NAME      = "Smoke Crew 015i"
EMPLOYEE_CODE  = "SMK15I-EMP-1"
EMPLOYEE_FIRST = "Smoke"
EMPLOYEE_LAST  = "Worker015i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work + identity parent rows the
    assignment write surface needs to validate FK references end to
    end.  Assignments validate four references at the API boundary —
    work_package_id, task_id (intra-work), employee_id, crew_id
    (identity) — so all four parent rows must exist.
    """
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK15I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK15I-SITE-1', :sname, true)
            ON CONFLICT (site_id) DO NOTHING
            """
        ),
        dict(sid=SITE_ID, cid=CLIENT_ID, sname=SITE_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.projects
              (project_id, project_code, title, client_id, site_id)
            VALUES
              (:pid, :pcode, :ptitle, :cid, :sid)
            ON CONFLICT (project_id) DO NOTHING
            """
        ),
        dict(
            pid=PROJECT_ID, pcode=PROJECT_CODE, ptitle=PROJECT_TITLE,
            cid=CLIENT_ID, sid=SITE_ID,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.work_packages
              (work_package_id, project_id, work_package_code, title,
               work_type, client_id, site_id)
            VALUES
              (:wpid, :pid, :wpcode, :wptitle,
               'testing', :cid, :sid)
            ON CONFLICT (work_package_id) DO NOTHING
            """
        ),
        dict(
            wpid=WORK_PACKAGE_ID, pid=PROJECT_ID, wpcode=WP_CODE,
            wptitle=WP_TITLE, cid=CLIENT_ID, sid=SITE_ID,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.tasks
              (task_id, work_package_id, task_code, title)
            VALUES
              (:tid, :wpid, :tcode, :ttitle)
            ON CONFLICT (task_id) DO NOTHING
            """
        ),
        dict(
            tid=TASK_ID, wpid=WORK_PACKAGE_ID,
            tcode=TASK_CODE, ttitle=TASK_TITLE,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO identity.crews
              (crew_id, crew_code, name, is_active)
            VALUES
              (:cwid, :ccode, :cname, true)
            ON CONFLICT (crew_id) DO NOTHING
            """
        ),
        dict(cwid=CREW_ID, ccode=CREW_CODE, cname=CREW_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO identity.employees
              (employee_id, employee_code, first_name, last_name, is_active)
            VALUES
              (:eid, :ecode, :efirst, :elast, true)
            ON CONFLICT (employee_id) DO NOTHING
            """
        ),
        dict(
            eid=EMPLOYEE_ID, ecode=EMPLOYEE_CODE,
            efirst=EMPLOYEE_FIRST, elast=EMPLOYEE_LAST,
        ),
    )


def _cleanup(conn):
    """Remove every fixture row the smoke inserted, children first.

    Sweep up every assignment row our POST calls created using the
    parent IDs as the discriminator (assignments don't carry a code
    column, so we match on work_package_id / task_id of the smoke
    fixtures).
    """
    conn.execute(
        text(
            """
            DELETE FROM work.assignments
            WHERE work_package_id = :wpid OR task_id = :tid
            """
        ),
        dict(wpid=WORK_PACKAGE_ID, tid=TASK_ID),
    )
    conn.execute(
        text("DELETE FROM identity.employees WHERE employee_id = :e"),
        dict(e=EMPLOYEE_ID),
    )
    conn.execute(
        text("DELETE FROM identity.crews WHERE crew_id = :c"),
        dict(c=CREW_ID),
    )
    conn.execute(
        text("DELETE FROM work.tasks WHERE task_id = :t"),
        dict(t=TASK_ID),
    )
    conn.execute(
        text("DELETE FROM work.work_packages WHERE work_package_id = :w"),
        dict(w=WORK_PACKAGE_ID),
    )
    conn.execute(
        text("DELETE FROM work.projects WHERE project_id = :p"),
        dict(p=PROJECT_ID),
    )
    conn.execute(
        text("DELETE FROM org.sites WHERE site_id = :s"),
        dict(s=SITE_ID),
    )
    conn.execute(
        text("DELETE FROM org.clients WHERE client_id = :c"),
        dict(c=CLIENT_ID),
    )


@pytest.fixture(scope="module")
def integration_engine():
    engine = create_engine(_DB_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def seeded_db(integration_engine):
    SessionLocal = sessionmaker(
        bind=integration_engine, autoflush=False,
        autocommit=False, future=True,
    )
    with integration_engine.begin() as conn:
        _seed_supporting_rows(conn)

    yield SessionLocal

    with integration_engine.begin() as conn:
        _cleanup(conn)


@pytest.fixture()
def client(seeded_db):
    SessionLocal = seeded_db

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests — real-PG end-to-end coverage of the assignment write surface
# ---------------------------------------------------------------------------

class TestAssignmentCreateIntegration:
    """POST /api/v1/work/assignments against the live PG runtime."""

    def test_create_with_work_package_only_returns_201(self, client):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] is None
        # Server defaults apply
        assert data["assignment_role"] == "primary"
        assert data["is_actual_participation"] is False
        assert data["created_from_source"] == "manual"
        # A new UUID is assigned by the DB default
        assert data["assignment_id"]

    def test_create_with_task_only_returns_201(self, client):
        payload = {
            "task_id": TASK_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["task_id"] == TASK_ID
        assert data["work_package_id"] is None

    def test_create_with_full_payload_persists_all_refs(self, client):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_id": TASK_ID,
            "employee_id": EMPLOYEE_ID,
            "crew_id": CREW_ID,
            "assignment_role": "support",
            "planned_hours": "12.50",
            "actual_hours": "10.00",
            "is_actual_participation": True,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] == TASK_ID
        assert data["employee_id"] == EMPLOYEE_ID
        assert data["crew_id"] == CREW_ID
        assert data["assignment_role"] == "support"
        assert data["planned_hours"] == "12.50"
        assert data["actual_hours"] == "10.00"
        assert data["is_actual_participation"] is True

    def test_create_rejects_missing_parent_with_422(self, client):
        """Pydantic @model_validator mirrors the DDL
        ck_assignments_at_least_one_parent constraint at the API
        boundary."""
        payload = {
            "employee_id": EMPLOYEE_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text

    def test_create_rejects_unknown_work_package_with_merged_422(self, client):
        """Intra-work FK validation fires against the live work.work_packages."""
        payload = {
            "work_package_id": NONEXISTENT_WP_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_rejects_unknown_task_with_merged_422(self, client):
        """Intra-work FK validation fires against the live work.tasks."""
        payload = {
            "task_id": NONEXISTENT_TASK_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "task_id" in data["errors"]

    def test_create_rejects_unknown_employee_with_merged_422(self, client):
        """Identity FK validation fires against the live identity.employees."""
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "employee_id": NONEXISTENT_EMPLOYEE_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "employee_id" in data["errors"]

    def test_create_rejects_unknown_crew_with_merged_422(self, client):
        """Identity FK validation fires against the live identity.crews."""
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "crew_id": NONEXISTENT_CREW_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "crew_id" in data["errors"]

    def test_create_rejects_all_four_bad_fks_with_merged_422(self, client):
        """All four bad FKs must be reported in a single merged error
        dict (merged-error behavior inherited from packet 015's
        _validate_assignment_references helper)."""
        payload = {
            "work_package_id": NONEXISTENT_WP_ID,
            "task_id": NONEXISTENT_TASK_ID,
            "employee_id": NONEXISTENT_EMPLOYEE_ID,
            "crew_id": NONEXISTENT_CREW_ID,
        }
        resp = client.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        for field in ("work_package_id", "task_id", "employee_id", "crew_id"):
            assert field in data["errors"], (
                f"Expected '{field}' in merged error dict, got "
                f"{list(data['errors'].keys())}"
            )


class TestAssignmentPatchIntegration:
    """PATCH /api/v1/work/assignments/{id} against the live PG runtime."""

    def test_patch_role_returns_200(self, client):
        # First create a row to patch
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]
        assert created.json()["assignment_role"] == "primary"

        patched = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"assignment_role": "support"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["assignment_id"] == assignment_id
        assert data["assignment_role"] == "support"
        # Other fields should be unchanged
        assert data["work_package_id"] == WORK_PACKAGE_ID

    def test_patch_employee_assignment_returns_200(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]
        assert created.json()["employee_id"] is None

        patched = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"employee_id": EMPLOYEE_ID},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["employee_id"] == EMPLOYEE_ID

    def test_patch_crew_assignment_returns_200(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"task_id": TASK_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]
        assert created.json()["crew_id"] is None

        patched = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"crew_id": CREW_ID},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["crew_id"] == CREW_ID

    def test_patch_hours_returns_200(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]

        patched = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"planned_hours": "8.00", "actual_hours": "6.50"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["planned_hours"] == "8.00"
        assert data["actual_hours"] == "6.50"

    def test_patch_nonexistent_assignment_returns_404(self, client):
        resp = client.patch(
            f"/api/v1/work/assignments/{NONEXISTENT_ASSIGNMENT_ID}",
            json={"assignment_role": "support"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_rejects_unknown_employee_with_merged_422(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]

        resp = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"employee_id": NONEXISTENT_EMPLOYEE_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "employee_id" in data["errors"]

    def test_patch_rejects_unknown_crew_with_merged_422(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]

        resp = client.patch(
            f"/api/v1/work/assignments/{assignment_id}",
            json={"crew_id": NONEXISTENT_CREW_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "crew_id" in data["errors"]

    def test_patch_empty_body_returns_200_unchanged(self, client):
        created = client.post(
            "/api/v1/work/assignments",
            json={"work_package_id": WORK_PACKAGE_ID, "planned_hours": "4.00"},
        )
        assert created.status_code == 201, created.text
        assignment_id = created.json()["assignment_id"]

        resp = client.patch(
            f"/api/v1/work/assignments/{assignment_id}", json={},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["assignment_id"] == assignment_id
        assert data["planned_hours"] == "4.00"


class TestReadOnlyBoundaryUnchanged:
    """Sanity-check: only WBS-node PM entities remain read-only after
    packet 018.  /assignments was opened for writes by packet 015,
    /dependencies by packet 016, /execution-issues by packet 017, and
    /progress-snapshots by packet 018, so none of those belong in this
    guard list any longer."""

    READ_ONLY_TARGETS = [
        "/api/v1/work/wbs-nodes",
    ]

    def test_post_still_rejected_for_read_only_entities(self, client):
        for path in self.READ_ONLY_TARGETS:
            resp = client.post(path, json={})
            assert resp.status_code == 405, (
                f"POST {path} should be 405, got {resp.status_code}"
            )

    def test_patch_still_rejected_for_read_only_entities(self, client):
        for path in self.READ_ONLY_TARGETS:
            resp = client.patch(path, json={})
            assert resp.status_code == 405, (
                f"PATCH {path} should be 405, got {resp.status_code}"
            )
