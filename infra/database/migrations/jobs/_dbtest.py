"""Host-native psycopg3 migration test helper for the jobs domain.
Applies .sql via the host psql over TCP; pins orchestration_test explicitly
because ambient PG env may point elsewhere. No Windows-path assumptions."""
import os
import subprocess

import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", "psql")
PGPW = os.environ.get("ORCH_TEST_PGPASSWORD") or os.environ.get("DEV_PG_PASSWORD") or "TCC_v5_2025"
DBNAME = os.environ.get("ORCH_TEST_DB", "orchestration_test")
DSN = os.environ.get("ORCH_TEST_DSN") or (
    f"host=127.0.0.1 port=5432 dbname={DBNAME} user=orchestration password={PGPW} sslmode=disable"
)


def psql_file(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "orchestration", "-d", DBNAME,
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


def connect():
    return psycopg.connect(DSN, autocommit=True)
