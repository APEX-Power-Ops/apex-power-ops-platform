from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CONTROL_PLANE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = CONTROL_PLANE_ROOT / ".env.example"
DEFAULT_TARGET = CONTROL_PLANE_ROOT / ".env"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy the tracked control-plane .env.example template into a local .env file "
            "without claiming runtime readiness."
        )
    )
    parser.add_argument(
        "--target",
        default=str(DEFAULT_TARGET),
        help="Target .env path to create. Defaults to apps/control-plane-api/.env.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target file if it already exists.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without creating the target file.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_path = DEFAULT_SOURCE
    target_path = Path(args.target).resolve()

    if not source_path.exists():
        raise SystemExit(f"Missing template file: {source_path}")

    print("BOOTSTRAP_LOCAL_ENV")
    print(f"SOURCE {source_path}")
    print(f"TARGET {target_path}")

    if target_path.exists() and not args.force:
        print("RESULT FAIL")
        print("- target file already exists; rerun with --force only if overwriting is intentional")
        return 1

    if args.dry_run:
        print("RESULT DRY_RUN")
        print("- template copy was not written")
        print("- copied placeholder values do not satisfy local host readiness until replaced")
        return 0

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, target_path)

    print("RESULT PASS")
    print("- template env file created")
    print("- replace placeholder values before expecting local host readiness to pass")
    print("- rerun apps/control-plane-api/scripts/check_local_host_readiness.py after provisioning real local values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())