"""Chip 1 - ops identity skeleton: invariant + reversibility tests (TDD).

Run (from anywhere) with the local-PG password in env:
    $env:PGPASSWORD="..."; uv run --with "psycopg[binary]" --with pytest pytest <thisfile> -v

Asserts the SSoT S4 laws against a fresh `ops_test`:
  - schema/tables/enums exist
  - apparatus.scope_id NOT NULL  (Law 1, FIXED binding)
  - cross-scope reassignment blocked by guard  (Law 1)
  - apparatus has NO actual_revenue / quoted_revenue  (Law 3 firewall; revenue = later chips)
  - apparatus has nullable equipment_model_ref  (Law 5 soft core seam)
  - FK enforcement
  - reversibility: down after up, up after down (clean)
"""
import os
import pathlib
import uuid

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

# NOTE: this environment's shell profile exports ambient PGHOST/PGUSER/PGDATABASE that
# point at the Supabase prod pooler. We therefore PIN the local ops_test connection
# explicitly (so those env vars can't redirect us) and read only the password from env.
# Override the whole DSN with OPS_DEV_ADMIN_DSN if your local setup differs.
DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
    "sslmode=disable"
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "001 migration tests run on ops_test ONLY"

HERE = pathlib.Path(__file__).parent
UP = HERE / "001_identity_skeleton.sql"
DOWN = HERE / "001_identity_skeleton_down.sql"


def _exec_file(path: pathlib.Path) -> None:
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session", autouse=True)
def apply_migration():
    """down (clean slate) -> up; tear down with down. Idempotent down (IF EXISTS)."""
    if DOWN.exists():
        _exec_file(DOWN)
    _exec_file(UP)
    yield
    _exec_file(DOWN)


@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:  # transactional; rolled back -> no test data persists
        try:
            yield c
        finally:
            c.rollback()


def _mk_scope(c) -> str:
    pid = c.execute(
        "insert into ops.projects (project_number, project_name) values (%s, 't') returning id",
        (f"P-{uuid.uuid4().hex[:8]}",),
    ).fetchone()[0]
    return c.execute(
        "insert into ops.scopes (project_id, scope_name) values (%s, 's') returning id",
        (pid,),
    ).fetchone()[0]


# ---- structural (read-only) ----

def test_tables_exist():
    with psycopg.connect(DSN, autocommit=True) as c:
        t = {r[0] for r in c.execute(
            "select table_name from information_schema.tables where table_schema='ops'"
        )}
    assert {"projects", "scopes", "apparatus", "tasks"} <= t


def test_enums_exist():
    with psycopg.connect(DSN, autocommit=True) as c:
        e = {r[0] for r in c.execute(
            "select t.typname from pg_type t join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='ops' and t.typtype='e'"
        )}
    assert {
        "project_status", "scope_status", "scope_type",
        "apparatus_status", "apparatus_assessment", "apparatus_availability",
        "task_status",
    } <= e


def test_apparatus_firewall_and_seam():
    with psycopg.connect(DSN, autocommit=True) as c:
        cols = {r[0] for r in c.execute(
            "select column_name from information_schema.columns "
            "where table_schema='ops' and table_name='apparatus'"
        )}
    assert "actual_revenue" not in cols      # Law 3 — recognized $ is the Chip 3 ledger
    assert "quoted_revenue" not in cols      # deferred to Chip 2 (lands with the quote)
    assert "equipment_model_ref" in cols     # Law 5 — soft core seam


def test_apparatus_scope_id_not_null():
    assert _scalar(
        "select is_nullable from information_schema.columns where table_schema='ops' "
        "and table_name='apparatus' and column_name='scope_id'"
    ) == "NO"


def test_equipment_model_ref_nullable():
    assert _scalar(
        "select is_nullable from information_schema.columns where table_schema='ops' "
        "and table_name='apparatus' and column_name='equipment_model_ref'"
    ) == "YES"


# ---- behavioral (txn rollback) ----

def test_apparatus_requires_scope(conn):
    with pytest.raises(psycopg.errors.NotNullViolation):
        with conn.transaction():
            conn.execute("insert into ops.apparatus (scope_id, apparatus_designation) values (null, 'A')")


def test_apparatus_bad_scope_fk(conn):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():
            conn.execute(
                "insert into ops.apparatus (scope_id, apparatus_designation) values (%s, 'A')",
                (str(uuid.uuid4()),),
            )


def test_valid_apparatus_then_no_cross_scope_move(conn):
    s1 = _mk_scope(conn)
    s2 = _mk_scope(conn)
    aid = conn.execute(
        "insert into ops.apparatus (scope_id, apparatus_designation) values (%s, 'A') returning id",
        (s1,),
    ).fetchone()[0]
    # Law 1: apparatus cannot move between scopes (guard raises)
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():
            conn.execute("update ops.apparatus set scope_id=%s where id=%s", (s2, aid))


# ---- reversibility (kept last; leaves schema present) ----

def test_reversibility():
    _exec_file(DOWN)
    assert _scalar("select 1 from information_schema.schemata where schema_name='ops'") is None
    _exec_file(UP)
    assert _scalar("select 1 from information_schema.schemata where schema_name='ops'") == 1
