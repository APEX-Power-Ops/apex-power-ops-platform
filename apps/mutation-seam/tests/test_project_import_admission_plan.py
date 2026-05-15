import base64
import json

from openpyxl import Workbook

from app.project_import_admission_plan import build_project_import_admission_plan, load_project_import_admission_plan
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


def test_build_project_import_admission_plan_defines_future_import_gate(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    plan = build_project_import_admission_plan(candidate)

    assert plan["admission_plan_id"] == "pm-import-candidate-miner-temp-power-admission-plan"
    assert plan["mutation_authority"] == "not_admitted"
    assert plan["review_status"] == "read_only_admission_design"
    assert plan["candidate_shape_fingerprint"]
    assert plan["source_stat_fingerprint"] == candidate["source_freshness"]["aggregate_fingerprint"]
    assert plan["target_row_plan"]["project_rows"] == 1
    assert plan["target_row_plan"]["task_rows"] == 2
    assert plan["target_row_plan"]["apparatus_rows"] == 3
    assert plan["approval_record_contract"]["storage_authority"] == "not_admitted"
    assert "source_stat_fingerprint" in plan["approval_record_contract"]["required_fields"]
    assert plan["idempotency_plan"]["sample_key"].startswith("pm-import:")
    assert {check["check_id"] for check in plan["preview_to_import_diff_checks"]} >= {
        "candidate-id-version-match",
        "source-stat-fingerprint-match",
        "candidate-shape-fingerprint-match",
    }
    no_go_by_id = {check["check_id"]: check for check in plan["no_go_checks"]}
    assert no_go_by_id["mutation-path-not-admitted"]["status"] == "no_go"
    assert no_go_by_id["approval-record-required"]["status"] == "pending_future_admission"
    assert "write_supabase" in plan["not_allowed_now"]


def test_project_import_admission_plan_route_returns_read_only_plan(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()

    response = client.get("/api/v1/reads/project-import-admission-plan", headers=_make_token())

    assert response.status_code == 200
    plan = response.json()
    assert plan["candidate_id"] == "pm-import-candidate-miner-temp-power"
    assert plan["mutation_authority"] == "not_admitted"
    assert plan["target_row_plan"]["task_rows"] == 2
    assert plan["idempotency_plan"]["strategy"] == "candidate_version_source_shape_counts"
    assert "persist_approval_record" in plan["not_allowed_now"]
    assert plan["approval_record_contract"]["minimum_expected_values"]["candidate_id"] == plan["candidate_id"]
