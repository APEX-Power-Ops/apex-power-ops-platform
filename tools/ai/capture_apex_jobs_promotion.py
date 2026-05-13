from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def fetch_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def initialize_and_list(endpoint: str) -> list[str]:
    initialize_response = fetch_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "apex-ai-workflow-promotion", "version": "0.1.0"},
            },
        },
    )
    initialize_result = initialize_response.get("result", {})
    if initialize_result.get("isError"):
        content = initialize_result.get("content", [])
        detail = content[0].get("text") if content else "Unknown MCP error"
        raise RuntimeError(detail)

    response = fetch_json(endpoint, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    result = response.get("result", {})
    if result.get("isError"):
        content = result.get("content", [])
        detail = content[0].get("text") if content else "Unknown MCP error"
        raise RuntimeError(detail)
    return [tool["name"] for tool in result.get("tools", [])]


def call_tool(endpoint: str, name: str, arguments: dict[str, Any]) -> Any:
    response = fetch_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
    )
    result = response.get("result", {})
    if result.get("isError"):
        content = result.get("content", [])
        detail = content[0].get("text") if content else "Unknown MCP error"
        raise RuntimeError(detail)
    if "structuredContent" in result:
        return result["structuredContent"]
    content = result.get("content", [])
    return json.loads(content[0]["text"]) if content else None


def write_output(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def emit_summary(path: Path | None, payload: dict[str, Any], exit_code: int) -> int:
    try:
        write_output(path, payload)
    except Exception as error:  # noqa: BLE001
        if payload.get("result") != "FAIL":
            payload["result"] = "FAIL"
            payload["error"] = str(error)
            exit_code = 1
        else:
            payload["output_error"] = str(error)

    print(json.dumps(payload, indent=2))
    return exit_code


def resolve_packet_id(packet_id: str | None) -> str:
    explicit = str(packet_id or "").strip()
    if explicit:
        return explicit

    env_packet_id = str(os.getenv("APEX_PACKET_ID") or "").strip()
    if env_packet_id:
        return env_packet_id

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    return f"adhoc-apex-jobs-promotion-{timestamp}"


def format_command() -> str:
    argv = [sys.executable, *sys.argv]
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def default_jobs_url() -> str:
    explicit_url = os.getenv("APEX_JOBS_MCP_URL")
    if explicit_url:
        return explicit_url

    port = os.getenv("APEX_DEV_MCP_JOBS_PORT", "8812")
    return f"http://127.0.0.1:{port}/mcp"


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture apex-jobs host success and promotion evidence.")
    parser.add_argument("--jobs-url", default=default_jobs_url())
    parser.add_argument("--packet-id")
    parser.add_argument("--service", default="ai-workflow")
    parser.add_argument("--env", default="host")
    parser.add_argument("--notes", default="host promotion validation proof")
    parser.add_argument("--output")
    args = parser.parse_args()

    packet_id = resolve_packet_id(args.packet_id)
    output_path = Path(args.output) if args.output else None
    summary: dict[str, Any] = {
        "packet_id": packet_id,
        "tool": "tools/ai/capture_apex_jobs_promotion.py",
        "command": format_command(),
        "endpoint": args.jobs_url,
        "env": args.env,
        "service": args.service,
        "notes": args.notes,
        "checks": {},
    }
    if output_path is not None:
        summary["artifact_path"] = str(output_path).replace("\\", "/")

    try:
        jobs_tools = initialize_and_list(args.jobs_url)
        summary["checks"]["jobs_tools"] = {"status": "pass", "tools": jobs_tools}

        started = call_tool(
            args.jobs_url,
            "start_run",
            {"env": args.env, "service": args.service, "packet_id": packet_id},
        )
        if not isinstance(started, dict) or not started.get("run_id"):
            summary["checks"]["jobs_start_run"] = {
                "status": "fail",
                "result": started,
                "error": "start_run returned an unexpected result shape",
            }
            raise RuntimeError("start_run returned an unexpected result shape")
        summary["checks"]["jobs_start_run"] = {"status": "pass", "run": started}

        ended = call_tool(
            args.jobs_url,
            "end_run",
            {"run_id": started["run_id"], "status": "success", "notes": args.notes},
        )
        if not isinstance(ended, dict) or ended.get("run_id") != started["run_id"]:
            summary["checks"]["jobs_end_run"] = {
                "status": "fail",
                "result": ended,
                "error": "end_run returned an unexpected result shape",
            }
            raise RuntimeError("end_run returned an unexpected result shape")
        summary["checks"]["jobs_end_run"] = {"status": "pass", "run": ended}
        summary["host_run"] = ended

        listed_runs = call_tool(
            args.jobs_url,
            "list_runs",
            {
                "env": args.env,
                "service": args.service,
                "packet_id": packet_id,
                "status": "success",
            },
        )
        if not isinstance(listed_runs, dict) or not isinstance(listed_runs.get("runs"), list):
            summary["checks"]["jobs_list_runs"] = {
                "status": "fail",
                "result": listed_runs,
                "error": "list_runs returned an unexpected result shape",
            }
            raise RuntimeError("list_runs returned an unexpected result shape")

        matching_run = next(
            (
                run for run in listed_runs["runs"]
                if run.get("run_id") == ended["run_id"]
                and run.get("packet_id") == packet_id
                and run.get("env") == args.env
                and run.get("status") == "success"
            ),
            None,
        )
        if matching_run is None:
            summary["checks"]["jobs_list_runs"] = {
                "status": "fail",
                "result": listed_runs,
                "error": "list_runs did not return the just-completed promotion-eligible run",
            }
            raise RuntimeError("list_runs did not return the just-completed promotion-eligible run")
        summary["checks"]["jobs_list_runs"] = {"status": "pass", "result": listed_runs}
        summary["host_success_runs"] = listed_runs["runs"]

        try:
            promoted = call_tool(args.jobs_url, "promote_packet", {"packet_id": packet_id})
        except Exception as error:  # noqa: BLE001
            summary["checks"]["jobs_promote_packet"] = {
                "status": "fail",
                "result": None,
                "error": str(error),
            }
            raise
        if not isinstance(promoted, dict) or promoted.get("packet_id") != packet_id:
            summary["checks"]["jobs_promote_packet"] = {
                "status": "fail",
                "result": promoted,
                "error": "promote_packet returned an unexpected result shape",
            }
            raise RuntimeError("promote_packet returned an unexpected result shape")
        summary["checks"]["jobs_promote_packet"] = {"status": "pass", "result": promoted}
        summary["promotion"] = promoted

        summary["result"] = "PASS"
        return emit_summary(output_path, summary, 0)
    except Exception as error:  # noqa: BLE001
        summary["result"] = "FAIL"
        summary["error"] = str(error)
        return emit_summary(output_path, summary, 1)


if __name__ == "__main__":
    raise SystemExit(main())