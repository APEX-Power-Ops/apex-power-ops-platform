"""FastAPI router for the initial remote control-plane scaffold.

This is an authenticated HTTP surface that mirrors the first packet, review,
queue, job, and validation-artifact domains defined in the governance spec.
It is intentionally narrower than the full future MCP server.
"""

from __future__ import annotations

import json
import math
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import get_db
from services.auth import AuthenticatedUser, get_current_user

from .queue import (
    ALLOWED_LOCAL_ACTION_TYPES,
    ALLOWED_QUEUE_PRIORITIES,
    enqueue_local_action,
    enqueue_render_validation,
)
from .schemas import (
    AttachCloseoutNoteRequest,
    CostEstimateRequest,
    CostEstimateResponse,
    CreateReviewDecisionRequest,
    ImageAssetDetail,
    ImageAssetStatusResponse,
    ImageAssetSummary,
    ImageGuideLinkRecord,
    JobRunDetail,
    JobRunSummary,
    LanePriorityItem,
    PlanPreviewRequest,
    PlanPreviewResponse,
    PlanPreviewStep,
    QueueLocalActionRequest,
    QueueLocalActionResponse,
    QueueRenderValidationRequest,
    ReviewDecisionRecord,
    TaskPacketDetail,
    TaskPacketStatusResponse,
    TaskPacketSummary,
    UpdateImageAssetStatusRequest,
    UpdateTaskPacketStatusRequest,
    ValidationArtifactDetail,
)

router = APIRouter(prefix="/api/v1/control-plane", tags=["control-plane"])

_ALLOWED_PACKET_STATUS_TRANSITIONS = {
    ("pending", "prepared"),
    ("prepared", "in_review"),
    ("in_review", "escalated"),
    ("in_review", "approved_for_local_action"),
    ("approved_for_local_action", "awaiting_results"),
    ("awaiting_results", "ready_for_closeout"),
    ("ready_for_closeout", "completed"),
}

_AUTHORING_QUEUEABLE_PACKET_STATUSES = {"approved_for_local_action", "awaiting_results"}

_ALLOWED_IMAGE_ASSET_STATUS_TRANSITIONS = {
    ("tagged", "in_progress"),
    ("in_progress", "review"),
    ("review", "integrated"),
    ("review", "deferred"),
}

_REQUIRED_IMAGE_TABLES = (
    "image_assets",
    "image_guide_links",
    "mcp_validation_artifacts",
)

_REQUIRED_TASK_PACKET_RELATIONS = (
    "mcp_task_packets",
    "mcp_task_packet_summary_v",
    "mcp_review_decisions",
)

_REQUIRED_LANE_PRIORITY_RELATIONS = (
    "mcp_lane_priorities",
)

_REQUIRED_JOB_RELATIONS = (
    "mcp_local_action_queue",
    "mcp_job_runs",
    "mcp_job_run_summary_v",
)

_MODEL_TIER_COSTS = {
    "tier-a": {"input_per_million": 5.0, "output_per_million": 15.0, "base_output": 4500, "duration": 18},
    "tier-b": {"input_per_million": 1.5, "output_per_million": 6.0, "base_output": 2500, "duration": 10},
    "tier-c": {"input_per_million": 0.5, "output_per_million": 2.0, "base_output": 1200, "duration": 5},
}


def _row_mapping(row: Any) -> dict[str, Any]:
    return dict(row._mapping) if row is not None else {}


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {} if value is None else dict(value)


def _json_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _normalize_relative_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _packet_summary_from_row(row: Any) -> TaskPacketSummary:
    payload = _row_mapping(row)
    return TaskPacketSummary(**payload)


def _review_decision_from_row(row: Any) -> ReviewDecisionRecord:
    payload = _row_mapping(row)
    payload["id"] = str(payload["id"])
    payload["evidence_links"] = _json_string_list(payload.get("evidence_links"))
    return ReviewDecisionRecord(**payload)


def _lane_priority_from_row(row: Any) -> LanePriorityItem:
    payload = _row_mapping(row)
    payload["id"] = str(payload["id"])
    return LanePriorityItem(**payload)


def _job_summary_from_row(row: Any) -> JobRunSummary:
    return JobRunSummary(**_row_mapping(row))


