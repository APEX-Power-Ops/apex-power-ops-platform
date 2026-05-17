"""
Audit logging for mutations.
"""
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from app.auth.jwt import Actor
from app.db.memory_store import store
from app.envelope.request import MutationRequest


def record_audit_event(
    actor: Actor,
    request: MutationRequest,
    from_state: Dict[str, Any],
    to_state: Dict[str, Any],
    mutation_id: str,
    event_id: str | None = None,
    entity_type: str | None = None,
) -> str:
    """
    Record a mutation to the audit log.
    
    Args:
        actor: The authenticated actor performing the mutation
        request: The original mutation request
        from_state: Entity state before mutation
        to_state: Entity state after mutation
        mutation_id: The assigned mutation ID
    
    Returns:
        The audit event ID
    """
    event_id = event_id or f"audit-{uuid4()}"
    now = datetime.now(timezone.utc).isoformat()

    event = {
        "id": event_id,
        "mutation_id": mutation_id,
        "actor_id": actor.actor_id,
        "actor_role": actor.actor_role,
        "entity_type": entity_type or to_state.get("entity_type"),
        "action_type": request.action_type,
        "entity_id": request.entity_id,
        "mutation_class": request.mutation_class,
        "from_state": from_state,
        "to_state": to_state,
        "reason": request.reason,
        "client_timestamp": request.client_timestamp,
        "server_timestamp": now,
    }

    store.audit_log.append(event)
    return event_id
