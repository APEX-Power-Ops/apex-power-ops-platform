from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jsonschema

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - exercised only in thin local shells
    psycopg2 = None


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
OUTPUT_DIR = SCRIPT_DIR / "output"

DEFAULT_INTERMEDIATE_JSON_PATH = REPO_ROOT / "apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_intermediate_20260521T103643Z.json"
DEFAULT_RECONCILIATION_REPORT_PATH = REPO_ROOT / "apps/mutation-seam/scripts/lane_501_onboarding_design/sample/miner_temp_power_testing_reconciliation_20260521T103643Z.json"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "apps/mutation-seam/scripts/lane_501_onboarding_design/contract/intermediate_ingest_contract_v1.schema.json"

EXPECTED_PROJECT_ID = "pm-import-project-miner-temp-power"
EXPECTED_REPORT_HASH = "1b87397b17ffecd27679073d9645012d5663533ad344e15110c91258993d6130"
ADMISSION_SENTINEL = "LANE_502_TEMP_POWER_SCOPE_BACKFILL_ADMITTED"
DEFAULT_ADMISSION_ENV = "LANE_502_ADMISSION_PHRASE"

EXPECTED_BASELINE_COUNTS = {
    "projects": 1,
    "tasks": 15,
    "apparatus": 184,
    "scopes": 0,
}

FINANCIAL_TABLES = (
    "seam.project_contract_snapshots",
    "seam.scope_labor_details",
    "seam.apparatus_financials",
    "seam.apparatus_revenue_events",
)

PUBLIC_TABLES = (
    "public.projects",
    "public.scopes",
)

SCOPE_INSERT_SQL = """
INSERT INTO seam.scopes (
    id,
    project_id,
    name,
    scope_type,
    total_hours,
    quoted_amount,
    multiplier
) VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO NOTHING
""".strip()

APPARATUS_UPDATE_SQL = """
UPDATE seam.apparatus
SET scope_id = %s, updated_at = NOW()
WHERE id = %s
  AND (scope_id IS NULL OR scope_id != %s)
""".strip()


class Lane502Failure(RuntimeError):
    pass


class Phase0Abort(Lane502Failure):
    pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the PM Lane 502 Miner Temp Power scope backfill under the Lane 501 admission gate."
        )
    )
    parser.add_argument(
        "--intermediate-json-path",
        default=str(DEFAULT_INTERMEDIATE_JSON_PATH),
        help="Path to the Lane 501 intermediate JSON contract.",
    )
    parser.add_argument(
        "--reconciliation-report-path",
        default=str(DEFAULT_RECONCILIATION_REPORT_PATH),
        help="Path to the Lane 501 reconciliation report JSON.",
    )
    parser.add_argument(
        "--schema-path",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to the Lane 501 intermediate JSON schema.",
    )
    parser.add_argument(
        "--admission-env",
        default=DEFAULT_ADMISSION_ENV,
        help="Environment variable that carries the Lane 502 admission phrase.",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional explicit output artifact path.",
    )
    parser.add_argument(
        "--idempotency-proof",
        action="store_true",
        help="Mark this run as the idempotency-proof rerun artifact.",
    )
    return parser.parse_args()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp_slug(ts: datetime) -> str:
    return ts.strftime("%Y%m%dT%H%M%SZ")


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def compute_report_hash(report_payload: dict[str, Any]) -> str:
    report_body = report_payload.get("report_body")
    if report_body is None:
        raise Phase0Abort("Reconciliation report is missing report_body.")
    return _sha256_bytes(_canonical_json_bytes(report_body))


def _validate_intermediate_json(schema_path: Path, intermediate_payload: dict[str, Any]) -> None:
    schema_payload = _read_json(schema_path)
    jsonschema.validate(intermediate_payload, schema_payload)


