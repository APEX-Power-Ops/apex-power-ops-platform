#!/usr/bin/env python3
"""
Re-transfer tcc_tmt_thermal_adj after dropping UNIQUE(frame_id) constraint.
Transfers all 14,628 rows (multiple thermal adjustments per frame).

Usage:
    python migrations/003_retransfer_thermal_adj.py --dry-run   # Preview
    python migrations/003_retransfer_thermal_adj.py             # Execute
"""

import sys
import time
import argparse
import os

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


SOURCE_URL = os.getenv("SOURCE_DATABASE_URL") or os.getenv("DATABASE_URL_LOCAL")
if not SOURCE_URL:
    raise RuntimeError("Missing required environment variable: SOURCE_DATABASE_URL or DATABASE_URL_LOCAL")

TARGET_URL = require_env("DATABASE_URL")

# Column mapping: source -> target
COL_MAP = {
    "thermal_adj_id": "id",
    "frame_size_id": "frame_id",
    "thermal_adj_setting": "adjustment",
}

SOURCE_TABLE = "breaker_tmt_thermal_adj"
TARGET_TABLE = "tcc_tmt_thermal_adj"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=== tcc_tmt_thermal_adj Re-Transfer ===\n")

    # Connect to source
    print("Connecting to source (local PG)...")
    try:
        src_conn = psycopg2.connect(SOURCE_URL)
        src_conn.set_session(readonly=True)
        print("✓ Connected to source")
    except Exception as e:
        print(f"✗ Source connection failed: {e}")
        sys.exit(1)

    # Connect to target
    print("Connecting to target (Supabase)...")
    try:
        tgt_conn = psycopg2.connect(TARGET_URL)
        tgt_conn.set_session(autocommit=False)
        print("✓ Connected to target")
    except Exception as e:
        print(f"✗ Target connection failed: {e}")
        sys.exit(1)

    # Get source columns
    with src_conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {SOURCE_TABLE} LIMIT 0")
        src_cols = [desc[0] for desc in cur.description]

    # Build target column names
    tgt_cols = [COL_MAP.get(c, c) for c in src_cols]

    # Count source rows
    with src_conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {SOURCE_TABLE}")
        src_count = cur.fetchone()[0]

    # Count current target rows
    with tgt_conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {TARGET_TABLE}")
        tgt_count = cur.fetchone()[0]

    print(f"\nSource rows: {src_count:,}")
    print(f"Target rows (current): {tgt_count:,}")
    print(f"Columns: {' → '.join(f'{s}→{t}' for s, t in zip(src_cols, tgt_cols))}")

    if args.dry_run:
        print("\n[DRY RUN] No data will be transferred.")
        src_conn.close()
        tgt_conn.close()
        return

    if tgt_count > 0:
        print(f"\n⚠ Target table has {tgt_count} existing rows. Truncating...")
        with tgt_conn.cursor() as cur:
            cur.execute(f"TRUNCATE {TARGET_TABLE}")
        tgt_conn.commit()
        print("✓ Truncated")

    # Get valid frame_ids from target (to filter out orphaned references)
    print("\nFetching valid frame IDs from Supabase...")
    with tgt_conn.cursor() as cur:
        cur.execute("SELECT id FROM tcc_tmt_frames")
        valid_frame_ids = {row[0] for row in cur.fetchall()}
    print(f"  {len(valid_frame_ids):,} valid frame IDs")

    # Fetch all source data
    print(f"Fetching {src_count:,} rows from source...")
    with src_conn.cursor() as cur:
        cur.execute(f"SELECT {', '.join(src_cols)} FROM {SOURCE_TABLE}")
        rows = cur.fetchall()

    # Filter out rows referencing frames that weren't transferred (NULL size frames)
    frame_id_col_idx = src_cols.index("frame_size_id")
    filtered_rows = [r for r in rows if r[frame_id_col_idx] in valid_frame_ids]
    skipped = len(rows) - len(filtered_rows)
    if skipped > 0:
        print(f"  Skipping {skipped} rows with orphaned frame_id references")

    # Insert into target
    print(f"Inserting {len(filtered_rows):,} rows into {TARGET_TABLE}...")
    start = time.time()

    col_list = ", ".join(f'"{col}"' for col in tgt_cols)
    with tgt_conn.cursor() as cur:
        execute_values(
            cur,
            f"INSERT INTO {TARGET_TABLE} ({col_list}) VALUES %s",
            filtered_rows,
            page_size=5000,
        )
    tgt_conn.commit()
    elapsed = time.time() - start

    # Reset sequence
    with tgt_conn.cursor() as cur:
        cur.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{TARGET_TABLE}', 'id'),
                COALESCE((SELECT MAX(id) FROM {TARGET_TABLE}), 1)
            )
        """)
    tgt_conn.commit()

    # Verify
    with tgt_conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {TARGET_TABLE}")
        final_count = cur.fetchone()[0]

    print(f"\n✓ Transfer complete!")
    print(f"  Source rows: {src_count:,}")
    print(f"  Skipped (orphaned FK): {skipped}")
    print(f"  Rows transferred: {final_count:,}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Match: {'✓' if final_count == len(filtered_rows) else '✗'} (expected: {len(filtered_rows):,}, actual: {final_count:,})")

    src_conn.close()
    tgt_conn.close()


if __name__ == "__main__":
    main()
