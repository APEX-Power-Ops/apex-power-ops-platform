"""Apply the learning migrations to a throwaway learning_test, then point the package at it.

The package reads LEARNING_DEV_DSN; tests override it to learning_test so capture writes never
touch learning_dev. We apply test_prereq.sql + 001 + 002 (idempotent) from the migrations lane so
the package's required schema is present without duplicating DDL.
"""
import os
import pathlib

import psycopg
import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]          # tests -> learning-capture -> packages -> repo root
MIG = REPO / "infra" / "database" / "migrations" / "learning"

_PW = os.environ.get("LEARNING_TEST_PGPASSWORD") or os.environ.get("LEARNING_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
TEST_DSN = os.environ.get("LEARNING_TEST_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=learning_test user=postgres password={_PW} sslmode=disable"
)
# The package's db.connect() reads LEARNING_DEV_DSN -- pin it to learning_test for the whole run.
os.environ["LEARNING_DEV_DSN"] = TEST_DSN

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def _exec_file(path):
    with psycopg.connect(TEST_DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def _schema():
    _exec_file(MIG / "test_prereq.sql")
    _exec_file(MIG / "002_learning_events_down.sql")   # clean slate
    _exec_file(MIG / "001_person_bridge_down.sql")
    _exec_file(MIG / "001_person_bridge.sql")
    _exec_file(MIG / "002_learning_events.sql")
    yield
    _exec_file(MIG / "002_learning_events_down.sql")