def _job_detail_from_rows(queue_row: Any, run_row: Any) -> JobRunDetail:
    queue_payload = _row_mapping(queue_row)
    run_payload = _row_mapping(run_row)
    return JobRunDetail(
        job_id=queue_payload["job_id"],
        action_type=queue_payload["action_type"],
        status=queue_payload["status"],
        subject_type=queue_payload["subject_type"],
        subject_id=queue_payload["subject_id"],
        created_at=queue_payload["created_at"],
        completed_at=queue_payload.get("completed_at"),
        result_summary=run_payload.get("result_summary"),
        task_id=queue_payload.get("task_id"),
        request_payload=_json_object(queue_payload.get("request_payload")),
        requested_by=queue_payload["requested_by"],
        claimed_at=queue_payload.get("claimed_at"),
        claimed_by=queue_payload.get("claimed_by"),
        latest_run_id=str(run_payload["id"]) if run_payload.get("id") is not None else None,
        latest_runner_id=run_payload.get("runner_id"),
        started_at=run_payload.get("started_at"),
        result_json=run_payload.get("result_json"),
        evidence_artifacts=_json_string_list(run_payload.get("evidence_artifacts")),
    )


def _validation_artifact_from_row(row: Any) -> ValidationArtifactDetail:
    payload = _row_mapping(row)
    payload["artifact_json"] = payload.get("artifact_json")
    return ValidationArtifactDetail(**payload)


def _image_asset_summary_from_row(row: Any) -> ImageAssetSummary:
    payload = _row_mapping(row)
    payload["guide_slugs"] = _json_string_list(payload.get("guide_slugs"))
    return ImageAssetSummary(**payload)


def _image_guide_link_from_row(row: Any) -> ImageGuideLinkRecord:
    return ImageGuideLinkRecord(**_row_mapping(row))


def _image_asset_detail_from_rows(asset_row: Any, link_rows: list[Any]) -> ImageAssetDetail:
    payload = _row_mapping(asset_row)
    payload["guide_slugs"] = _json_string_list(payload.get("guide_slugs"))
    payload["guide_links"] = [_image_guide_link_from_row(row) for row in link_rows]
    return ImageAssetDetail(**payload)


def _normalized_tier(value: Optional[str]) -> str:
    normalized = (value or "tier-b").strip().lower()
    if normalized not in _MODEL_TIER_COSTS:
        return "tier-b"
    return normalized


def _recommend_model_tier(task: str, preferred_model_tier: Optional[str], risk_level: Optional[str]) -> str:
    explicit = _normalized_tier(preferred_model_tier) if preferred_model_tier else None
    if explicit and preferred_model_tier:
        return explicit

    lowered_task = task.lower()
    if (risk_level or "").lower() == "high":
        return "tier-a"
    if any(keyword in lowered_task for keyword in ("governance", "authority", "review", "queue", "schema", "migration")):
        return "tier-a"
    if any(keyword in lowered_task for keyword in ("summary", "format", "documentation", "boilerplate")):
        return "tier-c"
    return "tier-b"


def _build_plan_preview(payload: PlanPreviewRequest) -> PlanPreviewResponse:
    recommended_tier = _recommend_model_tier(payload.task, payload.preferred_model_tier, payload.risk_level)
    workflow = "review_and_queue" if payload.requires_local_action else "review_only"
    lane = payload.lane or "control-plane"
    action_type = payload.action_type or "review"

    steps = [
        PlanPreviewStep(
            step=1,
            title="Assess packet boundary",
            owner=recommended_tier,
            outcome=f"Validate {lane} scope and confirm {action_type} objective.",
        ),
        PlanPreviewStep(
            step=2,
            title="Record authority decision",
            owner="control-plane",
            outcome="Produce a durable review decision or status transition reason.",
        ),
    ]

    if payload.requires_local_action:
        steps.append(
            PlanPreviewStep(
                step=3,
                title="Queue bounded local action",
                owner="control-plane",
                outcome="Submit a privileged local action through the governed queue seam.",
            )
        )
        steps.append(
            PlanPreviewStep(
                step=4,
                title="Review returned evidence",
                owner=recommended_tier,
                outcome="Evaluate results before closeout or escalation.",
            )
        )
    else:
        steps.append(
            PlanPreviewStep(
                step=3,
                title="Close out or escalate",
                owner=recommended_tier,
                outcome="Approve completion or escalate if the review gate is not satisfied.",
            )
        )

    return PlanPreviewResponse(
        recommended_model_tier=recommended_tier,
        workflow=workflow,
        needs_review_gate=payload.requires_review_decision,
        needs_local_action_queue=payload.requires_local_action,
        summary=(
            f"Use {recommended_tier} for the authority loop, keep the work in the {lane} lane, "
            f"and {'route privileged execution through the local-action queue' if payload.requires_local_action else 'avoid unnecessary queue expansion'}.") ,
        steps=steps,
    )


