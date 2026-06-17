#!/usr/bin/env python3
"""Generate 016_grounding_template.sql - the Grounding-System datasheet (NETA 7.13).

One leaf-bound single-procedure sheet (the smallest family): ats_grounding_v1 -> grounding_system;
NETA 7.13 (Grounding Systems); 6 ATS (3 VM + 3 electrical).

NOT PowerDB-anchored (no grounding form in the RESA PowerDB corpus) -> NETA-derived field structure.
R-A: a grounding system has no integral trip curve and no NETA IR/dielectric acceptance table, so
tolerance_source.engine is `mfr` only (ground resistance vs design / IEEE 81 / NEC spec; bolted-
connection resistance vs mfr) - never tcc; torque -> Table 100.12 stays an acceptance basis on the
VM row (not a tolerance_source window).

Capture-mode: the universal `attachments` cover section (Path 1) applies; there is NO instrument
bridge for ground testers, so capture.modes = [field, cover_attach] (no instrument_import).

Coverage invariant (fail-fast here, re-checked in test_016): union of section neta_covers covers all
7.13 ATS visual_mechanical+electrical items.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_grounding_template.py [path-to-json]
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
OUT = os.path.join(HERE, "016_grounding_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
GND_ID = str(uuid.uuid5(NS_TPL, "ats_grounding_v1"))
SEC = "7.13"
COND = ["sat", "unsat", "na"]
# No instrument bridge exists for ground testers -> field + cover only.
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat A=visual_mechanical / B=electrical, item_no, optional, section_key)
CONCEPTS = [
    ("nec250", "Ground system complies with drawings, specs, and NFPA 70 (NEC Article 250)", "A", 1, False, "identification"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.13.B.1)", "A", 3, False, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("fall_of_potential", "Fall-of-potential or alternative test (IEEE 81) on the main grounding electrode/system", "B", 2, False, "ground_resistance"),
    ("point_to_point", "Point-to-point resistance: main grounding system to equipment frames, system neutral, derived neutrals", "B", 3, False, "point_to_point"),
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
        rows.append({"key": c[0], "label": c[1], "neta_ref": f"{SEC}.{c[2]}.{c[3]}"})
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
# Path 1: a ground-grid study / fall-of-potential report can be attached as the cover/evidence.
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (study / report)", "kind": "attachment",
               "capture_mode": "cover_attach",
               "fields": [ctl("report", "Attached study / test report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["engineer_of_record", "third_party_lab", "field_instrument"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements", "selection", "data", options=COND)]}


def build():
    cov = covers_by_sec()
    sections = [
        {"key": "identification", "title": "Grounding System Identification", "kind": "fields",
         "fields": [ctl("system_description", "Grounding system / location", "text", "inherited"),
                    ctl("drawings_ref", "Reference drawings / specification", "text", "data"),
                    ctl("electrode_type", "Electrode type", "selection", "data",
                        options=["rod", "plate", "grid", "ufer_concrete_encased", "ring", "other"]),
                    ctl("nec_250_compliance", "Compliant with drawings, specs, NEC Article 250", "selection", "data", options=COND)]},
        vm_section(),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "fields",
         "fields": [ctl("resistance_uohm", "Resistance (low-resistance ohmmeter)", "numeric", "data", unit="uohm",
                        acceptance={"basis": "mfr_tolerance", "note": "vs mfr / comparison"},
                        tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                          "inputs": ["connection_type"]}),
                    ctl("result", "Within tolerance", "selection", "data", options=COND)]},
        {"key": "ground_resistance", "title": "Ground Resistance (fall-of-potential / IEEE 81)", "kind": "fields",
         "fields": [ctl("method", "Method", "selection", "data",
                        options=["fall_of_potential", "clamp_on", "three_point", "slope", "other"]),
                    ctl("test_standard", "Test standard", "text", "data"),
                    ctl("measured_ohms", "Measured ground resistance", "numeric", "data", unit="ohm",
                        acceptance={"basis": "design_spec", "note": "design / IEEE 81 / NEC limit"},
                        tolerance_source={"engine": "mfr", "function": "ground_resistance",
                                          "inputs": ["design_limit_ohms"]}),
                    ctl("soil_condition", "Soil / weather condition", "text", "data", optional=True)]},
        {"key": "point_to_point", "title": "Point-to-Point Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "path", "label": "Measured path", "rows": [
                       {"key": "equipment_frames", "label": "Equipment frames"},
                       {"key": "system_neutral", "label": "System neutral"},
                       {"key": "derived_neutral", "label": "Derived neutral point(s)", "optional": True}],
                       "grow": True},
                   "columns": [ctl("from_point", "From", "text"),
                               ctl("to_point", "To", "text"),
                               ctl("resistance_ohm", "Resistance", "numeric", unit="ohm",
                                   acceptance={"basis": "comparison", "note": "low / uniform vs design"}),
                               ctl("result", "Result", "selection", options=COND)]}},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "grounding", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["bolted_resistance", "ground_resistance", "point_to_point"]}],
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
    assert not missing, f"grounding gap: {sorted(missing)}"
    assert not phantom, f"grounding phantom: {sorted(phantom)}"
    assert len(required) == 6, f"grounding expected 6, got {len(required)}"
    assert len(schema["sections"]) == 8, f"grounding sections={len(schema['sections'])} != 8"
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
    g = build()
    n = check(g, src)
    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Grounding-System datasheet (ats_grounding_v1).",
        "-- GENERATED by gen_grounding_template.py - do not edit by hand.",
        "-- One leaf-bound single-procedure sheet: NETA 7.13 (Grounding Systems), 6 ATS.",
        "-- NOT PowerDB-anchored (no grounding form in the corpus) -> NETA-derived. R-A: mfr only",
        "-- (ground resistance vs design / IEEE 81; bolted-conn R) - NO tcc, NO neta_table window",
        "-- (torque -> 100.12 = acceptance basis on the VM row). Capture: field + cover_attach (no",
        "-- instrument bridge for ground testers). Windows resolved at provisioning. Idempotent UUID5.",
        f"-- Coverage: {n}/6 (7.13).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(GND_ID, "ats_grounding_v1", "Grounding System - ATS Field Data Sheet",
                     SEC, "grounding_system", g, "Grounding-system datasheet (NETA 7.13). Chip 2b; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"grounding: sections={len(g['sections'])} covered={n}/6")


if __name__ == "__main__":
    main()
