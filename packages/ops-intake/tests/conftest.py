import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fixtures.build_fixture import build

_OPS_TRUNCATE = (
    "truncate ops.apparatus, ops.scope_quote_line, ops.scope_quote, "
    "ops.scopes, ops.standard_hours, ops.projects, ops.tasks, "
    "ops.intake_validation_findings, ops.intake_source_files, ops.intake_runs cascade;"
)

_MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[3] / "infra/database/migrations/ops"


def _require_ops_test(dsn):
    from psycopg.conninfo import conninfo_to_dict
    db = conninfo_to_dict(dsn).get("dbname")
    assert db == "ops_test", (
        "Safety guard: DSN must target dbname=ops_test, got " + repr(db)
    )


def _dsn():
    d = os.environ.get("OPS_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=ops_dev user=postgres "
        "password={} sslmode=disable".format(
            os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
        )
    )
    _require_ops_test(d)
    return d


@pytest.fixture
def dsn():
    return _dsn()


@pytest.fixture
def clean_ops():
    import psycopg
    d = _dsn()
    _require_ops_test(d)
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(_OPS_TRUNCATE)
    return d


def _ops_schema_exists(conn) -> bool:
    row = conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone()
    return row is not None


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(tmp_path_factory):
    import psycopg
    d = _dsn()
    _require_ops_test(d)

    def _run_sql(conn, path):
        sql = path.read_text(encoding="utf-8")
        conn.execute(sql)

    mig_dir = _MIGRATIONS_DIR
    # pre-up reset: drop 009 THEN 008 (core + FK) THEN 001 (ops) so a leaked schema from a prior
    # session cannot make the up-migrations fail.
    # 009 down contains a CREATE OR REPLACE FUNCTION ops.* so it requires the ops schema to exist;
    # guard with an existence check so a brand-new ops_test database is safe.
    with psycopg.connect(d, autocommit=True) as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010 down's data-loss guard passes
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
        _run_sql(c, mig_dir / "008_core_equipment_models_down.sql")
        _run_sql(c, mig_dir / "001_identity_skeleton_down.sql")

    up_migrations = [
        "001_identity_skeleton.sql",
        "002_quote_model.sql",
        "003_intake_unique_keys.sql",
        "004_person_anchor.sql",
        "005_recognition_ledger.sql",
        "006_progress_billing.sql",
        "007_intake_envelope.sql",
        "008_core_equipment_models.sql",
        "009_recognition_bridge.sql",
        "010_native_envelope_intake.sql",
    ]
    with psycopg.connect(d, autocommit=True) as c:
        for name in up_migrations:
            _run_sql(c, mig_dir / name)

    yield

    with psycopg.connect(d, autocommit=True) as c:
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010 down's data-loss guard passes
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
        _run_sql(c, mig_dir / "008_core_equipment_models_down.sql")
        _run_sql(c, mig_dir / "001_identity_skeleton_down.sql")


@pytest.fixture(scope="session")
def mini_workbook(tmp_path_factory):
    return build(tmp_path_factory.mktemp("wb") / "mini_estimator.xlsx")


@pytest.fixture
def real_workbook():
    p = os.environ.get("MINER_WORKBOOK")
    if not p or not pathlib.Path(p).exists():
        pytest.skip("set MINER_WORKBOOK to the Rev10 .xlsm on the host")
    return pathlib.Path(p)
