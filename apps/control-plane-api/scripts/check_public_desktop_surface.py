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

from services.auth import describe_public_oauth_surface, get_public_oauth_server_metadata


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


def _validate_live_surface(base_url: str, expected_surface: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    normalized = base_url.rstrip("/")

    config_status, config_payload = _fetch_json(f"{normalized}/api/v1/auth/public-desktop-config")
    discovery_status, discovery_payload = _fetch_json(
        f"{normalized}/.well-known/oauth-authorization-server"
    )
    protected_status, protected_payload = _fetch_json(
        f"{normalized}/.well-known/oauth-protected-resource"
    )
    root_status, root_payload = _fetch_json(f"{normalized}/mcp")

    print(f"LIVE_CONFIG_STATUS {config_status}")
    _print_json_block("LIVE_CONFIG_PAYLOAD", config_payload)
    print(f"LIVE_DISCOVERY_STATUS {discovery_status}")
    _print_json_block("LIVE_DISCOVERY_PAYLOAD", discovery_payload)
    print(f"LIVE_PROTECTED_RESOURCE_STATUS {protected_status}")
    _print_json_block("LIVE_PROTECTED_RESOURCE_PAYLOAD", protected_payload)
    print(f"LIVE_MCP_ROOT_STATUS {root_status}")
    _print_json_block("LIVE_MCP_ROOT_PAYLOAD", root_payload)

    if config_status != 200:
        failures.append("public desktop config endpoint did not return HTTP 200")
    elif not config_payload.get("configured"):
        failures.append("public desktop config endpoint reports configured=false")

    if discovery_status != 200:
        failures.append("OAuth discovery endpoint did not return HTTP 200")
    elif not discovery_payload.get("issuer"):
        failures.append("OAuth discovery endpoint did not expose an issuer")
    else:
        expected_issuer = expected_surface.get("issuer")
        if expected_issuer and discovery_payload.get("issuer") != expected_issuer:
            failures.append(
                "OAuth discovery endpoint issuer does not match the configured target issuer"
            )
        expected_authorization_url = expected_surface.get("authorization_url")
        if (
            expected_authorization_url
            and discovery_payload.get("authorization_endpoint") != expected_authorization_url
        ):
            failures.append(
                "OAuth discovery endpoint authorization_endpoint does not match the configured target value"
            )
        expected_token_url = expected_surface.get("token_url")
        if expected_token_url and discovery_payload.get("token_endpoint") != expected_token_url:
            failures.append(
                "OAuth discovery endpoint token_endpoint does not match the configured target value"
            )
        expected_jwks_url = expected_surface.get("jwks_url")
        if expected_jwks_url and discovery_payload.get("jwks_uri") != expected_jwks_url:
            failures.append(
                "OAuth discovery endpoint jwks_uri does not match the configured target value"
            )

    if protected_status != 200:
        failures.append("OAuth protected-resource endpoint did not return HTTP 200")
    else:
        expected_resource = expected_surface.get("public_mcp_base_url")
        if expected_resource and protected_payload.get("resource") != expected_resource:
            failures.append(
                "OAuth protected-resource endpoint resource does not match the configured MCP base URL"
            )
        expected_authorization_servers = [expected_surface["issuer"]] if expected_surface.get("issuer") else []
        if expected_authorization_servers and protected_payload.get("authorization_servers") != expected_authorization_servers:
            failures.append(
                "OAuth protected-resource endpoint authorization_servers do not match the configured issuer"
            )

    if root_status != 200:
        failures.append("MCP root endpoint did not return HTTP 200")
    elif not root_payload.get("oauth_discovery_url"):
        failures.append("MCP root endpoint did not expose an oauth_discovery_url")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the governed public Desktop MCP/OAuth surface configuration."
    )
    parser.add_argument(
        "--base-url",
        help="Optional deployed public base URL to probe over HTTP in addition to local environment validation.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail unless the local configuration is fully ready for public activation.",
    )
    args = parser.parse_args()

    failures: list[str] = []

    local_surface = describe_public_oauth_surface()
    print("PUBLIC_DESKTOP_SURFACE_CHECK")
    _print_json_block("LOCAL_SURFACE", local_surface)

    if local_surface["validation_errors"]:
        failures.extend(local_surface["validation_errors"])

    if args.require_ready and not local_surface["public_activation_ready"]:
        failures.append("local public desktop configuration is not activation-ready")

    try:
        discovery_metadata = get_public_oauth_server_metadata()
        _print_json_block("LOCAL_DISCOVERY_METADATA", discovery_metadata)
    except RuntimeError as exc:
        print(f"LOCAL_DISCOVERY_METADATA_ERROR {exc}")
        if args.require_ready:
            failures.append(str(exc))

    if args.base_url:
        failures.extend(_validate_live_surface(args.base_url, local_surface))

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