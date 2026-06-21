"""ops Chip 5 -- intake envelope: structure, guards, reversibility (TDD). Throwaway ops_test ONLY."""
import os, pathlib, uuid
import psycopg, pytest
from psycopg.conninfo import conninfo_to_dict

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "Chip 5 migration tests must run on ops_test only"
HERE = pathlib.Path(__file__).parent
DOWN1 = HERE/"001_identity_skeleton_down.sql"
CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
         "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql","007_intake_envelope.sql"]
DOWN7 = HERE/"007_intake_envelope_down.sql"

def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec(DOWN1)
    for f in CHAIN: _exec(HERE/f)
    yield
    _exec(DOWN1)

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

def test_tables_and_enums_exist(conn):
    for t in ("intake_runs","intake_source_files","intake_validation_findings"):
        assert conn.execute("select to_regclass(%s)", (f"ops.{t}",)).fetchone()[0] is not None
    for typ, labels in [
        ("intake_run_status", ["parsed","reviewing","approved","rejected","revision_blocked","superseded"]),
        ("intake_conflict_kind", ["none","frozen","recognized","billed"]),
        ("intake_source_format", ["decomposed_scope_sheet","flat_quote","unsupported"])]:
        got = conn.execute(
            "select array_agg(e.enumlabel order by e.enumsortorder) from pg_enum e "
            "join pg_type t on t.oid=e.enumtypid join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='ops' and t.typname=%s", (typ,)).fetchone()[0]
        assert sorted(got) == sorted(labels), (typ, got)

def _person(c):
    return c.execute("insert into ops.persons (display_name) values ('U') returning person_id").fetchone()[0]

def test_canonical_payload_immutable(conn):
    pn = f"P-{uuid.uuid4().hex[:6]}"; who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, source_format, payload_schema_version, parser_version, "
        "canonical_payload_json, review_payload_json, uploaded_by) "
        "values (%s,'decomposed_scope_sheet','1','t',%s,%s,%s) returning id",
        (pn, '{}', '{}', who)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.intake_runs set canonical_payload_json='{\"x\":1}' where id=%s", (rid,))

def test_one_active_run_per_project(conn):
    pn = f"P-{uuid.uuid4().hex[:6]}"; who = _person(conn)
    def mk(status):
        return conn.execute(
            "insert into ops.intake_runs (project_number, status, source_format, payload_schema_version, "
            "parser_version, canonical_payload_json, review_payload_json, uploaded_by) "
            "values (%s,%s,'decomposed_scope_sheet','1','t','{}','{}',%s) returning id",
            (pn, status, who)).fetchone()[0]
    mk("parsed")
    with pytest.raises(psycopg.errors.UniqueViolation):
        mk("reviewing")

# NB: each failing statement aborts the txn, so a single test cannot chain two pytest.raises on the
# same `conn` (the 2nd would see InFailedSqlTransaction, not the specific error). Split per assertion.
def test_approved_at_is_set_once(conn):
    who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, status, source_format, payload_schema_version, parser_version,"
        " canonical_payload_json, review_payload_json, uploaded_by, approved_by, approved_at) "
        "values ('PA','approved','decomposed_scope_sheet','1','t','{}','{}',%s,%s, now()) returning id",
        (who, who)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):                      # approved_at is set-once
        conn.execute("update ops.intake_runs set approved_at = now() + interval '1 day' where id=%s", (rid,))

def test_source_file_byte_size_integrity(conn):
    who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, source_format, payload_schema_version, parser_version,"
        " canonical_payload_json, review_payload_json, uploaded_by) "
        "values ('PB','decomposed_scope_sheet','1','t','{}','{}',%s) returning id", (who,)).fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):                     # octet_length(raw_bytes) must == byte_size
        conn.execute(
            "insert into ops.intake_source_files (run_id, filename, content_type, byte_size, sha256, raw_bytes) "
            "values (%s,'f.xlsm','xlsm', 999, 'x', %s)", (rid, b"short"))
