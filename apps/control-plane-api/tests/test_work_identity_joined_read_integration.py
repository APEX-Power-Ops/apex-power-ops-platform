"""
PM/Work Domain — Identity-Joined Read Surface Integration Smoke
================================================================
Packet: 2026-04-14-pm-schema-012g

Locks in the real-PostgreSQL runtime behavior of the identity-joined
read surface wired by packet 012f.  Exercises the existing GET handlers
end-to-end against the live runtime path:

    FastAPI TestClient
       → /api/v1/work/<entity>
          → routes.py handler
             → services.work.queries (joinedload + hydrator)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * For each of the four affected entities, GET returns rows where the
    six identity-backed `*_name` fields populate from the live JOIN.
  * For sibling rows with null identity FKs, the same `*_name` fields
    remain `None`.

Design constraints (packet 012g hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 011f's project-only scope.
  - The module must degrade cleanly in environments without a reachable
    PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or `DATABASE_URL`) is
    absent or unreachable, the whole module is skipped rather than
    failing CI.

Seeding strategy:
  - All fixtures are tagged with the sentinel code prefix
    ``SMK12G-`` / ``WP-012G-`` / id-prefix ``012f0xxx-0000-4000-8000-``
    so they are distinguishable from all pre-existing rows.
  - Teardown deletes only the fixture rows; existing staging data is
    left untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_identity_joined_read_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Identity-joined read surface depends on PostgreSQL ENUMs; skip sqlite.
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
        "PostgreSQL URL hosting the work+identity schemas (e.g. apex_pm_stage)."
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
# Module-scope fixture: engine, Session factory, FastAPI client
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The real session factory + ORM models (deferred import so a missing DB URL
# doesn't explode module import).
if _DB_URL is not None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from config import get_db  # type: ignore
    from fastapi.testclient import TestClient
    from main import app  # type: ignore


# ---------------------------------------------------------------------------
# Sentinel UUIDs + codes so fixtures are easy to clean up
# ---------------------------------------------------------------------------

USER_REPORTER    = "012f0001-0000-4000-8000-000000000001"
USER_ASSIGNEE    = "012f0001-0000-4000-8000-000000000002"
USER_APPROVER    = "012f0001-0000-4000-8000-000000000003"
CREW_ALPHA       = "012f0002-0000-4000-8000-000000000001"
CREW_BETA        = "012f0002-0000-4000-8000-000000000002"
EMPLOYEE_GRACE   = "012f0003-0000-4000-8000-000000000001"

WP_POPULATED     = "012f0100-0000-4000-8000-000000000001"
WP_NULLFK        = "012f0100-0000-4000-8000-000000000002"
ASG_POPULATED    = "012f0200-0000-4000-8000-000000000001"
ASG_NULLFK       = "012f0200-0000-4000-8000-000000000002"
EI_POPULATED     = "012f0300-0000-4000-8000-000000000001"
EI_NULLFK        = "012f0300-0000-4000-8000-000000000002"
PS_POPULATED     = "012f0400-0000-4000-8000-000000000001"
PS_NULLFK        = "012f0400-0000-4000-8000-000000000002"

CREW_ALPHA_NAME  = "Smoke Crew Alpha 012g"
CREW_BETA_NAME   = "Smoke Crew Beta 012g"
EMPLOYEE_NAME    = "Grace Hopper"
REPORTER_NAME    = "Alice Reporter 012g"
ASSIGNEE_NAME    = "Bob Assignee 012g"
APPROVER_NAME    = "Carol Approver 012g"


SEED_STATEMENTS = [
    # identity rows
    """
    INSERT INTO identity.users (user_id, email, display_name, is_active)
    VALUES
      (:u_rep, 'smoke012g.reporter@example.com', :n_rep, true),
      (:u_asn, 'smoke012g.assignee@example.com', :n_asn, true),
      (:u_app, 'smoke012g.approver@example.com', :n_app, true)
    ON CONFLICT (user_id) DO NOTHING
    """,
    """
    INSERT INTO identity.crews (crew_id, crew_code, name, is_active)
    VALUES
      (:c_a, 'SMK12G-CREW-A', :n_a, true),
      (:c_b, 'SMK12G-CREW-B', :n_b, true)
    ON CONFLICT (crew_id) DO NOTHING
    """,
    """
    INSERT INTO identity.employees
      (employee_id, user_id, employee_code, first_name, last_name, is_active)
    VALUES (:e_grace, :u_rep, 'SMK12G-EMP-1', 'Grace', 'Hopper', true)
    ON CONFLICT (employee_id) DO NOTHING
    """,
]


def _existing_project_and_org(conn):
    """Reuse an already-seeded project/client/site from the staging DB so we
    don't need to activate org write scope just to seed a work_package."""
    row = conn.execute(
        text(
            "SELECT project_id, client_id, site_id "
            "FROM work.work_packages LIMIT 1"
        )
    ).fetchone()
    assert row is not None, (
        "Integration smoke requires at least one pre-existing work.work_packages "
        "row to source a valid (project_id, client_id, site_id) triple."
    )
    return row


