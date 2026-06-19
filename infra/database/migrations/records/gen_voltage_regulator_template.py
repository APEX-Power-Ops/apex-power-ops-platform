#!/usr/bin/env python3
"""Generate 036_voltage_regulator_template.sql - the Step Voltage Regulator datasheet (NETA 7.12.1.1).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_voltage_regulator_v1 -> leaf
'voltage_regulator'. NETA 7.12.1.1 (Step Voltage Regulators) = 15 VM + 16 electrical = 31 items - the
largest Chip 2c family. Motor/drive cutoff, leakage reactance (A.6 + B.7 dup-listed -> one section);
bolted R, winding-to-ground IR (Table 100.5) + PI, winding + dynamic winding resistance, PF/DF windings
+ bushings, turns-ratio per step, voltage-range-limiter + control functions, DGA/liquid screen,
heaters. R-A: IR -> 100.5 (neta_table); winding-R / PF/DF / turns-ratio / reactance -> mfr; DGA/liquid
-> standard-basis (ASTM D923 / IEEE C57.104) - mirrors the transformer R-A. Capture = field +
cover_attach.

Coverage invariant (fail-fast here, re-checked in test_036). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_voltage_regulator_template.py [path-to-json]
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
OUT = os.path.join(HERE, "036_voltage_regulator_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
VR_ID = str(uuid.uuid5(NS_TPL, "ats_voltage_regulator_v1"))
SEC = "7.12.1.1"
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
    ("impact_recorder", "Inspect impact recorder prior to unloading regulator", "A", 3, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 4, False, "visual_mechanical"),
    ("shipping_bracing", "Verify removal of any shipping bracing and vent plugs after final placement", "A", 5, False, "visual_mechanical"),
    ("leakage_reactance_vm", "Perform leakage reactance three-phase-equivalent and per-phase tests", "A", 6, False, "leakage_reactance"),
    ("clean", "Verify the unit is clean", "A", 7, False, "visual_mechanical"),
    ("aux_device", "Verify auxiliary device operation", "A", 8, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 9, False, "visual_mechanical"),
    ("motor_drive", "Verify motor and drive train and automatic motor cutoff at maximum lower and raise positions", "A", 10, False, "motor_drive"),
    ("lubrication", "Verify appropriate lubrication on drive motor components", "A", 11, False, "visual_mechanical"),
    ("liquid_level", "Verify correct liquid level in all tanks and bushings", "A", 12, False, "visual_mechanical"),
    ("mfr_inspections", "Perform specific inspections and mechanical tests as recommended by the manufacturer", "A", 13, False, "visual_mechanical"),
    ("counters", "Record as-found and as-left operation counter readings", "A", 14, False, "operation_counters"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 15, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Winding-to-ground insulation-resistance in any off-neutral position (Table 100.5); calculate polarization index", "B", 2, False, "insulation_resistance"),
    ("pf_windings", "Insulation power-factor / dissipation-factor tests on windings (per test-equipment mfr data)", "B", 3, False, "power_factor"),
    ("pf_bushings", "Power-factor / dissipation-factor on each bushing with PF tap (or hot-collar tests)", "B", 4, False, "bushing_pf"),
    ("winding_r", "Winding resistance of source windings (neutral) and all taps on load windings", "B", 5, False, "winding_resistance"),
    ("dynamic_winding_r", "Dynamic winding resistance measurement", "B", 6, False, "dynamic_winding_resistance"),
    ("leakage_reactance", "Perform leakage reactance three-phase-equivalent and per-phase test", "B", 7, False, "leakage_reactance"),
    ("special_tests", "Special tests and adjustments as recommended by the manufacturer", "B", 8, False, "special_tests"),
    ("gas_blanket_o2", "If separate tap-changer compartment: test for oxygen in the gas blanket in the main tank", "B", 9, True, "special_tests"),
    ("turns_ratio", "Turns-ratio test on each voltage step position; verify the indicator identifies all tap positions", "B", 10, False, "turns_ratio"),
    ("range_limiter", "Verify accurate operation of voltage range limiter", "B", 11, False, "control_functions"),
    ("control_functions", "Verify bandwidth, time-delay, voltage, and line-drop compensation functions of the control device", "B", 12, False, "control_functions"),
    ("dga", "Sample insulating liquid (main + tap-changer/common tank, ASTM D923) and perform DGA (IEEE C57.104 / ASTM D3612)", "B", 13, False, "insulating_liquid"),
    ("liquid_main", "Sample insulating liquid from main/common tank (ASTM D923); test per referenced standard", "B", 14, False, "insulating_liquid"),
    ("liquid_tapchanger", "If separate tap-changer compartment: sample insulating liquid from the tap-changer tank (ASTM D923)", "B", 15, True, "insulating_liquid"),
    ("heaters", "Verify operation of heaters", "B", 16, False, "functional"),
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
        ctl("rated_voltage", "Rated voltage", "numeric", "inherited", unit="kV"),
        ctl("rated_kva", "Rated power", "numeric", "inherited", unit="kVA"),
        ctl("regulation_range_pct", "Regulation range", "numeric", "inherited", unit="pct"),
        ctl("num_steps", "Number of steps", "numeric", "inherited"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    motor_drive = [
        ctl("motor_drive_ok", "Motor and drive train operate; automatic cutoff at max lower and raise",
            "selection", "data", options=COND, neta_ref=f"{SEC}.A.10"),
    ]
    operation_counters = [
        ctl("counter_as_found", "Operation counter (as found)", "numeric", "data", neta_ref=f"{SEC}.A.14"),
        ctl("counter_as_left", "Operation counter (as left)", "numeric", "data"),
    ]
    insulation_resistance = [
        ctl("ir_position", "Tap position (off-neutral)", "text", "data"),
        ctl("test_voltage", "Test voltage", "numeric", "data", unit="V"),
        ctl("ir_60s_mohm", "IR (60 s)", "numeric", "data", unit="Mohm",
            acceptance={"basis": "neta_table", "table": "100.5"},
            tolerance_source={"engine": "neta_table", "table": "100.5", "function": "insulation_resistance",
                              "inputs": ["rated_voltage"]}, neta_ref=f"{SEC}.B.2"),
        ctl("polarization_index", "Polarization index (10/1 min)", "numeric", "data"),
        ctl("winding_temp", "Winding temp", "numeric", "data", unit="degC"),
    ]
    bushing_pf = [
        ctl("bushing_method", "Method", "selection", "data", options=["pf_tap", "hot_collar"]),
        ctl("bushing_pf_pct", "Bushing PF / DF", "numeric", "data", unit="pct",
            acceptance={"basis": "mfr_tolerance"},
            tolerance_source={"engine": "mfr", "function": "bushing_power_factor",
                              "inputs": ["manufacturer", "model"]}, neta_ref=f"{SEC}.B.4"),
    ]
    special_tests = [
        ctl("special_tests", "Special tests and adjustments performed per manufacturer", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.8"),
        ctl("gas_blanket_o2", "Gas-blanket oxygen test (separate tap-changer compartment)", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.9"),
    ]
    control_functions = [
        ctl("range_limiter_ok", "Voltage range limiter operates accurately", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.11"),
        ctl("bandwidth_v", "Bandwidth", "numeric", "data", unit="V"),
        ctl("time_delay_s", "Time delay", "numeric", "data", unit="s"),
        ctl("ldc_r", "Line-drop compensation R", "numeric", "data", unit="V"),
        ctl("ldc_x", "Line-drop compensation X", "numeric", "data", unit="V"),
        ctl("control_functions_ok", "Bandwidth / time-delay / voltage / LDC functions verified", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.12"),
    ]
    insulating_liquid = [
        ctl("dga_attached", "Dissolved-gas analysis performed (IEEE C57.104 / ASTM D3612)", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.13"),
        ctl("liquid_screen_main", "Main/common-tank liquid screen (ASTM D923)", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.14"),
        ctl("liquid_screen_tapchanger", "Tap-changer-tank liquid sample (ASTM D923, if separate compartment)",
            "selection", "data", options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.15"),
    ]
    functional = [
        ctl("heaters", "Heaters operational", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.16"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "motor_drive", "title": "Motor and Drive Train", "kind": "fields", "fields": motor_drive},
        {"key": "operation_counters", "title": "Operation Counters", "kind": "fields", "fields": operation_counters},
        {"key": "leakage_reactance", "title": "Leakage Reactance", "kind": "table",
         "neta_basis": f"{SEC}.B.7",
         "note": "Satisfies the NETA VM-listed (A.6) and electrical-listed (B.7) leakage-reactance requirement",
         "table": {"row_dim": {"tag": "config", "label": "Configuration",
                               "rows": ["3-phase equivalent", "Phase 1", "Phase 2", "Phase 3"]},
                   "columns": [ctl("nameplate_pct", "Nameplate", "numeric", unit="pct"),
                               ctl("measured_pct", "Measured", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "leakage_reactance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct")]}},
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "insulation_resistance", "title": "Insulation Resistance (winding-to-ground, off-neutral)",
         "kind": "fields", "fields": insulation_resistance},
        {"key": "power_factor", "title": "Insulation Power-Factor / Dissipation-Factor (windings)", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "winding", "label": "Winding", "rows": ["Series", "Shunt"], "grow": True},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("pf_pct", "Power factor", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "power_factor",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "bushing_pf", "title": "Bushing Power-Factor", "kind": "fields", "fields": bushing_pf},
        {"key": "winding_resistance", "title": "Winding Resistance (source + load taps)", "kind": "table",
         "neta_basis": f"{SEC}.B.5",
         "table": {"row_dim": {"tag": "tap", "label": "Winding / tap", "rows": [], "grow": True},
                   "columns": [ctl("resistance", "Resistance", "numeric", unit="ohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "winding_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Winding temp", "numeric", unit="degC")]}},
        {"key": "dynamic_winding_resistance", "title": "Dynamic Winding Resistance", "kind": "fields",
         "neta_basis": f"{SEC}.B.6",
         "fields": [ctl("dwr_result", "Dynamic winding resistance acceptable (no make-before-break anomalies)",
                        "selection", "data", options=COND, neta_ref=f"{SEC}.B.6"),
                    ctl("dwr_note", "Note", "text", "data")]},
        {"key": "special_tests", "title": "Special Tests", "kind": "fields", "fields": special_tests},
        {"key": "turns_ratio", "title": "Turns Ratio (each step + tap-position indication)", "kind": "table",
         "neta_basis": f"{SEC}.B.10",
         "table": {"row_dim": {"tag": "step", "label": "Voltage step / tap", "rows": [], "grow": True},
                   "columns": [ctl("calculated", "Calculated ratio", "numeric"),
                               ctl("measured", "Measured ratio", "numeric",
                                   acceptance={"basis": "mfr_tolerance", "rule": "+/-0.5% deviation"},
                                   tolerance_source={"engine": "mfr", "function": "turns_ratio",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct"),
                               ctl("indicator_ok", "Indicator identifies tap", "selection", options=COND)]}},
        {"key": "control_functions", "title": "Regulator Control Functions", "kind": "fields",
         "fields": control_functions},
        {"key": "insulating_liquid", "title": "Insulating Liquid (DGA + screen)", "kind": "fields",
         "fields": insulating_liquid},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "voltage_regulator", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "power_factor", "winding_resistance",
                                        "turns_ratio", "insulating_liquid"]}],
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
    assert not missing, f"voltage-regulator gap: {sorted(missing)}"
    assert not phantom, f"voltage-regulator phantom: {sorted(phantom)}"
    assert len(required) == 31, f"voltage-regulator expected 31, got {len(required)}"
    assert len(schema["sections"]) == 19, f"voltage-regulator sections={len(schema['sections'])} != 19"
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
        "-- Records Chip 2c - Step Voltage Regulator datasheet (ats_voltage_regulator_v1).",
        "-- GENERATED by gen_voltage_regulator_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.12.1.1, 31 ATS items (the largest Chip 2c family).",
        "-- Motor/drive cutoff, leakage reactance (covers NETA's A.6 + B.7 dup-listing); bolted R,",
        "-- winding-to-ground IR (100.5) + PI, winding + dynamic winding resistance, PF/DF windings +",
        "-- bushings, turns-ratio per step, range-limiter + control functions, DGA/liquid, heaters.",
        "-- R-A: IR -> 100.5 (neta_table); winding-R / PF/DF / turns-ratio / reactance -> mfr; liquid",
        "-- -> standard-basis (ASTM D923 / IEEE C57.104). UUID5.",
        f"-- Coverage: {n}/31 (7.12.1.1).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(VR_ID, "ats_voltage_regulator_v1", "Step Voltage Regulator - ATS Field Data Sheet",
                     SEC, "voltage_regulator", schema,
                     "Step Voltage Regulator datasheet (NETA 7.12.1.1). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"voltage-regulator: sections={len(schema['sections'])} covered={n}/31")


if __name__ == "__main__":
    main()
