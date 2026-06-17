#!/usr/bin/env python3
"""Generate 018_motor_templates.sql - the Rotating-Machinery datasheets (NETA 7.15).

Three leaf-bound single-procedure sheets (the largest family; the clean recipe, one leaf/procedure):
  - ats_induction_motor_v1     -> rm_induction;   7.15.1; 27 ATS (11 VM + 16 elec).
  - ats_synchronous_machine_v1 -> rm_synchronous; 7.15.2; 37 ATS (11 VM + 26 elec).
  - ats_dc_machine_v1          -> rm_dc;          7.15.3; 20 ATS (10 VM + 10 elec).

NOT PowerDB-anchored (no motor form in the corpus) -> NETA-derived. R-A: rotating machinery tests to
IEEE 43 (IR/PI) / NEMA MG 1 (hipot) / mfr data, not a NETA acceptance table -> `mfr` only (torque ->
Table 100.12 stays a VM acceptance basis). Never tcc. Capture = field + cover_attach (no motor bridge).

Coverage invariant (fail-fast here, re-checked in test_018): per sheet, union of section neta_covers
covers all the procedure's ATS visual_mechanical+electrical items.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_motor_template.py [path-to-json]
"""
import copy
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
OUT = os.path.join(HERE, "018_motor_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
IND_ID = str(uuid.uuid5(NS_TPL, "ats_induction_motor_v1"))
SYN_ID = str(uuid.uuid5(NS_TPL, "ats_synchronous_machine_v1"))
DC_ID = str(uuid.uuid5(NS_TPL, "ats_dc_machine_v1"))
IND_SEC, SYN_SEC, DC_SEC = "7.15.1", "7.15.2", "7.15.3"
COND = ["sat", "unsat", "na"]
PF = ["pass", "fail"]
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat A=visual_mechanical / B=electrical, item_no, optional, section_key)
IND_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("components", "Inspect baffles, filters, stator winding/core, rotor, fans, slip rings, brushes, bearings", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.15.1.B.1)", "A", 5, False, "visual_mechanical"),
    ("air_gap", "Special tests: air-gap spacing and machine alignment", "A", 6, True, "visual_mechanical"),
    ("manual_rotor", "Manually rotate the rotor; check bearings / shaft", "A", 7, True, "visual_mechanical"),
    ("shaft_runout", "Measure and record shaft extension runout", "A", 8, True, "visual_mechanical"),
    ("lubrication", "Verify lubrication and lubrication systems", "A", 9, False, "visual_mechanical"),
    ("rtd_conform", "RTD circuits conform to drawings", "A", 10, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Insulation-resistance test (IEEE Std 43; IR + PI)", "B", 2, False, "insulation_resistance"),
    ("dielectric", "Dielectric withstand (machines >= 2300 V)", "B", 3, False, "dielectric_withstand"),
    ("stator_r", "Phase-to-phase stator resistance (machines >= 2300 V)", "B", 4, False, "winding_resistance"),
    ("pf_df", "Insulation power-factor / dissipation-factor test", "B", 5, True, "power_factor"),
    ("pf_tipup", "PF / DF tip-up test", "B", 6, True, "power_factor"),
    ("surge", "Surge comparison test", "B", 7, True, "surge_comparison"),
    ("bearing_ir", "IR test on insulated bearings (mfr data)", "B", 8, False, "insulation_resistance"),
    ("spd", "Test surge protection devices (Sections 7.19 / 7.20)", "B", 9, False, "protective_devices"),
    ("starter", "Test motor starter (Section 7.16)", "B", 10, False, "protective_devices"),
    ("rtd_r", "Resistance tests on RTD circuits", "B", 11, False, "auxiliary"),
    ("space_heater", "Verify operation of machine space heater", "B", 12, False, "auxiliary"),
    ("vibration", "Vibration test while running under load", "B", 13, True, "running_tests"),
    ("bearing_temp", "Measure bearing temperatures while running under load", "B", 14, True, "running_tests"),
    ("csa", "Current signature analysis while running under load", "B", 15, True, "running_tests"),
    ("pd", "Partial discharge test", "B", 16, True, "running_tests"),
]

