from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_missing_section_is_400():
    assert client.get("/api/v1/learning/resources").status_code == 422  # FastAPI required-param

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
