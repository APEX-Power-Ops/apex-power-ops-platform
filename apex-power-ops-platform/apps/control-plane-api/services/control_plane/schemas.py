"""Pydantic schemas for the remote control-plane HTTP scaffold."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReviewDecisionRecord(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    decision: str
    reasoning_summary: str
    required_next_action: Optional[str] = None
    actor_id: str
    source_tool: str
    evidence_links: list[str] = Field(default_factory=list)
    created_at: datetime


class TaskPacketSummary(BaseModel):
    task_id: str
    title: str
    lane: str
    status: str
    risk_level: str
    preferred_model_tier: Optional[str] = None
    review_gate: Optional[str] = None
    updated_at: datetime


class TaskPacketDetail(TaskPacketSummary):
    primary_repo: str
    action_type: str
    briefing_path: Optional[str] = None
    claimed_by: Optional[str] = None
    created_at: datetime
    last_reviewed_at: Optional[datetime] = None
    packet_json: dict[str, Any]
    review_decisions: list[ReviewDecisionRecord] = Field(default_factory=list)


class UpdateTaskPacketStatusRequest(BaseModel):
    new_status: str = Field(..., min_length=1, max_length=100)
    reasoning_summary: str = Field(..., min_length=1)


class TaskPacketStatusResponse(BaseModel):
    task_id: str
    previous_status: str
    new_status: str
    updated_at: datetime
    reasoning_summary: str


class CreateReviewDecisionRequest(BaseModel):
    subject_type: str = Field(..., min_length=1, max_length=100)
    subject_id: str = Field(..., min_length=1, max_length=200)
    decision: str = Field(..., min_length=1, max_length=100)
    reasoning_summary: str = Field(..., min_length=1)
    required_next_action: Optional[str] = None
    evidence_links: list[str] = Field(default_factory=list)


class LanePriorityItem(BaseModel):
    id: str
    lane: str
    priority_rank: int
    item_id: str
    title: str
    status: str
    source_surface: str
    notes: Optional[str] = None
    updated_at: datetime


class ImageGuideLinkRecord(BaseModel):
    guide_slug: str
    guide_file: str
    content_id: Optional[str] = None
    line_number: Optional[int] = None
    section_context: Optional[str] = None
    created_at: Optional[datetime] = None


class ImageAssetSummary(BaseModel):
    id: str
    caption: str
    status: str
    sourcing_method: str
    production_tool: Optional[str] = None
    guide_slugs: list[str] = Field(default_factory=list)
    git_path: Optional[str] = None
    storage_bucket: Optional[str] = None
    storage_path: Optional[str] = None
    storage_url: Optional[str] = None
    updated_at: datetime
    latest_validation_artifact_id: Optional[str] = None


class ImageAssetDetail(ImageAssetSummary):
    source_doc: Optional[str] = None
    source_ref: Optional[str] = None
    alt_text: Optional[str] = None
    notes: Optional[str] = None
    sourcing_hint: Optional[str] = None
    file_format: Optional[str] = None
    file_size_bytes: Optional[int] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    figma_file_key: Optional[str] = None
    figma_node_id: Optional[str] = None
    script_path: Optional[str] = None
    quality_tier: Optional[str] = None
    created_at: datetime
    classified_at: Optional[datetime] = None
    produced_at: Optional[datetime] = None
    integrated_at: Optional[datetime] = None
    latest_validation_artifact_summary: Optional[str] = None
    guide_links: list[ImageGuideLinkRecord] = Field(default_factory=list)


class UpdateImageAssetStatusRequest(BaseModel):
    new_status: str = Field(..., min_length=1, max_length=100)
    decision_basis: str = Field(..., min_length=1)


class ImageAssetStatusResponse(BaseModel):
    asset_id: str
    previous_status: str
    new_status: str
    updated_at: datetime
    decision_basis: str


class QueueLocalActionRequest(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=100)
    subject_type: str = Field(..., min_length=1, max_length=100)
    subject_id: str = Field(..., min_length=1, max_length=200)
    request_payload: dict[str, Any]
    task_id: Optional[str] = None
    priority: str = Field(default="normal", min_length=1, max_length=20)
    confirmed_by_user: bool = False


class QueueRenderValidationRequest(BaseModel):
    guide_slug: str = Field(..., min_length=1, max_length=200)
    validation_target: str = Field(..., min_length=1, max_length=200)
    expected_asset_ids: list[str] = Field(default_factory=list)
    task_id: Optional[str] = None
    priority: str = Field(default="normal", min_length=1, max_length=20)


class QueueLocalActionResponse(BaseModel):
    job_id: str
    action_type: str
    status: str
    priority: str
    task_id: Optional[str] = None
    subject_type: str
    subject_id: str
    requested_by: str
    created_at: datetime


class JobRunSummary(BaseModel):
    job_id: str
    action_type: str
    status: str
    subject_type: str
    subject_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_summary: Optional[str] = None


class JobRunDetail(JobRunSummary):
    task_id: Optional[str] = None
    request_payload: dict[str, Any]
    requested_by: str
    claimed_at: Optional[datetime] = None
    claimed_by: Optional[str] = None
    latest_run_id: Optional[str] = None
    latest_runner_id: Optional[str] = None
    started_at: Optional[datetime] = None
    result_json: Optional[dict[str, Any]] = None
    evidence_artifacts: list[str] = Field(default_factory=list)


class ValidationArtifactDetail(BaseModel):
    artifact_id: str
    artifact_type: str
    subject_type: str
    subject_id: str
    title: str
    summary: Optional[str] = None
    artifact_path: Optional[str] = None
    artifact_uri: Optional[str] = None
    artifact_json: Optional[dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime


class AttachCloseoutNoteRequest(BaseModel):
    subject_type: str = Field(..., min_length=1, max_length=100)
    subject_id: str = Field(..., min_length=1, max_length=200)
    note: str = Field(..., min_length=1)


class PlanPreviewRequest(BaseModel):
    task: str = Field(..., min_length=1)
    lane: Optional[str] = None
    action_type: Optional[str] = None
    risk_level: Optional[str] = None
    preferred_model_tier: Optional[str] = None
    requires_local_action: bool = False
    requires_review_decision: bool = True


class PlanPreviewStep(BaseModel):
    step: int
    title: str
    owner: str
    outcome: str


class PlanPreviewResponse(BaseModel):
    recommended_model_tier: str
    workflow: str
    needs_review_gate: bool
    needs_local_action_queue: bool
    summary: str
    steps: list[PlanPreviewStep] = Field(default_factory=list)


class CostEstimateRequest(BaseModel):
    task: str = Field(..., min_length=1)
    preferred_model_tier: str = Field(default="tier-b", min_length=1, max_length=50)
    expected_experts: Optional[int] = Field(default=None, ge=1, le=10)
    requires_review_decision: bool = True
    requires_local_action: bool = False


class CostEstimateResponse(BaseModel):
    task_tokens: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    estimated_duration_seconds: int
    estimated_experts: int
    preferred_model_tier: str