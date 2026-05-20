import asyncio
import base64
import json
from pathlib import Path

import pytest

from app.auth.jwt import Actor
from app.contract_support_response_fixtures import CONTRACT_SUPPORT_RESPONSE_FIXTURE_BY_FILENAME
from app.project_import_contract_support_persistence import (
    compute_project_import_contract_support_digest,
    reset_project_import_contract_support_state,
)
from app.routers import project_import_contract_support as contract_support_router


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "lane_415_envelope_export"


def _token(actor_role: str = "pm") -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _fixture_text(name: str) -> str:
    return json.dumps(_fixture(name), separators=(",", ":"), ensure_ascii=False)


def _canonical_json(value: dict) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _request_envelope() -> dict:
    return _fixture("request_envelope.json")


@pytest.fixture(autouse=True)
def reset_contract_support_state():
    reset_project_import_contract_support_state()
    yield
    reset_project_import_contract_support_state()


def test_contract_support_digest_matches_lane_415_frozen_request():
    request = _request_envelope()
    digest = compute_project_import_contract_support_digest(request["payload"])
    assert digest == request["idempotency_key"]


def test_contract_support_embedded_response_constants_match_lane_415_exports():
    for fixture_name, embedded_fixture in CONTRACT_SUPPORT_RESPONSE_FIXTURE_BY_FILENAME.items():
        assert _canonical_json(embedded_fixture) == _canonical_json(_fixture(fixture_name))


def test_contract_support_write_route_happy_path_matches_frozen_export(client):
    response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=_request_envelope(),
        headers=_token("pm"),
    )

    assert response.status_code == 201
    assert response.text == _fixture_text("response_success_first_write.json")


def test_contract_support_write_route_replay_matches_frozen_export(client):
    request = _request_envelope()
    first = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("operations"),
    )
    second = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("operations"),
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.text == _fixture_text("response_success_idempotent_hit.json")


def test_contract_support_write_route_conflict_matches_frozen_export(client):
    request = _request_envelope()
    first = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("pm"),
    )

    conflict_request = _request_envelope()
    conflict_request["payload"]["mutation_id"] = "mut-1d764f75-87a8-49bc-ac73-cd4dabaf95df"
    response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=conflict_request,
        headers=_token("pm"),
    )

    assert first.status_code == 201
    assert response.status_code == 409
    assert response.text == _fixture_text("response_conflict_duplicate_business_payload.json")


@pytest.mark.parametrize(
    ("force_failure", "fixture_name", "status_code"),
    [
        ("scope_detail_conflict", "response_rollback_scope_detail_conflict.json", 409),
        ("apparatus_financial_validation_failed", "response_rollback_apparatus_financial_validation_failed.json", 422),
        ("audit_write_unavailable", "response_rollback_audit_write_unavailable.json", 503),
        ("idempotency_write_unavailable", "response_rollback_idempotency_write_unavailable.json", 503),
    ],
)
def test_contract_support_force_failures_match_frozen_exports(client, monkeypatch, force_failure, fixture_name, status_code):
    monkeypatch.setenv("LANE_412_DRY_RUN_ENABLED", "1")
    request = _request_envelope()
    request["force_failure"] = force_failure

    response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("pm"),
    )

    assert response.status_code == status_code
    assert response.text == _fixture_text(fixture_name)


def test_contract_support_dry_run_and_force_failure_ignored_when_flag_disabled(client):
    request = _request_envelope()
    request["dry_run"] = True
    request["force_failure"] = "scope_detail_conflict"

    response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("pm"),
    )

    assert response.status_code == 201
    assert response.text == _fixture_text("response_success_first_write.json")


def test_contract_support_write_route_roles_and_auth(client):
    request = _request_envelope()

    pm_response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=request,
        headers=_token("pm"),
    )
    operations_response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=_request_envelope(),
        headers=_token("operations"),
    )
    task_lead_response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=_request_envelope(),
        headers=_token("task_lead"),
    )
    field_tech_response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=_request_envelope(),
        headers=_token("field_tech"),
    )
    no_auth_response = client.post(
        "/api/v1/mutations/project-import-contract-support",
        json=_request_envelope(),
    )

    assert pm_response.status_code == 201
    assert operations_response.status_code == 200
    assert task_lead_response.status_code == 403
    assert field_tech_response.status_code == 403
    assert no_auth_response.status_code == 401


def test_contract_support_readback_route_roles_and_baseline(client):
    query = {
        "project_id": "pm-import-project-miner-temp-power",
        "candidate_id": "pm-import-candidate-miner-temp-power",
        "source_fingerprint": "miner-temp-power-source-fingerprint-2026-05-20",
    }

    pm_response = client.get("/api/v1/reads/project-import-contract-support-status", params=query, headers=_token("pm"))
    operations_response = client.get(
        "/api/v1/reads/project-import-contract-support-status",
        params=query,
        headers=_token("operations"),
    )
    task_lead_response = client.get(
        "/api/v1/reads/project-import-contract-support-status",
        params=query,
        headers=_token("task_lead"),
    )
    field_tech_response = client.get(
        "/api/v1/reads/project-import-contract-support-status",
        params=query,
        headers=_token("field_tech"),
    )
    no_auth_response = client.get("/api/v1/reads/project-import-contract-support-status", params=query)

    assert pm_response.status_code == 200
    assert pm_response.text == _fixture_text("response_readback_missing.json")
    assert operations_response.status_code == 200
    assert operations_response.text == _fixture_text("response_readback_missing.json")
    assert task_lead_response.status_code == 403
    assert field_tech_response.status_code == 403
    assert no_auth_response.status_code == 401


def test_strict_auth_wrapper_rejects_missing_auth():
    with pytest.raises(Exception) as exc_info:
        asyncio.run(contract_support_router.get_strict_current_actor(None))

    assert exc_info.value.status_code == 401


def test_strict_auth_wrapper_rejects_invalid_auth():
    with pytest.raises(Exception) as exc_info:
        asyncio.run(contract_support_router.get_strict_current_actor("Token nope"))

    assert exc_info.value.status_code == 401


def test_strict_auth_wrapper_rejects_dev_actor_fallback(monkeypatch):
    async def _fake_get_current_actor(authorization=None):
        return Actor(actor_id="tech-001", actor_role="field_tech", project_scope=["proj-001"])

    monkeypatch.setattr(contract_support_router, "get_current_actor", _fake_get_current_actor)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(contract_support_router.get_strict_current_actor("Bearer valid"))

    assert exc_info.value.status_code == 401


def test_strict_auth_wrapper_uses_sentinel(monkeypatch):
    expected = Actor(actor_id="operations-001", actor_role="operations", project_scope=["proj-001"])

    async def _fake_get_current_actor(authorization=None):
        return expected

    def _fake_is_dev_fallback_actor(actor):
        assert actor == expected
        return True

    monkeypatch.setattr(contract_support_router, "get_current_actor", _fake_get_current_actor)
    monkeypatch.setattr(contract_support_router, "is_dev_fallback_actor", _fake_is_dev_fallback_actor)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(contract_support_router.get_strict_current_actor("Bearer valid"))

    assert exc_info.value.status_code == 401


def test_strict_auth_wrapper_returns_valid_actor(monkeypatch):
    expected = Actor(actor_id="operations-001", actor_role="operations", project_scope=["proj-001"])

    async def _fake_get_current_actor(authorization=None):
        return expected

    monkeypatch.setattr(contract_support_router, "get_current_actor", _fake_get_current_actor)

    actor = asyncio.run(contract_support_router.get_strict_current_actor("Bearer valid"))

    assert actor == expected
