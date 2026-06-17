#!/usr/bin/env python3
"""Generate 013_switchgear_templates.sql - the switchgear + panelboard datasheets.

Switchgear differs from breakers/transformers: FOUR leaves share NETA 7.1.1 (LV switchboard /
MV metal-clad / pad-mount / VFI), and panelboard is its own 7.1.2. So:
  - ats_switchgear_v1 covers 7.1.1 (35 ATS), with an assembly_type selector for the 4 types,
    and binds to the PARENT `switchgear` node (the 7.1.1 procedure's home) - four leaves share
    the procedure, so it cannot 1:1-bind to a leaf the way the prior sheets did. assembly_type
    is context (the four types share 7.1.1 identically; it changes no coverage).
  - ats_panelboard_v1 covers 7.1.2 (14 ATS), leaf-bound to `swgr_panelboard`.

R-A: a switchgear assembly has no integral trip curve, so tolerance_source.engine is neta_table
(IR -> Table 100.1, dielectric -> Table 100.2, torque -> 100.12) or mfr (bolted-connection
resistance) - never tcc. The IT (7.10) / surge-arrester (7.19) / ground (7.13) / metering (7.11)
items are cross-ref borrows covered (not fabricated): the actual tests live on those datasheets.

Coverage invariant (fail-fast here, re-checked in test_013): per sheet, the union of every
section's neta_covers covers all ATS visual_mechanical+electrical items of its procedure.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_switchgear_template.py [path-to-json]
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
OUT = os.path.join(HERE, "013_switchgear_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
SWGR_ID = str(uuid.uuid5(NS_TPL, "ats_switchgear_v1"))
PANEL_ID = str(uuid.uuid5(NS_TPL, "ats_panelboard_v1"))

SWGR_SEC = "7.1.1"
PANEL_SEC = "7.1.2"
COND = ["sat", "unsat", "na"]


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat, item_no, optional, section)
SWGR_CONCEPTS = [
    ("np_drawings", "Nameplate data compared with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Physical, electrical, and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Anchorage, alignment, grounding, required area clearances", "A", 3, False, "visual_mechanical"),
    ("clean_shipping", "Unit clean; shipping bracing / loose parts / docs removed", "A", 4, False, "visual_mechanical"),
    ("mimic_diagram", "Mimic diagram and device labeling vs drawings", "A", 5, False, "visual_mechanical"),
    ("fuse_breaker_sizes", "Fuse/breaker sizes and types vs drawings + coordination study", "A", 6, False, "visual_mechanical"),
    ("ct_vt_ratios", "CT/VT ratios vs drawings", "A", 7, False, "visual_mechanical"),
    ("wiring_connections", "Wiring connections tight and secure", "A", 8, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (calibrated wrench; Table 100.12)", "A", 9, False, "visual_mechanical"),
    ("interlocks", "Electrical/mechanical interlock operation and sequencing", "A", 10, False, "visual_mechanical"),
    ("lubrication", "Lubrication of moving current-carrying / sliding parts", "A", 11, False, "visual_mechanical"),
    ("insulators", "Insulators inspected for damage / contamination", "A", 12, False, "visual_mechanical"),
    ("barrier_shutter", "Barrier and shutter installation / operation", "A", 13, False, "visual_mechanical"),
    ("exercise_components", "Exercise all active components", "A", 14, False, "visual_mechanical"),
    ("mechanical_indicators", "Mechanical indicating devices operate correctly", "A", 15, False, "visual_mechanical"),
    ("filters_vents", "Filters in place and vents clear", "A", 16, False, "visual_mechanical"),
    ("it_visual", "Instrument-transformer visual/mechanical inspection per Section 7.10", "A", 17, False, "instrument_transformers"),
    ("sa_visual", "Surge-arrester visual/mechanical inspection per Section 7.19", "A", 18, False, "surge_arresters"),
    ("cpt_inspect", "Inspect control power transformers", "A", 19, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 20, True, "visual_mechanical"),
    ("bolted_r", "Bolted-connection resistance (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("bus_ir", "Insulation resistance per bus section, phase-phase + phase-ground (Table 100.1)", "B", 2, False, "insulation_resistance"),
    ("dielectric", "Dielectric withstand per bus section, phase-to-ground (Table 100.2)", "B", 3, False, "dielectric_withstand"),
    ("control_wiring_ir", "Control-wiring insulation resistance (500/1000 Vdc)", "B", 4, True, "insulation_resistance"),
    ("it_electrical", "Instrument-transformer electrical tests per Section 7.10", "B", 5, False, "instrument_transformers"),
    ("ground_resistance", "Ground-resistance tests per Section 7.13", "B", 6, False, "ground_resistance"),
    ("metering", "Metering devices per Section 7.11", "B", 7, False, "metering"),
    ("cpt", "Control power transformers", "B", 8, False, "instrument_transformers"),
    ("vt", "Voltage transformers", "B", 9, False, "instrument_transformers"),
    ("current_injection", "Current-injection tests on the entire current circuit, each section", "B", 10, False, "functional"),
    ("system_function", "System function tests (ANSI/NETA ECS)", "B", 11, False, "functional"),
    ("space_heaters", "Cubicle switchgear/switchboard space heaters and controller", "B", 12, False, "functional"),
    ("phasing", "Phasing checks (double-ended / dual-source)", "B", 13, False, "functional"),
    ("sa_electrical", "Surge-arrester electrical tests per Section 7.19", "B", 14, False, "surge_arresters"),
    ("partial_discharge", "Online partial-discharge survey (Section 11)", "B", 15, True, "partial_discharge"),
]

PANEL_CONCEPTS = [
    ("np_drawings", "Nameplate data compared with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Physical, electrical, and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Anchorage, alignment, grounding, bonding, required area clearances", "A", 3, False, "visual_mechanical"),
    ("clean_shipping", "Unit clean; shipping bracing / loose parts removed", "A", 4, False, "visual_mechanical"),
    ("fuse_breaker_sizes", "Fuse/breaker sizes and types vs drawings + coordination study", "A", 5, False, "visual_mechanical"),
    ("wiring_connections", "Wiring connections tight and secure", "A", 6, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (calibrated wrench; Table 100.12)", "A", 7, False, "visual_mechanical"),
    ("insulators", "Insulators inspected for damage / contamination", "A", 8, False, "visual_mechanical"),
    ("barrier", "Barrier installation", "A", 9, False, "visual_mechanical"),
    ("spd_visual", "Surge protective devices visual/mechanical inspection", "A", 10, False, "visual_mechanical"),
    ("exercise_components", "Exercise all active components", "A", 11, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 12, True, "visual_mechanical"),
    ("bus_ir", "Insulation resistance per bus section, phase-phase + phase-ground (Table 100.1)", "B", 1, False, "insulation_resistance"),
    ("ground_resistance", "Ground-resistance tests per Section 7.13", "B", 2, False, "ground_resistance"),
]


def covers_by_sec(concepts, section_code):
    cov = {}
    for c in concepts:
        cov.setdefault(c[5], set()).add(f"{section_code}.{c[2]}.{c[3]}")
    return cov


def vm_rows(concepts, section_code):
    rows = []
    for c in concepts:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_ref": f"{section_code}.{c[2]}.{c[3]}"}
        if c[4]:
            r["optional"] = True
        rows.append(r)
    return rows


def vm_section(concepts, section_code):
    return {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
            "neta_basis": section_code,
            "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": vm_rows(concepts, section_code)},
                      "columns": [ctl("inspected", "Inspected", "boolean"),
                                  ctl("condition", "Condition", "selection", options=COND),
                                  ctl("value", "Value", "text"), ctl("note", "Note", "text")]}}


def ir_section(with_control_wiring):
    rows = [
        {"key": "phase_a_g", "label": "A-ground"}, {"key": "phase_b_g", "label": "B-ground"},
        {"key": "phase_c_g", "label": "C-ground"}, {"key": "phase_a_b", "label": "A-B"},
        {"key": "phase_b_c", "label": "B-C"}, {"key": "phase_c_a", "label": "C-A"},
    ]
    if with_control_wiring:
        rows.append({"key": "control_wiring", "label": "Control wiring", "optional": True})
    return {"key": "insulation_resistance", "title": "Insulation Resistance (per bus section)",
            "kind": "table",
            "table": {"row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
                      "columns": [
                          ctl("bus_section", "Bus section", "text"),
                          ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                          ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                              acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"},
                              tolerance_source={"engine": "neta_table", "table": "100.1",
                                                "inputs": ["voltage_rating"]}),
                          ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
                      ]}}


def ground_section():
    return {"key": "ground_resistance", "title": "Ground Resistance (Cross-Reference)", "kind": "fields",
            "neta_basis": "7.13",
            "fields": [ctl("ground_resistance_xref",
                           "Ground-resistance tests - perform per NETA Section 7.13", "text", "reference"),
                       ctl("ground_resistance_ohms", "Ground resistance", "numeric", "data", unit="ohm", optional=True)]}


def nameplate_section(extra, with_assembly_type):
    fields = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model"),
        ctl("serial_no", "Serial no.", "text", "inherited"),
        ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
        ctl("bus_rating", "Bus / continuous current rating", "numeric", "inherited", unit="A"),
        ctl("interrupting_rating", "Short-circuit / withstand rating", "numeric", "inherited", unit="kA"),
    ] + extra
    if with_assembly_type:
        fields.insert(3, ctl("assembly_type", "Assembly type", "selection", "inherited",
                             options=["lv_switchboard", "mv_metalclad", "padmount", "vfi"]))
    fields.append(ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data", options=COND))
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields", "fields": fields}


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


def build_switchgear():
    cov = covers_by_sec(SWGR_CONCEPTS, SWGR_SEC)
    sections = [
        nameplate_section([
            ctl("bus_arrangement", "Bus arrangement", "text", "inherited"),
            ctl("enclosure_type", "Enclosure / NEMA type", "text", "inherited"),
        ], with_assembly_type=True),
        vm_section(SWGR_CONCEPTS, SWGR_SEC),
        ir_section(with_control_wiring=True),
        {"key": "dielectric_withstand", "title": "Dielectric Withstand (per bus section)", "kind": "table",
         "table": {"row_dim": {"tag": "phase", "label": "Phase (others grounded)",
                               "rows": [{"key": "phase_a", "label": "Phase A"}, {"key": "phase_b", "label": "Phase B"},
                                        {"key": "phase_c", "label": "Phase C"}]},
                   "columns": [ctl("bus_section", "Bus section", "text"),
                               ctl("test_kv", "Test voltage", "numeric", unit="kV",
                                   acceptance={"basis": "mfr_tolerance", "fallback_table": "100.2"},
                                   tolerance_source={"engine": "neta_table", "table": "100.2",
                                                     "inputs": ["voltage_rating"]}),
                               ctl("duration_s", "Duration", "numeric", unit="s"),
                               ctl("result", "Result", "selection", options=["pass", "fail"])]}},
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "instrument_transformers", "title": "Instrument Transformers / CPT / VT", "kind": "fields",
         "fields": [ctl("it_xref", "Instrument transformers - visual + electrical tests per NETA Section 7.10 (recorded on the instrument-transformer datasheet)", "text", "reference"),
                    ctl("cpt_result", "Control power transformers tested", "selection", "data", options=COND),
                    ctl("vt_result", "Voltage transformers tested", "selection", "data", options=COND)]},
        {"key": "metering", "title": "Metering (Cross-Reference)", "kind": "fields",
         "neta_basis": "7.11",
         "fields": [ctl("metering_xref", "Metering devices - test per NETA Section 7.11", "text", "reference")]},
        ground_section(),
        {"key": "functional", "title": "Functional / System Tests", "kind": "fields",
         "fields": [ctl("current_injection", "Current-injection on each section's current circuit", "selection", "data", options=COND),
                    ctl("system_function", "System function tests (ANSI/NETA ECS)", "selection", "data", options=COND),
                    ctl("space_heaters", "Space heaters and controller operational", "selection", "data", options=COND),
                    ctl("phasing", "Phasing checks (double-ended / dual-source)", "selection", "data", options=COND)]},
        {"key": "surge_arresters", "title": "Surge Arresters (Cross-Reference)", "kind": "fields",
         "neta_basis": "7.19",
         "fields": [ctl("sa_xref", "Surge arresters - visual + electrical tests per NETA Section 7.19 (recorded on the surge-arrester datasheet)", "text", "reference")]},
        {"key": "partial_discharge", "title": "Partial Discharge (optional)", "kind": "fields",
         "fields": [ctl("pd_survey", "Online partial-discharge survey (Section 11)", "graph", "data", optional=True)]},
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "switchgear_assembly",
            "selections": [
                {"tag": "assembly_type", "label": "Assembly type", "value_kind": "selection",
                 "options": ["lv_switchboard", "mv_metalclad", "padmount", "vfi"], "ties_to": "equipment_model"},
                {"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                 "options": ["insulation_resistance", "dielectric_withstand", "bolted_resistance",
                             "current_injection", "system_function"]},
            ], "sections": sections}


def build_panelboard():
    cov = covers_by_sec(PANEL_CONCEPTS, PANEL_SEC)
    sections = [
        nameplate_section([
            ctl("mains_rating", "Mains rating", "numeric", "inherited", unit="A"),
            ctl("phase_config", "Phase / wire configuration", "text", "inherited"),
        ], with_assembly_type=False),
        vm_section(PANEL_CONCEPTS, PANEL_SEC),
        ir_section(with_control_wiring=False),
        ground_section(),
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "panelboard_assembly",
            "selections": [
                {"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                 "options": ["insulation_resistance", "ground_resistance"]},
            ], "sections": sections}


def required_refs(json_path, section):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == section)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({f"{section}.A.{i + 1}" for i in range(len(vm))}
            | {f"{section}.B.{i + 1}" for i in range(len(el))})


def check(schema, src, section, n_expect, sec_expect):
    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src, section)
    missing = required - covered
    phantom = {r for r in covered if r.startswith(section + ".")} - required
    assert not missing, f"{schema['family']} gap: {sorted(missing)}"
    assert not phantom, f"{schema['family']} phantom: {sorted(phantom)}"
    assert len(required) == n_expect, f"{schema['family']} expected {n_expect}, got {len(required)}"
    assert len(schema["sections"]) == sec_expect, f"{schema['family']} sections={len(schema['sections'])}"
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
    swgr = build_switchgear()
    panel = build_panelboard()
    sn = check(swgr, src, SWGR_SEC, 35, 13)
    pn = check(panel, src, PANEL_SEC, 14, 6)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Switchgear + Panelboard datasheets (ats_switchgear_v1, ats_panelboard_v1).",
        "-- GENERATED by gen_switchgear_template.py - do not edit by hand.",
        "-- Four leaves share NETA 7.1.1 -> ats_switchgear_v1 binds the PARENT `switchgear` node",
        "-- (assembly_type selector for the 4 types). ats_panelboard_v1 (7.1.2) is leaf-bound.",
        "-- R-A: tolerance_source = neta_table (IR 100.1, dielectric 100.2) + mfr (bolted-conn R);",
        "-- IT/SA/ground/metering = cross-ref borrows. NOT tcc. Windows resolved at provisioning.",
        f"-- Coverage: switchgear {sn}/35 (7.1.1); panelboard {pn}/14 (7.1.2). Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(SWGR_ID, "ats_switchgear_v1",
                     "Switchgear / Switchboard Assembly - ATS Field Data Sheet", SWGR_SEC, "switchgear", swgr,
                     "Composite switchgear/switchboard datasheet (7.1.1; assembly_type selector; parent-bound - 4 leaves share the procedure). Chip 2b.")
    out += sql_value(PANEL_ID, "ats_panelboard_v1",
                     "Panelboard Assembly - ATS Field Data Sheet", PANEL_SEC, "swgr_panelboard", panel,
                     "Panelboard datasheet (NETA 7.1.2). Chip 2b.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"switchgear: sections={len(swgr['sections'])} covered={sn}/35   "
          f"panelboard: sections={len(panel['sections'])} covered={pn}/14")


if __name__ == "__main__":
    main()
