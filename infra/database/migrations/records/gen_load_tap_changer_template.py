#!/usr/bin/env python3
"""Generate 037_load_tap_changer_template.sql - the Load Tap-Changer datasheet (NETA 7.12.3).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_load_tap_changer_v1 -> leaf
'load_tap_changer'. NETA 7.12.3 = 14 VM + 13 electrical = 27 items (motor/drive cutoff; off-neutral IR
(per 7.2.2 -> Table 100.5), PF/DF, winding + dynamic winding resistance, leakage reactance, turns-ratio
all taps, DGA/liquid, vacuum-interrupter MAC + bottle dielectric, excitation all taps, heaters). R-A:
IR -> 100.5 (neta_table); winding-R / PF/DF / turns-ratio / reactance / vacuum-dielectric / excitation
-> mfr; DGA/liquid -> standard-basis (ASTM D923 / IEEE C57.104). Capture = field + cover_attach.

The LTC is the active element inside a regulating transformer; this is the standalone-LTC field sheet
(the xfmr sheet 012 cross-refs 7.12.3 for the integral LTC). Coverage invariant (fail-fast here,
re-checked in test_037). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_load_tap_changer_template.py [path-to-json]
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
OUT = os.path.join(HERE, "037_load_tap_changer_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
LTC_ID = str(uuid.uuid5(NS_TPL, "ats_load_tap_changer_v1"))
SEC = "7.12.3"
COND = ["sat", "unsat", "na"]
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat, item_no, optional, section_key)
CONCEPTS = [
    ("nameplate_vs_drawings", "Compare equipment nameplate data with drawings", "A", 1, False, "identification"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("impact_recorder", "Inspect impact recorder", "A", 4, False, "visual_mechanical"),
    ("shipping_bracing", "Verify removal of any shipping bracing and vent plugs", "A", 5, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 6, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 7, False, "visual_mechanical"),
    ("aux_device", "Verify correct auxiliary device operation", "A", 8, False, "visual_mechanical"),
    ("motor_drive", "Verify motor and drive train and automatic motor cutoff at maximum lower and raise positions", "A", 9, False, "motor_drive"),
    ("liquid_level", "Verify appropriate liquid level in all tanks", "A", 10, False, "visual_mechanical"),
    ("mfr_inspections", "Perform specific inspections and mechanical tests as recommended by the manufacturer", "A", 11, False, "visual_mechanical"),
    ("lubrication", "Verify appropriate lubrication on motor components", "A", 12, False, "visual_mechanical"),
    ("counters", "Record as-found and as-left operation counter readings", "A", 13, False, "operation_counters"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 14, True, "visual_mechanical"),
    ("ir", "Insulation-resistance tests in any off-neutral position (per Section 7.2.2; Table 100.5)", "B", 1, False, "insulation_resistance"),
    ("pf_df", "Insulation power-factor / dissipation-factor tests (per Section 7.2.2)", "B", 2, False, "power_factor"),
    ("winding_r", "Winding-resistance test at each tap position", "B", 3, False, "winding_resistance"),
    ("special_tests", "Special tests and adjustments as recommended by the manufacturer", "B", 4, False, "special_tests"),
    ("dynamic_winding_r", "Dynamic winding resistance measurement", "B", 5, False, "dynamic_winding_resistance"),
    ("leakage_reactance", "Leakage reactance three-phase-equivalent and per-phase tests", "B", 6, False, "leakage_reactance"),
    ("turns_ratio", "Turns-ratio test at all tap positions", "B", 7, False, "turns_ratio"),
    ("liquid_screen", "Sample insulating liquid (ASTM D923); test per referenced standard", "B", 8, False, "insulating_liquid"),
    ("dga", "Sample insulating liquid (ASTM D923) and perform dissolved-gas analysis (IEEE C57.104 / ASTM D3612)", "B", 9, False, "insulating_liquid"),
    ("mac_test", "Magnetron atmospheric-condition (MAC) test on each vacuum interrupter", "B", 10, False, "vacuum_integrity"),
    ("vacuum_dielectric", "Vacuum-bottle integrity (dielectric withstand) across each vacuum bottle, contacts open, per mfr", "B", 11, False, "vacuum_integrity"),
    ("excitation", "Excitation test on all taps and neutral position", "B", 12, False, "excitation"),
    ("heaters", "Verify operation of heaters", "B", 13, False, "functional"),
]


def covers_by_sec():
    cov = {}
    for c in CONCEPTS:
        cov.setdefault(c[5], set()).add(f"{SEC}.{c[2]}.{c[3]}")
    return cov


def vm_section():
    rows = []
    for c in CONCEPTS:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_ref": f"{SEC}.{c[2]}.{c[3]}"}
        if c[4]:
            r["optional"] = True
        rows.append(r)
    return {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
            "neta_basis": SEC,
            "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
                      "columns": [ctl("inspected", "Inspected", "boolean"),
                                  ctl("condition", "Condition", "selection", options=COND),
                                  ctl("value", "Value", "text"), ctl("note", "Note", "text")]}}


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
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (OEM / commissioning report)",
               "kind": "attachment", "capture_mode": "cover_attach",
               "fields": [ctl("report", "Attached report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["engineer_of_record", "third_party_lab", "oem"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements", "selection", "data", options=COND)]}


def build():
    cov = covers_by_sec()
    identification = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model"),
        ctl("serial_no", "Serial no.", "text", "inherited"),
        ctl("ltc_type", "Tap-changer type", "selection", "inherited",
            options=["resistive", "reactive", "vacuum"]),
        ctl("num_positions", "Number of tap positions", "numeric", "inherited"),
        ctl("associated_transformer", "Associated transformer", "text", "inherited"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    motor_drive = [
        ctl("motor_drive_ok", "Motor and drive train operate; automatic cutoff at max lower and raise",
            "selection", "data", options=COND, neta_ref=f"{SEC}.A.9"),
    ]
    operation_counters = [
        ctl("counter_as_found", "Operation counter (as found)", "numeric", "data", neta_ref=f"{SEC}.A.13"),
        ctl("counter_as_left", "Operation counter (as left)", "numeric", "data"),
    ]
    insulation_resistance = [
        ctl("ir_position", "Tap position (off-neutral)", "text", "data"),
        ctl("test_voltage", "Test voltage", "numeric", "data", unit="V"),
        ctl("ir_60s_mohm", "IR (60 s)", "numeric", "data", unit="Mohm",
            acceptance={"basis": "neta_table", "table": "100.5"},
            tolerance_source={"engine": "neta_table", "table": "100.5", "function": "insulation_resistance",
                              "inputs": ["associated_transformer"]}, neta_ref=f"{SEC}.B.1"),
        ctl("polarization_index", "Polarization index (10/1 min)", "numeric", "data"),
        ctl("winding_temp", "Winding temp", "numeric", "data", unit="degC"),
    ]
    special_tests = [
        ctl("special_tests", "Special tests and adjustments performed per manufacturer", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.4"),
    ]
    dynamic_winding_resistance = [
        ctl("dwr_result", "Dynamic winding resistance acceptable (no make-before-break anomalies)",
            "selection", "data", options=COND, neta_ref=f"{SEC}.B.5"),
        ctl("dwr_note", "Note", "text", "data"),
    ]
    insulating_liquid = [
        ctl("liquid_screen", "Insulating-liquid screen (ASTM D923)", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.8"),
        ctl("dga_attached", "Dissolved-gas analysis performed (IEEE C57.104 / ASTM D3612)", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.9"),
    ]
    functional = [
        ctl("heaters", "Heaters operational", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.13"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "motor_drive", "title": "Motor and Drive Train", "kind": "fields", "fields": motor_drive},
        {"key": "operation_counters", "title": "Operation Counters", "kind": "fields", "fields": operation_counters},
        {"key": "insulation_resistance", "title": "Insulation Resistance (off-neutral; per 7.2.2)",
         "kind": "fields", "fields": insulation_resistance},
        {"key": "power_factor", "title": "Insulation Power-Factor / Dissipation-Factor (per 7.2.2)", "kind": "table",
         "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "winding", "label": "Winding", "rows": ["Series", "Shunt"], "grow": True},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("pf_pct", "Power factor", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "power_factor",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "winding_resistance", "title": "Winding Resistance (each tap)", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "tap", "label": "Tap position", "rows": [], "grow": True},
                   "columns": [ctl("resistance", "Resistance", "numeric", unit="ohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Winding temp", "numeric", unit="degC")]}},
        {"key": "special_tests", "title": "Special Tests", "kind": "fields", "fields": special_tests},
        {"key": "dynamic_winding_resistance", "title": "Dynamic Winding Resistance", "kind": "fields",
         "fields": dynamic_winding_resistance},
        {"key": "leakage_reactance", "title": "Leakage Reactance", "kind": "table",
         "neta_basis": f"{SEC}.B.6",
         "table": {"row_dim": {"tag": "config", "label": "Configuration",
                               "rows": ["3-phase equivalent", "Phase 1", "Phase 2", "Phase 3"]},
                   "columns": [ctl("nameplate_pct", "Nameplate", "numeric", unit="pct"),
                               ctl("measured_pct", "Measured", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "leakage_reactance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct")]}},
        {"key": "turns_ratio", "title": "Turns Ratio (all tap positions)", "kind": "table",
         "neta_basis": f"{SEC}.B.7",
         "table": {"row_dim": {"tag": "tap", "label": "Tap position", "rows": [], "grow": True},
                   "columns": [ctl("calculated", "Calculated ratio", "numeric"),
                               ctl("measured", "Measured ratio", "numeric",
                                   acceptance={"basis": "mfr_tolerance", "rule": "+/-0.5% deviation"},
                                   tolerance_source={"engine": "mfr", "function": "turns_ratio",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct")]}},
        {"key": "insulating_liquid", "title": "Insulating Liquid (screen + DGA)", "kind": "fields",
         "fields": insulating_liquid},
        {"key": "vacuum_integrity", "title": "Vacuum-Interrupter Integrity (vacuum LTC)", "kind": "table",
         "neta_basis": f"{SEC}.B.11",
         "table": {"row_dim": {"tag": "bottle", "label": "Vacuum bottle", "rows": [], "grow": True},
                   "columns": [ctl("mac_result", "MAC test", "selection", options=COND + ["not_applicable"],
                                   neta_ref=f"{SEC}.B.10"),
                               ctl("dielectric_kv", "Dielectric withstand", "numeric", unit="kV",
                                   acceptance={"basis": "mfr_tolerance", "note": "mfr published data"},
                                   tolerance_source={"engine": "mfr", "function": "vacuum_bottle_dielectric",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND + ["not_applicable"])]}},
        {"key": "excitation", "title": "Excitation (all taps + neutral)", "kind": "table",
         "neta_basis": f"{SEC}.B.12",
         "table": {"row_dim": {"tag": "tap", "label": "Tap / position", "rows": [], "grow": True},
                   "columns": [ctl("exciting_current_ma", "Exciting current", "numeric", unit="mA",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "excitation",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("watts", "Watts", "numeric", unit="W"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "load_tap_changer", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "winding_resistance", "turns_ratio",
                                        "vacuum_integrity", "excitation", "insulating_liquid"]}],
            "sections": sections}


def required_refs(json_path, section):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == section)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({f"{section}.A.{i + 1}" for i in range(len(vm))}
            | {f"{section}.B.{i + 1}" for i in range(len(el))})


def check(schema, src):
    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src, SEC)
    missing = required - covered
    phantom = {r for r in covered if r.startswith(SEC + ".")} - required
    assert not missing, f"ltc gap: {sorted(missing)}"
    assert not phantom, f"ltc phantom: {sorted(phantom)}"
    assert len(required) == 27, f"ltc expected 27, got {len(required)}"
    assert len(schema["sections"]) == 18, f"ltc sections={len(schema['sections'])} != 18"
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
    schema = build()
    n = check(schema, src)
    out = [
        "-- =============================================================================",
        "-- Records Chip 2c - Load Tap-Changer datasheet (ats_load_tap_changer_v1).",
        "-- GENERATED by gen_load_tap_changer_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.12.3, 27 ATS items.",
        "-- Motor/drive cutoff; off-neutral IR (per 7.2.2 -> 100.5), PF/DF, winding + dynamic winding",
        "-- resistance, leakage reactance, turns-ratio all taps, DGA/liquid, vacuum-interrupter MAC +",
        "-- bottle dielectric, excitation all taps, heaters.",
        "-- R-A: IR -> 100.5 (neta_table); winding-R / PF/DF / turns-ratio / reactance / vacuum /",
        "-- excitation -> mfr; liquid -> standard-basis (ASTM D923 / IEEE C57.104). UUID5.",
        f"-- Coverage: {n}/27 (7.12.3).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(LTC_ID, "ats_load_tap_changer_v1", "Load Tap-Changer - ATS Field Data Sheet",
                     SEC, "load_tap_changer", schema,
                     "Load Tap-Changer datasheet (NETA 7.12.3). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"ltc: sections={len(schema['sections'])} covered={n}/27")


if __name__ == "__main__":
    main()
