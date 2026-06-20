from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_missing_section_is_400():
    assert client.get("/api/v1/learning/resources").status_code == 400


def test_blank_section_is_400():
    assert client.get("/api/v1/learning/resources", params={"neta_section": "   "}).status_code == 400


def test_invalid_level_is_400():
    r = client.get("/api/v1/learning/resources", params={"neta_section": "7.2.1.1", "level": "banana"})
    assert r.status_code == 400


def test_sections_endpoint_lists_known_section():
    r = client.get("/api/v1/learning/sections")
    assert r.status_code == 200
    assert "7.2.1.1" in r.json()["sections"]


def test_learning_routes_guarded_by_env(monkeypatch):
    from main import _learning_routes_enabled
    monkeypatch.delenv("LEARNING_DEV_DSN", raising=False)
    monkeypatch.delenv("LEARNING_DEV_PGPASSWORD", raising=False)
    assert _learning_routes_enabled() is False
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=learning_dev")
    assert _learning_routes_enabled() is True


def test_unknown_section_returns_empty_200():
    r = client.get("/api/v1/learning/resources", params={"neta_section": "9.9.9.9-nope"})
    assert r.status_code == 200
    body = r.json()
    assert body["context"]["neta_section"] == "9.9.9.9-nope"
    assert body["resources"] == []

def test_known_section_returns_ranked_resources():
    # 7.2.1.1 has curated links in the frozen baseline.
    r = client.get("/api/v1/learning/resources", params={"neta_section": "7.2.1.1", "limit": 5})
    assert r.status_code == 200
    res = r.json()["resources"]
    assert 0 < len(res) <= 5
    assert {"resource_type", "title", "source", "score"} <= set(res[0].keys())
    assert res == sorted(res, key=lambda x: -x["score"])
