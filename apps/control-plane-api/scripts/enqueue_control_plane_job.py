from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SessionLocal
from services.control_plane.queue import (
    ALLOWED_LOCAL_ACTION_TYPES,
    ALLOWED_QUEUE_PRIORITIES,
    enqueue_local_action,
    enqueue_render_validation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Queue a bounded control-plane local action without direct SQL."
    )
    parser.add_argument("--requested-by", required=True, help="Durable actor id recorded on the queued job.")
    parser.add_argument("--priority", default="normal", choices=sorted(ALLOWED_QUEUE_PRIORITIES))
    parser.add_argument("--task-id", help="Optional task packet id associated with the queued job.")
    parser.add_argument("--confirm", action="store_true", help="Required confirmation flag for live queue insertion.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved queue request without inserting it.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    local_action = subparsers.add_parser("local-action", help="Queue a generic local action.")
    local_action.add_argument("--action-type", required=True, choices=sorted(ALLOWED_LOCAL_ACTION_TYPES))
    local_action.add_argument("--subject-type", required=True)
    local_action.add_argument("--subject-id", required=True)
    local_action.add_argument(
        "--request-payload-json",
        default="{}",
        help="JSON object payload for the queued action.",
    )

    render_validation = subparsers.add_parser("render-validation", help="Queue a render-validation job.")
    render_validation.add_argument("--guide-slug", required=True)
    render_validation.add_argument("--validation-target", required=True)
    render_validation.add_argument("--expected-asset-id", action="append", default=[])
    return parser


def _load_json_object(raw_value: str) -> dict:
    value = json.loads(raw_value)
    if not isinstance(value, dict):
        raise ValueError("request payload must be a JSON object")
    return value


def main() -> int:
    args = build_parser().parse_args()

    if not args.confirm and not args.dry_run:
        print("RESULT FAIL")
        print("- explicit confirmation required; rerun with --confirm")
        return 2

    if args.command == "local-action":
        resolved_payload = {
            "action_type": args.action_type,
            "priority": args.priority,
            "task_id": args.task_id,
            "subject_type": args.subject_type,
            "subject_id": args.subject_id,
            "requested_by": args.requested_by,
            "request_payload": _load_json_object(args.request_payload_json),
        }
    else:
        resolved_payload = {
            "guide_slug": args.guide_slug,
            "validation_target": args.validation_target,
            "expected_asset_ids": args.expected_asset_id,
            "priority": args.priority,
            "task_id": args.task_id,
            "requested_by": args.requested_by,
        }

    print("CONTROL_PLANE_ENQUEUE")
    print(f"COMMAND {args.command}")
    print(f"REQUESTED_BY {args.requested_by}")
    print(f"PRIORITY {args.priority}")

    if args.dry_run:
        print("RESULT DRY_RUN")
        print(json.dumps(resolved_payload, indent=2, sort_keys=True))
        return 0

    db = SessionLocal()
    try:
        if args.command == "local-action":
            queued = enqueue_local_action(db, **resolved_payload)
        else:
            queued = enqueue_render_validation(db, **resolved_payload)
        db.commit()
    except ValueError as exc:
        db.rollback()
        print("RESULT FAIL")
        print(f"- {exc}")
        return 2
    except Exception as exc:
        db.rollback()
        print("RESULT FAIL")
        print(f"- {exc}")
        return 1
    finally:
        db.close()

    print("RESULT PASS")
    print(json.dumps(queued, default=str, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())