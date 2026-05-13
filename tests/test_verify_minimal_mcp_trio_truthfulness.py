from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")
_UNSET = object()


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
            if getattr(self.server, "initialize_error", None):
                result = {
                    "isError": True,
                    "content": [{"text": self.server.initialize_error}],
                }
            else:
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "serverInfo": {"name": f"fake-{server_name}", "version": "0.1.0"},
                }
        elif method == "tools/list":
            if getattr(self.server, "tools_list_error", None):
                result = {
                    "isError": True,
                    "content": [{"text": self.server.tools_list_error}],
                }
            else:
                result = {"tools": [{"name": name} for name in self.server.tool_names]}
        elif method == "tools/call":
            result = self.server.handle_tool_call(payload.get("params", {}))
        else:
            result = {
                "isError": True,
                "content": [{"text": f"unexpected method {method}"}],
            }

        body = json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


@pytest.fixture
def fake_trio():
    servers: list[ThreadingHTTPServer] = []

    def _start(
        *,
        db_query_error: str | None = None,
        initialize_errors: dict[str, str] | None = None,
        tools_list_errors: dict[str, str] | None = None,
        fs_read_error: str | None = None,
        promote_packet_error: str | None = None,
        start_run_error: str | None = None,
        end_run_error: str | None = None,
    ) -> tuple[str, str, str]:
        def fs_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            if tool_name == "read_text_file":
                if fs_read_error is not None:
                    return {
                        "isError": True,
                        "content": [{"text": fs_read_error}],
                    }
                return {"structuredContent": {"content": README_PREVIEW}}
            return {"isError": True, "content": [{"text": f"unexpected fs tool {tool_name}"}]}

        def db_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            if tool_name == "query":
                if db_query_error is not None:
                    return {"isError": True, "content": [{"text": db_query_error}]}
                return {"structuredContent": {"rowCount": 1, "rows": [{"ok": 1}]}}
            return {"isError": True, "content": [{"text": f"unexpected db tool {tool_name}"}]}

        def jobs_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "promote_packet":
                if promote_packet_error is not None:
                    return {
                        "isError": True,
                        "content": [{"text": promote_packet_error}],
                    }
                return {
                    "isError": True,
                    "content": [{"text": "no successful env=host run is on record for that packet_id"}],
                }
            if tool_name == "start_run":
                if start_run_error is not None:
                    return {
                        "isError": True,
                        "content": [{"text": start_run_error}],
                    }
                return {"structuredContent": {"run_id": "run-123", "packet_id": arguments.get("packet_id")}}
            if tool_name == "end_run":
                if end_run_error is not None:
                    return {
                        "isError": True,
                        "content": [{"text": end_run_error}],
                    }
                return {"structuredContent": {"run_id": arguments.get("run_id"), "status": arguments.get("status")}}
            return {"isError": True, "content": [{"text": f"unexpected jobs tool {tool_name}"}]}

        for service_name, tool_names, handler in (
            ("fs", ["read_text_file"], fs_handler),
            ("db", ["query"], db_handler),
            ("jobs", ["promote_packet", "start_run", "end_run"], jobs_handler),
        ):
            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
            server.service_name = service_name
            server.tool_names = tool_names
            server.handle_tool_call = handler
            server.initialize_error = (initialize_errors or {}).get(service_name)
            server.tools_list_error = (tools_list_errors or {}).get(service_name)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            servers.append(server)

        endpoints = tuple(f"http://127.0.0.1:{server.server_address[1]}/mcp" for server in servers)
        return endpoints  # type: ignore[return-value]

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


def _run_helper(
    fs_url: str | None,
    db_url: str | None,
    jobs_url: str | None,
    *,
    packet_id: str | None = "verify-trio-test",
    require_db_query: bool = False,
    env: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "tools/ai/verify_minimal_mcp_trio.py",
    ]
    if fs_url is not None:
        command.extend(["--fs-url", fs_url])
    if db_url is not None:
        command.extend(["--db-url", db_url])
    if jobs_url is not None:
        command.extend(["--jobs-url", jobs_url])
    if packet_id is not None:
        command[2:2] = ["--packet-id", packet_id]
    if require_db_query:
        command.append("--require-db-query")
    if output_path is not None:
        command.extend(["--output", str(output_path)])

    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _expected_verify_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)

    return shlex.join(argv)


