from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://127.0.0.1:8010"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_CANDIDATE_LIMIT = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_PATH = REPO_ROOT / "output" / "dev" / "control-plane-local-neta-family-smoke.json"

KNOWN_ETU_SCENARIO = {
    "sensor_id": 25,
    "manufacturer_name": "GE",
    "trip_type_name": "MVT RMS-9",
    "trip_style_name": "ICCB",
    "sensor_desc": "800",
    "rating": 800.0,
    "payload": {
        "sensor_id": 25,
        "plug_rating": 800.0,
        "ltpu_setting": 0.8,
        "ltd_setting": 6.0,
        "stpu_setting": 4.0,
        "std_setting": 0.21,
        "inst_setting": 10.0,
        "gfpu_setting": 0.4,
        "gfd_setting": 0.21,
        "maint_mode": False,
    },
    "measurements": [
        {"element": "LTPU", "measured_current": 650.0},
        {"element": "STPU", "measured_current": 3100.0},
        {"element": "GFPU", "measured_current": 310.0},
    ],
    "evaluate": {
        "overall_pass": False,
        "tested_count": 3,
        "passed_count": 2,
        "failed_count": 1,
        "passed_elements": {"LTPU", "GFPU"},
        "failed_elements": {"STPU"},
    },
    "calculate_warning_count": 0,
    "plot_warning_count": 0,
    "plot_curve_count": 2,
}

KNOWN_TMT_SCENARIO = {
    "frame_id": 8038,
    "manufacturer_name": "ABB",
    "trip_class": 4,
    "curve_count": 1,
}

