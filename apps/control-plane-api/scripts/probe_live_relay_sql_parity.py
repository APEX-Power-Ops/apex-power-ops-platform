from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any
from urllib import error, request

from sqlalchemy import text


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from config import SessionLocal


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE_URL = "https://control.apexpowerops.com"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "output" / "dev" / "control-plane-live-relay-sql-parity.json"
DEFAULT_MATRIX_PATH = APP_ROOT / "scripts" / "relay_parity_matrix.json"


ANALYTICAL_FAMILIES: dict[str, dict[str, object]] = {
    "iec": {
        "model_code": 2,
        "table_suffix": "iec",
        "parent_pk": "relay_curve_iec_id",
        "coefficients": ("v_k", "v_e", "dt_after", "dt_min_time"),
    },
    "meq": {
        "model_code": 3,
        "table_suffix": "meq",
        "parent_pk": "relay_curve_meq_id",
        "coefficients": ("v_a", "v_b", "v_c", "v_d", "v_e"),
    },
    "bsl": {
        "model_code": 4,
        "table_suffix": "bsl",
        "parent_pk": "relay_curve_bsl_id",
        "coefficients": ("v_a", "v_b", "v_c", "v_d", "v_n", "v_k", "v_r"),
    },
    "swz": {
        "model_code": 5,
        "table_suffix": "swz",
        "parent_pk": "relay_curve_swz_id",
        "coefficients": ("v_a", "v_b", "v_e"),
    },
    "pcd": {
        "model_code": 6,
        "table_suffix": "pcd",
        "parent_pk": "relay_curve_pcd_id",
        "coefficients": ("v_a", "v_b", "v_c"),
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare hosted relay preview route output against independent SQL-derived "
            "references from the governed live relay catalog."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for the control-plane runtime.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout for each request.",
    )
    parser.add_argument(
        "--matrix-path",
        default=str(DEFAULT_MATRIX_PATH),
        help="Scenario matrix describing the relay parity probes to run.",
    )
    parser.add_argument(
        "--artifact-path",
        default=str(DEFAULT_ARTIFACT_PATH),
        help="Optional JSON artifact path. Use an empty string to disable artifact writing.",
    )
    return parser


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout_seconds: int,
) -> tuple[int, Any]:
    body: bytes | None = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw.strip() else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail) if detail.strip() else {"detail": exc.reason}
        except json.JSONDecodeError:
            parsed = {"detail": detail or exc.reason}
        return exc.code, parsed
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc


