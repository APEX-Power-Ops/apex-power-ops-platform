from __future__ import annotations

"""approve_run — the SOLE writer of the operational ops.* domain tables.

Identity-gated. Full-replacement materialization under a precise lock order with an
approve-time conflict re-check (TOCTOU), then the quote freeze. ops.* is written
*only* here; nothing else in the package writes projects/scopes/tasks/apparatus/
scope_quote/scope_quote_line. No ops.standard_hours write (D4 — the catalog is a
seed, never written by intake).

Lock order (must match create_run so the two can never deadlock):
    advisory(project_number) -> intake_run row -> project -> apparatus
"""

import json

import psycopg

from .load import (
    insert_apparatus,
    insert_scope,
    insert_scope_quote,
    insert_scope_quote_line,
    insert_task,
    upsert_project,
)

_SOURCE = "ops-intake"
_UNGROUPED = "__ungrouped__"
_ACTIVE = ("parsed", "reviewing")


def materialize(cur, project_number, review_payload) -> None:
    """Full-replacement materialization of one project's intake-owned domain rows.

    Project upsert (stamp source='ops-intake') + delete this project's
    source='ops-intake' scopes (cascade) + insert fresh from the review payload:
    scopes, scope_quote, tasks (keyed on `section` with a deterministic
    `__ungrouped__` fallback so tasks.legacy_source_id is never null), quote lines
    (legacy_source_id = line_uid), and the QTY-expanded apparatus units
    (legacy_source_id = f"{project_number}:{line_uid}:u{i}" -- PROJECT-QUALIFIED).

    Does NOT commit (the caller owns the transaction).
    """
    project = review_payload.get("project", {}) or {}
    project_id = upsert_project(cur, project)

    # Full replacement: drop ONLY the rows the intake engine owns (cascade removes
    # the scope's quote, lines, tasks, apparatus). Foreign rows (source <> 'ops-intake')
    # are never touched.
    cur.execute(
        "delete from ops.scopes where project_id = %s and source = %s",
        (project_id, _SOURCE),
    )

    for s_ord, scope in enumerate(review_payload.get("scopes", []) or []):
        scope_id = insert_scope(cur, project_id, scope)
        quote = scope.get("quote", {}) or {}
        insert_scope_quote(cur, scope_id, quote)

        # one task per distinct section within this scope ('__ungrouped__' for null section)
        section_tasks: dict[str, str] = {}

        for line in scope.get("lines", []) or []:
            section = line.get("section")
            section_key = section if section else _UNGROUPED
            if section_key not in section_tasks:
                task_name = section if section else "Ungrouped"
                section_tasks[section_key] = insert_task(
                    cur, scope_id,
                    section_key=section_key,
                    task_name=task_name,
                    sort_order=len(section_tasks),
                )
            task_id = section_tasks[section_key]

            line_id = insert_scope_quote_line(cur, scope_id, line)

            line_uid = line.get("line_uid")
            qty = int(line.get("qty", 1) or 1)
            apparatus_type = line["apparatus_type"]
            drawing = line.get("drawing")
            hrs_per_unit = line.get("hrs_per_unit")
            for i in range(qty):
                insert_apparatus(
                    cur, scope_id, task_id, line_id,
                    legacy_source_id=f"{project_number}:{line_uid}:u{i}",
                    designation=f"{apparatus_type} {i + 1}",
                    apparatus_type=apparatus_type,
                    drawing=drawing,
                    quoted_hours=hrs_per_unit,
                )


def _freeze(cur, project_id) -> None:
    """Port of the load.py inline _approve freeze, scoped to ONE project.

    apparatus.quoted_revenue = round(quoted_hours * scope blended_rate, 2);
    scope_quote.is_frozen; provenance_status='approved'. blended_rate is a GENERATED
    column (P4 / J3) -- read it, never write it.
    """
    cur.execute(
        """
        update ops.apparatus a set quoted_revenue = round(a.quoted_hours * sq.blended_rate, 2),
            provenance_status='approved', updated_at=now()
        from ops.scope_quote sq, ops.scopes s
        where sq.scope_id = a.scope_id and s.id = a.scope_id and s.project_id = %s
          and a.quoted_hours is not null
        """,
        (project_id,),
    )
    cur.execute(
        """
        update ops.scope_quote sq set is_frozen=true, frozen_at=now()
        from ops.scopes s where s.id = sq.scope_id and s.project_id = %s
        """,
        (project_id,),
    )
    cur.execute(
        "update ops.projects set provenance_status='approved', updated_at=now() where id=%s",
        (project_id,),
    )


