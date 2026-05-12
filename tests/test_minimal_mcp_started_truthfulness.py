from __future__ import annotations

import json
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
PS_STATE_FILE = STATE_DIR / "minimal-mcp-trio.json"
BASH_STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
ENV_TEMPLATE_FILE = REPO_ROOT / ".env.dev.template"


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


def _expected_started_result() -> dict[str, object]:
    return {"status": "started"}


def _expected_start_refused_missing_entrypoints(*missing_entrypoints: str) -> dict[str, object]:
    return {
        "status": "start-refused",
        "reason": "missing-service-entrypoints",
        "missing_entrypoints": list(missing_entrypoints),
    }


def _expected_start_refused_services_not_ready() -> dict[str, object]:
    return {
        "status": "start-refused",
        "reason": "services-not-ready",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "fs_ready": False,
        "db_ready": False,
        "jobs_ready": False,
    }


def _invalid_packet_id_error(packet_id: str) -> str:
    return f"Invalid packet id '{packet_id}'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$."


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _contains_invalid_packet_id_message(text: str, packet_id: str) -> bool:
    normalized = _strip_ansi(text).replace("\r", "")
    return (
        f"Invalid packet id '{packet_id}'. Packet ids must match" in normalized
        and "^[A-Za-z0-9][A-Za-z0-9._-]*$." in normalized
    )


