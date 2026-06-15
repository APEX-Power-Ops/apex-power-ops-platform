from __future__ import annotations

import math
import re
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from power_test_converters.model import (
    PtmBushing,
    PtmJob,
    PtmLocation,
    PtmModel,
    PtmExcitingCurrentMeasurement,
    PtmExcitingCurrentTest,
    PtmPowerFactorMeasurement,
    PtmPowerRating,
    PtmTapChanger,
    PtmTransformer,
    PtmTurnsRatioMeasurement,
    PtmTurnsRatioTest,
    PtmWindingResistanceMeasurement,
    PtmWindingResistanceTest,
    PtmWinding,
)

_EMPTY_SENTINELS = {"", "NaN"}
_BUSHING_DESIGNATION_RE = re.compile(r"(?:^|[-_\s])([HXY]\d+|H0|X0|Y0)$", re.IGNORECASE)


def read_ptm(path: str | Path) -> PtmModel:
    source_path = Path(path)
    xml_docs = _read_xml_docs(source_path)
    transformer_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "Transformer"
    ]
    if not transformer_docs:
        raise ValueError(f"No Transformer asset was found in PTM package: {source_path}")

    test_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "TanDeltaTest"
    ]
    turns_ratio_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "TTSTTRTest"
    ]
    winding_resistance_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "TTSWindingResistanceTest"
    ]
    exciting_current_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "TTSHVExcitingCurrentTest"
    ]
    job_docs = [
        (entry_name, root)
        for entry_name, root in xml_docs.items()
        if _local_name(root.tag) == "Job"
    ]

    selected_root = _select_transformer(transformer_docs, test_docs, job_docs)
    transformer = _parse_transformer(selected_root)
    location = _parse_matching_location(xml_docs, transformer.location_id)
    job = _parse_matching_job(job_docs, transformer)
    bushing_ids = set(_child_texts(_child(selected_root, "Bushings"), "BushingId"))
    bushings = sorted(
        (
            _parse_bushing(root)
            for root in xml_docs.values()
            if _local_name(root.tag) == "Bushing"
            and (
                _export_id(root) in bushing_ids
                or _text(root, "ParentAssetId") == transformer.source_id
            )
        ),
        key=_bushing_sort_key,
    )
    tap_changers = sorted(
        (
            _parse_tap_changer(root)
            for root in xml_docs.values()
            if _local_name(root.tag) == "tTapChanger"
            and _text(root, "ParentAssetId") == transformer.source_id
        ),
        key=lambda tap: (not tap.enabled, tap.source_id),
    )

    overall: list[PtmPowerFactorMeasurement] = []
    bushing_pf: list[PtmPowerFactorMeasurement] = []
    matching_asset_ids = {transformer.source_id}
    if transformer.global_asset_id:
        matching_asset_ids.add(transformer.global_asset_id)

    for _entry_name, test_root in test_docs:
        if _text(test_root, "AssetId") not in matching_asset_ids:
            continue
        for measurement in _parse_tan_delta_measurements(test_root):
            if _is_overall_power_factor(measurement):
                overall.append(measurement)
            elif _is_bushing_power_factor(measurement):
                bushing_pf.append(measurement)

    turns_ratio_tests = [
        _parse_turns_ratio_test(root)
        for _entry_name, root in turns_ratio_docs
        if _text(root, "AssetId") in matching_asset_ids
    ]
    winding_resistance_tests = [
        _parse_winding_resistance_test(root)
        for _entry_name, root in winding_resistance_docs
        if _text(root, "AssetId") in matching_asset_ids
    ]
    exciting_current_tests = [
        _parse_exciting_current_test(root)
        for _entry_name, root in exciting_current_docs
        if _text(root, "AssetId") in matching_asset_ids
    ]

    return PtmModel(
        source_path=source_path,
        transformer=transformer,
        bushings=bushings,
        tap_changers=tap_changers,
        location=location,
        job=job,
        overall_power_factor=overall,
        bushing_power_factor=bushing_pf,
        turns_ratio_tests=turns_ratio_tests,
        winding_resistance_tests=winding_resistance_tests,
        exciting_current_tests=exciting_current_tests,
    )


