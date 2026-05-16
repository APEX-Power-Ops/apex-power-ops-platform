import base64
import json

from openpyxl import Workbook

from app.project_import_admission_plan import build_project_import_admission_plan
from app.project_import_approval_contract import build_project_import_approval_contract
from app.project_import_approval_storage_plan import build_project_import_approval_storage_plan
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


def _build_storage_plan(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    _clear_all_caches()
    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    admission_plan = build_project_import_admission_plan(candidate)
    contract = build_project_import_approval_contract(admission_plan)
    return build_project_import_approval_storage_plan(contract)


def test_build_project_import_approval_storage_plan_selects_dedicated_insert_only_table(tmp_path):
    plan = _build_storage_plan(tmp_path)

    assert plan["storage_plan_id"] == "pm-import-candidate-miner-temp-power-approval-storage-plan"
    assert plan["storage_plan_version"] == "pm_import_approval_storage_plan_read_only_v1"
    assert plan["mutation_authority"] == "not_admitted"
    assert plan["persistence_authority"] == "storage_decision_only_not_admitted"
    assert plan["selected_storage_decision"] == "dedicated_insert_only_import_candidate_approval_table"
    assert plan["recommended_table"] == "seam.pm_import_candidate_approvals"
    assert plan["recommended_entity_type"] == "pm_import_candidate_approval"
    assert plan["recommended_route"] == "/api/v1/mutations/project-import-approvals"
    assert plan["record_lifecycle"]["write_model"] == "insert_once_with_idempotent_replay"
    assert "persist_approval_record" in plan["not_allowed_now"]
    assert "import_project_rows" in plan["not_allowed_now"]


def test_project_import_approval_storage_plan_rejects_unsafe_storage_options(tmp_path):
    plan = _build_storage_plan(tmp_path)

    rejected = {option["option"]: option for option in plan["rejected_storage_options"]}
    assert "audit_log_only" in rejected
    assert "reuse_issue_task_or_workpackage" in rejected
    assert "generic_pgdict_upsert_without_adapter" in rejected
    assert "direct_supabase_from_excel_or_ui" in rejected
    assert "not the canonical approval object" in rejected["audit_log_only"]["reason"]

    adapter_requirements = " ".join(plan["adapter_requirements"])
    assert "explicit approval adapter" in adapter_requirements
    assert "Do not create project, workpackage, task, apparatus" in adapter_requirements


def test_project_import_approval_storage_plan_columns_and_constraints_match_contract(tmp_path):
    plan = _build_storage_plan(tmp_path)

    columns = {column["name"]: column for column in plan["recommended_columns"]}
    assert columns["decision"]["allowed_values"] == [
        "approve_for_import_packet",
        "return_for_revision",
        "reject_candidate",
    ]
    assert columns["approved_by_actor_id"]["source"] == "authenticated PM actor"
    assert columns["approved_at_utc"]["source"] == "server timestamp"
    assert columns["validation_result"]["type"] == "jsonb"

    constraints = {constraint["constraint_id"]: constraint for constraint in plan["recommended_constraints"]}
    assert "approval-record-primary-key" in constraints
    assert "candidate-identity-required" in constraints
    assert "insert-only-record" in constraints
    assert "no-go-overrides-json-array" in constraints


def test_project_import_approval_storage_plan_route_returns_read_only_plan(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()

    response = client.get("/api/v1/reads/project-import-approval-storage-plan", headers=_make_token())

    assert response.status_code == 200
    plan = response.json()
    assert plan["candidate_id"] == "pm-import-candidate-miner-temp-power"
    assert plan["mutation_authority"] == "not_admitted"
    assert plan["persistence_authority"] == "storage_decision_only_not_admitted"
    assert plan["recommended_table"] == "seam.pm_import_candidate_approvals"
    assert plan["contract_dependency"]["candidate_identity"]["idempotency_key"].startswith("pm-import:")
    assert "write_supabase" in plan["not_allowed_now"]
