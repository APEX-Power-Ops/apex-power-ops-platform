from pathlib import Path
import sys

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine
from models import Base
from schema_drift_acl import (
    MCP_ACL_VERBS,
    MCP_CONDITIONAL_OBJECTS,
    MCP_CORE_OBJECTS,
    MCP_HARDENED_ROLES,
    evaluate_definer_view_allowlist,
    evaluate_mcp_acl_posture,
    gate_acl_failures,
)


ACCEPTED_EXTRA_TCC_TABLES = {
    "tcc_emt",
    "tcc_emt_band_names",
    "tcc_emt_curves",
    "tcc_emt_frame_amps",
    "tcc_emt_frames",
    "tcc_emt_pickups",
    "tcc_emt_sections",
    "tcc_etu_settings",
}

EXPECTED_RLS_TABLES = {
    "tcc_test_plans",
    "tcc_test_results",
    "mcp_task_packets",
    "mcp_review_decisions",
    "mcp_local_action_queue",
    "mcp_job_runs",
    "mcp_validation_artifacts",
    "mcp_lane_priorities",
}

# The 6 core mcp tables carry a "RETIRED ... 01b-auth" comment once A2 has applied; that
# marker is how the drift check knows the 01b boundary is in place (so it enforces the
# anon/authenticated no-privilege assertion only post-apply -- see schema_drift_acl).
MCP_CORE_TABLES = (
    "mcp_job_runs",
    "mcp_lane_priorities",
    "mcp_local_action_queue",
    "mcp_review_decisions",
    "mcp_task_packets",
    "mcp_validation_artifacts",
)


