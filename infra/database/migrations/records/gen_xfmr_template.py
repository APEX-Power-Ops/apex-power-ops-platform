#!/usr/bin/env python3
"""Generate 012_xfmr_datasheet_templates.sql - the transformer composite datasheets.

TWO leaf-bound composites (matching cb_lv / cb_mvhv - one datasheet per leaf):
  - ats_dry_xfmr_v1  -> xfmr_dry; folds small (7.2.1.1) + large (7.2.1.2) via a `dry_class`
    selector (large gates in the full electrical battery + fan/temp-indicator visuals);
    covers their UNION = 35 ATS items.
  - ats_liquid_xfmr_v1 -> xfmr_liquid; 7.2.2; 39 ATS items, incl. the LTC (7.12.3),
    instrument-transformer (7.10) and surge-arrester (7.19) cross-ref borrows.

BOTH fold two-winding / three-winding via a `winding_config` selector that gates the
tertiary-winding measurement rows (H-Y, X-Y, Y-G) in the IR / turns-ratio / winding-
resistance / PF tables - measurement granularity, NOT NETA coverage (operator's ruling).

R-A (apparatus-appropriate): a transformer has no integral trip curve, so tolerance_source
.engine is `neta_table` (IR -> Table 100.5, torque -> 100.12) or `mfr` (winding resistance,
bushing PF, turns-ratio vs nameplate - the future mfr-layer slot) - never `tcc`. Oil/DGA
acceptance is standard-basis (ASTM D923 / IEEE C57.104), descriptive (no resolved window).

Coverage invariant (fail-fast here, re-checked in test_012): per sheet, the union of every
section's neta_covers must cover all ATS visual_mechanical+electrical items of the sheet's
NETA procedures - no silent drops, no phantom refs.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_xfmr_template.py [path-to-json]
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
OUT = os.path.join(HERE, "012_xfmr_datasheet_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
DRY_ID = str(uuid.uuid5(NS_TPL, "ats_dry_xfmr_v1"))
LIQ_ID = str(uuid.uuid5(NS_TPL, "ats_liquid_xfmr_v1"))

DRY_PROCS = {"small": "7.2.1.1", "large": "7.2.1.2"}
LIQ_PROC = "7.2.2"
COND = ["sat", "unsat", "na"]
W3 = "winding_config == 'three_winding'"
DRY_LARGE = "dry_class == 'large'"


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# ----- winding-pair / winding-unit row helpers (the 2W/3W fold) -----
def ww_wg_rows():
    """Insulation-resistance measurement points: winding-winding + winding-ground."""
    return [
        {"key": "h_x", "label": "H-X"},
        {"key": "h_g", "label": "H-G (ground)"},
        {"key": "x_g", "label": "X-G (ground)"},
        {"key": "h_y", "label": "H-Y", "visible_if": W3},
        {"key": "x_y", "label": "X-Y", "visible_if": W3},
        {"key": "y_g", "label": "Y-G (ground)", "visible_if": W3},
    ]


def ratio_rows():
    return [
        {"key": "h_x", "label": "H-X"},
        {"key": "h_y", "label": "H-Y", "visible_if": W3},
        {"key": "x_y", "label": "X-Y", "visible_if": W3},
    ]


def winding_unit_rows():
    return [
        {"key": "h", "label": "H winding"},
        {"key": "x", "label": "X winding"},
        {"key": "y", "label": "Y winding", "visible_if": W3},
    ]


def pf_rows():
    return [
        {"key": "ch", "label": "CH + CHG"},
        {"key": "cl", "label": "CL + CLG"},
        {"key": "chl", "label": "CHL"},
        {"key": "ct", "label": "CT (tertiary)", "visible_if": W3},
    ]


# =====================================================================================
# DRY transformer (xfmr_dry): small 7.2.1.1 + large 7.2.1.2
# (key, label, cat, {proc_key: item_no}, optional, section)
# =====================================================================================
DRY_CONCEPTS = [
    ("np_drawings",    "Nameplate data compared with drawings",                 "A", {"small": 1, "large": 1}, False, "nameplate"),
    ("phys_mech",      "Physical and mechanical condition",                     "A", {"small": 2, "large": 2}, False, "visual_mechanical"),
    ("anchorage",      "Anchorage, alignment, grounding",                       "A", {"small": 3, "large": 3}, False, "visual_mechanical"),
    ("resilient_mounts", "Resilient mounts free; shipping brackets removed",    "A", {"small": 4, "large": 4}, False, "visual_mechanical"),
    ("clean",          "Unit is clean",                                         "A", {"small": 5, "large": 5}, False, "visual_mechanical"),
    ("torque",         "Bolted connections torqued (Table 100.12)",             "A", {"small": 6, "large": 8}, False, "visual_mechanical"),
    ("as_left_taps",   "As-left tap connections as specified",                  "A", {"small": 7, "large": 10}, False, "visual_mechanical"),
    ("thermography",   "Thermographic survey (Section 9)",                      "A", {"small": 8, "large": 12}, True, "visual_mechanical"),
    ("temp_indicator", "Temperature-indicator control/alarm settings",          "A", {"large": 6}, True, "visual_mechanical"),
    ("cooling_fans",   "Cooling fans operate; fan-motor overcurrent protection", "A", {"large": 7}, False, "visual_mechanical"),
    ("mfr_inspections", "Manufacturer-recommended inspections and mechanical tests", "A", {"large": 9}, False, "visual_mechanical"),
    ("surge_arrester_presence", "Presence of surge arresters",                  "A", {"large": 11}, False, "visual_mechanical"),
    ("bolted_r",       "Bolted-connection resistance (low-resistance ohmmeter)", "B", {"small": 1, "large": 1}, False, "bolted_resistance"),
    ("ir_winding",     "Insulation resistance winding-winding / winding-ground (Table 100.5; DAR/PI)", "B", {"small": 2, "large": 2}, False, "insulation_resistance"),
    ("turns_ratio",    "Turns-ratio test (designated tap / all taps)",          "B", {"small": 3, "large": 5}, False, "turns_ratio"),
    ("pf_all",         "Power-factor / dissipation-factor on all windings",     "B", {"large": 3}, False, "power_factor"),
    ("pf_tipup",       "Power-factor tip-up (windings > 2.5 kV)",               "B", {"large": 4}, True, "power_factor"),
    ("excitation",     "Excitation-current test (each phase)",                  "B", {"large": 6}, True, "excitation_current"),
    ("winding_r",      "Winding resistance at each tap",                        "B", {"large": 7}, False, "winding_resistance"),
    ("core_ir",        "Core insulation resistance (500 Vdc, if removable strap)", "B", {"large": 8}, False, "insulation_resistance"),
    ("applied_voltage", "Applied-voltage (hipot) test, windings-to-ground",     "B", {"large": 9}, True, "dielectric_withstand"),
    ("secondary_voltage", "Correct secondary voltage after energization",       "B", {"large": 10}, True, "functional"),
    ("surge_arrester", "Surge arresters tested per Section 7.19",               "B", {"large": 11}, False, "surge_arresters"),
    ("pd",             "Online partial-discharge survey (Section 11)",          "B", {"large": 12}, True, "functional"),
]

# =====================================================================================
# LIQUID transformer (xfmr_liquid): 7.2.2
# (key, label, cat, item_no, optional, section)
# =====================================================================================
LIQ_CONCEPTS = [
    ("np_drawings",    "Nameplate data compared with drawings",                 "A", 1, False, "nameplate"),
    ("phys_mech",      "Physical and mechanical condition",                     "A", 2, False, "visual_mechanical"),
    ("impact_recorder", "Inspect impact recorder prior to unloading",           "A", 3, False, "visual_mechanical"),
    ("dew_point",      "Dew point of tank gases",                               "A", 4, True, "gas_blanket"),
    ("anchorage",      "Anchorage, alignment, grounding",                       "A", 5, False, "visual_mechanical"),
    ("pcb_labeling",   "PCB content labeling present",                          "A", 6, False, "visual_mechanical"),
    ("shipping_bracing", "Shipping bracing removed after placement",            "A", 7, False, "visual_mechanical"),
    ("bushings_clean", "Bushings are clean",                                    "A", 8, False, "visual_mechanical"),
    ("indicator_settings", "Alarm/control/trip settings on temp + level indicators", "A", 9, False, "visual_mechanical"),
    ("alarm_circuits", "Alarm/control/trip circuits (temp, level, pressure-relief, gas accumulator, fault-pressure relay)", "A", 10, False, "visual_mechanical"),
    ("cooling_fans_pumps", "Cooling fans/pumps operate; overcurrent protection", "A", 11, False, "visual_mechanical"),
    ("torque",         "Bolted connections torqued (Table 100.12)",             "A", 12, False, "visual_mechanical"),
    ("liquid_level",   "Correct liquid level in tanks and bushings",            "A", 13, False, "visual_mechanical"),
    ("valve_positions", "Valves in correct operating position",                 "A", 14, False, "visual_mechanical"),
    ("positive_pressure", "Positive pressure maintained on gas-blanketed unit", "A", 15, False, "visual_mechanical"),
    ("mfr_inspections", "Manufacturer-recommended inspections and mechanical tests", "A", 16, False, "visual_mechanical"),
    ("ltc_test",       "Test load tap-changer per Section 7.12.3",              "A", 17, False, "load_tap_changer"),
    ("surge_arrester_presence", "Presence of transformer surge arresters",      "A", 18, False, "visual_mechanical"),
    ("detc_position",  "De-energized tap-changer position left as specified",   "A", 19, False, "visual_mechanical"),
    ("thermography",   "Thermographic survey (Section 9)",                      "A", 20, True, "visual_mechanical"),
    ("bolted_r",       "Bolted-connection resistance (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir_winding",     "Insulation resistance winding-winding / winding-ground (Table 100.5; DAR/PI)", "B", 2, False, "insulation_resistance"),
    ("turns_ratio",    "Turns-ratio test at all tap positions",                 "B", 3, False, "turns_ratio"),
    ("pf_windings",    "Power-factor / dissipation-factor on all windings",     "B", 4, False, "power_factor"),
    ("pf_bushing",     "Power-factor on bushings (PF/cap tap; hot-collar)",     "B", 5, False, "power_factor"),
    ("excitation",     "Excitation-current test",                               "B", 6, False, "excitation_current"),
    ("sfra",           "Sweep frequency response analysis (SFRA)",              "B", 7, True, "advanced_diagnostics"),
    ("winding_r",      "Winding resistance at each tap",                        "B", 8, False, "winding_resistance"),
    ("ltc_dynamic_r",  "Dynamic resistance measurement for load tap changer",   "B", 9, True, "load_tap_changer"),
    ("leakage_reactance", "Leakage reactance (3-phase equivalent + per phase)", "B", 10, True, "advanced_diagnostics"),
    ("core_ir",        "Core insulation resistance (500 Vdc, if accessible)",   "B", 11, True, "insulation_resistance"),
    ("oxygen",         "Percent oxygen in the gas blanket",                     "B", 12, True, "gas_blanket"),
    ("dfr",            "Dielectric frequency response (DFR)",                   "B", 13, True, "advanced_diagnostics"),
    ("insulating_liquid", "Insulating-liquid sample + screen (ASTM D923)",      "B", 14, False, "insulating_liquid"),
    ("dga",            "Dissolved-gas analysis (IEEE C57.104 / ASTM D3612)",    "B", 15, False, "insulating_liquid"),
    ("instr_xfmr",     "Instrument transformers tested per Section 7.10",       "B", 16, False, "instrument_transformers"),
    ("surge_arrester", "Surge arresters tested per Section 7.19",               "B", 17, False, "surge_arresters"),
    ("neutral_grounding", "Transformer neutral grounding impedance device",     "B", 18, False, "auxiliary"),
    ("space_heaters",  "Cubicle / air-terminal compartment space heaters",      "B", 19, False, "auxiliary"),
]


def dry_refs(c):
    return [f"{DRY_PROCS[k]}.{c[2]}.{n}" for k, n in c[3].items()]


def liq_refs(c):
    return [f"{LIQ_PROC}.{c[2]}.{c[3]}"]


def dry_gate(c):
    keys = set(c[3])
    if keys == set(DRY_PROCS):
        return None
    return DRY_LARGE if keys == {"large"} else "dry_class == 'small'"


# ----- shared section pieces -----
TEST_EQUIPMENT = {
    "key": "test_equipment", "title": "Test Equipment Used", "kind": "table",
    "table": {"row_dim": {"tag": "equipment", "label": "Instrument", "rows": [], "grow": True},
              "columns": [
                  ctl("manufacturer", "Manufacturer", "text", "inherited"),
                  ctl("model", "Model", "text", "inherited"),
                  ctl("type", "Type", "text", "inherited"),
                  ctl("serial_id", "Serial / ID", "text", "inherited"),
                  ctl("cal_date", "Cal date", "date", "inherited"),
                  ctl("cal_due", "Cal due", "date", "inherited"),
              ]},
}
COMMENTS = {
    "key": "comments_deficiencies", "title": "Comments and Deficiencies", "kind": "fields",
    "fields": [ctl("comments", "Comments", "text", "data", grow=True),
               ctl("deficiencies", "Deficiencies", "text", "data", grow=True)],
}


def ir_columns():
    return [
        ctl("test_voltage", "Test voltage", "numeric", unit="V"),
        ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
            acceptance={"basis": "mfr_tolerance", "fallback_table": "100.5"},
            tolerance_source={"engine": "neta_table", "table": "100.5",
                              "inputs": ["voltage_rating"]}),
        ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
        ctl("dar", "DAR (30s/60s)", "numeric", "calc"),
        ctl("pi", "PI (10min/1min)", "numeric", "calc"),
    ]


def ir_section(core_label):
    rows = ww_wg_rows() + [{"key": "core", "label": core_label, "optional": True}]
    return {"key": "insulation_resistance", "title": "Insulation Resistance",
            "kind": "table",
            "table": {"row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
                      "columns": ir_columns()}}


def turns_ratio_section():
    return {"key": "turns_ratio", "title": "Turns-Ratio (TTR)", "kind": "table",
            "table": {"row_dim": {"tag": "winding_pair", "label": "Winding pair", "rows": ratio_rows()},
                      "columns": [
                          ctl("tap", "Tap position", "text"),
                          ctl("nominal_ratio", "Nameplate ratio", "numeric", "inherited"),
                          ctl("measured_ratio", "Measured ratio", "numeric"),
                          ctl("deviation_pct", "Deviation", "numeric", "calc", unit="pct",
                              acceptance={"basis": "mfr_tolerance",
                                          "rule": "within 0.5% of nameplate ratio (IEEE C57)"},
                              tolerance_source={"engine": "mfr", "function": "turns_ratio",
                                                "inputs": ["manufacturer", "model"]}),
                      ]}}


def winding_resistance_section():
    return {"key": "winding_resistance", "title": "Winding Resistance", "kind": "table",
            "visible_if": DRY_LARGE,
            "table": {"row_dim": {"tag": "winding", "label": "Winding", "rows": winding_unit_rows()},
                      "columns": [
                          ctl("tap", "Tap position", "text"),
                          ctl("ohms", "Resistance", "numeric", unit="ohm",
                              acceptance={"basis": "mfr_tolerance",
                                          "rule": "compare phases / prior; investigate deviation"},
                              tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                                "inputs": ["manufacturer", "model"]}),
                          ctl("temp", "Temp", "numeric", unit="degC"),
                      ]}}


def pf_section(with_bushing, gate=None):
    rows = pf_rows()
    if with_bushing:
        rows = rows + [{"key": "bushing", "label": "Bushing (PF/cap tap; hot-collar)", "grow": True}]
    sec = {"key": "power_factor", "title": "Power-Factor / Dissipation-Factor", "kind": "table",
           "table": {"row_dim": {"tag": "specimen", "label": "Specimen", "rows": rows},
                     "columns": [
                         ctl("pf_pct", "Power factor", "numeric", unit="pct",
                             acceptance={"basis": "comparison", "rule": "vs prior/similar or mfr (Doble) data"},
                             tolerance_source={"engine": "mfr", "function": "power_factor",
                                               "inputs": ["manufacturer", "model"]}),
                         ctl("capacitance", "Capacitance", "numeric", unit="pF"),
                         ctl("temp", "Temp", "numeric", unit="degC"),
                     ]}}
    if gate:
        sec["visible_if"] = gate
    return sec


# =====================================================================================
def build_dry():
    cov = {}
    for c in DRY_CONCEPTS:
        cov.setdefault(c[5], set()).update(dry_refs(c))

    nameplate = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model"),
        ctl("serial_no", "Serial no.", "text", "inherited"),
        ctl("kva", "Rating", "numeric", "inherited", unit="kVA"),
        ctl("hv_voltage", "HV voltage", "numeric", "inherited", unit="V"),
        ctl("lv_voltage", "LV voltage", "numeric", "inherited", unit="V"),
        ctl("tv_voltage", "Tertiary voltage", "numeric", "inherited", unit="V", visible_if=W3),
        ctl("cooling_class", "Cooling class (AA/FA)", "text", "inherited"),
        ctl("insulation_class", "Insulation class", "text", "inherited"),
        ctl("impedance_pct", "Impedance", "numeric", "inherited", unit="pct"),
        ctl("vector_group", "Vector group", "text", "inherited"),
        ctl("bil", "BIL", "numeric", "inherited", unit="kV"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data", options=COND),
    ]
    vm_rows = []
    for c in DRY_CONCEPTS:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_refs": sorted(dry_refs(c))}
        g = dry_gate(c)
        if g:
            r["visible_if"] = g
        if c[4]:
            r["optional"] = True
        vm_rows.append(r)

    sections = [
        {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields", "fields": nameplate},
        {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
         "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": vm_rows},
                   "columns": [ctl("inspected", "Inspected", "boolean"),
                               ctl("condition", "Condition", "selection", options=COND),
                               ctl("value", "Value", "text"), ctl("note", "Note", "text")]}},
        ir_section("Core (if removable ground strap)"),
        turns_ratio_section(),
        winding_resistance_section(),
        pf_section(with_bushing=False, gate=DRY_LARGE),
        {"key": "excitation_current", "title": "Excitation Current", "kind": "fields",
         "visible_if": DRY_LARGE,
         "fields": [ctl("phase_a", "Phase A", "numeric", unit="mA"),
                    ctl("phase_b", "Phase B", "numeric", unit="mA"),
                    ctl("phase_c", "Phase C", "numeric", unit="mA"),
                    ctl("pattern", "Pattern assessment", "selection", options=COND)]},
        {"key": "dielectric_withstand", "title": "Applied-Voltage (Hipot)", "kind": "fields",
         "visible_if": DRY_LARGE,
         "fields": [ctl("test_kv", "Test voltage", "numeric", unit="kV",
                        acceptance={"basis": "standard", "ref": "IEEE C57.12.91"}),
                    ctl("duration_s", "Duration", "numeric", unit="s"),
                    ctl("result", "Result", "selection", options=["pass", "fail"])]},
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "visible_if": DRY_LARGE,
         "fields": [ctl("secondary_voltage", "Secondary voltage after energization", "selection", "data", options=COND),
                    ctl("partial_discharge", "Online partial-discharge survey", "selection", "data", options=COND, optional=True)]},
        {"key": "surge_arresters", "title": "Surge Arresters (Cross-Reference)", "kind": "fields",
         "visible_if": DRY_LARGE,
         "fields": [ctl("surge_arresters_xref",
                        "Surge arresters - test per NETA 7.19 (recorded on the surge-arrester datasheet)",
                        "text", "reference")]},
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "dry_transformer",
            "selections": [
                {"tag": "dry_class", "label": "Dry-type class", "value_kind": "selection",
                 "options": ["small", "large"], "ties_to": "equipment_model"},
                {"tag": "winding_config", "label": "Winding configuration", "value_kind": "selection",
                 "options": ["two_winding", "three_winding"], "ties_to": "equipment_model"},
            ], "sections": sections}


def build_liquid():
    cov = {}
    for c in LIQ_CONCEPTS:
        cov.setdefault(c[5], set()).update(liq_refs(c))

    nameplate = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model"),
        ctl("serial_no", "Serial no.", "text", "inherited"),
        ctl("kva", "Rating", "numeric", "inherited", unit="kVA"),
        ctl("hv_voltage", "HV voltage", "numeric", "inherited", unit="V"),
        ctl("lv_voltage", "LV voltage", "numeric", "inherited", unit="V"),
        ctl("tv_voltage", "Tertiary voltage", "numeric", "inherited", unit="V", visible_if=W3),
        ctl("cooling_class", "Cooling class (ONAN/ONAF/...)", "text", "inherited"),
        ctl("liquid_type", "Insulating liquid type", "text", "inherited"),
        ctl("impedance_pct", "Impedance", "numeric", "inherited", unit="pct"),
        ctl("vector_group", "Vector group", "text", "inherited"),
        ctl("bil", "BIL", "numeric", "inherited", unit="kV"),
        ctl("gas_blanketed", "Gas-blanketed", "selection", "inherited", options=["yes", "no"]),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data", options=COND),
    ]
    vm_rows = []
    for c in LIQ_CONCEPTS:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_refs": sorted(liq_refs(c))}
        if c[4]:
            r["optional"] = True
        vm_rows.append(r)

    sections = [
        {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields", "fields": nameplate},
        {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
         "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": vm_rows},
                   "columns": [ctl("inspected", "Inspected", "boolean"),
                               ctl("condition", "Condition", "selection", options=COND),
                               ctl("value", "Value", "text"), ctl("note", "Note", "text")]}},
        ir_section("Core (if accessible ground strap)"),
        turns_ratio_section(),
        {"key": "winding_resistance", "title": "Winding Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "winding", "label": "Winding", "rows": winding_unit_rows()},
                   "columns": [ctl("tap", "Tap position", "text"),
                               ctl("ohms", "Resistance", "numeric", unit="ohm",
                                   acceptance={"basis": "mfr_tolerance",
                                               "rule": "compare phases / prior; IEEE C57.152"},
                                   tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        pf_section(with_bushing=True),
        {"key": "excitation_current", "title": "Excitation Current", "kind": "fields",
         "fields": [ctl("phase_a", "Phase A", "numeric", unit="mA"),
                    ctl("phase_b", "Phase B", "numeric", unit="mA"),
                    ctl("phase_c", "Phase C", "numeric", unit="mA"),
                    ctl("pattern", "Pattern assessment", "selection", options=COND)]},
        {"key": "advanced_diagnostics", "title": "Advanced Diagnostics (optional)", "kind": "fields",
         "fields": [ctl("sfra", "Sweep frequency response analysis", "graph", "data", optional=True),
                    ctl("leakage_reactance", "Leakage reactance", "numeric", "data", unit="pct", optional=True),
                    ctl("dfr", "Dielectric frequency response", "graph", "data", optional=True)]},
        {"key": "insulating_liquid", "title": "Insulating Liquid (Oil)", "kind": "fields",
         "fields": [ctl("dielectric_breakdown_kv", "Dielectric breakdown (ASTM D877/D1816)", "numeric", unit="kV",
                        acceptance={"basis": "standard", "ref": "ASTM D923"}),
                    ctl("color", "Color", "text"),
                    ctl("neutralization_number", "Neutralization number", "numeric", unit="mgKOH/g"),
                    ctl("interfacial_tension", "Interfacial tension", "numeric", unit="dyne/cm"),
                    ctl("water_content_ppm", "Water content", "numeric", unit="ppm"),
                    ctl("power_factor_pct", "Liquid power factor", "numeric", unit="pct"),
                    ctl("dga", "Dissolved-gas analysis (DGA)", "text", "data",
                        acceptance={"basis": "standard", "ref": "IEEE C57.104"})]},
        {"key": "gas_blanket", "title": "Gas Blanket", "kind": "fields", "visible_if": "gas_blanketed == 'yes'",
         "fields": [ctl("dew_point", "Dew point of tank gases", "numeric", "data", unit="degC", optional=True),
                    ctl("oxygen_pct", "Oxygen in gas blanket", "numeric", "data", unit="pct", optional=True)]},
        {"key": "load_tap_changer", "title": "Load Tap Changer", "kind": "fields",
         "fields": [ctl("ltc_xref", "Load tap-changer - test per NETA 7.12.3 (recorded on the LTC datasheet)",
                        "text", "reference"),
                    ctl("dynamic_resistance", "Dynamic resistance measurement", "graph", "data", optional=True)]},
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "auxiliary", "title": "Auxiliary", "kind": "fields",
         "fields": [ctl("neutral_grounding", "Neutral grounding impedance device", "selection", "data", options=COND),
                    ctl("space_heaters", "Space heaters operational", "selection", "data", options=COND)]},
        {"key": "instrument_transformers", "title": "Instrument Transformers (Cross-Reference)", "kind": "fields",
         "fields": [ctl("instrument_transformers_xref",
                        "Instrument transformers - test per NETA 7.10 (recorded on the instrument-transformer datasheet)",
                        "text", "reference")]},
        {"key": "surge_arresters", "title": "Surge Arresters (Cross-Reference)", "kind": "fields",
         "fields": [ctl("surge_arresters_xref",
                        "Surge arresters - test per NETA 7.19 (recorded on the surge-arrester datasheet)",
                        "text", "reference")]},
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "liquid_transformer",
            "selections": [
                {"tag": "winding_config", "label": "Winding configuration", "value_kind": "selection",
                 "options": ["two_winding", "three_winding"], "ties_to": "equipment_model"},
                {"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                 "options": ["insulation_resistance", "turns_ratio", "winding_resistance",
                             "power_factor", "excitation_current", "insulating_liquid"]},
            ], "sections": sections}


def required_refs(json_path, neta_sections):
    d = json.load(open(json_path, encoding="utf-8"))
    eqs = d["equipment"]
    req = set()
    for sec in neta_sections:
        e = next(x for x in eqs if x.get("section") == sec)
        ats = e.get("ats_data") or {}
        vm = ats.get("visual_mechanical") or []
        el = ats.get("electrical_tests") or []
        req |= {f"{sec}.A.{i + 1}" for i in range(len(vm))}
        req |= {f"{sec}.B.{i + 1}" for i in range(len(el))}
    return req


def check(schema, src, neta_sections, n_expect, sec_expect):
    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src, neta_sections)
    prefixes = tuple(s + "." for s in neta_sections)
    missing = required - covered
    phantom = {r for r in covered if r.startswith(prefixes)} - required
    assert not missing, f"{schema['family']} gap: {sorted(missing)}"
    assert not phantom, f"{schema['family']} phantom: {sorted(phantom)}"
    assert len(required) == n_expect, f"{schema['family']} expected {n_expect}, got {len(required)}"
    assert len(schema["sections"]) == sec_expect, f"{schema['family']} sections={len(schema['sections'])}"
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
    dry = build_dry()
    liq = build_liquid()
    dn = check(dry, src, list(DRY_PROCS.values()), 35, 13)
    ln = check(liq, src, [LIQ_PROC], 39, 17)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Transformer composite datasheets (ats_dry_xfmr_v1, ats_liquid_xfmr_v1).",
        "-- GENERATED by gen_xfmr_template.py - do not edit by hand.",
        "-- TWO leaf-bound composites; each folds two-winding/three-winding via winding_config;",
        "-- the dry sheet folds small/large via dry_class. R-A: tolerance_source = neta_table + mfr",
        "-- (IR -> Table 100.5; NOT tcc); windows DECLARED, resolved at provisioning.",
        f"-- Coverage: dry {dn}/35 (7.2.1.1 U 7.2.1.2); liquid {ln}/39 (7.2.2). Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(DRY_ID, "ats_dry_xfmr_v1",
                     "Dry-Type Transformer - ATS Field Data Sheet", "7.2.1.1", "xfmr_dry", dry,
                     "Composite dry-type transformer datasheet (small/large via dry_class; 2W/3W via winding_config). Chip 2b.")
    out += sql_value(LIQ_ID, "ats_liquid_xfmr_v1",
                     "Liquid-Filled Transformer - ATS Field Data Sheet", "7.2.2", "xfmr_liquid", liq,
                     "Composite liquid-filled transformer datasheet (2W/3W via winding_config; LTC/IT/SA cross-refs). Chip 2b.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"dry: sections={len(dry['sections'])} covered={dn}/35   "
          f"liquid: sections={len(liq['sections'])} covered={ln}/39")


if __name__ == "__main__":
    main()
