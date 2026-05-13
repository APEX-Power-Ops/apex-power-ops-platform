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


class _FakeJobsHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        method = payload.get("method")

        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "fake-jobs", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {"name": "promote_packet"},
                    {"name": "start_run"},
                    {"name": "end_run"},
                    {"name": "list_runs"},
                ]
            }
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
def fake_jobs():
    servers: list[ThreadingHTTPServer] = []

    def _start(
        *,
        start_run_error: str | None = None,
        end_run_error: str | None = None,
        list_runs_error: str | None = None,
        promote_packet_error: str | None = None,
        listed_runs: list[dict[str, object]] | None = None,
        promote_result: dict[str, object] | None = None,
    ) -> str:
        def jobs_handler(params: dict[str, object]) -> dict[str, object]:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if tool_name == "start_run":
                if start_run_error is not None:
                    return {"isError": True, "content": [{"text": start_run_error}]}
                return {
                    "structuredContent": {
                        "run_id": "host-run-123",
                        "env": arguments.get("env"),
                        "service": arguments.get("service"),
                        "packet_id": arguments.get("packet_id"),
                        "status": "running",
                    }
                }
            if tool_name == "end_run":
                if end_run_error is not None:
                    return {"isError": True, "content": [{"text": end_run_error}]}
                return {
                    "structuredContent": {
                        "run_id": arguments.get("run_id"),
                        "env": "host",
                        "service": "ai-workflow",
                        "packet_id": "promotion-test",
                        "status": arguments.get("status"),
                        "notes": arguments.get("notes"),
                    }
                }
            if tool_name == "list_runs":
                if list_runs_error is not None:
                    return {"isError": True, "content": [{"text": list_runs_error}]}
                runs = listed_runs
                if runs is None:
                    runs = [{
                        "run_id": "host-run-123",
                        "env": arguments.get("env"),
                        "service": arguments.get("service"),
                        "packet_id": arguments.get("packet_id"),
                        "status": arguments.get("status"),
                        "notes": "host promotion validation proof",
                    }]
                return {"structuredContent": {"runs": runs}}
            if tool_name == "promote_packet":
                if promote_packet_error is not None:
                    return {"isError": True, "content": [{"text": promote_packet_error}]}
                result = promote_result
                if result is None:
                    result = {
                        "packet_id": arguments.get("packet_id"),
                        "promoted_at": "2026-05-13T16:00:00.000Z",
                        "supporting_run_ids": ["host-run-123"],
                    }
                return {"structuredContent": result}
            return {"isError": True, "content": [{"text": f"unexpected jobs tool {tool_name}"}]}

        server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeJobsHandler)
        server.handle_tool_call = jobs_handler
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}/mcp"

    yield _start

    for server in servers:
        server.shutdown()
        server.server_close()


def _run_helper(
    jobs_url: str | None,
    *,
    packet_id: str | None = "promotion-test",
    env: dict[str, str] | None = None,
    output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "tools/ai/capture_apex_jobs_promotion.py"]
    if packet_id is not None:
        command.extend(["--packet-id", packet_id])
    if jobs_url is not None:
        command.extend(["--jobs-url", jobs_url])
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


