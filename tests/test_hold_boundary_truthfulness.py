from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path, PurePosixPath

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_DEV_FILE = REPO_ROOT / ".env.dev"
README_PREVIEW = (REPO_ROOT / "README.md").read_bytes()[:120].decode("utf-8")
DEFERRED_OPS_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "deferred-ops-view-counts" / "actual"
MCP_CONTRACT_ACTUAL_DIR = REPO_ROOT / "tests" / "canary" / "mcp-contract" / "actual"
STATE_FILE = REPO_ROOT / ".tmp" / "ai-workflow" / "minimal-mcp-trio.env"


@pytest.fixture(autouse=True)
def _clean_state_file() -> None:
    _cleanup_state_file()
    yield
    _cleanup_state_file()


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


def _wsl_repo_root() -> str:
    return subprocess.check_output(["bash", "-lc", "pwd -P"], cwd=REPO_ROOT, text=True).strip()


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


def _env_file_last_value(name: str) -> str | None:
    if not ENV_DEV_FILE.exists():
        return None

    value: str | None = None
    for raw_line in ENV_DEV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        assert raw_line == line
        current_name, current_value = raw_line.split("=", 1)
        assert current_name == current_name.strip()
        assert current_value == current_value.strip()
        if current_name == name:
            value = current_value
    return value


def _expected_minimal_trio_verifier_payload(
    packet_id: str,
    *,
    endpoint: str,
    output_path: str,
    command_endpoints: tuple[str, str, str] | None = None,
) -> dict[str, object]:
    command = (
        f"/usr/bin/python3 tools/ai/verify_minimal_mcp_trio.py --packet-id {packet_id} "
        f"--output '{output_path}'"
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


def _expected_deferred_ops_child_payload(
    packet_id: str,
    *,
    endpoint: str | None = None,
    db_source: str = "env:APEX_DB_MCP_URL",
    result: str,
    decision: str,
    deferred_view_counts: dict[str, object],
    reopen_candidates: list[str] | None = None,
) -> dict[str, object]:
    endpoint = endpoint or _env_file_last_value("APEX_DB_MCP_URL")

    assert endpoint is not None

    payload: dict[str, object] = {
        "packet_id": packet_id,
        "repo_root": _wsl_repo_root(),
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


def _assert_hold_boundary_child_artifacts(
    packet_id: str,
    result: dict[str, object],
    *,
    expected_hold_payload: dict[str, object],
    expected_endpoint: str | None = None,
    command_endpoints: tuple[str, str, str] | None = None,
) -> None:
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"

    assert minimal_output.exists()
    assert hold_output.exists()

    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))
    hold_payload = json.loads(hold_output.read_text(encoding="utf-8"))

    expected_endpoint = expected_endpoint or _env_file_last_value("APEX_FS_MCP_URL")

    assert expected_endpoint is not None
    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = f"{packet_id}-promote-guard-<generated>"

    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=expected_endpoint,
        output_path=str(result["outputs"]["minimal_mcp"]),
        command_endpoints=command_endpoints,
    )
    assert hold_payload == expected_hold_payload


