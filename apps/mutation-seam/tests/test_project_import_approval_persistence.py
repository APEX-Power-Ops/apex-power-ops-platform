import base64
import json
from copy import deepcopy
from pathlib import Path

from openpyxl import Workbook

from app.db.memory_store import store
from app.project_import_admission_plan import build_project_import_admission_plan
from app.project_import_approval_contract import build_project_import_approval_contract
from app.project_import_approval_persistence import (
    build_project_import_approval_record_id,
    classify_project_import_approval_record,
    load_project_import_approval_status,
)
from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


MIGRATION_PATH = Path(__file__).resolve().parents[1] / "migrations" / "003_pm_import_candidate_approvals.sql"


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
        "client_timestamp": "2026-05-16T20:00:00Z",
    }
    request.update(overrides)
    return request


def _approval_contract(tmp_path, monkeypatch):
    workbook_path = tmp_path / "estimator.xlsm"
    _write_candidate_estimator(workbook_path)
    monkeypatch.setenv("APEX_PROJECT_ESTIMATOR_WORKBOOK", str(workbook_path))
    monkeypatch.setenv("APEX_PROJECT_SLD_PDF", str(tmp_path / "missing.pdf"))
    _clear_all_caches()
    candidate = load_project_import_candidate(str(workbook_path), str(tmp_path / "missing.pdf"))
    admission_plan = build_project_import_admission_plan(candidate)
    return build_project_import_approval_contract(admission_plan)


def _domain_counts() -> dict[str, int]:
    return {
        "projects": len(store.projects),
        "workpackages": len(store.workpackages),
        "tasks": len(store.tasks),
        "apparatus": len(store.apparatus),
        "assignments": len(store.assignments),
        "snapshots": len(store.snapshots),
    }


def test_project_import_approval_route_persists_insert_only_approval_record(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)
    before_counts = _domain_counts()

    response = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(payload),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_type"] == "pm_import_candidate_approval"
    assert data["action_type"] == "persist_import_approval"
    assert data["new_state"]["decision"] == "approve_for_import_packet"
    assert data["new_state"]["approved_by_actor_id"] == "pm-001"
    assert data["new_state"]["approved_at_utc"] != "1900-01-01T00:00:00Z"
    assert data["new_state"]["approval_payload"]["approved_by_actor_id"] == "pm-001"
    assert data["new_state"]["validation_result"]["valid"] is True
    assert data["new_state"]["import_authority"] == "not_admitted"
    assert data["new_state"]["mutation_id"] == data["mutation_id"]
    assert data["new_state"]["audit_event_id"] == data["audit_event_id"]
    assert data["entity_id"] in store.pm_import_candidate_approvals
    stored_record = store.pm_import_candidate_approvals[data["entity_id"]]
    assert stored_record["mutation_id"] == data["mutation_id"]
    assert stored_record["audit_event_id"] == data["audit_event_id"]
    assert _domain_counts() == before_counts
    assert len(store.audit_log) == 1
    assert store.audit_log[0]["action_type"] == "persist_import_approval"
    assert store.audit_log[0]["entity_type"] == "pm_import_candidate_approval"
    assert store.audit_log[0]["id"] == data["audit_event_id"]


def test_project_import_approval_route_replays_identical_payload_without_second_insert(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)
    request = _approval_request(payload)

    first = client.post("/api/v1/mutations/project-import-approvals", json=request, headers=_token())
    second = client.post("/api/v1/mutations/project-import-approvals", json=request, headers=_token())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.json()["status"] == "idempotent_hit"
    assert second.json()["entity_id"] == first.json()["entity_id"]
    assert second.json()["mutation_id"] == first.json()["mutation_id"]
    assert second.json()["audit_event_id"] == first.json()["audit_event_id"]
    assert len(store.pm_import_candidate_approvals) == 1
    assert len(store.audit_log) == 1


def test_project_import_approval_readback_classifies_current_and_stale_records(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)
    request = _approval_request(payload)

    missing = load_project_import_approval_status()
    assert missing["classification"] == "no_approval_record"
    assert missing["approval_storage_available"] is True
    assert missing["route"] == "/api/v1/reads/project-import-approval-status"
    assert missing["audit_log_used_for_current_status"] is False

    missing_route = client.get("/api/v1/reads/project-import-approval-status", headers=_token())
    assert missing_route.status_code == 200
    assert missing_route.json()["classification"] == "no_approval_record"

    response = client.post("/api/v1/mutations/project-import-approvals", json=request, headers=_token())
    accepted = response.json()

    current = load_project_import_approval_status()
    assert current["classification"] == "approved_for_import_packet"
    assert current["approval_record_id"] == accepted["entity_id"]
    assert current["mutation_id"] == accepted["mutation_id"]
    assert current["audit_event_id"] == accepted["audit_event_id"]
    assert current["approval_storage_available"] is True
    assert current["route"] == "/api/v1/reads/project-import-approval-status"
    assert current["audit_log_used_for_current_status"] is False
    assert current["import_authority"] == "not_admitted"

    current_route = client.get("/api/v1/reads/project-import-approval-status", headers=_token())
    assert current_route.status_code == 200
    assert current_route.json()["classification"] == "approved_for_import_packet"
    assert current_route.json()["approval_record_id"] == accepted["entity_id"]

    stored_record = store.pm_import_candidate_approvals[accepted["entity_id"]]
    stale_record = dict(stored_record)
    stale_record["source_stat_fingerprint"] = "stale-source-stat"
    stale = classify_project_import_approval_record(stale_record, contract)
    assert stale["classification"] == "stale_approval_record"
    assert stale["current_candidate_match"] is False
    assert stale["stale_fields"] == ["source_stat_fingerprint"]
    assert stale["audit_log_used_for_current_status"] is False


