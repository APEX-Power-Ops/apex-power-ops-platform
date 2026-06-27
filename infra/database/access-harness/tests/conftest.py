"""pytest fixtures for the Access Fidelity Harness.

HARD FENCE: the pg fixture MUST connect to tcc_fidelity_test only.
It verifies current_database() == 'tcc_fidelity_test' before any DDL.
It must NEVER touch tcc_fidelity_staging.
"""
import pathlib

import psycopg
import pytest

from access_harness.config import apply_sql, test_pg_dsn

_SQL_DIR = pathlib.Path(__file__).parent.parent / "sql"
_HARNESS_SCHEMAS = [
    "access_raw",
    "access_meta",
    "access_validation",
    "tcc_snapshot",
]


@pytest.fixture
def pg():
    """Yield an open psycopg connection to tcc_fidelity_test with DDL applied.

    Setup:
      1. Connect using test_pg_dsn().
      2. HARD FENCE: assert current_database() == 'tcc_fidelity_test'.
      3. Drop and recreate the 4 harness schemas (idempotent).
      4. Apply sql/001_schemas.sql.
      5. Yield the open connection.

    Teardown:
      6. Drop the 4 harness schemas CASCADE.
    """
    dsn = test_pg_dsn()
    conn = psycopg.connect(dsn, autocommit=True)
    try:
        # HARD FENCE -- must be tcc_fidelity_test
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            (current_db,) = cur.fetchone()
        if current_db != "tcc_fidelity_test":
            raise RuntimeError(
                f"HARD FENCE VIOLATION: connected to '{current_db}' "
                "but test fixture requires 'tcc_fidelity_test'. "
                "Check ACCESS_HARNESS_SUPERUSER_DSN and test_pg_dsn()."
            )

        # Drop then recreate schemas to guarantee a clean slate
        with conn.cursor() as cur:
            for schema in _HARNESS_SCHEMAS:
                cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            for schema in _HARNESS_SCHEMAS:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

        # Apply DDL
        apply_sql(conn, _SQL_DIR / "001_schemas.sql")

        yield conn
    finally:
        # Teardown: drop schemas CASCADE
        try:
            with conn.cursor() as cur:
                for schema in _HARNESS_SCHEMAS:
                    cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        finally:
            conn.close()
