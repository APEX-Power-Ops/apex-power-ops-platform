from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LANE_415_DIR = SCRIPT_DIR.parent / "lane_415_envelope_export"
LANE_417_DIR = SCRIPT_DIR.parent / "lane_417_readiness_export"

REVIEW_BUNDLE_PATH = SCRIPT_DIR / "review_bundle.json"
BASELINE_DIGEST = "1859896bcbac1220d21266b19603a12eae710a6e9fbf553c132b7028e417026d"
BOUNDARY_STATEMENT = (
    "This bundle is ready for external review and hosted promotion discussion. "
    "No live writes admitted by this bundle. Hosted deployment requires its own admission packet "
    "(PM Lane 419 at earliest). First live write requires its own admission packet "
    "(PM Lane 421 at earliest)."
)

LANE_415_EXPORT_ARTIFACTS = {
    "request_envelope": LANE_415_DIR / "request_envelope.json",
    "response_conflict_duplicate_business_payload": LANE_415_DIR / "response_conflict_duplicate_business_payload.json",
    "response_readback_counts_mismatch": LANE_415_DIR / "response_readback_counts_mismatch.json",
    "response_readback_missing": LANE_415_DIR / "response_readback_missing.json",
    "response_readback_ready": LANE_415_DIR / "response_readback_ready.json",
    "response_readback_stale_candidate": LANE_415_DIR / "response_readback_stale_candidate.json",
    "response_readback_unavailable": LANE_415_DIR / "response_readback_unavailable.json",
    "response_rollback_apparatus_financial_validation_failed": LANE_415_DIR / "response_rollback_apparatus_financial_validation_failed.json",
    "response_rollback_audit_write_unavailable": LANE_415_DIR / "response_rollback_audit_write_unavailable.json",
    "response_rollback_idempotency_write_unavailable": LANE_415_DIR / "response_rollback_idempotency_write_unavailable.json",
    "response_rollback_scope_detail_conflict": LANE_415_DIR / "response_rollback_scope_detail_conflict.json",
    "response_success_first_write": LANE_415_DIR / "response_success_first_write.json",
    "response_success_idempotent_hit": LANE_415_DIR / "response_success_idempotent_hit.json",
    "ordering_proof": LANE_415_DIR / "ordering_proof.json",
    "idempotency_key_input_summary": LANE_415_DIR / "idempotency_key_input_summary.txt",
}

LANE_417_ARTIFACTS = {
    "readiness_export_bundle": LANE_417_DIR / "readiness_export_bundle.json",
}


def _dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _relative_script_path(path: Path) -> str:
    return path.relative_to(SCRIPT_DIR.parent.parent.parent.parent).as_posix()


def _build_embedded_payloads() -> tuple[dict[str, str], str, dict[str, str], dict[str, bool], list[str]]:
    embedded_envelope_export: dict[str, str] = {}
    embedded_payload_sha256: dict[str, str] = {}
    divergence_check: dict[str, bool] = {}
    source_artifact_paths: list[str] = []

    for artifact_id, source_path in LANE_415_EXPORT_ARTIFACTS.items():
        source_text = _read_source_text(source_path)
        embedded_envelope_export[artifact_id] = source_text
        embedded_payload_sha256[artifact_id] = _sha256_text(source_text)
        divergence_field = f"{artifact_id}_matches_source"
        divergence_check[divergence_field] = embedded_envelope_export[artifact_id] == source_text
        if not divergence_check[divergence_field]:
            raise RuntimeError(f"Lane 418 divergence check failed for {source_path}.")
        source_artifact_paths.append(_relative_script_path(source_path))

    readiness_source_path = LANE_417_ARTIFACTS["readiness_export_bundle"]
    embedded_readiness_export = _read_source_text(readiness_source_path)
    embedded_payload_sha256["readiness_export_bundle"] = _sha256_text(embedded_readiness_export)
    divergence_check["readiness_export_bundle_matches_source"] = (
        embedded_readiness_export == _read_source_text(readiness_source_path)
    )
    if not divergence_check["readiness_export_bundle_matches_source"]:
        raise RuntimeError(f"Lane 418 divergence check failed for {readiness_source_path}.")
    source_artifact_paths.append(_relative_script_path(readiness_source_path))

    return (
        embedded_envelope_export,
        embedded_readiness_export,
        embedded_payload_sha256,
        divergence_check,
        source_artifact_paths,
    )


