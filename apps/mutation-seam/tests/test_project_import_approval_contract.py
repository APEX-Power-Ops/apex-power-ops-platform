import base64
import json

from openpyxl import Workbook

from app.project_import_admission_plan import build_project_import_admission_plan
from app.project_import_approval_contract import (
    build_project_import_approval_contract,
    validate_project_import_approval_payload,
)
from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


def _make_token() -> dict[str, str]:
    payload = {
        "actor_id": "pm-001",
        "actor_role": "pm",
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _clear_all_caches() -> None:
    clear_project_import_candidate_cache()
    clear_project_seed_cache()
    clear_project_tracker_cache()
    clear_seed_cache()


def _write_candidate_estimator(path):
    workbook = Workbook()
    try:
        sheet = workbook.active
        sheet.title = "Updated"
        sheet.append([])
        sheet.append([None, "Updated"])
        sheet.append([None, None, "NETA", None, "Miner Temp Power", "SLD: E01-00, E01-01"])
        sheet.append([None, None, "ATS", None, "Santa Teresa, NM", "Dated: 03/05/2026"])
        sheet.append([None, None, "QTY", "Section", "Apparatus Type", "Designation", "Notes", None, "Hrs/Unit", "Hrs/Line"])
        sheet.append([None, None, 2, "Temp Power", "Switch MV - Fused Disconnect", "PD-1", "E01-00", None, 2.5, 5])
        sheet.append([None, None, 1, "Temp Power", "Panelboard LV", None, None, None, 1.5, 1.5])
        workbook.save(path)
    finally:
        workbook.close()


def _approval_payload_from_contract(contract: dict) -> dict:
    expected = contract["minimum_expected_values"]
    return {
        "candidate_id": expected["candidate_id"],
        "candidate_version": expected["candidate_version"],
        "source_stat_fingerprint": expected["source_stat_fingerprint"],
        "candidate_shape_fingerprint": expected["candidate_shape_fingerprint"],
        "idempotency_key": expected["idempotency_key"],
        "decision": "approve_for_import_packet",
        "approved_by_actor_id": "pm-001",
        "approved_at_utc": "2026-05-15T20:00:00Z",
        "accepted_warning_codes": list(expected["accepted_warning_codes"]),
        "accepted_no_go_overrides": list(expected["accepted_no_go_overrides"]),
        "review_notes": "PM accepted candidate warnings for future import packet authoring only.",
    }


def test_build_project_import_approval_contract_defines_persistence_without_admitting_writes(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    plan = build_project_import_admission_plan(candidate)
    contract = build_project_import_approval_contract(plan)

    assert contract["approval_contract_id"] == "pm-import-candidate-miner-temp-power-approval-persistence-contract"
    assert contract["approval_contract_version"] == "pm_import_approval_persistence_contract_read_only_v1"
    assert contract["mutation_authority"] == "not_admitted"
    assert contract["persistence_authority"] == "design_only_not_admitted"
    assert contract["storage_decision"] == "pending_future_packet"
    assert contract["minimum_expected_values"]["candidate_id"] == plan["candidate_id"]
    assert contract["minimum_expected_values"]["idempotency_key"] == plan["idempotency_plan"]["sample_key"]
    assert "source-files-are-accounted-for" in contract["minimum_expected_values"]["accepted_no_go_overrides"]
    assert "warnings-reviewed-by-pm" in contract["minimum_expected_values"]["accepted_no_go_overrides"]
    assert "mutation-path-not-admitted" in contract["human_acceptance_policy"]["non_overridable_check_ids"]
    assert contract["future_mutation_contract"]["current_authority"] == "not_admitted"
    assert "persist_approval_record" in contract["not_allowed_now"]
    assert "import_project_rows" in contract["not_allowed_now"]


def test_project_import_approval_payload_validator_accepts_current_contract_payload(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    plan = build_project_import_admission_plan(candidate)
    contract = build_project_import_approval_contract(plan)
    payload = _approval_payload_from_contract(contract)

    result = validate_project_import_approval_payload(payload, contract)

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["mutation_authority"] == "not_admitted"
    assert result["persistence_authority"] == "design_only_not_admitted"


def test_project_import_approval_payload_validator_rejects_stale_or_unsupported_payload(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    plan = build_project_import_admission_plan(candidate)
    contract = build_project_import_approval_contract(plan)
    payload = _approval_payload_from_contract(contract)
    payload["source_stat_fingerprint"] = "stale-source"
    payload["accepted_warning_codes"] = []
    payload["accepted_no_go_overrides"] = ["mutation-path-not-admitted"]
    payload["decision"] = "force_import"
    payload["review_notes"] = ""

    result = validate_project_import_approval_payload(payload, contract)

    assert result["valid"] is False
    error_codes = {error["code"] for error in result["errors"]}
    assert "unsupported_decision" in error_codes
    assert "stale_source_stat_fingerprint" in error_codes
    assert "warning_code_set_mismatch" in error_codes
    assert "human_acceptance_set_mismatch" in error_codes
    assert "non_overridable_check_acknowledged" in error_codes
    assert "review_notes_required" in error_codes


def test_project_import_approval_contract_route_returns_read_only_contract(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()

    response = client.get("/api/v1/reads/project-import-approval-contract", headers=_make_token())

    assert response.status_code == 200
    contract = response.json()
    assert contract["candidate_id"] == "pm-import-candidate-miner-temp-power"
    assert contract["mutation_authority"] == "not_admitted"
    assert contract["persistence_authority"] == "design_only_not_admitted"
    assert contract["decision_payload_template"]["decision"] == "approve_for_import_packet"
    assert "write_supabase" in contract["not_allowed_now"]