def test_project_import_approval_readback_classifies_returned_and_rejected_without_audit_dependency(monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    base = _approval_payload_from_contract(contract)
    returned = {
        **base,
        "approval_record_id": "approval-returned",
        "decision": "return_for_revision",
        "mutation_id": "mut-returned",
        "audit_event_id": "audit-returned",
        "import_authority": "not_admitted",
    }
    rejected = {
        **base,
        "approval_record_id": "approval-rejected",
        "decision": "reject_candidate",
        "mutation_id": "mut-rejected",
        "audit_event_id": "audit-rejected",
        "import_authority": "not_admitted",
    }

    returned_status = classify_project_import_approval_record(returned, contract)
    rejected_status = classify_project_import_approval_record(rejected, contract)

    assert returned_status["classification"] == "returned_for_revision"
    assert rejected_status["classification"] == "rejected_candidate"
    assert returned_status["audit_log_used_for_current_status"] is False
    assert rejected_status["audit_log_used_for_current_status"] is False


def test_project_import_approval_status_read_classifies_storage_unavailable(monkeypatch, tmp_path):
    _approval_contract(tmp_path, monkeypatch)

    class BrokenApprovalStore:
        def values(self):
            raise RuntimeError("approval table missing")

    monkeypatch.setattr(store, "pm_import_candidate_approvals", BrokenApprovalStore())

    status = load_project_import_approval_status()

    assert status["classification"] == "approval_storage_unavailable"
    assert status["approval_storage_available"] is False
    assert status["approval_record_count_for_candidate"] == 0
    assert status["audit_log_used_for_current_status"] is False
    assert status["import_authority"] == "not_admitted"
    assert status["error_type"] == "RuntimeError"


def test_project_import_approval_route_rejects_replay_mismatch(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)
    request = _approval_request(payload)

    first = client.post("/api/v1/mutations/project-import-approvals", json=request, headers=_token())
    changed_payload = deepcopy(payload)
    changed_payload["review_notes"] = "Changed notes with the same candidate/idempotency identity."
    second = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(changed_payload),
        headers=_token(),
    )

    assert first.json()["status"] == "accepted"
    assert second.status_code == 200
    assert second.json()["status"] == "rejected"
    assert second.json()["error"]["code"] == "IDEMPOTENCY_DUPLICATE"
    assert len(store.pm_import_candidate_approvals) == 1
    assert len(store.audit_log) == 1


def test_project_import_approval_route_rejects_invalid_payload_without_writes(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)
    payload["decision"] = "force_import"
    payload["accepted_warning_codes"] = []
    payload["review_notes"] = ""
    before_counts = _domain_counts()

    response = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(payload),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"
    validation_errors = {error["code"] for error in data["error"]["detail"]["validation_result"]["errors"]}
    assert "unsupported_decision" in validation_errors
    assert "warning_code_set_mismatch" in validation_errors
    assert "review_notes_required" in validation_errors
    assert len(store.pm_import_candidate_approvals) == 0
    assert len(store.audit_log) == 0
    assert _domain_counts() == before_counts


def test_project_import_approval_route_requires_pm_online_class_c(client, monkeypatch, tmp_path):
    contract = _approval_contract(tmp_path, monkeypatch)
    payload = _approval_payload_from_contract(contract)

    non_pm = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(payload),
        headers=_token("field_tech"),
    )
    offline = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(payload, source="offline_queue"),
        headers=_token(),
    )
    wrong_class = client.post(
        "/api/v1/mutations/project-import-approvals",
        json=_approval_request(payload, mutation_class="B"),
        headers=_token(),
    )

    assert non_pm.json()["status"] == "rejected"
    assert non_pm.json()["error"]["code"] == "UNAUTHORIZED_ROLE"
    assert offline.json()["status"] == "rejected"
    assert offline.json()["error"]["code"] == "OFFLINE_CLASS_C_REJECTED"
    assert wrong_class.json()["status"] == "rejected"
    assert wrong_class.json()["error"]["code"] == "INVALID_MUTATION_CLASS"
    assert len(store.pm_import_candidate_approvals) == 0
    assert len(store.audit_log) == 0


def test_pm_import_candidate_approval_migration_preserves_insert_only_boundary():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS seam.pm_import_candidate_approvals" in sql
    assert "approval_record_id           TEXT PRIMARY KEY" in sql
    assert "mutation_id                  TEXT NOT NULL" in sql
    assert "audit_event_id               TEXT NOT NULL" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_mutation_id" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS idx_pm_import_candidate_approvals_audit_event_id" in sql
    assert "FUNCTION seam.reject_pm_import_candidate_approval_mutation()" in sql
    assert "BEFORE UPDATE ON seam.pm_import_candidate_approvals" in sql
    assert "BEFORE DELETE ON seam.pm_import_candidate_approvals" in sql
    assert "decision IN ('approve_for_import_packet', 'return_for_revision', 'reject_candidate')" in sql
    assert "ALTER TABLE seam.pm_import_candidate_approvals ENABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE ALL ON TABLE seam.pm_import_candidate_approvals FROM anon" in sql
    assert "REVOKE ALL ON TABLE seam.pm_import_candidate_approvals FROM authenticated" in sql
    assert "CREATE TABLE IF NOT EXISTS seam.projects" not in sql
    assert "CREATE TABLE IF NOT EXISTS seam.workpackages" not in sql
    assert "CREATE TABLE IF NOT EXISTS seam.tasks" not in sql
    assert "CREATE TABLE IF NOT EXISTS seam.apparatus" not in sql
