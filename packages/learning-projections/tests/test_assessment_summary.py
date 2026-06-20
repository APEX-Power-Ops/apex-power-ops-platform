from learning_projections import assessment_summary

U_TARGET = "11111111-0000-0000-0000-000000000001"
C1 = "22222222-0000-0000-0000-000000000001"


def test_assessment_summary_target():
    rows = assessment_summary(U_TARGET)
    assert len(rows) == 1
    a = rows[0]
    assert a.study_content_id == C1
    assert a.assessment_attempts == 1
    assert a.latest_score_percent == 80 and a.mean_score_percent == 80
    assert a.self_assessment_count == 1
    assert a.latest_confidence == 4 and a.mean_confidence == 4
    # the section-only self_assessment (NULL study_content_id) is excluded: still 1 row and
    # self_assessment_count stays 1 (would be 2 / a null row if the null-content event leaked in).
    assert all(r.study_content_id is not None for r in rows)
