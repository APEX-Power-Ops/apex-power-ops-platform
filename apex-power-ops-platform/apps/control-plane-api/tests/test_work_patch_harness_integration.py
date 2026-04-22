"""
PM/Work Domain — Shared PATCH Harness Integration Smoke
========================================================
Packet: 2026-04-16-pm-schema-019i (executed jointly with packet 019)

Real-PostgreSQL variant of the unit harness in
``test_work_patch_harness``.  Exercises the three standardised PATCH
outcomes (200 empty-body no-op / 404 nonexistent target / 422 invalid
FK) against every live PATCH route on the PM surface:

    FastAPI TestClient
       → PATCH /api/v1/work/projects/{project_id}                     (packet 011f)
       → PATCH /api/v1/work/work-packages/{work_package_id}           (packet 013)
       → PATCH /api/v1/work/tasks/{task_id}                           (packet 014)
       → PATCH /api/v1/work/assignments/{assignment_id}               (packet 015)
       → PATCH /api/v1/work/dependencies/{dependency_id}              (packet 016)
       → PATCH /api/v1/work/execution-issues/{execution_issue_id}     (packet 017)
       → PATCH /api/v1/work/progress-snapshots/{progress_snapshot_id} (packet 018)

The harness asserts that every PATCH endpoint honours the uniform
contract the front-end relies on.  Entity-level write-integration
modules (``test_work_project_write_integration`` through
``test_work_progress_snapshot_write_integration``) remain authoritative
for field-level behaviour; this smoke only pins the cross-cutting
shape.

Skips cleanly when ``APEX_INTEGRATION_DATABASE_URL`` (or
``DATABASE_URL``) is unset or points at an unreachable host — mirrors
the skip-guard pattern used by packets 012g / 012i / 013i / 014i /
015i / 016i / 017i / 018i.

Seed + cleanup use the sentinel code prefix ``SMK19I-`` and the sentinel
UUID prefix ``019b0xxx-0000-4000-8000-`` ("i" is not a valid hex
character — ``019b`` is used in its place, matching 018b's convention).
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        return None
    return url


def _db_is_reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        parsed = urlparse(
            url.replace("postgresql+psycopg2://", "postgresql://")
        )
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
        "PATCH harness smoke skipped: set APEX_INTEGRATION_DATABASE_URL "
        "to a PostgreSQL URL hosting the work+org+identity schemas."
    ),
)

if _DB_URL is not None and not _db_is_reachable(_DB_URL):
    pytestmark = pytest.mark.skip(
        reason=(
            f"PATCH harness smoke skipped: PostgreSQL at {_DB_URL!s} is "
            "not reachable from this executor."
        )
    )


# ---------------------------------------------------------------------------
# Deferred imports
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if _DB_URL is not None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from config import get_db  # type: ignore
    from fastapi.testclient import TestClient
    from main import app  # type: ignore


# ---------------------------------------------------------------------------
# Sentinels
# ---------------------------------------------------------------------------

CLIENT_ID           = "019b0001-0000-4000-8000-000000000001"
SITE_ID             = "019b0002-0000-4000-8000-000000000001"
PROJECT_ID          = "019b0003-0000-4000-8000-000000000001"
WORK_PACKAGE_ID     = "019b0004-0000-4000-8000-000000000001"
TASK_ID             = "019b0005-0000-4000-8000-000000000001"
PRED_TASK_ID        = "019b0005-0000-4000-8000-000000000002"
SUCC_TASK_ID        = "019b0005-0000-4000-8000-000000000003"
DEPENDENCY_ID       = "019b0006-0000-4000-8000-000000000001"
ASSIGNMENT_ID       = "019b0007-0000-4000-8000-000000000001"
EXECUTION_ISSUE_ID  = "019b0008-0000-4000-8000-000000000001"
SNAPSHOT_ID         = "019b0009-0000-4000-8000-000000000001"

NONEXISTENT_ID = "019b0099-0000-4000-8000-000000000099"

NONEXISTENT_PROJECT_ID = "019b0091-0000-4000-8000-000000000091"
NONEXISTENT_WP_ID      = "019b0092-0000-4000-8000-000000000092"
NONEXISTENT_TASK_ID    = "019b0093-0000-4000-8000-000000000093"
NONEXISTENT_CLIENT_ID  = "019b0094-0000-4000-8000-000000000094"


# ---------------------------------------------------------------------------
# Seed / cleanup
# ---------------------------------------------------------------------------

def _seed(conn):
    conn.execute(text("""
        INSERT INTO org.clients (client_id, client_code, name, is_active)
        VALUES (:cid, 'SMK19I-CLIENT', 'Smoke Client 19i', true)
        ON CONFLICT (client_id) DO NOTHING
    """), dict(cid=CLIENT_ID))
    conn.execute(text("""
        INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
        VALUES (:sid, :cid, 'SMK19I-SITE', 'Smoke Site 19i', true)
        ON CONFLICT (site_id) DO NOTHING
    """), dict(sid=SITE_ID, cid=CLIENT_ID))
    conn.execute(text("""
        INSERT INTO work.projects
            (project_id, project_code, title, client_id, site_id)
        VALUES (:pid, 'SMK19I-PRJ', 'Smoke Project 19i', :cid, :sid)
        ON CONFLICT (project_id) DO NOTHING
    """), dict(pid=PROJECT_ID, cid=CLIENT_ID, sid=SITE_ID))
    conn.execute(text("""
        INSERT INTO work.work_packages
            (work_package_id, project_id, work_package_code, title,
             work_type, client_id, site_id)
        VALUES (:wpid, :pid, 'SMK19I-WP', 'Smoke WP 19i',
                'testing', :cid, :sid)
        ON CONFLICT (work_package_id) DO NOTHING
    """), dict(
        wpid=WORK_PACKAGE_ID, pid=PROJECT_ID, cid=CLIENT_ID, sid=SITE_ID,
    ))
    for tid, tcode in (
        (TASK_ID, "SMK19I-TASK-1"),
        (PRED_TASK_ID, "SMK19I-TASK-P"),
        (SUCC_TASK_ID, "SMK19I-TASK-S"),
    ):
        conn.execute(text("""
            INSERT INTO work.tasks
                (task_id, work_package_id, task_code, title, task_type)
            VALUES (:tid, :wpid, :tcode, 'Smoke Task 19i', 'task')
            ON CONFLICT (task_id) DO NOTHING
        """), dict(tid=tid, wpid=WORK_PACKAGE_ID, tcode=tcode))
    conn.execute(text("""
        INSERT INTO work.dependencies
            (dependency_id, predecessor_task_id, successor_task_id,
             relationship_type, source_system, is_active)
        VALUES (:did, :pred, :succ, 'FS', 'manual', true)
        ON CONFLICT (dependency_id) DO NOTHING
    """), dict(did=DEPENDENCY_ID, pred=PRED_TASK_ID, succ=SUCC_TASK_ID))
    conn.execute(text("""
        INSERT INTO work.assignments
            (assignment_id, work_package_id, assignment_role)
        VALUES (:aid, :wpid, 'lead')
        ON CONFLICT (assignment_id) DO NOTHING
    """), dict(aid=ASSIGNMENT_ID, wpid=WORK_PACKAGE_ID))
    conn.execute(text("""
        INSERT INTO work.execution_issues
            (execution_issue_id, work_package_id, issue_type,
             severity, status, summary)
        VALUES (:iid, :wpid, 'other', 'minor', 'open', 'Smoke Issue 19i')
        ON CONFLICT (execution_issue_id) DO NOTHING
    """), dict(iid=EXECUTION_ISSUE_ID, wpid=WORK_PACKAGE_ID))
    conn.execute(text("""
        INSERT INTO work.progress_snapshots
            (progress_snapshot_id, project_id,
             snapshot_period_start, snapshot_period_end)
        VALUES (:sid, :pid, DATE '2026-04-01', DATE '2026-04-14')
        ON CONFLICT (progress_snapshot_id) DO NOTHING
    """), dict(sid=SNAPSHOT_ID, pid=PROJECT_ID))


def _teardown(conn):
    for tbl, pk, ident in (
        ("work.progress_snapshots", "progress_snapshot_id", SNAPSHOT_ID),
        ("work.execution_issues", "execution_issue_id", EXECUTION_ISSUE_ID),
        ("work.assignments", "assignment_id", ASSIGNMENT_ID),
        ("work.dependencies", "dependency_id", DEPENDENCY_ID),
    ):
        conn.execute(
            text(f"DELETE FROM {tbl} WHERE {pk} = :v"), dict(v=ident),
        )
    for tid in (TASK_ID, PRED_TASK_ID, SUCC_TASK_ID):
        conn.execute(
            text("DELETE FROM work.tasks WHERE task_id = :v"), dict(v=tid),
        )
    conn.execute(
        text("DELETE FROM work.work_packages WHERE work_package_id = :v"),
        dict(v=WORK_PACKAGE_ID),
    )
    conn.execute(
        text("DELETE FROM work.projects WHERE project_id = :v"),
        dict(v=PROJECT_ID),
    )
    conn.execute(
        text("DELETE FROM org.sites WHERE site_id = :v"), dict(v=SITE_ID),
    )
    conn.execute(
        text("DELETE FROM org.clients WHERE client_id = :v"),
        dict(v=CLIENT_ID),
    )


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    engine = create_engine(_DB_URL, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with engine.begin() as conn:
        _seed(conn)

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
        with engine.begin() as conn:
            _teardown(conn)
        engine.dispose()


# ---------------------------------------------------------------------------
# Contract descriptors (paired with the unit harness)
# ---------------------------------------------------------------------------

PATCH_CASES = [
    (
        "/api/v1/work/projects",
        PROJECT_ID,
        {"client_id": NONEXISTENT_CLIENT_ID},
        "client_id",
    ),
    (
        "/api/v1/work/work-packages",
        WORK_PACKAGE_ID,
        {"project_id": NONEXISTENT_PROJECT_ID},
        "project_id",
    ),
    (
        "/api/v1/work/tasks",
        TASK_ID,
        {"work_package_id": NONEXISTENT_WP_ID},
        "work_package_id",
    ),
    (
        "/api/v1/work/dependencies",
        DEPENDENCY_ID,
        {"predecessor_task_id": NONEXISTENT_TASK_ID},
        "predecessor_task_id",
    ),
    (
        "/api/v1/work/assignments",
        ASSIGNMENT_ID,
        {"work_package_id": NONEXISTENT_WP_ID},
        "work_package_id",
    ),
    (
        "/api/v1/work/execution-issues",
        EXECUTION_ISSUE_ID,
        {"work_package_id": NONEXISTENT_WP_ID},
        "work_package_id",
    ),
    (
        "/api/v1/work/progress-snapshots",
        SNAPSHOT_ID,
        {"project_id": NONEXISTENT_PROJECT_ID},
        "project_id",
    ),
]


# ---------------------------------------------------------------------------
# Standardised contract
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entity_path,existing_id,_invalid_patch,_invalid_field",
    PATCH_CASES,
    ids=[c[0] for c in PATCH_CASES],
)
def test_patch_empty_body_returns_200(
    client, entity_path, existing_id, _invalid_patch, _invalid_field,
):
    resp = client.patch(f"{entity_path}/{existing_id}", json={})
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
    client, entity_path, _existing_id, _invalid_patch, _invalid_field,
):
    resp = client.patch(f"{entity_path}/{NONEXISTENT_ID}", json={})
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
    client, entity_path, existing_id, invalid_patch, invalid_field,
):
    resp = client.patch(
        f"{entity_path}/{existing_id}", json=invalid_patch,
    )
    assert resp.status_code == 422, (
        f"{entity_path}: expected 422 on invalid FK, got "
        f"{resp.status_code} — body: {resp.text[:200]}"
    )
    body = resp.json()
    assert "errors" in body
    assert invalid_field in body["errors"]
