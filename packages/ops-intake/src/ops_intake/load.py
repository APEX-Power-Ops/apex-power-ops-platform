from __future__ import annotations

"""Row-builder helpers for the ops.* domain tables.

These are the SOLE insert primitives used by ``approve.py`` / ``materialize`` to
write the operational ``ops.*`` substrate at approve-time. Every helper stamps
``source='ops-intake'`` so the full-replacement delete (which keys on
``source='ops-intake'``) owns exactly the rows it created and never touches
foreign rows.

There is intentionally NO direct-load domain-write path here anymore: the inline
``_approve`` freeze and the ``standard_hours`` catalog write were removed when the
envelope flow (create_run -> review_payload -> approve_run) became the only writer.
"""

_SOURCE = "ops-intake"


def upsert_project(cur, project: dict) -> str:
    """Upsert ops.projects keyed on project_number; stamp source='ops-intake'.

    Writes the minimal source-derived CRM columns (D2: source_client_name /
    source_site_*) from the review payload's project block. Returns project id.
    """
    # NB: cur may be a Connection OR a Cursor. Connection.execute() returns a NEW cursor
    # (Connection has no .fetchone()), so always read from the cursor .execute() returns.
    return cur.execute(
        """
        insert into ops.projects (project_number, project_name, status, quote_revision,
            contract_value, description,
            source_client_name, source_site_name, source_site_address,
            source_site_city, source_site_state, source_site_zip,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'project-intake','draft')
        on conflict (project_number) do update set
            project_name=excluded.project_name, status=excluded.status,
            quote_revision=excluded.quote_revision, contract_value=excluded.contract_value,
            description=excluded.description,
            source_client_name=excluded.source_client_name,
            source_site_name=excluded.source_site_name,
            source_site_address=excluded.source_site_address,
            source_site_city=excluded.source_site_city,
            source_site_state=excluded.source_site_state,
            source_site_zip=excluded.source_site_zip,
            source=excluded.source, updated_at=now()
        returning id
        """,
        (
            project["project_number"],
            project.get("project_name"),
            project.get("status", "Won"),
            project.get("quote_revision"),
            project.get("contract_value"),
            project.get("description"),
            project.get("client_name"),
            project.get("site_name"),
            project.get("site_address"),
            project.get("site_city"),
            project.get("site_state"),
            project.get("site_zip"),
            _SOURCE,
        ),
    ).fetchone()[0]


def insert_scope(cur, project_id, scope: dict) -> str:
    """Insert a fresh ops.scopes row stamped source='ops-intake'. Returns scope id."""
    quote = scope.get("quote", {}) or {}
    prov = "estimate" if quote.get("is_estimate") else "draft"
    return cur.execute(
        """
        insert into ops.scopes (project_id, scope_name, scope_type, sort_order,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s)
        returning id
        """,
        (
            project_id,
            scope["scope_name"],
            scope.get("scope_type", "OTHER"),
            scope.get("sort_order", 0),
            _SOURCE,
            scope.get("legacy_source_id", scope["scope_name"]),
            prov,
        ),
    ).fetchone()[0]


def insert_scope_quote(cur, scope_id, quote: dict) -> None:
    """Insert the 1:1 ops.scope_quote row (J3 total_quoted_hours is then maintained by the
    line-hours trigger as lines are inserted)."""
    prov = "estimate" if quote.get("is_estimate") else "draft"
    cur.execute(
        """
        insert into ops.scope_quote (scope_id, onsite_labor, offsite_labor, travel,
            outside_services, unit_multiplier, pct_adjust, total_quoted_hours, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            scope_id,
            quote.get("onsite_labor", 0),
            quote.get("offsite_labor", 0),
            quote.get("travel", 0),
            quote.get("outside_services", 0),
            quote.get("unit_multiplier", 1),
            quote.get("pct_adjust", 1),
            quote.get("total_quoted_hours", 0),
            prov,
        ),
    )


def insert_task(cur, scope_id, *, section_key: str, task_name: str, sort_order: int) -> str:
    """Insert (or fetch) the ops.tasks grouping row for a section within a scope.

    legacy_source_id = the deterministic section key (never null — a null-section
    line uses the '__ungrouped__' fallback), so uq_ops_tasks_intake (scope_id,
    legacy_source_id) applies and re-materialize is idempotent. Returns task id.
    """
    return cur.execute(
        """
        insert into ops.tasks (scope_id, task_name, task_type, sort_order,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,'draft')
        on conflict (scope_id, legacy_source_id) where legacy_source_id is not null
        do update set task_name=excluded.task_name, updated_at=now()
        returning id
        """,
        (scope_id, task_name, "intake-section", sort_order, _SOURCE, section_key),
    ).fetchone()[0]


def insert_scope_quote_line(cur, scope_id, line: dict) -> str:
    """Insert a fresh ops.scope_quote_line stamped source='ops-intake';
    legacy_source_id = the stable line_uid. Returns line id."""
    return cur.execute(
        """
        insert into ops.scope_quote_line (scope_id, apparatus_type, test_standard, qty,
            hrs_per_unit, catalog_default_hours, designation, notes, description, line_number,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
        returning id
        """,
        (
            scope_id,
            line["apparatus_type"],
            line.get("test_standard"),
            line.get("qty", 1),
            line["hrs_per_unit"],
            line.get("catalog_default_hours"),
            line.get("designation"),
            line.get("notes"),
            line.get("description"),
            line.get("line_number"),
            _SOURCE,
            line.get("line_uid"),
        ),
    ).fetchone()[0]


def insert_apparatus(cur, scope_id, task_id, quote_line_id, *, legacy_source_id: str,
                     designation: str, apparatus_type: str, drawing, quoted_hours,
                     equipment_model_ref: str) -> None:
    """Insert ONE apparatus unit (QTY-expansion). equipment_model_ref (required) =
    the resolved TERMINAL-ACTIVE core.equipment_models id (4b.1; never null on the
    live path). legacy_source_id is PROJECT-QUALIFIED by the caller."""
    cur.execute(
        """
        insert into ops.apparatus (scope_id, task_id, apparatus_designation, apparatus_type,
            equipment_model_ref, status, drawing_reference, quoted_hours, quote_line_id,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,'Not Started',%s,%s,%s,%s,%s,'draft')
        """,
        (
            scope_id,
            task_id,
            designation,
            apparatus_type,
            equipment_model_ref,
            drawing,
            quoted_hours,
            quote_line_id,
            _SOURCE,
            legacy_source_id,
        ),
    )
