from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SessionLocal
from services.control_plane.worker import (
    claim_next_job,
    complete_job,
    fail_job,
    mark_job_running,
    missing_worker_tables,
    process_job,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local control-plane worker against queued actions.")
    parser.add_argument("--study-root", required=True, help="Absolute path to the study-material repository root.")
    parser.add_argument("--runner-id", default="control-plane-worker", help="Identifier recorded on claimed jobs.")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job and exit.")
    parser.add_argument("--poll-seconds", type=int, default=10, help="Polling interval when not using --once.")
    parser.add_argument("--dry-run", action="store_true", help="Do not invoke live handlers; record dry-run results instead.")
    return parser


def ensure_worker_ready(study_root: Path) -> int:
    if not study_root.exists() or not study_root.is_dir():
        print(f"RESULT FAIL")
        print(f"- study root not found: {study_root}")
        return 2

    db = SessionLocal()
    try:
        missing_tables = missing_worker_tables(db)
        if missing_tables:
            print("RESULT FAIL")
            print(
                "- control-plane tables missing; apply supabase/migrations/20260328_000007_add_control_plane_tables.sql: "
                + ", ".join(missing_tables)
            )
            return 2
        return 0
    finally:
        db.close()


def process_one_job(study_root: Path, runner_id: str, dry_run: bool) -> bool:
    db = SessionLocal()
    try:
        job = claim_next_job(db, runner_id=runner_id)
        if job is None:
            db.rollback()
            return False

        mark_job_running(db, job.job_id)
        result = process_job(job, study_root=study_root, runner_id=runner_id, dry_run=dry_run, db=db)
        complete_job(
            db,
            job,
            runner_id=runner_id,
            result_summary=result["result_summary"],
            result_json=result["result_json"],
            evidence_artifacts=result.get("evidence_artifacts", []),
        )
        db.commit()
        print(f"PROCESSED_JOB {job.job_id} {job.action_type}")
        return True
    except Exception as exc:
        if 'job' in locals() and job is not None:
            fail_job(db, job, runner_id=runner_id, error_message=str(exc))
            db.commit()
        else:
            db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    args = build_parser().parse_args()
    study_root = Path(args.study_root).resolve()
    print(f"CONTROL_PLANE_WORKER runner={args.runner_id} dry_run={args.dry_run}")
    print(f"STUDY_ROOT {study_root}")

    readiness_status = ensure_worker_ready(study_root)
    if readiness_status != 0:
        return readiness_status

    if args.once:
        processed = process_one_job(study_root=study_root, runner_id=args.runner_id, dry_run=args.dry_run)
        print("RESULT PASS" if processed else "RESULT IDLE")
        return 0

    while True:
        processed = process_one_job(study_root=study_root, runner_id=args.runner_id, dry_run=args.dry_run)
        if not processed:
            time.sleep(max(1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())