def _post_json(base_url: str, path: str, payload: dict[str, Any], *, timeout_seconds: int) -> Any:
    status, response_payload = _request_json(
        "POST",
        f"{base_url}{path}",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    if status != 200:
        raise RuntimeError(f"POST {path} returned HTTP {status}: {response_payload}")
    return response_payload


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _resolve_path(path_text: str) -> Path:
    candidate = Path(path_text)
    if candidate.is_absolute():
        return candidate
    return (REPO_ROOT / candidate).resolve()


def _write_artifact(report: dict[str, Any], artifact_path: str | None) -> str | None:
    if not artifact_path:
        return None
    target = _resolve_path(artifact_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(target)


def _load_matrix(matrix_path: str) -> dict[str, Any]:
    target = _resolve_path(matrix_path)
    payload = json.loads(target.read_text(encoding="utf-8"))
    _ensure(isinstance(payload, dict), "Relay parity matrix must be a JSON object")
    scenarios = payload.get("scenarios")
    _ensure(isinstance(scenarios, list) and scenarios, "Relay parity matrix must define scenarios")

    families = {str(scenario.get("family", "")).lower() for scenario in scenarios if isinstance(scenario, dict)}
    _ensure("tcp" in families, "Relay parity matrix must include a TCP scenario")
    _ensure(len(families) >= 2, "Relay parity matrix must span at least two families")

    for scenario in scenarios:
        _ensure(isinstance(scenario, dict), "Each relay parity scenario must be an object")
        family = str(scenario.get("family", "")).lower()
        _ensure(family == "tcp" or family in ANALYTICAL_FAMILIES, f"Unsupported relay family in matrix: {family}")
        _ensure(isinstance(scenario.get("current_multiples"), list), "Each scenario must define current_multiples")
        _ensure(isinstance(scenario.get("expected_seconds"), list), "Each scenario must define expected_seconds")
        _ensure(
            len(scenario["current_multiples"]) == len(scenario["expected_seconds"]),
            "Each scenario current_multiples and expected_seconds length must match",
        )
    return payload


def _as_float(value: Any) -> float:
    if value is None:
        raise RuntimeError("Expected numeric value, got null")
    return float(value)


def _as_optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _almost_equal(actual: float, expected: float, *, abs_tol: float, rel_tol: float) -> bool:
    return math.isclose(float(actual), float(expected), abs_tol=abs_tol, rel_tol=rel_tol)


def _compare_series(
    *,
    actual: list[float],
    expected: list[float],
    label: str,
    abs_tol: float,
    rel_tol: float,
) -> list[str]:
    failures: list[str] = []
    if len(actual) != len(expected):
        return [f"{label} length mismatch: expected {len(expected)}, got {len(actual)}"]
    for index, (actual_value, expected_value) in enumerate(zip(actual, expected)):
        if not _almost_equal(actual_value, expected_value, abs_tol=abs_tol, rel_tol=rel_tol):
            failures.append(
                f"{label}[{index}] mismatch: expected {expected_value:.12g}, got {actual_value:.12g}"
            )
    return failures


def _tolerances(matrix: dict[str, Any], storage_kind: str) -> tuple[float, float]:
    configured = (matrix.get("tolerances") or {}).get(storage_kind) or {}
    return (
        float(configured.get("abs_seconds", 1e-6)),
        float(configured.get("rel_seconds", 1e-6)),
    )


def _fetch_database_identity() -> dict[str, Any]:
    with SessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user,
                    current_schema() AS current_schema
                """
            )
        ).mappings().one()
    return dict(row)


def _fetch_tcp_reference(scenario: dict[str, Any]) -> dict[str, Any]:
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT
                    t.source_row_id AS td_section_source_id,
                    c.source_row_id AS curve_parent_source_id,
                    c.curve_name,
                    p.source_ordinal,
                    p.time_dial,
                    p.td_desc,
                    p.current_value,
                    p.trip_time_seconds
                FROM tcc.relay_td_sections t
                JOIN tcc.relay_curves_tcp c ON c.relay_td_section_id = t.relay_td_section_id
                JOIN tcc.relay_curve_points_tcp p ON p.relay_curve_tcp_id = c.relay_curve_tcp_id
                WHERE t.source_row_id = :td_section_source_id
                  AND c.source_row_id = :curve_parent_source_id
                  AND p.source_ordinal = :source_ordinal
                ORDER BY p.current_index
                """
            ),
            {
                "td_section_source_id": scenario["td_section_source_id"],
                "curve_parent_source_id": scenario["curve_parent_source_id"],
                "source_ordinal": scenario["source_ordinal"],
            },
        ).mappings().all()

    _ensure(rows, f"TCP reference rows not found for {scenario['scenario_id']}")
    by_current = {round(float(row["current_value"]), 6): row for row in rows}
    reference_seconds: list[float] = []
    for current_multiple in scenario["current_multiples"]:
        row = by_current.get(round(float(current_multiple), 6))
        _ensure(
            row is not None,
            (
                f"TCP scenario {scenario['scenario_id']} current multiple {current_multiple} "
                "is not an exact stored point"
            ),
        )
        reference_seconds.append(float(row["trip_time_seconds"]))

    first = rows[0]
    return {
        "method": "stored SQL points from tcc.relay_curve_points_tcp",
        "storage_kind": "points",
        "family": "tcp",
        "curve_name": first["curve_name"],
        "point_count": len(rows),
        "time_dial": float(first["time_dial"]),
        "td_desc": first["td_desc"],
        "seconds": reference_seconds,
    }


