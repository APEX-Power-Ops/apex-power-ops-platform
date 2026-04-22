"""
PM/Work Domain — Org-Joined Read Surface Integration Smoke
==========================================================
Packet: 2026-04-14-pm-schema-012i

Locks in the real-PostgreSQL runtime behavior of the org-joined
read surface wired by packet 012h.  Exercises the existing GET
handlers end-to-end against the live runtime path:

    FastAPI TestClient
       → /api/v1/work/<entity>
          → routes.py handler
             → services.work.queries (joinedload + hydrator)
                → SQLAlchemy Session → real PostgreSQL

Assertions:
  * `GET /api/v1/work/projects/{id}` returns rows where all four
    org-backed fields materialize from the live JOIN:
      - ProjectRead.client_name
      - ProjectRead.site_name
      - ProjectRead.business_unit_name
      - ProjectRead.contract_title
  * For a sibling project with nullable org FKs set to NULL
    (`business_unit_id`, `contract_id`), those two `*_name` /
    `*_title` fields remain ``None``.
  * For a sibling project whose contract row exists but whose
    `org.contracts.title` display column is NULL, `contract_title`
    is ``None`` (proves hydrator respects the joined-display-column
    null case, not just the FK-null case).
  * `GET /api/v1/work/work-packages/{id}` returns rows where the
    two org-backed fields materialize from the live JOIN:
      - WorkPackageRead.client_name
      - WorkPackageRead.site_name

Design constraints (packet 012i hard requirements):
  - No new endpoints, no new schemas, no new SQL / DDL / migrations.
  - No write-surface expansion beyond packet 011f's project-only
    scope — seed rows are inserted directly via SQLAlchemy ``text()``
    statements, not through the write API.
  - The module must degrade cleanly in environments without a
    reachable PostgreSQL: if `APEX_INTEGRATION_DATABASE_URL` (or
    `DATABASE_URL`) is absent or unreachable, the whole module is
    skipped rather than failing CI.
  - Mirrors packet 012g's skip-when-unreachable posture.

Seeding strategy:
  - All fixtures are tagged with the sentinel code prefix
    ``SMK12I-`` and sentinel UUID prefix ``012b0xxx-0000-4000-8000-``
    ("i" is not a valid hex character — ``012b`` is used in its
    place, matching the convention established during packet-012i
    live MCP seeding).
  - Teardown deletes only the fixture rows; existing staging data
    is left untouched.

Run (outside the sandbox) with:

    APEX_INTEGRATION_DATABASE_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/apex_pm_stage \\
    pytest tests/test_work_org_joined_read_integration.py -q
"""

from __future__ import annotations

import os
import socket
import sys
from typing import Optional
from urllib.parse import urlparse

import pytest


# ---------------------------------------------------------------------------
# Skip-when-unreachable guard (mirrors packet 012g)
# ---------------------------------------------------------------------------

