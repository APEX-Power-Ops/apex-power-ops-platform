"""
Error codes and helpers for mutation responses.
"""
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from app.envelope.response import ErrorDetail, MutationResponse


class ErrorCode(str, Enum):
    """Standard error codes for the mutation seam."""

    IDEMPOTENCY_DUPLICATE = "IDEMPOTENCY_DUPLICATE"
    INVALID_ENVELOPE = "INVALID_ENVELOPE"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    UNAUTHORIZED_ROLE = "UNAUTHORIZED_ROLE"
    UNAUTHORIZED_SCOPE = "UNAUTHORIZED_SCOPE"
    OFFLINE_CLASS_C_REJECTED = "OFFLINE_CLASS_C_REJECTED"
    INVALID_MUTATION_CLASS = "INVALID_MUTATION_CLASS"
    TRANSITION_INVALID = "TRANSITION_INVALID"
    TRANSITION_CONFLICT = "TRANSITION_CONFLICT"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    ASSIGNMENT_CONFLICT = "ASSIGNMENT_CONFLICT"
    WITHDRAWAL_BLOCKED = "WITHDRAWAL_BLOCKED"
    CONCURRENT_MUTATION = "CONCURRENT_MUTATION"


ERROR_MESSAGES = {
    ErrorCode.IDEMPOTENCY_DUPLICATE: "This mutation was already processed",
    ErrorCode.INVALID_ENVELOPE: "Mutation request envelope is invalid",
    ErrorCode.INVALID_PAYLOAD: "Mutation payload failed validation",
    ErrorCode.ENTITY_NOT_FOUND: "Target entity does not exist",
    ErrorCode.UNAUTHORIZED_ROLE: "Current role is not authorized for this action",
    ErrorCode.UNAUTHORIZED_SCOPE: "Current scope does not include this resource",
    ErrorCode.OFFLINE_CLASS_C_REJECTED: "Class C mutations cannot be processed from offline queue",
    ErrorCode.INVALID_MUTATION_CLASS: "Mutation class is not valid for this action",
    ErrorCode.TRANSITION_INVALID: "State transition is not allowed",
    ErrorCode.TRANSITION_CONFLICT: "State has changed; transition is no longer valid",
    ErrorCode.PRECONDITION_FAILED: "Precondition for mutation not met",
    ErrorCode.ASSIGNMENT_CONFLICT: "Cannot reassign while already assigned to another user",
    ErrorCode.WITHDRAWAL_BLOCKED: "Cannot withdraw due to active dependencies",
    ErrorCode.CONCURRENT_MUTATION: "Concurrent mutation detected",
}


def error_response(
    code: ErrorCode,
    message: str,
    entity_id: str = "unknown",
    entity_type: str = "unknown",
    action_type: str = "unknown",
    detail: Optional[Dict[str, Any]] = None,
) -> MutationResponse:
    """
    Build a rejected mutation response.
    
    Args:
        code: ErrorCode enum value
        message: Custom error message
        entity_id: Target entity ID
        entity_type: Type of entity
        action_type: The action that was attempted
        detail: Optional additional error context
    
    Returns:
        MutationResponse with status="rejected"
    """
    return MutationResponse(
        status="rejected",
        mutation_id=f"mut-{uuid4()}",
        entity_id=entity_id,
        entity_type=entity_type,
        action_type=action_type,
        new_state={},
        audit_event_id=None,
        error=ErrorDetail(
            code=code.value,
            message=message,
            detail=detail,
        ),
        conflict=None,
    )
