"""control-plane-api Slice 2b projection routes. LEARNING_DEV_DSN is pinned to learning_test by
the run command (the mini-graph fixture must be applied there first)."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
U_TARGET = "11111111-0000-0000-0000-000000000001"


def test_progress_ok():
    r = client.get("/api/v1/learning/progress", params={"user_id": U_TARGET})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 2


def test_progress_missing_user_400():
    assert client.get("/api/v1/learning/progress").status_code == 400


def test_progress_bad_uuid_400():
    assert client.get("/api/v1/learning/progress", params={"user_id": "nope"}).status_code == 400


def test_progress_unknown_user_404():
    r = client.get("/api/v1/learning/progress", params={"user_id": "99999999-9999-9999-9999-999999999999"})
    assert r.status_code == 404


def test_competency_ok():
    r = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET})
    body = r.json()
    assert r.status_code == 200
    assert body["resolved_level"] == "II" and body["coverage"][0]["covered_ksas"] == 2


def test_competency_bad_level_400():
    assert client.get("/api/v1/learning/competency",
                      params={"user_id": U_TARGET, "level": "Z"}).status_code == 400


def test_cohort_ok():
    r = client.get("/api/v1/learning/cohort")
    assert r.status_code == 200
    assert r.json()["user_count"] == 4


U_NONE = "11111111-0000-0000-0000-000000000004"
UNKNOWN = "99999999-9999-9999-9999-999999999999"


def test_assessments_empty_200_for_view_only_user():
    # U_none has only a resource_viewed event -> known user, zero assessments -> 200 + []
    r = client.get("/api/v1/learning/assessments", params={"user_id": U_NONE})
    assert r.status_code == 200 and r.json()["items"] == []


def test_assessments_unknown_user_404():
    assert client.get("/api/v1/learning/assessments", params={"user_id": UNKNOWN}).status_code == 404


def test_competency_unknown_user_404():
    assert client.get("/api/v1/learning/competency", params={"user_id": UNKNOWN}).status_code == 404


def test_competency_is_bare_object_not_wrapped():
    # competency/cohort intentionally return the bare *Out, not an {items: [...]} wrapper
    body = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET}).json()
    assert "items" not in body and "coverage" in body


def test_competency_level_param_passthrough():
    r = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET, "level": "I"})
    body = r.json()
    assert r.status_code == 200
    assert body["resolved_level"] == "I" and body["coverage"][0]["coverage_percent"] is None


def test_cohort_level_param_passthrough():
    r = client.get("/api/v1/learning/cohort", params={"level": "II"})
    assert r.status_code == 200
    assert r.json()["mean_coverage_percent"] == 37.5


def test_learning_routes_absent_when_guard_disabled():
    # spec error matrix: guard env unset -> router not registered -> 404. The guard runs at
    # main-import time, so monkeypatching after `from main import app` is too late -- run an
    # import-isolated subprocess with the learning DSN/PGPASSWORD cleared.
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    env.pop("LEARNING_DEV_DSN", None)
    env.pop("LEARNING_DEV_PGPASSWORD", None)
    snippet = (
        "from fastapi.testclient import TestClient; from main import app; "
        "c = TestClient(app); "
        "r = c.get('/api/v1/learning/progress', params={'user_id': '11111111-0000-0000-0000-000000000001'}); "
        "assert r.status_code == 404, r.status_code; print('GUARD_OK')"
    )
    api_dir = os.path.dirname(os.path.dirname(__file__))  # apps/control-plane-api
    proc = subprocess.run([sys.executable, "-c", snippet], cwd=api_dir, env=env,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "GUARD_OK" in proc.stdout
