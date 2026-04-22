"""Tests for the repository_dispatch helper used by dedicated MCP surface readiness validation."""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.dispatch_dedicated_mcp_surface_check as dispatch_script


def test_build_payload_contains_expected_client_payload():
    args = dispatch_script.build_parser().parse_args(
        [
            "--supabase-base-url",
            "https://supabase-mcp.apexpowerops.com/",
            "--github-base-url",
            "https://github-mcp.apexpowerops.com/",
            "--initial-wait-seconds",
            "90",
            "--require-write-ready",
            "--deploy-id",
            "render-deploy-789",
        ]
    )

    payload = dispatch_script._build_payload(args)

    assert payload["event_type"] == "dedicated-mcp-surfaces-deploy-complete"
    assert payload["client_payload"]["supabase_base_url"] == "https://supabase-mcp.apexpowerops.com"
    assert payload["client_payload"]["github_base_url"] == "https://github-mcp.apexpowerops.com"
    assert payload["client_payload"]["initial_wait_seconds"] == "90"
    assert payload["client_payload"]["require_write_ready"] == "true"
    assert payload["client_payload"]["deploy_id"] == "render-deploy-789"


def test_main_dry_run_does_not_require_token(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY_DISPATCH_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_dedicated_mcp_surface_check.py",
            "--supabase-base-url",
            "https://supabase-mcp.apexpowerops.com",
            "--github-base-url",
            "https://github-mcp.apexpowerops.com",
            "--dry-run",
        ],
    )

    exit_code = dispatch_script.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "RESULT DRY_RUN" in output
    assert '"require_write_ready": "false"' in output


def test_main_posts_repository_dispatch(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY_DISPATCH_TOKEN", "token-from-env")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_dedicated_mcp_surface_check.py",
            "--initial-wait-seconds",
            "120",
            "--require-write-ready",
        ],
    )

    captured: dict[str, object] = {}

    class _Response:
        status = 204

        def read(self) -> bytes:
            return b""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(req.header_items())
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Response()

    with patch("scripts.dispatch_dedicated_mcp_surface_check.request.urlopen", side_effect=_fake_urlopen):
        exit_code = dispatch_script.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "RESULT PASS" in output
    assert captured["url"] == "https://api.github.com/repos/jasonlswenson-sys/apex-power-ops-platform/dispatches"
    assert captured["timeout"] == 30
    assert captured["body"] == {
        "event_type": "dedicated-mcp-surfaces-deploy-complete",
        "client_payload": {
            "supabase_base_url": "https://supabase-mcp.apexpowerops.com",
            "github_base_url": "https://github-mcp.apexpowerops.com",
            "initial_wait_seconds": "120",
            "environment": "production",
            "require_write_ready": "true",
            "source": "dispatch_dedicated_mcp_surface_check.py",
        },
    }


def test_main_rejects_negative_initial_wait(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_dedicated_mcp_surface_check.py",
            "--initial-wait-seconds",
            "-1",
            "--dry-run",
        ],
    )

    exit_code = dispatch_script.main()
    output = capsys.readouterr().out

    assert exit_code == 2
    assert "non-negative integer" in output