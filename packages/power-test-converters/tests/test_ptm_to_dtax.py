from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from power_test_converters.dtax import build_dtax_tree
from power_test_converters.dtax import write_dtax
from power_test_converters.ptm import read_ptm
from power_test_converters.testing import write_sample_ptm, write_sample_template


def test_read_ptm_extracts_transformer_and_power_factor(tmp_path: Path) -> None:
    ptm_path = write_sample_ptm(tmp_path)

    model = read_ptm(ptm_path)

    assert model.transformer.source_id == "22222222-2222-2222-2222-222222222222"
    assert model.transformer.apparatus_id == "XFM-1001"
    assert model.transformer.manufacturer == "Square D"
    assert model.transformer.power_ratings[0].rated_power_va == 3_000_000
    assert [w.name for w in model.transformer.windings] == ["Primary", "Secondary"]
    assert [b.designation for b in model.bushings] == ["H1", "X0"]
    assert len(model.overall_power_factor) == 2
    assert len(model.bushing_power_factor) == 1
    assert len(model.turns_ratio_tests) == 1
    assert len(model.turns_ratio_tests[0].measurements) == 3
    assert model.turns_ratio_tests[0].instrument is not None
    assert model.turns_ratio_tests[0].instrument.test_set_name == "TESTRANO 600"
    assert model.turns_ratio_tests[0].instrument.serial_number == "GH733Y"
    assert len(model.winding_resistance_tests) == 1
    assert len(model.winding_resistance_tests[0].measurements) == 3
    assert model.winding_resistance_tests[0].temperature_correction_active is True
    assert model.winding_resistance_tests[0].winding_material == "Copper"
    assert model.winding_resistance_tests[0].measured_temperature_c == 20
    assert model.winding_resistance_tests[0].reference_temperature_c == 75
    assert len(model.exciting_current_tests) == 1
    assert len(model.exciting_current_tests[0].measurements) == 3
    assert len(model.demagnetization_tests) == 1
    assert len(model.demagnetization_tests[0].measurements) == 1
    assert model.demagnetization_tests[0].measurements[0].status == "DemagStatus_Passed"
    assert model.demagnetization_tests[0].measurements[0].resistance_ohm == 0.378
    assert model.overall_power_factor[0].measurement_name == "ICH"


