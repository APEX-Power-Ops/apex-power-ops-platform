from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from power_test_converters.dtax import build_dtax_tree
from power_test_converters.dtax import write_dtax
from power_test_converters.ptm import read_ptm


def test_read_ptm_extracts_transformer_and_power_factor(tmp_path: Path) -> None:
    ptm_path = _write_sample_ptm(tmp_path)

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
    assert len(model.winding_resistance_tests) == 1
    assert len(model.winding_resistance_tests[0].measurements) == 3
    assert model.winding_resistance_tests[0].temperature_correction_active is True
    assert model.winding_resistance_tests[0].winding_material == "Copper"
    assert model.winding_resistance_tests[0].measured_temperature_c == 20
    assert model.winding_resistance_tests[0].reference_temperature_c == 75
    assert len(model.exciting_current_tests) == 1
    assert len(model.exciting_current_tests[0].measurements) == 3
    assert model.overall_power_factor[0].measurement_name == "ICH"


def test_build_dtax_tree_emits_doble_shape_and_converted_units(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))

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

    test_conditions = root.find(
        "./dta-sessions/dta-session/two-winding-transformer/test-conditions"
    )
    assert test_conditions is not None
    assert test_conditions.attrib["internal-temp"] == "20"

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
    assert lv_ttr_ref.attrib["tapchanger-id"] == "00000000-0000-0000-0000-000000000000"
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


def test_generated_dtax_round_trips_as_xml(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))
    root = build_dtax_tree(model)
    ET.indent(root)
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    parsed = ET.fromstring(xml_bytes)

    assert parsed.find("Apparatus").text == "TwoWindingTransformer"


def test_generated_dtax_contains_no_converter_branding(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))
    root = build_dtax_tree(model)
    ET.indent(root)

    xml_text = ET.tostring(root, encoding="unicode").lower()

    forbidden_terms = ["ap" + "ex", "converter", "generated from", "omicron", "ptm"]
    for term in forbidden_terms:
        assert term not in xml_text


def test_template_mode_preserves_doble_skeleton(tmp_path: Path) -> None:
    model = read_ptm(_write_sample_ptm(tmp_path))
    template_path = _write_sample_template(tmp_path)
    output_path = tmp_path / "templated.dtax"

    write_dtax(model, output_path, template_path=template_path)
    parsed = ET.parse(output_path).getroot()

    nameplate = parsed.find("two-winding-transformer-nameplate")
    assert nameplate is not None
    assert nameplate.attrib["special-id"] == "XFM-1001"
    assert nameplate.attrib["serial-num"] == "45120269-001-08"
    assert "phases" not in nameplate.attrib
    assert "config" not in nameplate.attrib
    hv_details = nameplate.find("HVWindingDetails")
    assert hv_details is not None
    assert hv_details.attrib["Winding"] == "High"
    assert "WindingType" not in hv_details.attrib
    lv_details = nameplate.find("LVWindingDetails")
    assert lv_details is not None
    assert lv_details.attrib["Winding"] == "Low"
    assert "WindingType" not in lv_details.attrib
    tapchanger = nameplate.find("./tapchanger-nameplates/tapchanger-nameplate")
    assert tapchanger is None

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
    assert (
        parsed.find("./dta-sessions/dta-session/two-winding-transformer/bushing-test-set")
        is None
    )


