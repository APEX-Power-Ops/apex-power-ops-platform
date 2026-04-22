"""Dedicated MCP transport for bounded Supabase platform operations."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.auth import (
    AuthenticatedUser,
    SUPABASE_MCP_OAUTH_SURFACE_ENV,
    build_www_authenticate_header_for_surface,
    describe_oauth_surface,
    get_authenticated_user_from_authorization_for_surface,
    user_has_required_scopes,
)

MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_SERVER_NAME = "apex-platform-supabase-operations"
MCP_SERVER_VERSION = "0.1.0"
_CHATGPT_COMPAT_SCOPES = ["openid", "profile", "email"]

_READONLY_SQL_PATTERN = re.compile(r"^\s*(select|with|show|explain)\b", re.IGNORECASE | re.DOTALL)
_DISALLOWED_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|alter|drop|create|grant|revoke|truncate|comment|vacuum|analyze|refresh|reindex|copy|call|do|merge|set|reset|begin|commit|rollback|savepoint|release|lock|checkpoint|listen|notify|unlisten)\b",
    re.IGNORECASE,
)
_COMMENT_PATTERN = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)
_MAX_READONLY_ROWS = 500
_MAX_LOG_ROWS = 200
_MAX_LOG_HOURS = 24
_DEFAULT_SUPABASE_CLI_TIMEOUT_SECONDS = 600
_DEFAULT_ALLOWED_MIGRATION_ROOTS = ("supabase/migrations", "migrations")


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


def build_supabase_mcp_root_payload(request: Request) -> dict[str, Any]:
    surface = describe_oauth_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
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
            "notes": "Use POST /supabase-mcp for initialize, tools/list, and tools/call. GET /supabase-mcp serves either JSON discovery metadata or an SSE compatibility stream.",
        },
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "approved_tools": [tool["name"] for tool in _tool_definitions()],
        "write_rules": {
            "confirmation_required": True,
            "allowlisted_paths_only": True,
            "audit_logging_required": True,
        },
    }


def handle_get_supabase_mcp(request: Request) -> JSONResponse:
    surface = describe_oauth_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "Supabase MCP surface is not configured"
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

    return JSONResponse(build_supabase_mcp_root_payload(request))


def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_mcp_sse_compat(request: Request):
    surface = describe_oauth_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
    yield _format_sse("endpoint", surface["mcp_root_url"])
    if not await request.is_disconnected():
        yield ": keep-alive\n\n"


async def handle_post_supabase_mcp(request: Request, db: Session) -> Response:
    surface = describe_oauth_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "Supabase MCP surface is not configured"
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


def _process_batch(messages: list[Any], request: Request, db: Session) -> list[dict[str, Any]]:
    responses: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            responses.append(_jsonrpc_error(None, -32600, "Invalid Request"))
            continue
        response = _process_message(message, request, db)
        if response is not None:
            responses.append(response)
    return responses


def _process_message(message: dict[str, Any], request: Request, db: Session) -> dict[str, Any] | None:
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
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": MCP_SERVER_NAME,
            "version": MCP_SERVER_VERSION,
        },
        "instructions": "This surface exposes bounded Supabase platform tools. Database reads are allowed through guarded read-only operations. Writes require explicit confirmation and allowlisted targets.",
    }


def _handle_tools_list() -> dict[str, Any]:
    return {"tools": _tool_definitions()}


def _handle_tools_call(params: dict[str, Any], request: Request, db: Session) -> dict[str, Any]:
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


def _require_tool_user(request: Request, *, scopes: list[str]) -> AuthenticatedUser:
    authorization = request.headers.get("authorization")
    try:
        user = get_authenticated_user_from_authorization_for_surface(
            request,
            authorization,
            surface_env=SUPABASE_MCP_OAUTH_SURFACE_ENV,
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
                    header or build_www_authenticate_header_for_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
                ]
            },
        ) from exc

    if not user_has_required_scopes(user, scopes):
        header = build_www_authenticate_header_for_surface(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
        required_scope_string = " ".join(scopes)
        raise McpToolExecutionError(
            f"Missing required scopes: {required_scope_string}",
            meta={"mcp/www_authenticate": [f'{header}, scope="{required_scope_string}"']},
        )
    return user


def _normalize_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {"items": result, "count": len(result)}
    return {"value": result}


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "get_project_context",
            "title": "Get Project Context",
            "description": "Return the bound Supabase project context and enabled tool families.",
            "inputSchema": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "list_tables",
            "title": "List Tables",
            "description": "List tables for one or more schemas with optional compact column summaries.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "schemas": {"type": "array", "items": {"type": "string"}},
                    "include_columns": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "describe_table",
            "title": "Describe Table",
            "description": "Return a detailed structure view for one table.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "schema": {"type": "string"},
                    "table": {"type": "string"},
                },
                "required": ["schema", "table"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "run_readonly_sql",
            "title": "Run Read-only SQL",
            "description": "Execute a strictly read-only SQL query with row and timeout guards.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "sql": {"type": "string"},
                    "row_limit": {"type": "integer", "minimum": 1, "maximum": _MAX_READONLY_ROWS, "default": 100},
                },
                "required": ["sql"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "get_advisory_notices",
            "title": "Get Advisory Notices",
            "description": "Return Supabase advisory notices when a management surface is configured.",
            "inputSchema": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "get_service_logs",
            "title": "Get Service Logs",
            "description": "Return recent service logs when a management surface is configured.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "service": {"type": "string"},
                    "hours": {"type": "integer", "minimum": 1, "maximum": _MAX_LOG_HOURS, "default": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_LOG_ROWS, "default": 50},
                },
                "required": ["service"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "search_supabase_docs",
            "title": "Search Supabase Docs",
            "description": "Return a normalized docs-search handoff for the requested query.",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": True, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "list_database_branches",
            "title": "List Database Branches",
            "description": "Return configured database branches when the management surface is available.",
            "inputSchema": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "create_database_branch",
            "title": "Create Database Branch",
            "description": "Create a disposable database branch after explicit confirmation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "branch_name": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["branch_name", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "list_edge_functions",
            "title": "List Edge Functions",
            "description": "List allowlisted Edge Function sources in the repository.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "get_edge_function_source",
            "title": "Get Edge Function Source",
            "description": "Read one allowlisted Edge Function source file from the repository.",
            "inputSchema": {
                "type": "object",
                "properties": {"function_name": {"type": "string"}},
                "required": ["function_name"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "deploy_edge_function_from_repo",
            "title": "Deploy Edge Function From Repo",
            "description": "Prepare or execute a bounded Edge Function deployment from an allowlisted repo root.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["function_name", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "apply_repo_migration",
            "title": "Apply Repo Migration",
            "description": "Apply one allowlisted repo migration after explicit confirmation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "migration_path": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["migration_path", "confirmed"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
        {
            "name": "get_publishable_keys",
            "title": "Get Publishable Keys",
            "description": "Return publishable API keys when the management surface is configured.",
            "inputSchema": {
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": _CHATGPT_COMPAT_SCOPES}],
        },
    ]


def _tool_registry() -> dict[str, dict[str, Any]]:
    return {
        "get_project_context": {"handler": _call_get_project_context, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "list_tables": {"handler": _call_list_tables, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "describe_table": {"handler": _call_describe_table, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "run_readonly_sql": {"handler": _call_run_readonly_sql, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "get_advisory_notices": {"handler": _call_get_advisory_notices, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "get_service_logs": {"handler": _call_get_service_logs, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "search_supabase_docs": {"handler": _call_search_supabase_docs, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "list_database_branches": {"handler": _call_list_database_branches, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "create_database_branch": {"handler": _call_create_database_branch, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "list_edge_functions": {"handler": _call_list_edge_functions, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "get_edge_function_source": {"handler": _call_get_edge_function_source, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "deploy_edge_function_from_repo": {"handler": _call_deploy_edge_function_from_repo, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "apply_repo_migration": {"handler": _call_apply_repo_migration, "required_scopes": _CHATGPT_COMPAT_SCOPES},
        "get_publishable_keys": {"handler": _call_get_publishable_keys, "required_scopes": _CHATGPT_COMPAT_SCOPES},
    }


def _is_initialize_request(payload: dict[str, Any]) -> bool:
    return payload.get("jsonrpc") == "2.0" and payload.get("method") == "initialize" and payload.get("id") is not None


def _jsonrpc_result(message_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _jsonrpc_error(message_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": message_id, "error": error}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_allowed_projects() -> list[dict[str, Any]]:
    raw = os.getenv("SUPABASE_ALLOWED_PROJECTS_JSON", "").strip()
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise McpToolExecutionError("SUPABASE_ALLOWED_PROJECTS_JSON is not valid JSON") from exc
        if not isinstance(payload, list):
            raise McpToolExecutionError("SUPABASE_ALLOWED_PROJECTS_JSON must be a JSON array")
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise McpToolExecutionError(f"SUPABASE_ALLOWED_PROJECTS_JSON[{index}] must be an object")
            normalized.append(
                {
                    "project_id": str(item.get("project_id") or item.get("project_ref") or "default").strip(),
                    "project_ref": str(item.get("project_ref") or item.get("project_id") or "default").strip(),
                    "environment_label": str(item.get("environment_label") or "unknown").strip(),
                    "allowed_write_modes": [str(value).strip() for value in item.get("allowed_write_modes", []) if str(value).strip()],
                    "enabled_tool_families": [str(value).strip() for value in item.get("enabled_tool_families", []) if str(value).strip()],
                }
            )
        return normalized

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    project_ref = "default"
    if supabase_url:
        host = supabase_url.split("//", 1)[-1].split("/", 1)[0]
        project_ref = host.split(".", 1)[0] or "default"
    return [
        {
            "project_id": project_ref,
            "project_ref": project_ref,
            "environment_label": os.getenv("APP_ENV", "development").strip() or "development",
            "allowed_write_modes": ["branches", "migrations", "edge_functions"],
            "enabled_tool_families": ["schema", "readonly_sql", "advisories", "logs", "branches", "edge_functions", "keys"],
        }
    ]


def _resolve_project(project_id: str | None) -> dict[str, Any]:
    projects = _parse_allowed_projects()
    if not projects:
        raise McpToolExecutionError("No allowed Supabase projects are configured")
    if not project_id:
        return projects[0]
    for project in projects:
        if project_id in {project["project_id"], project["project_ref"]}:
            return project
    raise McpToolExecutionError(f"Unknown or disallowed project_id: {project_id}")


def _require_project_write_mode(project: dict[str, Any], mode: str) -> None:
    allowed_modes = {str(value).strip() for value in project.get("allowed_write_modes", []) if str(value).strip()}
    if mode not in allowed_modes:
        raise McpToolExecutionError(
            f"Project {project['project_ref']} is not allowlisted for write mode: {mode}"
        )


def _supabase_management_base_url() -> str:
    return (os.getenv("SUPABASE_MANAGEMENT_API_URL", "https://api.supabase.com/v1").strip() or "https://api.supabase.com/v1").rstrip("/")


def _supabase_management_token() -> str:
    token = os.getenv("SUPABASE_MANAGEMENT_TOKEN", "").strip()
    if not token:
        raise _management_not_configured("management_api")
    return token


def _supabase_management_timeout_seconds() -> int:
    raw = os.getenv("SUPABASE_MANAGEMENT_TIMEOUT_SECONDS", "30").strip()
    try:
        timeout = int(raw or "30")
    except ValueError:
        timeout = 30
    return max(5, min(timeout, 120))


def _management_api_json(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    base_url = _supabase_management_base_url()
    token = _supabase_management_token()
    encoded_query = urlencode({key: value for key, value in (query or {}).items() if value is not None}, doseq=True)
    url = f"{base_url}{path}"
    if encoded_query:
        url = f"{url}?{encoded_query}"

    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": f"{MCP_SERVER_NAME}/{MCP_SERVER_VERSION}",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = UrlRequest(url, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=_supabase_management_timeout_seconds()) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace") if exc.fp is not None else ""
        detail = raw_body or exc.reason or f"HTTP {exc.code}"
        try:
            parsed = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            detail = str(parsed.get("error") or parsed.get("message") or parsed.get("msg") or detail)
        raise McpToolExecutionError(f"Supabase management API request failed: {detail}") from exc
    except URLError as exc:
        raise McpToolExecutionError(f"Supabase management API request failed: {exc.reason}") from exc

    if not raw_body:
        return {}
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise McpToolExecutionError("Supabase management API returned non-JSON content") from exc


def _normalize_advisory_item(payload: dict[str, Any], advisory_type: str) -> dict[str, Any]:
    categories = payload.get("categories") if isinstance(payload.get("categories"), list) else []
    return {
        "advisory_id": payload.get("cache_key") or payload.get("name"),
        "type": advisory_type,
        "severity": payload.get("level"),
        "category": categories[0] if categories else advisory_type.upper(),
        "summary": payload.get("title") or payload.get("description") or payload.get("name"),
        "recommended_action": payload.get("remediation"),
        "description": payload.get("description"),
        "detail": payload.get("detail"),
        "metadata": payload.get("metadata") or {},
    }


def _normalize_branch(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_id": payload.get("id"),
        "branch_name": payload.get("name"),
        "project_ref": payload.get("project_ref"),
        "parent_project_ref": payload.get("parent_project_ref"),
        "status": payload.get("status"),
        "git_branch": payload.get("git_branch"),
        "persistent": bool(payload.get("persistent")),
        "is_default": bool(payload.get("is_default")),
        "with_data": payload.get("with_data"),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "preview_project_status": payload.get("preview_project_status"),
    }


def _truncate_key_value(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 12:
        return value
    return f"{value[:8]}...{value[-4:]}"


def _normalize_publishable_key(payload: dict[str, Any], *, legacy_enabled: bool | None) -> dict[str, Any] | None:
    key_type = str(payload.get("type") or "").strip().lower()
    name = str(payload.get("name") or "").strip()
    lowered_name = name.lower()
    if key_type == "secret" or "service" in lowered_name:
        return None
    if key_type not in {"publishable", "legacy"} and "anon" not in lowered_name and "publishable" not in lowered_name:
        return None

    return {
        "key_id": payload.get("id"),
        "key_label": name or payload.get("id"),
        "key_type": key_type or None,
        "disabled": bool(payload.get("disabled", False)),
        "legacy_enabled": legacy_enabled if key_type == "legacy" else None,
        "value_preview": _truncate_key_value(str(payload.get("api_key") or "").strip() or None),
        "prefix": payload.get("prefix"),
        "description": payload.get("description"),
        "created_at": payload.get("inserted_at") or payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }


def _normalize_log_service(service: str) -> tuple[str, str]:
    normalized = str(service or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "api": ("edge_logs", "api"),
        "edge": ("edge_logs", "api"),
        "auth": ("auth_logs", "auth"),
        "storage": ("storage_logs", "storage"),
        "realtime": ("realtime_logs", "realtime"),
        "postgres": ("postgres_logs", "postgres"),
        "database": ("postgres_logs", "postgres"),
        "functions": ("function_logs", "functions"),
        "function": ("function_logs", "functions"),
        "edge_functions": ("function_logs", "functions"),
        "function_runtime": ("function_logs", "functions"),
        "function_edge": ("function_edge_logs", "function_edge"),
        "function_invocations": ("function_edge_logs", "function_edge"),
    }
    if normalized not in mapping:
        raise McpToolExecutionError(
            "service must be one of: api, auth, storage, realtime, postgres, database, functions, function_edge"
        )
    return mapping[normalized]


def _build_logs_sql(log_table: str, limit: int) -> str:
    bounded_limit = max(1, min(int(limit), _MAX_LOG_ROWS))
    return (
        "select datetime(timestamp) as timestamp, id, event_message, identifier "
        f"from {log_table} order by timestamp desc limit {bounded_limit}"
    )


def _iso_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _env_flag_enabled(name: str) -> bool:
    return str(os.getenv(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _require_execution_flag(tool_name: str, env_name: str) -> None:
    if not _env_flag_enabled(env_name):
        raise McpToolExecutionError(f"{tool_name} requires {env_name}=true in the server environment")


def _repo_relative_path(path: Path) -> str:
    repo_root = _repo_root()
    if path == repo_root or repo_root in path.parents:
        return str(path.relative_to(repo_root)).replace("\\", "/")
    return str(path)


def _truncate_command_output(value: str | None, *, limit: int = 2000) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[:limit].rstrip()}..."


def _supabase_cli_timeout_seconds() -> int:
    raw = str(os.getenv("SUPABASE_CLI_TIMEOUT_SECONDS") or "").strip()
    if not raw:
        return _DEFAULT_SUPABASE_CLI_TIMEOUT_SECONDS
    try:
        return max(30, min(int(raw), 3600))
    except ValueError as exc:
        raise McpToolExecutionError("SUPABASE_CLI_TIMEOUT_SECONDS must be an integer") from exc


def _supabase_cli_path() -> str:
    configured = str(os.getenv("SUPABASE_CLI_PATH") or "supabase").strip() or "supabase"
    candidate = Path(configured)
    if candidate.is_absolute():
        if candidate.exists() and candidate.is_file():
            return str(candidate)
        raise McpToolExecutionError(f"Supabase CLI executable not found: {configured}")

    resolved = shutil.which(configured)
    if resolved:
        return resolved
    raise McpToolExecutionError(
        "Supabase CLI executable not found. Set SUPABASE_CLI_PATH or install the Supabase CLI on the server host"
    )


def _supabase_cli_project_dir() -> Path:
    raw = str(os.getenv("SUPABASE_CLI_PROJECT_DIR") or "").strip()
    if not raw:
        return _repo_root()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (_repo_root() / candidate).resolve(strict=False)
    if not candidate.exists() or not candidate.is_dir():
        raise McpToolExecutionError(f"SUPABASE_CLI_PROJECT_DIR is not a directory: {candidate}")
    return candidate


def _supabase_access_token() -> str:
    token = str(os.getenv("SUPABASE_ACCESS_TOKEN") or "").strip()
    if not token:
        raise McpToolExecutionError("SUPABASE_ACCESS_TOKEN is required for Supabase CLI execution")
    return token


def _run_supabase_cli(command_args: list[str], *, cwd: Path) -> dict[str, Any]:
    command = [_supabase_cli_path(), *command_args]
    env = os.environ.copy()
    env["SUPABASE_ACCESS_TOKEN"] = _supabase_access_token()

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=_supabase_cli_timeout_seconds(),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise McpToolExecutionError(f"Supabase CLI command timed out after {exc.timeout} seconds") from exc
    except OSError as exc:
        raise McpToolExecutionError(f"Supabase CLI execution failed: {exc}") from exc

    stdout = _truncate_command_output(completed.stdout)
    stderr = _truncate_command_output(completed.stderr)
    if completed.returncode != 0:
        detail = stderr or stdout or "no output"
        raise McpToolExecutionError(f"Supabase CLI command failed: {detail}")

    return {
        "command": command_args,
        "cwd": str(cwd),
        "stdout": stdout,
        "stderr": stderr,
    }


def _read_sql_migration(migration_file: Path) -> str:
    sql_text = migration_file.read_text(encoding="utf-8")
    if not sql_text.strip():
        raise McpToolExecutionError(f"Migration file is empty: {_repo_relative_path(migration_file)}")
    return sql_text


def _apply_sql_migration(db: Session, migration_file: Path) -> dict[str, Any]:
    if db is None:
        raise McpToolExecutionError("Database session required for migration apply execution")

    sql_text = _read_sql_migration(migration_file)
    bind = db.get_bind() if hasattr(db, "get_bind") else None
    if bind is None or not hasattr(bind, "raw_connection"):
        raise McpToolExecutionError("Database session does not expose a raw connection for migration apply")

    raw_connection = bind.raw_connection()
    try:
        cursor = raw_connection.cursor()
        cursor.execute(sql_text)
        raw_connection.commit()
    except Exception as exc:
        raw_connection.rollback()
        raise McpToolExecutionError(f"Migration apply failed: {exc}") from exc
    finally:
        raw_connection.close()

    return {
        "execution_mode": "database_session",
        "line_count": len(sql_text.splitlines()),
        "byte_count": len(sql_text.encode("utf-8")),
    }


def _ensure_cli_deployable_function_layout(function_dir: Path, project_dir: Path) -> None:
    expected_root = (project_dir / "supabase" / "functions").resolve(strict=False)
    if function_dir.parent != expected_root:
        raise McpToolExecutionError(
            "deploy_edge_function_from_repo requires the function to live under SUPABASE_CLI_PROJECT_DIR/supabase/functions/<function_name>"
        )


def _record_write_audit(
    db: Session,
    *,
    tool_name: str,
    project: dict[str, Any],
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
                'supabase',
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
            "owner": "supabase",
            "repo": project["project_ref"],
            "target_type": target_type,
            "target_identifier": target_identifier,
            "request_summary": json.dumps(request_summary, default=str),
            "result_summary": json.dumps(result_summary, default=str),
        },
    )
    db.commit()
    return audit_id


def _normalize_schema_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["public"]
    normalized = [str(item).strip() for item in value if str(item).strip()]
    return normalized or ["public"]


def _sanitize_sql(sql: str) -> str:
    without_comments = _COMMENT_PATTERN.sub(" ", sql or "")
    return without_comments.strip()


def _assert_readonly_sql(sql: str) -> str:
    normalized = _sanitize_sql(sql)
    if not normalized:
        raise McpToolExecutionError("sql is required")
    if normalized.count(";") > 1 or (";" in normalized and not normalized.endswith(";")):
        raise McpToolExecutionError("Only a single SQL statement is allowed")
    normalized = normalized.rstrip(";").strip()
    if not _READONLY_SQL_PATTERN.match(normalized):
        raise McpToolExecutionError("Only read-only SELECT, WITH, SHOW, or EXPLAIN statements are allowed")
    if _DISALLOWED_SQL_PATTERN.search(normalized):
        raise McpToolExecutionError("The SQL statement is not read-only")
    return normalized


def _query_table_summaries(db: Session, schemas: list[str], *, include_columns: bool) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                t.table_schema,
                t.table_name,
                COALESCE(c.relrowsecurity, false) AS rls_enabled,
                CASE WHEN :include_columns THEN (
                    SELECT json_agg(
                        json_build_object(
                            'name', c2.column_name,
                            'data_type', c2.data_type,
                            'nullable', c2.is_nullable = 'YES'
                        )
                        ORDER BY c2.ordinal_position
                    )
                    FROM information_schema.columns c2
                    WHERE c2.table_schema = t.table_schema
                      AND c2.table_name = t.table_name
                ) ELSE NULL END AS columns
            FROM information_schema.tables t
            LEFT JOIN pg_namespace n ON n.nspname = t.table_schema
            LEFT JOIN pg_class c ON c.relname = t.table_name AND c.relnamespace = n.oid
            WHERE t.table_type = 'BASE TABLE'
              AND t.table_schema = ANY(:schemas)
            ORDER BY t.table_schema, t.table_name
            """
        ),
        {"schemas": schemas, "include_columns": include_columns},
    )
    return [dict(row._mapping) for row in rows]


