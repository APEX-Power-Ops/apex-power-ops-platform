"""Dedicated MCP transport for bounded GitHub repository and workflow operations."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

import jwt
from fastapi import HTTPException, Request as FastAPIRequest, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.auth import (
    AuthenticatedUser,
    GITHUB_MCP_OAUTH_SURFACE_ENV,
    build_www_authenticate_header_for_surface,
    describe_oauth_surface,
    get_authenticated_user_from_authorization_for_surface,
    user_has_required_scopes,
)

MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_SERVER_NAME = "apex-platform-github-repository-operations"
MCP_SERVER_VERSION = "0.1.0"
_CHATGPT_COMPAT_SCOPES = ["openid", "profile", "email"]
_GITHUB_API_BASE_URL = "https://api.github.com"
_GITHUB_API_VERSION = "2022-11-28"
_DEFAULT_USER_AGENT = "apex-platform-github-mcp/0.1.0"
_DEFAULT_ALLOWED_TOOL_FAMILIES = ("issues", "pull_requests", "actions", "writes")


class McpProtocolError(Exception):
    def __init__(self, code: int, message: str, data: Any | None = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class McpToolExecutionError(Exception):
    def __init__(self, message: str, *, meta: dict[str, Any] | None = None):
        self.message = message
        self.meta = meta or {}
        super().__init__(message)


def build_github_mcp_root_payload(request: FastAPIRequest) -> dict[str, Any]:
    surface = describe_oauth_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    return {
        "server_name": MCP_SERVER_NAME,
        "server_version": MCP_SERVER_VERSION,
        "status": "configured" if surface["public_activation_ready"] else "preproduction",
        "mcp_base_url": surface["mcp_root_url"],
        "oauth_discovery_url": surface["discovery_url"],
        "protected_resource_metadata_url": (
            f"{surface['public_mcp_base_url']}/.well-known/oauth-protected-resource"
            if surface["public_mcp_base_url"]
            else None
        ),
        "transport": {
            "type": "streamable-http",
            "protocol_version": MCP_PROTOCOL_VERSION,
            "supports_sse_get": True,
            "notes": "Use POST /github-mcp for initialize, tools/list, and tools/call. GET /github-mcp serves either JSON discovery metadata or an SSE compatibility stream.",
        },
        "capabilities": {"tools": {"listChanged": False}},
        "approved_tools": [tool["name"] for tool in _tool_definitions()],
        "write_rules": {
            "confirmation_required": True,
            "repo_allowlist_required": True,
            "durable_audit_required": True,
            "no_git_push_or_merge": True,
        },
    }


def handle_get_github_mcp(request: FastAPIRequest) -> JSONResponse:
    surface = describe_oauth_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "GitHub MCP surface is not configured"
        raise HTTPException(status_code=404, detail=detail)

    accept_header = request.headers.get("accept", "")
    if "text/event-stream" in accept_header:
        return StreamingResponse(
            _stream_mcp_sse_compat(request),
            media_type="text/event-stream",
            headers={
                "Allow": "GET, POST",
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return JSONResponse(build_github_mcp_root_payload(request))


def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_mcp_sse_compat(request: FastAPIRequest):
    surface = describe_oauth_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    yield _format_sse("endpoint", surface["mcp_root_url"])
    if not await request.is_disconnected():
        yield ": keep-alive\n\n"


async def handle_post_github_mcp(request: FastAPIRequest, db: Session) -> Response:
    surface = describe_oauth_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "GitHub MCP surface is not configured"
        raise HTTPException(status_code=404, detail=detail)

    payload = await request.json()
    if isinstance(payload, list):
        if not payload:
            raise HTTPException(status_code=400, detail="JSON-RPC batch payload must not be empty")
        responses = _process_batch(payload, request, db)
        if not responses:
            return Response(status_code=status.HTTP_202_ACCEPTED)
        return JSONResponse(responses)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="MCP payload must be a JSON object or batch array")

    response = _process_message(payload, request, db)
    if response is None:
        return Response(status_code=status.HTTP_202_ACCEPTED)

    headers: dict[str, str] = {"Allow": "GET, POST"}
    if _is_initialize_request(payload):
        headers["Mcp-Session-Id"] = str(uuid4())
    return JSONResponse(response, headers=headers)


def _process_batch(messages: list[Any], request: FastAPIRequest, db: Session) -> list[dict[str, Any]]:
    responses: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            responses.append(_jsonrpc_error(None, -32600, "Invalid Request"))
            continue
        response = _process_message(message, request, db)
        if response is not None:
            responses.append(response)
    return responses


def _process_message(message: dict[str, Any], request: FastAPIRequest, db: Session) -> dict[str, Any] | None:
    if message.get("jsonrpc") != "2.0":
        return _jsonrpc_error(message.get("id"), -32600, "Invalid Request")

    method = message.get("method")
    msg_id = message.get("id")
    is_notification = msg_id is None

    if not method:
        return None if is_notification else _jsonrpc_error(msg_id, -32600, "Invalid Request")

    try:
        if method == "initialize":
            if is_notification:
                raise McpProtocolError(-32600, "initialize must include an id")
            return _jsonrpc_result(msg_id, _handle_initialize(message.get("params") or {}))
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return None if is_notification else _jsonrpc_result(msg_id, {})
        if method == "tools/list":
            return None if is_notification else _jsonrpc_result(msg_id, _handle_tools_list())
        if method == "tools/call":
            if is_notification:
                raise McpProtocolError(-32600, "tools/call must include an id")
            result = _handle_tools_call(message.get("params") or {}, request, db)
            return _jsonrpc_result(msg_id, result)

        raise McpProtocolError(-32601, f"Method not found: {method}")
    except McpProtocolError as exc:
        return None if is_notification else _jsonrpc_error(msg_id, exc.code, exc.message, exc.data)


def _handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    client_version = str(params.get("protocolVersion") or "").strip()
    if not client_version:
        raise McpProtocolError(-32602, "initialize.protocolVersion is required")

    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION},
        "instructions": "This surface exposes bounded GitHub repository, pull request, CI, and workflow tools for allowlisted repositories. Writes require explicit confirmation and durable audit logging.",
    }


def _handle_tools_list() -> dict[str, Any]:
    return {"tools": _tool_definitions()}


def _handle_tools_call(params: dict[str, Any], request: FastAPIRequest, db: Session) -> dict[str, Any]:
    tool_name = str(params.get("name") or "").strip()
    arguments = params.get("arguments") or {}
    if not tool_name:
        raise McpProtocolError(-32602, "tools/call.params.name is required")
    if not isinstance(arguments, dict):
        raise McpProtocolError(-32602, "tools/call.params.arguments must be an object")

    tool = _tool_registry().get(tool_name)
    if tool is None:
        raise McpProtocolError(-32602, f"Unknown tool: {tool_name}")

    try:
        current_user = _require_tool_user(request, scopes=tool["required_scopes"])
        result = _normalize_tool_result(jsonable_encoder(tool["handler"](arguments, db, current_user)))
        return {
            "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            "structuredContent": result,
            "isError": False,
        }
    except McpToolExecutionError as exc:
        payload = {"content": [{"type": "text", "text": exc.message}], "isError": True}
        if exc.meta:
            payload["_meta"] = exc.meta
        return payload
    except HTTPException as exc:
        if exc.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}:
            header = None
            if exc.headers:
                header = exc.headers.get("WWW-Authenticate") or exc.headers.get("www-authenticate")
            meta = {}
            if header:
                meta["mcp/www_authenticate"] = [header]
            return {
                "content": [{"type": "text", "text": str(exc.detail)}],
                "isError": True,
                **({"_meta": meta} if meta else {}),
            }
        raise McpProtocolError(-32603, str(exc.detail)) from exc
    except Exception as exc:
        raise McpProtocolError(-32603, f"Tool execution failed: {exc}") from exc


def _require_tool_user(request: FastAPIRequest, *, scopes: list[str]) -> AuthenticatedUser:
    authorization = request.headers.get("authorization")
    try:
        user = get_authenticated_user_from_authorization_for_surface(
            request,
            authorization,
            surface_env=GITHUB_MCP_OAUTH_SURFACE_ENV,
        )
    except HTTPException as exc:
        header = None
        if exc.headers:
            header = exc.headers.get("WWW-Authenticate") or exc.headers.get("www-authenticate")
        detail = str(exc.detail)
        raise McpToolExecutionError(
            detail,
            meta={
                "mcp/www_authenticate": [
                    header or build_www_authenticate_header_for_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
                ]
            },
        ) from exc

    if not user_has_required_scopes(user, scopes):
        header = build_www_authenticate_header_for_surface(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
        raise McpToolExecutionError(
            f"Missing required scopes: {' '.join(scopes)}",
            meta={"mcp/www_authenticate": [f'{header}, scope="{" ".join(scopes)}"']},
        )
    return user


def _normalize_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"items": result, "count": len(result)}
    return {"value": result}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_json_env(name: str, default: Any) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise McpToolExecutionError(f"{name} is not valid JSON") from exc


def _allowed_repo_bindings() -> list[dict[str, Any]]:
    payload = _parse_json_env("GITHUB_ALLOWED_REPOS_JSON", [])
    if not isinstance(payload, list):
        raise McpToolExecutionError("GITHUB_ALLOWED_REPOS_JSON must be a JSON array")

    bindings: list[dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise McpToolExecutionError("Each GITHUB_ALLOWED_REPOS_JSON entry must be an object")
        owner = str(entry.get("owner") or "").strip()
        repo = str(entry.get("repo") or "").strip()
        if not owner or not repo:
            full_name = str(entry.get("full_name") or "").strip()
            if "/" in full_name:
                owner, repo = full_name.split("/", 1)
        if not owner or not repo:
            raise McpToolExecutionError("Each allowed GitHub repo must include owner and repo")

        tool_families = entry.get("enabled_tool_families")
        if isinstance(tool_families, list):
            enabled_tool_families = [str(item).strip() for item in tool_families if str(item).strip()]
        else:
            enabled_tool_families = list(_DEFAULT_ALLOWED_TOOL_FAMILIES)

        bindings.append(
            {
                "owner": owner,
                "repo": repo,
                "full_name": f"{owner}/{repo}",
                "default_branch": str(entry.get("default_branch") or "").strip() or None,
                "installation_id": entry.get("installation_id"),
                "enabled_tool_families": enabled_tool_families,
                "allowed_workflow_dispatches": entry.get("allowed_workflow_dispatches") or [],
                "copilot_review_reviewers": entry.get("copilot_review_reviewers") or [],
                "copilot_review_team_reviewers": entry.get("copilot_review_team_reviewers") or [],
            }
        )
    return bindings


def _installation_id_map() -> dict[str, int]:
    payload = _parse_json_env("GITHUB_APP_INSTALLATION_IDS_JSON", {})
    if not isinstance(payload, dict):
        raise McpToolExecutionError("GITHUB_APP_INSTALLATION_IDS_JSON must be a JSON object")
    mapping: dict[str, int] = {}
    for key, value in payload.items():
        try:
            mapping[str(key).strip()] = int(value)
        except (TypeError, ValueError) as exc:
            raise McpToolExecutionError("GITHUB_APP_INSTALLATION_IDS_JSON values must be integers") from exc
    return mapping


def _copilot_reviewer_map() -> dict[str, dict[str, list[str]]]:
    payload = _parse_json_env("GITHUB_COPILOT_REVIEWERS_JSON", {})
    if not isinstance(payload, dict):
        raise McpToolExecutionError("GITHUB_COPILOT_REVIEWERS_JSON must be a JSON object")
    result: dict[str, dict[str, list[str]]] = {}
    for key, value in payload.items():
        if not isinstance(value, dict):
            raise McpToolExecutionError("Each GITHUB_COPILOT_REVIEWERS_JSON entry must be an object")
        result[str(key).strip()] = {
            "reviewers": [str(item).strip() for item in value.get("reviewers", []) if str(item).strip()],
            "team_reviewers": [str(item).strip() for item in value.get("team_reviewers", []) if str(item).strip()],
        }
    return result


def _workflow_dispatch_allowlist_map() -> dict[str, list[str]]:
    payload = _parse_json_env("GITHUB_ALLOWED_WORKFLOW_DISPATCHES_JSON", {})
    if not isinstance(payload, dict):
        raise McpToolExecutionError("GITHUB_ALLOWED_WORKFLOW_DISPATCHES_JSON must be a JSON object")
    result: dict[str, list[str]] = {}
    for key, value in payload.items():
        if not isinstance(value, list):
            raise McpToolExecutionError("Each GITHUB_ALLOWED_WORKFLOW_DISPATCHES_JSON entry must be an array")
        result[str(key).strip()] = [str(item).strip() for item in value if str(item).strip()]
    return result


def _resolve_repo_binding(owner: str, repo: str) -> dict[str, Any]:
    normalized_full_name = f"{owner.strip()}/{repo.strip()}"
    for binding in _allowed_repo_bindings():
        if binding["full_name"].lower() == normalized_full_name.lower():
            return binding
    raise McpToolExecutionError(f"Repository {normalized_full_name} is not in the GitHub MCP allowlist")


def _require_repo_binding(arguments: dict[str, Any]) -> dict[str, Any]:
    owner = str(arguments.get("owner") or "").strip()
    repo = str(arguments.get("repo") or "").strip()
    if not owner or not repo:
        raise McpToolExecutionError("owner and repo are required")
    return _resolve_repo_binding(owner, repo)


def _require_tool_family(binding: dict[str, Any], family: str) -> None:
    enabled = binding.get("enabled_tool_families") or []
    if enabled and family not in enabled:
        raise McpToolExecutionError(f"Tool family '{family}' is not enabled for {binding['full_name']}")


def _github_app_id() -> str:
    app_id = os.getenv("GITHUB_APP_ID", "").strip()
    if not app_id:
        raise McpToolExecutionError("GITHUB_APP_ID is not configured")
    return app_id


def _github_app_private_key() -> str:
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "").strip()
    if not private_key:
        raise McpToolExecutionError("GITHUB_APP_PRIVATE_KEY is not configured")
    return private_key.replace("\\n", "\n")


def _github_app_jwt() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int((now - timedelta(seconds=60)).timestamp()),
        "exp": int((now + timedelta(minutes=9)).timestamp()),
        "iss": _github_app_id(),
    }
    encoded = jwt.encode(payload, _github_app_private_key(), algorithm="RS256")
    if isinstance(encoded, bytes):
        return encoded.decode("utf-8")
    return encoded


def _resolve_installation_id(binding: dict[str, Any]) -> int:
    raw_installation_id = binding.get("installation_id")
    if raw_installation_id is not None:
        try:
            return int(raw_installation_id)
        except (TypeError, ValueError) as exc:
            raise McpToolExecutionError(f"Invalid installation_id for {binding['full_name']}") from exc

    installation_ids = _installation_id_map()
    for key in (binding["full_name"], binding["repo"]):
        if key in installation_ids:
            return installation_ids[key]

    raise McpToolExecutionError(f"No GitHub App installation id is configured for {binding['full_name']}")


def _github_api_json(
    method: str,
    path: str,
    *,
    token: str,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    accept: str = "application/vnd.github+json",
    expected_status: tuple[int, ...] = (200,),
) -> Any:
    url = f"{_GITHUB_API_BASE_URL}{path}"
    if query:
        filtered_query = {key: value for key, value in query.items() if value is not None and value != ""}
        if filtered_query:
            url = f"{url}?{urlencode(filtered_query, doseq=True)}"

    headers = {
        "Accept": accept,
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": _GITHUB_API_VERSION,
        "User-Agent": _DEFAULT_USER_AGENT,
    }
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, headers=headers, method=method.upper())

    try:
        with urlopen(request, timeout=30) as response:
            status_code = int(response.status)
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        message = raw or str(exc)
        try:
            payload_json = json.loads(raw) if raw else {}
            message = str(payload_json.get("message") or message)
        except json.JSONDecodeError:
            payload_json = None
        raise McpToolExecutionError(f"GitHub API {method.upper()} {path} failed: {message}") from exc
    except URLError as exc:
        raise McpToolExecutionError(f"GitHub API request failed: {exc.reason}") from exc

    if status_code not in expected_status:
        raise McpToolExecutionError(
            f"GitHub API {method.upper()} {path} returned unexpected status {status_code}"
        )

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _get_installation_access_token(binding: dict[str, Any]) -> str:
    installation_id = _resolve_installation_id(binding)
    payload = _github_api_json(
        "POST",
        f"/app/installations/{installation_id}/access_tokens",
        token=_github_app_jwt(),
        body={},
        expected_status=(201,),
    )
    token = str(payload.get("token") or "").strip()
    if not token:
        raise McpToolExecutionError(f"GitHub App token minting did not return a token for {binding['full_name']}")
    return token


def _github_repo_path(binding: dict[str, Any], suffix: str = "") -> str:
    owner = quote(binding["owner"], safe="")
    repo = quote(binding["repo"], safe="")
    return f"/repos/{owner}/{repo}{suffix}"


def _get_repo_metadata(binding: dict[str, Any], token: str) -> dict[str, Any]:
    return _github_api_json("GET", _github_repo_path(binding), token=token)


def _normalize_repository(payload: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner": binding["owner"],
        "repo": binding["repo"],
        "full_name": binding["full_name"],
        "default_branch": payload.get("default_branch") or binding.get("default_branch"),
        "private": bool(payload.get("private")),
        "archived": bool(payload.get("archived")),
        "visibility": payload.get("visibility"),
        "open_issues_count": payload.get("open_issues_count"),
        "html_url": payload.get("html_url"),
        "description": payload.get("description"),
        "enabled_tool_families": binding.get("enabled_tool_families") or [],
        "installation_configured": True,
    }


def _normalize_issue(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": payload.get("number"),
        "title": payload.get("title"),
        "state": payload.get("state"),
        "locked": bool(payload.get("locked")),
        "html_url": payload.get("html_url"),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "user": (payload.get("user") or {}).get("login"),
        "labels": [label.get("name") for label in payload.get("labels", []) if isinstance(label, dict)],
        "comments": payload.get("comments"),
        "body": payload.get("body"),
    }


def _normalize_pull_request(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": payload.get("number"),
        "title": payload.get("title"),
        "state": payload.get("state"),
        "draft": bool(payload.get("draft")),
        "html_url": payload.get("html_url"),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "mergeable": payload.get("mergeable"),
        "mergeable_state": payload.get("mergeable_state"),
        "merged": bool(payload.get("merged")),
        "head": {
            "ref": (payload.get("head") or {}).get("ref"),
            "sha": (payload.get("head") or {}).get("sha"),
        },
        "base": {
            "ref": (payload.get("base") or {}).get("ref"),
            "sha": (payload.get("base") or {}).get("sha"),
        },
        "user": (payload.get("user") or {}).get("login"),
        "requested_reviewers": [
            reviewer.get("login") for reviewer in payload.get("requested_reviewers", []) if isinstance(reviewer, dict)
        ],
        "requested_teams": [
            team.get("slug") for team in payload.get("requested_teams", []) if isinstance(team, dict)
        ],
    }


def _normalize_review_summary(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    latest_by_user: dict[str, str] = {}
    ordered_reviews = sorted(reviews, key=lambda review: str(review.get("submitted_at") or ""))
    for review in ordered_reviews:
        login = str((review.get("user") or {}).get("login") or "").strip()
        state = str(review.get("state") or "").upper().strip()
        if login and state:
            latest_by_user[login] = state

    approved = sorted(user for user, state in latest_by_user.items() if state == "APPROVED")
    changes_requested = sorted(user for user, state in latest_by_user.items() if state == "CHANGES_REQUESTED")
    commented = sorted(user for user, state in latest_by_user.items() if state == "COMMENTED")

    return {
        "approvals": approved,
        "approval_count": len(approved),
        "changes_requested_by": changes_requested,
        "changes_requested_count": len(changes_requested),
        "commented_by": commented,
    }


def _normalize_check_runs(payload: dict[str, Any]) -> dict[str, Any]:
    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    failed = []
    pending = []
    succeeded = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        entry = {
            "name": run.get("name"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "html_url": run.get("html_url"),
        }
        status_value = str(run.get("status") or "").lower()
        conclusion_value = str(run.get("conclusion") or "").lower()
        if status_value != "completed":
            pending.append(entry)
        elif conclusion_value == "success":
            succeeded.append(entry)
        else:
            failed.append(entry)
    return {
        "total": len(runs),
        "successful": succeeded,
        "failed": failed,
        "pending": pending,
    }


def _normalize_status_contexts(payload: dict[str, Any]) -> dict[str, Any]:
    contexts = payload.get("statuses", []) if isinstance(payload, dict) else []
    failed = []
    pending = []
    successful = []
    for context in contexts:
        if not isinstance(context, dict):
            continue
        entry = {
            "context": context.get("context"),
            "state": context.get("state"),
            "description": context.get("description"),
            "target_url": context.get("target_url"),
        }
        state_value = str(context.get("state") or "").lower()
        if state_value == "success":
            successful.append(entry)
        elif state_value == "pending":
            pending.append(entry)
        else:
            failed.append(entry)
    return {
        "state": payload.get("state") if isinstance(payload, dict) else None,
        "successful": successful,
        "failed": failed,
        "pending": pending,
    }


def _merge_readiness(pr: dict[str, Any], review_summary: dict[str, Any], check_summary: dict[str, Any], status_summary: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if pr.get("draft"):
        blockers.append("pull request is still draft")
    if review_summary.get("changes_requested_count"):
        blockers.append("changes requested reviews remain open")
    if check_summary.get("failed"):
        blockers.append("one or more check runs failed")
    if check_summary.get("pending"):
        blockers.append("one or more check runs are still pending")
    if status_summary.get("failed"):
        blockers.append("one or more status contexts failed")
    if status_summary.get("pending"):
        blockers.append("one or more status contexts are still pending")

    mergeable_state = str(pr.get("mergeable_state") or "").strip()
    if mergeable_state and mergeable_state not in {"clean", "unstable", "has_hooks"}:
        blockers.append(f"mergeable_state={mergeable_state}")

    return {
        "mergeable": pr.get("mergeable"),
        "mergeable_state": mergeable_state or None,
        "ready_to_merge": not blockers,
        "blockers": blockers,
    }


def _get_content_path(binding: dict[str, Any], path: str, token: str, *, ref: str | None = None) -> Any | None:
    query = {"ref": ref} if ref else None
    try:
        return _github_api_json(
            "GET",
            _github_repo_path(binding, f"/contents/{quote(path, safe='/')}") ,
            token=token,
            query=query,
        )
    except McpToolExecutionError as exc:
        if "failed: Not Found" in exc.message:
            return None
        raise


def _decode_repo_content(payload: dict[str, Any]) -> str:
    content = str(payload.get("content") or "")
    if not content:
        return ""
    try:
        return base64.b64decode(content.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise McpToolExecutionError("Failed to decode repository content payload") from exc


def _load_pull_request_template(binding: dict[str, Any], token: str, *, ref: str | None = None) -> str | None:
    candidate_paths = [
        ".github/pull_request_template.md",
        "PULL_REQUEST_TEMPLATE.md",
        "docs/PULL_REQUEST_TEMPLATE.md",
    ]
    for candidate in candidate_paths:
        payload = _get_content_path(binding, candidate, token, ref=ref)
        if isinstance(payload, dict) and payload.get("type") == "file":
            decoded = _decode_repo_content(payload).strip()
            if decoded:
                return decoded

    directory_payload = _get_content_path(binding, ".github/PULL_REQUEST_TEMPLATE", token, ref=ref)
    if isinstance(directory_payload, list):
        for item in directory_payload:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "").strip()
            if not path.lower().endswith((".md", ".txt")):
                continue
            payload = _get_content_path(binding, path, token, ref=ref)
            if isinstance(payload, dict) and payload.get("type") == "file":
                decoded = _decode_repo_content(payload).strip()
                if decoded:
                    return decoded
    return None


def _require_confirmation(arguments: dict[str, Any], action_label: str) -> None:
    if arguments.get("confirmed") is not True:
        raise McpToolExecutionError(f"{action_label} requires confirmed=true")


def _sanitize_branch_name(raw_branch_name: str) -> str:
    branch_name = raw_branch_name.strip()
    if not branch_name:
        raise McpToolExecutionError("branch_name is required")
    if branch_name.startswith("refs/"):
        raise McpToolExecutionError("branch_name must not include refs/")
    if any(segment in {".", ".."} for segment in branch_name.split("/")):
        raise McpToolExecutionError("branch_name contains an invalid path segment")
    if any(char.isspace() for char in branch_name):
        raise McpToolExecutionError("branch_name must not contain whitespace")
    return branch_name


def _record_write_audit(
    db: Session,
    *,
    tool_name: str,
    binding: dict[str, Any],
    current_user: AuthenticatedUser,
    target_type: str,
    target_identifier: str,
    request_summary: dict[str, Any],
    result_summary: dict[str, Any],
) -> str:
    if db is None:
        raise McpToolExecutionError("Database session required for durable audit logging")

    audit_id = f"audit-{uuid4()}"
    db.execute(
        text(
            """
            INSERT INTO public.mcp_external_action_audits (
                audit_id,
                connector,
                tool_name,
                actor_id,
                actor_email,
                owner,
                repo,
                target_type,
                target_identifier,
                request_summary,
                result_summary
            )
            VALUES (
                :audit_id,
                'github',
                :tool_name,
                :actor_id,
                :actor_email,
                :owner,
                :repo,
                :target_type,
                :target_identifier,
                CAST(:request_summary AS jsonb),
                CAST(:result_summary AS jsonb)
            )
            """
        ),
        {
            "audit_id": audit_id,
            "tool_name": tool_name,
            "actor_id": str(current_user.user_id),
            "actor_email": current_user.email,
            "owner": binding["owner"],
            "repo": binding["repo"],
            "target_type": target_type,
            "target_identifier": target_identifier,
            "request_summary": json.dumps(request_summary, default=str),
            "result_summary": json.dumps(result_summary, default=str),
        },
    )
    db.commit()
    return audit_id


def _workflow_dispatch_allowlist(binding: dict[str, Any]) -> list[str]:
    explicit = binding.get("allowed_workflow_dispatches") or []
    if explicit:
        return [str(item).strip() for item in explicit if str(item).strip()]
    return _workflow_dispatch_allowlist_map().get(binding["full_name"], [])


def _copilot_review_targets(binding: dict[str, Any], arguments: dict[str, Any]) -> tuple[list[str], list[str]]:
    reviewers = [str(item).strip() for item in arguments.get("reviewers", []) if str(item).strip()]
    team_reviewers = [str(item).strip() for item in arguments.get("team_reviewers", []) if str(item).strip()]
    if reviewers or team_reviewers:
        return reviewers, team_reviewers

    repo_map = _copilot_reviewer_map().get(binding["full_name"], {})
    reviewers = [str(item).strip() for item in binding.get("copilot_review_reviewers", []) if str(item).strip()]
    team_reviewers = [str(item).strip() for item in binding.get("copilot_review_team_reviewers", []) if str(item).strip()]
    if repo_map:
        reviewers = repo_map.get("reviewers", reviewers)
        team_reviewers = repo_map.get("team_reviewers", team_reviewers)

    if not reviewers and not team_reviewers:
        raise McpToolExecutionError(
            "request_copilot_review requires configured reviewers via GITHUB_COPILOT_REVIEWERS_JSON or repo allowlist metadata"
        )
    return reviewers, team_reviewers


def _call_list_allowed_repositories(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    items = []
    installation_ids = _installation_id_map()
    for binding in _allowed_repo_bindings():
        items.append(
            {
                "owner": binding["owner"],
                "repo": binding["repo"],
                "default_branch": binding.get("default_branch"),
                "enabled_tool_families": binding.get("enabled_tool_families") or [],
                "installation_configured": bool(
                    binding.get("installation_id") is not None or binding["full_name"] in installation_ids or binding["repo"] in installation_ids
                ),
            }
        )
    return {"items": items, "count": len(items)}


def _call_fetch_repository(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    token = _get_installation_access_token(binding)
    payload = _get_repo_metadata(binding, token)
    return _normalize_repository(payload, binding)


def _call_search_issues(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "issues")
    query_text = str(arguments.get("query") or "").strip()
    if not query_text:
        raise McpToolExecutionError("query is required")
    limit = min(max(int(arguments.get("limit", 10)), 1), 50)
    token = _get_installation_access_token(binding)
    payload = _github_api_json(
        "GET",
        "/search/issues",
        token=token,
        query={"q": f"repo:{binding['full_name']} is:issue {query_text}", "per_page": limit},
    )
    items = [_normalize_issue(item) for item in payload.get("items", []) if isinstance(item, dict)]
    return {"items": items, "count": len(items), "query": query_text}


def _call_fetch_issue(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "issues")
    issue_number = int(arguments.get("issue_number") or 0)
    if issue_number < 1:
        raise McpToolExecutionError("issue_number must be a positive integer")
    token = _get_installation_access_token(binding)
    issue = _github_api_json("GET", _github_repo_path(binding, f"/issues/{issue_number}"), token=token)
    comments = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/issues/{issue_number}/comments"),
        token=token,
        query={"per_page": min(max(int(arguments.get("comment_limit", 20)), 1), 50)},
    )
    return {
        "issue": _normalize_issue(issue),
        "comments": [
            {
                "user": (comment.get("user") or {}).get("login"),
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "body": comment.get("body"),
            }
            for comment in comments
            if isinstance(comment, dict)
        ],
    }


def _call_search_pull_requests(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "pull_requests")
    query_text = str(arguments.get("query") or "").strip()
    if not query_text:
        raise McpToolExecutionError("query is required")
    limit = min(max(int(arguments.get("limit", 10)), 1), 50)
    token = _get_installation_access_token(binding)
    payload = _github_api_json(
        "GET",
        "/search/issues",
        token=token,
        query={"q": f"repo:{binding['full_name']} is:pr {query_text}", "per_page": limit},
    )
    items = [_normalize_pull_request(item) for item in payload.get("items", []) if isinstance(item, dict)]
    return {"items": items, "count": len(items), "query": query_text}


def _call_fetch_pull_request(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "pull_requests")
    pull_number = int(arguments.get("pull_number") or 0)
    if pull_number < 1:
        raise McpToolExecutionError("pull_number must be a positive integer")
    token = _get_installation_access_token(binding)
    pull_request = _github_api_json("GET", _github_repo_path(binding, f"/pulls/{pull_number}"), token=token)
    files = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/pulls/{pull_number}/files"),
        token=token,
        query={"per_page": min(max(int(arguments.get("file_limit", 100)), 1), 100)},
    )
    reviews = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/pulls/{pull_number}/reviews"),
        token=token,
        query={"per_page": 100},
    )
    return {
        "pull_request": _normalize_pull_request(pull_request),
        "files": [
            {
                "filename": item.get("filename"),
                "status": item.get("status"),
                "additions": item.get("additions"),
                "deletions": item.get("deletions"),
                "changes": item.get("changes"),
            }
            for item in files
            if isinstance(item, dict)
        ],
        "review_summary": _normalize_review_summary([item for item in reviews if isinstance(item, dict)]),
    }


def _call_fetch_pull_request_status_checks(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "pull_requests")
    pull_number = int(arguments.get("pull_number") or 0)
    if pull_number < 1:
        raise McpToolExecutionError("pull_number must be a positive integer")
    token = _get_installation_access_token(binding)
    pull_request = _github_api_json("GET", _github_repo_path(binding, f"/pulls/{pull_number}"), token=token)
    head_sha = str((pull_request.get("head") or {}).get("sha") or "").strip()
    if not head_sha:
        raise McpToolExecutionError("Pull request head SHA is missing")

    check_runs = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/commits/{head_sha}/check-runs"),
        token=token,
        query={"per_page": 100},
    )
    statuses = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/commits/{head_sha}/status"),
        token=token,
    )
    reviews = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/pulls/{pull_number}/reviews"),
        token=token,
        query={"per_page": 100},
    )
    requested_reviewers = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/pulls/{pull_number}/requested_reviewers"),
        token=token,
    )

    review_summary = _normalize_review_summary([item for item in reviews if isinstance(item, dict)])
    check_summary = _normalize_check_runs(check_runs)
    status_summary = _normalize_status_contexts(statuses)
    pr_summary = _normalize_pull_request(pull_request)

    return {
        "pull_request": pr_summary,
        "review_summary": {
            **review_summary,
            "requested_reviewers": [
                reviewer.get("login") for reviewer in requested_reviewers.get("users", []) if isinstance(reviewer, dict)
            ],
            "requested_teams": [
                team.get("slug") for team in requested_reviewers.get("teams", []) if isinstance(team, dict)
            ],
        },
        "check_runs": check_summary,
        "status_contexts": status_summary,
        "merge_readiness": _merge_readiness(pr_summary, review_summary, check_summary, status_summary),
    }


def _call_list_workflows(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "actions")
    token = _get_installation_access_token(binding)
    payload = _github_api_json("GET", _github_repo_path(binding, "/actions/workflows"), token=token)
    items = [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "path": item.get("path"),
            "state": item.get("state"),
            "html_url": item.get("html_url"),
        }
        for item in payload.get("workflows", [])
        if isinstance(item, dict)
    ]
    return {"items": items, "count": len(items)}


def _call_list_workflow_runs(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "actions")
    token = _get_installation_access_token(binding)
    workflow_id = arguments.get("workflow_id")
    limit = min(max(int(arguments.get("limit", 10)), 1), 50)
    suffix = f"/actions/workflows/{quote(str(workflow_id), safe='')}/runs" if workflow_id else "/actions/runs"
    payload = _github_api_json(
        "GET",
        _github_repo_path(binding, suffix),
        token=token,
        query={
            "per_page": limit,
            "branch": arguments.get("branch"),
            "status": arguments.get("status"),
        },
    )
    items = [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "display_title": item.get("display_title"),
            "head_branch": item.get("head_branch"),
            "head_sha": item.get("head_sha"),
            "status": item.get("status"),
            "conclusion": item.get("conclusion"),
            "event": item.get("event"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "html_url": item.get("html_url"),
        }
        for item in payload.get("workflow_runs", [])
        if isinstance(item, dict)
    ]
    return {"items": items, "count": len(items)}


def _call_fetch_workflow_run_logs(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "actions")
    run_id = int(arguments.get("run_id") or 0)
    if run_id < 1:
        raise McpToolExecutionError("run_id must be a positive integer")
    token = _get_installation_access_token(binding)
    run_payload = _github_api_json("GET", _github_repo_path(binding, f"/actions/runs/{run_id}"), token=token)
    jobs_payload = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/actions/runs/{run_id}/jobs"),
        token=token,
        query={"per_page": 100},
    )
    failed_jobs = []
    for job in jobs_payload.get("jobs", []):
        if not isinstance(job, dict):
            continue
        conclusion = str(job.get("conclusion") or "").lower()
        if conclusion == "success":
            continue
        failed_steps = []
        for step in job.get("steps", []):
            if not isinstance(step, dict):
                continue
            step_conclusion = str(step.get("conclusion") or "").lower()
            if step_conclusion and step_conclusion != "success":
                failed_steps.append(
                    {
                        "name": step.get("name"),
                        "status": step.get("status"),
                        "conclusion": step.get("conclusion"),
                        "number": step.get("number"),
                    }
                )
        failed_jobs.append(
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "html_url": job.get("html_url"),
                "failed_steps": failed_steps,
            }
        )
    return {
        "run": {
            "id": run_payload.get("id"),
            "name": run_payload.get("name"),
            "display_title": run_payload.get("display_title"),
            "status": run_payload.get("status"),
            "conclusion": run_payload.get("conclusion"),
            "html_url": run_payload.get("html_url"),
        },
        "failed_jobs": failed_jobs,
        "job_count": len(jobs_payload.get("jobs", [])),
        "failure_count": len(failed_jobs),
        "notes": "This first slice returns summarized failure detail from workflow jobs and steps rather than downloading raw ZIP logs.",
    }


def _call_add_issue_comment(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmation(arguments, "add_issue_comment")
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "writes")
    issue_number = int(arguments.get("issue_number") or 0)
    body = str(arguments.get("body") or "").strip()
    if issue_number < 1 or not body:
        raise McpToolExecutionError("issue_number and body are required")
    token = _get_installation_access_token(binding)
    payload = _github_api_json(
        "POST",
        _github_repo_path(binding, f"/issues/{issue_number}/comments"),
        token=token,
        body={"body": body},
        expected_status=(201,),
    )
    audit_id = _record_write_audit(
        db,
        tool_name="add_issue_comment",
        binding=binding,
        current_user=current_user,
        target_type="issue",
        target_identifier=str(issue_number),
        request_summary={"body_preview": body[:120]},
        result_summary={"comment_id": payload.get("id"), "html_url": payload.get("html_url")},
    )
    return {
        "comment_id": payload.get("id"),
        "html_url": payload.get("html_url"),
        "issue_number": issue_number,
        "audit_id": audit_id,
    }


def _call_create_branch_from_default(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmation(arguments, "create_branch_from_default")
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "writes")
    branch_name = _sanitize_branch_name(str(arguments.get("branch_name") or ""))
    token = _get_installation_access_token(binding)
    repo_payload = _get_repo_metadata(binding, token)
    default_branch = str(repo_payload.get("default_branch") or binding.get("default_branch") or "").strip()
    if not default_branch:
        raise McpToolExecutionError(f"Default branch is not known for {binding['full_name']}")
    default_ref = _github_api_json(
        "GET",
        _github_repo_path(binding, f"/git/ref/heads/{quote(default_branch, safe='') }"),
        token=token,
    )
    head_sha = ((default_ref.get("object") or {}).get("sha") or "").strip()
    if not head_sha:
        raise McpToolExecutionError(f"Default branch ref did not return a SHA for {binding['full_name']}")
    payload = _github_api_json(
        "POST",
        _github_repo_path(binding, "/git/refs"),
        token=token,
        body={"ref": f"refs/heads/{branch_name}", "sha": head_sha},
        expected_status=(201,),
    )
    audit_id = _record_write_audit(
        db,
        tool_name="create_branch_from_default",
        binding=binding,
        current_user=current_user,
        target_type="branch",
        target_identifier=branch_name,
        request_summary={"base_branch": default_branch},
        result_summary={"ref": payload.get("ref"), "sha": ((payload.get("object") or {}).get("sha"))},
    )
    return {
        "branch_name": branch_name,
        "base_branch": default_branch,
        "sha": (payload.get("object") or {}).get("sha"),
        "audit_id": audit_id,
    }


def _call_create_pull_request(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmation(arguments, "create_pull_request")
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "writes")
    title = str(arguments.get("title") or "").strip()
    head_branch = _sanitize_branch_name(str(arguments.get("head_branch") or arguments.get("head") or ""))
    if not title:
        raise McpToolExecutionError("title is required")

    token = _get_installation_access_token(binding)
    repo_payload = _get_repo_metadata(binding, token)
    base_branch = str(arguments.get("base") or repo_payload.get("default_branch") or binding.get("default_branch") or "").strip()
    if not base_branch:
        raise McpToolExecutionError(f"Base branch is not known for {binding['full_name']}")

    template = _load_pull_request_template(binding, token, ref=head_branch)
    body = str(arguments.get("body") or "").strip()
    if template and body:
        final_body = f"{template}\n\n## Additional Context\n\n{body}"
    elif template:
        final_body = template
    else:
        final_body = body

    payload = _github_api_json(
        "POST",
        _github_repo_path(binding, "/pulls"),
        token=token,
        body={
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": final_body,
            "draft": bool(arguments.get("draft", False)),
        },
        expected_status=(201,),
    )
    audit_id = _record_write_audit(
        db,
        tool_name="create_pull_request",
        binding=binding,
        current_user=current_user,
        target_type="pull_request",
        target_identifier=str(payload.get("number") or ""),
        request_summary={"head_branch": head_branch, "base_branch": base_branch, "used_template": bool(template)},
        result_summary={"pull_number": payload.get("number"), "html_url": payload.get("html_url")},
    )
    return {
        "pull_request": _normalize_pull_request(payload),
        "used_template": bool(template),
        "audit_id": audit_id,
    }


def _call_request_copilot_review(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmation(arguments, "request_copilot_review")
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "writes")
    pull_number = int(arguments.get("pull_number") or 0)
    if pull_number < 1:
        raise McpToolExecutionError("pull_number must be a positive integer")
    reviewers, team_reviewers = _copilot_review_targets(binding, arguments)
    token = _get_installation_access_token(binding)
    payload = _github_api_json(
        "POST",
        _github_repo_path(binding, f"/pulls/{pull_number}/requested_reviewers"),
        token=token,
        body={"reviewers": reviewers, "team_reviewers": team_reviewers},
        expected_status=(201,),
    )
    audit_id = _record_write_audit(
        db,
        tool_name="request_copilot_review",
        binding=binding,
        current_user=current_user,
        target_type="pull_request",
        target_identifier=str(pull_number),
        request_summary={"reviewers": reviewers, "team_reviewers": team_reviewers},
        result_summary={"requested_reviewers": reviewers, "requested_teams": team_reviewers},
    )
    return {
        "pull_number": pull_number,
        "requested_reviewers": reviewers,
        "requested_teams": team_reviewers,
        "mode": "configured-review-request-alias",
        "html_url": payload.get("html_url"),
        "audit_id": audit_id,
    }


def _call_dispatch_workflow(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmation(arguments, "dispatch_workflow")
    binding = _require_repo_binding(arguments)
    _require_tool_family(binding, "actions")
    workflow_id = str(arguments.get("workflow_id") or arguments.get("workflow") or "").strip()
    ref = str(arguments.get("ref") or "").strip()
    if not workflow_id or not ref:
        raise McpToolExecutionError("workflow_id and ref are required")
    allowed = _workflow_dispatch_allowlist(binding)
    if workflow_id not in allowed:
        raise McpToolExecutionError(
            f"Workflow {workflow_id} is not allowlisted for dispatch in {binding['full_name']}"
        )

    token = _get_installation_access_token(binding)
    _github_api_json(
        "POST",
        _github_repo_path(binding, f"/actions/workflows/{quote(workflow_id, safe='')}/dispatches"),
        token=token,
        body={"ref": ref, "inputs": arguments.get("inputs") or {}},
        expected_status=(204,),
    )
    audit_id = _record_write_audit(
        db,
        tool_name="dispatch_workflow",
        binding=binding,
        current_user=current_user,
        target_type="workflow",
        target_identifier=workflow_id,
        request_summary={"ref": ref, "inputs": arguments.get("inputs") or {}},
        result_summary={"status": "dispatched"},
    )
    return {
        "workflow_id": workflow_id,
        "ref": ref,
        "dispatched": True,
        "audit_id": audit_id,
    }


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "list_allowed_repositories",
            "title": "List Allowed Repositories",
            "description": "List the repositories this connector is allowed to access.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "fetch_repository",
            "title": "Fetch Repository",
            "description": "Return bounded repository metadata for one allowed repository.",
            "inputSchema": {
                "type": "object",
                "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}},
                "required": ["owner", "repo"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "search_issues",
            "title": "Search Issues",
            "description": "Search issues in one allowed repository using bounded GitHub query syntax.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                },
                "required": ["owner", "repo", "query"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "fetch_issue",
            "title": "Fetch Issue",
            "description": "Return issue detail, labels, assignees, and recent comments.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer", "minimum": 1},
                    "comment_limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
                },
                "required": ["owner", "repo", "issue_number"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "search_pull_requests",
            "title": "Search Pull Requests",
            "description": "Search pull requests in one allowed repository using bounded GitHub query syntax.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                },
                "required": ["owner", "repo", "query"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "fetch_pull_request",
            "title": "Fetch Pull Request",
            "description": "Return one pull request's summary, files, and review state.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "pull_number": {"type": "integer", "minimum": 1},
                    "file_limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 100},
                },
                "required": ["owner", "repo", "pull_number"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "fetch_pull_request_status_checks",
            "title": "Fetch Pull Request Status Checks",
            "description": "Return CI status, workflow failures, review requirements, and merge readiness for one pull request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "pull_number": {"type": "integer", "minimum": 1},
                },
                "required": ["owner", "repo", "pull_number"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "list_workflows",
            "title": "List Workflows",
            "description": "List workflows for one allowed repository.",
            "inputSchema": {
                "type": "object",
                "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}},
                "required": ["owner", "repo"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "list_workflow_runs",
            "title": "List Workflow Runs",
            "description": "List workflow runs for one allowed repository or workflow.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "workflow_id": {"type": "string"},
                    "branch": {"type": "string"},
                    "status": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                },
                "required": ["owner", "repo"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "fetch_workflow_run_logs",
            "title": "Fetch Workflow Run Logs",
            "description": "Return summarized failure detail for one workflow run.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "run_id": {"type": "integer", "minimum": 1},
                },
                "required": ["owner", "repo", "run_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "add_issue_comment",
            "title": "Add Issue Comment",
            "description": "Add one bounded issue or pull request comment.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer", "minimum": 1},
                    "body": {"type": "string"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["owner", "repo", "issue_number", "body", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "create_branch_from_default",
            "title": "Create Branch From Default",
            "description": "Create a branch from the default branch in one allowed repository.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "branch_name": {"type": "string"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["owner", "repo", "branch_name", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "create_pull_request",
            "title": "Create Pull Request",
            "description": "Create one pull request from an already-created branch using the repository template when present.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "title": {"type": "string"},
                    "head_branch": {"type": "string"},
                    "base": {"type": "string"},
                    "body": {"type": "string"},
                    "draft": {"type": "boolean", "default": False},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["owner", "repo", "title", "head_branch", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "request_copilot_review",
            "title": "Request Copilot Review",
            "description": "Request a configured review target for one existing pull request.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "pull_number": {"type": "integer", "minimum": 1},
                    "reviewers": {"type": "array", "items": {"type": "string"}},
                    "team_reviewers": {"type": "array", "items": {"type": "string"}},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["owner", "repo", "pull_number", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "dispatch_workflow",
            "title": "Dispatch Workflow",
            "description": "Trigger one allowlisted workflow manually.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "workflow_id": {"type": "string"},
                    "ref": {"type": "string"},
                    "inputs": {"type": "object"},
                    "confirmed": {"type": "boolean"},
                },
                "required": ["owner", "repo", "workflow_id", "ref", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
    ]


def _tool_registry() -> dict[str, dict[str, Any]]:
    return {
        "list_allowed_repositories": {
            "handler": _call_list_allowed_repositories,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "fetch_repository": {"handler": _call_fetch_repository, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "search_issues": {"handler": _call_search_issues, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "fetch_issue": {"handler": _call_fetch_issue, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "search_pull_requests": {
            "handler": _call_search_pull_requests,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "fetch_pull_request": {
            "handler": _call_fetch_pull_request,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "fetch_pull_request_status_checks": {
            "handler": _call_fetch_pull_request_status_checks,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "list_workflows": {"handler": _call_list_workflows, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "list_workflow_runs": {
            "handler": _call_list_workflow_runs,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "fetch_workflow_run_logs": {
            "handler": _call_fetch_workflow_run_logs,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "add_issue_comment": {"handler": _call_add_issue_comment, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "create_branch_from_default": {
            "handler": _call_create_branch_from_default,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "create_pull_request": {
            "handler": _call_create_pull_request,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "request_copilot_review": {
            "handler": _call_request_copilot_review,
            "required_scopes": _CHATGPT_COMPAT_SCOPES,
        },
        "dispatch_workflow": {"handler": _call_dispatch_workflow, "required_scopes": _CHATGPT_COMPAT_SCOPES},
    }


def _is_initialize_request(message: dict[str, Any]) -> bool:
    return message.get("method") == "initialize" and message.get("id") is not None


def _jsonrpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _jsonrpc_error(msg_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": error}