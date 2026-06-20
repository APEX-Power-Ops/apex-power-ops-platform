import pytest

from learning_projections import UserNotFoundError, content_progress

U_TARGET = "11111111-0000-0000-0000-000000000001"
C1 = "22222222-0000-0000-0000-000000000001"
C2 = "22222222-0000-0000-0000-000000000002"


def _by_id(rows):
    return {r.study_content_id: r for r in rows}


def test_content_progress_target():
    rows = _by_id(content_progress(U_TARGET))
    assert set(rows) == {C1, C2}
    assert rows[C1].view_count == 1 and rows[C1].is_completed and rows[C1].status == "completed"
    assert rows[C2].view_count == 1 and not rows[C2].is_completed and rows[C2].status == "in_progress"
    assert rows[C1].title == "Content 1" and rows[C1].neta_section == "7.1"


def test_content_progress_unknown_user_raises():
    with pytest.raises(UserNotFoundError):
        content_progress("99999999-9999-9999-9999-999999999999")