def _fetch_analytical_coefficients(scenario: dict[str, Any]) -> dict[str, Any]:
    family = str(scenario["family"]).lower()
    config = ANALYTICAL_FAMILIES[family]
    table_suffix = str(config["table_suffix"])
    parent_pk = str(config["parent_pk"])
    coefficients = tuple(config["coefficients"])  # type: ignore[arg-type]
    coefficient_select = ",\n                    ".join(f"rows.{column}" for column in coefficients)

    with SessionLocal() as session:
        row = session.execute(
            text(
                f"""
                SELECT
                    t.source_row_id AS td_section_source_id,
                    parent.source_row_id AS curve_parent_source_id,
                    rows.curve_name,
                    rows.ordinal AS curve_ordinal,
                    {coefficient_select}
                FROM tcc.relay_td_sections t
                JOIN tcc.relay_curves_{table_suffix} parent
                  ON parent.relay_td_section_id = t.relay_td_section_id
                JOIN tcc.relay_curve_rows_{table_suffix} rows
                  ON rows.{parent_pk} = parent.{parent_pk}
                WHERE t.source_row_id = :td_section_source_id
                  AND parent.source_row_id = :curve_parent_source_id
                  AND rows.ordinal = :curve_ordinal
                """
            ),
            {
                "td_section_source_id": scenario["td_section_source_id"],
                "curve_parent_source_id": scenario["curve_parent_source_id"],
                "curve_ordinal": scenario["curve_ordinal"],
            },
        ).mappings().one_or_none()

    _ensure(row is not None, f"Analytical reference row not found for {scenario['scenario_id']}")
    return {
        "curve_name": row["curve_name"],
        "coefficients": {column: _as_optional_float(row[column]) for column in coefficients},
    }


def _evaluate_iec(coefficients: dict[str, float | None], current_multiples: list[float], time_dial: float) -> list[float]:
    v_k = _as_float(coefficients.get("v_k"))
    v_e = _as_float(coefficients.get("v_e"))
    dt_after = coefficients.get("dt_after")
    dt_min_time = coefficients.get("dt_min_time")
    points: list[float] = []
    for current_multiple in current_multiples:
        denominator = math.pow(float(current_multiple), v_e) - 1.0
        _ensure(denominator > 0, f"IEC current multiple must be greater than 1.0: {current_multiple}")
        trip_time = time_dial * v_k / denominator
        if dt_after is not None and dt_min_time is not None and current_multiple >= float(dt_after):
            trip_time = max(trip_time, float(dt_min_time))
        points.append(trip_time)
    return points


def _evaluate_meq(coefficients: dict[str, float | None], current_multiples: list[float], time_dial: float) -> list[float]:
    v_a = _as_float(coefficients.get("v_a"))
    v_b = _as_float(coefficients.get("v_b"))
    v_c = _as_float(coefficients.get("v_c"))
    v_d = _as_float(coefficients.get("v_d"))
    v_e = _as_float(coefficients.get("v_e"))
    points: list[float] = []
    for current_multiple in current_multiples:
        delta = float(current_multiple) - v_c
        _ensure(delta > 0, f"MEQ current multiple must exceed v_c: {current_multiple}")
        delta_sq = delta * delta
        points.append((v_a + (v_b / delta) + (v_d / delta_sq) + (v_e / (delta_sq * delta))) * time_dial)
    return points


def _evaluate_bsl(coefficients: dict[str, float | None], current_multiples: list[float], time_dial: float) -> list[float]:
    v_a = _as_float(coefficients.get("v_a"))
    v_b = _as_float(coefficients.get("v_b"))
    v_c = _as_float(coefficients.get("v_c"))
    v_n = _as_float(coefficients.get("v_n"))
    v_k = _as_float(coefficients.get("v_k"))
    points: list[float] = []
    for current_multiple in current_multiples:
        denominator = math.pow(float(current_multiple), v_n) - v_c
        _ensure(denominator > 0, f"BSL current multiple must exceed denominator floor: {current_multiple}")
        points.append(time_dial * ((v_a / denominator) + v_b) + v_k)
    return points


