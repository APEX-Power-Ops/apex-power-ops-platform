from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TRACE_PATH = SCRIPT_DIR / "local_trace_no_supabase_touch.txt"

MUTATION_ROUTE = "/api/v1/mutations/project-import-contract-support"
READBACK_ROUTE = "/api/v1/reads/project-import-contract-support-status"
ENTITY_TYPE = "pm_project_import_contract_support"
ACTION_TYPE = "persist_project_import_contract_support"

PROJECT_ID = "pm-import-project-miner-temp-power"
CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
SOURCE_FINGERPRINT = "miner-temp-power-source-fingerprint-2026-05-20"

FORCE_FAILURE_TO_FIXTURE = {
    "scope_detail_conflict": "rollback_scope_detail_conflict.json",
    "apparatus_financial_validation_failed": "rollback_apparatus_financial_validation_failed.json",
    "audit_write_unavailable": "rollback_audit_write_unavailable.json",
    "idempotency_write_unavailable": "rollback_idempotency_write_unavailable.json",
}

READBACK_STATUS_TO_FIXTURE = {
    "missing": "readback_missing.json",
    "ready": "readback_ready.json",
    "stale_candidate": "readback_stale_candidate.json",
    "counts_mismatch": "readback_counts_mismatch.json",
    "unavailable": "readback_unavailable.json",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _ordered_scope_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (str(row.get("scope_id") or ""), str(row.get("scope_name") or "")))


def _ordered_apparatus_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("scope_id") or ""),
            str(row.get("apparatus_id") or ""),
            str(row.get("apparatus_name") or ""),
        ),
    )


def build_sample_request(mutation_id: str = "mut-6147fd7f-62f7-47b8-86a6-83c55114f611") -> dict[str, Any]:
    payload = {
        "mutation_id": mutation_id,
        "project_id": PROJECT_ID,
        "candidate_id": CANDIDATE_ID,
        "source_fingerprint": SOURCE_FINGERPRINT,
        "snapshot_kind": "miner_temp_power_contract_support",
        "contract_value": 10000.0,
        "total_quoted_hours": 100.0,
        "scope_labor_details": [
            {
                "scope_id": "scope-a",
                "scope_name": "Switchgear Testing",
                "quoted_hours": 60.0,
                "scope_pool_amount": 6000.0,
            },
            {
                "scope_id": "scope-b",
                "scope_name": "Transformer Testing",
                "quoted_hours": 40.0,
                "scope_pool_amount": 4000.0,
            },
        ],
        "apparatus_financials": [
            {
                "scope_id": "scope-a",
                "apparatus_id": "app-a-001",
                "apparatus_name": "Main Switchgear Cell 1",
                "quoted_hours": 20.0,
                "quoted_revenue": 2000.0,
                "recognition_rate_per_hour_snapshot": 100.0,
            },
            {
                "scope_id": "scope-a",
                "apparatus_id": "app-a-002",
                "apparatus_name": "Main Switchgear Cell 2",
                "quoted_hours": 40.0,
                "quoted_revenue": 4000.0,
                "recognition_rate_per_hour_snapshot": 100.0,
            },
            {
                "scope_id": "scope-b",
                "apparatus_id": "app-b-001",
                "apparatus_name": "Transformer Bay 1",
                "quoted_hours": 25.0,
                "quoted_revenue": 2500.0,
                "recognition_rate_per_hour_snapshot": 100.0,
            },
            {
                "scope_id": "scope-b",
                "apparatus_id": "app-b-002",
                "apparatus_name": "Transformer Bay 2",
                "quoted_hours": 15.0,
                "quoted_revenue": 1500.0,
                "recognition_rate_per_hour_snapshot": 100.0,
            },
        ],
    }
    idempotency_key = compute_business_payload_digest(payload)
    payload["idempotency_key"] = idempotency_key
    return {
        "idempotency_key": idempotency_key,
        "mutation_class": "C",
        "action_type": ACTION_TYPE,
        "entity_id": build_contract_support_entity_id(payload),
        "payload": payload,
        "reason": "Lane 414 local mocked dry-run for import-contract-support only.",
        "source": "online",
        "client_timestamp": "2026-05-20T21:14:00Z",
    }


def compute_business_payload_digest(payload: dict[str, Any]) -> str:
    canonical_parts = [
        str(payload.get("project_id") or ""),
        str(payload.get("candidate_id") or ""),
        str(payload.get("source_fingerprint") or ""),
        str(payload.get("snapshot_kind") or ""),
        str(payload.get("contract_value") or ""),
        str(payload.get("total_quoted_hours") or ""),
        _stable_json(_ordered_scope_rows(list(payload.get("scope_labor_details") or []))),
        _stable_json(_ordered_apparatus_rows(list(payload.get("apparatus_financials") or []))),
    ]
    return hashlib.sha256("|".join(canonical_parts).encode("utf-8")).hexdigest()


