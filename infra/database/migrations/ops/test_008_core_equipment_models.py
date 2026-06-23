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

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    with psycopg.connect(DSN) as c, c.cursor() as cur:       # review must-fix #1: hard runtime guard
        cur.execute("select current_database()")
        assert cur.fetchone()[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
    _exec(DOWN1)
    for f in CHAIN: _exec(HERE / f)         # applies 001..008
    yield
    _exec(DOWN1)

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
