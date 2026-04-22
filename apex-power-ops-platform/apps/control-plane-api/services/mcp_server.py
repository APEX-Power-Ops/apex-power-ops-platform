"""Minimal MCP transport for the governed control-plane surface."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from services.auth import (
    AuthenticatedUser,
    build_www_authenticate_header,
    describe_public_oauth_surface,
    get_authenticated_user_from_authorization,
)
from services.control_plane.router import (
    create_review_decision,
    fetch_job_run,
    fetch_priority_item,
    fetch_task_packet,
    fetch_validation_artifact,
    list_job_runs,
    list_lane_priorities,
    list_task_packets,
    lookup_validation_artifact,
    queue_local_action,
    update_task_packet_status,
)
from services.control_plane.schemas import (
    CreateReviewDecisionRequest,
    QueueLocalActionRequest,
    UpdateTaskPacketStatusRequest,
)

MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_SERVER_NAME = "apex-platform-governed-control-plane"
MCP_SERVER_VERSION = "1.0.0"


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


def build_mcp_root_payload(request: Request) -> dict[str, Any]:
    surface = describe_public_oauth_surface(request)
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
        "control_plane_url": surface["control_plane_url"],
        "transport": {
            "type": "streamable-http",
            "protocol_version": MCP_PROTOCOL_VERSION,
            "supports_sse_get": True,
            "notes": "Use POST /mcp for initialize, tools/list, and tools/call. GET /mcp serves either JSON discovery metadata or an SSE compatibility stream for clients that still expect GET-based event streams.",
        },
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "approved_tools": [tool["name"] for tool in _tool_definitions()],
        "authoring_scope": {
            "enabled": True,
            "mode": "staging_only",
            "requires_packet_allowlist": True,
            "requires_confirmed_by_user": True,
        },
    }


def handle_get_mcp(request: Request) -> JSONResponse:
    surface = describe_public_oauth_surface(request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "Public MCP root is not configured"
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

    return JSONResponse(build_mcp_root_payload(request))


def _format_sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def _stream_mcp_sse_compat(request: Request):
    surface = describe_public_oauth_surface(request)
    yield _format_sse("endpoint", surface["mcp_root_url"])
    if not await request.is_disconnected():
        yield ": keep-alive\n\n"


async def handle_post_mcp(request: Request, db: Session) -> Response:
    surface = describe_public_oauth_surface(request)
    if not surface["configured"]:
        detail = "; ".join(surface["validation_errors"]) if surface["validation_errors"] else "Public MCP root is not configured"
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
        "instructions": "Read-only and write tools are exposed through the governed control-plane only. Writes remain bounded and require confirmation and OAuth-backed identity.",
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
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, default=str),
                }
            ],
            "structuredContent": result,
            "isError": False,
        }
    except McpToolExecutionError as exc:
        payload = {
            "content": [{"type": "text", "text": exc.message}],
            "isError": True,
        }
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
        return get_authenticated_user_from_authorization(request, authorization)
    except HTTPException as exc:
        header = None
        if exc.headers:
            header = exc.headers.get("WWW-Authenticate") or exc.headers.get("www-authenticate")
        if header and scopes:
            header = f'{header}, scope="{" ".join(scopes)}"'
        detail = str(exc.detail)
        raise McpToolExecutionError(
            detail,
            meta={
                "mcp/www_authenticate": [
                    header or build_www_authenticate_header(request)
                ]
            },
        ) from exc


def _normalize_tool_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if isinstance(result, list):
        return {
            "items": result,
            "count": len(result),
        }
    return {"value": result}


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "list_task_packets",
            "title": "List Task Packets",
            "description": "List governed task packets filtered by lane, status, repo, or risk level.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "lane": {"type": "string"},
                    "status": {"type": "string"},
                    "primary_repo": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "fetch_task_packet",
            "title": "Fetch Task Packet",
            "description": "Fetch one governed task packet and its recent review decisions.",
            "inputSchema": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "update_task_packet_status",
            "title": "Update Task Packet Status",
            "description": "Advance a task packet through the approved status transitions with durable reasoning.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "new_status": {"type": "string"},
                    "reasoning_summary": {"type": "string"},
                },
                "required": ["task_id", "new_status", "reasoning_summary"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "create_review_decision",
            "title": "Create Review Decision",
            "description": "Record a governed review decision with optional evidence links.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "subject_type": {"type": "string"},
                    "subject_id": {"type": "string"},
                    "decision": {"type": "string"},
                    "reasoning_summary": {"type": "string"},
                    "required_next_action": {"type": ["string", "null"]},
                    "evidence_links": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["subject_type", "subject_id", "decision", "reasoning_summary"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "list_lane_priorities",
            "title": "List Lane Priorities",
            "description": "List lane-priority items by lane with the current ordering.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "lane": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
                },
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "fetch_priority_item",
            "title": "Fetch Priority Item",
            "description": "Fetch one lane-priority item by lane and item id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "lane": {"type": "string"},
                    "item_id": {"type": "string"},
                },
                "required": ["lane", "item_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "list_job_runs",
            "title": "List Job Runs",
            "description": "List governed local-action or validation job runs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "subject_type": {"type": "string"},
                    "subject_id": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "fetch_job_run",
            "title": "Fetch Job Run",
            "description": "Fetch one governed job run and its latest result payload.",
            "inputSchema": {
                "type": "object",
                "properties": {"job_id": {"type": "string"}},
                "required": ["job_id"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "fetch_validation_artifact",
            "title": "Fetch Validation Artifact",
            "description": "Fetch a validation artifact by artifact id or by subject type and subject id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "artifact_id": {"type": "string"},
                    "subject_type": {"type": "string"},
                    "subject_id": {"type": "string"},
                },
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
        {
            "name": "queue_local_action",
            "title": "Queue Local Action",
            "description": "Queue a bounded local action through the governed control-plane queue. Explicit confirmation is required.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "subject_type": {"type": "string"},
                    "subject_id": {"type": "string"},
                    "request_payload": {"type": "object"},
                    "task_id": {"type": ["string", "null"]},
                    "priority": {"type": "string", "default": "normal"},
                    "confirmed_by_user": {"type": "boolean", "const": True},
                },
                "required": ["action_type", "subject_type", "subject_id", "request_payload", "confirmed_by_user"],
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": False, "openWorldHint": False, "destructiveHint": False},
            "securitySchemes": [{"type": "oauth2", "scopes": ["openid", "profile", "email"]}],
        },
    ]


def _tool_registry() -> dict[str, dict[str, Any]]:
    registry = {
        "list_task_packets": {
            "handler": _call_list_task_packets,
            "required_scopes": ["openid", "profile", "email"],
        },
        "fetch_task_packet": {
            "handler": _call_fetch_task_packet,
            "required_scopes": ["openid", "profile", "email"],
        },
        "update_task_packet_status": {
            "handler": _call_update_task_packet_status,
            "required_scopes": ["openid", "profile", "email"],
        },
        "create_review_decision": {
            "handler": _call_create_review_decision,
            "required_scopes": ["openid", "profile", "email"],
        },
        "list_lane_priorities": {
            "handler": _call_list_lane_priorities,
            "required_scopes": ["openid", "profile", "email"],
        },
        "fetch_priority_item": {
            "handler": _call_fetch_priority_item,
            "required_scopes": ["openid", "profile", "email"],
        },
        "list_job_runs": {
            "handler": _call_list_job_runs,
            "required_scopes": ["openid", "profile", "email"],
        },
        "fetch_job_run": {
            "handler": _call_fetch_job_run,
            "required_scopes": ["openid", "profile", "email"],
        },
        "fetch_validation_artifact": {
            "handler": _call_fetch_validation_artifact,
            "required_scopes": ["openid", "profile", "email"],
        },
        "queue_local_action": {
            "handler": _call_queue_local_action,
            "required_scopes": ["openid", "profile", "email"],
        },
    }
    return registry


def _call_list_task_packets(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    return list_task_packets(
        lane=arguments.get("lane"),
        status_filter=arguments.get("status"),
        primary_repo=arguments.get("primary_repo"),
        risk_level=arguments.get("risk_level"),
        limit=int(arguments.get("limit") or 20),
        db=db,
        current_user=current_user,
    )


def _call_fetch_task_packet(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    task_id = str(arguments.get("task_id") or "").strip()
    if not task_id:
        raise McpProtocolError(-32602, "task_id is required")
    return fetch_task_packet(task_id=task_id, db=db, current_user=current_user)


def _call_update_task_packet_status(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    task_id = str(arguments.get("task_id") or "").strip()
    if not task_id:
        raise McpProtocolError(-32602, "task_id is required")
    payload = UpdateTaskPacketStatusRequest(
        new_status=arguments.get("new_status"),
        reasoning_summary=arguments.get("reasoning_summary"),
    )
    return update_task_packet_status(task_id=task_id, payload=payload, db=db, current_user=current_user)


def _call_create_review_decision(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    payload = CreateReviewDecisionRequest(
        subject_type=arguments.get("subject_type"),
        subject_id=arguments.get("subject_id"),
        decision=arguments.get("decision"),
        reasoning_summary=arguments.get("reasoning_summary"),
        required_next_action=arguments.get("required_next_action"),
        evidence_links=arguments.get("evidence_links") or [],
    )
    return create_review_decision(payload=payload, db=db, current_user=current_user)


def _call_list_lane_priorities(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    return list_lane_priorities(
        lane=arguments.get("lane"),
        limit=int(arguments.get("limit") or 20),
        db=db,
        current_user=current_user,
    )


def _call_fetch_priority_item(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    lane = str(arguments.get("lane") or "").strip()
    item_id = str(arguments.get("item_id") or "").strip()
    if not lane or not item_id:
        raise McpProtocolError(-32602, "lane and item_id are required")
    return fetch_priority_item(lane=lane, item_id=item_id, db=db, current_user=current_user)


def _call_list_job_runs(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    return list_job_runs(
        status_filter=arguments.get("status"),
        subject_type=arguments.get("subject_type"),
        subject_id=arguments.get("subject_id"),
        limit=int(arguments.get("limit") or 20),
        db=db,
        current_user=current_user,
    )


def _call_fetch_job_run(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    job_id = str(arguments.get("job_id") or "").strip()
    if not job_id:
        raise McpProtocolError(-32602, "job_id is required")
    return fetch_job_run(job_id=job_id, db=db, current_user=current_user)


def _call_fetch_validation_artifact(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    artifact_id = str(arguments.get("artifact_id") or "").strip() or None
    subject_type = str(arguments.get("subject_type") or "").strip() or None
    subject_id = str(arguments.get("subject_id") or "").strip() or None
    if artifact_id:
        return fetch_validation_artifact(artifact_id=artifact_id, db=db, current_user=current_user)
    if subject_type and subject_id:
        return lookup_validation_artifact(
            artifact_id=None,
            subject_type=subject_type,
            subject_id=subject_id,
            db=db,
            current_user=current_user,
        )
    raise McpProtocolError(-32602, "artifact_id or both subject_type and subject_id are required")


def _call_queue_local_action(arguments: dict[str, Any], db: Session, current_user: AuthenticatedUser) -> Any:
    payload = QueueLocalActionRequest(
        action_type=arguments.get("action_type"),
        subject_type=arguments.get("subject_type"),
        subject_id=arguments.get("subject_id"),
        request_payload=arguments.get("request_payload") or {},
        task_id=arguments.get("task_id"),
        priority=arguments.get("priority") or "normal",
        confirmed_by_user=bool(arguments.get("confirmed_by_user")),
    )
    return queue_local_action(payload=payload, db=db, current_user=current_user)


def _jsonrpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": jsonable_encoder(result)}


def _jsonrpc_error(msg_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if data is not None:
        payload["error"]["data"] = data
    return payload


def _is_initialize_request(message: dict[str, Any]) -> bool:
    return message.get("method") == "initialize"