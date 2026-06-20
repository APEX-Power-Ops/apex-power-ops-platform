from dataclasses import dataclass


class ProjectionError(Exception):
    """Base error for the projection engine."""


class UserNotFoundError(ProjectionError):
    """Raised when a user_id is absent from user_profiles (route maps to 404)."""


@dataclass
class ContentProgress:
    study_content_id: str
    title: str
    neta_section: str | None
    view_count: int
    is_completed: bool
    status: str
    first_seen_at: str | None
    last_activity_at: str | None


@dataclass
class AssessmentSummary:
    study_content_id: str
    title: str
    neta_section: str | None
    assessment_attempts: int
    latest_score_percent: float | None
    mean_score_percent: float | None
    self_assessment_count: int
    latest_confidence: int | None
    mean_confidence: float | None
    last_activity_at: str | None


@dataclass
class ConceptRef:
    concept_id: str
    concept_description: str | None


@dataclass
class LevelCoverage:
    level: str
    total_ksas_at_level: int
    covered_ksas: int
    coverage_percent: float | None


@dataclass
class CompetencyRollup:
    user_id: str
    resolved_level: str
    level_source: str
    levels_in_scope: list[str]
    evidence_event_count: int
    coverage: list[LevelCoverage]
    engaged_concepts: list[ConceptRef]


@dataclass
class CohortAggregate:
    level: str | None
    user_count: int
    mean_completed_content: float
    mean_latest_score: float | None
    scored_user_count: int
    mean_coverage_percent: float | None
    coverage_user_count: int
