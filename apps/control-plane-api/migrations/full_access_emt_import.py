r"""
Direct EMT family import from Access CSV exports into Supabase.

This script loads the EMT family from the authoritative Access CSV export path:
    C:\Users\jjswe\Box\TCC_Master\Access DB\tables

It is intentionally separate from the lowercase PostgreSQL-to-Supabase transfer
scripts because the currently available local PostgreSQL source snapshot does not
contain the EMT family, while the Access CSV export does.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    print("ERROR: Missing required environment variable: DATABASE_URL")
    sys.exit(1)

CSV_DIR = Path(r"C:\Users\jjswe\Box\TCC_Master\Access DB\tables")
REPORT_PATH = Path(__file__).with_name("emt_import_report.json")

# Default policy is quarantine. Alias application must be explicitly enabled.
STYLE_ID_ALIAS_MAP = {
    1: 73,
}

EMT_FILES = {
    "EMT.csv": [
        ("ID", "id", int),
        ("Mfr_ID", "manufacturer_id", int),
        ("Type", "type_name", str),
        ("Style", "style_name", str),
        ("TCCNumber", "tcc_number", str),
        ("Note", "notes", str),
        ("TripChar", "trip_char", int),
        ("TripPlug", "trip_plug", int),
    ],
    "EMT_Frames.csv": [
        ("ID", "id", int),
        ("StyleID", "emt_id", int),
        ("FrameSize", "frame_size", float),
        ("FrameDesc", "frame_desc", str),
        ("Ordinal", "ordinal", int),
    ],
    "EMT_FrameAmps.csv": [
        ("FrameID", "frame_id", int),
        ("TripAmp", "rating", float),
    ],
    "EMT_Sections.csv": [
        ("ID", "id", int),
        ("Name", "name", str),
        ("FrameID", "frame_id", int),
        ("SecChar", "sec_char", int),
        ("CurveType", "curve_type", int),
        ("PickupCalc", "pickup_calc", int),
        ("PickupTolerLow", "pickup_tol_lo", float),
        ("PickupTolerHigh", "pickup_tol_hi", float),
        ("PickupSetting", "pickup_setting", int),
        ("StepSize", "step_size", float),
        ("CurrentCalc", "current_calc", int),
        ("DelayClrCurve", "delay_clr_curve", int),
        ("DelayOpenTime", "delay_open_time", float),
        ("DelayClearTime", "delay_clear_time", float),
        ("OpenCurveRadius", "open_curve_radius", float),
        ("ClearCurveRadius", "clear_curve_radius", float),
    ],
    "EMT_BandNames.csv": [
        ("ID", "id", int),
        ("SecID", "section_id", int),
        ("BandName", "band_name", str),
        ("Ordinal", "ordinal", int),
        ("CurrentAt", "current_at", float),
    ],
    "EMT_Pickups.csv": [
        ("SecID", "section_id", int),
        ("Setting", "setting", float),
        ("Description", "description", str),
    ],
    "EMT_Curves.csv": [
        ("ParentID", "band_id", int),
        ("Class", "class", int),
        ("Time", "time_sec", float),
        ("Amps", "current_amp", float),
    ],
}

CSV_BASENAMES = tuple(EMT_FILES.keys())

IMPORT_PLAN = [
    ("EMT.csv", "tcc_emt"),
    ("EMT_Frames.csv", "tcc_emt_frames"),
    ("EMT_FrameAmps.csv", "tcc_emt_frame_amps"),
    ("EMT_Sections.csv", "tcc_emt_sections"),
    ("EMT_BandNames.csv", "tcc_emt_band_names"),
    ("EMT_Pickups.csv", "tcc_emt_pickups"),
    ("EMT_Curves.csv", "tcc_emt_curves"),
]

TRUNCATE_ORDER = [
    "tcc_emt_curves",
    "tcc_emt_band_names",
    "tcc_emt_pickups",
    "tcc_emt_sections",
    "tcc_emt_frame_amps",
    "tcc_emt_frames",
    "tcc_emt",
]


def clean_value(raw: str | None, caster):
    if raw is None:
        return None
    value = raw.strip()
    if value == "":
        return None
    if caster is str:
        return value
    try:
        if caster is int:
            return int(float(value))
        return caster(value)
    except (TypeError, ValueError):
        return None


def read_records(csv_name: str):
    path = CSV_DIR / csv_name
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    last_error = None

    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open("r", newline="", encoding=encoding) as handle:
                reader = csv.DictReader(handle)
                return [record for record in reader]
        except UnicodeDecodeError as exc:
            last_error = exc

    raise last_error


def map_rows(csv_name: str, records):
    mappings = EMT_FILES[csv_name]
    rows = []
    for record in records:
        first_value = record.get(mappings[0][0], "")
        if not first_value or not first_value.strip():
            continue
        rows.append(tuple(clean_value(record.get(src), caster) for src, _, caster in mappings))
    return rows


def truncate_tables(cur):
    for table in TRUNCATE_ORDER:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")


def import_table(cur, csv_name: str, target_table: str, rows):
    mappings = EMT_FILES[csv_name]
    columns = [target for _, target, _ in mappings]
    insert_sql = f"INSERT INTO {target_table} ({', '.join(columns)}) VALUES %s"
    if rows:
        execute_values(cur, insert_sql, rows, page_size=1000)
    return len(rows)


def verify_counts(cur, imported_counts):
    mismatches = []
    for _, target_table in IMPORT_PLAN:
        cur.execute(f"SELECT COUNT(*) FROM {target_table}")
        target_count = cur.fetchone()[0]
        source_count = imported_counts[target_table]
        if source_count != target_count:
            mismatches.append((target_table, source_count, target_count))
    return mismatches


def load_source_records():
    return {csv_name: read_records(csv_name) for csv_name in CSV_BASENAMES}


def alias_mode_enabled() -> bool:
    return os.getenv("EMT_ENABLE_STYLE_ALIASES", "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_style_alias(style_id_raw: str | None) -> int | None:
    style_id = clean_value(style_id_raw, int)
    if style_id is None:
        return None
    if alias_mode_enabled():
        return STYLE_ID_ALIAS_MAP.get(style_id, style_id)
    return style_id


def _strip_raw(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _normalized_frame_signature(frame_id: str, source_records):
    sections = [
        record for record in source_records["EMT_Sections.csv"]
        if _strip_raw(record.get("FrameID")) == frame_id
    ]
    sections.sort(
        key=lambda record: (
            _strip_raw(record.get("Name")),
            _strip_raw(record.get("SecChar")),
            _strip_raw(record.get("CurveType")),
            _strip_raw(record.get("PickupSetting")),
            _strip_raw(record.get("CurrentCalc")),
        )
    )

    section_aliases = {
        _strip_raw(record.get("ID")): f"section_{index}"
        for index, record in enumerate(sections, start=1)
        if _strip_raw(record.get("ID"))
    }

    normalized_sections = [
        {
            "name": _strip_raw(record.get("Name")),
            "sec_char": _strip_raw(record.get("SecChar")),
            "curve_type": _strip_raw(record.get("CurveType")),
            "pickup_calc": _strip_raw(record.get("PickupCalc")),
            "pickup_tol_lo": _strip_raw(record.get("PickupTolerLow")),
            "pickup_tol_hi": _strip_raw(record.get("PickupTolerHigh")),
            "pickup_setting": _strip_raw(record.get("PickupSetting")),
            "step_size": _strip_raw(record.get("StepSize")),
            "current_calc": _strip_raw(record.get("CurrentCalc")),
            "delay_clr_curve": _strip_raw(record.get("DelayClrCurve")),
            "delay_open_time": _strip_raw(record.get("DelayOpenTime")),
            "delay_clear_time": _strip_raw(record.get("DelayClearTime")),
            "open_curve_radius": _strip_raw(record.get("OpenCurveRadius")),
            "clear_curve_radius": _strip_raw(record.get("ClearCurveRadius")),
        }
        for record in sections
    ]

    pickups = [
        record for record in source_records["EMT_Pickups.csv"]
        if _strip_raw(record.get("SecID")) in section_aliases
    ]
    normalized_pickups = sorted(
        [
            {
                "section": section_aliases[_strip_raw(record.get("SecID"))],
                "setting": _strip_raw(record.get("Setting")),
                "description": _strip_raw(record.get("Description")),
            }
            for record in pickups
        ],
        key=lambda record: (record["section"], record["setting"], record["description"]),
    )

    bands = [
        record for record in source_records["EMT_BandNames.csv"]
        if _strip_raw(record.get("SecID")) in section_aliases
    ]
    bands.sort(
        key=lambda record: (
            section_aliases[_strip_raw(record.get("SecID"))],
            _strip_raw(record.get("Ordinal")),
            _strip_raw(record.get("BandName")),
            _strip_raw(record.get("CurrentAt")),
        )
    )
    band_aliases = {
        _strip_raw(record.get("ID")): f"band_{index}"
        for index, record in enumerate(bands, start=1)
        if _strip_raw(record.get("ID"))
    }
    normalized_bands = [
        {
            "section": section_aliases[_strip_raw(record.get("SecID"))],
            "band_name": _strip_raw(record.get("BandName")),
            "ordinal": _strip_raw(record.get("Ordinal")),
            "current_at": _strip_raw(record.get("CurrentAt")),
        }
        for record in bands
    ]

    curves = [
        record for record in source_records["EMT_Curves.csv"]
        if _strip_raw(record.get("ParentID")) in band_aliases
    ]
    normalized_curves = sorted(
        [
            {
                "band": band_aliases[_strip_raw(record.get("ParentID"))],
                "class": _strip_raw(record.get("Class")),
                "time": _strip_raw(record.get("Time")),
                "amps": _strip_raw(record.get("Amps")),
            }
            for record in curves
        ],
        key=lambda record: (record["band"], record["class"], record["time"], record["amps"]),
    )

    return {
        "sections": normalized_sections,
        "pickups": normalized_pickups,
        "bands": normalized_bands,
        "curves": normalized_curves,
    }


def _count_frame_descendants(frame_ids: set[str], source_records):
    sections = [
        record for record in source_records["EMT_Sections.csv"]
        if _strip_raw(record.get("FrameID")) in frame_ids
    ]
    section_ids = {
        _strip_raw(record.get("ID"))
        for record in sections
        if _strip_raw(record.get("ID"))
    }
    bands = [
        record for record in source_records["EMT_BandNames.csv"]
        if _strip_raw(record.get("SecID")) in section_ids
    ]
    band_ids = {
        _strip_raw(record.get("ID"))
        for record in bands
        if _strip_raw(record.get("ID"))
    }

    return {
        "frames": len(frame_ids),
        "frame_amps": len([
            record for record in source_records["EMT_FrameAmps.csv"]
            if _strip_raw(record.get("FrameID")) in frame_ids
        ]),
        "sections": len(sections),
        "bands": len(bands),
        "pickups": len([
            record for record in source_records["EMT_Pickups.csv"]
            if _strip_raw(record.get("SecID")) in section_ids
        ]),
        "curves": len([
            record for record in source_records["EMT_Curves.csv"]
            if _strip_raw(record.get("ParentID")) in band_ids
        ]),
    }


def _detect_orphan_duplicate_candidates(orphan_frames, valid_frames, source_records):
    valid_signatures: dict[str, list[dict[str, object]]] = {}
    for record in valid_frames:
        frame_id = _strip_raw(record.get("ID"))
        if not frame_id:
            continue
        signature = json.dumps(_normalized_frame_signature(frame_id, source_records), sort_keys=True)
        valid_signatures.setdefault(signature, []).append(record)

    candidates = []
    for record in orphan_frames:
        frame_id = _strip_raw(record.get("ID"))
        if not frame_id:
            continue
        signature = json.dumps(_normalized_frame_signature(frame_id, source_records), sort_keys=True)
        matches = valid_signatures.get(signature, [])
        candidate_style_ids = sorted(
            {
                int(float(style_id))
                for style_id in (_strip_raw(match.get("StyleID")) for match in matches)
                if style_id
            }
        )
        candidates.append(
            {
                "frame_id": int(float(frame_id)),
                "missing_style_id": clean_value(record.get("StyleID"), int),
                "frame_desc": _strip_raw(record.get("FrameDesc")),
                "frame_size": clean_value(record.get("FrameSize"), float),
                "candidate_style_ids": candidate_style_ids,
                "candidate_frame_ids": [
                    int(float(match["ID"]))
                    for match in matches
                    if _strip_raw(match.get("ID"))
                ],
                "exact_duplicate_match": bool(matches),
            }
        )

    return candidates


def write_import_report(imported_counts, anomalies, elapsed_seconds: float):
    report = {
        "csv_source": str(CSV_DIR),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "alias_mode_enabled": alias_mode_enabled(),
        "style_id_alias_map": STYLE_ID_ALIAS_MAP,
        "imported_counts": imported_counts,
        "missing_style_ids": anomalies.get("missing_style_ids", []),
        "orphan_counts": anomalies.get("orphan_counts", {}),
        "orphan_duplicate_candidates": anomalies.get("orphan_duplicate_candidates", []),
        "applied_style_aliases": anomalies.get("applied_style_aliases", {}),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return REPORT_PATH


def filter_valid_emt_graph(source_records):
    emt_records = source_records["EMT.csv"]
    valid_emt_ids = {
        int(float(record["ID"]))
        for record in emt_records
        if record.get("ID", "").strip()
    }

    frame_records = source_records["EMT_Frames.csv"]
    valid_frames = []
    orphan_frames = []
    applied_style_aliases: dict[int, int] = {}
    aliased_frames = []
    for record in frame_records:
        style_id = record.get("StyleID", "").strip()
        if not style_id:
            orphan_frames.append(record)
            continue
        resolved_style_id = resolve_style_alias(style_id)
        if resolved_style_id in valid_emt_ids:
            if resolved_style_id != int(float(style_id)):
                record = dict(record)
                record["StyleID"] = str(resolved_style_id)
                applied_style_aliases[int(float(style_id))] = resolved_style_id
                aliased_frames.append(record)
            valid_frames.append(record)
        else:
            orphan_frames.append(record)

    canonical_frames_by_signature: dict[tuple[int, str], list[dict[str, object]]] = {}
    for record in valid_frames:
        frame_id = _strip_raw(record.get("ID"))
        if not frame_id:
            continue
        style_id = clean_value(record.get("StyleID"), int)
        if style_id is None:
            continue
        signature = json.dumps(_normalized_frame_signature(frame_id, source_records), sort_keys=True)
        canonical_frames_by_signature.setdefault((style_id, signature), []).append(record)

    collapsed_aliased_duplicate_frames = []
    retained_frames = []
    for record in valid_frames:
        if record not in aliased_frames:
            retained_frames.append(record)
            continue

        frame_id = _strip_raw(record.get("ID"))
        style_id = clean_value(record.get("StyleID"), int)
        signature = json.dumps(_normalized_frame_signature(frame_id, source_records), sort_keys=True)
        matching_canonical_frames = [
            candidate for candidate in canonical_frames_by_signature.get((style_id, signature), [])
            if candidate is not record and candidate not in aliased_frames
        ]
        if matching_canonical_frames:
            canonical = matching_canonical_frames[0]
            collapsed_aliased_duplicate_frames.append(
                {
                    "frame_id": clean_value(record.get("ID"), int),
                    "aliased_style_id": style_id,
                    "canonical_frame_id": clean_value(canonical.get("ID"), int),
                    "frame_desc": _strip_raw(record.get("FrameDesc")),
                }
            )
            continue

        retained_frames.append(record)

    valid_frames = retained_frames

    valid_frame_ids = {
        record["ID"]
        for record in valid_frames
        if record.get("ID", "").strip()
    }
    valid_sections = [
        record for record in source_records["EMT_Sections.csv"]
        if record.get("FrameID", "").strip() in valid_frame_ids
    ]
    valid_section_ids = {
        record["ID"]
        for record in valid_sections
        if record.get("ID", "").strip()
    }
    valid_bands = [
        record for record in source_records["EMT_BandNames.csv"]
        if record.get("SecID", "").strip() in valid_section_ids
    ]
    valid_band_ids = {
        record["ID"]
        for record in valid_bands
        if record.get("ID", "").strip()
    }

    filtered = {
        "EMT.csv": emt_records,
        "EMT_Frames.csv": valid_frames,
        "EMT_FrameAmps.csv": [
            record for record in source_records["EMT_FrameAmps.csv"]
            if record.get("FrameID", "").strip() in valid_frame_ids
        ],
        "EMT_Sections.csv": valid_sections,
        "EMT_BandNames.csv": valid_bands,
        "EMT_Pickups.csv": [
            record for record in source_records["EMT_Pickups.csv"]
            if record.get("SecID", "").strip() in valid_section_ids
        ],
        "EMT_Curves.csv": [
            record for record in source_records["EMT_Curves.csv"]
            if record.get("ParentID", "").strip() in valid_band_ids
        ],
    }

    orphan_frame_ids = {
        record["ID"]
        for record in orphan_frames
        if record.get("ID", "").strip()
    }
    orphan_sections = [
        record for record in source_records["EMT_Sections.csv"]
        if record.get("FrameID", "").strip() in orphan_frame_ids
    ]
    orphan_section_ids = {
        record["ID"]
        for record in orphan_sections
        if record.get("ID", "").strip()
    }
    orphan_bands = [
        record for record in source_records["EMT_BandNames.csv"]
        if record.get("SecID", "").strip() in orphan_section_ids
    ]
    orphan_band_ids = {
        record["ID"]
        for record in orphan_bands
        if record.get("ID", "").strip()
    }

    anomalies = {
        "missing_style_ids": sorted(
            {
                int(float(record["StyleID"]))
                for record in orphan_frames
                if record.get("StyleID", "").strip()
            }
        ),
        "orphan_counts": {
            "frames": len(orphan_frames),
            "frame_amps": len([
                record for record in source_records["EMT_FrameAmps.csv"]
                if record.get("FrameID", "").strip() in orphan_frame_ids
            ]),
            "sections": len(orphan_sections),
            "bands": len(orphan_bands),
            "pickups": len([
                record for record in source_records["EMT_Pickups.csv"]
                if record.get("SecID", "").strip() in orphan_section_ids
            ]),
            "curves": len([
                record for record in source_records["EMT_Curves.csv"]
                if record.get("ParentID", "").strip() in orphan_band_ids
            ]),
        },
        "orphan_frames": orphan_frames,
        "orphan_duplicate_candidates": _detect_orphan_duplicate_candidates(
            orphan_frames,
            valid_frames,
            source_records,
        ),
        "applied_style_aliases": applied_style_aliases,
        "collapsed_alias_counts": _count_frame_descendants(
            {
                str(item["frame_id"])
                for item in collapsed_aliased_duplicate_frames
                if item.get("frame_id") is not None
            },
            source_records,
        ),
        "collapsed_aliased_duplicate_frames": collapsed_aliased_duplicate_frames,
    }

    return filtered, anomalies


def main():
    print("EMT Access CSV -> Supabase Import")
    print(f"CSV source: {CSV_DIR}")
    print(f"Tables to import: {len(IMPORT_PLAN)}")

    start = time.time()

    conn = psycopg2.connect(DB_URL, connect_timeout=10)
    conn.autocommit = False

    imported_counts = {}
    try:
        source_records = load_source_records()
        filtered_records, anomalies = filter_valid_emt_graph(source_records)

        with conn.cursor() as cur:
            print("Step 1: truncating EMT target tables...")
            truncate_tables(cur)
            conn.commit()

            print("Step 2: importing EMT CSVs...")
            for csv_name, target_table in IMPORT_PLAN:
                print(f"  importing {csv_name} -> {target_table} ... ", end="", flush=True)
                row_count = import_table(cur, csv_name, target_table, map_rows(csv_name, filtered_records[csv_name]))
                imported_counts[target_table] = row_count
                conn.commit()
                print(f"{row_count:,} rows")

            print("Step 3: verifying target counts...")
            mismatches = verify_counts(cur, imported_counts)
            if mismatches:
                print("Verification failed:")
                for table_name, source_count, target_count in mismatches:
                    print(f"  {table_name}: source={source_count:,}, target={target_count:,}")
                conn.rollback()
                return 1

        elapsed = time.time() - start
        print("Import complete.")
        for table_name, row_count in imported_counts.items():
            print(f"  {table_name}: {row_count:,} rows")
        if anomalies["missing_style_ids"]:
            print("Quarantined source anomaly:")
            print(f"  missing EMT parent style IDs: {anomalies['missing_style_ids']}")
            for key, value in anomalies["orphan_counts"].items():
                print(f"  skipped {key}: {value:,}")
            for candidate in anomalies.get("orphan_duplicate_candidates", []):
                if candidate["exact_duplicate_match"]:
                    print(
                        "  exact duplicate subtree candidate: "
                        f"frame {candidate['frame_id']} -> styles {candidate['candidate_style_ids']} "
                        f"via frames {candidate['candidate_frame_ids']}"
                    )
        if anomalies.get("applied_style_aliases"):
            print("Applied style aliases:")
            for source_style_id, target_style_id in sorted(anomalies["applied_style_aliases"].items()):
                print(f"  StyleID {source_style_id} -> {target_style_id}")
        if anomalies.get("collapsed_aliased_duplicate_frames"):
            print("Collapsed aliased duplicate frames:")
            for item in anomalies["collapsed_aliased_duplicate_frames"]:
                print(
                    "  frame "
                    f"{item['frame_id']} merged into canonical frame {item['canonical_frame_id']} "
                    f"under style {item['aliased_style_id']}"
                )
            for key, value in anomalies.get("collapsed_alias_counts", {}).items():
                print(f"  collapsed {key}: {value:,}")
        report_path = write_import_report(imported_counts, anomalies, elapsed)
        print(f"Report: {report_path}")
        print(f"Elapsed: {elapsed:.1f}s")
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())