def _build_cost_estimate(payload: CostEstimateRequest) -> CostEstimateResponse:
    preferred_tier = _normalized_tier(payload.preferred_model_tier)
    pricing = _MODEL_TIER_COSTS[preferred_tier]
    task_tokens = max(1, math.ceil(len(payload.task) / 4))

    estimated_experts = payload.expected_experts
    if estimated_experts is None:
        estimated_experts = 1
        if payload.requires_review_decision:
            estimated_experts += 1
        if payload.requires_local_action:
            estimated_experts += 1
        if preferred_tier == "tier-a":
            estimated_experts += 1

    estimated_input_tokens = task_tokens + (estimated_experts * 500)
    estimated_output_tokens = pricing["base_output"] * estimated_experts
    total_tokens = estimated_input_tokens + estimated_output_tokens
    estimated_cost_usd = round(
        ((estimated_input_tokens / 1_000_000) * pricing["input_per_million"]) +
        ((estimated_output_tokens / 1_000_000) * pricing["output_per_million"]),
        4,
    )
    estimated_duration_seconds = pricing["duration"] * estimated_experts

    return CostEstimateResponse(
        task_tokens=task_tokens,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        estimated_duration_seconds=estimated_duration_seconds,
        estimated_experts=estimated_experts,
        preferred_model_tier=preferred_tier,
    )


