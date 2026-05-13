from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


class _FakeDbHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")

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
                    "serverInfo": {"name": "fake-apex-db", "version": "0.1.0"},
                }
        elif method == "tools/call":
            tool_name = payload.get("params", {}).get("name")
            if tool_name != "query":
                result = {
                    "isError": True,
                    "content": [{"text": f"unexpected tool {tool_name}"}],
                }
            elif self.server.query_error is not None:
                result = {
                    "isError": True,
                    "content": [{"text": self.server.query_error}],
                }
            else:
                result = {
                    "structuredContent": self.server.query_result,
                }
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
def fake_db_server():
    servers: list[ThreadingHTTPServer] = []

    def _start(
        *,
        query_result: object | None = None,
        query_error: str | None = None,
        initialize_error: str | None = None,
    ) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeDbHandler)
        server.query_result = query_result
        server.query_error = query_error
        server.initialize_error = initialize_error
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}/mcp"

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


def _run_helper(
    db_url: str | None,
    *,
    packet_id: str | None = "deferred-ops-test",
    db_url_env: str | None = None,
    db_connection_string: str | None = None,
    db_connection_string_env: str | None = None,
    env: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "tools/ai/check_deferred_ops_view_counts.py",
    ]
    if db_url is not None:
        command.extend(["--db-url", db_url])
    if packet_id is not None:
        command.extend(["--packet-id", packet_id])
    if db_url_env is not None:
        command.extend(["--db-url-env", db_url_env])
    if db_connection_string is not None:
        command.extend(["--db-connection-string", db_connection_string])
    if db_connection_string_env is not None:
        command.extend(["--db-connection-string-env", db_connection_string_env])
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


def _expected_mcp_db_connection(db_url: str, *, source: str = "argument:db-url") -> dict[str, object]:
    return {
        "status": "pass",
        "source": source,
        "mode": "mcp",
        "endpoint": db_url,
    }


def _expected_deferred_ops_result(
    *,
    packet_id: str = "deferred-ops-test",
    db_url: str,
    db_connection_source: str = "argument:db-url",
    result: str,
    decision: str,
    deferred_view_counts: dict[str, object],
    reopen_candidates: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "packet_id": packet_id,
        "repo_root": str(REPO_ROOT),
        "checks": {
            "db_connection": _expected_mcp_db_connection(db_url, source=db_connection_source),
            "deferred_view_counts": deferred_view_counts,
        },
        "result": result,
        "decision": decision,
    }
    if reopen_candidates is not None:
        payload["reopen_candidates"] = reopen_candidates
    return payload


def _expected_deferred_ops_failure_result(*, db_url: str, error: str) -> dict[str, object]:
    return {
        "packet_id": "deferred-ops-test",
        "repo_root": str(REPO_ROOT),
        "checks": {
            "db_connection": _expected_mcp_db_connection(db_url),
        },
        "result": "FAIL",
        "error": error,
    }


def _normalized_adhoc_packet_payload(payload: dict[str, object]) -> dict[str, object]:
    packet_id = str(payload["packet_id"])
    assert re.fullmatch(r"adhoc-deferred-ops-view-counts-\d{4}-\d{2}-\d{2}-\d{6}", packet_id)
    normalized = dict(payload)
    normalized["packet_id"] = "adhoc-deferred-ops-view-counts-generated"
    return normalized


def _expected_direct_deferred_ops_failure_result(*, packet_id: str, source: str, error: str) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "repo_root": str(REPO_ROOT),
        "checks": {
            "db_connection": {
                "status": "pass",
                "source": source,
                "mode": "direct",
            },
        },
        "result": "FAIL",
        "error": error,
    }


def _expected_precondition_failure_result(*, packet_id: str, error: str) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "repo_root": str(REPO_ROOT),
        "checks": {},
        "result": "FAIL",
        "error": error,
    }


def test_check_deferred_ops_view_counts_reports_hold_when_views_are_empty(fake_db_server) -> None:
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_helper(db_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        db_url=db_url,
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
    )


def test_check_deferred_ops_view_counts_reports_reopen_when_view_has_rows(fake_db_server) -> None:
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 2},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_helper(db_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        db_url=db_url,
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
    )


def test_check_deferred_ops_view_counts_reports_unavailable_when_views_are_missing(fake_db_server) -> None:
    db_url = fake_db_server(query_error='relation "public.v_resource_allocation" does not exist')

    result = _run_helper(db_url)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        db_url=db_url,
        result="UNAVAILABLE",
        decision=(
            "Authoritative deferred view counts require apex-db to run against a live DSN such as "
            "SEAM_DATABASE_URL; the current database surface is not sufficient for this hold check."
        ),
        deferred_view_counts={
            "status": "unavailable",
            "reason": "The current apex-db surface does not expose the authoritative deferred operations views.",
        },
    )


