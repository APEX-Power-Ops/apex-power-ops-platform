from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5
from xml.etree import ElementTree as ET

from power_test_converters.model import (
    PtmBushing,
    PtmDemagnetizationTest,
    PtmExcitingCurrentMeasurement,
    PtmInstrumentInfo,
    PtmModel,
    PtmPowerFactorMeasurement,
    PtmPowerRating,
    PtmTransformer,
    PtmTurnsRatioMeasurement,
    PtmWindingResistanceMeasurement,
    PtmWindingResistanceTest,
    PtmWinding,
)

_ZERO_DATE = "0001-01-01 00:00:00"
_ZERO_ID = "00000000-0000-0000-0000-000000000000"
_DOUBLE_MIN = "-1.7976931348623157E+308"
_DTAX_CHILDREN = [
    "admin-data",
    "test-admin-data",
    "test-conditions",
    "bushing-test-set",
    "m7-bushing-test-set",
    "exciting-current-test-set",
    "bushing-designations",
    "arresters",
    "surge-arrester-test-set",
    "hot-collar-test-set",
    "insulatingfluid-test-set",
    "diagnostic-test-set",
    "configurable-powerfactor-test-set",
    "turns-ratio-test-set",
    "winding-resistance-test-set",
    "winding-resistance-winding-detail",
    "m7winding-resistance-tests-winding-1",
    "m7winding-resistance-tests-winding-2",
    "demagnetization-test-set",
    "dfr-test-set",
    "vflr-test-set",
    "fds-test-set",
    "overall-vfpf-test-set",
    "kneepoint-test-set",
    "ezct-test-set",
    "manual-data",
    "water-content",
    "tapchangers",
    "insulating-fluid-oil-quality-set",
    "dobledc-test-set",
    "dissolved-gas",
    "turns-ratio-connections",
    "turns-ratio-nameplate",
    "configurable-contact-resistance-test-set",
    "exciting-current-connections",
    "doble-ratio-test-set",
    "doble-ratio-cap-windings",
    "doble-ratio-connections",
    "lvttratio-test-set",
    "lvttratio-connections",
    "oltc-drm-test-set",
    "oltc-drm-connections",
    "transformer-layout",
    "gas-space",
    "leakage-reactance-3phase-test-set",
    "leakage-reactance-per-phase-hi-test-set",
    "leakage-reactance-per-phase-lo-test-set",
    "leakage-reactance-single-phase-test-set",
    "overall-test-set",
]
_TEMPLATE_PATCH_CHILDREN = [
    "admin-data",
    "test-admin-data",
    "test-conditions",
    "exciting-current-test-set",
    "bushing-designations",
    "turns-ratio-test-set",
    "lvttratio-test-set",
    "lvttratio-connections",
    "m7winding-resistance-tests-winding-1",
    "m7winding-resistance-tests-winding-2",
    "demagnetization-test-set",
    "turns-ratio-connections",
    "exciting-current-connections",
    "overall-test-set",
]

_OVERALL_INSULATION = {
    "IchAndIchl": "CH_CHL",
    "Ich": "CH",
    "Ichl": "CHL_UST",
    "IclAndIclh": "CL_CHL",
    "Icl": "CL",
    "Iclh": "CHL_UST",
}

_TEST_CIRCUIT_BY_MODE = {
    "Gst": "CIRC_GND_RB",
    "GstGa": "CIRC_GAR_RB",
    "GstGb": "CIRC_GAR_RB",
    "UstA": "CIRC_UST_RB",
    "UstB": "CIRC_UST_RB",
}
_TWO_WINDING_NAMEPLATE_ATTRS = (
    "year-mfg",
    "apparatus-type",
    "mfr",
    "mfr-location",
    "serial-num",
    "special-id",
    "config",
    "class",
    "coolant",
    "tanktype",
    "weight-units",
    "phases",
    "volume-units",
    "Va-units",
    "HVWindingLine",
    "LVWindingLine",
    "oil-volume",
    "Va-0",
    "Va-1",
    "Va-2",
    "Va-3",
    "BIL",
    "weight",
    "kV-0",
    "kV-1",
)


def write_dtax(
    model: PtmModel, path: str | Path, template_path: str | Path | None = None
) -> Path:
    output_path = Path(path)
    root = build_dtax_tree(model, template_path=template_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    xml_body = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    xml_text = '<?xml version="1.0" encoding="utf-8"?>\r\n' + xml_body
    xml_text = xml_text.replace("\r\n", "\n").replace("\n", "\r\n")
    output_path.write_text(xml_text, encoding="utf-8", newline="")
    return output_path


def build_dtax_tree(
    model: PtmModel, template_path: str | Path | None = None
) -> ET.Element:
    if template_path is not None:
        return _build_from_template(model, Path(template_path))

    root = ET.Element(
        "DataModel-R2",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "apparatus-note": "",
            "created-by-version": "8.3.1.0010",
            "modified-by-version": "8.3.1.0010",
            "xml-version": "83",
            "test-row-notes": "InTestRowsOnly",
        },
    )
    ET.SubElement(root, "external-system-properties")
    ET.SubElement(root, "ApparatusType")
    ET.SubElement(root, "Apparatus").text = "TwoWindingTransformer"
    root.append(_build_nameplate(model))
    root.append(_build_sessions(model))
    ET.SubElement(root, "copyright-notice")
    return root


def _build_from_template(model: PtmModel, template_path: Path) -> ET.Element:
    root = ET.parse(template_path).getroot()
    if root.tag != "DataModel-R2":
        raise ValueError(f"Template is not a Doble DataModel-R2 file: {template_path}")
    _normalize_root_attrs(root)

    _set_child_text(root, "Apparatus", "TwoWindingTransformer")
    _patch_nameplate(_ensure_child(root, "two-winding-transformer-nameplate"), model)

    sessions = _ensure_child(root, "dta-sessions")
    session = _ensure_child(sessions, "dta-session")
    _patch_session(
        session,
        model,
        create_full_child_set=False,
        preserve_overall_rows=True,
        preserve_template_metadata=True,
    )
    return root


def _normalize_root_attrs(root: ET.Element) -> None:
    created_by_version = root.attrib.get("created-by-version", "8.3.1.0010")
    ordered_attrs = {
        "xmlns:xsi": root.attrib.get(
            "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance"
        ),
        "xmlns:xsd": root.attrib.get(
            "xmlns:xsd", "http://www.w3.org/2001/XMLSchema"
        ),
        "apparatus-note": root.attrib.get("apparatus-note", ""),
        "created-by-version": created_by_version,
        "modified-by-version": root.attrib.get("modified-by-version", created_by_version),
        "xml-version": root.attrib.get("xml-version", "83"),
        "test-row-notes": root.attrib.get("test-row-notes", "InTestRowsOnly"),
    }
    root.attrib.clear()
    root.attrib.update(ordered_attrs)


def _sync_attrs(
    element: ET.Element, source_attrs: dict[str, str], managed_keys: tuple[str, ...]
) -> None:
    for key in managed_keys:
        if key not in source_attrs and key in element.attrib:
            del element.attrib[key]
    for key in managed_keys:
        if key in source_attrs:
            element.set(key, source_attrs[key])


def _patch_nameplate(nameplate: ET.Element, model: PtmModel) -> None:
    generated = _build_nameplate(model)
    _sync_attrs(nameplate, generated.attrib, _TWO_WINDING_NAMEPLATE_ATTRS)

    for child_name in ["HVWindingDetails", "LVWindingDetails", "TVWindingDetails"]:
        existing = nameplate.find(child_name)
        replacement = generated.find(child_name)
        if existing is None or replacement is None:
            continue
        existing.attrib.update(replacement.attrib)

    _patch_winding_properties(_ensure_child(nameplate, "winding-properties"), model)
    _replace_child(nameplate, "tapchanger-nameplates", generated.find("tapchanger-nameplates"))


