#!/usr/bin/env python3
"""Generate 042_network_protector_template.sql - the Network Protector datasheet (NETA 7.8).

records Chip 2c FOLLOW-ON (the last genuine missing apparatus-family leaf). The Chip-2-shell
(007) created the `network_protectors` parent INACTIVE with no leaf. This one migration:
  (a) INSERTs the `network_protector` leaf + activates the parent (post-foundation leaf-add,
      mirroring the surge 017 pattern);
  (b) links the leaf to the 7.8 procedure (primary);
  (c) INSERTs `ats_network_protector_v1` -- born v2 STANDARD-AWARE (post-244): shared physical
      sections, each carrying a per-standard `neta_covers` {ats,mts} map. Covers BOTH
      ATS (29 items: 17 VM + 12 electrical) and MTS (27 items: 16 VM + 11 electrical).
      The "minor differences" are item-level: ATS-only nameplate-compare (A.1) + phase
      rotation/sync (B.12); MTS-only as-found/clean/as-left maintenance (A.3/A.4/A.14).

R-A: IR -> 100.1 (neta_table); connection/contact/control-IR/power-fuse/relay-pickup -> mfr;
CT-ratio xref 7.10 + master/phasing-relay calibration xref 7.9; NEVER tcc (a network protector
has no integral trip curve -- protection is the external network-protector relay, 7.9).

Coverage invariant (fail-fast here, re-checked per-standard in test_042). ASCII-only. UUID5.
Run: uv run --no-project python gen_network_protector_template.py [path-to-json]
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
OUT = os.path.join(HERE, "042_network_protector_template.sql")
OUT_DOWN = os.path.join(HERE, "042_network_protector_template_down.sql")

NS_CLASS = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a2")  # matches gen_shell_seed.py
NS_BF = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a3")     # matches gen_backfill_seed.py
NS_TPL = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a4")    # matches the Chip-2c template gens

LEAF = "network_protector"
PARENT = "network_protectors"
SEC = "7.8"
CODE = "ats_network_protector_v1"

LEAF_ID = str(uuid.uuid5(NS_CLASS, LEAF))
ACNP_ID = str(uuid.uuid5(NS_BF, f"acnp:{LEAF}:{SEC}"))
TPL_ID = str(uuid.uuid5(NS_TPL, CODE))

COND = ["sat", "unsat", "na"]
CAPTURE = {"modes": ["field", "cover_attach"], "default": "field"}
STDS = ["ats", "mts"]


def ctl(tag, label, value_kind, data_source="data", **kw):
    c = {"tag": tag, "label": label, "value_kind": value_kind, "data_source": data_source}
    for k, v in kw.items():
        if v is not None:
            c[k] = v
    return c


# ---------------------------------------------------------------------------
# Per-standard item -> physical-section placement. The ATS and MTS item lists are
# semantically parallel but offset in numbering (the "minor differences"); both map onto
# the SAME physical sections, so each NETA section carries a {ats,mts} neta_covers map.
# (Verified against records_dev: ATS 17 VM + 12 elec = 29; MTS 16 VM + 11 elec = 27.)
# ---------------------------------------------------------------------------
ATS_PLACE = {
    "A.1": "identification",                                   # nameplate compare (ATS-only)
    **{f"A.{n}": "visual_mechanical" for n in range(2, 16)},   # A.2..A.15 inspection
    "A.16": "operation_counters",
    "A.17": "submersible_enclosure",
    "B.1": "connection_resistance",
    "B.2": "insulation_resistance",
    "B.3": "contact_resistance",
    "B.4": "control_wiring_ir",
    "B.5": "ct_ratio",
    "B.6": "power_fuse",
    "B.7": "relay_pickup", "B.8": "relay_pickup", "B.9": "relay_pickup",
    "B.10": "relay_calibration",
    "B.11": "operational", "B.12": "operational",              # B.12 phase rotation/sync (ATS-only)
}
MTS_PLACE = {
    **{f"A.{n}": "visual_mechanical" for n in range(1, 15)},   # A.1..A.14 inspection (incl. as-found/as-left)
    "A.15": "operation_counters",
    "A.16": "submersible_enclosure",
    "B.1": "connection_resistance",
    "B.2": "insulation_resistance",
    "B.3": "contact_resistance",
    "B.4": "control_wiring_ir",
    "B.5": "ct_ratio",
    "B.6": "power_fuse",
    "B.7": "relay_pickup", "B.8": "relay_pickup", "B.9": "relay_pickup",
    "B.10": "relay_calibration",
    "B.11": "operational",
}


def _refkey(ref):
    p = ref.split(".")
    return (p[2], int(p[3]))


def covers_for(section_key):
    a = sorted((f"{SEC}.{k}" for k, s in ATS_PLACE.items() if s == section_key), key=_refkey)
    m = sorted((f"{SEC}.{k}" for k, s in MTS_PLACE.items() if s == section_key), key=_refkey)
    return {"ats": a, "mts": m}


# ATS-numbered visual/mechanical inspection rows (A.2..A.15). Displayed face is ATS-oriented;
# the per-standard coverage lives in the section neta_covers map (MTS folded in).
VM_ROWS = [
    ("phys_mech", "Inspect physical and mechanical condition", "A.2"),
    ("anchorage", "Inspect anchorage, alignment, and grounding", "A.3"),
    ("clean", "Verify the unit is clean", "A.4"),
    ("arc_chutes", "Verify arc chutes are intact", "A.5"),
    ("primary_switch", "Inspect network transformer primary (open / close / ground) switch", "A.6"),
    ("isolation_switch", "Inspect the network protector collector-bus isolation switch", "A.7"),
    ("contacts", "Inspect moving and stationary contacts for condition and alignment", "A.8"),
    ("maint_devices", "Verify maintenance devices are available for servicing and operating the protector", "A.9"),
    ("contact_wipe", "Verify primary and secondary contact wipe and other vital dimensions", "A.10"),
    ("mech_operator", "Perform mechanical operator and contact-alignment tests on the protector and its operating mechanism", "A.11"),
    ("torque", "Verify tightness of accessible bolted electrical connections (calibrated torque-wrench; Table 100.12)", "A.12"),
    ("cell_fit", "Verify cell fit and element alignment", "A.13"),
    ("racking", "Verify racking-mechanism operation", "A.14"),
    ("lubrication", "Verify appropriate lubrication on moving current-carrying parts and moving / sliding surfaces", "A.15"),
]


def vm_section():
    rows = [{"key": k, "label": lbl, "neta_ref": f"{SEC}.{ref}"} for k, lbl, ref in VM_ROWS]
    return {
        "key": "visual_mechanical", "title": "Visual and Mechanical Inspection", "kind": "table",
        "neta_basis": SEC, "standards": STDS,
        "table": {"row_dim": {"tag": "item", "label": "Inspection item", "rows": rows},
                  "columns": [ctl("inspected", "Inspected", "boolean"),
                              ctl("condition", "Condition", "selection", options=COND),
                              ctl("value", "Value", "text"), ctl("note", "Note", "text")]},
        "neta_covers": covers_for("visual_mechanical"),
    }


TEST_EQUIPMENT = {
    "key": "test_equipment", "title": "Test Equipment Used", "kind": "table", "standards": STDS,
    "table": {"row_dim": {"tag": "equipment", "label": "Instrument", "rows": [], "grow": True},
              "columns": [ctl("manufacturer", "Manufacturer", "text", "inherited"),
                          ctl("model", "Model", "text", "inherited"),
                          ctl("type", "Type", "text", "inherited"),
                          ctl("serial_id", "Serial / ID", "text", "inherited"),
                          ctl("cal_date", "Cal date", "date", "inherited"),
                          ctl("cal_due", "Cal due", "date", "inherited")]},
    "neta_covers": {"ats": [], "mts": []},
}
COMMENTS = {"key": "comments_deficiencies", "title": "Comments and Deficiencies", "kind": "fields",
            "standards": STDS,
            "fields": [ctl("comments", "Comments", "text", "data", grow=True),
                       ctl("deficiencies", "Deficiencies", "text", "data", grow=True)],
            "neta_covers": {"ats": [], "mts": []}}
ATTACHMENTS = {"key": "attachments", "title": "Source Documents (OEM / commissioning report)",
               "kind": "attachment", "capture_mode": "cover_attach", "standards": STDS,
               "fields": [ctl("report", "Attached report", "attachment", "data", grow=True),
                          ctl("report_source", "Report source", "selection", "data",
                              options=["engineer_of_record", "third_party_lab", "oem"]),
                          ctl("report_satisfies", "Report satisfies the datasheet requirements",
                              "selection", "data", options=COND)],
               "neta_covers": {"ats": [], "mts": []}}


def build():
    identification = [
        ctl("manufacturer", "Manufacturer", "selection", "inherited", ties_to="equipment_model"),
        ctl("model", "Type / model", "selection", "inherited", ties_to="equipment_model"),
        ctl("serial_no", "Serial no.", "text", "inherited"),
        ctl("rated_voltage", "Rated voltage", "numeric", "inherited", unit="V"),
        ctl("continuous_current", "Continuous current rating", "numeric", "inherited", unit="A"),
        ctl("interrupting_rating", "Interrupting rating", "numeric", "inherited", unit="kA"),
        ctl("network_transformer", "Associated network transformer", "text", "inherited"),
        ctl("nameplate_vs_drawings",
            "Compare nameplate data of the protector, network transformer primary switch, and fuses with drawings",
            "selection", "data", options=COND, neta_ref=f"{SEC}.A.1"),
    ]
    operation_counters = [
        ctl("counter_as_found", "Operation counter (as found)", "numeric", "data", neta_ref=f"{SEC}.A.16"),
        ctl("counter_as_left", "Operation counter (as left)", "numeric", "data"),
    ]
    submersible_enclosure = [
        ctl("enclosure_type", "Enclosure type", "selection", "data",
            options=["submersible", "vault", "non_submersible"]),
        ctl("leak_test", "Submersible-enclosure leak test per mfr published data", "selection", "data",
            options=COND + ["not_applicable"], neta_ref=f"{SEC}.A.17"),
        ctl("leak_note", "Leak-test note", "text", "data"),
    ]
    control_wiring_ir = [
        ctl("control_test_v", "Applied voltage", "numeric", "data", unit="V"),
        ctl("control_ir_mohm", "Control-wiring IR (1 min, to ground)", "numeric", "data", unit="Mohm",
            acceptance={"basis": "mfr_tolerance"},
            tolerance_source={"engine": "mfr", "function": "control_wiring_ir",
                              "inputs": ["manufacturer", "model"]}, neta_ref=f"{SEC}.B.4"),
        ctl("control_result", "Result", "selection", "data", options=COND),
    ]
    ct_ratio = [
        ctl("ct_ratio_verified", "Current-transformer ratios verified (per Section 7.10)",
            "selection", "data", options=COND, neta_ref=f"{SEC}.B.5",
            acceptance={"basis": "cross_reference", "note": "see Section 7.10"}),
        ctl("ct_ratio_note", "CT ratio / note", "text", "data"),
    ]
    relay_calibration = [
        ctl("relay_type", "Network protector relay type", "selection", "data",
            options=["electro_mechanical", "solid_state", "microprocessor"]),
        ctl("relay_calibration",
            "Master and phasing relay tested and calibrated (per Section 7.9)",
            "selection", "data", options=COND, neta_ref=f"{SEC}.B.10",
            acceptance={"basis": "cross_reference", "note": "see Section 7.9"}),
        ctl("relay_note", "Calibration note", "text", "data"),
    ]
    operational = [
        ctl("operational_tests", "Operational tests performed", "selection", "data",
            options=COND, neta_ref=f"{SEC}.B.11"),
        ctl("phase_rotation", "Phase rotation, phasing, and synchronized operation verified",
            "selection", "data", options=COND + ["not_applicable"], neta_ref=f"{SEC}.B.12"),
    ]

    sections = [
        {"key": "identification", "title": "Identification / Nameplate", "kind": "fields",
         "neta_basis": f"{SEC}.A.1", "standards": STDS, "fields": identification,
         "neta_covers": covers_for("identification")},
        vm_section(),
        {"key": "operation_counters", "title": "Operation Counters", "kind": "fields",
         "standards": STDS, "fields": operation_counters,
         "neta_covers": covers_for("operation_counters")},
        {"key": "submersible_enclosure", "title": "Submersible Enclosure", "kind": "fields",
         "standards": STDS, "fields": submersible_enclosure,
         "neta_covers": covers_for("submersible_enclosure")},
        {"key": "connection_resistance", "title": "Connection Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.1", "standards": STDS,
         "table": {"row_dim": {"tag": "connection", "label": "Bolted connection", "rows": [], "grow": True},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "connection_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("temp", "Temp", "numeric", unit="degC")]},
         "neta_covers": covers_for("connection_resistance")},
        {"key": "insulation_resistance", "title": "Insulation Resistance (phase-phase and phase-ground)",
         "kind": "table", "neta_basis": f"{SEC}.B.2", "standards": STDS,
         "table": {"row_dim": {"tag": "config", "label": "Measurement",
                               "rows": ["P1-P2", "P2-P3", "P3-P1", "P1-G", "P2-G", "P3-G"]},
                   "columns": [ctl("test_v", "Test voltage", "numeric", unit="V"),
                               ctl("one_min_mohm", "1 min", "numeric", unit="Mohm",
                                   acceptance={"basis": "neta_table", "table": "100.1"},
                                   tolerance_source={"engine": "neta_table", "table": "100.1",
                                                     "function": "insulation_resistance",
                                                     "inputs": ["rated_voltage"]}),
                               ctl("temp", "Temp", "numeric", unit="degC"),
                               ctl("result", "Result", "selection", options=COND)]},
         "neta_covers": covers_for("insulation_resistance")},
        {"key": "contact_resistance", "title": "Contact / Pole Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.3", "standards": STDS,
         "table": {"row_dim": {"tag": "pole", "label": "Pole", "rows": ["P1", "P2", "P3"]},
                   "columns": [ctl("micro_ohms", "Resistance", "numeric", unit="uohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "contact_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]},
         "neta_covers": covers_for("contact_resistance")},
        {"key": "control_wiring_ir", "title": "Control-Wiring Insulation Resistance", "kind": "fields",
         "standards": STDS, "fields": control_wiring_ir,
         "neta_covers": covers_for("control_wiring_ir")},
        {"key": "ct_ratio", "title": "Current-Transformer Ratio (per 7.10)", "kind": "fields",
         "standards": STDS, "fields": ct_ratio, "neta_covers": covers_for("ct_ratio")},
        {"key": "power_fuse", "title": "Network Protector Power-Fuse Resistance", "kind": "table",
         "neta_basis": f"{SEC}.B.6", "standards": STDS,
         "table": {"row_dim": {"tag": "fuse", "label": "Power fuse", "rows": ["F1", "F2", "F3"]},
                   "columns": [ctl("milli_ohms", "Resistance", "numeric", unit="mohm",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "fuse_resistance",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]},
         "neta_covers": covers_for("power_fuse")},
        {"key": "relay_pickup", "title": "Minimum Pickup / Motor Operation", "kind": "table",
         "neta_basis": f"{SEC}.B.7", "standards": STDS,
         "table": {"row_dim": {"tag": "device", "label": "Device",
                               "rows": [{"key": "motor_control_relay", "label": "Motor control relay min pickup",
                                         "neta_ref": f"{SEC}.B.7"},
                                        {"key": "motor_charge", "label": "Motor charges closing mechanism at min voltage",
                                         "neta_ref": f"{SEC}.B.8"},
                                        {"key": "trip_actuator", "label": "Trip actuator min pickup (and reset)",
                                         "neta_ref": f"{SEC}.B.9"}]},
                   "columns": [ctl("rated_v", "Rated control V", "numeric", unit="V"),
                               ctl("pickup_v", "Min pickup", "numeric", unit="V",
                                   acceptance={"basis": "mfr_tolerance"},
                                   tolerance_source={"engine": "mfr", "function": "min_pickup",
                                                     "inputs": ["manufacturer", "model"]}),
                               ctl("result", "Result", "selection", options=COND)]},
         "neta_covers": covers_for("relay_pickup")},
        {"key": "relay_calibration", "title": "Network Protector Relay Calibration (per 7.9)",
         "kind": "fields", "neta_basis": f"{SEC}.B.10", "standards": STDS,
         "fields": relay_calibration, "neta_covers": covers_for("relay_calibration")},
        {"key": "operational", "title": "Operational / Phasing", "kind": "fields",
         "neta_basis": f"{SEC}.B.11", "standards": STDS, "fields": operational,
         "neta_covers": covers_for("operational")},
        TEST_EQUIPMENT, COMMENTS, ATTACHMENTS,
    ]
    return {"version": 1, "family": "network_protector", "capture": CAPTURE,
            "neta_standards": STDS,
            "selections": [{"tag": "tests_performed", "label": "Tests performed", "value_kind": "multiselect",
                            "options": ["insulation_resistance", "contact_resistance", "power_fuse",
                                        "relay_pickup", "relay_calibration", "operational"]}],
            "sections": sections}


def required_refs(json_path, std):
    d = json.load(open(json_path, encoding="utf-8"))
    e = next(x for x in d["equipment"] if x.get("section") == SEC)
    blk = e.get(f"{std}_data") or {}
    vm = blk.get("visual_mechanical") or []
    el = blk.get("electrical_tests") or []
    return ({f"{SEC}.A.{i + 1}" for i in range(len(vm))}
            | {f"{SEC}.B.{i + 1}" for i in range(len(el))})


def check(schema, src):
    for std, expect in (("ats", 29), ("mts", 27)):
        covered = set()
        for s in schema["sections"]:
            nc = s.get("neta_covers")
            if isinstance(nc, dict):
                covered |= set(nc.get(std, []))
        required = required_refs(src, std)
        missing = required - covered
        phantom = {r for r in covered if r.startswith(SEC + ".")} - required
        assert not missing, f"{std} gap: {sorted(missing)}"
        assert not phantom, f"{std} phantom: {sorted(phantom)}"
        assert len(required) == expect, f"{std} expected {expect}, got {len(required)}"
    # every neta_covers is a per-standard map; never tcc
    blob = json.dumps(schema).replace(" ", "")
    assert '"engine":"tcc"' not in blob, "network protector must never use the tcc engine"
    return len(schema["sections"])


def q(s):
    return s.replace("'", "''")


def build_up(schema):
    payload = json.dumps(schema, ensure_ascii=True, separators=(",", ":")).replace("'", "''")
    return "\n".join([
        "-- =============================================================================",
        "-- Records Chip 2c FOLLOW-ON - Network Protector datasheet (ats_network_protector_v1).",
        "-- GENERATED by gen_network_protector_template.py - do not edit by hand.",
        "-- (a) network_protector LEAF + activate the network_protectors parent (post-foundation",
        "--     leaf-add, surge-017 pattern); (b) leaf -> 7.8 procedure link (primary);",
        "-- (c) the datasheet, born v2 STANDARD-AWARE: ATS 29 + MTS 27 via per-standard neta_covers.",
        "-- R-A: IR -> 100.1 (neta_table); connection/contact/control-IR/fuse/pickup -> mfr;",
        "-- CT-ratio xref 7.10 + relay calibration xref 7.9; never tcc. Idempotent UUID5.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "-- (a) activate the parent (shell-seeded inactive) and add the leaf under it.",
        "UPDATE records.asset_classes SET is_active = true, updated_at = now()",
        f"  WHERE class_code = '{PARENT}';",
        "",
        "INSERT INTO records.asset_classes (asset_class_id, class_code, name, parent_class_id, is_active)",
        "VALUES (",
        f"  '{LEAF_ID}', '{LEAF}', 'Network Protector',",
        f"  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = '{PARENT}'),",
        "  true)",
        "ON CONFLICT (class_code) DO UPDATE SET name = EXCLUDED.name,",
        "  parent_class_id = EXCLUDED.parent_class_id, is_active = EXCLUDED.is_active, updated_at = now();",
        "",
        "-- (b) leaf -> 7.8 procedure link (primary).",
        "INSERT INTO records.asset_class_neta_procedure",
        "  (asset_class_neta_procedure_id, asset_class_id, neta_procedure_id, is_primary)",
        "VALUES (",
        f"  '{ACNP_ID}',",
        f"  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = '{LEAF}'),",
        f"  (SELECT neta_procedure_id FROM records.neta_procedures WHERE section = '{SEC}'),",
        "  true)",
        "ON CONFLICT (asset_class_id, neta_procedure_id) DO UPDATE SET is_primary = EXCLUDED.is_primary;",
        "",
        "-- (c) the datasheet.",
        "INSERT INTO records.form_templates",
        "  (template_id, template_code, title, form_type, neta_standard, neta_section,",
        "   asset_class_id, version, is_current, field_schema, description, source)",
        "VALUES (",
        f"  '{TPL_ID}', '{CODE}',",
        "  'Network Protector (600 V Class) - ATS Field Data Sheet',",
        f"  'neta_datasheet', 'ats', '{SEC}',",
        f"  (SELECT asset_class_id FROM records.asset_classes WHERE class_code = '{LEAF}'),",
        "  1, true,",
        f"  '{payload}'::jsonb,",
        "  'Network Protector datasheet (NETA 7.8). Chip 2c follow-on; NETA-derived; standard-aware (ATS+MTS).',",
        "  'manual'",
        ")",
        "ON CONFLICT (template_code, version) DO UPDATE SET",
        "  field_schema = EXCLUDED.field_schema, title = EXCLUDED.title,",
        "  neta_section = EXCLUDED.neta_section, asset_class_id = EXCLUDED.asset_class_id,",
        "  description = EXCLUDED.description, updated_at = now();",
        "",
        "COMMIT;",
        "",
    ])


def build_down():
    return "\n".join([
        "-- =============================================================================",
        "-- DOWN for 042 - remove the Network Protector datasheet, link, and leaf; re-deactivate parent.",
        "-- Reversible; leaves the 2a NETA reference + 2-shell taxonomy intact. Safe before the up",
        "-- (DELETEs are no-ops if absent). Order: template (FK), then link, then leaf, then parent flag.",
        "-- =============================================================================",
        "BEGIN;",
        f"DELETE FROM records.form_templates WHERE template_code = '{CODE}';",
        "DELETE FROM records.asset_class_neta_procedure",
        f"  WHERE asset_class_id = (SELECT asset_class_id FROM records.asset_classes WHERE class_code = '{LEAF}');",
        f"DELETE FROM records.asset_classes WHERE class_code = '{LEAF}';",
        "-- restore the parent to its shell-seeded inactive state (007 marked it future/inactive).",
        "UPDATE records.asset_classes SET is_active = false, updated_at = now()",
        f"  WHERE class_code = '{PARENT}';",
        "COMMIT;",
        "",
    ])


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    schema = build()
    n = check(schema, src)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_up(schema))
    with open(OUT_DOWN, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_down())
    print(f"wrote {OUT}")
    print(f"wrote {OUT_DOWN}")
    print(f"network-protector: sections={n}  leaf={LEAF}  parent={PARENT} (activated)  "
          f"ATS=29  MTS=27  template={CODE}")


if __name__ == "__main__":
    main()
