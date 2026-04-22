"""
PM/Work Domain — Task Write Surface Integration Smoke
======================================================
Packet: 2026-04-14-pm-schema-014i

Locks in the real-PostgreSQL runtime behavior of the task POST and
PATCH surface wired by packet 014.  Exercises the existing write
handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST /api/v1/work/tasks                    (packet 014)
       → PATCH /api/v1/work/tasks/{id}              (packet 014)
          → routes.py handler
             → services.work.mutations
                (_validate_task_references: work_package_id +
                 primary_wbs_node_id intra-work FKs)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with valid work_package_id returns 201 and a materialized
    TaskRead whose id is the inserted row.
  * POST with an optional primary_wbs_node_id persists that reference.
  * POST with an unknown work_package_id returns 422 with a merged-
    field error dict containing work_package_id.
  * POST with an unknown primary_wbs_node_id returns 422 with a
    merged-field error dict containing primary_wbs_node_id.
  * POST with both FKs bad returns 422 with BOTH fields in the error
    dict (merged-error behavior inherited from packet 014's
    _validate_task_references helper).
  * PATCH with valid fields returns 200 and the updated row.
  * PATCH with an unknown primary_wbs_node_id returns 422.
  * PATCH against a random non-existent task_id returns 404.
  * Non-task PM-write endpoints (assignments, dependencies, execution
    issues, progress snapshots) remain 405 on POST/PATCH (sanity
    boundary).

Design constraints (packet 014i hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 014's task-only scope —
    seed supporting rows (client, site, project, work_package, wbs_node)
    are inserted directly via SQLAlchemy ``text()`` statements, not
    through the write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or
    `DATABASE_URL`) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g, 012i, and
    013i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK14I-`` and sentinel
    UUID prefix ``014b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``014b`` is used in its place, matching the convention
    established by packets 012i / 013i).
  - Teardown deletes only the fixture rows (including any task rows
    created by the POST call), leaving existing staging data untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_task_write_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packets 012g, 012i, 013i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Task write surface depends on PostgreSQL ENUMs; skip sqlite.
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
# NOTE: "i" is not a valid hex character, so packet 014i adopts the
# "014b" prefix convention matching packets 012i / 013i.  All fixture
# IDs live in the 014b0xxx range, distinct from 013b0xxx used by
# packet 013i's work-package integration smoke.
# ---------------------------------------------------------------------------

CLIENT_ID        = "014b0001-0000-4000-8000-000000000001"
SITE_ID          = "014b0002-0000-4000-8000-000000000001"
PROJECT_ID       = "014b0003-0000-4000-8000-000000000001"
WORK_PACKAGE_ID  = "014b0004-0000-4000-8000-000000000001"
WBS_NODE_ID      = "014b0005-0000-4000-8000-000000000001"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_TASK_ID = "014b0099-0000-4000-8000-000000000099"
NONEXISTENT_WP_ID   = "014b0098-0000-4000-8000-000000000099"
NONEXISTENT_WBS_ID  = "014b0097-0000-4000-8000-000000000099"

CLIENT_NAME   = "Smoke Client 014i"
SITE_NAME     = "Smoke Site 014i"
PROJECT_CODE  = "SMK14I-PRJ-1"
PROJECT_TITLE = "Smoke Project 014i"
WP_CODE       = "SMK14I-WP-1"
WP_TITLE      = "Smoke WP 014i"
WBS_CODE      = "SMK14I-WBS-1"
WBS_TITLE     = "Smoke WBS 014i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work parent rows the task write surface
    needs to validate FK references.  Tasks have no direct identity or
    org FKs of their own — those flow transitively through the parent
    work_package — so identity.crews is not required here."""
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK14I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK14I-SITE-1', :sname, true)
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
            INSERT INTO work.wbs_nodes
              (wbs_node_id, project_id, wbs_code, title)
            VALUES
              (:wid, :pid, :wcode, :wtitle)
            ON CONFLICT (wbs_node_id) DO NOTHING
            """
        ),
        dict(
            wid=WBS_NODE_ID, pid=PROJECT_ID,
            wcode=WBS_CODE, wtitle=WBS_TITLE,
        ),
    )


def _cleanup(conn):
    """Remove every fixture row the smoke inserted, children first."""
    # Remove any task rows our POSTs created (match on work_package + code
    # prefix so we sweep up every SMK14I-* row that the write API
    # generated).
    conn.execute(
        text(
            """
            DELETE FROM work.tasks
            WHERE work_package_id = :wpid
              AND (task_code LIKE 'SMK14I-%' OR title LIKE 'Smoke Task%014i%')
            """
        ),
        dict(wpid=WORK_PACKAGE_ID),
    )
    conn.execute(
        text("DELETE FROM work.wbs_nodes WHERE wbs_node_id = :w"),
        dict(w=WBS_NODE_ID),
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
# Tests — real-PG end-to-end coverage of the task write surface
# ---------------------------------------------------------------------------

class TestTaskCreateIntegration:
    """POST /api/v1/work/tasks against the live PG runtime."""

    def test_create_valid_task_returns_201(self, client):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-CREATE-1",
            "title": "Smoke Task Created 014i",
        }
        resp = client.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_code"] == "SMK14I-TASK-CREATE-1"
        assert data["title"] == "Smoke Task Created 014i"
        # Server defaults apply
        assert data["task_type"] == "task"
        assert data["lifecycle_state"] == "not_started"
        # A new UUID is assigned by the DB default
        assert data["task_id"]

    def test_create_with_optional_wbs_node(self, client):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-CREATE-WBS",
            "title": "Smoke Task With WBS 014i",
            "primary_wbs_node_id": WBS_NODE_ID,
            "task_type": "milestone",
            "lifecycle_state": "ready",
            "duration_hours": "8.5",
            "estimated_labor_hours": "16.0",
        }
        resp = client.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["primary_wbs_node_id"] == WBS_NODE_ID
        assert data["task_type"] == "milestone"
        assert data["lifecycle_state"] == "ready"
        assert data["duration_hours"] == "8.50"
        assert data["estimated_labor_hours"] == "16.00"

    def test_create_rejects_unknown_work_package_with_merged_422(self, client):
        """Intra-work FK validation fires against the live work.work_packages."""
        payload = {
            "work_package_id": NONEXISTENT_WP_ID,
            "task_code": "SMK14I-TASK-CREATE-BADWP",
            "title": "Smoke Task Bad WP 014i",
        }
        resp = client.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_rejects_unknown_wbs_node_with_merged_422(self, client):
        """Intra-work FK validation fires against the live work.wbs_nodes."""
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-CREATE-BADWBS",
            "title": "Smoke Task Bad WBS 014i",
            "primary_wbs_node_id": NONEXISTENT_WBS_ID,
        }
        resp = client.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "primary_wbs_node_id" in data["errors"]

    def test_create_rejects_both_bad_fks_with_merged_422(self, client):
        """Both bad FKs must be reported in a single merged error dict."""
        payload = {
            "work_package_id": NONEXISTENT_WP_ID,
            "task_code": "SMK14I-TASK-CREATE-BOTH-BAD",
            "title": "Smoke Task Both Bad 014i",
            "primary_wbs_node_id": NONEXISTENT_WBS_ID,
        }
        resp = client.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]
        assert "primary_wbs_node_id" in data["errors"]


class TestTaskPatchIntegration:
    """PATCH /api/v1/work/tasks/{id} against the live PG runtime."""

    def test_patch_title_returns_200(self, client):
        # First create a row to patch
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-1",
            "title": "Smoke Task Pre-Patch 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]

        patched = client.patch(
            f"/api/v1/work/tasks/{task_id}",
            json={"title": "Smoke Task Post-Patch 014i"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["task_id"] == task_id
        assert data["title"] == "Smoke Task Post-Patch 014i"
        # Other fields should be unchanged
        assert data["task_code"] == "SMK14I-TASK-PATCH-1"
        assert data["work_package_id"] == WORK_PACKAGE_ID

    def test_patch_lifecycle_transition_returns_200(self, client):
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-LIFECYCLE",
            "title": "Smoke Task Lifecycle 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]
        assert created.json()["lifecycle_state"] == "not_started"

        patched = client.patch(
            f"/api/v1/work/tasks/{task_id}",
            json={"lifecycle_state": "active"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["lifecycle_state"] == "active"

    def test_patch_assigns_wbs_node_returns_200(self, client):
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-WBS",
            "title": "Smoke Task For WBS Assign 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]
        assert created.json()["primary_wbs_node_id"] is None

        patched = client.patch(
            f"/api/v1/work/tasks/{task_id}",
            json={"primary_wbs_node_id": WBS_NODE_ID},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["primary_wbs_node_id"] == WBS_NODE_ID

    def test_patch_nonexistent_task_returns_404(self, client):
        resp = client.patch(
            f"/api/v1/work/tasks/{NONEXISTENT_TASK_ID}",
            json={"title": "Should not apply"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_rejects_unknown_wbs_node_with_merged_422(self, client):
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-BADWBS",
            "title": "Smoke Task Patch BadWBS 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]

        resp = client.patch(
            f"/api/v1/work/tasks/{task_id}",
            json={"primary_wbs_node_id": NONEXISTENT_WBS_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "primary_wbs_node_id" in data["errors"]

    def test_patch_rejects_unknown_work_package_with_merged_422(self, client):
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-BADWP",
            "title": "Smoke Task Patch BadWP 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]

        resp = client.patch(
            f"/api/v1/work/tasks/{task_id}",
            json={"work_package_id": NONEXISTENT_WP_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_patch_empty_body_returns_200_unchanged(self, client):
        create_payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_code": "SMK14I-TASK-PATCH-EMPTY",
            "title": "Smoke Task Empty Patch 014i",
        }
        created = client.post("/api/v1/work/tasks", json=create_payload)
        assert created.status_code == 201, created.text
        task_id = created.json()["task_id"]

        resp = client.patch(f"/api/v1/work/tasks/{task_id}", json={})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["title"] == "Smoke Task Empty Patch 014i"


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
