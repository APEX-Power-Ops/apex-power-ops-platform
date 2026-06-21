import uuid as _uuid

from fastapi import APIRouter, HTTPException, Query, status

from learning_capture import CaptureError, list_events, list_users, record_event
from learning_projections import (
    assessment_summary, cohort_aggregate, competency_rollup, content_progress, UserNotFoundError,
)
from learning_resolver import list_sections, resolve

from .schemas import (
    AssessmentsResponse,
    AssessmentSummaryOut,
    CohortAggregateOut,
    CompetencyRollupOut,
    ConceptRefOut,
    ContentProgressOut,
    EventCreatedResponse,
    EventIn,
    EventOut,
    EventsResponse,
    LevelCoverageOut,
    ProgressResponse,
    ResolvedResourceOut,
    ResourcesContext,
    ResourcesResponse,
    SectionsResponse,
    UsersResponse,
)

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/resources", response_model=ResourcesResponse)
def get_resources(
    neta_section: str | None = Query(default=None),
    level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResourcesResponse:
    if not neta_section or not neta_section.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="neta_section is required")
    if level is not None and level not in {"II", "III", "IV"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="level must be II, III, or IV")
    section = neta_section.strip()
    items = resolve(section, level=level, limit=limit)
    return ResourcesResponse(
        context=ResourcesContext(neta_section=section, level=level, limit=limit),
        resources=[ResolvedResourceOut(**vars(r)) for r in items],
    )


@router.get("/sections", response_model=SectionsResponse)
def get_sections(limit: int = Query(default=500, ge=1, le=2000)) -> SectionsResponse:
    return SectionsResponse(sections=list_sections(limit=limit))


@router.post("/events", response_model=EventCreatedResponse, status_code=status.HTTP_201_CREATED)
def post_event(body: EventIn) -> EventCreatedResponse:
    try:
        ev = record_event(
            body.user_id, body.event_type,
            study_content_id=body.study_content_id,
            neta_section=body.neta_section,
            payload=body.payload,
        )
    except CaptureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return EventCreatedResponse(event=EventOut(**vars(ev)))


@router.get("/events", response_model=EventsResponse)
def get_events(
    user_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> EventsResponse:
    rows = list_events(user_id=user_id, limit=limit)
    return EventsResponse(events=[EventOut(**vars(r)) for r in rows])


@router.get("/users", response_model=UsersResponse)
def get_users(limit: int = Query(default=100, ge=1, le=500)) -> UsersResponse:
    return UsersResponse(users=list_users(limit=limit))


def _valid_user(user_id: str | None) -> str:
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    try:
        _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id must be a UUID")
    return user_id


def _valid_level(level: str | None) -> str | None:
    if level is not None and level not in {"I", "II", "III", "IV"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="level must be I, II, III, or IV")
    return level


@router.get("/progress", response_model=ProgressResponse)
def get_progress(user_id: str | None = Query(default=None)) -> ProgressResponse:
    uid = _valid_user(user_id)
    try:
        rows = content_progress(uid)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return ProgressResponse(items=[ContentProgressOut(**vars(r)) for r in rows])


@router.get("/assessments", response_model=AssessmentsResponse)
def get_assessments(user_id: str | None = Query(default=None)) -> AssessmentsResponse:
    uid = _valid_user(user_id)
    try:
        rows = assessment_summary(uid)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return AssessmentsResponse(items=[AssessmentSummaryOut(**vars(r)) for r in rows])


@router.get("/competency", response_model=CompetencyRollupOut)
def get_competency(user_id: str | None = Query(default=None),
                   level: str | None = Query(default=None)) -> CompetencyRollupOut:
    uid = _valid_user(user_id)
    _valid_level(level)
    try:
        roll = competency_rollup(uid, level=level)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return CompetencyRollupOut(
        user_id=roll.user_id, resolved_level=roll.resolved_level, level_source=roll.level_source,
        levels_in_scope=roll.levels_in_scope, evidence_event_count=roll.evidence_event_count,
        coverage=[LevelCoverageOut(**vars(c)) for c in roll.coverage],
        engaged_concepts=[ConceptRefOut(**vars(c)) for c in roll.engaged_concepts],
    )


@router.get("/cohort", response_model=CohortAggregateOut)
def get_cohort(level: str | None = Query(default=None)) -> CohortAggregateOut:
    _valid_level(level)
    return CohortAggregateOut(**vars(cohort_aggregate(level=level)))
