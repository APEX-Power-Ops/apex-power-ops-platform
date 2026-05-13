from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class _FakeRuntimeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            if getattr(self.server, "health_status", 200) != 200:
                self.send_response(self.server.health_status)
                self.end_headers()
                return
            body = json.dumps(self.server.health_payload).encode("utf-8")
        elif self.path == "/fixtures/stack-data-center":
            if getattr(self.server, "summary_status", 200) != 200:
                self.send_response(self.server.summary_status)
                self.end_headers()
                return
            body = json.dumps(self.server.summary_payload).encode("utf-8")
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


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
            if getattr(self.server, "initialize_error", None):
                result = {
                    "isError": True,
                    "content": [{"text": self.server.initialize_error}],
                }
            else:
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "serverInfo": {"name": f"fake-{self.server.service_name}", "version": "0.1.0"},
                }
        elif method == "tools/list":
            if getattr(self.server, "tools_list_error", None):
                result = {
                    "isError": True,
                    "content": [{"text": self.server.tools_list_error}],
                }
            else:
                result = {"tools": [{"name": name} for name in self.server.tool_names]}
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


def _start_runtime_server(
    *,
    health_payload: dict[str, object],
    summary_payload: dict[str, object],
    health_status: int = 200,
    summary_status: int = 200,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeRuntimeHandler)
    server.health_payload = health_payload
    server.summary_payload = summary_payload
    server.health_status = health_status
    server.summary_status = summary_status
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _start_mcp_server(
    service_name: str,
    tool_names: list[str],
    *,
    initialize_error: str | None = None,
    tools_list_error: str | None = None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMcpHandler)
    server.service_name = service_name
    server.tool_names = tool_names
    server.initialize_error = initialize_error
    server.tools_list_error = tools_list_error
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _expected_mcp_contract(
    *,
    fs_endpoint: str,
    db_endpoint: str,
    jobs_endpoint: str,
    forms_endpoint: str,
    p6_endpoint: str,
    jobs_tools: list[str] | None = None,
) -> dict[str, object]:
    return {
        "apex-fs": {
            "endpoint": fs_endpoint,
            "tools": ["read_text_file"],
        },
        "apex-db": {
            "endpoint": db_endpoint,
            "tools": ["query"],
        },
        "apex-jobs": {
            "endpoint": jobs_endpoint,
            "tools": jobs_tools or ["promote_packet", "start_run", "end_run"],
        },
        "apex-forms": {
            "endpoint": forms_endpoint,
            "tools": ["render_template"],
        },
        "apex-p6": {
            "endpoint": p6_endpoint,
            "tools": ["fixture_summary"],
        },
    }


def _assert_last_failure_line(completed: subprocess.CompletedProcess[str], expected_line: str) -> None:
    stream = completed.stderr if completed.stderr.strip() else completed.stdout
    lines = [line for line in stream.replace("\r\n", "\n").split("\n") if line]
    assert lines
    assert lines[-1] == expected_line


def _rendered_chart_sources(rendered_chart: str) -> list[str]:
    lines = rendered_chart.splitlines()
    source_lines = [line for line in lines if line.startswith("# Source: ")]
    source_like_lines = [line for line in lines if line.lstrip().startswith("# Source: ")]
    assert source_lines == source_like_lines
    assert all(line == line.rstrip() for line in source_lines)
    return source_lines


def test_run_canary_helper_uses_env_defaults_and_writes_output_tree(tmp_path: Path) -> None:
    forms_health = {"status": "ok", "service": "forms-engine"}
    p6_health = {"status": "ok", "service": "p6-ingest"}
    p6_summary = {"fixture": "stack-data-center", "projects": 1, "activities": 3}

    forms_server = _start_runtime_server(health_payload=forms_health, summary_payload={})
    p6_server = _start_runtime_server(health_payload=p6_health, summary_payload=p6_summary)
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet", "start_run", "end_run"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 0, completed.stderr

    assert json.loads((output_root / "forms-engine-dev-runtime" / "actual" / "health.json").read_text(encoding="utf-8")) == forms_health
    assert json.loads((output_root / "apex-forms-runtime-status" / "actual" / "health.json").read_text(encoding="utf-8")) == forms_health
    assert json.loads((output_root / "p6-ingest-dev-runtime" / "actual" / "health.json").read_text(encoding="utf-8")) == p6_health
    assert json.loads((output_root / "p6-ingest-dev-runtime" / "actual" / "summary.json").read_text(encoding="utf-8")) == p6_summary
    assert json.loads((output_root / "p6-ingest-stack-fixture" / "actual" / "summary.json").read_text(encoding="utf-8")) == p6_summary
    assert json.loads((output_root / "apex-p6-stack-summary" / "actual" / "summary.json").read_text(encoding="utf-8")) == p6_summary

    mcp_contract = json.loads((output_root / "mcp-contract" / "actual" / "mcp-tool-lists.json").read_text(encoding="utf-8"))
    assert mcp_contract == _expected_mcp_contract(
        fs_endpoint=f"http://127.0.0.1:{fs_server.server_address[1]}/mcp",
        db_endpoint=f"http://127.0.0.1:{db_server.server_address[1]}/mcp",
        jobs_endpoint=f"http://127.0.0.1:{jobs_server.server_address[1]}/mcp",
        forms_endpoint=f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp",
        p6_endpoint=f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp",
    )

    forms_manifest = (output_root / "forms-engine-staging-manifest" / "actual" / "OlaresManifest.yaml").read_text(encoding="utf-8")
    p6_manifest = (output_root / "p6-ingest-staging-manifest" / "actual" / "OlaresManifest.yaml").read_text(encoding="utf-8")
    assert forms_manifest == (REPO_ROOT / "infra" / "olares" / "forms-engine" / "OlaresManifest.yaml").read_text(encoding="utf-8")
    assert p6_manifest == (REPO_ROOT / "infra" / "olares" / "p6-ingest" / "OlaresManifest.yaml").read_text(encoding="utf-8")

    forms_render = (output_root / "forms-engine-staging-render" / "actual" / "rendered-chart.yaml").read_text(encoding="utf-8")
    p6_render = (output_root / "p6-ingest-staging-render" / "actual" / "rendered-chart.yaml").read_text(encoding="utf-8")
    assert _rendered_chart_sources(forms_render) == [
        "# Source: forms-engine/templates/configmap.yaml",
        "# Source: forms-engine/templates/service.yaml",
        "# Source: forms-engine/templates/deployment.yaml",
    ]
    assert _rendered_chart_sources(p6_render) == [
        "# Source: p6-ingest/templates/configmap.yaml",
        "# Source: p6-ingest/templates/service.yaml",
        "# Source: p6-ingest/templates/deployment.yaml",
    ]


