"""
Tests for NETA demo plan and result persistence.

Verifies:
  POST /api/v1/neta/plans              — Save a named plan
  GET  /api/v1/neta/plans              — List saved plans
  GET  /api/v1/neta/plans/{plan_id}    — Load a plan
  POST /api/v1/neta/plans/{plan_id}/results — Save a result artifact

Note: The live Supabase schema uses UUID primary keys.  All mock IDs in
these tests use UUID strings to match the live contract.
"""

import sys
import os
import json
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, PropertyMock
from fastapi.testclient import TestClient
from main import app
from config import get_db
from services.auth import AuthenticatedUser
from services.neta.plans import get_current_user


# ── Test UUIDs (deterministic for assertions) ──

PLAN_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
PLAN_UUID_2 = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
RESULT_UUID_1 = "c3d4e5f6-a7b8-9012-cdef-123456789012"
RESULT_UUID_2 = "d4e5f6a7-b8c9-0123-def0-234567890123"
TEST_USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"


# ── Fixtures ──

SAMPLE_PLAN = {
    "family": "etu",
    "name": "GE MVT RMS-9 800A Test",
    "sensor_id": 25,
    "manufacturer_id": 9,
    "manufacturer_name": "GE",
    "trip_type_id": 75,
    "trip_type_name": "MVT RMS-9",
    "trip_style_id": 3,
    "trip_style_name": "ICCB",
    "breaker_context_label": "ICCB · 800A",
    "breaker_context_source": "trip_style_sensor_rating",
    "sensor_desc": "800",
    "resolved_equipment": {
        "family": "etu",
        "family_label": "ETU",
        "resolved_id": "sensor:25",
        "primary_label": "GE MVT RMS-9 ICCB",
        "secondary_label": "ICCB · 800A",
        "breaker_context": {
            "label": "ICCB · 800A",
            "source": "trip_style_sensor_rating",
            "manufacturer_name": "GE",
            "breaker_style_name": "ICCB",
        },
        "trip_unit": {
            "manufacturer_name": "GE",
            "trip_type_name": "MVT RMS-9",
            "trip_style_name": "ICCB",
            "label": "GE MVT RMS-9 ICCB",
        },
        "rating_context": {
            "label": "Sensor 800",
            "sensor_id": 25,
            "sensor_desc": "800",
            "sensor_rating": 800.0,
            "amp_ratings": [],
        },
    },
    "settings": {
        "plug_rating": 800,
        "ltpu_setting": 0.8,
        "ltd_setting": 6,
        "stpu_setting": 4.0,
        "std_setting": 1.0,
        "inst_setting": 10.0,
        "gfpu_setting": 0.4,
        "gfd_setting": 1.0,
        "maint_mode": False,
    },
    "measurements": {
        "ltpu": 650,
        "ltd": 3.2,
        "stpu": 3100,
        "std": 0.42,
        "inst": None,
        "gfpu": 310,
        "gfd": 0.18,
    },
}

SAMPLE_RESULT = {
    "overall_pass": True,
    "tested_count": 3,
    "passed_count": 3,
    "failed_count": 0,
    "maint_mode": False,
    "elements": [
        {
            "element": "LTPU",
            "test_current": 640.0,
            "measured_current": 650.0,
            "limit_low": 576.0,
            "limit_high": 768.0,
            "passed": True,
            "deviation_pct": 1.6,
        },
        {
            "element": "STPU",
            "test_current": 3200.0,
            "measured_current": 3100.0,
            "limit_low": 2880.0,
            "limit_high": 3520.0,
            "passed": True,
            "deviation_pct": -3.1,
        },
    ],
    "warnings": [],
}


def _make_authenticated_user(user_id: str = TEST_USER_ID, email: str = "tester@example.com"):
    return AuthenticatedUser(
        user_id=UUID(user_id),
        email=email,
        role="authenticated",
        claims={"sub": user_id, "email": email, "role": "authenticated"},
    )


def _make_mock_db_for_save():
    """Mock DB that handles INSERT...RETURNING for plan save."""
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, idx: [PLAN_UUID, "2026-03-21T12:00:00", None][idx]
    mock_db.execute.return_value.fetchone.return_value = mock_row
    return mock_db


def _make_mock_db_for_list(plans):
    """Mock DB that returns a list of plan rows.

    Row layout: id, name, sensor_id, settings_snapshot, display_snapshot,
                created_at, updated_at
    """
    mock_db = MagicMock()
    rows = []
    for p in plans:
        row = MagicMock()
        display_snapshot = p.get("display_snapshot", {})
        row.__getitem__ = lambda self, idx, p=p, ds=display_snapshot: [
            p["id"], p["name"], p["sensor_id"],
            p["settings"],  # JSONB — may come back as dict
            ds,             # JSONB — display_snapshot
            p["created_at"], p.get("updated_at"),
        ][idx]
        rows.append(row)
    mock_db.execute.return_value.fetchall.return_value = rows
    return mock_db


