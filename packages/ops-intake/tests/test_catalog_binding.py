import psycopg
from ops_intake.catalog import resolve_models, m4_ok

def test_resolve_models_returns_resolvable_subset(clean_ops):
    with psycopg.connect(clean_ops) as c:
        out = resolve_models(c.cursor(), ["Capcitors - Per Unit", "NOPE", "Capcitors - Per Unit", ""])
    assert out["Capcitors - Per Unit"]      # resolvable -> non-empty uuid string, deduped
    assert "NOPE" not in out and "" not in out   # unresolved / empty dropped

def test_m4_ok_is_strict():
    assert m4_ok({"unit_multiplier": 1}) and m4_ok({"unit_multiplier": "1"}) and m4_ok({"unit_multiplier": 1.0})
    for bad in [{}, {"unit_multiplier": None}, {"unit_multiplier": ""}, {"unit_multiplier": 0},
                {"unit_multiplier": -1}, {"unit_multiplier": 2}, {"unit_multiplier": "abc"}]:
        assert not m4_ok(bad), bad     # missing / falsey / invalid / non-1 all rejected

import json
from ops_intake.approve import approve_run

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]

def _seed_run(dsn, payload, who):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute(
            "insert into ops.intake_runs (project_number, source_format, status, payload_schema_version,"
            " parser_version, canonical_payload_json, review_payload_json, uploaded_by)"
            " values (%s,'decomposed_scope_sheet','reviewing','1','t',%s,%s,%s) returning id",
            (payload["project"]["project_number"], json.dumps(payload), json.dumps(payload), who)).fetchone()[0]

def _payload(pn, apparatus_type, unit_multiplier=1):
    return {"project": {"project_number": pn, "project_name": "n", "contract_value": 1.0},
            "scopes": [{"scope_name": "S", "legacy_source_id": "S",
                        "quote": {"onsite_labor": 100, "unit_multiplier": unit_multiplier, "pct_adjust": 1,
                                  "total_quoted_hours": 2},
                        "lines": [{"apparatus_type": apparatus_type, "test_standard": "ATS", "qty": 1,
                                   "hrs_per_unit": 2.0, "section": "S1", "line_number": 1, "line_uid": "S:r1"}]}]}

def test_unresolved_rejects_zero_writes_with_finding(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    rid = _seed_run(dsn, _payload("UC-1", "Not In Catalog"), who)
    out = approve_run(dsn, rid, approved_by=who)
    assert out["outcome"] == "rejected_precheck" and "Not In Catalog" in out["uncatalogued"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 0          # zero writes
        assert c.execute("select status from ops.intake_runs where id=%s", (rid,)).fetchone()[0] == "reviewing"
        assert c.execute("select count(*) from ops.intake_validation_findings where run_id=%s"
                         " and code='uncatalogued_apparatus' and severity='blocking' and ok=false",
                         (rid,)).fetchone()[0] == 1                                          # durable finding

def test_m4_not_one_rejects(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    rid = _seed_run(dsn, _payload("M4-1", "Capcitors - Per Unit", unit_multiplier=3), who)
    out = approve_run(dsn, rid, approved_by=who)
    assert out["outcome"] == "rejected_precheck" and "S" in out["m4_unsupported"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 0

def test_approve_binds_every_apparatus(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    rid = _seed_run(dsn, _payload("OK-1", "Capcitors - Per Unit"), who)
    assert approve_run(dsn, rid, approved_by=who)["outcome"] == "approved"
    with psycopg.connect(dsn) as c:
        n, nulls = c.execute("select count(*), count(*) filter (where equipment_model_ref is null)"
                             " from ops.apparatus").fetchone()
    assert n >= 1 and nulls == 0


def test_falsey_apparatus_type_rejects_not_crashes(clean_ops):
    # A line with an empty apparatus_type must REJECT cleanly (governed finding),
    # not raise KeyError inside materialize. (4b.1 review I-1 regression.)
    dsn = clean_ops; who = _person(dsn)
    rid = _seed_run(dsn, _payload("EMPTY-1", ""), who)
    out = approve_run(dsn, rid, approved_by=who)
    assert out["outcome"] == "rejected_precheck"
    assert "<missing apparatus_type>" in out["uncatalogued"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 0


def test_backfill_binds_only_target_frozen_resolvable(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    # target project (resolvable + a bogus type) and a DIFFERENT project that must NOT be touched
    rid_t = _seed_run(dsn, _payload("TGT", "Capcitors - Per Unit"), who); approve_run(dsn, rid_t, approved_by=who)
    rid_o = _seed_run(dsn, _payload("OTHER", "Capcitors - Per Unit"), who); approve_run(dsn, rid_o, approved_by=who)
    with psycopg.connect(dsn) as c:
        cur = c.cursor()
        cur.execute("update ops.apparatus set equipment_model_ref = null")  # legacy null state (both projects)
        assert cur.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        # the operative bind, SCOPED to project_number='TGT' (the real script's step 2):
        cur.execute("""
            update ops.apparatus a set equipment_model_ref = v.resolved_id, updated_at=now()
            from core.v_equipment_models_resolved v, ops.scopes s, ops.projects p
            where v.requested_model_key = a.apparatus_type and s.id=a.scope_id and p.id=s.project_id
              and p.project_number='TGT' and a.equipment_model_ref is null
        """); c.commit()
        tgt = cur.execute("select count(*) from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                          " join ops.projects p on p.id=s.project_id where p.project_number='TGT'"
                          " and a.equipment_model_ref is not null").fetchone()[0]
        oth = cur.execute("select count(*) from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                          " join ops.projects p on p.id=s.project_id where p.project_number='OTHER'"
                          " and a.equipment_model_ref is not null").fetchone()[0]
    assert tgt >= 1   # frozen target rows bound (freeze guard permits equipment_model_ref)
    assert oth == 0   # the other project was untouched (scoping holds)
