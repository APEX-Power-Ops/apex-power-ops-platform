"""
Mutation request envelope models.
"""
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class MutationRequest(BaseModel):
    """
    Standard mutation request envelope.
    
    All mutations sent to the seam must conform to this structure.
    """

    idempotency_key: str = Field(
        ...,
        description="UUID or unique request identifier for idempotency",
        min_length=1,
    )
    mutation_class: Literal["A", "B", "C"] = Field(
        ...,
        description="Mutation governance class (A=online only, B=bidirectional, C=offline only)",
    )
    action_type: str = Field(
        ...,
        description="The mutation action (e.g., 'update_status', 'assign_apparatus')",
        min_length=1,
    )
    entity_id: Optional[str] = Field(
        None,
        description="Target entity ID; None for create actions",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Mutation data payload",
    )
    reason: Optional[str] = Field(
        None,
        description="Audit reason for the mutation",
    )
    source: Literal["online", "offline_queue"] = Field(
        "online",
        description="Where the mutation originated",
    )
    client_timestamp: str = Field(
        ...,
        description="Client-side ISO 8601 timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
                "mutation_class": "B",
                "action_type": "update_status",
                "entity_id": "app-001",
                "payload": {"status": "active"},
                "reason": "Started testing",
                "source": "online",
                "client_timestamp": "2026-04-16T14:30:00Z",
            }
        }
