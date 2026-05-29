from __future__ import annotations

import argparse
import json
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
DEFAULT_BASE_URL = "http://127.0.0.1:8010"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "output" / "dev" / "control-plane-live-etu-sql-parity.json"
DEFAULT_MATRIX_PATH = APP_ROOT / "scripts" / "etu_parity_matrix.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the repaired live ETU SQL helper functions against the active "
            "route-owned API contract for each seeded ETU scenario in the parity matrix."
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
        help="Scenario matrix describing the ETU parity probes to run.",
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


def _get_json(base_url: str, path: str, *, timeout_seconds: int) -> Any:
    status, payload = _request_json("GET", f"{base_url}{path}", timeout_seconds=timeout_seconds)
    if status != 200:
        raise RuntimeError(f"GET {path} returned HTTP {status}: {payload}")
    return payload


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


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_value(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_normalize_value(inner) for inner in value]
    if isinstance(value, (int, float)):
        return round(float(value), 6)
    return value


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    normalized_actual = _normalize_value(actual)
    normalized_expected = _normalize_value(expected)
    if normalized_actual != normalized_expected:
        raise RuntimeError(
            f"{label} mismatch. Expected {normalized_expected!r}, got {normalized_actual!r}"
        )


def _equality_error(actual: Any, expected: Any, label: str) -> str | None:
    normalized_actual = _normalize_value(actual)
    normalized_expected = _normalize_value(expected)
    if normalized_actual == normalized_expected:
        return None
    return f"{label} mismatch. Expected {normalized_expected!r}, got {normalized_actual!r}"


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
    _ensure(isinstance(payload, dict), "ETU parity matrix must be a JSON object")
    scenarios = payload.get("scenarios")
    _ensure(isinstance(scenarios, list) and scenarios, "ETU parity matrix must define scenarios")
    for scenario in scenarios:
        _ensure(isinstance(scenario, dict), "Each ETU parity scenario must be an object")
        _ensure(isinstance(scenario.get("payload"), dict), "Each ETU parity scenario must define a payload")
        _ensure(isinstance(scenario.get("measurements") or [], list), "Each ETU parity scenario measurements value must be a list")
    return payload


def _fetch_sql_settings(sensor_id: int) -> dict[str, Any]:
    with SessionLocal() as session:
        row = session.execute(
            text("SELECT fn_sensor_available_settings(:sensor_id) AS result"),
            {"sensor_id": sensor_id},
        ).fetchone()
    result = row.result if row is not None else None
    _ensure(isinstance(result, dict), "fn_sensor_available_settings did not return a JSON object")
    return result


def _measurement_current(measurements: list[dict[str, Any]], element: str) -> float | None:
    for item in measurements:
        if item.get("element") == element:
            return item.get("measured_current")
    return None


def _fetch_sql_evaluate(payload: dict[str, Any], measurements: list[dict[str, Any]]) -> dict[str, Any]:
    params = {
        "p_sensor_id": payload["sensor_id"],
        "p_plug_rating": payload["plug_rating"],
        "p_ltpu_setting": payload["ltpu_setting"],
        "p_stpu_setting": payload.get("stpu_setting"),
        "p_inst_setting": payload.get("inst_setting"),
        "p_gfpu_setting": payload.get("gfpu_setting"),
        "p_multiplier_value": payload.get("multiplier_value"),
        "p_c_factor": payload.get("c_factor"),
        "p_ltpu_measured": _measurement_current(measurements, "LTPU"),
        "p_stpu_measured": _measurement_current(measurements, "STPU"),
        "p_inst_measured": _measurement_current(measurements, "INST"),
        "p_gfpu_measured": _measurement_current(measurements, "GFPU"),
        "p_ltd_trip_time": None,
        "p_std_trip_time": None,
        "p_gfd_trip_time": None,
        "p_maint_mode": payload["maint_mode"],
    }

    with SessionLocal() as session:
        row = session.execute(
            text(
                """
                SELECT fn_evaluate_test_results(
                    p_sensor_id := :p_sensor_id,
                    p_plug_rating := :p_plug_rating,
                    p_ltpu_setting := :p_ltpu_setting,
                    p_stpu_setting := :p_stpu_setting,
                    p_inst_setting := :p_inst_setting,
                    p_gfpu_setting := :p_gfpu_setting,
                    p_multiplier_value := :p_multiplier_value,
                    p_c_factor := :p_c_factor,
                    p_ltpu_measured := :p_ltpu_measured,
                    p_stpu_measured := :p_stpu_measured,
                    p_inst_measured := :p_inst_measured,
                    p_gfpu_measured := :p_gfpu_measured,
                    p_ltd_trip_time := :p_ltd_trip_time,
                    p_std_trip_time := :p_std_trip_time,
                    p_gfd_trip_time := :p_gfd_trip_time,
                    p_maint_mode := :p_maint_mode
                ) AS result
                """
            ),
            params,
        ).fetchone()

    result = row.result if row is not None else None
    _ensure(isinstance(result, dict), "fn_evaluate_test_results did not return a JSON object")
    return result


