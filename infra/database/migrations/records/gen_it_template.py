#!/usr/bin/env python3
"""Generate 015_it_datasheet_templates.sql - the Instrument-Transformer datasheets.

Three leaf-bound single-procedure sheets (the clean recipe, one procedure per leaf):
  - ats_ct_v1  -> it_ct;  NETA 7.10.1 (Current Transformer);              18 ATS (9 VM + 9 elec).
  - ats_vt_v1  -> it_vt;  NETA 7.10.2 (Voltage / Potential Transformer);  18 ATS (11 VM + 7 elec).
  - ats_cvt_v1 -> it_cvt; NETA 7.10.3 (Coupling-Capacitor VT);            20 ATS (11 VM + 9 elec).

Anchored to the RESA PowerDB cover forms (27660 Multi-Winding CT / 27600 PT-VT / 99000 CVT):
the field structure (CtType bar/window, ANSI/IEC saturation standard, the PF connection matrix,
the CVT capacitor-section battery) comes from the harvested PowerDB layer; NETA stays the
coverage authority (the validator invariant below).

R-A: an instrument transformer has no integral trip curve, so tolerance_source.engine is
neta_table (IR -> Table 100.5, dielectric withstand -> Table 100.9, torque -> 100.12) or mfr
(PF/DF >= 15/38 kV per mfr data) - never tcc. Windows declared, resolved at provisioning.

CAPTURE-MODE CONTRACT (NEW - IT is the first capture-mode-aware build, ratified post-235):
  template-level `capture` {modes, default}; a standard `attachments` section
  (kind=attachment, capture_mode=cover_attach = Path 1, datasheet-as-cover for the mfr report);
  instrument-fillable sections carry capture_mode=instrument_import + an `import` hint
  {tool, profile} naming the bridge (ct_analyzer / dtax / ptm) = Path 2. The harvested control
  `tag` is the Path-2 import target id. Importer execution = Chip 10 (deferred).

Coverage invariant (fail-fast here, re-checked in test_015): per sheet, the union of every
section's neta_covers covers all ATS visual_mechanical+electrical items of its procedure.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_it_template.py [path-to-json]
"""
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
OUT = os.path.join(HERE, "015_it_datasheet_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
CT_ID = str(uuid.uuid5(NS_TPL, "ats_ct_v1"))
VT_ID = str(uuid.uuid5(NS_TPL, "ats_vt_v1"))
CVT_ID = str(uuid.uuid5(NS_TPL, "ats_cvt_v1"))

CT_SEC, VT_SEC, CVT_SEC = "7.10.1", "7.10.2", "7.10.3"
COND = ["sat", "unsat", "na"]
PF = ["pass", "fail"]
CAPTURE = {"modes": ["field", "instrument_import", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat A=visual_mechanical / B=electrical, item_no, optional, section_key)
CT_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("connection", "Verify correct connection with system requirements", "A", 3, False, "visual_mechanical"),
    ("clearances", "Adequate clearances between primary and secondary wiring", "A", 4, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 5, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12)", "A", 6, False, "visual_mechanical"),
    ("ground_short", "Grounding and shorting connections provide contact", "A", 7, False, "visual_mechanical"),
    ("lubrication", "Appropriate lubrication on moving / sliding surfaces", "A", 8, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 9, True, "visual_mechanical"),
    ("ir_secondary", "IR each CT + secondary wiring to ground, 1000 Vdc 1 min", "B", 1, False, "insulation_resistance"),
    ("polarity", "Polarity test (IEEE C57.13.1)", "B", 2, False, "ratio_polarity"),
    ("ratio", "Ratio-verification (voltage/current method, C57.13.1)", "B", 3, False, "ratio_polarity"),
    ("excitation", "Excitation test for relaying CTs (C57.13.1)", "B", 4, False, "excitation"),
    ("burden", "Measure current-circuit burden at CT shorting terminal block", "B", 5, False, "burden"),
    ("ir_primary_bar", "IR bar-type CT primary, secondary grounded (Table 100.5)", "B", 6, False, "insulation_resistance"),
    ("dielectric", "Dielectric withstand on bar-type CT primary (Table 100.9)", "B", 7, True, "dielectric_withstand"),
    ("pf_df", "Insulation PF/DF on bar-type CT >= 38 kV (mfr data)", "B", 8, False, "power_factor"),
    ("grounding", "Verify secondary grounded, single grounding point (C57.13.3)", "B", 9, False, "grounding"),
]

VT_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("connection", "Verify correct connection with system requirements", "A", 3, False, "visual_mechanical"),
    ("clearances", "Adequate clearances between primary and secondary wiring", "A", 4, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 5, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12)", "A", 6, False, "visual_mechanical"),
    ("ground_contact", "Grounding connections provide contact", "A", 7, False, "visual_mechanical"),
    ("fuse_sizes", "Verify correct primary and secondary fuse sizes", "A", 8, False, "visual_mechanical"),
    ("lubrication", "Appropriate lubrication on moving / sliding surfaces", "A", 9, False, "visual_mechanical"),
    ("as_left", "Perform as-left tests", "A", 10, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("ir", "IR winding-to-winding and winding-to-ground, 1 min (Table 100.5)", "B", 1, False, "insulation_resistance"),
    ("polarity", "Polarity test (H1-X1 relationship)", "B", 2, False, "ratio_polarity"),
    ("turns_ratio", "Turns-ratio test on all tap positions", "B", 3, False, "ratio_polarity"),
    ("burden", "Measure voltage-circuit burden at transformer terminals", "B", 4, False, "burden"),
    ("dielectric", "Dielectric withstand, primary >= 15 kV (Table 100.9)", "B", 5, True, "dielectric_withstand"),
    ("pf_df", "PF/DF, primary >= 15 kV (mfr data)", "B", 6, False, "power_factor"),
    ("grounding", "Verify secondary grounded, single grounding point (C57.13.3)", "B", 7, False, "grounding"),
]

CVT_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("connection", "Verify correct connection with system requirements", "A", 3, False, "visual_mechanical"),
    ("clearances", "Adequate clearances between primary and secondary wiring", "A", 4, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 5, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.10.3.B.1)", "A", 6, False, "visual_mechanical"),
    ("ground_contact", "Grounding connections provide contact", "A", 7, False, "visual_mechanical"),
    ("fuse_sizes", "Verify correct primary and secondary fuse sizes", "A", 8, False, "visual_mechanical"),
    ("lubrication", "Appropriate lubrication on moving / sliding surfaces", "A", 9, False, "visual_mechanical"),
    ("as_left", "Perform as-left tests", "A", 10, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "IR winding-to-winding and winding-to-ground, 1 min (Table 100.5)", "B", 2, False, "insulation_resistance"),
    ("polarity", "Polarity test (IEEE C93.1)", "B", 3, False, "ratio_polarity"),
    ("ratio", "Ratio test on all tap positions", "B", 4, False, "ratio_polarity"),
    ("burden", "Measure voltage-circuit burden at transformer terminals", "B", 5, False, "burden"),
    ("dielectric", "Dielectric withstand on primary (Table 100.9)", "B", 6, True, "dielectric_withstand"),
    ("capacitance", "Measure capacitance of capacitor sections", "B", 7, False, "capacitance_pf"),
    ("pf_df", "PF/DF (test-equipment mfr data)", "B", 8, False, "capacitance_pf"),
    ("grounding", "Verify grounded, single grounding point (C57.13.3)", "B", 9, False, "grounding"),
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


IR_COLS = [
    ctl("test_voltage", "Test voltage", "numeric", unit="V"),
    ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
        acceptance={"basis": "mfr_tolerance", "fallback_table": "100.5"},
        tolerance_source={"engine": "neta_table", "table": "100.5", "inputs": ["voltage_rating"]}),
    ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
]


