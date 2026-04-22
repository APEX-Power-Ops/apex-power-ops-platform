"""Shared helpers for control-plane queue insertion paths."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


ALLOWED_LOCAL_ACTION_TYPES = {
    "prepare_packet_briefing",
    "run_image_integration",
    "run_render_validation",
    "collect_validation_evidence",
    "list_workspace_directory",
    "read_workspace_file",
    "search_workspace",
    "write_review_artifact",
    "write_staging_authoring_candidate",
    "git_status",
}

ALLOWED_QUEUE_PRIORITIES = {"low", "normal", "high", "urgent"}


def _row_mapping(row: Any) -> dict[str, Any]:
    return dict(row._mapping) if row is not None else {}


def validate_local_action_type(action_type: str) -> None:
    if action_type not in ALLOWED_LOCAL_ACTION_TYPES:
        raise ValueError("Unsupported local action type")


def validate_queue_priority(priority: str) -> None:
    if priority not in ALLOWED_QUEUE_PRIORITIES:
        raise ValueError("Unsupported queue priority")


def enqueue_local_action(
    db: Session,
    *,
    action_type: str,
    priority: str,
    task_id: str | None,
    subject_type: str,
    subject_id: str,
    requested_by: str,
    request_payload: dict[str, Any],
) -> dict[str, Any]:
    validate_local_action_type(action_type)
    validate_queue_priority(priority)

    job_id = f"job-{uuid4()}"
    row = db.execute(
        text(
            """
            INSERT INTO public.mcp_local_action_queue (
                job_id,
                action_type,
                status,
                priority,
                task_id,
                subject_type,
                subject_id,
                requested_by,
                request_payload
            )
            VALUES (
                :job_id,
                :action_type,
                'queued',
                :priority,
                :task_id,
                :subject_type,
                :subject_id,
                :requested_by,
                CAST(:request_payload AS jsonb)
            )
            RETURNING
                job_id,
                action_type,
                status,
                priority,
                task_id,
                subject_type,
                subject_id,
                requested_by,
                created_at
            """
        ),
        {
            "job_id": job_id,
            "action_type": action_type,
            "priority": priority,
            "task_id": task_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "requested_by": requested_by,
            "request_payload": json.dumps(request_payload),
        },
    ).fetchone()
    return _row_mapping(row)


def enqueue_render_validation(
    db: Session,
    *,
    guide_slug: str,
    validation_target: str,
    expected_asset_ids: list[str],
    task_id: str | None,
    priority: str,
    requested_by: str,
) -> dict[str, Any]:
    request_payload = {
        "guide_slug": guide_slug,
        "validation_target": validation_target,
        "expected_asset_ids": expected_asset_ids,
    }
    return enqueue_local_action(
        db,
        action_type="run_render_validation",
        priority=priority,
        task_id=task_id,
        subject_type="guide",
        subject_id=guide_slug,
        requested_by=requested_by,
        request_payload=request_payload,
    )
