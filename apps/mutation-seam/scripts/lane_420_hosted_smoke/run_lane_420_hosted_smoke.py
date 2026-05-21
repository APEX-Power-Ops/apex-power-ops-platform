from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request

try:
    import psycopg2
except ModuleNotFoundError:  # pragma: no cover - exercised only in thin local shells
    psycopg2 = None


SCRIPT_DIR = Path(__file__).resolve().parent
APP_ROOT = SCRIPT_DIR.parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


FIXTURE_DIR = APP_ROOT / "scripts" / "lane_415_envelope_export"
OUTPUT_DIR = SCRIPT_DIR / "output"

WRITE_ROUTE = "/api/v1/mutations/project-import-contract-support"
READ_ROUTE = "/api/v1/reads/project-import-contract-support-status"
TABLES = [
    "seam.apparatus_financials",
    "seam.project_contract_snapshots",
    "seam.scope_labor_details",
    "seam.apparatus_revenue_events",
]

DEFAULT_BASE_URL = "https://mutation-seam.apexpowerops.com"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_POLL_ATTEMPTS = 6


class SmokeFailure(RuntimeError):
    pass


@dataclass
class ScenarioResult:
    name: str
    expected: str
    actual: str
    passed: bool
    status_code: int | None = None
    response_match: bool | None = None
    blocked: bool = False
    skipped: bool = False
    details: dict[str, Any] | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Lane 420 hosted dual-route smoke against a deployed mutation-seam host "
            "and record redacted structured evidence."
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LANE_420_BASE_URL") or os.getenv("MUTATION_SEAM_BASE_URL") or DEFAULT_BASE_URL,
        help="Hosted mutation-seam base URL.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--poll-attempts",
        type=int,
        default=DEFAULT_POLL_ATTEMPTS,
        help="How many times to poll OpenAPI for route registration before failing reachability.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds to wait between route-registration polls.",
    )
    parser.add_argument(
        "--dry-run-flag-observation",
        default=os.getenv("LANE_420_DRY_RUN_FLAG_OBSERVATION", "unknown"),
        choices=["unset", "set", "unknown"],
        help=(
            "Observed production state for LANE_412_DRY_RUN_ENABLED. Use 'unknown' when the hosted environment "
            "cannot be inspected from the current workspace."
        ),
    )
    parser.add_argument(
        "--db-dsn",
        default=os.getenv("LANE_420_DB_DSN", ""),
        help="Optional production Postgres DSN used only for read-only before/after row counts.",
    )
    return parser


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp_slug(ts: datetime) -> str:
    return ts.strftime("%Y%m%dT%H%M%SZ")


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _fixture_text(name: str) -> str:
    return json.dumps(_fixture(name), separators=(",", ":"), ensure_ascii=False)


def _stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _ordered_scope_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(row) for row in rows), key=lambda row: (str(row.get("scope_id") or ""), str(row.get("scope_name") or "")))


def _ordered_apparatus_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (dict(row) for row in rows),
        key=lambda row: (
            str(row.get("scope_id") or ""),
            str(row.get("apparatus_id") or ""),
            str(row.get("apparatus_name") or ""),
        ),
    )


def compute_project_import_contract_support_digest(payload: dict[str, Any]) -> str:
    canonical_parts = [
        str(payload.get("project_id") or ""),
        str(payload.get("candidate_id") or ""),
        str(payload.get("source_fingerprint") or ""),
        str(payload.get("snapshot_kind") or ""),
        str(payload.get("contract_value") or ""),
        str(payload.get("total_quoted_hours") or ""),
        _stable_json(_ordered_scope_rows(list(payload.get("scope_labor_details") or []))),
        _stable_json(_ordered_apparatus_rows(list(payload.get("apparatus_financials") or []))),
    ]
    return hashlib.sha256("|".join(canonical_parts).encode("utf-8")).hexdigest()


def build_project_import_contract_support_entity_id(payload: dict[str, Any]) -> str:
    identity = {
        "project_id": payload.get("project_id"),
        "candidate_id": payload.get("candidate_id"),
        "source_fingerprint": payload.get("source_fingerprint"),
        "snapshot_kind": payload.get("snapshot_kind"),
        "idempotency_key": payload.get("idempotency_key"),
    }
    digest = hashlib.sha256(_stable_json(identity).encode("utf-8")).hexdigest()[:24]
    return f"project-import-contract-support-{digest}"


