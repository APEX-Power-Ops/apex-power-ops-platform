"""Tests for the dedicated GitHub MCP transport exposed at /github-mcp."""

from __future__ import annotations

import os
import sys
from uuid import NAMESPACE_URL, uuid5

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app
from services.auth import AuthenticatedUser
import services.auth as auth
import services.github_mcp_server as github_mcp_server


def _reset_auth_caches():
    auth._get_jwks_client.cache_clear()
    auth._get_jwks_client_for_url.cache_clear()
    auth._get_issuer.cache_clear()
    auth._get_audience.cache_clear()
    auth._get_oidc_userinfo_url.cache_clear()


def _configure_github_mcp_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("GITHUB_MCP_PUBLIC_BASE_URL", "https://github-mcp.example.com")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/authorize")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    monkeypatch.setenv(
        "GITHUB_ALLOWED_REPOS_JSON",
        '[{"owner":"jasonlswenson-sys","repo":"apex-power-ops-platform","default_branch":"main","installation_id":12345,"enabled_tool_families":["issues","pull_requests","actions","writes"],"allowed_workflow_dispatches":["deployed-control-plane-smoke.yml"]}]',
    )
    _reset_auth_caches()


def _authenticated_user(scope: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid5(NAMESPACE_URL, "github-mcp-user"),
        email="github-test@example.com",
        role="authenticated",
        claims={"sub": "github-mcp-user", "scope": scope},
    )


def test_github_mcp_initialize_returns_capabilities_and_session_header(monkeypatch):
    _configure_github_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/github-mcp",
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
    assert payload["result"]["serverInfo"]["name"] == "apex-platform-github-repository-operations"


def test_github_mcp_tools_list_exposes_chatgpt_compatible_oidc_scopes(monkeypatch):
    _configure_github_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/github-mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert "fetch_pull_request_status_checks" in tool_names
    assert "add_issue_comment" in tool_names

    read_tool = next(tool for tool in tools if tool["name"] == "fetch_pull_request_status_checks")
    write_tool = next(tool for tool in tools if tool["name"] == "add_issue_comment")
    expected_scheme = [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}]
    assert read_tool["securitySchemes"] == expected_scheme
    assert write_tool["securitySchemes"] == expected_scheme


def test_github_mcp_tools_call_without_auth_triggers_surface_specific_metadata(monkeypatch):
    _configure_github_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/github-mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_allowed_repositories", "arguments": {}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is True
    challenge = payload["result"]["_meta"]["mcp/www_authenticate"][0]
    assert "github-mcp.example.com/.well-known/oauth-protected-resource" in challenge


def test_github_mcp_list_allowed_repositories_accepts_chatgpt_oidc_grant(monkeypatch):
    _configure_github_mcp_env(monkeypatch)
    app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(
        github_mcp_server,
        "get_authenticated_user_from_authorization_for_surface",
        lambda request, authorization_header, surface_env: _authenticated_user("openid profile email"),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/github-mcp",
            headers={"Authorization": "Bearer token-123"},
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "list_allowed_repositories", "arguments": {}},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is False
    assert payload["result"]["structuredContent"]["count"] == 1
    assert payload["result"]["structuredContent"]["items"][0]["repo"] == "apex-power-ops-platform"


