import base64
import json

from openpyxl import Workbook

from app.db.memory_store import store


def _make_token(actor_id: str = "tech-001", actor_role: str = "field_tech") -> dict[str, str]:
    payload = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _write_estimator_workbook(path):
    workbook = Workbook()
    try:
        sheet = workbook.active
        sheet.title = "Updated"
        sheet.append([])
        sheet.append([None, "Updated"])
        sheet.append([None, None, "NETA", None, "Miner Temp Power", "SLD: E01-00, E01-01, E01-02"])
        sheet.append([None, None, "ATS", None, "Santa Teresa, NM", "Dated: 03/05/2026"])
        sheet.append([None, None, "QTY", "Section", "Apparatus Type", "Designation", "Notes", None, "Hrs/Unit", "Hrs/Line"])
        sheet.append([None, None, 3, 7.5, "Switch MV - Fused Disconnect", "Pole Disconnect", "E01-00", None, 2.5, 7.5])
        sheet.append([None, None, 2, 7.1, "Switchboard - Distribution LV", "SWBD", "E01-01", None, 3, 6])
        workbook.save(path)
    finally:
        workbook.close()


def test_store_reset_uses_project_apparatus_seed(monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_estimator_workbook(workbook_path)

    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    monkeypatch.setenv("APEX_FIELD_SEED_EQUIPMENT_WORKBOOK", str(tmp_path / "missing-equipment.xlsx"))
    monkeypatch.setenv("APEX_FIELD_SEED_CAPABILITY_WORKBOOK", str(tmp_path / "missing-capability.xlsx"))

    store.reset()

    assert store.projects["proj-001"]["name"] == "Miner Temp Power"
    assert len(store.apparatus) == 5
    assert store.apparatus["app-001"]["name"] == "Pole Disconnect 01"
    assert store.apparatus["app-001"]["status"] == "not_started"
    assert store.apparatus["app-002"]["assigned_to"] == "tech-001"
    assert len(store.assignments) == 2
    assert "item-001" in store.checklist_items
    assert "issue-001" in store.issues


def test_reads_apparatus_and_approval_queue_use_project_seed(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_estimator_workbook(workbook_path)

    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    monkeypatch.setenv("APEX_FIELD_SEED_EQUIPMENT_WORKBOOK", str(tmp_path / "missing-equipment.xlsx"))
    monkeypatch.setenv("APEX_FIELD_SEED_CAPABILITY_WORKBOOK", str(tmp_path / "missing-capability.xlsx"))

    store.reset()

    apparatus_response = client.get("/api/v1/reads/apparatus", headers=_make_token())
    approval_response = client.get("/api/v1/reads/approval-queue", headers=_make_token("pm-001", "pm"))

    assert apparatus_response.status_code == 200
    apparatus = apparatus_response.json()
    assert len(apparatus) == 5
    assert apparatus[0]["name"] == "Pole Disconnect 01"

    assert approval_response.status_code == 200
    approval_queue = approval_response.json()
    assert approval_queue["total_count"] >= 2
    assert len(approval_queue["tasks"]) == 1
    assert len(approval_queue["escalated_issues"]) == 1