def _redacted_header_value(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith("Bearer "):
        return "Bearer <redacted>"
    return "<redacted>"


def _headers_with_auth(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = token
    return headers


def _request_json(
    url: str,
    *,
    method: str = "GET",
    timeout_seconds: int,
    headers: dict[str, str] | None = None,
    body_text: str | None = None,
) -> tuple[int, str, Any]:
    req = request.Request(
        url,
        method=method,
        headers=headers or {"Accept": "application/json"},
        data=body_text.encode("utf-8") if body_text is not None else None,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw.strip() else {}
            return int(response.status), raw, payload
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = json.loads(raw) if raw.strip() else {"detail": exc.reason}
        return int(exc.code), raw, payload


def _load_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SmokeFailure(f"Required environment variable {name} is not set.")
    return value


def _poll_openapi_for_routes(base_url: str, timeout_seconds: int, attempts: int, interval_seconds: int) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    required_paths = {WRITE_ROUTE, READ_ROUTE}
    openapi_url = f"{base_url.rstrip('/')}/openapi.json"
    final_payload: dict[str, Any] | None = None
    final_status: int | None = None
    for attempt in range(1, attempts + 1):
        status, raw_text, payload = _request_json(openapi_url, timeout_seconds=timeout_seconds)
        paths = payload.get("paths") if isinstance(payload, dict) else None
        available_paths = set(paths.keys()) if isinstance(paths, dict) else set()
        missing = sorted(required_paths - available_paths)
        history.append(
            {
                "attempt": attempt,
                "status": status,
                "missing_paths": missing,
            }
        )
        final_payload = {
            "status": status,
            "raw_text": raw_text,
            "payload": payload,
        }
        final_status = status
        if status == 200 and not missing:
            return {
                "ready": True,
                "history": history,
                "openapi": final_payload,
            }
        if attempt < attempts:
            time.sleep(interval_seconds)

    return {
        "ready": False,
        "history": history,
        "openapi": final_payload,
        "final_status": final_status,
    }


def _query_row_counts(dsn: str) -> dict[str, int]:
    if psycopg2 is None:
        raise SmokeFailure(
            "psycopg2 is not installed in the active Python environment; DB row-count verification cannot run."
        )
    counts: dict[str, int] = {}
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on;")
            missing_tables: list[str] = []
            for table in TABLES:
                cur.execute("SELECT to_regclass(%s)", (table,))
                if cur.fetchone()[0] is None:
                    missing_tables.append(table)
            if missing_tables:
                raise SmokeFailure(
                    "Production DB row-count verification is blocked because the required tables are missing: "
                    + ", ".join(missing_tables)
                )
            for table in TABLES:
                cur.execute(f"SELECT count(*) FROM {table}")
                counts[table] = int(cur.fetchone()[0])
        conn.rollback()
    finally:
        conn.close()
    return counts


def _append_result(results: list[ScenarioResult], **kwargs: Any) -> None:
    results.append(ScenarioResult(**kwargs))


def _request_envelope() -> dict[str, Any]:
    return _fixture("request_envelope.json")


def _query_string_from_request(request_envelope: dict[str, Any]) -> str:
    payload = request_envelope["payload"]
    return parse.urlencode(
        {
            "project_id": payload["project_id"],
            "candidate_id": payload["candidate_id"],
            "source_fingerprint": payload["source_fingerprint"],
        }
    )


def _operations_request() -> dict[str, Any]:
    request_envelope = deepcopy(_request_envelope())
    payload = request_envelope["payload"]
    payload["contract_value"] = 10001.0
    payload["mutation_id"] = "mut-operations-420-fresh-001"
    digest = compute_project_import_contract_support_digest(payload)
    payload["idempotency_key"] = digest
    request_envelope["idempotency_key"] = digest
    request_envelope["entity_id"] = build_project_import_contract_support_entity_id(payload)
    return request_envelope


def _run() -> tuple[int, dict[str, Any]]:
    args = build_parser().parse_args()
    started_at = _now_utc()
    base_url = args.base_url.rstrip("/")

    pm_token = _load_required_env("LANE_420_PM_TOKEN")
    operations_token = _load_required_env("LANE_420_OPERATIONS_TOKEN")
    task_lead_token = _load_required_env("LANE_420_TASK_LEAD_TOKEN")
    field_tech_token = os.getenv("LANE_420_FIELD_TECH_TOKEN", "").strip() or None

    scenario_results: list[ScenarioResult] = []
    phase_0: dict[str, Any] = {
        "base_url": base_url,
        "dry_run_flag_observation": args.dry_run_flag_observation,
        "render_env_inspection_available": False,
        "db_row_count_access_available": bool(args.db_dsn),
        "token_sources": {
            "pm": "LANE_420_PM_TOKEN",
            "operations": "LANE_420_OPERATIONS_TOKEN",
            "task_lead": "LANE_420_TASK_LEAD_TOKEN",
            "field_tech": "LANE_420_FIELD_TECH_TOKEN" if field_tech_token else "not supplied",
        },
    }

    if args.dry_run_flag_observation == "unset":
        _append_result(
            scenario_results,
            name="production_env_flag_verification",
            expected="Production LANE_412_DRY_RUN_ENABLED is not set.",
            actual="Observed production dry-run flag state: unset.",
            passed=True,
        )
    elif args.dry_run_flag_observation == "set":
        _append_result(
            scenario_results,
            name="production_env_flag_verification",
            expected="Production LANE_412_DRY_RUN_ENABLED is not set.",
            actual="Observed production dry-run flag state: set.",
            passed=False,
            blocked=True,
        )
    else:
        _append_result(
            scenario_results,
            name="production_env_flag_verification",
            expected="Production LANE_412_DRY_RUN_ENABLED is not set.",
            actual="Hosted environment inspection is unavailable from this workspace; flag state remains unknown.",
            passed=False,
            blocked=True,
        )

    before_counts: dict[str, Any]
    row_count_failure_reason: str | None = None
    if args.db_dsn:
        try:
            before_counts = {
                "available": True,
                "counts": _query_row_counts(args.db_dsn),
                "dsn": "<redacted>",
            }
        except SmokeFailure as exc:
            row_count_failure_reason = str(exc)
            before_counts = {
                "available": False,
                "counts": None,
                "reason": row_count_failure_reason,
            }
    else:
        before_counts = {
            "available": False,
            "counts": None,
            "reason": "LANE_420_DB_DSN not supplied; production financial-table row counts cannot be captured from this workspace.",
        }

    poll_result = _poll_openapi_for_routes(
        base_url=base_url,
        timeout_seconds=args.timeout_seconds,
        attempts=args.poll_attempts,
        interval_seconds=args.poll_interval_seconds,
    )
    phase_0["route_registration_poll"] = poll_result["history"]

    routes_ready = bool(poll_result["ready"])
    if routes_ready:
        _append_result(
            scenario_results,
            name="route_registration_poll",
            expected="OpenAPI advertises both Lane 420 routes before smoke scenarios run.",
            actual="Both hosted routes are present in OpenAPI.",
            passed=True,
        )
    else:
        _append_result(
            scenario_results,
            name="route_registration_poll",
            expected="OpenAPI advertises both Lane 420 routes before smoke scenarios run.",
            actual="Hosted OpenAPI still does not advertise both contract-support routes after polling.",
            passed=False,
            blocked=True,
            details={"poll_history": poll_result["history"]},
        )

    request_envelope = _request_envelope()
    request_text = json.dumps(request_envelope, separators=(",", ":"), ensure_ascii=False)
    request_query = _query_string_from_request(request_envelope)

    write_status, write_text, _ = _request_json(
        f"{base_url}{WRITE_ROUTE}",
        method="POST",
        timeout_seconds=args.timeout_seconds,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        body_text=request_text,
    )
    _append_result(
        scenario_results,
        name="write_route_reachability_no_auth",
        expected="POST without auth returns 401.",
        actual=f"POST without auth returned {write_status}.",
        passed=write_status == 401,
        status_code=write_status,
        details={"response_text": write_text},
        blocked=write_status == 404,
    )

    read_status, read_text, _ = _request_json(
        f"{base_url}{READ_ROUTE}?{request_query}",
        timeout_seconds=args.timeout_seconds,
        headers={"Accept": "application/json"},
    )
    _append_result(
        scenario_results,
        name="readback_route_reachability_no_auth",
        expected="GET without auth returns 401.",
        actual=f"GET without auth returned {read_status}.",
        passed=read_status == 401,
        status_code=read_status,
        details={"response_text": read_text},
        blocked=read_status == 404,
    )

    if routes_ready and write_status != 404 and read_status != 404:
        pm_headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": pm_token}
        operations_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": operations_token,
        }
        task_lead_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": task_lead_token,
        }
        field_tech_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": field_tech_token,
        } if field_tech_token else None

        pm_write_status, pm_write_text, _ = _request_json(
            f"{base_url}{WRITE_ROUTE}",
            method="POST",
            timeout_seconds=args.timeout_seconds,
            headers=pm_headers,
            body_text=request_text,
        )
        pm_write_matches_first = pm_write_text == _fixture_text("response_success_first_write.json")
        pm_write_matches_replay = pm_write_text == _fixture_text("response_success_idempotent_hit.json")
        _append_result(
            scenario_results,
            name="write_route_pm_success",
            expected="POST with PM token returns 201 with response_success_first_write.json, or 200 with response_success_idempotent_hit.json when the fixed smoke envelope was already committed.",
            actual=f"POST with PM token returned {pm_write_status}.",
            passed=(pm_write_status == 201 and pm_write_matches_first)
            or (pm_write_status == 200 and pm_write_matches_replay),
            status_code=pm_write_status,
            response_match=pm_write_matches_first or pm_write_matches_replay,
            details={
                "response_text": pm_write_text,
                "fixture": "response_success_first_write.json" if pm_write_matches_first else "response_success_idempotent_hit.json" if pm_write_matches_replay else None,
            },
        )

        replay_status, replay_text, _ = _request_json(
            f"{base_url}{WRITE_ROUTE}",
            method="POST",
            timeout_seconds=args.timeout_seconds,
            headers=pm_headers,
            body_text=request_text,
        )
        _append_result(
            scenario_results,
            name="write_route_pm_replay",
            expected="Replay POST with PM token returns 200 and matches response_success_idempotent_hit.json byte-identically.",
            actual=f"Replay POST with PM token returned {replay_status}.",
            passed=replay_status == 200 and replay_text == _fixture_text("response_success_idempotent_hit.json"),
            status_code=replay_status,
            response_match=replay_text == _fixture_text("response_success_idempotent_hit.json"),
            details={"response_text": replay_text},
        )

        conflict_request = deepcopy(request_envelope)
        conflict_request["payload"]["mutation_id"] = "mut-1d764f75-87a8-49bc-ac73-cd4dabaf95df"
        conflict_text = json.dumps(conflict_request, separators=(",", ":"), ensure_ascii=False)
        conflict_status, conflict_response_text, _ = _request_json(
            f"{base_url}{WRITE_ROUTE}",
            method="POST",
            timeout_seconds=args.timeout_seconds,
            headers=pm_headers,
            body_text=conflict_text,
        )
        _append_result(
            scenario_results,
            name="write_route_pm_conflict",
            expected="Conflict POST with PM token returns 409 and matches response_conflict_duplicate_business_payload.json byte-identically.",
            actual=f"Conflict POST with PM token returned {conflict_status}.",
            passed=conflict_status == 409 and conflict_response_text == _fixture_text("response_conflict_duplicate_business_payload.json"),
            status_code=conflict_status,
            response_match=conflict_response_text == _fixture_text("response_conflict_duplicate_business_payload.json"),
            details={"response_text": conflict_response_text},
        )

        operations_request = _operations_request()
        operations_text = json.dumps(operations_request, separators=(",", ":"), ensure_ascii=False)
        operations_status, operations_response_text, operations_response_json = _request_json(
            f"{base_url}{WRITE_ROUTE}",
            method="POST",
            timeout_seconds=args.timeout_seconds,
            headers=operations_headers,
            body_text=operations_text,
        )
        operations_is_replay = isinstance(operations_response_json, dict) and (
            operations_response_json.get("classification") == "idempotent_hit"
            and operations_response_json.get("mutation_status") == "previously_committed"
        )
        _append_result(
            scenario_results,
            name="write_route_operations_success",
            expected="Operations POST returns 201 on the first run, or 200 idempotent_hit on reruns of the fixed operations seed envelope.",
            actual=f"Fresh POST with Operations token returned {operations_status}.",
            passed=operations_status == 201 or (operations_status == 200 and operations_is_replay),
            status_code=operations_status,
            details={"response_text": operations_response_text},
        )

        task_lead_status, task_lead_text, _ = _request_json(
            f"{base_url}{WRITE_ROUTE}",
            method="POST",
            timeout_seconds=args.timeout_seconds,
            headers=task_lead_headers,
            body_text=request_text,
        )
        _append_result(
            scenario_results,
            name="write_route_task_lead_rejected",
            expected="POST with task_lead token returns 403.",
            actual=f"POST with task_lead token returned {task_lead_status}.",
            passed=task_lead_status == 403,
            status_code=task_lead_status,
            details={"response_text": task_lead_text},
        )

        if field_tech_headers:
            field_tech_status, field_tech_text, _ = _request_json(
                f"{base_url}{WRITE_ROUTE}",
                method="POST",
                timeout_seconds=args.timeout_seconds,
                headers=field_tech_headers,
                body_text=request_text,
            )
            _append_result(
                scenario_results,
                name="write_route_field_tech_rejected",
                expected="POST with field_tech token returns 403.",
                actual=f"POST with field_tech token returned {field_tech_status}.",
                passed=field_tech_status == 403,
                status_code=field_tech_status,
                details={"response_text": field_tech_text},
            )
        else:
            _append_result(
                scenario_results,
                name="write_route_field_tech_rejected",
                expected="POST with field_tech token returns 403.",
                actual="LANE_420_FIELD_TECH_TOKEN not supplied; field_tech rejection scenario skipped.",
                passed=False,
                skipped=True,
                blocked=True,
            )

        ready_status, ready_text, _ = _request_json(
            f"{base_url}{READ_ROUTE}?{request_query}",
            timeout_seconds=args.timeout_seconds,
            headers={"Accept": "application/json", "Authorization": pm_token},
        )
        _append_result(
            scenario_results,
            name="readback_route_pm",
            expected="GET with PM token returns 200 and matches the appropriate Lane 415 readback fixture byte-identically.",
            actual=f"GET with PM token returned {ready_status}.",
            passed=ready_status == 200 and ready_text == _fixture_text("response_readback_ready.json"),
            status_code=ready_status,
            response_match=ready_text == _fixture_text("response_readback_ready.json"),
            details={"response_text": ready_text, "fixture": "response_readback_ready.json"},
        )

        operations_read_status, operations_read_text, _ = _request_json(
            f"{base_url}{READ_ROUTE}?{request_query}",
            timeout_seconds=args.timeout_seconds,
            headers={"Accept": "application/json", "Authorization": operations_token},
        )
        _append_result(
            scenario_results,
            name="readback_route_operations",
            expected="GET with Operations token returns 200 and matches the appropriate Lane 415 readback fixture byte-identically.",
            actual=f"GET with Operations token returned {operations_read_status}.",
            passed=operations_read_status == 200 and operations_read_text == _fixture_text("response_readback_ready.json"),
            status_code=operations_read_status,
            response_match=operations_read_text == _fixture_text("response_readback_ready.json"),
            details={"response_text": operations_read_text, "fixture": "response_readback_ready.json"},
        )

        task_lead_read_status, task_lead_read_text, _ = _request_json(
            f"{base_url}{READ_ROUTE}?{request_query}",
            timeout_seconds=args.timeout_seconds,
            headers={"Accept": "application/json", "Authorization": task_lead_token},
        )
        _append_result(
            scenario_results,
            name="readback_route_task_lead_rejected",
            expected="GET with task_lead token returns 403.",
            actual=f"GET with task_lead token returned {task_lead_read_status}.",
            passed=task_lead_read_status == 403,
            status_code=task_lead_read_status,
            details={"response_text": task_lead_read_text},
        )

        if field_tech_token:
            field_tech_read_status, field_tech_read_text, _ = _request_json(
                f"{base_url}{READ_ROUTE}?{request_query}",
                timeout_seconds=args.timeout_seconds,
                headers={"Accept": "application/json", "Authorization": field_tech_token},
            )
            _append_result(
                scenario_results,
                name="readback_route_field_tech_rejected",
                expected="GET with field_tech token returns 403.",
                actual=f"GET with field_tech token returned {field_tech_read_status}.",
                passed=field_tech_read_status == 403,
                status_code=field_tech_read_status,
                details={"response_text": field_tech_read_text},
            )
    else:
        for name, expected in [
            ("write_route_pm_success", "POST with PM token returns 201 and matches response_success_first_write.json byte-identically."),
            ("write_route_pm_replay", "Replay POST with PM token returns 200 and matches response_success_idempotent_hit.json byte-identically."),
            ("write_route_pm_conflict", "Conflict POST with PM token returns 409 and matches response_conflict_duplicate_business_payload.json byte-identically."),
            ("write_route_operations_success", "Fresh POST with Operations token returns 201 to prove equal write authority."),
            ("write_route_task_lead_rejected", "POST with task_lead token returns 403."),
            ("write_route_field_tech_rejected", "POST with field_tech token returns 403."),
            ("readback_route_pm", "GET with PM token returns 200 and matches the appropriate Lane 415 readback fixture byte-identically."),
            ("readback_route_operations", "GET with Operations token returns 200 and matches the appropriate Lane 415 readback fixture byte-identically."),
            ("readback_route_task_lead_rejected", "GET with task_lead token returns 403."),
            ("readback_route_field_tech_rejected", "GET with field_tech token returns 403."),
        ]:
            _append_result(
                scenario_results,
                name=name,
                expected=expected,
                actual="Scenario skipped because the hosted route pair is not deployed on the target host.",
                passed=False,
                skipped=True,
                blocked=True,
            )

    if args.db_dsn and row_count_failure_reason is None:
        try:
            after_counts = {
                "available": True,
                "counts": _query_row_counts(args.db_dsn),
                "dsn": "<redacted>",
            }
        except SmokeFailure as exc:
            row_count_failure_reason = str(exc)
            after_counts = {
                "available": False,
                "counts": None,
                "reason": row_count_failure_reason,
            }

        if row_count_failure_reason is None:
            deltas = {
                table: after_counts["counts"][table] - before_counts["counts"][table]
                for table in TABLES
            }
            deltas_zero = all(delta == 0 for delta in deltas.values())
            _append_result(
                scenario_results,
                name="db_row_count_delta_verification",
                expected="All four financial-table row-count deltas remain zero before and after smoke.",
                actual=f"Observed deltas: {deltas}",
                passed=deltas_zero,
                details={"before": before_counts["counts"], "after": after_counts["counts"], "deltas": deltas},
            )
        else:
            _append_result(
                scenario_results,
                name="db_row_count_delta_verification",
                expected="All four financial-table row-count deltas remain zero before and after smoke.",
                actual=row_count_failure_reason,
                passed=False,
                blocked=True,
            )
    elif args.db_dsn and row_count_failure_reason is not None:
        after_counts = {
            "available": False,
            "counts": None,
            "reason": row_count_failure_reason,
        }
        _append_result(
            scenario_results,
            name="db_row_count_delta_verification",
            expected="All four financial-table row-count deltas remain zero before and after smoke.",
            actual=row_count_failure_reason,
            passed=False,
            blocked=True,
        )
    else:
        after_counts = {
            "available": False,
            "counts": None,
            "reason": "LANE_420_DB_DSN not supplied; after-count verification is unavailable.",
        }
        _append_result(
            scenario_results,
            name="db_row_count_delta_verification",
            expected="All four financial-table row-count deltas remain zero before and after smoke.",
            actual="Production DB DSN is unavailable, so before/after row counts could not be verified from this workspace.",
            passed=False,
            blocked=True,
        )

    finished_at = _now_utc()
    overall_passed = all(result.passed for result in scenario_results if not result.skipped)
    overall_blocked = any(result.blocked for result in scenario_results)
    overall_status = "passed" if overall_passed else "blocked" if overall_blocked else "failed"

    output_payload = {
        "lane": "PM Lane 420",
        "smoke_kind": "hosted_dual_route_smoke_readiness_no_live",
        "base_url": base_url,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "overall_status": overall_status,
        "phase_0": phase_0,
        "request_context": {
            "write_route": f"{base_url}{WRITE_ROUTE}",
            "read_route": f"{base_url}{READ_ROUTE}",
            "auth_headers": {
                "pm": _redacted_header_value(pm_token),
                "operations": _redacted_header_value(operations_token),
                "task_lead": _redacted_header_value(task_lead_token),
                "field_tech": _redacted_header_value(field_tech_token),
            },
        },
        "before_row_counts": before_counts,
        "after_row_counts": after_counts,
        "scenario_results": [asdict(result) for result in scenario_results],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"smoke_run_{_timestamp_slug(started_at)}.json"
    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"LANE_420_SMOKE_STATUS {overall_status}")
    print(f"LANE_420_SMOKE_OUTPUT {output_path}")

    return (0 if overall_status == "passed" else 1), output_payload


def main() -> int:
    try:
        exit_code, _ = _run()
        return exit_code
    except SmokeFailure as exc:
        print(f"LANE_420_SMOKE_ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())