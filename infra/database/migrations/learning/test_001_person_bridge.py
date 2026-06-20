"""learning migration 001 -- person bridge (public.user_profiles.employee_id): TDD.

Cross-DB contract-FK to prod public.employees.id (app-enforced, NO db FK -- employees is a
separate database). Mirrors records.persons.employee_ref / ops.persons.employee_ref. Runs against
a THROWAWAY learning_test (conftest applies test_prereq.sql first).

Run (host, from infra/database/migrations/learning/):
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
  LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q
"""
import pathlib

import psycopg
import pytest

from conftest import DSN

HERE = pathlib.Path(__file__).parent
UP = HERE / "001_person_bridge.sql"
DOWN = HERE / "001_person_bridge_down.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="module", autouse=True)
def migrate():
    _exec_file(DOWN)   # clean slate (user_profiles exists from the prereq fixture)
    _exec_file(UP)
    yield
    _exec_file(DOWN)


def test_employee_id_exists_and_nullable():
    assert _scalar(
        "select is_nullable from information_schema.columns "
        "where table_schema='public' and table_name='user_profiles' and column_name='employee_id'"
    ) == "YES"


def test_employee_id_has_no_db_fk():
    n = _scalar(
        "select count(*) from pg_constraint con "
        "join pg_attribute a on a.attrelid=con.conrelid and a.attnum = any(con.conkey) "
        "where con.conrelid='public.user_profiles'::regclass and con.contype='f' and a.attname='employee_id'"
    )
    assert n == 0


def test_employee_id_partial_unique():
    emp = "11111111-1111-1111-1111-111111111111"
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("insert into public.user_profiles (employee_id) values (%s::uuid)", (emp,))
        try:
            with pytest.raises(psycopg.errors.UniqueViolation):
                c.execute("insert into public.user_profiles (employee_id) values (%s::uuid)", (emp,))
        finally:
            c.execute("delete from public.user_profiles where employee_id = %s::uuid", (emp,))


def test_two_null_employee_ids_allowed():
    # partial unique (WHERE employee_id IS NOT NULL) -> multiple NULLs are fine.
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("insert into public.user_profiles (email) values ('a@x.io'), ('b@x.io')")
        c.execute("delete from public.user_profiles where email in ('a@x.io','b@x.io')")
