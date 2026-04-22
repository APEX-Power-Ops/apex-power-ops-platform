from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from urllib import error, request


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = (
    BACKEND_ROOT
    / "docs"
    / "contracts"
    / "CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json"
)
DEFAULT_BASE_URL = "http://127.0.0.1:8010"
DEFAULT_TEST_USER = "neta-test-a@example.com"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test the remote control-plane authoring queue over HTTP using local test auth."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Local FastAPI base URL.")
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to the remote control-plane tool schema JSON. Defaults to the platform-local contract copy.",
    )
    parser.add_argument(
        "--email",
        default=DEFAULT_TEST_USER,
        help="Local test auth user email for obtaining a bearer token.",
    )
    parser.add_argument("--task-id", required=True, help="Packet task id already approved for local action.")
    parser.add_argument(
        "--target-path",
        required=True,
        help="Exact packet-approved staging target path under Development/staging/.",
    )
    parser.add_argument(
        "--content",
        help="Inline content to queue for the authoring target. Mutually exclusive with --content-file.",
    )
    parser.add_argument(
        "--content-file",
        type=Path,
        help="File containing content to queue for the authoring target. Mutually exclusive with --content.",
    )
    parser.add_argument("--priority", default="normal", help="Queue priority to request.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Set request_payload.overwrite=true for existing target files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved auth and queue request without calling the live API.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="HTTP timeout for each request.",
    )
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_tool_schema(schema_path: Path, tool_name: str) -> dict[str, Any]:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema path not found: {schema_path}")
    payload = _load_json(schema_path)
    for tool in payload.get("tools") or []:
        if tool.get("name") == tool_name:
            return tool
    raise ValueError(f"Tool schema not found: {tool_name}")


def _load_content(args: argparse.Namespace) -> str:
    if args.content and args.content_file:
        raise ValueError("Use either --content or --content-file, not both")
    if args.content_file:
        return args.content_file.read_text(encoding="utf-8")
    if args.content is not None:
        return args.content
    raise ValueError("One of --content or --content-file is required")


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int,
) -> dict[str, Any]:
    body = None
    merged_headers = {"Accept": "application/json"}
    if headers:
        merged_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged_headers.setdefault("Content-Type", "application/json")

    req = request.Request(url, data=body, headers=merged_headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc

    if not raw.strip():
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object response from {url}")
    return parsed


def _build_queue_request(tool_schema: dict[str, Any], args: argparse.Namespace, content: str) -> dict[str, Any]:
    input_schema = tool_schema.get("inputSchema") or {}
    action_policy = (tool_schema.get("actionPolicies") or {}).get("write_staging_authoring_candidate") or {}
    priority_enum = ((input_schema.get("properties") or {}).get("priority") or {}).get("enum") or []
    if priority_enum and args.priority not in priority_enum:
        raise ValueError(f"Priority must be one of: {', '.join(priority_enum)}")

    if not str(args.target_path).strip().replace("\\", "/").startswith("Development/staging/"):
        raise ValueError("--target-path must remain under Development/staging/")

    return {
        "action_type": "write_staging_authoring_candidate",
        "task_id": args.task_id,
        "subject_type": action_policy.get("requiredSubjectType") or "authoring_target",
        "subject_id": args.target_path,
        "request_payload": {
            "path": args.target_path,
            "content": content,
            "overwrite": bool(args.overwrite),
        },
        "priority": args.priority,
        "confirmed_by_user": True,
    }


def main() -> int:
    args = build_parser().parse_args()

    try:
        content = _load_content(args)
        queue_tool = _load_tool_schema(args.schema_path, "queue_local_action")
        queue_request = _build_queue_request(queue_tool, args, content)
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 2

    auth_url = args.base_url.rstrip("/") + "/api/v1/auth/test-session"
    queue_url = args.base_url.rstrip("/") + "/api/v1/control-plane/local-actions"

    print("REMOTE_CONTROL_PLANE_AUTHORING_QUEUE_SMOKE")
    print(f"BASE_URL {args.base_url}")
    print(f"SCHEMA_PATH {args.schema_path}")
    print(f"TASK_ID {args.task_id}")
    print(f"TARGET_PATH {args.target_path}")
    print(f"TEST_USER {args.email}")

    if args.dry_run:
        print("RESULT DRY_RUN")
        print(
            json.dumps(
                {
                    "auth_request": {"email": args.email},
                    "auth_url": auth_url,
                    "queue_request": queue_request,
                    "queue_url": queue_url,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    try:
        auth_response = _request_json(
            "POST",
            auth_url,
            payload={"email": args.email},
            timeout_seconds=args.timeout_seconds,
        )
        access_token = str(auth_response.get("access_token") or "").strip()
        if not access_token:
            raise RuntimeError("Local test auth did not return an access_token")

        queue_response = _request_json(
            "POST",
            queue_url,
            payload=queue_request,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout_seconds=args.timeout_seconds,
        )
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 1

    print("RESULT PASS")
    print(json.dumps(queue_response, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())