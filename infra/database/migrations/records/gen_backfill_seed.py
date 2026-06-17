#!/usr/bin/env python3
"""Generate 009_backfill_seed.sql — leaf<->NETA-procedure links + the procedure xref graph.

Two seeds:
  1. asset_class_neta_procedure — the operator-approved leaf->procedure mapping (MAP).
     RESERVED procedures are excluded by construction; one is_primary per leaf.
  2. neta_procedure_xref — the procedure->procedure graph derived from the NETA JSON:
       * crossref      — crossref-only procedures' crossref_items (MCC -> constituents)
       * in_accordance — "in accordance with Section 7.x" refs scraped from item
                         descriptions (LTC 7.12.3 -> 7.2.2). Single-chapter refs
                         (e.g. "Section 9" thermography) are out of scope -- cross-chapter,
                         not procedure composition. Table 100.x refs already live on
                         neta_procedures.ats_table_refs, so they are not duplicated here.
     to_procedure_id resolves when the referenced section is an exact procedure; the
     category-level refs (7.1, 7.6) stay raw with NULL.

Deterministic UUID5 + ON CONFLICT = idempotent + FK-stable. leaf/procedure ids match
gen_shell_seed.py (NS ...a2) and gen_neta_seed.py (NS ...a1) exactly.
Run: uv run --no-project python gen_backfill_seed.py [path-to-json]
"""
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data\NETA-Master-Equipment-Table-Enhanced.json"
)
OUT = os.path.join(HERE, "009_backfill_seed.sql")
NS_NETA = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a1")   # matches gen_neta_seed.py
NS_CLASS = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a2")  # matches gen_shell_seed.py
NS_BF = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a3")     # this backfill's rows


def pid(section):
    return str(uuid.uuid5(NS_NETA, "proc:" + section))


def cid(code):
    return str(uuid.uuid5(NS_CLASS, code))


# leaf class_code -> [(section, is_primary), ...]   (RESERVED procedures intentionally absent)
MAP = {
    "cb_lv": [("7.6.1.2", True), ("7.6.1.1.1", False), ("7.6.1.1.2", False)],
    "cb_mvhv": [("7.6.1.3", True), ("7.6.2", False), ("7.6.3", False), ("7.6.4", False)],
    "xfmr_dry": [("7.2.1.1", True), ("7.2.1.2", False)],
    "xfmr_liquid": [("7.2.2", True)],
    "swgr_lv_switchboard": [("7.1.1", True)],
    "swgr_mv_metalclad": [("7.1.1", True)],
    "swgr_padmount": [("7.1.1", True)],
    "swgr_vfi": [("7.1.1", True)],
    "swgr_panelboard": [("7.1.2", True)],
    "it_ct": [("7.10.1", True)],
    "it_vt": [("7.10.2", True)],
    "it_cvt": [("7.10.3", True)],
    "cable_lv": [("7.3.2", True)],            # 7.3.1 is RESERVED
    "cable_mv": [("7.3.3", True)],
    "busway": [("7.4", True)],
    "cap_bank": [("7.20.1", True)],           # 7.20.2 RESERVED
    "reactor": [("7.20.3.1", True), ("7.20.3.2", False)],
    "ngr": [("7.20.4", True)],
    "harmonic_filter": [("7.20.1", True), ("7.20.3.1", False), ("7.20.3.2", False)],
    "mcc_lv": [("7.16.2.1", True)],
    "mcc_mv": [("7.16.2.2", True)],
    "motor_starter_lv": [("7.16.1.1", True)],
    "motor_starter_mv": [("7.16.1.2", True)],
    "rm_synchronous": [("7.15.2", True)],
    "rm_induction": [("7.15.1", True)],
    "rm_dc": [("7.15.3", True)],
    "battery": [("7.18.1.1", True), ("7.18.1.2", False), ("7.18.1.3", False)],
    "battery_charger": [("7.18.2", True)],    # 7.18.3 RESERVED
    "ats": [("7.22.3", True)],
    "ups": [("7.22.2", True)],
    "engine_generator": [("7.22.1", True)],
    "switch_disconnect": [("7.5.1.1", True), ("7.5.1.2", False), ("7.5.1.3", False),
                          ("7.5.2", False), ("7.5.3", False), ("7.5.4", False), ("7.5.5", False)],
    "grounding_system": [("7.13", True)],
    "surge_arrester": [("7.19.2", True), ("7.19.1", False)],
    "voltage_regulator": [("7.12.1.1", True), ("7.12.1.2", False)],   # 7.12.2 RESERVED
    "load_tap_changer": [("7.12.3", True)],
    "circuit_switcher": [("7.7", True)],
    "outdoor_bus_structure": [("7.21", True)],
    "meter": [("7.11.2", True), ("7.11.1", False)],
    "protective_relay": [("7.9.2", True), ("7.9.1", False)],
}