def test_build_dtax_tree_emits_doble_shape_and_converted_units(tmp_path: Path) -> None:
    model = read_ptm(write_sample_ptm(tmp_path))

    root = build_dtax_tree(model)

    assert root.tag == "DataModel-R2"
    nameplate = root.find("two-winding-transformer-nameplate")
    assert nameplate is not None
    assert nameplate.attrib["serial-num"] == "45120269-001-08"
    assert nameplate.attrib["Va-0"] == "3000"
    assert nameplate.attrib["kV-0"] == "13.8"
    assert nameplate.attrib["kV-1"] == "0.48"
    assert nameplate.attrib["config"] == "D_Y"
    winding_properties = nameplate.find("winding-properties")
    assert winding_properties is not None
    assert winding_properties.attrib["winding-material"] == "Copper"
    assert winding_properties.attrib["temperature-rise"] == "75"
    tapchanger = nameplate.find("./tapchanger-nameplates/tapchanger-nameplate")
    assert tapchanger is not None
    assert tapchanger.attrib["id"] == "55555555-5555-5555-5555-555555555555"
    assert tapchanger.attrib["tapchanger-type"] == "DETC"
    assert tapchanger.attrib["winding"] == "High"
    assert tapchanger.attrib["description"] == "DETC"

    test_conditions = root.find(
        "./dta-sessions/dta-session/two-winding-transformer/test-conditions"
    )
    assert test_conditions is not None
    assert test_conditions.attrib["internal-temp"] == "20"

    test_admin_rows = root.findall(
        "./dta-sessions/dta-session/two-winding-transformer/test-admin-data/admin-data"
    )
    assert [row.attrib["test-name"] for row in test_admin_rows] == [
        "TwoWindingOverall",
        "Bushings",
        "ExcitingCurrent",
        "LVTTR",
        "M7WindingResistance",
        "Demagnetization",
    ]
    assert all(row.attrib["test-set-type"] == "Undefined" for row in test_admin_rows)
    assert {row.attrib["bottom-sn"] for row in test_admin_rows} == {"TESTRANO 600"}
    assert {row.attrib["top_sn"] for row in test_admin_rows} == {"GH733Y"}

    bushing_designations = root.findall(
        "./dta-sessions/dta-session/two-winding-transformer/"
        "bushing-designations/bushing"
    )
    assert [item.attrib["designation"] for item in bushing_designations] == ["H1", "X0"]

    rows = root.findall(
        "./dta-sessions/dta-session/two-winding-transformer/"
        "overall-test-set/overall-test"
    )
    assert len(rows) == 2
    first = rows[0].attrib
    assert first["insulation"] == "CH"
    assert first["test-circuit"] == "CIRC_GAR_RB"
    assert first["requested-test-kV"] == "7"
    assert first["test-kV"] == "6.9995"
    assert first["mA"] == "4"
    assert first["measured-cap"] == "1500"
    assert first["pfm"] == "0.23"

    bushing_test = root.find(".//m7-bushing-test")
    assert bushing_test is not None
    assert bushing_test.attrib["bushing-id"] == "33333333-3333-3333-3333-333333333333"
    bushing_result = bushing_test.find("./bushing-test-results-set/bushing-test-results")
    assert bushing_result is not None
    assert bushing_result.attrib["test-circuit"] == "CIRC_UST_RB"
    assert bushing_result.attrib["bushing-insulation"] == "C1"
    assert bushing_result.attrib["requested-test-kV"] == "12"
    assert bushing_result.attrib["mA"] == "0.042"
    assert bushing_result.attrib["measured-cap"] == "9.4"
    assert bushing_test.find("./bushing-vfpf-test-set/vfpf-test") is not None

    assert len(root.findall(".//turns-ratio-test")) == 0
    lv_ttr = root.find(".//lvttratio-test")
    assert lv_ttr is not None
    assert lv_ttr.attrib["label"] == "H-X"
    lv_ttr_fields = lv_ttr.find("ratio-test-fields")
    assert lv_ttr_fields is not None
    assert lv_ttr_fields.attrib["detc-id"] == "00000000-0000-0000-0000-000000000000"
    assert lv_ttr_fields.attrib["benchmark-ratio"] == "28.75"
    assert lv_ttr_fields.attrib["hv-volt"] == "13.8"
    assert lv_ttr_fields.attrib["lv-volt"] == "0.48"
    assert lv_ttr_fields.attrib["ratio-1"] == "28.74"
    assert lv_ttr_fields.attrib["deviation-1"] == "-0.03"
    assert lv_ttr_fields.attrib["angle-1"] == "30"
    lv_ttr_ref = lv_ttr_fields.find("./tc-references/tc-reference-set/tc-reference")
    assert lv_ttr_ref is not None
    assert lv_ttr_ref.attrib["tapchanger-id"] == "55555555-5555-5555-5555-555555555555"
    assert lv_ttr.find("cablestates") is not None
    exciting = root.find(".//exciting-current-test")
    assert exciting is not None
    assert exciting.attrib["detc"] == "0"
    exciting_fields = exciting.find("exciting-current-fields")
    assert exciting_fields is not None
    assert exciting_fields.attrib["winding-tap"] == ""
    assert exciting_fields.attrib["FrequencyPCT1"] == "FREQ_5PCT"
    line_freq = exciting.find("linefreq-test-voltages")
    assert line_freq is not None
    assert line_freq.find("m_dHighFreqkV").text == "-1.7976931348623157E+308"
    connections = root.find(".//exciting-current-connections")
    assert connections is not None
    assert [connections.attrib[f"conn-{i}"] for i in range(1, 7)] == [
        "H1",
        "H3",
        "H2",
        "H1",
        "H3",
        "H2",
    ]
    assert len(root.findall(".//m7winding-resistance-test")) == 1
    winding_resistance = root.find(".//m7winding-resistance-test")
    assert winding_resistance is not None
    assert winding_resistance.attrib["include-in-plot"] == "true"
    winding_resistance_connections = root.find(".//m7winding-resistance-connections")
    assert winding_resistance_connections is not None
    assert [winding_resistance_connections.attrib[f"conn-{i}"] for i in range(1, 7)] == [
        "H1",
        "H2",
        "H2",
        "H3",
        "H3",
        "H1",
    ]
    winding_resistance_fields = root.find(".//winding-resistance-fields")
    assert winding_resistance_fields is not None
    assert (
        winding_resistance_fields.attrib["test-circuit-1"]
        == "EDC_LV3__MDV_LV1__EG_LV1__FLT_LV2"
    )
    assert winding_resistance_fields.attrib["corr-factor1"] == "1.2"
    assert winding_resistance_fields.attrib["calculated-resistance1"] == "0.22"
    assert winding_resistance_fields.attrib["corrected-resistance1"] == "0.26"
    assert winding_resistance_fields.attrib["spread-ab"] == "1"

    demag_connections = root.find(".//demagnetization-connections")
    assert demag_connections is not None
    assert demag_connections.attrib["demag-energize-lead-1"] == "LV3"
    assert demag_connections.attrib["demag-measure-lead-1"] == "LV1"
    demag_fields = root.find(".//demagnetization-demag-test")
    assert demag_fields is not None
    assert demag_fields.attrib["date-tested-utc"] == "2025-01-13 14:26:11"
    assert demag_fields.attrib["phase-a-test-completed"] == "true"
    assert demag_fields.attrib["current-c"] == "0.378"


def test_generated_dtax_round_trips_as_xml(tmp_path: Path) -> None:
    model = read_ptm(write_sample_ptm(tmp_path))
    root = build_dtax_tree(model)
    ET.indent(root)
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    parsed = ET.fromstring(xml_bytes)

    assert parsed.find("Apparatus").text == "TwoWindingTransformer"