def _make_mock_db_for_load(plan_data):
    """Mock DB that returns a single plan row, then a result count.

    Row layout: id, name, sensor_id, settings_snapshot, display_snapshot,
                created_at, updated_at
    """
    mock_db = MagicMock()
    plan_row = MagicMock()
    plan_row.__getitem__ = lambda self, idx, p=plan_data: [
        p["id"], p["name"], p["sensor_id"],
        p["settings"],  # JSONB — dict
        {
            "display": {
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "breaker_context_label": "ICCB · 800A",
                "breaker_context_source": "trip_style_sensor_rating",
                "sensor_desc": "800",
                "resolved_equipment": plan_data.get("resolved_equipment"),
            },
            "measurements": p.get("measurements"),
        },  # JSONB — dict
        p["created_at"], p.get("updated_at"),
    ][idx]

    count_row = MagicMock()
    count_row.__getitem__ = lambda self, idx: [2][idx]

    mock_db.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_row)),
        MagicMock(fetchone=MagicMock(return_value=count_row)),
    ]
    return mock_db


def _make_mock_db_for_result_save():
    """Mock DB that handles plan existence check + result INSERT."""
    mock_db = MagicMock()
    plan_check_row = MagicMock()
    plan_check_row.__getitem__ = lambda self, idx: [PLAN_UUID][idx]

    result_row_1 = MagicMock()
    result_row_1.__getitem__ = lambda self, idx: [RESULT_UUID_1, "2026-03-21T14:00:00"][idx]
    result_row_2 = MagicMock()
    result_row_2.__getitem__ = lambda self, idx: [RESULT_UUID_2, "2026-03-21T14:00:01"][idx]

    mock_db.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=plan_check_row)),
        MagicMock(fetchone=MagicMock(return_value=result_row_1)),
        MagicMock(fetchone=MagicMock(return_value=result_row_2)),
    ]
    return mock_db


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class TestAuthEnforcement:
    def test_plans_routes_require_authentication(self):
        mock_db = _make_mock_db_for_list([])
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            client = TestClient(app)
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ── Plan Save Tests ──

class TestPlanSave:
    """Tests for POST /api/v1/neta/plans."""

    def test_save_plan_returns_201(self, client):
        mock_db = _make_mock_db_for_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post("/api/v1/neta/plans", json=SAMPLE_PLAN)
            assert resp.status_code == 201
            data = resp.json()
            assert data["id"] == PLAN_UUID
            assert data["family"] == "etu"
            assert data["name"] == SAMPLE_PLAN["name"]
            assert data["sensor_id"] == 25
            assert data["manufacturer_id"] == 9
            assert data["trip_type_id"] == 75
            assert data["trip_style_id"] == 3
            assert data["manufacturer_name"] == "GE"
            assert data["breaker_context_label"] == "ICCB · 800A"
            assert data["breaker_context_source"] == "trip_style_sensor_rating"
            assert data["resolved_equipment"]["family"] == "etu"
            assert data["resolved_equipment"]["trip_unit"]["label"] == "GE MVT RMS-9 ICCB"
            assert data["settings"]["plug_rating"] == 800
            assert data["settings"]["maint_mode"] is False
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_plan_preserves_measurements(self, client):
        mock_db = _make_mock_db_for_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post("/api/v1/neta/plans", json=SAMPLE_PLAN)
            data = resp.json()
            assert data["measurements"]["ltpu"] == 650
            assert data["measurements"]["ltd"] == 3.2
            assert data["measurements"]["gfpu"] == 310
            assert data["measurements"]["gfd"] == 0.18
            assert data["measurements"]["inst"] is None
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_plan_requires_name(self, client):
        mock_db = _make_mock_db_for_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            bad = {**SAMPLE_PLAN, "name": ""}
            resp = client.post("/api/v1/neta/plans", json=bad)
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_plan_rejects_non_etu_family(self, client):
        mock_db = _make_mock_db_for_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            bad = {**SAMPLE_PLAN, "family": "tmt"}
            resp = client.post("/api/v1/neta/plans", json=bad)
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_plan_db_failure_returns_503(self, client):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("connection refused")
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post("/api/v1/neta/plans", json=SAMPLE_PLAN)
            assert resp.status_code == 503
            assert "unreachable" in resp.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_db, None)


# ── Plan List Tests ──

