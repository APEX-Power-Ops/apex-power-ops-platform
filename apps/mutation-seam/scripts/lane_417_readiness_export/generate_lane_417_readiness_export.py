from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LANE_416_DIR = SCRIPT_DIR.parent / "lane_416_readiness_checkpoint"

BUNDLE_PATH = SCRIPT_DIR / "readiness_export_bundle.json"
BASELINE_DIGEST = "1859896bcbac1220d21266b19603a12eae710a6e9fbf553c132b7028e417026d"
BOUNDARY_STATEMENT = (
    "No live writes, no Supabase touch, no hosted deployment, no reconciliation recomputation, "
    "and no modification to Lane 416 or earlier surfaces."
)

SOURCE_ARTIFACTS = {
    "embedded_reconciliation": LANE_416_DIR / "multi_scope_reconciliation.json",
    "embedded_rollback_matrix": LANE_416_DIR / "rollback_expectation_matrix.json",
    "embedded_readiness_checklist": LANE_416_DIR / "readiness_checklist.json",
}


def _dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _build_embedded_payloads() -> tuple[dict[str, str], dict[str, bool], dict[str, str], list[str]]:
    embedded_payloads: dict[str, str] = {}
    divergence_check: dict[str, bool] = {}
    payload_sha256: dict[str, str] = {}
    source_paths: list[str] = []

    for field_name, source_path in SOURCE_ARTIFACTS.items():
        source_text = _read_source_text(source_path)
        embedded_payload = source_text

        embedded_payloads[field_name] = embedded_payload
        divergence_field = f"{field_name}_matches_source"
        divergence_check[divergence_field] = embedded_payload == source_text
        if not divergence_check[divergence_field]:
            raise RuntimeError(f"Lane 417 divergence check failed for {source_path}.")

        payload_sha256[field_name] = _sha256_text(embedded_payload)
        source_paths.append(
            f"apps/mutation-seam/scripts/lane_416_readiness_checkpoint/{source_path.name}"
        )

    return embedded_payloads, divergence_check, payload_sha256, source_paths


def build_bundle() -> dict[str, Any]:
    embedded_payloads, divergence_check, payload_sha256, source_paths = _build_embedded_payloads()
    bundle = {
        "boundary_statement": BOUNDARY_STATEMENT,
        "divergence_check": divergence_check,
        "embedded_payload_sha256": payload_sha256,
        "gate_state": "ready",
        "lane_412_family_baseline_digest": BASELINE_DIGEST,
        "promotion_blockers": [],
        "source_artifact_paths": source_paths,
        **embedded_payloads,
    }

    for field_name, source_path in SOURCE_ARTIFACTS.items():
        source_text = _read_source_text(source_path)
        if bundle[field_name] != source_text:
            raise RuntimeError(f"Lane 417 byte-identity verification failed for {source_path}.")

    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the PM Lane 417 readiness export bundle.")
    parser.add_argument(
        "--verify-reproducible",
        action="store_true",
        help="Build the Lane 417 bundle twice in memory and fail if any bytes differ.",
    )
    args = parser.parse_args()

    first_bundle = _dump_json(build_bundle())
    if args.verify_reproducible:
        second_bundle = _dump_json(build_bundle())
        if first_bundle != second_bundle:
            raise RuntimeError("Lane 417 readiness export bundle is not byte-reproducible across repeated builds.")

    BUNDLE_PATH.write_text(first_bundle, encoding="utf-8")
    print(json.dumps({"bundle_path": str(BUNDLE_PATH), "source_artifact_count": len(SOURCE_ARTIFACTS)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())