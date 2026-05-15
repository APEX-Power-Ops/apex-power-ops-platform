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
from app.seed_workbooks import clear_seed_cache, load_seed_data


def _sample(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return items[: max(0, limit)]


def _build_preview(line_limit: int) -> dict[str, Any]:
    clear_project_seed_cache()
    clear_seed_cache()
    project = load_project_seed_sources()
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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--line-limit", type=int, default=8)
    args = parser.parse_args()

    if args.planning_root:
        os.environ["APEX_PROJECT_MINER_PLANNING_ROOT"] = args.planning_root

    preview = _build_preview(args.line_limit)
    if args.format == "json":
        print(json.dumps(preview, indent=2, sort_keys=True, default=str))
    else:
        _print_text(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
