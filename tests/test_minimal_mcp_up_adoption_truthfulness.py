from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
PS_STATE_FILE = STATE_DIR / "minimal-mcp-trio.json"
BASH_STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")


class _FakeMcpHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        result = self.server.handle_request(payload)

        body = json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _run_json(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _wsl_repo_root() -> str:
    return subprocess.check_output(["bash", "-lc", "pwd -P"], cwd=REPO_ROOT, text=True).strip()


def _endpoint_block_for_env(env: dict[str, str]) -> dict[str, str]:
    return {
        "fs": f"http://127.0.0.1:{env['APEX_DEV_MCP_FS_PORT']}/mcp",
        "db": f"http://127.0.0.1:{env['APEX_DEV_MCP_DB_PORT']}/mcp",
        "jobs": f"http://127.0.0.1:{env['APEX_DEV_MCP_JOBS_PORT']}/mcp",
    }


def _expected_adopted_result() -> dict[str, object]:
    return {"status": "adopted"}


def _expected_already_running_result() -> dict[str, object]:
    return {"status": "already-running"}


def _expected_workspace_root_mismatch_payload(
    workspace_root: str,
    *,
    expected_workspace_root: str,
) -> dict[str, object]:
    return {
        "status": "adoption-refused",
        "reason": "workspace-root-mismatch",
        "workspace_root": workspace_root,
        "expected_workspace_root": expected_workspace_root,
        "readme_preview": README_PREVIEW,
        "expected_readme_preview": README_PREVIEW,
    }


def _expected_readme_preview_mismatch_payload(workspace_root: str) -> dict[str, object]:
    return {
        "status": "adoption-refused",
        "reason": "readme-preview-mismatch",
        "workspace_root": workspace_root,
        "expected_workspace_root": workspace_root,
        "readme_preview": "foreign README preview",
        "expected_readme_preview": README_PREVIEW,
    }


def _normalized_powershell_adopted_state(state: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(state))
    normalized["started_at"] = "<generated>"
    return normalized


def _expected_powershell_adopted_state(packet_id: str, *, env: dict[str, str]) -> dict[str, object]:
    return {
        "started_at": "<generated>",
        "packet_id": packet_id,
        "mode": "adopted",
        "processes": [],
        "endpoints": _endpoint_block_for_env(env),
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
    }


def _read_bash_state_values() -> dict[str, str]:
    values: dict[str, str] = {}
    assignment_count = 0
    for raw_line in BASH_STATE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        assignment_count += 1
        values[key] = value.strip().strip("'")
    assert len(values) == assignment_count
    return values


def _normalized_bash_adopted_state(state: dict[str, str]) -> dict[str, str]:
    normalized = dict(state)
    normalized["STARTED_AT"] = "<generated>"
    return normalized


def _expected_bash_adopted_state(packet_id: str, *, env: dict[str, str]) -> dict[str, str]:
    endpoints = _endpoint_block_for_env(env)
    return {
        "STARTED_AT": "<generated>",
        "PACKET_ID": packet_id,
        "MODE": "adopted",
        "FS_PID": "",
        "DB_PID": "",
        "JOBS_PID": "",
        "LEDGER_PATH": f"{_wsl_repo_root()}/.apex-data/apex-jobs-ledger.json",
        "FS_ENDPOINT": endpoints["fs"],
        "DB_ENDPOINT": endpoints["db"],
        "JOBS_ENDPOINT": endpoints["jobs"],
    }


def _write_powershell_managed_state(pid: int) -> None:
    payload = {
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": "powershell-already-running-test",
        "mode": "managed",
        "processes": [
            {"name": "apex-fs", "pid": pid, "log": "fs.log"},
            {"name": "apex-db", "pid": pid, "log": "db.log"},
            {"name": "apex-jobs", "pid": pid, "log": "jobs.log"},
        ],
        "endpoints": {
            "fs": "http://127.0.0.1:59110/mcp",
            "db": "http://127.0.0.1:59111/mcp",
            "jobs": "http://127.0.0.1:59112/mcp",
        },
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
    }
    PS_STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_bash_managed_state(pid: str) -> None:
    BASH_STATE_FILE.write_text(
        "\n".join(
            [
                "STARTED_AT='2026-05-11T00:00:00Z'",
                "PACKET_ID='bash-already-running-test'",
                "MODE='managed'",
                f"FS_PID='{pid}'",
                f"DB_PID='{pid}'",
                f"JOBS_PID='{pid}'",
                f"LEDGER_PATH='{REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json'}'",
                "FS_ENDPOINT='http://127.0.0.1:59110/mcp'",
                "DB_ENDPOINT='http://127.0.0.1:59111/mcp'",
                "JOBS_ENDPOINT='http://127.0.0.1:59112/mcp'",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def _start_bash_sleep_process() -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        ["bash", "-lc", "printf '%s\n' \"$$\"; sleep 30"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    pid = process.stdout.readline().strip()
    if not pid:
        stderr = ""
        if process.stderr is not None:
            stderr = process.stderr.read()
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError(f"Failed to start Bash sleep process: {stderr}")
    return process, pid


@pytest.fixture(autouse=True)
def _clean_state_files() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()
    yield
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()


@pytest.fixture
def fake_unmanaged_trio_powershell():
    servers: list[ThreadingHTTPServer] = []
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(*, workspace_root: str | None = None, readme_preview: str | None = None) -> dict[str, str]:
        resolved_workspace_root = workspace_root or str(REPO_ROOT.resolve())
        resolved_readme_preview = readme_preview or README_PREVIEW

        def handle_request(payload: dict[str, object]) -> dict[str, object]:
            method = payload.get("method")
            if method == "initialize":
                return {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "serverInfo": {"name": "fake-unmanaged-trio", "version": "0.1.0"},
                }

            if method == "tools/call":
                tool_name = payload.get("params", {}).get("name")
                if tool_name == "list_roots":
                    return {"structuredContent": {"workspace": resolved_workspace_root}}
                if tool_name == "read_text_file":
                    return {"structuredContent": {"content": resolved_readme_preview}}
                return {"isError": True, "content": [{"text": f"unexpected tool {tool_name}"}]}

            return {"isError": True, "content": [{"text": f"unexpected method {method}"}]}

        server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
        server.handle_request = handle_request
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)

        port = str(server.server_address[1])
        env_lines = []
        if original_env_dev is not None:
            env_lines.append(original_env_dev.rstrip("\n"))
        env_lines.extend(
            [
                f"APEX_DEV_MCP_FS_PORT={port}",
                f"APEX_DEV_MCP_DB_PORT={port}",
                f"APEX_DEV_MCP_JOBS_PORT={port}",
            ]
        )
        ENV_DEV_FILE.write_text("\n".join(line for line in env_lines if line) + "\n", encoding="utf-8")

        env = os.environ.copy()
        env["APEX_DEV_MCP_FS_PORT"] = port
        env["APEX_DEV_MCP_DB_PORT"] = port
        env["APEX_DEV_MCP_JOBS_PORT"] = port
        return env

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()

    if original_env_dev is None:
        if ENV_DEV_FILE.exists():
            ENV_DEV_FILE.unlink()
    else:
        ENV_DEV_FILE.write_text(original_env_dev, encoding="utf-8")


@pytest.fixture
def fake_unmanaged_trio_bash():
    server_process: subprocess.Popen[str] | None = None
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(*, workspace_root: str | None = None, readme_preview: str | None = None) -> dict[str, str]:
        nonlocal server_process
        resolved_workspace_root = workspace_root or _wsl_repo_root()
        resolved_readme_preview = readme_preview or README_PREVIEW
        server_script = f"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKSPACE_ROOT = {json.dumps(resolved_workspace_root)}
README_PREVIEW = {json.dumps(resolved_readme_preview)}

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/mcp':
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length).decode('utf-8'))
        method = payload.get('method')

        if method == 'initialize':
            result = {{
                'protocolVersion': '2025-03-26',
                'capabilities': {{}},
                'serverInfo': {{'name': 'fake-unmanaged-trio', 'version': '0.1.0'}},
            }}
        elif method == 'tools/call':
            tool_name = payload.get('params', {{}}).get('name')
            if tool_name == 'list_roots':
                result = {{'structuredContent': {{'workspace': WORKSPACE_ROOT}}}}
            elif tool_name == 'read_text_file':
                result = {{'structuredContent': {{'content': README_PREVIEW}}}}
            else:
                result = {{'isError': True, 'content': [{{'text': f'unexpected tool {{tool_name}}'}}]}}
        else:
            result = {{'isError': True, 'content': [{{'text': f'unexpected method {{method}}'}}]}}

        body = json.dumps({{'jsonrpc': '2.0', 'id': payload.get('id'), 'result': result}}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
print(server.server_address[1], flush=True)
server.serve_forever()
"""

        server_process = subprocess.Popen(
            ["bash", "-lc", f"python3 -u - <<'PY'\n{server_script}\nPY"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert server_process.stdout is not None
        port = server_process.stdout.readline().strip()
        if not port:
            stderr = ""
            if server_process.stderr is not None:
                stderr = server_process.stderr.read()
            raise RuntimeError(f"Failed to start fake unmanaged MCP server: {stderr}")

        env_lines = []
        if original_env_dev is not None:
            env_lines.append(original_env_dev.rstrip("\n"))
        env_lines.extend(
            [
                f"APEX_DEV_MCP_FS_PORT={port}",
                f"APEX_DEV_MCP_DB_PORT={port}",
                f"APEX_DEV_MCP_JOBS_PORT={port}",
            ]
        )
        ENV_DEV_FILE.write_text("\n".join(line for line in env_lines if line) + "\n", encoding="utf-8")

        env = os.environ.copy()
        env["APEX_DEV_MCP_FS_PORT"] = port
        env["APEX_DEV_MCP_DB_PORT"] = port
        env["APEX_DEV_MCP_JOBS_PORT"] = port
        return env

    yield _start

    if server_process is not None:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait(timeout=5)

    if original_env_dev is None:
        if ENV_DEV_FILE.exists():
            ENV_DEV_FILE.unlink()
    else:
        ENV_DEV_FILE.write_text(original_env_dev, encoding="utf-8")


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_reports_adopted_when_live_trio_exists(fake_unmanaged_trio_powershell) -> None:
    packet_id = "powershell-adopted-up-test"
    env = fake_unmanaged_trio_powershell()

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", packet_id],
        env=env,
    )

    state = json.loads(PS_STATE_FILE.read_text(encoding="utf-8"))
    assert result == _expected_adopted_result()
    assert _normalized_powershell_adopted_state(state) == _expected_powershell_adopted_state(packet_id, env=env)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_refuses_adoption_when_live_trio_reports_foreign_workspace_root(
    fake_unmanaged_trio_powershell,
) -> None:
    packet_id = "powershell-adoption-refused-up-test"
    foreign_root = str((REPO_ROOT / ".." / "foreign-workspace-root").resolve())

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", packet_id],
        cwd=REPO_ROOT,
        env=fake_unmanaged_trio_powershell(workspace_root=foreign_root),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_workspace_root_mismatch_payload(
        foreign_root,
        expected_workspace_root=str(REPO_ROOT),
    )
    assert result.stderr == ""
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_refuses_adoption_when_live_trio_reports_mismatched_readme_preview(
    fake_unmanaged_trio_powershell,
) -> None:
    packet_id = "powershell-readme-refused-up-test"

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", packet_id],
        cwd=REPO_ROOT,
        env=fake_unmanaged_trio_powershell(readme_preview="foreign README preview"),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_readme_preview_mismatch_payload(str(REPO_ROOT))
    assert result.stderr == ""
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_reports_adopted_when_live_trio_exists(fake_unmanaged_trio_bash) -> None:
    packet_id = "bash-adopted-up-test"
    env = fake_unmanaged_trio_bash()

    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", packet_id],
        env=env,
    )

    state = _read_bash_state_values()
    assert result == _expected_adopted_result()
    assert _normalized_bash_adopted_state(state) == _expected_bash_adopted_state(packet_id, env=env)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_refuses_adoption_when_live_trio_reports_foreign_workspace_root(fake_unmanaged_trio_bash) -> None:
    packet_id = "bash-adoption-refused-up-test"
    foreign_root = f"{_wsl_repo_root().rsplit('/', 1)[0]}/foreign-workspace-root"

    result = subprocess.run(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", packet_id],
        cwd=REPO_ROOT,
        env=fake_unmanaged_trio_bash(workspace_root=foreign_root),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_workspace_root_mismatch_payload(
        foreign_root,
        expected_workspace_root=_wsl_repo_root(),
    )
    assert result.stderr == ""
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_refuses_adoption_when_live_trio_reports_mismatched_readme_preview(fake_unmanaged_trio_bash) -> None:
    packet_id = "bash-readme-refused-up-test"

    result = subprocess.run(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", packet_id],
        cwd=REPO_ROOT,
        env=fake_unmanaged_trio_bash(readme_preview="foreign README preview"),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_readme_preview_mismatch_payload(_wsl_repo_root())
    assert result.stderr == ""
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_reports_already_running_when_managed_state_processes_are_live() -> None:
    _write_powershell_managed_state(os.getpid())

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up"],
    )

    assert result == _expected_already_running_result()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_reports_already_running_when_managed_state_processes_are_live() -> None:
    process, pid = _start_bash_sleep_process()
    try:
        _write_bash_managed_state(pid)

        result = _run_json(
            ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up"],
        )

        assert result == _expected_already_running_result()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)