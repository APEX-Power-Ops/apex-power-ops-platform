"""Focused relay calc fixtures for the Tranche 3 relay package slice."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apex_calc_engine.services.calc_engine import (
    RelayCurveDefinition,
    RelayCurvePoint,
    RelayEvaluationStatus,
    RelayFormulaCode,
    evaluate_curve_definition,
    family_from_model_code,
)


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'relay' / 'golden_curves.json'


def _load_fixtures() -> list[dict]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
    return payload['fixtures']


@pytest.mark.parametrize('fixture', _load_fixtures(), ids=lambda fixture: f"{fixture['family'].lower()}-{fixture['curve_name']}")
def test_relay_family_golden_fixtures(fixture: dict) -> None:
    family = RelayFormulaCode[fixture['family']]
    definition = RelayCurveDefinition(
        family=family,
        curve_name=fixture['curve_name'],
        source_row_id=fixture['source_row_id'],
        parent_source_id=fixture['parent_source_id'],
        coefficients=fixture.get('coefficients', {}),
        points=tuple(
            RelayCurvePoint(
                current_multiple=point['current_multiple'],
                trip_time_seconds=point['trip_time_seconds'],
                source_ordinal=fixture.get('source_ordinal'),
                time_dial=fixture.get('time_dial'),
                label=fixture.get('label'),
            )
            for point in fixture.get('points', [])
        ),
        metadata={
            'time_dial': fixture.get('time_dial'),
            'source_ordinal': fixture.get('source_ordinal'),
            'td_desc': fixture.get('label'),
        },
    )

    result = evaluate_curve_definition(
        definition,
        fixture['current_multiples'],
        time_dial=fixture['time_dial'],
    )

    assert result.status == RelayEvaluationStatus.SUPPORTED
    assert len(result.points) == len(fixture['expected_seconds'])
    for point, expected_seconds in zip(result.points, fixture['expected_seconds'], strict=True):
        assert point.trip_time_seconds == pytest.approx(expected_seconds, rel=1e-6, abs=1e-9)


@pytest.mark.parametrize(
    ('model_code', 'family'),
    [
        (1, RelayFormulaCode.TCP),
        (2, RelayFormulaCode.IEC),
        (3, RelayFormulaCode.MEQ),
        (4, RelayFormulaCode.BSL),
        (5, RelayFormulaCode.SWZ),
        (6, RelayFormulaCode.PCD),
        (7, RelayFormulaCode.RXD),
        (8, RelayFormulaCode.LRM),
        (9, RelayFormulaCode.EGC),
    ],
)
def test_relay_model_code_mapping(model_code: int, family: RelayFormulaCode) -> None:
    assert family_from_model_code(model_code) == family


@pytest.mark.parametrize('family', [RelayFormulaCode.RXD, RelayFormulaCode.LRM, RelayFormulaCode.EGC])
def test_relay_unsupported_families_are_explicit(family: RelayFormulaCode) -> None:
    definition = RelayCurveDefinition(
        family=family,
        curve_name=f'{family.name} unsupported',
        source_row_id=999,
        parent_source_id=998,
    )

    result = evaluate_curve_definition(definition, [2.0, 5.0], time_dial=1.0)

    assert result.status == RelayEvaluationStatus.UNSUPPORTED
    assert result.points == ()
    assert result.reason is not None
    assert 'unsupported' in result.reason.lower()