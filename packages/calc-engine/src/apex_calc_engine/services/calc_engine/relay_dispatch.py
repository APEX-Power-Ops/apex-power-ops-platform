"""Relay family dispatch and definition builders."""

from __future__ import annotations

from decimal import Decimal
from typing import Callable, Sequence

from apex_calc_engine.models.relay import (
    RelayCurveBSL,
    RelayCurveIEC,
    RelayCurveMEQ,
    RelayCurvePCD,
    RelayCurvePointTCP,
    RelayCurveRowBSL,
    RelayCurveRowIEC,
    RelayCurveRowMEQ,
    RelayCurveRowPCD,
    RelayCurveRowSWZ,
    RelayCurveSWZ,
    RelayCurveTCP,
)

from .relay_family_bsl import evaluate_bsl
from .relay_family_iec import evaluate_iec
from .relay_family_meq import evaluate_meq
from .relay_family_pcd import evaluate_pcd
from .relay_family_swz import evaluate_swz
from .relay_family_tcp import evaluate_tcp
from .relay_types import (
    RelayCurveDefinition,
    RelayCurvePoint,
    RelayEvaluatedCurve,
    RelayEvaluationStatus,
    RelayFormulaCode,
    SUPPORTED_FAMILIES,
    UNSUPPORTED_FAMILIES,
)


Evaluator = Callable[[RelayCurveDefinition, Sequence[float], float], RelayEvaluatedCurve]


_EVALUATORS: dict[RelayFormulaCode, Evaluator] = {
    RelayFormulaCode.IEC: evaluate_iec,
    RelayFormulaCode.SWZ: evaluate_swz,
    RelayFormulaCode.BSL: evaluate_bsl,
    RelayFormulaCode.MEQ: evaluate_meq,
    RelayFormulaCode.PCD: evaluate_pcd,
    RelayFormulaCode.TCP: evaluate_tcp,
}


def family_from_model_code(model_code: int) -> RelayFormulaCode:
    try:
        return RelayFormulaCode(model_code)
    except ValueError as exc:
        raise ValueError(f'Unsupported relay model code: {model_code}') from exc


def evaluate_curve_definition(
    definition: RelayCurveDefinition,
    current_multiples: Sequence[float],
    *,
    time_dial: float = 1.0,
) -> RelayEvaluatedCurve:
    family = RelayFormulaCode(definition.family)
    normalized_multiples = tuple(float(value) for value in current_multiples)
    if not normalized_multiples:
        raise ValueError('At least one current multiple is required')

    for current_multiple in normalized_multiples:
        if current_multiple <= 0:
            raise ValueError(f'Current multiple must be positive, received {current_multiple}')

    if family in UNSUPPORTED_FAMILIES:
        return RelayEvaluatedCurve(
            family=family,
            curve_name=definition.curve_name,
            time_dial=float(time_dial),
            points=(),
            status=RelayEvaluationStatus.UNSUPPORTED,
            reason=f'{family.name.lower()} relay family remains explicitly unsupported in Tranche 3.',
        )

    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f'Relay family {family} is not registered for evaluation')

    return _EVALUATORS[family](definition, normalized_multiples, float(time_dial))


def definition_from_iec_row(parent: RelayCurveIEC, row: RelayCurveRowIEC) -> RelayCurveDefinition:
    return RelayCurveDefinition(
        family=RelayFormulaCode.IEC,
        curve_name=row.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=row.ordinal,
        coefficients={
            'v_k': _to_float(row.v_k),
            'v_e': _to_float(row.v_e),
            'dt_after': _optional_float(row.dt_after),
            'dt_min_time': _optional_float(row.dt_min_time),
        },
    )


def definition_from_swz_row(parent: RelayCurveSWZ, row: RelayCurveRowSWZ) -> RelayCurveDefinition:
    return RelayCurveDefinition(
        family=RelayFormulaCode.SWZ,
        curve_name=row.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=row.ordinal,
        coefficients={
            'v_a': _to_float(row.v_a),
            'v_b': _to_float(row.v_b),
            'v_e': _to_float(row.v_e),
        },
    )


def definition_from_bsl_row(parent: RelayCurveBSL, row: RelayCurveRowBSL) -> RelayCurveDefinition:
    return RelayCurveDefinition(
        family=RelayFormulaCode.BSL,
        curve_name=row.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=row.ordinal,
        coefficients={
            'v_a': _to_float(row.v_a),
            'v_b': _to_float(row.v_b),
            'v_c': _to_float(row.v_c),
            'v_d': _optional_float(row.v_d),
            'v_n': _to_float(row.v_n),
            'v_k': _to_float(row.v_k),
            'v_r': _optional_float(row.v_r),
        },
    )


def definition_from_meq_row(parent: RelayCurveMEQ, row: RelayCurveRowMEQ) -> RelayCurveDefinition:
    return RelayCurveDefinition(
        family=RelayFormulaCode.MEQ,
        curve_name=row.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=row.ordinal,
        coefficients={
            'v_a': _to_float(row.v_a),
            'v_b': _to_float(row.v_b),
            'v_c': _to_float(row.v_c),
            'v_d': _to_float(row.v_d),
            'v_e': _to_float(row.v_e),
        },
    )


def definition_from_pcd_row(parent: RelayCurvePCD, row: RelayCurveRowPCD) -> RelayCurveDefinition:
    return RelayCurveDefinition(
        family=RelayFormulaCode.PCD,
        curve_name=row.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=row.ordinal,
        coefficients={
            'v_a': _to_float(row.v_a),
            'v_b': _to_float(row.v_b),
            'v_c': _to_float(row.v_c),
        },
    )


def definition_from_tcp_points(parent: RelayCurveTCP, points: Sequence[RelayCurvePointTCP]) -> RelayCurveDefinition:
    ordered_points = tuple(sorted(points, key=lambda point: point.current_index))
    if not ordered_points:
        raise ValueError(f"TCP parent '{parent.curve_name}' has no normalized points")

    time_dials = {float(point.time_dial) for point in ordered_points}
    ordinals = {point.source_ordinal for point in ordered_points}
    labels = {point.td_desc for point in ordered_points}
    if len(time_dials) != 1 or len(ordinals) != 1:
        raise ValueError('TCP definitions must be built from a single time-dial row at a time')

    return RelayCurveDefinition(
        family=RelayFormulaCode.TCP,
        curve_name=parent.curve_name,
        source_row_id=parent.source_row_id,
        parent_source_id=parent.relay_td_section_source_id,
        ordinal=parent.ordinal,
        points=tuple(
            RelayCurvePoint(
                current_multiple=float(point.current_value),
                trip_time_seconds=float(point.trip_time_seconds),
                source_ordinal=point.source_ordinal,
                time_dial=float(point.time_dial),
                label=point.td_desc,
            )
            for point in ordered_points
        ),
        metadata={
            'time_dial': time_dials.pop(),
            'source_ordinal': ordinals.pop(),
            'td_desc': labels.pop(),
            'tcc_number': parent.tcc_number,
        },
    )


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        raise ValueError('Relay coefficient cannot be null for supported families')
    return float(value)


def _optional_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)