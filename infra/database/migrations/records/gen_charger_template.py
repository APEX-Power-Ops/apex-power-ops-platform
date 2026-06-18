#!/usr/bin/env python3
"""Generate 026_charger_template.sql - the Battery Charger datasheet (NETA 7.18.2).

records Chip 2c (slice-3 coverage backlog); companion to the battery sheet (025). One leaf-bound sheet:
ats_battery_charger_v1 -> leaf 'battery_charger'. NETA 7.18.2 = 8 VM + 9 electrical = 17 items
(float/equalize voltage, hv-shutdown, parallel load-sharing, alarms, input/output V&I, ac ripple,
full-load + current-limit; meter calibration cross-refs Section 7.11). R-A: mfr. Capture = field +
cover_attach.

Coverage invariant (fail-fast here, re-checked in test_026). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_charger_template.py [path-to-json]
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
OUT = os.path.join(HERE, "026_charger_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
CHG_ID = str(uuid.uuid5(NS_TPL, "ats_battery_charger_v1"))
SEC = "7.18.2"
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
    ("phys_mech", "Inspect for physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted electrical connections torqued (calibrated wrench; Table 100.12)", "A", 5, False, "visual_mechanical"),
    ("filter_tank_caps", "Inspect filter and tank capacitors", "A", 6, False, "visual_mechanical"),
    ("cooling_fans", "Verify operation of cooling fans and presence of filters", "A", 7, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 8, True, "visual_mechanical"),
    ("bolted_r", "Resistance through all bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("float_equalize", "Verify float voltage and equalize voltage", "B", 2, False, "charger_settings"),
    ("hv_shutdown", "Verify high-voltage shutdown settings", "B", 3, False, "charger_settings"),
    ("load_sharing", "Verify correct load sharing (parallel chargers)", "B", 4, False, "charger_settings"),
    ("meter_cal", "Verify calibration of meters (Section 7.11)", "B", 5, False, "functional"),
    ("alarms", "Verify operation of alarms", "B", 6, False, "functional"),
    ("input_output", "Measure and record input and output voltage and current", "B", 7, False, "output_measurements"),
    ("ac_ripple", "Measure and record ac ripple current and voltage imposed on the battery", "B", 8, False, "output_measurements"),
    ("full_load_current_limit", "Perform full-load testing and verify current limit of charger", "B", 9, False, "output_measurements"),
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
        ctl("ac_input_voltage", "AC input voltage", "numeric", "inherited", unit="V"),
        ctl("dc_output_voltage", "DC output voltage", "numeric", "inherited", unit="V"),
        ctl("output_current_rating", "DC output current rating", "numeric", "inherited", unit="A"),
        ctl("charger_type", "Charger type", "selection", "inherited", options=["scr", "ferroresonant", "switchmode"]),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    charger_settings = [
        ctl("float_voltage", "Float voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.2"),
        ctl("equalize_voltage", "Equalize voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.2"),
        ctl("hv_shutdown_v", "High-voltage shutdown setting", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.3"),
        ctl("load_sharing", "Correct load sharing (parallel chargers)", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.4"),
    ]
    functional = [
        ctl("meter_calibration_xref", "Meters calibrated per Section 7.11 (recorded on the metering datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.5"),
        ctl("alarms", "Alarms operational", "selection", "data", options=COND, neta_ref=f"{SEC}.B.6"),
    ]
    output_measurements = [
        ctl("input_voltage_v", "Input voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.7"),
        ctl("input_current_a", "Input current", "numeric", "data", unit="A"),
        ctl("output_voltage_v", "Output voltage", "numeric", "data", unit="V"),
        ctl("output_current_a", "Output current", "numeric", "data", unit="A"),
        ctl("ac_ripple_voltage_v", "AC ripple voltage on battery", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.8"),
        ctl("ac_ripple_current_a", "AC ripple current on battery", "numeric", "data", unit="A"),
        ctl("full_load_current_a", "Full-load output current", "numeric", "data", unit="A", neta_ref=f"{SEC}.B.9"),
        ctl("current_limit_a", "Current-limit setting", "numeric", "data", unit="A",
            acceptance={"basis": "mfr_tolerance", "rule": "vs mfr current-limit spec"}),
        ctl("current_limit_result", "Current limit within tolerance", "selection", "data", options=COND),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "charger_settings", "title": "Charger Settings", "kind": "fields", "fields": charger_settings},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        {"key": "output_measurements", "title": "Output Measurements", "kind": "fields", "fields": output_measurements},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "battery_charger", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["settings", "output_measurements"]}],
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
    assert not missing, f"charger gap: {sorted(missing)}"
    assert not phantom, f"charger phantom: {sorted(phantom)}"
    assert len(required) == 17, f"charger expected 17, got {len(required)}"
    assert len(schema["sections"]) == 9, f"charger sections={len(schema['sections'])} != 9"
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
        "-- Records Chip 2c - Battery Charger datasheet (ats_battery_charger_v1).",
        "-- GENERATED by gen_charger_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.18.2, 17 ATS items (companion to the battery sheet 025).",
        "-- Float/equalize, hv-shutdown, parallel load-sharing, ripple, full-load + current-limit;",
        "-- meter calibration cross-refs 7.11. R-A: mfr. Capture: field + cover_attach. UUID5.",
        f"-- Coverage: {n}/17 (7.18.2).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(CHG_ID, "ats_battery_charger_v1", "Battery Charger - ATS Field Data Sheet",
                     SEC, "battery_charger", schema, "Battery Charger datasheet (NETA 7.18.2). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"charger: sections={len(schema['sections'])} covered={n}/17")


if __name__ == "__main__":
    main()
