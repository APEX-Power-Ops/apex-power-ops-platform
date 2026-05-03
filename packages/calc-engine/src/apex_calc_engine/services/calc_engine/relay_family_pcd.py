"""Programmable curve-definition relay-family evaluator."""

from __future__ import annotations

from typing import Sequence

from .relay_types import RelayCurveDefinition, RelayCurvePoint, RelayEvaluatedCurve


def evaluate_pcd(definition: RelayCurveDefinition, current_multiples: Sequence[float], time_dial: float) -> RelayEvaluatedCurve:
    v_a, v_b, v_c = definition.require_coefficients('v_a', 'v_b', 'v_c')
    points = []
    for current_multiple in current_multiples:
        denominator = pow(float(current_multiple), v_c) - 1.0
        if denominator <= 0:
            raise ValueError(f'PCD current multiple must be greater than 1.0, received {current_multiple}')
        trip_time = time_dial * ((v_a / denominator) + v_b)
        points.append(RelayCurvePoint(current_multiple=float(current_multiple), trip_time_seconds=trip_time, time_dial=time_dial))

    return RelayEvaluatedCurve(
        family=definition.family,
        curve_name=definition.curve_name,
        time_dial=time_dial,
        points=tuple(points),
    )