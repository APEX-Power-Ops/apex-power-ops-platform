import base64
import json
from uuid import uuid4

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
    assert blocked["ai_advisory"]["mode"] == "draft_only"
    assert blocked["ai_advisory"]["mutation_authority"] == "not_admitted"
    assert blocked["ai_advisory"]["target_audience"] == "lead"
    assert blocked["apparatus_name"] in blocked["ai_advisory"]["brief"]
    assert blocked["primary_blocking_issue_id"] in {"issue-002", "issue-003"}
    assert blocked["blocking_issues"][0]["id"] == blocked["primary_blocking_issue_id"]
    assert blocked["returnable_issue_id"] in {None, "issue-003"}
    assert "blocked" in blocked["lens_tags"]
    assert "stale_blocker" in blocked["lens_tags"]
    assert workfront["lenses"]["blocked_count"] >= 1
    assert workfront["lenses"]["stale_blocker_count"] >= 1

    assigned = next(row for row in workfront["rows"] if row["apparatus_id"] == "app-002")
    assert assigned["designation"] == "Pole Disconnect"
    assert assigned["owner_name"] == "Alex Rivera"
    assert assigned["next_action"] == "Start field work"


def test_pm_workfront_surfaces_returned_followup_evidence(client):
    issue = store.issues["issue-002"].copy()
    issue["status"] = "escalated"
    store.issues["issue-002"] = issue

    before = client.get("/api/v1/reads/pm-workfront", headers=_make_token()).json()
    blocked = next(row for row in before["rows"] if row["returnable_issue_id"] == "issue-002")
    note = blocked["ai_advisory"]["brief"]

    response = client.post(
        "/api/v1/mutations/issues",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "C",
            "action_type": "return_to_lead",
            "entity_id": "issue-002",
            "payload": {
                "status": "in_review",
                "pm_followup_note": note,
                "pm_followup_sent_at": "2026-05-15T15:30:00Z",
                "pm_followup_workfront_row_id": blocked["id"],
            },
            "reason": "PM workfront lead follow-up",
            "source": "online",
            "client_timestamp": "2026-05-15T15:30:00Z",
        },
        headers=_make_token(),
    )

    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "accepted"
    assert result["new_state"]["status"] == "in_review"
    assert result["new_state"]["pm_followup_note"] == note

    after = client.get("/api/v1/reads/pm-workfront", headers=_make_token()).json()
    returned = next(row for row in after["rows"] if row["primary_blocking_issue_id"] == "issue-002")
    assert returned["returnable_issue_id"] is None
    assert returned["latest_pm_followup_note"] == note
    assert returned["latest_pm_followup_sent_at"] == "2026-05-15T15:30:00Z"
    assert returned["blocking_issues"][0]["pm_followup_note"] == note
    assert "returned_to_lead" in returned["lens_tags"]
    assert "stale_blocker" not in returned["lens_tags"]
    assert returned["last_pm_decision"]["action_type"] == "return_to_lead"
    assert returned["last_pm_decision"]["to_status"] == "in_review"
    assert after["lenses"]["returned_to_lead_count"] >= 1
