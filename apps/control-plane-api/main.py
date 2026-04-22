"""
Apex Power Ops Platform API — FastAPI Application

Health contract:
  GET /health       — Liveness: the app process is up and serving requests.
  GET /health/ready — Readiness: the app can reach the Supabase database.
"""
import logging
import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import get_db
from services.calc_engine.router import router as calc_router
from services.auth import (
    assert_local_test_auth_request_allowed,
    get_public_oauth_protected_resource_metadata,
    describe_public_oauth_surface,
    GITHUB_MCP_OAUTH_SURFACE_ENV,
    get_oauth_protected_resource_metadata,
    get_oauth_server_metadata,
    ensure_local_test_auth_user_exists,
    get_local_test_auth_users,
    get_public_auth_config,
    get_public_oauth_server_metadata,
    issue_operator_token_session,
    issue_local_test_auth_session,
    SUPABASE_MCP_OAUTH_SURFACE_ENV,
)
from services.control_plane.router import router as control_plane_router
from services.github_mcp_server import (
    build_github_mcp_root_payload,
    handle_get_github_mcp,
    handle_post_github_mcp,
)
from services.mcp_server import build_mcp_root_payload, handle_get_mcp, handle_post_mcp
from services.neta.router import router as neta_router
from services.neta.plans import router as plans_router
from services.work.router import router as work_router
from services.ops.router import router as ops_router
from services.supabase_mcp_server import (
    build_supabase_mcp_root_payload,
    handle_get_supabase_mcp,
    handle_post_supabase_mcp,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Apex Power Ops Platform API",
    version="5.2.0",
    description="Platform control-plane, governed MCP, and calculation surfaces "
                "for Apex Power Ops.",
)

app.include_router(calc_router)
app.include_router(control_plane_router)
app.include_router(neta_router)
app.include_router(plans_router)
app.include_router(work_router)
# ── Ops lane (packet 019g) ──
# Strictly outside ``/api/v1/work/*``.  Adds the minimal PM idempotency
# stats surface at ``GET /api/v1/ops/pm-idempotency/stats`` and nothing
# else; the work schema registry stays at 22 and the
# ``/api/v1/work/*`` path count stays at 15.
app.include_router(ops_router)

# ── PM idempotency seam: swap to durable DB-backed backend ──
# Packet 2026-04-16-pm-schema-019f
# The ``idempotency_cache`` singleton starts on the process-local
# in-memory backend (packet 019 behaviour) so that import order stays
# safe; here we upgrade it to the durable ``pm.idempotency_keys`` store
# backed by ``config.SessionLocal``.  The upgrade is wrapped in a
# try/except so a misconfigured DATABASE_URL (e.g. during local tooling)
# falls back cleanly to in-memory rather than crashing app import —
# tests that need the durable path swap it back in their fixtures.
try:
    from config import SessionLocal as _PMIdempotencySessionLocal
    from services.work.idempotency import (
        idempotency_cache as _pm_idempotency_cache,
    )

    _pm_idempotency_cache.use_durable_backend(_PMIdempotencySessionLocal)
except Exception as _pm_idempotency_exc:  # pragma: no cover - defensive
    logger.warning(
        "PM idempotency cache remaining on in-memory backend: %s",
        _pm_idempotency_exc,
    )

# ── Demo page ──
_DEMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo")


class TestAuthSessionRequest(BaseModel):
    email: str


class OperatorTokenExchangeRequest(BaseModel):
    bootstrap_token: str


class TestAuthResetRequest(BaseModel):
    email: str
    project: Optional[str] = "neta-demo"


@app.get("/")
def root_status():
    """Return a simple 200 root response for platform probes and operators."""
    return {"service": "apex-platform-control-plane-api", "status": "ok"}


@app.get("/demo/neta-tcc")
def demo_neta_tcc():
    """Serve the internal NETA TCC demo page."""
    return FileResponse(
        os.path.join(_DEMO_DIR, "neta_tcc.html"),
        media_type="text/html",
    )


@app.get("/oauth/consent")
def oauth_consent_page():
    """Serve the OAuth consent page used by the public Supabase OAuth server."""
    return FileResponse(
        os.path.join(_DEMO_DIR, "oauth_consent.html"),
        media_type="text/html",
    )


@app.get("/api/v1/auth/config")
def auth_config(request: Request):
    """Return the public Supabase auth config needed by the demo UI."""
    email_redirect_to = os.getenv("SUPABASE_EMAIL_REDIRECT_URL", "").strip()
    if not email_redirect_to:
        email_redirect_to = str(request.url_for("demo_neta_tcc"))

    config = get_public_auth_config()
    config["email_redirect_to"] = email_redirect_to
    config["desktop_oauth"] = describe_public_oauth_surface(request)
    return config


@app.get("/api/v1/auth/public-desktop-config")
def auth_public_desktop_config(request: Request):
    """Return the current public Desktop OAuth and MCP surface description."""
    return describe_public_oauth_surface(request)


