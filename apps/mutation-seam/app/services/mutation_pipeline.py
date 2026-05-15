"""
Core mutation pipeline orchestrator.
Implements the 13-stage governed mutation flow.
"""
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime, timezone
from uuid import uuid4

from app.auth.jwt import Actor
from app.auth.role_guard import check_role, check_scope
from app.audit.logger import record_audit_event
from app.db.memory_store import store
from app.envelope.errors import ErrorCode, error_response
from app.envelope.request import MutationRequest
from app.envelope.response import MutationResponse
from app.idempotency.store import check_idempotency, save_idempotency
from app.lifecycle.transitions import validate_transition


# Action registry: maps (entity_type, action_type) to mutation metadata.
# Action names are scoped per entity family, matching the UI-006 spec 1.3.
ACTION_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "apparatus": {
        "update_status": {
            "governed_class": "B",
            "allowed_roles": ["field_tech", "lead", "pm"],
            "is_lifecycle": True,
        },
        "update_assessment": {
            "governed_class": "B",
            "allowed_roles": ["field_tech", "lead"],
            "is_lifecycle": False,
        },
    },
    "checklist_item": {
        "complete_item": {
            "governed_class": "A",
            "allowed_roles": ["field_tech"],
            "is_lifecycle": False,
        },
        "update_note": {
            "governed_class": "A",
            "allowed_roles": ["field_tech"],
            "is_lifecycle": False,
        },
    },
    "hours": {
        "log_entry": {
            "governed_class": "A",
            "allowed_roles": ["field_tech"],
            "is_lifecycle": False,
        },
    },
    "issue": {
        "create": {
            "governed_class": "B",
            "allowed_roles": ["field_tech", "lead"],
            "is_lifecycle": False,
        },
        "begin_review": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "update_severity": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": False,
        },
        "set_blocking": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": False,
        },
        "resolve": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "escalate_to_pm": {
            "governed_class": "C",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "resolve_escalated": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "re_escalate": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "return_to_lead": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
    },
    "assignment": {
        "assign": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": False,
        },
        "reassign": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": False,
        },
        "reprioritize": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": False,
        },
    },
    "task": {
        "start": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "pause": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "resume": {
            "governed_class": "B",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "submit_for_review": {
            "governed_class": "C",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "withdraw_submission": {
            "governed_class": "C",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "approve": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "reject": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "escalate_review": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
    },
    "workpackage": {
        "submit_for_review": {
            "governed_class": "C",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "withdraw_submission": {
            "governed_class": "C",
            "allowed_roles": ["lead"],
            "is_lifecycle": True,
        },
        "approve": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "reject": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "escalate_review": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
    },
    "snapshot": {
        "approve": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
        "reject": {
            "governed_class": "C",
            "allowed_roles": ["pm"],
            "is_lifecycle": True,
        },
    },
}


async def execute_mutation(
    request: MutationRequest,
    actor: Actor,
    entity_type: str,
) -> MutationResponse:
    """
    Execute a mutation through the 13-stage pipeline.

    Stages:
    1. (Envelope validation done by Pydantic)
    2. Idempotency check
    3. Source validation (reject offline Class C)
    4. Class validation
    5. Role check
    6. Entity load
    7. Payload validation
    8. Transition validation (for lifecycle actions)
    8b. Blocking-issue gate (for approve actions)
    9. Apply mutation
    10. Audit event
    11. Save idempotency
    12. (Realtime deferred)
    13. Return response
    """
    mutation_id = f"mut-{uuid4()}"

    # ===== STAGE 2: Idempotency check =====
    existing = check_idempotency(request.idempotency_key)
    if existing:
        return MutationResponse(
            status="idempotent_hit",
            mutation_id=existing.mutation_id,
            entity_id=existing.entity_id,
            entity_type=existing.entity_type,
            action_type=existing.action_type,
            new_state=existing.new_state,
            audit_event_id=existing.audit_event_id,
        )

    # Get action metadata from two-level registry (entity_type -> action_type)
    entity_actions = ACTION_REGISTRY.get(entity_type, {})
    if request.action_type not in entity_actions:
        response = error_response(
            code=ErrorCode.INVALID_PAYLOAD,
            message=f"Unknown action type: {request.action_type} for entity {entity_type}",
            entity_id=request.entity_id or "unknown",
            entity_type=entity_type,
            action_type=request.action_type,
        )
        save_idempotency(request.idempotency_key, response)
        return response

    action_meta = entity_actions[request.action_type]

    # ===== STAGE 3: Source validation (reject offline Class C) =====
    if request.source == "offline_queue" and action_meta["governed_class"] == "C":
        response = error_response(
            code=ErrorCode.OFFLINE_CLASS_C_REJECTED,
            message="Class C mutations cannot be queued offline",
            entity_id=request.entity_id or "unknown",
            entity_type=entity_type,
            action_type=request.action_type,
        )
        save_idempotency(request.idempotency_key, response)
        return response

    # ===== STAGE 4: Class validation =====
    declared_class = request.mutation_class
    governed_class = action_meta["governed_class"]
    class_order = {"C": 0, "B": 1, "A": 2}
    if class_order.get(declared_class, -1) > class_order.get(governed_class, -1):
        response = error_response(
            code=ErrorCode.INVALID_MUTATION_CLASS,
            message=f"Action requires class {governed_class}, declared {declared_class}",
            entity_id=request.entity_id or "unknown",
            entity_type=entity_type,
            action_type=request.action_type,
        )
        save_idempotency(request.idempotency_key, response)
        return response

    # ===== STAGE 5: Role check =====
    allowed_roles = action_meta["allowed_roles"]
    if not check_role(actor, allowed_roles):
        response = error_response(
            code=ErrorCode.UNAUTHORIZED_ROLE,
            message=f"Role {actor.actor_role} not authorized; requires one of {allowed_roles}",
            entity_id=request.entity_id or "unknown",
            entity_type=entity_type,
            action_type=request.action_type,
        )
        save_idempotency(request.idempotency_key, response)
        return response

    # ===== STAGE 6: Entity load =====
    from_state = {}
    if request.entity_id:
        entity_store = _get_store_for_entity_type(entity_type)
        if request.entity_id not in entity_store:
            response = error_response(
                code=ErrorCode.ENTITY_NOT_FOUND,
                message=f"{entity_type} {request.entity_id} not found",
                entity_id=request.entity_id,
                entity_type=entity_type,
                action_type=request.action_type,
            )
            save_idempotency(request.idempotency_key, response)
            return response
        from_state = entity_store[request.entity_id].copy()

    # ===== STAGE 7: Payload validation =====
    if not request.payload:
        request.payload = {}

    if entity_type == "issue" and request.action_type == "return_to_lead":
        disposition_error = _validate_issue_return_to_lead(request, actor, from_state)
        if disposition_error:
            save_idempotency(request.idempotency_key, disposition_error)
            return disposition_error

    # ===== STAGE 8: Transition validation =====
    if action_meta["is_lifecycle"] and "status" in request.payload:
        new_status = request.payload["status"]
        old_status = from_state.get("status", "unknown")
        if not validate_transition(entity_type, old_status, new_status):
            response = error_response(
                code=ErrorCode.TRANSITION_INVALID,
                message=f"Cannot transition {entity_type} from {old_status} to {new_status}",
                entity_id=request.entity_id or "unknown",
                entity_type=entity_type,
                action_type=request.action_type,
                detail={
                    "from_state": old_status,
                    "to_state": new_status,
                },
            )
            save_idempotency(request.idempotency_key, response)
            return response

    # ===== STAGE 8b: Blocking-issue gate (for approve actions) =====
    if request.action_type == "approve" and entity_type in ("task", "workpackage"):
        blocking_issues = _get_blocking_issues_for_entity(entity_type, request.entity_id)
        if blocking_issues:
            response = error_response(
                code=ErrorCode.PRECONDITION_FAILED,
                message=f"Cannot approve {entity_type}: {len(blocking_issues)} unresolved blocking issue(s)",
                entity_id=request.entity_id or "unknown",
                entity_type=entity_type,
                action_type=request.action_type,
                detail={
                    "blocking_issues": [{"id": i["id"], "title": i.get("title", ""), "severity": i.get("severity", "")} for i in blocking_issues],
                },
            )
            save_idempotency(request.idempotency_key, response)
            return response

    # ===== STAGE 9: Apply mutation =====
    now = datetime.now(timezone.utc).isoformat()
    entity_store = _get_store_for_entity_type(entity_type)

    if request.entity_id and request.entity_id in entity_store:
        to_state = entity_store[request.entity_id].copy()
        to_state.update(request.payload)
        to_state["updated_at"] = now
        entity_store[request.entity_id] = to_state
    else:
        to_state = {
            "id": request.entity_id or f"{entity_type}-{uuid4()}",
            **request.payload,
            "created_at": now,
            "updated_at": now,
        }
        entity_store[to_state["id"]] = to_state

    # ===== STAGE 10: Audit event =====
    audit_event_id = record_audit_event(
        actor=actor,
        request=request,
        from_state=from_state,
        to_state=to_state,
        mutation_id=mutation_id,
    )

    # ===== STAGE 11: Save idempotency =====
    response = MutationResponse(
        status="accepted",
        mutation_id=mutation_id,
        entity_id=to_state["id"],
        entity_type=entity_type,
        action_type=request.action_type,
        new_state=to_state,
        audit_event_id=audit_event_id,
    )
    save_idempotency(request.idempotency_key, response)

    # ===== STAGE 12 (deferred): Realtime notification =====
    # TODO: Emit to realtime subscribers

    # ===== STAGE 13: Return response =====
    return response


def _get_store_for_entity_type(entity_type: str) -> Dict[str, Any]:
    """Get the appropriate memory store dict for an entity type."""
    stores = {
        "apparatus": store.apparatus,
        "checklist_item": store.checklist_items,
        "hours": store.hours,
        "issue": store.issues,
        "assignment": store.assignments,
        "task": store.tasks,
        "workpackage": store.workpackages,
        "snapshot": store.snapshots,
    }
    return stores.get(entity_type, {})


def _validate_issue_return_to_lead(
    request: MutationRequest,
    actor: Actor,
    from_state: Dict[str, Any],
) -> Optional[MutationResponse]:
    """Validate PM issue disposition semantics beyond generic issue transitions."""
    project_id = from_state.get("project_id")
    if not project_id or not check_scope(actor, project_id):
        return error_response(
            code=ErrorCode.UNAUTHORIZED_SCOPE,
            message="Actor project scope does not include this issue",
            entity_id=request.entity_id or "unknown",
            entity_type="issue",
            action_type=request.action_type,
            detail={"project_id": project_id, "actor_scope": actor.project_scope},
        )

    if str(from_state.get("status") or "").lower() != "escalated":
        return error_response(
            code=ErrorCode.PRECONDITION_FAILED,
            message="Only escalated issues can be returned to lead review",
            entity_id=request.entity_id or "unknown",
            entity_type="issue",
            action_type=request.action_type,
            detail={"current_status": from_state.get("status")},
        )

    if request.payload.get("status") != "in_review":
        return error_response(
            code=ErrorCode.INVALID_PAYLOAD,
            message="return_to_lead requires payload.status to be in_review",
            entity_id=request.entity_id or "unknown",
            entity_type="issue",
            action_type=request.action_type,
            detail={"requested_status": request.payload.get("status")},
        )

    if not (request.reason or "").strip():
        return error_response(
            code=ErrorCode.INVALID_PAYLOAD,
            message="return_to_lead requires a PM disposition reason",
            entity_id=request.entity_id or "unknown",
            entity_type="issue",
            action_type=request.action_type,
        )

    return None


def _get_blocking_issues_for_entity(entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
    """
    Find unresolved blocking issues for a task or workpackage.
    Used by the blocking-issue gate in the approve action.
    """
    blocking = []
    if entity_type == "task":
        for issue in store.issues.values():
            if (issue.get("blocks_completion") and
                    issue.get("status") not in ("resolved", "closed")):
                app = store.apparatus.get(issue.get("apparatus_id", ""))
                if app and app.get("task_id") == entity_id:
                    blocking.append(issue)
    elif entity_type == "workpackage":
        wp_task_ids = {t["id"] for t in store.tasks.values() if t.get("workpackage_id") == entity_id}
        for issue in store.issues.values():
            if (issue.get("blocks_completion") and
                    issue.get("status") not in ("resolved", "closed")):
                app = store.apparatus.get(issue.get("apparatus_id", ""))
                if app and app.get("task_id") in wp_task_ids:
                    blocking.append(issue)
    return blocking
