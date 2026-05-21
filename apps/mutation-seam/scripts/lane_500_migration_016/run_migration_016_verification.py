from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg2


OUTPUT_DIR = Path("apps/mutation-seam/scripts/lane_500_migration_016/output")
TEMP_POWER_PROJECT_ID = "pm-import-project-miner-temp-power"
EXPECTED_TOTAL_COUNTS = {
    "projects": 1,
    "tasks": 15,
    "apparatus": 184,
    "scopes": 0,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify PM Lane 500 migration 016 structural supplement state."
    )
    parser.add_argument(
        "--output-file",
        help="Optional explicit path for the JSON verification artifact.",
    )
    return parser.parse_args()


def _resolve_dsn() -> str:
    for env_name in (
        "LANE_500_MIGRATION_016_ADMIN_DSN",
        "SEAM_DATABASE_URL",
        "DATABASE_URL",
    ):
        value = os.environ.get(env_name)
        if value:
            return value
    raise RuntimeError(
        "No database DSN found. Set LANE_500_MIGRATION_016_ADMIN_DSN, "
        "SEAM_DATABASE_URL, or DATABASE_URL."
    )


def _query_rows(cursor, query: str, params: tuple = ()) -> list[dict]:
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _query_row(cursor, query: str, params: tuple = ()) -> dict:
    rows = _query_rows(cursor, query, params)
    if not rows:
        return {}
    return rows[0]


def _query_value(cursor, query: str, params: tuple = ()):
    cursor.execute(query, params)
    row = cursor.fetchone()
    return None if row is None else row[0]


def _role_metadata(cursor, role_name: str) -> dict:
    return _query_row(
        cursor,
        """
        SELECT
            EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s) AS role_exists,
            COALESCE((SELECT rolcanlogin FROM pg_roles WHERE rolname = %s), false) AS can_login,
            has_schema_privilege(%s, 'seam', 'USAGE') AS seam_usage,
            has_table_privilege(%s, 'seam.projects', 'SELECT') AS projects_select,
            has_table_privilege(%s, 'seam.projects', 'INSERT') AS projects_insert,
            has_table_privilege(%s, 'seam.projects', 'UPDATE') AS projects_update,
            has_table_privilege(%s, 'seam.tasks', 'SELECT') AS tasks_select,
            has_table_privilege(%s, 'seam.tasks', 'INSERT') AS tasks_insert,
            has_table_privilege(%s, 'seam.tasks', 'UPDATE') AS tasks_update,
            has_table_privilege(%s, 'seam.apparatus', 'SELECT') AS apparatus_select,
            has_table_privilege(%s, 'seam.apparatus', 'INSERT') AS apparatus_insert,
            has_table_privilege(%s, 'seam.apparatus', 'UPDATE') AS apparatus_update
        """,
        (
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
            role_name,
        ),
    )


