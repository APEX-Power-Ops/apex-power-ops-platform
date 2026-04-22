"""Tests for the MCP transport exposed at /mcp."""

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app
from services.auth import AuthenticatedUser
import services.auth as auth
import services.mcp_server as mcp_server
from tests.test_control_plane import TEST_USER_ID, _FakeControlPlaneDb


def _reset_auth_caches():
    auth._get_jwks_client.cache_clear()
    auth._get_issuer.cache_clear()
    auth._get_audience.cache_clear()
    auth._get_oidc_userinfo_url.cache_clear()


def test_mcp_initialize_returns_capabilities_and_session_header(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0.0"},
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["Mcp-Session-Id"]
    payload = response.json()
    assert payload["result"]["protocolVersion"] == "2025-03-26"
    assert payload["result"]["capabilities"]["tools"]["listChanged"] is False
    assert payload["result"]["serverInfo"]["name"] == "apex-platform-governed-control-plane"


def test_mcp_get_sse_compatibility_stream_advertises_post_endpoint(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.get("/mcp", headers={"Accept": "text/event-stream"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: endpoint" in response.text
    assert "data: https://control-plane.example.com/mcp" in response.text


def test_mcp_root_payload_advertises_sse_compatibility(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.get("/mcp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["transport"]["supports_sse_get"] is True


def test_mcp_tools_list_exposes_security_schemes(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert "list_task_packets" in tool_names
    assert "queue_local_action" in tool_names

    queue_tool = next(tool for tool in tools if tool["name"] == "queue_local_action")
    assert queue_tool["securitySchemes"] == [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}]
    assert queue_tool["annotations"]["readOnlyHint"] is False


def test_mcp_tools_call_without_auth_triggers_oauth_metadata(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_task_packets", "arguments": {"limit": 5}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is True
    challenge = payload["result"]["_meta"]["mcp/www_authenticate"][0]
    assert "oauth-protected-resource" in challenge
    assert 'scope="openid profile email"' in challenge


def test_mcp_tools_call_fetch_task_packet_uses_existing_control_plane_logic(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    fake_db = _FakeControlPlaneDb()
    app.dependency_overrides[get_db] = lambda: fake_db
    monkeypatch.setattr(
        mcp_server,
        "get_authenticated_user_from_authorization",
        lambda request, authorization_header: AuthenticatedUser(
            user_id=TEST_USER_ID,
            email="neta-test-a@example.com",
            role="authenticated",
            claims={"sub": TEST_USER_ID},
        ),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/mcp",
            headers={"Authorization": "Bearer token-123"},
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "fetch_task_packet",
                    "arguments": {"task_id": "2026-03-29-chatgpt-remote-control-plane-backend-001"},
                },
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is False
    assert payload["result"]["structuredContent"]["task_id"] == "2026-03-29-chatgpt-remote-control-plane-backend-001"
    assert "Accepted after live control-plane proof" in payload["result"]["content"][0]["text"]


def test_mcp_tools_call_list_task_packets_wraps_array_results_for_structured_content(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    _reset_auth_caches()

    app.dependency_overrides[get_db] = lambda: _FakeControlPlaneDb()
    monkeypatch.setattr(
        mcp_server,
        "get_authenticated_user_from_authorization",
        lambda request, authorization_header: AuthenticatedUser(
            user_id=TEST_USER_ID,
            email="neta-test-a@example.com",
            role="authenticated",
            claims={"sub": TEST_USER_ID},
        ),
    )
    monkeypatch.setattr(
        mcp_server,
        "list_task_packets",
        lambda **kwargs: [
            {
                "task_id": "2026-03-29-chatgpt-remote-control-plane-backend-001",
                "title": "Implement first remote control-plane backend slice",
                "lane": "workspace-governance",
                "status": "completed",
                "risk_level": "high",
                "preferred_model_tier": "tier-a",
                "review_gate": "tier-a review before completion acceptance",
                "updated_at": "2026-03-29T12:00:00Z",
            }
        ],
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/mcp",
            headers={"Authorization": "Bearer token-123"},
            json={
                "jsonrpc": "2.0",
                "id": 41,
                "method": "tools/call",
                "params": {
                    "name": "list_task_packets",
                    "arguments": {"limit": 1},
                },
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is False
    assert payload["result"]["structuredContent"]["count"] == 1
    assert payload["result"]["structuredContent"]["items"][0]["task_id"] == "2026-03-29-chatgpt-remote-control-plane-backend-001"


def test_mcp_tools_call_accepts_operator_direct_token(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    monkeypatch.setenv("OPERATOR_BOOTSTRAP_TOKEN", "bootstrap-secret")
    monkeypatch.setenv("OPERATOR_TOKEN_SIGNING_SECRET", "operator-signing-secret-should-be-long")
    monkeypatch.setenv("OPERATOR_TOKEN_EMAIL", "operator@example.com")
    monkeypatch.setenv("OPERATOR_TOKEN_USER_ID", str(TEST_USER_ID))
    _reset_auth_caches()

    fake_db = _FakeControlPlaneDb()
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        client = TestClient(app)
        token_response = client.post(
            "/api/v1/auth/operator-token",
            json={"bootstrap_token": "bootstrap-secret"},
        )
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]

        response = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "fetch_task_packet",
                    "arguments": {"task_id": "2026-03-29-chatgpt-remote-control-plane-backend-001"},
                },
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is False
    assert payload["result"]["structuredContent"]["task_id"] == "2026-03-29-chatgpt-remote-control-plane-backend-001"