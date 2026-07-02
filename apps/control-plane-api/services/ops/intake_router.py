"""
Ops Intake Router -- Task 13.

5 routes under /api/v1/ops/intake:
  POST   ""              -- upload workbook (multipart)
  GET    /{run_id}       -- get run (PM-safe)
  POST   /{run_id}/review  -- patch review payload
  POST   /{run_id}/approve -- approve run
  POST   /{run_id}/reject  -- reject run

Finance-redaction rule: every finding sent to the PM surface carries only
{code, severity, ok, message}; diagnostic_detail is NEVER returned.  All
dollar figures live in diagnostic_detail only, so PM never sees them.

The _pm_finding() helper enforces the contract for every findings list in
every route handler.  Adding it centrally ensures it cannot be forgotten on
one route.

DB connection: os.environ["OPS_INTAKE_WRITER_DSN"] -- set by the caller (not prod
resolve_database_url(); this router is import-gated by _ops_intake_enabled
in main.py which requires both OPS_INTAKE_WRITER_DSN and OPS_API_DSN to be set).
"""
from __future__ import annotations

import os
from typing import Any

import psycopg
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from ops_intake.approve import approve_run
from ops_intake.envelope import (
    ActiveRunExists,
    RunNotActive,
    create_run,
    create_run_native,
    get_run,
    patch_review,
    reject_run,
)

# content_type values the DB CHECK (mig 007) accepts; anything else is a 422 at the boundary so a
# stale/adversarial client can never turn an unexpected value into a DB constraint failure (500).
_ALLOWED_CONTENT_TYPES = {"xlsm", "json"}

router = APIRouter(prefix="/api/v1/ops/intake", tags=["ops-intake"])

_MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


def _dsn() -> str:
    return os.environ["OPS_INTAKE_WRITER_DSN"]


def _pm_finding(f: dict) -> dict:
    """Shape a finding for the PM surface: keep only {code, severity, ok, message}.

    diagnostic_detail is intentionally dropped -- it may contain dollar figures
    that must not reach the PM.
    """
    return {
        "code": f["code"],
        "severity": f["severity"],
        "ok": f["ok"],
        "message": f["message"],
    }


def _pm_findings(findings: list[dict]) -> list[dict]:
    return [_pm_finding(f) for f in findings]


# ---------------------------------------------------------------------------
# POST "" -- upload workbook
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_200_OK)
async def upload_workbook(
    file: UploadFile,
    uploaded_by: str = Form(...),
    content_type: str = Form(...),
) -> JSONResponse:
    """Upload an estimator workbook and create an intake run.

    Enforces 25 MB cap before reading.  Returns PM-safe run summary.
    """
    # Validate content_type at the boundary (the DB CHECK only accepts xlsm|json). A 422 here keeps a
    # stale/adversarial value from becoming a DB constraint failure (500) downstream.
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="content_type must be one of: xlsm, json",
        )

    # Enforce size cap before reading the body (check Content-Length via size
    # if provided by the client, then verify after reading).
    if file.size is not None and file.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 25 MB limit",
        )

    raw_bytes = await file.read()

    if len(raw_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 25 MB limit",
        )

    try:
        result = create_run(
            _dsn(),
            uploaded_by=uploaded_by,
            filename=file.filename or "upload",
            raw_bytes=raw_bytes,
            content_type=content_type,
        )
    except ActiveRunExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except psycopg.errors.ForeignKeyViolation:
        # uploaded_by must reference a known ops.persons row -- a clean 400, not an uncaught 500.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded_by is not a known person (configure a valid ops.persons UUID)",
        )

    return JSONResponse(
        {
            "run_id": result["run_id"],
            "status": result["status"],
            "conflict_kind": result["conflict_kind"],
            "source_format": result["source_format"],
            "review_payload": result["review_payload"],
            "findings": _pm_findings(result["findings"]),
        }
    )


# ---------------------------------------------------------------------------
# GET /{run_id} -- get run (PM-safe)
# ---------------------------------------------------------------------------


@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_run_route(run_id: str) -> JSONResponse:
    """Return a run by ID with PM-safe findings (no diagnostic_detail)."""
    try:
        run = get_run(_dsn(), run_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="run not found: " + run_id,
        )

    # Shape findings PM-safe before returning
    run = dict(run)
    run["findings"] = _pm_findings(run.get("findings") or [])
    return JSONResponse(run)


# ---------------------------------------------------------------------------
# POST /{run_id}/review -- patch review payload
# ---------------------------------------------------------------------------


