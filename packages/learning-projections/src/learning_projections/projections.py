from .db import connect
from .models import AssessmentSummary, ContentProgress, UserNotFoundError


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


def assessment_summary(user_id: str) -> list[AssessmentSummary]:
    with connect() as conn:
        _require_user(conn, user_id)
        rows = conn.execute(
            """
            select sc.id::text, sc.title, sc.neta_section_primary,
              count(*) filter (where e.event_type='assessment_completed') as assessment_attempts,
              (array_agg((e.payload->>'score_percent')::numeric order by e.occurred_at desc)
                 filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent'))[1] as latest_score,
              avg((e.payload->>'score_percent')::numeric)
                 filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent') as mean_score,
              count(*) filter (where e.event_type='self_assessment') as self_count,
              (array_agg((e.payload->>'confidence')::int order by e.occurred_at desc)
                 filter (where e.event_type='self_assessment' and e.payload ? 'confidence'))[1] as latest_conf,
              avg((e.payload->>'confidence')::numeric)
                 filter (where e.event_type='self_assessment' and e.payload ? 'confidence') as mean_conf,
              max(e.occurred_at) as last_activity_at
            from learning_events e
            join study_content sc on sc.id = e.study_content_id
            where e.user_id = %s and e.event_type in ('assessment_completed','self_assessment')
            group by sc.id, sc.title, sc.neta_section_primary
            order by max(e.occurred_at) desc
            """,
            (user_id,),
        ).fetchall()
    return [
        AssessmentSummary(
            study_content_id=r[0], title=r[1], neta_section=r[2],
            assessment_attempts=r[3],
            latest_score_percent=float(r[4]) if r[4] is not None else None,
            mean_score_percent=round(float(r[5]), 1) if r[5] is not None else None,
            self_assessment_count=r[6],
            latest_confidence=int(r[7]) if r[7] is not None else None,
            mean_confidence=round(float(r[8]), 1) if r[8] is not None else None,
            last_activity_at=_iso(r[9]),
        )
        for r in rows
    ]
