"""
Tests for the NETA available settings endpoint.

Verifies:
    GET /api/v1/neta/settings/{sensor_id} — returns dropdown values and expands
    boundary-only pickup ranges when the calc context provides step metadata.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from config import get_db
from main import app


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row

    def fetchall(self):
        if self._row is None:
            return []
        if isinstance(self._row, list):
            return self._row
        return [self._row]


class _MappingRow:
    def __init__(self, mapping=None, result=None):
        self._mapping = mapping or {}
        self.result = result


class _FakeSettingsDb:
    def __init__(
        self,
        settings_payload,
        context_mapping,
        std_band_rows=None,
        gfd_band_rows=None,
        ltd_band_rows=None,
        direct_rows=None,
        raise_on_function=False,
    ):
        self.settings_payload = settings_payload
        self.context_mapping = context_mapping
        derived_direct_rows = {
            "plugs": [{"value": value} for value in (settings_payload or {}).get("plug_values", [])],
            "ltpu": [{"value": value} for value in (settings_payload or {}).get("ltpu_settings", [])],
            "multipliers": [{"value": value} for value in (settings_payload or {}).get("ltd_multipliers", [])],
            "stpu": [{"value": value} for value in (settings_payload or {}).get("stpu_settings", [])],
            "inst": [{"value": value} for value in (settings_payload or {}).get("inst_settings", [])],
            "gfpu": [{"value": value} for value in (settings_payload or {}).get("gfpu_settings", [])],
        }
        merged_direct_rows = {**derived_direct_rows, **(direct_rows or {})}

        if ltd_band_rows is None:
            ltd_band_rows = (settings_payload or {}).get("ltd_settings", [])

        self.std_band_rows = [_MappingRow(mapping=row) for row in (std_band_rows or [])]
        self.gfd_band_rows = [_MappingRow(mapping=row) for row in (gfd_band_rows or [])]
        self.ltd_band_rows = [_MappingRow(mapping=row) for row in (ltd_band_rows or [])]
        self.direct_rows = {
            key: [_MappingRow(mapping=row) for row in rows]
            for key, rows in merged_direct_rows.items()
        }
        self.raise_on_function = raise_on_function
        self.function_calls = 0

    def execute(self, statement, params=None):
        sql = str(statement)
        if "fn_sensor_available_settings" in sql:
            self.function_calls += 1
            if self.raise_on_function:
                raise RuntimeError("stale function")
            return _Result(_MappingRow(result=self.settings_payload))
        if "vw_sensor_calc_context" in sql:
            return _Result(_MappingRow(mapping=self.context_mapping))
        if "FROM tcc.etu_" in sql and "GROUP BY p.sensor_id" in sql:
            return _Result([])
        if "FROM tcc.etu_plugs" in sql:
            return _Result(self.direct_rows.get("plugs", []))
        if "FROM tcc.etu_ltpu_pickups" in sql:
            return _Result(self.direct_rows.get("ltpu", []))
        if "FROM tcc.etu_ltpu_multipliers" in sql:
            return _Result(self.direct_rows.get("multipliers", []))
        if "FROM tcc.etu_stpu_pickups" in sql:
            return _Result(self.direct_rows.get("stpu", []))
        if "FROM tcc.etu_inst_pickups" in sql:
            return _Result(self.direct_rows.get("inst", []))
        if "FROM tcc.etu_gfpu_pickups" in sql:
            return _Result(self.direct_rows.get("gfpu", []))
        if "FROM tcc.etu_ltd_bands" in sql:
            return _Result(self.ltd_band_rows)
        if "FROM tcc.etu_std_bands" in sql:
            return _Result(self.std_band_rows)
        if "FROM tcc.etu_gfd_bands" in sql:
            return _Result(self.gfd_band_rows)
        raise AssertionError(f"Unexpected SQL: {sql}")


def test_settings_route_expands_boundary_only_pickups_from_primary_and_maint_steps():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload={
            "plug_values": [600, 800, 1000, 1200],
            "ltpu_settings": [0.4, 1.0],
            "ltd_settings": [],
            "ltd_multipliers": [],
            "stpu_settings": [0.6, 10.0],
            "inst_settings": [1.5, 15.0],
            "gfpu_settings": [0.1, 1.0],
        },
        context_mapping={
            "manufacturer_name": "ABB",
            "trip_type_name": "Ekip Touch",
            "trip_style_name": "XT7 LSI/G",
            "ltpu_step": 0.001,
            "stpu_step": 0.1,
            "inst_step": None,
            "gfpu_step": None,
            "maint_inst_step": 0.1,
            "maint_gfpu_step": 0.1,
        },
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/16798")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ltpu_settings"][:4] == [0.4, 0.401, 0.402, 0.403]
        assert data["ltpu_settings"][-1] == 1
        assert data["stpu_settings"][:5] == [0.6, 0.7, 0.8, 0.9, 1]
        assert data["stpu_settings"][-1] == 10
        assert data["inst_settings"][:5] == [1.5, 1.6, 1.7, 1.8, 1.9]
        assert data["inst_settings"][-1] == 15
        assert data["gfpu_settings"][:5] == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert data["gfpu_settings"][-1] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_settings_route_expands_non_abb_pickups_from_maint_step_fallback():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload={
            "plug_values": [800],
            "ltpu_settings": [],
            "ltd_settings": [],
            "ltd_multipliers": [],
            "stpu_settings": [],
            "inst_settings": [1.5, 4.0],
            "gfpu_settings": [0.2, 1.0],
        },
        context_mapping={
            "manufacturer_name": "Eaton",
            "trip_type_name": "Magnum PXR25",
            "trip_style_name": "Std Frm MPS",
            "ltpu_step": None,
            "stpu_step": None,
            "inst_step": None,
            "gfpu_step": None,
            "maint_inst_step": 0.5,
            "maint_gfpu_step": 0.2,
        },
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["inst_settings"] == [1.5, 2, 2.5, 3, 3.5, 4]
        assert data["gfpu_settings"] == [0.2, 0.4, 0.6, 0.8, 1]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_settings_route_leaves_boundary_pairs_unchanged_without_any_step_metadata():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload={
            "plug_values": [800],
            "ltpu_settings": [0.4, 1.0],
            "ltd_settings": [],
            "ltd_multipliers": [],
            "stpu_settings": [0.6, 10.0],
            "inst_settings": [1.5, 15.0],
            "gfpu_settings": [0.1, 1.0],
        },
        context_mapping={
            "manufacturer_name": "GE",
            "trip_type_name": "MVT RMS-9",
            "trip_style_name": "ICCB",
            "ltpu_step": None,
            "stpu_step": None,
            "inst_step": None,
            "gfpu_step": None,
            "maint_inst_step": None,
            "maint_gfpu_step": None,
        },
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ltpu_settings"] == [0.4, 1]
        assert data["stpu_settings"] == [0.6, 10]
        assert data["inst_settings"] == [1.5, 15]
        assert data["gfpu_settings"] == [0.1, 1]
        assert fake_db.function_calls == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_settings_route_deduplicates_ltd_rows_with_same_open_time():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload={
            "plug_values": [800],
            "ltpu_settings": [0.4, 1.0],
            "ltd_settings": [
                {"band": "I-C-2", "label": "C-2", "open_time": 6.0},
                {"band": "I-C-2", "label": "C-2", "open_time": 6.0},
                {"band": "I-C-3", "label": "C-3", "open_time": 12.0},
                {"band": "ALT-C-3", "label": "C-3 Alt", "open_time": 12.0},
            ],
            "ltd_multipliers": [],
            "stpu_settings": [0.6, 10.0],
            "inst_settings": [1.5, 15.0],
            "gfpu_settings": [0.1, 1.0],
        },
        context_mapping={
            "manufacturer_name": "GE",
            "trip_type_name": "MVT RMS-9",
            "trip_style_name": "ICCB",
            "ltpu_step": None,
            "stpu_step": None,
            "inst_step": None,
            "gfpu_step": None,
            "maint_inst_step": None,
            "maint_gfpu_step": None,
        },
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ltd_settings"] == [
            {"band": "I-C-2", "label": "C-2", "open_time": 6.0, "clear_time": None, "is_default": False},
            {"band": "I-C-3", "label": "C-3", "open_time": 12.0, "clear_time": None, "is_default": False},
        ]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_settings_route_returns_strict_std_and_gfd_band_options():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload={
            "plug_values": [800],
            "ltpu_settings": [0.4, 1.0],
            "ltd_settings": [],
            "ltd_multipliers": [],
            "stpu_settings": [0.6, 10.0],
            "inst_settings": [1.5, 15.0],
            "gfpu_settings": [0.1, 1.0],
        },
        context_mapping={
            "manufacturer_name": "GE",
            "trip_type_name": "MVT RMS-9",
            "trip_style_name": "ICCB",
            "ltpu_step": None,
            "stpu_step": None,
            "inst_step": None,
            "gfpu_step": None,
            "maint_inst_step": None,
            "maint_gfpu_step": None,
        },
        std_band_rows=[
            {"band": "I2T Min", "label": "Min", "open_time": 0.1, "clear_time": 0.2, "is_default": True},
            {"band": "I2T Min", "label": "Min", "open_time": 0.1, "clear_time": 0.2, "is_default": True},
            {"band": "I2T Max", "label": "Max", "open_time": 0.35, "clear_time": 0.5, "is_default": False},
        ],
        gfd_band_rows=[
            {"band": "GF Min", "label": "Min", "open_time": 0.2, "clear_time": 0.3, "is_default": True},
            {"band": "GF Max", "label": "Max", "open_time": 0.5, "clear_time": 0.8, "is_default": False},
        ],
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/25")
        assert resp.status_code == 200
        data = resp.json()
        assert data["std_settings"] == [
            {"band": "I2T Min", "label": "Min", "open_time": 0.1, "clear_time": 0.2, "is_default": True},
            {"band": "I2T Max", "label": "Max", "open_time": 0.35, "clear_time": 0.5, "is_default": False},
        ]
        assert data["gfd_settings"] == [
            {"band": "GF Min", "label": "Min", "open_time": 0.2, "clear_time": 0.3, "is_default": True},
            {"band": "GF Max", "label": "Max", "open_time": 0.5, "clear_time": 0.8, "is_default": False},
        ]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_settings_route_reads_direct_etu_tables_without_touching_stale_sql_function():
    client = TestClient(app)
    fake_db = _FakeSettingsDb(
        settings_payload=None,
        context_mapping={
            "manufacturer_name": "(Generic)",
            "trip_type_name": "Std",
            "trip_style_name": "Std",
            "rating": 800,
            "ltpu_step": 0.1,
            "stpu_step": 0.5,
            "inst_step": 1.0,
            "gfpu_step": 0.1,
            "maint_inst_step": None,
            "maint_gfpu_step": None,
        },
        ltd_band_rows=[
            {"band": "1", "label": "1", "open_time": 2.4, "clear_time": None, "is_default": False},
            {"band": "2", "label": "2", "open_time": 4.9, "clear_time": None, "is_default": False},
        ],
        std_band_rows=[
            {"band": "Min", "label": "Min", "open_time": 0.1, "clear_time": 0.16, "is_default": False},
        ],
        gfd_band_rows=[
            {"band": "Min", "label": "Min", "open_time": 0.2, "clear_time": 0.3, "is_default": False},
        ],
        direct_rows={
            "plugs": [{"value": 300}, {"value": 400}, {"value": 900}],
            "ltpu": [{"value": 0.5}, {"value": 0.6}],
            "multipliers": [{"value": 1.0}],
            "stpu": [{"value": 1.5}, {"value": 2.0}],
            "inst": [{"value": 3.0}, {"value": 4.0}],
            "gfpu": [{"value": 0.2}, {"value": 0.3}],
        },
        raise_on_function=True,
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get("/api/v1/neta/settings/3629")
        assert resp.status_code == 200
        data = resp.json()
        assert fake_db.function_calls == 0
        assert data["plug_values"] == [300, 400]
        assert data["ltpu_settings"] == [0.5, 0.6]
        assert data["ltd_settings"][0]["open_time"] == 2.4
        assert data["ltd_multipliers"] == [1]
        assert data["stpu_settings"] == [1.5, 2]
        assert data["inst_settings"] == [3, 4]
        assert data["gfpu_settings"] == [0.2, 0.3]
        assert data["std_settings"][0]["clear_time"] == 0.16
        assert data["gfd_settings"][0]["clear_time"] == 0.3
    finally:
        app.dependency_overrides.pop(get_db, None)