def test_run_canary_helper_prefers_explicit_mcp_urls_over_port_defaults(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={})
    p6_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={"fixture": "stack-data-center"})
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-explicit-urls"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"

    # Set conflicting port defaults so only explicit URL precedence can make the helper succeed.
    env["APEX_DEV_MCP_FS_PORT"] = "1"
    env["APEX_DEV_MCP_DB_PORT"] = "2"
    env["APEX_DEV_MCP_JOBS_PORT"] = "3"
    env["APEX_FS_MCP_URL"] = f"http://127.0.0.1:{fs_server.server_address[1]}/mcp"
    env["APEX_DB_MCP_URL"] = f"http://127.0.0.1:{db_server.server_address[1]}/mcp"
    env["APEX_JOBS_MCP_URL"] = f"http://127.0.0.1:{jobs_server.server_address[1]}/mcp"
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 0, completed.stderr

    mcp_contract = json.loads((output_root / "mcp-contract" / "actual" / "mcp-tool-lists.json").read_text(encoding="utf-8"))
    assert mcp_contract == _expected_mcp_contract(
        fs_endpoint=f"http://127.0.0.1:{fs_server.server_address[1]}/mcp",
        db_endpoint=f"http://127.0.0.1:{db_server.server_address[1]}/mcp",
        jobs_endpoint=f"http://127.0.0.1:{jobs_server.server_address[1]}/mcp",
        forms_endpoint=f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp",
        p6_endpoint=f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp",
        jobs_tools=["promote_packet"],
    )


def test_run_canary_helper_fails_when_mcp_initialize_errors(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={})
    p6_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={"fixture": "stack-data-center"})
    fs_server = _start_mcp_server("fs", ["read_text_file"], initialize_error="temporary fs initialize failure")
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-initialize-failure"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    _assert_last_failure_line(completed, "RuntimeError: temporary fs initialize failure")


def test_run_canary_helper_fails_when_mcp_tools_list_errors(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={})
    p6_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={"fixture": "stack-data-center"})
    fs_server = _start_mcp_server("fs", ["read_text_file"], tools_list_error="temporary fs tools/list failure")
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-tools-list-failure"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    _assert_last_failure_line(completed, "RuntimeError: temporary fs tools/list failure")


def test_run_canary_helper_fails_when_forms_runtime_health_errors(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(
        health_payload={"status": "not-ok"},
        summary_payload={},
        health_status=500,
    )
    p6_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={"fixture": "stack-data-center"})
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-forms-runtime-failure"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    _assert_last_failure_line(completed, "urllib.error.HTTPError: HTTP Error 500: Internal Server Error")


def test_run_canary_helper_fails_when_p6_summary_errors(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={})
    p6_server = _start_runtime_server(
        health_payload={"status": "ok"},
        summary_payload={"fixture": "stack-data-center"},
        summary_status=500,
    )
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-p6-summary-failure"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    _assert_last_failure_line(completed, "urllib.error.HTTPError: HTTP Error 500: Internal Server Error")