def _build_output_path(explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"migration_016_verification_{timestamp}.json"


def main() -> int:
    args = _parse_args()
    dsn = _resolve_dsn()
    output_path = _build_output_path(args.output_file)

    conn = psycopg2.connect(dsn)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cursor:
            db_identity = _query_row(
                cursor,
                "SELECT current_user, current_database(), current_schema()",
            )

            apparatus_scope_column = _query_rows(
                cursor,
                """
                SELECT
                    column_name,
                    data_type,
                    udt_name,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'seam'
                  AND table_name = 'apparatus'
                  AND column_name = 'scope_id'
                """,
            )

            apparatus_scope_fk = _query_rows(
                cursor,
                """
                SELECT
                    c.conname,
                    source_ns.nspname AS source_schema,
                    source_table.relname AS source_table,
                    source_attr.attname AS source_column,
                    target_ns.nspname AS target_schema,
                    target_table.relname AS target_table,
                    target_attr.attname AS target_column
                FROM pg_constraint c
                JOIN pg_class source_table ON source_table.oid = c.conrelid
                JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
                JOIN pg_class target_table ON target_table.oid = c.confrelid
                JOIN pg_namespace target_ns ON target_ns.oid = target_table.relnamespace
                JOIN unnest(c.conkey) WITH ORDINALITY AS source_key(attnum, ordinality) ON TRUE
                JOIN unnest(c.confkey) WITH ORDINALITY AS target_key(attnum, ordinality)
                    ON target_key.ordinality = source_key.ordinality
                JOIN pg_attribute source_attr
                    ON source_attr.attrelid = source_table.oid
                   AND source_attr.attnum = source_key.attnum
                JOIN pg_attribute target_attr
                    ON target_attr.attrelid = target_table.oid
                   AND target_attr.attnum = target_key.attnum
                WHERE c.contype = 'f'
                  AND source_ns.nspname = 'seam'
                  AND source_table.relname = 'apparatus'
                  AND source_attr.attname = 'scope_id'
                """,
            )

            apparatus_scope_index = _query_rows(
                cursor,
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'seam'
                  AND tablename = 'apparatus'
                  AND indexname = 'apparatus_scope_id_idx'
                """,
            )

            seam_totals = _query_row(
                cursor,
                """
                SELECT
                    (SELECT count(*) FROM seam.projects) AS projects,
                    (SELECT count(*) FROM seam.tasks) AS tasks,
                    (SELECT count(*) FROM seam.apparatus) AS apparatus,
                    (SELECT count(*) FROM seam.scopes) AS scopes
                """,
            )

            temp_power_counts = _query_row(
                cursor,
                """
                SELECT
                    (SELECT count(*) FROM seam.projects WHERE id = %s) AS projects,
                    (SELECT count(*) FROM seam.tasks WHERE id LIKE %s) AS tasks,
                    (SELECT count(*) FROM seam.apparatus WHERE id LIKE %s) AS apparatus,
                    (SELECT count(*) FROM seam.scopes WHERE project_id = %s) AS scopes
                """,
                (
                    TEMP_POWER_PROJECT_ID,
                    f"{TEMP_POWER_PROJECT_ID}-task-%",
                    f"{TEMP_POWER_PROJECT_ID}-app-%",
                    TEMP_POWER_PROJECT_ID,
                ),
            )

            apparatus_scope_nulls = _query_row(
                cursor,
                """
                SELECT
                    count(*) AS total_rows,
                    count(*) FILTER (WHERE scope_id IS NULL) AS null_scope_id_rows,
                    count(*) FILTER (WHERE scope_id IS NOT NULL) AS non_null_scope_id_rows
                FROM seam.apparatus
                """,
            )

            role_checks = {
                role_name: _role_metadata(cursor, role_name)
                for role_name in ("pm", "operations", "anon", "authenticated")
            }

            expected_counts_match = {
                table_name: seam_totals.get(table_name) == expected_count
                for table_name, expected_count in EXPECTED_TOTAL_COUNTS.items()
            }

            temp_power_counts_match = {
                table_name: temp_power_counts.get(table_name) == expected_count
                for table_name, expected_count in EXPECTED_TOTAL_COUNTS.items()
            }

            apparatus_scope_column_ok = any(
                row["column_name"] == "scope_id"
                and row["data_type"] == "text"
                and row["is_nullable"] == "YES"
                for row in apparatus_scope_column
            )

            apparatus_scope_fk_ok = any(
                row["target_schema"] == "seam"
                and row["target_table"] == "scopes"
                and row["target_column"] == "id"
                for row in apparatus_scope_fk
            )

            apparatus_scope_index_ok = len(apparatus_scope_index) == 1

            pm_operations_ok = all(
                role_checks[role_name].get("role_exists")
                and role_checks[role_name].get("seam_usage")
                and role_checks[role_name].get("projects_select")
                and role_checks[role_name].get("projects_insert")
                and role_checks[role_name].get("projects_update")
                and role_checks[role_name].get("tasks_select")
                and role_checks[role_name].get("tasks_insert")
                and role_checks[role_name].get("tasks_update")
                and role_checks[role_name].get("apparatus_select")
                and role_checks[role_name].get("apparatus_insert")
                and role_checks[role_name].get("apparatus_update")
                for role_name in ("pm", "operations")
            )

            public_revokes_ok = all(
                role_checks[role_name].get("role_exists")
                and not role_checks[role_name].get("projects_select")
                and not role_checks[role_name].get("projects_insert")
                and not role_checks[role_name].get("projects_update")
                and not role_checks[role_name].get("tasks_select")
                and not role_checks[role_name].get("tasks_insert")
                and not role_checks[role_name].get("tasks_update")
                and not role_checks[role_name].get("apparatus_select")
                and not role_checks[role_name].get("apparatus_insert")
                and not role_checks[role_name].get("apparatus_update")
                for role_name in ("anon", "authenticated")
            )

            apparatus_scope_nulls_ok = (
                apparatus_scope_nulls.get("total_rows") == EXPECTED_TOTAL_COUNTS["apparatus"]
                and apparatus_scope_nulls.get("null_scope_id_rows") == EXPECTED_TOTAL_COUNTS["apparatus"]
                and apparatus_scope_nulls.get("non_null_scope_id_rows") == 0
            )

            checks = {
                "apparatus_scope_column_ok": apparatus_scope_column_ok,
                "apparatus_scope_fk_ok": apparatus_scope_fk_ok,
                "apparatus_scope_index_ok": apparatus_scope_index_ok,
                "seam_totals_match_expected": all(expected_counts_match.values()),
                "temp_power_counts_match_expected": all(temp_power_counts_match.values()),
                "apparatus_scope_values_all_null": apparatus_scope_nulls_ok,
                "pm_operations_grants_ok": pm_operations_ok,
                "anon_authenticated_revokes_ok": public_revokes_ok,
            }

            overall_status = "passed" if all(checks.values()) else "failed"

            result = {
                "packet_id": "2026-05-21-pm-lane-500-migration-016-structural-supplement-no-live-packet",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "verification_kind": "pm_lane_500_migration_016_structural_supplement",
                "overall_status": overall_status,
                "db_identity": db_identity,
                "artifacts": {
                    "migration": "apps/mutation-seam/migrations/016_seam_apparatus_scope_id_and_operational_grants.sql",
                    "verification_runner": "apps/mutation-seam/scripts/lane_500_migration_016/run_migration_016_verification.py",
                    "output_file": output_path.as_posix(),
                },
                "checks": checks,
                "apparatus_scope_column": apparatus_scope_column,
                "apparatus_scope_fk": apparatus_scope_fk,
                "apparatus_scope_index": apparatus_scope_index,
                "seam_totals": seam_totals,
                "expected_total_counts": EXPECTED_TOTAL_COUNTS,
                "temp_power_counts": temp_power_counts,
                "apparatus_scope_nulls": apparatus_scope_nulls,
                "role_checks": role_checks,
            }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "overall_status": overall_status,
            "output_file": output_path.as_posix(),
        }))
        return 0 if overall_status == "passed" else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())