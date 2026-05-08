from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import uuid
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
    fetch_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "apex-ai-workflow-verify", "version": "0.1.0"},
            },
        },
    )
    response = fetch_json(endpoint, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    return [tool["name"] for tool in response.get("result", {}).get("tools", [])]


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the minimal MCP trio operator surface.")
    parser.add_argument("--fs-url", default=os.getenv("APEX_FS_MCP_URL", "http://127.0.0.1:8710/mcp"))
    parser.add_argument("--db-url", default=os.getenv("APEX_DB_MCP_URL", "http://127.0.0.1:8711/mcp"))
    parser.add_argument("--jobs-url", default=os.getenv("APEX_JOBS_MCP_URL", "http://127.0.0.1:8712/mcp"))
    parser.add_argument("--packet-id", default="2026-05-06-olares-dev-residency-037")
    parser.add_argument("--output")
    parser.add_argument("--require-db-query", action="store_true")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    summary: dict[str, Any] = {
        "packet_id": args.packet_id,
        "endpoints": {"fs": args.fs_url, "db": args.db_url, "jobs": args.jobs_url},
        "checks": {},
    }

    try:
        fs_tools = initialize_and_list(args.fs_url)
        summary["checks"]["fs_tools"] = {"status": "pass", "tools": fs_tools}
        fs_read = call_tool(
            args.fs_url,
            "read_text_file",
            {"root": "workspace", "relativePath": "README.md", "maxBytes": 120},
        )
        summary["checks"]["fs_read"] = {"status": "pass", "preview": fs_read["content"][:120]}

        db_tools = initialize_and_list(args.db_url)
        summary["checks"]["db_tools"] = {"status": "pass", "tools": db_tools}
        try:
            db_query = call_tool(args.db_url, "query", {"sql": "select 1 as ok"})
            summary["checks"]["db_query"] = {"status": "pass", "result": db_query}
        except Exception as error:  # noqa: BLE001
            status = "fail" if args.require_db_query else "degraded"
            summary["checks"]["db_query"] = {"status": status, "error": str(error)}
            if args.require_db_query:
                raise

        jobs_tools = initialize_and_list(args.jobs_url)
        summary["checks"]["jobs_tools"] = {"status": "pass", "tools": jobs_tools}
        promote_probe_packet_id = f"{args.packet_id}-promote-guard-{uuid.uuid4().hex[:8]}"
        try:
            call_tool(args.jobs_url, "promote_packet", {"packet_id": promote_probe_packet_id})
            raise RuntimeError(
                "promote_packet unexpectedly succeeded without any successful env=host run on record"
            )
        except RuntimeError as error:
            detail = str(error)
            if "no successful env=host run is on record" not in detail:
                raise
            summary["checks"]["jobs_promote_guard"] = {
                "status": "pass",
                "packet_id": promote_probe_packet_id,
                "detail": detail,
            }
        started = call_tool(
            args.jobs_url,
            "start_run",
            {"env": "sandbox", "service": "ai-workflow", "packet_id": args.packet_id},
        )
        summary["checks"]["jobs_start_run"] = {"status": "pass", "run": started}
        ended = call_tool(
            args.jobs_url,
            "end_run",
            {"run_id": started["run_id"], "status": "success", "notes": "minimal-mcp-trio verification"},
        )
        summary["checks"]["jobs_end_run"] = {"status": "pass", "run": ended}

        summary["result"] = "PASS"
        write_output(output_path, summary)
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as error:  # noqa: BLE001
        summary["result"] = "FAIL"
        summary["error"] = str(error)
        write_output(output_path, summary)
        print(json.dumps(summary, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())