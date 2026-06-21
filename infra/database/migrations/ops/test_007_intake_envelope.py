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

def _proj_scope(c):
    pid = c.execute("insert into ops.projects (project_number, project_name) values (%s,'p') returning id",
                    (f"P-{uuid.uuid4().hex[:6]}",)).fetchone()[0]
    s1 = c.execute("insert into ops.scopes (project_id, scope_name) values (%s,'s1') returning id",(pid,)).fetchone()[0]
    s2 = c.execute("insert into ops.scopes (project_id, scope_name) values (%s,'s2') returning id",(pid,)).fetchone()[0]
    return pid, s1, s2

def test_apparatus_task_must_match_scope(conn):
    _, s1, s2 = _proj_scope(conn)
    t1 = conn.execute("insert into ops.tasks (scope_id, task_name) values (%s,'t') returning id",(s1,)).fetchone()[0]
    # same scope: ok
    conn.execute("insert into ops.apparatus (scope_id, apparatus_designation, task_id) values (%s,'A',%s)",(s1,t1))
    # cross scope: rejected
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("insert into ops.apparatus (scope_id, apparatus_designation, task_id) values (%s,'B',%s)",(s2,t1))

def test_task_scope_immutable(conn):
    _, s1, s2 = _proj_scope(conn)
    t1 = conn.execute("insert into ops.tasks (scope_id, task_name) values (%s,'t') returning id",(s1,)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.tasks set scope_id=%s where id=%s",(s2,t1))

def test_tasks_intake_unique(conn):
    _, s1, _ = _proj_scope(conn)
    conn.execute("insert into ops.tasks (scope_id, task_name, legacy_source_id) values (%s,'t','SEC-A')",(s1,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute("insert into ops.tasks (scope_id, task_name, legacy_source_id) values (%s,'t2','SEC-A')",(s1,))

def test_source_columns_exist(conn):
    cols = conn.execute(
        "select column_name from information_schema.columns where table_schema='ops' and table_name='projects' "
        "and column_name like 'source_%'").fetchall()
    names = {r[0] for r in cols}
    assert {'source_client_name','source_site_name','source_site_address','source_site_city',
            'source_site_state','source_site_zip'} <= names


def test_down_then_up_is_idempotent_and_chips_survive():
    # apply down (007 only) then re-up; 006 objects (e.g. ops.billing_application) survive throughout.
    _exec(HERE/"007_intake_envelope_down.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        assert c.execute("select to_regclass('ops.intake_runs')").fetchone()[0] is None
        assert c.execute("select to_regclass('ops.billing_application')").fetchone()[0] is not None  # Chip 4 intact
        assert c.execute("select to_regclass('ops.scopes')").fetchone()[0] is not None               # Chip 1 intact
    _exec(HERE/"007_intake_envelope.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        assert c.execute("select to_regclass('ops.intake_runs')").fetchone()[0] is not None
