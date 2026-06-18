#!/usr/bin/env python3
"""Generate 027_switch_template.sql - the Disconnect / Load-Interrupter Switch datasheet (NETA 7.5.1.1).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_switch_disconnect_v1 -> leaf
'switch_disconnect'. NETA 7.5.1.1 (Switches, Air, Low-Voltage) = 13 VM + 7 electrical = 20 items
(blade alignment, fuse sizes + support, interlocks, phase barriers; bolted/contact/insulation/fuse
resistance, space heater, GF + protective-device cross-refs). Fused-disconnect: a dedicated fuse_data
section carries A.6 (sizes/types) + B.4 (fuse resistance). R-A: IR -> Table 100.1 (neta_table),
contact/bolted/fuse -> mfr. Capture = field + cover_attach.

MV/SF6/oil/vacuum variants (7.5.1.2 / 7.5.2 / 7.5.3 / 7.5.4) are follow-on folds (a switch_medium
selector, same recipe). Coverage invariant (fail-fast here, re-checked in test_027). ASCII-only.
Deterministic UUID5. Run: uv run --no-project python gen_switch_template.py [path-to-json]
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
OUT = os.path.join(HERE, "027_switch_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
SW_ID = str(uuid.uuid5(NS_TPL, "ats_switch_disconnect_v1"))
SEC = "7.5.1.1"
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
    ("anchorage", "Inspect anchorage, alignment, grounding, and required clearances", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("blade_alignment", "Verify blade alignment, penetration, travel stops, and mechanical operation", "A", 5, False, "visual_mechanical"),
    ("fuse_sizes", "Verify fuse sizes and types per drawings, short-circuit study, and coordination study", "A", 6, False, "fuse_data"),
    ("fuse_support", "Verify each fuse has adequate mechanical support and contact integrity", "A", 7, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 8, False, "visual_mechanical"),
    ("interlocks", "Verify operation and sequencing of interlocking systems", "A", 9, False, "visual_mechanical"),
    ("phase_barriers", "Verify correct phase barrier installation", "A", 10, False, "visual_mechanical"),
    ("indicating_control", "Verify correct operation of all indicating and control devices", "A", 11, False, "visual_mechanical"),
    ("lubrication", "Verify appropriate lubrication on moving current-carrying and sliding surfaces", "A", 12, False, "visual_mechanical"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 13, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("contact_r", "Contact resistance across each switchblade and fuseholder", "B", 2, False, "contact_resistance"),
    ("insulation_r", "Insulation-resistance test, one minute, each pole, ph-ph and ph-gnd (Table 100.1)", "B", 3, False, "insulation_resistance"),
    ("fuse_r", "Measure fuse resistance", "B", 4, False, "fuse_data"),
    ("space_heater", "Verify cubicle space heater operation", "B", 5, False, "functional"),
    ("ground_fault", "Perform ground fault test (Section 7.14)", "B", 6, True, "protective_xref"),
    ("protective_devices", "Perform tests on other protective devices (Section 7.9)", "B", 7, True, "protective_xref"),
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
        ctl("continuous_current", "Continuous current rating", "numeric", "inherited", unit="A"),
        ctl("interrupting_rating", "Interrupting / withstand rating", "numeric", "inherited", unit="A"),
        ctl("poles", "Number of poles", "numeric", "inherited"),
        ctl("fused", "Fused switch", "boolean", "inherited"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    functional = [
        ctl("space_heater", "Cubicle space heater operational", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.5"),
    ]
    protective_xref = [
        ctl("ground_fault_xref", "Ground fault test performed per Section 7.14 (recorded on the GF datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.6"),
        ctl("protective_devices_xref", "Other protective devices tested per Section 7.9 (recorded on the relay datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.7"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "fuse_data", "title": "Fuse Data and Resistance", "kind": "table",
         "neta_basis": SEC,
         "table": {"row_dim": {"tag": "position", "label": "Pole / position", "rows": [], "grow": True},
                   "columns": [ctl("fuse_manufacturer", "Mfr", "text"),
                               ctl("fuse_class", "Class / type", "text"),
                               ctl("fuse_rating_a", "Rating", "numeric", unit="A", neta_ref=f"{SEC}.A.6"),
                               ctl("fuse_micro_ohms", "Fuse resistance", "numeric", unit="uohm", neta_ref=f"{SEC}.B.4",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "fuse_resistance",
                                                     "inputs": ["fuse_manufacturer", "fuse_class"]})]}},
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "contact_resistance", "title": "Switchblade / Fuseholder Contact Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "pole", "label": "Pole", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("blade_micro_ohms", "Switchblade", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "contact_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("fuseholder_micro_ohms", "Fuseholder", "numeric", unit="uohm")]}},
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "measurement", "label": "Measurement",
                               "rows": ["P1-P2", "P2-P3", "P1-P3", "P1-G", "P2-G", "P3-G",
                                        "Across open P1", "Across open P2", "Across open P3"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        {"key": "protective_xref", "title": "Protective-Device Cross-References", "kind": "fields",
         "fields": protective_xref},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "switch_disconnect", "capture": CAPTURE,
            "selections": [{"tag": "switch_medium", "label": "Switching medium", "value_kind": "selection",
                            "options": ["air_lv"], "default": "air_lv",
                            "note": "MV air/oil/vacuum/SF6 variants are follow-on folds"}],
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
    assert not missing, f"switch gap: {sorted(missing)}"
    assert not phantom, f"switch phantom: {sorted(phantom)}"
    assert len(required) == 20, f"switch expected 20, got {len(required)}"
    assert len(schema["sections"]) == 11, f"switch sections={len(schema['sections'])} != 11"
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
        "-- Records Chip 2c - Disconnect / Load-Interrupter Switch datasheet (ats_switch_disconnect_v1).",
        "-- GENERATED by gen_switch_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.5.1.1 (Switches, Air, Low-Voltage), 20 ATS items.",
        "-- Blade alignment, fuse sizes + support, interlocks; bolted/contact/insulation/fuse resistance,",
        "-- space heater, GF (7.14) + protective-device (7.9) cross-refs. IR R-A: Table 100.1.",
        "-- Fused-disconnect: dedicated fuse_data section. Capture: field + cover_attach. UUID5.",
        f"-- Coverage: {n}/20 (7.5.1.1).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(SW_ID, "ats_switch_disconnect_v1", "Disconnect / Load-Interrupter Switch - ATS Field Data Sheet",
                     SEC, "switch_disconnect", schema,
                     "Disconnect / Load-Interrupter Switch datasheet (NETA 7.5.1.1, Air LV). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"switch: sections={len(schema['sections'])} covered={n}/20")


if __name__ == "__main__":
    main()
