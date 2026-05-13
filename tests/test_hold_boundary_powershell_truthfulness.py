from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")
DEFERRED_OPS_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "deferred-ops-view-counts" / "actual"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"
STATE_FILE = REPO_ROOT / ".tmp" / "ai-workflow" / "minimal-mcp-trio.json"


@pytest.fixture(autouse=True)
def _clean_state_file() -> None:
    _cleanup_state_file()
    yield
    _cleanup_state_file()


class _FakeMcpHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")

        if method == "initialize":
            result: dict[str, object] = {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "fake-hold-boundary-surface", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {"name": "read_text_file"},
                    {"name": "query"},
                    {"name": "promote_packet"},
                    {"name": "start_run"},
                    {"name": "end_run"},
                ]
            }
        elif method == "tools/call":
            params = payload.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "read_text_file":
                result = {"structuredContent": {"content": README_PREVIEW}}
            elif tool_name == "query":
                sql = str(arguments.get("sql") or "")
                if "select 1 as ok" in sql:
                    result = {"structuredContent": {"rowCount": 1, "rows": [{"ok": 1}]}}
                elif self.server.deferred_error is not None:
                    result = {"isError": True, "content": [{"text": self.server.deferred_error}]}
                else:
                    result = {"structuredContent": self.server.deferred_rows}
            elif tool_name == "promote_packet":
                result = {
                    "isError": True,
                    "content": [{"text": "no successful env=host run is on record for that packet_id"}],
                }
            elif tool_name == "start_run":
                result = {"structuredContent": {"run_id": "run-123", "packet_id": arguments.get("packet_id")}}
            elif tool_name == "end_run":
                result = {"structuredContent": {"run_id": arguments.get("run_id"), "status": arguments.get("status")}}
            else:
                result = {"isError": True, "content": [{"text": f"unexpected tool {tool_name}"}]}
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


def _cleanup_artifacts(packet_id: str) -> None:
    for artifact in (
        DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
        MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
    ):
        if artifact.exists():
            artifact.unlink()


def _cleanup_state_file() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def _expected_hold_boundary_result(packet_id: str, *, deferred_result: str, deferred_decision: str) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "minimal_mcp": "PASS",
        "deferred_ops": deferred_result,
        "deferred_ops_decision": deferred_decision,
        "outputs": {
            "minimal_mcp": str(MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"),
            "deferred_ops": str(DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"),
        },
    }


def _expected_direct_mode_helper_failure(packet_id: str) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "repo_root": str(REPO_ROOT),
        "checks": {
            "db_connection": {
                "status": "pass",
                "source": "env:SEAM_DATABASE_URL",
                "mode": "direct",
            },
        },
        "result": "FAIL",
        "error": "Could not parse SQLAlchemy URL from given URL string",
    }


def _expected_minimal_trio_verifier_payload(
    packet_id: str,
    *,
    endpoint: str,
    output_path: str,
    command_endpoints: tuple[str, str, str] | None = None,
) -> dict[str, object]:
    command = (
        f'"{REPO_ROOT / ".venv" / "Scripts" / "python.exe"}" '
        f"tools/ai/verify_minimal_mcp_trio.py --packet-id {packet_id} "
        f'--output "{output_path}"'
    )
    if command_endpoints is not None:
        command += (
            f" --fs-url {command_endpoints[0]}"
            f" --db-url {command_endpoints[1]}"
            f" --jobs-url {command_endpoints[2]}"
        )

    return {
        "packet_id": packet_id,
        "command": command,
        "endpoints": {
            "fs": endpoint,
            "db": endpoint,
            "jobs": endpoint,
        },
        "checks": {
            "fs_tools": {
                "status": "pass",
                "tools": [
                    "read_text_file",
                    "query",
                    "promote_packet",
                    "start_run",
                    "end_run",
                ],
            },
            "fs_read": {
                "status": "pass",
                "preview": README_PREVIEW,
            },
            "db_tools": {
                "status": "pass",
                "tools": [
                    "read_text_file",
                    "query",
                    "promote_packet",
                    "start_run",
                    "end_run",
                ],
            },
            "db_query": {
                "status": "pass",
                "result": {
                    "rowCount": 1,
                    "rows": [{"ok": 1}],
                },
            },
            "jobs_tools": {
                "status": "pass",
                "tools": [
                    "read_text_file",
                    "query",
                    "promote_packet",
                    "start_run",
                    "end_run",
                ],
            },
            "jobs_promote_guard": {
                "status": "pass",
                "packet_id": f"{packet_id}-promote-guard-<generated>",
                "detail": "no successful env=host run is on record for that packet_id",
            },
            "jobs_start_run": {
                "status": "pass",
                "run": {
                    "run_id": "run-123",
                    "packet_id": packet_id,
                },
            },
            "jobs_end_run": {
                "status": "pass",
                "run": {
                    "run_id": "run-123",
                    "status": "success",
                },
            },
        },
        "result": "PASS",
    }