def test_github_mcp_status_checks_aggregate_reviews_and_ci(monkeypatch):
    _configure_github_mcp_env(monkeypatch)
    app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(
        github_mcp_server,
        "get_authenticated_user_from_authorization_for_surface",
        lambda request, authorization_header, surface_env: _authenticated_user("openid profile email"),
    )
    monkeypatch.setattr(github_mcp_server, "_get_installation_access_token", lambda binding: "token-123")

    def fake_github_json(method, path, **kwargs):
        if path.endswith("/pulls/12"):
            return {
                "number": 12,
                "title": "Add GitHub MCP surface",
                "state": "open",
                "draft": False,
                "mergeable": True,
                "mergeable_state": "clean",
                "head": {"sha": "abc123", "ref": "feature/github-mcp"},
                "base": {"sha": "def456", "ref": "main"},
                "html_url": "https://github.com/jasonlswenson-sys/apex-power-ops-platform/pull/12",
            }
        if path.endswith("/commits/abc123/check-runs"):
            return {
                "check_runs": [
                    {"name": "pytest", "status": "completed", "conclusion": "success", "html_url": "https://example.com/pytest"}
                ]
            }
        if path.endswith("/commits/abc123/status"):
            return {"state": "success", "statuses": [{"context": "render", "state": "success"}]}
        if path.endswith("/pulls/12/reviews"):
            return [{"user": {"login": "reviewer-a"}, "state": "APPROVED", "submitted_at": "2026-04-07T12:00:00Z"}]
        if path.endswith("/pulls/12/requested_reviewers"):
            return {"users": [], "teams": []}
        raise AssertionError(f"Unexpected GitHub API path: {path}")

    monkeypatch.setattr(github_mcp_server, "_github_api_json", fake_github_json)

    try:
        client = TestClient(app)
        response = client.post(
            "/github-mcp",
            headers={"Authorization": "Bearer token-123"},
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "fetch_pull_request_status_checks",
                    "arguments": {"owner": "jasonlswenson-sys", "repo": "apex-power-ops-platform", "pull_number": 12},
                },
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()["result"]["structuredContent"]
    assert payload["merge_readiness"]["ready_to_merge"] is True
    assert payload["review_summary"]["approval_count"] == 1
    assert payload["check_runs"]["total"] == 1


def test_add_issue_comment_requires_confirmation(monkeypatch):
    _configure_github_mcp_env(monkeypatch)
    try:
        github_mcp_server._call_add_issue_comment(
            {"owner": "jasonlswenson-sys", "repo": "apex-power-ops-platform", "issue_number": 7, "body": "Test", "confirmed": False},
            db=None,
            current_user=_authenticated_user("github.write"),
        )
    except github_mcp_server.McpToolExecutionError as exc:
        assert "confirmed=true" in exc.message
    else:
        raise AssertionError("Expected confirmation gate to reject unconfirmed issue comment")


def test_dispatch_workflow_rejects_non_allowlisted_workflow(monkeypatch):
    _configure_github_mcp_env(monkeypatch)
    try:
        github_mcp_server._call_dispatch_workflow(
            {
                "owner": "jasonlswenson-sys",
                "repo": "apex-power-ops-platform",
                "workflow_id": "unapproved.yml",
                "ref": "main",
                "confirmed": True,
            },
            db=None,
            current_user=_authenticated_user("github.actions"),
        )
    except github_mcp_server.McpToolExecutionError as exc:
        assert "not allowlisted" in exc.message
    else:
        raise AssertionError("Expected allowlist gate to reject workflow dispatch")


def test_add_issue_comment_records_audit(monkeypatch):
    _configure_github_mcp_env(monkeypatch)
    monkeypatch.setattr(github_mcp_server, "_get_installation_access_token", lambda binding: "token-123")
    monkeypatch.setattr(
        github_mcp_server,
        "_github_api_json",
        lambda method, path, **kwargs: {"id": 99, "html_url": "https://github.com/example/comment/99"},
    )
    recorded = {}

    def fake_record_write_audit(db, **kwargs):
        recorded.update(kwargs)
        return "audit-123"

    monkeypatch.setattr(github_mcp_server, "_record_write_audit", fake_record_write_audit)

    result = github_mcp_server._call_add_issue_comment(
        {
            "owner": "jasonlswenson-sys",
            "repo": "apex-power-ops-platform",
            "issue_number": 7,
            "body": "Validation comment",
            "confirmed": True,
        },
        db=object(),
        current_user=_authenticated_user("github.write"),
    )

    assert result["audit_id"] == "audit-123"
    assert recorded["tool_name"] == "add_issue_comment"
    assert recorded["target_identifier"] == "7"