def _expected_command(argv: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def _expected_success_payload(
    jobs_url: str,
    *,
    packet_id: str = "promotion-test",
    output_path: Path | None = None,
    packet_id_arg: str | None = "promotion-test",
) -> dict[str, object]:
    command = [sys.executable, "tools/ai/capture_apex_jobs_promotion.py"]
    if packet_id_arg is not None:
        command.extend(["--packet-id", packet_id_arg])
    command.extend(["--jobs-url", jobs_url])
    if output_path is not None:
        command.extend(["--output", str(output_path)])
    payload: dict[str, object] = {
        "packet_id": packet_id,
        "tool": "tools/ai/capture_apex_jobs_promotion.py",
        "command": _expected_command(command),
        "endpoint": jobs_url,
        "env": "host",
        "service": "ai-workflow",
        "notes": "host promotion validation proof",
        "host_run": {
            "run_id": "host-run-123",
            "env": "host",
            "service": "ai-workflow",
            "packet_id": "promotion-test",
            "status": "success",
            "notes": "host promotion validation proof",
        },
        "host_success_runs": [{
            "run_id": "host-run-123",
            "env": "host",
            "service": "ai-workflow",
            "packet_id": packet_id,
            "status": "success",
            "notes": "host promotion validation proof",
        }],
        "promotion": {
            "packet_id": packet_id,
            "promoted_at": "2026-05-13T16:00:00.000Z",
            "supporting_run_ids": ["host-run-123"],
        },
        "checks": {
            "jobs_tools": {"status": "pass", "tools": ["promote_packet", "start_run", "end_run", "list_runs"]},
            "jobs_start_run": {"status": "pass", "run": {"run_id": "host-run-123", "env": "host", "service": "ai-workflow", "packet_id": packet_id, "status": "running"}},
            "jobs_end_run": {"status": "pass", "run": {"run_id": "host-run-123", "env": "host", "service": "ai-workflow", "packet_id": "promotion-test", "status": "success", "notes": "host promotion validation proof"}},
            "jobs_list_runs": {"status": "pass", "result": {"runs": [{"run_id": "host-run-123", "env": "host", "service": "ai-workflow", "packet_id": packet_id, "status": "success", "notes": "host promotion validation proof"}]}},
            "jobs_promote_packet": {"status": "pass", "result": {"packet_id": packet_id, "promoted_at": "2026-05-13T16:00:00.000Z", "supporting_run_ids": ["host-run-123"]}},
        },
        "result": "PASS",
    }
    if output_path is not None:
        payload["artifact_path"] = str(output_path).replace("\\", "/")
    return payload


def test_capture_apex_jobs_promotion_reports_success(fake_jobs, tmp_path: Path) -> None:
    jobs_url = fake_jobs()
    output_path = tmp_path / "promotion.json"

    completed = _run_helper(jobs_url, output_path=output_path)

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload == _expected_success_payload(jobs_url, output_path=output_path)
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_capture_apex_jobs_promotion_uses_env_packet_id(fake_jobs) -> None:
    jobs_url = fake_jobs()
    env = os.environ.copy()
    env["APEX_PACKET_ID"] = "promotion-from-env"

    completed = _run_helper(jobs_url, packet_id=None, env=env)

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload == _expected_success_payload(
        jobs_url,
        packet_id="promotion-from-env",
        packet_id_arg=None,
    )


def test_capture_apex_jobs_promotion_fails_when_list_runs_missing_completed_run(fake_jobs) -> None:
    jobs_url = fake_jobs(listed_runs=[])

    completed = _run_helper(jobs_url)

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["result"] == "FAIL"
    assert payload["error"] == "list_runs did not return the just-completed promotion-eligible run"
    assert payload["checks"]["jobs_list_runs"] == {
        "status": "fail",
        "result": {"runs": []},
        "error": "list_runs did not return the just-completed promotion-eligible run",
    }


def test_capture_apex_jobs_promotion_fails_when_promote_packet_errors(fake_jobs) -> None:
    jobs_url = fake_jobs(promote_packet_error="temporary promote_packet failure")

    completed = _run_helper(jobs_url)

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["result"] == "FAIL"
    assert payload["error"] == "temporary promote_packet failure"
    assert payload["checks"]["jobs_promote_packet"] == {
        "status": "fail",
        "result": None,
        "error": "temporary promote_packet failure",
    }


def test_capture_apex_jobs_promotion_generates_adhoc_packet_id_when_unset(fake_jobs) -> None:
    jobs_url = fake_jobs()
    env = os.environ.copy()
    env.pop("APEX_PACKET_ID", None)

    completed = _run_helper(jobs_url, packet_id=None, env=env)

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert re.fullmatch(r"adhoc-apex-jobs-promotion-\d{4}-\d{2}-\d{2}-\d{6}", payload["packet_id"])
    assert payload["checks"]["jobs_start_run"]["run"]["packet_id"] == payload["packet_id"]
    assert payload["checks"]["jobs_list_runs"]["result"]["runs"][0]["packet_id"] == payload["packet_id"]
    assert payload["checks"]["jobs_promote_packet"]["result"]["packet_id"] == payload["packet_id"]