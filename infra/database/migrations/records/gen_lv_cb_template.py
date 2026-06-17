#!/usr/bin/env python3
"""Generate 010_lv_cb_datasheet_template.sql - the LV circuit-breaker composite datasheet.

ONE composite template (ats_lv_cb_v1) for the cb_lv leaf. A construction_type selector
(power / insulated_case / molded_case) drives visible_if; the molded-case deltas (racking,
cell-fit, arc chutes, maintenance devices, counter) are gated OFF, not a separate template.

field_schema contract (object): {version, family, selections[], sections[]}. Each section is
kind=fields|table; controls carry tag/label/value_kind/unit?/options?/data_source/neta_ref?/
acceptance?/tolerance_source?. Acceptance windows are DECLARED (tolerance_source -> tcc) but
NOT valued - they resolve at provisioning (Chip 5) and ride down to the device (offline-sync
law). Computed fields (data_source=calc) are reserved; the calc engine is deferred (D-FORMS).

Coverage invariant (fail-fast here, re-checked in test_010 against records_dev): the union of
every section's neta_covers must cover all NETA 7.6.1.2 ATS visual_mechanical+electrical items
read from the master JSON - no silent drops, no phantom refs.

ASCII-only output (NETA trap). Deterministic UUID5 template_id + ON CONFLICT = idempotent.
Run: uv run --no-project python gen_lv_cb_template.py [path-to-json]
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
OUT = os.path.join(HERE, "010_lv_cb_datasheet_template.sql")
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")
TEMPLATE_ID = str(uuid.uuid5(NS_TPL, "ats_lv_cb_v1"))

SEC = "7.6.1.2"
DRAWOUT = "construction_type in ['power','insulated_case']"   # molded-case = sealed, non-drawout
LSIG = ["long", "short", "instantaneous", "ground"]
COND = ["sat", "unsat", "na"]


def ref(letter, n):
    return f"{SEC}.{letter}.{n}"


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# ---------------------------------------------------------------- selections
SELECTIONS = [
    {"tag": "construction_type", "label": "Breaker construction", "value_kind": "selection",
     "options": ["power", "insulated_case", "molded_case"], "ties_to": "equipment_model"},
    {"tag": "trip_unit_class", "label": "Trip unit", "value_kind": "selection",
     "options": ["electronic", "thermal_magnetic"], "ties_to": "equipment_model"},
    {"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
     "options": ["insulation_resistance", "contact_resistance",
                 "primary_injection", "secondary_injection"]},
]

# ---------------------------------------------------------------- 1. nameplate (R-C: inherited)
NAMEPLATE = [
    ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
    ctl("model", "Breaker type / model", "selection", "inherited", ties_to="equipment_model"),
    ctl("trip_unit", "Trip unit", "selection", "inherited", ties_to="equipment_model"),
    ctl("frame_size_a", "Frame size", "numeric", "inherited", unit="A"),
    ctl("sensor_tap_a", "Sensor tap", "numeric", "inherited", unit="A"),
    ctl("rating_plug_a", "Rating plug", "numeric", "inherited", unit="A"),
    ctl("catalog_no", "Catalog no.", "text", "inherited"),
    ctl("serial_no", "Serial no.", "text", "inherited"),
    ctl("mounting", "Mounting", "selection", "inherited", options=["drawout", "fixed"]),
    ctl("poles", "Poles", "numeric", "inherited"),
    ctl("voltage_rating", "Voltage rating", "numeric", "inherited", unit="V"),
    ctl("interrupting_rating", "Interrupting rating", "numeric", "inherited", unit="kA"),
    ctl("cubicle_code", "Cubicle code", "text", "data"),
    ctl("nameplate_vs_drawings", "Nameplate compared with drawings", "selection", "data",
        options=COND, neta_ref=ref("A", 1)),
]

# ---------------------------------------------------------------- 2. visual_mechanical (table)
# (key, neta item#, label, visible_if, optional)
VM_ROWS = [
    ("vm_phys_mech_condition", 2, "Physical and mechanical condition", None, False),
    ("vm_anchorage_align_ground", 3, "Anchorage, alignment, grounding", None, False),
    ("vm_maintenance_devices", 4, "Maintenance devices available", DRAWOUT, False),
    ("vm_clean", 5, "Unit is clean", None, False),
    ("vm_arc_chutes", 6, "Arc chutes intact", DRAWOUT, False),
    ("vm_contacts_condition_align", 7, "Moving/stationary contacts condition and alignment", None, False),
    ("vm_contact_wipe_dims", 8, "Primary/secondary contact wipe and dimensions", DRAWOUT, False),
    ("vm_mech_operator_align_tests", 9, "Mechanical operator and contact-alignment tests", None, False),
    ("vm_torque", 10, "Bolted connections torqued (calibrated wrench; Table 100.12)", None, False),
    ("vm_cell_fit_element_align", 11, "Cell fit and element alignment", DRAWOUT, False),
    ("vm_racking_mechanism", 12, "Racking mechanism operation", DRAWOUT, False),
    ("vm_lubrication", 13, "Lubrication of moving/sliding parts", None, False),
    ("vm_settings_per_coord_study", 14, "Protective-device settings per coordination study", None, False),
    ("vm_thermography", 16, "Thermographic survey (Section 9)", None, True),
]


def vm_section():
    rows = []
    for key, n, label, vis, opt in VM_ROWS:
        r = {"key": key, "label": label, "neta_ref": ref("A", n)}
        if vis:
            r["visible_if"] = vis
        if opt:
            r["optional"] = True
        rows.append(r)
    return {
        "key": "visual_mechanical", "title": "Visual and Mechanical Inspection",
        "kind": "table", "neta_basis": SEC,
        "table": {
            "row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
            "columns": [
                ctl("inspected", "Inspected", "boolean"),
                ctl("condition", "Condition", "selection", options=COND),
                ctl("clean_lube", "Clean / lube", "selection", options=COND + ["not_applicable"]),
                ctl("value", "Value (e.g. torque)", "text"),
                ctl("note", "Note", "text"),
            ],
        },
    }


# ---------------------------------------------------------------- 3. operation_counter (A.15)
COUNTER = [
    ctl("vm_counter_as_found", "Operation counter - as found", "numeric", "data",
        neta_ref=ref("A", 15), visible_if=DRAWOUT),
    ctl("vm_counter_as_left", "Operation counter - as left", "numeric", "data",
        neta_ref=ref("A", 15), visible_if=DRAWOUT),
]


# ---------------------------------------------------------------- helpers for tables
def lsig_rows():
    labels = {"long": "Long-time", "short": "Short-time",
              "instantaneous": "Instantaneous", "ground": "Ground-fault"}
    return [{"key": k, "label": labels[k]} for k in LSIG]


def settings_section():
    cols = []
    for af in ("af", "al"):
        pfx = "As-found" if af == "af" else "As-left"
        cols += [
            ctl(f"{af}_pickup", f"{pfx} pickup setting", "text"),
            ctl(f"{af}_factor", f"{pfx} pickup factor (x Ir)", "numeric"),
            ctl(f"{af}_delay", f"{pfx} delay", "text"),
            ctl(f"{af}_curve", f"{pfx} curve", "text"),
        ]
    return {
        "key": "settings_lsig", "title": "Trip-Unit Settings (As-Found / As-Left)",
        "kind": "table", "neta_basis": ref("A", 14),
        "visible_if": "trip_unit_class == 'electronic'",
        "table": {"row_dim": {"tag": "function", "label": "Function", "rows": lsig_rows()},
                  "columns": cols},
    }


def ir_section():
    rows = [
        {"key": "pole_1_2", "label": "Pole 1-2"},
        {"key": "pole_2_3", "label": "Pole 2-3"},
        {"key": "pole_1_3", "label": "Pole 1-3"},
        {"key": "pole_to_ground_closed", "label": "Pole-to-ground (closed)"},
        {"key": "across_open_pole", "label": "Across each open pole"},
        {"key": "control_wiring", "label": "Control wiring"},
        {"key": "line_to_load", "label": "Line-to-load"},
    ]
    return {
        "key": "insulation_resistance", "title": "Insulation Resistance",
        "kind": "table", "neta_basis": ref("B", 1), "neta_covers": [ref("B", 1)],
        "table": {
            "row_dim": {"tag": "measurement", "label": "Measurement", "rows": rows},
            "columns": [
                ctl("test_voltage", "Test voltage", "numeric", unit="V"),
                ctl("reading_mohm", "Reading", "numeric", unit="Mohm",
                    acceptance={"basis": "mfr_tolerance", "fallback_table": "100.1"}),
                ctl("equip_temp", "Equipment temp", "numeric", unit="degC"),
                ctl("tcf", "Temp-correction factor", "numeric", "calc"),
                ctl("corrected_mohm", "Corrected to 20degC", "numeric", "calc", unit="Mohm"),
            ],
        },
    }


def contact_r_section():
    return {
        "key": "contact_resistance", "title": "Contact / Pole Resistance",
        "kind": "table", "neta_basis": ref("B", 2), "neta_covers": [ref("B", 2)],
        "table": {
            "row_dim": {"tag": "pole", "label": "Pole",
                        "rows": [{"key": p, "label": f"Pole {p}"} for p in ("A", "B", "C")]},
            "columns": [
                ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                    acceptance={"basis": "mfr_tolerance", "rule": "investigate >50% pole-pole deviation"}),
                ctl("temp", "Temp", "numeric", unit="degC"),
            ],
        },
    }


def primary_injection_section():
    cols = [
        ctl("pickup_amps", "Pickup", "numeric", unit="A"),
        ctl("test_multiple", "Test multiple", "numeric"),
        ctl("test_amps", "Test current", "numeric", unit="A"),
        ctl("trip_time_af", "Trip time (as found)", "numeric", unit="s"),
        ctl("trip_time_al", "Trip time (as left)", "numeric", unit="s"),
        ctl("min_time", "Min acceptable time", "numeric", "calc", unit="s",
            acceptance={"basis": "mfr_tolerance", "fallback_table": "100.7"},
            tolerance_source={"engine": "tcc", "function": "$row",
                              "inputs": ["trip_unit", "construction_type", "$row_settings"]}),
        ctl("max_time", "Max acceptable time", "numeric", "calc", unit="s",
            acceptance={"basis": "mfr_tolerance", "fallback_table": "100.7"},
            tolerance_source={"engine": "tcc", "function": "$row",
                              "inputs": ["trip_unit", "construction_type", "$row_settings"]}),
        ctl("voltage_drop", "Voltage drop @ test current", "numeric", unit="mV"),
        ctl("result", "Result", "selection", "calc", options=["pass", "fail"]),
    ]
    return {
        "key": "primary_injection",
        "title": "Pickup and Timing (Primary Injection)",
        "kind": "table", "neta_basis": SEC, "per_pole": True,
        "visible_if": "'primary_injection' in tests_performed",
        "neta_covers": [ref("B", 3), ref("B", 4), ref("B", 5), ref("B", 6)],
        "table": {"row_dim": {"tag": "function", "label": "Function", "rows": lsig_rows()},
                  "columns": cols},
    }


SECONDARY = [
    ctl("si_trip_functions", "Trip-unit functions verified by secondary injection",
        "selection", "data", options=COND, neta_ref=ref("B", 7), optional=True),
]

AUX = [
    ctl("aux_zone_interlock", "Zone-selective interlocking", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_trip_pickup_indicators", "Trip and pickup indicators", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_electrical_close_trip", "Electrical close and trip", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_trip_free", "Trip-free operation", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_antipump", "Anti-pump function", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_battery_condition", "Trip-unit battery condition", "selection", "data", options=COND, neta_ref=ref("B", 8)),
    ctl("aux_charging_mechanism", "Charging mechanism operation", "selection", "data",
        options=COND, neta_ref=ref("B", 9), visible_if=DRAWOUT),
]

TEST_EQUIPMENT = {
    "key": "test_equipment", "title": "Test Equipment Used", "kind": "table",
    "table": {"row_dim": {"tag": "equipment", "label": "Instrument", "rows": [], "grow": True},
              "columns": [
                  ctl("manufacturer", "Manufacturer", "text", "inherited"),
                  ctl("model", "Model", "text", "inherited"),
                  ctl("type", "Type", "text", "inherited"),
                  ctl("serial_id", "Serial / ID", "text", "inherited"),
                  ctl("cal_date", "Cal date", "date", "inherited"),
                  ctl("cal_due", "Cal due", "date", "inherited"),
              ]},
}

COMMENTS = [
    ctl("comments", "Comments", "text", "data", grow=True),
    ctl("deficiencies", "Deficiencies", "text", "data", grow=True),
]


def collect_refs(section):
    """neta_covers = explicit seed UNION every neta_ref found in the section's controls/rows."""
    refs = set(section.get("neta_covers", []))
    for f in section.get("fields", []):
        if f.get("neta_ref"):
            refs.add(f["neta_ref"])
    tbl = section.get("table", {})
    for r in tbl.get("row_dim", {}).get("rows", []):
        if r.get("neta_ref"):
            refs.add(r["neta_ref"])
    for c in tbl.get("columns", []):
        if c.get("neta_ref"):
            refs.add(c["neta_ref"])
    if refs:
        section["neta_covers"] = sorted(refs)
    return section


