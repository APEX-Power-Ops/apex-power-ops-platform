from pathlib import Path
import sys

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine
from models import Base


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

    if failures:
        print("RESULT FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())