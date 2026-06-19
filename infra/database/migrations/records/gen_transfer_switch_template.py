#!/usr/bin/env python3
"""Generate 023_transfer_switch_template.sql - the Automatic Transfer Switch datasheet (NETA 7.22.3).

records Chip 2c (slice-3 coverage backlog): the Prime catalog ships an ATS datasheet; records did not.
One leaf-bound single-procedure sheet: ats_transfer_switch_v1 -> leaf 'ats' (already scaffolded in
Chip 2-shell). NETA 7.22.3 (Emergency Systems, Automatic Transfer Switches) = 11 VM + 8 electrical = 19.

R-A: an ATS has no integral trip curve; tolerance_source.engine is `neta_table` (IR -> Table 100.1) or
`mfr` (bolted/contact resistance; transfer timing vs mfr spec) - never tcc. The relay/timer calibration
(B.6) cross-refs Section 7.9 (recorded on the relay datasheet). Capture = field + cover_attach (no
standard single-instrument import format for an ATS).

Coverage invariant (fail-fast here, re-checked in test_023): union of section neta_covers covers all
7.22.3 ATS visual_mechanical + electrical items.

ASCII-only output. Deterministic UUID5 ids + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_transfer_switch_template.py [path-to-json]
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
OUT = os.path.join(HERE, "023_transfer_switch_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
ATS_ID = str(uuid.uuid5(NS_TPL, "ats_transfer_switch_v1"))
SEC = "7.22.3"
COND = ["sat", "unsat", "na"]
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# (key, label, cat A=visual_mechanical / B=electrical, item_no, optional, section_key)
CONCEPTS = [
    ("nameplate_vs_drawings", "Compare equipment nameplate data with drawings", "A", 1, False, "identification"),
    ("phys_mech", "Inspect physical and mechanical condition", "A", 2, False, "visual_mechanical"),
    ("anchorage", "Inspect anchorage, alignment, grounding, and required clearances", "A", 3, False, "visual_mechanical"),
    ("clean", "Verify the unit is clean", "A", 4, False, "visual_mechanical"),
    ("lubrication", "Verify lubrication on moving current-carrying and sliding parts", "A", 5, False, "visual_mechanical"),
    ("warning_labels", "Verify warning labels are attached and visible", "A", 6, False, "visual_mechanical"),
    ("control_tightness", "Verify tightness of all control connections", "A", 7, False, "visual_mechanical"),
    ("torque", "Bolted electrical connections torqued (calibrated wrench; Table 100.12)", "A", 8, False, "visual_mechanical"),
    ("manual_transfer", "Perform manual transfer operation", "A", 9, False, "visual_mechanical"),
    ("interlock", "Verify positive mechanical interlocking between normal and alternate sources", "A", 10, False, "visual_mechanical"),
    ("thermography", "Thermographic survey (Section 9)", "A", 11, True, "visual_mechanical"),
    ("bolted_r", "Resistance through bolted connections (low-resistance ohmmeter)", "B", 1, False, "bolted_resistance"),
    ("ir_poles", "Insulation resistance, 1 min, each pole, phase-phase and phase-ground", "B", 2, False, "insulation_resistance"),
    ("ir_control", "Insulation resistance on all control wiring to ground", "B", 3, False, "insulation_resistance"),
    ("contact_r", "Contact / pole-resistance test", "B", 4, False, "contact_resistance"),
    ("control_devices", "Verify settings and operation of control devices", "B", 5, False, "control_functions"),
    ("relays_timers", "Calibrate and set all relays and timers (Section 7.9)", "B", 6, False, "control_functions"),
    ("phase_rotation", "Verify phase rotation, phasing, and synchronized operation as required", "B", 7, False, "control_functions"),
    ("transfer_timing", "Verify correct operation and timing of transfer functions", "B", 8, False, "transfer_operation"),
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


def ir_section():
    rows = [
        {"key": "pole_1_2", "label": "Pole 1-2 (phase-phase)"},
        {"key": "pole_2_3", "label": "Pole 2-3 (phase-phase)"},
        {"key": "pole_1_3", "label": "Pole 1-3 (phase-phase)"},
        {"key": "pole_1_g", "label": "Pole 1 - ground"},
        {"key": "pole_2_g", "label": "Pole 2 - ground"},
        {"key": "pole_3_g", "label": "Pole 3 - ground"},
        {"key": "control_wiring", "label": "Control wiring - ground"},
    ]
    return {"key": "insulation_resistance", "title": "Insulation Resistance", "kind": "table",
            "table": {"row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
                      "columns": [
                          ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                          ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                              acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"},
                              tolerance_source={"engine": "neta_table", "table": "100.1",
                                                "inputs": ["voltage_rating"]}),
                          ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
                          ctl("corrected_mohm", "Corrected to 20degC", "numeric", "calc", unit="Mohm")]}}


def contact_r_section():
    return {"key": "contact_resistance", "title": "Contact / Pole Resistance", "kind": "table",
            "table": {"row_dim": {"tag": "pole", "label": "Pole",
                                  "rows": [{"key": p, "label": f"Pole {p}"} for p in ("A", "B", "C")]},
                      "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                      acceptance={"basis": "mfr_tolerance",
                                                  "rule": "compare poles / vs mfr; investigate deviation"},
                                      tolerance_source={"engine": "mfr", "function": "contact_resistance",
                                                        "inputs": ["manufacturer", "model"]}),
                                  ctl("temp", "Temp", "numeric", unit="degC")]}}


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
        ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
        ctl("current_rating", "Continuous current rating", "numeric", "inherited", unit="A"),
        ctl("poles", "Poles", "numeric", "inherited"),
        ctl("phases", "Phases", "numeric", "inherited"),
        ctl("withstand_rating", "Withstand / close-on rating", "numeric", "inherited", unit="kA"),
        ctl("transition_type", "Transition type", "selection", "inherited",
            options=["open", "closed", "delayed", "soft_load"]),
        ctl("control_voltage", "Control voltage", "numeric", "inherited", unit="V"),
        ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
            options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    control_functions = [
        ctl("control_devices", "Settings and operation of control devices verified", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.5"),
        ctl("relays_timers_xref", "Relays and timers calibrated/set per Section 7.9 (recorded on the relay datasheet)",
            "text", "reference", neta_ref=f"{SEC}.B.6"),
        ctl("phase_rotation", "Phase rotation, phasing, and synchronized operation verified", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.7"),
    ]
    transfer_operation = {
        "key": "transfer_operation", "title": "Transfer Operation and Timing", "kind": "table",
        "neta_basis": f"{SEC}.B.8",
        "table": {"row_dim": {"tag": "function", "label": "Function", "grow": True, "rows": [
            {"key": "normal_to_emergency", "label": "Transfer normal -> emergency"},
            {"key": "emergency_to_normal", "label": "Retransfer emergency -> normal"},
            {"key": "engine_start_delay", "label": "Engine start time delay"},
            {"key": "retransfer_delay", "label": "Retransfer time delay"},
            {"key": "neutral_dwell", "label": "Neutral / off-position dwell", "optional": True},
            {"key": "elevator_pretransfer", "label": "Pre-transfer signal", "optional": True}]},
            "columns": [ctl("spec_s", "Spec time (mfr)", "numeric", unit="s",
                            acceptance={"basis": "mfr_tolerance", "rule": "vs mfr setting / sequence-of-operations"},
                            tolerance_source={"engine": "mfr", "function": "transfer_timing",
                                              "inputs": ["manufacturer", "model"]}),
                        ctl("measured_s", "Measured time", "numeric", unit="s"),
                        ctl("result", "Result", "selection", options=["pass", "fail"])]},
    }

    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "fields": identification},
        vm_section(),
        {"key": "bolted_resistance", "title": "Bolted-Connection Resistance", "kind": "table",
         "table": {"row_dim": {"tag": "connection", "label": "Connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "bolted_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]}},
        ir_section(),
        contact_r_section(),
        {"key": "control_functions", "title": "Control Functions", "kind": "fields", "fields": control_functions},
        transfer_operation,
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    for s in sections:
        if cov.get(s["key"]):
            s["neta_covers"] = sorted(cov[s["key"]])
    return {"version": 1, "family": "transfer_switch", "capture": CAPTURE,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "contact_resistance", "transfer_timing"]}],
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
    assert not missing, f"ATS gap: {sorted(missing)}"
    assert not phantom, f"ATS phantom: {sorted(phantom)}"
    assert len(required) == 19, f"ATS expected 19, got {len(required)}"
    assert len(schema["sections"]) == 10, f"ATS sections={len(schema['sections'])} != 10"
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
        "-- Records Chip 2c - Automatic Transfer Switch datasheet (ats_transfer_switch_v1).",
        "-- GENERATED by gen_transfer_switch_template.py - do not edit by hand.",
        "-- One leaf-bound single-procedure sheet: NETA 7.22.3, 19 ATS items. Slice-3 coverage",
        "-- backlog (the Prime catalog has an ATS sheet; records did not). R-A: neta_table (IR ->",
        "-- 100.1) + mfr (bolted/contact R; transfer timing); relays/timers cross-ref 7.9. Capture:",
        "-- field + cover_attach (no instrument bridge). Windows resolved at provisioning. UUID5.",
        f"-- Coverage: {n}/19 (7.22.3).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
    ]
    out += sql_value(ATS_ID, "ats_transfer_switch_v1", "Automatic Transfer Switch - ATS Field Data Sheet",
                     SEC, "ats", schema, "Automatic Transfer Switch datasheet (NETA 7.22.3). Chip 2c; NETA-derived.")
    out += ["COMMIT;"]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"ATS: sections={len(schema['sections'])} covered={n}/19")


if __name__ == "__main__":
    main()
