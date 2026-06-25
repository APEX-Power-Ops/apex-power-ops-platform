# test_011_scope_quote_line_description.py — self-contained migration test.
# Mirrors test_010's autouse session fixture so this module can run standalone
# (CI: pytest infra/database/migrations/ops/test_011_scope_quote_line_description.py)
# AND alongside the package suite (the two session fixtures are idempotent via clean_slate).
import os, pathlib, uuid
import psycopg, pytest
from psycopg.conninfo import conninfo_to_dict

HERE = pathlib.Path(__file__).resolve().parent

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    "password={} sslmode=disable".format(
        os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
    )
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "011 migration tests run on ops_test ONLY"

DOWN1 = HERE / "001_identity_skeleton_down.sql"
CHAIN = [
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
    "011_scope_quote_line_description.sql",
]
DOWN011 = HERE / "011_scope_quote_line_description_down.sql"
UP011 = HERE / "011_scope_quote_line_description.sql"
DOWN010 = HERE / "010_native_envelope_intake_down.sql"
DOWN009 = HERE / "009_recognition_bridge_down.sql"
DOWN008 = HERE / "008_core_equipment_models_down.sql"


def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))


def _ops_schema_exists(conn) -> bool:
    row = conn.execute(
        "select 1 from pg_catalog.pg_namespace where nspname='ops'"
    ).fetchone()
    return row is not None


def _clean_slate():
    """Drop all ops + core schemas so migrations apply cleanly on any ops_test state."""
    with psycopg.connect(DSN, autocommit=True) as c:
        if _ops_schema_exists(c):
            # 010 down has a data-loss guard: clear native rows first
            c.execute("delete from ops.intake_runs")
            _exec(DOWN011)
            _exec(DOWN010)
            _exec(DOWN009)
        _exec(DOWN008)  # drops core schema (idempotent: down uses IF EXISTS)
    _exec(DOWN1)        # drops ops schema (001_down; also idempotent)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select current_database()")
        assert cur.fetchone()[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN:
        _exec(HERE / f)   # applies 001..011
    yield
    _clean_slate()


def _desc_col():
    with psycopg.connect(DSN, autocommit=True) as c:
        return c.execute(
            "select data_type from information_schema.columns "
            "where table_schema='ops' and table_name='scope_quote_line' and column_name='description'"
        ).fetchone()


def test_011_adds_description_column():
    row = _desc_col()
    assert row is not None and row[0] == 'text'


def test_011_reversible():
    # down drops it; up re-adds it; leave it PRESENT (chain/teardown expects it via _clean_slate -> 001 down)
    _exec(DOWN011); assert _desc_col() is None
    _exec(UP011);   assert _desc_col() is not None
