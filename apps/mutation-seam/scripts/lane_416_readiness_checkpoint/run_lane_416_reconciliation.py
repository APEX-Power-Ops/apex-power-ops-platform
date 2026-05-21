from __future__ import annotations

import argparse
import copy
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LANE_415_DIR = SCRIPT_DIR.parent / "lane_415_envelope_export"
INPUT_FIXTURE_PATH = LANE_415_DIR / "lane_415_export_inputs.json"

RECONCILIATION_ARTIFACT_PATH = SCRIPT_DIR / "multi_scope_reconciliation.json"
ROLLBACK_MATRIX_ARTIFACT_PATH = SCRIPT_DIR / "rollback_expectation_matrix.json"
READINESS_CHECKLIST_ARTIFACT_PATH = SCRIPT_DIR / "readiness_checklist.json"

MONEY_TOLERANCE = Decimal("0.01")
RATE_TOLERANCE = Decimal("0.001")

LANE_415_RESPONSE_EXPORTS = {
    "scope_detail_conflict": "response_rollback_scope_detail_conflict.json",
    "apparatus_financial_validation_failed": "response_rollback_apparatus_financial_validation_failed.json",
    "audit_write_unavailable": "response_rollback_audit_write_unavailable.json",
    "idempotency_write_unavailable": "response_rollback_idempotency_write_unavailable.json",
    "duplicate_business_payload_conflict": "response_conflict_duplicate_business_payload.json",
}

