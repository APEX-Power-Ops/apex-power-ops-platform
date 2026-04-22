"""Tests for shared control-plane queue helpers."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.control_plane.queue import enqueue_local_action, enqueue_render_validation


class _FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class _FakeSession:
    def __init__(self, response_mapping):
        self.response_mapping = response_mapping
        self.params = None

    def execute(self, _statement, params):
        self.params = params
        return SimpleNamespace(fetchone=lambda: _FakeRow(self.response_mapping))


def test_enqueue_local_action_rejects_unsupported_priority():
    session = _FakeSession({})

    with pytest.raises(ValueError, match="Unsupported queue priority"):
        enqueue_local_action(
            session,
            action_type="run_render_validation",
            priority="rush",
            task_id=None,
            subject_type="guide",
            subject_id="guide-a",
            requested_by="actor-1",
            request_payload={"guide_slug": "guide-a"},
        )


def test_enqueue_local_action_serializes_payload_and_returns_row():
    now = datetime.now(timezone.utc)
    session = _FakeSession(
        {
            "job_id": "job-1",
            "action_type": "collect_validation_evidence",
            "status": "queued",
            "priority": "high",
            "task_id": "task-1",
            "subject_type": "guide",
            "subject_id": "guide-a",
            "requested_by": "actor-1",
            "created_at": now,
        }
    )

    queued = enqueue_local_action(
        session,
        action_type="collect_validation_evidence",
        priority="high",
        task_id="task-1",
        subject_type="guide",
        subject_id="guide-a",
        requested_by="actor-1",
        request_payload={"artifact_type": "screenshot"},
    )

    assert queued["job_id"] == "job-1"
    assert session.params["requested_by"] == "actor-1"
    assert json.loads(session.params["request_payload"]) == {"artifact_type": "screenshot"}


def test_enqueue_render_validation_builds_expected_payload():
    now = datetime.now(timezone.utc)
    session = _FakeSession(
        {
            "job_id": "job-2",
            "action_type": "run_render_validation",
            "status": "queued",
            "priority": "normal",
            "task_id": "task-2",
            "subject_type": "guide",
            "subject_id": "motor-control-centers-low-voltage",
            "requested_by": "actor-2",
            "created_at": now,
        }
    )

    queued = enqueue_render_validation(
        session,
        guide_slug="motor-control-centers-low-voltage",
        validation_target="render-contract",
        expected_asset_ids=["asset-1", "asset-2"],
        task_id="task-2",
        priority="normal",
        requested_by="actor-2",
    )

    assert queued["action_type"] == "run_render_validation"
    assert session.params["subject_type"] == "guide"
    assert session.params["subject_id"] == "motor-control-centers-low-voltage"
    assert json.loads(session.params["request_payload"]) == {
        "guide_slug": "motor-control-centers-low-voltage",
        "validation_target": "render-contract",
        "expected_asset_ids": ["asset-1", "asset-2"],
    }


def test_enqueue_local_action_accepts_secure_bridge_read_action():
    now = datetime.now(timezone.utc)
    session = _FakeSession(
        {
            "job_id": "job-3",
            "action_type": "read_workspace_file",
            "status": "queued",
            "priority": "normal",
            "task_id": "task-3",
            "subject_type": "workspace_file",
            "subject_id": "Development/Control-Plane/example.md",
            "requested_by": "actor-3",
            "created_at": now,
        }
    )

    queued = enqueue_local_action(
        session,
        action_type="read_workspace_file",
        priority="normal",
        task_id="task-3",
        subject_type="workspace_file",
        subject_id="Development/Control-Plane/example.md",
        requested_by="actor-3",
        request_payload={"path": "Development/Control-Plane/example.md", "start_line": 1, "end_line": 40},
    )

    assert queued["action_type"] == "read_workspace_file"
    assert json.loads(session.params["request_payload"])["path"] == "Development/Control-Plane/example.md"


def test_enqueue_local_action_accepts_staging_authoring_action():
    now = datetime.now(timezone.utc)
    session = _FakeSession(
        {
            "job_id": "job-4",
            "action_type": "write_staging_authoring_candidate",
            "status": "queued",
            "priority": "normal",
            "task_id": "task-4",
            "subject_type": "authoring_target",
            "subject_id": "Development/staging/example/SG-CT-EXAMPLE.md",
            "requested_by": "actor-4",
            "created_at": now,
        }
    )

    queued = enqueue_local_action(
        session,
        action_type="write_staging_authoring_candidate",
        priority="normal",
        task_id="task-4",
        subject_type="authoring_target",
        subject_id="Development/staging/example/SG-CT-EXAMPLE.md",
        requested_by="actor-4",
        request_payload={
            "path": "Development/staging/example/SG-CT-EXAMPLE.md",
            "content": "# Example\n",
            "overwrite": True,
        },
    )

    assert queued["action_type"] == "write_staging_authoring_candidate"
    assert json.loads(session.params["request_payload"])["overwrite"] is True