def dielectric_section():
    return {"key": "dielectric_withstand", "title": "Dielectric Withstand (optional)", "kind": "fields",
            "fields": [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV", optional=True,
                           acceptance={"basis": "neta_table", "table": "100.9"},
                           tolerance_source={"engine": "neta_table", "table": "100.9",
                                             "inputs": ["voltage_rating", "insulation_class"]}),
                       ctl("duration_min", "Duration", "numeric", "data", unit="min", optional=True),
                       ctl("result", "Result", "selection", "data", options=PF, optional=True)]}


def grounding_section():
    return {"key": "grounding", "title": "Grounding Verification", "kind": "fields",
            "fields": [ctl("single_point", "Secondary grounded at a single point (IEEE C57.13.3)", "selection", "data", options=COND),
                       ctl("location_verified", "Grounding point per project drawings", "selection", "data", options=COND)]}


def burden_section():
    return {"key": "burden", "title": "Circuit Burden", "kind": "fields",
            "fields": [ctl("connected_burden_va", "Connected burden", "numeric", "data", unit="VA"),
                       ctl("burden_class", "Burden / accuracy class", "text", "data"),
                       ctl("result", "Within rated burden", "selection", "data", options=COND)]}


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
# Path 1: the datasheet doubles as a cover sheet for the manufacturer / OEM test report.
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (mfr / OEM report)", "kind": "attachment",
               "capture_mode": "cover_attach",
               "fields": [ctl("report", "Attached test report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["manufacturer", "third_party_lab", "field_instrument"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements", "selection", "data", options=COND)]}


