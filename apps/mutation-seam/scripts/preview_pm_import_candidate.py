from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


def _set_env_from_args(args: argparse.Namespace) -> None:
    if args.planning_root:
        os.environ["APEX_PROJECT_MINER_PLANNING_ROOT"] = args.planning_root
    if args.estimator_workbook:
        os.environ["APEX_PROJECT_ESTIMATOR_WORKBOOK"] = args.estimator_workbook
    if args.sld_pdf:
        os.environ["APEX_PROJECT_SLD_PDF"] = args.sld_pdf
    if args.equipment_workbook:
        os.environ["APEX_FIELD_SEED_EQUIPMENT_WORKBOOK"] = args.equipment_workbook
    if args.capability_workbook:
        os.environ["APEX_FIELD_SEED_CAPABILITY_WORKBOOK"] = args.capability_workbook
    if args.data_entry_workbook:
        os.environ["APEX_PROJECT_DATA_ENTRY_WORKBOOK"] = args.data_entry_workbook
    if args.reference_tracker_workbook:
        os.environ["APEX_REFERENCE_TRACKER_WORKBOOK"] = args.reference_tracker_workbook


def _clear_caches() -> None:
    clear_project_import_candidate_cache()
    clear_project_seed_cache()
    clear_project_tracker_cache()
    clear_seed_cache()


def _print_text(candidate: dict[str, Any]) -> None:
    project = candidate.get("project", {})
    summary = candidate.get("summary", {})
    print("PM Import Candidate Preview")
    print("===========================")
    print(f"Candidate: {candidate.get('candidate_id')}")
    print(f"Project: {project.get('name') or 'unknown'}")
    print(f"Location: {project.get('location') or 'unknown'}")
    print(f"Source format: {project.get('source_format') or 'unknown'}")
    print(f"Mutation authority: {candidate.get('mutation_authority')}")
    print()
    print("Summary")
    print(f"- workpackages: {summary.get('workpackage_count')}")
    print(f"- tasks: {summary.get('task_count')}")
    print(f"- apparatus candidates: {summary.get('apparatus_candidate_count')}")
    print(f"- warnings: {summary.get('warning_count')} blockers={summary.get('blocker_count')}")
    print(f"- human decisions: {summary.get('human_decision_count')}")
    print(f"- crew: {summary.get('crew_count')}")
    print(f"- equipment inventory rows: {summary.get('equipment_inventory_count')}")
    print(f"- capability rows: {summary.get('capability_count')}")
    print()
    print("Warnings")
    for warning in candidate.get("warnings", []):
        print(f"- {warning.get('severity')} {warning.get('code')}: {warning.get('message')}")
    if not candidate.get("warnings"):
        print("- none")
    print()
    print("Workpackages")
    for workpackage in candidate.get("workpackages", [])[:8]:
        print(
            f"- {workpackage.get('workpackage_id')}: {workpackage.get('title')} "
            f"tasks={workpackage.get('task_count')} apparatus={workpackage.get('apparatus_candidate_count')} "
            f"hours={workpackage.get('planned_hours')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview a read-only Project Miner PM import candidate without writing database state.",
    )
    parser.add_argument(
        "--planning-root",
        help="Folder containing Project Miner estimator, SLD PDF, equipment inventory, and capability matrix.",
    )
    parser.add_argument("--estimator-workbook", help="Specific estimator workbook to preview.")
    parser.add_argument("--sld-pdf", help="Specific SLD or drawing PDF to preview.")
    parser.add_argument("--equipment-workbook", help="Specific equipment inventory workbook to preview.")
    parser.add_argument("--capability-workbook", help="Specific technician capability workbook to preview.")
    parser.add_argument("--data-entry-workbook", help="Specific RESA project data entry workbook to preview.")
    parser.add_argument("--reference-tracker-workbook", help="Specific reference tracker workbook to preview.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    _set_env_from_args(args)
    _clear_caches()
    candidate = load_project_import_candidate()
    if args.format == "json":
        print(json.dumps(candidate, indent=2, sort_keys=True, default=str))
    else:
        _print_text(candidate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
