import base64
import json

from openpyxl import Workbook

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
        sheet.append([None, None, 1, "Temp Power", "Switch MV - Fused Disconnect", "PD-1", "E01-00", None, 2.5, 2.5])
        sheet.append([None, None, 1, "Temp Power", "Panelboard LV", None, None, None, 1.5, 1.5])
        workbook.save(path)
    finally:
        workbook.close()


def _write_ground_resistance_lot_estimator(path):
    workbook = Workbook()
    try:
        sheet = workbook.active
        sheet.title = "Updated"
        sheet.append([])
        sheet.append([None, "Updated"])
        sheet.append([None, None, "NETA", None, "Miner Temp Power", "SLD: E01-00, E01-01"])
        sheet.append([None, None, "ATS", None, "Santa Teresa, NM", "Dated: 03/05/2026"])
        sheet.append([None, None, "QTY", "Section", "Apparatus Type", "Designation", "Notes", None, "Hrs/Unit", "Hrs/Line"])
        sheet.append(
            [
                None,
                None,
                3,
                "7.13",
                "Ground Resistance Test - Two-Point (Lot)",
                None,
                "E01-00, E01-01, E01-02",
                None,
                8,
                24,
            ]
        )
        workbook.save(path)
    finally:
        workbook.close()


def test_load_project_import_candidate_groups_tasks_and_preserves_traceability(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))

    assert candidate["candidate_id"] == "pm-import-candidate-miner-temp-power"
    assert candidate["mutation_authority"] == "not_admitted"
    assert candidate["review_status"] == "draft_review_only"
    assert candidate["summary"]["workpackage_count"] == 1
    assert candidate["summary"]["task_count"] == 3
    assert candidate["summary"]["apparatus_candidate_count"] == 4
    assert candidate["project"]["location"] == "Santa Teresa, NM"
    assert candidate["workpackages"][0]["task_count"] == 3
    assert candidate["workpackages"][0]["apparatus_candidate_count"] == 4
    assert candidate["workpackages"][0]["planned_hours"] == 9.0
    assert candidate["workpackages"][0]["tasks"][0]["source_ref"]["source_row"] == 6
    assert candidate["workpackages"][0]["tasks"][0]["apparatus_candidates"][0]["source_row"] == 6
    warning_codes = {warning["code"] for warning in candidate["warnings"]}
    assert "MISSING_SLD_PDF" in warning_codes
    assert "DUPLICATE_LINE_ITEM_GROUPS" in warning_codes
    assert "MISSING_DESIGNATIONS" in warning_codes
    assert "MISSING_DRAWING_REFS" in warning_codes
    assert candidate["summary"]["human_decision_count"] >= 2
    assert "write_supabase" in candidate["review_guidance"]["not_allowed_now"]
    freshness = candidate["source_freshness"]
    assert freshness["strategy"] == "path_size_mtime_fingerprint"
    assert freshness["mutation_authority"] == "not_admitted"
    assert freshness["missing_count"] >= 1
    source_files = {source["source_id"]: source for source in freshness["source_files"]}
    assert source_files["estimator_workbook"]["found"] is True
    assert source_files["estimator_workbook"]["fingerprint"]
    assert source_files["estimator_workbook"]["modified_at"].endswith("Z")
    assert source_files["sld_pdf"]["freshness_status"] == "missing"


def test_ground_resistance_lot_gets_pm_designation_without_expanding_measurements(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_ground_resistance_lot_estimator(workbook_path)
    _clear_all_caches()

    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))

    task = candidate["workpackages"][0]["tasks"][0]
    assert task["source_line_id"] == "miner-line-001"
    assert task["designation"] == "Ground Resistance Test Lot"
    assert task["quantity"] == 3
    assert task["planned_hours"] == 24.0
    assert len(task["apparatus_candidates"]) == 1
    assert task["apparatus_candidates"][0]["designation"] == "Ground Resistance Test Lot"
    assert task["apparatus_candidates"][0]["display_name"] == "Ground Resistance Test Lot"
    assert task["apparatus_candidates"][0]["planned_hours"] == 24
    assert candidate["summary"]["apparatus_candidate_count"] == 1
    warning_codes = {warning["code"] for warning in candidate["warnings"]}
    assert "MISSING_DESIGNATIONS" not in warning_codes


def test_project_import_candidate_route_returns_read_only_candidate(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()

    response = client.get("/api/v1/reads/project-import-candidate", headers=_make_token())

    assert response.status_code == 200
    candidate = response.json()
    assert candidate["mutation_authority"] == "not_admitted"
    assert candidate["summary"]["task_count"] == 3
    assert candidate["summary"]["apparatus_candidate_count"] == 4
    assert candidate["workpackages"][0]["tasks"][0]["source_ref"]["estimator_workbook_path"] == str(workbook_path)
    assert candidate["source_freshness"]["source_files"][0]["source_id"] == "estimator_workbook"
