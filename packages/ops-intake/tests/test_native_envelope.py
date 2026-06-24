from decimal import Decimal
from ops_intake.native import validate_envelope, pivot_to_intake_payload, recompute_content_hash

def _catalog_env(**over):
    env = {
        "project_number": "JOB-1", "envelope_id": "env-1", "quote_version": 1,
        "content_hash": "abc", "source_draft_id": "d1", "source_revision_id": "r1",
        "totals": {"bid_cents": 100000, "service_hours": 0},
        "scopes": [{
            "scope_id": "S1", "name": "A1", "neta_standard": "ATS",
            "replication_m4": 1, "adjustment_multiplier_n4": 1,
            "scope_totals": {"onsite_labor_cents": 100000, "offsite_labor_cents": 0,
                             "cost_cents": 0, "service_cents": 0, "quoted_app_hours": 6,
                             "adjusted_cents": 100000},
            "lines": [{
                "line_uid": "S1:row1", "line_kind": "catalog", "included": True,
                "equipment_model_ref": "MV-CB-01", "base_qty": 3, "project_intake_qty": 3,
                "resolved_ref_hours": 2.0, "resolved_hours": 6.0,
            }],
        }],
    }
    env.update(over)
    return env

def _codes(findings):
    return {f.code for f in findings if not f.ok}

def test_clean_catalog_envelope_has_no_blocking():
    assert _codes(validate_envelope(_catalog_env())) == set()

def test_missing_project_number_rejects():
    assert "missing_project_number" in _codes(validate_envelope(_catalog_env(project_number=None)))

def test_non_catalog_line_rejects():
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["line_kind"] = "service"
    assert "non_catalog_line" in _codes(validate_envelope(env))

def test_nonzero_service_total_rejects():
    env = _catalog_env()
    env["scopes"][0]["scope_totals"]["service_cents"] = 500
    assert "nonzero_service" in _codes(validate_envelope(env))

def test_nonzero_cost_total_rejects():
    env = _catalog_env()
    env["scopes"][0]["scope_totals"]["cost_cents"] = 500
    assert "nonzero_cost" in _codes(validate_envelope(env))

def test_m4_not_one_rejects():
    env = _catalog_env()
    env["scopes"][0]["replication_m4"] = 2
    assert "m4_unsupported" in _codes(validate_envelope(env))

def test_missing_required_catalog_field_rejects():
    env = _catalog_env()
    del env["scopes"][0]["lines"][0]["resolved_ref_hours"]
    assert "missing_required_catalog_field" in _codes(validate_envelope(env))

def test_invalid_line_state_rejects():
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["line_kind"] = "not_a_kind"
    assert "invalid_line_state" in _codes(validate_envelope(env))

def test_findings_are_pm_dollar_safe():
    env = _catalog_env(project_number=None)
    for f in validate_envelope(env):
        assert "$" not in f.message

def test_pivot_maps_catalog_line_fields():
    p = pivot_to_intake_payload(_catalog_env())
    assert p["project"]["project_number"] == "JOB-1"
    assert p["project"]["project_name"] == "JOB-1"              # Q-2 fallback to project_number
    assert Decimal(str(p["project"]["contract_value"])) == Decimal("1000.00")  # 100000 cents -> numeric dollars
    s = p["scopes"][0]
    assert s["scope_name"] == "A1"
    assert Decimal(str(s["quote"]["onsite_labor"])) == Decimal("1000.00")
    assert Decimal(str(s["quote"]["travel"])) == Decimal("0") and Decimal(str(s["quote"]["outside_services"])) == Decimal("0")
    assert Decimal(str(s["quote"]["unit_multiplier"])) == Decimal("1") and Decimal(str(s["quote"]["pct_adjust"])) == Decimal("1")
    assert s["quote"]["total_quoted_hours"] == 6
    ln = s["lines"][0]
    assert ln["apparatus_type"] == "MV-CB-01"                   # model-key string (re-resolved at approve)
    assert ln["test_standard"] == "ATS"                         # scope.neta_standard fan-out
    assert ln["qty"] == 3                                       # base_qty (== project_intake_qty at M4==1)
    assert ln["hrs_per_unit"] == 2.0                            # resolved_ref_hours
    assert ln["catalog_default_hours"] == 2.0
    assert ln["line_uid"] == "S1:row1"
    assert ln["section"] is None                                # envelope has no section -> __ungrouped__

def test_pivot_output_is_intake_payload_shaped():
    from ops_intake.envelope import _payload_from_dict
    obj = _payload_from_dict(pivot_to_intake_payload(_catalog_env()))
    assert obj.project.project_number == "JOB-1"
    assert obj.scopes[0].lines[0].apparatus_type == "MV-CB-01"

def test_content_hash_is_deterministic_and_ignores_client_hash():
    a = recompute_content_hash(_catalog_env(content_hash="abc"))
    b = recompute_content_hash(_catalog_env(content_hash="DIFFERENT"))
    assert a == b and len(a) == 64

def test_pivot_payload_reconstructs_with_numeric_money_arithmetic():
    from decimal import Decimal
    from ops_intake.envelope import _payload_from_dict
    obj = _payload_from_dict(pivot_to_intake_payload(_catalog_env()))
    # adjusted_total = (onsite+offsite+travel+outside) * unit_multiplier * pct_adjust
    # must COMPUTE (numeric money), not raise TypeError on string money.
    assert Decimal(str(obj.scopes[0].quote.adjusted_total)) == Decimal("1000.00")

import psycopg
from ops_intake.envelope import create_run_native

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('N') returning person_id").fetchone()[0]

def test_create_run_native_persists_columns(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    out = create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())
    assert out["status"] == "parsed" and out["source_format"] == "native"
    with psycopg.connect(dsn) as c:
        row = c.execute(
            "select source_format, payload_schema_version, parser_version, envelope_id, quote_version,"
            " content_hash, source_draft_id, source_revision_id,"
            " canonical_payload_json = review_payload_json as same, estimate_envelope_json is not null as has_sidecar"
            " from ops.intake_runs where id=%s", (out["run_id"],)).fetchone()
    assert row[0] == "native" and row[1] == "estimate_envelope_v1" and row[3] == "env-1" and row[4] == 1
    assert row[8] is True            # canonical == review (C2: patch_review compatibility)
    assert row[9] is True            # raw envelope only in the sidecar

def test_create_run_native_rejects_non_catalog_without_domain_writes(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    env = _catalog_env(); env["scopes"][0]["lines"][0]["line_kind"] = "service"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected"
    assert any(f["code"] == "non_catalog_line" and not f["ok"] for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0   # no domain writes

def test_create_run_native_idempotent_on_content_hash(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())
    import pytest
    from ops_intake.envelope import ActiveRunExists
    with pytest.raises(ActiveRunExists):
        create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())  # same content_hash
