"""Manufacturer-display contract tests for NETA selector endpoints."""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/test")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app


class FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class FakeResult:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = [FakeRow(row) for row in (rows or [])]
        self._scalar_value = scalar_value

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._scalar_value


class FakeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in manufacturer-display test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def _assert_mfr_alias_joined(sql: str, join_key: str) -> None:
    assert "LEFT JOIN tcc.mfr_aliases a ON a.ep_mfr_name = " in sql
    assert join_key in sql
    assert "COALESCE(a.etap_mfr_name" in sql


def test_cascade_manufacturers_surface_display_names(client):
    fake_db = FakeDb([
        FakeResult(scalar_value=4),
        FakeResult(rows=[
            {
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "manufacturer_display": "General Electric",
                "trip_type_count": 2,
            },
            {
                "manufacturer_id": 10,
                "manufacturer_name": "Eaton",
                "manufacturer_display": "Eaton",
                "trip_type_count": 2,
            },
        ]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        body = resp.json()
        assert body["manufacturers"][0] == {
            "manufacturer_id": 9,
            "manufacturer_name": "GE",
            "manufacturer_display": "General Electric",
            "trip_type_count": 2,
        }
        assert body["manufacturers"][1]["manufacturer_display"] == body["manufacturers"][1]["manufacturer_name"]
        _assert_mfr_alias_joined(fake_db.calls[1]["statement"], "v.manufacturer_name")
    finally:
        app.dependency_overrides.clear()


def test_breaker_cascade_manufacturers_surface_display_names(client):
    fake_db = FakeDb([
        FakeResult(scalar_value=5),
        FakeResult(rows=[
            {
                "manufacturer_id": 21,
                "manufacturer_name": "Cutler Hammer",
                "manufacturer_display": "Cutler-Hammer",
                "breaker_count": 3,
            },
            {
                "manufacturer_id": 10,
                "manufacturer_name": "Eaton",
                "manufacturer_display": "Eaton",
                "breaker_count": 2,
            },
        ]),
        FakeResult(rows=[]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/etu/breaker-cascade")
        assert resp.status_code == 200
        body = resp.json()
        assert body["manufacturers"][0] == {
            "manufacturer_id": 21,
            "manufacturer_name": "Cutler Hammer",
            "manufacturer_display": "Cutler-Hammer",
            "breaker_count": 3,
        }
        assert body["manufacturers"][1]["manufacturer_display"] == body["manufacturers"][1]["manufacturer_name"]
        _assert_mfr_alias_joined(fake_db.calls[1]["statement"], "manufacturer_name")
    finally:
        app.dependency_overrides.clear()


def test_tmt_manufacturers_surface_display_names(client):
    fake_db = FakeDb([
        FakeResult(rows=[
            {
                "manufacturer_id": 21,
                "manufacturer_name": "Cutler Hammer",
                "manufacturer_display": "Cutler-Hammer",
                "frame_count": 3,
            },
            {
                "manufacturer_id": 10,
                "manufacturer_name": "Eaton",
                "manufacturer_display": "Eaton",
                "frame_count": 2,
            },
        ])
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/tmt/manufacturers", params={"breaker_class": "mccb"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["manufacturers"][0] == {
            "manufacturer_id": 21,
            "manufacturer_name": "Cutler Hammer",
            "manufacturer_display": "Cutler-Hammer",
            "frame_count": 3,
        }
        assert body["manufacturers"][1]["manufacturer_display"] == body["manufacturers"][1]["manufacturer_name"]
        _assert_mfr_alias_joined(fake_db.calls[0]["statement"], "m.mfr_name")
    finally:
        app.dependency_overrides.clear()


def test_emt_manufacturers_surface_display_names(client):
    fake_db = FakeDb([
        FakeResult(rows=[
            {
                "manufacturer_id": 25,
                "manufacturer_name": "ITE",
                "manufacturer_display": "ITE (BBC)",
                "frame_count": 4,
            },
            {
                "manufacturer_id": 10,
                "manufacturer_name": "Eaton",
                "manufacturer_display": "Eaton",
                "frame_count": 2,
            },
        ])
    ])
    resolved_columns = {
        "emt": {"manufacturer_id": "manufacturer_id"},
        "frames": {"emt_id": "emt_id"},
    }
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with patch("services.neta.router._resolve_emt_contract_columns", return_value=resolved_columns):
            resp = client.get("/api/v1/neta/emt/manufacturers")
        assert resp.status_code == 200
        body = resp.json()
        assert body["manufacturers"][0] == {
            "manufacturer_id": 25,
            "manufacturer_name": "ITE",
            "manufacturer_display": "ITE (BBC)",
            "frame_count": 4,
        }
        assert body["manufacturers"][1]["manufacturer_display"] == body["manufacturers"][1]["manufacturer_name"]
        _assert_mfr_alias_joined(fake_db.calls[0]["statement"], "m.mfr_name")
    finally:
        app.dependency_overrides.clear()
