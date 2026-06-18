"""TDD - records MTS-accommodation Chip C1: form_submissions.neta_standard (mig 041).

The test EVENT chooses the standard: a given apparatus is tested under ATS at commissioning and
MTS at maintenance intervals — same standard-aware template (migs 038-040), different event. This
adds form_submissions.neta_standard so the submission records which standard it ran under; the
render/validate layer (Chip C2, future serving) resolves coverage + acceptance against it.

RED until 041_form_submission_standard.sql exists. Run PER-CHIP:
  RECORDS_DEV_PGPASSWORD=... uv run --no-project --with "psycopg[binary]" --with pytest \
    pytest test_041_form_submission_standard.py -q
"""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


@pytest.fixture(scope="module")
def conn():
    _psql("041_form_submission_standard_down.sql")
    _psql("041_form_submission_standard.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def test_column_typed_notnull_default_ats(conn):
    row = conn.execute(
        "select udt_name, is_nullable, column_default from information_schema.columns "
        "where table_schema='records' and table_name='form_submissions' and column_name='neta_standard'"
    ).fetchone()
    assert row, "form_submissions.neta_standard missing"
    udt, nullable, default = row
    assert udt == "neta_standard_enum", f"wrong type {udt}"
    assert nullable == "NO", "neta_standard must be NOT NULL"
    assert default and "ats" in default, f"default should be 'ats', got {default}"


def test_enum_accepts_both_standards(conn):
    vals = {r[0] for r in conn.execute(
        "select unnest(enum_range(null::records.neta_standard_enum))::text").fetchall()}
    assert {"ats", "mts"} <= vals, f"neta_standard_enum must cover ats+mts, got {vals}"


def test_reversibility(conn):
    _psql("041_form_submission_standard_down.sql")
    with psycopg.connect(DSN) as c:
        gone = c.execute(
            "select count(*) from information_schema.columns where table_schema='records' "
            "and table_name='form_submissions' and column_name='neta_standard'"
        ).fetchone()[0]
        assert gone == 0, "down must drop neta_standard"
    _psql("041_form_submission_standard.sql")
