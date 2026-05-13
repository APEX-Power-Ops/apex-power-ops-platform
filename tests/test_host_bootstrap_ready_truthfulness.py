from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import textwrap
from pathlib import Path, PurePosixPath

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
STATE_DIR = REPO_ROOT / ".tmp" / "ai-workflow"
BASH_STATE_FILE = STATE_DIR / "minimal-mcp-trio.env"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")
HOST_BOOTSTRAP_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "host-bootstrap-status" / "actual"
DEFERRED_OPS_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "deferred-ops-view-counts" / "actual"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"


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


def _write_adopted_state(endpoint: str) -> None:
    BASH_STATE_FILE.write_text(
        "\n".join(
            [
                "STARTED_AT='2026-05-11T00:00:00Z'",
                "PACKET_ID='host-bootstrap-ready-state'",
                "MODE='adopted'",
                "FS_PID=''",
                "DB_PID=''",
                "JOBS_PID=''",
                f"LEDGER_PATH='{(REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json').as_posix()}'",
                f"FS_ENDPOINT='{endpoint}'",
                f"DB_ENDPOINT='{endpoint}'",
                f"JOBS_ENDPOINT='{endpoint}'",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def _write_managed_state(endpoint: str, pid: str) -> None:
    BASH_STATE_FILE.write_text(
        "\n".join(
            [
                "STARTED_AT='2026-05-11T00:00:00Z'",
                "PACKET_ID='host-bootstrap-managed-ready-state'",
                "MODE='managed'",
                f"FS_PID='{pid}'",
                f"DB_PID='{pid}'",
                f"JOBS_PID='{pid}'",
                f"LEDGER_PATH='{(REPO_ROOT / '.apex-data' / 'apex-jobs-ledger.json').as_posix()}'",
                f"FS_ENDPOINT='{endpoint}'",
                f"DB_ENDPOINT='{endpoint}'",
                f"JOBS_ENDPOINT='{endpoint}'",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def _start_bash_sleep_process() -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        ["bash", "-lc", "printf '%s\n' \"$$\"; sleep 180"],
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


def _cleanup_artifacts(packet_id: str) -> None:
    for artifact in (
        HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json",
        DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
        MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
    ):
        if artifact.exists():
            artifact.unlink()


def _expected_minimal_trio_verifier_payload(packet_id: str, *, endpoint: str, output_path: str) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "command": (
            f"/usr/bin/python3 tools/ai/verify_minimal_mcp_trio.py --packet-id {packet_id} "
            f"--output '{output_path}' "
            f"--fs-url {endpoint} --db-url {endpoint} --jobs-url {endpoint}"
        ),
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
    result: str,
    decision: str,
    deferred_view_counts: dict[str, object],
    reopen_candidates: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "packet_id": packet_id,
        "repo_root": _wsl_repo_root(),
        "checks": {
            "db_connection": {
                "status": "pass",
                "source": "argument:db-url",
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


def _assert_hold_boundary_child_artifacts(
    packet_id: str,
    hold_boundary: dict[str, object],
    *,
    endpoint: str,
    expected_hold_payload: dict[str, object],
) -> None:
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    expected_minimal_output = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "mcp-contract"
        / "actual"
        / f"verify-minimal-mcp-trio-{packet_id}.json"
    )
    expected_hold_output = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "deferred-ops-view-counts"
        / "actual"
        / f"deferred-ops-view-counts-{packet_id}.json"
    )

    outputs = hold_boundary["outputs"]
    assert outputs == {
        "minimal_mcp": expected_minimal_output,
        "deferred_ops": expected_hold_output,
    }
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
        output_path=expected_minimal_output,
    )
    assert hold_payload == expected_hold_payload


def _current_repo_git_metadata(*, created_before_snapshot: tuple[Path, ...] = ()) -> dict[str, object]:
    repo_root = _wsl_repo_root()
    output = subprocess.check_output(["bash", "-lc", f"git -C {shlex.quote(repo_root)} status --porcelain"], text=True)
    status_count = 0 if not output else len(output.rstrip("\n").splitlines())
    status_count += sum(1 for path in created_before_snapshot if not path.exists())
    return {
        "head": subprocess.check_output(["bash", "-lc", f"git -C {shlex.quote(repo_root)} rev-parse HEAD"], text=True).strip(),
        "status_count": status_count,
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


def _expected_adopted_ready_minimal_mcp(endpoint: str) -> dict[str, object]:
    return {
        "status": "adopted-running",
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": "host-bootstrap-ready-state",
        "mode": "adopted",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "ledger_path": (REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json").as_posix(),
        "fs_endpoint": endpoint,
        "db_endpoint": endpoint,
        "jobs_endpoint": endpoint,
    }


def _expected_managed_ready_minimal_mcp(endpoint: str) -> dict[str, object]:
    return {
        "status": "managed-running",
        "started_at": "2026-05-11T00:00:00Z",
        "packet_id": "host-bootstrap-managed-ready-state",
        "mode": "managed",
        "fs_running": True,
        "db_running": True,
        "jobs_running": True,
        "ledger_path": (REPO_ROOT / ".apex-data" / "apex-jobs-ledger.json").as_posix(),
        "fs_endpoint": endpoint,
        "db_endpoint": endpoint,
        "jobs_endpoint": endpoint,
    }


def _expected_hold_boundary_result(packet_id: str, *, deferred_result: str, deferred_decision: str) -> dict[str, object]:
    repo_root = _wsl_repo_root()
    return {
        "packet_id": packet_id,
        "minimal_mcp": "PASS",
        "deferred_ops": deferred_result,
        "deferred_ops_decision": deferred_decision,
        "outputs": {
            "minimal_mcp": str(
                PurePosixPath(repo_root)
                / "tests"
                / "canary"
                / "mcp-contract"
                / "actual"
                / f"verify-minimal-mcp-trio-{packet_id}.json"
            ),
            "deferred_ops": str(
                PurePosixPath(repo_root)
                / "tests"
                / "canary"
                / "deferred-ops-view-counts"
                / "actual"
                / f"deferred-ops-view-counts-{packet_id}.json"
            ),
        },
    }


def _expected_host_bootstrap_ready_result(
    packet_id: str,
    *,
    minimal_mcp: dict[str, object],
    hold_boundary: dict[str, object],
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
        "hold_boundary": hold_boundary,
        "output_artifact": expected_output_artifact,
    }


@pytest.fixture(autouse=True)
def _clean_state_file() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if BASH_STATE_FILE.exists():
        BASH_STATE_FILE.unlink()
    yield
    if BASH_STATE_FILE.exists():
        BASH_STATE_FILE.unlink()


@pytest.fixture
def fake_ready_host_bootstrap_surface():
    server_process: subprocess.Popen[str] | None = None
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(
        *,
        deferred_rows: list[dict[str, object]] | None = None,
        deferred_error: str | None = None,
    ) -> dict[str, object]:
        nonlocal server_process
        deferred_rows_json = json.dumps(deferred_rows or [])
        deferred_error_literal = repr(deferred_error)
        server_script = textwrap.dedent(f"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

README_PREVIEW = {json.dumps(README_PREVIEW)}
DEFERRED_ROWS = {deferred_rows_json}
DEFERRED_ERROR = {deferred_error_literal}

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
                'serverInfo': {{'name': 'fake-ready-host-bootstrap-surface', 'version': '0.1.0'}},
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
                sql = arguments.get('sql', '')
                if 'select 1 as ok' in sql:
                    result = {{'structuredContent': {{'rowCount': 1, 'rows': [{{'ok': 1}}]}}}}
                elif DEFERRED_ERROR is not None:
                    result = {{'isError': True, 'content': [{{'text': DEFERRED_ERROR}}]}}
                else:
                    result = {{'structuredContent': DEFERRED_ROWS}}
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
""")

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
            raise RuntimeError(f"Failed to start fake ready host-bootstrap MCP server: {stderr}")

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
        return {"env": os.environ.copy(), "url": url}

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
def test_host_bootstrap_delegates_to_hold_boundary_when_minimal_trio_is_ready(fake_ready_host_bootstrap_surface) -> None:
    packet_id = "host-bootstrap-ready-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    _write_adopted_state(surface["url"])
    expected_git = _current_repo_git_metadata(
        created_before_snapshot=(
            MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
            DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
        )
    )
    expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
    expected_minimal_mcp = _expected_adopted_ready_minimal_mcp(surface["url"])
    expected_hold_boundary = _expected_hold_boundary_result(
        packet_id,
        deferred_result="HOLD",
        deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=surface["env"],
    )

    assert result == _expected_host_bootstrap_ready_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        hold_boundary=expected_hold_boundary,
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result["hold_boundary"],
        endpoint=surface["url"],
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=surface["url"],
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
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_delegates_to_hold_boundary_when_minimal_trio_is_managed_running(fake_ready_host_bootstrap_surface) -> None:
    packet_id = "host-bootstrap-managed-ready-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    process, pid = _start_bash_sleep_process()
    try:
        _write_managed_state(surface["url"], pid)
        expected_git = _current_repo_git_metadata(
            created_before_snapshot=(
                MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
                DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
            )
        )
        expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
        expected_minimal_mcp = _expected_managed_ready_minimal_mcp(surface["url"])
        expected_hold_boundary = _expected_hold_boundary_result(
            packet_id,
            deferred_result="HOLD",
            deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
        )

        result = _run_json(
            ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
            env=surface["env"],
        )

        assert result == _expected_host_bootstrap_ready_result(
            packet_id,
            minimal_mcp=expected_minimal_mcp,
            hold_boundary=expected_hold_boundary,
            expected_output_artifact=expected_output_artifact,
            expected_git=expected_git,
            expected_toolchains=expected_toolchains,
        )
        assert artifact.exists()
        _assert_hold_boundary_child_artifacts(
            packet_id,
            result["hold_boundary"],
            endpoint=surface["url"],
            expected_hold_payload=_expected_deferred_ops_child_payload(
                packet_id,
                endpoint=surface["url"],
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
        assert json.loads(artifact.read_text(encoding="utf-8")) == result
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_delegates_reopen_when_adopted_minimal_trio_has_live_deferred_rows(
    fake_ready_host_bootstrap_surface,
) -> None:
    packet_id = "host-bootstrap-ready-reopen-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 2},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    _write_adopted_state(surface["url"])
    expected_git = _current_repo_git_metadata(
        created_before_snapshot=(
            MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
            DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
        )
    )
    expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
    expected_minimal_mcp = _expected_adopted_ready_minimal_mcp(surface["url"])
    expected_hold_boundary = _expected_hold_boundary_result(
        packet_id,
        deferred_result="REOPEN",
        deferred_decision="One or more deferred Operations Visibility seams now have live rows.",
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=surface["env"],
    )

    assert result == _expected_host_bootstrap_ready_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        hold_boundary=expected_hold_boundary,
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result["hold_boundary"],
        endpoint=surface["url"],
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=surface["url"],
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
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_delegates_unavailable_when_adopted_minimal_trio_lacks_authoritative_views(
    fake_ready_host_bootstrap_surface,
) -> None:
    packet_id = "host-bootstrap-ready-unavailable-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_error='relation "public.v_resource_allocation" does not exist'
    )
    _write_adopted_state(surface["url"])
    expected_git = _current_repo_git_metadata(
        created_before_snapshot=(
            MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
            DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
        )
    )
    expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
    expected_minimal_mcp = _expected_adopted_ready_minimal_mcp(surface["url"])
    expected_hold_boundary = _expected_hold_boundary_result(
        packet_id,
        deferred_result="UNAVAILABLE",
        deferred_decision=(
            "Authoritative deferred view counts require apex-db to run against a live DSN such as "
            "SEAM_DATABASE_URL; the current database surface is not sufficient for this hold check."
        ),
    )

    result = _run_json(
        ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
        env=surface["env"],
    )

    assert result == _expected_host_bootstrap_ready_result(
        packet_id,
        minimal_mcp=expected_minimal_mcp,
        hold_boundary=expected_hold_boundary,
        expected_output_artifact=expected_output_artifact,
        expected_git=expected_git,
        expected_toolchains=expected_toolchains,
    )
    assert artifact.exists()
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result["hold_boundary"],
        endpoint=surface["url"],
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
            endpoint=surface["url"],
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
    assert json.loads(artifact.read_text(encoding="utf-8")) == result

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_delegates_reopen_when_managed_minimal_trio_has_live_deferred_rows(
    fake_ready_host_bootstrap_surface,
) -> None:
    packet_id = "host-bootstrap-managed-ready-reopen-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 2},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    process, pid = _start_bash_sleep_process()
    try:
        _write_managed_state(surface["url"], pid)
        expected_git = _current_repo_git_metadata(
            created_before_snapshot=(
                MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
                DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
            )
        )
        expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
        expected_minimal_mcp = _expected_managed_ready_minimal_mcp(surface["url"])
        expected_hold_boundary = _expected_hold_boundary_result(
            packet_id,
            deferred_result="REOPEN",
            deferred_decision="One or more deferred Operations Visibility seams now have live rows.",
        )

        result = _run_json(
            ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
            env=surface["env"],
        )

        assert result == _expected_host_bootstrap_ready_result(
            packet_id,
            minimal_mcp=expected_minimal_mcp,
            hold_boundary=expected_hold_boundary,
            expected_output_artifact=expected_output_artifact,
            expected_git=expected_git,
            expected_toolchains=expected_toolchains,
        )
        assert artifact.exists()
        _assert_hold_boundary_child_artifacts(
            packet_id,
            result["hold_boundary"],
            endpoint=surface["url"],
            expected_hold_payload=_expected_deferred_ops_child_payload(
                packet_id,
                endpoint=surface["url"],
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
        assert json.loads(artifact.read_text(encoding="utf-8")) == result
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_host_bootstrap_delegates_unavailable_when_managed_minimal_trio_lacks_authoritative_views(
    fake_ready_host_bootstrap_surface,
) -> None:
    packet_id = "host-bootstrap-managed-ready-unavailable-test"
    artifact = HOST_BOOTSTRAP_ACTUAL_DIR / f"host-bootstrap-status-{packet_id}.json"
    expected_output_artifact = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "host-bootstrap-status"
        / "actual"
        / f"host-bootstrap-status-{packet_id}.json"
    )
    surface = fake_ready_host_bootstrap_surface(
        deferred_error='relation "public.v_resource_allocation" does not exist'
    )
    process, pid = _start_bash_sleep_process()
    try:
        _write_managed_state(surface["url"], pid)
        expected_git = _current_repo_git_metadata(
            created_before_snapshot=(
                MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json",
                DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json",
            )
        )
        expected_toolchains = _current_bash_toolchains_metadata(surface["env"])
        expected_minimal_mcp = _expected_managed_ready_minimal_mcp(surface["url"])
        expected_hold_boundary = _expected_hold_boundary_result(
            packet_id,
            deferred_result="UNAVAILABLE",
            deferred_decision=(
                "Authoritative deferred view counts require apex-db to run against a live DSN such as "
                "SEAM_DATABASE_URL; the current database surface is not sufficient for this hold check."
            ),
        )

        result = _run_json(
            ["bash", "tools/ai/run-olares-host-bootstrap-status.sh", packet_id],
            env=surface["env"],
        )

        assert result == _expected_host_bootstrap_ready_result(
            packet_id,
            minimal_mcp=expected_minimal_mcp,
            hold_boundary=expected_hold_boundary,
            expected_output_artifact=expected_output_artifact,
            expected_git=expected_git,
            expected_toolchains=expected_toolchains,
        )
        assert artifact.exists()
        _assert_hold_boundary_child_artifacts(
            packet_id,
            result["hold_boundary"],
            endpoint=surface["url"],
            expected_hold_payload=_expected_deferred_ops_child_payload(
                packet_id,
                endpoint=surface["url"],
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
        assert json.loads(artifact.read_text(encoding="utf-8")) == result
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        _cleanup_artifacts(packet_id)