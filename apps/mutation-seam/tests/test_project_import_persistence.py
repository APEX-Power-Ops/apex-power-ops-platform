import base64
import json

from openpyxl import Workbook

from app.db.memory_store import store
from app.project_import_admission_plan import build_project_import_admission_plan
from app.project_import_approval_contract import build_project_import_approval_contract
from app.project_import_approval_persistence import build_project_import_approval_record_id
from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_import_persistence import build_project_import_id, load_project_import_status
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


def _token(actor_role: str = "pm") -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
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
        "approved_by_actor_id": "spoofed-browser-value",
        "approved_at_utc": "1900-01-01T00:00:00Z",
        "accepted_warning_codes": list(expected["accepted_warning_codes"]),
        "accepted_no_go_overrides": list(expected["accepted_no_go_overrides"]),
        "review_notes": "PM accepted candidate warnings for future import packet authoring only.",
    }


def _approval_request(payload: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": "persist_import_approval",
        "entity_id": build_project_import_approval_record_id(payload),
        "payload": payload,
        "reason": "Persist PM import-candidate approval record only; do not import rows.",
        "source": "online",
        "client_timestamp": "2026-05-18T20:00:00Z",
    }
    request.update(overrides)
    return request


def _candidate_contract(tmp_path, monkeypatch):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()
    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    admission_plan = build_project_import_admission_plan(candidate)
    return candidate, build_project_import_approval_contract(admission_plan)


def _import_payload_from_contract(contract: dict, approval_record_id: str) -> dict:
    expected = contract["minimum_expected_values"]
    return {
        "candidate_id": expected["candidate_id"],
        "candidate_version": expected["candidate_version"],
        "source_stat_fingerprint": expected["source_stat_fingerprint"],
        "candidate_shape_fingerprint": expected["candidate_shape_fingerprint"],
        "idempotency_key": expected["idempotency_key"],
        "approval_record_id": approval_record_id,
        "accepted_warning_codes": list(expected["accepted_warning_codes"]),
        "accepted_no_go_overrides": list(expected["accepted_no_go_overrides"]),
        "import_notes": "PM Lane 278 imports only project, workpackage, task, and apparatus rows.",
    }


def _import_request(payload: dict, candidate: dict, **overrides) -> dict:
    request = {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": "persist_project_import",
        "entity_id": build_project_import_id(candidate),
        "payload": payload,
        "reason": "Persist approved Project Miner import rows only; keep downstream workflow blocked.",
        "source": "online",
        "client_timestamp": "2026-05-18T21:00:00Z",
    }
    request.update(overrides)
    return request


def _domain_counts() -> dict[str, int]:
    return {
        "projects": len(store.projects),
        "workpackages": len(store.workpackages),
        "tasks": len(store.tasks),
        "apparatus": len(store.apparatus),
        "assignments": len(store.assignments),
        "snapshots": len(store.snapshots),
        "issues": len(store.issues),
        "hours": len(store.hours),
    }


def test_project_import_route_rejects_without_current_approval_record(client, monkeypatch, tmp_path):
    candidate, contract = _candidate_contract(tmp_path, monkeypatch)
    payload = _import_payload_from_contract(contract, "missing-approval")
    before_counts = _domain_counts()

    response = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(payload, candidate),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"
    assert _domain_counts() == before_counts