def test_generated_dtax_contains_no_converter_branding(tmp_path: Path) -> None:
    model = read_ptm(write_sample_ptm(tmp_path))
    root = build_dtax_tree(model)
    ET.indent(root)

    xml_text = ET.tostring(root, encoding="unicode").lower()

    forbidden_terms = ["ap" + "ex", "converter", "generated from", "omicron", "ptm"]
    for term in forbidden_terms:
        assert term not in xml_text


def test_template_mode_preserves_doble_skeleton(tmp_path: Path) -> None:
    model = read_ptm(write_sample_ptm(tmp_path))
    template_path = write_sample_template(tmp_path)
    output_path = tmp_path / "templated.dtax"

    write_dtax(model, output_path, template_path=template_path)
    parsed = ET.parse(output_path).getroot()

    nameplate = parsed.find("two-winding-transformer-nameplate")
    assert nameplate is not None
    assert nameplate.attrib["special-id"] == "XFM-1001"
    assert nameplate.attrib["serial-num"] == "45120269-001-08"
    assert nameplate.attrib["phases"] == "Three"
    assert nameplate.attrib["config"] == "D_Y"
    assert "class" not in nameplate.attrib
    assert nameplate.attrib["coolant"] == "FR3"
    assert nameplate.attrib["tanktype"] == "N2BLANKETED"
    assert nameplate.attrib["kV-0"] == "13.8"
    assert nameplate.attrib["kV-1"] == "0.48"
    assert nameplate.attrib["Va-0"] == "3000"
    assert nameplate.attrib["Va-1"] == "3000"
    assert nameplate.attrib["Va-2"] == "3000"
    assert nameplate.attrib["Va-3"] == "3000"
    assert nameplate.attrib["BIL"] == "110"
    assert nameplate.attrib["oil-volume"] == "650"
    assert nameplate.attrib["weight"] == "16236"
    assert nameplate.attrib["HVWindingLine"] == "LineToLine"
    assert nameplate.attrib["LVWindingLine"] == "LineToLine"
    hv_details = nameplate.find("HVWindingDetails")
    assert hv_details is not None
    assert hv_details.attrib["Winding"] == "High"
    assert hv_details.attrib["WindingType"] == "Delta"
    lv_details = nameplate.find("LVWindingDetails")
    assert lv_details is not None
    assert lv_details.attrib["Winding"] == "Low"
    assert lv_details.attrib["WindingType"] == "Wye"
    tapchanger = nameplate.find("./tapchanger-nameplates/tapchanger-nameplate")
    assert tapchanger is not None
    assert tapchanger.attrib["id"] == "55555555-5555-5555-5555-555555555555"
    assert tapchanger.attrib["tapchanger-type"] == "DETC"
    assert tapchanger.attrib["winding"] == "High"
    assert tapchanger.attrib["description"] == "DETC"
    assert tapchanger.attrib["mfr"] == "Square D"
    assert tapchanger.attrib["tapchanger-serial-num"] == "TC-1"
    assert tapchanger.attrib["int-steps"] == "1"
    assert tapchanger.attrib["steps-up"] == "0"
    assert tapchanger.attrib["steps-down"] == "0"
    assert tapchanger.attrib["neutral-positions"] == "1"

    session = parsed.find("./dta-sessions/dta-session")
    assert session is not None
    assert session.attrib["cct-designation"] == "XFM-1001"
    assert session.attrib["company"] == "TemplateCo"
    assert session.attrib["location"] == "Template Location"

    admin = parsed.find("./dta-sessions/dta-session/two-winding-transformer/admin-data")
    assert admin is not None
    assert admin.attrib["wo"] == "old"
    assert admin.attrib["LineFrequency"] == "Custom"
    test_conditions = parsed.find(
        "./dta-sessions/dta-session/two-winding-transformer/test-conditions"
    )
    assert test_conditions is not None
    assert test_conditions.attrib["internal-temp"] == "20"

    retained_default = parsed.find(
        "./dta-sessions/dta-session/two-winding-transformer/"
        "overall-vfpf-test-set/vfpf-test"
    )
    assert retained_default is not None
    assert retained_default.attrib["line-id"] == "1"

    rows = parsed.findall(
        "./dta-sessions/dta-session/two-winding-transformer/"
        "overall-test-set/overall-test"
    )
    assert len(rows) == 2
    assert rows[0].attrib["insulation"] == "CH"
    assert len(parsed.findall(".//turns-ratio-test")) == 0
    assert len(parsed.findall(".//lvttratio-test")) == 1
    assert len(parsed.findall(".//exciting-current-test")) == 1
    assert len(parsed.findall(".//m7-bushing-test")) == 0
    assert len(parsed.findall(".//m7winding-resistance-test")) == 1
    assert len(parsed.findall(".//test-admin-data/admin-data")) == 6
    assert {
        ref.attrib["tapchanger-id"]
        for ref in parsed.findall(".//tc-reference")
        if ref.attrib.get("tapchanger-type") == "DETC"
    } == {"55555555-5555-5555-5555-555555555555"}
    assert (
        parsed.find("./dta-sessions/dta-session/two-winding-transformer/bushing-test-set")
        is None
    )

