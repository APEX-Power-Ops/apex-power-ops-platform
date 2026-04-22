"""
State machine definitions for lifecycle transitions.
"""
from typing import Dict, List

# Apparatus status transitions
APPARATUS_TRANSITIONS: Dict[str, List[str]] = {
    "not_started": ["ready", "active"],
    "ready": ["active", "not_started"],
    "active": ["on_hold", "complete"],
    "on_hold": ["active", "ready"],
    "complete": [],
}

# Task status transitions (aligned with UI-004 lead actions)
TASK_TRANSITIONS: Dict[str, List[str]] = {
    "not_started": ["ready", "active", "cancelled"],
    "ready": ["active", "on_hold", "cancelled"],
    "active": ["on_hold", "awaiting_review", "cancelled"],
    "on_hold": ["ready", "active"],
    "awaiting_review": ["active", "complete", "rejected"],
    "complete": [],
    "cancelled": [],
    "rejected": ["active"],
}

# WorkPackage status transitions (aligned with UI-004 lead submit-for-review)
WORKPACKAGE_TRANSITIONS: Dict[str, List[str]] = {
    "not_started": ["active"],
    "active": ["awaiting_review", "on_hold"],
    "on_hold": ["active"],
    "awaiting_review": ["active", "complete", "rejected"],
    "complete": [],
    "rejected": ["active"],
}

# Issue status transitions (aligned with UI-004 lead triage)
ISSUE_TRANSITIONS: Dict[str, List[str]] = {
    "open": ["in_review", "escalated"],
    "in_review": ["escalated", "resolved"],
    "escalated": ["resolved", "in_review"],
    "resolved": ["closed", "open"],
    "closed": [],
}

# ProgressSnapshot status transitions (aligned with UI-003 PM approval queue)
SNAPSHOT_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["submitted"],
    "submitted": ["approved", "rejected"],
    "approved": [],
    "rejected": ["draft"],
}

# Mapping of entity type to transitions
TRANSITION_RULES = {
    "apparatus": APPARATUS_TRANSITIONS,
    "task": TASK_TRANSITIONS,
    "workpackage": WORKPACKAGE_TRANSITIONS,
    "issue": ISSUE_TRANSITIONS,
    "snapshot": SNAPSHOT_TRANSITIONS,
}


def validate_transition(
    entity_type: str,
    from_state: str,
    to_state: str,
) -> bool:
    """
    Validate that a state transition is allowed.
    """
    if entity_type not in TRANSITION_RULES:
        return True

    transitions = TRANSITION_RULES[entity_type]

    if from_state not in transitions:
        return False

    allowed = transitions[from_state]
    return to_state in allowed