@app.get("/.well-known/oauth-authorization-server")
def oauth_authorization_server_metadata(request: Request):
    """Expose OAuth discovery metadata when the public Desktop surface is configured."""
    try:
        return get_public_oauth_server_metadata(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/.well-known/oauth-protected-resource")
def oauth_protected_resource_metadata(request: Request):
    """Expose MCP protected-resource metadata for ChatGPT/Desktop OAuth discovery."""
    try:
        return get_public_oauth_protected_resource_metadata(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/mcp")
def mcp_root_metadata(request: Request):
    """Expose discovery metadata for operators and non-protocol health checks."""
    return handle_get_mcp(request)


@app.post("/mcp")
async def mcp_transport(request: Request, db: Session = Depends(get_db)):
    """Streamable HTTP MCP entrypoint for initialize, tools/list, and tools/call."""
    return await handle_post_mcp(request, db)


@app.get("/supabase-mcp")
def supabase_mcp_root_metadata(request: Request):
    """Expose discovery metadata for the dedicated Supabase MCP surface."""
    return handle_get_supabase_mcp(request)


@app.post("/supabase-mcp")
async def supabase_mcp_transport(request: Request, db: Session = Depends(get_db)):
    """Streamable HTTP MCP entrypoint for the dedicated Supabase MCP surface."""
    return await handle_post_supabase_mcp(request, db)


@app.get("/github-mcp")
def github_mcp_root_metadata(request: Request):
    """Expose discovery metadata for the dedicated GitHub MCP surface."""
    return handle_get_github_mcp(request)


@app.post("/github-mcp")
async def github_mcp_transport(request: Request, db: Session = Depends(get_db)):
    """Streamable HTTP MCP entrypoint for the dedicated GitHub MCP surface."""
    return await handle_post_github_mcp(request, db)


@app.get("/supabase-mcp/.well-known/oauth-authorization-server")
def supabase_oauth_authorization_server_metadata(request: Request):
    """Expose OAuth discovery metadata for the dedicated Supabase MCP surface."""
    try:
        return get_oauth_server_metadata(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/supabase-mcp/.well-known/oauth-protected-resource")
def supabase_oauth_protected_resource_metadata(request: Request):
    """Expose protected-resource metadata for the dedicated Supabase MCP surface."""
    try:
        return get_oauth_protected_resource_metadata(SUPABASE_MCP_OAUTH_SURFACE_ENV, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/github-mcp/.well-known/oauth-authorization-server")
def github_oauth_authorization_server_metadata(request: Request):
    """Expose OAuth discovery metadata for the dedicated GitHub MCP surface."""
    try:
        return get_oauth_server_metadata(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/github-mcp/.well-known/oauth-protected-resource")
def github_oauth_protected_resource_metadata(request: Request):
    """Expose protected-resource metadata for the dedicated GitHub MCP surface."""
    try:
        return get_oauth_protected_resource_metadata(GITHUB_MCP_OAUTH_SURFACE_ENV, request)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/auth/test-session")
def auth_test_session(
    payload: TestAuthSessionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Return a local-only authenticated session for browser automation.

    This endpoint is only available when local test auth is explicitly enabled
    and the request originates from localhost. It is intended for unattended
    browser testing in development only.
    """
    assert_local_test_auth_request_allowed(request)

    try:
        ensure_local_test_auth_user_exists(db, payload.email)
        return issue_local_test_auth_session(payload.email)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/auth/operator-token")
def auth_operator_token(payload: OperatorTokenExchangeRequest):
    """Exchange a configured bootstrap secret for a short-lived operator bearer token."""
    try:
        return issue_operator_token_session(payload.bootstrap_token)
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/v1/auth/test-reset")
def auth_test_reset(
    payload: TestAuthResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete demo plans/results for a deterministic local test user.

    This is intended for unattended browser tests so repeated runs can start
    from a known-clean state without manual database cleanup.
    """
    assert_local_test_auth_request_allowed(request)

    users_by_email = {user["email"]: user for user in get_local_test_auth_users()}
    user = users_by_email.get(payload.email.strip().lower())
    if user is None:
        raise HTTPException(status_code=403, detail="Unknown local test auth user")

    project = (payload.project or "neta-demo").strip() or "neta-demo"

    try:
        deleted_results = db.execute(
            text(
                """
                DELETE FROM tcc_test_results r
                WHERE EXISTS (
                    SELECT 1
                    FROM tcc_test_plans p
                    WHERE p.id = r.plan_id
                      AND p.project = :project
                      AND p.user_id = CAST(:user_id AS uuid)
                )
                """
            ),
            {"project": project, "user_id": user["user_id"]},
        ).rowcount or 0

        deleted_plans = db.execute(
            text(
                """
                DELETE FROM tcc_test_plans
                WHERE project = :project
                  AND user_id = CAST(:user_id AS uuid)
                """
            ),
            {"project": project, "user_id": user["user_id"]},
        ).rowcount or 0

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=f"Local test auth reset failed: {exc}") from exc

    return {
        "email": user["email"],
        "project": project,
        "deleted_results": deleted_results,
        "deleted_plans": deleted_plans,
    }


# ── Health: Liveness ──

@app.get("/health")
def health():
    """Liveness probe — the app process is running and can serve HTTP."""
    return {"status": "ok"}


@app.get("/health/live")
def health_live():
    """Explicit liveness alias — identical to /health."""
    return {"status": "ok"}


# ── Health: Readiness ──

@app.get("/health/ready")
def health_ready():
    """Readiness probe — can the app reach the Supabase database?

    Returns 200 with database details when reachable, or 200 with
    ready=false and an error description when not.  We intentionally
    return 200 in both cases so monitoring can distinguish
    'app is down' (liveness fails) from 'database is unreachable'
    (readiness reports not-ready).
    """
    from config import engine  # late import to avoid circular at module level

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Also check that the catalog view exists (meaningful readiness)
            row = conn.execute(
                text(
                    "SELECT COUNT(*) AS n "
                    "FROM information_schema.views "
                    "WHERE table_name = 'vw_trip_unit_cascade'"
                )
            ).fetchone()
            catalog_available = row is not None and row[0] > 0
        return {
            "status": "ready",
            "database": "connected",
            "catalog_available": catalog_available,
        }
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return {
            "status": "not_ready",
            "database": "unreachable",
            "catalog_available": False,
            "error": str(exc),
        }
