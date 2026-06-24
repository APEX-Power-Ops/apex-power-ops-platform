from decimal import Decimal
from ops_intake.native import validate_envelope, pivot_to_intake_payload, recompute_content_hash

def _catalog_env(**over):
    env = {
        "schema_version": "estimate_envelope_v1", "source_kind": "native",
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

def test_create_run_native_idempotent_on_project_quote_version(clean_ops):
    # Idempotency is anchored on (project_number, quote_version) — C6-RESOLVED.
    # Submitting the SAME envelope (same project_number + same quote_version=1) a second time
    # must raise ActiveRunExists (via uq_intake_runs_proj_quote_version_native).
    dsn = clean_ops; who = _person(dsn)
    create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())
    import pytest
    from ops_intake.envelope import ActiveRunExists
    with pytest.raises(ActiveRunExists):
        create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())  # same (project_number, quote_version)


def test_native_new_quote_version_same_economics_allowed(clean_ops):
    # C6 fix proof: two legitimate quote-versions with IDENTICAL economics must NOT collide.
    # v1 and v2 share the same economics (same content_hash) but have different quote_version
    # and different envelope_id. The second call must succeed and return a new parsed run.
    import pytest
    from ops_intake.envelope import ActiveRunExists
    dsn = clean_ops; who = _person(dsn)
    env_v1 = _catalog_env()  # quote_version=1, envelope_id="env-1"
    out1 = create_run_native(dsn, uploaded_by=who, envelope=env_v1)
    assert out1["status"] == "parsed"
    # v2: identical economics, different quote_version + envelope_id
    env_v2 = _catalog_env(quote_version=2, envelope_id="env-2")
    out2 = create_run_native(dsn, uploaded_by=who, envelope=env_v2)
    assert out2["status"] == "parsed"
    assert out2["run_id"] != out1["run_id"]  # a NEW run was created (not the same)

from ops_intake.approve import approve_run

def _seeded_env(model_key="Capcitors - Per Unit"):
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["equipment_model_ref"] = model_key
    return env

