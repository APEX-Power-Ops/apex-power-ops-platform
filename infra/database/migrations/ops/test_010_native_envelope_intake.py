import os
import pathlib
import psycopg
import pytest

MIG = pathlib.Path(__file__).resolve().parent

def _dsn():
    d = os.environ.get("OPS_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
        "password={} sslmode=disable".format(os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", ""))
    )
    from psycopg.conninfo import conninfo_to_dict
    assert conninfo_to_dict(d).get("dbname") == "ops_test", "test must target ops_test"
    return d

def test_010_adds_native_enum_and_columns():
    with psycopg.connect(_dsn(), autocommit=True) as c:
        vals = [r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid"
            " where t.typname='intake_source_format'").fetchall()]
        assert "native" in vals
        cols = [r[0] for r in c.execute(
            "select column_name from information_schema.columns"
            " where table_schema='ops' and table_name='intake_runs'").fetchall()]
        for col in ("envelope_id","quote_version","content_hash","source_draft_id",
                    "source_revision_id","estimate_envelope_json"):
            assert col in cols, col
        assert "source_kind" not in cols  # C1: no source_kind

def test_010_identity_columns_are_immutable():
    """trg_intake_run_immutable must reject UPDATE drift on the new identity cols."""
    with psycopg.connect(_dsn(), autocommit=True) as c:
        pid = c.execute("insert into ops.persons (display_name) values ('m10') returning person_id").fetchone()[0]
        rid = c.execute(
            "insert into ops.intake_runs (project_number, source_format, status, conflict_kind,"
            " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
            " uploaded_by, content_hash, quote_version, envelope_id)"
            " values ('P10','native'::ops.intake_source_format,'parsed','none','estimate_envelope_v1',"
            " 'estimator-core/c051c02','{}'::jsonb,'{}'::jsonb,%s,'h1',1,'e1') returning id",
            (pid,)).fetchone()[0]
        # R1-6: typed drift per column — quote_version is integer, so a 'zzz' there fails on CAST, not the
        # trigger. Each value is valid for its type but DIFFERENT from the inserted row, so the trigger fires.
        drift = {"content_hash": "'zz'", "envelope_id": "'zz'", "source_revision_id": "'zz'",
                 "source_draft_id": "'zz'", "quote_version": "2"}
        for col, val in drift.items():
            with pytest.raises(psycopg.errors.RaiseException):
                c.execute(f"update ops.intake_runs set {col}={val} where id=%s", (rid,))

def test_010_partial_unique_native_only():
    with psycopg.connect(_dsn(), autocommit=True) as c:
        idx = [r[0] for r in c.execute(
            "select indexname from pg_indexes where schemaname='ops' and tablename='intake_runs'").fetchall()]
        assert "uq_intake_runs_content_hash_native" in idx
        assert "uq_intake_runs_proj_quote_version_native" in idx
