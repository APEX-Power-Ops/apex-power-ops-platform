"""Pytest fixtures: apply the jobs migrations to orchestration_test once per
session; truncate the tables before each test. Host-native psql, no Windows paths."""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MIG = os.path.join(REPO, "infra", "database", "migrations", "jobs")
PSQL = os.environ.get("PSQL_EXE", "psql")
DBNAME = os.environ.get("APEX_JOBS_DB", "orchestration_test")
PGPW = (os.environ.get("APEX_JOBS_PGPASSWORD")
        or os.environ.get("DEV_PG_PASSWORD") or "TCC_v5_2025")
DSN = f"host=127.0.0.1 port=5432 dbname={DBNAME} user=orchestration password={PGPW} sslmode=disable"

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql", "003_jobs_indexes.sql", "004_jobs_views.sql"]
DOWN = ["004_jobs_views_down.sql", "003_jobs_indexes_down.sql",
        "002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "orchestration", "-d", DBNAME,
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(MIG, fname)],
        env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname}: {r.stderr}\n{r.stdout}")


@pytest.fixture(scope="session", autouse=True)
def _schema():
    for f in DOWN:
        try:
            _psql(f)
        except Exception:
            pass
    for f in APPLY:
        _psql(f)
    yield


@pytest.fixture
def conn_test():
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("truncate jobs.gate, jobs.run, jobs.job cascade")
        yield c
