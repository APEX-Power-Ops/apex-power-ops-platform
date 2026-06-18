#!/usr/bin/env python3
"""Generate 038_neta_tables_standard.sql — standard-key records.neta_tables.

Chip A of the MTS-accommodation lane. The Chip-2a seed (006) loaded neta_tables
*deduped globally by table_number* (uq_neta_tables_number), so ATS Table 100.1 and
MTS Table 100.1 collapsed to one row — but their VALUES differ (new-equipment vs
service-aged limits). This migration adds a `standard` column, swaps the unique key
to (standard, table_number), and reseeds BOTH standards verbatim from the two
authoritative per-standard extracts:

  NETA-ATS-2025-tables-extracted.json   (44 tables / 319 data rows)
  NETA-MTS-2023-tables-extracted.json   (44 tables / 362 data rows)

Deterministic UUID5 ids (table:<std>:<num>) + TRUNCATE-then-INSERT => idempotent.
Run:  uv run --no-project python gen_038_neta_tables_standard.py
"""
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data"
)
SRC = [
    ("ats", os.path.join(DATA, "NETA-ATS-2025-tables-extracted.json")),
    ("mts", os.path.join(DATA, "NETA-MTS-2023-tables-extracted.json")),
]
OUT = os.path.join(HERE, "038_neta_tables_standard.sql")
OUT_DOWN = os.path.join(HERE, "038_neta_tables_standard_down.sql")
NS = uuid.UUID("7e7a9c2a-3b1d-4f6e-9a2c-0000000000a1")  # same records-neta namespace as 006


def tid(std, num):
    return uuid.uuid5(NS, f"table:{std}:{num}")


def s(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def j(o):
    if o is None:
        return "NULL"
    return "'" + json.dumps(o, ensure_ascii=False).replace("'", "''") + "'::jsonb"


def parent_of(num):
    parts = num.split(".")
    return ".".join(parts[:-1]) if len(parts) > 2 else None


def main():
    out = [
        "-- =============================================================================",
        "-- Records NETA Reference — Chip A: standard-key neta_tables. GENERATED, do not edit.",
        "-- Source: NETA-ATS-2025-tables-extracted.json + NETA-MTS-2023-tables-extracted.json",
        "-- Regenerate: uv run --no-project python gen_038_neta_tables_standard.py",
        "-- Adds neta_tables.standard, swaps unique to (standard, table_number), reseeds both",
        "-- standards verbatim. Idempotent (guarded DDL + TRUNCATE + UUID5 ids).",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "",
        "-- 1. schema: add the standard dimension, drop the global-dedupe unique key",
        "ALTER TABLE records.neta_tables ADD COLUMN IF NOT EXISTS standard records.neta_standard_enum;",
        "ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_number;",
        "ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_std_number;",
        "",
        "-- 2. reseed both standards verbatim (no FK references neta_tables -> TRUNCATE safe)",
        "TRUNCATE records.neta_tables;",
    ]

    counts = {}
    rows_total = {}
    for std, path in SRC:
        d = json.load(open(path, encoding="utf-8"))
        tables = d["tables"]
        counts[std] = len(tables)
        rows_total[std] = 0
        out.append("")
        out.append(f"-- ---- {d.get('standard', std)} acceptance tables ----")
        for num in sorted(tables):
            t = tables[num]
            data = t.get("data")
            if data is None:
                data = t.get("rows") or []
            rows_total[std] += len(data)
            out.append(
                "INSERT INTO records.neta_tables (neta_table_id, standard, table_number, title, "
                "status, parent_table_number, headers, rows) VALUES "
                f"('{tid(std, num)}', '{std}', {s(num)}, {s(t.get('title'))}, "
                f"{s(t.get('status'))}, {s(parent_of(num))}, {j(t.get('headers') or [])}, {j(data)});"
            )

    out += [
        "",
        "-- 3. lock the new shape: standard is mandatory, unique is now per (standard, table_number)",
        "ALTER TABLE records.neta_tables ALTER COLUMN standard SET NOT NULL;",
        "ALTER TABLE records.neta_tables ADD CONSTRAINT uq_neta_tables_std_number "
        "UNIQUE (standard, table_number);",
        "",
        "COMMIT;",
    ]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")

    down = [
        "-- =============================================================================",
        "-- DOWN for 038_neta_tables_standard.sql — revert to global-dedupe neta_tables.",
        "-- Drops the standard dimension; keeps the ATS rows under uq(table_number).",
        "-- Tolerant of pre-038 state (no standard column) so the test fixture can run it first.",
        "-- =============================================================================",
        "BEGIN;",
        "SET client_encoding TO 'UTF8';",
        "DO $$",
        "BEGIN",
        "  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='records'",
        "             AND table_name='neta_tables' AND column_name='standard') THEN",
        "    ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_std_number;",
        "    DELETE FROM records.neta_tables WHERE standard = 'mts';",
        "    ALTER TABLE records.neta_tables DROP COLUMN standard;",
        "  END IF;",
        "END $$;",
        "ALTER TABLE records.neta_tables DROP CONSTRAINT IF EXISTS uq_neta_tables_number;",
        "ALTER TABLE records.neta_tables ADD CONSTRAINT uq_neta_tables_number UNIQUE (table_number);",
        "COMMIT;",
    ]
    with open(OUT_DOWN, "w", encoding="utf-8") as fh:
        fh.write("\n".join(down) + "\n")

    print(f"wrote {OUT}")
    print(f"wrote {OUT_DOWN}")
    print(f"ats tables={counts.get('ats')} rows={rows_total.get('ats')} | "
          f"mts tables={counts.get('mts')} rows={rows_total.get('mts')}")


if __name__ == "__main__":
    main()
