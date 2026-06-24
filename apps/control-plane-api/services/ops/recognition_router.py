"""Ops Recognition Router — host-gated ops_dev bridge (Slice 1).

6 routes under /api/v1/ops/recognition, distinct from the prod derive-on-read
/api/v1/ops/revenue-recognition. Mounted only when OPS_DEV_DSN is set (main.py
_ops_intake_enabled). All mutations flow through the ops_intake.recognition
wrappers (sole-writer); errors are VALUE-FREE generic 400/409.
"""
from __future__ import annotations
import os
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ops_intake import recognition as rec

router = APIRouter(prefix="/api/v1/ops/recognition", tags=["ops-recognition"])

_CLEARANCE_ENUM = {"provided", "not_applicable"}

def _dsn() -> str:
    return os.environ["OPS_DEV_DSN"]

def _map(exc: rec.RecognitionError) -> HTTPException:
    if isinstance(exc, rec.RecognitionInputError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    # RecognitionConflict + RecognitionStateError -> 409
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

def _require(body: dict, *keys: str) -> None:
    for k in keys:
        if body.get(k) in (None, ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{k} is required")

@router.post("/completion/attest", status_code=status.HTTP_200_OK)
async def attest(request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    _require(body, "apparatus_id", "attested_by", "reason")
    try:
        att = rec.attest_complete(_dsn(), body["apparatus_id"], body["attested_by"], body["reason"])
    except rec.RecognitionError as e:
        raise _map(e)
    return JSONResponse({"attestation_id": att})

@router.post("/completion/{attestation_id}/revoke", status_code=status.HTTP_200_OK)
async def revoke(attestation_id: str, request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    _require(body, "revoked_by", "reason")
    try:
        out = rec.revoke(_dsn(), attestation_id, body["revoked_by"], body["reason"])
    except rec.RecognitionError as e:
        raise _map(e)
    return JSONResponse({"attestation_id": out})

@router.post("/events/recognize", status_code=status.HTTP_200_OK)
async def recognize(request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    _require(body, "apparatus_id", "recognized_by", "datasheet_clearance", "cx_clearance")
    # value-free enum validation at the boundary (never a raw PG cast error)
    for k in ("datasheet_clearance", "cx_clearance"):
        if body[k] not in _CLEARANCE_ENUM:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="clearance must be one of: provided, not_applicable")
    try:
        ev = rec.recognize(_dsn(), body["apparatus_id"], body["recognized_by"],
                           body["datasheet_clearance"], body.get("datasheet_ref"),
                           body["cx_clearance"], body.get("cx_ref"))
    except rec.RecognitionError as e:
        raise _map(e)
    return JSONResponse({"event_id": ev})

@router.post("/events/{event_id}/reverse", status_code=status.HTTP_200_OK)
async def reverse(event_id: str, request: Request) -> JSONResponse:
    body: dict[str, Any] = await request.json()
    _require(body, "reversed_by", "reason")
    try:
        rv = rec.reverse(_dsn(), event_id, body["reversed_by"], body["reason"])
    except rec.RecognitionError as e:
        raise _map(e)
    return JSONResponse({"reversal_id": rv})

def _read_view(view: str, project_number: str | None) -> list[dict]:
    sql = f"select * from ops.{view}"
    params: tuple = ()
    if project_number:
        sql += " where project_number = %s"
        params = (project_number,)
    with psycopg.connect(_dsn()) as c, c.cursor() as cur:
        cur.execute(sql, params)
        cols = [d.name for d in cur.description]
        # jsonable_encoder normalizes EVERY psycopg-adapted type that JSONResponse(json.dumps)
        # would choke on: uuid.UUID -> str, Decimal (numeric: quoted_revenue / net_recognized /
        # recognized_total) -> number, datetime/timestamptz -> isoformat str. The prior
        # `str(v) if hasattr(v,'isoformat')` cast MISSED both UUID and Decimal -> 500 on /worklist+/rollup.
        return [jsonable_encoder(dict(zip(cols, row))) for row in cur.fetchall()]

@router.get("/worklist", status_code=status.HTTP_200_OK)
def worklist(project_number: str | None = None) -> JSONResponse:
    return JSONResponse(_read_view("v_completion_recognition_worklist", project_number))

@router.get("/rollup", status_code=status.HTTP_200_OK)
def rollup(project_number: str | None = None) -> JSONResponse:
    return JSONResponse(_read_view("v_completion_recognition_rollup", project_number))
