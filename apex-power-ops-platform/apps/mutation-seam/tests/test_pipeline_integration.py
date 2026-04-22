"""
Integration tests for the mutation pipeline.
"""
from uuid import uuid4

import pytest


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