SYN_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("components", "Inspect baffles, filters, stator windings/core, rotor, fans, slip rings, brushes, bearings", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.15.2.B.1)", "A", 5, False, "visual_mechanical"),
    ("air_gap", "Special tests: air-gap spacing and machine alignment", "A", 6, False, "visual_mechanical"),
    ("manual_rotor", "Manually rotate the rotor; check bearings / shaft", "A", 7, False, "visual_mechanical"),
    ("shaft_runout", "Measure and record shaft extension runout", "A", 8, False, "visual_mechanical"),
    ("lubrication", "Verify lubrication and lubrication systems", "A", 9, False, "visual_mechanical"),
    ("rtd_conform", "RTD circuits conform to drawings", "A", 10, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Stator insulation-resistance test (IEEE Std 43; IR + PI)", "B", 2, False, "insulation_resistance"),
    ("dielectric", "Dielectric withstand (machines >= 2300 V)", "B", 3, False, "dielectric_withstand"),
    ("stator_r", "Phase-to-phase stator resistance (machines >= 2300 V)", "B", 4, False, "winding_resistance"),
    ("pf_df", "Insulation power-factor / dissipation-factor test", "B", 5, True, "power_factor"),
    ("pf_tipup", "PF / DF tip-up test", "B", 6, True, "power_factor"),
    ("surge", "Surge comparison test", "B", 7, True, "surge_comparison"),
    ("bearing_ir", "IR test on insulated bearings (mfr data)", "B", 8, False, "insulation_resistance"),
    ("spd", "Test surge protection devices (Sections 7.19 / 7.20)", "B", 9, False, "protective_devices"),
    ("starter", "Test motor starter (Section 7.16)", "B", 10, False, "protective_devices"),
    ("rtd_r", "Resistance tests on RTD circuits", "B", 11, False, "auxiliary"),
    ("space_heater", "Verify operation of machine space heater", "B", 12, False, "auxiliary"),
    ("vibration", "Vibration test while running under load", "B", 13, True, "running_tests"),
    ("rotor_ir", "IR of rotating-field, exciter-field, exciter-armature windings (IEEE Std 43)", "B", 14, False, "insulation_resistance"),
    ("field_vdrop", "AC voltage-drop test on all rotating field poles", "B", 15, True, "field_excitation"),
    ("exc_hipot", "High-potential test on the excitation system (IEEE Std 421.3)", "B", 16, True, "field_excitation"),
    ("field_r", "Resistance of field / exciter windings and field discharge resistors", "B", 17, False, "winding_resistance"),
    ("diode_scr", "Front-to-back diode + SCR gating tests (field semiconductors)", "B", 18, True, "field_excitation"),
    ("exc_set", "Apply exciter supply; set exciter-field current to nameplate", "B", 19, False, "field_excitation"),
    ("field_timer", "Field-application + enable timers for PF relay tested and set", "B", 20, False, "field_excitation"),
    ("accel_record", "Record stator current / voltage / field current over the acceleration period", "B", 21, True, "field_excitation"),
    ("v_curve", "Plot V-curve (stator current vs excitation) at ~50% load", "B", 22, True, "field_excitation"),
    ("pf_relay", "Reduce excitation below PF-relay trip; verify relay operation", "B", 23, True, "field_excitation"),
    ("bearing_temp", "Measure bearing temperatures while running under load", "B", 24, False, "running_tests"),
    ("csa", "Current signature analysis while running under load", "B", 25, True, "running_tests"),
    ("pd", "Partial discharge test", "B", 26, True, "running_tests"),
]

DC_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("components", "Inspect baffles, filters, field poles/yokes, armature, fans, commutator, brushes, bearings", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.15.3.B.1)", "A", 5, False, "visual_mechanical"),
    ("commutator", "Inspect commutator and tachometer generator", "A", 6, False, "visual_mechanical"),
    ("special", "Special tests: air-gap spacing, commutator bar tightness, alignment", "A", 7, True, "visual_mechanical"),
    ("manual_rotate", "Manually rotate armature; check bearings / shaft", "A", 8, True, "visual_mechanical"),
    ("shaft_runout", "Measure and record shaft extension runout", "A", 9, True, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 10, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Insulation-resistance test on all windings (IEEE Std 43)", "B", 2, False, "insulation_resistance"),
    ("hipot", "High-potential test (NEMA MG 1, Section 3.01)", "B", 3, True, "dielectric_withstand"),
    ("field_vdrop", "AC voltage-drop test on all field poles", "B", 4, True, "field_excitation"),
    ("surge", "Surge (impulse) comparison test on field + armature winding", "B", 5, True, "field_excitation"),
    ("commutator_r", "Armature commutator bar-to-bar resistance test", "B", 6, True, "field_excitation"),
    ("field_polarity", "Shunt/series field relative polarity checked; leads marked", "B", 7, False, "field_excitation"),
    ("running_current", "Measure armature running current and field current/voltage vs nameplate", "B", 8, False, "running_tests"),
    ("vibration", "Vibration tests while running under load", "B", 9, True, "running_tests"),
    ("protective", "Verify protective devices (Section 7.16)", "B", 10, False, "protective_devices"),
]


