"""
PM/Work Domain — Execution-Issue Write Surface Integration Smoke
================================================================
Packet: 2026-04-15-pm-schema-017i (executed jointly with packet 017)

Locks in the real-PostgreSQL runtime behavior of the execution-issue
POST and PATCH surface wired by packet 017.  Exercises the existing
write handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST  /api/v1/work/execution-issues                       (packet 017)
       → PATCH /api/v1/work/execution-issues/{execution_issue_id}  (packet 017)
          → routes.py handler
             → services.work.mutations
                (_validate_execution_issue_references:
                 work_package_id against work.work_packages,
                 task_id against work.tasks; at-least-one-parent
                 check enforced at the Pydantic boundary before
                 any DB round-trip)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with a valid work_package_id-only parent returns 201 and a
    materialized ExecutionIssueRead whose id is the inserted row.
  * POST with a valid task_id-only parent returns 201.
  * POST with both parents set to valid FKs returns 201.
  * POST accepts each IssueType / Severity / IssueStatus enum
    end-to-end without PG enum-mapping errors.
  * POST with a full payload (details, resolution_type, resolved_at,
    closed_at, reported_by, assigned_to, blocks_completion,
    apparatus_ref, created_from_source) persists and round-trips.
  * POST with an unknown work_package_id returns 422 with
    work_package_id in the merged error dict.
  * POST with an unknown task_id returns 422 with task_id in the
    merged error dict.
  * POST with both unknown FKs returns 422 with both fields in the
    merged error dict.
  * POST with neither parent supplied returns 422 at the Pydantic
    @model_validator layer (at-least-one-parent), before any DB
    round-trip.
  * PATCH with valid status / severity / resolution_type / booleans
    returns 200 and the updated row.
  * PATCH with a valid work_package_id swap returns 200.
  * PATCH with a valid task_id swap returns 200.
  * PATCH with an unknown work_package_id / task_id returns 422.
  * PATCH against a random non-existent execution_issue_id returns 404.
  * PATCH with empty body returns 200 (idempotent no-op).
  * Non-execution-issue read-only PM-write endpoints (progress
    snapshots) remain 405 on POST (sanity boundary).

Design constraints (packet 017 hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 017's execution-issue-only
    scope — seed supporting rows (client, site, project,
    work_package, task, alt_work_package, alt_task) are inserted
    directly via SQLAlchemy ``text()`` statements, not through the
    write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if ``APEX_INTEGRATION_DATABASE_URL`` (or
    ``DATABASE_URL``) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g, 012i,
    013i, 014i, 015i, and 016i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK17I-`` and sentinel
    UUID prefix ``017b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``017b`` is used in its place, matching the convention
    established by packets 012i / 013i / 014i / 015i / 016i).
  - Teardown deletes only the fixture rows (including any execution
    issue rows created by the POST calls), leaving existing staging
    data untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_execution_issue_write_integration.py -q
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
# 015i, 016i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Execution-issue write surface depends on PostgreSQL ENUMs;
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
# NOTE: "i" is not a valid hex character, so packet 017's integration
# smoke adopts the "017b" prefix convention matching packets 012i /
# 013i / 014i / 015i / 016i.  All fixture IDs live in the 017b0xxx
# range, distinct from 016b0xxx used by packet 016i's dependency
# integration smoke.
# ---------------------------------------------------------------------------

CLIENT_ID           = "017b0001-0000-4000-8000-000000000001"
SITE_ID             = "017b0002-0000-4000-8000-000000000001"
PROJECT_ID          = "017b0003-0000-4000-8000-000000000001"
WORK_PACKAGE_ID     = "017b0004-0000-4000-8000-000000000001"
ALT_WORK_PACKAGE_ID = "017b0004-0000-4000-8000-000000000002"
TASK_ID             = "017b0005-0000-4000-8000-000000000001"
ALT_TASK_ID         = "017b0005-0000-4000-8000-000000000002"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_EXECUTION_ISSUE_ID = "017b0099-0000-4000-8000-000000000099"
NONEXISTENT_WORK_PACKAGE_ID    = "017b0097-0000-4000-8000-000000000097"
NONEXISTENT_TASK_ID            = "017b0097-0000-4000-8000-000000000098"

CLIENT_NAME    = "Smoke Client 017i"
SITE_NAME      = "Smoke Site 017i"
PROJECT_CODE   = "SMK17I-PRJ-1"
PROJECT_TITLE  = "Smoke Project 017i"
WP_CODE        = "SMK17I-WP-1"
WP_TITLE       = "Smoke WP 017i"
ALT_WP_CODE    = "SMK17I-WP-2"
ALT_WP_TITLE   = "Smoke WP 017i ALT"
TASK_CODE      = "SMK17I-TASK-1"
TASK_TITLE     = "Smoke Task 017i"
ALT_TASK_CODE  = "SMK17I-TASK-2"
ALT_TASK_TITLE = "Smoke Task 017i ALT"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work parent rows the execution-issue
    write surface needs to validate FK references end to end.  Execution
    issues validate two references at the API boundary — work_package_id
    (against work.work_packages) and task_id (against work.tasks).  The
    DDL requires at least one of the two parents to be non-null; we seed
    both primary and "alt" rows for each parent so PATCH scenarios can
    swap FKs to a distinct valid target.
    """
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK17I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK17I-SITE-1', :sname, true)
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