def _resolve_dsn() -> str:
    for env_name in (
        "LANE_502_TEMP_POWER_SCOPE_BACKFILL_ADMIN_DSN",
        "SEAM_DATABASE_URL",
        "DATABASE_URL",
    ):
        value = os.environ.get(env_name)
        if value:
            return value
    raise Phase0Abort(
        "No database DSN found. Set LANE_502_TEMP_POWER_SCOPE_BACKFILL_ADMIN_DSN, "
        "SEAM_DATABASE_URL, or DATABASE_URL."
    )


def _resolve_admission_phrase(env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise Phase0Abort(
            f"Admission phrase not found in environment variable {env_name}."
        )
    return value


def _parse_iso8601_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC")
    return parsed.astimezone(timezone.utc)


def parse_admission_phrase(phrase_text: str) -> dict[str, str]:
    lines = [line.strip() for line in phrase_text.splitlines() if line.strip()]
    if not lines or lines[0] != ADMISSION_SENTINEL:
        raise Phase0Abort(
            f"Admission phrase must begin with {ADMISSION_SENTINEL}."
        )

    parsed: dict[str, str] = {}
    for line in lines[1:]:
        if "=" not in line:
            raise Phase0Abort(f"Invalid admission phrase line: {line!r}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise Phase0Abort(f"Invalid admission phrase line: {line!r}")
        if key in parsed:
            raise Phase0Abort(f"Duplicate admission phrase field: {key}")
        parsed[key] = value

    return parsed


def _scan_repo_for_exact_phrase(
    phrase_text: str,
    allowed_env_name: str,
) -> dict[str, Any]:
    disallowed_env_vars = sorted(
        env_name
        for env_name, env_value in os.environ.items()
        if env_name != allowed_env_name and env_value == phrase_text
    )

    excluded_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
    }
    matches: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded_dirs for part in path.parts):
            continue
        if path.is_relative_to(OUTPUT_DIR):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if phrase_text in content:
            matches.append(str(path.relative_to(REPO_ROOT)).replace("\\", "/"))

    return {
        "passed": not disallowed_env_vars and not matches,
        "matching_environment_variables": disallowed_env_vars,
        "matching_repo_files": matches,
    }