def _conflict_kind(cur, project_id):
    """Approve-time conflict re-check (membership/EXISTS, not balance). Mirrors
    envelope._classify_conflict but on a known project_id under the held locks."""
    cur.execute(
        "select 1 from ops.billing_application where project_id = %s limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return "billed"
    cur.execute(
        "select 1 from ops.revenue_recognition_event where project_id = %s limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return "recognized"
    cur.execute(
        "select 1 from ops.scope_quote sq join ops.scopes s on s.id = sq.scope_id"
        " where s.project_id = %s and sq.is_frozen = true limit 1",
        (project_id,),
    )
    if cur.fetchone() is not None:
        return "frozen"
    return "none"


def _block_to_revision(cur, run_id):
    cur.execute(
        "update ops.intake_runs set status='revision_blocked'::ops.intake_run_status,"
        " updated_at=now() where id=%s",
        (run_id,),
    )


def approve_run(dsn, run_id, *, approved_by) -> dict:
    """Identity-gated sole domain writer. Returns {outcome, run_id, ...}; each
    non-approved outcome COMMITS any status transition it made and returns it
    (the API maps outcome->HTTP). Raises only on genuine errors (unknown run_id,
    DB failure) -- never to signal a business outcome (a raise rolls back the
    committed status write).
    """
    with psycopg.connect(dsn) as conn:  # NOT autocommit: one explicit transaction
        with conn.cursor() as cur:
            # (0) LOCK ORDER. Read the project_number WITHOUT a lock, take the project
            #     advisory lock FIRST (matches create_run -> no deadlock), THEN lock the
            #     run row and re-read status.
            cur.execute(
                "select project_number from ops.intake_runs where id = %s",
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError("run not found: " + repr(run_id))
            project_number = row[0]

            cur.execute(
                "select pg_advisory_xact_lock(hashtext(%s))",
                (project_number,),
            )

            cur.execute(
                "select status, review_payload_json, review_payload_version"
                "  from ops.intake_runs where id = %s for update",
                (run_id,),
            )
            status, review_payload_json, review_version = cur.fetchone()

            # (1) 422 blocked_findings: any open blocking finding at the current version.
            cur.execute(
                "select 1 from ops.intake_validation_findings"
                " where run_id = %s and payload_version = %s"
                "   and severity = 'blocking' and ok = false limit 1",
                (run_id, review_version),
            )
            if cur.fetchone() is not None:
                conn.commit()
                return {"outcome": "blocked_findings", "run_id": run_id}

            # (3) 409 revision_blocked  /  (2) 409 not_active (any non-active status)
            if status == "revision_blocked":
                conn.commit()
                return {"outcome": "revision_blocked", "run_id": run_id}
            if status not in _ACTIVE:
                conn.commit()
                return {"outcome": "not_active", "run_id": run_id, "status": status}

            review_payload = (
                review_payload_json
                if isinstance(review_payload_json, dict)
                else json.loads(review_payload_json)
            )

            # (4) Upsert + FOR UPDATE the project (advisory lock covers the brand-new
            #     project where there is no row to lock yet); THEN lock apparatus so an
            #     in-flight Chip-3 approve_and_recognize serializes and its event is visible.
            cur.execute(
                "select id from ops.projects where project_number = %s",
                (project_number,),
            )
            prow = cur.fetchone()
            if prow is not None:
                project_id = prow[0]
                cur.execute(
                    "select id from ops.projects where id = %s for update", (project_id,)
                )
                cur.execute(
                    "select id from ops.apparatus a join ops.scopes s on s.id = a.scope_id"
                    " where s.project_id = %s for update",
                    (project_id,),
                )
                # (4) approve-time conflict re-check (TOCTOU): commit revision_blocked, don't raise.
                kind = _conflict_kind(cur, project_id)
                if kind != "none":
                    _block_to_revision(cur, run_id)
                    conn.commit()
                    return {"outcome": "revision_blocked", "run_id": run_id,
                            "conflict_kind": kind}
                # (4b) foreign-source guard: refuse a project the intake engine does not own.
                cur.execute(
                    "select 1 from ops.scopes where project_id = %s"
                    "   and source is distinct from %s limit 1",
                    (project_id, _SOURCE),
                )
                if cur.fetchone() is not None:
                    conn.commit()
                    return {"outcome": "foreign_source", "run_id": run_id}

            # (5) full-replacement materialization (project upsert happens inside).
            materialize(cur, project_number, review_payload)

            cur.execute(
                "select id from ops.projects where project_number = %s", (project_number,)
            )
            project_id = cur.fetchone()[0]

            # (6) freeze the quote for THIS project only.
            _freeze(cur, project_id)

            # (7) finalize the run (immutability trigger: approved_by+approved_at together,
            #     status=approved IFF approved_by set).
            cur.execute(
                "update ops.intake_runs set status='approved'::ops.intake_run_status,"
                " approved_by=%s, approved_at=now(), project_id=%s, updated_at=now()"
                " where id=%s",
                (str(approved_by), project_id, run_id),
            )

        conn.commit()

    return {"outcome": "approved", "run_id": run_id, "project_id": str(project_id)}
