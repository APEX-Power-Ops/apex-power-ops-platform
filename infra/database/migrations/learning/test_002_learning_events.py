"""learning migration 002 -- append-only learning_events ledger: TDD.

Capture substrate for Slice 2a. Immutable (UPDATE/DELETE blocked by a trigger). Runs against the
throwaway learning_test (conftest applies test_prereq.sql -> stub user_profiles + study_content +
seed rows 0001 / 0010).

Run (host, from infra/database/migrations/learning/):
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
  LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q
"""
import pathlib

import psycopg
import pytest

from conftest import DSN

HERE = pathlib.Path(__file__).parent
UP = HERE / "002_learning_events.sql"
DOWN = HERE / "002_learning_events_down.sql"

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="module", autouse=True)
def migrate():
    _exec_file(DOWN)
    _exec_file(UP)
    yield
    _exec_file(DOWN)


@pytest.fixture
def conn():
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _insert(c, etype, content=None, section=None):
    return c.execute(
        "insert into public.learning_events (user_id, event_type, study_content_id, neta_section) "
        "values (%s::uuid, %s, %s, %s) returning event_id",
        (USER, etype, content, section),
    ).fetchone()[0]


def test_table_exists():
    assert _scalar("select to_regclass('public.learning_events') is not null") is True


def test_accepts_the_four_event_types(conn):
    for etype in ("resource_viewed", "resource_completed", "assessment_completed", "self_assessment"):
        assert _insert(conn, etype) is not None


def test_rejects_unknown_event_type(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert(conn, "bogus_event")


def test_three_indexes_present():
    n = _scalar(
        "select count(*) from pg_indexes where schemaname='public' and tablename='learning_events' "
        "and indexname in ('ix_learning_events_user_time','ix_learning_events_section','ix_learning_events_type')"
    )
    assert n == 3


def test_append_only_blocks_update(conn):
    eid = _insert(conn, "resource_viewed")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update public.learning_events set neta_section='x' where event_id=%s", (eid,))


def test_append_only_blocks_delete(conn):
    eid = _insert(conn, "resource_viewed")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from public.learning_events where event_id=%s", (eid,))


def test_study_content_fk_set_null_semantics():
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' and conname like '%study_content%'"
    )
    assert rule == "n"  # 'n' = SET NULL


def test_user_fk_cascade_semantics():
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' and conname like '%user_id%'"
    )
    assert rule == "c"  # 'c' = CASCADE
