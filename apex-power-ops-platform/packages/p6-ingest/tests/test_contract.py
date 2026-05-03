from apex_p6_ingest.contract import DEFAULT_FIXTURE_PATH, get_fixture_summary, get_runtime_status


def test_runtime_status_matches_bounded_contract() -> None:
    status = get_runtime_status()

    assert status["service"] == "p6-ingest"
    assert status["status"] == "ok"
    assert status["port"] == 8081
    assert status["fixturePath"].endswith("apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer")
    assert status["fixtureExists"] is True
    assert status["storage"] == {
        "xerBucket": "p6-ingest-xer",
        "xerPrefix": "incoming",
    }
    assert status["oidc"] == {
        "issuerUrl": "https://auth.olares.local",
        "clientId": "p6-ingest-placeholder",
    }


def test_fixture_summary_matches_canary_contract() -> None:
    summary = get_fixture_summary()

    assert summary["fixture"] == "stack_data_center_baseline_sanitized.xer"
    assert summary["baseline_entry"]["p6_baseline_proj_id"] == "9998"
    assert summary["baseline_entry"]["matched_task_codes"] == ["A10", "A20", "A30"]
    assert summary["live_lane"]["task_codes"] == ["A10", "A20", "A30", "A99"]
    assert summary["negative_cases"] == {
        "baseline_only_a90_absent_from_live_lane": True,
        "live_only_a99_present": True,
    }
    assert summary["source_file"] == DEFAULT_FIXTURE_PATH.name