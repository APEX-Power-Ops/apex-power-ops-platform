#!/usr/bin/env python3
"""Generate 014_cable_templates.sql - the cable datasheets (LV + MV/HV).

Two leaf-bound single-procedure sheets (the clean recipe, one procedure per leaf):
  - ats_lv_cable_v1   -> cable_lv;  NETA 7.3.2 (LV, 600 V max); 11 ATS.
  - ats_mvhv_cable_v1 -> cable_mv;  NETA 7.3.3 (MV/HV); 18 ATS - adds the shielded-cable
    HV battery (shield continuity, TDR, jacket integrity, dielectric withstand, tan-delta, PD).

R-A: a cable has no integral trip curve, so tolerance_source.engine is neta_table (MV IR ->
Table 100.1, tan-delta -> Table 100.6.6, torque -> 100.12) or mfr (LV IR comparison, MV
dielectric withstand) - never tcc. Windows declared, resolved at provisioning.

Coverage invariant (fail-fast here, re-checked in test_014): per sheet, the union of every
section's neta_covers covers all ATS visual_mechanical+electrical items of its procedure.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_cable_template.py [path-to-json]
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
OUT = os.path.join(HERE, "014_cable_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
LV_ID = str(uuid.uuid5(NS_TPL, "ats_lv_cable_v1"))
MV_ID = str(uuid.uuid5(NS_TPL, "ats_mvhv_cable_v1"))

LV_SEC = "7.3.2"
MV_SEC = "7.3.3"
COND = ["sat", "unsat", "na"]


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat, item_no, optional, section)
LV_CONCEPTS = [
    ("cable_data", "Cable data compared with drawings and specifications", "A", 1, False, "nameplate"),
    ("inspect_exposed", "Exposed cables/connectors: physical damage, termination, correct connection", "A", 2, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12)", "A", 3, False, "visual_mechanical"),
    ("compression_connectors", "Compression connectors: correct cable match and indentation", "A", 4, False, "visual_mechanical"),
    ("identification", "Correct identification and arrangement", "A", 5, False, "visual_mechanical"),
    ("jacket_insulation", "Cable jacket insulation and condition", "A", 6, False, "visual_mechanical"),
    ("ct_window", "Window-CT terminations: neutral/ground placed for protective-device operation", "A", 7, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 8, True, "visual_mechanical"),
    ("ir", "Insulation resistance per conductor (500/1000 Vdc, 1 min)", "B", 1, False, "insulation_resistance"),
    ("continuity", "Continuity test (correct cable connection)", "B", 2, False, "continuity"),
    ("parallel_resistance", "Uniform resistance of parallel conductors", "B", 3, True, "continuity"),
]

MV_CONCEPTS = [
    ("cable_data", "Cable data compared with drawings and specifications", "A", 1, False, "nameplate"),
    ("inspect_terminations", "Terminations, splices, exposed sections: physical damage", "A", 2, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12)", "A", 3, False, "visual_mechanical"),
    ("compression_connectors", "Compression connectors: correct cable match and indentation", "A", 4, False, "visual_mechanical"),
    ("shield_grounding", "Shield grounding and cable supports", "A", 5, False, "visual_mechanical"),
    ("bending_radius", "Cable bends >= ICEA / mfr minimum bending radius", "A", 6, False, "visual_mechanical"),
    ("fireproofing", "Fireproofing in common cable areas", "A", 7, True, "visual_mechanical"),
    ("ct_window", "Window-CT terminations: neutral/ground/shield placed for protective-device operation", "A", 8, False, "visual_mechanical"),
    ("identification", "Correct identification and arrangement", "A", 9, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 10, True, "visual_mechanical"),
    ("ir", "Insulation resistance per conductor-to-shield (Table 100.1)", "B", 1, False, "insulation_resistance"),
    ("shield_continuity", "Shield-continuity test (ohmmeter)", "B", 2, False, "shield_continuity"),
    ("tdr", "Time-domain reflectometer (TDR) on each conductor", "B", 3, True, "tdr"),
    ("jacket_integrity", "Jacket integrity test (1 min; 2 kV <=35 kV / 5 kV >35 kV)", "B", 4, True, "jacket_integrity"),
    ("dielectric_withstand", "Dielectric withstand test (VLF / DC / AC)", "B", 5, False, "dielectric_withstand"),
    ("tan_delta", "Tan-delta (insulation PF/DF) per conductor (Table 100.6.6 / 100.6.7)", "B", 6, True, "tan_delta"),
    ("online_pd", "Online partial-discharge test", "B", 7, True, "partial_discharge"),
    ("offline_pd", "Offline partial-discharge test (Table 100.6.3/.4/.5)", "B", 8, True, "partial_discharge"),
]


def covers_by_sec(concepts, section_code):
    cov = {}
    for c in concepts:
        cov.setdefault(c[5], set()).add(f"{section_code}.{c[2]}.{c[3]}")
    return cov


def vm_section(concepts, section_code):
    rows = []
    for c in concepts:
        if c[5] != "visual_mechanical":
            continue
        r = {"key": c[0], "label": c[1], "neta_ref": f"{section_code}.{c[2]}.{c[3]}"}
        if c[4]:
            r["optional"] = True
        rows.append(r)
    return {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
            "neta_basis": section_code,
            "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
                      "columns": [ctl("inspected", "Inspected", "boolean"),
                                  ctl("condition", "Condition", "selection", options=COND),
                                  ctl("value", "Value", "text"), ctl("note", "Note", "text")]}}


def conductor_rows():
    return [{"key": "cond_a", "label": "Conductor A"}, {"key": "cond_b", "label": "Conductor B"},
            {"key": "cond_c", "label": "Conductor C"}, {"key": "cond_n", "label": "Neutral", "optional": True}]


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


def cable_nameplate(extra):
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
            "fields": [
                ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
                ctl("cable_type", "Cable type", "text", "inherited"),
                ctl("conductor_size", "Conductor size (AWG/kcmil)", "text", "inherited"),
                ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
                ctl("insulation_type", "Insulation type", "text", "inherited"),
                ctl("length_ft", "Length", "numeric", "inherited", unit="ft"),
            ] + extra + [
                ctl("cable_data_vs_drawings", "Cable data compared with drawings", "selection", "data", options=COND),
            ]}


def build_lv():
    cov = covers_by_sec(LV_CONCEPTS, LV_SEC)
    sections = [
        cable_nameplate([ctl("conductor_material", "Conductor material", "text", "inherited")]),
        vm_section(LV_CONCEPTS, LV_SEC),
        {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "conductor", "label": "Conductor (others grounded)", "rows": conductor_rows()},
                   "columns": [ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                               ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                                   acceptance={"basis": "comparison", "rule": "vs prior/similar or mfr data"},
                                   tolerance_source={"engine": "mfr", "function": "insulation_resistance",
                                                     "inputs": ["manufacturer", "cable_type"]}),
                               ctl("equip_temp", "Equipment temp", "numeric", unit="degC")]}},
        {"key": "continuity", "title": "Continuity", "kind": "fields",
         "fields": [ctl("continuity_result", "Continuity (correct cable connection)", "selection", "data", options=COND),
                    ctl("parallel_resistance", "Uniform resistance of parallel conductors", "selection", "data", options=COND, optional=True)]},
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "lv_cable",
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "continuity"]}],
            "sections": sections}


def build_mv():
    cov = covers_by_sec(MV_CONCEPTS, MV_SEC)
    sections = [
        cable_nameplate([ctl("shield_type", "Shield / neutral type", "text", "inherited")]),
        vm_section(MV_CONCEPTS, MV_SEC),
        {"key": "insulation_resistance", "title": "Insulation Resistance (conductor-to-shield)", "kind": "table",
         "table": {"row_dim": {"tag": "conductor", "label": "Conductor (others + shields grounded)", "rows": conductor_rows()[:3]},
                   "columns": [ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                               ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                                   acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "inputs": ["voltage_rating"]}),
                               ctl("equip_temp", "Equipment temp", "numeric", unit="degC")]}},
        {"key": "shield_continuity", "title": "Shield Continuity", "kind": "fields",
         "fields": [ctl("shield_continuity_result", "Shield continuity (ohmmeter)", "selection", "data", options=COND),
                    ctl("shield_ohms", "Shield resistance", "numeric", "data", unit="ohm", optional=True)]},
        {"key": "tdr", "title": "Time-Domain Reflectometer (optional)", "kind": "fields",
         "fields": [ctl("tdr_trace", "TDR measurement per conductor", "graph", "data", optional=True)]},
        {"key": "jacket_integrity", "title": "Jacket Integrity (optional)", "kind": "fields",
         "fields": [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV", optional=True),
                    ctl("duration_s", "Duration", "numeric", "data", unit="s", optional=True),
                    ctl("result", "Result", "selection", "data", options=["pass", "fail"], optional=True)]},
        {"key": "dielectric_withstand", "title": "Dielectric Withstand", "kind": "fields",
         "fields": [ctl("method", "Method", "selection", "data", options=["vlf", "dc", "ac"]),
                    ctl("test_kv", "Test voltage", "numeric", "data", unit="kV",
                        acceptance={"basis": "mfr_tolerance"},
                        tolerance_source={"engine": "mfr", "function": "dielectric_withstand",
                                          "inputs": ["manufacturer", "cable_type", "voltage_rating"]}),
                    ctl("duration_min", "Duration", "numeric", "data", unit="min"),
                    ctl("result", "Result", "selection", "data", options=["pass", "fail"])]},
        {"key": "tan_delta", "title": "Tan-Delta (optional)", "kind": "table",
         "table": {"row_dim": {"tag": "conductor", "label": "Conductor", "rows": conductor_rows()[:3]},
                   "columns": [ctl("step_kv", "Step voltage", "numeric", unit="kV"),
                               ctl("mean_td", "Mean tan-delta", "numeric", unit="E-3",
                                   acceptance={"basis": "mfr_tolerance", "fallback_table": "100.6.6"},
                                   tolerance_source={"engine": "neta_table", "table": "100.6.6",
                                                     "inputs": ["voltage_rating"]}),
                               ctl("stability", "Stability (std dev)", "numeric", unit="E-3")]}},
        {"key": "partial_discharge", "title": "Partial Discharge (optional)", "kind": "fields",
         "fields": [ctl("online_pd", "Online PD: ambient noise floor + phase-resolved pattern", "graph", "data", optional=True),
                    ctl("offline_pd", "Offline PD: calibration, inception/extinction, PRPD (Table 100.6.3/.4/.5)", "graph", "data", optional=True)]},
        TEST_EQUIPMENT, COMMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "mvhv_cable",
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "shield_continuity", "tdr", "jacket_integrity",
                                        "dielectric_withstand", "tan_delta", "partial_discharge"]}],
            "sections": sections}


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
    lv = build_lv()
    mv = build_mv()
    ln = check(lv, src, LV_SEC, 11, 6)
    mn = check(mv, src, MV_SEC, 18, 11)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Cable datasheets (ats_lv_cable_v1, ats_mvhv_cable_v1).",
        "-- GENERATED by gen_cable_template.py - do not edit by hand.",
        "-- Two leaf-bound single-procedure sheets: LV 7.3.2 (lean) + MV/HV 7.3.3 (adds the",
        "-- shielded-cable HV battery: shield continuity, TDR, jacket integrity, dielectric",
        "-- withstand, tan-delta, PD). R-A: tolerance_source = neta_table (MV IR 100.1, tan-delta",
        "-- 100.6.6) + mfr (LV IR, MV dielectric); NOT tcc. Windows resolved at provisioning.",
        f"-- Coverage: LV {ln}/11 (7.3.2); MV/HV {mn}/18 (7.3.3). Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(LV_ID, "ats_lv_cable_v1", "Low-Voltage Cable - ATS Field Data Sheet",
                     LV_SEC, "cable_lv", lv, "LV cable datasheet (NETA 7.3.2, 600 V max). Chip 2b.")
    out += sql_value(MV_ID, "ats_mvhv_cable_v1", "Medium/High-Voltage Cable - ATS Field Data Sheet",
                     MV_SEC, "cable_mv", mv, "MV/HV cable datasheet (NETA 7.3.3; shielded-cable HV battery). Chip 2b.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"lv: sections={len(lv['sections'])} covered={ln}/11   mv: sections={len(mv['sections'])} covered={mn}/18")


if __name__ == "__main__":
    main()
