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
