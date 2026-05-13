from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")
_BASH_FAKE_TOOLS = ["read_text_file", "query", "promote_packet", "start_run", "end_run"]


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


def _bash_repo_python() -> str:
    completed = subprocess.run(
        ["bash", "-lc", "source tools/shell/common.sh; get_apex_preferred_python"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _bash_repo_root() -> str:
    completed = subprocess.run(
        ["bash", "-lc", "source tools/shell/common.sh; get_apex_repo_root"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _expected_verify_command(argv: list[str]) -> str:
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
    command_endpoints: tuple[str, str, str] | None = None,
) -> dict[str, object]:
    bash_output_path = f"{_bash_repo_root()}/tests/canary/mcp-contract/actual/{output_path.name}"
    command = [
        _bash_repo_python(),
        "tools/ai/verify_minimal_mcp_trio.py",
        "--packet-id",
        packet_id,
        "--output",
        bash_output_path,
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
    return {
        "packet_id": packet_id,
        "command": _expected_verify_command(command),
        "endpoints": {"fs": fs_url, "db": db_url, "jobs": jobs_url},
        "checks": {
            "fs_tools": {"status": "pass", "tools": _BASH_FAKE_TOOLS},
            "fs_read": {"status": "pass", "preview": README_PREVIEW},
            "db_tools": {"status": "pass", "tools": _BASH_FAKE_TOOLS},
            "db_query": {"status": "pass", "result": {"rowCount": 1, "rows": [{"ok": 1}]}} ,
            "jobs_tools": {"status": "pass", "tools": _BASH_FAKE_TOOLS},
            "jobs_promote_guard": _expected_jobs_promote_guard_check(packet_id),
            "jobs_start_run": {"status": "pass", "run": {"run_id": "run-123", "packet_id": packet_id}},
            "jobs_end_run": {"status": "pass", "run": {"run_id": "run-123", "status": "success"}},
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


def _write_state(packet_id: str) -> None:
    lines = [
        "STARTED_AT='2026-05-11T00:00:00Z'",
        f"PACKET_ID='{packet_id}'",
        "MODE='adopted'",
        f"LEDGER_PATH='{(REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json').as_posix()}'",
        "FS_PID=''",
        "DB_PID=''",
        "JOBS_PID=''",
    ]
    with STATE_FILE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_state_with_endpoints(packet_id: str, *, fs_url: str, db_url: str, jobs_url: str) -> None:
    lines = [
        "STARTED_AT='2026-05-11T00:00:00Z'",
        f"PACKET_ID='{packet_id}'",
        "MODE='adopted'",
        f"LEDGER_PATH='{(REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json').as_posix()}'",
        "FS_PID=''",
        "DB_PID=''",
        "JOBS_PID=''",
        f"FS_ENDPOINT='{fs_url}'",
        f"DB_ENDPOINT='{db_url}'",
        f"JOBS_ENDPOINT='{jobs_url}'",
    ]
    with STATE_FILE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


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
    server_process: subprocess.Popen[str] | None = None
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start() -> None:
        nonlocal server_process
        server_script = f"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

README_PREVIEW = {json.dumps(README_PREVIEW)}

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
                'serverInfo': {{'name': 'fake-bash-minimal-mcp-verify-surface', 'version': '0.1.0'}},
            }}
        elif method == 'tools/list':
            result = {{
                'tools': [
                    {{'name': 'read_text_file'}},
                    {{'name': 'query'}},
                    {{'name': 'promote_packet'}},
                    {{'name': 'start_run'}},
                    {{'name': 'end_run'}},
                ]
            }}
        elif method == 'tools/call':
            params = payload.get('params', {{}})
            tool_name = params.get('name')
            arguments = params.get('arguments', {{}})
            if tool_name == 'read_text_file':
                result = {{'structuredContent': {{'content': README_PREVIEW}}}}
            elif tool_name == 'query':
                result = {{'structuredContent': {{'rowCount': 1, 'rows': [{{'ok': 1}}]}}}}
            elif tool_name == 'promote_packet':
                result = {{
                    'isError': True,
                    'content': [{{'text': 'no successful env=host run is on record for that packet_id'}}],
                }}
            elif tool_name == 'start_run':
                result = {{'structuredContent': {{'run_id': 'run-123', 'packet_id': arguments.get('packet_id')}}}}
            elif tool_name == 'end_run':
                result = {{'structuredContent': {{'run_id': arguments.get('run_id'), 'status': arguments.get('status')}}}}
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
            raise RuntimeError(f"Failed to start fake bash minimal-mcp verify server: {stderr}")

        url = f"http://127.0.0.1:{port}/mcp"
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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_verify_uses_state_packet_id_when_not_provided(fake_trio) -> None:
    state_packet_id = "state-bash-minimal-mcp-verify-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    _write_state(state_packet_id)
    output_path = _artifact_path(state_packet_id)

    payload = _run_json(["bash", "tools/ai/run-minimal-mcp-trio.sh", "verify"])

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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_verify_prefers_explicit_packet_id_over_state(fake_trio) -> None:
    state_packet_id = "state-bash-packet-should-not-win"
    explicit_packet_id = "explicit-bash-minimal-mcp-verify-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()
    _write_state(state_packet_id)
    output_path = _artifact_path(explicit_packet_id)

    payload = _run_json(["bash", "tools/ai/run-minimal-mcp-trio.sh", "verify", explicit_packet_id])

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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_verify_preserves_fail_json_when_verify_artifact_path_is_blocked(fake_trio) -> None:
    packet_id = "bash-minimal-mcp-verify-blocked-artifact-test"
    fake_trio()
    fs_url, db_url, jobs_url = _read_env_urls()

    output_path = _artifact_path(packet_id)
    output_path.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["bash", "tools/ai/run-minimal-mcp-trio.sh", "verify", packet_id],
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
    expected_output_path = str(output_path).lower().replace("\\", "/")
    if re.match(r"^[a-z]:/", expected_output_path):
        expected_output_path = f"/mnt/{expected_output_path[0]}{expected_output_path[2:]}"
    assert expected_output_path in normalized_error_text
    assert output_path.name.lower() in normalized_error_text or "already exists" in normalized_error_text
    assert re.search(r"directory|exists|permission denied", error_text)
    assert result.stderr == ""

    output_path.rmdir()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_bash_verify_prefers_state_endpoints_over_inherited_env_urls(fake_trio) -> None:
    packet_id = "bash-minimal-mcp-verify-state-endpoints-win"
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
    _write_state_with_endpoints(packet_id, fs_url=fs_url, db_url=db_url, jobs_url=jobs_url)

    payload = _run_json(["bash", "tools/ai/run-minimal-mcp-trio.sh", "verify"])

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