# test_010_native_envelope_intake.py — self-contained migration test.
# Mirrors test_009's autouse session fixture so this module can run standalone
# (CI: pytest infra/database/migrations/ops/test_010_native_envelope_intake.py)
# AND alongside the package suite (the two session fixtures are idempotent via clean_slate).
import os, pathlib, uuid
import psycopg, pytest
from psycopg.conninfo import conninfo_to_dict

HERE = pathlib.Path(__file__).resolve().parent

DSN = os.environ.get("OPS_DEV_ADMIN_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    "password={} sslmode=disable".format(
        os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
    )
)
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "010 migration tests run on ops_test ONLY"

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
]
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
        _exec(HERE / f)   # applies 001..010
    yield
    _clean_slate()


def _dsn():
    """Return the module-level DSN (for test bodies that need a function call)."""
    return DSN


def test_010_adds_native_enum_and_columns():
    with psycopg.connect(DSN, autocommit=True) as c:
        vals = [r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid"
            " where t.typname='intake_source_format'").fetchall()]
        assert "native" in vals
        cols = [r[0] for r in c.execute(
            "select column_name from information_schema.columns"
            " where table_schema='ops' and table_name='intake_runs'").fetchall()]
        for col in ("envelope_id", "quote_version", "content_hash", "source_draft_id",
                    "source_revision_id", "estimate_envelope_json"):
            assert col in cols, col
        assert "source_kind" not in cols  # C1: no source_kind


def test_010_identity_columns_are_immutable():
    """trg_intake_run_immutable must reject UPDATE drift on the new identity cols."""
    with psycopg.connect(DSN, autocommit=True) as c:
        pid = c.execute(
            "insert into ops.persons (display_name) values ('m10') returning person_id"
        ).fetchone()[0]
        rid = c.execute(
            "insert into ops.intake_runs (project_number, source_format, status, conflict_kind,"
            " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
            " uploaded_by, content_hash, quote_version, envelope_id)"
            " values ('P10','native'::ops.intake_source_format,'parsed','none','estimate_envelope_v1',"
            " 'estimator-core/c051c02','{}'::jsonb,'{}'::jsonb,%s,'h1',1,'e1') returning id",
            (pid,)).fetchone()[0]
        # R1-6: typed drift per column — quote_version is integer so a 'zzz' there fails on CAST,
        # not the trigger.  Each value is valid for its type but DIFFERENT from the inserted row,
        # so the trigger fires.
        drift = {
            "content_hash": "'zz'",
            "envelope_id": "'zz'",
            "source_revision_id": "'zz'",
            "source_draft_id": "'zz'",
            "quote_version": "2",
        }
        for col, val in drift.items():
            with pytest.raises(psycopg.errors.RaiseException):
                c.execute(f"update ops.intake_runs set {col}={val} where id=%s", (rid,))


def test_010_partial_unique_native_only():
    """C6-RESOLVED: content_hash global-uniqueness index must NOT exist; proj_quote_version index MUST exist.
    Idempotency / version-anchor = (project_number, quote_version); content_hash is provenance only."""
    with psycopg.connect(DSN, autocommit=True) as c:
        idx = [r[0] for r in c.execute(
            "select indexname from pg_indexes where schemaname='ops' and tablename='intake_runs'"
        ).fetchall()]
        assert "uq_intake_runs_proj_quote_version_native" in idx
        assert "uq_intake_runs_content_hash_native" not in idx  # C6: dropped; content_hash is provenance only
