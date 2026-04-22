"""
JWT authentication for the mutation seam.
For prototype, uses simple base64-encoded JSON tokens.
"""
import base64
import json
from dataclasses import dataclass
from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status


@dataclass
class Actor:
    """Authenticated user/principal."""

    actor_id: str
    actor_role: str
    project_scope: List[str]


async def get_current_actor(
    authorization: Optional[str] = Header(None),
) -> Actor:
    """
    Extract and validate the current actor from Authorization header.
    
    For the prototype, accepts a simple base64-encoded JSON payload.
    Production would use real JWT verification.
    
    Args:
        authorization: Bearer token from Authorization header
    
    Returns:
        Actor with credentials
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    # If no auth header, return default dev actor
    if not authorization:
        return Actor(
            actor_id="tech-001",
            actor_role="field_tech",
            project_scope=["proj-001"],
        )

    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization[7:]  # Remove "Bearer "

    try:
        # Decode base64 payload
        decoded = base64.b64decode(token).decode("utf-8")
        payload = json.loads(decoded)

        # Extract actor fields
        actor_id = payload.get("actor_id")
        actor_role = payload.get("actor_role")
        project_scope = payload.get("project_scope", [])

        if not actor_id or not actor_role:
            raise ValueError("Missing required fields in token")

        return Actor(
            actor_id=actor_id,
            actor_role=actor_role,
            project_scope=project_scope,
        )

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
