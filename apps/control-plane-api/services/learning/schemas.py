from datetime import datetime

from pydantic import BaseModel


class ResolvedResourceOut(BaseModel):
    resource_type: str
    title: str
    source: str
    reference: dict
    is_primary: bool
    is_mandatory: bool
    cert_level: str | None = None
    score: float
    why: str


class ResourcesContext(BaseModel):
    neta_section: str
    level: str | None = None
    limit: int


class ResourcesResponse(BaseModel):
    context: ResourcesContext
    resources: list[ResolvedResourceOut]


class SectionsResponse(BaseModel):
    sections: list[str]


class EventIn(BaseModel):
    user_id: str
    event_type: str
    study_content_id: str | None = None
    neta_section: str | None = None
    payload: dict = {}


class EventOut(BaseModel):
    event_id: str
    user_id: str
    event_type: str
    study_content_id: str | None = None
    neta_section: str | None = None
    occurred_at: datetime
    payload: dict
    created_at: datetime


class EventCreatedResponse(BaseModel):
    event: EventOut


class EventsResponse(BaseModel):
    events: list[EventOut]


class UsersResponse(BaseModel):
    users: list[dict]


class ContentProgressOut(BaseModel):
    study_content_id: str
    title: str | None = None
    neta_section: str | None = None
    view_count: int
    is_completed: bool
    status: str
    first_seen_at: str | None = None
    last_activity_at: str | None = None


class AssessmentSummaryOut(BaseModel):
    study_content_id: str
    title: str | None = None
    neta_section: str | None = None
    assessment_attempts: int
    latest_score_percent: float | None = None
    mean_score_percent: float | None = None
    self_assessment_count: int
    latest_confidence: int | None = None
    mean_confidence: float | None = None
    last_activity_at: str | None = None


class ConceptRefOut(BaseModel):
    concept_id: str
    concept_description: str | None = None


class LevelCoverageOut(BaseModel):
    level: str
    total_ksas_at_level: int
    covered_ksas: int
    coverage_percent: float | None = None


class CompetencyRollupOut(BaseModel):
    user_id: str
    resolved_level: str
    level_source: str
    levels_in_scope: list[str]
    evidence_event_count: int
    coverage: list[LevelCoverageOut]
    engaged_concepts: list[ConceptRefOut]


class CohortAggregateOut(BaseModel):
    level: str | None = None
    user_count: int
    mean_completed_content: float
    mean_latest_score: float | None = None
    scored_user_count: int
    mean_coverage_percent: float | None = None
    coverage_user_count: int


class ProgressResponse(BaseModel):
    items: list[ContentProgressOut]


class AssessmentsResponse(BaseModel):
    items: list[AssessmentSummaryOut]
