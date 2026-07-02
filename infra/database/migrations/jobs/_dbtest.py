"""Host-native psycopg3 migration test helper for the jobs domain.
Applies .sql via the host psql over TCP; pins orchestration_test explicitly
because ambient PG env may point elsewhere. No Windows-path assumptions.

Credentials come from env only -- no in-code fallback (records-lane convention):
ORCH_TEST_PGPASSWORD or DEV_PG_PASSWORD for psql apply + the default DSN, or
ORCH_TEST_DSN as a full psycopg override. On the host: set -a; . infra/.env;
set +a. DB-backed tests skip with a clear hint when the env is absent."""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", "psql")
DBNAME = os.environ.get("ORCH_TEST_DB", "orchestration_test")

ENV_HINT = (
    "DB env absent: set ORCH_TEST_PGPASSWORD or DEV_PG_PASSWORD "
    "(host: set -a; . infra/.env; set +a) -- no in-code fallback"
)


def _password():
    pw = os.environ.get("ORCH_TEST_PGPASSWORD") or os.environ.get("DEV_PG_PASSWORD")
    if not pw:
        pytest.skip(ENV_HINT)
    return pw


def psql_file(fname):
    env = {**os.environ, "PGPASSWORD": _password(), "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "orchestration", "-d", DBNAME,
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


def connect():
    dsn = os.environ.get("ORCH_TEST_DSN") or (
        f"host=127.0.0.1 port=5432 dbname={DBNAME} user=orchestration "
        f"password={_password()} sslmode=disable"
    )
    return psycopg.connect(dsn, autocommit=True)
