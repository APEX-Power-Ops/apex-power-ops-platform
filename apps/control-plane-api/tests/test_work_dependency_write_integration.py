"""
PM/Work Domain — Dependency Write Surface Integration Smoke
===========================================================
Packet: 2026-04-15-pm-schema-016i (executed jointly with packet 016)

Locks in the real-PostgreSQL runtime behavior of the dependency POST
and PATCH surface wired by packet 016.  Exercises the existing write
handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → POST  /api/v1/work/dependencies              (packet 016)
       → PATCH /api/v1/work/dependencies/{id}         (packet 016)
          → routes.py handler
             → services.work.mutations
                (_validate_dependency_references:
                 predecessor_task_id + successor_task_id
                 intra-work FKs; merged self-cycle check on
                 the effective (post-patch) pair)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * POST with valid predecessor + successor + default (FS) relationship
    returns 201 and a materialized DependencyRead whose id is the
    inserted row.
  * POST accepts each DependencyType (FS / SS / SF / FF) end-to-end.
  * POST with an unknown predecessor_task_id returns 422 with a merged
    error dict containing predecessor_task_id.
  * POST with an unknown successor_task_id returns 422 with
    successor_task_id in errors.
  * POST with both FKs bad returns 422 with both fields in the merged
    error dict.
  * POST with predecessor == successor (self-cycle) returns 422 at the
    Pydantic @model_validator boundary, before any DB round-trip.
  * PATCH with valid fields returns 200 and the updated row.
  * PATCH relationship_type swap returns 200.
  * PATCH with an unknown predecessor_task_id returns 422.
  * PATCH against a random non-existent dependency_id returns 404.
  * PATCH with empty body returns 200 (idempotent no-op).
  * PATCH that would collapse the effective pair to a self-cycle (patch
    predecessor to match stored successor, or vice versa) returns 422
    with both field names in the merged error dict.
  * Non-dependency read-only PM-write endpoints (execution issues,
    progress snapshots) remain 405 on POST (sanity boundary).

Design constraints (packet 016 hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 016's dependency-only
    scope — seed supporting rows (client, site, project, work_package,
    predecessor_task, successor_task, third_task) are inserted
    directly via SQLAlchemy ``text()`` statements, not through the
    write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or
    `DATABASE_URL`) is absent or unreachable, the whole module is
    skipped rather than failing CI.  Mirrors packets 012g, 012i,
    013i, 014i, and 015i.

Seeding strategy:
  - All fixtures use the sentinel code prefix ``SMK16I-`` and sentinel
    UUID prefix ``016b0xxx-0000-4000-8000-`` ("i" is not a valid hex
    character — ``016b`` is used in its place, matching the convention
    established by packets 012i / 013i / 014i / 015i).
  - Teardown deletes only the fixture rows (including any dependency
    rows created by the POST calls), leaving existing staging data
    untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_dependency_write_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packets 012g, 012i, 013i, 014i, 015i)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Dependency write surface depends on PostgreSQL ENUMs; skip sqlite.
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
# NOTE: "i" is not a valid hex character, so packet 016's integration
# smoke adopts the "016b" prefix convention matching packets 012i /
# 013i / 014i / 015i.  All fixture IDs live in the 016b0xxx range,
# distinct from 015b0xxx used by packet 015i's assignment integration
# smoke.
# ---------------------------------------------------------------------------

CLIENT_ID          = "016b0001-0000-4000-8000-000000000001"
SITE_ID            = "016b0002-0000-4000-8000-000000000001"
PROJECT_ID         = "016b0003-0000-4000-8000-000000000001"
WORK_PACKAGE_ID    = "016b0004-0000-4000-8000-000000000001"
PREDECESSOR_TASK_ID = "016b0005-0000-4000-8000-000000000001"
SUCCESSOR_TASK_ID   = "016b0005-0000-4000-8000-000000000002"
THIRD_TASK_ID       = "016b0005-0000-4000-8000-000000000003"

# A random UUID that will never exist — used for 404 and 422 assertions.
NONEXISTENT_DEPENDENCY_ID = "016b0099-0000-4000-8000-000000000099"
NONEXISTENT_TASK_ID       = "016b0097-0000-4000-8000-000000000099"

CLIENT_NAME    = "Smoke Client 016i"
SITE_NAME      = "Smoke Site 016i"
PROJECT_CODE   = "SMK16I-PRJ-1"
PROJECT_TITLE  = "Smoke Project 016i"
WP_CODE        = "SMK16I-WP-1"
WP_TITLE       = "Smoke WP 016i"
PRED_TASK_CODE = "SMK16I-TASK-PRED"
PRED_TASK_TITLE = "Smoke Predecessor 016i"
SUCC_TASK_CODE = "SMK16I-TASK-SUCC"
SUCC_TASK_TITLE = "Smoke Successor 016i"
THIRD_TASK_CODE = "SMK16I-TASK-THIRD"
THIRD_TASK_TITLE = "Smoke Third 016i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL (existing tables only — no schema changes)
# ---------------------------------------------------------------------------

def _seed_supporting_rows(conn):
    """Insert the minimum org + work parent rows the dependency write
    surface needs to validate FK references end to end.  Dependencies
    validate two references at the API boundary —
    predecessor_task_id and successor_task_id, both against work.tasks
    — so at least two sibling task rows are required.  A third task is
    seeded to support the PATCH-side valid-update scenarios and the
    effective-pair self-cycle assertions.
    """
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK16I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK16I-SITE-1', :sname, true)
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
    # Predecessor, successor, and third task — all siblings under the
    # same work_package so the dependency natural key test bench has
    # three distinct valid task references to mix and match.
    for tid, tcode, ttitle in (
        (PREDECESSOR_TASK_ID, PRED_TASK_CODE, PRED_TASK_TITLE),
        (SUCCESSOR_TASK_ID, SUCC_TASK_CODE, SUCC_TASK_TITLE),
        (THIRD_TASK_ID, THIRD_TASK_CODE, THIRD_TASK_TITLE),
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

    Sweep up every dependency row our POST calls created using the
    three seeded task IDs as the discriminator (dependencies don't
    carry a code column, so we match on predecessor_task_id /
    successor_task_id of the smoke fixtures).
    """
    conn.execute(
        text(
            """
            DELETE FROM work.dependencies
            WHERE predecessor_task_id IN (:p, :s, :t)
               OR successor_task_id   IN (:p, :s, :t)
            """
        ),
        dict(p=PREDECESSOR_TASK_ID, s=SUCCESSOR_TASK_ID, t=THIRD_TASK_ID),
    )
    conn.execute(
        text(
            """
            DELETE FROM work.tasks
            WHERE task_id IN (:p, :s, :t)
            """
        ),
        dict(p=PREDECESSOR_TASK_ID, s=SUCCESSOR_TASK_ID, t=THIRD_TASK_ID),
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


@pytest.fixture()
def clean_dependencies(integration_engine):
    """Remove any leftover dependency rows before each test to keep the
    (predecessor, successor, relationship_type) unique constraint from
    colliding across test invocations in the same module run."""
    with integration_engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM work.dependencies
                WHERE predecessor_task_id IN (:p, :s, :t)
                   OR successor_task_id   IN (:p, :s, :t)
                """
            ),
            dict(p=PREDECESSOR_TASK_ID, s=SUCCESSOR_TASK_ID, t=THIRD_TASK_ID),
        )
    yield
    with integration_engine.begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM work.dependencies
                WHERE predecessor_task_id IN (:p, :s, :t)
                   OR successor_task_id   IN (:p, :s, :t)
                """
            ),
            dict(p=PREDECESSOR_TASK_ID, s=SUCCESSOR_TASK_ID, t=THIRD_TASK_ID),
        )