def format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def main() -> int:
    inspector = inspect(engine)
    live_tables = sorted(inspector.get_table_names())
    model_tables = sorted(Base.metadata.tables.keys())

    missing_in_live = sorted(table for table in model_tables if table not in live_tables)
    extra_tcc_live = sorted(
        table for table in live_tables if table.startswith("tcc_") and table not in model_tables
    )
    unexpected_extra_tcc = sorted(
        table for table in extra_tcc_live if table not in ACCEPTED_EXTRA_TCC_TABLES
    )
    accepted_extra_tcc = sorted(
        table for table in extra_tcc_live if table in ACCEPTED_EXTRA_TCC_TABLES
    )

    failures: list[str] = []

    with engine.connect() as conn:
        plans_columns = {
            row[0]: {"is_nullable": row[1], "data_type": row[2]}
            for row in conn.execute(
                text(
                    """
                    select column_name, is_nullable, data_type
                    from information_schema.columns
                    where table_name = 'tcc_test_plans'
                    order by ordinal_position
                    """
                )
            ).fetchall()
        }
        rls_rows = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    """
                    select tablename, rowsecurity
                    from pg_tables
                    where tablename in (
                        'tcc_test_plans',
                        'tcc_test_results',
                        'mcp_task_packets',
                        'mcp_review_decisions',
                        'mcp_local_action_queue',
                        'mcp_job_runs',
                        'mcp_validation_artifacts',
                        'mcp_lane_priorities'
                    )
                    order by tablename
                    """
                )
            ).fetchall()
        }
        # --- schema-placement 01b ACL/view posture (review F1 / DESIGN 1b.4, 1b.5) ---
        # boundary_applied: the 6 core mcp tables carry the RETIRED-01b-auth comment marker.
        boundary_applied = bool(
            conn.execute(
                text(
                    """
                    select count(*) = 6
                    from pg_class c join pg_namespace n on n.oid = c.relnamespace
                    where n.nspname = 'public' and c.relkind = 'r'
                      and c.relname = any(:core)
                      and coalesce(obj_description(c.oid, 'pg_class'), '') like '%RETIRED%'
                      and coalesce(obj_description(c.oid, 'pg_class'), '') like '%01b-auth%'
                    """
                ),
                {"core": list(MCP_CORE_TABLES)},
            ).scalar()
        )
        # effective anon/authenticated privilege matrix over the hardened surface (probes
        # only objects and roles that exist, so it is safe on non-Supabase databases).
        mcp_candidates = list(MCP_CORE_OBJECTS) + list(MCP_CONDITIONAL_OBJECTS)
        mcp_acl_result = conn.execute(
            text(
                """
                select r.role, o.obj, v.verb,
                       has_table_privilege(r.role, format('public.%I', o.obj), v.verb) as has_priv
                from unnest(:roles ::text[]) as r(role)
                cross join unnest(:objs ::text[]) as o(obj)
                cross join unnest(:verbs ::text[]) as v(verb)
                where exists (select 1 from pg_roles pr where pr.rolname = r.role)
                  and to_regclass(format('public.%I', o.obj)) is not null
                """
            ),
            {
                "roles": list(MCP_HARDENED_ROLES),
                "objs": mcp_candidates,
                "verbs": list(MCP_ACL_VERBS),
            },
        ).fetchall()
        # public SECURITY DEFINER mcp views (security_invoker not set to true) -> allowlist.
        mcp_definer_views = {
            row[0]
            for row in conn.execute(
                text(
                    r"""
                    select c.relname
                    from pg_class c join pg_namespace n on n.oid = c.relnamespace
                    where n.nspname = 'public' and c.relkind = 'v' and c.relname like 'mcp\_%'
                      and coalesce((select option_value from pg_options_to_table(c.reloptions)
                                    where option_name = 'security_invoker'), 'false') = 'false'
                    """
                )
            ).fetchall()
        }

    mcp_acl_rows = [(row[0], row[1], row[2], bool(row[3])) for row in mcp_acl_result]
    mcp_probed = sorted({row[1] for row in mcp_acl_rows})
    mcp_acl_leaks = evaluate_mcp_acl_posture(mcp_acl_rows)
    mcp_acl_enforced = gate_acl_failures(mcp_acl_leaks, boundary_applied)
    mcp_definer_failures = evaluate_definer_view_allowlist(mcp_definer_views)

    if missing_in_live:
        failures.append(f"model tables missing in live schema: {format_list(missing_in_live)}")

    if unexpected_extra_tcc:
        failures.append(
            "unexpected extra live tcc tables outside the accepted allowlist: "
            f"{format_list(unexpected_extra_tcc)}"
        )

    user_id = plans_columns.get("user_id")
    if not user_id:
        failures.append("tcc_test_plans.user_id column missing from live schema")
    elif user_id["is_nullable"] != "NO":
        failures.append("tcc_test_plans.user_id is nullable in live schema")

    missing_rls = sorted(
        table_name for table_name in EXPECTED_RLS_TABLES if not rls_rows.get(table_name, False)
    )
    if missing_rls:
        failures.append(f"expected row-level security not enabled on: {format_list(missing_rls)}")

    # 01b definer-view allowlist is a standing invariant (checked pre- and post-apply);
    # the anon/authenticated no-privilege assertion is enforced only once the boundary is applied.
    failures.extend(mcp_definer_failures)
    if mcp_acl_enforced:
        failures.append(
            "01b boundary applied but anon/authenticated retain effective privilege on the mcp "
            f"surface (silent re-grant?): {format_list(mcp_acl_enforced)}"
        )

    print("SCHEMA_DRIFT_CHECK")
    print(f"LIVE_TABLE_COUNT {len(live_tables)}")
    print(f"MODEL_TABLE_COUNT {len(model_tables)}")
    print(f"ACCEPTED_EXTRA_TCC {format_list(accepted_extra_tcc)}")
    print(f"UNEXPECTED_EXTRA_TCC {format_list(unexpected_extra_tcc)}")
    print(f"MISSING_MODEL_TABLES_IN_LIVE {format_list(missing_in_live)}")
    print(
        "TCC_TEST_PLANS_USER_ID "
        f"nullable={user_id['is_nullable'] if user_id else 'MISSING'} "
        f"type={user_id['data_type'] if user_id else 'unknown'}"
    )
    print(
        "RLS_STATE "
        + ", ".join(
            f"{table_name}={rls_rows.get(table_name, False)}"
            for table_name in sorted(EXPECTED_RLS_TABLES)
        )
    )
    print(
        "MCP_01B_POSTURE "
        f"boundary_applied={boundary_applied} "
        f"probed={format_list(mcp_probed)} "
        f"anon_auth_priv_leaks={len(mcp_acl_leaks)} "
        f"definer_views={format_list(sorted(mcp_definer_views))}"
    )

    if failures:
        print("RESULT FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
