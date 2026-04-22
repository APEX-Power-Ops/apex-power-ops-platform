from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.auth import (
    GITHUB_MCP_OAUTH_SURFACE_ENV,
    SUPABASE_MCP_OAUTH_SURFACE_ENV,
    OAuthSurfaceEnv,
    describe_oauth_surface,
    get_oauth_protected_resource_metadata,
    get_oauth_server_metadata,
)


SURFACE_CONFIG: dict[str, dict[str, Any]] = {
    "supabase": {
        "surface_env": SUPABASE_MCP_OAUTH_SURFACE_ENV,
        "path": "/supabase-mcp",
        "required_envs": [
            "SUPABASE_ALLOWED_PROJECTS_JSON",
            "SUPABASE_MANAGEMENT_TOKEN",
        ],
        "write_ready_envs": [
            "SUPABASE_ENABLE_MIGRATION_APPLY",
            "SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY",
            "SUPABASE_ACCESS_TOKEN",
        ],
    },
    "github": {
        "surface_env": GITHUB_MCP_OAUTH_SURFACE_ENV,
        "path": "/github-mcp",
        "required_envs": [
            "GITHUB_ALLOWED_REPOS_JSON",
            "GITHUB_APP_ID",
            "GITHUB_APP_PRIVATE_KEY",
            "GITHUB_APP_INSTALLATION_IDS_JSON",
        ],
        "write_ready_envs": [],
    },
}


def _fetch_json(url: str) -> tuple[int, Any]:
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(body) if body else {"detail": exc.reason}
        except json.JSONDecodeError:
            payload = {"detail": body or exc.reason}
        return exc.code, payload
    except URLError as exc:
        raise RuntimeError(f"HTTP fetch failed for {url}: {exc}") from exc


def _print_json_block(label: str, payload: Any) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True))


def _is_nonempty_env(name: str) -> bool:
    import os

    return bool(str(os.getenv(name, "")).strip())


def _validate_local_surface(
    surface_name: str,
    surface_env: OAuthSurfaceEnv,
    *,
    require_ready: bool,
    require_write_ready: bool,
) -> tuple[dict[str, Any], list[str]]:
    config = SURFACE_CONFIG[surface_name]
    failures: list[str] = []
    surface = describe_oauth_surface(surface_env)
    print(f"{surface_name.upper()}_LOCAL_SURFACE")
    print(json.dumps(surface, indent=2, sort_keys=True))

    failures.extend(surface["validation_errors"])
    if require_ready and not surface["public_activation_ready"]:
        failures.append(f"{surface_name} OAuth surface is not activation-ready")

    for env_name in config["required_envs"]:
        if not _is_nonempty_env(env_name):
            failures.append(f"{surface_name} missing required environment variable: {env_name}")

    if require_write_ready:
        for env_name in config["write_ready_envs"]:
            if not _is_nonempty_env(env_name):
                failures.append(f"{surface_name} missing write-readiness environment variable: {env_name}")

    try:
        discovery = get_oauth_server_metadata(surface_env)
        _print_json_block(f"{surface_name.upper()}_LOCAL_DISCOVERY_METADATA", discovery)
    except RuntimeError as exc:
        print(f"{surface_name.upper()}_LOCAL_DISCOVERY_METADATA_ERROR {exc}")
        if require_ready:
            failures.append(str(exc))

    try:
        protected = get_oauth_protected_resource_metadata(surface_env)
        _print_json_block(f"{surface_name.upper()}_LOCAL_PROTECTED_RESOURCE_METADATA", protected)
    except RuntimeError as exc:
        print(f"{surface_name.upper()}_LOCAL_PROTECTED_RESOURCE_METADATA_ERROR {exc}")
        if require_ready:
            failures.append(str(exc))

    return surface, failures


def _validate_live_surface(surface_name: str, base_url: str, expected_surface: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    normalized = base_url.rstrip("/")
    path = SURFACE_CONFIG[surface_name]["path"]

    discovery_status, discovery_payload = _fetch_json(f"{normalized}{path}/.well-known/oauth-authorization-server")
    protected_status, protected_payload = _fetch_json(f"{normalized}{path}/.well-known/oauth-protected-resource")
    root_status, root_payload = _fetch_json(f"{normalized}{path}")

    print(f"{surface_name.upper()}_LIVE_DISCOVERY_STATUS {discovery_status}")
    _print_json_block(f"{surface_name.upper()}_LIVE_DISCOVERY_PAYLOAD", discovery_payload)
    print(f"{surface_name.upper()}_LIVE_PROTECTED_RESOURCE_STATUS {protected_status}")
    _print_json_block(f"{surface_name.upper()}_LIVE_PROTECTED_RESOURCE_PAYLOAD", protected_payload)
    print(f"{surface_name.upper()}_LIVE_ROOT_STATUS {root_status}")
    _print_json_block(f"{surface_name.upper()}_LIVE_ROOT_PAYLOAD", root_payload)

    if discovery_status != 200:
        failures.append(f"{surface_name} OAuth discovery endpoint did not return HTTP 200")
    else:
        expected_issuer = expected_surface.get("issuer")
        if expected_issuer and discovery_payload.get("issuer") != expected_issuer:
            failures.append(f"{surface_name} OAuth discovery issuer does not match the configured issuer")

    if protected_status != 200:
        failures.append(f"{surface_name} protected-resource endpoint did not return HTTP 200")
    else:
        expected_resource = expected_surface.get("public_mcp_base_url")
        if expected_resource and protected_payload.get("resource") != expected_resource:
            failures.append(f"{surface_name} protected-resource resource does not match the configured MCP base URL")

    if root_status != 200:
        failures.append(f"{surface_name} MCP root endpoint did not return HTTP 200")
    else:
        if not root_payload.get("oauth_discovery_url"):
            failures.append(f"{surface_name} MCP root endpoint did not expose oauth_discovery_url")
        if not root_payload.get("approved_tools"):
            failures.append(f"{surface_name} MCP root endpoint did not expose approved_tools")

    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the dedicated Supabase and GitHub MCP OAuth/MCP surfaces."
    )
    parser.add_argument(
        "--surface",
        choices=["all", "supabase", "github"],
        default="all",
        help="Which dedicated surface to validate.",
    )
    parser.add_argument(
        "--supabase-base-url",
        help="Optional deployed base URL to probe for the dedicated Supabase MCP surface.",
    )
    parser.add_argument(
        "--github-base-url",
        help="Optional deployed base URL to probe for the dedicated GitHub MCP surface.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail unless the selected local OAuth surface is fully activation-ready.",
    )
    parser.add_argument(
        "--require-write-ready",
        action="store_true",
        help="Fail unless the selected surface also has the write-execution env contract present.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selected = [args.surface] if args.surface != "all" else ["supabase", "github"]
    failures: list[str] = []

    print("DEDICATED_MCP_SURFACE_CHECK")
    for surface_name in selected:
        config = SURFACE_CONFIG[surface_name]
        surface, local_failures = _validate_local_surface(
            surface_name,
            config["surface_env"],
            require_ready=args.require_ready,
            require_write_ready=args.require_write_ready,
        )
        failures.extend(local_failures)

        base_url = args.supabase_base_url if surface_name == "supabase" else args.github_base_url
        if base_url:
            failures.extend(_validate_live_surface(surface_name, base_url, surface))

    if failures:
        deduped: list[str] = []
        seen: set[str] = set()
        for failure in failures:
            if failure in seen:
                continue
            seen.add(failure)
            deduped.append(failure)
        print("RESULT FAIL")
        for failure in deduped:
            print(f"- {failure}")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())