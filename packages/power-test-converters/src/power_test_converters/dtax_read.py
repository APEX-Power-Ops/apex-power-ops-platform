"""DTAX-read (Chip 10c): parse a Doble DataModel-R2 (.dtax) file into a PtmModel.

The inverse of `write_dtax` — it reads the same containers the writer fills, producing the same
`PtmModel` that `read_ptm` produces, so the records-import pipeline (map -> propose -> commit)
is reused unchanged. Built incrementally per test domain; see
docs/superpowers/plans/2026-06-17 / 2026-06-19-chip10c-dtax-read.md.

Additive: this module does NOT modify the settled writer (dtax.py), model, or read_ptm.
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from power_test_converters.model import (
    PtmExcitingCurrentMeasurement,
    PtmExcitingCurrentTest,
    PtmInstrumentInfo,
    PtmModel,
    PtmPowerFactorMeasurement,
    PtmTransformer,
    PtmTurnsRatioMeasurement,
    PtmTurnsRatioTest,
    PtmWindingResistanceMeasurement,
    PtmWindingResistanceTest,
)

_NAMEPLATE = "two-winding-transformer-nameplate"
_DOUBLE_MIN = "-1.7976931348623157E+308"
_SESSION_XFMR = "./dta-sessions/dta-session/two-winding-transformer"

# Inverse of the writer's _phase_number: phase index 1/2/3 -> the model's phase label.
_PHASE_LABEL = {1: "PhaseA", 2: "PhaseB", 3: "PhaseC"}


def read_dtax(path: str | Path) -> PtmModel:
    """Parse a .dtax (Doble DataModel-R2) file into a PtmModel."""
    source = Path(path)
    root = ET.parse(source).getroot()
    if root.tag != "DataModel-R2":
        raise ValueError(f"Not a Doble DataModel-R2 file: {source}")
    instruments = _read_test_admin_instruments(root)
    return PtmModel(
        source_path=source,
        transformer=_read_transformer(root),
        bushings=[],
        tap_changers=[],
        location=None,
        job=None,
        overall_power_factor=_read_overall_power_factor(root, instruments),
        bushing_power_factor=_read_bushing_power_factor(root),
        turns_ratio_tests=_read_turns_ratio_tests(root, instruments),
        winding_resistance_tests=_read_winding_resistance_tests(root, instruments),
        exciting_current_tests=_read_exciting_current_tests(root, instruments),
    )


def _read_transformer(root: ET.Element) -> PtmTransformer:
    nameplate = root.find(_NAMEPLATE)
    attrs = nameplate.attrib if nameplate is not None else {}
    return PtmTransformer(
        source_id="",
        serial_number=attrs.get("serial-num", ""),
        manufacturer=attrs.get("mfr", ""),
        manufacturing_year=attrs.get("year-mfg", ""),
        apparatus_id=attrs.get("special-id", ""),
    )


# --------------------------------------------------------------------------- #
# Phase 2 instrument map: test-admin-data/admin-data rows -> {test-name: info} #
# --------------------------------------------------------------------------- #
def _read_test_admin_instruments(root: ET.Element) -> dict[str, PtmInstrumentInfo]:
    """Invert _patch_test_admin_data: one admin-data row per test domain carries the instrument.

    Writer mapping (see _test_admin_attrs): top_sn<-serial_number, bottom-sn<-test_set_name,
    firmware-version<-software_version, field-calibration-date<-calibration_date.
    Keyed by `test-name` (TwoWindingOverall / Bushings / ExcitingCurrent / LVTTR /
    M7WindingResistance / Demagnetization).
    """
    instruments: dict[str, PtmInstrumentInfo] = {}
    container = root.find(f"{_SESSION_XFMR}/test-admin-data")
    if container is None:
        return instruments
    for row in container.findall("admin-data"):
        test_name = row.attrib.get("test-name", "")
        if not test_name:
            continue
        instruments[test_name] = PtmInstrumentInfo(
            test_set_name=row.attrib.get("bottom-sn", ""),
            serial_number=row.attrib.get("top_sn", ""),
            software_version=row.attrib.get("firmware-version", ""),
            calibration_date=row.attrib.get("field-calibration-date", ""),
        )
    return instruments


# --------------------------------------------------------------------------- #
# Phase 2: overall power factor                                                #
# --------------------------------------------------------------------------- #
def _read_overall_power_factor(
    root: ET.Element, instruments: dict[str, PtmInstrumentInfo]
) -> list[PtmPowerFactorMeasurement]:
    """Invert _append_overall_tests / _overall_test_attrs.

    Each overall-test row -> a PtmPowerFactorMeasurement. measurement_name is reconstructed as
    "I" + the row's `insulation` (CH -> ICH, etc.). The TwoWindingOverall instrument is attached
    to every row (the writer derives that admin row from these measurements' instrument).
    """
    container = root.find(f"{_SESSION_XFMR}/overall-test-set")
    if container is None:
        return []
    instrument = instruments.get("TwoWindingOverall")
    measurements: list[PtmPowerFactorMeasurement] = []
    for row in container.findall("overall-test"):
        attrs = row.attrib
        insulation = attrs.get("insulation", "")
        measurements.append(
            PtmPowerFactorMeasurement(
                source_test_id="",
                source_test_name="",
                measured_at=_read_datetime(attrs.get("date-tested-utc", "")),
                measurement_name=f"I{insulation}" if insulation else "",
                measurement_type="",
                transformer_winding="",
                transformer_overall_capacitance="",
                mode="",
                test_frequency_hz=None,
                requested_voltage_v=_kv_to_v(_num(attrs.get("requested-test-kV"))),
                voltage_out_v=_kv_to_v(_num(attrs.get("test-kV"))),
                current_measured_a=_ma_to_a(_num(attrs.get("mA"))),
                current_corrected_a=None,
                capacitance_measured_f=_pf_to_farad(_num(attrs.get("measured-cap"))),
                watt_losses=_num(attrs.get("watts")),
                power_factor_measured=_num(attrs.get("pfm")),
                power_factor_corrected=_num(attrs.get("pfc")),
                correction_factor=_num(attrs.get("correction-factor")),
                grade="",
                instrument=instrument,
            )
        )
    return measurements


# --------------------------------------------------------------------------- #
# Phase 3: turns ratio (lvttratio)                                             #
# --------------------------------------------------------------------------- #
def _read_turns_ratio_tests(
    root: ET.Element, instruments: dict[str, PtmInstrumentInfo]
) -> list[PtmTurnsRatioTest]:
    """Invert _patch_lv_ttr_tests: one PtmTurnsRatioTest per lvttratio-test.

    ratio-test-fields carries per-phase ratio-N / deviation-N / angle-N + benchmark-ratio
    (nominal) + requested-test-kV (test voltage). instrument = LVTTR.
    """
    container = root.find(f"{_SESSION_XFMR}/lvttratio-test-set")
    if container is None:
        return []
    instrument = instruments.get("LVTTR")
    tests: list[PtmTurnsRatioTest] = []
    for index, test_el in enumerate(container.findall("lvttratio-test"), start=1):
        fields = test_el.find("ratio-test-fields")
        if fields is None:
            continue
        attrs = fields.attrib
        measured_at = _read_datetime(attrs.get("date-tested-utc", ""))
        nominal = _num(attrs.get("benchmark-ratio"))
        measurements: list[PtmTurnsRatioMeasurement] = []
        for phase_number in (1, 2, 3):
            ratio = _num(attrs.get(f"ratio-{phase_number}"))
            if ratio is None:
                continue
            measurements.append(
                PtmTurnsRatioMeasurement(
                    measured_at=measured_at,
                    name="",
                    phase=_PHASE_LABEL[phase_number],
                    nominal_ratio=nominal,
                    voltage_turns_ratio=ratio,
                    ratio_deviation=_num(attrs.get(f"deviation-{phase_number}")),
                    secondary_voltage_phase_deg=_num(attrs.get(f"angle-{phase_number}")),
                )
            )
        tests.append(
            PtmTurnsRatioTest(
                source_test_id=str(index),
                name="",
                execution_date=measured_at,
                test_voltage_v=_kv_to_v(_num(attrs.get("requested-test-kV"))),
                instrument=instrument,
                measurements=measurements,
            )
        )
    return tests


# --------------------------------------------------------------------------- #
# Phase 4: winding resistance                                                  #
# --------------------------------------------------------------------------- #
def _read_winding_resistance_tests(
    root: ET.Element, instruments: dict[str, PtmInstrumentInfo]
) -> list[PtmWindingResistanceTest]:
    """Invert _patch_winding_resistance_tests for both winding groups (High, Low)."""
    instrument = instruments.get("M7WindingResistance")
    reference_temp = _winding_reference_temperature(root)
    measured_temp = _winding_measured_temperature(root)
    material = _winding_material(root)

    tests: list[PtmWindingResistanceTest] = []
    for group_tag, output_side in (
        ("m7winding-resistance-tests-winding-1", "OutputSide_HV"),
        ("m7winding-resistance-tests-winding-2", "OutputSide_LV"),
    ):
        group = root.find(f"{_SESSION_XFMR}/{group_tag}")
        if group is None:
            continue
        test_set = group.find("m7winding-resistance-test-set")
        if test_set is None:
            continue
        for source_index, test_el in enumerate(
            test_set.findall("m7winding-resistance-test"), start=1
        ):
            fields = test_el.find("winding-resistance-fields")
            if fields is None:
                continue
            attrs = fields.attrib
            measured_at = _read_datetime(attrs.get("date-tested-utc", ""))
            measurements: list[PtmWindingResistanceMeasurement] = []
            for phase_number in (1, 2, 3):
                corrected = _num(attrs.get(f"corrected-resistance{phase_number}"))
                calculated = _num(attrs.get(f"calculated-resistance{phase_number}"))
                current = _num(attrs.get(f"actual-amps{phase_number}"))
                if corrected is None and calculated is None and current is None:
                    continue
                measurements.append(
                    PtmWindingResistanceMeasurement(
                        measured_at=measured_at,
                        name="",
                        phase=_PHASE_LABEL[phase_number],
                        resistance_measured_ohm=calculated,
                        resistance_corrected_ohm=corrected,
                        current_a=current,
                    )
                )
            tests.append(
                PtmWindingResistanceTest(
                    source_test_id=f"{group_tag}-{source_index}",
                    name="",
                    execution_date=measured_at,
                    output_side=output_side,
                    correction_factor=_num(attrs.get("corr-factor1")),
                    winding_material=material,
                    measured_temperature_c=measured_temp,
                    reference_temperature_c=reference_temp,
                    instrument=instrument,
                    measurements=measurements,
                )
            )
    return tests


def _winding_reference_temperature(root: ET.Element) -> float | None:
    props = root.find(f"{_NAMEPLATE}/winding-properties")
    return _num(props.attrib.get("temperature-rise")) if props is not None else None


def _winding_measured_temperature(root: ET.Element) -> float | None:
    conditions = root.find(f"{_SESSION_XFMR}/test-conditions")
    return _num(conditions.attrib.get("internal-temp")) if conditions is not None else None


def _winding_material(root: ET.Element) -> str:
    props = root.find(f"{_NAMEPLATE}/winding-properties")
    return props.attrib.get("winding-material", "") if props is not None else ""


# --------------------------------------------------------------------------- #
# Phase 5: exciting current                                                    #
# --------------------------------------------------------------------------- #
def _read_exciting_current_tests(
    root: ET.Element, instruments: dict[str, PtmInstrumentInfo]
) -> list[PtmExcitingCurrentTest]:
    """Invert _patch_exciting_current_tests: one PtmExcitingCurrentTest per exciting-current-test."""
    container = root.find(f"{_SESSION_XFMR}/exciting-current-test-set")
    if container is None:
        return []
    instrument = instruments.get("ExcitingCurrent")
    tests: list[PtmExcitingCurrentTest] = []
    for source_index, test_el in enumerate(
        container.findall("exciting-current-test"), start=1
    ):
        fields = test_el.find("exciting-current-fields")
        if fields is None:
            continue
        attrs = fields.attrib
        measured_at = _read_datetime(attrs.get("date-tested-utc", ""))
        measurements: list[PtmExcitingCurrentMeasurement] = []
        for phase_number in (1, 2, 3):
            milliamps = _num(attrs.get(f"mA-{phase_number}"))
            if milliamps is None:
                continue
            measurements.append(
                PtmExcitingCurrentMeasurement(
                    measured_at=measured_at,
                    name="",
                    phase=_PHASE_LABEL[phase_number],
                    current_corrected_a=_ma_to_a(milliamps),
                    watt_losses=_num(attrs.get(f"watts-{phase_number}")),
                    voltage_out_v=_kv_to_v(_num(attrs.get(f"actualkv-{phase_number}"))),
                )
            )
        tests.append(
            PtmExcitingCurrentTest(
                source_test_id=str(source_index),
                name="",
                execution_date=measured_at,
                test_voltage_v=_kv_to_v(_num(attrs.get("test-kV"))),
                instrument=instrument,
                measurements=measurements,
            )
        )
    return tests


# --------------------------------------------------------------------------- #
# Phase 6: bushing power factor                                                #
# --------------------------------------------------------------------------- #
def _read_bushing_power_factor(root: ET.Element) -> list[PtmPowerFactorMeasurement]:
    """Invert _patch_bushing_tests: m7-bushing-test/bushing-test-results-set/bushing-test-results.

    measurement_name is resolved from the parent m7-bushing-test @bushing-id back to the bushing's
    `designation` via the nameplate bushing-nameplates (id) -> bushing-designations (id ->
    designation). If resolution is ambiguous it is left "" (still e2e-irrelevant; bushing-PF rows
    do not map to a datasheet target).
    """
    container = root.find(f"{_SESSION_XFMR}/m7-bushing-test-set")
    if container is None:
        return []
    designation_by_id = _bushing_designation_by_id(root)
    measurements: list[PtmPowerFactorMeasurement] = []
    for test_el in container.findall("m7-bushing-test"):
        bushing_id = test_el.attrib.get("bushing-id", "")
        designation = designation_by_id.get(bushing_id, "")
        results = test_el.find("bushing-test-results-set")
        if results is None:
            continue
        for row in results.findall("bushing-test-results"):
            attrs = row.attrib
            measurements.append(
                PtmPowerFactorMeasurement(
                    source_test_id="",
                    source_test_name="",
                    measured_at=_read_datetime(attrs.get("date-tested-utc", "")),
                    measurement_name=designation,
                    measurement_type="",
                    transformer_winding="",
                    transformer_overall_capacitance="",
                    mode="",
                    test_frequency_hz=None,
                    requested_voltage_v=_kv_to_v(_num(attrs.get("requested-test-kV"))),
                    voltage_out_v=_kv_to_v(_num(attrs.get("test-kV"))),
                    current_measured_a=_ma_to_a(_num(attrs.get("mA"))),
                    current_corrected_a=None,
                    capacitance_measured_f=_pf_to_farad(_num(attrs.get("measured-cap"))),
                    watt_losses=_num(attrs.get("watts")),
                    power_factor_measured=_num(attrs.get("pfm")),
                    power_factor_corrected=_num(attrs.get("pfc")),
                    correction_factor=_num(attrs.get("correction-factor")),
                    grade="",
                    instrument=None,
                )
            )
    return measurements


def _bushing_designation_by_id(root: ET.Element) -> dict[str, str]:
    designations = root.find(f"{_SESSION_XFMR}/bushing-designations")
    mapping: dict[str, str] = {}
    if designations is None:
        return mapping
    for bushing in designations.findall("bushing"):
        bushing_id = bushing.attrib.get("id", "")
        designation = bushing.attrib.get("designation", "")
        if bushing_id:
            mapping[bushing_id] = designation
    return mapping


# --------------------------------------------------------------------------- #
# Parse helpers (inverse of the writer's number / unit / datetime formatting)  #
# --------------------------------------------------------------------------- #
def _num(value: str | None) -> float | None:
    """Parse a numeric attribute. "" and the Double.MinValue sentinel both mean None."""
    if value is None:
        return None
    text = value.strip()
    if text == "" or text == _DOUBLE_MIN:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _kv_to_v(value: float | None) -> float | None:
    return value * 1000 if value is not None else None


def _ma_to_a(value: float | None) -> float | None:
    return value / 1000 if value is not None else None


def _pf_to_farad(value: float | None) -> float | None:
    return value / 1_000_000_000_000 if value is not None else None


def _read_datetime(value: str) -> str:
    """The writer emits zero-dates as 0001-01-01 00:00:00; surface those as "" (no date)."""
    text = (value or "").strip()
    if not text or text.startswith("0001-01-01"):
        return ""
    return text
