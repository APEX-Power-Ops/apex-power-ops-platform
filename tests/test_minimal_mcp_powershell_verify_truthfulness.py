from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
STATE_FILE = STATE_DIR / "minimal-mcp-trio.json"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")


class _FakeMcpHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")
        server_name = self.server.service_name

        if method == "initialize":
            result: dict[str, object] = {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": f"fake-{server_name}", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": [{"name": name} for name in self.server.tool_names]}
        elif method == "tools/call":
            result = self.server.handle_tool_call(payload.get("params", {}))
        else:
            result = {"isError": True, "content": [{"text": f"unexpected method {method}"}]}

        body = json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _artifact_path(packet_id: str) -> Path:
    return MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"


def _read_env_urls() -> tuple[str, str, str]:
    env_values: dict[str, str] = {}
    for line in ENV_DEV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        assert line == stripped
        key, value = line.split("=", 1)
        assert key == key.strip()
        assert value == value.strip()
        env_values[key] = value
    return (
        env_values["APEX_FS_MCP_URL"],
        env_values["APEX_DB_MCP_URL"],
        env_values["APEX_JOBS_MCP_URL"],
    )


def _expected_verify_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)

    return shlex.join(argv)


def _expected_jobs_promote_guard_check(packet_id: str) -> dict[str, object]:
    return {
        "status": "pass",
        "packet_id": f"{packet_id}-promote-guard-<generated>",
        "detail": "no successful env=host run is on record for that packet_id",
    }


def _normalized_promote_guard_payload(payload: dict[str, object], packet_id: str) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    normalized["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"
    return normalized


def _expected_verify_pass_payload(
    fs_url: str,
    db_url: str,
    jobs_url: str,
    *,
    packet_id: str,
    output_path: Path,
    profile: str = "baseline",
    command_profile: str | None = None,
    command_endpoints: tuple[str, str, str] | None = None,
) -> dict[str, object]:
    command = [
        sys.executable,
        "tools/ai/verify_minimal_mcp_trio.py",
        "--packet-id",
        packet_id,
        "--output",
        str(output_path),
    ]
    if command_endpoints is not None:
        command.extend(
            [
                "--fs-url",
                command_endpoints[0],
                "--db-url",
                command_endpoints[1],
                "--jobs-url",
                command_endpoints[2],
            ]
        )
    if command_profile is not None:
        command.extend(["--profile", command_profile])
    return {
        "packet_id": packet_id,
        "profile": profile,
        "command": _expected_verify_command(command),
        "endpoints": {"fs": fs_url, "db": db_url, "jobs": jobs_url},
        "checks": {
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}} ,
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run", "list_runs"]},
            "jobs_promote_guard": _expected_jobs_promote_guard_check(packet_id),
            "jobs_start_run": {"status": "pass", "run": {"run_id": "run-123", "packet_id": packet_id}},
            "jobs_end_run": {"status": "pass", "run": {"run_id": "run-123", "status": "success"}},
            "jobs_list_runs": {
                "status": "pass",
                "result": {
                    "runs": [{
                        "run_id": "run-123",
                        "env": "sandbox",
                        "service": "ai-workflow",
                        "packet_id": packet_id,
                        "status": "success",
                    }],
                },
            },
        },
        "result": "PASS",
    }


def _expected_verify_blocked_output_payload(
    fs_url: str,
    db_url: str,
    jobs_url: str,
    *,
    packet_id: str,
    output_path: Path,
) -> dict[str, object]:
    expected = _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=packet_id,
        output_path=output_path,
    )
    expected["result"] = "FAIL"
    return expected


@pytest.fixture(autouse=True)
def _clean_state_file() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    yield
    if STATE_FILE.exists():
        STATE_FILE.unlink()