class TestPlanList:
    """Tests for GET /api/v1/neta/plans."""

    def test_list_plans_returns_array(self, client):
        mock_db = _make_mock_db_for_list([
            {"id": PLAN_UUID, "name": "Plan A", "sensor_id": 25,
             "settings": {"maint_mode": False, "plug_rating": 800},
             "display_snapshot": {"display": {"sensor_desc": "800", "resolved_equipment": SAMPLE_PLAN["resolved_equipment"]}},
             "created_at": "2026-03-21T10:00:00", "updated_at": None},
            {"id": PLAN_UUID_2, "name": "Plan B", "sensor_id": 30,
             "settings": {"maint_mode": True, "plug_rating": 1200},
             "display_snapshot": {"display": {"sensor_desc": "1200"}},
             "created_at": "2026-03-21T11:00:00", "updated_at": None},
        ])
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            assert data[0]["family"] == "etu"
            assert data[0]["name"] == "Plan A"
            assert data[0]["resolved_equipment"]["resolved_id"] == "sensor:25"
            assert data[0]["cascade_state"]["sensor_id"] == 25
            assert data[0]["cascade_state"]["resolved_id"] == "sensor:25"
            assert data[1]["maint_mode"] is True
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_list_plans_empty(self, client):
        mock_db = _make_mock_db_for_list([])
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 200
            assert resp.json() == []
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_list_plans_db_failure_returns_503(self, client):
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("timeout")
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 503
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_list_plans_synthesizes_cascade_state_for_legacy_snapshots(self, client):
        mock_db = _make_mock_db_for_list([
            {
                "id": PLAN_UUID,
                "name": "Legacy Plan",
                "sensor_id": 25,
                "settings": {"maint_mode": False, "plug_rating": 800},
                "display_snapshot": {
                    "display": {
                        "family": "etu",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "breaker_context_label": "ICCB · 800A",
                        "breaker_context_source": "trip_style_sensor_rating",
                        "sensor_desc": "800",
                    }
                },
                "created_at": "2026-03-21T10:00:00",
                "updated_at": None,
            }
        ])
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 200
            data = resp.json()
            assert data[0]["cascade_state"] == {
                "family": "etu",
                "manufacturer_id": 9,
                "trip_type_id": 75,
                "trip_style_id": 3,
                "sensor_id": 25,
                "resolved_id": "sensor:25",
            }
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_plan_stamps_authenticated_user_id(self, client):
        mock_db = _make_mock_db_for_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post("/api/v1/neta/plans", json=SAMPLE_PLAN)
            assert resp.status_code == 201
            params = mock_db.execute.call_args.args[1]
            assert params["user_id"] == TEST_USER_ID
            snapshot = json.loads(params["display_snapshot"])
            assert snapshot["display"]["family"] == "etu"
            assert snapshot["display"]["cascade_state"]["family"] == "etu"
            assert snapshot["display"]["cascade_state"]["trip_style_id"] == 3
            assert snapshot["display"]["cascade_state"]["sensor_id"] == 25
            assert snapshot["display"]["breaker_context_label"] == "ICCB · 800A"
            assert snapshot["display"]["resolved_equipment"]["resolved_id"] == "sensor:25"
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_list_plans_queries_current_user_scope(self, client):
        mock_db = _make_mock_db_for_list([])
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/plans")
            assert resp.status_code == 200
            params = mock_db.execute.call_args.args[1]
            assert params["user_id"] == TEST_USER_ID
        finally:
            app.dependency_overrides.pop(get_db, None)


# ── Plan Load Tests ──

