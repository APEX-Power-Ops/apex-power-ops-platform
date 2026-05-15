import base64
import json

from openpyxl import Workbook

from app.db.memory_store import store


def _make_token(actor_id: str = "pm-001", actor_role: str = "pm") -> dict[str, str]:
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


def test_pm_workfront_read_model_surfaces_blocked_unassigned_owner_and_next_action(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_estimator_workbook(workbook_path)

    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    monkeypatch.setenv("APEX_FIELD_SEED_EQUIPMENT_WORKBOOK", str(tmp_path / "missing-equipment.xlsx"))
    monkeypatch.setenv("APEX_FIELD_SEED_CAPABILITY_WORKBOOK", str(tmp_path / "missing-capability.xlsx"))

    store.reset()

    response = client.get("/api/v1/reads/pm-workfront", headers=_make_token())

    assert response.status_code == 200
    workfront = response.json()
    assert workfront["advisory"]["mode"] == "read_only"
    assert workfront["advisory"]["ai_mutation_authority"] == "not_admitted"
    assert workfront["summary"]["total_count"] == 5
    assert workfront["summary"]["blocked_count"] >= 1
    assert workfront["summary"]["unassigned_count"] >= 1

    blocked = workfront["rows"][0]
    assert blocked["readiness"] == "blocked"
    assert blocked["drawing_ref"] in {"E01-00", "E01-01"}
    assert blocked["next_action"].startswith("Resolve blocker:")

    assigned = next(row for row in workfront["rows"] if row["apparatus_id"] == "app-002")
    assert assigned["designation"] == "Pole Disconnect"
    assert assigned["owner_name"] == "Alex Rivera"
    assert assigned["next_action"] == "Start field work"
