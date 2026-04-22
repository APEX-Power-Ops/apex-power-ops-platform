from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.check_dedicated_mcp_surfaces as check_script


def _configure_supabase_surface(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SUPABASE_MCP_PUBLIC_BASE_URL", "https://supabase-mcp.example.com")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/authorize")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_ISSUER", "https://auth.example.com/")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_AUDIENCE", "https://supabase-mcp.example.com")
    monkeypatch.setenv("SUPABASE_MCP_OAUTH_REDIRECT_URIS", "[\"https://chatgpt.com/callback\"]")
    monkeypatch.setenv("SUPABASE_ALLOWED_PROJECTS_JSON", "[{\"project_ref\":\"demo\"}]")
    monkeypatch.setenv("SUPABASE_MANAGEMENT_TOKEN", "mgmt-token")


def _configure_github_surface(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("GITHUB_MCP_PUBLIC_BASE_URL", "https://github-mcp.example.com")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/authorize")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_ISSUER", "https://auth.example.com/")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_AUDIENCE", "https://github-mcp.example.com")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_REDIRECT_URIS", "[\"https://chatgpt.com/callback\"]")
    monkeypatch.setenv("GITHUB_ALLOWED_REPOS_JSON", "[{\"owner\":\"octo\",\"repo\":\"demo\"}]")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----demo-----END PRIVATE KEY-----")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_IDS_JSON", "{\"octo/demo\":123}")


def test_main_passes_for_local_surfaces(monkeypatch, capsys):
    _configure_supabase_surface(monkeypatch)
    _configure_github_surface(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["check_dedicated_mcp_surfaces.py", "--require-ready"])

    exit_code = check_script.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "RESULT PASS" in output


def test_main_fails_when_github_app_env_missing(monkeypatch, capsys):
    _configure_github_surface(monkeypatch)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["check_dedicated_mcp_surfaces.py", "--surface", "github", "--require-ready"])

    exit_code = check_script.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "GITHUB_APP_PRIVATE_KEY" in output


def test_main_live_probe_passes(monkeypatch, capsys):
    _configure_supabase_surface(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_dedicated_mcp_surfaces.py",
            "--surface",
            "supabase",
            "--require-ready",
            "--supabase-base-url",
            "https://deploy.example.com",
        ],
    )

    responses = {
        (
            "https://deploy.example.com/supabase-mcp/.well-known/oauth-authorization-server"
        ): (200, {"issuer": "https://auth.example.com/"}),
        (
            "https://deploy.example.com/supabase-mcp/.well-known/oauth-protected-resource"
        ): (200, {"resource": "https://supabase-mcp.example.com"}),
        (
            "https://deploy.example.com/supabase-mcp"
        ): (200, {"oauth_discovery_url": "https://supabase-mcp.example.com/.well-known/oauth-authorization-server", "approved_tools": ["get_project_context"]}),
    }

    monkeypatch.setattr(check_script, "_fetch_json", lambda url: responses[url])

    exit_code = check_script.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "SUPABASE_LIVE_ROOT_STATUS 200" in output
    assert "RESULT PASS" in output