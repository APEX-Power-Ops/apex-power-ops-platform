#!/usr/bin/env python3
"""Generate 031_cap_bank_template.sql - the Capacitor Bank datasheet (NETA 7.20.1).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_cap_bank_v1 -> leaf 'cap_bank'.
NETA 7.20.1 (Capacitors) = 7 VM + 4 electrical = 11 items (configuration, torque; bolted resistance,
IR phase-to-case (Table 100.1), capacitance of all terminal combinations, internal discharge-resistor
resistance). R-A: IR -> 100.1 (neta_table); capacitance / discharge-R / bolted -> mfr. Capture = field
+ cover_attach.

Coverage invariant (fail-fast here, re-checked in test_031). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_cap_bank_template.py [path-to-json]
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
OUT = os.path.join(HERE, "031_cap_bank_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
CAP_ID = str(uuid.uuid5(NS_TPL, "ats_cap_bank_v1"))
SEC = "7.20.1"
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
    ("anchorage", "Inspect anchorage, alignment, grounding, and clearances", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("configuration", "Verify capacitors are electrically connected in their specified configuration", "A", 5, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 6, False, "visual_mechanical"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 7, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Insulation-resistance test, phase terminals to case, one minute (Table 100.1)", "B", 2, False, "insulation_resistance"),
    ("capacitance", "Measure capacitance of all terminal combinations", "B", 3, False, "capacitance"),
    ("discharge_r", "Measure resistance of the internal discharge resistors", "B", 4, False, "discharge_resistors"),
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
        ctl("rated_voltage", "Rated voltage", "numeric", "inherited", unit="V"),
        ctl("rated_kvar", "Rated reactive power", "numeric", "inherited", unit="kvar"),
        ctl("configuration", "Bank configuration", "selection", "inherited",
            options=["wye_grounded", "wye_ungrounded", "delta"]),
        ctl("num_units", "Number of capacitor units", "numeric", "inherited"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "insulation_resistance", "title": "Insulation Resistance (phase to case)", "kind": "table",
         "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "measurement", "label": "Measurement", "rows": ["Terminals-Case"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "capacitance", "title": "Capacitance", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "combination", "label": "Terminal combination", "rows": [], "grow": True},
                   "columns": [ctl("nameplate_uf", "Nameplate", "numeric", unit="uF"),
                               ctl("measured_uf", "Measured", "numeric", unit="uF",
                                   acceptance={"basis": "mfr_tolerance", "rule": "vs nameplate capacitance"},
                                   tolerance_source={"engine": "mfr", "function": "capacitance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "discharge_resistors", "title": "Internal Discharge Resistors", "kind": "table",
         "neta_basis": f"{SEC}.B.4",
         "table": {"row_dim": {"tag": "unit", "label": "Capacitor unit", "rows": [], "grow": True},
                   "columns": [ctl("resistance_kohm", "Discharge resistance", "numeric", unit="kohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "discharge_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]}},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "cap_bank", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "capacitance", "discharge_resistors"]}],
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
    assert not missing, f"cap gap: {sorted(missing)}"
    assert not phantom, f"cap phantom: {sorted(phantom)}"
    assert len(required) == 11, f"cap expected 11, got {len(required)}"
    assert len(schema["sections"]) == 9, f"cap sections={len(schema['sections'])} != 9"
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
        "-- Records Chip 2c - Capacitor Bank datasheet (ats_cap_bank_v1).",
        "-- GENERATED by gen_cap_bank_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.20.1, 11 ATS items.",
        "-- Configuration, torque; bolted resistance, IR phase-to-case (100.1), capacitance of all",
        "-- terminal combinations, internal discharge-resistor resistance.",
        "-- R-A: IR -> 100.1 (neta_table); capacitance / discharge-R / bolted -> mfr. UUID5.",
        f"-- Coverage: {n}/11 (7.20.1).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(CAP_ID, "ats_cap_bank_v1", "Capacitor Bank - ATS Field Data Sheet",
                     SEC, "cap_bank", schema,
                     "Capacitor Bank datasheet (NETA 7.20.1). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"cap: sections={len(schema['sections'])} covered={n}/11")


if __name__ == "__main__":
    main()
