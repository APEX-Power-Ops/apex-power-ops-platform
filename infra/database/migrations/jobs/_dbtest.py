"""Host-native psycopg3 migration test helper for the jobs domain.
Applies .sql via the host psql over TCP; pins orchestration_test explicitly
because ambient PG env may point elsewhere. No Windows-path assumptions.

Credentials come from env only -- no in-code fallback (records-lane convention):
ORCH_TEST_PGPASSWORD or DEV_PG_PASSWORD, or ORCH_TEST_DSN as a full override
that drives BOTH the psycopg connection and the psql apply path (parsed via
psycopg.conninfo; a DSN without a password still needs one of the password
vars). On the host: set -a; . infra/.env; set +a. DB-backed tests skip with a
clear hint when the env is absent."""
import os
import subprocess

import psycopg
import pytest
from psycopg import conninfo

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


def _params():
    """One connection target for both paths; ORCH_TEST_DSN wins whole."""
    dsn = os.environ.get("ORCH_TEST_DSN")
    if dsn:
        p = conninfo.conninfo_to_dict(dsn)
    else:
        p = {"host": "127.0.0.1", "port": "5432", "dbname": DBNAME,
             "user": "orchestration", "sslmode": "disable"}
    if not p.get("password"):
        p["password"] = _password()
    return p


def psql_file(fname):
    p = _params()
    env = {**os.environ, "PGPASSWORD": str(p["password"]),
           "PGSSLMODE": str(p.get("sslmode", "disable"))}
    r = subprocess.run(
        [PSQL, "-h", str(p.get("host", "127.0.0.1")), "-p", str(p.get("port", "5432")),
         "-U", str(p.get("user", "orchestration")), "-d", str(p.get("dbname", DBNAME)),
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


def connect():
    return psycopg.connect(conninfo.make_conninfo(**_params()), autocommit=True)
