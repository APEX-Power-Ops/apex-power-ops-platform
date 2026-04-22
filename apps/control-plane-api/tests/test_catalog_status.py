"""
Tests for the NETA catalog status endpoint.

Verifies:
  GET /api/v1/neta/catalog/status — reports live catalog availability
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from config import get_db


@pytest.fixture
def client():
    return TestClient(app)


def _mock_db_with_catalog(manufacturer_count=450, sensor_count=2572):
    """Create a mock DB session that returns catalog counts."""
    mock_db = MagicMock()
    mock_row = MagicMock()
    mock_row._mapping = {
        "manufacturer_count": manufacturer_count,
        "sensor_count": sensor_count,
    }
    mock_db.execute.return_value.fetchone.return_value = mock_row
    return mock_db


def _mock_db_unreachable():
    """Create a mock DB session that raises on any query."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("connection to server failed")
    return mock_db


class TestCatalogStatus:
    """Tests for GET /api/v1/neta/catalog/status."""

    def test_catalog_live_with_data(self, client):
        """When Supabase is reachable and has data, report live."""
        mock_db = _mock_db_with_catalog(450, 2572)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/catalog/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["catalog"] == "live"
            assert data["manufacturer_count"] == 450
            assert data["sensor_count"] == 2572
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_catalog_unavailable_when_db_unreachable(self, client):
        """When Supabase is unreachable, report unavailable with error."""
        mock_db = _mock_db_unreachable()
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/catalog/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["catalog"] == "unavailable"
            assert data["manufacturer_count"] == 0
            assert data["sensor_count"] == 0
            assert "error" in data
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_catalog_reports_zero_counts_when_empty(self, client):
        """When DB is up but tables are empty, still report live."""
        mock_db = _mock_db_with_catalog(0, 0)
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            resp = client.get("/api/v1/neta/catalog/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["catalog"] == "live"
            assert data["manufacturer_count"] == 0
            assert data["sensor_count"] == 0
        finally:
            app.dependency_overrides.pop(get_db, None)
