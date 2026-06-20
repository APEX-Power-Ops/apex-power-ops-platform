"""Capture path: append events to the learning_dev learning_events ledger. INSERT/SELECT only
(the DB trigger backs the append-only invariant). Payload shape per event_type is enforced here
(the design assigns payload validation to the package)."""
from numbers import Real

from psycopg.types.json import Json

from .db import connect
from .models import EVENT_TYPES, CapturedEvent

_COLS = ("event_id", "user_id", "event_type", "study_content_id",
         "neta_section", "occurred_at", "payload", "created_at")

_INSERT = (
    "insert into learning_events (user_id, event_type, study_content_id, neta_section, payload) "
    "values (%(user_id)s::uuid, %(event_type)s, %(study_content_id)s::uuid, %(neta_section)s, %(payload)s) "
    "returning " + ", ".join(_COLS)
)


class CaptureError(ValueError):
    """Invalid capture request (unknown event_type / missing referenced row / bad payload)."""


def _validate_payload(event_type, payload):
    if event_type == "assessment_completed":
        score = payload.get("score_percent")
        if not isinstance(score, Real) or isinstance(score, bool) or not (0 <= float(score) <= 100):
            raise CaptureError("assessment_completed requires numeric payload.score_percent in [0,100]")
    elif event_type == "self_assessment":
        conf = payload.get("confidence")
        if not isinstance(conf, int) or isinstance(conf, bool) or not (1 <= conf <= 5):
            raise CaptureError("self_assessment requires int payload.confidence in [1,5]")


def _row_to_event(r) -> CapturedEvent:
    (event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at) = r
    return CapturedEvent(
        event_id=str(event_id),
        user_id=str(user_id),
        event_type=event_type,
        study_content_id=str(study_content_id) if study_content_id is not None else None,
        neta_section=neta_section,
        occurred_at=occurred_at,
        payload=payload or {},
        created_at=created_at,
    )


def record_event(user_id, event_type, *, study_content_id=None, neta_section=None, payload=None) -> CapturedEvent:
    if event_type not in EVENT_TYPES:
        raise CaptureError(f"unknown event_type {event_type!r}; allowed: {sorted(EVENT_TYPES)}")
    payload = payload or {}
    _validate_payload(event_type, payload)
    with connect() as conn:
        if conn.execute("select 1 from user_profiles where id = %s::uuid", (user_id,)).fetchone() is None:
            raise CaptureError(f"no such user_profiles.id {user_id!r}")
        if study_content_id is not None and \
                conn.execute("select 1 from study_content where id = %s::uuid", (study_content_id,)).fetchone() is None:
            raise CaptureError(f"no such study_content.id {study_content_id!r}")
        row = conn.execute(_INSERT, {
            "user_id": user_id,
            "event_type": event_type,
            "study_content_id": study_content_id,
            "neta_section": neta_section,
            "payload": Json(payload),
        }).fetchone()
    return _row_to_event(row)


def list_events(user_id=None, limit=50) -> list[CapturedEvent]:
    sql = "select " + ", ".join(_COLS) + " from learning_events "
    with connect() as conn:
        if user_id is not None:
            rows = conn.execute(
                sql + "where user_id = %s::uuid order by occurred_at desc, event_id limit %s",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(sql + "order by occurred_at desc, event_id limit %s", (limit,)).fetchall()
    return [_row_to_event(r) for r in rows]


def list_users(limit=100) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("select id, email from user_profiles order by email limit %s", (limit,)).fetchall()
    return [{"id": str(i), "email": e} for i, e in rows]