def nameplate(fields):
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
            "fields": fields + [ctl("nameplate_vs_drawings", "Nameplate data compared with drawings",
                                    "selection", "data", options=COND)]}


def assign_covers(sections, cov):
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return sections


def build_ct():
    cov = covers_by_sec(CT_CONCEPTS, CT_SEC)
    sections = [
        nameplate([
            ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
            ctl("catalog_style", "Catalog / style", "text", "inherited"),
            ctl("serial", "Serial no.", "text", "inherited"),
            ctl("ratio", "Ratio (e.g. 600:5)", "text", "inherited"),
            ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
            ctl("accuracy_class", "Relaying / metering accuracy class", "text", "inherited"),
            ctl("insulation_rating", "Insulation rating (BIL)", "numeric", "inherited", unit="kV"),
            ctl("ct_type", "CT type", "selection", "data", options=["bar", "window_solid", "window_split_core"]),
            ctl("num_windings", "Number of windings", "numeric", "data"),
            ctl("saturation_standard", "Saturation standard", "selection", "data", options=["ansi", "iec"]),
            ctl("frequency", "Frequency", "selection", "data", options=["50", "60"], unit="Hz"),
        ]),
        vm_section(CT_CONCEPTS, CT_SEC),
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "test_point", "label": "Test point",
                               "rows": [{"key": "secondary_gnd", "label": "Secondary winding + wiring to ground (1000 Vdc)"},
                                        {"key": "primary_bar", "label": "Bar-type primary to ground, secondary grounded"}]},
                   "columns": IR_COLS}},
        {"key": "ratio_polarity", "title": "Ratio Verification and Polarity", "kind": "table",
         "capture_mode": "instrument_import", "import": {"tool": "ct_analyzer", "profile": "CT_RatioAccuracy"},
         "table": {"row_dim": {"tag": "winding", "label": "Winding / tap", "rows": [], "grow": True},
                   "columns": [ctl("method", "Method", "selection", options=["voltage", "current"]),
                               ctl("nameplate_ratio", "Nameplate ratio", "text"),
                               ctl("measured_ratio", "Measured ratio", "numeric"),
                               ctl("ratio_error_pct", "Ratio error", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance", "note": "vs nameplate / IEEE C57.13.1"}),
                               ctl("polarity", "Polarity", "selection", options=PF)]}},
        {"key": "excitation", "title": "Excitation (relaying CTs)", "kind": "fields",
         "capture_mode": "instrument_import", "import": {"tool": "ct_analyzer", "profile": "CT_ExcitationCurve"},
         "fields": [ctl("knee_point_v", "Knee-point voltage", "numeric", "data", unit="V"),
                    ctl("knee_point_i", "Knee-point current", "numeric", "data", unit="A"),
                    ctl("remanence_pct", "Remanence", "numeric", "data", unit="pct", optional=True),
                    ctl("excitation_curve", "Excitation curve (V/I)", "graph", "data")]},
        burden_section(),
        dielectric_section(),
        {"key": "power_factor", "title": "Insulation Power Factor / Dissipation Factor", "kind": "fields",
         "fields": [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV"),
                    ctl("pf_pct", "Power factor / dissipation factor", "numeric", "data", unit="pct",
                        acceptance={"basis": "mfr_tolerance"},
                        tolerance_source={"engine": "mfr", "function": "power_factor",
                                          "inputs": ["manufacturer", "model", "voltage_rating"]}),
                    ctl("watts", "Watts", "numeric", "data", unit="W"),
                    ctl("cap_pf", "Capacitance", "numeric", "data", unit="pF")]},
        grounding_section(),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    assign_covers(sections, cov)
    return {"version": 1, "family": "ct", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "ratio_polarity", "excitation", "burden",
                                        "dielectric_withstand", "power_factor", "grounding"]}],
            "sections": sections}


