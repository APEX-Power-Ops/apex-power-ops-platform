"""Smoke tests for the public OAuth consent route."""

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


client = TestClient(app)


def test_root_route_returns_ok():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"service": "apex-platform-control-plane-api", "status": "ok"}


def test_oauth_consent_route_returns_html():
    resp = client.get("/oauth/consent")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_oauth_consent_page_contains_authorization_id_flow():
    body = client.get("/oauth/consent").text
    assert "authorization_id" in body
    assert "getAuthorizationDetails" in body
    assert "authorization request expired or was already used" in body
    assert "saved sign-in session is no longer valid" in body
    assert "approveAuthorization" in body
    assert "denyAuthorization" in body
    assert "Magic Link" in body
    assert "Sign In with Password" in body
    assert "signInWithPassword" in body
    assert "Governed authorization" in body