def covers_by_sec(concepts, section_code):
    cov = {}
    for c in concepts:
        cov.setdefault(c[5], set()).add(f"{section_code}.{c[2]}.{c[3]}")
    return cov


def vm_section(concepts, section_code):
    rows = []
    for c in concepts:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_ref": f"{section_code}.{c[2]}.{c[3]}"}
        if c[4]:
            r["optional"] = True
        rows.append(r)
    return {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
            "neta_basis": section_code,
            "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
                      "columns": [ctl("inspected", "Inspected", "boolean"),
                                  ctl("condition", "Condition", "selection", options=COND),
                                  ctl("value", "Value", "text"), ctl("note", "Note", "text")]}}


def nameplate(extra):
    base = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("type_frame", "Type / frame", "text", "inherited"),
        ctl("rating_hp", "Rating (HP / kW)", "numeric", "inherited"),
        ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
        ctl("rpm", "Speed", "numeric", "inherited", unit="rpm"),
        ctl("fla", "Full-load amps", "numeric", "inherited", unit="A"),
        ctl("insulation_class", "Insulation class", "text", "inherited"),
    ]
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
            "fields": base + extra + [ctl("nameplate_vs_drawings", "Nameplate data compared with drawings",
                                          "selection", "data", options=COND)]}


def ir_section(extra):
    # the IR / PI section is the mfr (IEEE 43) acceptance slot on every motor sheet.
    return {"key": "insulation_resistance", "title": "Insulation Resistance (IEEE Std 43)", "kind": "fields",
            "fields": [ctl("test_voltage", "Test voltage", "numeric", "data", unit="V"),
                       ctl("ir_1min_mohm", "IR @ 1 min", "numeric", "data", unit="Mohm",
                           acceptance={"basis": "ieee_43", "note": "min IR = kV + 1 Mohm (IEEE 43)"},
                           tolerance_source={"engine": "mfr", "function": "insulation_resistance",
                                             "inputs": ["voltage_rating", "insulation_class"]}),
                       ctl("polarization_index", "Polarization index (10/1 min)", "numeric", "data",
                           acceptance={"basis": "ieee_43"}),
                       ctl("equip_temp", "Winding temp", "numeric", "data", unit="degC")] + extra}


def simple(key, title, fields):
    return {"key": key, "title": title, "kind": "fields", "fields": fields}


BOLTED = simple("bolted_resistance", "Bolted-Connection Resistance",
                [ctl("resistance_uohm", "Resistance (low-resistance ohmmeter)", "numeric", "data", unit="uohm",
                     acceptance={"basis": "comparison"}),
                 ctl("result", "Within tolerance", "selection", "data", options=COND)])
DIELECTRIC = simple("dielectric_withstand", "Dielectric Withstand / High-Potential",
                    [ctl("method", "Method", "selection", "data", options=["ac", "dc", "vlf"]),
                     ctl("test_kv", "Test voltage", "numeric", "data", unit="kV",
                         acceptance={"basis": "mfr_tolerance", "note": "IEEE / NEMA MG 1"},
                         tolerance_source={"engine": "mfr", "function": "dielectric_withstand",
                                           "inputs": ["voltage_rating"]}),
                     ctl("duration_min", "Duration", "numeric", "data", unit="min"),
                     ctl("result", "Result", "selection", "data", options=PF)])
