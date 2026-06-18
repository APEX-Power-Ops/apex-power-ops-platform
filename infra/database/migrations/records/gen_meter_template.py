#!/usr/bin/env python3
"""Generate 028_meter_template.sql - the Metering Device datasheet (NETA 7.11.2).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_meter_v1 -> leaf 'meter'.
NETA 7.11.2 (Metering Devices, Microprocessor-Based) = 10 VM + 3 electrical = 13 items (record
fw/sw/voltage, display, passwords, grounding/connection, settings upload; analog-input verification,
auxiliary I/O, energized consistency per ANSI/NETA ECS). R-A: mfr (metering accuracy vs mfr spec;
no IR section). Capture = field + cover_attach.

7.11.1 (electromechanical/solid-state) is a follow-on fold (a meter_kind selector, same recipe).
Coverage invariant (fail-fast here, re-checked in test_028). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_meter_template.py [path-to-json]
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
OUT = os.path.join(HERE, "028_meter_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
MTR_ID = str(uuid.uuid5(NS_TPL, "ats_meter_v1"))
SEC = "7.11.2"
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
    ("phys_damage", "Inspect meters and cases for physical damage", "A", 2, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 3, False, "visual_mechanical"),
    ("tightness", "Verify tightness of electrical connections", "A", 4, False, "visual_mechanical"),
    ("record_nameplate", "Record model, serial, firmware revision, software revision, and rated control voltage", "A", 5, False, "identification"),
    ("display_indicating", "Verify operation of display and indicating devices", "A", 6, False, "visual_mechanical"),
    ("record_passwords", "Record passwords", "A", 7, False, "settings"),
    ("grounded", "Verify unit is grounded per manufacturer instructions", "A", 8, False, "visual_mechanical"),
    ("connected", "Verify unit is connected per manufacturer instructions and project drawings", "A", 9, False, "visual_mechanical"),
    ("upload_settings", "Upload owner-supplied settings file", "A", 10, False, "settings"),
    ("analog_inputs", "Apply voltage or current to each analog input; verify correct measurement and indication", "B", 1, False, "input_verification"),
    ("aux_io", "Confirm operation and setting of each auxiliary input/output feature in use (relay, digital, analog)", "B", 2, False, "functional_io"),
    ("energized_consistency", "After energization, confirm measurements are consistent with loads (ANSI/NETA ECS)", "B", 3, False, "energized_check"),
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
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model", neta_ref=f"{SEC}.A.5"),
        ctl("serial_no", "Serial no.", "text", "inherited", neta_ref=f"{SEC}.A.5"),
        ctl("firmware_rev", "Firmware revision", "text", "data", neta_ref=f"{SEC}.A.5"),
        ctl("software_rev", "Software revision", "text", "data", neta_ref=f"{SEC}.A.5"),
        ctl("rated_control_voltage", "Rated control voltage", "numeric", "inherited", unit="V", neta_ref=f"{SEC}.A.5"),
        ctl("ct_ratio", "CT ratio", "text", "data"),
        ctl("pt_ratio", "PT ratio", "text", "data"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    settings = [
        ctl("passwords_recorded", "Passwords recorded", "selection", "data", options=COND, neta_ref=f"{SEC}.A.7"),
        ctl("settings_file_uploaded", "Owner-supplied settings file uploaded", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.A.10"),
    ]
    functional_io = [
        ctl("aux_io_verified", "Auxiliary I/O features operate and set correctly (relay, digital, analog)",
            "selection", "data", options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.2"),
    ]
    energized_check = [
        ctl("energized_consistency", "Energized measurements consistent with present loads (ANSI/NETA ECS)",
            "selection", "data", options=COND, neta_ref=f"{SEC}.B.3"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "settings", "title": "Settings and Passwords", "kind": "fields", "fields": settings},
        {"key": "input_verification", "title": "Analog-Input Verification", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "input", "label": "Analog input",
                               "rows": ["Va", "Vb", "Vc", "Ia", "Ib", "Ic"], "grow": True},
                   "columns": [ctl("applied", "Applied", "numeric"),
                               ctl("measured", "Meter reading", "numeric",
                                   acceptance={"basis": "mfr_tolerance", "rule": "vs meter accuracy class"},
                                   tolerance_source={"engine": "mfr", "function": "metering_accuracy",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("error_pct", "Error", "numeric", unit="pct"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "functional_io", "title": "Auxiliary I/O Functional Checks", "kind": "fields",
         "fields": functional_io},
        {"key": "energized_check", "title": "Energized Verification", "kind": "fields",
         "fields": energized_check},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "meter", "capture": CAPTURE,
            "selections": [{"tag": "meter_kind", "label": "Meter kind", "value_kind": "selection",
                            "options": ["microprocessor"], "default": "microprocessor",
                            "note": "electromechanical/solid-state (7.11.1) is a follow-on fold"}],
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
    assert not missing, f"meter gap: {sorted(missing)}"
    assert not phantom, f"meter phantom: {sorted(phantom)}"
    assert len(required) == 13, f"meter expected 13, got {len(required)}"
    assert len(schema["sections"]) == 9, f"meter sections={len(schema['sections'])} != 9"
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
        "-- Records Chip 2c - Metering Device datasheet (ats_meter_v1).",
        "-- GENERATED by gen_meter_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.11.2 (Microprocessor-Based), 13 ATS items.",
        "-- Record fw/sw/voltage, display, passwords, grounding/connection, settings upload;",
        "-- analog-input verification, auxiliary I/O, energized consistency (ANSI/NETA ECS).",
        "-- R-A: mfr (metering accuracy vs spec; no IR). Capture: field + cover_attach. UUID5.",
        f"-- Coverage: {n}/13 (7.11.2).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(MTR_ID, "ats_meter_v1", "Metering Device - ATS Field Data Sheet",
                     SEC, "meter", schema,
                     "Metering Device datasheet (NETA 7.11.2, Microprocessor-Based). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"meter: sections={len(schema['sections'])} covered={n}/13")


if __name__ == "__main__":
    main()