def _read_xml_docs(path: Path) -> dict[str, ET.Element]:
    if not path.exists():
        raise FileNotFoundError(path)
    docs: dict[str, ET.Element] = {}
    with zipfile.ZipFile(path) as package:
        for info in package.infolist():
            if not info.filename.lower().endswith(".xml"):
                continue
            docs[info.filename] = ET.fromstring(package.read(info.filename))
    return docs


def _select_transformer(
    transformer_docs: list[tuple[str, ET.Element]],
    test_docs: list[tuple[str, ET.Element]],
    job_docs: list[tuple[str, ET.Element]],
) -> ET.Element:
    test_asset_counts = Counter(_text(root, "AssetId") for _name, root in test_docs)
    job_asset_ids = {_text(root, "JobAssetId") for _name, root in job_docs}

    def score(root: ET.Element) -> tuple[int, int, int, str]:
        source_id = _export_id(root)
        global_id = _text(root, "GlobalAssetId")
        direct_tests = test_asset_counts[source_id]
        inherited_tests = test_asset_counts[global_id] if global_id else 0
        job_match = 1 if source_id in job_asset_ids else 0
        local_asset = 1 if not _bool_text(_text(root, "IsGlobalAsset")) else 0
        return (direct_tests + inherited_tests, job_match, local_asset, source_id)

    return max((root for _name, root in transformer_docs), key=score)


def _parse_transformer(root: ET.Element) -> PtmTransformer:
    return PtmTransformer(
        source_id=_export_id(root),
        serial_number=_text(root, "SerialNumber"),
        manufacturer=_text(root, "Manufacturer"),
        manufacturing_year=_text(root, "ManufacturingYear"),
        manufacturer_type=_text(root, "ManufacturerType"),
        apparatus_id=_text(root, "ApparatusId"),
        asset_system_code=_text(root, "AssetSystemCode"),
        rated_frequency_hz=_float_text(_text(root, "RatedFrequency")),
        number_of_phases=_int_text(_text(root, "NumberOfPhases")),
        feeder=_text(root, "Feeder"),
        category=_text(root, "Category"),
        status=_text(root, "Status"),
        tank_type=_text(root, "TankType"),
        fluid_type=_text(root, "FluidType"),
        fluid_volume_l=_float_text(_text(root, "FluidVolume")),
        total_weight_kg=_float_text(_text(root, "TotalWeight")),
        location_id=_text(root, "LocationId"),
        global_asset_id=_text(root, "GlobalAssetId"),
        is_global_asset=_bool_text(_text(root, "IsGlobalAsset")),
        windings=_parse_windings(_child(root, "Windings")),
        power_ratings=_parse_power_ratings(_child(root, "PowerRatings")),
    )


def _parse_windings(root: ET.Element | None) -> list[PtmWinding]:
    if root is None:
        return []
    windings: list[PtmWinding] = []
    for item in _children(root, "Winding"):
        windings.append(
            PtmWinding(
                name=_text(item, "Winding"),
                voltage_ll_v=_float_text(_text(item, "VoltageLL")),
                voltage_ln_v=_float_text(_text(item, "VoltageLN")),
                bil_v=_float_text(_text(item, "InsulationLevelLL")),
                vector_type=_text(item, "VectorType"),
                phase_shift=_text(item, "PhaseShift"),
                conductor_material=_text(item, "ConductorMaterial"),
            )
        )
    return windings


def _parse_power_ratings(root: ET.Element | None) -> list[PtmPowerRating]:
    if root is None:
        return []
    ratings: list[PtmPowerRating] = []
    for item in _children(root, "PowerRating"):
        ratings.append(
            PtmPowerRating(
                rated_power_va=_float_text(_text(item, "RatedPower")),
                cooling_class=_text(item, "CoolingClass"),
                primary_current_a=_float_text(_text(item, "RatedCurrentPrimary")),
                secondary_current_a=_float_text(_text(item, "RatedCurrentSecondary")),
            )
        )
    return ratings


