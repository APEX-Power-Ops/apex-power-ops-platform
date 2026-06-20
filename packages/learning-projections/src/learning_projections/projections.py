from .db import connect
from .models import ContentProgress, UserNotFoundError


def _require_user(conn, user_id: str) -> None:
    if conn.execute("select 1 from user_profiles where id = %s", (user_id,)).fetchone() is None:
        raise UserNotFoundError(f"user not found: {user_id}")


def _iso(v) -> str | None:
    return v.isoformat() if v is not None else None


def content_progress(user_id: str) -> list[ContentProgress]:
    with connect() as conn:
        _require_user(conn, user_id)
        rows = conn.execute(
            """
            select sc.id::text, sc.title, sc.neta_section_primary,
                   count(*) filter (where e.event_type='resource_viewed')     as view_count,
                   bool_or(e.event_type='resource_completed')                 as is_completed,
                   min(e.occurred_at) as first_seen_at, max(e.occurred_at) as last_activity_at
            from learning_events e
            join study_content sc on sc.id = e.study_content_id
            where e.user_id = %s and e.event_type in ('resource_viewed','resource_completed')
            group by sc.id, sc.title, sc.neta_section_primary
            order by max(e.occurred_at) desc
            """,
            (user_id,),
        ).fetchall()
    return [
        ContentProgress(
            study_content_id=r[0], title=r[1], neta_section=r[2],
            view_count=r[3], is_completed=r[4],
            status="completed" if r[4] else "in_progress",
            first_seen_at=_iso(r[5]), last_activity_at=_iso(r[6]),
        )
        for r in rows
    ]
