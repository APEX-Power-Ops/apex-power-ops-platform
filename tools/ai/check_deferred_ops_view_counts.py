from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def import_env_file() -> None:
    root = repo_root()
    env_file = root / ".env.dev"
    if not env_file.exists():
        env_file = root / ".env.dev.template"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip())


def resolve_db_url(args: argparse.Namespace) -> tuple[str, str]:
    import_env_file()

    if args.db_url:
        return args.db_url, "argument:db-url"

    if args.db_url_env:
        value = str(os.getenv(args.db_url_env) or "").strip()
        if value:
            return value, f"env:{args.db_url_env}"
        raise RuntimeError(f"{args.db_url_env} is not set; cannot run deferred ops view checks.")

    if os.getenv("APEX_DB_MCP_URL"):
        return os.environ["APEX_DB_MCP_URL"], "env:APEX_DB_MCP_URL"

    db_port = os.getenv("APEX_DEV_MCP_DB_PORT", "8811")
    return f"http://127.0.0.1:{db_port}/mcp", "default:apex-db-mcp"


def resolve_connection_string(args: argparse.Namespace) -> tuple[str, str] | None:
    import_env_file()

    if args.db_connection_string:
        return args.db_connection_string, "argument:db-connection-string"

    if args.db_connection_string_env:
        value = str(os.getenv(args.db_connection_string_env) or "").strip()
        if value:
            return value, f"env:{args.db_connection_string_env}"
        raise RuntimeError(f"{args.db_connection_string_env} is not set; cannot run deferred ops view checks.")

    return None


def fetch_json(url: str, payload: dict[str, Any]) -> Any:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def initialize_and_query(db_url: str, sql: str) -> Any:
    initialize_response = fetch_json(
        db_url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "apex-deferred-ops-check", "version": "0.1.0"},
            },
        },
    )
    initialize_result = initialize_response.get("result", {})
    if initialize_result.get("isError"):
        content = initialize_result.get("content", [])
        detail = content[0].get("text") if content else "Unknown MCP error"
        raise RuntimeError(detail)
    response = fetch_json(
        db_url,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "query", "arguments": {"sql": sql}},
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


def query_direct_connection(connection_string: str, sql: str) -> Any:
    try:
        from sqlalchemy import create_engine, text
    except ImportError as error:  # pragma: no cover - exercised only when SQLAlchemy is absent
        raise RuntimeError("SQLAlchemy is required for direct deferred ops view checks.") from error

    engine = create_engine(connection_string)
    with engine.connect() as connection:
        rows = connection.execute(text(sql))
        return [dict(row._mapping) for row in rows]


def normalize_query_rows(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, list):
        return [dict(row) for row in result]

    if isinstance(result, dict):
        rows = result.get("rows")
        if isinstance(rows, list):
            return [dict(row) for row in rows]

    raise RuntimeError("Deferred ops view check received an unexpected query result shape.")


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
    return f"adhoc-deferred-ops-view-counts-{timestamp}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether deferred Operations Visibility views have live rows.")
    parser.add_argument("--packet-id")
    parser.add_argument("--db-url")
    parser.add_argument("--db-url-env")
    parser.add_argument("--db-connection-string")
    parser.add_argument("--db-connection-string-env")
    parser.add_argument("--output")
    args = parser.parse_args()

    packet_id = resolve_packet_id(args.packet_id)
    output_path = Path(args.output) if args.output else None
    summary: dict[str, Any] = {
        "packet_id": packet_id,
        "repo_root": str(repo_root()),
        "checks": {},
    }

    sql = """
        select 'v_resource_allocation' as view_name, count(*) as row_count
        from public.v_resource_allocation
        union all
        select 'v_equipment_needs' as view_name, count(*) as row_count
        from public.v_equipment_needs
        order by view_name
    """

    try:
        connection_string = resolve_connection_string(args)
        if connection_string is not None:
            value, source = connection_string
            summary["checks"]["db_connection"] = {
                "status": "pass",
                "source": source,
                "mode": "direct",
            }
            rows = query_direct_connection(value, sql)
        else:
            db_url, db_url_source = resolve_db_url(args)
            summary["checks"]["db_connection"] = {
                "status": "pass",
                "source": db_url_source,
                "mode": "mcp",
                "endpoint": db_url,
            }

            try:
                rows = initialize_and_query(db_url, sql)
            except RuntimeError as error:
                if "relation \"public.v_resource_allocation\" does not exist" not in str(error):
                    raise
                summary["checks"]["deferred_view_counts"] = {
                    "status": "unavailable",
                    "reason": "The current apex-db surface does not expose the authoritative deferred operations views.",
                }
                summary["result"] = "UNAVAILABLE"
                summary["decision"] = (
                    "Authoritative deferred view counts require apex-db to run against a live DSN such as SEAM_DATABASE_URL; "
                    "the current database surface is not sufficient for this hold check."
                )
                return emit_summary(output_path, summary, 0)

        normalized_rows = normalize_query_rows(rows)
        counts = {row["view_name"]: int(row["row_count"]) for row in normalized_rows}
        reopen = [name for name, row_count in counts.items() if row_count > 0]

        summary["checks"]["deferred_view_counts"] = {
            "status": "pass",
            "counts": counts,
        }
        summary["result"] = "REOPEN" if reopen else "HOLD"
        summary["reopen_candidates"] = reopen
        summary["decision"] = (
            "One or more deferred Operations Visibility seams now have live rows."
            if reopen
            else "Deferred Operations Visibility seams remain empty and should stay on hold."
        )
        return emit_summary(output_path, summary, 0)
    except Exception as error:  # noqa: BLE001
        summary["result"] = "FAIL"
        summary["error"] = str(error)
        return emit_summary(output_path, summary, 1)


if __name__ == "__main__":
    raise SystemExit(main())