def test_check_deferred_ops_view_counts_fails_when_initialize_errors(fake_db_server) -> None:
    db_url = fake_db_server(initialize_error="temporary deferred ops initialize failure")

    result = _run_helper(db_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_failure_result(
        db_url=db_url,
        error="temporary deferred ops initialize failure",
    )


def test_check_deferred_ops_view_counts_fails_when_query_errors_unexpectedly(fake_db_server) -> None:
    db_url = fake_db_server(query_error="temporary deferred ops query failure")

    result = _run_helper(db_url)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_failure_result(
        db_url=db_url,
        error="temporary deferred ops query failure",
    )


def test_check_deferred_ops_view_counts_writes_failure_output_when_query_errors(fake_db_server, tmp_path: Path) -> None:
    db_url = fake_db_server(query_error="temporary deferred ops query failure")
    output_path = tmp_path / "deferred-ops-failure-output.json"

    result = _run_helper(db_url, output_path=output_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_failure_result(
        db_url=db_url,
        error="temporary deferred ops query failure",
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_check_deferred_ops_view_counts_preserves_fail_json_when_output_path_is_invalid(
    fake_db_server, tmp_path: Path
) -> None:
    db_url = fake_db_server(query_error="temporary deferred ops query failure")
    blocked_parent = tmp_path / "blocked-output-parent"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    output_path = blocked_parent / "deferred-ops-failure-output.json"

    result = _run_helper(db_url, output_path=output_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    payload_without_output_error = {key: value for key, value in payload.items() if key != "output_error"}
    assert payload_without_output_error == _expected_deferred_ops_failure_result(
        db_url=db_url,
        error="temporary deferred ops query failure",
    )
    output_error = payload["output_error"].lower()
    normalized_output_error = output_error.replace("\\\\", "\\")
    assert str(blocked_parent).lower() in normalized_output_error
    assert output_path.name.lower() in normalized_output_error or "already exists" in normalized_output_error
    assert re.search(r"directory|exists|permission denied", output_error)


def test_check_deferred_ops_view_counts_uses_env_packet_id_and_writes_output(fake_db_server, tmp_path: Path) -> None:
    packet_id = "env-deferred-ops-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    output_path = tmp_path / "deferred-ops-output.json"
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = packet_id

    result = _run_helper(db_url, packet_id=None, env=env, output_path=output_path)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
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
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_check_deferred_ops_view_counts_generates_adhoc_packet_id_when_omitted(fake_db_server) -> None:
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )

    result = _run_helper(db_url, packet_id=None, env=os.environ.copy())

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert _normalized_adhoc_packet_payload(payload) == _expected_deferred_ops_result(
        packet_id="adhoc-deferred-ops-view-counts-generated",
        db_url=db_url,
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
    )


def test_check_deferred_ops_view_counts_prefers_explicit_packet_id_over_env(fake_db_server) -> None:
    packet_id = "cli-deferred-ops-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "env-deferred-ops-test"

    result = _run_helper(db_url, packet_id=packet_id, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
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
    )


def test_check_deferred_ops_view_counts_prefers_explicit_env_db_url_over_port_default(fake_db_server) -> None:
    packet_id = "env-db-url-over-port-default-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env["APEX_DB_MCP_URL"] = db_url
    env["APEX_DEV_MCP_DB_PORT"] = "2"

    result = _run_helper(None, packet_id=packet_id, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
        db_connection_source="env:APEX_DB_MCP_URL",
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
    )


def test_check_deferred_ops_view_counts_prefers_explicit_cli_db_url_over_env_sources(fake_db_server) -> None:
    packet_id = "cli-db-url-over-env-sources-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env["DEFERRED_OPS_DB_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:3/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "4"

    result = _run_helper(
        db_url,
        packet_id=packet_id,
        db_url_env="DEFERRED_OPS_DB_URL",
        env=env,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
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
    )


def test_check_deferred_ops_view_counts_uses_port_default_when_explicit_url_is_absent(fake_db_server) -> None:
    packet_id = "port-default-db-url-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env["APEX_DB_MCP_URL"] = ""
    env["APEX_DEV_MCP_DB_PORT"] = db_url.removeprefix("http://127.0.0.1:").removesuffix("/mcp")

    result = _run_helper(None, packet_id=packet_id, env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
        db_connection_source="default:apex-db-mcp",
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
    )


def test_check_deferred_ops_view_counts_uses_named_db_url_env(fake_db_server) -> None:
    packet_id = "named-db-url-env-test"
    db_url = fake_db_server(
        query_result=[
            {"view_name": "v_equipment_needs", "row_count": 0},
            {"view_name": "v_resource_allocation", "row_count": 0},
        ]
    )
    env = os.environ.copy()
    env["DEFERRED_OPS_DB_URL"] = db_url
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "3"

    result = _run_helper(None, packet_id=packet_id, db_url_env="DEFERRED_OPS_DB_URL", env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload == _expected_deferred_ops_result(
        packet_id=packet_id,
        db_url=db_url,
        db_connection_source="env:DEFERRED_OPS_DB_URL",
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
    )


def test_check_deferred_ops_view_counts_fails_when_named_db_url_env_is_missing() -> None:
    packet_id = "missing-named-db-url-env-failure-test"
    env = os.environ.copy()
    env.pop("DEFERRED_OPS_DB_URL", None)
    env.pop("APEX_DB_MCP_URL", None)
    env.pop("APEX_DEV_MCP_DB_PORT", None)

    result = _run_helper(None, packet_id=packet_id, db_url_env="DEFERRED_OPS_DB_URL", env=env)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_precondition_failure_result(
        packet_id=packet_id,
        error="DEFERRED_OPS_DB_URL is not set; cannot run deferred ops view checks.",
    )


def test_check_deferred_ops_view_counts_fails_when_named_connection_string_env_is_missing() -> None:
    packet_id = "missing-named-db-connection-env-failure-test"
    env = os.environ.copy()
    env.pop("DEFERRED_OPS_DB_CONNECTION", None)
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "3"

    result = _run_helper(
        None,
        packet_id=packet_id,
        db_connection_string_env="DEFERRED_OPS_DB_CONNECTION",
        env=env,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_precondition_failure_result(
        packet_id=packet_id,
        error="DEFERRED_OPS_DB_CONNECTION is not set; cannot run deferred ops view checks.",
    )


def test_check_deferred_ops_view_counts_prefers_named_connection_string_env_over_mcp_defaults() -> None:
    packet_id = "direct-env-connection-string-failure-test"
    env = os.environ.copy()
    env["DEFERRED_OPS_DB_CONNECTION"] = "definitely-not-a-real-sqlalchemy-dialect://"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "3"

    result = _run_helper(
        None,
        packet_id=packet_id,
        db_connection_string_env="DEFERRED_OPS_DB_CONNECTION",
        env=env,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_direct_deferred_ops_failure_result(
        packet_id=packet_id,
        source="env:DEFERRED_OPS_DB_CONNECTION",
        error="Could not parse SQLAlchemy URL from given URL string",
    )


def test_check_deferred_ops_view_counts_writes_failure_output_when_direct_connection_fails(tmp_path: Path) -> None:
    packet_id = "direct-env-connection-string-failure-output-test"
    env = os.environ.copy()
    env["DEFERRED_OPS_DB_CONNECTION"] = "definitely-not-a-real-sqlalchemy-dialect://"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "3"
    output_path = tmp_path / "deferred-ops-direct-failure-output.json"

    result = _run_helper(
        None,
        packet_id=packet_id,
        db_connection_string_env="DEFERRED_OPS_DB_CONNECTION",
        env=env,
        output_path=output_path,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_direct_deferred_ops_failure_result(
        packet_id=packet_id,
        source="env:DEFERRED_OPS_DB_CONNECTION",
        error="Could not parse SQLAlchemy URL from given URL string",
    )
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_check_deferred_ops_view_counts_prefers_argument_connection_string_over_env_and_mcp_defaults() -> None:
    packet_id = "direct-argument-connection-string-failure-test"
    env = os.environ.copy()
    env["DEFERRED_OPS_DB_CONNECTION"] = "sqlite:///should-not-be-used.db"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:2/mcp"
    env["APEX_DEV_MCP_DB_PORT"] = "3"

    result = _run_helper(
        None,
        packet_id=packet_id,
        db_connection_string="definitely-not-a-real-sqlalchemy-dialect://",
        db_connection_string_env="DEFERRED_OPS_DB_CONNECTION",
        env=env,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload == _expected_direct_deferred_ops_failure_result(
        packet_id=packet_id,
        source="argument:db-connection-string",
        error="Could not parse SQLAlchemy URL from given URL string",
    )