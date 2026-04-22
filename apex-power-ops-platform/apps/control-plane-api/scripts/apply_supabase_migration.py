from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply a tracked SQL migration from supabase/migrations to the configured database."
    )
    parser.add_argument(
        "migration",
        help="Relative path from repo root or absolute path to the SQL migration file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the file exists and print the target without executing SQL.",
    )
    return parser


def resolve_migration_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def main() -> int:
    args = build_parser().parse_args()
    migration_path = resolve_migration_path(args.migration)

    print("SUPABASE_MIGRATION_APPLY")
    print(f"MIGRATION_FILE {migration_path}")

    if not migration_path.exists() or not migration_path.is_file():
        print("RESULT FAIL")
        print(f"- migration file not found: {migration_path}")
        return 2

    sql_text = migration_path.read_text(encoding="utf-8")
    if not sql_text.strip():
        print("RESULT FAIL")
        print(f"- migration file is empty: {migration_path}")
        return 2

    if args.dry_run:
        print("RESULT DRY_RUN")
        return 0

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        cursor.execute(sql_text)
        raw_connection.commit()
    except Exception as exc:
        raw_connection.rollback()
        print("RESULT FAIL")
        print(f"- {exc}")
        return 1
    finally:
        raw_connection.close()

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())