@pytest.fixture
def fake_trio():
    servers: list[ThreadingHTTPServer] = []
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start() -> None:
        def fs_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            if tool_name == "read_text_file":
                return {"structuredContent": {"content": README_PREVIEW}}
            return {"isError": True, "content": [{"text": f"unexpected fs tool {tool_name}"}]}

        def db_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            if tool_name == "query":
                return {"structuredContent": {"rowCount": 1, "rows": [{"ok": 1}]}}
            return {"isError": True, "content": [{"text": f"unexpected db tool {tool_name}"}]}

        def jobs_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "promote_packet":
                return {
                    "isError": True,
                    "content": [{"text": "no successful env=host run is on record for that packet_id"}],
                }
            if tool_name == "start_run":
                return {"structuredContent": {"run_id": "run-123", "packet_id": arguments.get("packet_id")}}
            if tool_name == "end_run":
                return {"structuredContent": {"run_id": arguments.get("run_id"), "status": arguments.get("status")}}
            if tool_name == "list_runs":
                return {"structuredContent": {"runs": [{
                    "run_id": "run-123",
                    "env": "sandbox",
                    "service": "ai-workflow",
                    "packet_id": arguments.get("packet_id"),
                    "status": "success",
                }]}}
            return {"isError": True, "content": [{"text": f"unexpected jobs tool {tool_name}"}]}

        for service_name, tool_names, handler in (
            ("fs", ["read_text_file"], fs_handler),
            ("db", ["query"], db_handler),
            ("jobs", ["promote_packet", "start_run", "end_run", "list_runs"], jobs_handler),
        ):
            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
            server.service_name = service_name
            server.tool_names = tool_names
            server.handle_tool_call = handler
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            servers.append(server)

        fs_url, db_url, jobs_url = tuple(f"http://127.0.0.1:{server.server_address[1]}/mcp" for server in servers)
        env_lines = []
        if original_env_dev is not None:
            env_lines.append(original_env_dev.rstrip("\n"))
        env_lines.extend(
            [
                f"APEX_FS_MCP_URL={fs_url}",
                f"APEX_DB_MCP_URL={db_url}",
                f"APEX_JOBS_MCP_URL={jobs_url}",
            ]
        )
        ENV_DEV_FILE.write_text("\n".join(line for line in env_lines if line) + "\n", encoding="utf-8")

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()

    if original_env_dev is None:
        if ENV_DEV_FILE.exists():
            ENV_DEV_FILE.unlink()
    else:
        ENV_DEV_FILE.write_text(original_env_dev, encoding="utf-8")


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_verify_uses_state_packet_id_when_not_provided(fake_trio) -> None:
    state_packet_id = "state-minimal-mcp-verify-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    STATE_FILE.write_text(json.dumps({"packet_id": state_packet_id}, indent=2) + "\n", encoding="utf-8")
    output_path = _artifact_path(state_packet_id)

    payload = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-minimal-mcp-trio.ps1",
        "-Action",
        "verify",
    ])

    assert _normalized_promote_guard_payload(payload, state_packet_id) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=state_packet_id,
        output_path=output_path,
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload

    output_path.unlink()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_verify_prefers_explicit_packet_id_over_state(fake_trio) -> None:
    state_packet_id = "state-packet-should-not-win"
    explicit_packet_id = "explicit-minimal-mcp-verify-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    STATE_FILE.write_text(json.dumps({"packet_id": state_packet_id}, indent=2) + "\n", encoding="utf-8")
    output_path = _artifact_path(explicit_packet_id)

    payload = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-minimal-mcp-trio.ps1",
        "-Action",
        "verify",
        "-PacketId",
        explicit_packet_id,
    ])

    assert _normalized_promote_guard_payload(payload, explicit_packet_id) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=explicit_packet_id,
        output_path=output_path,
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert not _artifact_path(state_packet_id).exists()

    output_path.unlink()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_verify_preserves_fail_json_when_verify_artifact_path_is_blocked(fake_trio) -> None:
    packet_id = "powershell-minimal-mcp-verify-blocked-artifact-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()

    output_path = _artifact_path(packet_id)
    output_path.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            "tools/ai/run-minimal-mcp-trio.ps1",
            "-Action",
            "verify",
            "-PacketId",
            packet_id,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    payload_without_error = {key: value for key, value in payload.items() if key != "error"}
    assert _normalized_promote_guard_payload(payload_without_error, packet_id) == _expected_verify_blocked_output_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=packet_id,
        output_path=output_path,
    )
    error_text = str(payload["error"]).lower()
    normalized_error_text = error_text.replace("\\\\", "\\")
    assert str(output_path).lower() in normalized_error_text
    assert output_path.name.lower() in normalized_error_text or "already exists" in normalized_error_text
    assert re.search(r"directory|exists|permission denied", error_text)
    assert result.stderr == ""

    output_path.rmdir()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_verify_prefers_state_endpoints_over_inherited_env_urls(fake_trio) -> None:
    packet_id = "powershell-minimal-mcp-verify-state-endpoints-win"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    output_path = _artifact_path(packet_id)

    ENV_DEV_FILE.write_text(
        "\n".join(
            [
                "APEX_FS_MCP_URL=http://127.0.0.1:1/mcp",
                "APEX_DB_MCP_URL=http://127.0.0.1:2/mcp",
                "APEX_JOBS_MCP_URL=http://127.0.0.1:3/mcp",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    STATE_FILE.write_text(
        json.dumps(
            {
                "packet_id": packet_id,
                "endpoints": {"fs": fs_url, "db": db_url, "jobs": jobs_url},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-minimal-mcp-trio.ps1",
        "-Action",
        "verify",
    ])

    assert _normalized_promote_guard_payload(payload, packet_id) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=packet_id,
        output_path=output_path,
        command_endpoints=(fs_url, db_url, jobs_url),
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload

    output_path.unlink()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_verify_routes_named_validation_profile(fake_trio) -> None:
    packet_id = "powershell-minimal-mcp-verify-strict-db-query"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    STATE_FILE.write_text(json.dumps({"packet_id": packet_id}, indent=2) + "\n", encoding="utf-8")
    output_path = _artifact_path(packet_id)

    payload = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-minimal-mcp-trio.ps1",
        "-Action",
        "verify",
        "-PacketId",
        packet_id,
        "-ValidationProfile",
        "strict-db-query",
    ])

    assert _normalized_promote_guard_payload(payload, packet_id) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id=packet_id,
        output_path=output_path,
        profile="strict-db-query",
        command_profile="strict-db-query",
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload

    output_path.unlink()