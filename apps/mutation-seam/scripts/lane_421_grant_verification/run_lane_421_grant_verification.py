from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - exercised only in thin local shells
    psycopg2 = None


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "output"

FINANCIAL_TABLES = [
    "seam.project_contract_snapshots",
    "seam.scope_labor_details",
    "seam.apparatus_financials",
    "seam.apparatus_revenue_events",
]
GRANTED_ROLES = ["pm", "operations"]
DENIED_ROLES = ["field_tech", "field_lead", "task_lead", "anon", "authenticated"]


class VerificationFailure(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the Lane 421 PM/Operations financial-table grant contract "
            "using an administrative Postgres connection and emit a redacted JSON artifact."
        )
    )
    parser.add_argument(
        "--admin-dsn",
        default="",
        help="Administrative Postgres DSN. Prefer env injection over a literal shell argument.",
    )
    parser.add_argument(
        "--admin-dsn-env",
        default="LANE_421_ADMIN_DSN",
        help="Environment variable to read when --admin-dsn is omitted.",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional explicit output path. Defaults to scripts/lane_421_grant_verification/output/.",
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


def _split_table_name(table_name: str) -> tuple[str, str]:
    schema_name, rel_name = table_name.split(".", 1)
    return schema_name, rel_name


def _query_table_metadata(cur: Any, table_name: str) -> dict[str, Any]:
    schema_name, rel_name = _split_table_name(table_name)
    cur.execute(
        """
        SELECT c.relrowsecurity, c.relforcerowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = %s
        """,
        (schema_name, rel_name),
    )
    row = cur.fetchone()
    if row is None:
        return {
            "exists": False,
            "row_level_security_enabled": False,
            "force_row_level_security": False,
        }
    return {
        "exists": True,
        "row_level_security_enabled": bool(row[0]),
        "force_row_level_security": bool(row[1]),
    }


def _query_role_observation(cur: Any, role_name: str) -> dict[str, Any]:
    cur.execute("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)", (role_name,))
    exists = bool(cur.fetchone()[0])

    observation = {
        "role_name": role_name,
        "exists": exists,
        "schema_usage": False,
        "table_privileges": {},
    }
    if not exists:
        return observation

    cur.execute("SELECT has_schema_privilege(%s, 'seam', 'USAGE')", (role_name,))
    observation["schema_usage"] = bool(cur.fetchone()[0])

    for table_name in FINANCIAL_TABLES:
        cur.execute(
            """
            SELECT
                has_table_privilege(%s, %s, 'SELECT'),
                has_table_privilege(%s, %s, 'INSERT'),
                has_table_privilege(%s, %s, 'UPDATE'),
                has_table_privilege(%s, %s, 'DELETE')
            """,
            (role_name, table_name, role_name, table_name, role_name, table_name, role_name, table_name),
        )
        select_priv, insert_priv, update_priv, delete_priv = cur.fetchone()
        observation["table_privileges"][table_name] = {
            "select": bool(select_priv),
            "insert": bool(insert_priv),
            "update": bool(update_priv),
            "delete": bool(delete_priv),
        }

    return observation


def _evaluate_contract(role_observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_role = {item["role_name"]: item for item in role_observations}
    failures: list[str] = []

    for role_name in GRANTED_ROLES:
        observation = by_role[role_name]
        if not observation["exists"]:
            failures.append(f"{role_name} role is missing")
            continue
        if not observation["schema_usage"]:
            failures.append(f"{role_name} lacks USAGE on schema seam")
        for table_name, privileges in observation["table_privileges"].items():
            if not privileges["select"]:
                failures.append(f"{role_name} lacks SELECT on {table_name}")
            if not privileges["insert"]:
                failures.append(f"{role_name} lacks INSERT on {table_name}")
            if privileges["update"]:
                failures.append(f"{role_name} unexpectedly has UPDATE on {table_name}")
            if privileges["delete"]:
                failures.append(f"{role_name} unexpectedly has DELETE on {table_name}")

    for role_name in DENIED_ROLES:
        observation = by_role[role_name]
        if not observation["exists"]:
            continue
        for table_name, privileges in observation["table_privileges"].items():
            if privileges["select"] or privileges["insert"] or privileges["update"] or privileges["delete"]:
                failures.append(
                    f"{role_name} unexpectedly retains table privileges on {table_name}"
                )

    return {
        "passed": not failures,
        "failures": failures,
    }


def _output_path(args: argparse.Namespace, started_at: datetime) -> Path:
    if args.output_file.strip():
        return Path(args.output_file).resolve()
    return OUTPUT_DIR / f"grant_verification_{_timestamp_slug(started_at)}.json"


def _run() -> tuple[int, dict[str, Any]]:
    if psycopg2 is None:
        raise VerificationFailure(
            "psycopg2 is not installed in the active Python environment; Lane 421 grant verification cannot run."
        )

    args = build_parser().parse_args()
    started_at = _now_utc()
    dsn = _load_dsn(args)

    role_names = GRANTED_ROLES + DENIED_ROLES
    table_metadata: dict[str, Any] = {}
    role_observations: list[dict[str, Any]] = []

    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on;")
            for table_name in FINANCIAL_TABLES:
                table_metadata[table_name] = _query_table_metadata(cur, table_name)
            for role_name in role_names:
                role_observations.append(_query_role_observation(cur, role_name))
        conn.rollback()
    finally:
        conn.close()

    contract = _evaluate_contract(role_observations)
    output = {
        "artifact_type": "pm_lane_421_grant_verification",
        "lane": 421,
        "checked_at": started_at.isoformat(),
        "verification_mode": "metadata_only_no_write",
        "dsn_source": args.admin_dsn_env if not args.admin_dsn.strip() else "cli_argument",
        "financial_tables": table_metadata,
        "role_observations": role_observations,
        "expected_contract": {
            "granted_roles": GRANTED_ROLES,
            "denied_roles": DENIED_ROLES,
            "table_privileges_required": ["SELECT", "INSERT"],
            "table_privileges_forbidden": ["UPDATE", "DELETE"],
        },
        "overall_status": "passed" if contract["passed"] else "failed",
        "failures": contract["failures"],
    }
    return 0 if contract["passed"] else 1, output


def main() -> int:
    started_at = _now_utc()
    args = build_parser().parse_args()
    output_path = _output_path(args, started_at)
    try:
        exit_code, output = _run()
    except VerificationFailure as exc:
        output = {
            "artifact_type": "pm_lane_421_grant_verification",
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