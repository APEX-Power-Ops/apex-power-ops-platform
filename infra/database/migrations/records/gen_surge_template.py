#!/usr/bin/env python3
"""Generate 017_surge_templates.sql - the Surge-Protection datasheets (LV SPD + MV/HV arrester).

Operator ruling (2026-06-17): SPLIT the single `surge_arrester` leaf, because NETA 7.19 is two
genuinely different apparatus. This migration therefore does a small TAXONOMY SPLIT then two
leaf-bound sheets:
  - NEW leaf `spd_lv` (Surge Protective Device, Low-Voltage) under the `surge_protection` parent;
    relink 7.19.1 -> spd_lv (primary) and drop the stale surge_arrester -> 7.19.1 link.
  - ats_lv_spd_v1        -> spd_lv;         NETA 7.19.1 (LV SPD);            8 ATS (6 VM + 2 elec).
  - ats_mvhv_arrester_v1 -> surge_arrester; NETA 7.19.2 (MV/HV arrester);  12 ATS (8 VM + 4 elec).

NOT PowerDB-anchored (no surge form in the corpus) -> NETA-derived. R-A: LV SPD has no NETA
measurement table -> `mfr` (grounding connection per 7.13); MV/HV arrester IR -> Table 100.1
(`neta_table`) + watts-loss -> `mfr`; never tcc. Capture = field + cover_attach (no arrester bridge).

Coverage invariant (fail-fast here, re-checked in test_017): per sheet, union of section neta_covers
covers all the procedure's ATS visual_mechanical+electrical items.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_surge_template.py [path-to-json]
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
OUT = os.path.join(HERE, "017_surge_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
NS_LEAF = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000c1")
LV_ID = str(uuid.uuid5(NS_TPL, "ats_lv_spd_v1"))
MV_ID = str(uuid.uuid5(NS_TPL, "ats_mvhv_arrester_v1"))
SPD_LEAF_ID = str(uuid.uuid5(NS_LEAF, "spd_lv"))
SPD_ACNP_ID = str(uuid.uuid5(NS_LEAF, "acnp:spd_lv:7.19.1"))

LV_SEC, MV_SEC = "7.19.1", "7.19.2"
COND = ["sat", "unsat", "na"]
PF = ["pass", "fail"]
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat A=visual_mechanical / B=electrical, item_no, optional, section_key)
LV_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, grounding, and clearances", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the device is clean", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12)", "A", 5, False, "visual_mechanical"),
    ("ground_lead", "Ground lead attached with the shortest wire length possible", "A", 6, False, "visual_mechanical"),
    ("self_test", "Verify self-test operation, alarms, counter-indication, status indicators", "B", 1, False, "functional_status"),
    ("grounding", "Test grounding connection (per Section 7.13)", "B", 2, False, "grounding"),
]

MV_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, grounding, and clearances", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the arresters are clean", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued (Table 100.12 / 7.19.2.B.1)", "A", 5, False, "visual_mechanical"),
    ("ground_lead", "Each ground lead individually attached, shortest wire length possible", "A", 6, False, "visual_mechanical"),
    ("counter_mounted", "Stroke counter correctly mounted and electrically connected", "A", 7, False, "visual_mechanical"),
    ("counter_reading", "Record the stroke counter reading", "A", 8, False, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir", "IR each arrester, phase terminal-to-ground (mfr data; Table 100.1)", "B", 2, False, "insulation_resistance"),
    ("grounding", "Test grounding connection (per Section 7.13)", "B", 3, False, "grounding"),
    ("watts_loss", "Watts-loss test for substation-class surge arresters", "B", 4, False, "watts_loss"),
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
        rows.append({"key": c[0], "label": c[1], "neta_ref": f"{section_code}.{c[2]}.{c[3]}"})
    return {"key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
            "neta_basis": section_code,
            "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
                      "columns": [ctl("inspected", "Inspected", "boolean"),
                                  ctl("condition", "Condition", "selection", options=COND),
                                  ctl("value", "Value", "text"), ctl("note", "Note", "text")]}}


def grounding_section():
    # 7.13 cross-ref: capture the ground-connection result + resistance (mfr / design basis).
    return {"key": "grounding", "title": "Grounding Connection (per 7.13)", "kind": "fields",
            "fields": [ctl("ground_connection", "Ground connection verified (Section 7.13)", "selection", "data", options=COND),
                       ctl("ground_resistance_ohm", "Ground resistance", "numeric", "data", unit="ohm",
                           acceptance={"basis": "design_spec", "note": "design / IEEE 81 limit"},
                           tolerance_source={"engine": "mfr", "function": "ground_resistance",
                                             "inputs": ["design_limit_ohms"]})]}


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
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (mfr / OEM report)", "kind": "attachment",
               "capture_mode": "cover_attach",
               "fields": [ctl("report", "Attached test report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["manufacturer", "third_party_lab", "field_instrument"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements", "selection", "data", options=COND)]}


def nameplate(fields):
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
            "fields": fields + [ctl("nameplate_vs_drawings", "Nameplate data compared with drawings",
                                    "selection", "data", options=COND)]}


def assign_covers(sections, cov):
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])


def build_lv():
    cov = covers_by_sec(LV_CONCEPTS, LV_SEC)
    sections = [
        nameplate([
            ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
            ctl("type_model", "Type / model", "text", "inherited"),
            ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
            ctl("mcov", "MCOV", "numeric", "data", unit="V"),
            ctl("protection_modes", "Protection modes (L-N / L-G / N-G)", "text", "data"),
            ctl("spd_type", "SPD type (Type 1 / 2 / 3)", "selection", "data", options=["type1", "type2", "type3"]),
        ]),
        vm_section(LV_CONCEPTS, LV_SEC),
        {"key": "functional_status", "title": "Functional / Status", "kind": "fields",
         "fields": [ctl("self_test", "Self-test operation", "selection", "data", options=PF),
                    ctl("alarms", "Alarms", "selection", "data", options=["ok", "alarm"]),
                    ctl("status_indicators", "Status indicators", "selection", "data", options=["ok", "fault"]),
                    ctl("surge_counter", "Surge counter reading", "numeric", "data", optional=True)]},
        grounding_section(),
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    assign_covers(sections, cov)
    return {"version": 1, "family": "lv_spd", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["functional_status", "grounding"]}],
            "sections": sections}


def build_mv():
    cov = covers_by_sec(MV_CONCEPTS, MV_SEC)
    sections = [
        nameplate([
            ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
            ctl("arrester_class", "Arrester class", "selection", "data",
                options=["station", "intermediate", "distribution", "riser_pole"]),
            ctl("rated_voltage", "Rated voltage (duty cycle)", "numeric", "inherited", unit="kV"),
            ctl("mcov", "MCOV", "numeric", "data", unit="kV"),
            ctl("discharge_class", "Discharge / energy class", "text", "data"),
        ]),
        vm_section(MV_CONCEPTS, MV_SEC),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "fields",
         "fields": [ctl("resistance_uohm", "Resistance (low-resistance ohmmeter)", "numeric", "data", unit="uohm",
                        acceptance={"basis": "comparison", "note": "vs mfr / similar"}),
                    ctl("result", "Within tolerance", "selection", "data", options=COND)]},
        {"key": "insulation_resistance", "title": "Insulation Resistance (terminal-to-ground)", "kind": "table",
         "table": {"row_dim": {"tag": "phase", "label": "Arrester / phase",
                               "rows": [{"key": "a", "label": "Phase A"}, {"key": "b", "label": "Phase B"},
                                        {"key": "c", "label": "Phase C"}]},
                   "columns": [ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                               ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                                   acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("equip_temp", "Equipment temp", "numeric", unit="degC")]}},
        grounding_section(),
        {"key": "watts_loss", "title": "Watts-Loss (substation class)", "kind": "fields",
         "fields": [ctl("test_kv", "Test voltage", "numeric", "data", unit="kV"),
                    ctl("watts", "Watts loss", "numeric", "data", unit="W",
                        acceptance={"basis": "mfr_tolerance"},
                        tolerance_source={"engine": "mfr", "function": "watts_loss",
                                          "inputs": ["manufacturer", "model", "rated_voltage"]}),
                    ctl("ma", "Current", "numeric", "data", unit="mA"),
                    ctl("result", "Result", "selection", "data", options=COND)]},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    assign_covers(sections, cov)
    return {"version": 1, "family": "mvhv_arrester", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["bolted_resistance", "insulation_resistance", "grounding", "watts_loss"]}],
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
    assert len(schema["sections"]) == sec_expect, f"{schema['family']} sections={len(schema['sections'])} != {sec_expect}"
    return len(covered & required)


def taxonomy_prologue():
    return [
        "-- Operator-ruled split (2026-06-17): NETA 7.19 is two apparatus. Add the LV-SPD leaf and",
        "-- move 7.19.1 to it; surge_arrester keeps 7.19.2 (MV/HV arrester).",
        "INSERT INTO records.asset_classes (asset_class_id, class_code, name, parent_class_id, is_active)",
        "VALUES (",
        f"  '{SPD_LEAF_ID}', 'spd_lv', 'Surge Protective Device (Low-Voltage)',",
        "  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'surge_protection'),",
        "  true)",
        "ON CONFLICT (class_code) DO UPDATE SET name = EXCLUDED.name,",
        "  parent_class_id = EXCLUDED.parent_class_id, updated_at = now();",
        "",
        "INSERT INTO records.asset_class_neta_procedure",
        "  (asset_class_neta_procedure_id, asset_class_id, neta_procedure_id, is_primary)",
        "VALUES (",
        f"  '{SPD_ACNP_ID}',",
        "  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'spd_lv'),",
        "  (SELECT neta_procedure_id FROM records.neta_procedures WHERE section = '7.19.1'),",
        "  true)",
        "ON CONFLICT (asset_class_id, neta_procedure_id) DO UPDATE SET is_primary = EXCLUDED.is_primary;",
        "",
        "-- 7.19.1 now belongs to spd_lv; drop the stale surge_arrester -> 7.19.1 link",
        "DELETE FROM records.asset_class_neta_procedure",
        "WHERE asset_class_id = (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'surge_arrester')",
        "  AND neta_procedure_id = (SELECT neta_procedure_id FROM records.neta_procedures WHERE section = '7.19.1');",
        "",
    ]


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
    lv, mv = build_lv(), build_mv()
    ln = check(lv, src, LV_SEC, 8, 7)
    mn = check(mv, src, MV_SEC, 12, 9)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Surge-Protection datasheets (ats_lv_spd_v1, ats_mvhv_arrester_v1).",
        "-- GENERATED by gen_surge_template.py - do not edit by hand.",
        "-- Operator-ruled SPLIT of the surge_arrester leaf: adds the `spd_lv` leaf + relinks 7.19.1,",
        "-- then two leaf-bound sheets (LV SPD 7.19.1 / MV-HV arrester 7.19.2). NOT PowerDB-anchored.",
        "-- R-A: LV SPD -> mfr (grounding); MV/HV arrester -> neta_table (IR 100.1) + mfr (watts-loss);",
        "-- never tcc. Capture = field + cover_attach (no arrester bridge). Idempotent UUID5.",
        f"-- Coverage: LV SPD {ln}/8 (7.19.1); MV/HV arrester {mn}/12 (7.19.2).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += taxonomy_prologue()
    out += sql_value(LV_ID, "ats_lv_spd_v1", "Low-Voltage Surge Protective Device - ATS Field Data Sheet",
                     LV_SEC, "spd_lv", lv, "LV SPD datasheet (NETA 7.19.1). Chip 2b; NETA-derived; leaf split.")
    out += sql_value(MV_ID, "ats_mvhv_arrester_v1", "Medium/High-Voltage Surge Arrester - ATS Field Data Sheet",
                     MV_SEC, "surge_arrester", mv, "MV/HV surge-arrester datasheet (NETA 7.19.2). Chip 2b; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"lv_spd: sections={len(lv['sections'])} covered={ln}/8   mvhv_arrester: sections={len(mv['sections'])} covered={mn}/12")


if __name__ == "__main__":
    main()
