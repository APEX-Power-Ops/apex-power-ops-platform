from __future__ import annotations

from dataclasses import dataclass

import psycopg

from .model import IntakePayload

_SOURCE = "miner_rev10.xlsm"


@dataclass
class LoadResult:
    projects: int = 0
    scopes: int = 0
    lines: int = 0
    apparatus: int = 0
    standard_hours: int = 0


def load_payload(p: IntakePayload, dsn: str, *, approve: bool = False) -> LoadResult:
    """Idempotent upsert of an IntakePayload into ops.* (keyed on stable provenance). QTY-expands
    each quote line into individual ops.apparatus units. Set approve=True to freeze quoted_revenue."""
    res = LoadResult()
    with psycopg.connect(dsn, autocommit=False) as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ops.projects (project_number, project_name, status, quote_revision,
                contract_value, description, source, legacy_source_id, provenance_status)
            values (%s,%s,%s,%s,%s,%s,%s,'project-miner','draft')
            on conflict (project_number) do update set
                project_name=excluded.project_name, status=excluded.status,
                quote_revision=excluded.quote_revision, contract_value=excluded.contract_value,
                description=excluded.description, updated_at=now()
            returning id
            """,
            (p.project.project_number, p.project.project_name, p.project.status,
             p.project.quote_revision, p.project.contract_value, p.project.description, _SOURCE),
        )
        pid = cur.fetchone()[0]
        res.projects = 1

        for h in p.standard_hours:
            cur.execute(
                """
                insert into ops.standard_hours (apparatus_type, test_standard, default_hours, neta_section)
                values (%s,%s,%s,%s)
                on conflict (apparatus_type, test_standard) do update set
                    default_hours=excluded.default_hours, neta_section=excluded.neta_section, updated_at=now()
                """,
                (h.apparatus_type, h.test_standard, h.default_hours, h.neta_section),
            )
            res.standard_hours += 1

        for s in p.scopes:
            prov = "estimate" if s.quote.is_estimate else "draft"
            cur.execute(
                """
                insert into ops.scopes (project_id, scope_name, scope_type, sort_order,
                    source, legacy_source_id, provenance_status)
                values (%s,%s,%s,%s,%s,%s,%s)
                on conflict (project_id, legacy_source_id) where legacy_source_id is not null
                do update set scope_name=excluded.scope_name, scope_type=excluded.scope_type,
                    sort_order=excluded.sort_order, updated_at=now()
                returning id
                """,
                (pid, s.scope_name, s.scope_type, s.sort_order, _SOURCE, s.scope_name, prov),
            )
            sid = cur.fetchone()[0]
            res.scopes += 1

            cur.execute(
                """
                insert into ops.scope_quote (scope_id, onsite_labor, offsite_labor, travel,
                    outside_services, unit_multiplier, pct_adjust, total_quoted_hours, provenance_status)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (scope_id) do update set
                    onsite_labor=excluded.onsite_labor, offsite_labor=excluded.offsite_labor,
                    travel=excluded.travel, outside_services=excluded.outside_services,
                    unit_multiplier=excluded.unit_multiplier, pct_adjust=excluded.pct_adjust,
                    total_quoted_hours=excluded.total_quoted_hours, updated_at=now()
                """,
                (sid, s.quote.onsite_labor, s.quote.offsite_labor, s.quote.travel,
                 s.quote.outside_services, s.quote.unit_multiplier, s.quote.pct_adjust,
                 s.quote.total_quoted_hours, prov),
            )

            for ln in s.lines:
                cur.execute(
                    """
                    insert into ops.scope_quote_line (scope_id, apparatus_type, test_standard, qty,
                        hrs_per_unit, designation, line_number, source, legacy_source_id, provenance_status)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
                    on conflict (scope_id, line_number) where line_number is not null
                    do update set apparatus_type=excluded.apparatus_type, test_standard=excluded.test_standard,
                        qty=excluded.qty, hrs_per_unit=excluded.hrs_per_unit, updated_at=now()
                    returning id
                    """,
                    (sid, ln.apparatus_type, ln.test_standard, ln.qty, ln.hrs_per_unit,
                     ln.designation, ln.line_number, _SOURCE, f"{s.scope_name}:row{ln.line_number}"),
                )
                lid = cur.fetchone()[0]
                res.lines += 1

                for i in range(1, ln.qty + 1):
                    cur.execute(
                        """
                        insert into ops.apparatus (scope_id, apparatus_designation, apparatus_type, status,
                            drawing_reference, quoted_hours, quote_line_id, source, legacy_source_id,
                            provenance_status)
                        values (%s,%s,%s,'Not Started',%s,%s,%s,%s,%s,'draft')
                        on conflict (legacy_source_id) where legacy_source_id is not null
                        do update set quoted_hours=excluded.quoted_hours, quote_line_id=excluded.quote_line_id,
                            apparatus_type=excluded.apparatus_type, updated_at=now()
                        """,
                        (sid, f"{ln.apparatus_type} {i}", ln.apparatus_type, ln.drawing,
                         ln.hrs_per_unit, lid, _SOURCE, f"{s.scope_name}:row{ln.line_number}:u{i}"),
                    )
                    res.apparatus += 1
        conn.commit()

    if approve:
        _approve(p, dsn)
    return res


def _approve(p: IntakePayload, dsn: str) -> None:
    """Freeze the quote: apparatus.quoted_revenue = quoted_hours x scope blended_rate; mark frozen/approved."""
    with psycopg.connect(dsn, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            """
            update ops.apparatus a set quoted_revenue = round(a.quoted_hours * sq.blended_rate, 2),
                provenance_status='approved', updated_at=now()
            from ops.scope_quote sq
            where sq.scope_id = a.scope_id and a.quoted_hours is not null
            """
        )
        cur.execute("update ops.scope_quote set is_frozen=true, frozen_at=now()")
        cur.execute("update ops.projects set provenance_status='approved', updated_at=now() "
                    "where legacy_source_id='project-miner'")
