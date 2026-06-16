"""Generate records migration 007 — the asset_class family shell (2-level, NETA-anchored).

PARENTS = the NETA equipment categories (27: 19 active + 8 future/inactive). They carry
`neta_category` (the anchor into records.neta_procedures.category) and own no assets directly.
LEAVES = the practical apparatus class a field tech selects (36); they hang off a parent via
`parent_class_id`, carry no neta_category (resolved through the parent), and are where
form_templates + assets attach in later chips.

Granularity is operator-approved (2026-06-15): split where the tests genuinely differ
(CT/VT/CVT; capacitor/reactor/NGR/HFB; LV vs MV/HV breaker), one leaf where they share a sheet.

Deterministic uuid5(NS, class_code) so re-runs are stable and parent FKs resolve. Idempotent
via ON CONFLICT (class_code). Emits 007_asset_class_shell.sql (up) + 007_asset_class_shell_down.sql.

Run:  python gen_shell_seed.py     (writes both files next to this script)
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
# Asset-class namespace ('...a2'); Chip-2a's NETA seed used '...a1'.
NS = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a2")


def cid(code: str) -> str:
    return str(uuid.uuid5(NS, code))


# (class_code, display name, is_active). class_code == the NETA category key so the
# neta_category anchor is the column value itself.
PARENTS = [
    ("circuit_breakers", "Circuit Breakers", True),
    ("transformers", "Transformers", True),
    ("switchgear", "Switchgear and Switchboard Assemblies", True),
    ("instrument_transformers", "Instrument Transformers", True),
    ("cables", "Cables", True),
    ("busways", "Metal-Enclosed Busways", True),
    ("capacitors_reactors_resistors", "Capacitors, Reactors, and Resistors", True),
    ("motor_control", "Motor Control", True),
    ("rotating_machinery", "Rotating Machinery", True),
    ("dc_systems", "Direct-Current Systems", True),
    ("emergency_systems", "Emergency Systems", True),
    ("switches", "Switches", True),
    ("grounding_systems", "Grounding Systems", True),
    ("surge_protection", "Surge Protective Devices", True),
    ("regulating_apparatus", "Regulating Apparatus", True),
    ("circuit_switchers", "Circuit Switchers", True),
    ("outdoor_bus", "Outdoor Bus Structures", True),
    ("metering_devices", "Metering Devices", True),
    ("protective_relays", "Protective Relays", True),
    # future / inactive — present so NETA maps 1:1, not in the active build yet
    ("reclosers_sectionalizers", "Automatic Circuit Reclosers and Line Sectionalizers", False),
    ("network_protectors", "Network Protectors", False),
    ("ground_fault_protection", "Ground-Fault Protection Systems", False),
    ("adjustable_speed_drives", "Adjustable Speed Drive Systems", False),
    ("automation_communications", "Automation Systems and Communications", False),
    ("ev_charging", "Electric Vehicle Charging Systems", False),
    ("fiber_optic", "Fiber-Optic Cables", False),
    ("renewable_energy", "Renewable and Emerging Systems", False),
]

# parent_code -> [(leaf_code, leaf_name), ...]  (all leaves active)
LEAVES = {
    "circuit_breakers": [("cb_lv", "LV Circuit Breaker"), ("cb_mvhv", "MV/HV Circuit Breaker")],
    "transformers": [("xfmr_dry", "Dry-Type Transformer"), ("xfmr_liquid", "Liquid-Filled Transformer")],
    "switchgear": [
        ("swgr_lv_switchboard", "LV Switchboard"),
        ("swgr_mv_metalclad", "MV Metal-Clad Switchgear"),
        ("swgr_panelboard", "Panelboard"),
        ("swgr_padmount", "Pad-Mount Switchgear"),
        ("swgr_vfi", "VFI Switchgear"),
    ],
    "instrument_transformers": [
        ("it_ct", "Current Transformer"),
        ("it_vt", "Voltage Transformer"),
        ("it_cvt", "Capacitive Voltage Transformer"),
    ],
    "cables": [("cable_lv", "LV Cable"), ("cable_mv", "MV Cable")],
    "busways": [("busway", "Busway / Busduct")],
    "capacitors_reactors_resistors": [
        ("cap_bank", "Capacitor Bank"),
        ("reactor", "Reactor"),
        ("ngr", "Neutral-Grounding Resistor"),
        ("harmonic_filter", "Harmonic Filter Bank"),
    ],
    "motor_control": [("mcc_lv", "LV Motor Control Center"), ("motor_starter_mv", "MV Motor Starter")],
    "rotating_machinery": [("rm_synchronous", "Synchronous Machine"), ("rm_induction", "Induction Motor")],
    "dc_systems": [("battery", "Storage Battery"), ("battery_charger", "Battery Charger")],
    "emergency_systems": [
        ("ats", "Automatic Transfer Switch"),
        ("ups", "Uninterruptible Power Supply"),
        ("engine_generator", "Engine Generator"),
    ],
    "switches": [("switch_disconnect", "Disconnect / Load-Interrupter Switch")],
    "grounding_systems": [("grounding_system", "Grounding System")],
    "surge_protection": [("surge_arrester", "Surge Arrester")],
    "regulating_apparatus": [("voltage_regulator", "Voltage Regulator")],
    "circuit_switchers": [("circuit_switcher", "Circuit Switcher")],
    "outdoor_bus": [("outdoor_bus_structure", "Outdoor Bus Structure")],
    "metering_devices": [("meter", "Meter")],
    "protective_relays": [("protective_relay", "Protective Relay")],
}


def q(s: str) -> str:
    return s.replace("'", "''")


COLS = "(asset_class_id, class_code, name, neta_category, parent_class_id, is_active)"
ON_CONFLICT = (
    "ON CONFLICT (class_code) DO UPDATE\n"
    "  SET name = EXCLUDED.name, neta_category = EXCLUDED.neta_category,\n"
    "      parent_class_id = EXCLUDED.parent_class_id, is_active = EXCLUDED.is_active,\n"
    "      updated_at = now()"
)


def build_up() -> str:
    lines = [
        "-- 007_asset_class_shell.sql — records Chip 2-shell: asset_class family taxonomy (2-level).",
        "-- GENERATED by gen_shell_seed.py — do not hand-edit; change the taxonomy in the generator + regen.",
        "-- Parents = NETA categories (27: 19 active + 8 future). Leaves = practical apparatus classes (36).",
        "-- Idempotent: ON CONFLICT (class_code). Anchor: parent.neta_category in records.neta_procedures.category.",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "-- Parents (NETA categories) — inserted first to satisfy the self-FK from leaves.",
        f"INSERT INTO records.asset_classes {COLS} VALUES",
    ]
    rows = []
    for code, name, active in PARENTS:
        rows.append(
            f"  ('{cid(code)}', '{q(code)}', '{q(name)}', '{q(code)}', NULL, {str(active).lower()})"
        )
    lines.append(",\n".join(rows))
    lines.append(ON_CONFLICT + ";")
    lines.append("")
    lines.append("-- Leaves (practical apparatus classes) — neta_category resolved via the parent.")
    lines.append(f"INSERT INTO records.asset_classes {COLS} VALUES")
    rows = []
    for parent_code, kids in LEAVES.items():
        pid = cid(parent_code)
        for leaf_code, leaf_name in kids:
            rows.append(
                f"  ('{cid(leaf_code)}', '{q(leaf_code)}', '{q(leaf_name)}', NULL, '{pid}', true)"
            )
    lines.append(",\n".join(rows))
    lines.append(ON_CONFLICT + ";")
    lines.append("")
    lines.append("COMMIT;")
    lines.append("")
    return "\n".join(lines)


def build_down() -> str:
    leaf_codes = [lc for kids in LEAVES.values() for lc, _ in kids]
    parent_codes = [c for c, _, _ in PARENTS]
    leaf_in = ", ".join(f"'{q(c)}'" for c in leaf_codes)
    parent_in = ", ".join(f"'{q(c)}'" for c in parent_codes)
    return "\n".join([
        "-- 007_asset_class_shell_down.sql — reverse the Chip 2-shell seed.",
        "-- Leaves first (self-FK), then parents. Idempotent (no-op if rows absent).",
        "BEGIN;",
        f"DELETE FROM records.asset_classes WHERE class_code IN ({leaf_in});",
        f"DELETE FROM records.asset_classes WHERE class_code IN ({parent_in});",
        "COMMIT;",
        "",
    ])


def main():
    n_parents = len(PARENTS)
    n_leaves = sum(len(v) for v in LEAVES.values())
    assert n_parents == 27, n_parents
    assert n_leaves == 36, n_leaves
    # sanity: every leaf parent is a real parent code; all codes unique
    pcodes = {c for c, _, _ in PARENTS}
    assert set(LEAVES) <= pcodes, set(LEAVES) - pcodes
    all_codes = [c for c, _, _ in PARENTS] + [lc for kids in LEAVES.values() for lc, _ in kids]
    assert len(all_codes) == len(set(all_codes)) == 63, "duplicate or wrong-count class_code"
    with open(os.path.join(HERE, "007_asset_class_shell.sql"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_up())
    with open(os.path.join(HERE, "007_asset_class_shell_down.sql"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_down())
    print(f"wrote 007_asset_class_shell.sql + _down.sql  ({n_parents} parents + {n_leaves} leaves = {n_parents + n_leaves})")


if __name__ == "__main__":
    main()