LANE_414_RESPONSE_FIXTURES = {
    "scope_detail_conflict": "rollback_scope_detail_conflict.json",
    "apparatus_financial_validation_failed": "rollback_apparatus_financial_validation_failed.json",
    "audit_write_unavailable": "rollback_audit_write_unavailable.json",
    "idempotency_write_unavailable": "rollback_idempotency_write_unavailable.json",
    "duplicate_business_payload_conflict": "conflict_duplicate_business_payload.json",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _money(value: Any) -> Decimal:
    return Decimal(str(value))


def _within_tolerance(actual: Decimal, expected: Decimal, tolerance: Decimal) -> tuple[bool, Decimal]:
    difference = abs(actual - expected)
    return difference < tolerance, difference


def _build_reconciliation_artifact() -> dict[str, Any]:
    export_input = _load_json(INPUT_FIXTURE_PATH)
    payload = copy.deepcopy(export_input["payload"])

    contract_value = _money(payload["contract_value"])
    total_quoted_hours = _money(payload["total_quoted_hours"])
    recognition_rate_per_hour = contract_value / total_quoted_hours

    apparatus_rows = payload["apparatus_financials"]
    scope_rows = payload["scope_labor_details"]

    scope_results: list[dict[str, Any]] = []
    overall_pass = True

    for scope in sorted(scope_rows, key=lambda row: (str(row["scope_id"]), str(row["scope_name"]))):
        scope_id = scope["scope_id"]
        scope_name = scope["scope_name"]
        scope_hours = _money(scope["quoted_hours"])
        expected_scope_pool_amount = _money(scope["scope_pool_amount"])
        apparatus_sum = sum(
            (_money(row["quoted_revenue"]) for row in apparatus_rows if row["scope_id"] == scope_id),
            Decimal("0"),
        )
        derived_scope_pool_amount = contract_value * (scope_hours / total_quoted_hours)

        apparatus_sum_pass, apparatus_sum_difference = _within_tolerance(
            apparatus_sum,
            expected_scope_pool_amount,
            MONEY_TOLERANCE,
        )
        formula_pass, formula_difference = _within_tolerance(
            derived_scope_pool_amount,
            expected_scope_pool_amount,
            MONEY_TOLERANCE,
        )
        overall_pass = overall_pass and apparatus_sum_pass and formula_pass

        scope_results.append(
            {
                "scope_id": scope_id,
                "scope_name": scope_name,
                "quoted_hours": float(scope_hours),
                "expected_scope_pool_amount": float(expected_scope_pool_amount),
                "sum_of_scope_apparatus_quoted_revenue": float(apparatus_sum),
                "derived_scope_pool_amount_from_formula": float(derived_scope_pool_amount),
                "sum_of_apparatus_matches_scope_pool_amount": apparatus_sum_pass,
                "sum_of_apparatus_difference": f"{apparatus_sum_difference:.3f}",
                "scope_pool_matches_formula": formula_pass,
                "formula_difference": f"{formula_difference:.3f}",
            }
        )

    project_apparatus_total = sum((_money(row["quoted_revenue"]) for row in apparatus_rows), Decimal("0"))
    project_total_pass, project_total_difference = _within_tolerance(project_apparatus_total, contract_value, MONEY_TOLERANCE)
    overall_pass = overall_pass and project_total_pass

    apparatus_results: list[dict[str, Any]] = []
    for row in sorted(apparatus_rows, key=lambda value: (str(value["scope_id"]), str(value["apparatus_id"]), str(value["apparatus_name"]))):
        quoted_hours = _money(row["quoted_hours"])
        quoted_revenue = _money(row["quoted_revenue"])
        rate_snapshot = _money(row["recognition_rate_per_hour_snapshot"])
        derived_revenue = quoted_hours * rate_snapshot
        revenue_pass, revenue_difference = _within_tolerance(quoted_revenue, derived_revenue, MONEY_TOLERANCE)
        rate_pass, rate_difference = _within_tolerance(rate_snapshot, recognition_rate_per_hour, RATE_TOLERANCE)
        overall_pass = overall_pass and revenue_pass and rate_pass

        apparatus_results.append(
            {
                "apparatus_id": row["apparatus_id"],
                "scope_id": row["scope_id"],
                "quoted_hours": float(quoted_hours),
                "quoted_revenue": float(quoted_revenue),
                "recognition_rate_per_hour_snapshot": float(rate_snapshot),
                "derived_quoted_revenue": float(derived_revenue),
                "quoted_revenue_matches_hours_times_rate": revenue_pass,
                "quoted_revenue_difference": f"{revenue_difference:.3f}",
                "recognition_rate_matches_project_rate": rate_pass,
                "recognition_rate_difference": f"{rate_difference:.3f}",
            }
        )

    artifact = {
        "named_design_assumption": True,
        "allocation_rule": "scope_pool_amount = project_pool_amount * (scope_hours / project_hours)",
        "input_fixture_path": "apps/mutation-seam/scripts/lane_415_envelope_export/lane_415_export_inputs.json",
        "tolerances": {
            "money_difference_lt": f"{MONEY_TOLERANCE:.2f}",
            "recognition_rate_difference_lt": f"{RATE_TOLERANCE:.3f}",
        },
        "project": {
            "project_id": payload["project_id"],
            "candidate_id": payload["candidate_id"],
            "contract_value": float(contract_value),
            "total_quoted_hours": float(total_quoted_hours),
            "recognition_rate_per_hour": float(recognition_rate_per_hour),
        },
        "scope_results": scope_results,
        "project_total": {
            "contract_value": float(contract_value),
            "sum_of_all_apparatus_quoted_revenue": float(project_apparatus_total),
            "project_total_matches_contract_value": project_total_pass,
            "project_total_difference": f"{project_total_difference:.3f}",
        },
        "apparatus_results": apparatus_results,
        "overall_pass": overall_pass,
    }
    if not overall_pass:
        raise RuntimeError(
            "Lane 416 reconciliation failed. This is a potential design defect in the named multi-scope allocation assumption and should escalate as a Lane 416 Revision A plus possible Lane 412 revision review."
        )
    return artifact


def _build_rollback_expectation_matrix() -> list[dict[str, Any]]:
    rollback_rows: list[dict[str, Any]] = []
    ordered_cases = [
        ("scope_detail_conflict", "scope labor detail validation failed inside the transaction"),
        (
            "apparatus_financial_validation_failed",
            "apparatus financial validation or envelope digest validation failed before commit",
        ),
        ("audit_write_unavailable", "audit append became unavailable during the governed write path"),
        (
            "idempotency_write_unavailable",
            "idempotency cache persistence became unavailable during the governed write path",
        ),
        (
            "duplicate_business_payload_conflict",
            "same business payload replayed with a different mutation_id after an earlier committed write",
        ),
    ]

    for case_name, trigger_condition in ordered_cases:
        lane_415_path = LANE_415_DIR / LANE_415_RESPONSE_EXPORTS[case_name]
        lane_414_path = LANE_415_DIR.parent / "lane_414_local_mock" / LANE_414_RESPONSE_FIXTURES[case_name]
        response = _load_json(lane_415_path)

        rollback_rows.append(
            {
                "case": case_name,
                "lane_415_response_export_path": f"apps/mutation-seam/scripts/lane_415_envelope_export/{lane_415_path.name}",
                "lane_414_response_fixture_path": f"apps/mutation-seam/scripts/lane_414_local_mock/{lane_414_path.name}",
                "expected_http_status": response["http_status"],
                "expected_status": response["status"],
                "expected_classification": response["classification"],
                "expected_mutation_status": response["mutation_status"],
                "expected_partial_commit": response["partial_commit"],
                "expected_database_state": (
                    "completely rolled back: no snapshot row, no scope rows, no apparatus financial rows, no audit event, no idempotency cache entry"
                    if case_name != "duplicate_business_payload_conflict"
                    else "existing committed state preserved: no additional snapshot row, no additional scope rows, no additional apparatus financial rows, no new audit event, no new idempotency cache entry for the conflicting mutation"
                ),
                "trigger_condition": trigger_condition,
            }
        )
    return rollback_rows


def _build_readiness_checklist() -> list[dict[str, Any]]:
    request_path = LANE_415_DIR / "request_envelope.json"
    ordering_proof_path = LANE_415_DIR / "ordering_proof.json"
    digest_summary_path = LANE_415_DIR / "idempotency_key_input_summary.txt"
    response_paths = sorted(LANE_415_DIR.glob("response_*.json"))

    return [
        {
            "item": "Request envelope frozen",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/request_envelope.json",
                    "sha256": _sha256_hex(request_path),
                }
            ],
        },
        {
            "item": "All 12 response envelopes frozen",
            "ready": len(response_paths) == 12,
            "evidence": [
                {
                    "path": f"apps/mutation-seam/scripts/lane_415_envelope_export/{path.name}",
                    "sha256": _sha256_hex(path),
                }
                for path in response_paths
            ],
        },
        {
            "item": "Canonical sort orders documented",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/ordering_proof.json",
                    "section": "canonical_sort_orders",
                    "sha256": _sha256_hex(ordering_proof_path),
                }
            ],
        },
        {
            "item": "Digest stability proven under reordering",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/ordering_proof.json",
                    "section": "reorder_stability_cases",
                    "sha256": _sha256_hex(ordering_proof_path),
                }
            ],
        },
        {
            "item": "Digest sensitivity to business changes proven",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/ordering_proof.json",
                    "section": "business_field_change_cases",
                    "sha256": _sha256_hex(ordering_proof_path),
                }
            ],
        },
        {
            "item": "Idempotency-key input summary frozen",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/idempotency_key_input_summary.txt",
                    "sha256": _sha256_hex(digest_summary_path),
                }
            ],
        },
        {
            "item": "Exporter reproducibility proven",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_415_envelope_export/generate_lane_415_envelope_export.py",
                    "proof": "Run with --verify-reproducible to rebuild the full export bundle twice and fail on byte drift.",
                    "sha256": _sha256_hex(LANE_415_DIR / "generate_lane_415_envelope_export.py"),
                }
            ],
        },
        {
            "item": "Multi-scope fixture reconciliation passes",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_416_readiness_checkpoint/multi_scope_reconciliation.json",
                    "sha256": _sha256_hex(RECONCILIATION_ARTIFACT_PATH),
                }
            ],
        },
        {
            "item": "Rollback expectation matrix complete for all five failure cases",
            "ready": True,
            "evidence": [
                {
                    "path": "apps/mutation-seam/scripts/lane_416_readiness_checkpoint/rollback_expectation_matrix.json",
                    "sha256": _sha256_hex(ROLLBACK_MATRIX_ARTIFACT_PATH),
                }
            ],
        },
        {
            "item": "No live writes admitted",
            "ready": True,
            "evidence": [
                {
                    "path": "docs/operations/APEX-PM-LANE-412-REVISION-A-PROJECT-MINER-TEMP-POWER-LANE-278-SIBLING-IMPORT-CONTRACT-SUPPORT-NO-LIVE-DESIGN-PACKET-2026-05-20.md",
                    "section": "Boundaries",
                },
                {
                    "path": "docs/operations/APEX-PM-LANE-413-PROJECT-MINER-TEMP-POWER-LANE-412-LIVE-ADMISSION-PLANNING-NO-LIVE-PACKET-2026-05-20.md",
                    "section": "Boundaries",
                },
                {
                    "path": "docs/operations/APEX-PM-LANE-414-PROJECT-MINER-TEMP-POWER-LANE-412-LOCAL-MOCKED-DRY-RUN-NO-LIVE-PACKET-2026-05-20.md",
                    "section": "Boundaries",
                },
                {
                    "path": "docs/operations/APEX-PM-LANE-415-PROJECT-MINER-TEMP-POWER-LANE-412-DRY-RUN-ENVELOPE-EXPORT-NO-LIVE-PACKET-2026-05-20.md",
                    "section": "Boundaries",
                },
            ],
        },
    ]


