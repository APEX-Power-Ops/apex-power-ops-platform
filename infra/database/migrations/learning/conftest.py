"""Host-portable defaults + throwaway-DB bootstrap for the learning migration tests.

Runs against a THROWAWAY learning_test (NEVER learning_dev). learning_events FKs reference
public.user_profiles + public.study_content, which a bare test DB lacks -- so this session-scoped
autouse fixture applies test_prereq.sql (idempotent stub tables + seed rows) before any migration.
Create the DB first (Task 0).
"""
import os
import pathlib

import psycopg
import pytest

DSN = os.environ.get("LEARNING_TEST_DSN") or (
    "host=127.0.0.1 port=5432 dbname=learning_test user=postgres "
    f"password={os.environ.get('LEARNING_TEST_PGPASSWORD') or os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
    "sslmode=disable"
)
HERE = pathlib.Path(__file__).parent
PREREQ = HERE / "test_prereq.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def _prereq():
    _exec_file(PREREQ)
    yield