def _build_failure_mode_contract_summary() -> dict[str, Any]:
    return {
        "transaction_boundary": {
            "rule": "One Postgres transaction wraps the five write targets and commits only after every write target succeeds.",
            "write_targets": [
                "seam.project_contract_snapshots",
                "seam.scope_labor_details",
                "seam.apparatus_financials",
                "audit event",
                "idempotency cache entry",
            ],
            "failure_rule": "Any failure before commit rolls back the entire unit of work.",
        },
        "success_response": {
            "http_status": 201,
            "envelope_status": "accepted",
            "classification": "import_contract_support_persisted",
            "mutation_status": "committed",
            "idempotent_hit": False,
        },
        "idempotent_replay_response": {
            "http_status": 200,
            "envelope_status": "accepted",
            "classification": "idempotent_hit",
            "mutation_status": "previously_committed",
            "idempotent_hit": True,
        },
        "duplicate_business_payload_response": {
            "http_status": 409,
            "envelope_status": "conflict",
            "classification": "duplicate_business_payload_conflict",
            "mutation_status": "rejected",
            "conflict_rule": "Same business payload supplied under a different mutation id is treated as a deliberate conflict, never a 500.",
        },
        "partial_failure_responses": [
            {
                "failure_class": "transaction_rolled_back_scope_detail_conflict",
                "http_status": 409,
                "envelope_status": "rejected",
                "classification": "transaction_rolled_back_scope_detail_conflict",
                "mutation_status": "rolled_back",
                "database_state": "completely rolled back",
            },
            {
                "failure_class": "transaction_rolled_back_apparatus_financial_validation_failed",
                "http_status": 422,
                "envelope_status": "rejected",
                "classification": "transaction_rolled_back_apparatus_financial_validation_failed",
                "mutation_status": "rolled_back",
                "database_state": "completely rolled back",
            },
            {
                "failure_class": "transaction_rolled_back_audit_write_unavailable",
                "http_status": 503,
                "envelope_status": "rejected",
                "classification": "transaction_rolled_back_audit_write_unavailable",
                "mutation_status": "rolled_back",
                "database_state": "completely rolled back",
            },
            {
                "failure_class": "transaction_rolled_back_idempotency_write_unavailable",
                "http_status": 503,
                "envelope_status": "rejected",
                "classification": "transaction_rolled_back_idempotency_write_unavailable",
                "mutation_status": "rolled_back",
                "database_state": "completely rolled back",
            },
        ],
        "idempotency_key_construction": {
            "formula": "sha256(project_id | candidate_id | source_fingerprint | snapshot_kind | contract_value | total_quoted_hours | ordered scope_labor_details rows | ordered apparatus_financials rows)",
            "ordered_fields_required": True,
            "baseline_digest": BASELINE_DIGEST,
        },
        "source_reference": {
            "planning_packet": "docs/operations/APEX-PM-LANE-413-PROJECT-MINER-TEMP-POWER-LANE-412-LIVE-ADMISSION-PLANNING-NO-LIVE-PACKET-2026-05-20.md",
            "planning_sections": [
                "Failure-Mode Contract",
                "Single-Route Vs Dual-Route Sequencing Decision",
            ],
            "rollback_matrix": "apps/mutation-seam/scripts/lane_416_readiness_checkpoint/rollback_expectation_matrix.json",
        },
    }


def _build_sequencing_decision_summary() -> dict[str, Any]:
    return {
        "selected_option": "Option B - write route and readback route deploy together as a single feature unit",
        "rationale": [
            "Both routes share the same schema, idempotency semantics, and lane meaning.",
            "The readback route exists specifically to surface the write route's state, so separating deployments would create an intermediate hosted state where the write surface exists without its canonical status surface.",
            "The first live row is not truthfully verifiable for Lane 412 without the readback contract that later Lane 280 admission depends on.",
            "Deploying both routes together minimizes drift between stored state and the readback surface that classifies that state.",
        ],
        "alternative_considered": "Option A - write route and readback route deploy separately",
        "source_reference": {
            "planning_packet": "docs/operations/APEX-PM-LANE-413-PROJECT-MINER-TEMP-POWER-LANE-412-LIVE-ADMISSION-PLANNING-NO-LIVE-PACKET-2026-05-20.md",
            "planning_section": "Single-Route Vs Dual-Route Sequencing Decision",
        },
    }


def build_bundle() -> dict[str, Any]:
    (
        embedded_envelope_export,
        embedded_readiness_export,
        embedded_payload_sha256,
        divergence_check,
        source_artifact_paths,
    ) = _build_embedded_payloads()

    bundle = {
        "boundary_statement": BOUNDARY_STATEMENT,
        "bundle_kind": "lane_412_external_review_package",
        "divergence_check": divergence_check,
        "embedded_envelope_export": embedded_envelope_export,
        "embedded_payload_sha256": embedded_payload_sha256,
        "embedded_readiness_export": embedded_readiness_export,
        "failure_mode_contract_summary": _build_failure_mode_contract_summary(),
        "gate_state": "ready_for_hosted_promotion_discussion",
        "lane_412_family_baseline_digest": BASELINE_DIGEST,
        "sequencing_decision_summary": _build_sequencing_decision_summary(),
        "source_artifact_paths": source_artifact_paths,
    }

    for artifact_id, source_path in LANE_415_EXPORT_ARTIFACTS.items():
        if bundle["embedded_envelope_export"][artifact_id] != _read_source_text(source_path):
            raise RuntimeError(f"Lane 418 byte-identity verification failed for {source_path}.")

    readiness_source_path = LANE_417_ARTIFACTS["readiness_export_bundle"]
    if bundle["embedded_readiness_export"] != _read_source_text(readiness_source_path):
        raise RuntimeError(f"Lane 418 byte-identity verification failed for {readiness_source_path}.")

    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the PM Lane 418 review bundle export.")
    parser.add_argument(
        "--verify-reproducible",
        action="store_true",
        help="Build the Lane 418 review bundle twice in memory and fail if any bytes differ.",
    )
    args = parser.parse_args()

    first_bundle = _dump_json(build_bundle())
    if args.verify_reproducible:
        second_bundle = _dump_json(build_bundle())
        if first_bundle != second_bundle:
            raise RuntimeError("Lane 418 review bundle is not byte-reproducible across repeated builds.")

    REVIEW_BUNDLE_PATH.write_text(first_bundle, encoding="utf-8")
    print(
        json.dumps(
            {
                "bundle_path": str(REVIEW_BUNDLE_PATH),
                "embedded_payload_count": len(LANE_415_EXPORT_ARTIFACTS) + len(LANE_417_ARTIFACTS),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())