#!/usr/bin/env python3
"""Generate 035_circuit_switcher_template.sql - the Circuit Switcher datasheet (NETA 7.7).

records Chip 2c (slice-3 coverage backlog). One leaf-bound sheet: ats_circuit_switcher_v1 -> leaf
'circuit_switcher'. NETA 7.7 = 13 VM + 11 electrical = 24 items (SF6 interrupters + pressure,
isolating switch, interlocks, operation counters; connection + contact resistance, pole IR (Table
100.1), control-wiring IR, coil min-pickup, aux features / protective-device trip / electrical trip /
heaters, dielectric withstand, PF/DF open+closed). R-A: IR -> 100.1 (neta_table); contact/connection/
coil/dielectric/PF -> mfr. Capture = field + cover_attach.

Coverage invariant (fail-fast here, re-checked in test_035). ASCII-only. Deterministic UUID5.
Run: uv run --no-project python gen_circuit_switcher_template.py [path-to-json]
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
OUT = os.path.join(HERE, "035_circuit_switcher_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
CS_ID = str(uuid.uuid5(NS_TPL, "ats_circuit_switcher_v1"))
SEC = "7.7"
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
    ("bushings_clean", "Verify the bushings and insulators are clean", "A", 4, False, "visual_mechanical"),
    ("mech_operate", "Verify circuit switcher and operating mechanism mechanically operate per mfr published data", "A", 5, False, "visual_mechanical"),
    ("torque", "Verify tightness of bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A", 6, False, "visual_mechanical"),
    ("sf6_interrupters", "Verify operation of SF6 interrupters per mfr published data", "A", 7, False, "visual_mechanical"),
    ("sf6_pressure", "Verify SF6 pressure per mfr published data", "A", 8, False, "visual_mechanical"),
    ("isolating_switch", "Verify operation of isolating switch per system design and mfr published data", "A", 9, False, "visual_mechanical"),
    ("interlocks", "Verify all interlocking systems operate and sequence per system design and mfr published data", "A", 10, False, "visual_mechanical"),
    ("lubrication", "Verify appropriate lubrication on moving current-carrying and sliding surfaces", "A", 11, False, "visual_mechanical"),
    ("counters", "Record as-found and as-left operation counter readings", "A", 12, False, "operation_counters"),
    ("thermography", "Perform thermographic survey (Section 9)", "A", 13, True, "visual_mechanical"),
    ("connection_r", "Resistance through all connections (low-resistance ohmmeter)", "B", 1, False, "connection_resistance"),
    ("contact_r", "Contact-resistance test of interrupters and isolating switches", "B", 2, False, "contact_resistance"),
    ("ir", "Insulation-resistance tests on each pole phase-to-ground (Table 100.1)", "B", 3, False, "insulation_resistance"),
    ("control_ir", "Insulation-resistance tests on all control wiring (500/1000 V dc, one minute)", "B", 4, False, "control_wiring_ir"),
    ("coil_pickup", "Minimum pickup voltage tests on trip and close coils per mfr published data", "B", 5, False, "coil_pickup"),
    ("aux_features", "Verify auxiliary features (electrical close/trip, trip-free, anti-pump); reset trip logs", "B", 6, False, "functional"),
    ("trip_protective", "Trip circuit switcher by operation of each protective device", "B", 7, False, "functional"),
    ("electrical_trip", "Verify correct operation of electrical trip of interrupters", "B", 8, False, "functional"),
    ("dielectric", "Dielectric withstand voltage test per mfr published data", "B", 9, True, "dielectric_withstand"),
    ("pf_df", "Insulation power-factor / dissipation-factor tests on each pole (open) and each phase (closed)", "B", 10, False, "power_factor"),
    ("heaters", "Verify operation of heaters", "B", 11, False, "functional"),
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
        ctl("rated_voltage", "Rated voltage", "numeric", "inherited", unit="kV"),
        ctl("continuous_current", "Continuous current rating", "numeric", "inherited", unit="A"),
        ctl("interrupting_rating", "Interrupting rating", "numeric", "inherited", unit="A"),
        ctl("sf6_rated_pressure", "SF6 rated pressure", "numeric", "inherited", unit="psig"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    operation_counters = [
        ctl("counter_as_found", "Operation counter (as found)", "numeric", "data", neta_ref=f"{SEC}.A.12"),
        ctl("counter_as_left", "Operation counter (as left)", "numeric", "data"),
    ]
    control_wiring_ir = [
        ctl("control_test_v", "Applied voltage", "numeric", "data", unit="V"),
        ctl("control_ir_mohm", "Control-wiring IR (1 min)", "numeric", "data", unit="Mohm",
            acceptance={"basis": "mfr_tolerance"},
            tolerance_source={"engine": "mfr", "function": "control_wiring_ir",
                              "inputs": ["manufacturer", "model"]}, neta_ref=f"{SEC}.B.4"),
        ctl("control_result", "Result", "selection", "data", options=COND),
    ]
    functional = [
        ctl("aux_features", "Auxiliary features verified (electrical close/trip, trip-free, anti-pump); trip logs reset",
            "selection", "data", options=COND, neta_ref=f"{SEC}.B.6"),
        ctl("trip_protective", "Tripped by operation of each protective device", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.7"),
        ctl("electrical_trip", "Electrical trip of interrupters operates correctly", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.8"),
        ctl("heaters", "Heaters operational", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.11"),
    ]
    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "operation_counters", "title": "Operation Counters", "kind": "fields",
         "fields": operation_counters},
        {"key": "connection_resistance", "title": "Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "connection_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        {"key": "contact_resistance", "title": "Contact Resistance (interrupters / isolating switches)",
         "kind": "table", "neta_basis": f"{SEC}.B.2",
         "table": {"row_dim": {"tag": "pole", "label": "Pole", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("interrupter_micro_ohms", "Interrupter", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "contact_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("isolator_micro_ohms", "Isolating switch", "numeric", unit="uohm")]}},
        {"key": "insulation_resistance", "title": "Insulation Resistance (pole to ground)", "kind": "table",
         "neta_basis": f"{SEC}.B.3",
         "table": {"row_dim": {"tag": "pole", "label": "Pole (to ground)", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "control_wiring_ir", "title": "Control-Wiring Insulation Resistance", "kind": "fields",
         "fields": control_wiring_ir},
        {"key": "coil_pickup", "title": "Coil Minimum Pickup Voltage", "kind": "table",
         "neta_basis": f"{SEC}.B.5",
         "table": {"row_dim": {"tag": "coil", "label": "Coil", "rows": ["Trip", "Close"]},
                   "columns": [ctl("rated_v", "Rated control V", "numeric", unit="V"),
                               ctl("pickup_v", "Min pickup", "numeric", unit="V",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "coil_pickup",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "functional", "title": "Functional Checks", "kind": "fields", "fields": functional},
        {"key": "dielectric_withstand", "title": "Dielectric Withstand", "kind": "table",
         "neta_basis": f"{SEC}.B.9",
         "table": {"row_dim": {"tag": "pole", "label": "Pole (to ground)", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV",
                                   acceptance={"basis": "mfr_tolerance", "note": "mfr published data"},
                                   tolerance_source={"engine": "mfr", "function": "dielectric_withstand",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("leakage_ua", "Leakage", "numeric", unit="uA"),
                               ctl("result", "Result", "selection", options=COND)]}},
        {"key": "power_factor", "title": "Insulation Power-Factor / Dissipation-Factor", "kind": "table",
         "neta_basis": f"{SEC}.B.10",
         "table": {"row_dim": {"tag": "config", "label": "Configuration",
                               "rows": ["P1 open", "P2 open", "P3 open", "P1 closed", "P2 closed", "P3 closed"]},
                   "columns": [ctl("test_kv", "Test voltage", "numeric", unit="kV"),
                               ctl("pf_pct", "Power factor", "numeric", unit="pct",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "power_factor",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]}},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "circuit_switcher", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "contact_resistance", "coil_pickup",
                                        "dielectric_withstand", "power_factor"]}],
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
    assert not missing, f"circuit-switcher gap: {sorted(missing)}"
    assert not phantom, f"circuit-switcher phantom: {sorted(phantom)}"
    assert len(required) == 24, f"circuit-switcher expected 24, got {len(required)}"
    assert len(schema["sections"]) == 14, f"circuit-switcher sections={len(schema['sections'])} != 14"
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
        "-- Records Chip 2c - Circuit Switcher datasheet (ats_circuit_switcher_v1).",
        "-- GENERATED by gen_circuit_switcher_template.py - do not edit by hand.",
        "-- One leaf-bound sheet: NETA 7.7, 24 ATS items.",
        "-- SF6 interrupters + pressure, isolating switch, interlocks, operation counters; connection",
        "-- + contact resistance, pole IR (100.1), control-wiring IR, coil min-pickup, functional",
        "-- (aux / protective-trip / electrical-trip / heaters), dielectric withstand, PF/DF open+closed.",
        "-- R-A: IR -> 100.1 (neta_table); contact/connection/coil/dielectric/PF -> mfr. UUID5.",
        f"-- Coverage: {n}/24 (7.7).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(CS_ID, "ats_circuit_switcher_v1", "Circuit Switcher - ATS Field Data Sheet",
                     SEC, "circuit_switcher", schema,
                     "Circuit Switcher datasheet (NETA 7.7). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"circuit-switcher: sections={len(schema['sections'])} covered={n}/24")


if __name__ == "__main__":
    main()