def _parse_bushing(root: ET.Element) -> PtmBushing:
    serial = _text(root, "SerialNumber")
    designation = _designation_from_serial(serial) or _designation_from_position(
        _int_text(_text(root, "Position"))
    )
    return PtmBushing(
        source_id=_export_id(root),
        parent_asset_id=_text(root, "ParentAssetId"),
        serial_number=serial,
        manufacturer=_text(root, "Manufacturer"),
        manufacturing_year=_text(root, "ManufacturingYear"),
        manufacturer_type=_text(root, "ManufacturerType"),
        position=_int_text(_text(root, "Position")),
        designation=designation,
        voltage_class=_voltage_class_from_designation(designation),
        rated_voltage_v=_float_text(_text(root, "RatedVoltage")),
        rated_current_a=_float_text(_text(root, "RatedCurrent")),
        capacitance_c1_f=_float_text(_text(root, "Cap1")),
        capacitance_c2_f=_float_text(_text(root, "Cap2")),
        power_factor_c1=_float_text(_text(root, "PF1")),
        power_factor_c2=_float_text(_text(root, "PF2")),
        insulation_type=_text(root, "InsulationType"),
        catalog_number=_text(root, "CatalogNumber"),
        drawing_number=_text(root, "DrawingNumber"),
        style_number=_text(root, "StyleNumber"),
    )


def _parse_tap_changer(root: ET.Element) -> PtmTapChanger:
    return PtmTapChanger(
        source_id=_export_id(root),
        parent_asset_id=_text(root, "ParentAssetId"),
        serial_number=_text(root, "SerialNumber"),
        manufacturer=_text(root, "Manufacturer"),
        manufacturing_year=_text(root, "ManufacturingYear"),
        manufacturer_type=_text(root, "ManufacturerType"),
        enabled=_bool_text(_text(root, "IsTapChangerEnabled")),
    )


def _parse_matching_location(
    xml_docs: dict[str, ET.Element], location_id: str
) -> PtmLocation | None:
    for root in xml_docs.values():
        if _local_name(root.tag) == "tSubstation" and _export_id(root) == location_id:
            return PtmLocation(
                source_id=_export_id(root),
                name=_text(root, "Name"),
                division=_text(root, "Division"),
                region=_text(root, "Region"),
                city=_text(root, "City"),
                state=_text(root, "State"),
                country=_text(root, "Country"),
            )
    return None


def _parse_matching_job(
    job_docs: list[tuple[str, ET.Element]], transformer: PtmTransformer
) -> PtmJob | None:
    matching_ids = {transformer.source_id}
    if transformer.global_asset_id:
        matching_ids.add(transformer.global_asset_id)
    for _entry_name, root in job_docs:
        if _text(root, "JobAssetId") in matching_ids or _text(root, "AssetId") in matching_ids:
            return PtmJob(
                source_id=_export_id(root),
                name=_text(root, "Name"),
                asset_id=_text(root, "AssetId"),
                job_asset_id=_text(root, "JobAssetId"),
                work_order=_text(root, "WorkOrder"),
                tester=_text(root, "Tester"),
                approved_by=_text(root, "ApprovedBy"),
                execution_date=_text(root, "ExecutionDate"),
                created=_text(root, "Created"),
                last_modified=_text(root, "LastModified"),
            )
    return None


def _parse_tan_delta_measurements(root: ET.Element) -> list[PtmPowerFactorMeasurement]:
    measurements: list[PtmPowerFactorMeasurement] = []
    test_id = _text(root, "TestId")
    test_name = _text(root, "Name")
    test_grade = _text(root, "Grade")
    global_correction_factor = _float_text(_text(root, "CorrectionFactor"))

    measurements_root = _child(root, "Measurements")
    if measurements_root is None:
        return []

    for measurement in _children(measurements_root, "Measurement"):
        point = _first_measurement_point(measurement)
        if point is None:
            continue
        correction_factor = _float_text(_text(measurement, "CorrectionFactor"))
        measurements.append(
            PtmPowerFactorMeasurement(
                source_test_id=test_id,
                source_test_name=test_name,
                measured_at=_text(measurement, "MeasuredDate") or _text(root, "ExecutionDate"),
                measurement_name=_text(measurement, "Name"),
                measurement_type=_text(measurement, "MeasurementType"),
                transformer_winding=_text(measurement, "TransformerWinding"),
                transformer_overall_capacitance=_text(
                    measurement, "TransformerOverallCapacitance"
                ),
                mode=_text(measurement, "Mode"),
                test_frequency_hz=_float_text(_text(point, "TestFrequency")),
                requested_voltage_v=_float_text(_text(point, "TestVoltage")),
                voltage_out_v=_float_text(_text(point, "VoltageOut")),
                current_measured_a=_float_text(_text(point, "CurrentMeasured")),
                current_corrected_a=_float_text(_text(point, "CurrentCorrected")),
                capacitance_measured_f=_float_text(_text(point, "CapacitanceMeasured")),
                watt_losses=_float_text(_text(point, "WattLosses")),
                power_factor_measured=_float_text(_text(point, "PowerFactorMeasured")),
                power_factor_corrected=_float_text(_text(point, "PowerFactorCorrected")),
                correction_factor=correction_factor or global_correction_factor,
                grade=test_grade,
            )
        )
    return measurements