class TestPlanLoad:
    """Tests for GET /api/v1/neta/plans/{plan_id}."""

    def test_load_plan_returns_full_detail(self, client):
        mock_db = _make_mock_db_for_load({
            "id": PLAN_UUID, "name": "GE Test", "sensor_id": 25,
            "resolved_equipment": SAMPLE_PLAN["resolved_equipment"],
            "settings": {
                "plug_rating": 800, "ltpu_setting": 0.8,
                "ltd_setting": 6, "stpu_setting": 4.0,
                "std_setting": 1.0, "inst_setting": 10.0,
                "gfpu_setting": 0.4, "gfd_setting": 1.0,
                "maint_mode": False,
            },
            "measurements": {
                "ltpu": 650,
                "ltd": 3.2,
                "stpu": 3100,
                "std": 0.42,
                "inst": None,
                "gfpu": 310,
                "gfd": 0.18,
            },
            "created_at": "2026-03-21T12:00:00", "updated_at": None,
        })
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(f"/api/v1/neta/plans/{PLAN_UUID}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == PLAN_UUID
            assert data["family"] == "etu"
            assert data["name"] == "GE Test"
            assert data["settings"]["plug_rating"] == 800
            assert data["manufacturer_id"] == 9
            assert data["manufacturer_name"] == "GE"
            assert data["trip_type_id"] == 75
            assert data["trip_type_name"] == "MVT RMS-9"
            assert data["trip_style_id"] == 3
            assert data["trip_style_name"] == "ICCB"
            assert data["breaker_context_label"] == "ICCB · 800A"
            assert data["breaker_context_source"] == "trip_style_sensor_rating"
            assert data["cascade_state"]["trip_style_id"] == 3
            assert data["cascade_state"]["sensor_id"] == 25
            assert data["cascade_state"]["resolved_id"] == "sensor:25"
            assert data["resolved_equipment"]["resolved_id"] == "sensor:25"
            assert data["resolved_equipment"]["rating_context"]["sensor_desc"] == "800"
            assert data["result_count"] == 2
            assert data["measurements"]["ltpu"] == 650
            assert data["measurements"]["std"] == 0.42
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_load_plan_not_found_returns_404(self, client):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(f"/api/v1/neta/plans/{PLAN_UUID}")
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_load_plan_settings_shape_matches_save(self, client):
        """Loaded settings must have the same shape as saved settings."""
        saved = SAMPLE_PLAN["settings"]
        mock_db = _make_mock_db_for_load({
            "id": PLAN_UUID, "name": "Shape Test", "sensor_id": 25,
            "settings": saved,
            "measurements": None,
            "created_at": "2026-03-21T12:00:00", "updated_at": None,
        })
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(f"/api/v1/neta/plans/{PLAN_UUID}")
            loaded = resp.json()["settings"]
            for key in saved:
                assert key in loaded, f"Settings key '{key}' missing from loaded plan"
                assert loaded[key] == saved[key], \
                    f"Settings key '{key}': saved {saved[key]} != loaded {loaded[key]}"
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_load_plan_returns_404_for_other_users_scope(self, client):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user(
            user_id=OTHER_USER_ID,
            email="other@example.com",
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(f"/api/v1/neta/plans/{PLAN_UUID}")
            assert resp.status_code == 404
            params = mock_db.execute.call_args.args[1]
            assert params["user_id"] == OTHER_USER_ID
            assert params["pid"] == PLAN_UUID
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_load_plan_synthesizes_cascade_state_for_legacy_snapshot(self, client):
        mock_db = _make_mock_db_for_load({
            "id": PLAN_UUID,
            "name": "Legacy Load",
            "sensor_id": 25,
            "settings": SAMPLE_PLAN["settings"],
            "measurements": None,
            "created_at": "2026-03-21T12:00:00",
            "updated_at": None,
        })
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get(f"/api/v1/neta/plans/{PLAN_UUID}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["cascade_state"] == {
                "family": "etu",
                "manufacturer_id": 9,
                "trip_type_id": 75,
                "trip_style_id": 3,
                "sensor_id": 25,
                "resolved_id": "sensor:25",
            }
        finally:
            app.dependency_overrides.pop(get_db, None)


# ── Result Save Tests ──

class TestResultSave:
    """Tests for POST /api/v1/neta/plans/{plan_id}/results."""

    def test_save_result_returns_201(self, client):
        mock_db = _make_mock_db_for_result_save()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post(f"/api/v1/neta/plans/{PLAN_UUID}/results", json=SAMPLE_RESULT)
            assert resp.status_code == 201
            data = resp.json()
            assert data["id"] == RESULT_UUID_1
            assert data["plan_id"] == PLAN_UUID
            assert data["overall_pass"] is True
            assert data["tested_count"] == 3
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_result_plan_not_found(self, client):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post(f"/api/v1/neta/plans/{PLAN_UUID}/results", json=SAMPLE_RESULT)
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_result_empty_elements_returns_400(self, client):
        mock_db = MagicMock()
        plan_row = MagicMock()
        plan_row.__getitem__ = lambda self, idx: [PLAN_UUID][idx]
        mock_db.execute.return_value.fetchone.return_value = plan_row
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post(f"/api/v1/neta/plans/{PLAN_UUID}/results", json={
                **SAMPLE_RESULT,
                "elements": [],
            })
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_result_db_failure_returns_503(self, client):
        mock_db = MagicMock()
        # Plan check succeeds, then insert fails
        plan_row = MagicMock()
        plan_row.__getitem__ = lambda self, idx: [PLAN_UUID][idx]
        mock_db.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=plan_row)),
            Exception("disk full"),
        ]
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post(f"/api/v1/neta/plans/{PLAN_UUID}/results", json=SAMPLE_RESULT)
            assert resp.status_code == 503
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_save_result_rejects_other_users_plan_scope(self, client):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = None
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user(
            user_id=OTHER_USER_ID,
            email="other@example.com",
        )
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.post(f"/api/v1/neta/plans/{PLAN_UUID}/results", json=SAMPLE_RESULT)
            assert resp.status_code == 404
            params = mock_db.execute.call_args.args[1]
            assert params["user_id"] == OTHER_USER_ID
            assert params["pid"] == PLAN_UUID
        finally:
            app.dependency_overrides.pop(get_db, None)
