import pytest

from learning_capture import CaptureError, list_events, list_users, record_event
from learning_capture.models import CapturedEvent
from tests.conftest import CONTENT, USER


def test_record_event_returns_captured_event():
    ev = record_event(USER, "resource_viewed", study_content_id=CONTENT, neta_section="7.2.1.1")
    assert isinstance(ev, CapturedEvent)
    assert ev.event_id
    assert ev.user_id == USER
    assert ev.event_type == "resource_viewed"
    assert ev.study_content_id == CONTENT
    assert ev.neta_section == "7.2.1.1"


def test_record_event_rejects_unknown_type():
    with pytest.raises(CaptureError):
        record_event(USER, "bogus")


def test_record_event_rejects_unknown_user():
    with pytest.raises(CaptureError):
        record_event("22222222-2222-2222-2222-222222222222", "resource_viewed")


def test_record_event_rejects_unknown_content():
    with pytest.raises(CaptureError):
        record_event(USER, "resource_viewed", study_content_id="33333333-3333-3333-3333-333333333333")


def test_assessment_requires_score_percent():
    with pytest.raises(CaptureError):
        record_event(USER, "assessment_completed")                       # no payload
    with pytest.raises(CaptureError):
        record_event(USER, "assessment_completed", payload={"score_percent": 150})  # out of range
    ev = record_event(USER, "assessment_completed", payload={"score_percent": 80})
    assert ev.payload["score_percent"] == 80


def test_self_assessment_requires_confidence():
    with pytest.raises(CaptureError):
        record_event(USER, "self_assessment")                            # no payload
    with pytest.raises(CaptureError):
        record_event(USER, "self_assessment", payload={"confidence": 9})  # out of range
    ev = record_event(USER, "self_assessment", payload={"confidence": 3})
    assert ev.payload["confidence"] == 3


def test_list_events_filters_by_user_and_orders_desc():
    record_event(USER, "resource_viewed")
    record_event(USER, "resource_completed")
    rows = list_events(user_id=USER, limit=2)
    assert len(rows) == 2
    assert rows[0].occurred_at >= rows[1].occurred_at


def test_list_users_returns_seed_user():
    assert any(u["id"] == USER for u in list_users())
