from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts/lane_502_temp_power_scope_backfill/run_lane_502_temp_power_scope_backfill.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("lane_502_temp_power_scope_backfill", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sample_report_hash_matches_lane_501_freeze():
    module = _load_module()
    report_payload = module._read_json(module.DEFAULT_RECONCILIATION_REPORT_PATH)

    assert module.compute_report_hash(report_payload) == module.EXPECTED_REPORT_HASH


def test_scope_insertability_gap_is_detected_from_frozen_sample():
    module = _load_module()
    intermediate_payload = module._read_json(module.DEFAULT_INTERMEDIATE_JSON_PATH)

    with pytest.raises(module.Phase0Abort) as exc_info:
        module._build_scope_rows(intermediate_payload["scopes"])

    assert "quoted_amount is null" in str(exc_info.value)


def test_admission_parser_and_sql_shapes_match_lane_502_contract():
    module = _load_module()
    phrase = "\n".join(
        [
            module.ADMISSION_SENTINEL,
            f"RECONCILIATION_REPORT_HASH={module.EXPECTED_REPORT_HASH}",
            "INTERMEDIATE_JSON_PATH=apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_intermediate_20260521T103643Z.json",
            "OPERATOR=GitHub Copilot",
            "TIMESTAMP=2026-05-21T12:00:00Z",
        ]
    )

    parsed = module.parse_admission_phrase(phrase)

    assert parsed["OPERATOR"] == "GitHub Copilot"
    assert module._parse_iso8601_utc(parsed["TIMESTAMP"]).isoformat() == "2026-05-21T12:00:00+00:00"
    assert "ON CONFLICT (id) DO NOTHING" in module.SCOPE_INSERT_SQL
    assert "scope_id IS NULL OR scope_id != %s" in module.APPARATUS_UPDATE_SQL