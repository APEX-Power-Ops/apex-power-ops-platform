"""Tests for local-only test auth bootstrap used by unattended browser automation."""

import os
import sys
from unittest.mock import MagicMock
from urllib.error import HTTPError

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app
import services.auth as auth


class _EmptyPlansDb:
    def __init__(self):
        self.execute_calls = []
        self.commit_called = False
        self.rollback_called = False

    def execute(self, statement, params=None):
        self.execute_calls.append((str(statement), params))
        result = MagicMock()
        result.fetchall.return_value = []
        return result

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


class _ResetDb:
    def __init__(self):
        self.execute_calls = []
        self.commit_called = False
        self.rollback_called = False

    def execute(self, statement, params=None):
        self.execute_calls.append((str(statement), params))
        result = MagicMock()
        result.rowcount = 2 if len(self.execute_calls) == 1 else 1
        return result

    def commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


def _reset_auth_caches():
    auth._get_jwks_client.cache_clear()
    auth._get_issuer.cache_clear()
    auth._get_audience.cache_clear()
    auth._get_oidc_userinfo_url.cache_clear()


class _FakeUserinfoResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_auth_config_exposes_local_test_auth(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_TEST_AUTH", "true")
    monkeypatch.delenv("PUBLIC_MCP_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_AUTHORIZATION_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_TOKEN_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_REDIRECT_URIS", raising=False)
    _reset_auth_caches()

    client = TestClient(app)
    response = client.get("/api/v1/auth/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["test_auth"]["enabled"] is True
    assert payload["operator_token"]["enabled"] is False
    assert payload["desktop_oauth"]["configured"] is False
    assert [user["email"] for user in payload["test_auth"]["users"]] == [
        "neta-test-a@example.com",
        "neta-test-b@example.com",
    ]


def test_auth_config_exposes_operator_token_exchange(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPERATOR_BOOTSTRAP_TOKEN", "bootstrap-secret")
    monkeypatch.setenv("OPERATOR_TOKEN_SIGNING_SECRET", "operator-signing-secret-should-be-long")
    monkeypatch.setenv("OPERATOR_TOKEN_EMAIL", "operator@example.com")
    monkeypatch.setenv("OPERATOR_TOKEN_USER_ID", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    monkeypatch.setenv("OPERATOR_TOKEN_TTL_MINUTES", "30")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.get("/api/v1/auth/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["operator_token"] == {
        "enabled": True,
        "ttl_minutes": 30,
        "email": "operator@example.com",
        "label": "Operator Direct Access",
        "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "validation_errors": [],
    }


def test_public_desktop_config_and_discovery_expose_configured_surface(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REGISTRATION_URL", "https://auth.example.com/oidc/register")
    monkeypatch.setenv("PUBLIC_OAUTH_ISSUER", "https://auth.example.com/")
    monkeypatch.setenv(
        "PUBLIC_OAUTH_REDIRECT_URIS",
        '["https://chat.openai.com/aip/callback","https://chatgpt.com/aip/callback"]',
    )
    _reset_auth_caches()

    client = TestClient(app)

    config_response = client.get("/api/v1/auth/public-desktop-config")
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["configured"] is True
    assert config_payload["public_activation_ready"] is True
    assert config_payload["mcp_root_url"] == "https://control-plane.example.com/mcp"
    assert config_payload["registration_url"] == "https://auth.example.com/oidc/register"
    assert config_payload["registered_redirect_uris"] == [
        "https://chat.openai.com/aip/callback",
        "https://chatgpt.com/aip/callback",
    ]

    discovery_response = client.get("/.well-known/oauth-authorization-server")
    assert discovery_response.status_code == 200
    discovery_payload = discovery_response.json()
    assert discovery_payload["issuer"] == "https://auth.example.com/"
    assert discovery_payload["authorization_endpoint"] == "https://auth.example.com/oauth/authorize"
    assert discovery_payload["token_endpoint"] == "https://auth.example.com/oauth/token"
    assert discovery_payload["registration_endpoint"] == "https://auth.example.com/oidc/register"
    assert discovery_payload["code_challenge_methods_supported"] == ["S256"]

    protected_response = client.get("/.well-known/oauth-protected-resource")
    assert protected_response.status_code == 200
    protected_payload = protected_response.json()
    assert protected_payload == {
        "resource": "https://control-plane.example.com",
        "authorization_servers": ["https://auth.example.com/"],
        "scopes_supported": ["openid", "profile", "email"],
    }

    root_response = client.get("/mcp")
    assert root_response.status_code == 200
    root_payload = root_response.json()
    assert root_payload["status"] == "configured"
    assert root_payload["oauth_discovery_url"] == "https://control-plane.example.com/.well-known/oauth-authorization-server"
    assert root_payload["transport"]["type"] == "streamable-http"


def test_protected_route_advertises_resource_metadata_when_public_surface_is_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv(
        "PUBLIC_OAUTH_REDIRECT_URIS",
        "https://chatgpt.com/connector/oauth/example-callback",
    )
    _reset_auth_caches()

    client = TestClient(app)
    response = client.get("/api/v1/control-plane/task-packets")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        'Bearer resource_metadata="https://control-plane.example.com/.well-known/oauth-protected-resource"'
    )


def test_public_desktop_discovery_rejects_unregistered_or_insecure_redirect_config(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_MCP_BASE_URL", "https://control-plane.example.com")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://auth.example.com/oauth/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://auth.example.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_REDIRECT_URIS", "http://chat.openai.com/aip/callback")
    _reset_auth_caches()

    client = TestClient(app)

    config_response = client.get("/api/v1/auth/public-desktop-config")
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["configured"] is False
    assert config_payload["public_activation_ready"] is False
    assert any("localhost development" in message or "https outside local development" in message for message in config_payload["validation_errors"])

    discovery_response = client.get("/.well-known/oauth-authorization-server")
    assert discovery_response.status_code == 404

    protected_response = client.get("/.well-known/oauth-protected-resource")
    assert protected_response.status_code == 404

    root_response = client.get("/mcp")
    assert root_response.status_code == 404


def test_placeholder_supabase_values_degrade_public_auth_surfaces_without_500(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("PUBLIC_MCP_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_AUTHORIZATION_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_TOKEN_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_JWKS_URL", raising=False)
    monkeypatch.delenv("PUBLIC_OAUTH_REDIRECT_URIS", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://[project-ref].supabase.co")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://[project-ref].supabase.co/auth/v1/.well-known/jwks.json")
    _reset_auth_caches()

    client = TestClient(app)

    config_response = client.get("/api/v1/auth/public-desktop-config")
    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["configured"] is False
    assert any("unresolved placeholder" in message for message in config_payload["validation_errors"])

    discovery_response = client.get("/.well-known/oauth-authorization-server")
    assert discovery_response.status_code == 404

    protected_response = client.get("/.well-known/oauth-protected-resource")
    assert protected_response.status_code == 404

    root_response = client.get("/mcp")
    assert root_response.status_code == 404

    unauth_response = client.get("/api/v1/control-plane/task-packets")
    assert unauth_response.status_code == 401
    assert unauth_response.headers["www-authenticate"] == "Bearer"


def test_oidc_userinfo_fallback_populates_surface_scopes_when_scope_claim_missing(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_ISSUER", "https://auth.example.com/")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_JWKS_URL", "https://auth.example.com/.well-known/jwks.json")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_USERINFO_URL", "https://auth.example.com/userinfo")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_SCOPES", "openid profile email")
    monkeypatch.setenv("GITHUB_MCP_OAUTH_AUDIENCE", "https://github-mcp.apexpowerops.com")
    _reset_auth_caches()

    class _BrokenJwksClient:
        def get_signing_key_from_jwt(self, token):
            raise auth.InvalidTokenError("audience mismatch")

    monkeypatch.setattr(auth, "_get_jwks_client_for_url", lambda url: _BrokenJwksClient())
    monkeypatch.setattr(
        auth,
        "urlopen",
        lambda request, timeout=10: _FakeUserinfoResponse(
            b'{"sub":"google-oauth2|1234567890","email":"user@example.com"}'
        ),
    )

    user = auth.verify_bearer_jwt("opaque-token", surface_env=auth.GITHUB_MCP_OAUTH_SURFACE_ENV)

    assert user.claims["scope"] == "openid profile email"
    assert auth.user_has_required_scopes(user, ["openid", "profile", "email"]) is True


def test_oidc_userinfo_fallback_handles_jwks_client_key_lookup_failures(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_OAUTH_ISSUER", "https://dev-cxahx0lfpdvwnayd.us.auth0.com/")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://dev-cxahx0lfpdvwnayd.us.auth0.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_USERINFO_URL", "https://dev-cxahx0lfpdvwnayd.us.auth0.com/userinfo")
    monkeypatch.setenv("PUBLIC_OAUTH_SCOPES", "openid profile email")
    _reset_auth_caches()

    class _MissingKidJwksClient:
        def get_signing_key_from_jwt(self, token):
            raise auth.PyJWKClientError("Unable to find a signing key that matches: 'rotated-kid'")

    monkeypatch.setattr(auth, "_get_jwks_client_for_url", lambda url: _MissingKidJwksClient())
    monkeypatch.setattr(
        auth,
        "urlopen",
        lambda request, timeout=10: _FakeUserinfoResponse(
            b'{"sub":"auth0|1234567890","email":"user@example.com"}'
        ),
    )

    user = auth.verify_bearer_jwt("opaque-token")

    assert user.email == "user@example.com"
    assert user.claims["scope"] == "openid profile email"


def test_local_test_auth_session_allows_owner_scoped_plan_access(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_TEST_AUTH", "true")
    _reset_auth_caches()

    fake_db = _EmptyPlansDb()
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        client = TestClient(app)
        session_response = client.post(
            "/api/v1/auth/test-session",
            json={"email": "neta-test-a@example.com"},
        )
        assert session_response.status_code == 200
        access_token = session_response.json()["access_token"]

        response = client.get(
            "/api/v1/neta/plans",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json() == []
        assert len(fake_db.execute_calls) >= 2, "Expected bootstrap + plans queries"
        _, params = fake_db.execute_calls[-1]
        assert params["user_id"] == "11111111-1111-1111-1111-111111111111"
        assert fake_db.commit_called is True
    finally:
        app.dependency_overrides.clear()


def test_local_test_auth_rejects_unknown_user(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_TEST_AUTH", "true")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/test-session",
        json={"email": "someone-else@example.com"},
    )

    assert response.status_code == 403
    assert "Unknown local test auth user" in response.json()["detail"]


def test_local_test_auth_endpoint_is_hidden_when_disabled(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_TEST_AUTH", "false")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/test-session",
        json={"email": "neta-test-a@example.com"},
    )

    assert response.status_code == 404


def test_operator_token_exchange_issues_valid_bearer_token(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPERATOR_BOOTSTRAP_TOKEN", "bootstrap-secret")
    monkeypatch.setenv("OPERATOR_TOKEN_SIGNING_SECRET", "operator-signing-secret-should-be-long")
    monkeypatch.setenv("OPERATOR_TOKEN_EMAIL", "operator@example.com")
    monkeypatch.setenv("OPERATOR_TOKEN_USER_ID", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    monkeypatch.setenv("OPERATOR_TOKEN_TTL_MINUTES", "15")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/operator-token",
        json={"bootstrap_token": "bootstrap-secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    user = auth.verify_supabase_jwt(payload["access_token"])
    assert payload["provider"] == "operator-token"
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "operator@example.com"
    assert str(user.user_id) == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert user.email == "operator@example.com"
    assert user.role == "operator"


def test_generic_oauth_jwt_enforces_audience_and_maps_non_uuid_subject(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://dev.example.us.auth0.com/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://dev.example.us.auth0.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://dev.example.us.auth0.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_ISSUER", "https://dev.example.us.auth0.com/")
    monkeypatch.setenv("PUBLIC_OAUTH_AUDIENCE", "https://control-plane.example.com")
    _reset_auth_caches()

    fake_signing_key = MagicMock()
    fake_signing_key.key = "public-key"
    fake_jwks_client = MagicMock()
    fake_jwks_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr(auth, "_get_jwks_client_for_url", lambda url: fake_jwks_client)

    decode_call: dict[str, object] = {}

    def _fake_decode(token, key, **kwargs):
        decode_call.update(kwargs)
        return {
            "sub": "auth0|operator-123",
            "email": "auth0-user@example.com",
            "role": "authenticated",
            "iss": "https://dev.example.us.auth0.com/",
            "exp": 4102444800,
            "iat": 1704067200,
            "aud": "https://control-plane.example.com",
        }

    monkeypatch.setattr(auth.jwt, "decode", _fake_decode)

    user = auth.verify_supabase_jwt("header.payload.signature")

    assert decode_call["issuer"] == "https://dev.example.us.auth0.com/"
    assert decode_call["audience"] == "https://control-plane.example.com"
    assert decode_call["options"]["verify_aud"] is True
    expected_user_id = auth._stable_subject_uuid(
        "auth0|operator-123",
        "https://dev.example.us.auth0.com/",
    )
    assert user.user_id == expected_user_id
    assert user.email == "auth0-user@example.com"


def test_generic_oauth_falls_back_to_userinfo_for_non_decodable_access_tokens(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_OAUTH_AUTHORIZATION_URL", "https://dev.example.us.auth0.com/authorize")
    monkeypatch.setenv("PUBLIC_OAUTH_TOKEN_URL", "https://dev.example.us.auth0.com/oauth/token")
    monkeypatch.setenv("PUBLIC_OAUTH_JWKS_URL", "https://dev.example.us.auth0.com/.well-known/jwks.json")
    monkeypatch.setenv("PUBLIC_OAUTH_ISSUER", "https://dev.example.us.auth0.com/")
    monkeypatch.setenv("PUBLIC_OAUTH_AUDIENCE", "https://control-plane.example.com")
    _reset_auth_caches()

    fake_signing_key = MagicMock()
    fake_signing_key.key = "public-key"
    fake_jwks_client = MagicMock()
    fake_jwks_client.get_signing_key_from_jwt.return_value = fake_signing_key
    monkeypatch.setattr(auth, "_get_jwks_client", lambda: fake_jwks_client)

    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            auth.InvalidTokenError("Invalid payload string: 'utf-8' codec can't decode byte 0x84")
        ),
    )

    class _FakeHeaders:
        @staticmethod
        def get_content_charset():
            return "utf-8"

    class _FakeResponse:
        headers = _FakeHeaders()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        def read():
            return (
                b'{"sub":"auth0|operator-123","email":"userinfo@example.com","role":"authenticated"}'
            )

    captured_request: dict[str, str] = {}

    def _fake_urlopen(request, timeout=10):
        captured_request["url"] = request.full_url
        captured_request["authorization"] = request.get_header("Authorization")
        return _FakeResponse()

    monkeypatch.setattr(auth, "urlopen", _fake_urlopen)

    user = auth.verify_supabase_jwt("opaque-or-encrypted-token")

    assert captured_request["url"] == "https://dev.example.us.auth0.com/userinfo"
    assert captured_request["authorization"] == "Bearer opaque-or-encrypted-token"
    expected_user_id = auth._stable_subject_uuid(
        "auth0|operator-123",
        "https://dev.example.us.auth0.com/",
    )
    assert user.user_id == expected_user_id
    assert user.email == "userinfo@example.com"
    assert user.role == "authenticated"


def test_operator_token_exchange_rejects_invalid_bootstrap(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("OPERATOR_BOOTSTRAP_TOKEN", "bootstrap-secret")
    monkeypatch.setenv("OPERATOR_TOKEN_SIGNING_SECRET", "operator-signing-secret-should-be-long")
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/operator-token",
        json={"bootstrap_token": "wrong-secret"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid operator bootstrap token"


def test_operator_token_exchange_is_hidden_when_disabled(monkeypatch):
    monkeypatch.delenv("OPERATOR_BOOTSTRAP_TOKEN", raising=False)
    monkeypatch.delenv("OPERATOR_TOKEN_SIGNING_SECRET", raising=False)
    _reset_auth_caches()

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/operator-token",
        json={"bootstrap_token": "anything"},
    )

    assert response.status_code == 404


def test_local_test_auth_reset_cleans_user_owned_demo_rows(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_TEST_AUTH", "true")
    _reset_auth_caches()

    fake_db = _ResetDb()
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/test-reset",
            json={"email": "neta-test-b@example.com"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["email"] == "neta-test-b@example.com"
        assert payload["deleted_results"] == 2
        assert payload["deleted_plans"] == 1
        assert fake_db.commit_called is True
        assert fake_db.rollback_called is False
        assert len(fake_db.execute_calls) == 2
        assert fake_db.execute_calls[0][1]["user_id"] == "22222222-2222-2222-2222-222222222222"
        assert fake_db.execute_calls[1][1]["project"] == "neta-demo"
    finally:
        app.dependency_overrides.clear()