def test_native_approve_materializes_and_reconciles(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    env = _seeded_env()
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", out["findings"]
    res = approve_run(dsn, out["run_id"], approved_by=who)
    assert res["outcome"] == "approved", res
    with psycopg.connect(dsn) as c:
        # exact projection: 3 apparatus (base_qty=3, M4=1), one scope_quote_line, frozen quote
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 3
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 1
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        assert c.execute("select status from ops.intake_runs where id=%s", (out["run_id"],)).fetchone()[0] == "approved"
        # +/-1c reconciliation: envelope bid_cents vs sum(scope_quote.adjusted_total)
        adj = c.execute("select coalesce(sum(adjusted_total),0) from ops.scope_quote").fetchone()[0]
    bid = Decimal(env["totals"]["bid_cents"]) / Decimal(100)
    assert abs(Decimal(str(adj)) - bid) <= Decimal("0.01"), (adj, bid)

def test_native_patch_review_compatible(clean_ops):
    """canonical==review flat shape -> patch_review's allowlist accepts an editable-field change."""
    dsn = clean_ops; who = _person(dsn)
    from ops_intake.envelope import get_run, patch_review
    out = create_run_native(dsn, uploaded_by=who, envelope=_seeded_env())
    run = get_run(dsn, out["run_id"])
    review = run["review_payload"]
    review["scopes"][0]["lines"][0]["hrs_per_unit"] = 2.5    # _LINE_MUTABLE field -> allowed
    patched = patch_review(dsn, out["run_id"], review_payload=review)
    assert patched["review_payload_version"] == 2


# ---------------------------------------------------------------------------
# Hardening A -- new BLOCKING guards (scope/line/total fields)
# ---------------------------------------------------------------------------

def _deep_copy_env():
    """Return a fresh deep copy of the clean catalog env to avoid test cross-contamination."""
    import copy
    return copy.deepcopy(_catalog_env())


def test_missing_scope_name_rejects():
    env = _deep_copy_env()
    del env["scopes"][0]["name"]
    assert "missing_scope_name" in _codes(validate_envelope(env))


def test_missing_scope_id_rejects():
    env = _deep_copy_env()
    del env["scopes"][0]["scope_id"]
    assert "missing_scope_id" in _codes(validate_envelope(env))


def test_missing_neta_standard_rejects():
    env = _deep_copy_env()
    del env["scopes"][0]["neta_standard"]
    assert "missing_neta_standard" in _codes(validate_envelope(env))


def test_missing_line_uid_rejects():
    env = _deep_copy_env()
    del env["scopes"][0]["lines"][0]["line_uid"]
    assert "missing_line_uid" in _codes(validate_envelope(env))


def test_non_numeric_base_qty_rejects():
    env = _deep_copy_env()
    env["scopes"][0]["lines"][0]["base_qty"] = "abc"
    assert "malformed_catalog_field" in _codes(validate_envelope(env))


def test_qty_mismatch_rejects():
    env = _deep_copy_env()
    env["scopes"][0]["lines"][0]["base_qty"] = 3
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 5
    assert "qty_mismatch" in _codes(validate_envelope(env))


def test_malformed_total_rejects():
    env = _deep_copy_env()
    env["totals"]["bid_cents"] = "abc"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_malformed_scope_total_adj_multiplier_rejects():
    env = _deep_copy_env()
    env["scopes"][0]["adjustment_multiplier_n4"] = "bad"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_create_run_native_rejects_malformed_without_crash(clean_ops):
    """Pivot must NEVER be reached on a malformed envelope -- verify governed reject, no exception."""
    dsn = clean_ops; who = _person(dsn)

    # Case 1: base_qty="abc" (non-numeric numeric field -> malformed_catalog_field)
    env1 = _deep_copy_env()
    env1["scopes"][0]["lines"][0]["base_qty"] = "abc"
    out1 = create_run_native(dsn, uploaded_by=who, envelope=env1)
    assert out1["status"] == "rejected", out1
    assert any(f["code"] == "malformed_catalog_field" for f in out1["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0

    # Case 2: scope missing name (missing_scope_name)
    # Must use a different project_number AND envelope_id to avoid the
    # uq_intake_runs_proj_quote_version_native constraint (project_number, quote_version) collision.
    env2 = _deep_copy_env()
    env2["project_number"] = "JOB-MALFORMED-2"
    env2["envelope_id"] = "env-malformed-2"
    del env2["scopes"][0]["name"]
    out2 = create_run_native(dsn, uploaded_by=who, envelope=env2)
    assert out2["status"] == "rejected", out2
    assert any(f["code"] == "missing_scope_name" for f in out2["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Hardening B -- validate_payload accepts 'native' + economic reconciliation
# ---------------------------------------------------------------------------


def test_native_patch_then_approve_succeeds(clean_ops):
    """P2a: a BENIGN edit (section) -> patch_review -> approve_run must yield 'approved',
    not 'blocked_findings'. After patch, findings must NOT contain unsupported_format."""
    dsn = clean_ops
    who = _person(dsn)
    from ops_intake.envelope import get_run, patch_review

    # create a clean native run using the seeded model key
    env = _seeded_env()
    env["envelope_id"] = "env-p2a"
    env["project_number"] = "JOB-P2A"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", out.get("findings")

    # benign edit: set section on the line (a _LINE_MUTABLE field that preserves reconciliation)
    run = get_run(dsn, out["run_id"])
    review = run["review_payload"]
    review["scopes"][0]["lines"][0]["section"] = "Panel A"
    patched = patch_review(dsn, out["run_id"], review_payload=review)

    # after patch, findings at the new version must NOT include unsupported_format
    codes_after = {f["code"] for f in patched["findings"]}
    assert "unsupported_format" not in codes_after, (
        "patch_review produced unsupported_format for source_format='native': " + str(patched["findings"])
    )

    # approve must succeed (not blocked)
    res = approve_run(dsn, out["run_id"], approved_by=who)
    assert res["outcome"] == "approved", res


def test_native_inconsistent_economics_blocks_approval(clean_ops):
    """P1: bid_cents=200000 but onsite_labor_cents=100000 -> Sigma adjusted ($1000) != contract ($2000).
    create_run_native -> status='parsed' with blocking contract_total finding.
    approve_run -> outcome='blocked_findings'. ops.apparatus count == 0 (nothing materialized)."""
    dsn = clean_ops
    who = _person(dsn)

    # Build structurally-valid envelope that passes validate_envelope,
    # but has an economic mismatch: bid_cents=$2000, scope adjusted=$1000
    env = _catalog_env()
    env["project_number"] = "JOB-P1"
    env["envelope_id"] = "env-p1"
    env["quote_version"] = 99
    env["totals"]["bid_cents"] = 200000            # contract = $2000
    # scope_totals stay at 100000 (adjusted_cents=$1000) -> Sigma=$1000 != $2000

    out = create_run_native(dsn, uploaded_by=who, envelope=env)

    # Must be parsed (not rejected) — the envelope structure is valid
    assert out["status"] == "parsed", out.get("findings")

    # Must have a blocking contract_total finding
    blocking_codes = {f["code"] for f in out["findings"] if not f["ok"] and f["severity"] == "blocking"}
    assert "contract_total" in blocking_codes, (
        "Expected blocking contract_total finding; got: " + str(out["findings"])
    )

    # approve_run must return blocked_findings (not approved)
    res = approve_run(dsn, out["run_id"], approved_by=who)
    assert res["outcome"] == "blocked_findings", res

    # nothing materialized
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Hardening D1 -- strict typed input guards + required quote_version
# ---------------------------------------------------------------------------

import copy as _copy


def _d1_env(**over):
    """Deep-copy the clean env then apply overrides (nested path support via over)."""
    return _copy.deepcopy(_catalog_env(**over))


# --- present-null / fractional guards on scope-level fields ---

def test_d1_adjustment_multiplier_null_rejects():
    """present-null adjustment_multiplier_n4 -> malformed_total (was Decimal(str(None)) crash)."""
    env = _d1_env()
    env["scopes"][0]["adjustment_multiplier_n4"] = None
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_quoted_app_hours_null_rejects():
    """present-null quoted_app_hours -> malformed_total (was None-hours arithmetic crash)."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["quoted_app_hours"] = None
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_bid_cents_fractional_rejects():
    """Fractional string bid_cents -> malformed_total (was int('100000.5') crash)."""
    env = _d1_env()
    env["totals"]["bid_cents"] = "100000.5"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_bid_cents_float_fractional_rejects():
    """Float fractional bid_cents -> malformed_total."""
    env = _d1_env()
    env["totals"]["bid_cents"] = 100000.5
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_bid_cents_negative_rejects():
    """Negative bid_cents -> malformed_total."""
    env = _d1_env()
    env["totals"]["bid_cents"] = -1
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_base_qty_fractional_rejects():
    """Fractional base_qty (1.5) -> malformed_catalog_field (was silent truncate to qty=1)."""
    env = _d1_env()
    env["scopes"][0]["lines"][0]["base_qty"] = 1.5
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 1.5
    assert "malformed_catalog_field" in _codes(validate_envelope(env))


def test_d1_project_intake_qty_fractional_rejects():
    """Fractional project_intake_qty -> malformed_catalog_field."""
    env = _d1_env()
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 2.7
    assert "malformed_catalog_field" in _codes(validate_envelope(env))


def test_d1_base_qty_negative_rejects():
    """Negative base_qty -> malformed_catalog_field."""
    env = _d1_env()
    env["scopes"][0]["lines"][0]["base_qty"] = -1
    env["scopes"][0]["lines"][0]["project_intake_qty"] = -1
    assert "malformed_catalog_field" in _codes(validate_envelope(env))


def test_d1_onsite_labor_cents_fractional_rejects():
    """Fractional onsite_labor_cents -> malformed_total."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["onsite_labor_cents"] = "50000.5"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_onsite_labor_cents_null_rejects():
    """present-null onsite_labor_cents -> malformed_total."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["onsite_labor_cents"] = None
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_offsite_labor_cents_fractional_rejects():
    """Fractional offsite_labor_cents -> malformed_total."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["offsite_labor_cents"] = 100.9
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_service_cents_non_numeric_rejects():
    """service_cents='abc' -> malformed_total (was silently zeroed, bypassed nonzero_service)."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["service_cents"] = "abc"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_cost_cents_non_numeric_rejects():
    """cost_cents='abc' -> malformed_total (was silently zeroed)."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["cost_cents"] = "abc"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d1_service_cents_non_numeric_does_not_also_fire_nonzero_service():
    """When cost_cents is non-numeric, we get malformed_total NOT nonzero_service."""
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["service_cents"] = "abc"
    codes = _codes(validate_envelope(env))
    assert "malformed_total" in codes
    # nonzero_service should NOT fire (the value is not numeric, it's already rejected)
    assert "nonzero_service" not in codes


# --- quote_version guards ---

def test_d1_quote_version_absent_passes():
    """absent quote_version (key not in envelope) -- wait, quote_version IS required in D1.
    quote_version is now REQUIRED; absent -> missing_quote_version."""
    env = _d1_env()
    del env["quote_version"]
    assert "missing_quote_version" in _codes(validate_envelope(env))


def test_d1_quote_version_none_rejects():
    """present-null quote_version -> missing_quote_version."""
    env = _d1_env()
    env["quote_version"] = None
    assert "missing_quote_version" in _codes(validate_envelope(env))


def test_d1_quote_version_string_rejects():
    """Non-integer quote_version ('abc') -> missing_quote_version."""
    env = _d1_env()
    env["quote_version"] = "abc"
    assert "missing_quote_version" in _codes(validate_envelope(env))


def test_d1_quote_version_fractional_rejects():
    """Fractional quote_version (1.5) -> missing_quote_version."""
    env = _d1_env()
    env["quote_version"] = 1.5
    assert "missing_quote_version" in _codes(validate_envelope(env))


def test_d1_quote_version_integer_string_rejects():
    """String '1' is not an integer -> missing_quote_version."""
    env = _d1_env()
    env["quote_version"] = "1"
    assert "missing_quote_version" in _codes(validate_envelope(env))


def test_d1_quote_version_integer_passes():
    """Integer quote_version passes."""
    env = _d1_env()
    env["quote_version"] = 1
    assert "missing_quote_version" not in _codes(validate_envelope(env))


def test_d1_quote_version_float_whole_passes():
    """quote_version=1.0 (float, integer-valued) -> ACCEPTED (no missing_quote_version).
    The guard uses Decimal-based integer-valued check: Decimal('1.0')==Decimal('1.0').to_integral_value()
    -> True, so 1.0 is accepted. create_run_native must also ACCEPT it (no 500) by normalizing
    to int(1) before binding to the integer column."""
    env = _d1_env()
    env["quote_version"] = 1.0
    assert "missing_quote_version" not in _codes(validate_envelope(env))


# --- create_run_native: null-version duplicate scenario (can't happen now) ---

def test_d1_null_quote_version_rejected(clean_ops):
    """quote_version=None -> rejected run (the two-NULL-runs-accepted scenario can't happen)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["quote_version"] = None
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "missing_quote_version" for f in out["findings"])


def test_d1_duplicate_rejected_submission_is_governed(clean_ops):
    """Submitting a malformed envelope (service_cents='abc') with quote_version=1 TWICE:
    both must return status='rejected', no UniqueViolation/500.
    Rejected rows store quote_version=NULL so they're excluded from the unique index."""
    dsn = clean_ops; who = _person(dsn)

    def _bad_env(pn):
        env = _d1_env()
        env["project_number"] = pn
        env["scopes"][0]["scope_totals"]["service_cents"] = "abc"
        return env

    out1 = create_run_native(dsn, uploaded_by=who, envelope=_bad_env("D1-DUP-1"))
    assert out1["status"] == "rejected", out1

    out2 = create_run_native(dsn, uploaded_by=who, envelope=_bad_env("D1-DUP-1"))
    assert out2["status"] == "rejected", out2

    # verify both rows are stored and both have NULL quote_version
    with psycopg.connect(dsn) as c:
        rows = c.execute(
            "select quote_version from ops.intake_runs where project_number='D1-DUP-1' order by uploaded_at"
        ).fetchall()
    assert len(rows) == 2, f"Expected 2 rows, got {rows}"
    assert all(r[0] is None for r in rows), f"Expected NULL quote_version for rejected rows, got {rows}"


def test_d1_adjustment_multiplier_null_create_run_native_no_crash(clean_ops):
    """present-null adjustment_multiplier_n4 -> create_run_native returns rejected (no 500)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["scopes"][0]["adjustment_multiplier_n4"] = None
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])


def test_d1_quoted_app_hours_null_create_run_native_no_crash(clean_ops):
    """present-null quoted_app_hours -> create_run_native returns rejected (no 500)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["scopes"][0]["scope_totals"]["quoted_app_hours"] = None
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])


def test_d1_bid_cents_fractional_create_run_native_no_crash(clean_ops):
    """Fractional bid_cents string -> create_run_native returns rejected (no 500)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-BID-FRAC"
    env["totals"]["bid_cents"] = "100000.5"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])


def test_d1_base_qty_fractional_create_run_native_no_crash(clean_ops):
    """Fractional base_qty -> create_run_native returns rejected (no 500)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-QTY-FRAC"
    env["scopes"][0]["lines"][0]["base_qty"] = 1.5
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 1.5
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out


# ---------------------------------------------------------------------------
# Hardening D1 FIX -- integer-valued string/float forms ACCEPTED (no 500)
# ---------------------------------------------------------------------------


def test_d1_bid_cents_integer_string_accepted(clean_ops):
    """bid_cents='100000.0' (integer-valued string) -> create_run_native ACCEPTED (status='parsed'),
    NOT a 500 crash. The pivot must coerce via Decimal so int('100000.0') path is avoided."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-INT-STR-BID"
    env["envelope_id"] = "env-int-str-bid"
    env["totals"]["bid_cents"] = "100000.0"
    # scope_totals stays at 100000 int -> consistent economics ($1000.00 == $1000.00)
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed, got {out['status']}; findings={out.get('findings')}"
    # Verify pivot produced correct dollar value
    contract_value = out["review_payload"]["project"]["contract_value"]
    from decimal import Decimal as _Decimal
    assert _Decimal(str(contract_value)) == _Decimal("1000.00"), f"Expected 1000.00, got {contract_value}"


def test_d1_bid_cents_scientific_notation_accepted(clean_ops):
    """bid_cents='1e5' (100000 in scientific notation, integer-valued string) -> ACCEPTED, $1000.00."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-INT-SCI-BID"
    env["envelope_id"] = "env-int-sci-bid"
    env["totals"]["bid_cents"] = "1e5"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    from decimal import Decimal as _Decimal
    contract_value = out["review_payload"]["project"]["contract_value"]
    assert _Decimal(str(contract_value)) == _Decimal("1000.00"), f"Expected 1000.00, got {contract_value}"


def test_d1_onsite_labor_cents_integer_string_accepted(clean_ops):
    """onsite_labor_cents='100000.0' -> ACCEPTED, materializes $1000.00."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-INT-STR-LABOR"
    env["envelope_id"] = "env-int-str-labor"
    env["scopes"][0]["scope_totals"]["onsite_labor_cents"] = "100000.0"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    from decimal import Decimal as _Decimal
    onsite = out["review_payload"]["scopes"][0]["quote"]["onsite_labor"]
    assert _Decimal(str(onsite)) == _Decimal("1000.00"), f"Expected 1000.00, got {onsite}"


def test_d1_onsite_labor_cents_sci_notation_accepted(clean_ops):
    """onsite_labor_cents='1e5' (scientific notation) -> ACCEPTED, materializes $1000.00."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-SCI-LABOR"
    env["envelope_id"] = "env-sci-labor"
    env["scopes"][0]["scope_totals"]["onsite_labor_cents"] = "1e5"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    from decimal import Decimal as _Decimal
    onsite = out["review_payload"]["scopes"][0]["quote"]["onsite_labor"]
    assert _Decimal(str(onsite)) == _Decimal("1000.00"), f"Expected 1000.00, got {onsite}"


def test_d1_base_qty_integer_string_accepted(clean_ops):
    """base_qty='3.0' + project_intake_qty='3.0' -> ACCEPTED, materializes 3 apparatus (not a crash)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-QTY-STR"
    env["envelope_id"] = "env-qty-str"
    env["scopes"][0]["lines"][0]["base_qty"] = "3.0"
    env["scopes"][0]["lines"][0]["project_intake_qty"] = "3.0"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    qty = out["review_payload"]["scopes"][0]["lines"][0]["qty"]
    assert qty == 3, f"Expected qty=3, got {qty}"


def test_d1_quote_version_float_whole_create_run_native_accepted(clean_ops):
    """quote_version=1.0 (float, integer-valued) -> create_run_native ACCEPTED (status='parsed'),
    NOT a 500 crash. The stored quote_version column must be the integer 1."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-QV-FLOAT"
    env["envelope_id"] = "env-qv-float"
    env["quote_version"] = 1.0
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    with psycopg.connect(dsn) as c:
        qv = c.execute(
            "select quote_version from ops.intake_runs where id=%s", (out["run_id"],)
        ).fetchone()[0]
    assert qv == 1, f"Expected stored quote_version=1 (int), got {qv!r}"


def test_d1_quote_version_integer_string_one_create_run_native_accepted(clean_ops):
    """quote_version='1' -> wait: validate_envelope REJECTS string quote_version.
    So this must remain a governed reject (missing_quote_version)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-QV-STR-1"
    env["envelope_id"] = "env-qv-str-1"
    env["quote_version"] = "1"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    # "1" is a STRING -> REJECT (guard explicitly rejects string quote_version)
    assert out["status"] == "rejected", f"Expected rejected for string qv; got {out['status']}"
    assert any(f["code"] == "missing_quote_version" for f in out["findings"])


def test_d1_fractional_bid_cents_still_rejected(clean_ops):
    """Regression guard: bid_cents='100000.5' is still malformed_total (fractional not accepted)."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-FRAC-GUARD"
    env["totals"]["bid_cents"] = "100000.5"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])


def test_d1_fractional_base_qty_still_rejected(clean_ops):
    """Regression guard: base_qty=1.5 still malformed_catalog_field."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-FRAC-QTY-GUARD"
    env["scopes"][0]["lines"][0]["base_qty"] = 1.5
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 1.5
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_catalog_field" for f in out["findings"])


def test_d1_fractional_quote_version_still_rejected(clean_ops):
    """Regression guard: quote_version=1.5 still missing_quote_version."""
    dsn = clean_ops; who = _person(dsn)
    env = _d1_env()
    env["project_number"] = "D1-FRAC-QV-GUARD"
    env["quote_version"] = 1.5
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "missing_quote_version" for f in out["findings"])


# ---------------------------------------------------------------------------
# Hardening D2 -- native per-scope adjusted-cents reconciliation
# ---------------------------------------------------------------------------


def test_d2_scope_adjusted_mismatch_rejects():
    """Per-scope adjusted_cents mismatch: onsite=100000, offsite=0, m4=1, n4=1
    -> derived=100000 but adjusted_cents=150000 -> scope_adjusted_mismatch blocking finding."""
    env = _copy.deepcopy(_catalog_env())
    env["scopes"][0]["scope_totals"]["adjusted_cents"] = 150000  # stated != derived (100000)
    codes = _codes(validate_envelope(env))
    assert "scope_adjusted_mismatch" in codes, f"Expected scope_adjusted_mismatch; got {codes}"


def test_d2_clean_env_no_mismatch():
    """Clean env: onsite=100000, offsite=0, m4=1, n4=1, adjusted_cents=100000
    -> derived=100000 -> NO scope_adjusted_mismatch (no over-block)."""
    env = _catalog_env()
    codes = _codes(validate_envelope(env))
    assert "scope_adjusted_mismatch" not in codes, f"Over-block: got {codes}"


def test_d2_within_tolerance_no_mismatch():
    """adjusted_cents within ±1 cent of derived -> NO scope_adjusted_mismatch."""
    env = _copy.deepcopy(_catalog_env())
    # derived = 100000 * 1 * 1 = 100000; adjusted_cents = 100001 (1 cent over, within tolerance)
    env["scopes"][0]["scope_totals"]["adjusted_cents"] = 100001
    codes = _codes(validate_envelope(env))
    assert "scope_adjusted_mismatch" not in codes, f"Unexpected mismatch within tolerance: {codes}"


def test_d2_mismatch_create_run_native_rejects(clean_ops):
    """scope_adjusted_mismatch is a blocking finding: create_run_native -> status='rejected';
    ops.scopes count == 0 (no domain writes on reject)."""
    dsn = clean_ops; who = _person(dsn)
    env = _copy.deepcopy(_catalog_env())
    env["project_number"] = "D2-MISMATCH"
    env["envelope_id"] = "env-d2-mismatch"
    env["scopes"][0]["scope_totals"]["adjusted_cents"] = 150000  # mismatch
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "scope_adjusted_mismatch" for f in out["findings"]), out["findings"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


def test_d2_malformed_adjusted_cents_does_not_double_fire(clean_ops):
    """When adjusted_cents is absent/non-numeric (malformed), the mismatch guard
    must NOT double-fire. The existing typed finding fires first; no scope_adjusted_mismatch."""
    env = _copy.deepcopy(_catalog_env())
    # Remove adjusted_cents entirely — absent field, guard should skip mismatch check
    del env["scopes"][0]["scope_totals"]["adjusted_cents"]
    codes = _codes(validate_envelope(env))
    assert "scope_adjusted_mismatch" not in codes, f"Double-fire on absent adjusted_cents: {codes}"


def test_d2_e2e_approve_still_passes(clean_ops):
    """Regression: the clean env + approve flow must still work after D2 guard is added."""
    dsn = clean_ops; who = _person(dsn)
    env = _seeded_env()
    env["project_number"] = "D2-APPROVE"
    env["envelope_id"] = "env-d2-approve"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", out["findings"]
    res = approve_run(dsn, out["run_id"], approved_by=who)
    assert res["outcome"] == "approved", res


# ---------------------------------------------------------------------------
# Hardening D3 -- schema_version/source_kind contract, service_hours,
#                  adjusted_cents required, duplicate line_uid,
#                  resolved_ref_hours coerce+nonneg
# ---------------------------------------------------------------------------


def _d3_env(**over):
    """Deep-copy the clean env (now with schema_version+source_kind) then apply overrides."""
    import copy
    return copy.deepcopy(_catalog_env(**over))


# --- Gap 1: schema_version / source_kind contract ---

def test_d3_schema_version_missing_rejects():
    """schema_version absent -> invalid_schema_version blocking."""
    env = _d3_env()
    del env["schema_version"]
    assert "invalid_schema_version" in _codes(validate_envelope(env))


def test_d3_schema_version_wrong_rejects():
    """schema_version='estimate_envelope_v2' -> invalid_schema_version blocking."""
    env = _d3_env()
    env["schema_version"] = "estimate_envelope_v2"
    assert "invalid_schema_version" in _codes(validate_envelope(env))


def test_d3_source_kind_missing_rejects():
    """source_kind absent -> invalid_source_kind blocking."""
    env = _d3_env()
    del env["source_kind"]
    assert "invalid_source_kind" in _codes(validate_envelope(env))


def test_d3_source_kind_wrong_rejects():
    """source_kind='workbook_intake' -> invalid_source_kind blocking."""
    env = _d3_env()
    env["source_kind"] = "workbook_intake"
    assert "invalid_source_kind" in _codes(validate_envelope(env))


def test_d3_schema_version_missing_create_run_rejected(clean_ops):
    """schema_version absent -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    del env["schema_version"]
    env["project_number"] = "D3-SV-MISS"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "invalid_schema_version" for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


def test_d3_source_kind_wrong_create_run_rejected(clean_ops):
    """source_kind='workbook_intake' -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    env["source_kind"] = "workbook_intake"
    env["project_number"] = "D3-SK-WRONG"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "invalid_source_kind" for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# --- Gap 2: malformed/null service_hours ---

def test_d3_service_hours_null_rejects():
    """service_hours=None (present-null) -> malformed_total (not silently zeroed)."""
    env = _d3_env()
    env["scopes"][0]["scope_totals"]["service_hours"] = None
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d3_service_hours_non_numeric_rejects():
    """service_hours='abc' -> malformed_total (was silently zeroed, bypassed nonzero_service)."""
    env = _d3_env()
    env["scopes"][0]["scope_totals"]["service_hours"] = "abc"
    assert "malformed_total" in _codes(validate_envelope(env))


def test_d3_service_hours_null_create_run_rejected(clean_ops):
    """service_hours=None -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    env["project_number"] = "D3-SH-NULL"
    env["scopes"][0]["scope_totals"]["service_hours"] = None
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


def test_d3_service_hours_non_numeric_create_run_rejected(clean_ops):
    """service_hours='abc' -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    env["project_number"] = "D3-SH-NAN"
    env["scopes"][0]["scope_totals"]["service_hours"] = "abc"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_total" for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# --- Gap 3: adjusted_cents required (no silent skip) ---

def test_d3_adjusted_cents_absent_rejects():
    """adjusted_cents absent -> blocking (no silent skip of reconciliation)."""
    env = _d3_env()
    del env["scopes"][0]["scope_totals"]["adjusted_cents"]
    codes = _codes(validate_envelope(env))
    assert "missing_adjusted_cents" in codes or "malformed_total" in codes, (
        f"Expected missing_adjusted_cents or malformed_total; got {codes}"
    )


def test_d3_adjusted_cents_non_numeric_rejects():
    """adjusted_cents='abc' -> blocking finding (was silently skipped)."""
    env = _d3_env()
    env["scopes"][0]["scope_totals"]["adjusted_cents"] = "abc"
    codes = _codes(validate_envelope(env))
    assert "missing_adjusted_cents" in codes or "malformed_total" in codes, (
        f"Expected missing_adjusted_cents or malformed_total; got {codes}"
    )


def test_d3_adjusted_cents_absent_create_run_rejected(clean_ops):
    """adjusted_cents absent -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    env["project_number"] = "D3-ADJ-MISS"
    del env["scopes"][0]["scope_totals"]["adjusted_cents"]
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


def test_d3_adjusted_cents_non_numeric_create_run_rejected(clean_ops):
    """adjusted_cents='abc' -> create_run_native returns status='rejected', no domain writes."""
    dsn = clean_ops; who = _person(dsn)
    env = _d3_env()
    env["project_number"] = "D3-ADJ-NAN"
    env["scopes"][0]["scope_totals"]["adjusted_cents"] = "abc"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# --- Gap 4: duplicate line_uid global uniqueness ---

def test_d3_duplicate_line_uid_rejects():
    """Two included catalog lines with the same line_uid -> duplicate_line_uid blocking."""
    import copy
    env = copy.deepcopy(_catalog_env())
    # Add a second scope with a line that shares the same line_uid as scope 1
    scope2 = copy.deepcopy(env["scopes"][0])
    scope2["scope_id"] = "S2"
    scope2["name"] = "A2"
    # Same line_uid "S1:row1" as scope 1's line
    env["scopes"].append(scope2)
    codes = _codes(validate_envelope(env))
    assert "duplicate_line_uid" in codes, f"Expected duplicate_line_uid; got {codes}"


def test_d3_duplicate_line_uid_within_scope_rejects():
    """Two included catalog lines in the SAME scope with the same line_uid -> duplicate_line_uid."""
    import copy
    env = copy.deepcopy(_catalog_env())
    line2 = copy.deepcopy(env["scopes"][0]["lines"][0])
    # Same line_uid "S1:row1"
    env["scopes"][0]["lines"].append(line2)
    codes = _codes(validate_envelope(env))
    assert "duplicate_line_uid" in codes, f"Expected duplicate_line_uid; got {codes}"


def test_d3_unique_line_uids_no_false_positive():
    """Two included catalog lines with DIFFERENT line_uids -> no duplicate_line_uid."""
    import copy
    env = copy.deepcopy(_catalog_env())
    line2 = copy.deepcopy(env["scopes"][0]["lines"][0])
    line2["line_uid"] = "S1:row2"
    env["scopes"][0]["lines"].append(line2)
    codes = _codes(validate_envelope(env))
    assert "duplicate_line_uid" not in codes, f"False positive duplicate_line_uid; got {codes}"


def test_d3_duplicate_line_uid_create_run_rejected(clean_ops):
    """Duplicate line_uid -> create_run_native returns status='rejected', no domain writes (not a DB 500)."""
    import copy
    dsn = clean_ops; who = _person(dsn)
    env = copy.deepcopy(_catalog_env())
    env["project_number"] = "D3-DUP-UID"
    env["envelope_id"] = "env-d3-dup-uid"
    # Add a second line with the same line_uid
    line2 = copy.deepcopy(env["scopes"][0]["lines"][0])
    env["scopes"][0]["lines"].append(line2)
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "duplicate_line_uid" for f in out["findings"]), out["findings"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# --- Gap 5: resolved_ref_hours coerce + non-negative ---

def test_d3_resolved_ref_hours_string_accepted():
    """resolved_ref_hours='10.0' (string) -> ACCEPTED by validate_envelope (no malformed_catalog_field)."""
    env = _d3_env()
    env["scopes"][0]["lines"][0]["resolved_ref_hours"] = "10.0"
    codes = _codes(validate_envelope(env))
    assert "malformed_catalog_field" not in codes, (
        f"String resolved_ref_hours should be accepted (coercible); got {codes}"
    )


def test_d3_resolved_ref_hours_negative_rejects():
    """resolved_ref_hours=-1 -> malformed_catalog_field (negative hours)."""
    env = _d3_env()
    env["scopes"][0]["lines"][0]["resolved_ref_hours"] = -1
    codes = _codes(validate_envelope(env))
    assert "malformed_catalog_field" in codes, f"Expected malformed_catalog_field; got {codes}"


def test_d3_resolved_ref_hours_string_create_run_accepted(clean_ops):
    """resolved_ref_hours='10.0' (string) -> create_run_native returns status='parsed' (NOT rejected, NOT crash)."""
    import copy
    dsn = clean_ops; who = _person(dsn)
    env = copy.deepcopy(_seeded_env())
    env["project_number"] = "D3-RRH-STR"
    env["envelope_id"] = "env-d3-rrh-str"
    env["scopes"][0]["scope_totals"]["quoted_app_hours"] = 10
    env["scopes"][0]["lines"][0]["resolved_ref_hours"] = "10.0"  # string form
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", f"Expected parsed; findings={out.get('findings')}"
    # Pivot must coerce to float — check the review_payload
    hrs = out["review_payload"]["scopes"][0]["lines"][0]["hrs_per_unit"]
    from decimal import Decimal as _D
    assert _D(str(hrs)) == _D("10.0"), f"Expected hrs_per_unit=10.0, got {hrs!r}"


def test_d3_resolved_ref_hours_negative_create_run_rejected(clean_ops):
    """resolved_ref_hours=-1 -> create_run_native returns status='rejected', no domain writes."""
    import copy
    dsn = clean_ops; who = _person(dsn)
    env = copy.deepcopy(_catalog_env())
    env["project_number"] = "D3-RRH-NEG"
    env["envelope_id"] = "env-d3-rrh-neg"
    env["scopes"][0]["lines"][0]["resolved_ref_hours"] = -1
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_catalog_field" for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Hardening D3 FIX -- zero-quantity catalog line reject
# ---------------------------------------------------------------------------


def test_native_zero_base_qty_rejects():
    """base_qty=0 / project_intake_qty=0 -> blocking malformed_catalog_field.
    An included catalog line with zero quantity is malformed: included means 'test >=1 of these'."""
    import copy
    env = copy.deepcopy(_catalog_env())
    env["scopes"][0]["lines"][0]["base_qty"] = 0
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 0
    codes = _codes(validate_envelope(env))
    assert "malformed_catalog_field" in codes, (
        f"Expected malformed_catalog_field for zero base_qty; got {codes}"
    )


def test_native_zero_base_qty_create_run_rejected(clean_ops):
    """base_qty=0 / project_intake_qty=0 -> create_run_native returns status='rejected',
    ops.scopes count == 0 (zero-qty line never reaches materialize, no 1-apparatus mis-materialize)."""
    import copy
    dsn = clean_ops; who = _person(dsn)
    env = copy.deepcopy(_catalog_env())
    env["project_number"] = "D3-ZERO-QTY"
    env["envelope_id"] = "env-d3-zero-qty"
    env["scopes"][0]["lines"][0]["base_qty"] = 0
    env["scopes"][0]["lines"][0]["project_intake_qty"] = 0
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected", out
    assert any(f["code"] == "malformed_catalog_field" for f in out["findings"]), out["findings"]
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0
