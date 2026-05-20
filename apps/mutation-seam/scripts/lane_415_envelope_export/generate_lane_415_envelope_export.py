from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FIXTURE_PATH = SCRIPT_DIR / "lane_415_export_inputs.json"
LANE_414_SCRIPT_PATH = SCRIPT_DIR.parent / "lane_414_local_mock" / "run_lane_414_local_mock.py"

REQUEST_EXPORT_FILENAME = "request_envelope.json"
ORDERING_PROOF_FILENAME = "ordering_proof.json"
IDEMPOTENCY_SUMMARY_FILENAME = "idempotency_key_input_summary.txt"

RESPONSE_EXPORT_FILENAMES = {
    "first_write": "response_success_first_write.json",
    "replay": "response_success_idempotent_hit.json",
    "conflict": "response_conflict_duplicate_business_payload.json",
    "rollback_scope_detail_conflict": "response_rollback_scope_detail_conflict.json",
    "rollback_apparatus_financial_validation_failed": "response_rollback_apparatus_financial_validation_failed.json",
    "rollback_audit_write_unavailable": "response_rollback_audit_write_unavailable.json",
    "rollback_idempotency_write_unavailable": "response_rollback_idempotency_write_unavailable.json",
    "readback_missing": "response_readback_missing.json",
    "readback_ready": "response_readback_ready.json",
    "readback_stale_candidate": "response_readback_stale_candidate.json",
    "readback_counts_mismatch": "response_readback_counts_mismatch.json",
    "readback_unavailable": "response_readback_unavailable.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _load_lane_414_module() -> Any:
    spec = importlib.util.spec_from_file_location("lane_414_local_mock", LANE_414_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Lane 414 module from {LANE_414_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scope_row_key(row: dict[str, Any]) -> str:
    return f"{row.get('scope_id')}|{row.get('scope_name')}"


def _apparatus_row_key(row: dict[str, Any]) -> str:
    return f"{row.get('scope_id')}|{row.get('apparatus_id')}|{row.get('apparatus_name')}"


def _canonicalize_payload(module: Any, payload: dict[str, Any]) -> dict[str, Any]:
    canonical_payload = copy.deepcopy(payload)
    canonical_payload["scope_labor_details"] = module._ordered_scope_rows(list(payload.get("scope_labor_details") or []))
    canonical_payload["apparatus_financials"] = module._ordered_apparatus_rows(list(payload.get("apparatus_financials") or []))
    return canonical_payload


def _digest_parts(module: Any, payload: dict[str, Any]) -> list[str]:
    ordered_payload = _canonicalize_payload(module, payload)
    return [
        str(ordered_payload.get("project_id") or ""),
        str(ordered_payload.get("candidate_id") or ""),
        str(ordered_payload.get("source_fingerprint") or ""),
        str(ordered_payload.get("snapshot_kind") or ""),
        str(ordered_payload.get("contract_value") or ""),
        str(ordered_payload.get("total_quoted_hours") or ""),
        module._stable_json(ordered_payload.get("scope_labor_details") or []),
        module._stable_json(ordered_payload.get("apparatus_financials") or []),
    ]


def _build_request_envelope(module: Any, export_inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_payload = copy.deepcopy(export_inputs["payload"])
    digest = module.compute_business_payload_digest(raw_payload)
    canonical_payload = _canonicalize_payload(module, raw_payload)
    canonical_payload["idempotency_key"] = digest

    request_metadata = export_inputs["request_envelope"]
    request_envelope = {
        "idempotency_key": digest,
        "mutation_class": request_metadata["mutation_class"],
        "action_type": module.ACTION_TYPE,
        "entity_id": module.build_contract_support_entity_id(canonical_payload),
        "payload": canonical_payload,
        "reason": request_metadata["reason"],
        "source": request_metadata["source"],
        "client_timestamp": request_metadata["client_timestamp"],
    }
    return request_envelope, raw_payload


def _build_response_exports(module: Any, request_envelope: dict[str, Any], export_inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fixed_generated_at = export_inputs["response_placeholders"]["generated_at"]
    conflicting_mutation_id = export_inputs["response_placeholders"]["conflicting_mutation_id"]
    original_iso_now = module._iso_now
    try:
        module._iso_now = lambda: fixed_generated_at
        mock = module.LocalContractSupportMock()

        first_write = mock.persist(copy.deepcopy(request_envelope))
        replay = mock.persist(copy.deepcopy(request_envelope))

        conflicting_request = copy.deepcopy(request_envelope)
        conflicting_request["payload"]["mutation_id"] = conflicting_mutation_id
        conflict = mock.persist(conflicting_request)

        rollback_scope_detail_conflict = mock.persist(copy.deepcopy(request_envelope), force_failure="scope_detail_conflict")
        rollback_apparatus_financial_validation_failed = mock.persist(
            copy.deepcopy(request_envelope),
            force_failure="apparatus_financial_validation_failed",
        )
        rollback_audit_write_unavailable = mock.persist(copy.deepcopy(request_envelope), force_failure="audit_write_unavailable")
        rollback_idempotency_write_unavailable = mock.persist(
            copy.deepcopy(request_envelope),
            force_failure="idempotency_write_unavailable",
        )

        readback_missing = mock.readback("missing")
        readback_ready = mock.readback("ready")
        readback_stale_candidate = mock.readback("stale_candidate")
        readback_counts_mismatch = mock.readback("counts_mismatch")
        readback_unavailable = mock.readback("unavailable")
    finally:
        module._iso_now = original_iso_now

    return {
        "first_write": first_write,
        "replay": replay,
        "conflict": conflict,
        "rollback_scope_detail_conflict": rollback_scope_detail_conflict,
        "rollback_apparatus_financial_validation_failed": rollback_apparatus_financial_validation_failed,
        "rollback_audit_write_unavailable": rollback_audit_write_unavailable,
        "rollback_idempotency_write_unavailable": rollback_idempotency_write_unavailable,
        "readback_missing": readback_missing,
        "readback_ready": readback_ready,
        "readback_stale_candidate": readback_stale_candidate,
        "readback_counts_mismatch": readback_counts_mismatch,
        "readback_unavailable": readback_unavailable,
    }


def _reorder_payload(payload: dict[str, Any], scope_rows: list[dict[str, Any]], apparatus_rows: list[dict[str, Any]]) -> dict[str, Any]:
    reordered = copy.deepcopy(payload)
    reordered["scope_labor_details"] = copy.deepcopy(scope_rows)
    reordered["apparatus_financials"] = copy.deepcopy(apparatus_rows)
    return reordered


def _build_ordering_case(module: Any, name: str, payload: dict[str, Any], baseline_digest: str) -> dict[str, Any]:
    canonical_payload = _canonicalize_payload(module, payload)
    digest = module.compute_business_payload_digest(payload)
    return {
        "case": name,
        "input_payload": copy.deepcopy(payload),
        "input_scope_order": [_scope_row_key(row) for row in payload.get("scope_labor_details") or []],
        "input_apparatus_order": [_apparatus_row_key(row) for row in payload.get("apparatus_financials") or []],
        "canonical_scope_order": [_scope_row_key(row) for row in canonical_payload.get("scope_labor_details") or []],
        "canonical_apparatus_order": [_apparatus_row_key(row) for row in canonical_payload.get("apparatus_financials") or []],
        "digest": digest,
        "matches_baseline_digest": digest == baseline_digest,
    }


def _build_ordering_proof(module: Any, raw_payload: dict[str, Any], request_envelope: dict[str, Any]) -> dict[str, Any]:
    baseline_digest = request_envelope["idempotency_key"]
    canonical_payload = request_envelope["payload"]

    reversed_payload = _reorder_payload(
        raw_payload,
        list(reversed(raw_payload.get("scope_labor_details") or [])),
        list(reversed(raw_payload.get("apparatus_financials") or [])),
    )
    canonical_order_payload = _reorder_payload(
        raw_payload,
        canonical_payload.get("scope_labor_details") or [],
        canonical_payload.get("apparatus_financials") or [],
    )

    reorder_cases = [
        _build_ordering_case(module, "input_fixture_order", raw_payload, baseline_digest),
        _build_ordering_case(module, "reversed_input_order", reversed_payload, baseline_digest),
        _build_ordering_case(module, "canonical_sorted_order", canonical_order_payload, baseline_digest),
    ]

    changed_scope_pool_amount = copy.deepcopy(raw_payload)
    changed_scope_pool_amount["scope_labor_details"][0]["scope_pool_amount"] = 4001.0

    changed_apparatus_revenue = copy.deepcopy(raw_payload)
    changed_apparatus_revenue["apparatus_financials"][0]["quoted_revenue"] = 1501.0

    added_apparatus_row = copy.deepcopy(raw_payload)
    added_apparatus_row["apparatus_financials"].append(
        {
            "scope_id": "scope-b",
            "apparatus_id": "app-b-003",
            "apparatus_name": "Transformer Bay 3",
            "quoted_hours": 5.0,
            "quoted_revenue": 500.0,
            "recognition_rate_per_hour_snapshot": 100.0,
        }
    )

    removed_apparatus_row = copy.deepcopy(raw_payload)
    removed_apparatus_row["apparatus_financials"] = removed_apparatus_row["apparatus_financials"][1:]

    business_field_change_cases = [
        {
            "case": "scope_pool_amount_changed",
            "change": "scope_labor_details[0].scope_pool_amount changed from 4000.0 to 4001.0",
            "input_payload": changed_scope_pool_amount,
            "digest": module.compute_business_payload_digest(changed_scope_pool_amount),
            "matches_baseline_digest": module.compute_business_payload_digest(changed_scope_pool_amount) == baseline_digest,
        },
        {
            "case": "apparatus_quoted_revenue_changed",
            "change": "apparatus_financials[0].quoted_revenue changed from 1500.0 to 1501.0",
            "input_payload": changed_apparatus_revenue,
            "digest": module.compute_business_payload_digest(changed_apparatus_revenue),
            "matches_baseline_digest": module.compute_business_payload_digest(changed_apparatus_revenue) == baseline_digest,
        },
        {
            "case": "apparatus_row_added",
            "change": "one additional apparatus_financials row appended for scope-b",
            "input_payload": added_apparatus_row,
            "digest": module.compute_business_payload_digest(added_apparatus_row),
            "matches_baseline_digest": module.compute_business_payload_digest(added_apparatus_row) == baseline_digest,
        },
        {
            "case": "apparatus_row_removed",
            "change": "first apparatus_financials row removed from the business payload",
            "input_payload": removed_apparatus_row,
            "digest": module.compute_business_payload_digest(removed_apparatus_row),
            "matches_baseline_digest": module.compute_business_payload_digest(removed_apparatus_row) == baseline_digest,
        },
    ]

    return {
        "canonical_sort_orders": {
            "scope_labor_details": [
                "scope_id ascending",
                "scope_name ascending",
            ],
            "apparatus_financials": [
                "scope_id ascending",
                "apparatus_id ascending",
                "apparatus_name ascending",
            ],
        },
        "baseline_digest": baseline_digest,
        "reorder_stability_cases": reorder_cases,
        "business_field_change_cases": business_field_change_cases,
    }


def _build_idempotency_summary(module: Any, request_envelope: dict[str, Any]) -> str:
    payload = request_envelope["payload"]
    digest_parts = _digest_parts(module, payload)
    concatenated_input = "|".join(digest_parts)
    digest = hashlib.sha256(concatenated_input.encode("utf-8")).hexdigest()

    summary_lines = [
        "PM Lane 415 idempotency-key input summary",
        f"project_id={payload['project_id']}",
        f"candidate_id={payload['candidate_id']}",
        f"source_fingerprint={payload['source_fingerprint']}",
        f"snapshot_kind={payload['snapshot_kind']}",
        f"contract_value={payload['contract_value']}",
        f"total_quoted_hours={payload['total_quoted_hours']}",
        "scope_labor_details_canonical=",
    ]
    for index, row in enumerate(payload.get("scope_labor_details") or [], start=1):
        summary_lines.append(f"  {index}. {module._stable_json(row)}")

    summary_lines.append("apparatus_financials_canonical=")
    for index, row in enumerate(payload.get("apparatus_financials") or [], start=1):
        summary_lines.append(f"  {index}. {module._stable_json(row)}")

    summary_lines.extend(
        [
            "sha256_concatenated_input=",
            concatenated_input,
            f"sha256_digest={digest}",
        ]
    )

    if digest != request_envelope["idempotency_key"]:
        raise RuntimeError("Computed digest summary does not match the exported request idempotency key.")

    return "\n".join(summary_lines) + "\n"


def build_export_bundle() -> dict[str, str]:
    module = _load_lane_414_module()
    export_inputs = _load_json(INPUT_FIXTURE_PATH)
    request_envelope, raw_payload = _build_request_envelope(module, export_inputs)
    response_exports = _build_response_exports(module, request_envelope, export_inputs)
    ordering_proof = _build_ordering_proof(module, raw_payload, request_envelope)
    idempotency_summary = _build_idempotency_summary(module, request_envelope)

    bundle: dict[str, str] = {
        REQUEST_EXPORT_FILENAME: _dump_json(request_envelope),
        ORDERING_PROOF_FILENAME: _dump_json(ordering_proof),
        IDEMPOTENCY_SUMMARY_FILENAME: idempotency_summary,
    }
    for key, filename in RESPONSE_EXPORT_FILENAMES.items():
        bundle[filename] = _dump_json(response_exports[key])
    return bundle


def _write_bundle(bundle: dict[str, str]) -> None:
    for filename, content in sorted(bundle.items()):
        (SCRIPT_DIR / filename).write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the PM Lane 415 dry-run envelope export artifacts.")
    parser.add_argument(
        "--verify-reproducible",
        action="store_true",
        help="Build the full export bundle twice in memory and fail if any output differs.",
    )
    args = parser.parse_args()

    first_bundle = build_export_bundle()
    if args.verify_reproducible:
        second_bundle = build_export_bundle()
        if first_bundle != second_bundle:
            raise RuntimeError("Lane 415 export bundle is not byte-reproducible across repeated builds.")

    _write_bundle(first_bundle)
    print(json.dumps({"artifact_count": len(first_bundle), "output_directory": str(SCRIPT_DIR)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())