def test_project_import_route_persists_approved_candidate_rows_and_replays(client, monkeypatch, tmp_path):
    candidate, contract = _candidate_contract(tmp_path, monkeypatch)
    approval_payload = _approval_payload_from_contract(contract)
    approval = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(approval_payload),
        headers=_token(),
    ).json()
    import_payload = _import_payload_from_contract(contract, approval["entity_id"])
    before_counts = _domain_counts()

    first = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate),
        headers=_token(),
    )
    second = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate),
        headers=_token(),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()
    second_data = second.json()
    assert first_data["status"] == "accepted"
    assert second_data["status"] == "idempotent_hit"
    assert second_data["entity_id"] == first_data["entity_id"]
    assert second_data["mutation_id"] == first_data["mutation_id"]
    assert second_data["audit_event_id"] == first_data["audit_event_id"]
    assert first_data["entity_type"] == "pm_import"
    assert first_data["action_type"] == "persist_project_import"
    assert first_data["new_state"]["import_authority"] == "admitted_by_pm_lane_278"
    assert first_data["new_state"]["row_counts"]["projects"] == 1
    assert first_data["new_state"]["row_counts"]["workpackages"] == candidate["summary"]["workpackage_count"]
    assert first_data["new_state"]["row_counts"]["tasks"] == candidate["summary"]["task_count"]
    assert first_data["new_state"]["row_counts"]["apparatus"] == candidate["summary"]["apparatus_candidate_count"]
    assert first_data["new_state"]["row_counts"]["source_trace_rows"] == (
        candidate["summary"]["task_count"] + candidate["summary"]["apparatus_candidate_count"]
    )
    assert first_data["new_state"]["row_counts"]["warning_review_rows"] == candidate["summary"]["warning_count"]

    after_counts = _domain_counts()
    assert after_counts["projects"] == before_counts["projects"] + 1
    assert after_counts["workpackages"] == before_counts["workpackages"] + candidate["summary"]["workpackage_count"]
    assert after_counts["tasks"] == before_counts["tasks"] + candidate["summary"]["task_count"]
    assert after_counts["apparatus"] == before_counts["apparatus"] + candidate["summary"]["apparatus_candidate_count"]
    assert after_counts["assignments"] == before_counts["assignments"]
    assert after_counts["snapshots"] == before_counts["snapshots"]
    assert after_counts["issues"] == before_counts["issues"]
    assert after_counts["hours"] == before_counts["hours"]

    status = load_project_import_status()
    assert status["classification"] == "imported"
    assert status["counts_match"] is True
    assert status["current_candidate_match"] is True
    assert status["imported_row_counts"] == status["expected_row_counts"]

    status_route = client.get("/api/v1/reads/project-import-status", headers=_token())
    assert status_route.status_code == 200
    assert status_route.json()["classification"] == "imported"


def test_project_import_route_rejects_replay_mismatch(client, monkeypatch, tmp_path):
    candidate, contract = _candidate_contract(tmp_path, monkeypatch)
    approval_payload = _approval_payload_from_contract(contract)
    approval = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(approval_payload),
        headers=_token(),
    ).json()
    import_payload = _import_payload_from_contract(contract, approval["entity_id"])

    first = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate),
        headers=_token(),
    )
    changed_payload = dict(import_payload)
    changed_payload["import_notes"] = "Changed import notes with the same candidate identity."
    second = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(changed_payload, candidate),
        headers=_token(),
    )

    assert first.json()["status"] == "accepted"
    assert second.status_code == 200
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"


def test_project_import_route_requires_pm_online_class_c(client, monkeypatch, tmp_path):
    candidate, contract = _candidate_contract(tmp_path, monkeypatch)
    approval_payload = _approval_payload_from_contract(contract)
    approval = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(approval_payload),
        headers=_token(),
    ).json()
    import_payload = _import_payload_from_contract(contract, approval["entity_id"])

    non_pm = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate),
        headers=_token("field_tech"),
    )
    offline = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate, source="offline_queue"),
        headers=_token(),
    )
    wrong_class = client.post(
        "/api/v1/mutations/project-imports",
        json=_import_request(import_payload, candidate, mutation_class="B"),
        headers=_token(),
    )

    assert non_pm.json()["status"] == "rejected"
    assert non_pm.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert offline.json()["status"] == "rejected"
    assert offline.json()["error"]["code"] == "OFFLINE_CLASS_C_REJECTED"
    assert wrong_class.json()["status"] == "rejected"
    assert wrong_class.json()["error"]["code"] == "INVALID_MUTATION_CLASS"