def _build_nameplate(model: PtmModel) -> ET.Element:
    transformer = model.transformer
    high = _winding_by_name(transformer, "Primary")
    low = _winding_by_name(transformer, "Secondary")
    rating = transformer.power_ratings[0] if transformer.power_ratings else None

    attrs = {
        "year-mfg": _year_or_unknown(transformer.manufacturing_year),
        "apparatus-type": "TwoWindingTransformer",
        "mfr": transformer.manufacturer,
        "mfr-location": "",
        "serial-num": transformer.serial_number,
        "special-id": transformer.apparatus_id,
        "config": _config_code(high, low),
        "weight-units": "LB",
        "phases": _phase_label(transformer.number_of_phases),
        "volume-units": "UG",
        "Va-units": "KVA",
        "HVWindingLine": "LineToLine",
        "LVWindingLine": "LineToLine",
    }
    cooling_class = _cooling_class(rating.cooling_class if rating else "")
    if cooling_class:
        attrs["class"] = cooling_class
    coolant = _coolant(transformer.fluid_type)
    if coolant:
        attrs["coolant"] = coolant
    tank_type = _tank_type(transformer.tank_type)
    if tank_type:
        attrs["tanktype"] = tank_type
    _set_if_number(attrs, "oil-volume", _liters_to_us_gallons(transformer.fluid_volume_l))
    for index, value in enumerate(_nameplate_kva_values(transformer.power_ratings)):
        _set_if_number(attrs, f"Va-{index}", value)
    _set_if_number(attrs, "BIL", _v_to_kv(high.bil_v if high else None))
    _set_if_number(attrs, "weight", _kg_to_lb(transformer.total_weight_kg))
    _set_if_number(attrs, "kV-0", _v_to_kv(high.voltage_ll_v if high else None))
    _set_if_number(attrs, "kV-1", _v_to_kv(low.voltage_ll_v if low else None))

    nameplate = ET.Element("two-winding-transformer-nameplate", _strip_empty_attrs(attrs))
    _append_bushing_nameplates(nameplate, model.bushings)
    ET.SubElement(nameplate, "arrester-nameplates")
    winding_properties = ET.SubElement(nameplate, "winding-properties")
    _patch_winding_properties(winding_properties, model)
    nameplate.append(_winding_details("HVWindingDetails", "High", high))
    nameplate.append(_winding_details("LVWindingDetails", "Low", low))
    ET.SubElement(nameplate, "TVWindingDetails", {"Winding": "Tertiary"})
    ET.SubElement(nameplate, "leakage-reactance-nameplates")
    _append_tapchanger_nameplates(nameplate, model)
    ET.SubElement(nameplate, "physical-layout")
    return nameplate


def _build_sessions(model: PtmModel) -> ET.Element:
    sessions = ET.Element("dta-sessions")
    session = ET.SubElement(sessions, "dta-session")
    transformer = ET.SubElement(session, "two-winding-transformer")
    children = {name: ET.SubElement(transformer, name) for name in _DTAX_CHILDREN}
    _patch_session(session, model, children=children)
    return sessions


def _patch_session(
    session: ET.Element,
    model: PtmModel,
    children: dict[str, ET.Element] | None = None,
    create_full_child_set: bool = True,
    preserve_overall_rows: bool = False,
    preserve_template_metadata: bool = False,
) -> None:
    location = model.location
    job = model.job
    if preserve_template_metadata:
        if model.transformer.apparatus_id and "cct-designation" in session.attrib:
            session.set("cct-designation", model.transformer.apparatus_id)
    else:
        session.attrib.update(
            _strip_empty_attrs(
                {
                    "current-timezone": session.attrib.get("current-timezone", ""),
                    "utc-offset-minutes": session.attrib.get("utc-offset-minutes", ""),
                    "location": location.name if location else "",
                    "division": location.division if location else "",
                    "company": session.attrib.get("company") or "Resa Power",
                    "cct-designation": model.transformer.apparatus_id,
                    "session-note": session.attrib.get("session-note", ""),
                    "session-created-date-utc": _dtax_datetime(
                        job.created if job else model.first_test_date
                    ),
                    "first-test-date-utc": _dtax_datetime(model.first_test_date),
                    "last-test-date-utc": _dtax_datetime(model.last_test_date),
                }
            )
        )
    transformer = _ensure_child(session, "two-winding-transformer")
    if children is None:
        child_names = _DTAX_CHILDREN if create_full_child_set else _TEMPLATE_PATCH_CHILDREN
        children = {name: _ensure_child(transformer, name) for name in child_names}

    if not preserve_template_metadata:
        children["admin-data"].attrib.update(
            _strip_empty_attrs(
                {
                    "copies": "N/A",
                    "top_sn": "",
                    "tested-by": job.tester if job else "",
                    "retest-date-utc": _ZERO_DATE,
                    "check-date-utc": _ZERO_DATE,
                    "checked-by": job.approved_by if job else "",
                    "wo": job.work_order if job else "",
                    "bottom-sn": "",
                    "po-num": job.work_order if job else "",
                    "last-date-utc": _dtax_datetime(model.last_test_date),
                    "test-set-type": "Undefined",
                    "reason-enum": "Acceptance",
                    "LineFrequency": _line_frequency(model.transformer.rated_frequency_hz),
                    "test-name": "Undefined",
                }
            )
        )
        _append_test_conditions(children["test-conditions"])
    _patch_winding_resistance_temperature_conditions(children["test-conditions"], model)
    if preserve_overall_rows:
        _patch_existing_bushing_designations(
            children["bushing-designations"], model.bushings
        )
        _patch_overall_tests(children["overall-test-set"], model.overall_power_factor)
    else:
        _clear(children["bushing-designations"])
        _append_bushing_designations(children["bushing-designations"], model.bushings)
        _clear(children["overall-test-set"])
        _append_overall_tests(children["overall-test-set"], model.overall_power_factor)
    if not preserve_template_metadata:
        _patch_bushing_tests(children["m7-bushing-test-set"], model)
    _patch_test_admin_data(children["test-admin-data"], model)
    _clear(children["turns-ratio-test-set"])
    _patch_lv_ttr_tests(children["lvttratio-test-set"], model)
    _patch_lv_ttr_connections(children["lvttratio-connections"], model)
    _patch_exciting_current_tests(children["exciting-current-test-set"], model)
    _patch_exciting_current_connections(children["exciting-current-connections"], model)
    _patch_winding_resistance_tests(
        children["m7winding-resistance-tests-winding-1"], model, "High"
    )
    _patch_winding_resistance_tests(
        children["m7winding-resistance-tests-winding-2"], model, "Low"
    )
    _patch_demagnetization_tests(children["demagnetization-test-set"], model)


def _patch_test_admin_data(parent: ET.Element, model: PtmModel) -> None:
    _clear(parent)
    for test_name, instrument, last_date in _test_admin_entries(model):
        ET.SubElement(
            parent,
            "admin-data",
            _test_admin_attrs(
                test_name=test_name,
                instrument=instrument,
                last_date=last_date,
                line_frequency=_line_frequency(model.transformer.rated_frequency_hz),
            ),
        )


