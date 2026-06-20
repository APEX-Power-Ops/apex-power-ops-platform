"""Builds the deterministic mini-graph on a THROWAWAY learning_test DB. Refuses to run on any
DB whose DSN is not learning_test (db.py defaults to learning_dev -- this guard prevents nuking
the frozen baseline). Point LEARNING_DEV_DSN at learning_test before running these tests."""
import pathlib

import psycopg
import pytest

from learning_projections.db import dsn as _dsn

HERE = pathlib.Path(__file__).parent
REPO = HERE.parents[2]
MIG_002 = REPO / "infra" / "database" / "migrations" / "learning" / "002_learning_events.sql"
PREREQ = HERE / "projections_prereq.sql"
EVENTS = HERE / "projections_events_seed.sql"


def _target() -> str:
    d = _dsn()
    if "learning_test" not in d:
        raise RuntimeError(f"refusing to build the projections fixture on a non-test DB: {d!r}")
    return d


@pytest.fixture(scope="session", autouse=True)
def _fixture():
    d = _target()
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(PREREQ.read_text(encoding="utf-8"))
        c.execute(MIG_002.read_text(encoding="utf-8"))
        c.execute(EVENTS.read_text(encoding="utf-8"))
    yield
