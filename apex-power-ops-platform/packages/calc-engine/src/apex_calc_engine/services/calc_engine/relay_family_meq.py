"""GE Multilin relay-family evaluator."""

from __future__ import annotations

from typing import Sequence

from .relay_types import RelayCurveDefinition, RelayCurvePoint, RelayEvaluatedCurve


def evaluate_meq(definition: RelayCurveDefinition, current_multiples: Sequence[float], time_dial: float) -> RelayEvaluatedCurve:
    v_a, v_b, v_c, v_d, v_e = definition.require_coefficients('v_a', 'v_b', 'v_c', 'v_d', 'v_e')
    points = []
    for current_multiple in current_multiples:
        delta = float(current_multiple) - v_c
        if delta <= 0:
            raise ValueError(f'MEQ current multiple must exceed v_c, received {current_multiple}')
        delta_sq = delta * delta
        trip_time = (v_a + (v_b / delta) + (v_d / delta_sq) + (v_e / (delta_sq * delta))) * time_dial
        points.append(RelayCurvePoint(current_multiple=float(current_multiple), trip_time_seconds=trip_time, time_dial=time_dial))

    return RelayEvaluatedCurve(
        family=definition.family,
        curve_name=definition.curve_name,
        time_dial=time_dial,
        points=tuple(points),
    )