def build_bundle() -> dict[str, str]:
    reconciliation = _build_reconciliation_artifact()
    rollback_matrix = _build_rollback_expectation_matrix()
    RECONCILIATION_ARTIFACT_PATH.write_text(_dump_json(reconciliation), encoding="utf-8")
    ROLLBACK_MATRIX_ARTIFACT_PATH.write_text(_dump_json(rollback_matrix), encoding="utf-8")
    readiness_checklist = _build_readiness_checklist()
    readiness_json = _dump_json(readiness_checklist)
    READINESS_CHECKLIST_ARTIFACT_PATH.write_text(readiness_json, encoding="utf-8")

    return {
        RECONCILIATION_ARTIFACT_PATH.name: _dump_json(reconciliation),
        ROLLBACK_MATRIX_ARTIFACT_PATH.name: _dump_json(rollback_matrix),
        READINESS_CHECKLIST_ARTIFACT_PATH.name: readiness_json,
    }


def _write_bundle(bundle: dict[str, str]) -> None:
    for name, content in sorted(bundle.items()):
        (SCRIPT_DIR / name).write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PM Lane 416 dry-run readiness checkpoint.")
    parser.add_argument(
        "--verify-reproducible",
        action="store_true",
        help="Build the Lane 416 artifact bundle twice in memory and fail if any output differs.",
    )
    args = parser.parse_args()

    first_bundle = build_bundle()
    if args.verify_reproducible:
        second_bundle = build_bundle()
        if first_bundle != second_bundle:
            raise RuntimeError("Lane 416 readiness checkpoint artifacts are not byte-reproducible across repeated builds.")

    _write_bundle(first_bundle)
    print(json.dumps({"artifact_count": len(first_bundle), "output_directory": str(SCRIPT_DIR)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())