def _write_sample_ptm(tmp_path: Path) -> Path:
    ptm_path = tmp_path / "sample.ptm"
    with zipfile.ZipFile(ptm_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr(
            "Assets/11111111-1111-1111-1111-111111111111.xml",
            _transformer_xml(
                "11111111-1111-1111-1111-111111111111",
                is_global="true",
                global_asset_id="",
            ),
        )
        package.writestr(
            "Assets/22222222-2222-2222-2222-222222222222.xml",
            _transformer_xml(
                "22222222-2222-2222-2222-222222222222",
                is_global="false",
                global_asset_id="11111111-1111-1111-1111-111111111111",
            ),
        )
        package.writestr(
            "Assets/33333333-3333-3333-3333-333333333333.xml",
            _bushing_xml(
                "33333333-3333-3333-3333-333333333333",
                "22222222-2222-2222-2222-222222222222",
                "45120269-001-08-H1",
                "0",
            ),
        )
        package.writestr(
            "Assets/44444444-4444-4444-4444-444444444444.xml",
            _bushing_xml(
                "44444444-4444-4444-4444-444444444444",
                "22222222-2222-2222-2222-222222222222",
                "45120269-001-08-X0",
                "7",
            ),
        )
        package.writestr(
            "Assets/55555555-5555-5555-5555-555555555555.xml",
            """
            <tTapChanger ExportId="55555555-5555-5555-5555-555555555555">
              <ParentAssetId>22222222-2222-2222-2222-222222222222</ParentAssetId>
              <SerialNumber>TC-1</SerialNumber>
              <Manufacturer>Square D</Manufacturer>
              <IsTapChangerEnabled>true</IsTapChangerEnabled>
            </tTapChanger>
            """,
        )
        package.writestr(
            "Substations/66666666-6666-6666-6666-666666666666.xml",
            """
            <tSubstation ExportId="66666666-6666-6666-6666-666666666666">
              <Name>Test Substation</Name>
              <Division>Phoenix</Division>
              <Region>North America</Region>
            </tSubstation>
            """,
        )
        package.writestr(
            "Jobs/77777777-7777-7777-7777-777777777777.xml",
            """
            <Job ExportId="77777777-7777-7777-7777-777777777777">
              <Name>XFM-1001</Name>
              <AssetId>11111111-1111-1111-1111-111111111111</AssetId>
              <JobAssetId>22222222-2222-2222-2222-222222222222</JobAssetId>
              <WorkOrder>559082</WorkOrder>
              <Tester>Austin Painter</Tester>
              <ApprovedBy>Jason Swenson</ApprovedBy>
              <Created>2025-01-09T17:50:36Z</Created>
            </Job>
            """,
        )
        package.writestr(
            "Tests/88888888-8888-8888-8888-888888888888.xml",
            _tan_delta_xml(),
        )
        package.writestr(
            "Tests/99999999-9999-9999-9999-999999999991.xml",
            _turns_ratio_xml(),
        )
        package.writestr(
            "Tests/99999999-9999-9999-9999-999999999992.xml",
            _winding_resistance_xml(),
        )
        package.writestr(
            "Tests/99999999-9999-9999-9999-999999999993.xml",
            _exciting_current_xml(),
        )
    return ptm_path


def _write_sample_template(tmp_path: Path) -> Path:
    template_path = tmp_path / "template.dtax"
    template_path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<DataModel-R2 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
  created-by-version="8.3.1.0010"
  modified-by-version="8.3.1.0010"
  xml-version="83"
  test-row-notes="InTestRowsOnly">
  <external-system-properties />
  <ApparatusType />
  <Apparatus>TwoWindingTransformer</Apparatus>
  <two-winding-transformer-nameplate serial-num="old" special-id="old">
    <bushing-nameplates />
    <arrester-nameplates />
    <winding-properties />
    <HVWindingDetails Winding="High" />
    <LVWindingDetails Winding="Low" />
    <TVWindingDetails Winding="Tertiary" />
    <leakage-reactance-nameplates />
    <tapchanger-nameplates no-tapchanger-confirmation="false" use-only-custom-tap-positions="false" />
    <physical-layout />
  </two-winding-transformer-nameplate>
  <dta-sessions>
    <dta-session company="TemplateCo" location="Template Location" cct-designation="old">
      <two-winding-transformer>
        <admin-data wo="old" LineFrequency="Custom" />
        <test-admin-data />
        <test-conditions />
        <m7-bushing-test-set />
        <exciting-current-test-set>
          <exciting-current-test include-in-plot="true" />
        </exciting-current-test-set>
        <bushing-designations />
        <arresters />
        <surge-arrester-test-set />
        <hot-collar-test-set />
        <insulatingfluid-test-set />
        <diagnostic-test-set />
        <configurable-powerfactor-test-set />
        <turns-ratio-test-set />
        <winding-resistance-test-set />
        <winding-resistance-winding-detail />
        <m7winding-resistance-tests-winding-1 />
        <m7winding-resistance-tests-winding-2 />
        <demagnetization-test-set />
        <dfr-test-set />
        <vflr-test-set />
        <fds-test-set />
        <overall-vfpf-test-set>
          <vfpf-test line-id="1" insulation="CH" />
        </overall-vfpf-test-set>
        <kneepoint-test-set />
        <ezct-test-set />
        <manual-data />
        <water-content />
        <tapchangers />
        <insulating-fluid-oil-quality-set />
        <dobledc-test-set />
        <dissolved-gas />
        <turns-ratio-connections />
        <turns-ratio-nameplate />
        <configurable-contact-resistance-test-set />
        <exciting-current-connections />
        <doble-ratio-test-set />
        <doble-ratio-cap-windings />
        <doble-ratio-connections />
        <lvttratio-test-set />
        <lvttratio-connections />
        <oltc-drm-test-set />
        <oltc-drm-connections />
        <transformer-layout />
        <gas-space />
        <leakage-reactance-3phase-test-set />
        <leakage-reactance-per-phase-hi-test-set />
        <leakage-reactance-per-phase-lo-test-set />
        <leakage-reactance-single-phase-test-set />
        <overall-test-set>
          <overall-test line-id="99" insulation="old" />
        </overall-test-set>
      </two-winding-transformer>
    </dta-session>
  </dta-sessions>
  <copyright-notice>template</copyright-notice>
</DataModel-R2>
""",
        encoding="utf-8",
    )
    return template_path


def _transformer_xml(export_id: str, is_global: str, global_asset_id: str) -> str:
    global_asset = f"<GlobalAssetId>{global_asset_id}</GlobalAssetId>" if global_asset_id else ""
    return f"""
    <Transformer ExportId="{export_id}">
      <SerialNumber>45120269-001-08</SerialNumber>
      <Manufacturer>Square D</Manufacturer>
      <ManufacturingYear>2023</ManufacturingYear>
      <ApparatusId>XFM-1001</ApparatusId>
      <RatedFrequency>60</RatedFrequency>
      <LocationId>66666666-6666-6666-6666-666666666666</LocationId>
      <Feeder>MSG-1001</Feeder>
      <NumberOfPhases>3</NumberOfPhases>
      <FluidVolume>2460.5176596</FluidVolume>
      <TotalWeight>7364.52571932</TotalWeight>
      <TankType>Sealed</TankType>
      <FluidType>NaturalEster</FluidType>
      {global_asset}
      <IsGlobalAsset>{is_global}</IsGlobalAsset>
      <PowerRatings>
        <PowerRating>
          <RatedPower unit="VA">3000000</RatedPower>
          <CoolingClass>BlankEntry</CoolingClass>
          <RatedCurrentPrimary unit="A">125.51</RatedCurrentPrimary>
          <RatedCurrentSecondary unit="A">3609</RatedCurrentSecondary>
        </PowerRating>
      </PowerRatings>
      <Windings>
        <Winding>
          <Winding>Primary</Winding>
          <VoltageLL unit="V">13800</VoltageLL>
          <InsulationLevelLL unit="V">110000</InsulationLevelLL>
          <VectorType>D</VectorType>
          <PhaseShift>NotSelected</PhaseShift>
        </Winding>
        <Winding>
          <Winding>Secondary</Winding>
          <VoltageLL unit="V">480</VoltageLL>
          <VoltageLN unit="V">277.128</VoltageLN>
          <InsulationLevelLL unit="V">45000</InsulationLevelLL>
          <VectorType>YN</VectorType>
          <PhaseShift>_1</PhaseShift>
        </Winding>
      </Windings>
      <Bushings>
        <BushingId>33333333-3333-3333-3333-333333333333</BushingId>
        <BushingId>44444444-4444-4444-4444-444444444444</BushingId>
      </Bushings>
    </Transformer>
    """


def _bushing_xml(export_id: str, parent_id: str, serial: str, position: str) -> str:
    return f"""
    <Bushing ExportId="{export_id}">
      <SerialNumber>{serial}</SerialNumber>
      <ParentAssetId>{parent_id}</ParentAssetId>
      <ManufacturingYear>0</ManufacturingYear>
      <Position>{position}</Position>
      <InsulationType>SelectInsulationType</InsulationType>
    </Bushing>
    """


def _tan_delta_xml() -> str:
    return """
    <TanDeltaTest ExportId="88888888-8888-8888-8888-888888888888">
      <TestId>test-1</TestId>
      <AssetId>22222222-2222-2222-2222-222222222222</AssetId>
      <ExecutionDate>2025-01-13T14:55:55Z</ExecutionDate>
      <Name>Overall PF &amp; CAP</Name>
      <CorrectionFactor>1</CorrectionFactor>
      <Grade>Normal</Grade>
      <Measurements>
        <Measurement>
          <MeasuredDate>2025-01-13T14:37:47Z</MeasuredDate>
          <MeasurementType>Measurement</MeasurementType>
          <TransformerWinding>Primary</TransformerWinding>
          <TransformerOverallCapacitance>Ich</TransformerOverallCapacitance>
          <Mode>GstGa</Mode>
          <Name>ICH</Name>
          <CorrectionFactor>1</CorrectionFactor>
          <MeasurementPoints>
            <MeasurementPoint>
              <TestFrequency>60</TestFrequency>
              <TestVoltage>7000</TestVoltage>
              <VoltageOut>6999.5</VoltageOut>
              <CurrentMeasured>0.004</CurrentMeasured>
              <CurrentCorrected>0.0057</CurrentCorrected>
              <CapacitanceMeasured>1.5E-09</CapacitanceMeasured>
              <WattLosses>0.13</WattLosses>
              <PowerFactorMeasured>0.23</PowerFactorMeasured>
              <PowerFactorCorrected>0.24</PowerFactorCorrected>
            </MeasurementPoint>
          </MeasurementPoints>
        </Measurement>
        <Measurement>
          <MeasuredDate>2025-01-13T14:42:18Z</MeasuredDate>
          <MeasurementType>Measurement</MeasurementType>
          <TransformerWinding>Primary</TransformerWinding>
          <TransformerOverallCapacitance>Ichl</TransformerOverallCapacitance>
          <Mode>UstA</Mode>
          <Name>ICHL</Name>
          <MeasurementPoints>
            <MeasurementPoint>
              <TestFrequency>60</TestFrequency>
              <TestVoltage>7000</TestVoltage>
              <VoltageOut>7000</VoltageOut>
              <CurrentMeasured>0.009</CurrentMeasured>
              <CapacitanceMeasured>3.5E-09</CapacitanceMeasured>
              <WattLosses>0.85</WattLosses>
              <PowerFactorMeasured>0.64</PowerFactorMeasured>
              <PowerFactorCorrected>0.65</PowerFactorCorrected>
            </MeasurementPoint>
          </MeasurementPoints>
        </Measurement>
        <Measurement>
          <MeasuredDate>2025-01-13T15:19:35Z</MeasuredDate>
          <MeasurementType>Measurement</MeasurementType>
          <TransformerWinding>Primary</TransformerWinding>
          <TransformerOverallCapacitance>NullValue</TransformerOverallCapacitance>
          <Mode>UstA</Mode>
          <Name>H1</Name>
          <MeasurementPoints>
            <MeasurementPoint>
              <TestFrequency>60</TestFrequency>
              <TestVoltage>12000</TestVoltage>
              <VoltageOut>12000</VoltageOut>
              <CurrentMeasured>4.2E-05</CurrentMeasured>
              <CapacitanceMeasured>9.4E-12</CapacitanceMeasured>
              <WattLosses>0.007</WattLosses>
              <PowerFactorMeasured>1.5</PowerFactorMeasured>
              <PowerFactorCorrected>1.5</PowerFactorCorrected>
            </MeasurementPoint>
          </MeasurementPoints>
        </Measurement>
      </Measurements>
    </TanDeltaTest>
    """


def _turns_ratio_xml() -> str:
    return """
    <TTSTTRTest ExportId="99999999-9999-9999-9999-999999999991">
      <TestId>ttr-1</TestId>
      <AssetId>22222222-2222-2222-2222-222222222222</AssetId>
      <ExecutionDate>2025-01-13T14:07:26Z</ExecutionDate>
      <Name>TTR H-X</Name>
      <Settings>
        <TestVoltage>120</TestVoltage>
        <TestFrequency>60</TestFrequency>
      </Settings>
      <Measurements>
        <tTTSTTRMeasurement>
          <MeasuredDate>2025-01-13T14:07:26Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseA</Phase>
          <TapIndex>0</TapIndex>
          <NominalRatioVTR>28.75</NominalRatioVTR>
          <VoltageTurnsRatio>28.74</VoltageTurnsRatio>
          <RatioDeviation>-0.03</RatioDeviation>
          <VPrim>120</VPrim>
          <VSec>4.17333333333333</VSec>
          <VPhase>30</VPhase>
        </tTTSTTRMeasurement>
        <tTTSTTRMeasurement>
          <MeasuredDate>2025-01-13T14:07:25Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseB</Phase>
          <TapIndex>0</TapIndex>
          <NominalRatioVTR>28.75</NominalRatioVTR>
          <VoltageTurnsRatio>28.76</VoltageTurnsRatio>
          <RatioDeviation>0.03</RatioDeviation>
          <VPrim>120</VPrim>
          <VSec>4.17333333333333</VSec>
          <VPhase>30</VPhase>
        </tTTSTTRMeasurement>
        <tTTSTTRMeasurement>
          <MeasuredDate>2025-01-13T14:07:24Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseC</Phase>
          <TapIndex>0</TapIndex>
          <NominalRatioVTR>28.75</NominalRatioVTR>
          <VoltageTurnsRatio>28.75</VoltageTurnsRatio>
          <RatioDeviation>0</RatioDeviation>
          <VPrim>120</VPrim>
          <VSec>4.17333333333333</VSec>
          <VPhase>30</VPhase>
        </tTTSTTRMeasurement>
      </Measurements>
    </TTSTTRTest>
    """


def _winding_resistance_xml() -> str:
    return """
    <TTSWindingResistanceTest ExportId="99999999-9999-9999-9999-999999999992">
      <TestId>wr-1</TestId>
      <AssetId>22222222-2222-2222-2222-222222222222</AssetId>
      <ExecutionDate>2025-01-13T14:19:14Z</ExecutionDate>
      <Name>DC Winding Resistance H</Name>
      <Settings>
        <OutputSide>OutputSide_HV</OutputSide>
        <TestCurrent>10</TestCurrent>
        <TemperatureCorrectionActive>true</TemperatureCorrectionActive>
        <WindingMaterial>Copper</WindingMaterial>
        <MeasTemp unit="C">20</MeasTemp>
        <RefTemp unit="C">75</RefTemp>
        <CorrectionFactor>1.2</CorrectionFactor>
      </Settings>
      <Measurements>
        <tTTSWindingResistanceMeasurement>
          <MeasuredDate>2025-01-13T14:19:14Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseA</Phase>
          <TapIndex>0</TapIndex>
          <ResistanceMeasured>0.22</ResistanceMeasured>
          <ResistanceCorrected>0.26</ResistanceCorrected>
          <ResistanceDeviation>0.01</ResistanceDeviation>
          <IDC>10</IDC>
          <VDC>2.2</VDC>
          <VDCCorrected>2.2</VDCCorrected>
        </tTTSWindingResistanceMeasurement>
        <tTTSWindingResistanceMeasurement>
          <MeasuredDate>2025-01-13T14:18:40Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseB</Phase>
          <TapIndex>0</TapIndex>
          <ResistanceMeasured>0.23</ResistanceMeasured>
          <ResistanceCorrected>0.27</ResistanceCorrected>
          <ResistanceDeviation>0.01</ResistanceDeviation>
          <IDC>10</IDC>
          <VDC>2.3</VDC>
          <VDCCorrected>2.3</VDCCorrected>
        </tTTSWindingResistanceMeasurement>
        <tTTSWindingResistanceMeasurement>
          <MeasuredDate>2025-01-13T14:18:03Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseC</Phase>
          <TapIndex>0</TapIndex>
          <ResistanceMeasured>0.24</ResistanceMeasured>
          <ResistanceCorrected>0.28</ResistanceCorrected>
          <ResistanceDeviation>0.01</ResistanceDeviation>
          <IDC>10</IDC>
          <VDC>2.4</VDC>
          <VDCCorrected>2.4</VDCCorrected>
        </tTTSWindingResistanceMeasurement>
      </Measurements>
    </TTSWindingResistanceTest>
    """


def _exciting_current_xml() -> str:
    return """
    <TTSHVExcitingCurrentTest ExportId="99999999-9999-9999-9999-999999999993">
      <TestId>exc-1</TestId>
      <AssetId>22222222-2222-2222-2222-222222222222</AssetId>
      <ExecutionDate>2025-01-13T15:14:51Z</ExecutionDate>
      <Name>Exciting Current</Name>
      <Settings>
        <TestVoltage>7000</TestVoltage>
        <TestFrequency>60</TestFrequency>
      </Settings>
      <Measurements>
        <tTTSHVExcitingCurrentMeasurement>
          <MeasuredDate>2025-01-13T15:14:51Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseA</Phase>
          <TapIndex>0</TapIndex>
          <VOut>7000</VOut>
          <IOut>0.05</IOut>
          <IOutCorrected>0.05</IOutCorrected>
          <WattLosses>280</WattLosses>
        </tTTSHVExcitingCurrentMeasurement>
        <tTTSHVExcitingCurrentMeasurement>
          <MeasuredDate>2025-01-13T15:14:50Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseB</Phase>
          <TapIndex>0</TapIndex>
          <VOut>7000</VOut>
          <IOut>0.06</IOut>
          <IOutCorrected>0.06</IOutCorrected>
          <WattLosses>290</WattLosses>
        </tTTSHVExcitingCurrentMeasurement>
        <tTTSHVExcitingCurrentMeasurement>
          <MeasuredDate>2025-01-13T15:14:49Z</MeasuredDate>
          <Assessment>Pass</Assessment>
          <Name>1</Name>
          <Phase>PhaseC</Phase>
          <TapIndex>0</TapIndex>
          <VOut>7000</VOut>
          <IOut>0.07</IOut>
          <IOutCorrected>0.07</IOutCorrected>
          <WattLosses>300</WattLosses>
        </tTTSHVExcitingCurrentMeasurement>
      </Measurements>
    </TTSHVExcitingCurrentTest>
    """
