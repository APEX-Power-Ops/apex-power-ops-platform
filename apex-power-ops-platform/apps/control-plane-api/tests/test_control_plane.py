"""Tests for the remote control-plane API scaffold."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from unittest.mock import MagicMock
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from config import get_db
from services.auth import AuthenticatedUser
from services.control_plane.router import get_current_user


TEST_USER_ID = "11111111-1111-1111-1111-111111111111"
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REMOTE_TOOL_SCHEMA_PATH = (
    BACKEND_ROOT / "docs" / "contracts" / "CHATGPT-REMOTE-CONTROL-PLANE-TOOL-SCHEMAS-2026-03-28.json"
)


def _dt(hours: int = 0) -> datetime:
    return datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc) + timedelta(hours=hours)


def _load_remote_tool_schema(tool_name: str) -> dict:
    payload = json.loads(REMOTE_TOOL_SCHEMA_PATH.read_text(encoding="utf-8"))
    for tool in payload.get("tools") or []:
        if tool.get("name") == tool_name:
            return tool
    raise AssertionError(f"Tool schema not found: {tool_name}")


class _FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class _FakeControlPlaneDb:
    def __init__(self):
        self.execute_calls = []
        self.commit_called = False
        self.updated_status_params = None
        self.audit_params = None
        self.queued_local_action_params = None
        self.packet_status_update_params = None
        self.task_packet_status_response_updated_at = _dt(6)
        self.task_packet_row = {
            "task_id": "2026-03-29-chatgpt-remote-control-plane-backend-001",
            "title": "Implement first remote control-plane backend slice",
            "lane": "workspace-governance",
            "primary_repo": "apex-power-ops-platform",
            "status": "completed",
            "action_type": "edit",
            "risk_level": "high",
            "preferred_model_tier": "tier-a",
            "review_gate": "tier-a review before completion acceptance",
            "briefing_path": "Development/Control-Plane/CHATGPT-REMOTE-CONTROL-PLANE-BACKEND-IMPLEMENTATION-HANDOFF-2026-03-29.md",
            "packet_json": {
                "task_id": "2026-03-29-chatgpt-remote-control-plane-backend-001",
                "status": "completed",
            },
            "claimed_by": "GitHub Copilot",
            "created_at": _dt(-4),
            "updated_at": _dt(4),
            "last_reviewed_at": _dt(3),
        }

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.execute_calls.append((sql, params))
        result = MagicMock()

        if "FROM public.mcp_task_packets" in sql and "WHERE task_id = :task_id" in sql:
            result.fetchone.return_value = _FakeRow(self.task_packet_row)
            return result

        if "UPDATE public.mcp_task_packets" in sql and "SET status = 'awaiting_results'" in sql:
            self.packet_status_update_params = params
            result.scalar_one.return_value = _dt(6)
            return result

        if "UPDATE public.mcp_task_packets" in sql and "SET status = :new_status," in sql:
            self.updated_status_params = params
            self.task_packet_row["status"] = params["new_status"]
            packet_json = dict(self.task_packet_row.get("packet_json") or {})
            packet_json["status"] = params["new_status"]
            self.task_packet_row["packet_json"] = packet_json
            result.scalar_one.return_value = self.task_packet_status_response_updated_at
            return result

        if "INSERT INTO public.mcp_local_action_queue" in sql:
            self.queued_local_action_params = params
            result.fetchone.return_value = _FakeRow(
                {
                    "job_id": params["job_id"],
                    "action_type": params["action_type"],
                    "status": "queued",
                    "priority": params["priority"],
                    "task_id": params["task_id"],
                    "subject_type": params["subject_type"],
                    "subject_id": params["subject_id"],
                    "requested_by": params["requested_by"],
                    "created_at": _dt(6),
                }
            )
            return result

        if "FROM public.mcp_review_decisions" in sql and "WHERE subject_type = 'task_packet'" in sql:
            result.fetchall.return_value = [
                _FakeRow(
                    {
                        "id": "c4c0200b-79c7-4bfb-9789-24b57927224d",
                        "subject_type": "task_packet",
                        "subject_id": "2026-03-29-chatgpt-remote-control-plane-backend-001",
                        "decision": "completion_acceptance",
                        "reasoning_summary": "Accepted after live control-plane proof.",
                        "required_next_action": "Use the live path for the next packet.",
                        "actor_id": TEST_USER_ID,
                        "source_tool": "create_review_decision",
                        "evidence_links": ["Development/Control-Plane/EXECUTION-TASKS-CURRENT.md"],
                        "created_at": _dt(5),
                    }
                )
            ]
            return result

        if "to_regclass('public.image_assets') AS image_assets" in sql:
            result.fetchone.return_value = _FakeRow(
                {
                    "image_assets": "image_assets",
                    "image_guide_links": "image_guide_links",
                    "mcp_validation_artifacts": "mcp_validation_artifacts",
                }
            )
            return result

        if "FROM public.image_assets ia" in sql and "WHERE ia.id = :asset_id" not in sql:
            result.fetchall.return_value = [
                _FakeRow(
                    {
                        "id": "mcc-lineup-anatomy-overview",
                        "caption": "MCC lineup anatomy overview",
                        "status": "review",
                        "sourcing_method": "custom_diagram",
                        "production_tool": "svg_manual",
                        "guide_slugs": ["motor-control-centers-low-voltage"],
                        "git_path": "Visual-Assets/Guide-Images/motor-control-centers-low-voltage/mcc-lineup-anatomy-overview.svg",
                        "storage_bucket": "study-images",
                        "storage_path": "motor-control-centers-low-voltage/mcc-lineup-anatomy-overview.svg",
                        "storage_url": "https://example.com/mcc-lineup-anatomy-overview.svg",
                        "updated_at": _dt(1),
                        "latest_validation_artifact_id": "artifact-image-1",
                    }
                )
            ]
            return result

        if "FROM public.image_assets ia" in sql and "WHERE ia.id = :asset_id" in sql:
            result.fetchone.return_value = _FakeRow(
                {
                    "id": "mcc-lineup-anatomy-overview",
                    "caption": "MCC lineup anatomy overview",
                    "source_doc": "NETA MTS 2023",
                    "source_ref": "Section 7.1",
                    "alt_text": "Overview of an MCC lineup",
                    "notes": "Guide-specific redraw.",
                    "sourcing_method": "custom_diagram",
                    "sourcing_hint": "custom_diagram",
                    "production_tool": "svg_manual",
                    "status": "review",
                    "git_path": "Visual-Assets/Guide-Images/motor-control-centers-low-voltage/mcc-lineup-anatomy-overview.svg",
                    "storage_bucket": "study-images",
                    "storage_path": "motor-control-centers-low-voltage/mcc-lineup-anatomy-overview.svg",
                    "storage_url": "https://example.com/mcc-lineup-anatomy-overview.svg",
                    "file_format": "svg",
                    "file_size_bytes": 2048,
                    "width_px": 1400,
                    "height_px": 900,
                    "figma_file_key": None,
                    "figma_node_id": None,
                    "script_path": None,
                    "quality_tier": "complete",
                    "created_at": _dt(-2),
                    "updated_at": _dt(1),
                    "classified_at": _dt(-1),
                    "produced_at": _dt(0),
                    "integrated_at": None,
                    "guide_slugs": ["motor-control-centers-low-voltage"],
                    "latest_validation_artifact_id": "artifact-image-1",
                    "latest_validation_artifact_summary": "Asset-level validation is current.",
                }
            )
            return result

        if "FROM public.image_guide_links" in sql and "WHERE image_asset_id = :asset_id" in sql:
            result.fetchall.return_value = [
                _FakeRow(
                    {
                        "guide_slug": "motor-control-centers-low-voltage",
                        "guide_file": "SG-CT-MOTOR-CONTROL-CENTERS.md",
                        "content_id": "SG-CT-MOTOR-CONTROL-CENTERS",
                        "line_number": 42,
                        "section_context": "Lineup overview",
                        "created_at": _dt(-1),
                    }
                )
            ]
            return result

        if "SELECT id, status FROM public.image_assets" in sql:
            result.fetchone.return_value = _FakeRow(
                {
                    "id": "mcc-lineup-anatomy-overview",
                    "status": "review",
                }
            )
            return result

        if "UPDATE public.image_assets SET status = :new_status" in sql:
            self.updated_status_params = params
            result.scalar_one.return_value = _dt(2)
            return result

        if "INSERT INTO public.mcp_review_decisions" in sql:
            self.audit_params = params
            result.fetchone.return_value = None
            return result

        if "FROM public.mcp_validation_artifacts" in sql and "WHERE subject_type = :subject_type AND subject_id = :subject_id" in sql:
            result.fetchone.return_value = _FakeRow(
                {
                    "artifact_id": "artifact-guide-1",
                    "artifact_type": "render_validation_report",
                    "subject_type": "guide",
                    "subject_id": "motor-control-centers-low-voltage",
                    "title": "MCC render validation",
                    "summary": "All linked assets are integrated.",
                    "artifact_path": "Development/Validation-Runs/image-assets/mcc.json",
                    "artifact_uri": None,
                    "artifact_json": {"readiness": "render_ready"},
                    "created_by": "worker-a",
                    "created_at": _dt(3),
                }
            )
            return result

        if "FROM public.mcp_validation_artifacts" in sql and "WHERE artifact_id = :artifact_id" in sql:
            result.fetchone.return_value = _FakeRow(
                {
                    "artifact_id": "artifact-guide-1",
                    "artifact_type": "render_validation_report",
                    "subject_type": "guide",
                    "subject_id": "motor-control-centers-low-voltage",
                    "title": "MCC render validation",
                    "summary": "All linked assets are integrated.",
                    "artifact_path": "Development/Validation-Runs/image-assets/mcc.json",
                    "artifact_uri": None,
                    "artifact_json": {"readiness": "render_ready"},
                    "created_by": "worker-a",
                    "created_at": _dt(3),
                }
            )
            return result

        raise AssertionError(f"Unexpected SQL in control-plane test fake DB: {sql}")

    def commit(self):
        self.commit_called = True


def _make_authenticated_user():
    return AuthenticatedUser(
        user_id=UUID(TEST_USER_ID),
        email="control-plane@example.com",
        role="authenticated",
        claims={"sub": TEST_USER_ID, "email": "control-plane@example.com", "role": "authenticated"},
    )


@pytest.fixture
def client():
    fake_db = _FakeControlPlaneDb()
    app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        test_client = TestClient(app)
        test_client.fake_db = fake_db
        yield test_client
    finally:
        app.dependency_overrides.clear()


def test_control_plane_requires_authentication():
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = lambda: None
    try:
        client = TestClient(app)
        response = client.get("/api/v1/control-plane/task-packets")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_plan_preview_recommends_tier_a_for_governance_work(client):
    response = client.post(
        "/api/v1/control-plane/plan-preview",
        json={
            "task": "Review governance packet and approve queue transition for schema migration.",
            "lane": "workspace-governance",
            "action_type": "route",
            "risk_level": "high",
            "requires_local_action": True,
            "requires_review_decision": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_model_tier"] == "tier-a"
    assert body["workflow"] == "review_and_queue"
    assert body["needs_local_action_queue"] is True
    assert len(body["steps"]) == 4
    assert any(step["title"] == "Queue bounded local action" for step in body["steps"])


def test_cost_estimate_scales_for_tier_a_review_work(client):
    response = client.post(
        "/api/v1/control-plane/cost-estimate",
        json={
            "task": "Assess a high-risk packet, record a review decision, and validate closeout evidence.",
            "preferred_model_tier": "tier-a",
            "requires_review_decision": True,
            "requires_local_action": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preferred_model_tier"] == "tier-a"
    assert body["estimated_experts"] >= 3
    assert body["total_tokens"] > body["estimated_input_tokens"]
    assert body["estimated_cost_usd"] > 0
    assert body["estimated_duration_seconds"] > 0


def test_fetch_task_packet_returns_detail_with_packet_json_and_reviews(client):
    response = client.get(
        "/api/v1/control-plane/task-packets/2026-03-29-chatgpt-remote-control-plane-backend-001"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "2026-03-29-chatgpt-remote-control-plane-backend-001"
    assert body["packet_json"]["status"] == "completed"
    assert len(body["review_decisions"]) == 1
    assert body["review_decisions"][0]["decision"] == "completion_acceptance"


def test_update_task_packet_status_allows_final_closeout(client):
    client.fake_db.task_packet_row = {
        **client.fake_db.task_packet_row,
        "task_id": "2026-04-04-chatgpt-browser-authoring-proof-001",
        "status": "ready_for_closeout",
        "packet_json": {
            "task_id": "2026-04-04-chatgpt-browser-authoring-proof-001",
            "status": "ready_for_closeout",
        },
    }

    response = client.post(
        "/api/v1/control-plane/task-packets/2026-04-04-chatgpt-browser-authoring-proof-001/status",
        json={
            "new_status": "completed",
            "reasoning_summary": "Authoring evidence validated and accepted for final closeout.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["previous_status"] == "ready_for_closeout"
    assert body["new_status"] == "completed"
    assert client.fake_db.updated_status_params == {
        "task_id": "2026-04-04-chatgpt-browser-authoring-proof-001",
        "new_status": "completed",
    }
    assert client.fake_db.task_packet_row["status"] == "completed"
    assert client.fake_db.task_packet_row["packet_json"]["status"] == "completed"
    assert client.fake_db.audit_params["new_status"] == "completed"
    assert client.fake_db.commit_called is True


def test_update_task_packet_status_rejects_skipped_transition(client):
    client.fake_db.task_packet_row = {
        **client.fake_db.task_packet_row,
        "task_id": "2026-04-04-chatgpt-browser-authoring-proof-001",
        "status": "awaiting_results",
        "packet_json": {
            "task_id": "2026-04-04-chatgpt-browser-authoring-proof-001",
            "status": "awaiting_results",
        },
    }

    response = client.post(
        "/api/v1/control-plane/task-packets/2026-04-04-chatgpt-browser-authoring-proof-001/status",
        json={
            "new_status": "completed",
            "reasoning_summary": "Attempted to bypass closeout review.",
        },
    )

    assert response.status_code == 400
    assert "Disallowed packet status transition" in response.json()["detail"]
    assert client.fake_db.updated_status_params is None
    assert client.fake_db.commit_called is False


def test_queue_local_action_requires_explicit_confirmation(client):
    response = client.post(
        "/api/v1/control-plane/local-actions",
        json={
            "action_type": "run_render_validation",
            "subject_type": "guide",
            "subject_id": "motor-control-centers-low-voltage",
            "request_payload": {"guide_slug": "motor-control-centers-low-voltage"},
            "priority": "normal",
            "confirmed_by_user": False,
        },
    )

    assert response.status_code == 400
    assert "Explicit user confirmation is required" in response.json()["detail"]


def test_queue_local_action_authoring_rejects_unapproved_packet_status(client):
    client.fake_db.task_packet_row = {
        **client.fake_db.task_packet_row,
        "task_id": "2026-03-29-authoring-001",
        "status": "prepared",
        "action_type": "edit",
        "packet_json": {
            "task_id": "2026-03-29-authoring-001",
            "status": "prepared",
            "authoring": {
                "enabled": True,
                "mode": "staging_only",
                "allowed_target_files": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
            },
            "route": {
                "allow_auto_apply": True,
            },
        },
    }

    response = client.post(
        "/api/v1/control-plane/local-actions",
        json={
            "action_type": "write_staging_authoring_candidate",
            "task_id": "2026-03-29-authoring-001",
            "subject_type": "authoring_target",
            "subject_id": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
            "request_payload": {
                "path": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
                "content": "# Example\n",
                "overwrite": True,
            },
            "priority": "normal",
            "confirmed_by_user": True,
        },
    )

    assert response.status_code == 400
    assert "packet status does not allow authoring queue submission" in response.json()["detail"]
    assert client.fake_db.queued_local_action_params is None


def test_queue_local_action_authoring_advances_packet_to_awaiting_results(client):
    client.fake_db.task_packet_row = {
        **client.fake_db.task_packet_row,
        "task_id": "2026-03-29-authoring-002",
        "status": "approved_for_local_action",
        "action_type": "edit",
        "packet_json": {
            "task_id": "2026-03-29-authoring-002",
            "status": "approved_for_local_action",
            "authoring": {
                "enabled": True,
                "mode": "staging_only",
                "allowed_target_files": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
            },
            "route": {
                "allow_auto_apply": True,
            },
        },
    }

    response = client.post(
        "/api/v1/control-plane/local-actions",
        json={
            "action_type": "write_staging_authoring_candidate",
            "task_id": "2026-03-29-authoring-002",
            "subject_type": "authoring_target",
            "subject_id": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
            "request_payload": {
                "path": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
                "content": "# Example\n",
                "overwrite": True,
            },
            "priority": "normal",
            "confirmed_by_user": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["action_type"] == "write_staging_authoring_candidate"
    assert body["task_id"] == "2026-03-29-authoring-002"
    assert client.fake_db.queued_local_action_params is not None
    assert client.fake_db.packet_status_update_params == {"task_id": "2026-03-29-authoring-002"}
    assert client.fake_db.audit_params["task_id"] == "2026-03-29-authoring-002"
    assert "awaiting local action results" in client.fake_db.audit_params["reasoning_summary"]
    assert client.fake_db.commit_called is True


def test_remote_tool_schema_drives_authoring_queue_smoke_request(client):
    queue_tool = _load_remote_tool_schema("queue_local_action")
    input_schema = queue_tool["inputSchema"]
    authoring_policy = queue_tool["actionPolicies"]["write_staging_authoring_candidate"]
    target_path = "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"
    task_id = "2026-03-29-authoring-remote-contract-001"

    client.fake_db.task_packet_row = {
        **client.fake_db.task_packet_row,
        "task_id": task_id,
        "status": authoring_policy["requiredTaskPacketStatuses"][0],
        "action_type": "edit",
        "packet_json": {
            "task_id": task_id,
            "status": authoring_policy["requiredTaskPacketStatuses"][0],
            "authoring": {
                "enabled": True,
                "mode": "staging_only",
                "allowed_target_files": [target_path],
            },
            "route": {
                "allow_auto_apply": True,
            },
        },
    }

    request_payload = {
        "path": target_path,
        "content": "# Example\n",
        "overwrite": True,
    }
    queue_request = {
        "action_type": "write_staging_authoring_candidate",
        "task_id": task_id,
        "subject_type": authoring_policy["requiredSubjectType"],
        "subject_id": request_payload["path"],
        "request_payload": request_payload,
        "priority": input_schema["properties"]["priority"]["enum"][1],
        "confirmed_by_user": input_schema["properties"]["confirmed_by_user"]["const"],
    }

    response = client.post("/api/v1/control-plane/local-actions", json=queue_request)

    assert response.status_code == 201
    body = response.json()
    assert body["action_type"] == queue_request["action_type"]
    assert body["subject_type"] == authoring_policy["requiredSubjectType"]
    assert client.fake_db.queued_local_action_params["priority"] == queue_request["priority"]
    assert client.fake_db.queued_local_action_params["subject_id"] == request_payload["path"]
    assert client.fake_db.packet_status_update_params == {"task_id": task_id}


def test_list_image_assets_returns_filtered_asset_summaries(client):
    response = client.get(
        "/api/v1/control-plane/image-assets",
        params={"guide_slug": "motor-control-centers-low-voltage", "status": "review"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "mcc-lineup-anatomy-overview"
    assert body[0]["guide_slugs"] == ["motor-control-centers-low-voltage"]
    assert body[0]["latest_validation_artifact_id"] == "artifact-image-1"


def test_fetch_image_asset_returns_detail_with_links(client):
    response = client.get("/api/v1/control-plane/image-assets/mcc-lineup-anatomy-overview")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "mcc-lineup-anatomy-overview"
    assert body["status"] == "review"
    assert body["guide_links"][0]["content_id"] == "SG-CT-MOTOR-CONTROL-CENTERS"
    assert body["latest_validation_artifact_summary"] == "Asset-level validation is current."


def test_update_image_asset_status_writes_audit_record(client):
    response = client.post(
        "/api/v1/control-plane/image-assets/mcc-lineup-anatomy-overview/status",
        json={
            "new_status": "integrated",
            "decision_basis": "Storage upload and review evidence are complete.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["previous_status"] == "review"
    assert body["new_status"] == "integrated"
    assert client.fake_db.updated_status_params == {
        "asset_id": "mcc-lineup-anatomy-overview",
        "new_status": "integrated",
    }
    assert client.fake_db.audit_params["asset_id"] == "mcc-lineup-anatomy-overview"
    assert "review -> integrated" in client.fake_db.audit_params["reasoning_summary"]
    assert client.fake_db.commit_called is True


def test_lookup_validation_artifact_allows_subject_lookup(client):
    response = client.get(
        "/api/v1/control-plane/validation-artifacts",
        params={
            "subject_type": "guide",
            "subject_id": "motor-control-centers-low-voltage",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["artifact_id"] == "artifact-guide-1"
    assert body["artifact_json"]["readiness"] == "render_ready"


def test_lookup_validation_artifact_requires_identifier(client):
    response = client.get("/api/v1/control-plane/validation-artifacts")

    assert response.status_code == 400
    assert "Provide artifact_id or both subject_type and subject_id" in response.json()["detail"]