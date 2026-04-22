"""
Tests for mutation envelope validation and basic pipeline flow.
"""
from uuid import uuid4

import pytest


def test_valid_apparatus_status_update_succeeds(
    client, field_tech_token, sample_apparatus_id
):
    """Test that a valid apparatus status update request succeeds."""
    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "active"},
            "reason": "Starting testing",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["entity_id"] == sample_apparatus_id
    assert data["entity_type"] == "apparatus"
    assert data["new_state"]["status"] == "active"
    assert data["mutation_id"].startswith("mut-")
    assert data["audit_event_id"] is not None


def test_missing_idempotency_key_fails(client, field_tech_token, sample_apparatus_id):
    """Test that a request without idempotency_key fails validation."""
    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "active"},
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response.status_code == 422


def test_offline_class_c_is_rejected(client):
    """Test that Class C mutations from offline queue are rejected."""
    import base64
    import json as json_mod

    payload = {
        "actor_id": "lead-001",
        "actor_role": "lead",
        "project_scope": ["proj-001"],
    }
    token = f"Bearer {base64.b64encode(json_mod.dumps(payload).encode()).decode()}"

    response = client.post(
        "/api/v1/mutations/issues",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "C",
            "action_type": "escalate_to_pm",
            "entity_id": "issue-001",
            "payload": {},
            "source": "offline_queue",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "OFFLINE_CLASS_C_REJECTED"


def test_idempotent_duplicate_returns_original(
    client, field_tech_token, sample_apparatus_id
):
    """Test that a duplicate idempotency key returns the original response."""
    idempotency_key = str(uuid4())

    response1 = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": idempotency_key,
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "active"},
            "reason": "First attempt",
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response1.status_code == 200
    data1 = response1.json()
    first_mutation_id = data1["mutation_id"]

    response2 = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": idempotency_key,
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "on_hold"},
            "reason": "Second attempt",
            "source": "online",
            "client_timestamp": "2026-04-16T14:31:00Z",
        },
        headers={"Authorization": field_tech_token},
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["status"] == "idempotent_hit"
    assert data2["mutation_id"] == first_mutation_id
    assert data2["new_state"]["status"] == "active"


def test_unauthorized_role_rejected(client, sample_apparatus_id):
    """Test that an unauthorized role is rejected."""
    import base64
    import json

    payload = {
        "actor_id": "user-001",
        "actor_role": "viewer",
        "project_scope": ["proj-001"],
    }
    token = f"Bearer {base64.b64encode(json.dumps(payload).encode()).decode()}"

    response = client.post(
        "/api/v1/mutations/apparatus",
        json={
            "idempotency_key": str(uuid4()),
            "mutation_class": "B",
            "action_type": "update_status",
            "entity_id": sample_apparatus_id,
            "payload": {"status": "active"},
            "source": "online",
            "client_timestamp": "2026-04-16T14:30:00Z",
        },
        headers={"Authorization": token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "UNAUTHORIZED_ROLE"


def test_health_check_endpoint(client):
    """Test that the health check endpoint responds."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["seam"] == "mutation-seam"


def test_root_endpoint(client):
    """Test that the root endpoint returns service info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "apex-mutation-seam"
    assert data["version"] == "0.1.0"
