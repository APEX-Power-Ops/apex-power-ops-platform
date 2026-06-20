from .db import connect
from .models import (
    AssessmentSummary,
    CompetencyRollup,
    ConceptRef,
    ContentProgress,
    LevelCoverage,
    UserNotFoundError,
)


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


ALL_LEVELS = ["II", "III", "IV"]


def _resolve_level(conn, user_id, level):
    if level is not None:
        return level, "explicit", [level]
    row = conn.execute(
        "select target_certification_level, current_certification_level from user_profiles where id=%s",
        (user_id,),
    ).fetchone()
    target, current = row
    if target is not None:
        return target, "target", [target]
    if current is not None:
        return current, "current", [current]
    return "all", "all", list(ALL_LEVELS)


def competency_rollup(user_id: str, level: str | None = None) -> CompetencyRollup:
    with connect() as conn:
        _require_user(conn, user_id)
        resolved, source, scope = _resolve_level(conn, user_id, level)

        evidence_event_count = conn.execute(
            """select count(*) from learning_events
               where user_id=%s and event_type in ('resource_completed','assessment_completed')
                 and study_content_id is not null""",
            (user_id,),
        ).fetchone()[0]

        # covered ksa_code grouped by level (active maps, level-pinned, orphans dropped by the
        # inner join). NOTE: this is computed across ALL reachable levels; the `scope` loop below
        # is what filters to levels_in_scope -- the SQL is intentionally not scope-pinned.
        covered_rows = conn.execute(
            """
            with evidence as (
              select distinct study_content_id as content_id from learning_events
              where user_id=%s and event_type in ('resource_completed','assessment_completed')
                and study_content_id is not null
            ),
            covered as (
              select distinct k.ksa_code, k.certification_level::text as lvl
              from evidence ev
              join content_concept_links ccl on ccl.content_id = ev.content_id
              join edition_ksa_map ekm on ekm.concept_id = ccl.concept_id and ekm.is_active
              join ksas k on k.ksa_code = ekm.ksa_code and k.certification_level::text = ekm.level
            )
            select lvl, count(distinct ksa_code) from covered group by lvl
            """,
            (user_id,),
        ).fetchall()
        covered_by_level = {lvl: n for lvl, n in covered_rows}

        totals = dict(
            conn.execute(
                "select certification_level::text, count(distinct ksa_code) from ksas group by 1"
            ).fetchall()
        )

        engaged = conn.execute(
            """
            with evidence as (
              select distinct study_content_id as content_id from learning_events
              where user_id=%s and event_type in ('resource_completed','assessment_completed')
                and study_content_id is not null
            )
            select distinct c.concept_id, c.concept_description
            from evidence ev
            join content_concept_links ccl on ccl.content_id = ev.content_id
            join concepts c on c.concept_id = ccl.concept_id
            order by c.concept_id
            """,
            (user_id,),
        ).fetchall()

    coverage = []
    for lvl in scope:
        total = totals.get(lvl, 0)
        cov = covered_by_level.get(lvl, 0)
        pct = round(100.0 * cov / total, 1) if total > 0 else None
        coverage.append(LevelCoverage(level=lvl, total_ksas_at_level=total, covered_ksas=cov, coverage_percent=pct))

    return CompetencyRollup(
        user_id=user_id, resolved_level=resolved, level_source=source, levels_in_scope=scope,
        evidence_event_count=evidence_event_count, coverage=coverage,
        engaged_concepts=[ConceptRef(concept_id=r[0], concept_description=r[1]) for r in engaged],
    )
