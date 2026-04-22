from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib import error, parse, request


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://REQUIRED-PUBLIC-ROOT.example.com"
DEFAULT_TOKEN_ENV = "PUBLIC_CONTROL_PLANE_BEARER_TOKEN"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test the deployed public Desktop discovery surface and authenticated control-plane access "
            "using a real bearer token."
        )
    )
    parser.add_argument("--base-url", required=True, help="Public base URL for the deployed backend.")
    parser.add_argument(
        "--bearer-token",
        help="Bearer token for the deployed control-plane. If omitted, read from --token-env.",
    )
    parser.add_argument(
        "--token-env",
        default=DEFAULT_TOKEN_ENV,
        help="Environment variable containing the bearer token when --bearer-token is omitted.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="How many task packet summaries to request during the authenticated proof.",
    )
    parser.add_argument(
        "--lane",
        help="Optional lane filter to include in the authenticated task-packet request.",
    )
    parser.add_argument(
        "--task-id",
        help="Optional task packet id to fetch after the summary-list proof succeeds.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="HTTP timeout for each request.",
    )
    return parser


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout_seconds: int,
) -> tuple[int, Any]:
    merged_headers = {"Accept": "application/json"}
    if headers:
        merged_headers.update(headers)

    req = request.Request(url, headers=merged_headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw.strip() else {}
            return response.status, payload
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail) if detail.strip() else {"detail": exc.reason}
        except json.JSONDecodeError:
            payload = {"detail": detail or exc.reason}
        return exc.code, payload
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc


def _print_json(label: str, payload: Any) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True))


def _resolve_token(args: argparse.Namespace) -> str:
    token = (args.bearer_token or os.getenv(args.token_env, "")).strip()
    if not token:
        raise RuntimeError(
            f"A bearer token is required. Pass --bearer-token or set {args.token_env}."
        )
    return token


def _build_task_packet_url(args: argparse.Namespace) -> str:
    query = {"limit": str(args.limit)}
    if args.lane:
        query["lane"] = args.lane
    return args.base_url.rstrip("/") + "/api/v1/control-plane/task-packets?" + parse.urlencode(query)


def main() -> int:
    args = build_parser().parse_args()

    try:
        token = _resolve_token(args)
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 2

    print("PUBLIC_CONTROL_PLANE_ACCESS_SMOKE")
    print(f"BASE_URL {args.base_url}")
    print(f"TOKEN_ENV {args.token_env}")
    if args.lane:
        print(f"LANE_FILTER {args.lane}")
    if args.task_id:
        print(f"TASK_ID {args.task_id}")

    failures: list[str] = []

    config_url = args.base_url.rstrip("/") + "/api/v1/auth/public-desktop-config"
    discovery_url = args.base_url.rstrip("/") + "/.well-known/oauth-authorization-server"
    mcp_url = args.base_url.rstrip("/") + "/mcp"
    packet_list_url = _build_task_packet_url(args)

    try:
        config_status, config_payload = _request_json(
            "GET", config_url, timeout_seconds=args.timeout_seconds
        )
        discovery_status, discovery_payload = _request_json(
            "GET", discovery_url, timeout_seconds=args.timeout_seconds
        )
        mcp_status, mcp_payload = _request_json(
            "GET", mcp_url, timeout_seconds=args.timeout_seconds
        )
        packet_status, packet_payload = _request_json(
            "GET",
            packet_list_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 1

    print(f"CONFIG_STATUS {config_status}")
    _print_json("CONFIG_PAYLOAD", config_payload)
    print(f"DISCOVERY_STATUS {discovery_status}")
    _print_json("DISCOVERY_PAYLOAD", discovery_payload)
    print(f"MCP_STATUS {mcp_status}")
    _print_json("MCP_PAYLOAD", mcp_payload)
    print(f"TASK_PACKET_LIST_STATUS {packet_status}")
    _print_json("TASK_PACKET_LIST_PAYLOAD", packet_payload)

    if config_status != 200 or not config_payload.get("configured"):
        failures.append("public desktop config endpoint is not configured on the deployed host")
    if discovery_status != 200:
        failures.append("OAuth discovery endpoint did not return HTTP 200 on the deployed host")
    if mcp_status != 200:
        failures.append("MCP root endpoint did not return HTTP 200 on the deployed host")
    if packet_status != 200:
        failures.append("authenticated task-packet list request did not return HTTP 200")
    elif not isinstance(packet_payload, list):
        failures.append("authenticated task-packet list response was not a JSON array")

    if args.task_id:
        fetch_url = args.base_url.rstrip("/") + f"/api/v1/control-plane/task-packets/{parse.quote(args.task_id)}"
        try:
            fetch_status, fetch_payload = _request_json(
                "GET",
                fetch_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout_seconds=args.timeout_seconds,
            )
        except Exception as exc:
            print("RESULT FAIL")
            print(f"- {exc}")
            return 1

        print(f"TASK_PACKET_FETCH_STATUS {fetch_status}")
        _print_json("TASK_PACKET_FETCH_PAYLOAD", fetch_payload)

        if fetch_status != 200:
            failures.append("authenticated task-packet fetch request did not return HTTP 200")
        elif str(fetch_payload.get("task_id") or "") != args.task_id:
            failures.append("authenticated task-packet fetch response did not match the requested task_id")

    if failures:
        print("RESULT FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())