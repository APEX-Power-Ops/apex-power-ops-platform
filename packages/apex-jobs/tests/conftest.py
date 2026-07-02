"""Pytest fixtures: apply the jobs migrations to orchestration_test once per
session; truncate the tables before each test. Host-native psql, no Windows paths.

Credentials come from env only -- no in-code fallback (records-lane convention):
APEX_JOBS_PGPASSWORD or DEV_PG_PASSWORD (host: set -a; . infra/.env; set +a).
The whole suite skips with a clear hint when the env is absent.

The engine's resolve_dsn() defaults to orchestration_dev, while these fixtures
prep DBNAME (default orchestration_test) -- so the runtime is PINNED below to
the exact fixture target (DB + host + port + user). Without the pin, a run
missing APEX_JOBS_DB writes test jobs into the live dev DB. APEX_JOBS_DSN and
DBNAME=orchestration_dev are refused outright: the fixtures down/up + truncate
their target, which must never be the dev DB or an unvetted foreign DSN."""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MIG = os.path.join(REPO, "infra", "database", "migrations", "jobs")
PSQL = os.environ.get("PSQL_EXE", "psql")
DBNAME = os.environ.get("APEX_JOBS_DB", "orchestration_test")

if DBNAME == "orchestration_dev":
    pytest.exit(
        "refusing to run the apex-jobs suite against orchestration_dev: the "
        "fixtures down/up the jobs schema and truncate its tables. Use "
        "APEX_JOBS_DB=orchestration_test (or another disposable *_test DB).",
        returncode=4,
    )
if os.environ.get("APEX_JOBS_DSN"):
    pytest.exit(
        "APEX_JOBS_DSN is set, but this suite pins the engine runtime to the "
        "fixture target (host 127.0.0.1:5432, user orchestration, db "
        f"{DBNAME}). Unset APEX_JOBS_DSN; use APEX_JOBS_DB to pick the test DB.",
        returncode=4,
    )

# Pin the engine runtime to the fixture target so app writes can never land in
# a different DB than the one the fixtures prep and truncate.
os.environ["APEX_JOBS_DB"] = DBNAME
os.environ["APEX_JOBS_HOST"] = "127.0.0.1"
os.environ["APEX_JOBS_PORT"] = "5432"
os.environ["APEX_JOBS_USER"] = "orchestration"

PGPW = os.environ.get("APEX_JOBS_PGPASSWORD") or os.environ.get("DEV_PG_PASSWORD")
DSN = (
    f"host=127.0.0.1 port=5432 dbname={DBNAME} user=orchestration "
    f"password={PGPW} sslmode=disable"
) if PGPW else None

ENV_HINT = (
    "DB env absent: set APEX_JOBS_PGPASSWORD or DEV_PG_PASSWORD "
    "(host: set -a; . infra/.env; set +a) -- no in-code fallback"
)

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql", "003_jobs_indexes.sql",
         "004_jobs_views.sql", "005_durability_and_agents.sql"]
DOWN = ["005_durability_and_agents_down.sql", "004_jobs_views_down.sql",
        "003_jobs_indexes_down.sql", "002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


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
    if not PGPW:
        pytest.skip(ENV_HINT)
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