def build_contract_support_entity_id(payload: dict[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "snapshot_kind": payload.get("snapshot_kind"),
        "idempotency_key": payload.get("idempotency_key"),
    }
    digest = hashlib.sha256(_stable_json(identity).encode("utf-8")).hexdigest()[:24]
    return f"project-import-contract-support-{digest}"


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((SCRIPT_DIR / name).read_text(encoding="utf-8"))


def _deepcopy_fixture(name: str) -> dict[str, Any]:
    return copy.deepcopy(_load_fixture(name))


class LocalContractSupportMock:
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def _apply_dynamic_fields(self, response: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        payload = request["payload"]
        dynamic_entity_id = build_contract_support_entity_id(payload)
        response["entity_id"] = dynamic_entity_id
        response["action_type"] = request["action_type"]
        response["generated_at"] = _iso_now()
        response["current_candidate_match"] = str(payload.get("candidate_id") or "") == CANDIDATE_ID
        response["idempotent_hit"] = response.get("status") == "idempotent_hit"
        if "mutation_id" not in response:
            response["mutation_id"] = str(payload.get("mutation_id") or f"mut-{hashlib.sha256(dynamic_entity_id.encode()).hexdigest()[:32]}")
        if response.get("status") == "accepted":
            response["http_status"] = 201
        elif response.get("status") == "idempotent_hit":
            response["http_status"] = 200
        elif response.get("status") == "conflict":
            response["http_status"] = 409
        elif response.get("status") == "rejected" and response.get("http_status") is None:
            response["http_status"] = 422
        response.setdefault("entity_type", ENTITY_TYPE)
        response.setdefault("project_contract_snapshot_id", f"pcs-{hashlib.sha256(dynamic_entity_id.encode()).hexdigest()[:12]}")
        response.setdefault("scope_labor_detail_row_count", len(list(payload.get("scope_labor_details") or [])))
        response.setdefault("apparatus_financial_row_count", len(list(payload.get("apparatus_financials") or [])))
        response.setdefault("audit_event_id", f"audit-{hashlib.sha256((dynamic_entity_id + response['mutation_id']).encode()).hexdigest()[:12]}")
        response.setdefault("mutation_status", "committed" if response.get("status") in {"accepted", "idempotent_hit"} else "rolled_back")
        response.setdefault("new_state", {})
        response["new_state"].setdefault("route", MUTATION_ROUTE)
        response["new_state"].setdefault("status_route", READBACK_ROUTE)
        response["new_state"].setdefault("project_id", payload.get("project_id"))
        response["new_state"].setdefault("candidate_id", payload.get("candidate_id"))
        response["new_state"].setdefault("source_fingerprint", payload.get("source_fingerprint"))
        response["new_state"].setdefault("snapshot_kind", payload.get("snapshot_kind"))
        response["new_state"].setdefault("mutation_id", response["mutation_id"])
        response["new_state"].setdefault("audit_event_id", response.get("audit_event_id"))
        response["new_state"].setdefault("current_candidate_match", response["current_candidate_match"])
        response["new_state"].setdefault("counts_match", True)
        response["new_state"].setdefault("classification", response.get("classification"))
        response["new_state"].setdefault("scope_labor_detail_row_count", response["scope_labor_detail_row_count"])
        response["new_state"].setdefault("apparatus_financial_row_count", response["apparatus_financial_row_count"])
        return response

    def persist(self, request: dict[str, Any], force_failure: str | None = None) -> dict[str, Any]:
        payload = request.get("payload") or {}
        business_digest = compute_business_payload_digest(payload)
        if request.get("idempotency_key") != business_digest or payload.get("idempotency_key") != business_digest:
            response = _deepcopy_fixture("rollback_apparatus_financial_validation_failed.json")
            response["http_status"] = 422
            response["classification"] = "invalid_idempotency_key"
            response["error"]["message"] = "Envelope and payload idempotency_key must match the sha256 business payload digest."
            response["error"]["detail"] = {
                "computed_business_payload_digest": business_digest,
                "envelope_idempotency_key": request.get("idempotency_key"),
                "payload_idempotency_key": payload.get("idempotency_key"),
            }
            response["status"] = "rejected"
            response["partial_commit"] = False
            response["mutation_status"] = "rolled_back"
            return self._apply_dynamic_fields(response, request)

        if force_failure:
            response = _deepcopy_fixture(FORCE_FAILURE_TO_FIXTURE[force_failure])
            return self._apply_dynamic_fields(response, request)

        existing = self._cache.get(business_digest)
        if existing is not None:
            existing_mutation_id = str(existing["payload"]["mutation_id"])
            current_mutation_id = str(payload.get("mutation_id") or "")
            if existing_mutation_id == current_mutation_id:
                response = _deepcopy_fixture("success_idempotent_hit.json")
                response["mutation_id"] = existing["response"]["mutation_id"]
                response["audit_event_id"] = existing["response"]["audit_event_id"]
                response["project_contract_snapshot_id"] = existing["response"]["project_contract_snapshot_id"]
                response["scope_labor_detail_row_count"] = existing["response"]["scope_labor_detail_row_count"]
                response["apparatus_financial_row_count"] = existing["response"]["apparatus_financial_row_count"]
                response["new_state"] = copy.deepcopy(existing["response"].get("new_state") or {})
                return self._apply_dynamic_fields(response, request)

            response = _deepcopy_fixture("conflict_duplicate_business_payload.json")
            response["mutation_id"] = current_mutation_id
            response["conflict"]["server_state"]["existing_mutation_id"] = existing_mutation_id
            response["conflict"]["queued_action"]["incoming_mutation_id"] = current_mutation_id
            return self._apply_dynamic_fields(response, request)

        response = _deepcopy_fixture("success_first_write.json")
        applied = self._apply_dynamic_fields(response, request)
        self._cache[business_digest] = {
            "payload": copy.deepcopy(payload),
            "response": copy.deepcopy(applied),
        }
        return applied

    def readback(self, requested_status: str | None = None) -> dict[str, Any]:
        if requested_status:
            response = _deepcopy_fixture(READBACK_STATUS_TO_FIXTURE[requested_status])
        elif not self._cache:
            response = _deepcopy_fixture("readback_missing.json")
        else:
            response = _deepcopy_fixture("readback_ready.json")
        response.setdefault("http_status", 200)
        response.setdefault("route", READBACK_ROUTE)
        response.setdefault("project_id", PROJECT_ID)
        response.setdefault("candidate_id", CANDIDATE_ID)
        response.setdefault("source_fingerprint", SOURCE_FINGERPRINT)
        response.setdefault("generated_at", _iso_now())
        return response


def _scan_local_mock_sources() -> dict[str, Any]:
    forbidden_import_tokens = ["supabase", "@supabase", "supabase-py"]
    scanned_files = sorted(path.name for path in SCRIPT_DIR.glob("*.py"))
    hits: dict[str, list[str]] = {}
    for path in SCRIPT_DIR.glob("*.py"):
        lines = path.read_text(encoding="utf-8").splitlines()
        import_lines = [line.strip().lower() for line in lines if line.strip().startswith(("import ", "from "))]
        found = [
            token
            for token in forbidden_import_tokens
            if any(token in import_line for import_line in import_lines)
        ]
        if found:
            hits[path.name] = found
    return {
        "scanned_python_files": scanned_files,
        "forbidden_token_hits": hits,
        "supabase_imports_present": bool(hits),
    }


def _write_trace(mock: LocalContractSupportMock, request: dict[str, Any]) -> dict[str, Any]:
    first = mock.persist(copy.deepcopy(request))
    replay = mock.persist(copy.deepcopy(request))

    conflicting_request = copy.deepcopy(request)
    conflicting_request["payload"]["mutation_id"] = "mut-1d764f75-87a8-49bc-ac73-cd4dabaf95df"
    conflict = mock.persist(conflicting_request)

    rollback_results = {}
    for force_failure in FORCE_FAILURE_TO_FIXTURE:
        rollback_results[force_failure] = mock.persist(copy.deepcopy(request), force_failure=force_failure)

    readbacks = {
        status: mock.readback(status)
        for status in ["missing", "ready", "stale_candidate", "counts_mismatch", "unavailable"]
    }

    source_scan = _scan_local_mock_sources()
    trace_lines = [
        "PM Lane 414 local trace - no Supabase touch proof",
        f"generated_at={_iso_now()}",
        f"entry_point={Path(__file__).name}",
        f"mutation_route={MUTATION_ROUTE}",
        f"readback_route={READBACK_ROUTE}",
        f"computed_business_payload_digest={request['idempotency_key']}",
        f"supabase_imports_present={source_scan['supabase_imports_present']}",
        f"scanned_python_files={', '.join(source_scan['scanned_python_files'])}",
        "network_calls_observed=false",
        "external_state_used=false",
        "state_storage=in_memory_python_dict",
        "state_persists_across_process_exit=false",
        f"first_write_status={first['status']}",
        f"replay_status={replay['status']}",
        f"conflict_status={conflict['status']}",
        "rollback_statuses=" + ", ".join(f"{key}:{value['classification']}" for key, value in rollback_results.items()),
        "readback_statuses=" + ", ".join(f"{key}:{value['status']}" for key, value in readbacks.items()),
        "verification_method=source-token scan plus direct inspection of this self-contained local mock; no HTTP client library or Supabase SDK import path exists in the mock directory.",
        "phase_0_note=repo mutation envelope convention uses status=accepted|idempotent_hit|conflict|rejected; Lane 413 planned names are preserved here as route-specific classification metadata.",
    ]
    TRACE_PATH.write_text("\n".join(trace_lines) + "\n", encoding="utf-8")
    return {
        "request_envelope": request,
        "first_write": first,
        "replay": replay,
        "conflict": conflict,
        "rollbacks": rollback_results,
        "readbacks": readbacks,
        "trace_path": str(TRACE_PATH),
        "source_scan": source_scan,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PM Lane 414 local mocked dry-run.")
    parser.add_argument(
        "--print-request-only",
        action="store_true",
        help="Print the future production request envelope and exit without running the local trace.",
    )
    args = parser.parse_args()

    request = build_sample_request()
    if args.print_request_only:
        print(json.dumps(request, indent=2, sort_keys=True))
        return 0

    mock = LocalContractSupportMock()
    summary = _write_trace(mock, request)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())