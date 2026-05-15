import base64
import json
from uuid import uuid4

import pytest

from app.db.memory_store import store


def _token(actor_role: str = "pm", project_scope: list[str] | None = None) -> dict[str, str]:
    payload = {
        "actor_id": f"{actor_role}-001",
        "actor_role": actor_role,
        "project_scope": project_scope if project_scope is not None else ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _issue_disposition_payload(action_type: str, status: str, **overrides):
    payload = {
        "idempotency_key": str(uuid4()),
        "mutation_class": "C",
        "action_type": action_type,
        "entity_id": "issue-002",
        "payload": {
            "status": status,
            "pm_disposition": action_type,
        },
        "reason": f"PM disposition {action_type} for issue-002",
        "source": "online",
        "client_timestamp": "2026-05-15T16:00:00Z",
    }
    payload.update(overrides)
    return payload


def _return_to_lead_payload(**overrides):
    return _issue_disposition_payload("return_to_lead", "in_review", **overrides)


def _resolve_escalated_payload(**overrides):
    return _issue_disposition_payload("resolve_escalated", "resolved", **overrides)


def _re_escalate_payload(**overrides):
    return _issue_disposition_payload("re_escalate", "escalated", **overrides)


def _mark_issue_status(status: str):
    issue = store.issues["issue-002"].copy()
    issue["status"] = status
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
    _mark_issue_status("escalated")

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
    _mark_issue_status("escalated")

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
    _mark_issue_status("escalated")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_return_to_lead_payload(reason=""),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"


@pytest.mark.parametrize(
    ("payload_factory", "source_status"),
    [
        (_resolve_escalated_payload, "escalated"),
        (_re_escalate_payload, "in_review"),
    ],
)
def test_pm_issue_dispositions_require_project_scope(client, payload_factory, source_status):
    _mark_issue_status(source_status)

    response = client.post(
        "/api/v1/mutations/issues",
        json=payload_factory(),
        headers=_token(project_scope=["other-project"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "UNAUTHORIZED_SCOPE"


def test_resolve_escalated_requires_escalated_issue(client):
    response = client.post(
        "/api/v1/mutations/issues",
        json=_resolve_escalated_payload(),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"


def test_resolve_escalated_requires_resolved_status(client):
    _mark_issue_status("escalated")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_resolve_escalated_payload(payload={"status": "in_review"}),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"


def test_resolve_escalated_requires_pm_reason(client):
    _mark_issue_status("escalated")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_resolve_escalated_payload(reason=""),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"


def test_re_escalate_requires_in_review_issue(client):
    _mark_issue_status("escalated")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_re_escalate_payload(),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "PRECONDITION_FAILED"


def test_re_escalate_requires_escalated_status(client):
    _mark_issue_status("in_review")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_re_escalate_payload(payload={"status": "resolved"}),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"


def test_re_escalate_requires_pm_reason(client):
    _mark_issue_status("in_review")

    response = client.post(
        "/api/v1/mutations/issues",
        json=_re_escalate_payload(reason=""),
        headers=_token(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["error"]["code"] == "INVALID_PAYLOAD"