def _normalized_promote_guard_payload(payload: dict[str, object], packet_id: str) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    normalized["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"
    return normalized


def _normalized_adhoc_packet_id_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    normalized_packet_id = "adhoc-verify-minimal-mcp-trio-<generated>"
    normalized["packet_id"] = normalized_packet_id
    normalized["checks"]["jobs_promote_guard"]["packet_id"] = f"{normalized_packet_id}-promote-guard-<generated>"
    normalized["checks"]["jobs_start_run"]["run"]["packet_id"] = normalized_packet_id
    return normalized


def _expected_jobs_promote_guard_check(packet_id: str = "verify-trio-test") -> dict[str, object]:
    return {
        "status": "pass",
        "packet_id": f"{packet_id}-promote-guard-<generated>",
        "detail": "no successful env=host run is on record for that packet_id",
    }


def _expected_verify_pass_payload(
    fs_url: str,
    db_url: str,
    jobs_url: str,
    *,
    packet_id: str = "verify-trio-test",
    packet_id_arg: object | str | None = _UNSET,
    fs_url_arg: str | None = None,
    db_url_arg: str | None = None,
    jobs_url_arg: str | None = None,
    output_path: Path | None = None,
    include_url_args: bool = True,
) -> dict[str, object]:
    command = [
        sys.executable,
        "tools/ai/verify_minimal_mcp_trio.py",
    ]
    if packet_id_arg is _UNSET:
        packet_id_arg = packet_id
    if packet_id_arg is not None:
        command.extend(["--packet-id", packet_id_arg])
    if include_url_args:
        if fs_url_arg is None:
            fs_url_arg = fs_url
        if db_url_arg is None:
            db_url_arg = db_url
        if jobs_url_arg is None:
            jobs_url_arg = jobs_url
        if fs_url_arg is not None:
            command.extend(["--fs-url", fs_url_arg])
        if db_url_arg is not None:
            command.extend(["--db-url", db_url_arg])
        if jobs_url_arg is not None:
            command.extend(["--jobs-url", jobs_url_arg])
    if output_path is not None:
        command.extend(["--output", str(output_path)])
    return {
        "packet_id": packet_id,
        "command": _expected_verify_command(command),
        "endpoints": {"fs": fs_url, "db": db_url, "jobs": jobs_url},
        "checks": {
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}},
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run"]},
            "jobs_promote_guard": _expected_jobs_promote_guard_check(packet_id),
            "jobs_start_run": {"status": "pass", "run": {"run_id": "run-123", "packet_id": packet_id}},
            "jobs_end_run": {"status": "pass", "run": {"run_id": "run-123", "status": "success"}},
        },
        "result": "PASS",
    }


def _expected_verify_degraded_db_query_payload(
    fs_url: str,
    db_url: str,
    jobs_url: str,
    *,
    packet_id: str = "verify-trio-test",
    error: str = "temporary db query failure",
) -> dict[str, object]:
    expected = json.loads(json.dumps(_expected_verify_pass_payload(fs_url, db_url, jobs_url, packet_id=packet_id)))
    expected["checks"]["db_query"] = {"status": "degraded", "error": error}
    return expected


def _expected_verify_failure_payload(
    fs_url: str,
    db_url: str,
    jobs_url: str,
    *,
    packet_id: str = "verify-trio-test",
    error: str,
    checks: dict[str, object] | None = None,
    require_db_query: bool = False,
    output_path: Path | None = None,
) -> dict[str, object]:
    command = [
        sys.executable,
        "tools/ai/verify_minimal_mcp_trio.py",
        "--packet-id",
        packet_id,
        "--fs-url",
        fs_url,
        "--db-url",
        db_url,
        "--jobs-url",
        jobs_url,
    ]
    if require_db_query:
        command.append("--require-db-query")
    if output_path is not None:
        command.extend(["--output", str(output_path)])
    return {
        "packet_id": packet_id,
        "command": _expected_verify_command(command),
        "endpoints": {"fs": fs_url, "db": db_url, "jobs": jobs_url},
        "checks": checks or {},
        "result": "FAIL",
        "error": error,
    }


