"""
Tests for the health/readiness contract.

Verifies:
  GET /health       — always returns {"status": "ok"} (liveness)
  GET /health/live  — alias for liveness
  GET /health/ready — reports database reachability and catalog availability
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


# ── Liveness ──

class TestLiveness:
    """Liveness probes should always succeed if the app is running."""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_live_returns_ok(self, client):
        resp = client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── Readiness ──

class TestReadiness:
    """Readiness probe should report database state honestly."""

    def test_ready_returns_200_even_when_db_unreachable(self, client):
        """Readiness always returns 200 — the body distinguishes state."""
        with patch("config.engine") as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection refused")
            resp = client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "unreachable"
        assert data["catalog_available"] is False
        assert "error" in data

    def test_ready_reports_connected_when_db_reachable(self, client):
        """When DB is reachable and catalog view exists, report ready."""
        mock_conn = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 1
        mock_conn.execute.side_effect = [
            None,       # SELECT 1
            MagicMock(fetchone=lambda: mock_row),  # view check
        ]
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda self: mock_conn
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("config.engine") as mock_engine:
            mock_engine.connect.return_value = mock_ctx
            resp = client.get("/health/ready")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert data["catalog_available"] is True

    def test_ready_reports_no_catalog_when_view_missing(self, client):
        """When DB is up but the catalog view doesn't exist, report accordingly."""
        mock_conn = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 0  # view not found
        mock_conn.execute.side_effect = [
            None,
            MagicMock(fetchone=lambda: mock_row),
        ]
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = lambda self: mock_conn
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("config.engine") as mock_engine:
            mock_engine.connect.return_value = mock_ctx
            resp = client.get("/health/ready")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert data["catalog_available"] is False
