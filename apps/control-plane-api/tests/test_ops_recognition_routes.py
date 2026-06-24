from __future__ import annotations
import os, pathlib, subprocess, sys, uuid
import psycopg, pytest

_MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[3] / "infra/database/migrations/ops"

def _require_ops_test(dsn):
    from psycopg.conninfo import conninfo_to_dict
    assert conninfo_to_dict(dsn).get("dbname") == "ops_test", "must target ops_test"

def _dsn(): return os.environ["OPS_DEV_DSN"]

_CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
          "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql",
          "007_intake_envelope.sql","008_core_equipment_models.sql","009_recognition_bridge.sql"]

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    d=_dsn(); _require_ops_test(d)
    def run(c,p): c.execute(pathlib.Path(p).read_text(encoding="utf-8"))
    with psycopg.connect(d, autocommit=True) as c:
        c.execute("drop schema if exists core cascade")
        run(c, _MIGRATIONS_DIR/"001_identity_skeleton_down.sql")
    with psycopg.connect(d, autocommit=True) as c:
        for n in _CHAIN: run(c, _MIGRATIONS_DIR/n)
    yield
    with psycopg.connect(d, autocommit=True) as c:
        c.execute("drop schema if exists core cascade")
        run(c, _MIGRATIONS_DIR/"001_identity_skeleton_down.sql")

@pytest.fixture
def person_id():
    with psycopg.connect(_dsn(), autocommit=True) as c:
        return str(c.execute("insert into ops.persons (display_name) values ('PM') returning person_id").fetchone()[0])

@pytest.fixture
def eligible(person_id):
    with psycopg.connect(_dsn(), autocommit=True) as c, c.cursor() as cur:
        cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                    " values (%s,'P','Active','approved') returning id, project_number",(f"P-{uuid.uuid4().hex[:8]}",))
        pid, pnum=cur.fetchone()
        cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                    " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
        sid=cur.fetchone()[0]
        cur.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
                    "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())",(sid,))
        cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                    "quoted_hours,quoted_revenue,source) values (%s,'A','In Progress','approved',10,1500,'ops-intake') returning id",(sid,))
        aid=str(cur.fetchone()[0])
    return {"apparatus_id": aid, "project_number": pnum}

@pytest.fixture(scope="session")
def client(apply_migrations):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)

def _contains(obj, sub):
    if isinstance(obj,str): return sub in obj
    if isinstance(obj,dict): return any(_contains(v,sub) for v in obj.values())
    if isinstance(obj,(list,tuple)): return any(_contains(v,sub) for v in obj)
    return False

def test_recognition_router_host_gated_subprocess():
    """With OPS_DEV_DSN unset, the recognition routes are NOT mounted (404), mirroring the
    intake host-gating. Run a fresh interpreter with the env var removed."""
    env={k:v for k,v in os.environ.items() if k!="OPS_DEV_DSN"}
    code=("import os; os.environ.pop('OPS_DEV_DSN',None);"
          "from fastapi.testclient import TestClient; from main import app;"
          "c=TestClient(app);"
          "import sys; sys.exit(0 if c.post('/api/v1/ops/recognition/completion/attest',json={}).status_code==404 else 1)")
    r=subprocess.run([sys.executable,"-c",code], cwd=str(pathlib.Path(__file__).resolve().parents[1]), env=env)
    assert r.returncode==0, "recognition routes must be absent when OPS_DEV_DSN is unset"

def test_attest_recognize_reverse_revoke_happy_path(client, eligible, person_id):
    aid=eligible["apparatus_id"]
    r=client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":aid,"attested_by":person_id,"reason":"tested ok"})
    assert r.status_code==200, r.text; att=r.json()["attestation_id"]
    r=client.post("/api/v1/ops/recognition/events/recognize",
                  json={"apparatus_id":aid,"recognized_by":person_id,
                        "datasheet_clearance":"not_applicable","datasheet_ref":None,
                        "cx_clearance":"not_applicable","cx_ref":None})
    assert r.status_code==200, r.text; ev=r.json()["event_id"]
    r=client.post(f"/api/v1/ops/recognition/events/{ev}/reverse",
                  json={"reversed_by":person_id,"reason":"correction"})
    assert r.status_code==200, r.text
    r=client.post(f"/api/v1/ops/recognition/completion/{att}/revoke",
                  json={"revoked_by":person_id,"reason":"superseded"})
    assert r.status_code==200, r.text

def test_attest_unknown_actor_returns_400(client, eligible):
    r=client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":eligible["apparatus_id"],"attested_by":str(uuid.uuid4()),"reason":"x"})
    assert r.status_code==400, r.text

def test_recognize_out_of_enum_clearance_returns_400_value_free(client, eligible, person_id):
    aid=eligible["apparatus_id"]
    client.post("/api/v1/ops/recognition/completion/attest",
                json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
    r=client.post("/api/v1/ops/recognition/events/recognize",
                  json={"apparatus_id":aid,"recognized_by":person_id,
                        "datasheet_clearance":"bogus_value","datasheet_ref":None,
                        "cx_clearance":"not_applicable","cx_ref":None})
    assert r.status_code==400, r.text
    assert not _contains(r.json(),"bogus_value") and not _contains(r.json(),"$")

def test_second_active_attest_returns_409(client, eligible, person_id):
    aid=eligible["apparatus_id"]
    client.post("/api/v1/ops/recognition/completion/attest",
                json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
    r=client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":aid,"attested_by":person_id,"reason":"y"})
    assert r.status_code==409, r.text

def test_worklist_and_rollup_read(client, eligible, person_id):
    aid=eligible["apparatus_id"]; pnum=eligible["project_number"]
    client.post("/api/v1/ops/recognition/completion/attest",
                json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
    client.post("/api/v1/ops/recognition/events/recognize",
                json={"apparatus_id":aid,"recognized_by":person_id,
                      "datasheet_clearance":"not_applicable","datasheet_ref":None,
                      "cx_clearance":"not_applicable","cx_ref":None})
    w=client.get(f"/api/v1/ops/recognition/worklist?project_number={pnum}")
    assert w.status_code==200 and any(row["apparatus_id"]==aid for row in w.json())
    ro=client.get(f"/api/v1/ops/recognition/rollup?project_number={pnum}")
    assert ro.status_code==200 and any(float(r["recognized_total"])>0 for r in ro.json())
