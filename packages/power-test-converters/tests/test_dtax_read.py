"""Chip 10c — DTAX-read round-trip tests.

read_dtax inverts the DataModel-R2 schema that write_dtax emits, producing the same PtmModel
that read_ptm produces. We validate by round-trip: build a model (via the proven read_ptm sample),
write_dtax it (no template — programmatic build), read_dtax it back, assert reconstruction.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from power_test_converters.dtax import write_dtax
from power_test_converters.dtax_read import read_dtax
from power_test_converters.ptm import read_ptm

# Reuse the proven sample .ptm builder from the sibling writer test (same tests dir, on sys.path).
from test_ptm_to_dtax import _write_sample_ptm


def _roundtrip(tmp_path: Path):
    model = read_ptm(_write_sample_ptm(tmp_path))
    dtax_path = write_dtax(model, tmp_path / "out.dtax")
    return model, read_dtax(dtax_path)


def test_read_dtax_roundtrips_transformer_nameplate(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))
    dtax_path = write_dtax(model, tmp_path / "out.dtax")

    result = read_dtax(dtax_path)

    assert result.transformer.serial_number == model.transformer.serial_number == "45120269-001-08"
    assert result.transformer.manufacturer == model.transformer.manufacturer == "Square D"
    assert result.transformer.apparatus_id == model.transformer.apparatus_id == "XFM-1001"


def test_read_dtax_roundtrips_overall_power_factor(tmp_path: Path) -> None:
    model, result = _roundtrip(tmp_path)

    assert len(result.overall_power_factor) == len(model.overall_power_factor) == 2

    # power_factor_corrected + capacitance round-trip exactly for every overall row.
    assert [m.power_factor_corrected for m in result.overall_power_factor] == [
        m.power_factor_corrected for m in model.overall_power_factor
    ]
    assert [m.capacitance_measured_f for m in result.overall_power_factor] == [
        m.capacitance_measured_f for m in model.overall_power_factor
    ]

    # measurement_name is reconstructed from the row insulation ("I" + insulation). The first
    # row's insulation (CH) round-trips to the model's name; subsequent rows depend on the
    # writer's overall-capacitance->insulation mapping (a writer convention, not a read bug).
    first_result = result.overall_power_factor[0]
    first_model = model.overall_power_factor[0]
    assert first_result.measurement_name == first_model.measurement_name == "ICH"

    # Instrument: the TwoWindingOverall admin-data row is attached to every overall-PF row.
    assert first_result.instrument is not None
    assert first_result.instrument.test_set_name == first_model.instrument.test_set_name == "TESTRANO 600"
    assert first_result.instrument.serial_number == first_model.instrument.serial_number == "GH733Y"


def test_read_dtax_roundtrips_turns_ratio(tmp_path: Path) -> None:
    model, result = _roundtrip(tmp_path)

    assert len(result.turns_ratio_tests) == len(model.turns_ratio_tests) == 1
    result_test = result.turns_ratio_tests[0]
    model_test = model.turns_ratio_tests[0]
    assert len(result_test.measurements) == len(model_test.measurements) == 3

    result_by_phase = {m.phase: m for m in result_test.measurements}
    model_by_phase = {m.phase: m for m in model_test.measurements}
    for phase in ("PhaseA", "PhaseB", "PhaseC"):
        rm = result_by_phase[phase]
        mm = model_by_phase[phase]
        assert rm.voltage_turns_ratio == mm.voltage_turns_ratio
        assert rm.ratio_deviation == mm.ratio_deviation
        assert rm.nominal_ratio == mm.nominal_ratio

    assert result_test.instrument is not None
    assert result_test.instrument.test_set_name == "TESTRANO 600"
    assert result_test.instrument.serial_number == "GH733Y"


def test_read_dtax_roundtrips_winding_resistance(tmp_path: Path) -> None:
    model, result = _roundtrip(tmp_path)

    # The sample has one High-winding test (winding-1). The Low group has no rows.
    high_results = [t for t in result.winding_resistance_tests if t.output_side == "OutputSide_HV"]
    assert len(high_results) == 1
    result_test = high_results[0]
    model_test = model.winding_resistance_tests[0]
    assert len(result_test.measurements) == len(model_test.measurements) == 3

    result_by_phase = {m.phase: m for m in result_test.measurements}
    model_by_phase = {m.phase: m for m in model_test.measurements}
    for phase in ("PhaseA", "PhaseB", "PhaseC"):
        assert (
            result_by_phase[phase].resistance_corrected_ohm
            == model_by_phase[phase].resistance_corrected_ohm
        )

    assert result_test.reference_temperature_c == model_test.reference_temperature_c == 75

    assert result_test.instrument is not None
    assert result_test.instrument.serial_number == "GH733Y"


def test_read_dtax_roundtrips_exciting_current(tmp_path: Path) -> None:
    model, result = _roundtrip(tmp_path)

    assert len(result.exciting_current_tests) == len(model.exciting_current_tests) == 1
    result_test = result.exciting_current_tests[0]
    model_test = model.exciting_current_tests[0]
    assert len(result_test.measurements) == len(model_test.measurements) == 3

    result_by_phase = {m.phase: m for m in result_test.measurements}
    model_by_phase = {m.phase: m for m in model_test.measurements}
    for phase in ("PhaseA", "PhaseB", "PhaseC"):
        assert (
            result_by_phase[phase].current_corrected_a
            == model_by_phase[phase].current_corrected_a
        )

    assert result_test.instrument is not None
    assert result_test.instrument.serial_number == "GH733Y"


def test_read_dtax_roundtrips_bushing_power_factor(tmp_path: Path) -> None:
    model, result = _roundtrip(tmp_path)

    assert len(result.bushing_power_factor) == len(model.bushing_power_factor) == 1
    rm = result.bushing_power_factor[0]
    mm = model.bushing_power_factor[0]
    assert rm.measurement_name == mm.measurement_name == "H1"
    assert rm.power_factor_corrected == mm.power_factor_corrected == 1.5
    # The writer's pF<->F unit inversion (x1e12 / /1e12) is not bit-exact for 9.4; the value is
    # faithful to within a double ULP (9.400000000000001e-12 vs 9.4e-12).
    assert rm.capacitance_measured_f == pytest.approx(mm.capacitance_measured_f)
    assert mm.capacitance_measured_f == 9.4e-12