def _query_table_columns(db: Session, schema: str, table: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable = 'YES' AS is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
            ORDER BY ordinal_position
            """
        ),
        {"schema": schema, "table": table},
    )
    return [dict(row._mapping) for row in rows]


def _query_primary_keys(db: Session, schema: str, table: str) -> list[str]:
    rows = db.execute(
        text(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = :schema
              AND tc.table_name = :table
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """
        ),
        {"schema": schema, "table": table},
    )
    return [str(row._mapping["column_name"]) for row in rows]


def _query_foreign_keys(db: Session, schema: str, table: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = :schema
              AND tc.table_name = :table
            ORDER BY tc.constraint_name, kcu.ordinal_position
            """
        ),
        {"schema": schema, "table": table},
    )
    return [dict(row._mapping) for row in rows]


def _query_indexes(db: Session, schema: str, table: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = :schema
              AND tablename = :table
            ORDER BY indexname
            """
        ),
        {"schema": schema, "table": table},
    )
    return [dict(row._mapping) for row in rows]


def _query_rls_status(db: Session, schema: str, table: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT COALESCE(c.relrowsecurity, false) AS rls_enabled
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = :schema
              AND c.relname = :table
            """
        ),
        {"schema": schema, "table": table},
    ).first()
    return bool(row._mapping["rls_enabled"]) if row is not None else False


def _run_sql_rows(db: Session, sql: str, *, row_limit: int) -> dict[str, Any]:
    limited = max(1, min(int(row_limit), _MAX_READONLY_ROWS))
    result = db.execute(text(sql))
    mappings = result.mappings().fetchmany(limited + 1)
    truncated = len(mappings) > limited
    rows = [dict(item) for item in mappings[:limited]]
    return {
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "row_limit": limited,
    }


def _normalize_function_name(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _allowed_function_roots() -> list[Path]:
    raw = os.getenv("SUPABASE_ALLOWED_FUNCTION_ROOTS", "").strip()
    if not raw:
        return []
    roots: list[Path] = []
    repo_root = _repo_root()
    for part in raw.replace("\r", "\n").replace(",", "\n").split("\n"):
        candidate = part.strip()
        if not candidate:
            continue
        root = Path(candidate)
        if not root.is_absolute():
            root = (repo_root / root).resolve(strict=False)
        roots.append(root)
    return roots


def _find_edge_function(function_name: str) -> Path:
    normalized_name = _normalize_function_name(function_name).strip("/")
    if not normalized_name:
        raise McpToolExecutionError("function_name is required")
    for root in _allowed_function_roots():
        candidate = (root / normalized_name).resolve(strict=False)
        if candidate.exists() and candidate.is_dir() and root in candidate.parents:
            return candidate
    raise McpToolExecutionError(f"Function root is not allowlisted or does not exist: {function_name}")


def _list_functions() -> list[dict[str, Any]]:
    functions: list[dict[str, Any]] = []
    for root in _allowed_function_roots():
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir():
                functions.append({
                    "function_name": child.name,
                    "root": str(root.relative_to(_repo_root())).replace("\\", "/") if _repo_root() in root.parents or root == _repo_root() else str(root),
                    "path": str(child.relative_to(_repo_root())).replace("\\", "/") if _repo_root() in child.parents or child == _repo_root() else str(child),
                })
    return functions


def _allowed_migration_roots() -> list[Path]:
    raw = os.getenv("SUPABASE_ALLOWED_MIGRATION_ROOTS", "").strip()
    values = [part.strip() for part in raw.replace("\r", "\n").replace(",", "\n").split("\n") if part.strip()]
    if not values:
        values = list(_DEFAULT_ALLOWED_MIGRATION_ROOTS)
    repo_root = _repo_root()
    return [(repo_root / value).resolve(strict=False) for value in values]


def _resolve_allowlisted_migration(migration_path: str) -> Path:
    repo_root = _repo_root()
    candidate = Path(str(migration_path or "").strip().replace("\\", "/"))
    if not str(candidate):
        raise McpToolExecutionError("migration_path is required")
    if candidate.is_absolute():
        raise McpToolExecutionError("migration_path must be relative to the repository root")
    resolved = (repo_root / candidate).resolve(strict=False)
    if not resolved.exists() or not resolved.is_file():
        raise McpToolExecutionError(f"Migration file not found: {migration_path}")
    if not any(root == resolved.parent or root in resolved.parents for root in _allowed_migration_roots()):
        raise McpToolExecutionError("migration_path is outside the allowlisted migration roots")
    return resolved


def _call_get_project_context(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    return {
        "project_id": project["project_id"],
        "project_ref": project["project_ref"],
        "environment_label": project["environment_label"],
        "allowed_write_modes": project["allowed_write_modes"],
        "enabled_tool_families": project["enabled_tool_families"],
    }


def _call_list_tables(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    schemas = _normalize_schema_list(arguments.get("schemas"))
    include_columns = bool(arguments.get("include_columns", False))
    items = _query_table_summaries(db, schemas, include_columns=include_columns)
    return {
        "project_ref": project["project_ref"],
        "schemas": schemas,
        "count": len(items),
        "items": items,
    }


def _call_describe_table(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    schema = str(arguments.get("schema") or "").strip()
    table = str(arguments.get("table") or "").strip()
    if not schema or not table:
        raise McpToolExecutionError("schema and table are required")

    columns = _query_table_columns(db, schema, table)
    if not columns:
        raise McpToolExecutionError(f"Table not found: {schema}.{table}")

    return {
        "project_ref": project["project_ref"],
        "schema": schema,
        "table": table,
        "columns": columns,
        "primary_key": _query_primary_keys(db, schema, table),
        "foreign_keys": _query_foreign_keys(db, schema, table),
        "indexes": _query_indexes(db, schema, table),
        "rls_enabled": _query_rls_status(db, schema, table),
    }


def _call_run_readonly_sql(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    sql = _assert_readonly_sql(str(arguments.get("sql") or ""))
    row_limit = int(arguments.get("row_limit") or 100)
    result = _run_sql_rows(db, sql, row_limit=row_limit)
    result.update({"project_ref": project["project_ref"], "sql": sql})
    return result


def _management_not_configured(tool_name: str) -> McpToolExecutionError:
    return McpToolExecutionError(f"{tool_name} requires a configured Supabase management surface and is not available in the current environment")


def _call_get_advisory_notices(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    ref = quote(project["project_ref"], safe="")
    items: list[dict[str, Any]] = []
    for advisory_type in ("security", "performance"):
        payload = _management_api_json("GET", f"/projects/{ref}/advisors/{advisory_type}")
        lints = payload.get("lints", []) if isinstance(payload, dict) else []
        for lint in lints:
            if isinstance(lint, dict):
                items.append(_normalize_advisory_item(lint, advisory_type))
    return {
        "project_ref": project["project_ref"],
        "count": len(items),
        "items": items,
    }


def _call_get_service_logs(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    log_table, normalized_service = _normalize_log_service(str(arguments.get("service") or ""))
    hours = max(1, min(int(arguments.get("hours") or 1), _MAX_LOG_HOURS))
    limit = max(1, min(int(arguments.get("limit") or 50), _MAX_LOG_ROWS))
    end_time = _iso_utc_now().replace(microsecond=0)
    start_time = (end_time - timedelta(hours=hours)).replace(microsecond=0)
    payload = _management_api_json(
        "GET",
        f"/projects/{quote(project['project_ref'], safe='')}/analytics/endpoints/logs.all",
        query={
            "iso_timestamp_start": start_time.isoformat().replace("+00:00", "Z"),
            "iso_timestamp_end": end_time.isoformat().replace("+00:00", "Z"),
            "sql": _build_logs_sql(log_table, limit),
        },
    )
    results = payload.get("result", []) if isinstance(payload, dict) else []
    error = payload.get("error") if isinstance(payload, dict) else None
    if error:
        raise McpToolExecutionError(f"Supabase logs query failed: {error}")
    items = [item for item in results if isinstance(item, dict)]
    return {
        "project_ref": project["project_ref"],
        "service": normalized_service,
        "log_source": log_table,
        "hours": hours,
        "limit": limit,
        "count": len(items),
        "items": items,
    }


def _call_search_supabase_docs(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise McpToolExecutionError("query is required")
    return {
        "query": query,
        "search_url": f"https://supabase.com/docs?query={query.replace(' ', '+')}",
        "notes": "Public docs search is not yet server-indexed in this backend slice; use the returned query URL for manual follow-through.",
    }


def _call_list_database_branches(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    payload = _management_api_json("GET", f"/projects/{quote(project['project_ref'], safe='')}/branches")
    branches = payload if isinstance(payload, list) else []
    items = [_normalize_branch(branch) for branch in branches if isinstance(branch, dict)]
    return {
        "project_ref": project["project_ref"],
        "count": len(items),
        "items": items,
    }


def _require_confirmed(arguments: dict[str, Any], *, action_label: str) -> None:
    if not bool(arguments.get("confirmed", False)):
        raise McpToolExecutionError(f"{action_label} requires confirmed=true")


def _call_create_database_branch(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmed(arguments, action_label="create_database_branch")
    project = _resolve_project(arguments.get("project_id"))
    _require_project_write_mode(project, "branches")
    branch_name = str(arguments.get("branch_name") or "").strip()
    if not branch_name:
        raise McpToolExecutionError("branch_name is required")
    if any(char.isspace() for char in branch_name):
        raise McpToolExecutionError("branch_name must not contain whitespace")
    payload = _management_api_json(
        "POST",
        f"/projects/{quote(project['project_ref'], safe='')}/branches",
        body={"branch_name": branch_name},
    )
    if not isinstance(payload, dict):
        raise McpToolExecutionError("Supabase management API returned an invalid branch payload")
    branch = _normalize_branch(payload)
    audit_id = _record_write_audit(
        db,
        tool_name="create_database_branch",
        project=project,
        current_user=current_user,
        target_type="database_branch",
        target_identifier=branch_name,
        request_summary={"project_ref": project["project_ref"], "branch_name": branch_name},
        result_summary={"branch_id": branch.get("branch_id"), "status": branch.get("status")},
    )
    branch["audit_id"] = audit_id
    return branch


def _call_list_edge_functions(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    items = _list_functions()
    return {"count": len(items), "items": items}


def _call_get_edge_function_source(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    function_dir = _find_edge_function(str(arguments.get("function_name") or ""))
    files: list[dict[str, Any]] = []
    for child in sorted(function_dir.rglob("*")):
        if child.is_file() and child.stat().st_size <= 100_000:
            files.append(
                {
                    "path": str(child.relative_to(_repo_root())).replace("\\", "/"),
                    "content": child.read_text(encoding="utf-8"),
                }
            )
    return {
        "function_name": function_dir.name,
        "path": str(function_dir.relative_to(_repo_root())).replace("\\", "/"),
        "files": files,
    }


def _call_deploy_edge_function_from_repo(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmed(arguments, action_label="deploy_edge_function_from_repo")
    project = _resolve_project(arguments.get("project_id"))
    _require_project_write_mode(project, "edge_functions")
    _require_execution_flag("deploy_edge_function_from_repo", "SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY")
    function_dir = _find_edge_function(str(arguments.get("function_name") or ""))
    project_dir = _supabase_cli_project_dir()
    _ensure_cli_deployable_function_layout(function_dir, project_dir)
    cli_result = _run_supabase_cli(
        ["functions", "deploy", function_dir.name, "--project-ref", project["project_ref"]],
        cwd=project_dir,
    )
    audit_id = _record_write_audit(
        db,
        tool_name="deploy_edge_function_from_repo",
        project=project,
        current_user=current_user,
        target_type="edge_function",
        target_identifier=function_dir.name,
        request_summary={
            "project_ref": project["project_ref"],
            "function_name": function_dir.name,
            "path": _repo_relative_path(function_dir),
        },
        result_summary={
            "execution_mode": "supabase_cli",
            "stdout": cli_result.get("stdout"),
            "stderr": cli_result.get("stderr"),
        },
    )
    return {
        "status": "deployed",
        "project_ref": project["project_ref"],
        "function_name": function_dir.name,
        "path": _repo_relative_path(function_dir),
        "execution_mode": "supabase_cli",
        "command": cli_result["command"],
        "stdout": cli_result.get("stdout"),
        "stderr": cli_result.get("stderr"),
        "audit_id": audit_id,
    }


def _call_apply_repo_migration(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    _require_confirmed(arguments, action_label="apply_repo_migration")
    project = _resolve_project(arguments.get("project_id"))
    _require_project_write_mode(project, "migrations")
    _require_execution_flag("apply_repo_migration", "SUPABASE_ENABLE_MIGRATION_APPLY")
    migration_file = _resolve_allowlisted_migration(str(arguments.get("migration_path") or ""))
    apply_result = _apply_sql_migration(db, migration_file)
    audit_id = _record_write_audit(
        db,
        tool_name="apply_repo_migration",
        project=project,
        current_user=current_user,
        target_type="sql_migration",
        target_identifier=_repo_relative_path(migration_file),
        request_summary={
            "project_ref": project["project_ref"],
            "migration_path": _repo_relative_path(migration_file),
        },
        result_summary=apply_result,
    )
    return {
        "status": "applied",
        "project_ref": project["project_ref"],
        "migration_path": _repo_relative_path(migration_file),
        "audit_id": audit_id,
        **apply_result,
    }


def _call_get_publishable_keys(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    project = _resolve_project(arguments.get("project_id"))
    ref = quote(project["project_ref"], safe="")
    keys_payload = _management_api_json("GET", f"/projects/{ref}/api-keys")
    legacy_payload = _management_api_json("GET", f"/projects/{ref}/api-keys/legacy")
    legacy_enabled = legacy_payload.get("enabled") if isinstance(legacy_payload, dict) else None
    keys = keys_payload if isinstance(keys_payload, list) else []
    items = []
    for key_payload in keys:
        if not isinstance(key_payload, dict):
            continue
        normalized = _normalize_publishable_key(key_payload, legacy_enabled=legacy_enabled)
        if normalized is not None:
            items.append(normalized)
    return {
        "project_ref": project["project_ref"],
        "count": len(items),
        "items": items,
    }