def _seed_work_rows(conn, project_id, client_id, site_id):
    conn.execute(
        text(
            """
            INSERT INTO work.work_packages
              (work_package_id, project_id, work_package_code, title, work_type,
               client_id, site_id, assigned_crew_id)
            VALUES
              (:wp_pop, :pid, 'WP-012G-POP', 'Smoke 012g populated WP',
               'testing', :cid, :sid, :crew_a),
              (:wp_nul, :pid, 'WP-012G-NUL', 'Smoke 012g null-fk WP',
               'testing', :cid, :sid, NULL)
            ON CONFLICT (work_package_id) DO NOTHING
            """
        ),
        dict(
            wp_pop=WP_POPULATED, wp_nul=WP_NULLFK,
            pid=project_id, cid=client_id, sid=site_id,
            crew_a=CREW_ALPHA,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.assignments
              (assignment_id, work_package_id, employee_id, crew_id, assignment_role)
            VALUES
              (:a_pop, :wp_pop, :emp, :crew_b, 'primary'),
              (:a_nul, :wp_pop, NULL, NULL, 'support')
            ON CONFLICT (assignment_id) DO NOTHING
            """
        ),
        dict(
            a_pop=ASG_POPULATED, a_nul=ASG_NULLFK,
            wp_pop=WP_POPULATED, emp=EMPLOYEE_GRACE, crew_b=CREW_BETA,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.execution_issues
              (execution_issue_id, work_package_id, issue_type, severity, summary,
               reported_by, assigned_to)
            VALUES
              (:ei_pop, :wp_pop, 'safety_hold', 'major',
               'Smoke 012g populated EI', :u_rep, :u_asn),
              (:ei_nul, :wp_pop, 'test_failure', 'minor',
               'Smoke 012g null-fk EI',  NULL,   NULL)
            ON CONFLICT (execution_issue_id) DO NOTHING
            """
        ),
        dict(
            ei_pop=EI_POPULATED, ei_nul=EI_NULLFK,
            wp_pop=WP_POPULATED, u_rep=USER_REPORTER, u_asn=USER_ASSIGNEE,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.progress_snapshots
              (progress_snapshot_id, project_id, work_package_id,
               snapshot_period_start, snapshot_period_end, approved_by)
            VALUES
              (:ps_pop, :pid, :wp_pop, DATE '2026-04-01', DATE '2026-04-14', :u_app),
              (:ps_nul, :pid, :wp_pop, DATE '2026-04-01', DATE '2026-04-14', NULL)
            ON CONFLICT (progress_snapshot_id) DO NOTHING
            """
        ),
        dict(
            ps_pop=PS_POPULATED, ps_nul=PS_NULLFK,
            pid=project_id, wp_pop=WP_POPULATED, u_app=USER_APPROVER,
        ),
    )


def _cleanup(conn):
    # Children first, then parents.
    conn.execute(text("DELETE FROM work.progress_snapshots "
                      "WHERE progress_snapshot_id IN (:a, :b)"),
                 dict(a=PS_POPULATED, b=PS_NULLFK))
    conn.execute(text("DELETE FROM work.execution_issues "
                      "WHERE execution_issue_id IN (:a, :b)"),
                 dict(a=EI_POPULATED, b=EI_NULLFK))
    conn.execute(text("DELETE FROM work.assignments "
                      "WHERE assignment_id IN (:a, :b)"),
                 dict(a=ASG_POPULATED, b=ASG_NULLFK))
    conn.execute(text("DELETE FROM work.work_packages "
                      "WHERE work_package_id IN (:a, :b)"),
                 dict(a=WP_POPULATED, b=WP_NULLFK))
    conn.execute(text("DELETE FROM identity.employees WHERE employee_id = :e"),
                 dict(e=EMPLOYEE_GRACE))
    conn.execute(text("DELETE FROM identity.crews "
                      "WHERE crew_id IN (:a, :b)"),
                 dict(a=CREW_ALPHA, b=CREW_BETA))
    conn.execute(text("DELETE FROM identity.users "
                      "WHERE user_id IN (:a, :b, :c)"),
                 dict(a=USER_REPORTER, b=USER_ASSIGNEE, c=USER_APPROVER))


@pytest.fixture(scope="module")
def integration_engine():
    engine = create_engine(_DB_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def seeded_db(integration_engine):
    SessionLocal = sessionmaker(bind=integration_engine, autoflush=False,
                                autocommit=False, future=True)
    with integration_engine.begin() as conn:
        project_id, client_id, site_id = _existing_project_and_org(conn)
        for stmt in SEED_STATEMENTS:
            conn.execute(
                text(stmt),
                dict(
                    u_rep=USER_REPORTER, u_asn=USER_ASSIGNEE, u_app=USER_APPROVER,
                    n_rep=REPORTER_NAME, n_asn=ASSIGNEE_NAME, n_app=APPROVER_NAME,
                    c_a=CREW_ALPHA, c_b=CREW_BETA,
                    n_a=CREW_ALPHA_NAME, n_b=CREW_BETA_NAME,
                    e_grace=EMPLOYEE_GRACE,
                ),
            )
        _seed_work_rows(conn, project_id, client_id, site_id)

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
# Tests — real-PG end-to-end materialization of the six *_name fields
# ---------------------------------------------------------------------------

def _first_matching(rows, predicate):
    for r in rows:
        if predicate(r):
            return r
    return None


class TestWorkPackageIdentityRead:

    def test_populated_assigned_crew_materializes(self, client):
        resp = client.get(
            f"/api/v1/work/work-packages/{WP_POPULATED}"
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["work_package_id"] == WP_POPULATED
        assert body["assigned_crew_id"] == CREW_ALPHA
        assert body["assigned_crew_name"] == CREW_ALPHA_NAME

    def test_null_fk_returns_none_name(self, client):
        resp = client.get(
            f"/api/v1/work/work-packages/{WP_NULLFK}"
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["assigned_crew_id"] is None
        assert body["assigned_crew_name"] is None

    def test_list_surfaces_both_rows_with_correct_names(self, client):
        # Request a page big enough to guarantee we see both smoke rows.
        resp = client.get("/api/v1/work/work-packages?limit=50&offset=0")
        assert resp.status_code == 200
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("work_package_id") == WP_POPULATED)
        nul = _first_matching(rows, lambda r: r.get("work_package_id") == WP_NULLFK)
        assert pop is not None, "Populated smoke WP not surfaced in list response"
        assert nul is not None, "Null-FK smoke WP not surfaced in list response"
        assert pop["assigned_crew_name"] == CREW_ALPHA_NAME
        assert nul["assigned_crew_name"] is None


class TestAssignmentIdentityRead:

    def test_populated_assignment_materializes_both_names(self, client):
        resp = client.get(
            f"/api/v1/work/assignments?work_package_id={WP_POPULATED}&limit=50"
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("assignment_id") == ASG_POPULATED)
        assert pop is not None
        assert pop["employee_id"] == EMPLOYEE_GRACE
        assert pop["crew_id"]     == CREW_BETA
        assert pop["employee_name"] == EMPLOYEE_NAME
        assert pop["crew_name"]     == CREW_BETA_NAME

    def test_null_fk_assignment_returns_none_names(self, client):
        resp = client.get(
            f"/api/v1/work/assignments?work_package_id={WP_POPULATED}&limit=50"
        )
        assert resp.status_code == 200
        rows = resp.json()
        nul = _first_matching(rows, lambda r: r.get("assignment_id") == ASG_NULLFK)
        assert nul is not None
        assert nul["employee_id"] is None
        assert nul["crew_id"]     is None
        assert nul["employee_name"] is None
        assert nul["crew_name"]     is None


class TestExecutionIssueIdentityRead:

    def test_populated_execution_issue_materializes_both_names(self, client):
        resp = client.get(
            f"/api/v1/work/execution-issues?work_package_id={WP_POPULATED}&limit=50"
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("execution_issue_id") == EI_POPULATED)
        assert pop is not None
        assert pop["reported_by"] == USER_REPORTER
        assert pop["assigned_to"] == USER_ASSIGNEE
        assert pop["reported_by_name"] == REPORTER_NAME
        assert pop["assigned_to_name"] == ASSIGNEE_NAME

    def test_null_fk_execution_issue_returns_none_names(self, client):
        resp = client.get(
            f"/api/v1/work/execution-issues?work_package_id={WP_POPULATED}&limit=50"
        )
        rows = resp.json()
        nul = _first_matching(rows, lambda r: r.get("execution_issue_id") == EI_NULLFK)
        assert nul is not None
        assert nul["reported_by"] is None
        assert nul["assigned_to"] is None
        assert nul["reported_by_name"] is None
        assert nul["assigned_to_name"] is None


class TestProgressSnapshotIdentityRead:

    def test_populated_snapshot_materializes_approver_name(self, client):
        resp = client.get(
            f"/api/v1/work/progress-snapshots?work_package_id={WP_POPULATED}&limit=50"
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("progress_snapshot_id") == PS_POPULATED)
        assert pop is not None
        assert pop["approved_by"] == USER_APPROVER
        assert pop["approved_by_name"] == APPROVER_NAME

    def test_null_fk_snapshot_returns_none_name(self, client):
        resp = client.get(
            f"/api/v1/work/progress-snapshots?work_package_id={WP_POPULATED}&limit=50"
        )
        rows = resp.json()
        nul = _first_matching(rows, lambda r: r.get("progress_snapshot_id") == PS_NULLFK)
        assert nul is not None
        assert nul["approved_by"] is None
        assert nul["approved_by_name"] is None


# ---------------------------------------------------------------------------
# Boundary confirmation — still read-surface only
# ---------------------------------------------------------------------------

class TestBoundaryConfirmation:
    """Re-assert packet-012f boundary (endpoint inventory) against the real-PG
    runtime path to prove no drift was introduced by the smoke addition."""

    def test_work_paths_still_fifteen(self, client):
        # Packet 015 added PATCH /assignments/{assignment_id} (→ 12),
        # packet 016 added PATCH /dependencies/{dependency_id} (→ 13),
        # packet 017 added PATCH /execution-issues/{execution_issue_id}
        # (→ 14), and packet 018 added PATCH
        # /progress-snapshots/{progress_snapshot_id} only — the POST
        # /progress-snapshots handler reuses the path already present
        # from the 010b GET, so the overall path count increments by
        # exactly one (→ 15).
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        work_paths = sorted(p for p in paths if p.startswith("/api/v1/work"))
        assert len(work_paths) == 15, work_paths
