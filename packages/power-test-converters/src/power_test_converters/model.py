from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PtmWinding:
    name: str
    voltage_ll_v: float | None = None
    voltage_ln_v: float | None = None
    bil_v: float | None = None
    vector_type: str = ""
    phase_shift: str = ""
    conductor_material: str = ""


@dataclass(frozen=True)
class PtmPowerRating:
    rated_power_va: float | None = None
    cooling_class: str = ""
    primary_current_a: float | None = None
    secondary_current_a: float | None = None


@dataclass(frozen=True)
class PtmTransformer:
    source_id: str
    serial_number: str = ""
    manufacturer: str = ""
    manufacturing_year: str = ""
    manufacturer_type: str = ""
    apparatus_id: str = ""
    asset_system_code: str = ""
    rated_frequency_hz: float | None = None
    number_of_phases: int | None = None
    feeder: str = ""
    category: str = ""
    status: str = ""
    tank_type: str = ""
    fluid_type: str = ""
    fluid_volume_l: float | None = None
    total_weight_kg: float | None = None
    location_id: str = ""
    global_asset_id: str = ""
    is_global_asset: bool = False
    windings: list[PtmWinding] = field(default_factory=list)
    power_ratings: list[PtmPowerRating] = field(default_factory=list)


@dataclass(frozen=True)
class PtmBushing:
    source_id: str
    parent_asset_id: str = ""
    serial_number: str = ""
    manufacturer: str = ""
    manufacturing_year: str = ""
    manufacturer_type: str = ""
    position: int | None = None
    designation: str = ""
    voltage_class: str = ""
    rated_voltage_v: float | None = None
    rated_current_a: float | None = None
    capacitance_c1_f: float | None = None
    capacitance_c2_f: float | None = None
    power_factor_c1: float | None = None
    power_factor_c2: float | None = None
    insulation_type: str = ""
    catalog_number: str = ""
    drawing_number: str = ""
    style_number: str = ""


@dataclass(frozen=True)
class PtmTapChanger:
    source_id: str
    parent_asset_id: str = ""
    serial_number: str = ""
    manufacturer: str = ""
    manufacturing_year: str = ""
    manufacturer_type: str = ""
    enabled: bool = False


@dataclass(frozen=True)
class PtmLocation:
    source_id: str
    name: str = ""
    division: str = ""
    region: str = ""
    city: str = ""
    state: str = ""
    country: str = ""


@dataclass(frozen=True)
class PtmJob:
    source_id: str
    name: str = ""
    asset_id: str = ""
    job_asset_id: str = ""
    work_order: str = ""
    tester: str = ""
    approved_by: str = ""
    execution_date: str = ""
    created: str = ""
    last_modified: str = ""


@dataclass(frozen=True)
class PtmPowerFactorMeasurement:
    source_test_id: str
    source_test_name: str
    measured_at: str
    measurement_name: str
    measurement_type: str
    transformer_winding: str
    transformer_overall_capacitance: str
    mode: str
    test_frequency_hz: float | None
    requested_voltage_v: float | None
    voltage_out_v: float | None
    current_measured_a: float | None
    current_corrected_a: float | None
    capacitance_measured_f: float | None
    watt_losses: float | None
    power_factor_measured: float | None
    power_factor_corrected: float | None
    correction_factor: float | None
    grade: str


@dataclass(frozen=True)
class PtmTurnsRatioMeasurement:
    measured_at: str
    name: str = ""
    phase: str = ""
    tap_index: int | None = None
    nominal_ratio: float | None = None
    voltage_turns_ratio: float | None = None
    ratio_deviation: float | None = None
    primary_voltage_v: float | None = None
    secondary_voltage_v: float | None = None
    primary_current_a: float | None = None
    primary_current_phase_deg: float | None = None
    secondary_voltage_phase_deg: float | None = None
    assessment: str = ""


@dataclass(frozen=True)
class PtmTurnsRatioTest:
    source_test_id: str
    name: str = ""
    execution_date: str = ""
    test_voltage_v: float | None = None
    test_frequency_hz: float | None = None
    measurements: list[PtmTurnsRatioMeasurement] = field(default_factory=list)


@dataclass(frozen=True)
class PtmWindingResistanceMeasurement:
    measured_at: str
    name: str = ""
    phase: str = ""
    tap_index: int | None = None
    resistance_measured_ohm: float | None = None
    resistance_corrected_ohm: float | None = None
    resistance_deviation: float | None = None
    current_a: float | None = None
    voltage_v: float | None = None
    corrected_voltage_v: float | None = None
    assessment: str = ""


@dataclass(frozen=True)
class PtmWindingResistanceTest:
    source_test_id: str
    name: str = ""
    execution_date: str = ""
    output_side: str = ""
    test_current_a: float | None = None
    correction_factor: float | None = None
    temperature_correction_active: bool = False
    winding_material: str = ""
    measured_temperature_c: float | None = None
    reference_temperature_c: float | None = None
    measurements: list[PtmWindingResistanceMeasurement] = field(default_factory=list)


@dataclass(frozen=True)
class PtmExcitingCurrentMeasurement:
    measured_at: str
    name: str = ""
    phase: str = ""
    tap_index: int | None = None
    voltage_out_v: float | None = None
    current_out_a: float | None = None
    current_corrected_a: float | None = None
    current_phase_deg: float | None = None
    watt_losses: float | None = None
    reactance_ohm: float | None = None
    resistance_ohm: float | None = None
    assessment: str = ""


@dataclass(frozen=True)
class PtmExcitingCurrentTest:
    source_test_id: str
    name: str = ""
    execution_date: str = ""
    test_voltage_v: float | None = None
    test_frequency_hz: float | None = None
    measurements: list[PtmExcitingCurrentMeasurement] = field(default_factory=list)


@dataclass(frozen=True)
class PtmModel:
    source_path: Path
    transformer: PtmTransformer
    bushings: list[PtmBushing]
    tap_changers: list[PtmTapChanger]
    location: PtmLocation | None
    job: PtmJob | None
    overall_power_factor: list[PtmPowerFactorMeasurement]
    bushing_power_factor: list[PtmPowerFactorMeasurement]
    turns_ratio_tests: list[PtmTurnsRatioTest] = field(default_factory=list)
    winding_resistance_tests: list[PtmWindingResistanceTest] = field(default_factory=list)
    exciting_current_tests: list[PtmExcitingCurrentTest] = field(default_factory=list)

    @property
    def first_test_date(self) -> str:
        measurements = self.overall_power_factor + self.bushing_power_factor
        measurements += [
            measurement
            for test in self.turns_ratio_tests
            for measurement in test.measurements
        ]
        measurements += [
            measurement
            for test in self.winding_resistance_tests
            for measurement in test.measurements
        ]
        measurements += [
            measurement
            for test in self.exciting_current_tests
            for measurement in test.measurements
        ]
        dates = sorted(m.measured_at for m in measurements if m.measured_at)
        return dates[0] if dates else ""

    @property
    def last_test_date(self) -> str:
        measurements = self.overall_power_factor + self.bushing_power_factor
        measurements += [
            measurement
            for test in self.turns_ratio_tests
            for measurement in test.measurements
        ]
        measurements += [
            measurement
            for test in self.winding_resistance_tests
            for measurement in test.measurements
        ]
        measurements += [
            measurement
            for test in self.exciting_current_tests
            for measurement in test.measurements
        ]
        dates = sorted(m.measured_at for m in measurements if m.measured_at)
        return dates[-1] if dates else ""
