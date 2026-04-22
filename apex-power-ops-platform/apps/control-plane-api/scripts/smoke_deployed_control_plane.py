from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any
from urllib import error, parse, request


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://REQUIRED-PUBLIC-ROOT.example.com"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_TOKEN_ENV = "PUBLIC_CONTROL_PLANE_BEARER_TOKEN"
DEFAULT_SUPABASE_URL_ENV = "SUPABASE_URL"
DEFAULT_SUPABASE_ANON_KEY_ENV = "SUPABASE_ANON_KEY"
DEFAULT_SUPABASE_SERVICE_ROLE_KEY_ENV = "SUPABASE_SERVICE_ROLE_KEY"
DEFAULT_APPARATUS_PROBE_ID = "00000000-0000-0000-0000-000000000000"
APPARATUS_STUDY_ROUTE_PATH = "/api/v1/neta/apparatus/{apparatus_id}/resources"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the target control-plane surface end to end. "
            "The script can use an existing bearer token or create a disposable confirmed Supabase user "
            "to obtain a real end-user access token for the authenticated proof."
        )
    )
    parser.add_argument("--base-url", required=True, help="Base URL for the target backend.")
    parser.add_argument(
        "--local-runtime",
        action="store_true",
        help=(
            "Validate a workstation-local runtime host instead of the public-host contract. "
            "This keeps health/readiness, control-plane auth behavior, and apparatus-route checks, "
            "but does not require public OAuth discovery or MCP metadata endpoints to return HTTP 200."
        ),
    )
    parser.add_argument(
        "--bearer-token",
        help="Bearer token for the deployed control-plane. If omitted, read from --token-env or mint a disposable user token.",
    )
    parser.add_argument(
        "--token-env",
        default=DEFAULT_TOKEN_ENV,
        help="Environment variable containing a bearer token when --bearer-token is omitted.",
    )
    parser.add_argument(
        "--supabase-url",
        help="Supabase project base URL. Required for disposable-user auth unless provided via env.",
    )
    parser.add_argument(
        "--supabase-url-env",
        default=DEFAULT_SUPABASE_URL_ENV,
        help="Environment variable containing SUPABASE_URL.",
    )
    parser.add_argument(
        "--supabase-anon-key",
        help="Supabase anon key. Required for disposable-user auth unless provided via env.",
    )
    parser.add_argument(
        "--supabase-anon-key-env",
        default=DEFAULT_SUPABASE_ANON_KEY_ENV,
        help="Environment variable containing SUPABASE_ANON_KEY.",
    )
    parser.add_argument(
        "--supabase-service-role-key",
        help="Supabase service role key. Required for disposable-user auth unless provided via env.",
    )
    parser.add_argument(
        "--supabase-service-role-key-env",
        default=DEFAULT_SUPABASE_SERVICE_ROLE_KEY_ENV,
        help="Environment variable containing SUPABASE_SERVICE_ROLE_KEY.",
    )
    parser.add_argument(
        "--task-id",
        help="Optional task packet id to fetch during detail validation. Defaults to the first returned packet.",
    )
    parser.add_argument(
        "--job-id",
        help="Optional job id to fetch during detail validation. Defaults to the first returned job.",
    )
    parser.add_argument(
        "--task-limit",
        type=int,
        default=5,
        help="How many task packets to request during the authenticated proof.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=5,
        help="How many job runs to request during the authenticated proof.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout for each request.",
    )
    parser.add_argument(
        "--skip-authenticated-checks",
        action="store_true",
        help="Skip bearer-token and disposable-user authenticated checks and run only public-host validation.",
    )
    parser.add_argument(
        "--require-apparatus-study-route",
        action="store_true",
        help=(
            "Require the deployed host to expose the governed apparatus study-resource route and advertise it "
            "in OpenAPI."
        ),
    )
    parser.add_argument(
        "--apparatus-probe-id",
        default=DEFAULT_APPARATUS_PROBE_ID,
        help="UUID used to probe the apparatus study-resource route when --require-apparatus-study-route is set.",
    )
    return parser


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int,
) -> tuple[int, Any, dict[str, str]]:
    merged_headers = {"Accept": "application/json"}
    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged_headers["Content-Type"] = "application/json"
    if headers:
        merged_headers.update(headers)

    req = request.Request(url, headers=merged_headers, data=body, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            response_headers = {str(key).lower(): value for key, value in response.headers.items()}
            parsed_payload = json.loads(raw) if raw.strip() else {}
            return response.status, parsed_payload, response_headers
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed_payload = json.loads(detail) if detail.strip() else {"detail": exc.reason}
        except json.JSONDecodeError:
            parsed_payload = {"detail": detail or exc.reason}
        response_headers = {str(key).lower(): value for key, value in exc.headers.items()}
        return exc.code, parsed_payload, response_headers
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc


def _print_json(label: str, payload: Any) -> None:
    print(label)
    print(json.dumps(payload, indent=2, sort_keys=True))


def _resolve_env_or_arg(explicit_value: str | None, env_name: str) -> str:
    return (explicit_value or os.getenv(env_name, "")).strip()


def _resolve_bearer_token(args: argparse.Namespace) -> str | None:
    token = _resolve_env_or_arg(args.bearer_token, args.token_env)
    return token or None


def _response_detail(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    detail = payload.get("detail")
    return str(detail).strip() if detail is not None else ""


def _openapi_has_path(payload: Any, path: str) -> bool:
    if not isinstance(payload, dict):
        return False
    paths = payload.get("paths")
    return isinstance(paths, dict) and path in paths


def _validate_apparatus_study_route(
    *,
    openapi_status: int,
    openapi_payload: Any,
    route_status: int,
    route_payload: Any,
) -> list[str]:
    failures: list[str] = []
    if openapi_status != 200:
        failures.append("OpenAPI document did not return HTTP 200 for apparatus route validation")
        return failures

    if not _openapi_has_path(openapi_payload, APPARATUS_STUDY_ROUTE_PATH):
        failures.append("deployed OpenAPI does not advertise the apparatus study-resource route")

    detail = _response_detail(route_payload)
    if route_status == 404 and detail == "Not Found":
        failures.append("deployed apparatus study-resource route returned framework 404 Not Found")
    elif route_status not in {200, 404, 503}:
        failures.append(
            f"apparatus study-resource route returned unexpected status {route_status}"
        )

    return failures


def _validate_surface_contract(
    *,
    local_runtime: bool,
    discovery_status: int,
    mcp_status: int,
) -> list[str]:
    if local_runtime:
        return []

    failures: list[str] = []
    if discovery_status != 200:
        failures.append("OAuth discovery endpoint did not return HTTP 200")
    if mcp_status != 200:
        failures.append("MCP root endpoint did not return HTTP 200")
    return failures


def _validate_control_plane_auth_contract(
    *,
    local_runtime: bool,
    unauth_status: int,
    unauth_headers: dict[str, str],
) -> list[str]:
    if local_runtime:
        return []

    failures: list[str] = []
    if unauth_status != 401:
        failures.append("unauthenticated task-packets route did not return HTTP 401")
    unauthenticate_header = unauth_headers.get("www-authenticate", "")
    if not unauthenticate_header.startswith("Bearer"):
        failures.append(
            "unauthenticated task-packets route did not advertise WWW-Authenticate: Bearer"
        )
    return failures


def _resolve_disposable_auth_inputs(args: argparse.Namespace) -> tuple[str, str, str]:
    supabase_url = _resolve_env_or_arg(args.supabase_url, args.supabase_url_env).rstrip("/")
    anon_key = _resolve_env_or_arg(args.supabase_anon_key, args.supabase_anon_key_env)
    service_role_key = _resolve_env_or_arg(
        args.supabase_service_role_key,
        args.supabase_service_role_key_env,
    )
    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if not service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise RuntimeError(
            "A bearer token was not provided, so disposable-user auth requires: " + ", ".join(missing)
        )
    return supabase_url, anon_key, service_role_key


def _create_disposable_session(
    supabase_url: str,
    anon_key: str,
    service_role_key: str,
    timeout_seconds: int,
) -> tuple[str, dict[str, str]]:
    suffix = secrets.token_hex(6)
    email = f"render-smoke-{suffix}@example.com"
    password = f"Apex!Smoke{secrets.token_hex(6)}"

    user_payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"label": "render-smoke-validation"},
    }
    create_headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
    }
    create_status, created_user, _ = _request_json(
        "POST",
        f"{supabase_url}/auth/v1/admin/users",
        headers=create_headers,
        payload=user_payload,
        timeout_seconds=timeout_seconds,
    )
    if create_status not in {200, 201}:
        raise RuntimeError(f"Failed to create disposable Supabase user: HTTP {create_status} {created_user}")

    session_headers = {"apikey": anon_key}
    session_payload = {"email": email, "password": password}
    token_status, session_payload_json, _ = _request_json(
        "POST",
        f"{supabase_url}/auth/v1/token?grant_type=password",
        headers=session_headers,
        payload=session_payload,
        timeout_seconds=timeout_seconds,
    )
    if token_status != 200:
        raise RuntimeError(
            f"Failed to sign in disposable Supabase user: HTTP {token_status} {session_payload_json}"
        )

    access_token = str(session_payload_json.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError("Supabase password sign-in did not return an access token")

    cleanup_context = {
        "supabase_url": supabase_url,
        "service_role_key": service_role_key,
        "user_id": str(created_user.get("id") or "").strip(),
        "email": email,
    }
    if not cleanup_context["user_id"]:
        raise RuntimeError("Disposable Supabase user creation did not return a user id")

    return access_token, cleanup_context


def _cleanup_disposable_user(cleanup_context: dict[str, str], timeout_seconds: int) -> None:
    status, payload, _ = _request_json(
        "DELETE",
        f"{cleanup_context['supabase_url']}/auth/v1/admin/users/{parse.quote(cleanup_context['user_id'])}",
        headers={
            "Authorization": f"Bearer {cleanup_context['service_role_key']}",
            "apikey": cleanup_context["service_role_key"],
        },
        timeout_seconds=timeout_seconds,
    )
    if status not in {200, 204}:
        raise RuntimeError(
            f"Failed to delete disposable Supabase user {cleanup_context['email']}: HTTP {status} {payload}"
        )


def main() -> int:
    args = build_parser().parse_args()

    print("DEPLOYED_CONTROL_PLANE_SMOKE")
    print(f"BASE_URL {args.base_url}")
    print(f"HOST_MODE {'local-runtime' if args.local_runtime else 'public-host'}")

    failures: list[str] = []
    cleanup_context: dict[str, str] | None = None

    try:
        base_url = args.base_url.rstrip("/")

        health_status, health_payload, _ = _request_json(
            "GET", f"{base_url}/health", timeout_seconds=args.timeout_seconds
        )
        ready_status, ready_payload, _ = _request_json(
            "GET", f"{base_url}/health/ready", timeout_seconds=args.timeout_seconds
        )
        discovery_status, discovery_payload, _ = _request_json(
            "GET", f"{base_url}/.well-known/oauth-authorization-server", timeout_seconds=args.timeout_seconds
        )
        mcp_status, mcp_payload, _ = _request_json(
            "GET", f"{base_url}/mcp", timeout_seconds=args.timeout_seconds
        )
        openapi_status, openapi_payload, _ = _request_json(
            "GET", f"{base_url}/openapi.json", timeout_seconds=args.timeout_seconds
        )
        unauth_status, unauth_payload, unauth_headers = _request_json(
            "GET", f"{base_url}/api/v1/control-plane/task-packets", timeout_seconds=args.timeout_seconds
        )

        apparatus_route_status = None
        apparatus_route_payload: Any = None
        if args.require_apparatus_study_route:
            apparatus_route_status, apparatus_route_payload, _ = _request_json(
                "GET",
                f"{base_url}/api/v1/neta/apparatus/{parse.quote(args.apparatus_probe_id)}/resources",
                timeout_seconds=args.timeout_seconds,
            )

        task_status = None
        task_payload: Any = None
        lane_status = None
        lane_payload: Any = None
        job_status = None
        job_payload: Any = None
        task_detail_status = None
        task_detail_payload: Any = None
        job_detail_status = None
        job_detail_payload: Any = None

        if args.skip_authenticated_checks:
            print("AUTH_MODE skipped-authenticated-checks")
            task_id = None
            job_id = None
        else:
            bearer_token = _resolve_bearer_token(args)
            if bearer_token:
                print(f"AUTH_MODE existing-token:{args.token_env}")
            else:
                supabase_url, anon_key, service_role_key = _resolve_disposable_auth_inputs(args)
                bearer_token, cleanup_context = _create_disposable_session(
                    supabase_url=supabase_url,
                    anon_key=anon_key,
                    service_role_key=service_role_key,
                    timeout_seconds=args.timeout_seconds,
                )
                print(f"AUTH_MODE disposable-user:{cleanup_context['email']}")

            auth_headers = {"Authorization": f"Bearer {bearer_token}"}

            task_query = parse.urlencode({"limit": str(args.task_limit)})
            task_status, task_payload, _ = _request_json(
                "GET",
                f"{base_url}/api/v1/control-plane/task-packets?{task_query}",
                headers=auth_headers,
                timeout_seconds=args.timeout_seconds,
            )
            lane_status, lane_payload, _ = _request_json(
                "GET",
                f"{base_url}/api/v1/control-plane/lane-priorities",
                headers=auth_headers,
                timeout_seconds=args.timeout_seconds,
            )
            job_query = parse.urlencode({"limit": str(args.job_limit)})
            job_status, job_payload, _ = _request_json(
                "GET",
                f"{base_url}/api/v1/control-plane/job-runs?{job_query}",
                headers=auth_headers,
                timeout_seconds=args.timeout_seconds,
            )

            task_id = args.task_id
            if not task_id and isinstance(task_payload, list) and task_payload:
                task_id = str(task_payload[0].get("task_id") or "").strip() or None
            job_id = args.job_id
            if not job_id and isinstance(job_payload, list) and job_payload:
                job_id = str(job_payload[0].get("job_id") or "").strip() or None

            if task_id:
                task_detail_status, task_detail_payload, _ = _request_json(
                    "GET",
                    f"{base_url}/api/v1/control-plane/task-packets/{parse.quote(task_id)}",
                    headers=auth_headers,
                    timeout_seconds=args.timeout_seconds,
                )

            if job_id:
                job_detail_status, job_detail_payload, _ = _request_json(
                    "GET",
                    f"{base_url}/api/v1/control-plane/job-runs/{parse.quote(job_id)}",
                    headers=auth_headers,
                    timeout_seconds=args.timeout_seconds,
                )

        print(f"HEALTH_STATUS {health_status}")
        _print_json("HEALTH_PAYLOAD", health_payload)
        print(f"READY_STATUS {ready_status}")
        _print_json("READY_PAYLOAD", ready_payload)
        print(f"DISCOVERY_STATUS {discovery_status}")
        _print_json("DISCOVERY_PAYLOAD", discovery_payload)
        print(f"MCP_STATUS {mcp_status}")
        _print_json("MCP_PAYLOAD", mcp_payload)
        print(f"OPENAPI_STATUS {openapi_status}")
        if args.require_apparatus_study_route:
            print(f"APPARATUS_ROUTE_STATUS {apparatus_route_status}")
            _print_json("APPARATUS_ROUTE_PAYLOAD", apparatus_route_payload)
        print(f"UNAUTH_TASK_PACKETS_STATUS {unauth_status}")
        _print_json("UNAUTH_TASK_PACKETS_PAYLOAD", unauth_payload)
        print("UNAUTH_WWW_AUTHENTICATE " + unauth_headers.get("www-authenticate", ""))
        if not args.skip_authenticated_checks:
            print(f"AUTH_TASK_PACKETS_STATUS {task_status}")
            _print_json("AUTH_TASK_PACKETS_PAYLOAD", task_payload)
            print(f"LANE_PRIORITIES_STATUS {lane_status}")
            _print_json("LANE_PRIORITIES_PAYLOAD", lane_payload)
            print(f"JOB_RUNS_STATUS {job_status}")
            _print_json("JOB_RUNS_PAYLOAD", job_payload)
            if task_id:
                print(f"TASK_DETAIL_STATUS {task_detail_status}")
                print(f"TASK_DETAIL_ID {task_id}")
                _print_json("TASK_DETAIL_PAYLOAD", task_detail_payload)
            if job_id:
                print(f"JOB_DETAIL_STATUS {job_detail_status}")
                print(f"JOB_DETAIL_ID {job_id}")
                _print_json("JOB_DETAIL_PAYLOAD", job_detail_payload)

        if health_status != 200 or str(health_payload.get("status") or "") != "ok":
            failures.append("health endpoint did not return the expected live status")
        if ready_status != 200 or str(ready_payload.get("database") or "") != "connected":
            failures.append("readiness endpoint did not report database connected")
        failures.extend(
            _validate_surface_contract(
                local_runtime=args.local_runtime,
                discovery_status=discovery_status,
                mcp_status=mcp_status,
            )
        )
        failures.extend(
            _validate_control_plane_auth_contract(
                local_runtime=args.local_runtime,
                unauth_status=unauth_status,
                unauth_headers=unauth_headers,
            )
        )
        if args.require_apparatus_study_route:
            failures.extend(
                _validate_apparatus_study_route(
                    openapi_status=openapi_status,
                    openapi_payload=openapi_payload,
                    route_status=int(apparatus_route_status or 0),
                    route_payload=apparatus_route_payload,
                )
            )
        if not args.skip_authenticated_checks:
            if task_status != 200 or not isinstance(task_payload, list):
                failures.append("authenticated task-packets request did not return a JSON array with HTTP 200")
            if lane_status != 200 or not isinstance(lane_payload, list):
                failures.append("lane-priorities request did not return a JSON array with HTTP 200")
            if job_status != 200 or not isinstance(job_payload, list):
                failures.append("job-runs request did not return a JSON array with HTTP 200")
            if task_id and task_detail_status != 200:
                failures.append("task-packet detail request did not return HTTP 200")
            if task_id and str(task_detail_payload.get("task_id") or "") != task_id:
                failures.append("task-packet detail response did not match the requested task_id")
            if job_id and job_detail_status != 200:
                failures.append("job-run detail request did not return HTTP 200")
            if job_id and str(job_detail_payload.get("job_id") or "") != job_id:
                failures.append("job-run detail response did not match the requested job_id")

    except Exception as exc:
        print("RESULT FAIL")
        print(f"- {exc}")
        return 1
    finally:
        if cleanup_context is not None:
            try:
                _cleanup_disposable_user(cleanup_context, args.timeout_seconds)
                print(f"DISPOSABLE_USER_CLEANUP deleted:{cleanup_context['email']}")
            except Exception as cleanup_exc:
                print(f"DISPOSABLE_USER_CLEANUP_FAIL {cleanup_exc}")
                failures.append(f"cleanup failed: {cleanup_exc}")

    if failures:
        print("RESULT FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())