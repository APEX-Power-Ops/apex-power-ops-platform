from learning_projections import competency_rollup

U_TARGET = "11111111-0000-0000-0000-000000000001"
U_CURRENT = "11111111-0000-0000-0000-000000000002"
U_ALL = "11111111-0000-0000-0000-000000000003"
U_NONE = "11111111-0000-0000-0000-000000000004"


def _cov(r):
    return {c.level: c for c in r.coverage}


def test_target_level_ii():
    r = competency_rollup(U_TARGET)
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("II", "target", ["II"])
    c = _cov(r)["II"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (4, 2, 50.0)
    assert r.evidence_event_count == 2
    assert {c.concept_id for c in r.engaged_concepts} == {"concept-1", "concept-2"}


def test_current_orphan_and_inactive_excluded():
    r = competency_rollup(U_CURRENT)
    assert (r.resolved_level, r.level_source) == ("III", "current")
    c = _cov(r)["III"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (3, 2, 66.7)
    # orphan-only concept-3 appears in engaged_concepts though it adds 0 covered ksas:
    assert {c.concept_id for c in r.engaged_concepts} == {"concept-1", "concept-2", "concept-3"}
    assert r.evidence_event_count == 3


def test_all_fallback():
    r = competency_rollup(U_ALL)
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("all", "all", ["II", "III", "IV"])
    c = _cov(r)
    assert (c["II"].covered_ksas, c["II"].coverage_percent) == (2, 50.0)
    assert (c["III"].covered_ksas, c["III"].coverage_percent) == (2, 66.7)
    assert (c["IV"].total_ksas_at_level, c["IV"].covered_ksas, c["IV"].coverage_percent) == (2, 0, 0.0)


def test_explicit_level_i_is_null_coverage():
    r = competency_rollup(U_TARGET, level="I")
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("I", "explicit", ["I"])
    c = _cov(r)["I"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (0, 0, None)


def test_no_evidence_zero():
    r = competency_rollup(U_NONE)
    c = _cov(r)["II"]
    assert (c.covered_ksas, c.coverage_percent) == (0, 0.0)
    assert r.evidence_event_count == 0 and r.engaged_concepts == []