def _resolve_integration_db_url() -> Optional[str]:
    url = (
        os.environ.get("APEX_INTEGRATION_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
    )
    if not url:
        return None
    if "sqlite" in url.lower():
        # Org-joined read surface depends on PostgreSQL ENUMs; skip sqlite.
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
        "PostgreSQL URL hosting the work+org schemas (e.g. apex_pm_stage)."
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
# Sentinel UUIDs + codes so fixtures are easy to clean up.
#
# NOTE: "i" is not a valid hex character, so the 012i packet adopts the
# "012b" prefix convention established during live MCP seeding.  All
# fixture IDs live in the 012b0xxx range, distinct from 012f0xxx used by
# packet 012g's identity smoke.
# ---------------------------------------------------------------------------

CLIENT_ID             = "012b0001-0000-4000-8000-000000000001"
SITE_ID               = "012b0002-0000-4000-8000-000000000001"
BU_ID                 = "012b0003-0000-4000-8000-000000000001"
CONTRACT_WITH_TITLE   = "012b0004-0000-4000-8000-000000000001"
CONTRACT_NULL_TITLE   = "012b0004-0000-4000-8000-000000000002"

PRJ_FULL              = "012b0005-0000-4000-8000-000000000001"
PRJ_NULL_OPT          = "012b0005-0000-4000-8000-000000000002"
PRJ_CTR_NULLTITLE     = "012b0005-0000-4000-8000-000000000003"

WP_POPULATED          = "012b0006-0000-4000-8000-000000000001"

CLIENT_NAME           = "Smoke Client 012i"
SITE_NAME             = "Smoke Site 012i"
BU_NAME               = "Smoke BU 012i"
CONTRACT_TITLE        = "Smoke Contract With Title 012i"


# ---------------------------------------------------------------------------
# Seed + cleanup SQL
# ---------------------------------------------------------------------------

def _seed_org_rows(conn):
    conn.execute(
        text(
            """
            INSERT INTO org.clients (client_id, client_code, name, is_active)
            VALUES (:cid, 'SMK12I-CLIENT-1', :cname, true)
            ON CONFLICT (client_id) DO NOTHING
            """
        ),
        dict(cid=CLIENT_ID, cname=CLIENT_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.sites (site_id, client_id, site_code, name, is_active)
            VALUES (:sid, :cid, 'SMK12I-SITE-1', :sname, true)
            ON CONFLICT (site_id) DO NOTHING
            """
        ),
        dict(sid=SITE_ID, cid=CLIENT_ID, sname=SITE_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.business_units
              (business_unit_id, code, name, is_active)
            VALUES (:bid, 'SMK12I-BU-1', :bname, true)
            ON CONFLICT (business_unit_id) DO NOTHING
            """
        ),
        dict(bid=BU_ID, bname=BU_NAME),
    )
    conn.execute(
        text(
            """
            INSERT INTO org.contracts
              (contract_id, client_id, contract_code, title, is_active)
            VALUES
              (:ctr_ok,   :cid, 'SMK12I-CTR-1', :ctitle, true),
              (:ctr_null, :cid, 'SMK12I-CTR-2', NULL,    true)
            ON CONFLICT (contract_id) DO NOTHING
            """
        ),
        dict(
            ctr_ok=CONTRACT_WITH_TITLE,
            ctr_null=CONTRACT_NULL_TITLE,
            cid=CLIENT_ID,
            ctitle=CONTRACT_TITLE,
        ),
    )


def _seed_work_rows(conn):
    conn.execute(
        text(
            """
            INSERT INTO work.projects
              (project_id, project_code, title,
               client_id, site_id, business_unit_id, contract_id)
            VALUES
              (:p_full,  'SMK12I-PRJ-FULL',
               'Smoke Project Full 012i',
               :cid, :sid, :bid, :ctr_ok),
              (:p_nul,   'SMK12I-PRJ-NULL-OPT',
               'Smoke Project Null Optionals 012i',
               :cid, :sid, NULL, NULL),
              (:p_ctrnt, 'SMK12I-PRJ-CTR-NULLTITLE',
               'Smoke Project Contract NullTitle 012i',
               :cid, :sid, :bid, :ctr_null)
            ON CONFLICT (project_id) DO NOTHING
            """
        ),
        dict(
            p_full=PRJ_FULL, p_nul=PRJ_NULL_OPT, p_ctrnt=PRJ_CTR_NULLTITLE,
            cid=CLIENT_ID, sid=SITE_ID, bid=BU_ID,
            ctr_ok=CONTRACT_WITH_TITLE, ctr_null=CONTRACT_NULL_TITLE,
        ),
    )
    conn.execute(
        text(
            """
            INSERT INTO work.work_packages
              (work_package_id, project_id, work_package_code, title, work_type,
               client_id, site_id)
            VALUES
              (:wp_pop, :p_full, 'SMK12I-WP-1',
               'Smoke WorkPackage 012i', 'testing', :cid, :sid)
            ON CONFLICT (work_package_id) DO NOTHING
            """
        ),
        dict(
            wp_pop=WP_POPULATED, p_full=PRJ_FULL,
            cid=CLIENT_ID, sid=SITE_ID,
        ),
    )


def _cleanup(conn):
    # Children first, then parents.
    conn.execute(
        text("DELETE FROM work.work_packages WHERE work_package_id = :w"),
        dict(w=WP_POPULATED),
    )
    conn.execute(
        text(
            "DELETE FROM work.projects "
            "WHERE project_id IN (:a, :b, :c)"
        ),
        dict(a=PRJ_FULL, b=PRJ_NULL_OPT, c=PRJ_CTR_NULLTITLE),
    )
    conn.execute(
        text(
            "DELETE FROM org.contracts "
            "WHERE contract_id IN (:a, :b)"
        ),
        dict(a=CONTRACT_WITH_TITLE, b=CONTRACT_NULL_TITLE),
    )
    conn.execute(
        text("DELETE FROM org.business_units WHERE business_unit_id = :b"),
        dict(b=BU_ID),
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
        _seed_org_rows(conn)
        _seed_work_rows(conn)

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
# Tests — real-PG end-to-end materialization of the six org-backed fields
# ---------------------------------------------------------------------------

def _first_matching(rows, predicate):
    for r in rows:
        if predicate(r):
            return r
    return None


class TestProjectOrgReadPopulated:
    """Project row with all four org FKs set + contract.title populated."""

    def test_get_materializes_all_four_org_fields(self, client):
        resp = client.get(f"/api/v1/work/projects/{PRJ_FULL}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["project_id"]         == PRJ_FULL
        assert body["client_id"]          == CLIENT_ID
        assert body["site_id"]            == SITE_ID
        assert body["business_unit_id"]   == BU_ID
        assert body["contract_id"]        == CONTRACT_WITH_TITLE
        assert body["client_name"]        == CLIENT_NAME
        assert body["site_name"]          == SITE_NAME
        assert body["business_unit_name"] == BU_NAME
        assert body["contract_title"]     == CONTRACT_TITLE

    def test_list_surfaces_populated_project(self, client):
        resp = client.get("/api/v1/work/projects?limit=200&offset=0")
        assert resp.status_code == 200
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("project_id") == PRJ_FULL)
        assert pop is not None, "Populated smoke project missing from list"
        assert pop["client_name"]        == CLIENT_NAME
        assert pop["site_name"]          == SITE_NAME
        assert pop["business_unit_name"] == BU_NAME
        assert pop["contract_title"]     == CONTRACT_TITLE


class TestProjectOrgReadNullableFksNull:
    """Project row with nullable org FKs set to NULL."""

    def test_get_null_optionals_returns_none_names(self, client):
        resp = client.get(f"/api/v1/work/projects/{PRJ_NULL_OPT}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["project_id"]       == PRJ_NULL_OPT
        # Required FKs still populate:
        assert body["client_id"]        == CLIENT_ID
        assert body["site_id"]          == SITE_ID
        assert body["client_name"]      == CLIENT_NAME
        assert body["site_name"]        == SITE_NAME
        # Nullable FKs → None, so the joined display fields stay None:
        assert body["business_unit_id"] is None
        assert body["contract_id"]      is None
        assert body["business_unit_name"] is None
        assert body["contract_title"]     is None

    def test_list_preserves_null_fk_none_semantics(self, client):
        resp = client.get("/api/v1/work/projects?limit=200&offset=0")
        assert resp.status_code == 200
        rows = resp.json()
        nul = _first_matching(rows, lambda r: r.get("project_id") == PRJ_NULL_OPT)
        assert nul is not None
        assert nul["business_unit_name"] is None
        assert nul["contract_title"]     is None


class TestProjectOrgReadContractNullDisplayColumn:
    """Project row with contract_id set, but org.contracts.title IS NULL.

    Proves the hydrator treats `contract.title == NULL` as `None`, not as an
    empty string or an exception, i.e. joined-display-column nulls flow
    through the same way as joined-relationship-missing nulls.
    """

    def test_get_contract_null_title_yields_none(self, client):
        resp = client.get(f"/api/v1/work/projects/{PRJ_CTR_NULLTITLE}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["project_id"]       == PRJ_CTR_NULLTITLE
        # Contract FK IS set — this distinguishes the null-display case
        # from the null-FK case proven above:
        assert body["contract_id"]      == CONTRACT_NULL_TITLE
        # But contract.title is NULL, so the read field remains None:
        assert body["contract_title"]   is None
        # The other three org-backed fields still materialize normally:
        assert body["client_name"]        == CLIENT_NAME
        assert body["site_name"]          == SITE_NAME
        assert body["business_unit_name"] == BU_NAME


class TestWorkPackageOrgRead:
    """WorkPackage row with required org FKs set."""

    def test_get_materializes_client_and_site_names(self, client):
        resp = client.get(f"/api/v1/work/work-packages/{WP_POPULATED}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["work_package_id"] == WP_POPULATED
        assert body["client_id"]       == CLIENT_ID
        assert body["site_id"]         == SITE_ID
        assert body["client_name"]     == CLIENT_NAME
        assert body["site_name"]       == SITE_NAME

    def test_list_surfaces_work_package_with_org_names(self, client):
        resp = client.get("/api/v1/work/work-packages?limit=200&offset=0")
        assert resp.status_code == 200
        rows = resp.json()
        pop = _first_matching(rows, lambda r: r.get("work_package_id") == WP_POPULATED)
        assert pop is not None, "Smoke work_package missing from list"
        assert pop["client_name"] == CLIENT_NAME
        assert pop["site_name"]   == SITE_NAME


# ---------------------------------------------------------------------------
# Boundary confirmation — still read-surface only
# ---------------------------------------------------------------------------

class TestBoundaryConfirmation:
    """Re-assert packet-012h boundary (endpoint inventory) against the real-PG
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
