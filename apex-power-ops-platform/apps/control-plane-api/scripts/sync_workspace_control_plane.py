from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SessionLocal
from services.control_plane.sync import (
    discover_task_packets,
    parse_immediate_top10,
    replace_lane_priorities,
    upsert_task_packets,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync governed workspace task packets and priorities into control-plane tables.")
    parser.add_argument(
        "--platform-root",
        "--study-root",
        required=True,
        dest="platform_root",
        help="Absolute path to the apex-power-ops-platform repository root.",
    )
    parser.add_argument(
        "--skip-packets",
        action="store_true",
        help="Skip packet JSON sync from Development/Agent-Inbox.",
    )
    parser.add_argument(
        "--skip-priorities",
        action="store_true",
        help="Skip priority sync from ETT-IMMEDIATE-TOP-10-CURRENT.md.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report counts without writing to the database.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    platform_root = Path(args.platform_root).resolve()
    inbox_path = platform_root / "Development" / "Agent-Inbox"
    top10_path = platform_root / "Development" / "Control-Plane" / "ETT-IMMEDIATE-TOP-10-CURRENT.md"

    packet_records = []
    priority_records = []

    if not args.skip_packets:
        packet_records = discover_task_packets(inbox_path)

    if not args.skip_priorities:
        priority_records = parse_immediate_top10(
            top10_path.read_text(encoding="utf-8"),
            source_surface="Development/Control-Plane/ETT-IMMEDIATE-TOP-10-CURRENT.md",
        )

    print("CONTROL_PLANE_SYNC")
    print(f"PLATFORM_ROOT {platform_root}")
    print(f"PACKET_COUNT {len(packet_records)}")
    print(f"PRIORITY_COUNT {len(priority_records)}")

    if args.dry_run:
        print("RESULT DRY_RUN")
        return 0

    db = SessionLocal()
    try:
        synced_packets = 0
        synced_priorities = 0

        if packet_records:
            synced_packets = upsert_task_packets(db, packet_records)
        if priority_records:
            synced_priorities = replace_lane_priorities(
                db,
                priority_records,
                source_surface="Development/Control-Plane/ETT-IMMEDIATE-TOP-10-CURRENT.md",
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"SYNCED_PACKETS {synced_packets}")
    print(f"SYNCED_PRIORITIES {synced_priorities}")
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())