def vt_pf_section():
    return {"key": "power_factor", "title": "Insulation Power Factor / Dissipation Factor", "kind": "fields",
            "capture_mode": "instrument_import", "import": {"tool": "dtax", "profile": "TX_PFDF"},
            "fields": [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV"),
                       ctl("pf_pct", "Power factor / dissipation factor", "numeric", "data", unit="pct",
                           acceptance={"basis": "mfr_tolerance"},
                           tolerance_source={"engine": "mfr", "function": "power_factor",
                                             "inputs": ["manufacturer", "model", "voltage_rating"]}),
                       ctl("watts", "Watts", "numeric", "data", unit="W")]}


def ratio_polarity_taps(tool, profile, polarity_ref):
    return {"key": "ratio_polarity", "title": "Turns-Ratio and Polarity", "kind": "table",
            "capture_mode": "instrument_import", "import": {"tool": tool, "profile": profile},
            "table": {"row_dim": {"tag": "tap", "label": "Tap position", "rows": [], "grow": True},
                      "columns": [ctl("nameplate_ratio", "Nameplate ratio", "text"),
                                  ctl("measured_ratio", "Measured ratio", "numeric"),
                                  ctl("ratio_error_pct", "Ratio error", "numeric", unit="pct",
                                      acceptance={"basis": "mfr_tolerance", "note": polarity_ref}),
                                  ctl("polarity", "Polarity", "selection", options=PF)]}}


def build_vt():
    cov = covers_by_sec(VT_CONCEPTS, VT_SEC)
    sections = [
        nameplate([
            ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
            ctl("catalog_style", "Catalog / style", "text", "inherited"),
            ctl("year", "Year", "text", "inherited"),
            ctl("serial", "Serial no.", "text", "inherited"),
            ctl("ratio", "Ratio (e.g. 7200:120)", "text", "inherited"),
            ctl("kv_rating", "Voltage rating", "numeric", "inherited", unit="kV"),
            ctl("bil", "BIL", "numeric", "inherited", unit="kV"),
            ctl("accuracy_class", "Accuracy class", "text", "inherited"),
            ctl("insulation_type", "Insulation type", "selection", "data", options=["oil", "dry", "sf6", "cast"]),
            ctl("va_rating", "VA rating (primary / secondary / tertiary)", "text", "data"),
        ]),
        vm_section(VT_CONCEPTS, VT_SEC),
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "test_point", "label": "Test point",
                               "rows": [{"key": "winding_to_winding", "label": "Winding-to-winding"},
                                        {"key": "winding_to_ground", "label": "Each winding-to-ground"}]},
                   "columns": IR_COLS}},
        ratio_polarity_taps("ptm", "TX_TTR", "vs nameplate; H1-X1 polarity"),
        burden_section(),
        dielectric_section(),
        vt_pf_section(),
        grounding_section(),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    assign_covers(sections, cov)
    return {"version": 1, "family": "vt", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "ratio_polarity", "burden",
                                        "dielectric_withstand", "power_factor", "grounding"]}],
            "sections": sections}


