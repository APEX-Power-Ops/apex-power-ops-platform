"""
Read-only SQL helpers for the `schedule.*` tables — packet UI-002a.

Design posture
--------------
Every helper opens a SHORT-LIVED connection from a lazily-instantiated pool
stub and runs a READ-ONLY SQL statement. There is no `UPDATE`, `INSERT`, or
`DELETE` anywhere in this module, and the connection is always set to
`default_transaction_read_only = on` at session start — so even if a caller
assembled a write query by accident, the session would reject it.

This is the bridge's side of the 'read-only bridge' requirement in packet
UI-002a:

    > expose that schedule context through read-only PM-facing read models
    > preserve the governed seam boundary and keep schedule mutations out of scope

Scope-id joins are intentionally LEFT joins so the bridge still returns P6
planning context for tasks that do not have a matching seam.tasks row. The
seam domain remains canonical owner of execution truth — the bridge never
mutates seam or invents seam rows.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore


def _get_dsn() -> str:
    dsn = os.getenv("SEAM_DATABASE_URL")
    if not dsn:
        raise RuntimeError(
            "SEAM_DATABASE_URL is not set; schedule read bridge cannot connect."
        )
    return dsn


def _open_readonly():
    """Open a new psycopg2 connection forced into read-only mode.

    Any attempt to write via this session will be rejected by Postgres with a
    'cannot execute INSERT/UPDATE/DELETE in a read-only transaction' error —
    a defensive second line under the explicit GET-only router.
    """
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed.")
    conn = psycopg2.connect(_get_dsn())
    conn.autocommit = False
    with conn.cursor() as cur:
        cur.execute("SET default_transaction_read_only = on;")
    conn.commit()
    return conn


def _rows_to_dicts(cur) -> List[Dict[str, Any]]:
    cols = [c.name for c in cur.description]
    out: List[Dict[str, Any]] = []
    for row in cur.fetchall():
        d: Dict[str, Any] = {}
        for c, v in zip(cols, row):
            if hasattr(v, "isoformat"):
                d[c] = v.isoformat()
            else:
                d[c] = v
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def list_projects() -> List[Dict[str, Any]]:
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, p6_project_id, name, scope_project_id,
                       data_date, planned_start, planned_finish,
                       actual_start, actual_finish, must_finish_by,
                       last_imported_at, source_file
                  FROM schedule.projects
                 ORDER BY id
                """
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def get_project(schedule_project_id: str) -> Optional[Dict[str, Any]]:
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, p6_project_id, name, scope_project_id,
                       data_date, planned_start, planned_finish,
                       actual_start, actual_finish, must_finish_by,
                       last_imported_at, source_file
                  FROM schedule.projects
                 WHERE id = %s
                """,
                (schedule_project_id,),
            )
            rows = _rows_to_dicts(cur)
            return rows[0] if rows else None
    finally:
        conn.close()


def list_wbs(schedule_project_id: str) -> List[Dict[str, Any]]:
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, p6_wbs_id, schedule_project_id, parent_wbs_id,
                       name, short_name, seq, level
                  FROM schedule.wbs_nodes
                 WHERE schedule_project_id = %s
                 ORDER BY level NULLS LAST, seq NULLS LAST, id
                """,
                (schedule_project_id,),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def list_tasks(
    *,
    schedule_project_id: Optional[str] = None,
    critical_only: bool = False,
) -> List[Dict[str, Any]]:
    """List schedule tasks, optionally filtered by project and critical flag.

    Does NOT join into seam.* — use `list_tasks_with_scope` for a joined read.
    """
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            # Baseline columns are included as additive, GET-only surface per
            # packet UI-002d. NULLs mean "no baseline captured for this task";
            # consumers MUST render nothing in that case (no fabrication).
            sql = """
                SELECT id, p6_task_id, schedule_project_id, schedule_wbs_id, scope_id,
                       p6_status, apex_status, task_code, task_name, task_type,
                       duration_hours,
                       planned_start, planned_finish, actual_start, actual_finish,
                       total_float_hours, free_float_hours, critical_flag,
                       constraint_type, constraint_date,
                       baseline_start_at, baseline_end_at,
                       baseline_name, baseline_source,
                       baselined_at, baseline_event_id
                  FROM schedule.tasks
                 WHERE (%s::text IS NULL OR schedule_project_id = %s)
                   AND (NOT %s OR critical_flag = TRUE)
                 ORDER BY planned_start NULLS LAST, id
            """
            cur.execute(sql, (schedule_project_id, schedule_project_id, critical_only))
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def list_tasks_with_scope(schedule_project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Joined read: schedule.tasks LEFT JOIN seam.tasks on scope_id.

    The LEFT join ensures schedule tasks missing a seam match are still
    returned with `seam_status = NULL`; callers should NOT treat a NULL
    seam match as 'no operational state' — it simply means the scope link
    has not been resolved yet.

    Purely read-only; no mutation of seam or schedule rows.
    """
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            # Same GET-only baseline surfacing as list_tasks. NULL baseline
            # fields pass through unchanged; the consumer decides to skip the
            # baseline render, not this layer.
            cur.execute(
                """
                SELECT st.id                 AS schedule_task_id,
                       st.p6_task_id,
                       st.task_code,
                       st.task_name,
                       st.schedule_project_id,
                       st.schedule_wbs_id,
                       st.scope_id,
                       st.apex_status        AS schedule_apex_status,
                       st.planned_start,
                       st.planned_finish,
                       st.total_float_hours,
                       st.critical_flag,
                       st.baseline_start_at,
                       st.baseline_end_at,
                       st.baseline_name,
                       st.baseline_source,
                       st.baselined_at,
                       st.baseline_event_id,
                       t.status              AS seam_status,
                       t.workpackage_id      AS seam_workpackage_id
                  FROM schedule.tasks st
                  LEFT JOIN seam.tasks t ON t.id = st.scope_id
                 WHERE (%s::text IS NULL OR st.schedule_project_id = %s)
                 ORDER BY st.planned_start NULLS LAST, st.id
                """,
                (schedule_project_id, schedule_project_id),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def list_relationships(
    *,
    schedule_project_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List P6 relationships, optionally filtered by project or by a task
    (matching either predecessor or successor)."""
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, p6_taskpred_id, schedule_project_id,
                       predecessor_task_id, successor_task_id,
                       rel_type, lag_hours
                  FROM schedule.relationships
                 WHERE (%s::text IS NULL OR schedule_project_id = %s)
                   AND (%s::text IS NULL
                        OR predecessor_task_id = %s
                        OR successor_task_id   = %s)
                 ORDER BY id
                """,
                (schedule_project_id, schedule_project_id,
                 task_id, task_id, task_id),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def list_driver_edges(
    *,
    schedule_project_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List critical-path driving edges — packet UI-002e first slice.

    An edge is "driving" when the PREDECESSOR task sits on the critical path
    (``schedule.tasks.critical_flag = TRUE``). This is the narrow,
    schema-derivable first slice the UI-002e packet scopes; it is intentionally
    NOT a general float-driver analysis and does not fabricate dependency
    semantics the schedule does not already carry.

    Returns one row per driving edge, each carrying enough driver/driven
    context for the PM review surface to render the edge without having to
    join back to ``/tasks`` on the client. Only schema-bearing fields are
    returned — no derived or computed columns beyond what Postgres produces.

    Read-only by construction: routes through :func:`_open_readonly`, which
    sets ``default_transaction_read_only = on`` at session start.
    """
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id                       AS relationship_id,
                       r.p6_taskpred_id,
                       r.schedule_project_id,
                       r.rel_type,
                       r.lag_hours,
                       d.id                       AS driver_task_id,
                       d.p6_task_id               AS driver_p6_task_id,
                       d.task_code                AS driver_task_code,
                       d.task_name                AS driver_task_name,
                       d.planned_start            AS driver_planned_start,
                       d.planned_finish           AS driver_planned_finish,
                       d.total_float_hours        AS driver_total_float_hours,
                       d.critical_flag            AS driver_critical_flag,
                       s.id                       AS driven_task_id,
                       s.p6_task_id               AS driven_p6_task_id,
                       s.task_code                AS driven_task_code,
                       s.task_name                AS driven_task_name,
                       s.planned_start            AS driven_planned_start,
                       s.planned_finish           AS driven_planned_finish,
                       s.total_float_hours        AS driven_total_float_hours,
                       s.critical_flag            AS driven_critical_flag
                  FROM schedule.relationships r
                  JOIN schedule.tasks d ON d.id = r.predecessor_task_id
                  JOIN schedule.tasks s ON s.id = r.successor_task_id
                 WHERE d.critical_flag = TRUE
                   AND (%s::text IS NULL OR r.schedule_project_id = %s)
                 ORDER BY d.planned_finish NULLS LAST,
                          s.planned_start  NULLS LAST,
                          r.id
                """,
                (schedule_project_id, schedule_project_id),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Packet UI-002f — bounded ancestor-chain tracer
#
# First slice: "bounded ancestor chain". Given a selected schedule task, walk
# predecessor edges in ``schedule.relationships`` up to a depth cap, returning
# one joined record per chain edge with both sides' key P6 context so the PM
# review surface can explain the upstream constraint chain without doing a
# client-side join.
#
# Rationale for the shape lock:
#   * The packet JSON calls for "root task, depth, parent-child chain records,
#     and task labels" — i.e., explicit depth and ancestry context, not just
#     immediate predecessors (which the client already has via /relationships).
#   * Traversal MUST terminate. The recursive CTE is bounded by MAX_DEPTH
#     (default 10) AND a cycle-guard via a walked-id array, because
#     `schedule.relationships` does not structurally prohibit cycles and a
#     pathological P6 import could otherwise runaway.
#   * Traversal uses persisted schedule.relationships exclusively — the client
#     must NOT synthesize graph edges it does not actually hold.
# ---------------------------------------------------------------------------

_TRACER_DEFAULT_MAX_DEPTH = 10
_TRACER_HARD_MAX_DEPTH = 25  # absolute safety cap regardless of caller input


def list_tracer_chain(
    *,
    task_id: str,
    max_depth: int = _TRACER_DEFAULT_MAX_DEPTH,
) -> List[Dict[str, Any]]:
    """List the bounded upstream predecessor chain for a selected task.

    Walks ``schedule.relationships`` recursively from the selected task
    backwards through its predecessors, returning one record per edge with
    joined task context on both sides. Depth is bounded by ``max_depth``
    (callers cannot exceed :data:`_TRACER_HARD_MAX_DEPTH`), and a per-row
    cycle guard prevents re-entry into any task already visited on that
    branch.

    Returns an empty list when the selected task has no upstream predecessors
    or when the task id is unknown — callers MUST render that as "no upstream
    chain" rather than fabricating one.

    Read-only by construction: routes through :func:`_open_readonly`, which
    sets ``default_transaction_read_only = on`` at session start.
    """
    if not task_id:
        raise ValueError("task_id is required for tracer traversal")
    # Cap the caller-provided depth. Negative or zero inputs fall back to the
    # default; oversize inputs are silently capped. We never trust raw callers
    # to set unbounded depth on a recursive CTE.
    try:
        effective_depth = int(max_depth)
    except (TypeError, ValueError):
        effective_depth = _TRACER_DEFAULT_MAX_DEPTH
    if effective_depth <= 0:
        effective_depth = _TRACER_DEFAULT_MAX_DEPTH
    if effective_depth > _TRACER_HARD_MAX_DEPTH:
        effective_depth = _TRACER_HARD_MAX_DEPTH

    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH RECURSIVE trace_chain AS (
                    SELECT
                        %s::text                        AS seed_task_id,
                        1                               AS depth,
                        r.predecessor_task_id           AS parent_task_id,
                        r.successor_task_id             AS child_task_id,
                        r.rel_type                      AS rel_type,
                        r.lag_hours                     AS lag_hours,
                        r.id                            AS relationship_id,
                        ARRAY[r.successor_task_id,
                              r.predecessor_task_id]    AS visited_chain
                      FROM schedule.relationships r
                     WHERE r.successor_task_id = %s

                    UNION ALL

                    SELECT
                        t.seed_task_id,
                        t.depth + 1,
                        r.predecessor_task_id,
                        r.successor_task_id,
                        r.rel_type,
                        r.lag_hours,
                        r.id,
                        t.visited_chain || r.predecessor_task_id
                      FROM trace_chain t
                      JOIN schedule.relationships r
                        ON r.successor_task_id = t.parent_task_id
                     WHERE t.depth < %s
                       AND NOT (r.predecessor_task_id = ANY(t.visited_chain))
                )
                SELECT
                    t.seed_task_id,
                    t.depth,
                    t.relationship_id,
                    t.rel_type,
                    t.lag_hours,
                    t.parent_task_id,
                    p.p6_task_id               AS parent_p6_task_id,
                    p.task_code                AS parent_task_code,
                    p.task_name                AS parent_task_name,
                    p.planned_start            AS parent_planned_start,
                    p.planned_finish           AS parent_planned_finish,
                    p.total_float_hours        AS parent_total_float_hours,
                    p.critical_flag            AS parent_critical_flag,
                    t.child_task_id,
                    c.p6_task_id               AS child_p6_task_id,
                    c.task_code                AS child_task_code,
                    c.task_name                AS child_task_name,
                    c.planned_start            AS child_planned_start,
                    c.planned_finish           AS child_planned_finish,
                    c.total_float_hours        AS child_total_float_hours,
                    c.critical_flag            AS child_critical_flag
                  FROM trace_chain t
                  JOIN schedule.tasks p ON p.id = t.parent_task_id
                  JOIN schedule.tasks c ON c.id = t.child_task_id
                 ORDER BY t.depth, t.parent_task_id
                """,
                (task_id, task_id, effective_depth),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Packet UI-002g — comparative schedule analytics (current vs baseline variance)
#
# First slice: per-task current-vs-baseline variance derived from fields
# already persisted on ``schedule.tasks`` (see packet UI-002d baseline-surface
# columns + packet 020c/020g-a baseline ingestion). Three signed-hour
# variances are emitted server-side so the PM review surface does not have
# to reconstruct them from raw timestamps and cannot accidentally fabricate
# variance for a task whose baseline is not actually persisted:
#
#   * ``start_variance_hours``    — planned_start  − baseline_start_at
#   * ``finish_variance_hours``   — planned_finish − baseline_end_at
#   * ``duration_variance_hours`` — planned duration − baseline duration
#
# Guard rails:
#   * Every derived field is NULL-preserving. If either side of the pair is
#     NULL (no baseline captured, or no planned date yet) the variance for
#     that pair is NULL. The UI MUST render nothing in that case.
#   * Nothing is derived from the degraded third-party add/delete delta
#     export. Every variance emitted here is anchored in the persisted
#     ``schedule.tasks`` row and the baseline columns that were landed by
#     the governed loader path (packets 020c, 020d, 020g-a). The delta
#     export is not authoritative; this helper never consults it.
#   * Read-only by construction — routes through :func:`_open_readonly`.
# ---------------------------------------------------------------------------


def list_variance_rows(
    *,
    schedule_project_id: Optional[str] = None,
    with_baseline_only: bool = False,
    only_slipping: bool = False,
) -> List[Dict[str, Any]]:
    """List per-task current-vs-baseline variance rows.

    Returns, per schedule task, a joined dict carrying (a) the current
    planning fields already landed on ``schedule.tasks``, (b) the persisted
    baseline columns (``baseline_start_at``, ``baseline_end_at``,
    ``baseline_name``, ``baseline_source``, ``baselined_at``), and (c) three
    NULL-preserving derived variance fields computed server-side.

    Filters:
      * ``schedule_project_id``  — project filter (NULL passes through).
      * ``with_baseline_only``  — restrict to tasks that actually carry a
        persisted baseline pair. Default False so the surface can surface
        "no baseline" visibly rather than silently hiding tasks.
      * ``only_slipping``       — restrict to tasks whose current planned
        finish is strictly after their persisted baseline end. Requires
        both pair sides present; never synthesizes a slip.

    Read-only by construction; the session is primed with
    ``default_transaction_read_only = on`` before the SELECT fires.
    """
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT st.id                   AS schedule_task_id,
                       st.p6_task_id,
                       st.schedule_project_id,
                       st.task_code,
                       st.task_name,
                       st.p6_status,
                       st.apex_status,
                       st.planned_start,
                       st.planned_finish,
                       st.actual_start,
                       st.actual_finish,
                       st.duration_hours,
                       st.total_float_hours,
                       st.free_float_hours,
                       st.critical_flag,
                       st.baseline_start_at,
                       st.baseline_end_at,
                       st.baseline_name,
                       st.baseline_source,
                       st.baselined_at,
                       CASE
                         WHEN st.planned_start    IS NULL
                           OR st.baseline_start_at IS NULL THEN NULL
                         ELSE EXTRACT(EPOCH FROM
                                (st.planned_start - st.baseline_start_at)
                              ) / 3600.0
                       END                     AS start_variance_hours,
                       CASE
                         WHEN st.planned_finish IS NULL
                           OR st.baseline_end_at IS NULL THEN NULL
                         ELSE EXTRACT(EPOCH FROM
                                (st.planned_finish - st.baseline_end_at)
                              ) / 3600.0
                       END                     AS finish_variance_hours,
                       CASE
                         WHEN st.planned_start    IS NULL
                           OR st.planned_finish   IS NULL
                           OR st.baseline_start_at IS NULL
                           OR st.baseline_end_at   IS NULL THEN NULL
                         ELSE
                            EXTRACT(EPOCH FROM
                              (st.planned_finish   - st.planned_start)
                            ) / 3600.0
                          - EXTRACT(EPOCH FROM
                              (st.baseline_end_at  - st.baseline_start_at)
                            ) / 3600.0
                       END                     AS duration_variance_hours,
                       (st.baseline_start_at IS NOT NULL
                        AND st.baseline_end_at IS NOT NULL)
                                               AS has_baseline
                  FROM schedule.tasks st
                 WHERE (%s::text IS NULL OR st.schedule_project_id = %s)
                   AND (NOT %s
                        OR (st.baseline_start_at IS NOT NULL
                            AND st.baseline_end_at IS NOT NULL))
                   AND (NOT %s
                        OR (st.planned_finish   IS NOT NULL
                            AND st.baseline_end_at IS NOT NULL
                            AND st.planned_finish > st.baseline_end_at))
                 ORDER BY finish_variance_hours DESC NULLS LAST,
                          st.planned_finish     NULLS LAST,
                          st.id
                """,
                (
                    schedule_project_id,
                    schedule_project_id,
                    with_baseline_only,
                    only_slipping,
                ),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()


def list_sync_log(limit: int = 20) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    conn = _open_readonly()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source_type, source_file, data_date,
                       started_at, finished_at, status, stats, error_text
                  FROM schedule.sync_log
                 ORDER BY started_at DESC
                 LIMIT %s
                """,
                (limit,),
            )
            return _rows_to_dicts(cur)
    finally:
        conn.close()
