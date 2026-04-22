from __future__ import annotations

import argparse
import json
import os
from urllib import error, request


DEFAULT_OWNER = "jasonlswenson-sys"
DEFAULT_REPO = "apex-power-ops-platform"
DEFAULT_EVENT_TYPE = "dedicated-mcp-surfaces-deploy-complete"
DEFAULT_TOKEN_ENV = "GITHUB_REPOSITORY_DISPATCH_TOKEN"
DEFAULT_API_URL = "https://api.github.com"
DEFAULT_SUPABASE_BASE_URL = "https://supabase-mcp.apexpowerops.com"
DEFAULT_GITHUB_BASE_URL = "https://github-mcp.apexpowerops.com"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Trigger the dedicated MCP surface readiness workflow through GitHub repository_dispatch. "
            "Use this after Render/Auth0/GitHub connector env provisioning or host changes."
        )
    )
    parser.add_argument("--owner", default=DEFAULT_OWNER, help="GitHub repository owner.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository name.")
    parser.add_argument("--event-type", default=DEFAULT_EVENT_TYPE, help="repository_dispatch event type configured in the readiness workflow.")
    parser.add_argument("--supabase-base-url", default=DEFAULT_SUPABASE_BASE_URL, help="Public Supabase MCP base URL to validate.")
    parser.add_argument("--github-base-url", default=DEFAULT_GITHUB_BASE_URL, help="Public GitHub MCP base URL to validate.")
    parser.add_argument("--initial-wait-seconds", type=int, default=0, help="Optional propagation delay before the workflow starts validation.")
    parser.add_argument("--environment", default="production", help="Logical environment label to include in the dispatch payload.")
    parser.add_argument("--require-write-ready", action="store_true", help="Require the workflow to validate the confirmed-write env contract too.")
    parser.add_argument("--deploy-id", help="Optional deploy identifier to include in the dispatch payload for auditability.")
    parser.add_argument("--token", help="GitHub token with permission to send repository_dispatch events. If omitted, read from --token-env.")
    parser.add_argument("--token-env", default=DEFAULT_TOKEN_ENV, help="Environment variable that holds the GitHub token when --token is omitted.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="GitHub API base URL. Override only for GitHub Enterprise Server.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved dispatch request without sending it.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="HTTP timeout for the repository_dispatch request.")
    return parser


def _resolve_token(explicit_token: str | None, env_name: str) -> str:
    token = (explicit_token or os.getenv(env_name, "")).strip()
    if not token:
        raise RuntimeError(f"A GitHub token is required. Pass --token or set {env_name}.")
    return token


def _build_payload(args: argparse.Namespace) -> dict[str, object]:
    if args.initial_wait_seconds < 0:
        raise RuntimeError("--initial-wait-seconds must be a non-negative integer")

    client_payload: dict[str, object] = {
        "supabase_base_url": args.supabase_base_url.rstrip("/"),
        "github_base_url": args.github_base_url.rstrip("/"),
        "initial_wait_seconds": str(args.initial_wait_seconds),
        "environment": args.environment,
        "require_write_ready": "true" if args.require_write_ready else "false",
        "source": "dispatch_dedicated_mcp_surface_check.py",
    }
    if args.deploy_id:
        client_payload["deploy_id"] = args.deploy_id

    return {"event_type": args.event_type, "client_payload": client_payload}


def _build_dispatch_url(api_url: str, owner: str, repo: str) -> str:
    return f"{api_url.rstrip('/')}/repos/{owner}/{repo}/dispatches"


def _build_request(api_url: str, owner: str, repo: str, token: str, payload: dict[str, object]) -> request.Request:
    url = _build_dispatch_url(api_url, owner, repo)
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "apex-power-ops-platform-dispatch-dedicated-mcp-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return request.Request(url, data=body, headers=headers, method="POST")


def main() -> int:
    args = build_parser().parse_args()

    try:
        payload = _build_payload(args)
        dispatch_url = _build_dispatch_url(args.api_url, args.owner, args.repo)
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 2

    print("DEDICATED_MCP_SURFACE_CHECK_DISPATCH")
    print(f"OWNER {args.owner}")
    print(f"REPO {args.repo}")
    print(f"EVENT_TYPE {args.event_type}")
    print(f"SUPABASE_BASE_URL {payload['client_payload']['supabase_base_url']}")
    print(f"GITHUB_BASE_URL {payload['client_payload']['github_base_url']}")
    print(f"INITIAL_WAIT_SECONDS {payload['client_payload']['initial_wait_seconds']}")
    print(f"ENVIRONMENT {args.environment}")
    print(f"REQUIRE_WRITE_READY {payload['client_payload']['require_write_ready']}")
    if args.deploy_id:
        print(f"DEPLOY_ID {args.deploy_id}")

    if args.dry_run:
        print("RESULT DRY_RUN")
        print(json.dumps({"url": dispatch_url, "payload": payload, "token_env": args.token_env}, indent=2, sort_keys=True))
        return 0

    try:
        token = _resolve_token(args.token, args.token_env)
        dispatch_request = _build_request(args.api_url, args.owner, args.repo, token, payload)
    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 2

    try:
        with request.urlopen(dispatch_request, timeout=args.timeout_seconds) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print("RESULT FAIL")
        print(f"- GitHub API returned HTTP {exc.code}: {detail or exc.reason}")
        return 1
    except error.URLError as exc:
        print("RESULT FAIL")
        print(f"- Failed to reach GitHub API: {exc.reason}")
        return 1

    if status not in {200, 201, 202, 204}:
        print("RESULT FAIL")
        print(f"- Unexpected GitHub API status: {status} {body}")
        return 1

    print("RESULT PASS")
    print(f"DISPATCH_STATUS {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())