def _expected_deferred_ops_child_payload(
    packet_id: str,
    *,
    endpoint: str,
    db_source: str = "env:APEX_DB_MCP_URL",
    result: str,
    decision: str,
    deferred_view_counts: dict[str, object],
    reopen_candidates: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "packet_id": packet_id,
        "repo_root": str(REPO_ROOT),
        "checks": {
            "db_connection": {
                "status": "pass",
                "source": db_source,
                "mode": "mcp",
                "endpoint": endpoint,
            },
            "deferred_view_counts": deferred_view_counts,
        },
        "result": result,
        "decision": decision,
    }
    if reopen_candidates is not None:
        payload["reopen_candidates"] = reopen_candidates
    return payload


def _normalized_powershell_throw_message(stderr: str) -> str:
    stripped_stderr = re.sub(r"\x1b\[[0-9;]*m", "", stderr)
    return " ".join(
        content[1:]
        for line in stripped_stderr.splitlines()
        if "|" in line
        for _, separator, content in [line.partition("|")]
        if separator
        if content.startswith(" ")
        if content == f" {content[1:].strip()}"
        if content[1:]
        and not content[1:].startswith("throw")
        and not set(content[1:]) <= {"~"}
    )


def _assert_hold_boundary_child_artifacts(
    packet_id: str,
    result: dict[str, object],
    *,
    endpoint: str,
    expected_hold_payload: dict[str, object],
    command_endpoints: tuple[str, str, str] | None = None,
) -> None:
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"

    assert minimal_output.exists()
    assert hold_output.exists()

    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))
    hold_payload = json.loads(hold_output.read_text(encoding="utf-8"))

    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"

    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=endpoint,
        output_path=str(minimal_output),
        command_endpoints=command_endpoints,
    )
    assert hold_payload == expected_hold_payload