def _evaluate_swz(coefficients: dict[str, float | None], current_multiples: list[float], time_dial: float) -> list[float]:
    v_a = _as_float(coefficients.get("v_a"))
    v_b = _as_float(coefficients.get("v_b"))
    v_e = _as_float(coefficients.get("v_e"))
    points: list[float] = []
    for current_multiple in current_multiples:
        denominator = math.pow(float(current_multiple), v_e) - 1.0
        _ensure(denominator > 0, f"SWZ current multiple must be greater than 1.0: {current_multiple}")
        points.append(time_dial * ((v_b / denominator) + v_a))
    return points


def _evaluate_pcd(coefficients: dict[str, float | None], current_multiples: list[float], time_dial: float) -> list[float]:
    v_a = _as_float(coefficients.get("v_a"))
    v_b = _as_float(coefficients.get("v_b"))
    v_c = _as_float(coefficients.get("v_c"))
    points: list[float] = []
    for current_multiple in current_multiples:
        denominator = math.pow(float(current_multiple), v_c) - 1.0
        _ensure(denominator > 0, f"PCD current multiple must be greater than 1.0: {current_multiple}")
        points.append(time_dial * ((v_a / denominator) + v_b))
    return points


INDEPENDENT_EVALUATORS = {
    "iec": _evaluate_iec,
    "meq": _evaluate_meq,
    "bsl": _evaluate_bsl,
    "swz": _evaluate_swz,
    "pcd": _evaluate_pcd,
}


def _fetch_analytical_reference(scenario: dict[str, Any]) -> dict[str, Any]:
    family = str(scenario["family"]).lower()
    row = _fetch_analytical_coefficients(scenario)
    current_multiples = [float(value) for value in scenario["current_multiples"]]
    time_dial = float(scenario.get("time_dial", 1.0))
    seconds = INDEPENDENT_EVALUATORS[family](row["coefficients"], current_multiples, time_dial)
    return {
        "method": f"independent {family.upper()} inverse-time equation evaluated from SQL coefficients",
        "storage_kind": "constants",
        "family": family,
        "curve_name": row["curve_name"],
        "coefficients": row["coefficients"],
        "seconds": seconds,
    }


def _fetch_sql_reference(scenario: dict[str, Any]) -> dict[str, Any]:
    family = str(scenario["family"]).lower()
    if family == "tcp":
        return _fetch_tcp_reference(scenario)
    return _fetch_analytical_reference(scenario)


def _route_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "td_section_source_id": scenario["td_section_source_id"],
        "current_multiples": scenario["current_multiples"],
    }
    if scenario.get("curve_parent_source_id") is not None:
        payload["curve_parent_source_id"] = scenario["curve_parent_source_id"]
    if scenario.get("curve_ordinal") is not None:
        payload["curve_ordinal"] = scenario["curve_ordinal"]
    if scenario.get("source_ordinal") is not None:
        payload["source_ordinal"] = scenario["source_ordinal"]
    if scenario.get("time_dial") is not None:
        payload["time_dial"] = scenario["time_dial"]
    return payload


def _route_seconds(response_payload: dict[str, Any]) -> list[float]:
    curves = response_payload.get("curves") or []
    _ensure(len(curves) == 1, f"Relay route returned {len(curves)} curve(s), expected 1")
    points = curves[0].get("points") or []
    return [float(point["seconds"]) for point in points]


