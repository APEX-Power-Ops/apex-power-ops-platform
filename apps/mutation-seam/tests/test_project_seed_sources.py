import base64
import json

from openpyxl import Workbook

from app.project_seed_sources import clear_project_seed_cache, extract_topology_labels_from_text, load_project_seed_sources


def _make_token() -> dict[str, str]:
    payload = {
        "actor_id": "tech-001",
        "actor_role": "field_tech",
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


def test_extract_topology_labels_from_text_finds_equipment_labels():
    text = "MVTX -A SWBD -C PWR SKID -25 LVPP -2 MVS -4"

    labels = extract_topology_labels_from_text(text)

    assert labels == ["PWR SKID -25", "MVTX -A", "SWBD -C", "MVS -4", "LVPP -2"]


def test_load_project_seed_sources_reads_workbook_line_items(tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_estimator_workbook(workbook_path)

    data = load_project_seed_sources(str(workbook_path), str(tmp_path / "missing.pdf"))

    assert data["project_name"] == "Miner Temp Power"
    assert data["location"] == "Santa Teresa, NM"
    assert data["source_sheet"] == "Updated"
    assert len(data["line_items"]) == 2
    assert len(data["expanded_apparatus_candidates"]) == 5
    assert data["expanded_apparatus_candidates"][0]["display_name"] == "Pole Disconnect 01"
    assert data["expanded_apparatus_candidates"][3]["display_name"] == "SWBD 01"


def test_project_apparatus_plan_route_returns_workbook_backed_rows(client, monkeypatch, tmp_path):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_estimator_workbook(workbook_path)

    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    clear_project_seed_cache()

    response = client.get("/api/v1/reads/project-apparatus-plan", headers=_make_token())

    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "Miner Temp Power"
    assert data["metadata"]["estimator_workbook_found"] is True
    assert data["metadata"]["sld_pdf_found"] is False
    assert len(data["line_items"]) == 2
    assert len(data["expanded_apparatus_candidates"]) == 5