@pytest.fixture
def fake_hold_boundary_surface():
    servers: list[ThreadingHTTPServer] = []
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(*, deferred_rows: list[dict[str, object]] | None = None, deferred_error: str | None = None) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
        server.deferred_rows = deferred_rows or []
        server.deferred_error = deferred_error
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)

        url = f"http://127.0.0.1:{server.server_address[1]}/mcp"
        env_lines = []
        if original_env_dev is not None:
            env_lines.append(original_env_dev.rstrip("\n"))
        env_lines.extend(
            [
                f"APEX_FS_MCP_URL={url}",
                f"APEX_DB_MCP_URL={url}",
                f"APEX_JOBS_MCP_URL={url}",
            ]
        )
        ENV_DEV_FILE.write_text("\n".join(line for line in env_lines if line) + "\n", encoding="utf-8")
        return url

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
def test_powershell_hold_boundary_reports_hold_when_deferred_views_are_empty(fake_hold_boundary_surface) -> None:
    packet_id = "powershell-hold-boundary-empty-views-test"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-olares-hold-boundary-check.ps1",
        "-PacketId",
        packet_id,
    ])

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="HOLD",
        deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        endpoint=endpoint,
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=endpoint,
            result="HOLD",
            decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
            deferred_view_counts={
                "status": "pass",
                "counts": {
                    "v_equipment_needs": 0,
                    "v_resource_allocation": 0,
                },
            },
            reopen_candidates=[],
        ),
    )

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_reports_reopen_when_deferred_view_has_rows(fake_hold_boundary_surface) -> None:
    packet_id = "powershell-hold-boundary-reopen-test"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 2},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-olares-hold-boundary-check.ps1",
        "-PacketId",
        packet_id,
    ])

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="REOPEN",
        deferred_decision="One or more deferred Operations Visibility seams now have live rows.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        endpoint=endpoint,
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=endpoint,
            result="REOPEN",
            decision="One or more deferred Operations Visibility seams now have live rows.",
            deferred_view_counts={
                "status": "pass",
                "counts": {
                    "v_equipment_needs": 2,
                    "v_resource_allocation": 0,
                },
            },
            reopen_candidates=["v_equipment_needs"],
        ),
    )

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_reports_unavailable_when_authoritative_views_are_missing(fake_hold_boundary_surface) -> None:
    packet_id = "powershell-hold-boundary-unavailable-test"
    endpoint = fake_hold_boundary_surface(deferred_error='relation "public.v_resource_allocation" does not exist')

    result = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-olares-hold-boundary-check.ps1",
        "-PacketId",
        packet_id,
    ])

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="UNAVAILABLE",
        deferred_decision=(
            "Authoritative deferred view counts require apex-db to run against a live DSN such as "
            "SEAM_DATABASE_URL; the current database surface is not sufficient for this hold check."
        ),
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        endpoint=endpoint,
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=endpoint,
            result="UNAVAILABLE",
            decision=(
                "Authoritative deferred view counts require apex-db to run against a live DSN such as "
                "SEAM_DATABASE_URL; the current database surface is not sufficient for this hold check."
            ),
            deferred_view_counts={
                "status": "unavailable",
                "reason": "The current apex-db surface does not expose the authoritative deferred operations views.",
            },
        ),
    )

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_refuses_missing_live_dsn_env_before_running_checks() -> None:
    packet_id = "powershell-hold-boundary-missing-live-dsn-env-test"
    missing_env_name = "MISSING_POWERSHELL_HOLD_BOUNDARY_DSN_ENV"
    env = os.environ.copy()
    env.pop(missing_env_name, None)

    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            "tools/ai/run-olares-hold-boundary-check.ps1",
            "-PacketId",
            packet_id,
            "-DsnEnv",
            missing_env_name,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    normalized_message = _normalized_powershell_throw_message(result.stderr)
    assert normalized_message == (
        f"{missing_env_name} is not set; cannot run the hold-boundary cadence check against a live DSN."
    )
    assert not (DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json").exists()
    assert not (MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json").exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_live_dsn_direct_mode_surfaces_helper_failure(
    fake_hold_boundary_surface,
) -> None:
    packet_id = "powershell-hold-boundary-live-dsn-direct-fail-test"
    dsn_env_name = "POWERSHELL_HOLD_BOUNDARY_LIVE_DSN"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env[dsn_env_name] = "definitely-not-a-real-sqlalchemy-dialect://"

    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            "tools/ai/run-olares-hold-boundary-check.ps1",
            "-PacketId",
            packet_id,
            "-DsnEnv",
            dsn_env_name,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == ""
    assert minimal_output.exists()
    assert hold_output.exists()

    payload = json.loads(hold_output.read_text(encoding="utf-8"))
    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))

    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"

    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=endpoint,
        output_path=str(minimal_output),
    )
    assert payload == _expected_direct_mode_helper_failure(packet_id)

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_live_dsn_fallback_times_out_when_local_db_never_becomes_healthy(
    fake_hold_boundary_surface,
    tmp_path: Path,
) -> None:
    packet_id = "powershell-hold-boundary-live-dsn-timeout-test"
    dsn_env_name = "POWERSHELL_HOLD_BOUNDARY_TIMEOUT_DSN"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    real_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir()
    shim_path = shim_dir / "fake-python.ps1"
    shim_path.write_text(
        "\n".join(
            [
                "param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)",
                'if ($Args.Length -ge 2 -and $Args[0] -eq "-c" -and $Args[1] -eq "import sqlalchemy") { exit 1 }',
                f'& {str(real_python)!r} @Args',
                "exit $LASTEXITCODE",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    env["APEX_PLATFORM_PYTHON"] = "fake-python.ps1"
    env[dsn_env_name] = "postgresql://example:example@127.0.0.1:55432/example"

    command = " ; ".join(
        [
            "function Start-Process { param([Parameter(ValueFromRemainingArguments=$true)]$Args) [pscustomobject]@{ Id = 123; HasExited = $false } }",
            "function Invoke-WebRequest { param([Parameter(ValueFromRemainingArguments=$true)]$Args) throw 'offline' }",
            "function Stop-Process { param([Parameter(ValueFromRemainingArguments=$true)]$Args) }",
            "function Start-Sleep { param([int]$Milliseconds) }",
            f"& './tools/ai/run-olares-hold-boundary-check.ps1' -PacketId {packet_id} -DsnEnv {dsn_env_name}",
        ]
    )

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"

    assert result.returncode == 1
    assert _normalized_powershell_throw_message(result.stderr) == (
        "Timed out waiting for live hold-boundary apex-db on port 8721."
    )
    assert minimal_output.exists()
    assert not hold_output.exists()

    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))
    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"

    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=endpoint,
        output_path=str(minimal_output),
    )

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_surfaces_helper_failure_when_deferred_ops_artifact_path_is_blocked(
    fake_hold_boundary_surface,
) -> None:
    packet_id = "powershell-hold-boundary-blocked-deferred-artifact-test"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()

    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
    hold_output.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            "tools/ai/run-olares-hold-boundary-check.ps1",
            "-PacketId",
            packet_id,
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    expected_payload = _expected_hold_boundary_result(
        packet_id,
        deferred_result="FAIL",
        deferred_decision="<os-shaped-blocked-deferred-decision>",
    )
    payload_without_decision = {key: value for key, value in payload.items() if key != "deferred_ops_decision"}
    expected_without_decision = {key: value for key, value in expected_payload.items() if key != "deferred_ops_decision"}
    assert payload_without_decision == expected_without_decision
    deferred_decision = str(payload.get("deferred_ops_decision") or "").lower()
    normalized_deferred_decision = deferred_decision.replace("\\\\", "\\")
    assert str(hold_output).lower() in normalized_deferred_decision
    assert hold_output.name.lower() in normalized_deferred_decision or "access to the path" in normalized_deferred_decision
    assert re.search(r"permission denied|errno 13", deferred_decision)
    assert result.stderr == ""
    assert minimal_output.exists()
    assert hold_output.exists()
    assert hold_output.is_dir()

    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))
    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"

    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=endpoint,
        output_path=str(minimal_output),
    )

    shutil.rmtree(hold_output)
    _cleanup_artifacts(packet_id)
    _cleanup_state_file()
    _cleanup_state_file()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_hold_boundary_prefers_state_db_endpoint_over_inherited_env_url(fake_hold_boundary_surface) -> None:
    packet_id = "powershell-hold-boundary-state-db-endpoint-wins"
    endpoint = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

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
                "endpoints": {"fs": endpoint, "db": endpoint, "jobs": endpoint},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_json([
        "pwsh",
        "-NoProfile",
        "-File",
        "tools/ai/run-olares-hold-boundary-check.ps1",
        "-PacketId",
        packet_id,
    ])

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="HOLD",
        deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        endpoint=endpoint,
        command_endpoints=(endpoint, endpoint, endpoint),
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=endpoint,
            db_source="argument:db-url",
            result="HOLD",
            decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
            deferred_view_counts={
                "status": "pass",
                "counts": {
                    "v_equipment_needs": 0,
                    "v_resource_allocation": 0,
                },
            },
            reopen_candidates=[],
        ),
    )

    _cleanup_artifacts(packet_id)
    _cleanup_state_file()