def probe_parity(
    base_url: str,
    matrix: dict[str, Any],
    scenario: dict[str, Any],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    storage_kind = str(scenario["storage_kind"])
    abs_tol, rel_tol = _tolerances(matrix, storage_kind)
    sql_reference = _fetch_sql_reference(scenario)
    expected_seconds = [float(value) for value in scenario["expected_seconds"]]
    current_multiples = [float(value) for value in scenario["current_multiples"]]

    route_response = _post_json(
        base_url,
        "/api/v1/neta/relay/plot-tcc",
        _route_payload(scenario),
        timeout_seconds=timeout_seconds,
    )
    route_meta = route_response.get("meta") or {}
    route_seconds = _route_seconds(route_response)

    failures: list[str] = []
    warnings: list[str] = []
    failures.extend(
        _compare_series(
            actual=[float(value) for value in sql_reference["seconds"]],
            expected=expected_seconds,
            label="frozen SQL reference",
            abs_tol=abs_tol,
            rel_tol=rel_tol,
        )
    )
    failures.extend(
        _compare_series(
            actual=route_seconds,
            expected=[float(value) for value in sql_reference["seconds"]],
            label="route vs SQL reference",
            abs_tol=abs_tol,
            rel_tol=rel_tol,
        )
    )

    if route_meta.get("status") != "supported":
        failures.append(f"route status expected supported, got {route_meta.get('status')!r}")
    if str(route_meta.get("family_name")).lower() != str(scenario["family"]).lower():
        failures.append(f"route family mismatch: expected {scenario['family']!r}, got {route_meta.get('family_name')!r}")
    if str(route_meta.get("storage_kind")).lower() != storage_kind:
        failures.append(f"route storage_kind mismatch: expected {storage_kind!r}, got {route_meta.get('storage_kind')!r}")

    return {
        "scenario_id": scenario.get("scenario_id"),
        "status": "fail" if failures else ("warn" if warnings else "pass"),
        "warnings": warnings,
        "failures": failures,
        "family": scenario["family"],
        "storage_kind": storage_kind,
        "td_section_source_id": scenario["td_section_source_id"],
        "curve_parent_source_id": scenario.get("curve_parent_source_id"),
        "curve_ordinal": scenario.get("curve_ordinal"),
        "source_ordinal": scenario.get("source_ordinal"),
        "time_dial": scenario.get("time_dial"),
        "current_multiples": current_multiples,
        "tolerance": {
            "abs_seconds": abs_tol,
            "rel_seconds": rel_tol,
        },
        "reference": {
            "method": sql_reference["method"],
            "curve_name": sql_reference.get("curve_name"),
            "seconds": [round(float(value), 12) for value in sql_reference["seconds"]],
            "coefficients": sql_reference.get("coefficients"),
            "point_count": sql_reference.get("point_count"),
        },
        "route": {
            "seconds": [round(float(value), 12) for value in route_seconds],
            "meta": route_meta,
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        matrix = _load_matrix(args.matrix_path)
        scenario_reports = [
            probe_parity(base_url, matrix, scenario, timeout_seconds=args.timeout_seconds)
            for scenario in matrix["scenarios"]
        ]
        database_identity = _fetch_database_identity()
        summary = {
            "scenario_count": len(scenario_reports),
            "family_count": len({item["family"] for item in scenario_reports}),
            "families": sorted({str(item["family"]) for item in scenario_reports}),
            "pass_count": sum(1 for item in scenario_reports if item["status"] == "pass"),
            "warn_count": sum(1 for item in scenario_reports if item["status"] == "warn"),
            "fail_count": sum(1 for item in scenario_reports if item["status"] == "fail"),
            "warning_count": sum(len(item["warnings"]) for item in scenario_reports),
            "failure_count": sum(len(item["failures"]) for item in scenario_reports),
            "blocked_requirements": matrix.get("blocked_requirements") or [],
        }
        report = {
            "base_url": base_url,
            "database_identity": database_identity,
            "matrix_path": str(_resolve_path(args.matrix_path)),
            "summary": summary,
            "scenarios": scenario_reports,
        }
        artifact_path = _write_artifact(report, args.artifact_path)
    except Exception as exc:
        print(f"RESULT FAIL: {exc}", file=sys.stderr)
        return 1

    if artifact_path:
        print(f"ARTIFACT {artifact_path}")

    if summary["fail_count"]:
        print(
            "RESULT FAIL: live relay SQL parity found "
            f"{summary['failure_count']} failure(s) across {summary['scenario_count']} scenario(s)",
            file=sys.stderr,
        )
        return 1

    result_label = "WARN" if summary["warn_count"] else "PASS"
    print(
        f"RESULT {result_label}: live relay SQL parity holds across "
        f"{summary['scenario_count']} seeded scenario(s); families: {', '.join(summary['families'])}; "
        f"warnings: {summary['warning_count']}; failures: {summary['failure_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