def test_run_canary_helper_fails_when_p6_runtime_health_errors(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok"}, summary_payload={})
    p6_server = _start_runtime_server(
        health_payload={"status": "not-ok"},
        summary_payload={"fixture": "stack-data-center"},
        health_status=500,
    )
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-p6-runtime-health-failure"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    _assert_last_failure_line(completed, "urllib.error.HTTPError: HTTP Error 500: Internal Server Error")


def test_run_canary_helper_prefers_explicit_cli_endpoints_over_env_defaults(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok", "service": "forms-engine"}, summary_payload={})
    p6_server = _start_runtime_server(
        health_payload={"status": "ok", "service": "p6-ingest"},
        summary_payload={"fixture": "stack-data-center", "projects": 1},
    )
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    output_root = tmp_path / "canary-output-explicit-cli"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = "http://127.0.0.1:1"
    env["APEX_P6_RUNTIME_URL"] = "http://127.0.0.1:2"
    env["APEX_FS_MCP_URL"] = "http://127.0.0.1:3/mcp"
    env["APEX_DB_MCP_URL"] = "http://127.0.0.1:4/mcp"
    env["APEX_JOBS_MCP_URL"] = "http://127.0.0.1:5/mcp"
    env["APEX_P6_MCP_URL"] = "http://127.0.0.1:6/mcp"
    env["APEX_FORMS_MCP_URL"] = "http://127.0.0.1:7/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
                "--forms-runtime-url",
                f"http://127.0.0.1:{forms_server.server_address[1]}",
                "--p6-runtime-url",
                f"http://127.0.0.1:{p6_server.server_address[1]}",
                "--fs-mcp-url",
                f"http://127.0.0.1:{fs_server.server_address[1]}/mcp",
                "--db-mcp-url",
                f"http://127.0.0.1:{db_server.server_address[1]}/mcp",
                "--jobs-mcp-url",
                f"http://127.0.0.1:{jobs_server.server_address[1]}/mcp",
                "--p6-mcp-url",
                f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp",
                "--forms-mcp-url",
                f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 0, completed.stderr

    assert json.loads((output_root / "forms-engine-dev-runtime" / "actual" / "health.json").read_text(encoding="utf-8")) == {
        "status": "ok",
        "service": "forms-engine",
    }
    assert json.loads((output_root / "p6-ingest-dev-runtime" / "actual" / "health.json").read_text(encoding="utf-8")) == {
        "status": "ok",
        "service": "p6-ingest",
    }

    mcp_contract = json.loads((output_root / "mcp-contract" / "actual" / "mcp-tool-lists.json").read_text(encoding="utf-8"))
    assert mcp_contract == _expected_mcp_contract(
        fs_endpoint=f"http://127.0.0.1:{fs_server.server_address[1]}/mcp",
        db_endpoint=f"http://127.0.0.1:{db_server.server_address[1]}/mcp",
        jobs_endpoint=f"http://127.0.0.1:{jobs_server.server_address[1]}/mcp",
        forms_endpoint=f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp",
        p6_endpoint=f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp",
        jobs_tools=["promote_packet"],
    )


def test_run_canary_helper_fails_when_output_root_path_is_blocked(tmp_path: Path) -> None:
    forms_server = _start_runtime_server(health_payload={"status": "ok", "service": "forms-engine"}, summary_payload={})
    p6_server = _start_runtime_server(
        health_payload={"status": "ok", "service": "p6-ingest"},
        summary_payload={"fixture": "stack-data-center", "projects": 1},
    )
    fs_server = _start_mcp_server("fs", ["read_text_file"])
    db_server = _start_mcp_server("db", ["query"])
    jobs_server = _start_mcp_server("jobs", ["promote_packet"])
    forms_mcp_server = _start_mcp_server("forms", ["render_template"])
    p6_mcp_server = _start_mcp_server("p6", ["fixture_summary"])

    blocked_parent = tmp_path / "blocked-canary-output-root"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    output_root = blocked_parent / "canary-output"
    env = os.environ.copy()
    env["APEX_FORMS_RUNTIME_URL"] = f"http://127.0.0.1:{forms_server.server_address[1]}"
    env["APEX_P6_RUNTIME_URL"] = f"http://127.0.0.1:{p6_server.server_address[1]}"
    env["APEX_DEV_MCP_FS_PORT"] = str(fs_server.server_address[1])
    env["APEX_DEV_MCP_DB_PORT"] = str(db_server.server_address[1])
    env["APEX_DEV_MCP_JOBS_PORT"] = str(jobs_server.server_address[1])
    env["APEX_P6_MCP_URL"] = f"http://127.0.0.1:{p6_mcp_server.server_address[1]}/mcp"
    env["APEX_FORMS_MCP_URL"] = f"http://127.0.0.1:{forms_mcp_server.server_address[1]}/mcp"

    try:
        completed = subprocess.run(
            [
                ".\\.venv\\Scripts\\python.exe",
                "tools/canary/run_canary.py",
                "--output-root",
                str(output_root),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        for server in (forms_server, p6_server, fs_server, db_server, jobs_server, forms_mcp_server, p6_mcp_server):
            server.shutdown()
            server.server_close()

    assert completed.returncode == 1
    error_text = (completed.stderr or completed.stdout).lower()
    normalized_error_text = error_text.replace("\\\\", "\\")
    assert str(output_root).lower() in normalized_error_text
    assert output_root.name.lower() in normalized_error_text or "already exists" in normalized_error_text
    assert re.search(r"directory|exists|permission denied", error_text)
