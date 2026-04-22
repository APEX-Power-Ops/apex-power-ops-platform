"""Tests for the dedicated Supabase MCP transport exposed at /supabase-mcp."""

from __future__ import annotations

import json
import os
import sys
from urllib.parse import parse_qs, unquote, urlparse

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app
from services.auth import AuthenticatedUser
import services.auth as auth
import services.supabase_mcp_server as supabase_mcp_server


def _reset_auth_caches():
    auth._get_jwks_client.cache_clear()
    auth._get_jwks_client_for_url.cache_clear()
    auth._get_issuer.cache_clear()
    auth._get_audience.cache_clear()
    auth._get_oidc_userinfo_url.cache_clear()


def _configure_supabase_mcp_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SUPABASE_MCP_PUBLIC_BASE_URL", "https://supabase-mcp.example.com")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/authorize")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_REDIRECT_URIS", "https://chatgpt.com/connector/oauth/example-callback")
    monkeypatch.setenv(
        "SUPABASE_ALLOWED_PROJECTS_JSON",
        '[{"project_id":"fxoyniqnrlkxfligbxmg","project_ref":"fxoyniqnrlkxfligbxmg","environment_label":"development","allowed_write_modes":["branches","migrations"],"enabled_tool_families":["schema","readonly_sql"]}]',
    )
    monkeypatch.setenv("SUPABASE_MANAGEMENT_TOKEN", "sbp_test_token")
    _reset_auth_caches()


class _FakeHTTPResponse:
    def __init__(self, payload, *, status: int = 200):
        self._payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeAuditDb:
    def __init__(self):
        self.executed = []
        self.committed = False

    def execute(self, statement, params=None):
        self.executed.append((statement, params or {}))

    def commit(self):
        self.committed = True


class _FakeCursor:
    def __init__(self):
        self.executed_sql = []

    def execute(self, sql):
        self.executed_sql.append(sql)


class _FakeRawConnection:
    def __init__(self):
        self.cursor_obj = _FakeCursor()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class _FakeBind:
    def __init__(self, raw_connection):
        self._raw_connection = raw_connection

    def raw_connection(self):
        return self._raw_connection


class _FakeExecutionDb(_FakeAuditDb):
    def __init__(self):
        super().__init__()
        self.raw_connection_obj = _FakeRawConnection()

    def get_bind(self):
        return _FakeBind(self.raw_connection_obj)


def _fake_user(scopes: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=auth.uuid5(auth.NAMESPACE_URL, "supabase-mcp-user"),
        email="supabase-test@example.com",
        role="authenticated",
        claims={"sub": "supabase-mcp-user", "scope": scopes},
    )


