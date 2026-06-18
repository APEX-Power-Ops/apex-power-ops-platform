#!/usr/bin/env python3
"""Generate 029_engine_generator_template.sql - the Engine Generator datasheet (NETA 7.22.1).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_engine_generator_v1 -> leaf
'engine_generator'. NETA 7.22.1 (Emergency Systems, Engine Generator) = 4 VM + 7 electrical = 11
items (IR per IEEE 43 + DA ratio, phasing/synchronizing, engine-shutdown protection, vibration per
bearing cap, NFPA 110 performance, governor + regulator). R-A: mfr - IR/DA per IEEE 43 (NOT a NETA
table window), performance per NFPA 110. Capture = field + cover_attach.

The packaged genset cross-refs the bare rotating machine (7.15) for the alternator. Coverage
invariant (fail-fast here, re-checked in test_029). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_engine_generator_template.py [path-to-json]
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
OUT = os.path.join(HERE, "029_engine_generator_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
GEN_ID = str(uuid.uuid5(NS_TPL, "ats_engine_generator_v1"))
SEC = "7.22.1"
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
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("ir", "Insulation-resistance test (IEEE Std 43)", "B", 1, False, "insulation_resistance"),
    ("da_ratio", "Machines 200 hp (150 kW) and less: one-minute test; calculate dielectric-absorption ratio", "B", 2, False, "insulation_resistance"),
    ("phasing", "Verify phase rotation, phasing, and synchronized operation", "B", 3, False, "phasing"),
    ("engine_shutdown", "Functionally test engine shutdown (low oil pressure, overtemperature, overspeed, others)", "B", 4, False, "engine_protection"),
    ("vibration", "Perform vibration test for each main bearing cap", "B", 5, False, "vibration"),
    ("performance", "Conduct performance test per NFPA 110", "B", 6, False, "performance"),
    ("governor_regulator", "Verify correct functioning of the governor and regulator", "B", 7, False, "governor_regulator"),
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
        ctl("kw_rating", "Power rating", "numeric", "inherited", unit="kW"),
        ctl("kva_rating", "Apparent-power rating", "numeric", "inherited", unit="kVA"),
        ctl("voltage", "Rated voltage", "numeric", "inherited", unit="V"),
        ctl("rpm", "Speed", "numeric", "inherited", unit="rpm"),
        ctl("fuel_type", "Fuel type", "selection", "inherited", options=["diesel", "natural_gas", "propane", "other"]),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    insulation_resistance = [
        ctl("test_voltage", "Test voltage", "numeric", "data", unit="V"),
        ctl("ir_60s_mohm", "IR (60 s)", "numeric", "data", unit="Mohm",
            acceptance={"basis": "ieee_43", "note": "min IR = kV + 1 Mohm (IEEE 43)"},
            tolerance_source={"engine": "mfr", "function": "insulation_resistance",
                              "inputs": ["voltage", "kw_rating"]}, neta_ref=f"{SEC}.B.1"),
        ctl("da_ratio", "Dielectric-absorption ratio (60/30 s)", "numeric", "data",
            acceptance={"basis": "ieee_43"}, neta_ref=f"{SEC}.B.2"),
        ctl("winding_temp", "Winding temp", "numeric", "data", unit="degC"),
    ]
    phasing = [
        ctl("phase_rotation", "Phase rotation", "selection", "data", options=["abc", "cba"]),
        ctl("phasing_verified", "Phasing verified", "selection", "data", options=COND),
        ctl("sync_operation", "Synchronized operation verified (as required by application)", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.3"),
    ]
    performance = [
        ctl("load_pct", "Test load", "numeric", "data", unit="pct"),
        ctl("duration_min", "Run duration", "numeric", "data", unit="min"),
        ctl("out_voltage", "Output voltage", "numeric", "data", unit="V"),
        ctl("frequency", "Frequency", "numeric", "data", unit="Hz"),
        ctl("start_time_s", "Time to start and reach rated voltage/frequency", "numeric", "data", unit="s"),
        ctl("nfpa110_result", "NFPA 110 performance test result", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.6"),
    ]
    governor_regulator = [
        ctl("governor_ok", "Governor functions correctly", "selection", "data", options=COND, neta_ref=f"{SEC}.B.7"),
        ctl("regulator_ok", "Voltage regulator functions correctly", "selection", "data", options=COND),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "insulation_resistance", "title": "Insulation Resistance (IEEE Std 43)", "kind": "fields",
         "fields": insulation_resistance},
        {"key": "phasing", "title": "Phasing and Synchronizing", "kind": "fields", "fields": phasing},
        {"key": "engine_protection", "title": "Engine Shutdown / Protection", "kind": "table",
         "neta_basis": f"{SEC}.B.4",
         "table": {"row_dim": {"tag": "function", "label": "Protection function",
                               "rows": ["Low oil pressure", "High coolant temperature", "Overspeed",
                                        "Low coolant level", "Overcrank"], "grow": True},
                   "columns": [ctl("setpoint", "Setpoint", "text"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "vibration", "title": "Vibration (each main bearing cap)", "kind": "table",
         "neta_basis": f"{SEC}.B.5",
         "table": {"row_dim": {"tag": "location", "label": "Bearing cap", "rows": [], "grow": True},
                   "columns": [ctl("reading", "Reading", "numeric", unit="in/s"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "performance", "title": "Performance Test (NFPA 110)", "kind": "fields", "fields": performance},
        {"key": "governor_regulator", "title": "Governor and Regulator", "kind": "fields",
         "fields": governor_regulator},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "engine_generator", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "performance", "vibration"]}],
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
    assert not missing, f"genset gap: {sorted(missing)}"
    assert not phantom, f"genset phantom: {sorted(phantom)}"
    assert len(required) == 11, f"genset expected 11, got {len(required)}"
    assert len(schema["sections"]) == 11, f"genset sections={len(schema['sections'])} != 11"
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
        "-- Records Chip 2c - Engine Generator datasheet (ats_engine_generator_v1).",
        "-- GENERATED by gen_engine_generator_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.22.1 (Emergency Systems), 11 ATS items.",
        "-- IR per IEEE 43 + DA ratio, phasing/synchronizing, engine-shutdown protection,",
        "-- vibration per bearing cap, NFPA 110 performance, governor + regulator.",
        "-- R-A: mfr (IR/DA per IEEE 43 - NOT a NETA table; perf per NFPA 110). UUID5.",
        f"-- Coverage: {n}/11 (7.22.1).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(GEN_ID, "ats_engine_generator_v1", "Engine Generator - ATS Field Data Sheet",
                     SEC, "engine_generator", schema,
                     "Engine Generator datasheet (NETA 7.22.1, Emergency Systems). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"genset: sections={len(schema['sections'])} covered={n}/11")


if __name__ == "__main__":
    main()
