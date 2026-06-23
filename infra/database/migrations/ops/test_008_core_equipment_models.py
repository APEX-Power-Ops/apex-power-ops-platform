# test_008_core_equipment_models.py — MIRRORS test_007's DSN/guard/fixture idiom; runs on ops_test ONLY.
import hashlib, json, os, pathlib, uuid
import psycopg, pytest
from psycopg.conninfo import conninfo_to_dict
HERE = pathlib.Path(__file__).parent
DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "step-4a migration tests run on ops_test ONLY"
DOWN1 = HERE / "001_identity_skeleton_down.sql"
CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
         "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql",
         "007_intake_envelope.sql","008_core_equipment_models.sql"]   # 008 appended to the lane chain

def _exec(path):                            # autocommit, lane idiom (test_007)
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))

def _clean_slate():
    # idempotent pre-clean: 001_down drops `ops` (cascade, taking the 008 FK with it); the 008
    # objects live in their own `core` schema, so clear that too. Mirrors the lane idiom of running
    # the (idempotent, IF EXISTS) downs before an up so re-runs start from a clean DB.
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("drop schema if exists core cascade")
    _exec(DOWN1)

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with psycopg.connect(DSN) as c, c.cursor() as cur:       # review must-fix #1: hard runtime guard
        cur.execute("select current_database()")
        assert cur.fetchone()[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _clean_slate()
    for f in CHAIN: _exec(HERE / f)         # applies 001..008
    yield
    _clean_slate()

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

# Every test below takes `conn` (auto-rollback); the session fixture already applied 001..008.
# Use a SAVEPOINT only to survive an expected constraint error. Reversibility (Task 4) uses _exec(down/up).

def test_db_is_ops_test(conn):
    with conn.cursor() as cur:
        cur.execute("select current_database()"); assert cur.fetchone()[0] == "ops_test"

def test_core_schema_table_enums_present(conn):
    with conn.cursor() as cur:
        cur.execute("select 1 from information_schema.schemata where schema_name='core'")
        assert cur.fetchone()
        cur.execute("select count(*) from core.equipment_models"); assert cur.fetchone()[0] == 120
        cur.execute("select count(*) from core.equipment_models where unit_of_issue='set'"); assert cur.fetchone()[0] == 4
        cur.execute("select count(distinct model_key) from core.equipment_models"); assert cur.fetchone()[0] == 120

def test_seed_source_sha256_pinned():
    raw = (HERE / "008_equipment_models.seed.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "dfe59bc3c35a6d74388ca9b703fa276bc7ef9d184c973dfb9c0cc4e288a8c8d1"

def test_seed_values_match_source_field_by_field():   # review must-fix #4
    models = json.loads((HERE / "008_equipment_models.seed.json").read_bytes())
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        for m in models:
            cur.execute("""select apparatus, neta_section_ats, neta_section_mts,
                                  ref_hours_ats, ref_hours_mts, unit_of_issue, lifecycle_status
                           from core.equipment_models where model_key=%s""", (m["ref"],))
            row = cur.fetchone()
            assert row is not None, f"missing model_key {m['ref']!r}"
            ap, na, nm, ra, rm, uoi, life = row
            assert ap == m["apparatus"]
            assert na == m["neta_section"].get("ATS") and nm == m["neta_section"].get("MTS")
            assert (float(ra) if ra is not None else None) == m["ref_hours"].get("ATS")
            assert (float(rm) if rm is not None else None) == m["ref_hours"].get("MTS")
            assert uoi == m["unit_of_issue"] and life == m["lifecycle_status"]

def test_committed_seed_block_matches_generator():    # review should-fix #5(c) + operator audit: EXACT block
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen008", HERE / "gen_008_seed.py")
    gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    sql = (HERE / "008_core_equipment_models.sql").read_text()
    BEGIN = "-- SEED:BEGIN (exact gen_008_seed.py emit_inserts() output — sentinel-bounded, tested byte-equal)\n"
    END = "\n-- SEED:END"
    assert sql.count("-- SEED:BEGIN") == 1 and sql.count("-- SEED:END") == 1, "exactly one sentinel-bounded seed block"
    block = sql.split(BEGIN, 1)[1].split(END, 1)[0] + "\n"
    assert block == gen.emit_inserts(), "committed seed block != generator output (must be byte-exact)"
    assert block.count("insert into core.equipment_models") == 120, "seed block must hold EXACTLY 120 inserts"

def test_resolver_by_id_and_model_key_and_merge(): # must-fix #3 + true-terminal + operator audit: id entry
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select id, model_key from core.equipment_models order by model_key limit 2")
        (a_id, a_key), (b_id, b_key) = cur.fetchall()
        # entry by model_key AND by id both resolve to self (active)
        cur.execute("select resolved_id, resolved_model_key from core.v_equipment_models_resolved where requested_model_key=%s", (a_key,))
        assert cur.fetchone() == (a_id, a_key)
        cur.execute("select resolved_id from core.v_equipment_models_resolved where requested_id=%s", (a_id,))
        assert cur.fetchone() == (a_id,)
        # merge A -> B (savepoint); BOTH the model_key and the ORIGIN id redirect to terminal B
        cur.execute("update core.equipment_models set lifecycle_status='merged', merged_into_id=%s where id=%s", (b_id, a_id))
        cur.execute("select resolved_id, resolved_model_key from core.v_equipment_models_resolved where requested_model_key=%s", (a_key,))
        assert cur.fetchone() == (b_id, b_key)
        cur.execute("select resolved_id from core.v_equipment_models_resolved where requested_id=%s", (a_id,))
        assert cur.fetchone() == (b_id,)
        c.rollback()

def test_resolver_active_only_terminal(): # operator audit: chase only to an ACTIVE identity
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select id, model_key from core.equipment_models order by model_key limit 2")
        (a_id, _), (b_id, _) = cur.fetchall()
        # B deprecated (leaf); A merged -> B. A resolves to NO row (terminal not active); B (deprecated leaf) too.
        cur.execute("update core.equipment_models set lifecycle_status='deprecated' where id=%s", (b_id,))
        cur.execute("update core.equipment_models set lifecycle_status='merged', merged_into_id=%s where id=%s", (b_id, a_id))
        cur.execute("select count(*) from core.v_equipment_models_resolved where requested_id=%s", (a_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("select count(*) from core.v_equipment_models_resolved where requested_id=%s", (b_id,))
        assert cur.fetchone()[0] == 0
        c.rollback()

def test_every_resolution_terminates_at_active(): # review nit #10
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select count(*) from core.v_equipment_models_resolved where lifecycle_status <> 'active'")
        assert cur.fetchone()[0] == 0
        cur.execute("select count(*) from core.equipment_models"), cur.fetchone()
        cur.execute("select count(distinct requested_id) from core.v_equipment_models_resolved")
        assert cur.fetchone()[0] == 120   # every (active) origin resolves to exactly one terminal

def test_resolver_cycle_yields_no_row(): # review nit #8
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select id from core.equipment_models order by model_key limit 2")
        a_id, b_id = (r[0] for r in cur.fetchall())
        cur.execute("update core.equipment_models set lifecycle_status='merged', merged_into_id=%s where id=%s", (b_id, a_id))
        cur.execute("update core.equipment_models set lifecycle_status='merged', merged_into_id=%s where id=%s", (a_id, b_id))
        cur.execute("select count(*) from core.v_equipment_models_resolved where requested_id in (%s,%s)", (a_id, b_id))
        assert cur.fetchone()[0] == 0   # a cycle resolves to NO terminal, not a silent wrong row
        c.rollback()

def test_apparatus_fk_present_nullable_enforced(): # review must-fix #2
    import uuid
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select is_nullable from information_schema.columns where table_schema='ops' and table_name='apparatus' and column_name='equipment_model_ref'")
        assert cur.fetchone()[0] == "YES"
        # verify the FK constrains the RIGHT column AND references the RIGHT target (not just a name)
        cur.execute("""select kcu.column_name, ccu.table_schema, ccu.table_name, ccu.column_name
                       from information_schema.table_constraints tc
                       join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name
                       join information_schema.constraint_column_usage ccu on ccu.constraint_name=tc.constraint_name
                       where tc.constraint_name='apparatus_equipment_model_ref_fkey' and tc.constraint_type='FOREIGN KEY'""")
        assert cur.fetchone() == ("equipment_model_ref", "core", "equipment_models", "id")
        # ENFORCEMENT: self-seed a scope, attempt a bogus ref, assert it is rejected (unconditional)
        cur.execute("savepoint s")
        cur.execute("insert into ops.projects (project_number, project_name) values ('STEP4A-TEST','t') returning id")
        proj = cur.fetchone()[0]
        cur.execute("insert into ops.scopes (project_id, scope_name) values (%s,'t') returning id", (proj,))
        scope = cur.fetchone()[0]
        try:
            cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, equipment_model_ref) values (%s,'X',%s)", (scope, str(uuid.uuid4())))
            assert False, "bogus equipment_model_ref accepted — FK not enforcing"
        except psycopg.errors.ForeignKeyViolation:
            pass
        cur.execute("rollback to savepoint s"); c.rollback()

def test_up_down_up_clean_and_chips_survive():   # no `conn` fixture: this test drives DDL via _exec
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select count(*) from ops.apparatus"); before = cur.fetchone()[0]
    _exec(HERE / "008_core_equipment_models_down.sql")        # DOWN (autocommit, lane idiom)
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select 1 from information_schema.schemata where schema_name='core'")
        assert cur.fetchone() is None, "core schema not dropped"
        cur.execute("select 1 from information_schema.columns where table_schema='ops' and table_name='apparatus' and column_name='equipment_model_ref'")
        assert cur.fetchone(), "down wrongly dropped the mig-001 column"
        cur.execute("select count(*) from ops.apparatus"); assert cur.fetchone()[0] == before
        cur.execute("select 1 from information_schema.table_constraints where constraint_name='apparatus_equipment_model_ref_fkey'")
        assert cur.fetchone() is None, "FK not dropped by down"
    _exec(HERE / "008_core_equipment_models.sql")             # UP again, clean (restores the session post-state)
    with psycopg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("select count(*) from core.equipment_models"); assert cur.fetchone()[0] == 120
