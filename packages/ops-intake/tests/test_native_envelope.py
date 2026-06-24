from ops_intake.native import validate_envelope

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