SEC_RE = re.compile(r"Section\s+(7\.\d+(?:\.\d+)*)")   # chapter-7 procedure references only


def s(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def desc_of(it):
    return it.get("description", "") if isinstance(it, dict) else str(it)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    d = json.load(open(src, encoding="utf-8"))
    eq = d["equipment"]
    sections = {e["section"] for e in eq}

    # fail fast on a typo'd mapping (would otherwise be an opaque FK error)
    for code, rows in MAP.items():
        for section, _ in rows:
            assert section in sections, f"MAP section {section} (leaf {code}) is not a real NETA procedure"

    out = [
        "-- =============================================================================",
        "-- Records NETA Backfill Seed (Chip 2-backfill) — GENERATED, do not edit by hand.",
        "-- leaf<->procedure links (operator-approved MAP) + the procedure xref graph.",
        "-- Regenerate: uv run --no-project python gen_backfill_seed.py",
        "-- Idempotent (ON CONFLICT); deterministic UUID5 ids.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "-- ---- leaf <-> procedure links ----",
    ]
    n_links = 0
    for code, rows in MAP.items():
        for section, primary in rows:
            rid = uuid.uuid5(NS_BF, f"acnp:{code}:{section}")
            out.append(
                "INSERT INTO records.asset_class_neta_procedure "
                "(asset_class_neta_procedure_id, asset_class_id, neta_procedure_id, is_primary) VALUES "
                f"('{rid}', '{cid(code)}', '{pid(section)}', {'true' if primary else 'false'}) "
                "ON CONFLICT (asset_class_id, neta_procedure_id) DO UPDATE SET is_primary=EXCLUDED.is_primary;"
            )
            n_links += 1

    # ---- procedure xref graph ----
    out.append("")
    out.append("-- ---- procedure xref graph (crossref composition + in_accordance method borrowing) ----")
    seen = set()
    xrows = []

    def add(from_sec, to_sec, kind):
        if to_sec == from_sec:
            return
        key = (from_sec, to_sec, kind)
        if key in seen:
            return
        seen.add(key)
        xrows.append((from_sec, to_sec, kind))

    for e in eq:
        from_sec = e["section"]
        for std_key in ("ats_data", "mts_data"):
            blk = e.get(std_key) or {}
            if blk.get("crossref_only"):
                for it in blk.get("crossref_items") or []:
                    for m in SEC_RE.finditer(desc_of(it)):
                        add(from_sec, m.group(1), "crossref")
            else:
                for jkey in ("visual_mechanical", "electrical_tests",
                             "test_values_visual", "test_values_electrical"):
                    sub = blk.get(jkey)
                    if not isinstance(sub, list):
                        continue
                    for it in sub:
                        for m in SEC_RE.finditer(desc_of(it)):
                            add(from_sec, m.group(1), "in_accordance")

    n_xref = 0
    for from_sec, to_sec, kind in xrows:
        rid = uuid.uuid5(NS_BF, f"xref:{from_sec}:{to_sec}:{kind}")
        to_pid = f"'{pid(to_sec)}'" if to_sec in sections else "NULL"
        out.append(
            "INSERT INTO records.neta_procedure_xref "
            "(neta_procedure_xref_id, from_procedure_id, to_section, to_procedure_id, ref_kind) VALUES "
            f"('{rid}', '{pid(from_sec)}', {s(to_sec)}, {to_pid}, '{kind}') "
            "ON CONFLICT (from_procedure_id, to_section, ref_kind) DO UPDATE SET to_procedure_id=EXCLUDED.to_procedure_id;"
        )
        n_xref += 1

    out.append("")
    out.append("COMMIT;")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"links={n_links}  xref={n_xref}  "
          f"(crossref={sum(1 for _, _, k in xrows if k == 'crossref')}, "
          f"in_accordance={sum(1 for _, _, k in xrows if k == 'in_accordance')})")
    assert n_links == 61, n_links


if __name__ == "__main__":
    main()
