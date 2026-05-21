from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import Json
except ModuleNotFoundError:  # pragma: no cover - exercised only in thin local shells
    psycopg2 = None
    Json = None


SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = SCRIPT_DIR.parents[1] / "lane_415_envelope_export"
OUTPUT_DIR = SCRIPT_DIR / "output"

TARGET_TABLES = [
    "seam.project_contract_snapshots",
    "seam.scope_labor_details",
    "seam.apparatus_financials",
    "seam.apparatus_revenue_events",
    "seam.idempotency_keys",
]
DEFAULT_PROJECT_ID = "pm-import-project-miner-temp-power"
DEFAULT_CANDIDATE_ID = "pm-import-candidate-miner-temp-power"
DEFAULT_LANE_415_DIGEST = "1859896bcbac1220d21266b19603a12eae710a6e9fbf553c132b7028e417026d"


class ProbeFailure(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Lane 421 rollback-only five-target transaction probe against production "
            "and emit a structured JSON artifact."
        )
    )
    parser.add_argument("--admin-dsn", default="", help="Administrative Postgres DSN.")
    parser.add_argument(
        "--admin-dsn-env",
        default="LANE_421_ADMIN_DSN",
        help="Environment variable to read when --admin-dsn is omitted.",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help="Existing seam.projects id to use as the probe anchor.",
    )
    parser.add_argument(
        "--scope-id",
        required=True,
        help="Existing seam.scopes id (TEXT) used by the probe.",
    )
    parser.add_argument(
        "--apparatus-id",
        required=True,
        help="Existing seam.apparatus id used by the probe.",
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

    raise ProbeFailure("Administrative DSN not provided. Supply --admin-dsn or set the named env var.")


def _fixture_request_envelope() -> dict[str, Any]:
    path = FIXTURE_DIR / "request_envelope.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _count_tables(cur: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in TARGET_TABLES:
        cur.execute("SELECT to_regclass(%s)", (table_name,))
        if cur.fetchone()[0] is None:
            raise ProbeFailure(f"Required table is missing: {table_name}")
        cur.execute(f"SELECT count(*) FROM {table_name}")
        counts[table_name] = int(cur.fetchone()[0])
    return counts


def _validate_anchor_rows(cur: Any, project_id: str, scope_id: str, apparatus_id: str) -> dict[str, bool]:
    cur.execute("SELECT EXISTS (SELECT 1 FROM seam.projects WHERE id = %s)", (project_id,))
    project_exists = bool(cur.fetchone()[0])
    cur.execute("SELECT EXISTS (SELECT 1 FROM seam.scopes WHERE id = %s)", (scope_id,))
    scope_exists = bool(cur.fetchone()[0])
    cur.execute("SELECT EXISTS (SELECT 1 FROM seam.apparatus WHERE id = %s)", (apparatus_id,))
    apparatus_exists = bool(cur.fetchone()[0])
    return {
        "project_exists": project_exists,
        "scope_exists": scope_exists,
        "apparatus_exists": apparatus_exists,
    }


def _probe_identifiers(started_at: datetime) -> dict[str, str]:
    slug = _timestamp_slug(started_at).lower()
    numeric_suffix = started_at.strftime("%m%d%H%M%S")
    probe_key = f"pm-lane-421-atomic-probe:{slug}"
    return {
        "probe_slug": slug,
        "probe_key": probe_key,
        "snapshot_id": f"pcs-l421-{slug}",
        "scope_labor_detail_id": f"sld-l421-{slug}",
        "apparatus_financial_id": f"af-l421-{slug}",
        "revenue_event_id": f"are-l421-{slug}",
        "snapshot_kind": f"change_order_{numeric_suffix}",
        "mutation_id": f"mut-l421-{slug}",
        "audit_event_id": f"audit-l421-{slug}",
        "created_by": "pm-lane-421-atomic-probe",
    }


def _run_probe(args: argparse.Namespace, started_at: datetime) -> tuple[int, dict[str, Any]]:
    if psycopg2 is None or Json is None:
        raise ProbeFailure(
            "psycopg2 is not installed in the active Python environment; Lane 421 atomic probe cannot run."
        )

    dsn = _load_dsn(args)
    envelope = _fixture_request_envelope()
    ids = _probe_identifiers(started_at)
    today = date.today().isoformat()

    conn = psycopg2.connect(dsn)
    baseline_counts: dict[str, int] = {}
    in_transaction_counts: dict[str, int] = {}
    post_rollback_counts: dict[str, int] = {}
    anchor_validation: dict[str, bool] = {}
    row_visibility_after_rollback: dict[str, bool] = {}

    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            anchor_validation = _validate_anchor_rows(cur, args.project_id, args.scope_id, args.apparatus_id)
            if not all(anchor_validation.values()):
                raise ProbeFailure(f"Anchor validation failed: {anchor_validation}")

            baseline_counts = _count_tables(cur)

            cur.execute(
                """
                INSERT INTO seam.project_contract_snapshots (
                    id,
                    project_id,
                    snapshot_kind,
                    contract_value,
                    total_quoted_hours,
                    recognition_rate_per_hour,
                    effective_date,
                    source_fingerprint,
                    created_by,
                    audit_event_id,
                    mutation_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::date, %s, %s, %s, %s)
                """,
                (
                    ids["snapshot_id"],
                    args.project_id,
                    ids["snapshot_kind"],
                    100.00,
                    1.00,
                    100.00,
                    today,
                    ids["probe_key"],
                    ids["created_by"],
                    ids["audit_event_id"],
                    ids["mutation_id"],
                ),
            )
            cur.execute(
                """
                INSERT INTO seam.scope_labor_details (
                    id,
                    scope_id,
                    contract_snapshot_id,
                    labor_category,
                    quoted_amount,
                    quoted_hours,
                    rate,
                    created_by,
                    audit_event_id,
                    mutation_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ids["scope_labor_detail_id"],
                    args.scope_id,
                    ids["snapshot_id"],
                    "Onsite Labor",
                    100.00,
                    1.00,
                    100.00,
                    ids["created_by"],
                    ids["audit_event_id"],
                    ids["mutation_id"],
                ),
            )
            cur.execute(
                """
                INSERT INTO seam.apparatus_financials (
                    id,
                    apparatus_id,
                    contract_snapshot_id,
                    quoted_hours,
                    quoted_revenue,
                    recognition_rate_per_hour_snapshot,
                    created_by,
                    audit_event_id,
                    mutation_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ids["apparatus_financial_id"],
                    args.apparatus_id,
                    ids["snapshot_id"],
                    1.00,
                    100.00,
                    100.00,
                    ids["created_by"],
                    ids["audit_event_id"],
                    ids["mutation_id"],
                ),
            )
            cur.execute(
                """
                INSERT INTO seam.apparatus_revenue_events (
                    id,
                    record_kind,
                    apparatus_id,
                    scope_id,
                    project_id,
                    contract_snapshot_id,
                    recognized_amount,
                    recognition_percent,
                    recognition_date,
                    idempotency_key,
                    mutation_id,
                    audit_event_id,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::date, %s, %s, %s, %s)
                """,
                (
                    ids["revenue_event_id"],
                    "apparatus_revenue_zero_baseline",
                    args.apparatus_id,
                    args.scope_id,
                    args.project_id,
                    ids["snapshot_id"],
                    0.00,
                    0.00,
                    today,
                    ids["probe_key"],
                    ids["mutation_id"],
                    ids["audit_event_id"],
                    ids["created_by"],
                ),
            )
            cur.execute(
                "INSERT INTO seam.idempotency_keys (key, response) VALUES (%s, %s)",
                (
                    ids["probe_key"],
                    Json(
                        {
                            "artifact_type": "pm_lane_421_atomic_transaction_probe_response",
                            "probe_key": ids["probe_key"],
                            "project_id": args.project_id,
                            "candidate_id": envelope.get("payload", {}).get("candidate_id", DEFAULT_CANDIDATE_ID),
                            "lane_415_digest": envelope.get("idempotency_key", DEFAULT_LANE_415_DIGEST),
                        }
                    ),
                ),
            )

            in_transaction_counts = _count_tables(cur)
            conn.rollback()

        with conn.cursor() as cur:
            post_rollback_counts = _count_tables(cur)
            cur.execute("SELECT EXISTS (SELECT 1 FROM seam.project_contract_snapshots WHERE id = %s)", (ids["snapshot_id"],))
            row_visibility_after_rollback["project_contract_snapshot"] = bool(cur.fetchone()[0])
            cur.execute("SELECT EXISTS (SELECT 1 FROM seam.scope_labor_details WHERE id = %s)", (ids["scope_labor_detail_id"],))
            row_visibility_after_rollback["scope_labor_detail"] = bool(cur.fetchone()[0])
            cur.execute("SELECT EXISTS (SELECT 1 FROM seam.apparatus_financials WHERE id = %s)", (ids["apparatus_financial_id"],))
            row_visibility_after_rollback["apparatus_financial"] = bool(cur.fetchone()[0])
            cur.execute("SELECT EXISTS (SELECT 1 FROM seam.apparatus_revenue_events WHERE id = %s)", (ids["revenue_event_id"],))
            row_visibility_after_rollback["apparatus_revenue_event"] = bool(cur.fetchone()[0])
            cur.execute("SELECT EXISTS (SELECT 1 FROM seam.idempotency_keys WHERE key = %s)", (ids["probe_key"],))
            row_visibility_after_rollback["idempotency_key"] = bool(cur.fetchone()[0])
        conn.rollback()
    finally:
        conn.close()

    in_transaction_deltas = {
        table_name: in_transaction_counts[table_name] - baseline_counts[table_name]
        for table_name in TARGET_TABLES
    }
    post_rollback_deltas = {
        table_name: post_rollback_counts[table_name] - baseline_counts[table_name]
        for table_name in TARGET_TABLES
    }

    failures: list[str] = []
    for table_name, delta in in_transaction_deltas.items():
        if delta != 1:
            failures.append(f"In-transaction delta for {table_name} is {delta}, expected 1")
    for table_name, delta in post_rollback_deltas.items():
        if delta != 0:
            failures.append(f"Post-rollback delta for {table_name} is {delta}, expected 0")
    for label, still_exists in row_visibility_after_rollback.items():
        if still_exists:
            failures.append(f"Rolled-back probe row is still visible for {label}")

    output = {
        "artifact_type": "pm_lane_421_atomic_transaction_probe",
        "lane": 421,
        "checked_at": started_at.isoformat(),
        "probe_mode": "rollback_only_no_commit",
        "dsn_source": args.admin_dsn_env if not args.admin_dsn.strip() else "cli_argument",
        "anchor_inputs": {
            "project_id": args.project_id,
            "scope_id": args.scope_id,
            "apparatus_id": args.apparatus_id,
        },
        "anchor_validation": anchor_validation,
        "lane_415_gate_inputs": {
            "project_id": envelope.get("payload", {}).get("project_id", DEFAULT_PROJECT_ID),
            "candidate_id": envelope.get("payload", {}).get("candidate_id", DEFAULT_CANDIDATE_ID),
            "lane_415_digest": envelope.get("idempotency_key", DEFAULT_LANE_415_DIGEST),
        },
        "probe_identifiers": ids,
        "baseline_counts": baseline_counts,
        "in_transaction_counts": in_transaction_counts,
        "in_transaction_deltas": in_transaction_deltas,
        "post_rollback_counts": post_rollback_counts,
        "post_rollback_deltas": post_rollback_deltas,
        "row_visibility_after_rollback": row_visibility_after_rollback,
        "overall_status": "passed" if not failures else "failed",
        "failures": failures,
    }
    return 0 if not failures else 1, output


def _output_path(args: argparse.Namespace, started_at: datetime) -> Path:
    if args.output_file.strip():
        return Path(args.output_file).resolve()
    return OUTPUT_DIR / f"atomic_transaction_probe_{_timestamp_slug(started_at)}.json"


def main() -> int:
    args = build_parser().parse_args()
    started_at = _now_utc()
    output_path = _output_path(args, started_at)
    try:
        exit_code, output = _run_probe(args, started_at)
    except ProbeFailure as exc:
        output = {
            "artifact_type": "pm_lane_421_atomic_transaction_probe",
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