def test_verify_minimal_mcp_trio_reports_pass_with_fake_trio(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "verify-trio-test") == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
    )


def test_verify_minimal_mcp_trio_degrades_db_query_when_not_required(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(db_query_error="temporary db query failure")

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "verify-trio-test") == _expected_verify_degraded_db_query_payload(
        fs_url,
        db_url,
        jobs_url,
    )


def test_verify_minimal_mcp_trio_fails_when_fs_initialize_errors(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(initialize_errors={"fs": "temporary fs initialize failure"})

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary fs initialize failure",
    )


def test_verify_minimal_mcp_trio_fails_when_fs_tools_list_errors(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(tools_list_errors={"fs": "temporary fs tools/list failure"})

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary fs tools/list failure",
    )


def test_verify_minimal_mcp_trio_fails_when_fs_read_errors_unexpectedly(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(fs_read_error="temporary fs read failure")

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary fs read failure",
        checks={"fs_tools": {"status": "pass", "tools": ["read_text_file"]}},
    )


def test_verify_minimal_mcp_trio_fails_when_promote_packet_errors_unexpectedly(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(promote_packet_error="temporary promote_packet failure")

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary promote_packet failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}},
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run"]},
        },
    )


def test_verify_minimal_mcp_trio_fails_when_start_run_errors_unexpectedly(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(start_run_error="temporary start_run failure")

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "verify-trio-test") == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary start_run failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}},
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run"]},
            "jobs_promote_guard": _expected_jobs_promote_guard_check(),
        },
    )


def test_verify_minimal_mcp_trio_fails_when_end_run_errors_unexpectedly(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(end_run_error="temporary end_run failure")

    result = _run_helper(fs_url, db_url, jobs_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "verify-trio-test") == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary end_run failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}},
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run"]},
            "jobs_promote_guard": _expected_jobs_promote_guard_check(),
            "jobs_start_run": {"status": "pass", "run": {"run_id": "run-123", "packet_id": "verify-trio-test"}},
        },
    )


def test_verify_minimal_mcp_trio_fails_db_query_when_required(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio(db_query_error="temporary db query failure")

    result = _run_helper(fs_url, db_url, jobs_url, require_db_query=True)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary db query failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "fail", "error": "temporary db query failure"},
        },
        require_db_query=True,
    )


