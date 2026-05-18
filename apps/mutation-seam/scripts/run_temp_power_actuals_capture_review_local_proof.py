from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SEAM_STORE_BACKEND", "memory")

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from fastapi.testclient import TestClient

from app.db.memory_store import store
from app.main import app
from app.temp_power_actuals_capture_review_persistence import (
    TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE,
    TEMP_POWER_CANDIDATE_ID,
    TEMP_POWER_PROJECT_ID,
    TEMP_POWER_SOURCE_FINGERPRINT,
    build_temp_power_actuals_capture_review_id,
)


def _token(actor_role: str = "pm", project_scope: list[str] | None = None) -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": project_scope or [TEMP_POWER_PROJECT_ID],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _seed_temp_power_scope() -> None:
    store.projects[TEMP_POWER_PROJECT_ID] = {
        "id": TEMP_POWER_PROJECT_ID,
        "name": "Project Miner Temp Power",
    }
    store.workpackages["pm-import-project-miner-temp-power-wp-001"] = {
        "id": "pm-import-project-miner-temp-power-wp-001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "status": "not_started",
    }
    store.tasks["pm-import-project-miner-temp-power-task-0001"] = {
        "id": "pm-import-project-miner-temp-power-task-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "workpackage_id": "pm-import-project-miner-temp-power-wp-001",
        "status": "ready",
    }
    store.apparatus["pm-import-project-miner-temp-power-app-0001"] = {
        "id": "pm-import-project-miner-temp-power-app-0001",
        "project_id": TEMP_POWER_PROJECT_ID,
        "task_id": "pm-import-project-miner-temp-power-task-0001",
        "status": "ready",
    }


def _payload() -> dict:
    return {
        "idempotency_key": "pm-lane-305-actuals-review-local-proof:pm-import-project-miner-temp-power:task-0001:app-0001:2026-05-18",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "task_id": "pm-import-project-miner-temp-power-task-0001",
        "apparatus_id": "pm-import-project-miner-temp-power-app-0001",
        "task_day_fallback_reason": None,
        "work_date": "2026-05-18",
        "recorder_role": "field_tech",
        "actual_labor_hours_preview": 6.5,
        "work_summary_note": "Local first-write proof for one Temp Power apparatus only; customer delivery and finance remain blocked.",
        "primary_evidence_type": "field_ticket",
        "primary_evidence_ref": "ticket://temp-power/2026-05-18/app-0001/local-proof",
        "supporting_evidence_refs": ["photo://temp-power/app-0001/2026-05-18/local-proof"],
        "correction_mode": "ORIGINAL_REVIEW",
        "supersedes_review_id": None,
        "replacement_reason": None,
        "pm_review_status": "REVIEW_ONLY_READY_FOR_PM_REVIEW",
        "pm_review_note": "Local first-write proof only; customer preview, customer delivery, finance, and source writeback remain blocked.",
    }


def _request(payload: dict) -> dict:
    return {
        "idempotency_key": payload["idempotency_key"],
        "mutation_class": "C",
        "action_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE,
        "entity_id": build_temp_power_actuals_capture_review_id(payload),
        "payload": payload,
        "reason": "Local first-write proof for admitted Temp Power actuals-capture review only.",
        "source": "online",
        "client_timestamp": "2026-05-18T23:10:00Z",
    }


def _domain_counts() -> dict[str, int]:
    return {
        "projects": len(store.projects),
        "workpackages": len(store.workpackages),
        "tasks": len(store.tasks),
        "apparatus": len(store.apparatus),
        "assignments": len(store.assignments),
        "hours": len(store.hours),
        "issues": len(store.issues),
    }


def _result_or_fail(label: str, response_data: dict, expected_status: str) -> None:
    actual_status = response_data.get("status")
    if actual_status != expected_status:
        raise RuntimeError(f"{label} expected status {expected_status!r}, got {actual_status!r}: {response_data}")


