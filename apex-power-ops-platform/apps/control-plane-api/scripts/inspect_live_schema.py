from pathlib import Path
import sys

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine
from models import Base


def main() -> None:
    inspector = inspect(engine)
    live_tables = sorted(inspector.get_table_names())
    live_views = sorted(inspector.get_view_names())
    model_tables = sorted(Base.metadata.tables.keys())

    missing_in_live = [table for table in model_tables if table not in live_tables]
    extra_tcc_live = [
        table for table in live_tables if table.startswith("tcc_") and table not in model_tables
    ]

    print("LIVE_TABLE_COUNT", len(live_tables))
    print("LIVE_VIEW_COUNT", len(live_views))
    print("MODEL_TABLE_COUNT", len(model_tables))
    print("MISSING_IN_LIVE", missing_in_live)
    print("EXTRA_TCC_LIVE", extra_tcc_live)

    with engine.connect() as conn:
        plans_cols = conn.execute(
            text(
                """
                select column_name, is_nullable, data_type
                from information_schema.columns
                where table_name = 'tcc_test_plans'
                order by ordinal_position
                """
            )
        ).fetchall()
        results_cols = conn.execute(
            text(
                """
                select column_name, is_nullable, data_type
                from information_schema.columns
                where table_name = 'tcc_test_results'
                order by ordinal_position
                """
            )
        ).fetchall()
        rls_rows = conn.execute(
            text(
                """
                select schemaname, tablename, rowsecurity
                from pg_tables
                where tablename in ('tcc_test_plans', 'tcc_test_results')
                order by tablename
                """
            )
        ).fetchall()
        policy_rows = conn.execute(
            text(
                """
                select tablename, policyname, permissive, roles, cmd
                from pg_policies
                where tablename in ('tcc_test_plans', 'tcc_test_results')
                order by tablename, policyname
                """
            )
        ).fetchall()

        extra_table_columns = {}
        for table_name in extra_tcc_live:
            extra_table_columns[table_name] = conn.execute(
                text(
                    """
                    select column_name, data_type, is_nullable
                    from information_schema.columns
                    where table_name = :table_name
                    order by ordinal_position
                    """
                ),
                {"table_name": table_name},
            ).fetchall()

    print("TCC_TEST_PLANS_COLUMNS", plans_cols)
    print("TCC_TEST_RESULTS_COLUMNS", results_cols)
    print("RLS_STATE", rls_rows)
    print("POLICIES", policy_rows)
    print("EXTRA_TCC_LIVE_COLUMNS", extra_table_columns)


if __name__ == "__main__":
    main()