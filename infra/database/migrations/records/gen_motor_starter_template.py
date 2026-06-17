#!/usr/bin/env python3
"""Generate 019_motor_starter_templates.sql - the Motor-Starter datasheets (NETA 7.16.1).

Two leaf-bound single-procedure sheets (the complete 7.16 procedures):
  - ats_lv_motor_starter_v1 -> motor_starter_lv; 7.16.1.1 (LV); 14 ATS (9 VM + 5 elec).
  - ats_mv_motor_starter_v1 -> motor_starter_mv; 7.16.1.2 (MV); 29 ATS (12 VM + 17 elec).

SCOPE RULING (MCC crossref): the two MCC leaves (mcc_lv -> 7.16.2.1, mcc_mv -> 7.16.2.2) are pure
`crossref` procedures with NO own NETA items - they refer out to 7.1 (bus) + 7.5.1.x (switches) +
7.6 (breakers) + 7.16.1.x (starters). A standalone MCC datasheet would invent content NETA defines
only by reference, so the MCC leaves are deferred to asset-tree composition (an MCC asset = bus +
switch + breaker + starter child assets, each on its own sheet). This chip ships the two real starter
sheets; the one not-yet-built constituent for full MCC composition is 7.5 switches.

PowerDB-anchored to the RESA cover forms (31000 Motor Starter / 31300 MV Vacuum Motor Starter); NETA
stays the coverage authority (the validator invariant below). R-A: a starter has no integral trip
curve, so tolerance_source.engine is neta_table (IR -> Table 100.1) or mfr (motor-protection /
dielectric per mfr data; torque -> 100.12 stays a VM acceptance basis) - never tcc. No starter
instrument bridge is wired (the PowerDB bridges are CT-Analyzer / DTAX / PTM), so capture = field +
cover_attach - no instrument_import section.

Coverage invariant (fail-fast here, re-checked in test_019): per sheet, the union of every section's
neta_covers covers all ATS visual_mechanical+electrical items of its procedure.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_motor_starter_template.py [path-to-json]
"""
import copy
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
OUT = os.path.join(HERE, "019_motor_starter_templates.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
LV_ID = str(uuid.uuid5(NS_TPL, "ats_lv_motor_starter_v1"))
MV_ID = str(uuid.uuid5(NS_TPL, "ats_mv_motor_starter_v1"))
LV_SEC, MV_SEC = "7.16.1.1", "7.16.1.2"
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
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("contactors", "Inspect contactors", "A", 5, False, "visual_mechanical"),
    ("motor_running_protection", "Inspect motor-running (overload) protection", "A", 6, True, "visual_mechanical"),
    ("torque", "Bolted connections torqued by calibrated torque wrench (mfr data / Table 100.12)", "A", 7, False, "visual_mechanical"),
    ("lubrication", "Verify lubrication on moving current-carrying and sliding surfaces", "A", 8, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 9, True, "visual_mechanical"),
    ("ir_starter", "IR 1 min each pole, phase-to-phase + phase-to-ground (closed) and across each open pole", "B", 1, False, "insulation_resistance"),
    ("ir_control", "IR control wiring to ground (500/1000 Vdc, 1 min)", "B", 2, True, "insulation_resistance"),
    ("motor_protection", "Test motor protection devices (mfr data / Section 7.9)", "B", 3, False, "protective_devices"),
    ("breakers", "Test circuit breakers (Section 7.6.1.1)", "B", 4, False, "protective_devices"),
    ("operational", "Operational tests by initiating control devices", "B", 5, False, "functional"),
]

