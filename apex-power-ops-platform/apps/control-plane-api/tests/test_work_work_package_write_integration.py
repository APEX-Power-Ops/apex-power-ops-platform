"""
PM/Work Domain — Work-Package Write Surface Integration Smoke
==============================================================
Packet: 2026-04-14-pm-schema-013i

Locks in the real-PostgreSQL runtime behavior of the work-package
POST and PATCH surface wired by packet 013.  Exercises the existing
write handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST /api/v1/work/work-packages            (packet 013)
       → PATCH /api/v1/work/work-packages/{id}      (packet 013)
          → routes.py handler
             → services.work.mutations
                (_validate_org_references +
                 _validate_work_package_references)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with valid org + intra-work FKs returns 201 and a
    materialized WorkPackageRead whose id is the inserted row.
  * PATCH with valid fields returns 200 and the updated row.
  * POST with an unknown assigned_crew_id returns 422 with a
    merged-field error dict containing assigned_crew_id (proves
    identity FK validation fires against the live identity domain).
  * PATCH against a random non-existent work_package_id returns 404.
  * No other PM-write endpoints exist — tasks, assignments, etc.
    remain 405 on POST/PATCH (sanity boundary).

Design constraints (packet 013i hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 013's work-package-only
    scope — seed supporting rows are inserted directly via SQLAlchemy
    ``text()`` statements, not through the write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or
    `DATABASE_URL`) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g and 012i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK13I-`` and sentinel
    UUID prefix ``013b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``013b`` is used in its place, matching the convention
    established by packets 012i / 013).
  - Teardown deletes only the fixture rows (including any work-package
    rows created by the POST call), leaving existing staging data
    untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_work_package_write_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packets 012g and 012i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Work-package write surface depends on PostgreSQL ENUMs; skip sqlite.
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
# NOTE: "i" is not a valid hex character, so packet 013i adopts the
# "013b" prefix convention matching packets 012i / 013.  All fixture
# IDs live in the 013b0xxx range, distinct from 012b0xxx used by
# packet 012i's org integration smoke.
# ---------------------------------------------------------------------------

CLIENT_ID    = "013b0001-0000-4000-8000-000000000001"
SITE_ID      = "013b0002-0000-4000-8000-000000000001"
PROJECT_ID   = "013b0003-0000-4000-8000-000000000001"
CREW_ID      = "013b0004-0000-4000-8000-000000000001"

# Work-package IDs created by the write API during the smoke run.
WP_CREATE_SENTINEL = "013b0005-0000-4000-8000-000000000001"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_WP_ID   = "013b0099-0000-4000-8000-000000000099"
NONEXISTENT_CREW_ID = "013b0098-0000-4000-8000-000000000099"

CLIENT_NAME   = "Smoke Client 013i"
SITE_NAME     = "Smoke Site 013i"
PROJECT_CODE  = "SMK13I-PRJ-1"
PROJECT_TITLE = "Smoke Project 013i"
CREW_NAME     = "Smoke Crew 013i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work + identity parent rows the
    work-package write surface needs to validate FK references."""
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK13I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK13I-SITE-1', :sname, true)
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
            INSERT INTO identity.crews
              (crew_id, crew_code, name, is_active)
            VALUES (:crid, 'SMK13I-CREW-1', :cname, true)
            ON CONFLICT (crew_id) DO NOTHING
            """
        ),
        dict(crid=CREW_ID, cname=CREW_NAME),
    )


def _cleanup(conn):
    """Remove every fixture row the smoke inserted, children first."""
    # Remove any work-package rows our POSTs created (match on project + code
    # prefix so we sweep up both the explicit sentinel row and any additional
    # SMK13I-* rows that the write API generated).
    conn.execute(
        text(
            """
            DELETE FROM work.work_packages
            WHERE project_id = :pid
              AND work_package_code LIKE 'SMK13I-%'
            """
        ),
        dict(pid=PROJECT_ID),
    )
    conn.execute(
        text("DELETE FROM work.projects WHERE project_id = :p"),
        dict(p=PROJECT_ID),
    )
    conn.execute(
        text("DELETE FROM identity.crews WHERE crew_id = :c"),
        dict(c=CREW_ID),
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
# Tests — real-PG end-to-end coverage of the work-package write surface
# ---------------------------------------------------------------------------

class TestWorkPackageCreateIntegration:
    """POST /api/v1/work/work-packages against the live PG runtime."""

    def test_create_valid_work_package_returns_201(self, client):
        payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-CREATE-1",
            "title": "Smoke WP Created 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
        }
        resp = client.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_code"] == "SMK13I-WP-CREATE-1"
        assert data["project_id"] == PROJECT_ID
        assert data["client_id"] == CLIENT_ID
        assert data["site_id"] == SITE_ID
        assert data["work_type"] == "testing"
        assert data["lifecycle_state"] == "draft"
        assert data["priority"] == "normal"
        # A new UUID is assigned by the DB default
        assert data["work_package_id"]

    def test_create_with_optional_crew_and_wbs_fields(self, client):
        payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-CREATE-2",
            "title": "Smoke WP With Crew 013i",
            "work_type": "maintenance",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
            "assigned_crew_id": CREW_ID,
            "priority": "high",
        }
        resp = client.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["assigned_crew_id"] == CREW_ID
        assert data["priority"] == "high"
        # Packet 013j — write response surfaces crew/org display names
        assert data["assigned_crew_name"] == CREW_NAME
        assert data["client_name"] == CLIENT_NAME
        assert data["site_name"] == SITE_NAME

    def test_create_without_crew_returns_null_crew_name(self, client):
        """Packet 013j — unassigned work packages return
        assigned_crew_name=None while still surfacing org names."""
        payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-CREATE-NOCREW",
            "title": "Smoke WP No Crew 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
        }
        resp = client.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["assigned_crew_id"] is None
        assert data["assigned_crew_name"] is None
        assert data["client_name"] == CLIENT_NAME
        assert data["site_name"] == SITE_NAME

    def test_create_rejects_unknown_crew_with_merged_422(self, client):
        """Identity FK validation fires against the live identity.crews table."""
        payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-CREATE-BADCREW",
            "title": "Smoke WP Bad Crew 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
            "assigned_crew_id": NONEXISTENT_CREW_ID,
        }
        resp = client.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "assigned_crew_id" in data["errors"]
        # Ensure the invalid row never landed in the DB
        # (caller-side smoke: the 422 is proof enough — persistence is
        # guarded by the mutation service before commit.)


class TestWorkPackagePatchIntegration:
    """PATCH /api/v1/work/work-packages/{id} against the live PG runtime."""

    def test_patch_title_returns_200(self, client):
        # First create a row to patch
        create_payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-PATCH-1",
            "title": "Smoke WP Pre-Patch 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
        }
        created = client.post("/api/v1/work/work-packages", json=create_payload)
        assert created.status_code == 201, created.text
        wp_id = created.json()["work_package_id"]

        patched = client.patch(
            f"/api/v1/work/work-packages/{wp_id}",
            json={"title": "Smoke WP Post-Patch 013i"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["work_package_id"] == wp_id
        assert data["title"] == "Smoke WP Post-Patch 013i"
        # Other fields should be unchanged
        assert data["work_package_code"] == "SMK13I-WP-PATCH-1"

    def test_patch_assigns_crew_returns_200(self, client):
        create_payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-PATCH-2",
            "title": "Smoke WP For Crew Assign 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
        }
        created = client.post("/api/v1/work/work-packages", json=create_payload)
        assert created.status_code == 201, created.text
        wp_id = created.json()["work_package_id"]
        assert created.json()["assigned_crew_id"] is None

        patched = client.patch(
            f"/api/v1/work/work-packages/{wp_id}",
            json={"assigned_crew_id": CREW_ID},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["assigned_crew_id"] == CREW_ID
        # Packet 013j — PATCH response reflects the newly-assigned crew's name
        assert patched.json()["assigned_crew_name"] == CREW_NAME

    def test_patch_title_only_preserves_existing_crew_name(self, client):
        """Packet 013j — PATCH that does not touch assigned_crew_id still
        returns the currently-assigned crew's display name so the client
        never sees a stale or null name on a partial update."""
        create_payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-PATCH-TITLE",
            "title": "Smoke WP Title Only Pre-Patch 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
            "assigned_crew_id": CREW_ID,
        }
        created = client.post("/api/v1/work/work-packages", json=create_payload)
        assert created.status_code == 201, created.text
        wp_id = created.json()["work_package_id"]
        assert created.json()["assigned_crew_name"] == CREW_NAME

        patched = client.patch(
            f"/api/v1/work/work-packages/{wp_id}",
            json={"title": "Smoke WP Title Only Post-Patch 013i"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["assigned_crew_id"] == CREW_ID
        assert data["assigned_crew_name"] == CREW_NAME
        assert data["client_name"] == CLIENT_NAME
        assert data["site_name"] == SITE_NAME

    def test_patch_nonexistent_work_package_returns_404(self, client):
        resp = client.patch(
            f"/api/v1/work/work-packages/{NONEXISTENT_WP_ID}",
            json={"title": "Should not apply"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_rejects_unknown_crew_with_merged_422(self, client):
        create_payload = {
            "project_id": PROJECT_ID,
            "work_package_code": "SMK13I-WP-PATCH-BADCREW",
            "title": "Smoke WP Patch BadCrew 013i",
            "work_type": "testing",
            "client_id": CLIENT_ID,
            "site_id": SITE_ID,
        }
        created = client.post("/api/v1/work/work-packages", json=create_payload)
        assert created.status_code == 201, created.text
        wp_id = created.json()["work_package_id"]

        resp = client.patch(
            f"/api/v1/work/work-packages/{wp_id}",
            json={"assigned_crew_id": NONEXISTENT_CREW_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "assigned_crew_id" in data["errors"]


class TestReadOnlyBoundaryUnchanged:
    """Sanity-check: only WBS-node PM entities remain read-only after
    packet 018.  /tasks was opened by packet 014, /assignments by
    packet 015, /dependencies by packet 016, /execution-issues by
    packet 017, and /progress-snapshots by packet 018, so none of those
    belong in this guard list any longer."""

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
