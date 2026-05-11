from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def fetch_json(url: str, payload: dict[str, Any]) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def call_tool(endpoint: str, name: str, arguments: dict[str, Any] | None = None) -> Any:
    response = fetch_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
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


def normalize_path(value: str) -> str:
    return os.path.normcase(os.path.realpath(os.path.normpath(value)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that a live apex-fs endpoint belongs to the current repo root.")
    parser.add_argument("--fs-url", required=True)
    parser.add_argument("--expected-workspace-root", required=True)
    parser.add_argument("--expected-readme-path")
    args = parser.parse_args()

    expected_workspace_root = normalize_path(args.expected_workspace_root)
    expected_readme_preview = None
    if args.expected_readme_path:
        expected_readme_preview = Path(args.expected_readme_path).read_text(encoding="utf-8")[:120]

    try:
        fetch_json(
            args.fs_url,
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "apex-fs-ownership-check", "version": "0.1.0"},
                },
            },
        )
        roots = call_tool(args.fs_url, "list_roots")
        workspace_root = str(roots.get("workspace") or "")
        normalized_workspace_root = normalize_path(workspace_root) if workspace_root else ""

        payload: dict[str, Any] = {
            "status": "owned",
            "workspace_root": workspace_root,
            "expected_workspace_root": args.expected_workspace_root,
        }

        if expected_readme_preview is not None:
            actual_readme = call_tool(
                args.fs_url,
                "read_text_file",
                {"root": "workspace", "relativePath": "README.md", "maxBytes": 120},
            )
            actual_readme_preview = str(actual_readme.get("content") or "")[:120]
            payload["readme_preview"] = actual_readme_preview
            payload["expected_readme_preview"] = expected_readme_preview

        if normalized_workspace_root != expected_workspace_root:
            payload["status"] = "adoption-refused"
            payload["reason"] = "workspace-root-mismatch"
            print(json.dumps(payload))
            return 1

        if expected_readme_preview is not None and payload.get("readme_preview") != expected_readme_preview:
            payload["status"] = "adoption-refused"
            payload["reason"] = "readme-preview-mismatch"
            print(json.dumps(payload))
            return 1

        print(json.dumps(payload))
        return 0
    except Exception as error:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "status": "adoption-refused",
                    "reason": "fs-ownership-probe-failed",
                    "expected_workspace_root": args.expected_workspace_root,
                    "detail": str(error),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())