def _test_admin_entries(
    model: PtmModel,
) -> list[tuple[str, PtmInstrumentInfo | None, str]]:
    entries: list[tuple[str, PtmInstrumentInfo | None, str]] = []
    if model.overall_power_factor:
        entries.append(
            (
                "TwoWindingOverall",
                _measurement_instrument(model.overall_power_factor),
                _latest_measurement_date(model.overall_power_factor),
            )
        )
    if model.bushing_power_factor:
        entries.append(
            (
                "Bushings",
                _measurement_instrument(model.bushing_power_factor),
                _latest_measurement_date(model.bushing_power_factor),
            )
        )
    if model.exciting_current_tests:
        entries.append(
            (
                "ExcitingCurrent",
                _test_instrument(model.exciting_current_tests),
                _latest_test_date(model.exciting_current_tests),
            )
        )
    if model.turns_ratio_tests:
        entries.append(
            (
                "LVTTR",
                _test_instrument(model.turns_ratio_tests),
                _latest_test_date(model.turns_ratio_tests),
            )
        )
    if model.winding_resistance_tests:
        entries.append(
            (
                "M7WindingResistance",
                _test_instrument(model.winding_resistance_tests),
                _latest_test_date(model.winding_resistance_tests),
            )
        )
    if model.demagnetization_tests:
        entries.append(
            (
                "Demagnetization",
                _test_instrument(model.demagnetization_tests),
                _latest_test_date(model.demagnetization_tests),
            )
        )
    return entries


def _test_admin_attrs(
    *,
    test_name: str,
    instrument: PtmInstrumentInfo | None,
    last_date: str,
    line_frequency: str,
) -> dict[str, str]:
    return {
        "copies": "",
        "top_sn": instrument.serial_number if instrument else "",
        "tested-by": "",
        "retest-date-utc": _ZERO_DATE,
        "check-date-utc": _ZERO_DATE,
        "checked-by": "",
        "wo": "",
        "bottom-sn": instrument.test_set_name if instrument else "",
        "po-num": "",
        "insurance-book": "",
        "travel-time": "",
        "duration": "",
        "last-date-utc": _dtax_datetime(last_date),
        "last-sheet": "",
        "test-set-type": "Undefined",
        "reason": "",
        "reason-enum": "Undefined",
        "sheet-num": "",
        "crew-size": "-2147483648",
        "counter-1": "-2147483648",
        "counter-2": "-2147483648",
        "counter-3": "-2147483648",
        "resonator-counter": "",
        "resonator-date-tested-utc": _ZERO_DATE,
        "factory-calibration-date": "0001-01-01T00:00:00",
        "factory-recalibration-date": "0001-01-01T00:00:00",
        "field-calibration-date": (
            _dtax_date(instrument.calibration_date) if instrument else "0001-01-01T00:00:00"
        ),
        "LineFrequency": line_frequency,
        "firmware-version": instrument.software_version if instrument else "",
        "dta-version": "",
        "test-name": test_name,
    }


def _measurement_instrument(measurements: list[object]) -> PtmInstrumentInfo | None:
    for measurement in measurements:
        instrument = getattr(measurement, "instrument", None)
        if instrument is not None:
            return instrument
    return None


def _test_instrument(tests: list[object]) -> PtmInstrumentInfo | None:
    for test in tests:
        instrument = getattr(test, "instrument", None)
        if instrument is not None:
            return instrument
    return None


def _latest_measurement_date(measurements: list[object]) -> str:
    return _latest_date(getattr(measurement, "measured_at", "") for measurement in measurements)


def _latest_test_date(tests: list[object]) -> str:
    dates: list[str] = []
    for test in tests:
        dates.append(getattr(test, "execution_date", ""))
        dates.extend(
            getattr(measurement, "measured_at", "")
            for measurement in getattr(test, "measurements", [])
        )
    return _latest_date(dates)


def _latest_date(values: object) -> str:
    dates = sorted(value for value in values if value)
    return dates[-1] if dates else ""


def _append_bushing_nameplates(parent: ET.Element, bushings: list[PtmBushing]) -> None:
    container = ET.SubElement(parent, "bushing-nameplates")
    for bushing in bushings:
        item = ET.SubElement(
            container,
            "bushing-nameplate",
            _strip_empty_attrs(
                {
                    "id": _stable_id(bushing.source_id),
                    "autogenerated": "false",
                    "year-mfg": _year_or_unknown(bushing.manufacturing_year),
                    "tap": "",
                    "style": bushing.style_number,
                    "drwg": bushing.drawing_number,
                    "other": "",
                    "so-num": "",
                    "bushing-serial-num": bushing.serial_number,
                    "termination-id": "",
                    "mfr": bushing.manufacturer,
                    "type": bushing.manufacturer_type,
                    "location": "",
                    "class": bushing.insulation_type,
                    "catalog-num": bushing.catalog_number,
                    "status": "InService",
                    "replacement-date-utc": _ZERO_DATE,
                }
            ),
        )
        ET.SubElement(item, "bushing-dimensions", {"length-units": ""})
        ET.SubElement(item, "bushing-voltage").text = bushing.voltage_class


