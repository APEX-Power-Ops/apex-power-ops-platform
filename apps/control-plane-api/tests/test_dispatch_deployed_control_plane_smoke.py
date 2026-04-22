"""Focused tests for the deployed control-plane smoke dispatch helper."""

import json
import sys
from unittest.mock import patch

from scripts import dispatch_deployed_control_plane_smoke as dispatch


def test_build_payload_defaults_do_not_require_apparatus_route():
    args = dispatch.build_parser().parse_args([
        "--base-url",
        "https://control.apexpowerops.com",
    ])

    payload = dispatch._build_payload(args)

    assert payload["event_type"] == "control-plane-deploy-complete"
    assert payload["client_payload"]["base_url"] == "https://control.apexpowerops.com"
    assert payload["client_payload"]["require_apparatus_study_route"] == "false"


def test_build_payload_can_require_apparatus_route_and_include_deploy_metadata():
    args = dispatch.build_parser().parse_args([
        "--base-url",
        "https://control.apexpowerops.com/",
        "--initial-wait-seconds",
        "90",
        "--environment",
        "production",
        "--deploy-id",
        "render-control-plane-20260421",
        "--require-apparatus-study-route",
    ])

    payload = dispatch._build_payload(args)

    assert payload["client_payload"] == {
        "base_url": "https://control.apexpowerops.com",
        "initial_wait_seconds": "90",
        "environment": "production",
        "require_apparatus_study_route": "true",
        "source": "dispatch_deployed_control_plane_smoke.py",
        "deploy_id": "render-control-plane-20260421",
    }


def test_build_payload_rejects_negative_initial_wait():
    args = dispatch.build_parser().parse_args([
        "--base-url",
        "https://control.apexpowerops.com",
        "--initial-wait-seconds",
        "-1",
    ])

    try:
        dispatch._build_payload(args)
    except RuntimeError as exc:
        assert str(exc) == "--initial-wait-seconds must be a non-negative integer"
    else:
        raise AssertionError("Expected _build_payload to reject negative wait seconds")


def test_resolve_token_reads_from_environment(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY_DISPATCH_TOKEN", "token-from-env")

    resolved = dispatch._resolve_token(None, "GITHUB_REPOSITORY_DISPATCH_TOKEN")

    assert resolved == "token-from-env"


def test_main_dry_run_prints_apparatus_route_requirement(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_REPOSITORY_DISPATCH_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_deployed_control_plane_smoke.py",
            "--base-url",
            "https://control.apexpowerops.com",
            "--initial-wait-seconds",
            "45",
            "--require-apparatus-study-route",
            "--dry-run",
        ],
    )

    exit_code = dispatch.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "RESULT DRY_RUN" in output
    assert "REQUIRE_APPARATUS_STUDY_ROUTE true" in output
    assert '"require_apparatus_study_route": "true"' in output


def test_main_posts_repository_dispatch_with_route_gate(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_REPOSITORY_DISPATCH_TOKEN", "token-from-env")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_deployed_control_plane_smoke.py",
            "--base-url",
            "https://control.apexpowerops.com",
            "--initial-wait-seconds",
            "120",
            "--deploy-id",
            "render-deploy-456",
            "--require-apparatus-study-route",
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

    with patch("scripts.dispatch_deployed_control_plane_smoke.request.urlopen", side_effect=_fake_urlopen):
        exit_code = dispatch.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "RESULT PASS" in output
    assert captured["url"] == "https://api.github.com/repos/jasonlswenson-sys/apex-power-ops-platform/dispatches"
    assert captured["timeout"] == 30
    assert captured["body"] == {
        "event_type": "control-plane-deploy-complete",
        "client_payload": {
            "base_url": "https://control.apexpowerops.com",
            "initial_wait_seconds": "120",
            "environment": "production",
            "require_apparatus_study_route": "true",
            "source": "dispatch_deployed_control_plane_smoke.py",
            "deploy_id": "render-deploy-456",
        },
    }
    authorization_header = captured["headers"].get("Authorization") or captured["headers"].get("authorization")
    assert authorization_header == "Bearer token-from-env"


def test_main_rejects_negative_initial_wait(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dispatch_deployed_control_plane_smoke.py",
            "--base-url",
            "https://control.apexpowerops.com",
            "--initial-wait-seconds",
            "-1",
            "--dry-run",
        ],
    )

    exit_code = dispatch.main()
    output = capsys.readouterr().out

    assert exit_code == 2
    assert "non-negative integer" in output