@router.post("/{run_id}/review", status_code=status.HTTP_200_OK)
async def post_review(run_id: str, request: Request) -> JSONResponse:
    """Patch the review payload for a run.

    409 if the run is not in an active status (parsed/reviewing).
    400 if the review_payload violates the allowlist or cross-scope guard.
    """
    body: dict[str, Any] = await request.json()
    review_payload = body.get("review_payload")
    if review_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="review_payload is required",
        )

    # Check run status first to distinguish 409-inactive from 400-guard.
    try:
        current = get_run(_dsn(), run_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="run not found: " + run_id,
        )

    active_statuses = {"parsed", "reviewing"}
    if current["status"] not in active_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="run " + run_id + " is not active (status=" + current["status"] + ")",
        )

    try:
        updated = patch_review(_dsn(), run_id, review_payload=review_payload)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="run not found: " + run_id,
        )
    except RunNotActive:
        # Lifecycle race: the run was approved/rejected/superseded between the status check and the
        # FOR UPDATE lock inside patch_review. A controlled 409, not a 400.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="run " + run_id + " is no longer active",
        )
    except ValueError:
        # GENERIC PM-safe detail -- NEVER str(exc). The allowlist/cross-scope guards can reference the
        # quote dollar basis; returning the raw message would leak protected values to the PM surface.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Review edit rejected: only the task grouping (section) and hours-per-unit are "
                    "editable; every other field must match the parsed quote."),
        )

    updated = dict(updated)
    updated["findings"] = _pm_findings(updated.get("findings") or [])
    return JSONResponse(updated)


# ---------------------------------------------------------------------------
# POST /{run_id}/approve -- approve run
# ---------------------------------------------------------------------------


@router.post("/{run_id}/approve", status_code=status.HTTP_200_OK)
async def post_approve(run_id: str, request: Request) -> JSONResponse:
    """Approve a run.

    outcome mapping:
      approved         -> 200 {status: "approved"}
      blocked_findings -> 422 (open blocking findings)
      revision_blocked, not_active, foreign_source -> 409
    Unknown run_id -> 404.
    """
    body: dict[str, Any] = await request.json()
    approved_by = body.get("approved_by")
    if not approved_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="approved_by is required",
        )

    try:
        result = approve_run(_dsn(), run_id, approved_by=approved_by)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="run not found: " + run_id,
        )
    except psycopg.errors.ForeignKeyViolation:
        # approved_by must reference a known ops.persons row -- a clean 400, not an uncaught 500.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="approved_by is not a known person (configure a valid ops.persons UUID)",
        )

    outcome = result.get("outcome")

    if outcome == "approved":
        return JSONResponse({"status": "approved", "run_id": run_id})

    if outcome == "blocked_findings":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"outcome": outcome, "run_id": run_id},
        )

    # revision_blocked / not_active / foreign_source -> 409
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"outcome": outcome, **{k: v for k, v in result.items() if k != "outcome"}},
    )


# ---------------------------------------------------------------------------
# POST /{run_id}/reject -- reject run
# ---------------------------------------------------------------------------


@router.post("/{run_id}/reject", status_code=status.HTTP_200_OK)
async def post_reject(run_id: str, request: Request) -> JSONResponse:
    """Reject an active intake run.

    404 if unknown.  409 if the run is not in an active status.
    """
    body: dict[str, Any] = await request.json()
    reason = body.get("reason", "")

    try:
        updated = reject_run(_dsn(), run_id, reason=reason)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="run not found: " + run_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    updated = dict(updated)
    updated["findings"] = _pm_findings(updated.get("findings") or [])
    return JSONResponse(updated)


# ---------------------------------------------------------------------------
# POST /native -- create native intake run from compiled EstimateEnvelope
# ---------------------------------------------------------------------------


@router.post("/native", status_code=status.HTTP_200_OK)
async def upload_native_envelope(request: Request) -> JSONResponse:
    """Create a native (estimator) intake run from a compiled EstimateEnvelope (catalog-only v1).
    Body: {uploaded_by: uuid, envelope: <EstimateEnvelope JSON>}. Returns the PM-safe run summary."""
    body: dict[str, Any] = await request.json()
    uploaded_by = body.get("uploaded_by")
    envelope = body.get("envelope")
    if not uploaded_by or not isinstance(envelope, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="uploaded_by and envelope (object) are required")
    try:
        result = create_run_native(_dsn(), uploaded_by=uploaded_by, envelope=envelope)
    except ActiveRunExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="uploaded_by is not a known person")
    return JSONResponse({
        "run_id": result["run_id"], "status": result["status"],
        "conflict_kind": result["conflict_kind"], "source_format": result["source_format"],
        "findings": _pm_findings(result["findings"]),
    })
