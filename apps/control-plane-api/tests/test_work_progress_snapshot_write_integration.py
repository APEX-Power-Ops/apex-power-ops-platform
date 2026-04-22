"""
PM/Work Domain — Progress-Snapshot Write Surface Integration Smoke
===================================================================
Packet: 2026-04-15-pm-schema-018i (executed jointly with packet 018)

Locks in the real-PostgreSQL runtime behavior of the progress-snapshot
POST and PATCH surface wired by packet 018.  Exercises the existing
write handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST  /api/v1/work/progress-snapshots                        (packet 018)
       → PATCH /api/v1/work/progress-snapshots/{progress_snapshot_id} (packet 018)
          → routes.py handler
             → services.work.mutations
                (_validate_progress_snapshot_references:
                 project_id against work.projects,
                 work_package_id against work.work_packages,
                 task_id against work.tasks,
                 supersedes_snapshot_id against work.progress_snapshots (self),
                 approved_by against identity.users;
                 period-monotonicity enforced at the Pydantic
                 boundary on create and at the service layer via
                 effective-pair on update;
                 self-reference enforced at service layer via
                 effective-pair on update)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with only the required fields (project_id +
    snapshot_period_start/end) returns 201 and a materialized
    ProgressSnapshotRead whose id is the inserted row.
  * POST with every optional FK populated (work_package_id, task_id,
    supersedes_snapshot_id, approved_by) returns 201.
  * POST with each SnapshotStatus enum value round-trips without PG
    enum-mapping errors.
  * POST with a full payload (percent_complete, apparatus counts,
    billable_amount, billing_reference, approved_by / approved_at,
    source_data_date, created_from_source) persists and round-trips.
  * POST with an unknown project_id / work_package_id / task_id /
    supersedes_snapshot_id / approved_by returns 422 with the expected
    field in the merged error dict.
  * POST with period_end < period_start returns 422 at the Pydantic
    @model_validator layer before any DB round-trip.
  * PATCH with valid snapshot_status / percent_complete / apparatus
    counts / approved_by returns 200 and the updated row.
  * PATCH with a valid FK swap (project_id, work_package_id, task_id,
    supersedes_snapshot_id, approved_by) returns 200.
  * PATCH with an unknown FK returns 422 with the field keyed in
    errors.
  * PATCH self-reference (supersedes_snapshot_id == progress_snapshot_id)
    returns 422.
  * PATCH that violates period monotonicity using only one end (the
    other filled in from the existing row) returns 422.
  * PATCH against a random non-existent progress_snapshot_id returns
    404.
  * PATCH with empty body returns 200 (idempotent no-op).
  * Non-progress-snapshot read-only PM-write endpoints (WBS nodes)
    remain 405 on POST.

Design constraints (packet 018 hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 018's progress-snapshot-only
    scope — seed supporting rows (client, site, project, work_package,
    alt_work_package, task, alt_task, identity user, parent snapshot)
    are inserted directly via SQLAlchemy ``text()`` statements, not
    through the write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if ``APEX_INTEGRATION_DATABASE_URL`` (or
    ``DATABASE_URL``) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g, 012i,
    013i, 014i, 015i, 016i, and 017i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK18I-`` and sentinel
    UUID prefix ``018b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``018b`` is used in its place, matching the convention
    established by packets 012i / 013i / 014i / 015i / 016i / 017i).
  - Teardown deletes only the fixture rows (including any
    progress_snapshot rows created by the POST calls), leaving
    existing staging data untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_progress_snapshot_write_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packets 012g, 012i, 013i, 014i,
# 015i, 016i, 017i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Progress-snapshot write surface depends on PostgreSQL ENUMs;
        # skip sqlite.
        return None
    return url


def _db_is_reachable(url: str, timeout: float = 2.0) -> bool:
    """TCP-level reachability probe.  Avoids authentication noise."""
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
# NOTE: "i" is not a valid hex character, so packet 018's integration
# smoke adopts the "018b" prefix convention matching packets 012i /
# 013i / 014i / 015i / 016i / 017i.  All fixture IDs live in the 018b0xxx
# range, distinct from 017b0xxx used by packet 017i's execution-issue
# integration smoke.
# ---------------------------------------------------------------------------

CLIENT_ID           = "018b0001-0000-4000-8000-000000000001"
SITE_ID             = "018b0002-0000-4000-8000-000000000001"
PROJECT_ID          = "018b0003-0000-4000-8000-000000000001"
ALT_PROJECT_ID      = "018b0003-0000-4000-8000-000000000002"
WORK_PACKAGE_ID     = "018b0004-0000-4000-8000-000000000001"
ALT_WORK_PACKAGE_ID = "018b0004-0000-4000-8000-000000000002"
TASK_ID             = "018b0005-0000-4000-8000-000000000001"
ALT_TASK_ID         = "018b0005-0000-4000-8000-000000000002"
APPROVER_USER_ID    = "018b0006-0000-4000-8000-000000000001"
PARENT_SNAPSHOT_ID  = "018b0007-0000-4000-8000-000000000001"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_SNAPSHOT_ID   = "018b0099-0000-4000-8000-000000000099"
NONEXISTENT_PROJECT_ID    = "018b0097-0000-4000-8000-000000000091"
NONEXISTENT_WORK_PKG_ID   = "018b0097-0000-4000-8000-000000000092"
NONEXISTENT_TASK_ID       = "018b0097-0000-4000-8000-000000000093"
NONEXISTENT_SUPERSEDES_ID = "018b0097-0000-4000-8000-000000000094"
NONEXISTENT_APPROVER_ID   = "018b0097-0000-4000-8000-000000000095"

CLIENT_NAME      = "Smoke Client 018i"
SITE_NAME        = "Smoke Site 018i"
PROJECT_CODE     = "SMK18I-PRJ-1"
PROJECT_TITLE    = "Smoke Project 018i"
ALT_PROJECT_CODE = "SMK18I-PRJ-2"
ALT_PROJECT_TITLE = "Smoke Project 018i ALT"
WP_CODE          = "SMK18I-WP-1"
WP_TITLE         = "Smoke WP 018i"
ALT_WP_CODE      = "SMK18I-WP-2"
ALT_WP_TITLE     = "Smoke WP 018i ALT"
TASK_CODE        = "SMK18I-TASK-1"
TASK_TITLE       = "Smoke Task 018i"
ALT_TASK_CODE    = "SMK18I-TASK-2"
ALT_TASK_TITLE   = "Smoke Task 018i ALT"
APPROVER_NAME    = "Carol Approver 018i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work + identity parent rows the
    progress-snapshot write surface needs to validate FK references
    end-to-end.  Progress snapshots validate five references at the
    API boundary — project_id, work_package_id, task_id,
    supersedes_snapshot_id (self), approved_by (identity.users).
    """
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK18I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK18I-SITE-1', :sname, true)
            ON CONFLICT (site_id) DO NOTHING
            """
        ),
        dict(sid=SITE_ID, cid=CLIENT_ID, sname=SITE_NAME),
    )
    for pid, pcode, ptitle in (
        (PROJECT_ID, PROJECT_CODE, PROJECT_TITLE),
        (ALT_PROJECT_ID, ALT_PROJECT_CODE, ALT_PROJECT_TITLE),
    ):
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
                pid=pid, pcode=pcode, ptitle=ptitle,
                cid=CLIENT_ID, sid=SITE_ID,
            ),
        )
    for wpid, wpcode, wptitle in (
        (WORK_PACKAGE_ID, WP_CODE, WP_TITLE),
        (ALT_WORK_PACKAGE_ID, ALT_WP_CODE, ALT_WP_TITLE),
    ):
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
                wpid=wpid, pid=PROJECT_ID, wpcode=wpcode,
                wptitle=wptitle, cid=CLIENT_ID, sid=SITE_ID,
            ),
        )
    for tid, tcode, ttitle in (
        (TASK_ID, TASK_CODE, TASK_TITLE),
        (ALT_TASK_ID, ALT_TASK_CODE, ALT_TASK_TITLE),
    ):
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
                tid=tid, wpid=WORK_PACKAGE_ID,
                tcode=tcode, ttitle=ttitle,
            ),
        )
    conn.execute(
        text(
            """
            INSERT INTO identity.users (user_id, email, display_name, is_active)
            VALUES (:uid, 'smoke018i.approver@example.com', :uname, true)
            ON CONFLICT (user_id) DO NOTHING
            """
        ),
        dict(uid=APPROVER_USER_ID, uname=APPROVER_NAME),
    )
    # Seed a parent snapshot that new snapshots can supersede.
    conn.execute(
        text(
            """
            INSERT INTO work.progress_snapshots
              (progress_snapshot_id, project_id,
               snapshot_period_start, snapshot_period_end,
               snapshot_status, created_from_source)
            VALUES
              (:sid, :pid, '2026-03-01', '2026-03-31', 'approved', 'manual')
            ON CONFLICT (progress_snapshot_id) DO NOTHING
            """
        ),
        dict(sid=PARENT_SNAPSHOT_ID, pid=PROJECT_ID),
    )


def _cleanup(conn):
    """Remove every fixture row the smoke inserted, children first.

    Sweep up every progress_snapshot row our POST calls created using
    the seeded project IDs as the discriminator.
    """
    conn.execute(
        text(
            """
            DELETE FROM work.progress_snapshots
            WHERE project_id IN (:p, :alt_p)
            """
        ),
        dict(p=PROJECT_ID, alt_p=ALT_PROJECT_ID),
    )
    conn.execute(
        text(
            """
            DELETE FROM identity.users
            WHERE user_id = :u
            """
        ),
        dict(u=APPROVER_USER_ID),
    )
    conn.execute(
        text(
            """
            DELETE FROM work.tasks
            WHERE task_id IN (:t, :alt_t)
            """
        ),
        dict(t=TASK_ID, alt_t=ALT_TASK_ID),
    )
    conn.execute(
        text(
            """
            DELETE FROM work.work_packages
            WHERE work_package_id IN (:wp, :alt_wp)
            """
        ),
        dict(wp=WORK_PACKAGE_ID, alt_wp=ALT_WORK_PACKAGE_ID),
    )
    conn.execute(
        text(
            """
            DELETE FROM work.projects
            WHERE project_id IN (:p, :alt_p)
            """
        ),
        dict(p=PROJECT_ID, alt_p=ALT_PROJECT_ID),
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


@pytest.fixture()
def clean_child_snapshots(integration_engine):
    """Remove any leftover progress-snapshot rows authored by these
    tests before and after each test run.  The parent snapshot
    (PARENT_SNAPSHOT_ID) is retained across tests for supersedes
    reference."""
    def _wipe(conn):
        conn.execute(
            text(
                """
                DELETE FROM work.progress_snapshots
                WHERE project_id IN (:p, :alt_p)
                  AND progress_snapshot_id <> :parent
                """
            ),
            dict(
                p=PROJECT_ID, alt_p=ALT_PROJECT_ID,
                parent=PARENT_SNAPSHOT_ID,
            ),
        )

    with integration_engine.begin() as conn:
        _wipe(conn)
    yield
    with integration_engine.begin() as conn:
        _wipe(conn)


MINIMAL_SNAPSHOT_PAYLOAD = {
    "project_id": PROJECT_ID,
    "snapshot_period_start": "2026-04-01",
    "snapshot_period_end": "2026-04-14",
}


# ---------------------------------------------------------------------------
# Tests — real-PG end-to-end coverage of the progress-snapshot write surface
# ---------------------------------------------------------------------------

class TestProgressSnapshotCreateIntegration:
    """POST /api/v1/work/progress-snapshots against the live PG runtime."""

    def test_create_minimal_returns_201(self, client, clean_child_snapshots):
        resp = client.post(
            "/api/v1/work/progress-snapshots",
            json=MINIMAL_SNAPSHOT_PAYLOAD,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["project_id"] == PROJECT_ID
        assert data["snapshot_period_start"] == "2026-04-01"
        assert data["snapshot_period_end"] == "2026-04-14"
        # Server defaults apply
        assert data["snapshot_status"] == "draft"
        assert data["created_from_source"] == "manual"
        # Server-assigned PK
        assert data["progress_snapshot_id"]
        assert data["created_at"]
        assert data["updated_at"]

    def test_create_with_all_optional_fks_returns_201(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "work_package_id": WORK_PACKAGE_ID,
            "task_id": TASK_ID,
            "supersedes_snapshot_id": PARENT_SNAPSHOT_ID,
            "approved_by": APPROVER_USER_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] == TASK_ID
        assert data["supersedes_snapshot_id"] == PARENT_SNAPSHOT_ID
        assert data["approved_by"] == APPROVER_USER_ID

    @pytest.mark.parametrize(
        "snapshot_status",
        ["draft", "submitted", "approved", "rejected"],
    )
    def test_create_accepts_all_snapshot_statuses(
        self, client, clean_child_snapshots, snapshot_status,
    ):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "snapshot_status": snapshot_status}
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["snapshot_status"] == snapshot_status

    def test_create_with_full_payload_persists_all_fields(
        self, client, clean_child_snapshots,
    ):
        payload = {
            "project_id": PROJECT_ID,
            "work_package_id": WORK_PACKAGE_ID,
            "task_id": TASK_ID,
            "snapshot_period_start": "2026-04-01",
            "snapshot_period_end": "2026-04-14",
            "snapshot_status": "approved",
            "completed_apparatus_count": 12,
            "total_apparatus_count": 20,
            "percent_complete": "60.00",
            "actual_labor_hours": "240.50",
            "billable_amount": "15000.75",
            "billing_reference": "INV-018I-001",
            "approved_by": APPROVER_USER_ID,
            "approved_at": "2026-04-15T08:00:00+00:00",
            "supersedes_snapshot_id": PARENT_SNAPSHOT_ID,
            "source_data_date": "2026-04-14T23:59:59+00:00",
            "created_from_source": "p6_import",
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["snapshot_status"] == "approved"
        assert data["completed_apparatus_count"] == 12
        assert data["total_apparatus_count"] == 20
        assert data["billing_reference"] == "INV-018I-001"
        assert data["created_from_source"] == "p6_import"
        assert data["supersedes_snapshot_id"] == PARENT_SNAPSHOT_ID

    def test_create_rejects_unknown_project_id(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "project_id": NONEXISTENT_PROJECT_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "project_id" in data["errors"]

    def test_create_rejects_unknown_work_package_id(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "work_package_id": NONEXISTENT_WORK_PKG_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        assert "work_package_id" in resp.json()["errors"]

    def test_create_rejects_unknown_task_id(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "task_id": NONEXISTENT_TASK_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        assert "task_id" in resp.json()["errors"]

    def test_create_rejects_unknown_supersedes_snapshot_id(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "supersedes_snapshot_id": NONEXISTENT_SUPERSEDES_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        assert "supersedes_snapshot_id" in resp.json()["errors"]

    def test_create_rejects_unknown_approved_by(
        self, client, clean_child_snapshots,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "approved_by": NONEXISTENT_APPROVER_ID,
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        assert "approved_by" in resp.json()["errors"]

    def test_create_rejects_all_five_bad_fks_with_merged_422(
        self, client, clean_child_snapshots,
    ):
        payload = {
            "project_id": NONEXISTENT_PROJECT_ID,
            "work_package_id": NONEXISTENT_WORK_PKG_ID,
            "task_id": NONEXISTENT_TASK_ID,
            "supersedes_snapshot_id": NONEXISTENT_SUPERSEDES_ID,
            "approved_by": NONEXISTENT_APPROVER_ID,
            "snapshot_period_start": "2026-04-01",
            "snapshot_period_end": "2026-04-14",
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        errors = resp.json()["errors"]
        assert "project_id" in errors
        assert "work_package_id" in errors
        assert "task_id" in errors
        assert "supersedes_snapshot_id" in errors
        assert "approved_by" in errors

    def test_create_rejects_period_end_before_period_start(
        self, client, clean_child_snapshots,
    ):
        """Pydantic model_validator raises 422 before any DB round-trip."""
        payload = {
            "project_id": PROJECT_ID,
            "snapshot_period_start": "2026-04-14",
            "snapshot_period_end": "2026-04-01",
        }
        resp = client.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422, resp.text
        rendered = str(resp.json()).lower()
        assert "on or after" in rendered


class TestProgressSnapshotPatchIntegration:
    """PATCH /api/v1/work/progress-snapshots/{id} against the live PG runtime."""

    def _seed_one(self, client):
        """Create one progress-snapshot via the API and return its id."""
        resp = client.post(
            "/api/v1/work/progress-snapshots",
            json=MINIMAL_SNAPSHOT_PAYLOAD,
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["progress_snapshot_id"]

    def test_patch_snapshot_status_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"snapshot_status": "submitted"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["progress_snapshot_id"] == snapshot_id
        assert data["snapshot_status"] == "submitted"

    def test_patch_percent_complete_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"percent_complete": "42.50"},
        )
        assert resp.status_code == 200, resp.text

    def test_patch_apparatus_counts_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={
                "completed_apparatus_count": 7,
                "total_apparatus_count": 10,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["completed_apparatus_count"] == 7
        assert data["total_apparatus_count"] == 10

    def test_patch_approved_by_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={
                "approved_by": APPROVER_USER_ID,
                "approved_at": "2026-04-15T09:30:00+00:00",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["approved_by"] == APPROVER_USER_ID

    def test_patch_project_id_swap_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"project_id": ALT_PROJECT_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["project_id"] == ALT_PROJECT_ID

    def test_patch_work_package_id_swap_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"work_package_id": ALT_WORK_PACKAGE_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["work_package_id"] == ALT_WORK_PACKAGE_ID

    def test_patch_task_id_swap_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"task_id": ALT_TASK_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["task_id"] == ALT_TASK_ID

    def test_patch_supersedes_snapshot_id_returns_200(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"supersedes_snapshot_id": PARENT_SNAPSHOT_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["supersedes_snapshot_id"] == PARENT_SNAPSHOT_ID

    def test_patch_rejects_unknown_project_id(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"project_id": NONEXISTENT_PROJECT_ID},
        )
        assert resp.status_code == 422, resp.text
        assert "project_id" in resp.json()["errors"]

    def test_patch_rejects_unknown_work_package_id(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"work_package_id": NONEXISTENT_WORK_PKG_ID},
        )
        assert resp.status_code == 422, resp.text
        assert "work_package_id" in resp.json()["errors"]

    def test_patch_rejects_unknown_task_id(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"task_id": NONEXISTENT_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        assert "task_id" in resp.json()["errors"]

    def test_patch_rejects_unknown_supersedes_snapshot_id(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"supersedes_snapshot_id": NONEXISTENT_SUPERSEDES_ID},
        )
        assert resp.status_code == 422, resp.text
        assert "supersedes_snapshot_id" in resp.json()["errors"]

    def test_patch_rejects_unknown_approved_by(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"approved_by": NONEXISTENT_APPROVER_ID},
        )
        assert resp.status_code == 422, resp.text
        assert "approved_by" in resp.json()["errors"]

    def test_patch_rejects_self_reference(
        self, client, clean_child_snapshots,
    ):
        """A snapshot cannot supersede itself — service-layer
        effective-pair guard returns 422."""
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"supersedes_snapshot_id": snapshot_id},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "supersedes_snapshot_id" in data["errors"]
        assert "itself" in data["errors"]["supersedes_snapshot_id"].lower()

    def test_patch_rejects_period_end_before_existing_start(
        self, client, clean_child_snapshots,
    ):
        """Effective-pair monotonicity: supplying only a new end that
        falls before the existing start raises 422."""
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"snapshot_period_end": "2026-03-01"},
        )
        assert resp.status_code == 422, resp.text
        assert "snapshot_period_end" in resp.json()["errors"]

    def test_patch_rejects_period_start_after_existing_end(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}",
            json={"snapshot_period_start": "2026-05-01"},
        )
        assert resp.status_code == 422, resp.text
        assert "snapshot_period_end" in resp.json()["errors"]

    def test_patch_nonexistent_progress_snapshot_returns_404(
        self, client, clean_child_snapshots,
    ):
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{NONEXISTENT_SNAPSHOT_ID}",
            json={"snapshot_status": "approved"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_empty_body_returns_200_unchanged(
        self, client, clean_child_snapshots,
    ):
        snapshot_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/progress-snapshots/{snapshot_id}", json={},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["progress_snapshot_id"] == snapshot_id
        # Baseline values still in place
        assert data["snapshot_status"] == "draft"
        assert data["project_id"] == PROJECT_ID


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
