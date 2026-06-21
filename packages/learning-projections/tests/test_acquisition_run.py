import pathlib
import psycopg
import pytest
from learning_projections.db import dsn as _dsn
from learning_projections import (content_progress, assessment_summary, competency_rollup,
                                   cohort_aggregate)
from learning_capture.acquisition import record_acquired_event

HERE = pathlib.Path(__file__).parent
REPO = HERE.parents[2]
MIG = REPO / "infra" / "database" / "migrations" / "learning"
PREREQ = HERE / "projections_prereq.sql"
MIG_002 = MIG / "002_learning_events.sql"
EVENTS = HERE / "projections_events_seed.sql"
ACQ_PREREQ = HERE / "acquisition_prereq.sql"
PROVISION = REPO / "scripts" / "learning" / "slice2d_provision_cohort.sql"

COHORT = "a0000000-2d00-4000-8000-000000000001"
NEG_NOEV = "a0000000-2d00-4000-8000-000000000002"
NEG_LVL1 = "a0000000-2d00-4000-8000-000000000003"
C1 = "22222222-0000-0000-0000-000000000001"   # concept-1 (II SA1,SA2) + concept-2 (III SB1,SB2)
C2 = "22222222-0000-0000-0000-000000000002"   # concept-3 -> orphan only (progress, not competency)
ENV = dict(acquisition_run_id="slice2d-rehearsal-01", source_surface="cli",
           observed_by="JS", evidence_ref="runbook#run01", data_fidelity="rehearsal")


def _apply(*paths):
    with psycopg.connect(_dsn(), autocommit=True) as c:
        for p in paths:
            c.execute(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _acq(_fixture):
    # ISOLATED rebuild WITHOUT the 12-event seed so cohort numbers are absolute + exactly pinnable.
    # Active users after this = 4 seed (user9 is inactive) + 2 negative-control + 1 cohort = 7.
    _apply(PREREQ, MIG_002, ACQ_PREREQ, PROVISION)
    yield
    # restore the standard seeded state for the other projection test modules in this session.
    _apply(PREREQ, MIG_002, EVENTS)


def _scalar(sql, *args):
    with psycopg.connect(_dsn(), autocommit=True) as c:
        return c.execute(sql, args).fetchone()


def test_rehearsal_run_moves_all_four_read_models_to_manifest():
    # replay the rehearsal sequence through the guarded helper (all events content-bound)
    record_acquired_event(user_id=COHORT, event_type="resource_viewed", study_content_id=C2,
                          neta_section="7.2", **ENV)                        # in_progress on C2
    record_acquired_event(user_id=COHORT, event_type="resource_viewed", study_content_id=C1,
                          neta_section="7.1", **ENV)
    record_acquired_event(user_id=COHORT, event_type="resource_completed", study_content_id=C1,
                          neta_section="7.1", **ENV)                        # completed + competency
    record_acquired_event(user_id=COHORT, event_type="assessment_completed", study_content_id=C1,
                          neta_section="7.1", score_percent=88, **ENV)

    # --- content_progress: C1 completed (view_count 1), C2 in_progress ---
    progress = {p.study_content_id: p for p in content_progress(COHORT)}
    assert progress[C1].status == "completed" and progress[C1].is_completed is True
    assert progress[C1].view_count == 1
    assert progress[C2].status == "in_progress" and progress[C2].is_completed is False

    # --- assessment_summary: latest 88 on C1, one attempt ---
    asmt = {a.study_content_id: a for a in assessment_summary(COHORT)}
    assert asmt[C1].latest_score_percent == 88.0 and asmt[C1].assessment_attempts == 1

    # --- competency_rollup: III, total 3, covered 2, pct 66.7, evidence 2 ---
    comp = competency_rollup(COHORT)
    assert comp.resolved_level == "III" and comp.level_source == "target"
    iii = [lc for lc in comp.coverage if lc.level == "III"][0]
    assert iii.total_ksas_at_level == 3
    assert iii.covered_ksas == 2
    assert iii.coverage_percent == 66.7
    assert comp.evidence_event_count == 2   # resource_completed + assessment_completed on C1

    # --- independent KSA-code manifest (the engine exposes only a count, not the set) ---
    codes = _scalar(
        """select array_agg(distinct k.ksa_code order by k.ksa_code)
           from learning_events le
           join content_concept_links ccl on ccl.content_id = le.study_content_id
           join edition_ksa_map ekm on ekm.concept_id = ccl.concept_id and ekm.is_active
           join ksas k on k.ksa_code = ekm.ksa_code and k.certification_level::text = ekm.level
           where le.user_id = %s and le.event_type in ('resource_completed','assessment_completed')
             and le.study_content_id is not null and k.certification_level::text = 'III'""", COHORT)[0]
    assert codes == ["SB1", "SB2"]

    # --- cohort_aggregate(III): exact absolute manifest over the 7 active users ---
    cohort = cohort_aggregate(level="III")
    assert cohort.user_count == 7
    assert cohort.mean_completed_content == 0.1      # 1 completed content / 7 users
    assert cohort.scored_user_count == 1
    assert cohort.mean_latest_score == 88.0
    assert cohort.coverage_user_count == 7           # every active user has non-null III coverage
    assert cohort.mean_coverage_percent == 9.5       # (66.7 + 0.0*6) / 7

    # --- provenance envelope present on EVERY run event; occurred_at ~ created_at (no backdating) ---
    with psycopg.connect(_dsn(), autocommit=True) as c:
        rows = c.execute(
            "select payload, extract(epoch from (occurred_at - created_at)) "
            "from learning_events where user_id=%s", (COHORT,)).fetchall()
    assert len(rows) == 4
    for payload, drift in rows:
        assert all(payload.get(k) for k in ("acquisition_run_id", "source_surface", "observed_by",
                                            "evidence_ref", "data_fidelity"))
        assert payload["acquisition_run_id"] == "slice2d-rehearsal-01"
        assert abs(drift) < 2            # server now() for both timestamps -> no client backdating


def test_negative_controls():
    neg = competency_rollup(NEG_NOEV)         # leveled, no content-linked evidence -> 0 / 0.0
    iii = [lc for lc in neg.coverage if lc.level == "III"][0]
    assert iii.covered_ksas == 0 and iii.coverage_percent == 0.0
    lvl1 = competency_rollup(NEG_LVL1)        # Level I -> 0 KSAs -> null coverage
    i = [lc for lc in lvl1.coverage if lc.level == "I"][0]
    assert i.total_ksas_at_level == 0 and i.coverage_percent is None
