from learning_projections import cohort_aggregate


def test_cohort_no_level():
    a = cohort_aggregate()
    assert a.user_count == 4                      # active only (U_inactive excluded)
    assert a.mean_completed_content == 1.0        # (1+2+1+0)/4
    assert a.mean_latest_score == 85.0 and a.scored_user_count == 2
    assert a.mean_coverage_percent == 38.9 and a.coverage_user_count == 3   # U_all 'all' excluded


def test_cohort_explicit_level_ii():
    a = cohort_aggregate(level="II")
    assert a.coverage_user_count == 4
    assert a.mean_coverage_percent == 37.5        # (50+50+50+0)/4


def test_cohort_level_i_degenerate():
    a = cohort_aggregate(level="I")
    assert a.mean_coverage_percent is None and a.coverage_user_count == 0
    assert a.mean_completed_content == 1.0 and a.mean_latest_score == 85.0
