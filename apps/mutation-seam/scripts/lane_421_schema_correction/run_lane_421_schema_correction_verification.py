from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg2
    from psycopg2 import sql
except ModuleNotFoundError:  # pragma: no cover - exercised only in thin local shells
    psycopg2 = None
    sql = None


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"
ROLE_NAMES = ["pm", "operations"]
EXPECTED_SCOPE_FK_TARGETS = {
    "seam.scope_labor_details": "seam.scopes.id",
    "seam.apparatus_revenue_events": "seam.scopes.id",
}
EXPECTED_SCOPE_TYPES = {
    "seam.scope_labor_details.scope_id": "text",
    "seam.apparatus_revenue_events.scope_id": "text",
}


class VerificationFailure(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the PM Lane 421 schema architecture correction using an administrative "
            "Postgres connection and emit a structured JSON artifact."
        )
    )
    parser.add_argument(
        "--admin-dsn",
        default="",
        help="Administrative Postgres DSN. Prefer env injection over a literal shell argument.",
    )
    parser.add_argument(
        "--admin-dsn-env",
        default="LANE_421_SCHEMA_CORRECTION_ADMIN_DSN",
        help="Environment variable to read when --admin-dsn is omitted.",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional explicit output path. Defaults to scripts/lane_421_schema_correction/output/.",
    )
    return parser


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp_slug(ts: datetime) -> str:
    return ts.strftime("%Y%m%dT%H%M%SZ")


def _load_dsn(args: argparse.Namespace) -> str:
    if args.admin_dsn.strip():
        return args.admin_dsn.strip()

    for env_name in [args.admin_dsn_env, "SEAM_DATABASE_URL", "DATABASE_URL"]:
        value = os.getenv(env_name, "").strip()
        if value:
            return value

    raise VerificationFailure(
        "Administrative DSN not provided. Supply --admin-dsn or set the named env var."
    )


def _output_path(args: argparse.Namespace, started_at: datetime) -> Path:
    if args.output_file.strip():
        return Path(args.output_file).resolve()
    return OUTPUT_DIR / f"schema_correction_verification_{_timestamp_slug(started_at)}.json"


