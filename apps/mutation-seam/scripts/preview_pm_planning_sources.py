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

from app.project_seed_sources import clear_project_seed_cache, load_project_seed_sources
from app.project_tracker_sources import clear_project_tracker_cache, load_project_tracker_sources
from app.seed_workbooks import clear_seed_cache, load_seed_data


def _sample(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return items[: max(0, limit)]


def _build_preview(line_limit: int) -> dict[str, Any]:
    clear_project_seed_cache()
    clear_project_tracker_cache()
    clear_seed_cache()
    project = load_project_seed_sources()
    trackers = load_project_tracker_sources()
    seed = load_seed_data()
    line_items = project.get("line_items", [])
    apparatus_candidates = project.get("expanded_apparatus_candidates", [])
    capabilities = seed.get("tech_capabilities", [])

    return {
        "project": {
            "name": project.get("project_name"),
            "location": project.get("location"),
            "drawing_package": project.get("drawing_package"),
            "issue_date": project.get("issue_date"),
            "source_sheet": project.get("source_sheet"),
            "source_format": project.get("source_format"),
            "scope_count": project.get("scope_count"),
            "scope_sheets": project.get("scope_sheets", []),
            "line_item_count": len(line_items),
            "apparatus_candidate_count": len(apparatus_candidates),
            "topology_label_count": len(project.get("topology_labels", [])),
            "topology_counts": project.get("topology_counts", {}),
        },
        "source_metadata": {
            **project.get("metadata", {}),
            "equipment_workbook_path": seed.get("metadata", {}).get("equipment_workbook_path"),
            "equipment_workbook_found": seed.get("metadata", {}).get("equipment_workbook_found"),
            "capability_workbook_path": seed.get("metadata", {}).get("capability_workbook_path"),
            "capability_workbook_found": seed.get("metadata", {}).get("capability_workbook_found"),
        },
        "crew": {
            "count": len(seed.get("crew", [])),
            "sample": _sample(seed.get("crew", []), line_limit),
        },
        "equipment": {
            "inventory_count": len(seed.get("equipment_inventory", [])),
            "standard_tech_list_count": len(seed.get("standard_tech_list", [])),
            "capability_count": len(capabilities),
            "capability_sample": _sample(capabilities, line_limit),
        },
        "planning_workbooks": {
            "metadata": trackers.get("metadata", {}),
            "project_data_entry": {
                **{
                    key: value
                    for key, value in trackers.get("project_data_entry", {}).items()
                    if key not in {"task_entry_sample", "all_tasks_sample"}
                },
                "task_entry_sample": _sample(
                    trackers.get("project_data_entry", {}).get("task_entry_sample", []), line_limit
                ),
                "all_tasks_sample": _sample(
                    trackers.get("project_data_entry", {}).get("all_tasks_sample", []), line_limit
                ),
            },
            "reference_tracker": {
                **{
                    key: value
                    for key, value in trackers.get("reference_tracker", {}).items()
                    if key not in {"task_entry_sample", "all_tasks_sample"}
                },
                "task_entry_sample": _sample(
                    trackers.get("reference_tracker", {}).get("task_entry_sample", []), line_limit
                ),
                "all_tasks_sample": _sample(
                    trackers.get("reference_tracker", {}).get("all_tasks_sample", []), line_limit
                ),
            },
        },
        "line_item_sample": _sample(line_items, line_limit),
        "apparatus_candidate_sample": _sample(apparatus_candidates, line_limit),
    }


def _print_text(preview: dict[str, Any]) -> None:
    project = preview["project"]
    metadata = preview["source_metadata"]
    print("PM Planning Source Preview")
    print("==========================")
    print(f"Project: {project.get('name') or 'unknown'}")
    print(f"Location: {project.get('location') or 'unknown'}")
    print(f"Drawing package: {project.get('drawing_package') or 'unknown'}")
    print(f"Issue date: {project.get('issue_date') or 'unknown'}")
    print(f"Source sheet: {project.get('source_sheet') or 'unknown'}")
    print(f"Source format: {project.get('source_format') or 'unknown'}")
    if project.get("scope_count"):
        print(f"Scope sheets: {project.get('scope_count')} {project.get('scope_sheets') or []}")
    print(f"Line items: {project['line_item_count']}")
    print(f"Apparatus candidates: {project['apparatus_candidate_count']}")
    print(f"Topology labels: {project['topology_label_count']} {project.get('topology_counts') or {}}")
    print()
    print("Sources")
    print(f"- estimator: {metadata.get('estimator_workbook_path')} found={metadata.get('estimator_workbook_found')}")
    print(f"- SLD PDF: {metadata.get('sld_pdf_path')} found={metadata.get('sld_pdf_found')}")
    print(f"- equipment: {metadata.get('equipment_workbook_path')} found={metadata.get('equipment_workbook_found')}")
    print(f"- capabilities: {metadata.get('capability_workbook_path')} found={metadata.get('capability_workbook_found')}")
    print()
    print(f"Crew: {preview['crew']['count']}")
    print(f"Equipment inventory rows: {preview['equipment']['inventory_count']}")
    print(f"Standard tech list rows: {preview['equipment']['standard_tech_list_count']}")
    print(f"Capability rows: {preview['equipment']['capability_count']}")
    print()
    planning_workbooks = preview.get("planning_workbooks", {})
    data_entry = planning_workbooks.get("project_data_entry", {})
    reference_tracker = planning_workbooks.get("reference_tracker", {})
    print("Planning Workbooks")
    print(
        "- project data entry: "
        f"{data_entry.get('path')} found={data_entry.get('found')} "
        f"task_entry_rows={data_entry.get('task_entry_count')} "
        f"all_tasks_rows={data_entry.get('all_tasks_count')} "
        f"formula_error_rows={data_entry.get('formula_error_row_count')}"
    )
    print(
        "- reference tracker: "
        f"{reference_tracker.get('path')} found={reference_tracker.get('found')} "
        f"task_entry_rows={reference_tracker.get('task_entry_count')} "
        f"all_tasks_rows={reference_tracker.get('all_tasks_count')} "
        f"statuses={reference_tracker.get('status_counts') or {}}"
    )
    print()
    print("Line Item Sample")
    for item in preview["line_item_sample"]:
        print(
            f"- {item.get('line_id')}: qty={item.get('qty')} "
            f"section={item.get('section')} apparatus={item.get('apparatus_type')} "
            f"designation={item.get('designation')} drawing={item.get('drawing_ref')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preview read-only Project Miner PM planning sources without writing database state.",
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
    parser.add_argument("--line-limit", type=int, default=8)
    args = parser.parse_args()

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

    preview = _build_preview(args.line_limit)
    if args.format == "json":
        print(json.dumps(preview, indent=2, sort_keys=True, default=str))
    else:
        _print_text(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