WINDING_R = simple("winding_resistance", "Winding Resistance",
                   [ctl("phase_ab", "R(A-B)", "numeric", "data", unit="ohm"),
                    ctl("phase_bc", "R(B-C)", "numeric", "data", unit="ohm"),
                    ctl("phase_ca", "R(C-A)", "numeric", "data", unit="ohm"),
                    ctl("imbalance_pct", "Imbalance", "numeric", "data", unit="pct",
                        acceptance={"basis": "mfr_tolerance"},
                        tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                          "inputs": ["manufacturer", "model"]}),
                    ctl("temp", "Winding temp", "numeric", "data", unit="degC")])
POWER_FACTOR = simple("power_factor", "Power Factor / Dissipation Factor",
                      [ctl("pf_pct", "PF / DF", "numeric", "data", unit="pct",
                           acceptance={"basis": "mfr_tolerance"},
                           tolerance_source={"engine": "mfr", "function": "power_factor",
                                             "inputs": ["manufacturer", "model"]}),
                       ctl("tip_up_pct", "PF / DF tip-up", "numeric", "data", unit="pct", optional=True)])
SURGE = simple("surge_comparison", "Surge Comparison",
               [ctl("result", "Surge comparison result", "selection", "data", options=PF),
                ctl("waveform", "Comparison waveform", "graph", "data", optional=True)])
PROTECTIVE = simple("protective_devices", "Protective Devices (cross-reference)",
                    [ctl("spd", "Surge protection devices tested (7.19 / 7.20)", "selection", "data", options=COND),
                     ctl("starter", "Motor starter / protective devices tested (7.16)", "selection", "data", options=COND)])
AUXILIARY = simple("auxiliary", "Auxiliary (RTD / Space Heater)",
                   [ctl("rtd_resistance", "RTD-circuit resistance", "numeric", "data", unit="ohm"),
                    ctl("space_heater", "Space-heater operation", "selection", "data", options=PF)])
TEST_EQUIPMENT = {
    "key": "test_equipment", "title": "Test Equipment Used", "kind": "table",
    "table": {"row_dim": {"tag": "equipment", "label": "Instrument", "rows": [], "grow": True},
              "columns": [ctl("manufacturer", "Manufacturer", "text", "inherited"),
                          ctl("model", "Model", "text", "inherited"),
                          ctl("type", "Type", "text", "inherited"),
                          ctl("serial_id", "Serial / ID", "text", "inherited"),
                          ctl("cal_date", "Cal date", "date", "inherited"),
                          ctl("cal_due", "Cal due", "date", "inherited")]},
}
COMMENTS = {"key": "comments_deficiencies", "title": "Comments and Deficiencies", "kind": "fields",
            "fields": [ctl("comments", "Comments", "text", "data", grow=True),
                       ctl("deficiencies", "Deficiencies", "text", "data", grow=True)]}
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (mfr / OEM report)", "kind": "attachment",
               "capture_mode": "cover_attach",
               "fields": [ctl("report", "Attached test report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["manufacturer", "third_party_lab", "field_instrument"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements", "selection", "data", options=COND)]}


def assign_covers(sections, cov):
    # deep-copy per sheet: the shared section dicts (BOLTED, DIELECTRIC, ...) are reused across all
    # three machines, so neta_covers must be set on a private copy, not the shared module object.
    out = []
    for s in sections:
        s = copy.deepcopy(s)
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
        out.append(s)
    return out


def build_induction():
    cov = covers_by_sec(IND_CONCEPTS, IND_SEC)
    sections = [
        nameplate([ctl("service_factor", "Service factor", "numeric", "inherited", optional=True)]),
        vm_section(IND_CONCEPTS, IND_SEC),
        BOLTED, ir_section([ctl("bearing_ir_mohm", "Insulated-bearing IR (mfr data)", "numeric", "data", unit="Mohm")]),
        DIELECTRIC, WINDING_R, POWER_FACTOR, SURGE, PROTECTIVE, AUXILIARY,
        simple("running_tests", "Running / Load Tests",
               [ctl("vibration", "Vibration (under load)", "numeric", "data", unit="in_s", optional=True),
                ctl("bearing_temp", "Bearing temperature (under load)", "numeric", "data", unit="degC", optional=True),
                ctl("csa", "Current signature analysis", "graph", "data", optional=True),
                ctl("partial_discharge", "Partial discharge", "graph", "data", optional=True)]),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "induction_motor", "capture": CAPTURE,
            "selections": [], "sections": assign_covers(sections, cov)}


