#!/usr/bin/env python3
"""Generate 025_battery_template.sql - the Storage Battery datasheet (NETA 7.18.1.3, VRLA).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_battery_v1 -> leaf 'battery'.
Built for VRLA (7.18.1.3 - the dominant modern stationary battery): 10 VM + 8 electrical = 18 items.
Flooded-LA (7.18.1.1) and vented-NiCd (7.18.1.2) folds are a clean follow-on (same recipe + a
battery_type selector gating the type-specific items). The per-cell battery is a grow table (cell
voltage / intercell resistance / internal ohmic / negative-post temperature), aligned to IEEE 1188.

R-A: mfr (cell voltage / ohmic / load test vs IEEE 1188 + mfr data) - never tcc. Capture = field +
cover_attach (a discharge/load-test report can be the cover; no standard single-instrument import).

Coverage invariant (fail-fast here, re-checked in test_025). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_battery_template.py [path-to-json]
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
OUT = os.path.join(HERE, "025_battery_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
BAT_ID = str(uuid.uuid5(NS_TPL, "ats_battery_v1"))
SEC = "7.18.1.3"
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
    ("nameplate_vs_drawings", "Compare equipment nameplate data with drawings", "A", 4, False, "identification"),
    ("located", "Verify batteries are adequately located", "A", 1, False, "installation_safety"),
    ("ventilation", "Verify battery area ventilation system is operable", "A", 2, False, "installation_safety"),
    ("eyewash", "Verify existence of suitable eyewash equipment", "A", 3, False, "installation_safety"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 5, False, "visual_mechanical"),
    ("racks", "Verify adequacy of racks/cabinets, mounting, anchorage, alignment, grounding", "A", 6, False, "visual_mechanical"),
    ("clean", "Verify the units are clean", "A", 7, False, "visual_mechanical"),
    ("oxide_inhibitor", "Verify application of an oxide inhibitor on terminal connections", "A", 8, False, "visual_mechanical"),
    ("torque", "Bolted electrical connections torqued (calibrated wrench; Table 100.12)", "A", 9, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 10, True, "visual_mechanical"),
    ("neg_post_temp", "Measure negative post temperature", "B", 1, False, "cell_data"),
    ("charger_float_equalize", "Measure charger float and equalizing voltage levels", "B", 2, False, "charger_interface"),
    ("charger_functions", "Verify all charger functions and alarms", "B", 3, False, "charger_interface"),
    ("cell_voltage", "Measure each cell voltage and total battery voltage (charger in float)", "B", 4, False, "cell_data"),
    ("intercell_r", "Measure intercell connection resistances", "B", 5, False, "cell_data"),
    ("internal_ohmic", "Perform internal ohmic measurement tests", "B", 6, False, "cell_data"),
    ("load_test", "Perform a load test (mfr published data / IEEE 1188)", "B", 7, False, "load_test"),
    ("ground_voltage", "Measure system voltage positive-to-ground and negative-to-ground", "B", 8, False, "ground_voltage"),
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
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (discharge / load-test report)",
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
        ctl("chemistry", "Chemistry", "selection", "inherited",
            options=["vrla", "flooded_lead_acid", "vented_nicd"]),
        ctl("cell_count", "Number of cells", "numeric", "inherited"),
        ctl("nominal_voltage", "Nominal system voltage", "numeric", "inherited", unit="V"),
        ctl("ah_capacity", "Rated capacity", "numeric", "inherited", unit="Ah"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.4"),
    ]
    installation_safety = [
        ctl("battery_location", "Battery location adequate", "selection", "data", options=COND, neta_ref=f"{SEC}.A.1"),
        ctl("ventilation_operable", "Ventilation system operable", "selection", "data", options=COND, neta_ref=f"{SEC}.A.2"),
        ctl("eyewash_present", "Suitable eyewash equipment present", "selection", "data", options=COND, neta_ref=f"{SEC}.A.3"),
    ]
    charger_interface = [
        ctl("float_voltage", "Charger float voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.2"),
        ctl("equalize_voltage", "Charger equalize voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.2"),
        ctl("total_battery_voltage", "Total battery voltage (float)", "numeric", "data", unit="V"),
        ctl("charger_functions", "Charger functions verified", "selection", "data", options=COND, neta_ref=f"{SEC}.B.3"),
        ctl("charger_alarms", "Charger alarms verified", "selection", "data", options=COND, neta_ref=f"{SEC}.B.3"),
    ]
    cell_data = {
        "key": "cell_data", "title": "Per-Cell Measurements", "kind": "table",
        "neta_basis": f"{SEC}.B.4",
        "table": {"row_dim": {"tag": "cell", "label": "Cell / monoblock", "rows": [], "grow": True},
                  "columns": [
                      ctl("cell_no", "Cell no.", "text"),
                      ctl("float_voltage_v", "Float voltage", "numeric", unit="V",
                          acceptance={"basis": "mfr_tolerance", "rule": "vs mfr float spec; flag low cells"}),
                      ctl("neg_post_temp_c", "Negative-post temp", "numeric", unit="degC"),
                      ctl("intercell_uohm", "Intercell resistance", "numeric", unit="uohm",
                          acceptance={"basis": "mfr_tolerance", "rule": "vs baseline; investigate >20% rise"}),
                      ctl("internal_mohm", "Internal ohmic", "numeric", unit="mohm",
                          acceptance={"basis": "comparison", "rule": "vs baseline / reference (IEEE 1188)"}),
                      ctl("result", "Result", "selection", options=COND)]},
    }
    load_test = [
        ctl("method", "Load-test method", "selection", "data",
            options=["constant_current", "constant_power", "modified_performance", "per_mfr"], neta_ref=f"{SEC}.B.7"),
        ctl("test_current_a", "Test current", "numeric", "data", unit="A"),
        ctl("duration_min", "Duration", "numeric", "data", unit="min"),
        ctl("capacity_pct", "Capacity (% of rated)", "numeric", "data", unit="pct",
            acceptance={"basis": "standard", "ref": "IEEE 1188 (>=80% / replace)"}),
        ctl("standard", "Test standard", "text", "data"),
        ctl("result", "Result", "selection", "data", options=["pass", "fail"])]
    ground_voltage = [
        ctl("pos_to_ground_v", "Positive-to-ground voltage", "numeric", "data", unit="V", neta_ref=f"{SEC}.B.8"),
        ctl("neg_to_ground_v", "Negative-to-ground voltage", "numeric", "data", unit="V"),
        ctl("ground_fault", "Ground-fault indication", "selection", "data", options=["none", "positive", "negative"])]

    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.4", "fields": identification},
        {"key": "installation_safety", "title": "Installation and Safety", "kind": "fields",
         "fields": installation_safety},
        vm_section(),
        {"key": "charger_interface", "title": "Charger Interface (float / equalize)", "kind": "fields",
         "fields": charger_interface},
        cell_data,
        {"key": "load_test", "title": "Capacity / Load Test", "kind": "fields", "fields": load_test},
        {"key": "ground_voltage", "title": "System Ground Voltage", "kind": "fields", "fields": ground_voltage},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "battery", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["cell_measurements", "load_test"]}],
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
    assert not missing, f"battery gap: {sorted(missing)}"
    assert not phantom, f"battery phantom: {sorted(phantom)}"
    assert len(required) == 18, f"battery expected 18, got {len(required)}"
    assert len(schema["sections"]) == 10, f"battery sections={len(schema['sections'])} != 10"
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
        "-- Records Chip 2c - Storage Battery datasheet (ats_battery_v1).",
        "-- GENERATED by gen_battery_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.18.1.3 (VRLA), 18 ATS items. Per-cell grow table",
        "-- (cell voltage / intercell R / internal ohmic / neg-post temp) aligned to IEEE 1188.",
        "-- Flooded-LA (7.18.1.1) / NiCd (7.18.1.2) folds = follow-on. R-A: mfr. Capture: field +",
        "-- cover_attach (discharge/load-test report). UUID5.",
        f"-- Coverage: {n}/18 (7.18.1.3).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(BAT_ID, "ats_battery_v1", "Storage Battery (VRLA) - ATS Field Data Sheet",
                     SEC, "battery", schema, "Storage Battery datasheet (NETA 7.18.1.3, VRLA). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"battery: sections={len(schema['sections'])} covered={n}/18")


if __name__ == "__main__":
    main()