def _allocate_ports(count: int) -> list[str]:
    sockets: list[socket.socket] = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [str(sock.getsockname()[1]) for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


def _normalized_powershell_managed_state(state: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(state))
    normalized["started_at"] = "<generated>"
    for process in normalized["processes"]:
        process["pid"] = "<generated>"
    return normalized


def _expected_powershell_managed_state(packet_id: str, *, fs_port: str, db_port: str, jobs_port: str) -> dict[str, object]:
    return {
        "started_at": "<generated>",
        "packet_id": packet_id,
        "mode": "managed",
        "processes": [
            {"name": "apex-fs", "pid": "<generated>", "log": str(STATE_DIR / "logs" / "apex-fs.log")},
            {"name": "apex-db", "pid": "<generated>", "log": str(STATE_DIR / "logs" / "apex-db.log")},
            {"name": "apex-jobs", "pid": "<generated>", "log": str(STATE_DIR / "logs" / "apex-jobs.log")},
        ],
        "endpoints": {
            "fs": f"http://127.0.0.1:{fs_port}/mcp",
            "db": f"http://127.0.0.1:{db_port}/mcp",
            "jobs": f"http://127.0.0.1:{jobs_port}/mcp",
        },
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


def _normalized_bash_managed_state(state: dict[str, str]) -> dict[str, str]:
    normalized = dict(state)
    normalized["STARTED_AT"] = "<generated>"
    normalized["FS_PID"] = "<generated>"
    normalized["DB_PID"] = "<generated>"
    normalized["JOBS_PID"] = "<generated>"
    return normalized


def _expected_bash_managed_state(packet_id: str) -> dict[str, str]:
    return _expected_bash_managed_state_with_ports(packet_id, fs_port="8810", db_port="8811", jobs_port="8812")


def _expected_bash_managed_state_with_ports(packet_id: str, *, fs_port: str, db_port: str, jobs_port: str) -> dict[str, str]:
    wsl_root = subprocess.check_output(["bash", "-lc", "pwd -P"], cwd=REPO_ROOT, text=True).strip()
    return {
        "STARTED_AT": "<generated>",
        "PACKET_ID": packet_id,
        "MODE": "managed",
        "FS_PID": "<generated>",
        "DB_PID": "<generated>",
        "JOBS_PID": "<generated>",
        "LEDGER_PATH": f"{wsl_root}/.apex-data/apex-jobs-ledger.json",
        "FS_ENDPOINT": f"http://127.0.0.1:{fs_port}/mcp",
        "DB_ENDPOINT": f"http://127.0.0.1:{db_port}/mcp",
        "JOBS_ENDPOINT": f"http://127.0.0.1:{jobs_port}/mcp",
    }


def _write_fake_bash_node(shim_dir: Path) -> Path:
    node_path = shim_dir / "node"
    node_path.write_text("#!/usr/bin/env bash\nsleep 30\n", encoding="utf-8", newline="\n")
    node_path.chmod(node_path.stat().st_mode | stat.S_IEXEC)
    return node_path


def _write_fake_windows_node(shim_dir: Path) -> Path:
    node_path = shim_dir / "node.cmd"
    node_path.write_text("@echo off\r\ntimeout /t 30 /nobreak >nul\r\n", encoding="utf-8", newline="")
    return node_path


def _write_ready_windows_node(shim_dir: Path) -> Path:
    server_script = shim_dir / "fake_mcp_ready_server.py"
    server_script.write_text(
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "import json\n"
        "import os\n"
        "\n"
        "class ReusableHTTPServer(HTTPServer):\n"
        "    allow_reuse_address = True\n"
        "\n"
        "class Handler(BaseHTTPRequestHandler):\n"
        "    def do_POST(self):\n"
        "        response = {\"jsonrpc\": \"2.0\", \"id\": 0, \"result\": {\"protocolVersion\": \"2025-03-26\", \"capabilities\": {}, \"serverInfo\": {\"name\": \"fake-mcp\", \"version\": \"0.1.0\"}}}\n"
        "        body = json.dumps(response).encode('utf-8')\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type', 'application/json')\n"
        "        self.send_header('Content-Length', str(len(body)))\n"
        "        self.end_headers()\n"
        "        self.wfile.write(body)\n"
        "    def log_message(self, format, *args):\n"
        "        return\n"
        "\n"
        "port = int(os.environ['APEX_MCP_HTTP_PORT'])\n"
        "ReusableHTTPServer(('127.0.0.1', port), Handler).serve_forever()\n",
        encoding="utf-8",
        newline="\n",
    )

    node_path = shim_dir / "node.cmd"
    node_path.write_text(
        f"@echo off\r\n\"{sys.executable}\" \"{server_script}\"\r\n",
        encoding="utf-8",
        newline="",
    )
    return node_path


def _write_ready_bash_node(shim_dir: Path) -> Path:
    node_path = shim_dir / "node"
    node_path.write_text(
        "#!/usr/bin/env bash\n"
        "exec python3 - <<'PY'\n"
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "import json\n"
        "import os\n"
        "\n"
        "class ReusableHTTPServer(HTTPServer):\n"
        "    allow_reuse_address = True\n"
        "\n"
        "class Handler(BaseHTTPRequestHandler):\n"
        "    def do_POST(self):\n"
        "        response = {\"jsonrpc\": \"2.0\", \"id\": 0, \"result\": {\"protocolVersion\": \"2025-03-26\", \"capabilities\": {}, \"serverInfo\": {\"name\": \"fake-mcp\", \"version\": \"0.1.0\"}}}\n"
        "        body = json.dumps(response).encode('utf-8')\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type', 'application/json')\n"
        "        self.send_header('Content-Length', str(len(body)))\n"
        "        self.end_headers()\n"
        "        self.wfile.write(body)\n"
        "    def log_message(self, format, *args):\n"
        "        return\n"
        "\n"
        "port = int(os.environ['APEX_MCP_HTTP_PORT'])\n"
        "ReusableHTTPServer(('127.0.0.1', port), Handler).serve_forever()\n"
        "PY\n",
        encoding="utf-8",
        newline="\n",
    )
    node_path.chmod(node_path.stat().st_mode | stat.S_IEXEC)
    return node_path


@contextmanager
def _temporarily_remove_entrypoint(relative_path: str):
    entrypoint = REPO_ROOT / relative_path
    backup_path = entrypoint.with_suffix(entrypoint.suffix + ".bak-test")
    entrypoint.rename(backup_path)
    try:
        yield
    finally:
        if backup_path.exists():
            backup_path.rename(entrypoint)


@contextmanager
def _temporarily_hide_env_files():
    backups: list[tuple[Path, Path]] = []
    for env_file in (ENV_DEV_FILE, ENV_TEMPLATE_FILE):
        if env_file.exists():
            backup_path = env_file.with_suffix(env_file.suffix + ".bak-test")
            env_file.rename(backup_path)
            backups.append((env_file, backup_path))

    try:
        yield
    finally:
        for env_file, backup_path in reversed(backups):
            if backup_path.exists():
                backup_path.rename(env_file)


def _cleanup_bash_processes() -> None:
    if not BASH_STATE_FILE.exists():
        return

    lines = BASH_STATE_FILE.read_text(encoding="utf-8").splitlines()
    pids = [line.split("=", 1)[1].strip().strip("'") for line in lines if line.startswith(("FS_PID=", "DB_PID=", "JOBS_PID="))]
    for pid in pids:
        if not pid:
            continue
        subprocess.run(["bash", "-lc", f"kill {pid} >/dev/null 2>&1 || true"], cwd=REPO_ROOT, check=False)


def _cleanup_powershell_processes() -> None:
    if not PS_STATE_FILE.exists():
        return

    payload = json.loads(PS_STATE_FILE.read_text(encoding="utf-8"))
    for process in payload.get("processes", []):
        pid = process.get("pid")
        if not pid:
            continue
        subprocess.run(
            ["pwsh", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )


@pytest.fixture(autouse=True)
def _clean_state_files() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()
    yield
    _cleanup_powershell_processes()
    _cleanup_bash_processes()
    for path in (PS_STATE_FILE, BASH_STATE_FILE):
        if path.exists():
            path.unlink()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_reports_started_and_persists_managed_state(tmp_path: Path) -> None:
    shim_dir = tmp_path / "pwsh-shim"
    shim_dir.mkdir()
    _write_ready_windows_node(shim_dir)

    fs_port, db_port, jobs_port = _allocate_ports(3)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    env["APEX_DEV_MCP_FS_PORT"] = fs_port
    env["APEX_DEV_MCP_DB_PORT"] = db_port
    env["APEX_DEV_MCP_JOBS_PORT"] = jobs_port

    with _temporarily_hide_env_files():
        result = _run_json(
            ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", "powershell-started-up-test"],
            env=env,
        )

    state = json.loads(PS_STATE_FILE.read_text(encoding="utf-8"))
    assert result == _expected_started_result()
    assert _normalized_powershell_managed_state(state) == _expected_powershell_managed_state(
        "powershell-started-up-test",
        fs_port=fs_port,
        db_port=db_port,
        jobs_port=jobs_port,
    )


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_refuses_managed_start_when_services_do_not_become_ready(tmp_path: Path) -> None:
    shim_dir = tmp_path / "pwsh-timeout-shim"
    shim_dir.mkdir()
    _write_fake_windows_node(shim_dir)

    fs_port, db_port, jobs_port = _allocate_ports(3)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    env["APEX_DEV_MCP_FS_PORT"] = fs_port
    env["APEX_DEV_MCP_DB_PORT"] = db_port
    env["APEX_DEV_MCP_JOBS_PORT"] = jobs_port
    env["APEX_MINIMAL_MCP_READY_ATTEMPTS"] = "1"
    env["APEX_MINIMAL_MCP_READY_INTERVAL_SECONDS"] = "0.01"

    with _temporarily_hide_env_files():
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", "powershell-services-not-ready-test"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert result.returncode == 1
    assert json.loads(result.stdout) == _expected_start_refused_services_not_ready()
    assert result.stderr == ""
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_rejects_invalid_packet_id_before_writing_state(tmp_path: Path) -> None:
    shim_dir = tmp_path / "pwsh-invalid-packet-shim"
    shim_dir.mkdir()
    _write_ready_windows_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", "bad packet id"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert _contains_invalid_packet_id_message(result.stderr, "bad packet id")
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh is required for PowerShell wrapper tests")
def test_powershell_up_refuses_managed_start_when_service_entrypoint_is_missing(tmp_path: Path) -> None:
    shim_dir = tmp_path / "pwsh-shim"
    shim_dir.mkdir()
    _write_fake_windows_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    env["APEX_DEV_MCP_FS_PORT"] = "18813"
    env["APEX_DEV_MCP_DB_PORT"] = "18814"
    env["APEX_DEV_MCP_JOBS_PORT"] = "18815"

    with _temporarily_hide_env_files():
        with _temporarily_remove_entrypoint("services/mcp/apex-fs/build/http.js"):
            result = subprocess.run(
                ["pwsh", "-NoProfile", "-File", "tools/ai/run-minimal-mcp-trio.ps1", "-Action", "up", "-PacketId", "powershell-missing-entrypoint-test"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

    assert result.returncode == 1
    assert json.loads(result.stdout) == _expected_start_refused_missing_entrypoints("services/mcp/apex-fs/build/http.js")
    assert result.stderr == ""
    assert not PS_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_reports_started_and_persists_managed_state(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bash-shim"
    shim_dir.mkdir()
    _write_ready_bash_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"

    with _temporarily_hide_env_files():
        result = _run_json(
            ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", "bash-started-up-test"],
            env=env,
        )

    state = _read_bash_state_values()
    assert result == _expected_started_result()
    assert _normalized_bash_managed_state(state) == _expected_bash_managed_state("bash-started-up-test")


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_refuses_managed_start_when_services_do_not_become_ready(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bash-timeout-shim"
    shim_dir.mkdir()
    _write_fake_bash_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"
    env["APEX_MINIMAL_MCP_READY_ATTEMPTS"] = "1"
    env["APEX_MINIMAL_MCP_READY_INTERVAL_SECONDS"] = "0.01"

    with _temporarily_hide_env_files():
        result = subprocess.run(
            ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", "bash-services-not-ready-test"],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )

    assert result.returncode == 1
    assert json.loads(result.stdout) == _expected_start_refused_services_not_ready()
    assert result.stderr == ""
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_rejects_invalid_packet_id_before_writing_state(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bash-invalid-packet-shim"
    shim_dir.mkdir()
    _write_ready_bash_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", "bad packet id"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == _invalid_packet_id_error("bad packet id")
    assert not BASH_STATE_FILE.exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_up_refuses_managed_start_when_service_entrypoint_is_missing(tmp_path: Path) -> None:
    shim_dir = tmp_path / "bash-shim"
    shim_dir.mkdir()
    _write_fake_bash_node(shim_dir)

    env = os.environ.copy()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"

    with _temporarily_hide_env_files():
        with _temporarily_remove_entrypoint("services/mcp/apex-fs/build/http.js"):
            result = subprocess.run(
                ["bash", "tools/ai/run-minimal-mcp-trio.sh", "up", "bash-missing-entrypoint-test"],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

    assert result.returncode == 1
    assert json.loads(result.stdout) == _expected_start_refused_missing_entrypoints("services/mcp/apex-fs/build/http.js")
    assert result.stderr == ""
    assert not BASH_STATE_FILE.exists()