def build_synchronous():
    cov = covers_by_sec(SYN_CONCEPTS, SYN_SEC)
    sections = [
        nameplate([ctl("excitation_voltage", "Excitation voltage", "numeric", "inherited", optional=True)]),
        vm_section(SYN_CONCEPTS, SYN_SEC),
        BOLTED, ir_section([ctl("bearing_ir_mohm", "Insulated-bearing IR (mfr data)", "numeric", "data", unit="Mohm"),
                            ctl("rotor_ir_mohm", "Rotor field / exciter IR (IEEE 43)", "numeric", "data", unit="Mohm")]),
        DIELECTRIC,
        simple("winding_resistance", "Winding Resistance (stator + field)",
               [ctl("stator_ab", "Stator R(A-B)", "numeric", "data", unit="ohm"),
                ctl("stator_bc", "Stator R(B-C)", "numeric", "data", unit="ohm"),
                ctl("stator_ca", "Stator R(C-A)", "numeric", "data", unit="ohm"),
                ctl("field_winding", "Field / exciter winding resistance", "numeric", "data", unit="ohm",
                    acceptance={"basis": "mfr_tolerance"},
                    tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                      "inputs": ["manufacturer", "model"]}),
                ctl("discharge_resistor", "Field-discharge resistor", "numeric", "data", unit="ohm")]),
        POWER_FACTOR, SURGE,
        simple("field_excitation", "Field / Excitation System",
               [ctl("field_voltage_drop", "AC voltage-drop, rotating field poles", "selection", "data", options=PF, optional=True),
                ctl("excitation_hipot", "Excitation-system hipot (IEEE 421.3)", "selection", "data", options=PF, optional=True),
                ctl("diode_scr", "Diode front-to-back + SCR gating", "selection", "data", options=PF, optional=True),
                ctl("exciter_field_set", "Exciter-field current set to nameplate", "selection", "data", options=COND),
                ctl("field_timer", "Field-application / enable timers set (PF relay)", "selection", "data", options=COND),
                ctl("accel_record", "Acceleration record (stator I/V, field I)", "graph", "data", optional=True),
                ctl("v_curve", "V-curve (stator I vs excitation) at ~50% load", "graph", "data", optional=True),
                ctl("pf_relay_op", "PF-relay operation verified", "selection", "data", options=PF, optional=True)]),
        PROTECTIVE, AUXILIARY,
        simple("running_tests", "Running / Load Tests",
               [ctl("vibration", "Vibration (under load)", "numeric", "data", unit="in_s", optional=True),
                ctl("bearing_temp", "Bearing temperature (under load)", "numeric", "data", unit="degC"),
                ctl("csa", "Current signature analysis", "graph", "data", optional=True),
                ctl("partial_discharge", "Partial discharge", "graph", "data", optional=True)]),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "synchronous_machine", "capture": CAPTURE,
            "selections": [], "sections": assign_covers(sections, cov)}


def build_dc():
    cov = covers_by_sec(DC_CONCEPTS, DC_SEC)
    sections = [
        nameplate([ctl("field_type", "Field type (shunt / series / compound)", "selection", "inherited",
                       options=["shunt", "series", "compound"], optional=True)]),
        vm_section(DC_CONCEPTS, DC_SEC),
        BOLTED, ir_section([]),
        simple("dielectric_withstand", "High-Potential Test (NEMA MG 1)",
               [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV", optional=True,
                    acceptance={"basis": "mfr_tolerance", "note": "NEMA MG 1 Section 3.01"},
                    tolerance_source={"engine": "mfr", "function": "dielectric_withstand",
                                      "inputs": ["voltage_rating"]}),
                ctl("result", "Result", "selection", "data", options=PF, optional=True)]),
        simple("field_excitation", "Field / Armature Tests",
               [ctl("field_voltage_drop", "AC voltage-drop, field poles", "selection", "data", options=PF, optional=True),
                ctl("surge_comparison", "Surge (impulse) comparison, field + armature", "selection", "data", options=PF, optional=True),
                ctl("commutator_bar_r", "Commutator bar-to-bar resistance", "numeric", "data", unit="uohm", optional=True),
                ctl("field_polarity", "Shunt/series polarity checked; leads marked", "selection", "data", options=COND)]),
        simple("running_tests", "Running / Load Tests",
               [ctl("armature_current", "Armature running current", "numeric", "data", unit="A"),
                ctl("field_current", "Field current / voltage", "numeric", "data"),
                ctl("vs_nameplate", "Compared to nameplate", "selection", "data", options=COND),
                ctl("vibration", "Vibration (under load)", "numeric", "data", unit="in_s", optional=True)]),
        PROTECTIVE, TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "dc_machine", "capture": CAPTURE,
            "selections": [], "sections": assign_covers(sections, cov)}


