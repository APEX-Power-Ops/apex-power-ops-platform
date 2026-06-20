from fastapi import APIRouter, HTTPException, Query, status

from learning_capture import CaptureError, list_events, list_users, record_event
from learning_resolver import list_sections, resolve

from .schemas import (
    EventCreatedResponse,
    EventIn,
    EventOut,
    EventsResponse,
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
