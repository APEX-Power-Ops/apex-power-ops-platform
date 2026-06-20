"""control-plane-api learning capture routes (Slice 2a). The route layer calls the
learning-capture package, which writes the learning_test DB (LEARNING_DEV_DSN is pinned to
learning_test by the run command). A valid DATABASE_URL must be importable for config.py.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def test_post_event_returns_201():
    r = client.post("/api/v1/learning/events", json={
        "user_id": USER, "event_type": "resource_viewed",
        "study_content_id": CONTENT, "neta_section": "7.2.1.1",
    })
    assert r.status_code == 201
    body = r.json()["event"]
    assert body["event_type"] == "resource_viewed"
    assert body["user_id"] == USER


def test_post_event_bad_type_is_400():
    r = client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "bogus"})
    assert r.status_code == 400


def test_post_event_unknown_user_is_400():
    r = client.post("/api/v1/learning/events",
                    json={"user_id": "22222222-2222-2222-2222-222222222222", "event_type": "resource_viewed"})
    assert r.status_code == 400


def test_post_self_assessment_requires_confidence():
    bad = client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "self_assessment"})
    assert bad.status_code == 400
    ok = client.post("/api/v1/learning/events",
                     json={"user_id": USER, "event_type": "self_assessment", "payload": {"confidence": 4}})
    assert ok.status_code == 201
    assert ok.json()["event"]["payload"]["confidence"] == 4


def test_get_events_reads_back():
    client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "resource_completed"})
    r = client.get("/api/v1/learning/events", params={"user_id": USER, "limit": 10})
    assert r.status_code == 200
    events = r.json()["events"]
    assert len(events) >= 1
    assert {"event_id", "event_type", "user_id"} <= set(events[0].keys())


def test_get_users_lists_seed_user():
    r = client.get("/api/v1/learning/users")
    assert r.status_code == 200
    assert any(u["id"] == USER for u in r.json()["users"])
