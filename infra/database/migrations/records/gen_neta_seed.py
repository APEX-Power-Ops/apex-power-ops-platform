#!/usr/bin/env python3
"""Generate 006_neta_reference_seed.sql from the NETA Master Equipment Table.

The committed seed SQL is the authoritative artifact; this generator documents its
provenance and makes regeneration reproducible. Deterministic UUID5 ids + ON CONFLICT
make the seed idempotent and FK-stable across re-runs.

Source: ANSI/NETA ATS-2025 + MTS-2023 master equipment table (operator-held study
material). Run:  uv run --no-project python gen_neta_seed.py [path-to-json]
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
OUT = os.path.join(HERE, "006_neta_reference_seed.sql")
NS = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a1")  # fixed records-neta namespace

# JSON sub-list -> records.neta_test_category_enum
CAT_MAP = {
    "visual_mechanical": "visual_mechanical",
    "electrical_tests": "electrical",
    "test_values_visual": "test_value_visual",
    "test_values_electrical": "test_value_electrical",
}


def pid(section):
    return uuid.uuid5(NS, "proc:" + section)


def tid(num):
    return uuid.uuid5(NS, "table:" + num)


def iid(section, std, cat, num):
    return uuid.uuid5(NS, f"item:{section}:{std}:{cat}:{num}")


def s(v):
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def j(o):
    if o is None:
        return "NULL"
    return "'" + json.dumps(o, ensure_ascii=False).replace("'", "''") + "'::jsonb"


def b(v):
    return "true" if v else "false"


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON
    d = json.load(open(src, encoding="utf-8"))
    eq = d["equipment"]
    meta = d.get("metadata", {})

    out = [
        "-- =============================================================================",
        "-- Records NETA Reference Seed (Chip 2a) — GENERATED, do not edit by hand.",
        f"-- Source: {meta.get('standard_primary','ANSI/NETA ATS-2025')} + "
        f"{meta.get('standard_secondary','MTS-2023')} master equipment table.",
        "-- Regenerate: uv run --no-project python gen_neta_seed.py",
        "-- Idempotent (ON CONFLICT); deterministic UUID5 ids.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "-- ---- procedures (one per NETA section) ----",
    ]

    for e in eq:
        sec = e["section"]
        ats = e.get("ats_data") or {}
        mts = e.get("mts_data") or {}
        out.append(
            "INSERT INTO records.neta_procedures (neta_procedure_id, section, name, category, "
            "category_name, status, has_ats, has_mts, ats_table_refs, mts_table_refs, notes, source) VALUES "
            f"('{pid(sec)}', {s(sec)}, {s(e.get('name'))}, {s(e.get('category'))}, "
            f"{s(e.get('category_name'))}, {s(e.get('status'))}, {b(e.get('has_ats'))}, {b(e.get('has_mts'))}, "
            f"{j(ats.get('table_refs') or [])}, {j(mts.get('table_refs') or [])}, {j(e.get('notes'))}, 'migration') "
            "ON CONFLICT (section) DO UPDATE SET name=EXCLUDED.name, category=EXCLUDED.category, "
            "category_name=EXCLUDED.category_name, status=EXCLUDED.status, has_ats=EXCLUDED.has_ats, "
            "has_mts=EXCLUDED.has_mts, ats_table_refs=EXCLUDED.ats_table_refs, "
            "mts_table_refs=EXCLUDED.mts_table_refs, notes=EXCLUDED.notes, updated_at=now();"
        )

    out.append("")
    out.append("-- ---- test items (per procedure x standard x category) ----")
    n_items = 0
    for e in eq:
        sec = e["section"]
        for std_key, std in (("ats_data", "ats"), ("mts_data", "mts")):
            block = e.get(std_key) or {}
            for jkey, cat in CAT_MAP.items():
                for i, it in enumerate(block.get(jkey) or []):
                    if isinstance(it, dict):
                        num, desc, opt = str(it.get("number", i + 1)), it.get("description"), it.get("optional")
                    else:
                        num, desc, opt = str(i + 1), str(it), False
                    out.append(
                        "INSERT INTO records.neta_test_items (neta_test_item_id, neta_procedure_id, "
                        "standard, category, item_number, description, is_optional, sort_order) VALUES "
                        f"('{iid(sec, std, cat, num)}', '{pid(sec)}', '{std}', '{cat}', {s(num)}, "
                        f"{s(desc)}, {b(opt)}, {i}) "
                        "ON CONFLICT (neta_procedure_id, standard, category, item_number) DO UPDATE SET "
                        "description=EXCLUDED.description, is_optional=EXCLUDED.is_optional, "
                        "sort_order=EXCLUDED.sort_order;"
                    )
                    n_items += 1

    out.append("")
    out.append("-- ---- acceptance tables (deduped globally by table_number) ----")
    seen = {}
    for e in eq:
        for tn, t in (e.get("tables") or {}).items():
            if tn not in seen:
                seen[tn] = t if isinstance(t, dict) else {"rows": t}
    for tn in sorted(seen):
        t = seen[tn]
        parts = tn.split(".")
        parent = ".".join(parts[:-1]) if len(parts) > 2 else None
        out.append(
            "INSERT INTO records.neta_tables (neta_table_id, table_number, title, status, "
            "parent_table_number, headers, rows) VALUES "
            f"('{tid(tn)}', {s(tn)}, {s(t.get('title'))}, {s(t.get('status'))}, {s(parent)}, "
            f"{j(t.get('headers') or [])}, {j(t.get('rows') or [])}) "
            "ON CONFLICT (table_number) DO UPDATE SET title=EXCLUDED.title, status=EXCLUDED.status, "
            "parent_table_number=EXCLUDED.parent_table_number, headers=EXCLUDED.headers, rows=EXCLUDED.rows;"
        )

    out.append("")
    out.append("COMMIT;")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print(f"procedures={len(eq)}  test_items={n_items}  tables={len(seen)}")


if __name__ == "__main__":
    main()