@pytest.fixture
def fake_hold_boundary_surface():
    server_process: subprocess.Popen[str] | None = None
    original_env_dev = ENV_DEV_FILE.read_text(encoding="utf-8") if ENV_DEV_FILE.exists() else None

    def _start(*, deferred_rows: list[dict[str, object]] | None = None, deferred_error: str | None = None) -> dict[str, str]:
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
                'serverInfo': {{'name': 'fake-hold-boundary-surface', 'version': '0.1.0'}},
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
        port = server_process.stdout.readline().strip()
        if not port:
            stderr = ""
            if server_process.stderr is not None:
                stderr = server_process.stderr.read()
            raise RuntimeError(f"Failed to start fake hold-boundary MCP server: {stderr}")

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
        return os.environ.copy()

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
def test_hold_boundary_reports_hold_when_deferred_views_are_empty(fake_hold_boundary_surface) -> None:
    packet_id = "hold-boundary-empty-views-test"
    env = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_json(["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id], env=env)

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="HOLD",
        deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_reports_reopen_when_deferred_view_has_rows(fake_hold_boundary_surface) -> None:
    packet_id = "hold-boundary-reopen-test"
    env = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 2},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_json(["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id], env=env)

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="REOPEN",
        deferred_decision="One or more deferred Operations Visibility seams now have live rows.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_reports_unavailable_when_authoritative_views_are_missing(fake_hold_boundary_surface) -> None:
    packet_id = "hold-boundary-unavailable-test"
    env = fake_hold_boundary_surface(deferred_error='relation "public.v_resource_allocation" does not exist')

    result = _run_json(["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id], env=env)

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
        expected_hold_payload=_expected_deferred_ops_child_payload(
            packet_id,
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


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_refuses_missing_live_dsn_env_before_running_checks() -> None:
    packet_id = "hold-boundary-missing-live-dsn-env-test"
    missing_env_name = "MISSING_HOLD_BOUNDARY_DSN_ENV"
    env = os.environ.copy()
    env.pop(missing_env_name, None)

    result = subprocess.run(
        ["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id, missing_env_name],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == (
        f"{missing_env_name} is not set; cannot run the hold-boundary cadence check against a live DSN."
    )
    assert not (DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json").exists()
    assert not (MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json").exists()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_times_out_when_live_dsn_falls_back_to_local_apex_db(
    fake_hold_boundary_surface,
) -> None:
    packet_id = "hold-boundary-live-dsn-direct-mode-test"
    dsn_env_name = "HOLD_BOUNDARY_LIVE_DSN"
    env = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f"export {dsn_env_name}='definitely-not-a-real-sqlalchemy-dialect://'; "
                f"bash tools/ai/run-olares-hold-boundary-check.sh {packet_id} {dsn_env_name}"
            ),
        ],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
    expected_minimal_output = str(
        PurePosixPath(_wsl_repo_root())
        / "tests"
        / "canary"
        / "mcp-contract"
        / "actual"
        / f"verify-minimal-mcp-trio-{packet_id}.json"
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.strip() == "Timed out waiting for live hold-boundary apex-db on port 8721."
    assert minimal_output.exists()
    assert not hold_output.exists()

    minimal_payload = json.loads(minimal_output.read_text(encoding="utf-8"))
    expected_endpoint = _env_file_last_value("APEX_DB_MCP_URL")

    assert expected_endpoint is not None
    promote_guard_packet_id = str(minimal_payload["checks"]["jobs_promote_guard"]["packet_id"])
    assert re.fullmatch(rf"{re.escape(packet_id)}-promote-guard-[a-z0-9]{{8}}", promote_guard_packet_id)
    minimal_payload["checks"]["jobs_promote_guard"]["packet_id"] = (
        f"{packet_id}-promote-guard-<generated>"
    )
    assert minimal_payload == _expected_minimal_trio_verifier_payload(
        packet_id,
        endpoint=expected_endpoint,
        output_path=expected_minimal_output,
    )

    _cleanup_artifacts(packet_id)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_surfaces_helper_failure_when_deferred_ops_artifact_path_is_blocked(
    fake_hold_boundary_surface,
) -> None:
    packet_id = "hold-boundary-blocked-deferred-artifact-test"
    env = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    hold_output = DEFERRED_OPS_ACTUAL_DIR / f"deferred-ops-view-counts-{packet_id}.json"
    minimal_output = MCP_CONTRACT_ACTUAL_DIR / f"verify-minimal-mcp-trio-{packet_id}.json"
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
    hold_output.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id],
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
    assert expected_hold_output.lower() in normalized_deferred_decision
    assert hold_output.name.lower() in normalized_deferred_decision or "is a directory" in deferred_decision
    assert re.search(r"is a directory|errno 21", deferred_decision)
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
        endpoint=str(_env_file_last_value("APEX_DB_MCP_URL")),
        output_path=expected_minimal_output,
    )

    shutil.rmtree(hold_output)
    _cleanup_artifacts(packet_id)
    _cleanup_state_file()
    _cleanup_state_file()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required for Bash wrapper tests")
def test_hold_boundary_prefers_state_db_endpoint_over_inherited_env_url(fake_hold_boundary_surface) -> None:
    packet_id = "hold-boundary-state-db-endpoint-wins"
    env = fake_hold_boundary_surface(
        deferred_rows=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    endpoint = _env_file_last_value("APEX_DB_MCP_URL")
    assert endpoint is not None

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
        "\n".join(
            [
                "STARTED_AT='2026-05-12T00:00:00Z'",
                f"PACKET_ID='{packet_id}'",
                "MODE='adopted'",
                "FS_PID=''",
                "DB_PID=''",
                "JOBS_PID=''",
                f"FS_ENDPOINT='{endpoint}'",
                f"DB_ENDPOINT='{endpoint}'",
                f"JOBS_ENDPOINT='{endpoint}'",
                f"LEDGER_PATH='{PurePosixPath(_wsl_repo_root()) / '.apex-data' / 'apex-jobs-ledger.json'}'",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    result = _run_json(["bash", "tools/ai/run-olares-hold-boundary-check.sh", packet_id], env=env)

    assert result == _expected_hold_boundary_result(
        packet_id,
        deferred_result="HOLD",
        deferred_decision="Deferred Operations Visibility seams remain empty and should stay on hold.",
    )
    _assert_hold_boundary_child_artifacts(
        packet_id,
        result,
        expected_endpoint=endpoint,
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