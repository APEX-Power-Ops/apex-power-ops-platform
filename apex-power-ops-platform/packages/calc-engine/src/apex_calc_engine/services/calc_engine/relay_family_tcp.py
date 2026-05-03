"""Time-current-point relay-family evaluator."""

from __future__ import annotations

import math
from typing import Sequence

from .relay_types import RelayCurveDefinition, RelayCurvePoint, RelayEvaluatedCurve


def evaluate_tcp(definition: RelayCurveDefinition, current_multiples: Sequence[float], time_dial: float) -> RelayEvaluatedCurve:
    if not definition.points:
        raise ValueError(f"TCP curve '{definition.curve_name}' has no normalized points")

    ordered_points = tuple(sorted(definition.points, key=lambda point: point.current_multiple))
    expected_time_dial = definition.metadata.get('time_dial')
    if expected_time_dial is not None and not math.isclose(float(expected_time_dial), time_dial, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(
            f"TCP curve '{definition.curve_name}' is bound to time dial {expected_time_dial}, received {time_dial}"
        )

    points = []
    for current_multiple in current_multiples:
        trip_time = _log_log_interpolate(ordered_points, float(current_multiple))
        points.append(
            RelayCurvePoint(
                current_multiple=float(current_multiple),
                trip_time_seconds=trip_time,
                time_dial=time_dial,
                source_ordinal=ordered_points[0].source_ordinal,
                label=ordered_points[0].label,
            )
        )

    return RelayEvaluatedCurve(
        family=definition.family,
        curve_name=definition.curve_name,
        time_dial=time_dial,
        points=tuple(points),
    )


def _log_log_interpolate(points: tuple[RelayCurvePoint, ...], current_multiple: float) -> float:
    if current_multiple <= 0:
        raise ValueError(f'Current multiple must be positive, received {current_multiple}')
    if current_multiple < points[0].current_multiple or current_multiple > points[-1].current_multiple:
        raise ValueError(
            f'Current multiple {current_multiple} is outside the TCP domain '
            f'[{points[0].current_multiple}, {points[-1].current_multiple}]'
        )

    for point in points:
        if math.isclose(point.current_multiple, current_multiple, rel_tol=1e-9, abs_tol=1e-9):
            return point.trip_time_seconds

    lower, upper = _find_bracketing_points(points, current_multiple)
    x1 = math.log10(lower.current_multiple)
    x2 = math.log10(upper.current_multiple)
    y1 = math.log10(lower.trip_time_seconds)
    y2 = math.log10(upper.trip_time_seconds)
    x = math.log10(current_multiple)
    y = y1 + ((y2 - y1) * (x - x1) / (x2 - x1))
    return 10 ** y


def _find_bracketing_points(points: tuple[RelayCurvePoint, ...], current_multiple: float) -> tuple[RelayCurvePoint, RelayCurvePoint]:
    for index in range(1, len(points)):
        lower = points[index - 1]
        upper = points[index]
        if lower.current_multiple <= current_multiple <= upper.current_multiple:
            return lower, upper
    raise ValueError(f'Current multiple {current_multiple} has no TCP segment')