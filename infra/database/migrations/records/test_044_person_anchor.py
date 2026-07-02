"""TDD - records migration 044: records.persons anchor + form_submissions.technician_person_id.

Phase-5 additive identity slice (contract C1/C3/D2/D4/D5). Guards the invariants that must
not regress:
  - records.persons exists; RLS stays DISABLED (records-lane Amendment 1, mig 043).
  - employee_ref is a bare uuid (NO db FK -- it is the cross-DB contract pointer); a partial
    unique index forbids two anchors for the same real employee.
  - worker_class / match_confidence CHECKs reject bad input; adjudication by/at are paired.
  - form_submissions.technician_person_id is a nullable FK to records.persons with
    ON DELETE SET NULL (preserves the evidence row when an anchor is deleted).
  - idempotent up; clean reversal (down then up).

Run PER-CHIP (never a bulk `pytest .` -- see the records MANIFEST). On the Olares host:
  RECORDS_DEV_PGPASSWORD=<host postgres pw> uv run --no-project \
    --with "psycopg[binary]" --with pytest pytest test_044_person_anchor.py -q
"""
import os
import subprocess

import psycopg
import pytest

import _dbtest

HERE = os.path.dirname(os.path.abspath(__file__))
DSN = _dbtest.dsn()
UP = "044_person_anchor.sql"
DOWN = "044_person_anchor_down.sql"


def _psql(fname):
    _dbtest.run_psql(fname, DSN)


@pytest.fixture(scope="module", autouse=True)
def migrate():
    # clean slate -> up; leave applied (records_dev keeps the slice for downstream work).
    _psql(DOWN)
    _psql(UP)
    yield


def _ac():
    return psycopg.connect(DSN, autocommit=True)


def _tx():
    return psycopg.connect(DSN)  # non-autocommit; caller rolls back


def test_persons_table_exists():
    with _ac() as c:
        assert c.execute("select to_regclass('records.persons') is not null").fetchone()[0] is True


def test_rls_disabled_on_persons():
    with _ac() as c:
        rls = c.execute(
            "select relrowsecurity from pg_class where oid = 'records.persons'::regclass"
        ).fetchone()[0]
        assert rls is False


def test_employee_ref_has_no_db_fk():
    with _ac() as c:
        n = c.execute(
            "select count(*) from pg_constraint "
            "where conrelid='records.persons'::regclass and contype='f'"
        ).fetchone()[0]
        assert n == 0


def test_worker_class_check():
    c = _tx()
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            c.execute("insert into records.persons (display_name, worker_class) values ('x','bogus')")
    finally:
        c.rollback(); c.close()


def test_match_confidence_check():
    c = _tx()
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            c.execute("insert into records.persons (display_name, match_confidence) values ('x','fuzzy')")
    finally:
        c.rollback(); c.close()


def test_adjudication_paired_check():
    c = _tx()
    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            c.execute("insert into records.persons (display_name, match_adjudicated_by) "
                      "values ('x', gen_random_uuid())")
    finally:
        c.rollback(); c.close()


def test_employee_ref_partial_unique():
    emp = "11111111-1111-1111-1111-111111111111"
    c = _tx()
    try:
        c.execute("insert into records.persons (display_name, employee_ref) values ('a', %s)", (emp,))
        with pytest.raises(psycopg.errors.UniqueViolation):
            c.execute("insert into records.persons (display_name, employee_ref) values ('b', %s)", (emp,))
    finally:
        c.rollback(); c.close()


def test_form_submissions_fk_set_null():
    with _ac() as c:
        nullable = c.execute(
            "select is_nullable from information_schema.columns "
            "where table_schema='records' and table_name='form_submissions' "
            "and column_name='technician_person_id'"
        ).fetchone()
        assert nullable is not None and nullable[0] == 'YES'
        act = c.execute(
            "select confdeltype from pg_constraint "
            "where conname='fk_form_submissions_technician_person'"
        ).fetchone()[0]
        assert act == 'n'  # 'n' = ON DELETE SET NULL


def test_idempotent_up():
    _psql(UP)  # second apply must not error
    with _ac() as c:
        assert c.execute("select to_regclass('records.persons') is not null").fetchone()[0] is True