def build_schema():
    sections = [
        {"key": "nameplate", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": ref("A", 1), "fields": NAMEPLATE},
        vm_section(),
        {"key": "operation_counter", "title": "Operation Counter", "kind": "fields",
         "neta_basis": ref("A", 15), "fields": COUNTER},
        settings_section(),
        ir_section(),
        contact_r_section(),
        primary_injection_section(),
        {"key": "secondary_injection", "title": "Secondary Injection (optional)", "kind": "fields",
         "neta_basis": ref("B", 7), "visible_if": "'secondary_injection' in tests_performed",
         "fields": SECONDARY},
        {"key": "auxiliary", "title": "Auxiliary Features", "kind": "fields",
         "neta_basis": ref("B", 8), "fields": AUX},
        TEST_EQUIPMENT,
        {"key": "comments_deficiencies", "title": "Comments and Deficiencies", "kind": "fields",
         "fields": COMMENTS},
    ]
    for s in sections:
        collect_refs(s)
    return {"version": 1, "family": "lv_circuit_breaker",
            "selections": SELECTIONS, "sections": sections}


def required_refs(json_path):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x["section"] == SEC)
    ats = e.get("ats_data") or {}
    vm = ats.get("visual_mechanical") or []
    el = ats.get("electrical_tests") or []
    return ({ref("A", i + 1) for i in range(len(vm))}
            | {ref("B", i + 1) for i in range(len(el))})


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    schema = build_schema()

    covered = set()
    for s in schema["sections"]:
        covered |= set(s.get("neta_covers", []))
    required = required_refs(src)
    missing = required - covered
    phantom = {r for r in covered if r.startswith(SEC + ".")} - required
    assert not missing, f"coverage gap (silent drop): {sorted(missing)}"
    assert not phantom, f"phantom coverage (no such NETA item): {sorted(phantom)}"
    assert len(schema["sections"]) == 11, len(schema["sections"])

    payload = json.dumps(schema, ensure_ascii=True, separators=(",", ":"))
    sql_json = payload.replace("'", "''")
    out = [
        "-- =============================================================================",
        "-- Records Chip 2b - LV Circuit-Breaker composite datasheet (ats_lv_cb_v1).",
        "-- GENERATED by gen_lv_cb_template.py - do not edit by hand.",
        "-- ONE template; construction_type selector gates the molded-case deltas.",
        "-- Acceptance windows DECLARED (tolerance_source -> tcc), resolved at provisioning.",
        f"-- Coverage: all {len(required)} NETA {SEC} ATS items mapped (validator-enforced).",
        "-- Idempotent (ON CONFLICT); deterministic UUID5 template_id.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "INSERT INTO records.form_templates",
        "  (template_id, template_code, title, form_type, neta_standard, neta_section,",
        "   asset_class_id, version, is_current, field_schema, description, source)",
        "VALUES (",
        f"  '{TEMPLATE_ID}', 'ats_lv_cb_v1',",
        "  'Low-Voltage Circuit Breaker - ATS Field Data Sheet',",
        "  'neta_datasheet', 'ats', '7.6.1.2',",
        "  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = 'cb_lv'),",
        "  1, true,",
        f"  '{sql_json}'::jsonb,",
        "  'Composite LV circuit-breaker datasheet (Power/ICCB/MCCB via construction_type). Chip 2b.',",
        "  'manual'",
        ")",
        "ON CONFLICT (template_code, version) DO UPDATE SET",
        "  field_schema = EXCLUDED.field_schema, title = EXCLUDED.title,",
        "  neta_section = EXCLUDED.neta_section, asset_class_id = EXCLUDED.asset_class_id,",
        "  description = EXCLUDED.description, updated_at = now();",
        "",
        "COMMIT;",
    ]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"sections={len(schema['sections'])}  selections={len(schema['selections'])}  "
          f"neta_covered={len(covered & required)}/{len(required)}  json_bytes={len(payload)}")


if __name__ == "__main__":
    main()