def _append_tapchanger_nameplates(parent: ET.Element, model: PtmModel) -> None:
    enabled = [tap for tap in model.tap_changers if tap.enabled]
    container = ET.SubElement(
        parent,
        "tapchanger-nameplates",
        {
            "no-tapchanger-confirmation": "false" if enabled else "true",
            "use-only-custom-tap-positions": "false",
        },
    )
    for tap in enabled[:1]:
        position_count = _tapchanger_position_count(model)
        steps_up = max((position_count - 1) // 2, 0)
        steps_down = max(position_count - 1 - steps_up, 0)
        attrs = {
            "id": _stable_id(tap.source_id),
            "line-id": "",
            "tapchanger-type": "DETC",
            "winding": "High",
            "description": "DETC",
            "mfr": tap.manufacturer,
            "type": tap.manufacturer_type,
            "tapchanger-serial-num": tap.serial_number,
            "int-steps": str(position_count) if position_count else "",
            "steps-up": str(steps_up) if position_count else "",
            "steps-down": str(steps_down) if position_count else "",
            "neutral-positions": "1" if position_count else "",
            "oil-volume": _DOUBLE_MIN,
            "naming-preference": "DETCNumeric",
            "pulse-duration": "Undefined",
            "delay-after-movement": "0",
        }
        step_kv = _tapchanger_step_kv(model)
        _set_if_number(attrs, "StepkV", step_kv)
        step_percent = _tapchanger_step_percent(model, step_kv)
        _set_if_number(attrs, "dbl-boost", step_percent)
        _set_if_number(attrs, "dbl-buck", step_percent)
        item = ET.SubElement(
            container,
            "tapchanger-nameplate",
            _strip_empty_attrs(attrs),
        )
        ET.SubElement(item, "detc-connections")


def _append_bushing_designations(parent: ET.Element, bushings: list[PtmBushing]) -> None:
    for bushing in bushings:
        ET.SubElement(
            parent,
            "bushing",
            _strip_empty_attrs(
                {
                    "id": _stable_id(bushing.source_id),
                    "serial-number": bushing.serial_number,
                    "designation": bushing.designation,
                    "termination-phase": "",
                    "status": "InService",
                }
            ),
        )


def _patch_existing_bushing_designations(
    parent: ET.Element, bushings: list[PtmBushing]
) -> None:
    existing_rows = parent.findall("bushing")
    if not existing_rows:
        return
    for row, bushing in zip(existing_rows, bushings, strict=False):
        for key, value in {
            "id": _stable_id(bushing.source_id),
            "serial-number": bushing.serial_number,
            "designation": bushing.designation,
            "status": "InService",
        }.items():
            if key in row.attrib:
                row.set(key, value)


def _patch_bushing_tests(parent: ET.Element, model: PtmModel) -> None:
    _clear(parent)
    if not model.bushing_power_factor:
        return

    measurements_by_designation: dict[str, list[PtmPowerFactorMeasurement]] = {}
    for measurement in model.bushing_power_factor:
        designation = measurement.measurement_name.upper()
        measurements_by_designation.setdefault(designation, []).append(measurement)

    for bushing in model.bushings:
        measurements = measurements_by_designation.get(bushing.designation.upper(), [])
        if not measurements:
            continue
        row = ET.SubElement(
            parent,
            "m7-bushing-test",
            {"bushing-id": _stable_id(bushing.source_id)},
        )
        results = ET.SubElement(row, "bushing-test-results-set")
        for measurement in measurements:
            item = ET.SubElement(
                results,
                "bushing-test-results",
                _strip_empty_attrs(_bushing_test_attrs(measurement)),
            )
            ET.SubElement(item, "iwc-data")
        _append_bushing_vfpf_defaults(ET.SubElement(row, "bushing-vfpf-test-set"))


def _bushing_test_attrs(measurement: PtmPowerFactorMeasurement) -> dict[str, str]:
    attrs = {
        "date-tested-utc": _dtax_datetime(measurement.measured_at),
        "rating-expert-system": _rating_from_grade(measurement.grade),
        "rating-tester": _rating_from_grade(measurement.grade),
        "message-expert-system": "",
        "test-circuit": _TEST_CIRCUIT_BY_MODE.get(measurement.mode, ""),
        "bushing-insulation": _bushing_insulation(measurement),
        "use-arrhenius-tcf": "false",
        "arrhenius-VFPF-session-date-utc": _ZERO_DATE,
    }
    _set_if_number(attrs, "requested-test-kV", _v_to_kv(measurement.requested_voltage_v))
    _set_if_number(attrs, "test-kV", _v_to_kv(measurement.voltage_out_v))
    _set_if_number(attrs, "mA", _a_to_ma(measurement.current_measured_a))
    _set_if_number(attrs, "watts", measurement.watt_losses)
    _set_if_number(attrs, "measured-cap", _farad_to_pf(measurement.capacitance_measured_f))
    _set_if_number(attrs, "pfm", measurement.power_factor_measured)
    _set_if_number(attrs, "pfc", measurement.power_factor_corrected)
    _set_if_number(attrs, "correction-factor", measurement.correction_factor)
    return attrs


def _bushing_insulation(measurement: PtmPowerFactorMeasurement) -> str:
    upper_name = measurement.measurement_name.upper()
    if "C2" in upper_name:
        return "C2"
    if "C1" in upper_name:
        return "C1"
    if measurement.mode in {"Gst", "GstGa", "GstGb"}:
        return "C2"
    return "C1"


def _append_bushing_vfpf_defaults(parent: ET.Element) -> None:
    for insulation, circuit in [
        ("C1", "EV_HV1__MC_HV2__EG_MG"),
        ("C2", "EV_HV2__MC_MG__EG_HV1"),
        ("C1_PLUS_C2", ""),
        ("C1_INV", "EV_HV2__MC_HV1__EG_MG"),
        ("C1C2_MINUS_C1C2", ""),
        ("C1_MINUS_C1_INV", ""),
    ]:
        attrs = {
            "date-tested-utc": _ZERO_DATE,
            "rating-expert-system": "Unrated",
            "rating-tester": "Unrated",
            "test-circuit": circuit,
            "line-id": "",
            "insulation": insulation,
            "start-frequency": "400",
            "stop-frequency": "15",
            "temperature": _DOUBLE_MIN,
            "arrhenius-temp-corrected": "20",
            "arrhenius-activation-energy": "0.6",
            "arrhenius-measured-PF": _DOUBLE_MIN,
            "arrhenius-corrected-PF": _DOUBLE_MIN,
            "arrhenius-tcf": _DOUBLE_MIN,
        }
        row = ET.SubElement(parent, "vfpf-test", _strip_empty_attrs(attrs))
        ET.SubElement(row, "iwc-data")
        ET.SubElement(row, "m7dual-cablestates", _all_ig_cable_states())
        ET.SubElement(row, "m7single-cablestates", _all_ig_cable_states())
        ET.SubElement(row, "fds-test-results")


def _append_test_conditions(parent: ET.Element) -> None:
    parent.attrib.update(
        _strip_empty_attrs(
            {
                "weather": "",
                "internal-temp": "",
                "air-temp": "",
                "humidity": "",
            }
        )
    )


def _patch_winding_properties(parent: ET.Element, model: PtmModel) -> None:
    material = _winding_resistance_material(model)
    if material:
        parent.set("winding-material", material)

    reference_temp = _first_number(
        test.reference_temperature_c for test in model.winding_resistance_tests
    )
    _set_if_number(parent.attrib, "temperature-rise", reference_temp)


def _patch_winding_resistance_temperature_conditions(
    parent: ET.Element, model: PtmModel
) -> None:
    measured_temp = _first_number(
        test.measured_temperature_c for test in model.winding_resistance_tests
    )
    _set_if_number(parent.attrib, "internal-temp", measured_temp)


def _winding_resistance_material(model: PtmModel) -> str:
    for test in model.winding_resistance_tests:
        if test.winding_material:
            return test.winding_material
    for winding in model.transformer.windings:
        if winding.conductor_material:
            return winding.conductor_material
    return ""


def _append_overall_tests(
    parent: ET.Element, measurements: list[PtmPowerFactorMeasurement]
) -> None:
    for line_id, measurement in enumerate(measurements, start=1):
        attrs = _overall_test_attrs(measurement, str(line_id))
        item = ET.SubElement(parent, "overall-test", _strip_empty_attrs(attrs))
        ET.SubElement(item, "iwc-data")


def _patch_overall_tests(
    parent: ET.Element, measurements: list[PtmPowerFactorMeasurement]
) -> None:
    existing_rows = parent.findall("overall-test")
    used_ids: set[int] = set()

    for row in existing_rows:
        _reset_overall_test_row(row)

    for measurement in measurements:
        target_insulation = _overall_insulation(measurement)
        row = _find_available_overall_row(existing_rows, used_ids, target_insulation)
        if row is None:
            row = ET.SubElement(parent, "overall-test")
            existing_rows.append(row)
        used_ids.add(id(row))
        line_id = row.attrib.get("line-id") or str(len(existing_rows))
        row.attrib.clear()
        row.attrib.update(_strip_empty_attrs(_overall_test_attrs(measurement, line_id)))
        _set_single_iwc_data_child(row)


def _patch_turns_ratio_tests(parent: ET.Element, model: PtmModel) -> None:
    _clear(parent)
    high = _winding_by_name(model.transformer, "Primary")
    low = _winding_by_name(model.transformer, "Secondary")

    for test in model.turns_ratio_tests:
        for tap_index, tap_name, phase_rows in _phase_groups(test.measurements):
            row = ET.SubElement(parent, "turns-ratio-test")
            attrs = {
                "date-tested-utc": _dtax_datetime(_latest_measured_at(phase_rows)),
                "rating-expert-system": _rating_from_phase_rows(phase_rows),
                "rating-tester": _rating_from_phase_rows(phase_rows),
                "message-expert-system": "",
                "detc-position": _tap_index_text(tap_index),
                "ltc-position": "0",
                "tap-position1": _tap_position_text(tap_index, tap_name),
                "tap-position2": _tap_position_text(tap_index, tap_name),
                "wdg-id": "",
                "wdg-tap": "",
                "var": "Undefined",
                "var_manual": "",
                "detc-id": "00000000-0000-0000-0000-000000000000",
                "ltc-id": "00000000-0000-0000-0000-000000000000",
            }
            _set_if_number(attrs, "requested-test-kV", _v_to_kv(test.test_voltage_v))
            _set_if_number(attrs, "np-volt1", high.voltage_ll_v if high else None)
            _set_if_number(attrs, "np-volt2", low.voltage_ll_v if low else None)

            nominal = _first_number(
                row.nominal_ratio for row in phase_rows.values()
            )
            _set_if_number(attrs, "calratio", nominal)
            if nominal is not None:
                _set_if_number(attrs, "min-limit", nominal * 0.995)
                _set_if_number(attrs, "max-limit", nominal * 1.005)

            for phase_number, measurement in phase_rows.items():
                _set_if_number(
                    attrs, f"ratio-{phase_number}", measurement.voltage_turns_ratio
                )
                _set_if_number(
                    attrs, f"deviation-{phase_number}", measurement.ratio_deviation
                )

            ET.SubElement(row, "ratio-test-fields", _strip_empty_attrs(attrs))
            ET.SubElement(row, "iwc-data")
            refs = ET.SubElement(row, "tc-references")
            ET.SubElement(refs, "tc-reference-set")


def _patch_turns_ratio_connections(parent: ET.Element, model: PtmModel) -> None:
    if not model.turns_ratio_tests:
        return
    fields = _ensure_child(parent, "ratio-connection-fields")
    for index in range(1, 13):
        fields.attrib.setdefault(f"conn-{index}", "")


def _patch_lv_ttr_tests(parent: ET.Element, model: PtmModel) -> None:
    _clear(parent)
    low = _winding_by_name(model.transformer, "Secondary")
    tapchanger_id = _detc_tapchanger_id(model)
    for test in model.turns_ratio_tests:
        for tap_index, tap_name, phase_rows in _phase_groups(test.measurements):
            row = ET.SubElement(parent, "lvttratio-test", {"label": "H-X"})
            nominal = _first_number(
                measurement.nominal_ratio for measurement in phase_rows.values()
            )
            attrs = {
                "date-tested-utc": _dtax_datetime(_latest_measured_at(phase_rows)),
                "rating-expert-system": _rating_from_phase_rows(phase_rows),
                "rating-tester": _rating_from_phase_rows(phase_rows),
                "message-expert-system": "",
                "detc-id": _ZERO_ID,
                "ltc-id": _ZERO_ID,
                "tri-phase-rating-expert-system": _rating_from_phase_rows(phase_rows),
                "tri-phase-rating-tester": _rating_from_phase_rows(phase_rows),
            }
            _set_if_number(attrs, "requested-test-kV", _v_to_kv(test.test_voltage_v))
            _set_if_number(attrs, "hv-volt", _lv_ttr_high_kv(nominal, low))
            _set_if_number(attrs, "lv-volt", _v_to_kv(low.voltage_ll_v if low else None))
            _set_if_number(attrs, "benchmark-ratio", nominal)
            _set_if_number(attrs, "benchmark-ratio-triple-phase", nominal)
            if nominal is not None:
                _set_if_number(attrs, "min-limit", nominal * 0.995)
                _set_if_number(attrs, "max-limit", nominal * 1.005)
                _set_if_number(attrs, "min-limit-triple-phase", nominal * 0.995)
                _set_if_number(attrs, "max-limit-triple-phase", nominal * 1.005)
            for phase_number, measurement in phase_rows.items():
                _set_if_number(
                    attrs, f"ratio-{phase_number}", measurement.voltage_turns_ratio
                )
                _set_if_number(
                    attrs, f"deviation-{phase_number}", measurement.ratio_deviation
                )
                _set_if_number(
                    attrs,
                    f"angle-{phase_number}",
                    measurement.secondary_voltage_phase_deg,
                )

            fields = ET.SubElement(row, "ratio-test-fields", _strip_empty_attrs(attrs))
            ET.SubElement(fields, "iwc-data")
            refs = ET.SubElement(fields, "tc-references")
            ref_set = ET.SubElement(refs, "tc-reference-set")
            if tap_index is not None and tap_index >= 0:
                ET.SubElement(
                    ref_set,
                    "tc-reference",
                    {
                        "tapchanger-id": tapchanger_id,
                        "tapchanger-position": _tap_position_text(tap_index, tap_name),
                        "tapchanger-type": "DETC",
                    },
                )
            ET.SubElement(row, "cablestates", _lv_ttr_cable_states())


def _patch_lv_ttr_connections(parent: ET.Element, model: PtmModel) -> None:
    if not model.turns_ratio_tests:
        return


def _lv_ttr_high_kv(nominal_ratio: float | None, low: PtmWinding | None) -> float | None:
    if nominal_ratio is not None and low and low.voltage_ll_v is not None:
        return _v_to_kv(nominal_ratio * low.voltage_ll_v)
    return None


def _lv_ttr_cable_states() -> dict[str, str]:
    return {
        "HV1": "IG",
        "HV2": "IG",
        "LV1": "IG",
        "LV2": "IG",
        "LV3": "IG",
        "LVN": "EG",
        "M1": "IG",
        "M2": "IG",
        "M3": "IG",
        "MG": "IG",
    }


def _all_ig_cable_states() -> dict[str, str]:
    return {
        "HV1": "IG",
        "HV2": "IG",
        "LV1": "IG",
        "LV2": "IG",
        "LV3": "IG",
        "LVN": "IG",
        "M1": "IG",
        "M2": "IG",
        "M3": "IG",
        "MG": "IG",
    }


def _patch_exciting_current_tests(parent: ET.Element, model: PtmModel) -> None:
    _clear(parent)
    tapchanger_id = _detc_tapchanger_id(model)
    for test in model.exciting_current_tests:
        for tap_index, tap_name, phase_rows in _phase_groups(test.measurements):
            row = ET.SubElement(
                parent,
                "exciting-current-test",
                {
                    "detc": "0",
                    "ltc": "0",
                    "use-iwc-for-linefreq-test": "false",
                    "line-frequency": _line_frequency(test.test_frequency_hz),
                    "include-in-plot": "true",
                    "detc-id": _ZERO_ID,
                    "ltc-id": _ZERO_ID,
                },
            )
            for _phase_number in range(1, 4):
                ET.SubElement(row, "iwc-data")
            for _phase_number in range(1, 4):
                voltages = ET.SubElement(row, "linefreq-test-voltages")
                ET.SubElement(voltages, "m_dHighFreqkV").text = _DOUBLE_MIN
                ET.SubElement(voltages, "m_dLowFreqkV").text = _DOUBLE_MIN

            attrs = {
                "date-tested-utc": _dtax_datetime(_latest_measured_at(phase_rows)),
                "rating-expert-system": _rating_from_phase_rows(phase_rows),
                "rating-tester": _rating_from_phase_rows(phase_rows),
                "message-expert-system": "",
                "test-circuit-1": "CIRC_UST_R",
                "test-circuit-2": "CIRC_UST_R",
                "test-circuit-3": "CIRC_UST_R",
                "l-or-c-1": "L",
                "l-or-c-2": "L",
                "l-or-c-3": "L",
                "FrequencyPCT1": "FREQ_5PCT",
                "FrequencyPCT2": "FREQ_5PCT",
                "FrequencyPCT3": "FREQ_5PCT",
                "winding-id": "",
                "winding-tap": "",
            }
            _set_if_number(attrs, "test-kV", _v_to_kv(test.test_voltage_v))
            for phase_number, measurement in phase_rows.items():
                _set_if_number(
                    attrs,
                    f"mA-{phase_number}",
                    _a_to_ma(
                        measurement.current_corrected_a
                        if measurement.current_corrected_a is not None
                        else measurement.current_out_a
                    ),
                )
                _set_if_number(attrs, f"watts-{phase_number}", measurement.watt_losses)
                _set_if_number(
                    attrs, f"actualkv-{phase_number}", _v_to_kv(measurement.voltage_out_v)
                )
            ET.SubElement(row, "exciting-current-fields", _strip_empty_attrs(attrs))
            refs = ET.SubElement(row, "tc-references")
            ref_set = ET.SubElement(refs, "tc-reference-set")
            if tap_index is not None and tap_index >= 0:
                ET.SubElement(
                    ref_set,
                    "tc-reference",
                    {
                        "tapchanger-id": tapchanger_id,
                        "tapchanger-position": str(tap_index),
                        "tapchanger-type": "DETC",
                    },
                )


def _patch_exciting_current_connections(parent: ET.Element, model: PtmModel) -> None:
    if not model.exciting_current_tests:
        return
    for key, value in _exciting_current_connection_labels(model).items():
        parent.set(key, value)
    parent.attrib.setdefault("circuit-description", "CIRC_UST_RB")
    for key in [
        "m4-circuit-description1",
        "m4-circuit-description2",
        "m4-circuit-description3",
    ]:
        parent.set(key, "CIRC_UST_R")


def _exciting_current_connection_labels(model: PtmModel) -> dict[str, str]:
    high = _winding_by_name(model.transformer, "Primary")
    vector = (high.vector_type if high else "").upper()
    if vector.startswith("Y"):
        labels = ["H1", "H0", "H2", "H0", "H3", "H0"]
    else:
        labels = ["H1", "H3", "H2", "H1", "H3", "H2"]
    return {f"conn-{index}": value for index, value in enumerate(labels, start=1)}


def _patch_winding_resistance_tests(
    parent: ET.Element, model: PtmModel, winding: str
) -> None:
    matching_tests = [
        test
        for test in model.winding_resistance_tests
        if _winding_resistance_winding(test) == winding
    ]
    if matching_tests:
        _patch_winding_resistance_connections(parent, model, winding)

    test_set = _ensure_child(parent, "m7winding-resistance-test-set")
    _clear(test_set)
    for test in matching_tests:
        for _tap_index, _tap_name, phase_rows in _phase_groups(test.measurements):
            row = ET.SubElement(
                test_set,
                "m7winding-resistance-test",
                _strip_empty_attrs(
                    {
                        "date-tested-utc": _dtax_datetime(
                            _latest_measured_at(phase_rows)
                        ),
                        "rating-expert-system": _rating_from_phase_rows(phase_rows),
                        "rating-tester": _rating_from_phase_rows(phase_rows),
                        "IEEE-Standard-Data": "false",
                        "include-in-plot": "true",
                        "dc-voltage-limit": "0.1",
                    }
                ),
            )
            _set_if_number(row.attrib, "requested-test-amps", test.test_current_a)
            ET.SubElement(row, "iwc-data")
            refs = ET.SubElement(row, "tc-references")
            ET.SubElement(refs, "tc-reference-set")

            attrs = {
                "date-tested-utc": _dtax_datetime(_latest_measured_at(phase_rows)),
                "rating-expert-system": _rating_from_phase_rows(phase_rows),
                "rating-tester": _rating_from_phase_rows(phase_rows),
                "message-expert-system": "",
            }
            for phase_number, description in enumerate(
                _winding_resistance_circuit_descriptions(winding), start=1
            ):
                attrs[f"test-circuit-{phase_number}"] = description

            for phase_number, measurement in phase_rows.items():
                voltage = (
                    measurement.corrected_voltage_v
                    if measurement.corrected_voltage_v is not None
                    else measurement.voltage_v
                )
                _set_if_number(
                    attrs,
                    f"corr-factor{phase_number}",
                    _winding_resistance_correction_factor(test, measurement),
                )
                _set_if_number(
                    attrs,
                    f"calculated-resistance{phase_number}",
                    measurement.resistance_measured_ohm,
                )
                _set_if_number(
                    attrs,
                    f"corrected-resistance{phase_number}",
                    measurement.resistance_corrected_ohm,
                )
                spread_key = _winding_resistance_spread_key(phase_number)
                if spread_key:
                    _set_if_number(
                        attrs,
                        spread_key,
                        _winding_resistance_spread_percent(measurement),
                    )
                _set_if_number(attrs, f"test-kV{phase_number}", _v_to_kv(voltage))
                _set_if_number(attrs, f"actual-amps{phase_number}", measurement.current_a)
            ET.SubElement(row, "winding-resistance-fields", _strip_empty_attrs(attrs))


def _patch_winding_resistance_connections(
    parent: ET.Element, model: PtmModel, winding: str
) -> None:
    connections = _ensure_child(parent, "m7winding-resistance-connections")
    for key, value in _winding_resistance_connection_labels(model, winding).items():
        connections.set(key, value)
    for index, description in enumerate(
        _winding_resistance_circuit_descriptions(winding), start=1
    ):
        connections.set(f"circuit-description-{index}", description)


def _patch_demagnetization_tests(parent: ET.Element, model: PtmModel) -> None:
    if not model.demagnetization_tests:
        return

    _clear(parent)
    ET.SubElement(
        parent,
        "demagnetization-connections",
        {
            "conn-1": "",
            "conn-2": "",
            "conn-3": "",
            "conn-4": "",
            "conn-5": "",
            "conn-6": "",
            "demag-energize-lead-1": "LV3",
            "demag-energize-lead-2": "LV1",
            "demag-energize-lead-3": "LV2",
            "demag-measure-lead-1": "LV1",
            "demag-measure-lead-2": "LV2",
            "demag-measure-lead-3": "LV3",
            "rated-volts": _DOUBLE_MIN,
        },
    )
    results = ET.SubElement(parent, "demagnetization-test-results-set")
    for test in model.demagnetization_tests:
        for measurement in test.measurements:
            result = ET.SubElement(results, "demagnetization-test-results")
            attrs = {
                "date-tested-utc": _dtax_datetime(
                    measurement.measured_at or test.execution_date
                ),
                "phase-a-test-completed": _bool_dtax(
                    _demagnetization_measurement_completed(measurement.status)
                ),
                "phase-b-test-completed": _bool_dtax(
                    _demagnetization_measurement_completed(measurement.status)
                ),
                "phase-c-test-completed": _bool_dtax(
                    _demagnetization_measurement_completed(measurement.status)
                ),
            }
            _set_if_number(attrs, "frequency", model.transformer.rated_frequency_hz)
            _set_if_number(attrs, "current-c", measurement.resistance_ohm)
            ET.SubElement(result, "demagnetization-demag-test", _strip_empty_attrs(attrs))


def _demagnetization_measurement_completed(status: str) -> bool:
    normalized = status.lower()
    if "fail" in normalized:
        return False
    return True


def _winding_resistance_connection_labels(
    model: PtmModel, winding: str
) -> dict[str, str]:
    if winding == "High":
        terminal = "H"
        source_winding = _winding_by_name(model.transformer, "Primary")
    else:
        terminal = "X"
        source_winding = _winding_by_name(model.transformer, "Secondary")

    vector = (source_winding.vector_type if source_winding else "").upper()
    if vector.startswith("Y"):
        labels = [
            f"{terminal}1",
            f"{terminal}0",
            f"{terminal}2",
            f"{terminal}0",
            f"{terminal}3",
            f"{terminal}0",
        ]
    else:
        labels = [
            f"{terminal}1",
            f"{terminal}2",
            f"{terminal}2",
            f"{terminal}3",
            f"{terminal}3",
            f"{terminal}1",
        ]
    return {f"conn-{index}": value for index, value in enumerate(labels, start=1)}


def _winding_resistance_circuit_descriptions(winding: str) -> list[str]:
    if winding == "High":
        return [
            "EDC_LV3__MDV_LV1__EG_LV1__FLT_LV2",
            "EDC_LV1__MDV_LV2__EG_LV2__FLT_LV3",
            "EDC_LV2__MDV_LV3__EG_LV3__FLT_LV1",
        ]
    return [
        "EDC_LV1__MDV_LVN__EG_LVN__FLT_LV2__FLT_LV3",
        "EDC_LV2__MDV_LVN__EG_LVN__FLT_LV1__FLT_LV3",
        "EDC_LV3__MDV_LVN__EG_LVN__FLT_LV1__FLT_LV2",
    ]


def _winding_resistance_correction_factor(
    test: PtmWindingResistanceTest, measurement: PtmWindingResistanceMeasurement
) -> float | None:
    if test.correction_factor is not None:
        return test.correction_factor
    measured = measurement.resistance_measured_ohm
    corrected = measurement.resistance_corrected_ohm
    if measured not in {None, 0} and corrected is not None:
        return corrected / measured
    return None


def _winding_resistance_spread_key(phase_number: int) -> str:
    return {1: "spread-ab", 2: "spread-bc", 3: "spread-ca"}.get(phase_number, "")


def _winding_resistance_spread_percent(
    measurement: PtmWindingResistanceMeasurement,
) -> float | None:
    if measurement.resistance_deviation is None:
        return None
    return measurement.resistance_deviation * 100


def _reset_overall_test_row(row: ET.Element) -> None:
    line_id = row.attrib.get("line-id", "")
    insulation = row.attrib.get("insulation", "")
    row.attrib.clear()
    row.attrib.update(
        _strip_empty_attrs(
            {
                "date-tested-utc": _ZERO_DATE,
                "rating-expert-system": "Unrated",
                "rating-tester": "Unrated",
                "use-arrhenius-tcf": "false",
                "arrhenius-VFPF-session-date-utc": _ZERO_DATE,
                "line-id": line_id,
                "insulation": insulation,
            }
        )
    )
    _set_single_iwc_data_child(row)


def _find_available_overall_row(
    rows: list[ET.Element], used_ids: set[int], target_insulation: str
) -> ET.Element | None:
    for row in rows:
        if id(row) not in used_ids and row.attrib.get("insulation") == target_insulation:
            return row
    for row in rows:
        if id(row) not in used_ids:
            return row
    return None


def _set_single_iwc_data_child(row: ET.Element) -> None:
    for child in list(row):
        row.remove(child)
    ET.SubElement(row, "iwc-data")


def _overall_test_attrs(
    measurement: PtmPowerFactorMeasurement, line_id: str
) -> dict[str, str]:
    attrs = {
        "date-tested-utc": _dtax_datetime(measurement.measured_at),
        "rating-expert-system": "Undefined",
        "rating-tester": _rating_from_grade(measurement.grade),
        "message-expert-system": "",
        "test-circuit": _TEST_CIRCUIT_BY_MODE.get(measurement.mode, ""),
        "line-id": line_id,
        "insulation": _overall_insulation(measurement),
        "use-arrhenius-tcf": "false",
        "arrhenius-VFPF-session-date-utc": _ZERO_DATE,
    }
    _set_if_number(attrs, "requested-test-kV", _v_to_kv(measurement.requested_voltage_v))
    _set_if_number(attrs, "test-kV", _v_to_kv(measurement.voltage_out_v))
    _set_if_number(attrs, "mA", _a_to_ma(measurement.current_measured_a))
    _set_if_number(attrs, "watts", measurement.watt_losses)
    _set_if_number(attrs, "measured-cap", _farad_to_pf(measurement.capacitance_measured_f))
    _set_if_number(attrs, "pfm", measurement.power_factor_measured)
    _set_if_number(attrs, "pfc", measurement.power_factor_corrected)
    _set_if_number(attrs, "correction-factor", measurement.correction_factor)
    return attrs


def _overall_insulation(measurement: PtmPowerFactorMeasurement) -> str:
    return _OVERALL_INSULATION.get(
        measurement.transformer_overall_capacitance,
        measurement.transformer_overall_capacitance,
    )


def _phase_groups(
    measurements: list[
        PtmTurnsRatioMeasurement
        | PtmWindingResistanceMeasurement
        | PtmExcitingCurrentMeasurement
    ],
) -> list[tuple[int | None, str, dict[int, object]]]:
    grouped: dict[tuple[int | None, str], dict[int, object]] = {}
    for measurement in sorted(measurements, key=lambda item: item.measured_at):
        phase_number = _phase_number(measurement.phase)
        if phase_number is None:
            continue
        key = (measurement.tap_index, measurement.name)
        grouped.setdefault(key, {})[phase_number] = measurement
    return [
        (tap_index, tap_name, phases)
        for (tap_index, tap_name), phases in sorted(
            grouped.items(),
            key=lambda item: (
                item[0][0] is None,
                item[0][0] if item[0][0] is not None else 0,
                item[0][1],
            ),
        )
    ]


def _phase_number(phase: str) -> int | None:
    return {"PhaseA": 1, "PhaseB": 2, "PhaseC": 3}.get(phase)


def _latest_measured_at(measurements: dict[int, object]) -> str:
    dates = [
        getattr(measurement, "measured_at", "")
        for measurement in measurements.values()
        if getattr(measurement, "measured_at", "")
    ]
    return sorted(dates)[-1] if dates else ""


def _tap_index_text(tap_index: int | None) -> str:
    if tap_index is None or tap_index < 0:
        return "0"
    return str(tap_index)


def _tap_position_text(tap_index: int | None, tap_name: str) -> str:
    if tap_name:
        return tap_name
    if tap_index is None or tap_index < 0:
        return ""
    return str(tap_index + 1)


def _detc_tapchanger_id(model: PtmModel) -> str:
    for tapchanger in model.tap_changers:
        if tapchanger.enabled:
            return _stable_id(tapchanger.source_id)
    return _ZERO_ID


def _tapchanger_position_count(model: PtmModel) -> int:
    indices = {
        measurement.tap_index
        for test in model.turns_ratio_tests
        for measurement in test.measurements
        if measurement.tap_index is not None and measurement.tap_index >= 0
    }
    return len(indices)


def _tapchanger_step_kv(model: PtmModel) -> float | None:
    low = _winding_by_name(model.transformer, "Secondary")
    low_kv = _v_to_kv(low.voltage_ll_v if low else None)
    if low_kv is None:
        return None

    ratios_by_tap: dict[int, float] = {}
    for test in model.turns_ratio_tests:
        for measurement in test.measurements:
            if (
                measurement.tap_index is not None
                and measurement.tap_index >= 0
                and measurement.nominal_ratio is not None
                and measurement.tap_index not in ratios_by_tap
            ):
                ratios_by_tap[measurement.tap_index] = measurement.nominal_ratio

    ordered = [ratio for _tap, ratio in sorted(ratios_by_tap.items())]
    if len(ordered) < 2:
        return None
    steps = [
        abs(next_ratio - ratio) * low_kv
        for ratio, next_ratio in zip(ordered, ordered[1:], strict=False)
        if next_ratio != ratio
    ]
    if not steps:
        return None
    return sorted(steps)[len(steps) // 2]


def _tapchanger_step_percent(model: PtmModel, step_kv: float | None) -> float | None:
    if step_kv is None:
        return None
    high = _winding_by_name(model.transformer, "Primary")
    high_kv = _v_to_kv(high.voltage_ll_v if high else None)
    if high_kv in {None, 0}:
        return None
    return step_kv / high_kv * 100


def _first_number(values: object) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def _nameplate_kva_values(ratings: list[PtmPowerRating]) -> list[float]:
    values = [
        kva
        for kva in (_va_to_kva(rating.rated_power_va) for rating in ratings)
        if kva is not None
    ]
    if not values:
        return []
    if len(values) == 1:
        return values * 4
    repeated = values.copy()
    while len(repeated) < 4:
        repeated.extend(values)
    return repeated[:4]


def _rating_from_phase_rows(measurements: dict[int, object]) -> str:
    ratings = {
        _rating_from_assessment(getattr(measurement, "assessment", ""))
        for measurement in measurements.values()
    }
    if "Investigate" in ratings:
        return "Investigate"
    if "Good" in ratings:
        return "Good"
    return "Unrated"


def _rating_from_assessment(assessment: str) -> str:
    if assessment in {"Pass", "Normal", "Good"}:
        return "Good"
    if assessment in {"Fail", "Failed"}:
        return "Investigate"
    return "Unrated"


def _winding_resistance_winding(test: PtmWindingResistanceTest) -> str:
    if test.output_side == "OutputSide_HV":
        return "High"
    if test.output_side == "OutputSide_LV":
        return "Low"
    upper_name = test.name.upper()
    if " H" in upper_name or upper_name.endswith("H"):
        return "High"
    if " X" in upper_name or upper_name.endswith("X"):
        return "Low"
    return ""


def _winding_details(name: str, winding_name: str, winding: PtmWinding | None) -> ET.Element:
    vector = winding.vector_type if winding else ""
    attrs = {
        "Winding": winding_name,
        "WindingType": _winding_type(vector),
        "WindingSubType": _winding_subtype(vector),
        "IECVector": _iec_vector(winding),
        "TerminalRotation": "Clockwise",
    }
    return ET.Element(name, _strip_empty_attrs(attrs))


def _winding_by_name(transformer: PtmTransformer, name: str) -> PtmWinding | None:
    for winding in transformer.windings:
        if winding.name == name:
            return winding
    return None


def _config_code(high: PtmWinding | None, low: PtmWinding | None) -> str:
    high_code = _vector_config(high.vector_type if high else "")
    low_code = _vector_config(low.vector_type if low else "")
    return "_".join(code for code in [high_code, low_code] if code)


def _vector_config(vector: str) -> str:
    normalized = vector.upper()
    if normalized.startswith("D"):
        return "D"
    if normalized.startswith("Y"):
        return "Y"
    return normalized


def _winding_type(vector: str) -> str:
    normalized = vector.upper()
    if normalized.startswith("D"):
        return "Delta"
    if normalized.startswith("Y"):
        return "Wye"
    return ""


def _winding_subtype(vector: str) -> str:
    normalized = vector.upper()
    if normalized.startswith("D"):
        return "Delta_Standard"
    if normalized.startswith("YN"):
        return "Wye_AccessibleNeutral"
    if normalized.startswith("Y"):
        return "Wye_Standard"
    return ""


def _iec_vector(winding: PtmWinding | None) -> str:
    if winding is None:
        return ""
    shift = winding.phase_shift.strip("_")
    if shift.isdigit():
        return f"V{shift}"
    return "V0"


def _phase_label(number_of_phases: int | None) -> str:
    return {1: "Single", 3: "Three"}.get(number_of_phases, "")


def _coolant(fluid_type: str) -> str:
    return {
        "NaturalEster": "FR3",
        "NaturalEsters": "FR3",
        "MineralOil": "Oil",
    }.get(fluid_type, fluid_type)


def _tank_type(tank_type: str) -> str:
    return {
        "Sealed": "N2BLANKETED",
        "NitrogenBlanketed": "N2BLANKETED",
        "SealedConservator": "SEALEDCONSER",
        "Conservator": "SEALEDCONSER",
    }.get(tank_type, tank_type)


def _cooling_class(cooling_class: str) -> str:
    return "" if cooling_class in {"BlankEntry", "NotSelected"} else cooling_class


def _line_frequency(frequency: float | None) -> str:
    if frequency == 60:
        return "Hertz60"
    if frequency == 50:
        return "Hertz50"
    return "Custom"


def _bool_dtax(value: bool) -> str:
    return "true" if value else "false"


def _rating_from_grade(grade: str) -> str:
    return "Good" if grade in {"Normal", "Good"} else "Unrated"


def _stable_id(value: str) -> str:
    if not value:
        return str(uuid5(NAMESPACE_URL, "power-test-converters:blank"))
    try:
        return str(UUID(value))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, value))


