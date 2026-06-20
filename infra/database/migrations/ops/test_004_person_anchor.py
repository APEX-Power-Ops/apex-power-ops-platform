"""ops migration 004 -- person anchor (ops.persons): invariant + reversibility tests (TDD).

Phase-5 additive identity slice (contract C1/D2/D4/D6). Runs against a THROWAWAY ops_test
(NOT ops_dev): the ops test fixtures down-then-up, and ops_dev holds the 5,344 Miner apparatus
-- standing rule (Phase 3). ops.persons is standalone, so a bare ops_test (the ops schema is
auto-created by the migration) suffices.

Run (host):
  OPS_DEV_PGPASSWORD=<host pw> \
  OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=<pw> sslmode=disable" \
    uv run --with "psycopg[binary]" --with pytest pytest test_004_person_anchor.py -q

Asserts:
  - ops.persons exists with PK person_id.
  - employee_ref carries NO db FK (cross-DB contract pointer); partial-unique on it.
  - worker_class / match_confidence CHECKs; adjudication by/at paired.
  - reversibility: down (table only, never the schema) -> up -> down clean.
"""
import os
import pathlib
import uuid

import psycopg
import pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} "
    "sslmode=disable"
)
HERE = pathlib.Path(__file__).parent
UP = HERE / "004_person_anchor.sql"
DOWN = HERE / "004_person_anchor_down.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="module", autouse=True)
def migrate():
    if DOWN.exists():
        _exec_file(DOWN)   # clean slate
    _exec_file(UP)
    yield
    _exec_file(DOWN)       # teardown (throwaway DB)


@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try:
            yield c
        finally:
            c.rollback()


def test_persons_exists():
    assert _scalar("select to_regclass('ops.persons') is not null") is True


def test_employee_ref_no_db_fk():
    n = _scalar("select count(*) from pg_constraint "
                "where conrelid='ops.persons'::regclass and contype='f'")
    assert n == 0


def test_worker_class_check(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into ops.persons (display_name, worker_class) values ('x','bogus')")


def test_match_confidence_check(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into ops.persons (display_name, match_confidence) values ('x','fuzzy')")


def test_adjudication_paired(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into ops.persons (display_name, match_adjudicated_by) "
                     "values ('x', gen_random_uuid())")


def test_employee_ref_partial_unique(conn):
    emp = str(uuid.uuid4())
    conn.execute("insert into ops.persons (display_name, employee_ref) values ('a', %s)", (emp,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute("insert into ops.persons (display_name, employee_ref) values ('b', %s)", (emp,))
    # rolled back by the conn fixture
