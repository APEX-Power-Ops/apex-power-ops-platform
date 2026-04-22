"""
Mutation response envelope models.
"""
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail within a rejection response."""

    code: str = Field(
        ...,
        description="Machine-readable error code",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    detail: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional structured error information",
    )


class ConflictDetail(BaseModel):
    """Conflict detail for concurrent mutation scenarios."""

    server_state: Dict[str, Any] = Field(
        ...,
        description="Current server state of the entity",
    )
    queued_action: Dict[str, Any] = Field(
        ...,
        description="The conflicting action that would have been applied",
    )
    resolution_hint: str = Field(
        ...,
        description="Guidance on how to resolve the conflict",
    )


class MutationResponse(BaseModel):
    """
    Standard mutation response envelope.
    
    All mutations return via this structure, regardless of outcome.
    """

    status: Literal["accepted", "rejected", "conflict", "idempotent_hit"] = Field(
        ...,
        description="Mutation outcome status",
    )
    mutation_id: str = Field(
        ...,
        description="Server-assigned unique mutation ID",
    )
    entity_id: str = Field(
        ...,
        description="Target entity ID",
    )
    entity_type: str = Field(
        ...,
        description="Type of entity affected",
    )
    action_type: str = Field(
        ...,
        description="The mutation action type",
    )
    new_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Updated entity state (for accepted mutations)",
    )
    audit_event_id: Optional[str] = Field(
        None,
        description="ID of the audit log entry",
    )
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error details (if rejected)",
    )
    conflict: Optional[ConflictDetail] = Field(
        None,
        description="Conflict details (if conflict status)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "mutation_id": "mut-550e8400-e29b-41d4",
                "entity_id": "app-001",
                "entity_type": "apparatus",
                "action_type": "update_status",
                "new_state": {
                    "id": "app-001",
                    "status": "active",
                    "updated_at": "2026-04-16T14:30:05Z",
                },
                "audit_event_id": "audit-123456",
            }
        }
