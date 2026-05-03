"""IEC relay-family evaluator."""

from __future__ import annotations

from typing import Sequence

from .relay_types import RelayCurveDefinition, RelayCurvePoint, RelayEvaluatedCurve


def evaluate_iec(definition: RelayCurveDefinition, current_multiples: Sequence[float], time_dial: float) -> RelayEvaluatedCurve:
    v_k, v_e = definition.require_coefficients('v_k', 'v_e')
    dt_after = definition.coefficients.get('dt_after')
    dt_min_time = definition.coefficients.get('dt_min_time')
    points = []
    for current_multiple in current_multiples:
        denominator = pow(float(current_multiple), v_e) - 1.0
        if denominator <= 0:
            raise ValueError(f'IEC current multiple must be greater than 1.0, received {current_multiple}')
        trip_time = time_dial * v_k / denominator
        if dt_after is not None and dt_min_time is not None and float(current_multiple) >= float(dt_after):
            trip_time = max(trip_time, float(dt_min_time))
        points.append(RelayCurvePoint(current_multiple=float(current_multiple), trip_time_seconds=trip_time, time_dial=time_dial))

    return RelayEvaluatedCurve(
        family=definition.family,
        curve_name=definition.curve_name,
        time_dial=time_dial,
        points=tuple(points),
    )