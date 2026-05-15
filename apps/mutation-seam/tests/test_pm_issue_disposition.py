import base64
import json
from uuid import uuid4

from app.db.memory_store import store


def _token(actor_role: str = "pm", project_scope: list[str] | None = None) -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": project_scope if project_scope is not None else ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _return_to_lead_payload(**overrides):
    payload = {
        "idempotency_key": str(uuid4()),
        "mutation_class": "C",
        "action_type": "return_to_lead",
        "entity_id": "issue-002",
        "payload": {
            "status": "in_review",
            "pm_disposition": "return_to_lead",
        },
        "reason": "PM returned issue issue-002 to lead review",
        "source": "online",
        "client_timestamp": "2026-05-15T16:00:00Z",
    }
    payload.update(overrides)
    return payload


def _mark_issue_escalated():
    issue = store.issues["issue-002"].copy()
    issue["status"] = "escalated"
    issue["blocks_completion"] = True
    store.issues["issue-002"] = issue


def test_return_to_lead_requires_escalated_issue(client):
    response = client.post(
        "/api/v1/mutations/issues",
        json=_return_to_lead_payload(),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"


def test_return_to_lead_requires_project_scope(client):
    _mark_issue_escalated()

    response = client.post(
        "/api/v1/mutations/issues",
        json=_return_to_lead_payload(),
        headers=_token(project_scope=["other-project"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "UNAUTHORIZED_SCOPE"


def test_return_to_lead_requires_in_review_status(client):
    _mark_issue_escalated()

    response = client.post(
        "/api/v1/mutations/issues",
        json=_return_to_lead_payload(payload={"status": "resolved"}),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"


def test_return_to_lead_requires_pm_reason(client):
    _mark_issue_escalated()

    response = client.post(
        "/api/v1/mutations/issues",
        json=_return_to_lead_payload(reason=""),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"
