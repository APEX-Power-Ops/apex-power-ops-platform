"""
Integration tests for the mutation pipeline.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


def _make_token(actor_id: str, actor_role: str) -> str:
    import base64
    import json

    payload = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"Bearer {encoded}"


def test_state_transition_validation_prevents_invalid_transition(
    client, field_tech_token, sample_apparatus_id
):
    """Test that invalid state transitions are rejected."""
    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "on_hold"},
            "reason": "Testing invalid transition",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "TRANSITION_INVALID"


def test_valid_state_transition_succeeds(
    client, field_tech_token, sample_apparatus_id
):
    """Test that a valid state transition is accepted."""
    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "ready"},
            "reason": "Preparing for testing",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["new_state"]["status"] == "ready"


def test_audit_log_records_mutation(
    client, field_tech_token, sample_apparatus_id
):
    """Test that mutations are recorded in the audit log."""
    from app.db.memory_store import store

    idempotency_key = str(uuid4())

    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": idempotency_key,
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "active"},
            "reason": "Test audit",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    audit_event_id = data["audit_event_id"]

    audit_entries = [e for e in store.audit_log if e["id"] == audit_event_id]
    assert len(audit_entries) == 1

    entry = audit_entries[0]
    assert entry["action_type"] == "update_status"
    assert entry["entity_id"] == sample_apparatus_id
    assert entry["actor_id"] == "tech-001"
    assert entry["actor_role"] == "field_tech"
    assert entry["reason"] == "Test audit"
    assert entry["to_state"]["status"] == "active"


def test_sequential_valid_transitions(client, field_tech_token, sample_apparatus_id):
    """Test a sequence of valid state transitions."""
    states = ["ready", "active", "on_hold", "active", "complete"]

    for state in states:
        response = client.post(
            "/api/v1/mutations/apparatus",
            json={
                "idempotency_key": str(uuid4()),
                "mutation_class": "B",
                "action_type": "update_status",
                "entity_id": sample_apparatus_id,
                "payload": {"status": state},
                "source": "online",
                "client_timestamp": "2026-04-16T14:30:00Z",
            },
            headers={"Authorization": field_tech_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted", f"Failed to transition to {state}"
        assert data["new_state"]["status"] == state


def test_checklist_completion(client, field_tech_token):
    """Test completing a checklist item."""
    checklist_item_id = "item-001"

    response = client.post(
        "/api/v1/mutations/checklist",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "A",
            "action_type": "complete_item",
            "entity_id": checklist_item_id,
            "payload": {"completed": True},
            "reason": "Task completed",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["new_state"]["completed"] is True


def test_multiple_mutations_independent(client, field_tech_token):
    """Test that multiple mutations on different entities are independent."""
    from app.db.memory_store import store

    app_ids = ["app-001", "app-002"]

    for app_id in app_ids:
        response = client.post(
            "/api/v1/mutations/apparatus",
            json={
                "idempotency_key": str(uuid4()),
                "mutation_class": "B",
                "action_type": "update_status",
                "entity_id": app_id,
                "payload": {"status": "active"},
                "source": "online",
                "client_timestamp": "2026-04-16T14:30:00Z",
            },
            headers={"Authorization": field_tech_token},
        )

        assert response.status_code == 200

    assert store.apparatus["app-001"]["status"] == "active"
    assert store.apparatus["app-002"]["status"] == "active"


def test_pm_return_to_lead_issue_disposition_is_audited_and_idempotent(client):
    """PM can send an escalated issue back to lead through the governed Class C issue path."""
    from app.db.memory_store import store

    issue = store.issues["issue-002"].copy()
    issue["status"] = "escalated"
    issue["blocks_completion"] = True
    store.issues["issue-002"] = issue

    idempotency_key = str(uuid4())
    payload = {
        "idempotency_key": idempotency_key,
        "mutation_class": "C",
        "action_type": "return_to_lead",
        "entity_id": "issue-002",
        "payload": {
            "status": "in_review",
            "pm_followup_note": "Please verify torque record and return disposition.",
            "pm_followup_sent_at": "2026-05-15T15:45:00Z",
            "pm_followup_workfront_row_id": "workfront-app-001",
        },
        "reason": "PM workfront lead follow-up",
        "source": "online",
        "client_timestamp": "2026-05-15T15:45:00Z",
    }

    first = client.post(
        "/api/v1/mutations/issues",
        json=payload,
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert first.status_code == 200
    first_data = first.json()
    assert first_data["status"] == "accepted"
    assert first_data["entity_type"] == "issue"
    assert first_data["action_type"] == "return_to_lead"
    assert first_data["new_state"]["status"] == "in_review"
    assert first_data["new_state"]["pm_followup_note"] == "Please verify torque record and return disposition."

    audit_entries = [entry for entry in store.audit_log if entry["id"] == first_data["audit_event_id"]]
    assert len(audit_entries) == 1
    assert audit_entries[0]["actor_role"] == "pm"
    assert audit_entries[0]["action_type"] == "return_to_lead"
    assert audit_entries[0]["from_state"]["status"] == "escalated"
    assert audit_entries[0]["to_state"]["status"] == "in_review"

    duplicate = client.post(
        "/api/v1/mutations/issues",
        json={
            **payload,
            "payload": {
                "status": "resolved",
                "pm_followup_note": "This should be ignored by idempotency.",
            },
        },
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert duplicate.status_code == 200
    duplicate_data = duplicate.json()
    assert duplicate_data["status"] == "idempotent_hit"
    assert duplicate_data["mutation_id"] == first_data["mutation_id"]
    assert duplicate_data["new_state"]["status"] == "in_review"
    assert duplicate_data["new_state"]["pm_followup_note"] == "Please verify torque record and return disposition."
    assert len([entry for entry in store.audit_log if entry["mutation_id"] == first_data["mutation_id"]]) == 1

    history = client.get(
        "/api/v1/reads/decision-history",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )
    assert history.status_code == 200
    history_rows = history.json()
    returned_history = next(
        entry for entry in history_rows
        if entry["action_type"] == "return_to_lead" and entry["entity_id"] == "issue-002"
    )
    assert returned_history["timestamp"] == audit_entries[0]["server_timestamp"]


@pytest.mark.parametrize(
    ("action_type", "source_status", "target_status"),
    [
        ("resolve_escalated", "escalated", "resolved"),
        ("re_escalate", "in_review", "escalated"),
    ],
)
def test_pm_issue_disposition_siblings_are_audited_and_idempotent(
    client,
    action_type,
    source_status,
    target_status,
):
    """Sibling PM issue dispositions require explicit status and audit exactly once."""
    from app.db.memory_store import store

    issue = store.issues["issue-002"].copy()
    issue["status"] = source_status
    issue["blocks_completion"] = True
    store.issues["issue-002"] = issue

    idempotency_key = str(uuid4())
    payload = {
        "idempotency_key": idempotency_key,
        "mutation_class": "C",
        "action_type": action_type,
        "entity_id": "issue-002",
        "payload": {
            "status": target_status,
            "pm_disposition": action_type,
        },
        "reason": f"PM issue disposition {action_type}",
        "source": "online",
        "client_timestamp": "2026-05-15T16:10:00Z",
    }

    first = client.post(
        "/api/v1/mutations/issues",
        json=payload,
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert first.status_code == 200
    first_data = first.json()
    assert first_data["status"] == "accepted"
    assert first_data["entity_type"] == "issue"
    assert first_data["action_type"] == action_type
    assert first_data["new_state"]["status"] == target_status
    assert first_data["new_state"]["pm_disposition"] == action_type

    audit_entries = [entry for entry in store.audit_log if entry["id"] == first_data["audit_event_id"]]
    assert len(audit_entries) == 1
    assert audit_entries[0]["actor_role"] == "pm"
    assert audit_entries[0]["action_type"] == action_type
    assert audit_entries[0]["from_state"]["status"] == source_status
    assert audit_entries[0]["to_state"]["status"] == target_status

    duplicate = client.post(
        "/api/v1/mutations/issues",
        json={
            **payload,
            "payload": {
                "status": "in_review" if target_status == "resolved" else "resolved",
                "pm_disposition": "ignored_by_idempotency",
            },
        },
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert duplicate.status_code == 200
    duplicate_data = duplicate.json()
    assert duplicate_data["status"] == "idempotent_hit"
    assert duplicate_data["mutation_id"] == first_data["mutation_id"]
    assert duplicate_data["new_state"]["status"] == target_status
    assert duplicate_data["new_state"]["pm_disposition"] == action_type
    assert len([entry for entry in store.audit_log if entry["mutation_id"] == first_data["mutation_id"]]) == 1


def test_decision_history_normalizes_timestamp_shapes(client):
    """Decision-history reads sort memory and persisted audit timestamp shapes consistently."""
    from app.db.memory_store import store

    store.audit_log.append(
        {
            "id": "audit-old-client",
            "mutation_id": "mut-old-client",
            "actor_id": "pm-001",
            "actor_role": "pm",
            "action_type": "approve",
            "entity_id": "task-001",
            "from_state": {"status": "awaiting_review"},
            "to_state": {"status": "complete"},
            "client_timestamp": "2026-05-15T09:00:00Z",
        }
    )
    store.audit_log.append(
        {
            "id": "audit-new-server",
            "mutation_id": "mut-new-server",
            "actor_id": "pm-001",
            "actor_role": "pm",
            "action_type": "return_to_lead",
            "entity_id": "issue-002",
            "from_state": {"status": "escalated"},
            "to_state": {"status": "in_review"},
            "server_timestamp": "2026-05-15T10:00:00Z",
        }
    )

    history = client.get(
        "/api/v1/reads/decision-history",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert history.status_code == 200
    rows = history.json()
    assert [row["id"] for row in rows[:2]] == ["audit-new-server", "audit-old-client"]
    assert rows[0]["timestamp"] == "2026-05-15T10:00:00Z"
    assert rows[1]["timestamp"] == "2026-05-15T09:00:00Z"

    filtered = client.get(
        "/api/v1/reads/decision-history?entity_id=issue-002",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )
    assert filtered.status_code == 200
    assert [row["id"] for row in filtered.json()] == ["audit-new-server"]

    repeated = client.get(
        "/api/v1/reads/decision-history?entity_id=issue-002&entity_id=task-001",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )
    assert repeated.status_code == 200
    assert [row["id"] for row in repeated.json()] == ["audit-new-server", "audit-old-client"]

    newest_only = client.get(
        "/api/v1/reads/decision-history?entity_id=issue-002&entity_id=task-001&limit=1",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )
    assert newest_only.status_code == 200
    assert [row["id"] for row in newest_only.json()] == ["audit-new-server"]

    invalid_limit = client.get(
        "/api/v1/reads/decision-history?limit=0",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )
    assert invalid_limit.status_code == 422


def test_decision_history_limit_is_capped(client):
    """Decision-history query narrowing keeps PM timeline reads bounded."""
    from app.db.memory_store import store

    base = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    for index in range(120):
        store.audit_log.append(
            {
                "id": f"audit-bulk-{index:03d}",
                "mutation_id": f"mut-bulk-{index:03d}",
                "actor_id": "pm-001",
                "actor_role": "pm",
                "action_type": "return_to_lead",
                "entity_id": "issue-002",
                "from_state": {"status": "escalated"},
                "to_state": {"status": "in_review"},
                "server_timestamp": (base + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
            }
        )

    limited = client.get(
        "/api/v1/reads/decision-history?entity_id=issue-002&limit=250",
        headers={"Authorization": _make_token("pm-001", "pm")},
    )

    assert limited.status_code == 200
    rows = limited.json()
    assert len(rows) == 100
    assert rows[0]["id"] == "audit-bulk-119"
    assert rows[-1]["id"] == "audit-bulk-020"


def test_field_tech_cannot_return_issue_to_lead(client, field_tech_token):
    """The workfront issue disposition remains PM-only for this Class C action."""
    response = client.post(
        "/api/v1/mutations/issues",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "C",
            "action_type": "return_to_lead",
            "entity_id": "issue-002",
            "payload": {"status": "in_review"},
            "reason": "Unauthorized attempt",
            "source": "online",
            "client_timestamp": "2026-05-15T15:50:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "UNAUTHORIZED_ROLE"
