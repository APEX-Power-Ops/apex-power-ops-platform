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

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)
UP = "044_person_anchor.sql"
DOWN = "044_person_anchor_down.sql"


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


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