# ---------------------------------------------------------------------------
# Tests — real-PG end-to-end coverage of the dependency write surface
# ---------------------------------------------------------------------------

class TestDependencyCreateIntegration:
    """POST /api/v1/work/dependencies against the live PG runtime."""

    def test_create_with_defaults_returns_201(self, client, clean_dependencies):
        payload = {
            "predecessor_task_id": PREDECESSOR_TASK_ID,
            "successor_task_id": SUCCESSOR_TASK_ID,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["predecessor_task_id"] == PREDECESSOR_TASK_ID
        assert data["successor_task_id"] == SUCCESSOR_TASK_ID
        # Server defaults apply
        assert data["relationship_type"] == "FS"
        assert data["source_system"] == "manual"
        assert data["is_active"] is True
        assert data["created_from_source"] == "manual"
        # A new UUID is assigned by the DB default
        assert data["dependency_id"]

    @pytest.mark.parametrize("rel_type", ["FS", "SS", "SF", "FF"])
    def test_create_accepts_all_dependency_types(
        self, client, clean_dependencies, rel_type
    ):
        payload = {
            "predecessor_task_id": PREDECESSOR_TASK_ID,
            "successor_task_id": SUCCESSOR_TASK_ID,
            "relationship_type": rel_type,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 201, resp.text
        assert resp.json()["relationship_type"] == rel_type

    def test_create_with_full_payload_persists_all_fields(
        self, client, clean_dependencies
    ):
        payload = {
            "predecessor_task_id": PREDECESSOR_TASK_ID,
            "successor_task_id": SUCCESSOR_TASK_ID,
            "relationship_type": "SS",
            "lag_hours": "2.50",
            "source_system": "p6_import",
            "is_active": False,
            "created_from_source": "p6_import",
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["predecessor_task_id"] == PREDECESSOR_TASK_ID
        assert data["successor_task_id"] == SUCCESSOR_TASK_ID
        assert data["relationship_type"] == "SS"
        assert data["lag_hours"] == "2.50"
        assert data["source_system"] == "p6_import"
        assert data["is_active"] is False
        assert data["created_from_source"] == "p6_import"

    def test_create_rejects_unknown_predecessor_with_merged_422(
        self, client, clean_dependencies
    ):
        """Intra-work FK validation fires against the live work.tasks."""
        payload = {
            "predecessor_task_id": NONEXISTENT_TASK_ID,
            "successor_task_id": SUCCESSOR_TASK_ID,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]

    def test_create_rejects_unknown_successor_with_merged_422(
        self, client, clean_dependencies
    ):
        payload = {
            "predecessor_task_id": PREDECESSOR_TASK_ID,
            "successor_task_id": NONEXISTENT_TASK_ID,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "successor_task_id" in data["errors"]

    def test_create_rejects_both_bad_fks_with_merged_422(
        self, client, clean_dependencies
    ):
        """Both bad FKs must be reported in a single merged error dict
        (merged-error behavior inherited from packet 016's
        _validate_dependency_references helper)."""
        payload = {
            "predecessor_task_id": NONEXISTENT_TASK_ID,
            "successor_task_id": NONEXISTENT_TASK_ID,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        # Note: predecessor == successor == NONEXISTENT_TASK_ID would be
        # a self-cycle by strict equality, which the Pydantic validator
        # catches first.  Use distinct unknown IDs to probe the merged
        # FK-error path instead.
        assert resp.status_code == 422
        # With identical unknown IDs, we may hit the self-cycle guard
        # before the FK check — accept either detail shape.
        payload2 = {
            "predecessor_task_id": NONEXISTENT_TASK_ID,
            "successor_task_id": "016b0097-0000-4000-8000-000000000098",
        }
        resp2 = client.post("/api/v1/work/dependencies", json=payload2)
        assert resp2.status_code == 422, resp2.text
        data = resp2.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]

    def test_create_rejects_self_cycle_at_pydantic_boundary(
        self, client, clean_dependencies
    ):
        """predecessor == successor must 422 at the @model_validator
        layer before any DB round-trip, mirroring the DDL no-self-cycle
        intent.  The error lives in the Pydantic detail list, not the
        OrgValidationError 'errors' dict."""
        payload = {
            "predecessor_task_id": PREDECESSOR_TASK_ID,
            "successor_task_id": PREDECESSOR_TASK_ID,
        }
        resp = client.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422, resp.text
        rendered = str(resp.json()).lower()
        assert "different tasks" in rendered


class TestDependencyPatchIntegration:
    """PATCH /api/v1/work/dependencies/{id} against the live PG runtime."""

    def test_patch_relationship_type_returns_200(
        self, client, clean_dependencies
    ):
        # First create a row to patch
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]
        assert created.json()["relationship_type"] == "FS"

        patched = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"relationship_type": "SS"},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["dependency_id"] == dependency_id
        assert data["relationship_type"] == "SS"
        # Other fields should be unchanged
        assert data["predecessor_task_id"] == PREDECESSOR_TASK_ID
        assert data["successor_task_id"] == SUCCESSOR_TASK_ID

    def test_patch_lag_hours_returns_200(self, client, clean_dependencies):
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        patched = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"lag_hours": "4.00"},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["lag_hours"] == "4.00"

    def test_patch_is_active_returns_200(self, client, clean_dependencies):
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        patched = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"is_active": False},
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["is_active"] is False

    def test_patch_predecessor_to_valid_third_task_returns_200(
        self, client, clean_dependencies
    ):
        """Swap predecessor to the third task; stored successor stays
        SUCCESSOR_TASK_ID, so the effective pair is distinct."""
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        patched = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"predecessor_task_id": THIRD_TASK_ID},
        )
        assert patched.status_code == 200, patched.text
        data = patched.json()
        assert data["predecessor_task_id"] == THIRD_TASK_ID
        assert data["successor_task_id"] == SUCCESSOR_TASK_ID

    def test_patch_nonexistent_dependency_returns_404(
        self, client, clean_dependencies
    ):
        resp = client.patch(
            f"/api/v1/work/dependencies/{NONEXISTENT_DEPENDENCY_ID}",
            json={"relationship_type": "SS"},
        )
        assert resp.status_code == 404, resp.text

    def test_patch_rejects_unknown_predecessor_with_merged_422(
        self, client, clean_dependencies
    ):
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        resp = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"predecessor_task_id": NONEXISTENT_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]

    def test_patch_rejects_unknown_successor_with_merged_422(
        self, client, clean_dependencies
    ):
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        resp = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"successor_task_id": NONEXISTENT_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "successor_task_id" in data["errors"]

    def test_patch_effective_pair_self_cycle_predecessor_to_stored_successor(
        self, client, clean_dependencies
    ):
        """Stored successor is SUCCESSOR_TASK_ID; patching predecessor
        to that same task collapses the effective pair to a self-cycle.
        The service-layer merged check must 422 with both field names
        in the errors dict."""
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        resp = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"predecessor_task_id": SUCCESSOR_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]
        rendered = str(data).lower()
        assert "different tasks" in rendered

    def test_patch_effective_pair_self_cycle_successor_to_stored_predecessor(
        self, client, clean_dependencies
    ):
        """Mirror: stored predecessor is PREDECESSOR_TASK_ID; patching
        successor to that same task collapses the effective pair to a
        self-cycle."""
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        resp = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}",
            json={"successor_task_id": PREDECESSOR_TASK_ID},
        )
        assert resp.status_code == 422, resp.text
        data = resp.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]

    def test_patch_empty_body_returns_200_unchanged(
        self, client, clean_dependencies
    ):
        created = client.post(
            "/api/v1/work/dependencies",
            json={
                "predecessor_task_id": PREDECESSOR_TASK_ID,
                "successor_task_id": SUCCESSOR_TASK_ID,
                "lag_hours": "1.00",
            },
        )
        assert created.status_code == 201, created.text
        dependency_id = created.json()["dependency_id"]

        resp = client.patch(
            f"/api/v1/work/dependencies/{dependency_id}", json={},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["dependency_id"] == dependency_id
        assert data["lag_hours"] == "1.00"


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
