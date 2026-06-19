#!/usr/bin/env python3
"""Generate 024_ups_template.sql - the Uninterruptible Power Systems datasheet (NETA 7.22.2).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_ups_v1 -> leaf 'ups'. NETA 7.22.2
= 10 VM + 10 electrical = 20 items. A UPS is a SYSTEM: electrical B.7-B.10 cross-ref the component
datasheets (breakers 7.6 / ATS 7.22.3 / batteries 7.18 / rotating machinery 7.15); B.1-B.6 are the
UPS-specific tests. R-A: neta_table (IR n/a here) + mfr; the cross-refs are `reference` data_source.
Capture = field + cover_attach.

Coverage invariant (fail-fast here, re-checked in test_024). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_ups_template.py [path-to-json]
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
OUT = os.path.join(HERE, "024_ups_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
UPS_ID = str(uuid.uuid5(NS_TPL, "ats_ups_v1"))
SEC = "7.22.2"
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
    ("fuse_sizes", "Verify fuse sizes and types correspond to drawings", "A", 4, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 5, False, "visual_mechanical"),
    ("interlocks", "Test electrical and mechanical interlock systems for operation and sequencing", "A", 6, False, "visual_mechanical"),
    ("torque", "Bolted electrical connections torqued (calibrated wrench; Table 100.12)", "A", 7, False, "visual_mechanical"),
    ("forced_ventilation", "Verify operation of forced ventilation", "A", 8, False, "visual_mechanical"),
    ("filters_vents", "Verify filters are in place and/or vents are clear", "A", 9, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 10, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("static_transfer", "Test static transfer from inverter to bypass and back (normal load if possible)", "B", 2, False, "ups_functional"),
    ("oscillator_freq", "Set free-running frequency of oscillator", "B", 3, False, "ups_functional"),
    ("dc_undervoltage_trip", "Test dc undervoltage trip level on inverter input breaker (mfr setting)", "B", 4, False, "ups_functional"),
    ("alarm_circuits", "Test alarm circuits", "B", 5, False, "ups_functional"),
    ("sync_indicators", "Verify synchronizing indicators for static switch and bypass switches", "B", 6, False, "ups_functional"),
    ("breakers_xref", "UPS system breakers tested per Section 7.6", "B", 7, False, "component_tests"),
    ("ats_xref", "UPS system automatic transfer switches tested per Section 7.22.3", "B", 8, False, "component_tests"),
    ("batteries_xref", "UPS system batteries tested per Section 7.18", "B", 9, False, "component_tests"),
    ("rotating_xref", "UPS rotating machinery tested per Section 7.15", "B", 10, False, "component_tests"),
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
        ctl("kva_rating", "Rating", "numeric", "inherited", unit="kVA"),
        ctl("input_voltage", "Input voltage", "numeric", "inherited", unit="V"),
        ctl("output_voltage", "Output voltage", "numeric", "inherited", unit="V"),
        ctl("topology", "Topology", "selection", "inherited",
            options=["online_double_conversion", "line_interactive", "standby"]),
        ctl("battery_runtime_min", "Rated battery runtime", "numeric", "inherited", unit="min"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    ups_functional = [
        ctl("static_transfer", "Static transfer inverter <-> bypass tested", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.2"),
        ctl("oscillator_freq", "Free-running oscillator frequency", "numeric", "data", unit="Hz",
            neta_ref=f"{SEC}.B.3"),
        ctl("dc_undervoltage_trip", "DC undervoltage trip level (inverter input breaker)", "numeric", "data",
            unit="V", acceptance={"basis": "mfr_tolerance", "rule": "per mfr published data"},
            neta_ref=f"{SEC}.B.4"),
        ctl("alarm_circuits", "Alarm circuits tested", "selection", "data", options=COND, neta_ref=f"{SEC}.B.5"),
        ctl("sync_indicators", "Synchronizing indicators verified (static + bypass)", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.6"),
    ]
    component_tests = [
        ctl("system_breakers_xref", "UPS system breakers - test per Section 7.6 (recorded on the breaker datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.7"),
        ctl("system_ats_xref", "UPS system transfer switches - test per Section 7.22.3 (recorded on the ATS datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.8"),
        ctl("system_batteries_xref", "UPS system batteries - test per Section 7.18 (recorded on the battery datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.9"),
        ctl("system_rotating_xref", "UPS rotating machinery - test per Section 7.15 (recorded on the machine datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.10"),
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
        {"key": "ups_functional", "title": "UPS Functional Tests", "kind": "fields", "fields": ups_functional},
        {"key": "component_tests", "title": "Component Tests (Cross-Reference)", "kind": "fields",
         "fields": component_tests},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "ups", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["functional", "component_tests"]}],
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
    assert not missing, f"UPS gap: {sorted(missing)}"
    assert not phantom, f"UPS phantom: {sorted(phantom)}"
    assert len(required) == 20, f"UPS expected 20, got {len(required)}"
    assert len(schema["sections"]) == 8, f"UPS sections={len(schema['sections'])} != 8"
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
        "-- Records Chip 2c - Uninterruptible Power Systems datasheet (ats_ups_v1).",
        "-- GENERATED by gen_ups_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.22.2, 20 ATS items. A UPS is a SYSTEM - electrical B.7-B.10",
        "-- cross-ref the component datasheets (7.6 / 7.22.3 / 7.18 / 7.15); B.1-B.6 are UPS-specific.",
        "-- R-A: mfr (functional / bolted R); cross-refs = reference. Capture: field + cover_attach. UUID5.",
        f"-- Coverage: {n}/20 (7.22.2).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(UPS_ID, "ats_ups_v1", "Uninterruptible Power System - ATS Field Data Sheet",
                     SEC, "ups", schema, "Uninterruptible Power System datasheet (NETA 7.22.2). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"UPS: sections={len(schema['sections'])} covered={n}/20")


if __name__ == "__main__":
    main()