def _query_rows(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _query_row(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
    rows = _query_rows(cursor, query, params)
    return rows[0] if rows else {}


def _query_value(cursor: Any, query: str, params: tuple[Any, ...] = ()) -> Any:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return None if row is None else row[0]


def _collect_state(cursor: Any) -> dict[str, Any]:
    state: dict[str, Any] = {
        "seam": _query_row(
            cursor,
            """
            SELECT
                (SELECT count(*) FROM seam.projects) AS projects,
                (SELECT count(*) FROM seam.tasks) AS tasks,
                (SELECT count(*) FROM seam.scopes) AS scopes,
                (SELECT count(*) FROM seam.apparatus) AS apparatus,
                (SELECT count(*) FROM seam.apparatus WHERE scope_id IS NULL) AS apparatus_scope_id_null,
                (SELECT count(*) FROM seam.apparatus WHERE scope_id IS NOT NULL) AS apparatus_scope_id_non_null
            """,
        ),
        "financial": {},
        "public": {},
    }
    for table_name in FINANCIAL_TABLES:
        state["financial"][table_name] = int(
            _query_value(cursor, f"SELECT count(*) FROM {table_name}")
        )
    for table_name in PUBLIC_TABLES:
        state["public"][table_name] = int(
            _query_value(cursor, f"SELECT count(*) FROM {table_name}")
        )
    return state


def _build_scope_rows(scopes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    insert_rows: list[dict[str, Any]] = []
    missing_quoted_amount: list[str] = []
    for scope in scopes:
        quoted_amount = scope.get("quoted_amount")
        if quoted_amount is None:
            missing_quoted_amount.append(scope["id"])
            continue
        insert_rows.append(
            {
                "id": scope["id"],
                "project_id": scope["project_id"],
                "name": scope["name"],
                "scope_type": scope["scope_type"],
                "total_hours": scope["total_hours"],
                "quoted_amount": quoted_amount,
                "multiplier": 1.0 if scope.get("multiplier") is None else scope["multiplier"],
            }
        )
    if missing_quoted_amount:
        raise Phase0Abort(
            "Frozen Lane 501 scope contract is not insertable into seam.scopes: "
            "quoted_amount is null for scope ids "
            + ", ".join(missing_quoted_amount)
        )
    return insert_rows


def _build_apparatus_updates(intermediate_payload: dict[str, Any]) -> list[dict[str, str]]:
    outcome_counts = intermediate_payload["reconciliation"]["outcome_counts"]
    if outcome_counts["conflicting"] > 0:
        raise Phase0Abort("Reconciliation report contains conflicting rows.")
    if outcome_counts["unmatched_extractor"] > 0:
        raise Phase0Abort(
            "Reconciliation report contains unmatched_extractor rows; insert admission is out of scope."
        )

    updates: list[dict[str, str]] = []
    for row in intermediate_payload["apparatus"]:
        if row["match_status"] != "matched":
            continue
        updates.append({"id": row["id"], "scope_id": row["scope_id"]})
    return updates


def _validate_admission_phrase(
    phrase_text: str,
    parsed_phrase: dict[str, str],
    report_hash: str,
    intermediate_payload: dict[str, Any],
    resolved_intermediate_path: Path,
    allowed_env_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    required_fields = {
        "RECONCILIATION_REPORT_HASH",
        "INTERMEDIATE_JSON_PATH",
        "OPERATOR",
        "TIMESTAMP",
    }
    required_fields_present = required_fields.issubset(set(parsed_phrase))

    timestamp_valid = False
    timestamp_error = None
    try:
        _parse_iso8601_utc(parsed_phrase.get("TIMESTAMP", ""))
        timestamp_valid = True
    except ValueError as exc:
        timestamp_error = str(exc)

    linkage_matches = (
        Path(parsed_phrase.get("INTERMEDIATE_JSON_PATH", "")).as_posix().replace(REPO_ROOT.as_posix() + "/", "")
        == str(resolved_intermediate_path.relative_to(REPO_ROOT)).replace("\\", "/")
        and intermediate_payload["reconciliation"]["report_content_sha256"] == report_hash
    )

    operator_present = bool(parsed_phrase.get("OPERATOR", "").strip())

    results = {
        "required_fields_present": {
            "passed": required_fields_present,
            "expected_fields": sorted(required_fields),
            "observed_fields": sorted(parsed_phrase.keys()),
        },
        "reconciliation_report_hash_matches_runtime": {
            "passed": parsed_phrase.get("RECONCILIATION_REPORT_HASH") == report_hash,
            "expected": report_hash,
            "observed": parsed_phrase.get("RECONCILIATION_REPORT_HASH"),
        },
        "intermediate_json_linkage_matches_report_hash": {
            "passed": linkage_matches,
            "expected_path": str(resolved_intermediate_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "observed_path": parsed_phrase.get("INTERMEDIATE_JSON_PATH"),
            "expected_report_hash": report_hash,
            "embedded_report_hash": intermediate_payload["reconciliation"]["report_content_sha256"],
            "note": (
                "Lane 501 froze the report hash inside the intermediate JSON but did not freeze a separate "
                "intermediate-file hash inside the reconciliation report."
            ),
        },
        "operator_present": {
            "passed": operator_present,
            "observed": parsed_phrase.get("OPERATOR", ""),
        },
        "timestamp_is_iso8601_utc": {
            "passed": timestamp_valid,
            "observed": parsed_phrase.get("TIMESTAMP"),
            "error": timestamp_error,
        },
    }

    pre_supplied_scan = _scan_repo_for_exact_phrase(phrase_text, allowed_env_name)
    return results, pre_supplied_scan


def _phase_0_database_findings(cursor: Any) -> dict[str, Any]:
    migration_016 = _query_row(
        cursor,
        """
        SELECT
            EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'seam'
                  AND table_name = 'apparatus'
                  AND column_name = 'scope_id'
                  AND data_type = 'text'
                  AND is_nullable = 'YES'
            ) AS scope_id_text_nullable,
            EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class source_table ON source_table.oid = c.conrelid
                JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
                JOIN pg_class target_table ON target_table.oid = c.confrelid
                JOIN pg_namespace target_ns ON target_ns.oid = target_table.relnamespace
                WHERE c.contype = 'f'
                  AND source_ns.nspname = 'seam'
                  AND source_table.relname = 'apparatus'
                  AND c.conname = 'apparatus_scope_id_fkey'
                  AND target_ns.nspname = 'seam'
                  AND target_table.relname = 'scopes'
            ) AS has_scope_fk,
            EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'seam'
                  AND tablename = 'apparatus'
                  AND indexname = 'apparatus_scope_id_idx'
            ) AS has_scope_idx,
            has_table_privilege('pm', 'seam.projects', 'SELECT,INSERT,UPDATE') AS pm_projects_siu,
            has_table_privilege('pm', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS pm_tasks_siu,
            has_table_privilege('pm', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS pm_apparatus_siu,
            has_table_privilege('operations', 'seam.projects', 'SELECT,INSERT,UPDATE') AS operations_projects_siu,
            has_table_privilege('operations', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS operations_tasks_siu,
            has_table_privilege('operations', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS operations_apparatus_siu,
            has_table_privilege('anon', 'seam.projects', 'SELECT,INSERT,UPDATE') AS anon_projects_siu,
            has_table_privilege('anon', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS anon_tasks_siu,
            has_table_privilege('anon', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS anon_apparatus_siu,
            has_table_privilege('authenticated', 'seam.projects', 'SELECT,INSERT,UPDATE') AS authenticated_projects_siu,
            has_table_privilege('authenticated', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS authenticated_tasks_siu,
            has_table_privilege('authenticated', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS authenticated_apparatus_siu
        """,
    )

    role_identity = _query_row(
        cursor,
        """
        SELECT
            current_user,
            session_user,
            COALESCE((SELECT rolcanlogin FROM pg_roles WHERE rolname = 'pm'), false) AS pm_can_login,
            COALESCE((SELECT rolcanlogin FROM pg_roles WHERE rolname = 'operations'), false) AS operations_can_login
        """,
    )

    row_counts = _query_row(
        cursor,
        """
        SELECT
            (SELECT count(*) FROM seam.projects) AS projects,
            (SELECT count(*) FROM seam.tasks) AS tasks,
            (SELECT count(*) FROM seam.apparatus) AS apparatus,
            (SELECT count(*) FROM seam.scopes) AS scopes,
            (SELECT count(*) FROM seam.apparatus WHERE scope_id IS NOT NULL) AS apparatus_scope_id_non_null
        """,
    )

    return {
        "migration_016": migration_016,
        "role_identity": role_identity,
        "row_counts": row_counts,
    }


def _run_pre_transaction_phase_0(
    dsn: str,
    intermediate_payload: dict[str, Any],
    report_payload: dict[str, Any],
    report_hash: str,
    scope_rows: list[dict[str, Any]] | None,
    schema_path: Path,
    admission_phrase_text: str,
    parsed_phrase: dict[str, str],
    admission_env_name: str,
    intermediate_json_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    phase_0: dict[str, Any] = {}
    pre_write_state: dict[str, Any] = {}
    connection_role: dict[str, Any] = {}

    phase_0["lane_501_artifact_drift_check"] = {
        "passed": report_hash == EXPECTED_REPORT_HASH,
        "expected": EXPECTED_REPORT_HASH,
        "observed": report_hash,
    }

    try:
        _validate_intermediate_json(schema_path, intermediate_payload)
        schema_validation = {"passed": True, "schema_path": str(schema_path)}
    except jsonschema.ValidationError as exc:
        schema_validation = {
            "passed": False,
            "schema_path": str(schema_path),
            "error": exc.message,
        }
    phase_0["intermediate_json_validation"] = schema_validation

    phase_0["reconciliation_report_category_counts"] = {
        "passed": report_payload["report_body"]["outcome_counts"]
        == {
            "matched": 184,
            "unmatched_existing": 0,
            "unmatched_extractor": 0,
            "conflicting": 0,
        },
        "observed": report_payload["report_body"]["outcome_counts"],
    }

    scope_ids = [scope["id"] for scope in intermediate_payload["scopes"]]
    expected_scope_ids = [
        f"{EXPECTED_PROJECT_ID}-scope-{number:03d}" for number in range(1, 8)
    ]
    phase_0["scope_identifier_pattern_check"] = {
        "passed": scope_ids == expected_scope_ids,
        "scope_ids": scope_ids,
        "expected_scope_ids": expected_scope_ids,
    }

    if scope_rows is None:
        phase_0["scope_insertability_check"] = {
            "passed": False,
            "reason": (
                "Frozen Lane 501 contract does not provide non-null quoted_amount values required by "
                "the insert-only seam.scopes table."
            ),
        }
    else:
        phase_0["scope_insertability_check"] = {
            "passed": True,
            "scope_count": len(scope_rows),
        }

    admission_validation, pre_supplied_scan = _validate_admission_phrase(
        phrase_text=admission_phrase_text,
        parsed_phrase=parsed_phrase,
        report_hash=report_hash,
        intermediate_payload=intermediate_payload,
        resolved_intermediate_path=intermediate_json_path,
        allowed_env_name=admission_env_name,
    )
    phase_0["admission_phrase_discovery"] = pre_supplied_scan

    if psycopg2 is None:
        raise Phase0Abort(
            "psycopg2 is not installed in the active Python environment; Lane 502 cannot connect to Postgres."
        )

    conn = psycopg2.connect(dsn)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cursor:
            db_findings = _phase_0_database_findings(cursor)
            connection_role = db_findings["role_identity"]
            pre_write_state = _collect_state(cursor)

            phase_0["migration_016_state"] = {
                "passed": all(
                    [
                        db_findings["migration_016"]["scope_id_text_nullable"],
                        db_findings["migration_016"]["has_scope_fk"],
                        db_findings["migration_016"]["has_scope_idx"],
                        db_findings["migration_016"]["pm_projects_siu"],
                        db_findings["migration_016"]["pm_tasks_siu"],
                        db_findings["migration_016"]["pm_apparatus_siu"],
                        db_findings["migration_016"]["operations_projects_siu"],
                        db_findings["migration_016"]["operations_tasks_siu"],
                        db_findings["migration_016"]["operations_apparatus_siu"],
                        not db_findings["migration_016"]["anon_projects_siu"],
                        not db_findings["migration_016"]["anon_tasks_siu"],
                        not db_findings["migration_016"]["anon_apparatus_siu"],
                        not db_findings["migration_016"]["authenticated_projects_siu"],
                        not db_findings["migration_016"]["authenticated_tasks_siu"],
                        not db_findings["migration_016"]["authenticated_apparatus_siu"],
                    ]
                ),
                "details": db_findings["migration_016"],
            }

            phase_0["production_row_count_drift_check"] = {
                "passed": {
                    "projects": db_findings["row_counts"]["projects"] == EXPECTED_BASELINE_COUNTS["projects"],
                    "tasks": db_findings["row_counts"]["tasks"] == EXPECTED_BASELINE_COUNTS["tasks"],
                    "apparatus": db_findings["row_counts"]["apparatus"] == EXPECTED_BASELINE_COUNTS["apparatus"],
                    "scopes": db_findings["row_counts"]["scopes"] == EXPECTED_BASELINE_COUNTS["scopes"],
                },
                "observed": db_findings["row_counts"],
            }
            phase_0["seam_apparatus_scope_id_baseline"] = {
                "passed": db_findings["row_counts"]["apparatus_scope_id_non_null"] == 0,
                "non_null_count": db_findings["row_counts"]["apparatus_scope_id_non_null"],
            }
            phase_0["connection_role_for_writes"] = {
                "passed": (
                    not db_findings["role_identity"]["pm_can_login"]
                    and not db_findings["role_identity"]["operations_can_login"]
                ),
                "details": db_findings["role_identity"],
            }
    finally:
        conn.close()

    return phase_0, admission_validation, pre_supplied_scan, pre_write_state, connection_role


def _post_write_verification(
    pre_write_state: dict[str, Any],
    post_write_state: dict[str, Any],
    fk_join_count: int,
) -> dict[str, Any]:
    scopes_delta = post_write_state["seam"]["scopes"] - pre_write_state["seam"]["scopes"]
    financial_unchanged = (
        pre_write_state["financial"] == post_write_state["financial"]
    )
    public_unchanged = pre_write_state["public"] == post_write_state["public"]
    return {
        "scopes_count_matches_expected": scopes_delta in {0, 7},
        "apparatus_scope_id_count_matches_expected": (
            post_write_state["seam"]["apparatus_scope_id_non_null"] == 184
        ),
        "apparatus_scope_id_null_count_zero": (
            post_write_state["seam"]["apparatus_scope_id_null"] == 0
        ),
        "fk_integrity": {
            "passed": fk_join_count == post_write_state["seam"]["apparatus_scope_id_non_null"],
            "joined_count": fk_join_count,
            "non_null_scope_id_count": post_write_state["seam"]["apparatus_scope_id_non_null"],
        },
        "financial_tables_unchanged": financial_unchanged,
        "seam_tasks_unchanged": (
            pre_write_state["seam"]["tasks"] == post_write_state["seam"]["tasks"]
        ),
        "public_unchanged": public_unchanged,
        "pre_state_sha256": _sha256_bytes(_canonical_json_bytes(pre_write_state)),
        "post_state_sha256": _sha256_bytes(_canonical_json_bytes(post_write_state)),
    }


def _write_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n", encoding="utf-8")


def _build_output_path(args: argparse.Namespace, started_at: datetime) -> Path:
    if args.output_file:
        return Path(args.output_file)
    suffix = "_idempotency_proof" if args.idempotency_proof else ""
    return OUTPUT_DIR / f"scope_backfill_{_timestamp_slug(started_at)}{suffix}.json"


def _execute_write_transaction(
    dsn: str,
    scope_rows: list[dict[str, Any]],
    apparatus_updates: list[dict[str, str]],
) -> tuple[list[str], list[str], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if psycopg2 is None:
        raise Phase0Abort("psycopg2 is not installed in the active Python environment.")

    inserted_scope_ids: list[str] = []
    updated_apparatus_ids: list[str] = []
    pre_write_state: dict[str, Any] = {}
    post_write_state: dict[str, Any] = {}
    verification: dict[str, Any] = {}

    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cursor:
            pre_write_state = _collect_state(cursor)
            for scope in scope_rows:
                cursor.execute(
                    SCOPE_INSERT_SQL,
                    (
                        scope["id"],
                        scope["project_id"],
                        scope["name"],
                        scope["scope_type"],
                        scope["total_hours"],
                        scope["quoted_amount"],
                        scope["multiplier"],
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_scope_ids.append(scope["id"])

            for row in apparatus_updates:
                cursor.execute(
                    APPARATUS_UPDATE_SQL,
                    (row["scope_id"], row["id"], row["scope_id"]),
                )
                if cursor.rowcount > 0:
                    updated_apparatus_ids.append(row["id"])

        conn.commit()

        conn.autocommit = True
        with conn.cursor() as cursor:
            post_write_state = _collect_state(cursor)
            fk_join_count = int(
                _query_value(
                    cursor,
                    """
                    SELECT count(*)
                    FROM seam.apparatus apparatus
                    JOIN seam.scopes scope
                      ON scope.id = apparatus.scope_id
                    WHERE apparatus.scope_id IS NOT NULL
                    """,
                )
            )
            verification = _post_write_verification(
                pre_write_state=pre_write_state,
                post_write_state=post_write_state,
                fk_join_count=fk_join_count,
            )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return inserted_scope_ids, updated_apparatus_ids, pre_write_state, post_write_state, verification


def main() -> int:
    args = _parse_args()
    started_at = _now_utc()
    output_path = _build_output_path(args, started_at)

    artifact: dict[str, Any] = {
        "timestamp_utc": started_at.isoformat(),
        "operator": None,
        "admission_phrase_validation": {},
        "reconciliation_report_hash": None,
        "intermediate_json_path": None,
        "intermediate_json_hash": None,
        "connection_role": {},
        "pre_write_state": {},
        "inserted_scope_ids": [],
        "updated_apparatus_ids": [],
        "skipped_unmatched_existing": {"count": 0, "sample_ids": []},
        "skipped_unmatched_extractor": {"count": 0, "sample_ids": []},
        "aborted_conflicting": {"count": 0},
        "post_write_state": {},
        "post_write_verification": {},
        "transaction_status": "aborted_pre_transaction",
        "verdict": {"status": "failed", "rationale": "not started"},
        "phase_0_findings": {},
    }

    try:
        dsn = _resolve_dsn()
        intermediate_json_path = Path(args.intermediate_json_path).resolve()
        report_path = Path(args.reconciliation_report_path).resolve()
        schema_path = Path(args.schema_path).resolve()
        admission_phrase_text = _resolve_admission_phrase(args.admission_env)
        parsed_phrase = parse_admission_phrase(admission_phrase_text)

        intermediate_payload = _read_json(intermediate_json_path)
        report_payload = _read_json(report_path)
        report_hash = compute_report_hash(report_payload)
        intermediate_json_hash = _file_sha256(intermediate_json_path)

        artifact["operator"] = parsed_phrase.get("OPERATOR")
        artifact["reconciliation_report_hash"] = report_hash
        artifact["intermediate_json_path"] = str(intermediate_json_path)
        artifact["intermediate_json_hash"] = intermediate_json_hash
        artifact["skipped_unmatched_existing"] = {
            "count": report_payload["report_body"]["outcome_counts"]["unmatched_existing"],
            "sample_ids": [
                row.get("id")
                for row in report_payload["report_body"].get("unmatched_existing", [])[:10]
            ],
        }
        artifact["skipped_unmatched_extractor"] = {
            "count": report_payload["report_body"]["outcome_counts"]["unmatched_extractor"],
            "sample_ids": [
                row.get("extractor_candidate_id")
                for row in report_payload["report_body"].get("unmatched_extractor", [])[:10]
            ],
        }
        artifact["aborted_conflicting"] = {
            "count": report_payload["report_body"]["outcome_counts"]["conflicting"]
        }

        scope_rows: list[dict[str, Any]] | None = None
        scope_insertability_error = None
        try:
            scope_rows = _build_scope_rows(intermediate_payload["scopes"])
        except Phase0Abort as exc:
            scope_insertability_error = str(exc)

        apparatus_updates = _build_apparatus_updates(intermediate_payload)

        phase_0, admission_validation, admission_discovery, pre_write_state, connection_role = _run_pre_transaction_phase_0(
            dsn=dsn,
            intermediate_payload=intermediate_payload,
            report_payload=report_payload,
            report_hash=report_hash,
            scope_rows=scope_rows,
            schema_path=schema_path,
            admission_phrase_text=admission_phrase_text,
            parsed_phrase=parsed_phrase,
            admission_env_name=args.admission_env,
            intermediate_json_path=intermediate_json_path,
        )
        if scope_insertability_error is not None:
            phase_0["scope_insertability_check"]["error"] = scope_insertability_error

        artifact["phase_0_findings"] = phase_0
        artifact["admission_phrase_validation"] = admission_validation
        artifact["pre_write_state"] = pre_write_state
        artifact["post_write_state"] = pre_write_state
        artifact["connection_role"] = connection_role

        phase_0_failures: list[str] = []
        for finding_name, finding in phase_0.items():
            if finding_name == "production_row_count_drift_check":
                if not all(finding["passed"].values()):
                    phase_0_failures.append(finding_name)
                continue
            if not finding.get("passed", False):
                phase_0_failures.append(finding_name)
        for validation_name, validation in admission_validation.items():
            if not validation["passed"]:
                phase_0_failures.append(f"admission:{validation_name}")
        if not admission_discovery["passed"]:
            phase_0_failures.append("admission_phrase_discovery")
        try:
            _validate_intermediate_json(schema_path, intermediate_payload)
        except jsonschema.ValidationError:
            phase_0_failures.append("intermediate_json_validation")
        if report_hash != EXPECTED_REPORT_HASH:
            phase_0_failures.append("lane_501_artifact_drift_check")

        if phase_0_failures:
            raise Phase0Abort(
                "Phase 0 blocked before transaction open: " + ", ".join(phase_0_failures)
            )

        inserted_scope_ids, updated_apparatus_ids, tx_pre_state, post_write_state, verification = _execute_write_transaction(
            dsn=dsn,
            scope_rows=scope_rows or [],
            apparatus_updates=apparatus_updates,
        )
        artifact["transaction_status"] = "committed"
        artifact["inserted_scope_ids"] = inserted_scope_ids
        artifact["updated_apparatus_ids"] = updated_apparatus_ids
        artifact["pre_write_state"] = tx_pre_state
        artifact["post_write_state"] = post_write_state
        artifact["post_write_verification"] = verification

        if not all(
            [
                verification["scopes_count_matches_expected"],
                verification["apparatus_scope_id_count_matches_expected"],
                verification["apparatus_scope_id_null_count_zero"],
                verification["fk_integrity"]["passed"],
                verification["financial_tables_unchanged"],
                verification["seam_tasks_unchanged"],
                verification["public_unchanged"],
            ]
        ):
            artifact["verdict"] = {
                "status": "failed",
                "rationale": "Transaction committed but post-write verification failed.",
            }
            _write_artifact(output_path, artifact)
            return 1

        artifact["verdict"] = {
            "status": "passed",
            "rationale": "Lane 502 scope backfill committed and verified successfully.",
        }
        _write_artifact(output_path, artifact)
        return 0
    except Phase0Abort as exc:
        artifact["verdict"] = {
            "status": "failed",
            "rationale": str(exc),
        }
        artifact["post_write_verification"] = {
            "scopes_count_matches_expected": False,
            "apparatus_scope_id_count_matches_expected": False,
            "apparatus_scope_id_null_count_zero": False,
            "fk_integrity": {"passed": False, "joined_count": 0, "non_null_scope_id_count": 0},
            "financial_tables_unchanged": True,
            "seam_tasks_unchanged": True,
            "public_unchanged": True,
        }
        _write_artifact(output_path, artifact)
        return 1
    except Exception as exc:  # pragma: no cover - exercised by live runtime failures
        artifact["transaction_status"] = "rolled_back_partial_failure"
        artifact["verdict"] = {
            "status": "failed",
            "rationale": f"Unexpected Lane 502 failure: {exc}",
        }
        _write_artifact(output_path, artifact)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())