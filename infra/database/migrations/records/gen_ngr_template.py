#!/usr/bin/env python3
"""Generate 034_ngr_template.sql - the Neutral-Grounding Resistor datasheet (NETA 7.20.4 Resistors).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_ngr_v1 -> leaf 'ngr'. NETA
7.20.4 (Resistors) = 11 VM + 4 electrical = 15 items (liquid level, filters/vents, monitoring, torque;
bolted resistance, resistor-to-ground IR (Table 100.1), resistance value, instrument-transformer
cross-refs to 7.10). R-A: IR -> 100.1 (neta_table); resistance value / bolted -> mfr. Capture = field
+ cover_attach.

Coverage invariant (fail-fast here, re-checked in test_034). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_ngr_template.py [path-to-json]
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
OUT = os.path.join(HERE, "034_ngr_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
NGR_ID = str(uuid.uuid5(NS_TPL, "ats_ngr_v1"))
SEC = "7.20.4"
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
    ("anchorage", "Verify proper anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 5, False, "visual_mechanical"),
    ("liquid_level", "Verify correct liquid level in all tanks and bushings", "A", 6, False, "visual_mechanical"),
    ("mech_tests", "Perform mechanical inspections and tests as recommended by the manufacturer", "A", 7, False, "visual_mechanical"),
    ("filters_vents", "Verify that filters are in place and vents are clear", "A", 8, False, "visual_mechanical"),
    ("it_vm", "Visual and mechanical inspection of instrument transformers (Section 7.10)", "A", 9, False, "it_xref"),
    ("monitoring", "Verify monitoring and auxiliary systems", "A", 10, False, "visual_mechanical"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Resistor-to-ground insulation-resistance test (Table 100.1)", "B", 2, False, "insulation_resistance"),
    ("resistance_value", "Measure resistance value", "B", 3, False, "resistance_value"),
    ("it_electrical", "Electrical tests on instrument transformers (Section 7.10)", "B", 4, False, "it_xref"),
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
        ctl("rated_current", "Rated current", "numeric", "inherited", unit="A"),
        ctl("resistance_ohms", "Resistance", "numeric", "inherited", unit="ohm"),
        ctl("time_rating", "Time rating", "selection", "inherited",
            options=["10s", "1min", "10min", "extended", "continuous"]),
        ctl("cooling", "Cooling", "selection", "inherited", options=["dry", "liquid"]),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    it_xref = [
        ctl("it_vm_xref", "Instrument transformers inspected per Section 7.10 (recorded on the IT datasheet)",
            "text", "reference", neta_ref=f"{SEC}.A.9"),
        ctl("it_electrical_xref", "Instrument transformers electrically tested per Section 7.10 (recorded on the IT datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.4"),
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
        {"key": "insulation_resistance", "title": "Resistor-to-Ground Insulation Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "measurement", "label": "Measurement", "rows": ["Resistor-Ground"], "grow": True},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "resistance_value", "title": "Resistance Value", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "element", "label": "Resistor element / phase",
                               "rows": ["P1", "P2", "P3"], "grow": True},
                   "columns": [ctl("nameplate_ohms", "Nameplate", "numeric", unit="ohm"),
                               ctl("measured_ohms", "Measured", "numeric", unit="ohm",
                                   acceptance={"basis": "mfr_tolerance", "rule": "vs nameplate resistance"},
                                   tolerance_source={"engine": "mfr", "function": "resistance_value",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("deviation_pct", "Deviation", "numeric", unit="pct"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "it_xref", "title": "Instrument-Transformer Cross-References (Section 7.10)", "kind": "fields",
         "fields": it_xref},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "ngr", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "resistance_value"]}],
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
    assert not missing, f"ngr gap: {sorted(missing)}"
    assert not phantom, f"ngr phantom: {sorted(phantom)}"
    assert len(required) == 15, f"ngr expected 15, got {len(required)}"
    assert len(schema["sections"]) == 9, f"ngr sections={len(schema['sections'])} != 9"
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
        "-- Records Chip 2c - Neutral-Grounding Resistor datasheet (ats_ngr_v1).",
        "-- GENERATED by gen_ngr_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.20.4 (Resistors), 15 ATS items.",
        "-- Liquid level, filters/vents, monitoring, torque; bolted resistance, resistor-to-ground",
        "-- IR (100.1), resistance value, instrument-transformer cross-refs (7.10).",
        "-- R-A: IR -> 100.1 (neta_table); resistance value / bolted -> mfr. UUID5.",
        f"-- Coverage: {n}/15 (7.20.4).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(NGR_ID, "ats_ngr_v1", "Neutral-Grounding Resistor - ATS Field Data Sheet",
                     SEC, "ngr", schema,
                     "Neutral-Grounding Resistor datasheet (NETA 7.20.4 Resistors). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"ngr: sections={len(schema['sections'])} covered={n}/15")


if __name__ == "__main__":
    main()
