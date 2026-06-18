from pathlib import Path

from power_test_converters.model import (
    PtmModel, PtmTransformer, PtmInstrumentInfo,
    PtmTurnsRatioTest, PtmTurnsRatioMeasurement,
    PtmWindingResistanceTest, PtmWindingResistanceMeasurement,
    PtmExcitingCurrentTest, PtmExcitingCurrentMeasurement,
    PtmPowerFactorMeasurement,
)

from records_import.mappings.ptm_transformer import map_ptm_transformer

INST = PtmInstrumentInfo(test_set_name="TESTRANO 600", serial_number="GH733Y")


def _model():
    ttr = PtmTurnsRatioTest(source_test_id="t1", instrument=INST, measurements=[
        PtmTurnsRatioMeasurement(measured_at="2026-06-01T10:00:00", name="H-X", phase="H-X",
                                 nominal_ratio=10.0, voltage_turns_ratio=10.02, ratio_deviation=0.2),
    ])
    wr = PtmWindingResistanceTest(source_test_id="w1", instrument=INST, reference_temperature_c=75.0, measurements=[
        PtmWindingResistanceMeasurement(measured_at="2026-06-01T10:05:00", name="H", phase="H",
                                        resistance_measured_ohm=0.500, resistance_corrected_ohm=0.512),
    ])
    ex = PtmExcitingCurrentTest(source_test_id="e1", instrument=INST, measurements=[
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:00", phase="A", current_corrected_a=0.011),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:01", phase="B", current_corrected_a=0.009),
        PtmExcitingCurrentMeasurement(measured_at="2026-06-01T10:10:02", phase="C", current_corrected_a=0.012),
    ])
    pf = PtmPowerFactorMeasurement(
        source_test_id="p1", source_test_name="Overall", measured_at="2026-06-01T10:15:00",
        measurement_name="ICH", measurement_type="overall", transformer_winding="",
        transformer_overall_capacitance="", mode="", test_frequency_hz=60.0,
        requested_voltage_v=10000.0, voltage_out_v=10000.0, current_measured_a=0.0,
        current_corrected_a=0.0, capacitance_measured_f=1.1e-9, watt_losses=0.0,
        power_factor_measured=0.31, power_factor_corrected=0.30, correction_factor=1.0,
        grade="Good", instrument=INST)
    return PtmModel(source_path=Path("x.ptm"), transformer=PtmTransformer(source_id="s"), bushings=[],
                    tap_changers=[], location=None, job=None, overall_power_factor=[pf], bushing_power_factor=[],
                    turns_ratio_tests=[ttr], winding_resistance_tests=[wr], exciting_current_tests=[ex],
                    demagnetization_tests=[])


def _by_key(rows):
    return {r.field_key: r for r in rows}


def test_turns_ratio_maps_to_h_x_row():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["turns_ratio.h_x.measured_ratio"].value_numeric == 10.02
    assert rows["turns_ratio.h_x.deviation_pct"].value_numeric == 0.2
    assert rows["turns_ratio.h_x.nominal_ratio"].value_numeric == 10.0


def test_winding_resistance_uses_corrected_and_temp():
    rows = _by_key(map_ptm_transformer(_model()))
    r = rows["winding_resistance.h.ohms"]
    assert r.value_numeric == 0.512 and r.unit == "ohm"
    assert "measured=0.5" in (r.notes or "")
    assert rows["winding_resistance.h.temp"].value_numeric == 75.0


def test_excitation_phase_fields():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["excitation_current.phase_a"].value_numeric == 0.011
    assert rows["excitation_current.phase_b"].value_numeric == 0.009
    assert rows["excitation_current.phase_c"].value_numeric == 0.012


def test_power_factor_ich_maps_to_ch_row():
    rows = _by_key(map_ptm_transformer(_model()))
    assert rows["power_factor.ch.pf_pct"].value_numeric == 0.30
    assert rows["power_factor.ch.capacitance"].value_numeric == 1.1e-9


def test_every_row_carries_provenance():
    rows = map_ptm_transformer(_model())
    assert rows, "expected proposed values"
    for r in rows:
        assert r.origin_device and "GH733Y" in r.origin_device
        assert r.measured_at and r.value_kind == "numeric"
        assert r.field_key and r.test_group


def test_unknown_rows_are_skipped_not_invented():
    # a measurement with an unmapped winding-pair must not produce a phantom row
    m = _model()
    m.turns_ratio_tests[0].measurements.append(
        PtmTurnsRatioMeasurement(measured_at="2026-06-01T10:00:01", name="Z-Z", phase="Z-Z",
                                 nominal_ratio=1.0, voltage_turns_ratio=1.0))
    keys = {r.field_key for r in map_ptm_transformer(m)}
    assert not any(k.startswith("turns_ratio.z_z") for k in keys)
