"""
Ops Router — PM Idempotency Observability
==========================================
Packet: 2026-04-16-pm-schema-019g  (stats endpoint)
Packet: 2026-04-16-pm-schema-019i  (by-route endpoint)

Exposes the minimal operator-facing observability surface for the PM
idempotency seam (packets 019 + 019f).  Strictly read-only; strictly
mounted under ``/api/v1/ops/*`` so the ``/api/v1/work/*`` path count
stays unchanged at 15.

Endpoints authored here:

  * ``GET  /api/v1/ops/pm-idempotency/stats`` — returns
    ``{count, expired_count, oldest_expires_at, backend_kind}``.  No
    side effects.  Safe to scrape at arbitrary cadence by a
    monitoring system (Prometheus-style).  (packet 019g)

  * ``GET  /api/v1/ops/pm-idempotency/by-route`` — returns
    ``{by_route: [{route, count, expired_count, oldest_expires_at},
    ...], backend_kind}`` where ``by_route`` always carries exactly
    seven rows (one per pinned PM POST route in sorted order) with
    zero-padded counts for routes that currently have no entries.
    No side effects.  (packet 019i)

What this module intentionally does NOT add:

  * No new PM write endpoints.
  * No new PM entity write surfaces.
  * No mutation of ``pm.idempotency_keys`` shape.
  * No broadening of the seven PM POST handlers' request/response
    contract.
  * No writes to ``work.wbs_nodes``.
  * No second sweep implementation path; the sweep surface remains a
    CLI entrypoint (``scripts/sweep_pm_idempotency.py``, packet 019g)
    driven by the deployment-side schedule authored in packet 019h.

The sweep path (``idempotency_cache.sweep_expired()``) is deliberately
*not* exposed as an HTTP surface from this router.  Operators drive it
via the packaged CLI / cron / k8s-CronJob entrypoint at
``scripts/sweep_pm_idempotency.py`` (packet 019g) wired into the
``.github/workflows/pm-idempotency-sweep.yml`` scheduled workflow
(packet 019h).  This keeps the HTTP surface strictly read-only and
keeps POST count unchanged across the platform.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import get_db
from services.work.idempotency import idempotency_cache


router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class PMIdempotencyStats(BaseModel):
    """Minimal ops payload for the PM idempotency seam.

    Shape is pinned by the packet 019g prompt §Mission: the payload is
    ``{count, oldest_expires_at, backend_kind}`` plus an
    operationally-useful ``expired_count`` so dashboards can surface
    sweep pressure without a follow-up call.
    """

    count: int = Field(
        ...,
        description=(
            "Total rows in pm.idempotency_keys (durable) or entries in "
            "the in-memory dict, depending on backend_kind."
        ),
    )
    expired_count: int = Field(
        ...,
        description=(
            "Rows whose expires_at <= now(); these are eligible targets "
            "for the next sweep_expired() invocation."
        ),
    )
    oldest_expires_at: Optional[datetime] = Field(
        None,
        description=(
            "Earliest expires_at across all rows, or null when the "
            "store is empty."
        ),
    )
    backend_kind: str = Field(
        ...,
        description=(
            "Which backend is currently serving the seam — "
            "'in_memory' or 'durable'."
        ),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/pm-idempotency/stats",
    response_model=PMIdempotencyStats,
    summary="Minimal PM idempotency seam stats (read-only).",
)
def pm_idempotency_stats() -> PMIdempotencyStats:
    """Return ``{count, expired_count, oldest_expires_at, backend_kind}``.

    Strictly read-only.  Under the durable backend the call resolves to
    a single ``SELECT COUNT(*), COUNT(*) FILTER (...), MIN(expires_at)
    FROM pm.idempotency_keys`` round-trip; under the in-memory backend
    it iterates the local dict.  No DDL, no writes, no changes to the
    seven PM POST handler contracts.
    """
    payload = idempotency_cache.stats()
    return PMIdempotencyStats(**payload)


# ---------------------------------------------------------------------------
# Per-route response model (packet 019i)
# ---------------------------------------------------------------------------

class PMIdempotencyByRouteRow(BaseModel):
    """One row of per-route PM idempotency inventory.

    Shape is pinned: ``{route, count, expired_count,
    oldest_expires_at}``.  One row per pinned PM POST route; zero-padded
    when the route has no entries so the payload always carries exactly
    the seven routes in sorted order.
    """

    route: str = Field(
        ...,
        description=(
            "One of the seven PM POST routes: /projects, /work-packages, "
            "/tasks, /assignments, /dependencies, /execution-issues, "
            "/progress-snapshots."
        ),
    )
    count: int = Field(
        ...,
        description=(
            "Total rows in pm.idempotency_keys for this route (durable), "
            "or in-memory entries for this route (in_memory)."
        ),
    )
    expired_count: int = Field(
        ...,
        description=(
            "Rows for this route whose expires_at <= now(); eligible "
            "targets for the next sweep_expired() invocation."
        ),
    )
    oldest_expires_at: Optional[datetime] = Field(
        None,
        description=(
            "Earliest expires_at across this route's rows, or null "
            "when the route has no entries."
        ),
    )


class PMIdempotencyByRoute(BaseModel):
    """Per-route PM idempotency inventory payload.

    ``by_route`` is always exactly seven rows, one per pinned PM POST
    route, sorted lexicographically.  Operators can spot hot routes or
    expiry pressure on individual handlers without widening the PM
    write surface or introducing a second observability path.
    """

    by_route: List[PMIdempotencyByRouteRow] = Field(
        ...,
        description=(
            "Per-route inventory.  Exactly seven rows, one per pinned "
            "PM POST route, sorted by route."
        ),
    )
    backend_kind: str = Field(
        ...,
        description=(
            "Which backend is currently serving the seam — "
            "'in_memory' or 'durable'."
        ),
    )


class MasterOperationsSummary(BaseModel):
    """Read-only summary row from ``public.v_master_operations``."""

    project_id: str = Field(..., description="Project UUID from the Operations Visibility dashboard view.")
    project_number: Optional[str] = Field(None, description="Human-readable project number.")
    project_name: Optional[str] = Field(None, description="Human-readable project name.")
    project_status: Optional[str] = Field(None, description="Current project status.")
    client_name: Optional[str] = Field(None, description="Client company name.")
    resa_location: Optional[str] = Field(None, description="RESA location serving the project.")
    site_city: Optional[str] = Field(None, description="Job site city.")
    project_due: Optional[date] = Field(None, description="Contractual project due date.")
    scope_count: int = Field(..., description="Total active scope count represented in the rollup.")
    total_apparatus: int = Field(..., description="Total apparatus count represented in the rollup.")
    completed: int = Field(..., description="Completed apparatus count.")
    remaining: int = Field(..., description="Remaining apparatus count.")
    completion_percent: float = Field(..., description="Calculated apparatus completion percent.")
    ready_to_work: int = Field(..., description="Ready-to-work apparatus count.")
    on_hold: int = Field(..., description="On-hold apparatus count.")
    not_available: int = Field(..., description="Not-available apparatus count.")
    issues: int = Field(..., description="Apparatus count with failing or non-serviceable assessment.")
    overdue: int = Field(..., description="Overdue apparatus count.")
    due_today: int = Field(..., description="Apparatus due today.")
    due_this_week: int = Field(..., description="Apparatus due within the next week.")
    ready_hours: float = Field(..., description="Quoted hours currently ready to execute.")
    remaining_hours: float = Field(..., description="Quoted hours still remaining on the project.")
    health_status: str = Field(..., description="Derived health classification from the view.")


@router.get(
    "/pm-idempotency/by-route",
    response_model=PMIdempotencyByRoute,
    summary="Per-route PM idempotency inventory (read-only).",
)
def pm_idempotency_by_route() -> PMIdempotencyByRoute:
    """Return ``{by_route: [...], backend_kind}`` with exactly seven rows.

    One row per pinned PM POST route in sorted order.  Zero-padded rows
    for routes with no current entries so the payload shape is stable
    regardless of backend state.  Strictly read-only: under the durable
    backend the call resolves to a single ``SELECT route, COUNT(*),
    COUNT(*) FILTER (...), MIN(expires_at) FROM pm.idempotency_keys
    GROUP BY route`` round-trip; under the in-memory backend it
    iterates the local dict once.  No DDL; no writes; no changes to
    the seven PM POST handler contracts.
    """
    payload = idempotency_cache.stats_by_route()
    return PMIdempotencyByRoute(**payload)


@router.get(
    "/master-operations",
    response_model=list[MasterOperationsSummary],
    summary="Operations Visibility master dashboard rollup (read-only).",
)
def master_operations_summary(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[MasterOperationsSummary]:
    """Return bounded rows from ``public.v_master_operations``.

    This keeps browser consumption behind the governed control-plane API
    instead of reopening direct browser-side Supabase reads.
    """

    rows = (
        db.execute(
            text(
                """
                SELECT
                    project_id,
                    project_number,
                    project_name,
                    project_status,
                    client_name,
                    resa_location,
                    site_city,
                    project_due,
                    scope_count,
                    total_apparatus,
                    completed,
                    remaining,
                    completion_percent,
                    ready_to_work,
                    on_hold,
                    not_available,
                    issues,
                    overdue,
                    due_today,
                    due_this_week,
                    ready_hours,
                    remaining_hours,
                    health_status
                FROM public.v_master_operations
                LIMIT :limit
                """
            ),
            {"limit": limit},
        )
        .mappings()
        .all()
    )
    return [MasterOperationsSummary(**row) for row in rows]
