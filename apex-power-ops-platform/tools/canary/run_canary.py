from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _fetch_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _mcp_tools(endpoint: str) -> list[str]:
    _fetch_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "apex-canary", "version": "0.1.0"}},
        },
    )
    response = _fetch_json(endpoint, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = response.get("result", {}).get("tools", [])
    return [tool["name"] for tool in tools]


def _render_chart(app_dir: Path, app_name: str) -> str:
    template_names = ["configmap.yaml", "service.yaml", "deployment.yaml"]
    rendered_parts: list[str] = []
    for template_name in template_names:
        template_path = app_dir / "templates" / template_name
        content = template_path.read_text(encoding="utf-8").strip()
        rendered_parts.append(f"---\n# Source: {app_name}/templates/{template_name}\n{content}\n")
    return "".join(rendered_parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh bounded Olares canary artifacts.")
    parser.add_argument("--output-root", default=str(_repo_root() / "tests" / "canary"))
    parser.add_argument("--forms-runtime-url", default=os.getenv("APEX_FORMS_RUNTIME_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--p6-runtime-url", default=os.getenv("APEX_P6_RUNTIME_URL", "http://127.0.0.1:8081"))
    parser.add_argument("--fs-mcp-url", default=os.getenv("APEX_FS_MCP_URL", "http://127.0.0.1:8710/mcp"))
    parser.add_argument("--db-mcp-url", default=os.getenv("APEX_DB_MCP_URL", "http://127.0.0.1:8711/mcp"))
    parser.add_argument("--jobs-mcp-url", default=os.getenv("APEX_JOBS_MCP_URL", "http://127.0.0.1:8712/mcp"))
    parser.add_argument("--p6-mcp-url", default=os.getenv("APEX_P6_MCP_URL", "http://127.0.0.1:8713/mcp"))
    parser.add_argument("--forms-mcp-url", default=os.getenv("APEX_FORMS_MCP_URL", "http://127.0.0.1:8714/mcp"))
    args = parser.parse_args()

    repo_root = _repo_root()
    output_root = Path(args.output_root)

    forms_health = _fetch_json(f"{args.forms_runtime_url.rstrip('/')}/health")
    p6_health = _fetch_json(f"{args.p6_runtime_url.rstrip('/')}/health")
    p6_summary = _fetch_json(f"{args.p6_runtime_url.rstrip('/')}/fixtures/stack-data-center")

    mcp_contract = {
        "apex-fs": {"endpoint": args.fs_mcp_url, "tools": _mcp_tools(args.fs_mcp_url)},
        "apex-db": {"endpoint": args.db_mcp_url, "tools": _mcp_tools(args.db_mcp_url)},
        "apex-jobs": {"endpoint": args.jobs_mcp_url, "tools": _mcp_tools(args.jobs_mcp_url)},
        "apex-forms": {"endpoint": args.forms_mcp_url, "tools": _mcp_tools(args.forms_mcp_url)},
        "apex-p6": {"endpoint": args.p6_mcp_url, "tools": _mcp_tools(args.p6_mcp_url)},
    }

    _write_json(output_root / "forms-engine-dev-runtime" / "actual" / "health.json", forms_health)
    _write_json(output_root / "apex-forms-runtime-status" / "actual" / "health.json", forms_health)
    _write_json(output_root / "p6-ingest-dev-runtime" / "actual" / "health.json", p6_health)
    _write_json(output_root / "p6-ingest-dev-runtime" / "actual" / "summary.json", p6_summary)
    _write_json(output_root / "p6-ingest-stack-fixture" / "actual" / "summary.json", p6_summary)
    _write_json(output_root / "apex-p6-stack-summary" / "actual" / "summary.json", p6_summary)
    _write_json(output_root / "mcp-contract" / "actual" / "mcp-tool-lists.json", mcp_contract)

    forms_dir = repo_root / "infra" / "olares" / "forms-engine"
    p6_dir = repo_root / "infra" / "olares" / "p6-ingest"

    _write_text(
        output_root / "forms-engine-staging-manifest" / "actual" / "OlaresManifest.yaml",
        (forms_dir / "OlaresManifest.yaml").read_text(encoding="utf-8"),
    )
    _write_text(
        output_root / "p6-ingest-staging-manifest" / "actual" / "OlaresManifest.yaml",
        (p6_dir / "OlaresManifest.yaml").read_text(encoding="utf-8"),
    )
    _write_text(
        output_root / "forms-engine-staging-render" / "actual" / "rendered-chart.yaml",
        _render_chart(forms_dir, "forms-engine"),
    )
    _write_text(
        output_root / "p6-ingest-staging-render" / "actual" / "rendered-chart.yaml",
        _render_chart(p6_dir, "p6-ingest"),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
