#!/usr/bin/env python3
"""Generate 030_busway_template.sql - the Metal-Enclosed Busway datasheet (NETA 7.4).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_busway_v1 -> leaf 'busway'.
NETA 7.4 (Metal-Enclosed Busways) = 10 VM + 7 electrical = 17 items (single-line connection, joint
torque, orientation/cooling, weep plugs, joint shield; bolted + assembled-connection resistance, IR
(Table 100.1), dielectric withstand (Table 100.17), tie-section phasing, space heaters, online PD).
R-A: IR -> 100.1 + dielectric -> 100.17 (neta_table); bolted/assembled R -> mfr. Capture = field +
cover_attach.

Coverage invariant (fail-fast here, re-checked in test_030). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_busway_template.py [path-to-json]
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
OUT = os.path.join(HERE, "030_busway_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
BUS_ID = str(uuid.uuid5(NS_TPL, "ats_busway_v1"))
SEC = "7.4"
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
    ("connection_sld", "Verify correct connection in accordance with single-line diagram", "A", 4, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted connections and bus joints (calibrated torque-wrench; Table 100.12)", "A", 5, False, "visual_mechanical"),
    ("orientation", "Confirm physical orientation per manufacturer labels to ensure adequate cooling", "A", 6, False, "visual_mechanical"),
    ("weep_plugs", "Verify weep or drain plugs are in accordance with manufacturer published data", "A", 7, False, "visual_mechanical"),
    ("joint_shield", "Verify correct installation of joint shield", "A", 8, False, "visual_mechanical"),
    ("vents_clean", "Verify ventilating openings are clean", "A", 9, False, "visual_mechanical"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 10, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections and bus joints (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "Insulation-resistance test, one minute, phase-to-phase and phase-to-ground (Table 100.1)", "B", 2, False, "insulation_resistance"),
    ("dielectric", "Dielectric withstand voltage test, phase-to-ground (Table 100.17)", "B", 3, True, "dielectric_withstand"),
    ("assembled_r", "Connection resistance of assembled busway (low-resistance ohmmeter)", "B", 4, False, "assembled_resistance"),
    ("phasing", "Phasing test on each busway tie section energized by separate sources", "B", 5, False, "phasing"),
    ("space_heater", "Verify operation of busway space heaters", "B", 6, False, "functional"),
    ("pd_survey", "Perform online partial-discharge survey (Section 11)", "B", 7, True, "pd_survey"),
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
        ctl("bus_material", "Bus material", "selection", "inherited", options=["copper", "aluminum"]),
        ctl("run_length_ft", "Run length", "numeric", "data", unit="ft"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    phasing = [
        ctl("phase_rotation", "Phase rotation", "selection", "data", options=["abc", "cba"]),
        ctl("tie_phasing", "Tie-section phasing verified (separate sources, permanent sources)",
            "selection", "data", options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.5"),
    ]
    functional = [
        ctl("space_heater", "Busway space heaters operational", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.6"),
    ]
    pd_survey = [
        ctl("pd_survey", "Online partial-discharge survey performed (Section 11)", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.7"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "bolted_resistance", "title": "Bolted-Connection / Bus-Joint Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "joint", "label": "Connection / joint", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "measurement", "label": "Measurement",
                               "rows": ["P1-P2", "P2-P3", "P1-P3", "P1-G", "P2-G", "P3-G"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "dielectric_withstand", "title": "Dielectric Withstand", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "phase", "label": "Phase (to ground, others grounded)",
                               "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV",
                                   acceptance={"basis": "neta_table", "table": "100.17"},
                                   tolerance_source={"engine": "neta_table", "table": "100.17",
                                                     "function": "dielectric_withstand",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("leakage_ua", "Leakage", "numeric", unit="uA"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "assembled_resistance", "title": "Assembled-Busway Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.4",
         "table": {"row_dim": {"tag": "phase", "label": "Phase", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "connection_resistance",
                                                     "inputs": ["manufacturer", "model"]})]}},
        {"key": "phasing", "title": "Phasing", "kind": "fields", "fields": phasing},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        {"key": "pd_survey", "title": "Partial-Discharge Survey", "kind": "fields", "fields": pd_survey},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "busway", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "dielectric_withstand", "phasing"]}],
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
    assert not missing, f"busway gap: {sorted(missing)}"
    assert not phantom, f"busway phantom: {sorted(phantom)}"
    assert len(required) == 17, f"busway expected 17, got {len(required)}"
    assert len(schema["sections"]) == 12, f"busway sections={len(schema['sections'])} != 12"
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
        "-- Records Chip 2c - Metal-Enclosed Busway datasheet (ats_busway_v1).",
        "-- GENERATED by gen_busway_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.4, 17 ATS items.",
        "-- SLD connection, joint torque, orientation/cooling, weep plugs, joint shield;",
        "-- bolted + assembled-connection resistance, IR (100.1), dielectric (100.17),",
        "-- tie-section phasing, space heaters, online PD. R-A: neta_table + mfr. UUID5.",
        f"-- Coverage: {n}/17 (7.4).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(BUS_ID, "ats_busway_v1", "Metal-Enclosed Busway - ATS Field Data Sheet",
                     SEC, "busway", schema,
                     "Metal-Enclosed Busway datasheet (NETA 7.4). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"busway: sections={len(schema['sections'])} covered={n}/17")


if __name__ == "__main__":
    main()
