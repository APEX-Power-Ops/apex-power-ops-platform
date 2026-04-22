"""Focused tests for the deployed control-plane smoke gate helpers."""

from scripts import smoke_deployed_control_plane as smoke


def test_validate_apparatus_route_accepts_route_level_not_found_when_openapi_has_path():
    failures = smoke._validate_apparatus_study_route(
        openapi_status=200,
        openapi_payload={"paths": {smoke.APPARATUS_STUDY_ROUTE_PATH: {"get": {}}}},
        route_status=404,
        route_payload={"detail": "Apparatus 00000000-0000-0000-0000-000000000000 not found"},
    )

    assert failures == []


def test_validate_apparatus_route_reports_missing_openapi_and_framework_404():
    failures = smoke._validate_apparatus_study_route(
        openapi_status=200,
        openapi_payload={"paths": {}},
        route_status=404,
        route_payload={"detail": "Not Found"},
    )

    assert failures == [
        "deployed OpenAPI does not advertise the apparatus study-resource route",
        "deployed apparatus study-resource route returned framework 404 Not Found",
    ]


def test_validate_apparatus_route_reports_unexpected_status():
    failures = smoke._validate_apparatus_study_route(
        openapi_status=200,
        openapi_payload={"paths": {smoke.APPARATUS_STUDY_ROUTE_PATH: {"get": {}}}},
        route_status=401,
        route_payload={"detail": "Unauthorized"},
    )

    assert failures == ["apparatus study-resource route returned unexpected status 401"]


def test_validate_apparatus_route_requires_openapi_document():
    failures = smoke._validate_apparatus_study_route(
        openapi_status=503,
        openapi_payload={"detail": "unavailable"},
        route_status=503,
        route_payload={"detail": "migration-gated"},
    )

    assert failures == ["OpenAPI document did not return HTTP 200 for apparatus route validation"]


def test_validate_surface_contract_requires_public_discovery_and_mcp_for_public_hosts():
    failures = smoke._validate_surface_contract(
        local_runtime=False,
        discovery_status=500,
        mcp_status=503,
    )

    assert failures == [
        "OAuth discovery endpoint did not return HTTP 200",
        "MCP root endpoint did not return HTTP 200",
    ]


def test_validate_surface_contract_skips_public_discovery_and_mcp_for_local_runtime():
    failures = smoke._validate_surface_contract(
        local_runtime=True,
        discovery_status=500,
        mcp_status=503,
    )

    assert failures == []


def test_validate_control_plane_auth_contract_requires_401_and_bearer_for_public_hosts():
    failures = smoke._validate_control_plane_auth_contract(
        local_runtime=False,
        unauth_status=500,
        unauth_headers={},
    )

    assert failures == [
        "unauthenticated task-packets route did not return HTTP 401",
        "unauthenticated task-packets route did not advertise WWW-Authenticate: Bearer",
    ]


def test_validate_control_plane_auth_contract_skips_checks_for_local_runtime():
    failures = smoke._validate_control_plane_auth_contract(
        local_runtime=True,
        unauth_status=500,
        unauth_headers={},
    )

    assert failures == []