MV_CONCEPTS = [
    ("np_vs_drawings", "Compare nameplate data with drawings", "A", 1, False, "nameplate"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("torque", "Bolted connections torqued by calibrated torque wrench (mfr data / Table 100.12)", "A", 5, False, "visual_mechanical"),
    ("interlocks", "Test electrical and mechanical interlock systems for correct operation / sequencing", "A", 6, False, "visual_mechanical"),
    ("barriers_shutters", "Verify correct barrier and shutter installation and operation", "A", 7, False, "visual_mechanical"),
    ("active_components", "Exercise active components; confirm correct operation of indicating devices", "A", 8, False, "visual_mechanical"),
    ("contactors", "Inspect contactors", "A", 9, False, "visual_mechanical"),
    ("overload_rating", "Verify overload protection rating; set adjustable devices per coordination study", "A", 10, False, "visual_mechanical"),
    ("lubrication", "Verify lubrication on moving current-carrying and sliding surfaces", "A", 11, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 12, True, "visual_mechanical"),
    ("ir_contactor", "IR 1 min on contactor(s), phase-to-ground + phase-to-phase (closed) and across each open contact", "B", 1, False, "insulation_resistance"),
    ("ir_control", "IR control wiring to ground (500/1000 Vdc, 1 min)", "B", 2, True, "insulation_resistance"),
    ("mac_test", "Magnetron atmospheric condition (MAC) test on each vacuum interrupter", "B", 3, True, "vacuum_integrity"),
    ("dielectric", "Dielectric withstand voltage test (mfr data / Table 100.9)", "B", 4, True, "dielectric_withstand"),
    ("vacuum_bottle", "Vacuum bottle integrity (dielectric withstand across each bottle, contacts open, mfr data)", "B", 5, False, "vacuum_integrity"),
    ("contact_pole_r", "Contact / pole resistance test", "B", 6, False, "contact_resistance"),
    ("blowout_coil_r", "Measure blowout coil circuit resistance", "B", 7, False, "contact_resistance"),
    ("power_fuse_r", "Measure resistance of power fuses", "B", 8, False, "contact_resistance"),
    ("energize_armature", "Energize contactor (aux source); adjust armature to minimize operating vibration", "B", 9, False, "functional"),
    ("cpt", "Test control power transformers (Section 7.1.B.8)", "B", 10, False, "associated_devices"),
    ("starting_xfmr", "Test starting transformers (Section 7.2.1)", "B", 11, False, "associated_devices"),
    ("starting_reactor", "Test starting reactors (Section 7.20.3)", "B", 12, False, "associated_devices"),
    ("motor_protection", "Test motor protection devices (mfr data / Section 7.9)", "B", 13, False, "associated_devices"),
    ("system_function", "System function test (ANSI/NETA ECS)", "B", 14, True, "functional"),
    ("cubicle_heater", "Verify operation of cubicle space heater", "B", 15, False, "auxiliary"),
    ("instrument_transformers", "Test instrument transformers (Section 7.10)", "B", 16, False, "associated_devices"),
    ("metering", "Test metering devices (Section 7.11)", "B", 17, False, "associated_devices"),
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


def nameplate(extra):
    base = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("catalog_series", "Catalog / series", "text", "inherited"),
        ctl("starter_size", "Starter size (NEMA)", "text", "inherited"),
        ctl("operating_voltage", "Operating voltage", "numeric", "inherited", unit="V"),
        ctl("control_voltage", "Control voltage", "numeric", "inherited", unit="V"),
        ctl("overload_rating", "Overload rating", "text", "inherited"),
    ]
    return {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
            "fields": base + extra + [ctl("nameplate_vs_drawings", "Nameplate data compared with drawings",
                                          "selection", "data", options=COND)]}


def ir_section(main_label):
    # the IR section is the neta_table (Table 100.1) acceptance slot on every starter sheet.
    return {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "fields",
            "fields": [ctl("test_voltage", "Test voltage", "numeric", "data", unit="V",
                           acceptance={"basis": "mfr_or_table", "table": "100.1",
                                       "note": "mfr published data or Table 100.1"}),
                       ctl("ir_main", main_label, "numeric", "data", unit="Mohm",
                           acceptance={"basis": "neta_table", "table": "100.1"},
                           tolerance_source={"engine": "neta_table", "table": "100.1",
                                             "inputs": ["voltage_rating"]}),
                       ctl("ir_across_open", "IR across each open pole / contact", "numeric", "data", unit="Mohm"),
                       ctl("ir_control_wiring", "IR control wiring to ground (500/1000 Vdc)", "numeric", "data",
                           unit="Mohm", optional=True),
                       ctl("temp", "Equipment temp", "numeric", "data", unit="degC")]}


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


def assign_covers(sections, cov):
    # deep-copy per sheet: shared section dicts (TEST_EQUIPMENT, ...) are reused across both sheets, so
    # neta_covers must land on a private copy, not the shared module object.
    out = []
    for s in sections:
        s = copy.deepcopy(s)
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
        out.append(s)
    return out


def build_lv():
    cov = covers_by_sec(LV_CONCEPTS, LV_SEC)
    sections = [
        nameplate([]),
        vm_section(LV_CONCEPTS, LV_SEC),
        ir_section("IR each pole, phase-to-phase + phase-to-ground (starter closed)"),
        {"key": "protective_devices", "title": "Protective Devices", "kind": "fields",
         "fields": [
             ctl("motor_protection", "Motor protection devices tested (mfr data / 7.9)", "selection", "data",
                 options=COND, tolerance_source={"engine": "mfr", "function": "motor_protection",
                                                 "inputs": ["manufacturer", "model"]}),
             ctl("breakers", "Circuit breakers tested (7.6.1.1)", "selection", "data", options=COND)]},
        {"key": "functional", "title": "Operational Test", "kind": "fields",
         "fields": [ctl("operational", "Operational test by initiating control devices", "selection", "data", options=PF)]},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "lv_motor_starter", "capture": CAPTURE,
            "selections": [], "sections": assign_covers(sections, cov)}


def build_mv():
    cov = covers_by_sec(MV_CONCEPTS, MV_SEC)
    sections = [
        nameplate([ctl("max_voltage", "Maximum voltage", "numeric", "inherited", unit="kV", optional=True)]),
        vm_section(MV_CONCEPTS, MV_SEC),
        ir_section("IR on contactor(s), phase-to-ground + phase-to-phase (closed)"),
        {"key": "vacuum_integrity", "title": "Vacuum Interrupter Integrity", "kind": "fields",
         "fields": [
             ctl("mac_test", "Magnetron atmospheric condition (MAC) test per interrupter", "selection", "data", options=PF, optional=True),
             ctl("vacuum_bottle", "Vacuum bottle integrity (dielectric withstand, contacts open)", "selection", "data", options=PF),
             ctl("withstand_kv", "Withstand voltage", "numeric", "data", unit="kV", optional=True,
                 acceptance={"basis": "mfr_tolerance", "note": "strictly per mfr published data"})]},
        {"key": "dielectric_withstand", "title": "Dielectric Withstand", "kind": "fields",
         "fields": [
             ctl("method", "Method", "selection", "data", options=["ac", "dc"], optional=True),
             ctl("test_kv", "Test voltage", "numeric", "data", unit="kV", optional=True,
                 acceptance={"basis": "mfr_tolerance", "note": "mfr published data; fallback Table 100.9"},
                 tolerance_source={"engine": "mfr", "function": "dielectric_withstand", "inputs": ["voltage_rating"]}),
             ctl("result", "Result", "selection", "data", options=PF, optional=True)]},
        {"key": "contact_resistance", "title": "Contact / Coil / Fuse Resistance", "kind": "fields",
         "fields": [
             ctl("contact_pole_uohm", "Contact / pole resistance", "numeric", "data", unit="uohm",
                 acceptance={"basis": "mfr_tolerance"}),
             ctl("blowout_coil_ohm", "Blowout coil circuit resistance", "numeric", "data", unit="ohm"),
             ctl("power_fuse_ohm", "Power fuse resistance", "numeric", "data", unit="ohm")]},
        {"key": "functional", "title": "Operational / Functional Tests", "kind": "fields",
         "fields": [
             ctl("energize_armature", "Energize contactor (aux source); armature adjusted to minimize vibration", "selection", "data", options=PF),
             ctl("system_function", "System function test (ANSI/NETA ECS)", "selection", "data", options=PF, optional=True)]},
        {"key": "associated_devices", "title": "Associated Devices (cross-reference)", "kind": "fields",
         "fields": [
             ctl("cpt", "Control power transformers tested (7.1.B.8)", "selection", "data", options=COND),
             ctl("starting_xfmr", "Starting transformers tested (7.2.1)", "selection", "data", options=COND),
             ctl("starting_reactor", "Starting reactors tested (7.20.3)", "selection", "data", options=COND),
             ctl("motor_protection", "Motor protection devices tested (mfr data / 7.9)", "selection", "data",
                 options=COND, tolerance_source={"engine": "mfr", "function": "motor_protection",
                                                 "inputs": ["manufacturer", "model"]}),
             ctl("instrument_transformers", "Instrument transformers tested (7.10)", "selection", "data", options=COND),
             ctl("metering", "Metering devices tested (7.11)", "selection", "data", options=COND)]},
        {"key": "auxiliary", "title": "Auxiliary", "kind": "fields",
         "fields": [ctl("space_heater", "Cubicle space-heater operation", "selection", "data", options=PF)]},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "mv_motor_starter", "capture": CAPTURE,
            "selections": [], "sections": assign_covers(sections, cov)}


def required_refs(json_path, section):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == section)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical")
    el = ats.get("electrical_tests")
    vm = vm if isinstance(vm, list) else []
    el = el if isinstance(el, list) else []
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
    a = check(lv, src, LV_SEC, 14, 8)
    b = check(mv, src, MV_SEC, 29, 12)

    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - Motor-Starter datasheets (LV 7.16.1.1 / MV 7.16.1.2).",
        "-- GENERATED by gen_motor_starter_template.py - do not edit by hand.",
        "-- Two leaf-bound single-procedure sheets. The MCC leaves (7.16.2.x) are pure crossref ->",
        "-- deferred as asset-tree composition (no own NETA items). PowerDB-anchored (31000 / 31300).",
        "-- R-A: neta_table (IR -> 100.1) + mfr (motor-protection / dielectric); NOT tcc; torque ->",
        "-- 100.12 = VM acceptance basis. Capture = field + cover_attach (no starter instrument bridge).",
        f"-- Coverage: LV {a}/14 (7.16.1.1); MV {b}/29 (7.16.1.2). Idempotent UUID5 + ON CONFLICT.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(LV_ID, "ats_lv_motor_starter_v1", "Low-Voltage Motor Starter - ATS Field Data Sheet",
                     LV_SEC, "motor_starter_lv", lv,
                     "LV motor-starter datasheet (NETA 7.16.1.1). Chip 2b; PowerDB-anchored (31000).")
    out += sql_value(MV_ID, "ats_mv_motor_starter_v1", "Medium-Voltage Motor Starter - ATS Field Data Sheet",
                     MV_SEC, "motor_starter_mv", mv,
                     "MV motor-starter datasheet (NETA 7.16.1.2). Chip 2b; PowerDB-anchored (31300).")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"lv: sec={len(lv['sections'])} cov={a}/14   mv: sec={len(mv['sections'])} cov={b}/29")


if __name__ == "__main__":
    main()