def build_cvt():
    cov = covers_by_sec(CVT_CONCEPTS, CVT_SEC)
    sections = [
        nameplate([
            ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
            ctl("type_model", "Type / model", "text", "inherited"),
            ctl("year", "Year", "text", "inherited"),
            ctl("serial", "Serial no.", "text", "inherited"),
            ctl("bil", "BIL", "numeric", "inherited", unit="kV"),
            ctl("rated_capacitance_pf", "Rated capacitance", "numeric", "inherited", unit="pF"),
            ctl("frequency", "Frequency", "selection", "data", options=["50", "60"], unit="Hz"),
            ctl("insulation_type", "Insulation type", "selection", "data", options=["oil", "synthetic_oil", "dry"]),
            ctl("num_stacks", "Number of stacks", "numeric", "data"),
            ctl("capacitor_sections", "Capacitor sections (CN / C1 / C2)", "text", "data"),
        ]),
        vm_section(CVT_CONCEPTS, CVT_SEC),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "fields",
         "fields": [ctl("resistance_uohm", "Resistance (low-resistance ohmmeter)", "numeric", "data", unit="uohm"),
                    ctl("result", "Within mfr / comparison tolerance", "selection", "data", options=COND)]},
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "test_point", "label": "Test point",
                               "rows": [{"key": "winding_to_winding", "label": "Winding-to-winding"},
                                        {"key": "winding_to_ground", "label": "Each winding-to-ground"}]},
                   "columns": IR_COLS}},
        ratio_polarity_taps("ptm", "TX_TTR", "vs nameplate; IEEE C93.1 polarity"),
        burden_section(),
        dielectric_section(),
        {"key": "capacitance_pf", "title": "Capacitance and Power Factor (capacitor sections)", "kind": "table",
         "capture_mode": "instrument_import", "import": {"tool": "dtax", "profile": "TX_PFDF"},
         "table": {"row_dim": {"tag": "section", "label": "Capacitor section",
                               "rows": [{"key": "c1", "label": "C1 (B1-POT)"},
                                        {"key": "c2", "label": "C2 (CAR-POT)"},
                                        {"key": "cn", "label": "CN"}]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("measured_cap_pf", "Measured capacitance", "numeric", unit="pF",
                                   acceptance={"basis": "mfr_tolerance"}),
                               ctl("pf_pct", "Power factor / dissipation factor", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "power_factor",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("watts", "Watts", "numeric", unit="W")]}},
        grounding_section(),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    assign_covers(sections, cov)
    return {"version": 1, "family": "cvt", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["bolted_resistance", "insulation_resistance", "ratio_polarity", "burden",
                                        "dielectric_withstand", "capacitance_pf", "grounding"]}],
            "sections": sections}


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
    ct, vt, cvt = build_ct(), build_vt(), build_cvt()
    cn = check(ct, src, CT_SEC, 18, 12)
    vn = check(vt, src, VT_SEC, 18, 11)
    vcn = check(cvt, src, CVT_SEC, 20, 12)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Instrument-Transformer datasheets (ats_ct_v1, ats_vt_v1, ats_cvt_v1).",
        "-- GENERATED by gen_it_template.py - do not edit by hand.",
        "-- Three leaf-bound single-procedure sheets: CT 7.10.1 / VT 7.10.2 / CVT 7.10.3.",
        "-- Anchored to the RESA PowerDB cover forms (27660 CT / 27600 PT-VT / 99000 CVT); NETA is",
        "-- the coverage authority. R-A: neta_table (IR 100.5, dielectric 100.9, torque 100.12) +",
        "-- mfr (PF/DF); NOT tcc. FIRST capture-mode-aware build: template `capture` block +",
        "-- `attachments` cover section (Path 1) + instrument_import hints (Path 2: ct_analyzer /",
        "-- ptm / dtax bridges). Windows resolved at provisioning; import execution = Chip 10.",
        f"-- Coverage: CT {cn}/18 (7.10.1); VT {vn}/18 (7.10.2); CVT {vcn}/20 (7.10.3). Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(CT_ID, "ats_ct_v1", "Current Transformer - ATS Field Data Sheet",
                     CT_SEC, "it_ct", ct, "CT datasheet (NETA 7.10.1; PowerDB 27660). Chip 2b; capture-mode.")
    out += sql_value(VT_ID, "ats_vt_v1", "Voltage / Potential Transformer - ATS Field Data Sheet",
                     VT_SEC, "it_vt", vt, "VT/PT datasheet (NETA 7.10.2; PowerDB 27600). Chip 2b; capture-mode.")
    out += sql_value(CVT_ID, "ats_cvt_v1", "Coupling-Capacitor Voltage Transformer - ATS Field Data Sheet",
                     CVT_SEC, "it_cvt", cvt, "CVT datasheet (NETA 7.10.3; PowerDB 99000). Chip 2b; capture-mode.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"ct: sections={len(ct['sections'])} covered={cn}/18  "
          f"vt: sections={len(vt['sections'])} covered={vn}/18  "
          f"cvt: sections={len(cvt['sections'])} covered={vcn}/20")


if __name__ == "__main__":
    main()