def _dtax_datetime(value: str) -> str:
    if not value:
        return _ZERO_DATE
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value.replace("T", " ").split(".")[0].replace("Z", "")
    return parsed.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")


def _dtax_date(value: str) -> str:
    if not value:
        return "0001-01-01T00:00:00"
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value.split("T")[0] + "T00:00:00"
    return parsed.replace(tzinfo=None).strftime("%Y-%m-%dT00:00:00")


def _set_if_number(attrs: dict[str, str], key: str, value: float | None) -> None:
    if value is not None:
        attrs[key] = _format_number(value)


def _format_number(value: float) -> str:
    return f"{value:.15g}"


def _strip_empty_attrs(attrs: dict[str, str | None]) -> dict[str, str]:
    return {key: value for key, value in attrs.items() if value is not None}


def _replace_child(parent: ET.Element, tag: str, replacement: ET.Element | None) -> None:
    if replacement is None:
        return
    existing = parent.find(tag)
    if existing is None:
        parent.append(replacement)
        return
    index = list(parent).index(existing)
    parent.remove(existing)
    parent.insert(index, replacement)


def _ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def _clone_element(element: ET.Element) -> ET.Element:
    return ET.fromstring(ET.tostring(element, encoding="unicode"))


def _set_child_text(parent: ET.Element, tag: str, text: str) -> None:
    child = _ensure_child(parent, tag)
    child.text = text


def _clear(element: ET.Element) -> None:
    element.text = None
    element.tail = None
    for child in list(element):
        element.remove(child)


def _year_or_unknown(value: str) -> str:
    return value if value and value != "0" else "-2147483648"


def _v_to_kv(value: float | None) -> float | None:
    return value / 1000 if value is not None else None


def _va_to_kva(value: float | None) -> float | None:
    return value / 1000 if value is not None else None


def _a_to_ma(value: float | None) -> float | None:
    return value * 1000 if value is not None else None


def _farad_to_pf(value: float | None) -> float | None:
    return value * 1_000_000_000_000 if value is not None else None


def _liters_to_us_gallons(value: float | None) -> float | None:
    return _converted_unit_value(value, 0.2641720524)


def _kg_to_lb(value: float | None) -> float | None:
    return _converted_unit_value(value, 2.20462262185)


def _converted_unit_value(value: float | None, factor: float) -> float | None:
    if value is None:
        return None
    converted = value * factor
    rounded = round(converted)
    if abs(converted - rounded) < 0.000001:
        return float(rounded)
    return round(converted, 6)