def test_supabase_mcp_initialize_returns_capabilities_and_session_header(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/supabase-mcp",
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
    assert payload["result"]["serverInfo"]["name"] == "apex-platform-supabase-operations"


def test_supabase_mcp_tools_list_exposes_chatgpt_compatible_oidc_scopes(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/supabase-mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    assert response.status_code == 200
    tools = response.json()["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert "run_readonly_sql" in tool_names
    assert "create_database_branch" in tool_names

    readonly_tool = next(tool for tool in tools if tool["name"] == "run_readonly_sql")
    write_tool = next(tool for tool in tools if tool["name"] == "create_database_branch")
    admin_tool = next(tool for tool in tools if tool["name"] == "get_publishable_keys")
    expected_scheme = [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}]
    assert readonly_tool["securitySchemes"] == expected_scheme
    assert write_tool["securitySchemes"] == expected_scheme
    assert admin_tool["securitySchemes"] == expected_scheme


def test_supabase_mcp_tools_call_without_auth_triggers_surface_specific_metadata(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/supabase-mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_project_context", "arguments": {}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is True
    challenge = payload["result"]["_meta"]["mcp/www_authenticate"][0]
    assert "supabase-mcp.example.com/.well-known/oauth-protected-resource" in challenge


def test_supabase_mcp_get_project_context_accepts_chatgpt_oidc_grant(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)
    app.dependency_overrides[get_db] = lambda: None
    monkeypatch.setattr(
        supabase_mcp_server,
        "get_authenticated_user_from_authorization_for_surface",
        lambda request, authorization_header, surface_env: AuthenticatedUser(
            user_id=auth.uuid5(auth.NAMESPACE_URL, "supabase-mcp-user"),
            email="supabase-test@example.com",
            role="authenticated",
            claims={"sub": "supabase-mcp-user", "scope": "openid profile email"},
        ),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/supabase-mcp",
            headers={"Authorization": "Bearer token-123"},
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "get_project_context", "arguments": {}},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["isError"] is False
    assert payload["result"]["structuredContent"]["project_ref"] == "fxoyniqnrlkxfligbxmg"


def test_run_readonly_sql_rejects_write_statements():
    try:
        supabase_mcp_server._assert_readonly_sql("update public.mcp_task_packets set status = 'completed'")
    except supabase_mcp_server.McpToolExecutionError as exc:
        assert "read-only" in exc.message.lower()
    else:
        raise AssertionError("Expected write SQL to be rejected")


def test_apply_repo_migration_requires_confirmation(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)
    try:
        supabase_mcp_server._call_apply_repo_migration(
            {"migration_path": "supabase/migrations/20260328_000007_add_control_plane_tables.sql", "confirmed": False},
            db=None,
            current_user=AuthenticatedUser(
                user_id=auth.uuid5(auth.NAMESPACE_URL, "supabase-mcp-user"),
                email="supabase-test@example.com",
                role="authenticated",
                claims={"sub": "supabase-mcp-user", "scope": "supabase.write"},
            ),
        )
    except supabase_mcp_server.McpToolExecutionError as exc:
        assert "confirmed=true" in exc.message
    else:
        raise AssertionError("Expected confirmation gate to reject unconfirmed migration apply")


def test_apply_repo_migration_executes_sql_and_records_audit(monkeypatch, tmp_path):
    _configure_supabase_mcp_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_ENABLE_MIGRATION_APPLY", "true")
    migration_file = tmp_path / "20260407_test.sql"
    migration_file.write_text("create table test_table(id integer);\n", encoding="utf-8")
    execution_db = _FakeExecutionDb()

    monkeypatch.setattr(supabase_mcp_server, "_resolve_allowlisted_migration", lambda _: migration_file)

    result = supabase_mcp_server._call_apply_repo_migration(
        {"migration_path": "supabase/migrations/20260407_test.sql", "confirmed": True},
        db=execution_db,
        current_user=_fake_user("supabase.write"),
    )

    assert result["status"] == "applied"
    assert result["audit_id"].startswith("audit-")
    assert result["execution_mode"] == "database_session"
    assert execution_db.raw_connection_obj.committed is True
    assert execution_db.raw_connection_obj.closed is True
    assert execution_db.raw_connection_obj.cursor_obj.executed_sql == ["create table test_table(id integer);\n"]
    assert execution_db.executed


def test_deploy_edge_function_from_repo_invokes_cli_and_records_audit(monkeypatch, tmp_path):
    _configure_supabase_mcp_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY", "true")
    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "sb_access_token")
    monkeypatch.setenv(
        "SUPABASE_ALLOWED_PROJECTS_JSON",
        '[{"project_id":"fxoyniqnrlkxfligbxmg","project_ref":"fxoyniqnrlkxfligbxmg","environment_label":"development","allowed_write_modes":["branches","migrations","edge_functions"],"enabled_tool_families":["schema","readonly_sql"]}]',
    )

    project_dir = tmp_path / "supabase-project"
    function_root = project_dir / "supabase" / "functions"
    function_dir = function_root / "hello-world"
    function_dir.mkdir(parents=True)
    (function_dir / "index.ts").write_text("export default async () => new Response('ok');\n", encoding="utf-8")

    monkeypatch.setenv("SUPABASE_ALLOWED_FUNCTION_ROOTS", str(function_root))
    monkeypatch.setenv("SUPABASE_CLI_PROJECT_DIR", str(project_dir))
    monkeypatch.setattr(supabase_mcp_server.shutil, "which", lambda name: f"/mock/bin/{name}")

    captured = {}

    def fake_run(command, cwd, env, capture_output, text, timeout, check):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["token"] = env["SUPABASE_ACCESS_TOKEN"]
        captured["timeout"] = timeout
        return type("Completed", (), {"returncode": 0, "stdout": "Deployed hello-world", "stderr": ""})()

    monkeypatch.setattr(supabase_mcp_server.subprocess, "run", fake_run)
    audit_db = _FakeAuditDb()

    result = supabase_mcp_server._call_deploy_edge_function_from_repo(
        {"function_name": "hello-world", "confirmed": True},
        db=audit_db,
        current_user=_fake_user("supabase.write"),
    )

    assert result["status"] == "deployed"
    assert result["function_name"] == "hello-world"
    assert result["audit_id"].startswith("audit-")
    assert result["command"] == ["functions", "deploy", "hello-world", "--project-ref", "fxoyniqnrlkxfligbxmg"]
    assert result["stdout"] == "Deployed hello-world"
    assert captured["cwd"] == str(project_dir)
    assert captured["token"] == "sb_access_token"
    assert audit_db.executed


def test_get_advisory_notices_combines_security_and_performance(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    def fake_urlopen(request, timeout=30):
        if request.full_url.endswith("/advisors/security"):
            return _FakeHTTPResponse({
                "lints": [{
                    "cache_key": "security-1",
                    "title": "RLS missing",
                    "level": "ERROR",
                    "categories": ["SECURITY"],
                    "description": "rls disabled",
                    "remediation": "enable rls",
                    "detail": "public table exposed",
                }]
            })
        if request.full_url.endswith("/advisors/performance"):
            return _FakeHTTPResponse({
                "lints": [{
                    "cache_key": "performance-1",
                    "title": "Missing index",
                    "level": "WARN",
                    "categories": ["PERFORMANCE"],
                    "description": "index missing",
                    "remediation": "add index",
                    "detail": "query slow",
                }]
            })
        raise AssertionError(request.full_url)

    monkeypatch.setattr(supabase_mcp_server, "urlopen", fake_urlopen)

    result = supabase_mcp_server._call_get_advisory_notices({}, db=None, current_user=_fake_user("supabase.read"))

    assert result["count"] == 2
    assert {item["type"] for item in result["items"]} == {"security", "performance"}


def test_get_service_logs_queries_expected_log_source(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    def fake_urlopen(request, timeout=30):
        parsed = urlparse(request.full_url)
        params = parse_qs(parsed.query)
        sql = unquote(params["sql"][0])
        assert "from postgres_logs" in sql
        return _FakeHTTPResponse({
            "result": [{"timestamp": "2026-04-07T12:00:00Z", "id": "evt-1", "event_message": "statement logged", "identifier": "postgres"}],
            "error": None,
        })

    monkeypatch.setattr(supabase_mcp_server, "urlopen", fake_urlopen)

    result = supabase_mcp_server._call_get_service_logs(
        {"service": "postgres", "hours": 2, "limit": 10},
        db=None,
        current_user=_fake_user("supabase.read"),
    )

    assert result["service"] == "postgres"
    assert result["log_source"] == "postgres_logs"
    assert result["count"] == 1


def test_list_database_branches_returns_normalized_items(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    monkeypatch.setattr(
        supabase_mcp_server,
        "urlopen",
        lambda request, timeout=30: _FakeHTTPResponse([
            {
                "id": "branch-1",
                "name": "dev-branch",
                "project_ref": "fxoyniqnrlkxfligbxmg",
                "parent_project_ref": "fxoyniqnrlkxfligbxmg",
                "status": "ACTIVE",
                "persistent": False,
                "is_default": False,
                "with_data": False,
            }
        ]),
    )

    result = supabase_mcp_server._call_list_database_branches({}, db=None, current_user=_fake_user("supabase.read"))

    assert result["count"] == 1
    assert result["items"][0]["branch_name"] == "dev-branch"


def test_create_database_branch_records_audit(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)
    audit_db = _FakeAuditDb()

    monkeypatch.setattr(
        supabase_mcp_server,
        "urlopen",
        lambda request, timeout=30: _FakeHTTPResponse(
            {
                "id": "branch-123",
                "name": "mcp-validation-001",
                "project_ref": "fxoyniqnrlkxfligbxmg",
                "parent_project_ref": "fxoyniqnrlkxfligbxmg",
                "status": "CREATING_PROJECT",
                "persistent": False,
                "is_default": False,
                "with_data": False,
            }
        ),
    )

    result = supabase_mcp_server._call_create_database_branch(
        {"branch_name": "mcp-validation-001", "confirmed": True},
        db=audit_db,
        current_user=_fake_user("supabase.write"),
    )

    assert result["branch_id"] == "branch-123"
    assert result["audit_id"].startswith("audit-")
    assert audit_db.committed is True
    assert audit_db.executed


def test_get_publishable_keys_filters_out_secret_keys(monkeypatch):
    _configure_supabase_mcp_env(monkeypatch)

    def fake_urlopen(request, timeout=30):
        if request.full_url.endswith("/api-keys"):
            return _FakeHTTPResponse([
                {"id": "key-1", "type": "publishable", "name": "publishable", "api_key": "sb_publishable_1234567890"},
                {"id": "key-2", "type": "legacy", "name": "anon", "api_key": "sb_anon_1234567890"},
                {"id": "key-3", "type": "secret", "name": "service_role", "api_key": "sb_secret_1234567890"},
            ])
        if request.full_url.endswith("/api-keys/legacy"):
            return _FakeHTTPResponse({"enabled": True})
        raise AssertionError(request.full_url)

    monkeypatch.setattr(supabase_mcp_server, "urlopen", fake_urlopen)

    result = supabase_mcp_server._call_get_publishable_keys({}, db=None, current_user=_fake_user("supabase.admin"))

    assert result["count"] == 2
    assert all(item["key_type"] != "secret" for item in result["items"])