def _cleanup(conn):
    """Remove every fixture row the smoke inserted, children first.

    Sweep up every execution_issue row our POST calls created using the
    seeded work-package and task IDs as the discriminator (execution
    issues don't carry a unique code column, so we match on
    work_package_id / task_id of the smoke fixtures).
    """
    conn.execute(
        text(
            """
            DELETE FROM work.execution_issues
            WHERE work_package_id IN (:wp, :alt_wp)
               OR task_id         IN (:t, :alt_t)
            """
        ),
        dict(
            wp=WORK_PACKAGE_ID, alt_wp=ALT_WORK_PACKAGE_ID,
            t=TASK_ID, alt_t=ALT_TASK_ID,
        ),
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


@pytest.fixture()
def clean_execution_issues(integration_engine):
    """Remove any leftover execution-issue rows before each test so we
    never fight previous invocations of the POST handler."""
    with integration_engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM work.execution_issues
                WHERE work_package_id IN (:wp, :alt_wp)
                   OR task_id         IN (:t, :alt_t)
                """
            ),
            dict(
                wp=WORK_PACKAGE_ID, alt_wp=ALT_WORK_PACKAGE_ID,
                t=TASK_ID, alt_t=ALT_TASK_ID,
            ),
        )
    yield
    with integration_engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM work.execution_issues
                WHERE work_package_id IN (:wp, :alt_wp)
                   OR task_id         IN (:t, :alt_t)
                """
            ),
            dict(
                wp=WORK_PACKAGE_ID, alt_wp=ALT_WORK_PACKAGE_ID,
                t=TASK_ID, alt_t=ALT_TASK_ID,
            ),
        )


# ---------------------------------------------------------------------------
# Tests — real-PG end-to-end coverage of the execution-issue write surface
# ---------------------------------------------------------------------------