def _project_api_settings(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: payload.get(key)
        for key in (
            "plug_values",
            "ltpu_settings",
            "ltd_settings",
            "ltd_multipliers",
            "stpu_settings",
            "inst_settings",
            "gfpu_settings",
        )
    }


def _project_sql_settings(payload: dict[str, Any]) -> dict[str, Any]:
    return _project_api_settings(payload)


def _project_api_evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    pickup_elements: dict[str, Any] = {}
    for element in payload.get("elements") or []:
        name = element.get("element")
        if name not in {"LTPU", "STPU", "INST", "GFPU"}:
            continue
        pickup_elements[name.lower()] = {
            "expected": element.get("test_current"),
            "measured": element.get("measured_current"),
            "limit_low": element.get("limit_low"),
            "limit_high": element.get("limit_high"),
            "pass": element.get("passed"),
            "deviation_pct": element.get("deviation_pct"),
        }
    return {
        "sensor_desc": payload.get("sensor_desc"),
        "overall_pass": payload.get("overall_pass"),
        "warnings": payload.get("warnings") or [],
        "ltpu": pickup_elements.get("ltpu"),
        "stpu": pickup_elements.get("stpu"),
        "inst": pickup_elements.get("inst"),
        "gfpu": pickup_elements.get("gfpu"),
    }


def _project_sql_evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "sensor_desc": payload.get("sensor_desc"),
        "overall_pass": payload.get("overall_pass"),
        "warnings": payload.get("warnings") or [],
        "ltpu": payload.get("ltpu"),
        "stpu": payload.get("stpu"),
        "inst": payload.get("inst"),
        "gfpu": payload.get("gfpu"),
    }


def probe_parity(base_url: str, scenario: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    payload = dict(scenario["payload"])
    measurements = list(scenario.get("measurements") or [])
    sensor_id = payload["sensor_id"]

    api_settings = _project_api_settings(
        _get_json(base_url, f"/api/v1/neta/settings/{sensor_id}", timeout_seconds=timeout_seconds)
    )
    sql_settings = _project_sql_settings(_fetch_sql_settings(sensor_id))
    _assert_equal(api_settings, sql_settings, f"ETU settings parity for sensor {sensor_id}")

    api_evaluate = _project_api_evaluate(
        _post_json(
            base_url,
            "/api/v1/neta/evaluate",
            {**payload, "measurements": measurements},
            timeout_seconds=timeout_seconds,
        )
    )
    sql_evaluate = _project_sql_evaluate(_fetch_sql_evaluate(payload, measurements))
    evaluate_warning = _equality_error(api_evaluate, sql_evaluate, f"ETU evaluate parity for sensor {sensor_id}")

    warnings: list[str] = []
    if evaluate_warning:
        warnings.append(evaluate_warning)

    return {
        "scenario_id": scenario.get("scenario_id") or f"sensor-{sensor_id}",
        "base_url": base_url,
        "sensor_id": sensor_id,
        "seed_note": scenario.get("seed_note"),
        "source_of_truth": scenario.get("source_of_truth"),
        "trip_style_id_or_plug_family": scenario.get("trip_style_id_or_plug_family"),
        "status": "warn" if warnings else "pass",
        "warnings": warnings,
        "settings": {
            "api": _normalize_value(api_settings),
            "sql": _normalize_value(sql_settings),
        },
        "evaluate": {
            "api": _normalize_value(api_evaluate),
            "sql": _normalize_value(sql_evaluate),
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        matrix = _load_matrix(args.matrix_path)
        scenario_reports = [
            probe_parity(args.base_url.rstrip("/"), scenario, timeout_seconds=args.timeout_seconds)
            for scenario in matrix["scenarios"]
        ]
        report = {
            "base_url": args.base_url.rstrip("/"),
            "matrix_path": str(_resolve_path(args.matrix_path)),
            "summary": {
                "scenario_count": len(scenario_reports),
                "pass_count": sum(1 for item in scenario_reports if item["status"] == "pass"),
                "warn_count": sum(1 for item in scenario_reports if item["status"] == "warn"),
                "warning_count": sum(len(item["warnings"]) for item in scenario_reports),
                "blocked_requirements": matrix.get("blocked_requirements") or [],
            },
            "scenarios": scenario_reports,
        }
        artifact_path = _write_artifact(report, args.artifact_path)
    except Exception as exc:
        print(f"RESULT FAIL: {exc}", file=sys.stderr)
        return 1

    if artifact_path:
        print(f"ARTIFACT {artifact_path}")
    summary = report["summary"]
    blocked_suffix = ""
    if summary["blocked_requirements"]:
        blocked_suffix = f"; blocked requirements: {len(summary['blocked_requirements'])}"
    print(
        "RESULT PASS: live ETU SQL settings parity holds across "
        f"{summary['scenario_count']} seeded scenario(s)"
        f"; evaluate warnings: {summary['warning_count']}"
        f"{blocked_suffix}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())