KNOWN_EMT_SCENARIO = {
    "frame_id": 2953,
    "section_id": 6200,
    "band_id": 12354,
    "curve_class": 0,
    "manufacturer_name": "Allis-Chalmers",
    "curve_count": 1,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the local NETA family runtime against a live-backed control-plane host. "
            "The smoke proves ETU cascade/search availability, then loads one TMT and one EMT "
            "candidate deeply enough to render their plot routes."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for the local control-plane runtime.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout for each request.",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=DEFAULT_CANDIDATE_LIMIT,
        help="How many TMT/EMT frame candidates to scan when selecting a smoke target.",
    )
    parser.add_argument(
        "--artifact-path",
        default=str(DEFAULT_ARTIFACT_PATH),
        help="Optional JSON artifact path for the smoke report. Use an empty string to disable artifact writing.",
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
            parsed_payload = json.loads(raw) if raw.strip() else {}
            return response.status, parsed_payload
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed_payload = json.loads(detail) if detail.strip() else {"detail": exc.reason}
        except json.JSONDecodeError:
            parsed_payload = {"detail": detail or exc.reason}
        return exc.code, parsed_payload
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


def _normalize_number(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return float(value)
    return value


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if _normalize_number(actual) != _normalize_number(expected):
        raise RuntimeError(f"{label}: expected {expected!r}, got {actual!r}")


def _find_by_id(items: list[dict[str, Any]], key: str, expected_value: Any) -> dict[str, Any] | None:
    for item in items:
        if item.get(key) == expected_value:
            return item
    return None


def _write_artifact(report: dict[str, Any], artifact_path: str | None) -> str | None:
    if not artifact_path:
        return None
    target = Path(artifact_path)
    if not target.is_absolute():
        target = (REPO_ROOT / target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(target)


def _validate_etu_known_scenario(base_url: str, *, timeout_seconds: int) -> dict[str, Any]:
    sensor_id = KNOWN_ETU_SCENARIO["sensor_id"]
    context = _get_json(base_url, f"/api/v1/neta/context/{sensor_id}", timeout_seconds=timeout_seconds)
    settings = _get_json(base_url, f"/api/v1/neta/settings/{sensor_id}", timeout_seconds=timeout_seconds)

    _assert_equal(context.get("manufacturer_name"), KNOWN_ETU_SCENARIO["manufacturer_name"], "ETU context manufacturer")
    _assert_equal(context.get("trip_type_name"), KNOWN_ETU_SCENARIO["trip_type_name"], "ETU context trip type")
    _assert_equal(context.get("trip_style_name"), KNOWN_ETU_SCENARIO["trip_style_name"], "ETU context trip style")
    _assert_equal(context.get("sensor_desc"), KNOWN_ETU_SCENARIO["sensor_desc"], "ETU context sensor description")
    _assert_equal(context.get("rating"), KNOWN_ETU_SCENARIO["rating"], "ETU context rating")

    payload = dict(KNOWN_ETU_SCENARIO["payload"])
    plug_values = list(settings.get("plug_values") or [])
    ltpu_settings = list(settings.get("ltpu_settings") or [])
    ltd_open_times = [entry.get("open_time") for entry in settings.get("ltd_settings") or []]
    stpu_settings = list(settings.get("stpu_settings") or [])
    std_open_times = [entry.get("open_time") for entry in settings.get("std_settings") or []]
    inst_settings = list(settings.get("inst_settings") or [])
    gfpu_settings = list(settings.get("gfpu_settings") or [])
    gfd_open_times = [entry.get("open_time") for entry in settings.get("gfd_settings") or []]
    for value, values, label in [
        (payload["plug_rating"], plug_values, "ETU plug setting"),
        (payload["ltpu_setting"], ltpu_settings, "ETU LTPU setting"),
        (payload["ltd_setting"], ltd_open_times, "ETU LTD setting"),
        (payload["stpu_setting"], stpu_settings, "ETU STPU setting"),
        (payload["std_setting"], std_open_times, "ETU STD setting"),
        (payload["inst_setting"], inst_settings, "ETU INST setting"),
        (payload["gfpu_setting"], gfpu_settings, "ETU GFPU setting"),
        (payload["gfd_setting"], gfd_open_times, "ETU GFD setting"),
    ]:
        _ensure(any(_normalize_number(item) == _normalize_number(value) for item in values), f"{label}: expected {value!r} in {values!r}")

    calculate = _post_json(base_url, "/api/v1/neta/calculate", payload, timeout_seconds=timeout_seconds)
    calculate_warnings = list(calculate.get("warnings") or [])
    _assert_equal(len(calculate_warnings), KNOWN_ETU_SCENARIO["calculate_warning_count"], "ETU calculate warning count")
    calc_elements = {element.get("element"): element for element in calculate.get("elements") or []}
    _assert_equal(calc_elements.get("LTPU", {}).get("test_current"), 640.0, "ETU calculate LTPU current")
    _assert_equal(calc_elements.get("STPU", {}).get("test_current"), 2560.0, "ETU calculate STPU current")
    _assert_equal(calc_elements.get("GFPU", {}).get("test_current"), 320.0, "ETU calculate GFPU current")

    measurements = list(KNOWN_ETU_SCENARIO["measurements"])
    evaluate = _post_json(
        base_url,
        "/api/v1/neta/evaluate",
        {**payload, "measurements": measurements},
        timeout_seconds=timeout_seconds,
    )
    expected_eval = KNOWN_ETU_SCENARIO["evaluate"]
    for key in ("overall_pass", "tested_count", "passed_count", "failed_count"):
        _assert_equal(evaluate.get(key), expected_eval[key], f"ETU evaluate {key}")
    eval_elements = {element.get("element"): element for element in evaluate.get("elements") or []}
    passed_elements = {name for name, element in eval_elements.items() if element.get("passed") is True}
    failed_elements = {name for name, element in eval_elements.items() if element.get("passed") is False}
    _assert_equal(passed_elements, expected_eval["passed_elements"], "ETU evaluate passed elements")
    _assert_equal(failed_elements, expected_eval["failed_elements"], "ETU evaluate failed elements")

    plot = _post_json(
        base_url,
        "/api/v1/neta/plot-tcc",
        {**payload, "measurements": measurements, "include_measured_markers": True},
        timeout_seconds=timeout_seconds,
    )
    plot_warnings = list(plot.get("warnings") or [])
    _assert_equal(len(plot_warnings), KNOWN_ETU_SCENARIO["plot_warning_count"], "ETU plot warning count")
    plot_meta = dict(plot.get("meta") or {})
    _assert_equal(len(plot.get("curves") or []), KNOWN_ETU_SCENARIO["plot_curve_count"], "ETU plot curve count")
    _assert_equal(plot_meta.get("sensor_desc"), KNOWN_ETU_SCENARIO["sensor_desc"], "ETU plot sensor description")

    return {
        "sensor_id": sensor_id,
        "manufacturer_name": context.get("manufacturer_name"),
        "trip_type_name": context.get("trip_type_name"),
        "trip_style_name": context.get("trip_style_name"),
        "sensor_desc": context.get("sensor_desc"),
        "rating": context.get("rating"),
        "calculate_warning_count": len(calculate_warnings),
        "evaluate": {
            "overall_pass": evaluate.get("overall_pass"),
            "tested_count": evaluate.get("tested_count"),
            "passed_count": evaluate.get("passed_count"),
            "failed_count": evaluate.get("failed_count"),
            "passed_elements": sorted(passed_elements),
            "failed_elements": sorted(failed_elements),
        },
        "plot_warning_count": len(plot_warnings),
        "plot_curve_count": len(plot.get("curves") or []),
    }


def _validate_tmt_known_scenario(base_url: str, *, timeout_seconds: int) -> dict[str, Any]:
    frames_payload = _get_json(base_url, "/api/v1/neta/tmt/frames", timeout_seconds=timeout_seconds)
    frames = list(frames_payload.get("frames") or [])
    _ensure(bool(frames), "TMT frame search returned no frames")
    frame = _find_by_id(frames, "frame_id", KNOWN_TMT_SCENARIO["frame_id"])
    _ensure(frame is not None, f"TMT known frame {KNOWN_TMT_SCENARIO['frame_id']} was not returned by /tmt/frames")
    context = _get_json(base_url, f"/api/v1/neta/tmt/context/{KNOWN_TMT_SCENARIO['frame_id']}", timeout_seconds=timeout_seconds)
    settings = _get_json(base_url, f"/api/v1/neta/tmt/settings/{KNOWN_TMT_SCENARIO['frame_id']}", timeout_seconds=timeout_seconds)
    _assert_equal(context.get("manufacturer_name"), KNOWN_TMT_SCENARIO["manufacturer_name"], "TMT context manufacturer")
    _ensure(KNOWN_TMT_SCENARIO["trip_class"] in list(settings.get("available_trip_classes") or []), "TMT known trip class is absent from settings")
    plot = _post_json(
        base_url,
        "/api/v1/neta/tmt/plot-tcc",
        {
            "frame_id": KNOWN_TMT_SCENARIO["frame_id"],
            "trip_class": KNOWN_TMT_SCENARIO["trip_class"],
            "include_raw_points": True,
        },
        timeout_seconds=timeout_seconds,
    )
    _assert_equal(len(plot.get("curves") or []), KNOWN_TMT_SCENARIO["curve_count"], "TMT plot curve count")
    return {
        "frame_count": len(frames),
        "frame_id": KNOWN_TMT_SCENARIO["frame_id"],
        "manufacturer_name": context.get("manufacturer_name"),
        "trip_class": KNOWN_TMT_SCENARIO["trip_class"],
        "curve_count": len(plot.get("curves") or []),
    }


def _validate_emt_known_scenario(base_url: str, *, timeout_seconds: int) -> dict[str, Any]:
    frames_payload = _get_json(base_url, "/api/v1/neta/emt/frames", timeout_seconds=timeout_seconds)
    frames = list(frames_payload.get("frames") or [])
    _ensure(bool(frames), "EMT frame search returned no frames")
    frame = _find_by_id(frames, "frame_id", KNOWN_EMT_SCENARIO["frame_id"])
    _ensure(frame is not None, f"EMT known frame {KNOWN_EMT_SCENARIO['frame_id']} was not returned by /emt/frames")
    context = _get_json(base_url, f"/api/v1/neta/emt/context/{KNOWN_EMT_SCENARIO['frame_id']}", timeout_seconds=timeout_seconds)
    _assert_equal(context.get("manufacturer_name"), KNOWN_EMT_SCENARIO["manufacturer_name"], "EMT context manufacturer")
    section = _find_by_id(list(context.get("sections") or []), "section_id", KNOWN_EMT_SCENARIO["section_id"])
    _ensure(section is not None, f"EMT known section {KNOWN_EMT_SCENARIO['section_id']} was not returned by /emt/context")
    settings = _get_json(base_url, f"/api/v1/neta/emt/settings/{KNOWN_EMT_SCENARIO['section_id']}", timeout_seconds=timeout_seconds)
    band = _find_by_id(list(settings.get("bands") or []), "band_id", KNOWN_EMT_SCENARIO["band_id"])
    _ensure(band is not None, f"EMT known band {KNOWN_EMT_SCENARIO['band_id']} was not returned by /emt/settings")
    curve_classes = list(band.get("curve_classes") or [])
    _ensure(KNOWN_EMT_SCENARIO["curve_class"] in curve_classes, "EMT known curve class is absent from the known band")
    plot = _post_json(
        base_url,
        "/api/v1/neta/emt/plot-tcc",
        {
            "section_id": KNOWN_EMT_SCENARIO["section_id"],
            "band_id": KNOWN_EMT_SCENARIO["band_id"],
            "curve_class": KNOWN_EMT_SCENARIO["curve_class"],
        },
        timeout_seconds=timeout_seconds,
    )
    _assert_equal(len(plot.get("curves") or []), KNOWN_EMT_SCENARIO["curve_count"], "EMT plot curve count")
    return {
        "frame_count": len(frames),
        "frame_id": KNOWN_EMT_SCENARIO["frame_id"],
        "section_id": KNOWN_EMT_SCENARIO["section_id"],
        "band_id": KNOWN_EMT_SCENARIO["band_id"],
        "manufacturer_name": context.get("manufacturer_name"),
        "curve_count": len(plot.get("curves") or []),
    }


def _choose_tmt_candidate(base_url: str, *, timeout_seconds: int, candidate_limit: int) -> dict[str, Any]:
    frames_payload = _get_json(base_url, "/api/v1/neta/tmt/frames", timeout_seconds=timeout_seconds)
    frames = list(frames_payload.get("frames") or [])
    _ensure(bool(frames), "TMT frame search returned no frames")

    for frame in frames[:candidate_limit]:
        frame_id = frame.get("frame_id")
        if frame_id is None:
            continue
        context = _get_json(base_url, f"/api/v1/neta/tmt/context/{frame_id}", timeout_seconds=timeout_seconds)
        settings = _get_json(base_url, f"/api/v1/neta/tmt/settings/{frame_id}", timeout_seconds=timeout_seconds)
        trip_classes = list(settings.get("available_trip_classes") or [])
        if trip_classes:
            return {
                "frame": frame,
                "context": context,
                "settings": settings,
                "trip_class": trip_classes[0],
                "frame_count": len(frames),
            }

    raise RuntimeError("No TMT frame candidate exposed at least one trip class")


def _choose_emt_candidate(base_url: str, *, timeout_seconds: int, candidate_limit: int) -> dict[str, Any]:
    frames_payload = _get_json(base_url, "/api/v1/neta/emt/frames", timeout_seconds=timeout_seconds)
    frames = list(frames_payload.get("frames") or [])
    _ensure(bool(frames), "EMT frame search returned no frames")

    for frame in frames[:candidate_limit]:
        frame_id = frame.get("frame_id")
        if frame_id is None:
            continue
        context = _get_json(base_url, f"/api/v1/neta/emt/context/{frame_id}", timeout_seconds=timeout_seconds)
        sections = list(context.get("sections") or [])
        for section in sections:
            section_id = section.get("section_id")
            if section_id is None:
                continue
            settings = _get_json(base_url, f"/api/v1/neta/emt/settings/{section_id}", timeout_seconds=timeout_seconds)
            bands = list(settings.get("bands") or [])
            if bands:
                band = bands[0]
                curve_classes = list(band.get("curve_classes") or [])
                return {
                    "frame": frame,
                    "context": context,
                    "section": section,
                    "settings": settings,
                    "band": band,
                    "curve_class": curve_classes[0] if curve_classes else None,
                    "frame_count": len(frames),
                }

    raise RuntimeError("No EMT frame candidate exposed at least one banded section")


def main() -> int:
    args = build_parser().parse_args()
    base_url = args.base_url.rstrip("/")

    catalog = _get_json(base_url, "/api/v1/neta/catalog/status", timeout_seconds=args.timeout_seconds)
    _ensure(catalog.get("catalog") == "live", f"Catalog is not live: {catalog}")
    _ensure((catalog.get("manufacturer_count") or 0) > 0, f"Catalog returned no manufacturers: {catalog}")
    _ensure((catalog.get("sensor_count") or 0) > 0, f"Catalog returned no sensors: {catalog}")

    cascade = _get_json(base_url, "/api/v1/neta/cascade", timeout_seconds=args.timeout_seconds)
    manufacturers = list(cascade.get("manufacturers") or [])
    _ensure(bool(manufacturers), "ETU cascade returned no manufacturers")

    query = parse.urlencode({"limit": 25})
    etu_search = _get_json(base_url, f"/api/v1/neta/etu/search?{query}", timeout_seconds=args.timeout_seconds)
    etu_results = list(etu_search.get("results") or [])
    _ensure(bool(etu_results), "ETU search returned no matches")

    etu = _validate_etu_known_scenario(base_url, timeout_seconds=args.timeout_seconds)
    tmt = _validate_tmt_known_scenario(base_url, timeout_seconds=args.timeout_seconds)
    emt = _validate_emt_known_scenario(base_url, timeout_seconds=args.timeout_seconds)

    report = {
        "base_url": base_url,
        "catalog": {
            "manufacturer_count": catalog.get("manufacturer_count"),
            "sensor_count": catalog.get("sensor_count"),
        },
        "etu": {
            "manufacturer_options": len(manufacturers),
            "search_count": etu_search.get("count"),
            "sample_sensor_id": etu_results[0].get("sensor_id"),
            "known_scenario": etu,
        },
        "tmt": tmt,
        "emt": emt,
    }
    artifact_path = _write_artifact(report, args.artifact_path.strip())
    if artifact_path:
        report["artifact_path"] = artifact_path
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())