def _require_packet_row(db: Session, task_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT
                task_id,
                title,
                lane,
                primary_repo,
                status,
                action_type,
                risk_level,
                preferred_model_tier,
                review_gate,
                briefing_path,
                packet_json,
                claimed_by,
                created_at,
                updated_at,
                last_reviewed_at
            FROM public.mcp_task_packets
            WHERE task_id = :task_id
            """
        ),
        {"task_id": task_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task packet not found")
    return _row_mapping(row)


def _validate_authoring_queue_request(db: Session, payload: QueueLocalActionRequest) -> dict[str, Any]:
    if not payload.task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_id is required for staging authoring queue requests",
        )

    packet = _require_packet_row(db, payload.task_id)
    packet_status = str(packet.get("status") or "").strip()
    if packet_status not in _AUTHORING_QUEUEABLE_PACKET_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task packet status does not allow authoring queue submission",
        )

    if str(packet.get("action_type") or "").strip() not in {"draft", "edit"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task packet action_type does not authorize staging authoring",
        )

    packet_json = _json_object(packet.get("packet_json"))
    authoring = _json_object(packet_json.get("authoring"))
    route = _json_object(packet_json.get("route"))

    if not bool(authoring.get("enabled") or False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task packet does not enable staging authoring",
        )
    if str(authoring.get("mode") or "").strip() != "staging_only":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task packet authoring mode is not supported",
        )
    if not bool(route.get("allow_auto_apply") or False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task packet does not permit auto-apply authoring",
        )
    if payload.subject_type != "authoring_target":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="staging authoring queue requests must use subject_type 'authoring_target'",
        )

    requested_path = _normalize_relative_path(payload.request_payload.get("path") or payload.subject_id)
    subject_path = _normalize_relative_path(payload.subject_id)
    if not requested_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="staging authoring queue requests must include a target path",
        )
    if subject_path != requested_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="subject_id must match the requested authoring target path",
        )
    if not requested_path.startswith("Development/staging/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="staging authoring queue target must remain inside Development/staging/",
        )

    allowed_target_files = {
        _normalize_relative_path(item)
        for item in authoring.get("allowed_target_files") or []
        if _normalize_relative_path(item)
    }
    if requested_path not in allowed_target_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="staging authoring queue target is not allowed by the task packet",
        )

    return packet


def _mark_authoring_packet_awaiting_results(
    db: Session,
    *,
    task_id: str,
    current_status: str,
    actor_id: str,
    action_type: str,
    subject_id: str,
) -> None:
    if current_status != "approved_for_local_action":
        return

    db.execute(
        text(
            """
            UPDATE public.mcp_task_packets
            SET status = 'awaiting_results',
                last_reviewed_at = NOW()
            WHERE task_id = :task_id
            """
        ),
        {"task_id": task_id},
    )
    db.execute(
        text(
            """
            INSERT INTO public.mcp_review_decisions (
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links
            )
            VALUES (
                'task_packet',
                :task_id,
                'local_action_queued',
                :reasoning_summary,
                'awaiting_results',
                :actor_id,
                'queue_local_action',
                '[]'::jsonb
            )
            """
        ),
        {
            "task_id": task_id,
            "reasoning_summary": f"Queued {action_type} for {subject_id}; packet is now awaiting local action results.",
            "actor_id": actor_id,
        },
    )


def _require_image_tables(db: Session) -> None:
    row = db.execute(
        text(
            """
            SELECT
                to_regclass('public.image_assets') AS image_assets,
                to_regclass('public.image_guide_links') AS image_guide_links,
                to_regclass('public.mcp_validation_artifacts') AS mcp_validation_artifacts
            """
        )
    ).fetchone()
    payload = _row_mapping(row)
    missing = [table_name for table_name in _REQUIRED_IMAGE_TABLES if payload.get(table_name) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image asset dependencies missing in database: " + ", ".join(missing),
        )


def _require_control_plane_relations(db: Session, relation_names: tuple[str, ...]) -> None:
    relation_select_sql = ",\n                ".join(
        f"to_regclass('public.{relation_name}') AS {relation_name}"
        for relation_name in relation_names
    )
    row = db.execute(
        text(
            f"""
            SELECT
                {relation_select_sql}
            """
        )
    ).fetchone()
    payload = _row_mapping(row)
    missing = [relation_name for relation_name in relation_names if payload.get(relation_name) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Control-plane dependencies missing in database: " + ", ".join(missing),
        )


def _require_image_asset_row(db: Session, asset_id: str) -> Any:
    row = db.execute(
        text(
            """
            SELECT
                ia.id,
                ia.caption,
                ia.source_doc,
                ia.source_ref,
                ia.alt_text,
                ia.notes,
                ia.sourcing_method,
                ia.sourcing_hint,
                ia.production_tool,
                ia.status,
                ia.git_path,
                ia.storage_bucket,
                ia.storage_path,
                ia.storage_url,
                ia.file_format,
                ia.file_size_bytes,
                ia.width_px,
                ia.height_px,
                ia.figma_file_key,
                ia.figma_node_id,
                ia.script_path,
                ia.quality_tier,
                ia.created_at,
                ia.updated_at,
                ia.classified_at,
                ia.produced_at,
                ia.integrated_at,
                COALESCE(array_remove(array_agg(DISTINCT igl.guide_slug), NULL), ARRAY[]::text[]) AS guide_slugs,
                latest_va.artifact_id AS latest_validation_artifact_id,
                latest_va.summary AS latest_validation_artifact_summary
            FROM public.image_assets ia
            LEFT JOIN public.image_guide_links igl
              ON igl.image_asset_id = ia.id
            LEFT JOIN LATERAL (
                SELECT artifact_id, summary
                FROM public.mcp_validation_artifacts va
                WHERE va.subject_type = 'image_asset'
                  AND va.subject_id = ia.id
                ORDER BY va.created_at DESC
                LIMIT 1
            ) latest_va ON TRUE
            WHERE ia.id = :asset_id
            GROUP BY
                ia.id,
                ia.caption,
                ia.source_doc,
                ia.source_ref,
                ia.alt_text,
                ia.notes,
                ia.sourcing_method,
                ia.sourcing_hint,
                ia.production_tool,
                ia.status,
                ia.git_path,
                ia.storage_bucket,
                ia.storage_path,
                ia.storage_url,
                ia.file_format,
                ia.file_size_bytes,
                ia.width_px,
                ia.height_px,
                ia.figma_file_key,
                ia.figma_node_id,
                ia.script_path,
                ia.quality_tier,
                ia.created_at,
                ia.updated_at,
                ia.classified_at,
                ia.produced_at,
                ia.integrated_at,
                latest_va.artifact_id,
                latest_va.summary
            """
        ),
        {"asset_id": asset_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image asset not found")
    return row


def _fetch_validation_artifact_row(
    db: Session,
    *,
    artifact_id: Optional[str] = None,
    subject_type: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> Any:
    if artifact_id:
        row = db.execute(
            text(
                """
                SELECT
                    artifact_id,
                    artifact_type,
                    subject_type,
                    subject_id,
                    title,
                    summary,
                    artifact_path,
                    artifact_uri,
                    artifact_json,
                    created_by,
                    created_at
                FROM public.mcp_validation_artifacts
                WHERE artifact_id = :artifact_id
                """
            ),
            {"artifact_id": artifact_id},
        ).fetchone()
    else:
        row = db.execute(
            text(
                """
                SELECT
                    artifact_id,
                    artifact_type,
                    subject_type,
                    subject_id,
                    title,
                    summary,
                    artifact_path,
                    artifact_uri,
                    artifact_json,
                    created_by,
                    created_at
                FROM public.mcp_validation_artifacts
                WHERE subject_type = :subject_type
                  AND subject_id = :subject_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"subject_type": subject_type, "subject_id": subject_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation artifact not found")
    return row


@router.get("/task-packets", response_model=list[TaskPacketSummary])
def list_task_packets(
    lane: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    primary_repo: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_TASK_PACKET_RELATIONS)
    rows = db.execute(
        text(
            """
            SELECT
                task_id,
                title,
                lane,
                status,
                risk_level,
                preferred_model_tier,
                review_gate,
                updated_at
            FROM public.mcp_task_packet_summary_v
            WHERE (:lane IS NULL OR lane = :lane)
              AND (:status_filter IS NULL OR status = :status_filter)
              AND (:primary_repo IS NULL OR task_id IN (
                    SELECT task_id
                    FROM public.mcp_task_packets
                    WHERE primary_repo = :primary_repo
                ))
              AND (:risk_level IS NULL OR risk_level = :risk_level)
            ORDER BY updated_at DESC
            LIMIT :limit
            """
        ),
        {
            "lane": lane,
            "status_filter": status_filter,
            "primary_repo": primary_repo,
            "risk_level": risk_level,
            "limit": limit,
        },
    ).fetchall()
    return [_packet_summary_from_row(row) for row in rows]


@router.post("/plan-preview", response_model=PlanPreviewResponse)
def explain_plan(
    payload: PlanPreviewRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    return _build_plan_preview(payload)


@router.post("/cost-estimate", response_model=CostEstimateResponse)
def cost_estimate(
    payload: CostEstimateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    return _build_cost_estimate(payload)


@router.get("/task-packets/{task_id}", response_model=TaskPacketDetail)
def fetch_task_packet(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_TASK_PACKET_RELATIONS)
    packet = _require_packet_row(db, task_id)
    decision_rows = db.execute(
        text(
            """
            SELECT
                id,
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links,
                created_at
            FROM public.mcp_review_decisions
            WHERE subject_type = 'task_packet'
              AND subject_id = :task_id
            ORDER BY created_at DESC
            LIMIT 10
            """
        ),
        {"task_id": task_id},
    ).fetchall()
    packet_payload = dict(packet)
    packet_payload["packet_json"] = _json_object(packet_payload.get("packet_json"))
    return TaskPacketDetail(
        **packet_payload,
        review_decisions=[_review_decision_from_row(row) for row in decision_rows],
    )


@router.post("/task-packets/{task_id}/status", response_model=TaskPacketStatusResponse)
def update_task_packet_status(
    task_id: str,
    payload: UpdateTaskPacketStatusRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    packet = _require_packet_row(db, task_id)
    previous_status = str(packet["status"])
    transition = (previous_status, payload.new_status)
    if transition not in _ALLOWED_PACKET_STATUS_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Disallowed packet status transition: {previous_status} -> {payload.new_status}",
        )

    updated_at = db.execute(
        text(
            """
            UPDATE public.mcp_task_packets
            SET status = :new_status,
                packet_json = jsonb_set(
                    COALESCE(packet_json, '{}'::jsonb),
                    '{status}',
                    to_jsonb(CAST(:new_status AS text)),
                    true
                ),
                last_reviewed_at = NOW()
            WHERE task_id = :task_id
            RETURNING updated_at
            """
        ),
        {"task_id": task_id, "new_status": payload.new_status},
    ).scalar_one()

    db.execute(
        text(
            """
            INSERT INTO public.mcp_review_decisions (
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links
            )
            VALUES (
                'task_packet',
                :task_id,
                'status_transition',
                :reasoning_summary,
                :new_status,
                :actor_id,
                'update_task_packet_status',
                '[]'::jsonb
            )
            """
        ),
        {
            "task_id": task_id,
            "reasoning_summary": payload.reasoning_summary,
            "new_status": payload.new_status,
            "actor_id": str(current_user.user_id),
        },
    )
    db.commit()

    return TaskPacketStatusResponse(
        task_id=task_id,
        previous_status=previous_status,
        new_status=payload.new_status,
        updated_at=updated_at,
        reasoning_summary=payload.reasoning_summary,
    )


@router.post("/review-decisions", response_model=ReviewDecisionRecord, status_code=status.HTTP_201_CREATED)
def create_review_decision(
    payload: CreateReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    row = db.execute(
        text(
            """
            INSERT INTO public.mcp_review_decisions (
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links
            )
            VALUES (
                :subject_type,
                :subject_id,
                :decision,
                :reasoning_summary,
                :required_next_action,
                :actor_id,
                'create_review_decision',
                CAST(:evidence_links AS jsonb)
            )
            RETURNING
                id,
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links,
                created_at
            """
        ),
        {
            "subject_type": payload.subject_type,
            "subject_id": payload.subject_id,
            "decision": payload.decision,
            "reasoning_summary": payload.reasoning_summary,
            "required_next_action": payload.required_next_action,
            "actor_id": str(current_user.user_id),
            "evidence_links": json.dumps(payload.evidence_links),
        },
    ).fetchone()
    db.commit()
    return _review_decision_from_row(row)


@router.get("/lane-priorities", response_model=list[LanePriorityItem])
def list_lane_priorities(
    lane: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_LANE_PRIORITY_RELATIONS)
    rows = db.execute(
        text(
            """
            SELECT
                id,
                lane,
                priority_rank,
                item_id,
                title,
                status,
                source_surface,
                notes,
                updated_at
            FROM public.mcp_lane_priorities
            WHERE (:lane IS NULL OR lane = :lane)
            ORDER BY lane ASC, priority_rank ASC, updated_at DESC
            LIMIT :limit
            """
        ),
        {"lane": lane, "limit": limit},
    ).fetchall()
    return [_lane_priority_from_row(row) for row in rows]


@router.get("/lane-priorities/{lane}/{item_id}", response_model=LanePriorityItem)
def fetch_priority_item(
    lane: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_LANE_PRIORITY_RELATIONS)
    row = db.execute(
        text(
            """
            SELECT
                id,
                lane,
                priority_rank,
                item_id,
                title,
                status,
                source_surface,
                notes,
                updated_at
            FROM public.mcp_lane_priorities
            WHERE lane = :lane
              AND item_id = :item_id
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"lane": lane, "item_id": item_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Priority item not found")
    return _lane_priority_from_row(row)


@router.get("/image-assets", response_model=list[ImageAssetSummary])
def list_image_assets(
    guide_slug: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    sourcing_method: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_image_tables(db)
    rows = db.execute(
        text(
            """
            SELECT
                ia.id,
                ia.caption,
                ia.status,
                ia.sourcing_method,
                ia.production_tool,
                COALESCE(array_remove(array_agg(DISTINCT igl.guide_slug), NULL), ARRAY[]::text[]) AS guide_slugs,
                ia.git_path,
                ia.storage_bucket,
                ia.storage_path,
                ia.storage_url,
                ia.updated_at,
                latest_va.artifact_id AS latest_validation_artifact_id
            FROM public.image_assets ia
            LEFT JOIN public.image_guide_links igl
              ON igl.image_asset_id = ia.id
            LEFT JOIN LATERAL (
                SELECT artifact_id
                FROM public.mcp_validation_artifacts va
                WHERE va.subject_type = 'image_asset'
                  AND va.subject_id = ia.id
                ORDER BY va.created_at DESC
                LIMIT 1
            ) latest_va ON TRUE
            WHERE (:status_filter IS NULL OR ia.status = :status_filter)
              AND (:sourcing_method IS NULL OR ia.sourcing_method = :sourcing_method)
              AND (
                    :guide_slug IS NULL
                    OR EXISTS (
                        SELECT 1
                        FROM public.image_guide_links igf
                        WHERE igf.image_asset_id = ia.id
                          AND igf.guide_slug = :guide_slug
                    )
                )
            GROUP BY
                ia.id,
                ia.caption,
                ia.status,
                ia.sourcing_method,
                ia.production_tool,
                ia.git_path,
                ia.storage_bucket,
                ia.storage_path,
                ia.storage_url,
                ia.updated_at,
                latest_va.artifact_id
            ORDER BY ia.updated_at DESC, ia.id ASC
            LIMIT :limit
            """
        ),
        {
            "guide_slug": guide_slug,
            "status_filter": status_filter,
            "sourcing_method": sourcing_method,
            "limit": limit,
        },
    ).fetchall()
    return [_image_asset_summary_from_row(row) for row in rows]


@router.get("/image-assets/{asset_id}", response_model=ImageAssetDetail)
def fetch_image_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_image_tables(db)
    asset_row = _require_image_asset_row(db, asset_id)
    link_rows = db.execute(
        text(
            """
            SELECT
                guide_slug,
                guide_file,
                content_id,
                line_number,
                section_context,
                created_at
            FROM public.image_guide_links
            WHERE image_asset_id = :asset_id
            ORDER BY guide_slug ASC, guide_file ASC, line_number ASC NULLS LAST
            """
        ),
        {"asset_id": asset_id},
    ).fetchall()
    return _image_asset_detail_from_rows(asset_row, link_rows)


@router.post("/image-assets/{asset_id}/status", response_model=ImageAssetStatusResponse)
def update_image_asset_status(
    asset_id: str,
    payload: UpdateImageAssetStatusRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    _require_image_tables(db)
    asset = _row_mapping(
        db.execute(
            text(
                """
                SELECT id, status
                FROM public.image_assets
                WHERE id = :asset_id
                """
            ),
            {"asset_id": asset_id},
        ).fetchone()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image asset not found")

    previous_status = str(asset["status"])
    transition = (previous_status, payload.new_status)
    if transition not in _ALLOWED_IMAGE_ASSET_STATUS_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Disallowed image asset status transition: {previous_status} -> {payload.new_status}",
        )

    updated_at = db.execute(
        text(
            """
            UPDATE public.image_assets
            SET status = :new_status,
                integrated_at = CASE
                    WHEN :new_status = 'integrated' THEN COALESCE(integrated_at, NOW())
                    ELSE integrated_at
                END
            WHERE id = :asset_id
            RETURNING updated_at
            """
        ),
        {"asset_id": asset_id, "new_status": payload.new_status},
    ).scalar_one()

    db.execute(
        text(
            """
            INSERT INTO public.mcp_review_decisions (
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links
            )
            VALUES (
                'image_asset',
                :asset_id,
                'status_transition',
                :reasoning_summary,
                :new_status,
                :actor_id,
                'update_image_asset_status',
                '[]'::jsonb
            )
            """
        ),
        {
            "asset_id": asset_id,
            "reasoning_summary": f"{previous_status} -> {payload.new_status}: {payload.decision_basis}",
            "new_status": payload.new_status,
            "actor_id": str(current_user.user_id),
        },
    )
    db.commit()

    return ImageAssetStatusResponse(
        asset_id=asset_id,
        previous_status=previous_status,
        new_status=payload.new_status,
        updated_at=updated_at,
        decision_basis=payload.decision_basis,
    )


@router.post("/local-actions", response_model=QueueLocalActionResponse, status_code=status.HTTP_201_CREATED)
def queue_local_action(
    payload: QueueLocalActionRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    authoring_packet = None
    if not payload.confirmed_by_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit user confirmation is required for queue_local_action",
        )
    if payload.action_type == "write_staging_authoring_candidate":
        authoring_packet = _validate_authoring_queue_request(db, payload)
    try:
        queued = enqueue_local_action(
            db,
            action_type=payload.action_type,
            priority=payload.priority,
            task_id=payload.task_id,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            requested_by=str(current_user.user_id),
            request_payload=payload.request_payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if authoring_packet is not None:
        _mark_authoring_packet_awaiting_results(
            db,
            task_id=str(authoring_packet["task_id"]),
            current_status=str(authoring_packet.get("status") or ""),
            actor_id=str(current_user.user_id),
            action_type=payload.action_type,
            subject_id=payload.subject_id,
        )
    db.commit()
    return QueueLocalActionResponse(**queued)


@router.post("/render-validations", response_model=QueueLocalActionResponse, status_code=status.HTTP_201_CREATED)
def queue_render_validation(
    payload: QueueRenderValidationRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        queued = enqueue_render_validation(
            db,
            guide_slug=payload.guide_slug,
            validation_target=payload.validation_target,
            expected_asset_ids=payload.expected_asset_ids,
            task_id=payload.task_id,
            priority=payload.priority,
            requested_by=str(current_user.user_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return QueueLocalActionResponse(**queued)


@router.get("/job-runs", response_model=list[JobRunSummary])
def list_job_runs(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    subject_type: Optional[str] = Query(default=None),
    subject_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_JOB_RELATIONS)
    rows = db.execute(
        text(
            """
            SELECT
                job_id,
                action_type,
                status,
                subject_type,
                subject_id,
                created_at,
                completed_at,
                result_summary
            FROM public.mcp_job_run_summary_v
            WHERE (:status_filter IS NULL OR status = :status_filter)
              AND (:subject_type IS NULL OR subject_type = :subject_type)
              AND (:subject_id IS NULL OR subject_id = :subject_id)
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {
            "status_filter": status_filter,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "limit": limit,
        },
    ).fetchall()
    return [_job_summary_from_row(row) for row in rows]


@router.get("/job-runs/{job_id}", response_model=JobRunDetail)
def fetch_job_run(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    _require_control_plane_relations(db, _REQUIRED_JOB_RELATIONS)
    queue_row = db.execute(
        text(
            """
            SELECT
                job_id,
                action_type,
                status,
                priority,
                task_id,
                subject_type,
                subject_id,
                requested_by,
                request_payload,
                created_at,
                claimed_at,
                claimed_by,
                completed_at
            FROM public.mcp_local_action_queue
            WHERE job_id = :job_id
            """
        ),
        {"job_id": job_id},
    ).fetchone()
    if queue_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job run not found")

    run_row = db.execute(
        text(
            """
            SELECT
                id,
                status,
                result_summary,
                result_json,
                evidence_artifacts,
                runner_id,
                started_at,
                completed_at
            FROM public.mcp_job_runs
            WHERE job_id = :job_id
            ORDER BY COALESCE(completed_at, started_at) DESC NULLS LAST
            LIMIT 1
            """
        ),
        {"job_id": job_id},
    ).fetchone()
    return _job_detail_from_rows(queue_row, run_row)


@router.get("/validation-artifacts/{artifact_id}", response_model=ValidationArtifactDetail)
def fetch_validation_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    row = _fetch_validation_artifact_row(db, artifact_id=artifact_id)
    return _validation_artifact_from_row(row)


@router.get("/validation-artifacts", response_model=ValidationArtifactDetail)
def lookup_validation_artifact(
    artifact_id: Optional[str] = Query(default=None),
    subject_type: Optional[str] = Query(default=None),
    subject_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    del current_user
    if not artifact_id and not (subject_type and subject_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide artifact_id or both subject_type and subject_id",
        )
    row = _fetch_validation_artifact_row(
        db,
        artifact_id=artifact_id,
        subject_type=subject_type,
        subject_id=subject_id,
    )
    return _validation_artifact_from_row(row)


@router.post("/closeout-notes", response_model=ReviewDecisionRecord, status_code=status.HTTP_201_CREATED)
def attach_closeout_note(
    payload: AttachCloseoutNoteRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    row = db.execute(
        text(
            """
            INSERT INTO public.mcp_review_decisions (
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links
            )
            VALUES (
                :subject_type,
                :subject_id,
                'closeout_note',
                :note,
                NULL,
                :actor_id,
                'attach_closeout_note',
                '[]'::jsonb
            )
            RETURNING
                id,
                subject_type,
                subject_id,
                decision,
                reasoning_summary,
                required_next_action,
                actor_id,
                source_tool,
                evidence_links,
                created_at
            """
        ),
        {
            "subject_type": payload.subject_type,
            "subject_id": payload.subject_id,
            "note": payload.note,
            "actor_id": str(current_user.user_id),
        },
    ).fetchone()
    db.commit()
    return _review_decision_from_row(row)