"""OAuth bearer-token verification helpers for FastAPI routes."""

from __future__ import annotations

import hmac
import os
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Optional
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, UUID, uuid5

import jwt
from fastapi import Depends, HTTPException, Request as FastAPIRequest, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWKSetError
from sqlalchemy import text
from sqlalchemy.orm import Session


bearer_scheme = HTTPBearer(auto_error=False)
_LOCAL_TEST_AUTH_ISSUER = "local-test-auth"
_OPERATOR_TOKEN_ISSUER = "operator-direct-access"
_LOCAL_TEST_AUTH_STORAGE_KEY = "neta_test_auth_session"
_DEFAULT_TEST_AUTH_USERS = (
    {
        "email": "neta-test-a@example.com",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "label": "Local Test User A",
    },
    {
        "email": "neta-test-b@example.com",
        "user_id": "22222222-2222-2222-2222-222222222222",
        "label": "Local Test User B",
    },
)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Authenticated user extracted from a verified bearer token."""

    user_id: UUID
    email: Optional[str]
    role: Optional[str]
    claims: dict[str, Any]


@dataclass(frozen=True)
class OAuthSurfaceEnv:
    """Environment-variable contract for one public OAuth-protected MCP surface."""

    base_url_env: str
    authorization_url_env: str
    token_url_env: str
    jwks_url_env: str
    registration_url_env: str
    issuer_env: str
    audience_env: str
    client_id_env: str
    redirect_uris_env: str
    scopes_env: str
    userinfo_url_env: str
    default_scopes: str
    default_local_path: str


DEFAULT_OAUTH_SURFACE_ENV = OAuthSurfaceEnv(
    base_url_env="PUBLIC_MCP_BASE_URL",
    authorization_url_env="PUBLIC_OAUTH_AUTHORIZATION_URL",
    token_url_env="PUBLIC_OAUTH_TOKEN_URL",
    jwks_url_env="PUBLIC_OAUTH_JWKS_URL",
    registration_url_env="PUBLIC_OAUTH_REGISTRATION_URL",
    issuer_env="PUBLIC_OAUTH_ISSUER",
    audience_env="PUBLIC_OAUTH_AUDIENCE",
    client_id_env="PUBLIC_OAUTH_CLIENT_ID",
    redirect_uris_env="PUBLIC_OAUTH_REDIRECT_URIS",
    scopes_env="PUBLIC_OAUTH_SCOPES",
    userinfo_url_env="PUBLIC_OAUTH_USERINFO_URL",
    default_scopes="openid profile email",
    default_local_path="",
)


SUPABASE_MCP_OAUTH_SURFACE_ENV = OAuthSurfaceEnv(
    base_url_env="SUPABASE_MCP_PUBLIC_BASE_URL",
    authorization_url_env="SUPABASE_MCP_OAUTH_AUTHORIZATION_URL",
    token_url_env="SUPABASE_MCP_OAUTH_TOKEN_URL",
    jwks_url_env="SUPABASE_MCP_OAUTH_JWKS_URL",
    registration_url_env="SUPABASE_MCP_OAUTH_REGISTRATION_URL",
    issuer_env="SUPABASE_MCP_OAUTH_ISSUER",
    audience_env="SUPABASE_MCP_OAUTH_AUDIENCE",
    client_id_env="SUPABASE_MCP_OAUTH_CLIENT_ID",
    redirect_uris_env="SUPABASE_MCP_OAUTH_REDIRECT_URIS",
    scopes_env="SUPABASE_MCP_OAUTH_SCOPES",
    userinfo_url_env="SUPABASE_MCP_OAUTH_USERINFO_URL",
    default_scopes="openid profile email",
    default_local_path="/supabase-mcp",
)


GITHUB_MCP_OAUTH_SURFACE_ENV = OAuthSurfaceEnv(
    base_url_env="GITHUB_MCP_PUBLIC_BASE_URL",
    authorization_url_env="GITHUB_MCP_OAUTH_AUTHORIZATION_URL",
    token_url_env="GITHUB_MCP_OAUTH_TOKEN_URL",
    jwks_url_env="GITHUB_MCP_OAUTH_JWKS_URL",
    registration_url_env="GITHUB_MCP_OAUTH_REGISTRATION_URL",
    issuer_env="GITHUB_MCP_OAUTH_ISSUER",
    audience_env="GITHUB_MCP_OAUTH_AUDIENCE",
    client_id_env="GITHUB_MCP_OAUTH_CLIENT_ID",
    redirect_uris_env="GITHUB_MCP_OAUTH_REDIRECT_URIS",
    scopes_env="GITHUB_MCP_OAUTH_SCOPES",
    userinfo_url_env="GITHUB_MCP_OAUTH_USERINFO_URL",
    default_scopes="openid profile email",
    default_local_path="/github-mcp",
)


def _truthy_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_production_env() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() == "production"


def _local_test_auth_secret() -> str:
    default_secret = "local-test-auth-dev-only-secret-2026"
    return os.getenv("LOCAL_TEST_AUTH_SECRET", default_secret).strip() or default_secret


def _operator_bootstrap_token() -> str:
    return os.getenv("OPERATOR_BOOTSTRAP_TOKEN", "").strip()


def _operator_token_signing_secret() -> str:
    return os.getenv("OPERATOR_TOKEN_SIGNING_SECRET", "").strip()


def _validated_operator_token_signing_secret() -> str:
    secret = _operator_token_signing_secret()
    if len(secret) < 32:
        raise RuntimeError("OPERATOR_TOKEN_SIGNING_SECRET must be at least 32 characters")
    return secret


def _operator_token_email() -> str:
    email = os.getenv("OPERATOR_TOKEN_EMAIL", "operator-direct@apexpowerops.com").strip().lower()
    return email or "operator-direct@apexpowerops.com"


def _operator_token_label() -> str:
    label = os.getenv("OPERATOR_TOKEN_LABEL", "Operator Direct Access").strip()
    return label or "Operator Direct Access"


def _operator_token_user_id() -> UUID:
    raw = os.getenv("OPERATOR_TOKEN_USER_ID", "").strip()
    if raw:
        return UUID(raw)
    return uuid5(NAMESPACE_URL, _operator_token_email())


def _operator_token_ttl_minutes() -> int:
    raw = os.getenv("OPERATOR_TOKEN_TTL_MINUTES", "15").strip() or "15"
    try:
        ttl_minutes = int(raw)
    except ValueError as exc:
        raise RuntimeError("OPERATOR_TOKEN_TTL_MINUTES must be an integer") from exc

    if ttl_minutes < 1 or ttl_minutes > 1440:
        raise RuntimeError("OPERATOR_TOKEN_TTL_MINUTES must be between 1 and 1440")
    return ttl_minutes


def _load_test_auth_users() -> list[dict[str, str]]:
    raw = os.getenv("LOCAL_TEST_AUTH_USERS_JSON", "").strip()
    if not raw:
        return [dict(user) for user in _DEFAULT_TEST_AUTH_USERS]

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LOCAL_TEST_AUTH_USERS_JSON is not valid JSON") from exc

    if not isinstance(payload, list):
        raise RuntimeError("LOCAL_TEST_AUTH_USERS_JSON must be a JSON array")

    users: list[dict[str, str]] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise RuntimeError(f"LOCAL_TEST_AUTH_USERS_JSON[{index}] must be an object")
        email = str(entry.get("email", "")).strip().lower()
        user_id = str(entry.get("user_id", "")).strip()
        label = str(entry.get("label", email or f"Local Test User {index + 1}")).strip()
        if not email or not user_id:
            raise RuntimeError("Each local test auth user must include email and user_id")
        UUID(user_id)
        users.append({"email": email, "user_id": user_id, "label": label})

    return users


def is_local_test_auth_enabled() -> bool:
    if _is_production_env():
        return False
    return _truthy_env("ENABLE_LOCAL_TEST_AUTH", default=False)


def get_local_test_auth_users() -> list[dict[str, str]]:
    if not is_local_test_auth_enabled():
        return []
    return _load_test_auth_users()


def is_operator_token_auth_enabled() -> bool:
    return bool(_operator_bootstrap_token() and _operator_token_signing_secret())


def get_operator_token_auth_config() -> dict[str, Any]:
    configured = bool(_operator_bootstrap_token() and _operator_token_signing_secret())
    validation_errors: list[str] = []
    ttl_minutes: int | None = None
    user_id: str | None = None

    if configured:
        try:
            _validated_operator_token_signing_secret()
        except RuntimeError as exc:
            validation_errors.append(str(exc))

        try:
            ttl_minutes = _operator_token_ttl_minutes()
        except RuntimeError as exc:
            validation_errors.append(str(exc))

        try:
            user_id = str(_operator_token_user_id())
        except ValueError as exc:
            validation_errors.append(f"OPERATOR_TOKEN_USER_ID must be a valid UUID: {exc}")

    return {
        "enabled": configured and not validation_errors,
        "ttl_minutes": ttl_minutes,
        "email": _operator_token_email() if configured else None,
        "label": _operator_token_label() if configured else None,
        "user_id": user_id,
        "validation_errors": validation_errors,
    }


def get_public_auth_config() -> dict[str, Any]:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    supabase_enabled = bool(supabase_url and supabase_anon_key)

    users = [
        {"email": user["email"], "label": user["label"]}
        for user in get_local_test_auth_users()
    ]

    return {
        "enabled": supabase_enabled or bool(users),
        "supabase_enabled": supabase_enabled,
        "supabase_url": supabase_url if supabase_enabled else None,
        "supabase_anon_key": supabase_anon_key if supabase_enabled else None,
        "test_auth": {
            "enabled": bool(users),
            "users": users,
            "storage_key": _LOCAL_TEST_AUTH_STORAGE_KEY,
        },
        "operator_token": get_operator_token_auth_config(),
    }


def _is_loopback_host(hostname: Optional[str]) -> bool:
    if not hostname:
        return False
    normalized = hostname.strip().lower()
    return normalized in {"127.0.0.1", "::1", "localhost"}


def _looks_like_unresolved_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    return any(
        token in normalized
        for token in ("[project-ref]", "[password]", "[region]", "[local-password]", "change-me")
    )


def _normalize_absolute_url(value: str, *, name: str, require_https: bool) -> str:
    if _looks_like_unresolved_placeholder(value):
        raise RuntimeError(f"{name} must not use unresolved placeholder values")

    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an absolute http or https URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be an absolute http or https URL")

    if require_https and parsed.scheme != "https":
        raise RuntimeError(f"{name} must use https outside local development")

    if parsed.scheme == "http" and not _is_loopback_host(parsed.hostname):
        raise RuntimeError(f"{name} may only use http for localhost development")

    return parsed.geturl().rstrip("/")


def _normalize_issuer_url(value: str, *, name: str, require_https: bool) -> str:
    if _looks_like_unresolved_placeholder(value):
        raise RuntimeError(f"{name} must not use unresolved placeholder values")

    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an absolute http or https URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be an absolute http or https URL")

    if require_https and parsed.scheme != "https":
        raise RuntimeError(f"{name} must use https outside local development")

    if parsed.scheme == "http" and not _is_loopback_host(parsed.hostname):
        raise RuntimeError(f"{name} may only use http for localhost development")

    normalized = parsed._replace(params="", query="", fragment="")
    if normalized.path in {"", "/"}:
        return f"{normalized.scheme}://{normalized.netloc}/"
    return normalized.geturl().rstrip("/")


def _derive_issuer_from_known_endpoint(url: str) -> str | None:
    if _looks_like_unresolved_placeholder(url):
        return None

    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    suffixes = (
        "/oauth/authorize",
        "/authorize",
        "/oauth/token",
        "/.well-known/jwks.json",
    )
    for suffix in suffixes:
        if parsed.path.endswith(suffix):
            issuer_path = parsed.path[: -len(suffix)] or "/"
            return parsed._replace(path=issuer_path, params="", query="", fragment="").geturl()
    return None


def _resolve_oauth_issuer(surface_env: OAuthSurfaceEnv, *, require_https: bool) -> str | None:
    issuer_raw = os.getenv(surface_env.issuer_env, "").strip()
    if issuer_raw:
        return _normalize_issuer_url(
            issuer_raw,
            name=surface_env.issuer_env,
            require_https=require_https,
        )

    for name in (
        surface_env.authorization_url_env,
        surface_env.token_url_env,
        surface_env.jwks_url_env,
    ):
        candidate = os.getenv(name, "").strip()
        if not candidate:
            continue
        derived = _derive_issuer_from_known_endpoint(candidate)
        if derived:
            return _normalize_issuer_url(derived, name=f"derived {name} issuer", require_https=require_https)

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    if supabase_url:
        return _normalize_issuer_url(
            f"{supabase_url.rstrip('/')}/auth/v1",
            name="derived SUPABASE_URL issuer",
            require_https=require_https,
        )

    return None


def _resolve_public_oauth_issuer(*, require_https: bool) -> str | None:
    return _resolve_oauth_issuer(DEFAULT_OAUTH_SURFACE_ENV, require_https=require_https)


def _resolve_oauth_userinfo_url(surface_env: OAuthSurfaceEnv, *, require_https: bool) -> str | None:
    userinfo_raw = os.getenv(surface_env.userinfo_url_env, "").strip()
    if userinfo_raw:
        return _normalize_absolute_url(
            userinfo_raw,
            name=surface_env.userinfo_url_env,
            require_https=require_https,
        )

    issuer = _resolve_oauth_issuer(surface_env, require_https=require_https)
    if not issuer:
        return None

    return _normalize_absolute_url(
        urljoin(f"{issuer.rstrip('/')}/", "userinfo"),
        name=f"derived {surface_env.userinfo_url_env}",
        require_https=require_https,
    )


def _resolve_public_oauth_userinfo_url(*, require_https: bool) -> str | None:
    return _resolve_oauth_userinfo_url(DEFAULT_OAUTH_SURFACE_ENV, require_https=require_https)


def _parse_url_list_env(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []

    if raw.startswith("["):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{name} must be valid JSON when provided as an array") from exc
        if not isinstance(payload, list):
            raise RuntimeError(f"{name} must decode to a JSON array")
        return [str(item).strip() for item in payload if str(item).strip()]

    candidates = []
    for chunk in raw.replace("\r", "\n").split("\n"):
        candidates.extend(part.strip() for part in chunk.split(","))
    return [item for item in candidates if item]


def _normalize_redirect_uris(values: list[str], *, require_https: bool, env_name: str = "PUBLIC_OAUTH_REDIRECT_URIS") -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        uri = _normalize_absolute_url(
            value,
            name=f"{env_name}[{index}]",
            require_https=require_https,
        )
        if uri in seen:
            continue
        seen.add(uri)
        normalized.append(uri)
    return normalized


def _split_scopes(value: str) -> list[str]:
    normalized = value.strip()
    if normalized.startswith('"') and normalized.endswith('"') and len(normalized) >= 2:
        normalized = normalized[1:-1].strip()
    normalized = normalized.replace(",", " ")
    scopes = [scope.strip() for scope in normalized.split() if scope.strip()]
    return scopes or ["openid", "profile", "email"]


def describe_oauth_surface(
    surface_env: OAuthSurfaceEnv,
    request: FastAPIRequest | None = None,
) -> dict[str, Any]:
    require_https = _is_production_env()
    errors: list[str] = []

    public_base_url_raw = os.getenv(surface_env.base_url_env, "").strip()
    if not public_base_url_raw and request is not None and not require_https:
        public_base_url_raw = str(request.base_url).rstrip("/")
        if surface_env.default_local_path:
            public_base_url_raw = f"{public_base_url_raw}{surface_env.default_local_path}"

    public_base_url = None
    if public_base_url_raw:
        try:
            public_base_url = _normalize_absolute_url(
                public_base_url_raw,
                name=surface_env.base_url_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    issuer = None
    try:
        issuer = _resolve_oauth_issuer(surface_env, require_https=require_https)
    except RuntimeError as exc:
        errors.append(str(exc))

    authorization_url = None
    authorization_url_raw = os.getenv(surface_env.authorization_url_env, "").strip()
    if authorization_url_raw:
        try:
            authorization_url = _normalize_absolute_url(
                authorization_url_raw,
                name=surface_env.authorization_url_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    token_url = None
    token_url_raw = os.getenv(surface_env.token_url_env, "").strip()
    if token_url_raw:
        try:
            token_url = _normalize_absolute_url(
                token_url_raw,
                name=surface_env.token_url_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    jwks_url = None
    jwks_url_raw = os.getenv(surface_env.jwks_url_env, "").strip()
    if surface_env == DEFAULT_OAUTH_SURFACE_ENV and not jwks_url_raw:
        jwks_url_raw = os.getenv("SUPABASE_JWKS_URL", "").strip()
    if jwks_url_raw:
        try:
            jwks_url = _normalize_absolute_url(
                jwks_url_raw,
                name=surface_env.jwks_url_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    registration_url = None
    registration_url_raw = os.getenv(surface_env.registration_url_env, "").strip()
    if registration_url_raw:
        try:
            registration_url = _normalize_absolute_url(
                registration_url_raw,
                name=surface_env.registration_url_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    registered_redirect_uris: list[str] = []
    try:
        registered_redirect_uris = _normalize_redirect_uris(
            _parse_url_list_env(surface_env.redirect_uris_env),
            require_https=require_https,
            env_name=surface_env.redirect_uris_env,
        )
    except RuntimeError as exc:
        errors.append(str(exc))

    scopes_supported = _split_scopes(os.getenv(surface_env.scopes_env, surface_env.default_scopes))
    client_id = os.getenv(surface_env.client_id_env, "").strip() or None
    audience = os.getenv(surface_env.audience_env, "").strip() or None
    if audience:
        try:
            audience = _normalize_absolute_url(
                audience,
                name=surface_env.audience_env,
                require_https=require_https,
            )
        except RuntimeError as exc:
            errors.append(str(exc))
    discovery_url = f"{public_base_url}/.well-known/oauth-authorization-server" if public_base_url else None
    control_plane_url = f"{public_base_url}/api/v1/control-plane" if public_base_url else None
    mcp_root_url = f"{public_base_url}/mcp" if public_base_url else None

    oauth_discovery_ready = bool(
        public_base_url
        and issuer
        and authorization_url
        and token_url
        and jwks_url
        and not errors
    )
    public_activation_ready = bool(oauth_discovery_ready and registered_redirect_uris)

    return {
        "configured": oauth_discovery_ready,
        "public_activation_ready": public_activation_ready,
        "public_mcp_base_url": public_base_url,
        "mcp_root_url": mcp_root_url,
        "control_plane_url": control_plane_url,
        "issuer": issuer,
        "discovery_url": discovery_url,
        "authorization_url": authorization_url,
        "token_url": token_url,
        "jwks_url": jwks_url,
        "registration_url": registration_url,
        "audience": audience,
        "client_id": client_id,
        "registered_redirect_uris": registered_redirect_uris,
        "scopes_supported": scopes_supported,
        "validation_errors": errors,
    }


def describe_public_oauth_surface(request: FastAPIRequest | None = None) -> dict[str, Any]:
    return describe_oauth_surface(DEFAULT_OAUTH_SURFACE_ENV, request)


def get_oauth_server_metadata(
    surface_env: OAuthSurfaceEnv,
    request: FastAPIRequest | None = None,
) -> dict[str, Any]:
    surface = describe_oauth_surface(surface_env, request)
    if not surface["configured"]:
        errors = surface["validation_errors"] or [
            f"{surface_env.base_url_env}, {surface_env.authorization_url_env}, {surface_env.token_url_env}, and {surface_env.redirect_uris_env} must be configured"
        ]
        raise RuntimeError("; ".join(errors))

    return {
        "issuer": surface["issuer"],
        "authorization_endpoint": surface["authorization_url"],
        "token_endpoint": surface["token_url"],
        "jwks_uri": surface["jwks_url"],
        **({"registration_endpoint": surface["registration_url"]} if surface["registration_url"] else {}),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"],
        "scopes_supported": surface["scopes_supported"],
        "code_challenge_methods_supported": ["S256"],
        "response_modes_supported": ["query"],
    }


def get_public_oauth_server_metadata(request: FastAPIRequest | None = None) -> dict[str, Any]:
    return get_oauth_server_metadata(DEFAULT_OAUTH_SURFACE_ENV, request)


def get_oauth_protected_resource_metadata(
    surface_env: OAuthSurfaceEnv,
    request: FastAPIRequest | None = None,
) -> dict[str, Any]:
    surface = describe_oauth_surface(surface_env, request)
    if not surface["configured"]:
        errors = surface["validation_errors"] or [
            f"{surface_env.base_url_env}, {surface_env.authorization_url_env}, and {surface_env.token_url_env} must be configured"
        ]
        raise RuntimeError("; ".join(errors))

    return {
        "resource": surface["public_mcp_base_url"],
        "authorization_servers": [surface["issuer"]],
        "scopes_supported": surface["scopes_supported"],
    }


def get_public_oauth_protected_resource_metadata(
    request: FastAPIRequest | None = None,
) -> dict[str, Any]:
    return get_oauth_protected_resource_metadata(DEFAULT_OAUTH_SURFACE_ENV, request)


def build_www_authenticate_header_for_surface(
    surface_env: OAuthSurfaceEnv,
    request: FastAPIRequest | None = None,
) -> str:
    surface = describe_oauth_surface(surface_env, request)
    if surface["configured"] and surface["public_mcp_base_url"]:
        resource_metadata_url = f'{surface["public_mcp_base_url"]}/.well-known/oauth-protected-resource'
        return f'Bearer resource_metadata="{resource_metadata_url}"'
    return "Bearer"


def build_www_authenticate_header(request: FastAPIRequest | None = None) -> str:
    return build_www_authenticate_header_for_surface(DEFAULT_OAUTH_SURFACE_ENV, request)


def _build_local_test_auth_claims(user: dict[str, str], lifetime_minutes: int = 60) -> dict[str, Any]:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=lifetime_minutes)
    return {
        "sub": user["user_id"],
        "email": user["email"],
        "role": "authenticated",
        "iss": _LOCAL_TEST_AUTH_ISSUER,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }


def issue_local_test_auth_session(email: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    users_by_email = {user["email"]: user for user in get_local_test_auth_users()}
    user = users_by_email.get(normalized_email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown local test auth user")

    claims = _build_local_test_auth_claims(user)
    access_token = jwt.encode(claims, _local_test_auth_secret(), algorithm="HS256")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": claims["exp"],
        "user": {
            "id": user["user_id"],
            "email": user["email"],
            "role": "authenticated",
        },
        "provider": "local-test-auth",
    }


def _build_operator_token_claims() -> dict[str, Any]:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=_operator_token_ttl_minutes())
    return {
        "sub": str(_operator_token_user_id()),
        "email": _operator_token_email(),
        "role": "operator",
        "iss": _OPERATOR_TOKEN_ISSUER,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "auth_mode": "operator-token",
        "label": _operator_token_label(),
    }


def issue_operator_token_session(bootstrap_token: str) -> dict[str, Any]:
    if not is_operator_token_auth_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator token exchange is disabled")

    expected = _operator_bootstrap_token()
    provided = bootstrap_token.strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid operator bootstrap token")

    claims = _build_operator_token_claims()
    access_token = jwt.encode(claims, _validated_operator_token_signing_secret(), algorithm="HS256")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": claims["exp"],
        "user": {
            "id": claims["sub"],
            "email": claims["email"],
            "role": claims["role"],
            "label": claims["label"],
        },
        "provider": "operator-token",
    }


def ensure_local_test_auth_user_exists(db: Session, email: str) -> dict[str, str]:
    normalized_email = email.strip().lower()
    users_by_email = {user["email"]: user for user in get_local_test_auth_users()}
    user = users_by_email.get(normalized_email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown local test auth user")

    app_meta = json.dumps({"provider": "email", "providers": ["email"]})
    user_meta = json.dumps(
        {
            "sub": user["user_id"],
            "email": user["email"],
            "email_verified": True,
            "phone_verified": False,
        }
    )

    db.execute(
        text(
            """
            INSERT INTO auth.users (
                id,
                aud,
                role,
                email,
                encrypted_password,
                email_confirmed_at,
                raw_app_meta_data,
                raw_user_meta_data,
                created_at,
                updated_at,
                is_sso_user,
                is_anonymous
            )
            VALUES (
                CAST(:user_id AS uuid),
                'authenticated',
                'authenticated',
                :email,
                '',
                NOW(),
                CAST(:app_meta AS jsonb),
                CAST(:user_meta AS jsonb),
                NOW(),
                NOW(),
                FALSE,
                FALSE
            )
            ON CONFLICT (id) DO UPDATE
            SET email = EXCLUDED.email,
                raw_app_meta_data = EXCLUDED.raw_app_meta_data,
                raw_user_meta_data = EXCLUDED.raw_user_meta_data,
                updated_at = NOW()
            """
        ),
        {
            "user_id": user["user_id"],
            "email": user["email"],
            "app_meta": app_meta,
            "user_meta": user_meta,
        },
    )
    db.commit()
    return user


def assert_local_test_auth_request_allowed(request: FastAPIRequest) -> None:
    if not is_local_test_auth_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local test auth is disabled")

    client_host = request.client.host if request.client else None
    if client_host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local test auth is only available from localhost")


def _verify_local_test_jwt(token: str) -> AuthenticatedUser:
    claims = jwt.decode(
        token,
        _local_test_auth_secret(),
        algorithms=["HS256"],
        issuer=_LOCAL_TEST_AUTH_ISSUER,
        options={
            "require": ["sub", "exp", "iat", "iss"],
            "verify_aud": False,
        },
    )
    try:
        user_id = UUID(str(claims["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError("Local test JWT is missing a valid user subject") from exc

    return AuthenticatedUser(
        user_id=user_id,
        email=claims.get("email"),
        role=claims.get("role"),
        claims=claims,
    )


def _verify_operator_token(token: str) -> AuthenticatedUser:
    claims = jwt.decode(
        token,
        _validated_operator_token_signing_secret(),
        algorithms=["HS256"],
        issuer=_OPERATOR_TOKEN_ISSUER,
        options={
            "require": ["sub", "exp", "iat", "iss"],
            "verify_aud": False,
        },
    )
    try:
        user_id = UUID(str(claims["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidTokenError("Operator token is missing a valid user subject") from exc

    return AuthenticatedUser(
        user_id=user_id,
        email=claims.get("email"),
        role=claims.get("role"),
        claims=claims,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=16)
def _get_jwks_client_for_url(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _get_surface_jwks_url(surface_env: OAuthSurfaceEnv) -> str:
    jwks_url = os.getenv(surface_env.jwks_url_env, "").strip()
    if surface_env == DEFAULT_OAUTH_SURFACE_ENV and not jwks_url:
        jwks_url = os.getenv("SUPABASE_JWKS_URL", "").strip()
    if not jwks_url:
        if surface_env == DEFAULT_OAUTH_SURFACE_ENV:
            raise RuntimeError("Missing required environment variable: PUBLIC_OAUTH_JWKS_URL or SUPABASE_JWKS_URL")
        raise RuntimeError(f"Missing required environment variable: {surface_env.jwks_url_env}")
    return jwks_url


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    return _get_jwks_client_for_url(_get_surface_jwks_url(DEFAULT_OAUTH_SURFACE_ENV))


@lru_cache(maxsize=1)
def _get_issuer() -> str:
    issuer = _resolve_public_oauth_issuer(require_https=_is_production_env())
    if not issuer:
        raise RuntimeError("Missing required environment variable: PUBLIC_OAUTH_ISSUER or PUBLIC_OAUTH_AUTHORIZATION_URL")
    return issuer


def _get_surface_issuer(surface_env: OAuthSurfaceEnv) -> str:
    issuer = _resolve_oauth_issuer(surface_env, require_https=_is_production_env())
    if not issuer:
        raise RuntimeError(
            f"Missing required environment variable: {surface_env.issuer_env} or {surface_env.authorization_url_env}"
        )
    return issuer


@lru_cache(maxsize=1)
def _get_audience() -> str | None:
    raw = os.getenv("PUBLIC_OAUTH_AUDIENCE", "").strip()
    if not raw:
        return None
    return _normalize_absolute_url(
        raw,
        name="PUBLIC_OAUTH_AUDIENCE",
        require_https=_is_production_env(),
    )


def _get_surface_audience(surface_env: OAuthSurfaceEnv) -> str | None:
    raw = os.getenv(surface_env.audience_env, "").strip()
    if not raw:
        return None
    return _normalize_absolute_url(
        raw,
        name=surface_env.audience_env,
        require_https=_is_production_env(),
    )


def _stable_subject_uuid(subject: str, issuer: str | None) -> UUID:
    return uuid5(NAMESPACE_URL, f"{issuer or 'unknown-issuer'}::{subject}")


def _extract_user_id_from_subject(subject: Any, issuer: str | None) -> UUID:
    normalized = str(subject).strip()
    if not normalized:
        raise InvalidTokenError("JWT is missing a valid user subject")

    try:
        return UUID(normalized)
    except ValueError:
        return _stable_subject_uuid(normalized, issuer)


def _should_use_supabase_userinfo_fallback() -> bool:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    supabase_jwks_url = os.getenv("SUPABASE_JWKS_URL", "").strip()
    public_jwks_url = os.getenv("PUBLIC_OAUTH_JWKS_URL", "").strip()

    if not (supabase_url and supabase_anon_key and supabase_jwks_url):
        return False

    if public_jwks_url and public_jwks_url != supabase_jwks_url:
        return False

    try:
        supabase_issuer = _normalize_issuer_url(
            f"{supabase_url.rstrip('/')}/auth/v1",
            name="derived SUPABASE_URL issuer",
            require_https=_is_production_env(),
        )
    except RuntimeError:
        return False

    return _get_issuer() == supabase_issuer


@lru_cache(maxsize=1)
def _get_oidc_userinfo_url() -> str | None:
    return _resolve_public_oauth_userinfo_url(require_https=_is_production_env())


def _should_use_oidc_userinfo_fallback() -> bool:
    if _should_use_supabase_userinfo_fallback():
        return False
    return bool(_get_oidc_userinfo_url())


def _get_surface_oidc_userinfo_url(surface_env: OAuthSurfaceEnv) -> str | None:
    return _resolve_oauth_userinfo_url(surface_env, require_https=_is_production_env())


def _load_json_response(response: Any, *, source_name: str) -> dict[str, Any]:
    raw_payload = response.read()
    charset = "utf-8"
    headers = getattr(response, "headers", None)
    if headers is not None:
        get_content_charset = getattr(headers, "get_content_charset", None)
        if callable(get_content_charset):
            charset = get_content_charset() or charset

    try:
        payload = json.loads(raw_payload.decode(charset))
    except UnicodeDecodeError as exc:
        raise InvalidTokenError(f"{source_name} returned a non-text payload") from exc
    except json.JSONDecodeError as exc:
        raise InvalidTokenError(f"{source_name} returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise InvalidTokenError(f"{source_name} returned an invalid JSON object")
    return payload


def _verify_with_oidc_userinfo(token: str, *, surface_env: OAuthSurfaceEnv = DEFAULT_OAUTH_SURFACE_ENV) -> AuthenticatedUser:
    """Fallback validation for OAuth providers that issue opaque or encrypted access tokens."""
    userinfo_url = _get_surface_oidc_userinfo_url(surface_env)
    if not userinfo_url:
        raise InvalidTokenError("OAuth userinfo fallback is not configured")

    request = Request(
        userinfo_url,
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = _load_json_response(response, source_name="OAuth userinfo")
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise InvalidTokenError("OAuth provider rejected the bearer token") from exc
        raise RuntimeError(f"OAuth userinfo verification failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"OAuth userinfo endpoint is unreachable: {exc}") from exc

    try:
        user_id = _extract_user_id_from_subject(payload["sub"], _get_surface_issuer(surface_env))
    except (KeyError, TypeError, ValueError, InvalidTokenError) as exc:
        raise InvalidTokenError("OAuth userinfo payload is missing a valid subject") from exc

    claims = dict(payload)
    if "scope" not in claims and "permissions" not in claims:
        fallback_scopes = _split_scopes(os.getenv(surface_env.scopes_env, surface_env.default_scopes))
        if fallback_scopes:
            claims["scope"] = " ".join(fallback_scopes)

    return AuthenticatedUser(
        user_id=user_id,
        email=claims.get("email"),
        role=claims.get("role"),
        claims=claims,
    )


def _verify_with_supabase_userinfo(token: str) -> AuthenticatedUser:
    """Fallback validation for projects that do not expose JWKS keys."""
    supabase_url = _require_env("SUPABASE_URL").rstrip("/")
    apikey = _require_env("SUPABASE_ANON_KEY")
    request = Request(
        f"{supabase_url}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": apikey,
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = _load_json_response(response, source_name="Supabase userinfo")
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise InvalidTokenError("Supabase rejected the bearer token") from exc
        raise RuntimeError(f"Supabase auth verification failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Supabase auth verification endpoint is unreachable: {exc}") from exc

    try:
        user_id = _extract_user_id_from_subject(payload["id"], _get_issuer())
    except (KeyError, TypeError, ValueError, InvalidTokenError) as exc:
        raise InvalidTokenError("Supabase user payload is missing a valid id") from exc

    role = None
    if isinstance(payload.get("app_metadata"), dict):
        role = payload["app_metadata"].get("role")

    return AuthenticatedUser(
        user_id=user_id,
        email=payload.get("email"),
        role=role,
        claims=payload,
    )


def verify_bearer_jwt(token: str, *, surface_env: OAuthSurfaceEnv = DEFAULT_OAUTH_SURFACE_ENV) -> AuthenticatedUser:
    """Verify a configured OAuth bearer token and extract user identity."""
    if is_local_test_auth_enabled():
        try:
            return _verify_local_test_jwt(token)
        except InvalidTokenError:
            pass

    if is_operator_token_auth_enabled():
        try:
            return _verify_operator_token(token)
        except InvalidTokenError:
            pass

    issuer = _get_surface_issuer(surface_env)
    audience = _get_surface_audience(surface_env)

    try:
        signing_key = _get_jwks_client_for_url(_get_surface_jwks_url(surface_env)).get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": issuer,
            "options": {
                "require": ["sub", "exp", "iat", "iss"],
                "verify_aud": bool(audience),
            },
        }
        if audience:
            decode_kwargs["audience"] = audience

        claims = jwt.decode(token, signing_key.key, **decode_kwargs)

        try:
            user_id = _extract_user_id_from_subject(claims["sub"], issuer)
        except (KeyError, TypeError, ValueError, InvalidTokenError) as exc:
            raise InvalidTokenError("JWT is missing a valid user subject") from exc

        return AuthenticatedUser(
            user_id=user_id,
            email=claims.get("email"),
            role=claims.get("role"),
            claims=claims,
        )
    except (PyJWKSetError, PyJWKClientError) as exc:
        if surface_env == DEFAULT_OAUTH_SURFACE_ENV and _should_use_supabase_userinfo_fallback():
            return _verify_with_supabase_userinfo(token)
        if _get_surface_oidc_userinfo_url(surface_env):
            return _verify_with_oidc_userinfo(token, surface_env=surface_env)
        raise InvalidTokenError("OAuth JWKS verification failed") from exc
    except InvalidTokenError:
        if _get_surface_oidc_userinfo_url(surface_env):
            return _verify_with_oidc_userinfo(token, surface_env=surface_env)
        raise


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    return verify_bearer_jwt(token, surface_env=DEFAULT_OAUTH_SURFACE_ENV)


def get_current_user(
    request: FastAPIRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """FastAPI dependency that requires a valid Supabase bearer token."""
    authorization_header = None
    if credentials is not None:
        authorization_header = f"{credentials.scheme} {credentials.credentials}"
    return get_authenticated_user_from_authorization(request, authorization_header)


def get_authenticated_user_from_authorization(
    request: FastAPIRequest,
    authorization_header: str | None,
) -> AuthenticatedUser:
    return get_authenticated_user_from_authorization_for_surface(
        request,
        authorization_header,
        surface_env=DEFAULT_OAUTH_SURFACE_ENV,
    )


def get_authenticated_user_from_authorization_for_surface(
    request: FastAPIRequest,
    authorization_header: str | None,
    *,
    surface_env: OAuthSurfaceEnv,
) -> AuthenticatedUser:
    """Resolve an authenticated user from a raw Authorization header."""
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": build_www_authenticate_header_for_surface(surface_env, request)},
        )

    try:
        scheme, token = authorization_header.split(" ", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": build_www_authenticate_header_for_surface(surface_env, request)},
        ) from exc

    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": build_www_authenticate_header_for_surface(surface_env, request)},
        )

    try:
        return verify_bearer_jwt(token.strip(), surface_env=surface_env)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth verification is not configured: {exc}",
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid bearer token: {exc}",
            headers={"WWW-Authenticate": build_www_authenticate_header_for_surface(surface_env, request)},
        ) from exc


def _extract_scopes_from_claims(claims: dict[str, Any]) -> set[str]:
    scopes: set[str] = set()

    raw_scope = claims.get("scope")
    if isinstance(raw_scope, str):
        scopes.update(_split_scopes(raw_scope))

    raw_permissions = claims.get("permissions")
    if isinstance(raw_permissions, list):
        scopes.update(str(item).strip() for item in raw_permissions if str(item).strip())

    return scopes


def user_has_required_scopes(user: AuthenticatedUser, required_scopes: list[str]) -> bool:
    if not required_scopes:
        return True

    issuer = str(user.claims.get("iss") or "").strip()
    if issuer in {_LOCAL_TEST_AUTH_ISSUER, _OPERATOR_TOKEN_ISSUER}:
        return True

    granted = _extract_scopes_from_claims(user.claims)
    return all(scope in granted for scope in required_scopes)