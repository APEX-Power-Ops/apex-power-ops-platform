from dataclasses import dataclass
from datetime import datetime

EVENT_TYPES = frozenset(
    {"resource_viewed", "resource_completed", "assessment_completed", "self_assessment"}
)


@dataclass
class CapturedEvent:
    event_id: str
    user_id: str
    event_type: str
    study_content_id: str | None
    neta_section: str | None
    occurred_at: datetime
    payload: dict
    created_at: datetime