def _parse_turns_ratio_test(root: ET.Element) -> PtmTurnsRatioTest:
    settings = _child(root, "Settings")
    execution_date = _text(root, "ExecutionDate")
    measurements = [
        PtmTurnsRatioMeasurement(
            measured_at=_text(item, "MeasuredDate") or execution_date,
            name=_text(item, "Name"),
            phase=_text(item, "Phase"),
            tap_index=_int_text(_text(item, "TapIndex")),
            nominal_ratio=_float_text(_text(item, "NominalRatioVTR")),
            voltage_turns_ratio=_float_text(_text(item, "VoltageTurnsRatio")),
            ratio_deviation=_float_text(_text(item, "RatioDeviation")),
            primary_voltage_v=_float_text(_text(item, "VPrim")),
            secondary_voltage_v=_float_text(_text(item, "VSec")),
            primary_current_a=_float_text(_text(item, "IPrim")),
            primary_current_phase_deg=_float_text(_text(item, "IPhase")),
            secondary_voltage_phase_deg=_float_text(_text(item, "VPhase")),
            assessment=_text(item, "Assessment"),
        )
        for item in _children(_child(root, "Measurements"), "tTTSTTRMeasurement")
    ]
    return PtmTurnsRatioTest(
        source_test_id=_text(root, "TestId") or _export_id(root),
        name=_text(root, "Name"),
        execution_date=execution_date,
        test_voltage_v=_float_text(_text(settings, "TestVoltage")) if settings is not None else None,
        test_frequency_hz=_float_text(_text(settings, "TestFrequency")) if settings is not None else None,
        measurements=measurements,
    )


def _parse_winding_resistance_test(root: ET.Element) -> PtmWindingResistanceTest:
    settings = _child(root, "Settings")
    execution_date = _text(root, "ExecutionDate")
    measurements = [
        PtmWindingResistanceMeasurement(
            measured_at=_text(item, "MeasuredDate") or execution_date,
            name=_text(item, "Name"),
            phase=_text(item, "Phase"),
            tap_index=_int_text(_text(item, "TapIndex")),
            resistance_measured_ohm=_float_text(_text(item, "ResistanceMeasured")),
            resistance_corrected_ohm=_float_text(_text(item, "ResistanceCorrected")),
            resistance_deviation=_float_text(_text(item, "ResistanceDeviation")),
            current_a=_float_text(_text(item, "IDC")),
            voltage_v=_float_text(_text(item, "VDC")),
            corrected_voltage_v=_float_text(_text(item, "VDCCorrected")),
            assessment=_text(item, "Assessment"),
        )
        for item in _children(
            _child(root, "Measurements"), "tTTSWindingResistanceMeasurement"
        )
    ]
    return PtmWindingResistanceTest(
        source_test_id=_text(root, "TestId") or _export_id(root),
        name=_text(root, "Name"),
        execution_date=execution_date,
        output_side=_text(settings, "OutputSide") if settings is not None else "",
        test_current_a=_float_text(_text(settings, "TestCurrent")) if settings is not None else None,
        correction_factor=_float_text(_text(settings, "CorrectionFactor")) if settings is not None else None,
        temperature_correction_active=(
            _bool_text(_text(settings, "TemperatureCorrectionActive"))
            if settings is not None
            else False
        ),
        winding_material=_text(settings, "WindingMaterial") if settings is not None else "",
        measured_temperature_c=_float_text(_text(settings, "MeasTemp")) if settings is not None else None,
        reference_temperature_c=_float_text(_text(settings, "RefTemp")) if settings is not None else None,
        measurements=measurements,
    )


