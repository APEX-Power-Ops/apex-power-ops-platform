from __future__ import annotations

import json
import os
import contextlib
import shlex
import shutil
import subprocess
import threading
from pathlib import Path, PurePosixPath
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
PS_STATE_FILE = STATE_DIR / "minimal-mcp-trio.json"
BASH_STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"
HOST_BOOTSTRAP_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "host-bootstrap-status" / "actual"
DEFERRED_OPS_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "deferred-ops-view-counts" / "actual"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")


@contextlib.contextmanager
def _hide_repo_env_file() -> None:
    backup = ENV_DEV_FILE.with_suffix(".env.dev.backup")
    had_env_dev = ENV_DEV_FILE.exists()

    if had_env_dev:
        ENV_DEV_FILE.replace(backup)

    try:
        yield
    finally:
        if ENV_DEV_FILE.exists() and not had_env_dev:
            ENV_DEV_FILE.unlink()
        if had_env_dev:
            if ENV_DEV_FILE.exists():
                ENV_DEV_FILE.unlink()
            backup.replace(ENV_DEV_FILE)


class _FakeMcpHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")
        result = self.server.handle_request(payload, method)

        body = json.dumps({"jsonrpc": "2.0", "id": payload.get("id"), "result": result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _base_env(fs_port: str = "59110", db_port: str = "59111", jobs_port: str = "59112") -> dict[str, str]:
    env = os.environ.copy()
    env["APEX_DEV_MCP_FS_PORT"] = fs_port
    env["APEX_DEV_MCP_DB_PORT"] = db_port
    env["APEX_DEV_MCP_JOBS_PORT"] = jobs_port
    return env


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


def _write_powershell_state(mode: str) -> None:
    payload = {
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": f"stale-{mode}-test",
        "mode": mode,
        "processes": []
        if mode == "adopted"
        else [
            {"name": "apex-fs", "pid": 999991, "log": "fs.log"},
            {"name": "apex-db", "pid": 999992, "log": "db.log"},
            {"name": "apex-jobs", "pid": 999993, "log": "jobs.log"},
        ],
        "endpoints": {
            "fs": "http://127.0.0.1:59110/mcp",
            "db": "http://127.0.0.1:59111/mcp",
            "jobs": "http://127.0.0.1:59112/mcp",
        },
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
    }
    PS_STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_bash_state(mode: str) -> None:
    lines = [
        "STARTED_AT='2026-05-11T00:00:00Z'",
        f"PACKET_ID='stale-{mode}-test'",
        f"MODE='{mode}'",
        f"LEDGER_PATH='{(REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json').as_posix()}'",
        "FS_ENDPOINT='http://127.0.0.1:59110/mcp'",
        "DB_ENDPOINT='http://127.0.0.1:59111/mcp'",
        "JOBS_ENDPOINT='http://127.0.0.1:59112/mcp'",
    ]
    if mode == "managed":
        lines.extend(
            [
                "FS_PID='999991'",
                "DB_PID='999992'",
                "JOBS_PID='999993'",
            ]
        )
    with BASH_STATE_FILE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def _cleanup_host_bootstrap_artifact(packet_id: str) -> None:
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    if artifact.exists():
        artifact.unlink()


def _assert_no_hold_boundary_child_artifacts(
    packet_id: str,
    hold_boundary: dict[str, object],
    minimal_mcp: dict[str, object],
    expected_minimal_mcp: str,
    expected_deferred_ops_decision: str,
) -> None:
    deferred_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"

    assert hold_boundary == {
        "packet_id": "status-only",
        "minimal_mcp": expected_minimal_mcp,
        "minimal_mcp_detail": minimal_mcp,
        "deferred_ops": "UNAVAILABLE",
        "deferred_ops_decision": expected_deferred_ops_decision,
        "outputs": {},
    }
    assert not deferred_output.exists()
    assert not minimal_output.exists()


def _expected_stale_bash_minimal_mcp(mode: str) -> dict[str, object]:
    return {
        "status": "not-running",
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": f"stale-{mode}-test",
        "mode": mode,
        "fs_running": False,
        "db_running": False,
        "jobs_running": False,
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json").replace("\\", "/"),
        "fs_endpoint": "http://127.0.0.1:59110/mcp",
        "db_endpoint": "http://127.0.0.1:59111/mcp",
        "jobs_endpoint": "http://127.0.0.1:59112/mcp",
    }


def _expected_stale_powershell_status(mode: str) -> dict[str, object]:
    endpoints = {
        "fs": "http://127.0.0.1:59110/mcp",
        "db": "http://127.0.0.1:59111/mcp",
        "jobs": "http://127.0.0.1:59112/mcp",
    }
    return {
        "status": "not-running",
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": f"stale-{mode}-test",
        "mode": mode,
        "fs_running": False,
        "db_running": False,
        "jobs_running": False,
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
        "fs_endpoint": endpoints["fs"],
        "db_endpoint": endpoints["db"],
        "jobs_endpoint": endpoints["jobs"],
        "endpoints": endpoints,
        "processes": []
        if mode == "adopted"
        else [
            {"name": "apex-fs", "pid": 999991, "running": False, "log": "fs.log"},
            {"name": "apex-db", "pid": 999992, "running": False, "log": "db.log"},
            {"name": "apex-jobs", "pid": 999993, "running": False, "log": "jobs.log"},
        ],
    }


def _expected_unmanaged_powershell_status(env: dict[str, str]) -> dict[str, object]:
    return {
        "status": "unmanaged-running",
        "mode": "unmanaged",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "ledger_path": str(REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json"),
        "fs_endpoint": f"http://127.0.0.1:{env['APEX_DEV_MCP_FS_PORT']}/mcp",
        "db_endpoint": f"http://127.0.0.1:{env['APEX_DEV_MCP_DB_PORT']}/mcp",
        "jobs_endpoint": f"http://127.0.0.1:{env['APEX_DEV_MCP_JOBS_PORT']}/mcp",
    }


def _expected_unmanaged_bash_minimal_mcp(
    env: dict[str, str],
    ownership_probe: dict[str, object],
) -> dict[str, object]:
    port = env["APEX_DEV_MCP_FS_PORT"]
    return {
        "status": "unmanaged-running",
        "mode": "unmanaged",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "ledger_path": f"{_wsl_repo_root()}/.apex-data/apex-jobs-ledger.json",
        "fs_endpoint": f"http://127.0.0.1:{port}/mcp",
        "db_endpoint": f"http://127.0.0.1:{port}/mcp",
        "jobs_endpoint": f"http://127.0.0.1:{port}/mcp",
        "ownership_probe": ownership_probe,
    }


def _expected_unmanaged_bash_status(env: dict[str, str]) -> dict[str, object]:
    port = env["APEX_DEV_MCP_FS_PORT"]
    return {
        "status": "unmanaged-running",
        "mode": "unmanaged",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "ledger_path": f"{_wsl_repo_root()}/.apex-data/apex-jobs-ledger.json",
        "fs_endpoint": f"http://127.0.0.1:{port}/mcp",
        "db_endpoint": f"http://127.0.0.1:{port}/mcp",
        "jobs_endpoint": f"http://127.0.0.1:{port}/mcp",
    }


def _current_repo_git_metadata() -> dict[str, object]:
    repo_root = _wsl_repo_root()
    output = subprocess.check_output(["bash", "-lc", f"git -C {shlex.quote(repo_root)} status --porcelain"], text=True)
    return {
        "head": subprocess.check_output(["bash", "-lc", f"git -C {shlex.quote(repo_root)} rev-parse HEAD"], text=True).strip(),
        "status_count": 0 if not output else len(output.rstrip("\n").splitlines()),
        "old_clone": {
            "path": "/home/olares/src/apex-power-ops-platform",
            "exists": False,
            "head": None,
            "status_count": 0,
        },
    }


def _bash_output(command: str, *, env: dict[str, str]) -> str:
    completed = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = completed.stdout.replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    assert len(lines) <= 1
    assert all(line == line.strip() for line in lines)
    return lines[0] if lines else ""


def _current_bash_toolchains_metadata(env: dict[str, str]) -> dict[str, object]:
    preferred_python = _bash_output(
        "source tools/shell/common.sh; import_apex_env_file; get_apex_preferred_python",
        env=env,
    )
    python3_path = _bash_output("command -v python3 || true", env=env) or None
    node_path = _bash_output("command -v node || true", env=env) or None
    pnpm_path = _bash_output(
        "path='/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm'; "
        "if [[ -e \"$path\" ]]; then printf '%s' \"$path\"; fi",
        env=env,
    ) or None
    calc_engine_python = _bash_output(
        "path='/home/olares/apex-data/toolchains/calc-engine-venv/bin/python'; "
        "if [[ -e \"$path\" ]]; then printf '%s' \"$path\"; fi",
        env=env,
    ) or None

    return {
        "preferred_python": {
            "path": preferred_python or None,
            "version": _bash_output(f"{shlex.quote(preferred_python)} --version | head -n 1", env=env)
            if preferred_python
            else None,
        },
        "python3": {
            "path": python3_path,
            "version": _bash_output("python3 --version | head -n 1", env=env) if python3_path else None,
        },
        "node": {
            "path": node_path,
            "version": _bash_output("node --version | head -n 1", env=env) if node_path else None,
        },
        "pnpm_materialized": {
            "path": pnpm_path,
            "version": _bash_output(f"{shlex.quote(pnpm_path)} --version | head -n 1", env=env) if pnpm_path else None,
        },
        "calc_engine_python": {
            "path": calc_engine_python,
            "version": _bash_output(f"{shlex.quote(calc_engine_python)} --version | head -n 1", env=env)
            if calc_engine_python
            else None,
        },
    }


def _expected_status_only_host_bootstrap_result(
    packet_id: str,
    *,
    minimal_mcp: dict[str, object],
    expected_minimal_mcp: str,
    expected_deferred_ops_decision: str,
    expected_output_artifact: str,
    expected_git: dict[str, object],
    expected_toolchains: dict[str, object],
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "host_container_root": str(PurePosixPath(_wsl_repo_root()).parent),
        "implementation_root": _wsl_repo_root(),
        "git": expected_git,
        "toolchains": expected_toolchains,
        "minimal_mcp": minimal_mcp,
        "hold_boundary": {
            "packet_id": "status-only",
            "minimal_mcp": expected_minimal_mcp,
            "minimal_mcp_detail": minimal_mcp,
            "deferred_ops": "UNAVAILABLE",
            "deferred_ops_decision": expected_deferred_ops_decision,
            "outputs": {},
        },
        "output_artifact": expected_output_artifact,
    }


def _wsl_repo_root() -> str:
    lines = subprocess.check_output(["bash", "-lc", "pwd -P"], cwd=REPO_ROOT, text=True).replace("\r\n", "\n").split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    assert len(lines) == 1
    assert lines[0] == lines[0].strip()
    return lines[0]


def _run_json(command: list[str], *, env: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


@pytest.fixture
def fake_unmanaged_trio():
    server_process: subprocess.Popen[str] | None = None
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(
        *,
        workspace_root: str | None = None,
        readme_preview: str | None = None,
        read_text_file_error: str | None = None,
    ) -> dict[str, str]:
        nonlocal server_process
        resolved_workspace_root = workspace_root or _wsl_repo_root()
        resolved_readme_preview = readme_preview or README_PREVIEW
        resolved_read_text_file_error = read_text_file_error
        server_script = f"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WORKSPACE_ROOT = {json.dumps(resolved_workspace_root)}
README_PREVIEW = {json.dumps(resolved_readme_preview)}
READ_TEXT_FILE_ERROR = {resolved_read_text_file_error!r}

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
            params = payload.get('params', {{}})
            tool_name = params.get('name')
            if tool_name == 'list_roots':
                result = {{'structuredContent': {{'workspace': WORKSPACE_ROOT}}}}
            elif tool_name == 'read_text_file':
                if READ_TEXT_FILE_ERROR is not None:
                    result = {{'isError': True, 'content': [{{'text': READ_TEXT_FILE_ERROR}}]}}
                else:
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
        port_line = server_process.stdout.readline().replace("\r\n", "\n")
        assert port_line.endswith("\n")
        port = port_line[:-1]
        assert port == port.strip()
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
        return _base_env(port, port, port)

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


@pytest.fixture
def fake_unmanaged_trio_powershell():
    servers: list[ThreadingHTTPServer] = []
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(*, workspace_root: str | None = None, readme_preview: str | None = None) -> dict[str, str]:
        resolved_workspace_root = workspace_root or str(REPO_ROOT.resolve())
        resolved_readme_preview = readme_preview or README_PREVIEW

        def handle_request(payload: dict[str, object], method: str) -> dict[str, object]:
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
            return {"isError": True, "content": [{"text": f"unexpected method {method}"}]}

        for _ in range(3):
            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
            server.handle_request = handle_request
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            servers.append(server)

        fs_port, db_port, jobs_port = tuple(str(server.server_address[1]) for server in servers)
        env_lines = []
        if original_env_dev is not None:
            env_lines.append(original_env_dev.rstrip("\n"))
        env_lines.extend(
            [
                f"APEX_DEV_MCP_FS_PORT={fs_port}",
                f"APEX_DEV_MCP_DB_PORT={db_port}",
                f"APEX_DEV_MCP_JOBS_PORT={jobs_port}",
            ]
        )
        ENV_DEV_FILE.write_text("\n".join(line for line in env_lines if line) + "\n", encoding="utf-8")
        return _base_env(fs_port, db_port, jobs_port)

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
@pytest.mark.parametrize("mode", ["managed", "adopted"])
def test_powershell_status_downgrades_stale_state_to_not_running(mode: str) -> None:
    _write_powershell_state(mode)

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "status"],
        env=_base_env(),
    )

    assert result == _expected_stale_powershell_status(mode)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_status_reports_not_running_when_no_state_and_no_live_trio() -> None:
    with _hide_repo_env_file():
        result = _run_json(
            ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "status"],
            env=_base_env(),
        )

    assert result == {"status": "not-running"}


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
@pytest.mark.parametrize("mode", ["managed", "adopted"])
def test_bash_status_downgrades_stale_state_to_not_running(mode: str) -> None:
    _write_bash_state(mode)

    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "status"],
        env=_base_env(),
    )

    assert result == _expected_stale_bash_minimal_mcp(mode)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_status_reports_not_running_when_no_state_and_no_live_trio() -> None:
    with _hide_repo_env_file():
        result = _run_json(
            ["bash", "tools/ai/run-minimal-mcp-trio.sh", "status"],
            env=_base_env(),
        )

    assert result == {"status": "not-running"}


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_status_reports_unmanaged_running_when_live_trio_exists(fake_unmanaged_trio_powershell) -> None:
    env = fake_unmanaged_trio_powershell()

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_powershell_status(env)


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_status_keeps_foreign_live_trio_unmanaged(fake_unmanaged_trio_powershell) -> None:
    foreign_root = str((REPO_ROOT / ".." / "foreign-workspace-root").resolve())
    env = fake_unmanaged_trio_powershell(workspace_root=foreign_root)

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_powershell_status(env)
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_status_keeps_readme_mismatched_live_trio_unmanaged(fake_unmanaged_trio_powershell) -> None:
    env = fake_unmanaged_trio_powershell(readme_preview="foreign README preview")

    result = _run_json(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_powershell_status(env)
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_status_reports_unmanaged_running_when_live_trio_exists(fake_unmanaged_trio) -> None:
    env = fake_unmanaged_trio()

    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_bash_status(env)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_status_keeps_foreign_live_trio_unmanaged(fake_unmanaged_trio) -> None:
    foreign_root = str(PurePosixPath(_wsl_repo_root()).parent / "foreign-workspace-root")
    env = fake_unmanaged_trio(workspace_root=foreign_root)

    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_bash_status(env)
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_status_keeps_readme_mismatched_live_trio_unmanaged(fake_unmanaged_trio) -> None:
    env = fake_unmanaged_trio(readme_preview="foreign README preview")

    result = _run_json(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "status"],
        env=env,
    )

    assert result == _expected_unmanaged_bash_status(env)
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_treats_stale_managed_state_as_not_running() -> None:
    packet_id = "stale-managed-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    _write_bash_state("managed")
    env = _base_env()
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_stale_bash_minimal_mcp("managed")

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="NOT_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_not_running",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_treats_stale_adopted_state_as_not_running() -> None:
    packet_id = "stale-adopted-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    _write_bash_state("adopted")
    env = _base_env()
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_stale_bash_minimal_mcp("adopted")

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="NOT_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_not_running",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_reports_not_running_when_no_state_and_no_live_trio() -> None:
    packet_id = "no-state-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    env = _base_env()
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()

    with _hide_repo_env_file():
        result = _run_json(
            ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
            env=env,
        )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp={"status": "not-running"},
        expected_minimal_mcp="NOT_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_not_running",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_reports_unmanaged_running_with_owned_probe(fake_unmanaged_trio) -> None:
    packet_id = "unmanaged-owned-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    env = fake_unmanaged_trio()
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_unmanaged_bash_minimal_mcp(
        env,
        {
            "status": "owned",
            "workspace_root": _wsl_repo_root(),
            "expected_workspace_root": _wsl_repo_root(),
            "readme_preview": README_PREVIEW,
            "expected_readme_preview": README_PREVIEW,
        },
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="UNMANAGED_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_unmanaged",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_reports_unmanaged_running_with_mismatched_ownership_probe(fake_unmanaged_trio) -> None:
    packet_id = "unmanaged-mismatched-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    env = fake_unmanaged_trio(workspace_root=str(PurePosixPath(_wsl_repo_root()).parent))
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_unmanaged_bash_minimal_mcp(
        env,
        {
            "status": "adoption-refused",
            "workspace_root": str(PurePosixPath(_wsl_repo_root()).parent),
            "expected_workspace_root": _wsl_repo_root(),
            "readme_preview": README_PREVIEW,
            "expected_readme_preview": README_PREVIEW,
            "reason": "workspace-root-mismatch",
        },
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="UNMANAGED_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_unmanaged",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_reports_unmanaged_running_with_readme_mismatched_ownership_probe(fake_unmanaged_trio) -> None:
    packet_id = "unmanaged-readme-mismatched-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    env = fake_unmanaged_trio(readme_preview="foreign README preview")
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_unmanaged_bash_minimal_mcp(
        env,
        {
            "status": "adoption-refused",
            "workspace_root": _wsl_repo_root(),
            "expected_workspace_root": _wsl_repo_root(),
            "readme_preview": "foreign README preview",
            "expected_readme_preview": README_PREVIEW,
            "reason": "readme-preview-mismatch",
        },
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="UNMANAGED_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_unmanaged",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_reports_unmanaged_running_with_ownership_probe_failure(fake_unmanaged_trio) -> None:
    packet_id = "unmanaged-ownership-probe-failed-host-bootstrap-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    env = fake_unmanaged_trio(read_text_file_error="forced read_text_file failure")
    expected_toolchains = _current_bash_toolchains_metadata(env)
    expected_git = _current_repo_git_metadata()
    expected_minimal_mcp = _expected_unmanaged_bash_minimal_mcp(
        env,
        {
            "status": "adoption-refused",
            "reason": "fs-ownership-probe-failed",
            "expected_workspace_root": _wsl_repo_root(),
            "detail": "forced read_text_file failure",
        },
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=env,
    )

    assert result == _expected_status_only_host_bootstrap_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        expected_minimal_mcp="UNMANAGED_RUNNING",
        expected_deferred_ops_decision="minimal_mcp_unmanaged",
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_host_bootstrap_artifact(packet_id)