def _table_exists(cur: Any, schema_name: str, table_name: str) -> bool:
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        )
        """,
        (schema_name, table_name),
    )
    return bool(cur.fetchone()[0])


def _admin_scope_table_observation(cur: Any) -> dict[str, Any]:
    exists = _table_exists(cur, "seam", "scopes")
    observation = {"exists": exists, "row_count": None}
    if exists:
        cur.execute("SELECT count(*) FROM seam.scopes")
        observation["row_count"] = int(cur.fetchone()[0])
    return observation


def _role_scope_privilege_metadata(dsn: str, role_name: str) -> dict[str, Any]:
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname = %s", (role_name,))
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                return {
                    "exists": False,
                    "can_login": False,
                    "schema_usage": False,
                    "select_privilege": False,
                    "insert_privilege": False,
                }

            cur.execute("SELECT has_schema_privilege(%s, 'seam', 'USAGE')", (role_name,))
            schema_usage = bool(cur.fetchone()[0])
            cur.execute(
                "SELECT has_table_privilege(%s, 'seam.scopes', 'SELECT'), has_table_privilege(%s, 'seam.scopes', 'INSERT')",
                (role_name, role_name),
            )
            select_privilege, insert_privilege = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()

    return {
        "exists": True,
        "can_login": bool(row[0]),
        "schema_usage": schema_usage,
        "select_privilege": bool(select_privilege),
        "insert_privilege": bool(insert_privilege),
    }


def _role_scope_select_check(dsn: str, role_name: str) -> dict[str, Any]:
    role_metadata = _role_scope_privilege_metadata(dsn, role_name)
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role_name)))
            cur.execute("SELECT count(*) FROM seam.scopes")
            row_count = int(cur.fetchone()[0])
            cur.execute("RESET ROLE")
        conn.rollback()
    except Exception as exc:  # pragma: no cover - exercised via live DB
        conn.rollback()
        return {
            "role_name": role_name,
            "passed": bool(
                role_metadata["exists"]
                and role_metadata["schema_usage"]
                and role_metadata["select_privilege"]
                and role_metadata["insert_privilege"]
            ),
            "row_count": None,
            "error": str(exc),
            "probe_mode": "privilege_metadata_only",
            "role_metadata": role_metadata,
        }
    finally:
        conn.close()

    return {
        "role_name": role_name,
        "passed": True,
        "row_count": row_count,
        "error": None,
        "probe_mode": "session_role_select",
        "role_metadata": role_metadata,
    }


def _fk_observations(cur: Any) -> dict[str, dict[str, Any]]:
    cur.execute(
        """
        SELECT
            tc.table_schema,
            tc.table_name,
            kcu.column_name,
            tc.constraint_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND (
                (tc.table_schema = 'seam' AND tc.table_name = 'scope_labor_details' AND kcu.column_name = 'scope_id')
             OR (tc.table_schema = 'seam' AND tc.table_name = 'apparatus_revenue_events' AND kcu.column_name = 'scope_id')
          )
        ORDER BY tc.table_schema, tc.table_name
        """
    )
    observations: dict[str, dict[str, Any]] = {}
    for row in cur.fetchall():
        key = f"{row[0]}.{row[1]}"
        observations[key] = {
            "column_name": row[2],
            "constraint_name": row[3],
            "target": f"{row[4]}.{row[5]}.{row[6]}",
        }
    return observations


def _column_type_observations(cur: Any) -> dict[str, dict[str, Any]]:
    cur.execute(
        """
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type,
            udt_schema,
            udt_name,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'seam'
          AND column_name = 'scope_id'
          AND table_name IN ('scope_labor_details', 'apparatus_revenue_events')
        ORDER BY table_name
        """
    )
    observations: dict[str, dict[str, Any]] = {}
    for row in cur.fetchall():
        key = f"{row[0]}.{row[1]}.{row[2]}"
        observations[key] = {
            "data_type": row[3],
            "udt_schema": row[4],
            "udt_name": row[5],
            "is_nullable": row[6],
        }
    return observations


def _evaluate(
    scope_table: dict[str, Any],
    role_checks: list[dict[str, Any]],
    fk_observations: dict[str, dict[str, Any]],
    column_types: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures: list[str] = []

    if not scope_table["exists"]:
        failures.append("seam.scopes does not exist")
    elif scope_table["row_count"] != 0:
        failures.append(f"seam.scopes row count is {scope_table['row_count']}, expected 0")

    for role_check in role_checks:
        if not role_check["passed"]:
            failures.append(
                f"{role_check['role_name']} lacks the required seam.scopes access contract: {role_check['error']}"
            )
            continue

        role_metadata = role_check["role_metadata"]
        if not role_metadata["exists"]:
            failures.append(f"{role_check['role_name']} role is missing")
        if not role_metadata["schema_usage"]:
            failures.append(f"{role_check['role_name']} lacks USAGE on schema seam")
        if not role_metadata["select_privilege"]:
            failures.append(f"{role_check['role_name']} lacks SELECT on seam.scopes")
        if not role_metadata["insert_privilege"]:
            failures.append(f"{role_check['role_name']} lacks INSERT on seam.scopes")

        if role_check["probe_mode"] == "session_role_select" and role_check["row_count"] != 0:
            failures.append(
                f"{role_check['role_name']} observed seam.scopes row count {role_check['row_count']}, expected 0"
            )

    for table_name, expected_target in EXPECTED_SCOPE_FK_TARGETS.items():
        observation = fk_observations.get(table_name)
        if observation is None:
            failures.append(f"Missing FK observation for {table_name}.scope_id")
            continue
        if observation["target"] != expected_target:
            failures.append(
                f"{table_name}.scope_id targets {observation['target']}, expected {expected_target}"
            )

    for column_name, expected_type in EXPECTED_SCOPE_TYPES.items():
        observation = column_types.get(column_name)
        if observation is None:
            failures.append(f"Missing column-type observation for {column_name}")
            continue
        if observation["data_type"] != expected_type:
            failures.append(
                f"{column_name} type is {observation['data_type']}, expected {expected_type}"
            )

    return {"passed": not failures, "failures": failures}


def _run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    if psycopg2 is None or sql is None:
        raise VerificationFailure(
            "psycopg2 is not installed in the active Python environment; schema-correction verification cannot run."
        )

    started_at = _now_utc()
    dsn = _load_dsn(args)

    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on;")
            scope_table = _admin_scope_table_observation(cur)
            fk_observations = _fk_observations(cur)
            column_types = _column_type_observations(cur)
        conn.rollback()
    finally:
        conn.close()

    role_checks = [_role_scope_select_check(dsn, role_name) for role_name in ROLE_NAMES]
    evaluation = _evaluate(scope_table, role_checks, fk_observations, column_types)

    output = {
        "artifact_type": "pm_lane_421_schema_correction_verification",
        "lane": 421,
        "checked_at": started_at.isoformat(),
        "verification_mode": "metadata_and_role_access_no_write",
        "dsn_source": args.admin_dsn_env if not args.admin_dsn.strip() else "cli_argument",
        "seam_scopes": scope_table,
        "role_select_checks": role_checks,
        "fk_observations": fk_observations,
        "column_type_observations": column_types,
        "overall_status": "passed" if evaluation["passed"] else "failed",
        "failures": evaluation["failures"],
    }
    return (0 if evaluation["passed"] else 1), output


def main() -> int:
    args = build_parser().parse_args()
    started_at = _now_utc()
    output_path = _output_path(args, started_at)

    try:
        exit_code, output = _run(args)
    except VerificationFailure as exc:
        output = {
            "artifact_type": "pm_lane_421_schema_correction_verification",
            "lane": 421,
            "checked_at": started_at.isoformat(),
            "overall_status": "failed",
            "failures": [str(exc)],
        }
        exit_code = 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": output["overall_status"], "output_file": str(output_path)}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())