def _parse_exciting_current_test(root: ET.Element) -> PtmExcitingCurrentTest:
    settings = _child(root, "Settings")
    execution_date = _text(root, "ExecutionDate")
    measurements = [
        PtmExcitingCurrentMeasurement(
            measured_at=_text(item, "MeasuredDate") or execution_date,
            name=_text(item, "Name"),
            phase=_text(item, "Phase"),
            tap_index=_int_text(_text(item, "TapIndex")),
            voltage_out_v=_float_text(_text(item, "VOut")),
            current_out_a=_float_text(_text(item, "IOut")),
            current_corrected_a=_float_text(_text(item, "IOutCorrected")),
            current_phase_deg=_float_text(_text(item, "IPhase")),
            watt_losses=_float_text(_text(item, "WattLosses")),
            reactance_ohm=_float_text(_text(item, "Reactance")),
            resistance_ohm=_float_text(_text(item, "ZReal")),
            assessment=_text(item, "Assessment"),
        )
        for item in _children(
            _child(root, "Measurements"), "tTTSHVExcitingCurrentMeasurement"
        )
    ]
    return PtmExcitingCurrentTest(
        source_test_id=_text(root, "TestId") or _export_id(root),
        name=_text(root, "Name"),
        execution_date=execution_date,
        test_voltage_v=_float_text(_text(settings, "TestVoltage")) if settings is not None else None,
        test_frequency_hz=_float_text(_text(settings, "TestFrequency")) if settings is not None else None,
        measurements=measurements,
    )


def _first_measurement_point(measurement: ET.Element) -> ET.Element | None:
    points = _child(measurement, "MeasurementPoints")
    if points is None:
        return None
    point_children = _children(points, "MeasurementPoint")
    if not point_children:
        return None
    for point in point_children:
        frequency = _float_text(_text(point, "TestFrequency"))
        if frequency == 60:
            return point
    return point_children[0]


def _is_overall_power_factor(measurement: PtmPowerFactorMeasurement) -> bool:
    return (
        measurement.measurement_type == "Measurement"
        and measurement.transformer_overall_capacitance
        and measurement.transformer_overall_capacitance != "NullValue"
        and measurement.measurement_name.upper() not in {"NONE"}
    )


def _is_bushing_power_factor(measurement: PtmPowerFactorMeasurement) -> bool:
    return (
        measurement.measurement_type == "Measurement"
        and measurement.transformer_overall_capacitance == "NullValue"
        and bool(_voltage_class_from_designation(measurement.measurement_name))
    )


def _designation_from_serial(serial: str) -> str:
    match = _BUSHING_DESIGNATION_RE.search(serial or "")
    return match.group(1).upper() if match else ""


def _designation_from_position(position: int | None) -> str:
    if position is None:
        return ""
    default_positions = {
        0: "H1",
        1: "H2",
        2: "H3",
        4: "X1",
        5: "X2",
        6: "X3",
        7: "X0",
    }
    return default_positions.get(position, "")


def _voltage_class_from_designation(designation: str) -> str:
    upper = designation.upper()
    if upper.startswith("H"):
        return "High"
    if upper.startswith("X"):
        return "Low"
    if upper.startswith("Y"):
        return "Tertiary"
    return ""


def _bushing_sort_key(bushing: PtmBushing) -> tuple[int, int, str]:
    designation = bushing.designation.upper()
    prefix_order = {"H": 0, "X": 1, "Y": 2}
    prefix = designation[:1]
    number = _int_text(designation[1:]) if len(designation) > 1 else None
    return (
        prefix_order.get(prefix, 9),
        number if number is not None else (bushing.position if bushing.position is not None else 99),
        bushing.source_id,
    )


def _child(root: ET.Element | None, name: str) -> ET.Element | None:
    if root is None:
        return None
    for child in root:
        if _local_name(child.tag) == name:
            return child
    return None


def _children(root: ET.Element | None, name: str) -> list[ET.Element]:
    if root is None:
        return []
    return [child for child in root if _local_name(child.tag) == name]


def _child_texts(root: ET.Element | None, name: str) -> list[str]:
    return [_clean_text(child.text) for child in _children(root, name) if _clean_text(child.text)]


def _text(root: ET.Element, name: str) -> str:
    child = _child(root, name)
    if child is None:
        return ""
    return _clean_text(child.text)


def _clean_text(value: str | None) -> str:
    if value is None:
        return ""
    text = value.strip()
    if text in _EMPTY_SENTINELS:
        return ""
    return text


def _float_text(value: str) -> float | None:
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _int_text(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _bool_text(value: str) -> bool:
    return value.strip().lower() == "true"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _export_id(root: ET.Element) -> str:
    return root.attrib.get("ExportId", "")