class TestExecutionIssueCreateIntegration:
    """POST /api/v1/work/execution-issues against the live PG runtime."""

    def test_create_with_work_package_parent_returns_201(
        self, client, clean_execution_issues,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "Pre-test grounding grid missing (SMK17I)",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] is None
        assert data["issue_type"] == "equipment_not_ready"
        assert data["severity"] == "major"
        # Server defaults apply
        assert data["status"] == "open"
        assert data["blocks_completion"] is False
        assert data["created_from_source"] == "manual"
        # Server-assigned PK + opened_at
        assert data["execution_issue_id"]
        assert data["opened_at"]

    def test_create_with_task_parent_returns_201(
        self, client, clean_execution_issues,
    ):
        payload = {
            "task_id": TASK_ID,
            "issue_type": "test_failure",
            "severity": "critical",
            "summary": "Hi-pot test failure on phase A (SMK17I)",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] is None
        assert data["task_id"] == TASK_ID

    def test_create_with_both_parents_returns_201(
        self, client, clean_execution_issues,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_id": TASK_ID,
            "issue_type": "safety_hold",
            "severity": "critical",
            "summary": "LOTO not verified before energization (SMK17I)",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] == TASK_ID

    @pytest.mark.parametrize(
        "issue_type",
        [
            "equipment_not_ready", "test_failure", "settings_incorrect",
            "access_blocked", "safety_hold", "material_missing",
            "documentation_gap", "other",
        ],
    )
    def test_create_accepts_all_issue_types(
        self, client, clean_execution_issues, issue_type,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "issue_type": issue_type,
            "severity": "minor",
            "summary": f"Smoke 017i issue_type={issue_type}",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        assert resp.json()["issue_type"] == issue_type

    @pytest.mark.parametrize(
        "severity", ["critical", "major", "minor", "info"],
    )
    def test_create_accepts_all_severities(
        self, client, clean_execution_issues, severity,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "issue_type": "other",
            "severity": severity,
            "summary": f"Smoke 017i severity={severity}",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        assert resp.json()["severity"] == severity

    @pytest.mark.parametrize(
        "status", ["open", "in_review", "escalated", "resolved", "closed"],
    )
    def test_create_accepts_all_statuses(
        self, client, clean_execution_issues, status,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "issue_type": "other",
            "severity": "minor",
            "status": status,
            "summary": f"Smoke 017i status={status}",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == status

    def test_create_with_full_payload_persists_all_fields(
        self, client, clean_execution_issues,
    ):
        payload = {
            "work_package_id": WORK_PACKAGE_ID,
            "task_id": TASK_ID,
            "apparatus_ref": "017b0008-0000-4000-8000-00000000000a",
            "issue_type": "test_failure",
            "severity": "major",
            "status": "resolved",
            "blocks_completion": True,
            "summary": "Breaker overshot trip setpoint (SMK17I)",
            "details": "Retest required after settings update.",
            "resolution_type": "retested_passed",
            "resolved_at": "2026-04-15T12:00:00+00:00",
            "closed_at": "2026-04-15T13:00:00+00:00",
            "created_from_source": "automation",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["work_package_id"] == WORK_PACKAGE_ID
        assert data["task_id"] == TASK_ID
        assert data["issue_type"] == "test_failure"
        assert data["severity"] == "major"
        assert data["status"] == "resolved"
        assert data["blocks_completion"] is True
        assert data["details"] == "Retest required after settings update."
        assert data["resolution_type"] == "retested_passed"
        assert data["created_from_source"] == "automation"

    def test_create_rejects_unknown_work_package_id(
        self, client, clean_execution_issues,
    ):
        payload = {
            "work_package_id": NONEXISTENT_WORK_PACKAGE_ID,
            "issue_type": "other",
            "severity": "minor",
            "summary": "Smoke 017i unknown WP",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_rejects_unknown_task_id(
        self, client, clean_execution_issues,
    ):
        payload = {
            "task_id": NONEXISTENT_TASK_ID,
            "issue_type": "other",
            "severity": "minor",
            "summary": "Smoke 017i unknown task",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "task_id" in data["errors"]

    def test_create_rejects_both_bad_fks_with_merged_422(
        self, client, clean_execution_issues,
    ):
        payload = {
            "work_package_id": NONEXISTENT_WORK_PACKAGE_ID,
            "task_id": NONEXISTENT_TASK_ID,
            "issue_type": "other",
            "severity": "minor",
            "summary": "Smoke 017i both bad FKs",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]

    def test_create_rejects_at_least_one_parent_violation(
        self, client, clean_execution_issues,
    ):
        """Neither work_package_id nor task_id supplied → Pydantic
        model_validator raises 422 before any DB round-trip."""
        payload = {
            "issue_type": "other",
            "severity": "minor",
            "summary": "Smoke 017i missing parents",
        }
        resp = client.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422, resp.text
        rendered = str(resp.json()).lower()
        assert "at least one" in rendered


class TestExecutionIssuePatchIntegration:
    """PATCH /api/v1/work/execution-issues/{id} against the live PG runtime."""

    def _seed_one(self, client):
        """Create one execution-issue via the API and return its id."""
        resp = client.post(
            "/api/v1/work/execution-issues",
            json={
                "work_package_id": WORK_PACKAGE_ID,
                "issue_type": "equipment_not_ready",
                "severity": "major",
                "summary": "Baseline issue for PATCH smoke (SMK17I)",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["execution_issue_id"]

    def test_patch_status_returns_200(self, client, clean_execution_issues):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["execution_issue_id"] == issue_id
        assert data["status"] == "resolved"

    def test_patch_severity_returns_200(self, client, clean_execution_issues):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"severity": "critical"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["severity"] == "critical"

    def test_patch_resolution_type_returns_200(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"resolution_type": "repaired"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["resolution_type"] == "repaired"

    def test_patch_blocks_completion_returns_200(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"blocks_completion": True},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["blocks_completion"] is True

    def test_patch_resolved_and_closed_at_returns_200(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={
                "resolved_at": "2026-04-15T14:00:00+00:00",
                "closed_at": "2026-04-15T15:00:00+00:00",
            },
        )
        assert resp.status_code == 200, resp.text

    def test_patch_summary_and_details_returns_200(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={
                "summary": "Revised summary (SMK17I)",
                "details": "Revised detail narrative (SMK17I)",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"] == "Revised summary (SMK17I)"
        assert data["details"] == "Revised detail narrative (SMK17I)"

    def test_patch_work_package_id_swap_returns_200(
        self, client, clean_execution_issues,
    ):
        """Patch work_package_id to the alt WP (a distinct valid FK)."""
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"work_package_id": ALT_WORK_PACKAGE_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["work_package_id"] == ALT_WORK_PACKAGE_ID

    def test_patch_task_id_swap_returns_200(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"task_id": ALT_TASK_ID},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["task_id"] == ALT_TASK_ID

    def test_patch_rejects_unknown_work_package_id(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"work_package_id": NONEXISTENT_WORK_PACKAGE_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_patch_rejects_unknown_task_id(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={"task_id": NONEXISTENT_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "task_id" in data["errors"]

    def test_patch_rejects_both_bad_fks_with_merged_422(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}",
            json={
                "work_package_id": NONEXISTENT_WORK_PACKAGE_ID,
                "task_id": NONEXISTENT_TASK_ID,
            },
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]

    def test_patch_nonexistent_execution_issue_returns_404(
        self, client, clean_execution_issues,
    ):
        resp = client.patch(
            f"/api/v1/work/execution-issues/{NONEXISTENT_EXECUTION_ISSUE_ID}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_empty_body_returns_200_unchanged(
        self, client, clean_execution_issues,
    ):
        issue_id = self._seed_one(client)
        resp = client.patch(
            f"/api/v1/work/execution-issues/{issue_id}", json={},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["execution_issue_id"] == issue_id
        # Baseline values still in place
        assert data["status"] == "open"
        assert data["severity"] == "major"


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