def test_verify_minimal_mcp_trio_writes_failure_output_when_required_db_query_fails(
    fake_trio, tmp_path: Path
) -> None:
    fs_url, db_url, jobs_url = fake_trio(db_query_error="temporary db query failure")
    output_path = tmp_path / "verify-minimal-mcp-trio-failure.json"

    result = _run_helper(
        fs_url,
        db_url,
        jobs_url,
        require_db_query=True,
        output_path=output_path,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary db query failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "fail", "error": "temporary db query failure"},
        },
        require_db_query=True,
        output_path=output_path,
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_verify_minimal_mcp_trio_preserves_fail_json_when_output_path_is_invalid(
    fake_trio, tmp_path: Path
) -> None:
    fs_url, db_url, jobs_url = fake_trio(db_query_error="temporary db query failure")
    blocked_parent = tmp_path / "blocked-output-parent"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    output_path = blocked_parent / "verify-minimal-mcp-trio-failure.json"

    result = _run_helper(
        fs_url,
        db_url,
        jobs_url,
        require_db_query=True,
        output_path=output_path,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    payload_without_output_error = {key: value for key, value in payload.items() if key != "output_error"}
    assert payload_without_output_error == _expected_verify_failure_payload(
        fs_url,
        db_url,
        jobs_url,
        error="temporary db query failure",
        checks={
            "fs_tools": {"status": "pass", "tools": ["read_text_file"]},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": ["query"]},
            "db_query": {"status": "fail", "error": "temporary db query failure"},
        },
        require_db_query=True,
        output_path=output_path,
    )
    output_error = payload["output_error"].lower()
    normalized_output_error = output_error.replace("\\\\", "\\")
    assert str(blocked_parent).lower() in normalized_output_error
    assert output_path.name.lower() in normalized_output_error or "already exists" in normalized_output_error
    assert re.search(r"directory|exists|permission denied", output_error)


def test_verify_minimal_mcp_trio_uses_env_packet_id_and_writes_output(fake_trio, tmp_path: Path) -> None:
    fs_url, db_url, jobs_url = fake_trio()
    output_path = tmp_path / "verify-minimal-mcp-trio.json"
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "env-verify-trio-test"

    result = _run_helper(
        fs_url,
        db_url,
        jobs_url,
        packet_id=None,
        env=env,
        output_path=output_path,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "env-verify-trio-test") == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="env-verify-trio-test",
        packet_id_arg=None,
        output_path=output_path,
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_verify_minimal_mcp_trio_generates_adhoc_packet_id_when_omitted(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()

    result = _run_helper(fs_url, db_url, jobs_url, packet_id=None, env=os.environ.copy())

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_adhoc_packet_id_payload(payload) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="adhoc-verify-minimal-mcp-trio-<generated>",
        packet_id_arg=None,
    )


def test_verify_minimal_mcp_trio_prefers_explicit_packet_id_over_env(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "env-verify-trio-test"

    result = _run_helper(fs_url, db_url, jobs_url, packet_id="cli-verify-trio-test", env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_promote_guard_payload(payload, "cli-verify-trio-test") == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="cli-verify-trio-test",
    )


def test_verify_minimal_mcp_trio_prefers_explicit_urls_over_port_defaults(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()
    env = os.environ.copy()
    env["APEX_DEV_MCP_FS_PORT"] = "1"
    env["APEX_DEV_MCP_DB_PORT"] = "2"
    env["APEX_DEV_MCP_JOBS_PORT"] = "3"
    env["APEX_FS_MCP_URL"] = fs_url
    env["APEX_DB_MCP_URL"] = db_url
    env["APEX_JOBS_MCP_URL"] = jobs_url

    result = _run_helper(None, None, None, packet_id=None, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_adhoc_packet_id_payload(payload) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="adhoc-verify-minimal-mcp-trio-<generated>",
        packet_id_arg=None,
        include_url_args=False,
    )


def test_verify_minimal_mcp_trio_uses_port_defaults_when_explicit_urls_are_absent(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()
    env = os.environ.copy()
    env.pop("APEX_FS_MCP_URL", None)
    env.pop("APEX_DB_MCP_URL", None)
    env.pop("APEX_JOBS_MCP_URL", None)
    env["APEX_DEV_MCP_FS_PORT"] = fs_url.removeprefix("http://127.0.0.1:").removesuffix("/mcp")
    env["APEX_DEV_MCP_DB_PORT"] = db_url.removeprefix("http://127.0.0.1:").removesuffix("/mcp")
    env["APEX_DEV_MCP_JOBS_PORT"] = jobs_url.removeprefix("http://127.0.0.1:").removesuffix("/mcp")

    result = _run_helper(None, None, None, packet_id=None, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_adhoc_packet_id_payload(payload) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="adhoc-verify-minimal-mcp-trio-<generated>",
        packet_id_arg=None,
        include_url_args=False,
    )


def test_verify_minimal_mcp_trio_prefers_explicit_cli_urls_over_env_defaults(fake_trio) -> None:
    fs_url, db_url, jobs_url = fake_trio()
    env = os.environ.copy()
    env["APEX_FS_MCP_URL"] = "http://127.0.0.1:1/mcp"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_JOBS_MCP_URL"] = "http://127.0.0.1:3/mcp"
    env["APEX_DEV_MCP_FS_PORT"] = "4"
    env["APEX_DEV_MCP_DB_PORT"] = "5"
    env["APEX_DEV_MCP_JOBS_PORT"] = "6"

    result = _run_helper(fs_url, db_url, jobs_url, packet_id=None, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_adhoc_packet_id_payload(payload) == _expected_verify_pass_payload(
        fs_url,
        db_url,
        jobs_url,
        packet_id="adhoc-verify-minimal-mcp-trio-<generated>",
        packet_id_arg=None,
        fs_url_arg=fs_url,
        db_url_arg=db_url,
        jobs_url_arg=jobs_url,
    )