def required_refs(json_path, section):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == section)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({f"{section}.A.{i + 1}" for i in range(len(vm))}
            | {f"{section}.B.{i + 1}" for i in range(len(el))})


def check(schema, src, section, n_expect, sec_expect):
    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src, section)
    missing = required - covered
    phantom = {r for r in covered if r.startswith(section + ".")} - required
    assert not missing, f"{schema['family']} gap: {sorted(missing)}"
    assert not phantom, f"{schema['family']} phantom: {sorted(phantom)}"
    assert len(required) == n_expect, f"{schema['family']} expected {n_expect}, got {len(required)}"
    assert len(schema["sections"]) == sec_expect, f"{schema['family']} sections={len(schema['sections'])} != {sec_expect}"
    return len(covered & required)


def sql_value(template_id, code, title, section, leaf, schema, desc):
    payload = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
    return [
        "INSERT INTO records.form_templates",
        "  (template_id, template_code, title, form_type, neta_standard, neta_section,",
        "   asset_class_id, version, is_current, field_schema, description, source)",
        "VALUES (",
        f"  '{template_id}', '{code}',",
        f"  '{title}',",
        f"  'neta_datasheet', 'ats', '{section}',",
        f"  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = '{leaf}'),",
        "  1, true,",
        f"  '{payload.replace(chr(39), chr(39) * 2)}'::jsonb,",
        f"  '{desc}',",
        "  'manual'",
        ")",
        "ON CONFLICT (template_code, version) DO UPDATE SET",
        "  field_schema = EXCLUDED.field_schema, title = EXCLUDED.title,",
        "  neta_section = EXCLUDED.neta_section, asset_class_id = EXCLUDED.asset_class_id,",
        "  description = EXCLUDED.description, updated_at = now();",
        "",
    ]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    ind, syn, dc = build_induction(), build_synchronous(), build_dc()
    a = check(ind, src, IND_SEC, 27, 14)
    b = check(syn, src, SYN_SEC, 37, 15)
    c = check(dc, src, DC_SEC, 20, 11)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Rotating-Machinery datasheets (induction / synchronous / DC).",
        "-- GENERATED by gen_motor_template.py - do not edit by hand.",
        "-- Three leaf-bound single-procedure sheets (7.15.1 / 7.15.2 / 7.15.3); the largest family.",
        "-- NOT PowerDB-anchored -> NETA-derived. R-A: mfr only (IR/PI per IEEE 43, hipot per NEMA MG 1,",
        "-- winding R + PF/DF per mfr) - NO tcc, NO neta_table window (motors test to IEEE 43 / NEMA,",
        "-- not a NETA table; torque -> 100.12 = VM acceptance basis). Capture = field + cover_attach.",
        f"-- Coverage: induction {a}/27 (7.15.1); synchronous {b}/37 (7.15.2); DC {c}/20 (7.15.3). Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(IND_ID, "ats_induction_motor_v1", "AC Induction Motor / Generator - ATS Field Data Sheet",
                     IND_SEC, "rm_induction", ind, "Induction-motor datasheet (NETA 7.15.1). Chip 2b; NETA-derived.")
    out += sql_value(SYN_ID, "ats_synchronous_machine_v1", "Synchronous Motor / Generator - ATS Field Data Sheet",
                     SYN_SEC, "rm_synchronous", syn, "Synchronous-machine datasheet (NETA 7.15.2). Chip 2b; NETA-derived.")
    out += sql_value(DC_ID, "ats_dc_machine_v1", "DC Motor / Generator - ATS Field Data Sheet",
                     DC_SEC, "rm_dc", dc, "DC-machine datasheet (NETA 7.15.3). Chip 2b; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"induction: sec={len(ind['sections'])} cov={a}/27   synchronous: sec={len(syn['sections'])} cov={b}/37   dc: sec={len(dc['sections'])} cov={c}/20")


if __name__ == "__main__":
    main()