def main() -> int:
    store.reset()
    _seed_temp_power_scope()
    payload = _payload()
    request = _request(payload)
    counts_before = _domain_counts()

    client = TestClient(app)
    first_response = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=request,
        headers=_token(),
    )
    replay_response = client.post(
        "/api/v1/mutations/temp-power-actuals-capture-reviews",
        json=request,
        headers=_token(),
    )
    readback_response = client.get(
        "/api/v1/reads/temp-power-actuals-capture-review-status",
        headers=_token(),
    )
    counts_after = _domain_counts()

    if first_response.status_code != 200:
        raise RuntimeError(f"first write returned HTTP {first_response.status_code}: {first_response.text}")
    if replay_response.status_code != 200:
        raise RuntimeError(f"replay returned HTTP {replay_response.status_code}: {replay_response.text}")
    if readback_response.status_code != 200:
        raise RuntimeError(f"readback returned HTTP {readback_response.status_code}: {readback_response.text}")

    first_data = first_response.json()
    replay_data = replay_response.json()
    readback_data = readback_response.json()

    _result_or_fail("first write", first_data, "accepted")
    _result_or_fail("replay", replay_data, "idempotent_hit")
    if readback_data.get("status") != "actuals_capture_review_recorded_current_match":
        raise RuntimeError(f"readback expected current-match classification, got {readback_data}")
    if counts_before != counts_after:
        raise RuntimeError(f"downstream counts changed: before={counts_before} after={counts_after}")

    proof = {
        "proof_type": "temp_power_actuals_capture_review_local_first_write_proof",
        "project_id": TEMP_POWER_PROJECT_ID,
        "candidate_id": TEMP_POWER_CANDIDATE_ID,
        "source_fingerprint": TEMP_POWER_SOURCE_FINGERPRINT,
        "request": {
            "route": "/api/v1/mutations/temp-power-actuals-capture-reviews",
            "action_type": TEMP_POWER_ACTUALS_CAPTURE_REVIEW_ACTION_TYPE,
            "entity_id": request["entity_id"],
            "idempotency_key": request["idempotency_key"],
            "task_id": payload["task_id"],
            "apparatus_id": payload["apparatus_id"],
            "work_date": payload["work_date"],
        },
        "accepted_write": {
            "status": first_data["status"],
            "mutation_id": first_data["mutation_id"],
            "audit_event_id": first_data["audit_event_id"],
            "entity_id": first_data["entity_id"],
        },
        "replay": {
            "status": replay_data["status"],
            "mutation_id": replay_data["mutation_id"],
            "audit_event_id": replay_data["audit_event_id"],
            "same_mutation_id_as_first": replay_data["mutation_id"] == first_data["mutation_id"],
            "same_audit_event_id_as_first": replay_data["audit_event_id"] == first_data["audit_event_id"],
        },
        "readback": {
            "route": "/api/v1/reads/temp-power-actuals-capture-review-status",
            "status": readback_data["status"],
            "current_candidate_match": readback_data.get("current_candidate_match"),
            "current_source_fingerprint_match": readback_data.get("current_source_fingerprint_match"),
            "record_count": readback_data.get("record_count"),
            "latest_review_id": readback_data.get("latest_review_id"),
        },
        "downstream_counts": {
            "before": counts_before,
            "after": counts_after,
            "unchanged": counts_before == counts_after,
        },
        "blocked_boundaries": {
            "customer_delivery_authority": first_data["new_state"].get("customer_delivery_authority"),
            "finance_authority": first_data["new_state"].get("finance_authority"),
            "source_writeback_authority": first_data["new_state"].get("source_writeback_authority"),
            "durable_delivery_event": first_data["new_state"].get("durable_delivery_event"),
        },
        "audit_log_count": len(store.audit_log),
        "canonical_record_count": len(getattr(store, "temp_power_actuals_capture_reviews", {})),
    }
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())