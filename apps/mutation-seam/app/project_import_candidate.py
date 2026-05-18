from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.project_seed_sources import load_project_seed_sources
from app.project_import_snapshot import clear_project_import_snapshot_cache, load_project_import_candidate_snapshot
from app.project_tracker_sources import load_project_tracker_sources
from app.seed_workbooks import load_seed_data


IMPORT_CANDIDATE_VERSION = "pm_import_candidate_read_only_v1"
MUTATION_AUTHORITY = "not_admitted"


def clear_project_import_candidate_cache() -> None:
    load_project_import_candidate.cache_clear()
    clear_project_import_snapshot_cache()


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slug(value: Any, fallback: str = "unknown") -> str:
    text = _clean_text(value) or fallback
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or fallback


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def _source_file_state(source_id: str, label: str, path_value: Any) -> Dict[str, Any]:
    path_text = _clean_text(path_value)
    state: Dict[str, Any] = {
        "source_id": source_id,
        "label": label,
        "path": path_text,
        "found": False,
        "size_bytes": None,
        "modified_at": None,
        "fingerprint": None,
        "freshness_status": "missing",
    }
    if not path_text:
        return state

    path = Path(path_text)
    try:
        stat = path.stat()
    except OSError:
        return state

    modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    fingerprint_input = f"{source_id}|{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}"
    state.update(
        {
            "found": True,
            "size_bytes": stat.st_size,
            "modified_at": modified_at,
            "fingerprint": hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()[:24],
            "freshness_status": "available",
        }
    )
    return state


def _source_freshness_summary(
    project: Dict[str, Any],
    trackers: Dict[str, Any],
    seed: Dict[str, Any],
) -> Dict[str, Any]:
    metadata = project.get("metadata", {})
    source_files = [
        _source_file_state("estimator_workbook", "Estimator workbook", metadata.get("estimator_workbook_path")),
        _source_file_state("sld_pdf", "SLD or drawing PDF", metadata.get("sld_pdf_path")),
        _source_file_state(
            "project_data_entry",
            "Project data entry workbook",
            trackers.get("project_data_entry", {}).get("path"),
        ),
        _source_file_state(
            "reference_tracker",
            "Reference tracker workbook",
            trackers.get("reference_tracker", {}).get("path"),
        ),
        _source_file_state(
            "equipment_workbook",
            "Equipment inventory workbook",
            seed.get("metadata", {}).get("equipment_workbook_path"),
        ),
        _source_file_state(
            "capability_workbook",
            "Crew capability workbook",
            seed.get("metadata", {}).get("capability_workbook_path"),
        ),
    ]
    aggregate_input = "|".join(
        str(file_state.get("fingerprint") or file_state.get("path") or file_state.get("source_id"))
        for file_state in source_files
    )
    missing_count = sum(1 for file_state in source_files if not file_state.get("found"))
    return {
        "strategy": "path_size_mtime_fingerprint",
        "mutation_authority": MUTATION_AUTHORITY,
        "source_files": source_files,
        "available_count": len(source_files) - missing_count,
        "missing_count": missing_count,
        "aggregate_fingerprint": hashlib.sha256(aggregate_input.encode("utf-8")).hexdigest()[:24],
        "review_action": "Refresh this candidate if any source path, file size, or modified time changes before import approval is admitted.",
    }


def _source_ref(project: Dict[str, Any], line_item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = project.get("metadata", {})
    return {
        "estimator_workbook_path": metadata.get("estimator_workbook_path"),
        "source_format": project.get("source_format"),
        "source_sheet": project.get("source_sheet"),
        "scope_sheet": line_item.get("scope_sheet"),
        "source_row": line_item.get("source_row"),
        "line_id": line_item.get("line_id"),
        "drawing_ref": line_item.get("drawing_ref"),
    }


def _workpackage_key(line_item: Dict[str, Any]) -> str:
    return str(
        line_item.get("scope_sheet")
        or line_item.get("section")
        or line_item.get("drawing_ref")
        or "Unassigned Scope"
    )


def _task_title(line_item: Dict[str, Any]) -> str:
    apparatus_type = _clean_text(line_item.get("apparatus_type")) or "Apparatus"
    designation = _clean_text(line_item.get("designation"))
    if designation and designation.casefold() not in apparatus_type.casefold():
        return f"{designation} - {apparatus_type}"
    return apparatus_type


def _build_warnings(
    project: Dict[str, Any],
    trackers: Dict[str, Any],
    line_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    metadata = project.get("metadata", {})

    if not metadata.get("estimator_workbook_found"):
        warnings.append(
            {
                "severity": "blocker",
                "code": "MISSING_ESTIMATOR_WORKBOOK",
                "message": "Estimator workbook was not found, so no reliable project import candidate can be produced.",
                "review_action": "Place the Project Miner estimator workbook in the planning folder or pass an explicit workbook path.",
            }
        )

    if not metadata.get("sld_pdf_found"):
        warnings.append(
            {
                "severity": "warning",
                "code": "MISSING_SLD_PDF",
                "message": "SLD or drawing PDF was not found; topology labels and drawing cross-checks may be incomplete.",
                "review_action": "Confirm the drawing PDF path before approving an import.",
            }
        )

    if not line_items:
        warnings.append(
            {
                "severity": "blocker",
                "code": "NO_ESTIMATOR_LINE_ITEMS",
                "message": "No estimator line items were available for task and apparatus proposal.",
                "review_action": "Verify the estimator shape and active sheets before import.",
            }
        )

    missing_designation_count = sum(1 for item in line_items if not item.get("designation"))
    if missing_designation_count:
        warnings.append(
            {
                "severity": "info",
                "code": "MISSING_DESIGNATIONS",
                "message": f"{missing_designation_count} estimator line items do not have explicit designations.",
                "review_action": "Review task naming and apparatus naming before approving the candidate.",
            }
        )

    missing_drawing_count = sum(1 for item in line_items if not item.get("drawing_ref"))
    if missing_drawing_count:
        warnings.append(
            {
                "severity": "warning",
                "code": "MISSING_DRAWING_REFS",
                "message": f"{missing_drawing_count} estimator line items do not have drawing references.",
                "review_action": "Confirm drawing references or accept the candidate with known traceability gaps.",
            }
        )

    duplicate_keys = [
        (
            _clean_text(item.get("section")),
            _clean_text(item.get("apparatus_type")),
            _clean_text(item.get("designation")),
            _clean_text(item.get("drawing_ref")),
        )
        for item in line_items
    ]
    duplicate_groups = [
        {"key": [part for part in key if part is not None], "count": count}
        for key, count in Counter(duplicate_keys).items()
        if count > 1 and any(part is not None for part in key)
    ]
    if duplicate_groups:
        warnings.append(
            {
                "severity": "warning",
                "code": "DUPLICATE_LINE_ITEM_GROUPS",
                "message": f"{len(duplicate_groups)} repeated estimator line-item group(s) should be reviewed for intended duplicates.",
                "review_action": "Confirm repeated rows are expected quantities or intentionally separate tasks.",
                "groups": duplicate_groups[:10],
            }
        )

    planning_sources = [
        ("PROJECT_DATA_ENTRY_FORMULA_ERRORS", trackers.get("project_data_entry", {})),
        ("REFERENCE_TRACKER_FORMULA_ERRORS", trackers.get("reference_tracker", {})),
    ]
    for code, source in planning_sources:
        row_count = int(source.get("formula_error_row_count") or 0)
        cell_count = int(source.get("formula_error_cell_count") or 0)
        if row_count:
            warnings.append(
                {
                    "severity": "warning",
                    "code": code,
                    "message": f"{row_count} planning-workbook row(s) include formula errors across {cell_count} cell(s).",
                    "review_action": "Treat the tracker as lineage evidence only until formula errors are understood.",
                    "source_path": source.get("path"),
                    "formula_error_row_count": row_count,
                    "formula_error_cell_count": cell_count,
                    "formula_error_column_counts": _json_safe(source.get("formula_error_column_counts", {})),
                    "formula_error_sample_rows": _json_safe(source.get("formula_error_sample_rows", [])),
                }
            )

    return warnings


def _human_decisions(warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    decisions = [
        {
            "decision_id": "decision-approve-candidate-for-import-planning",
            "severity": "required_before_import",
            "prompt": "Does this candidate correctly represent the project, workpackages, tasks, and apparatus that should be staged for import?",
            "recommended_action": "Approve only after blocker and warning review is complete. This approval still does not write production data.",
        }
    ]
    for index, warning in enumerate(warnings, start=1):
        if warning.get("severity") in {"blocker", "warning"}:
            decisions.append(
                {
                    "decision_id": f"decision-warning-{index:03d}",
                    "severity": warning.get("severity"),
                    "prompt": warning.get("message"),
                    "recommended_action": warning.get("review_action"),
                    "warning_code": warning.get("code"),
                }
            )
    return decisions


def build_project_import_candidate(
    project: Dict[str, Any],
    trackers: Dict[str, Any],
    seed: Dict[str, Any],
) -> Dict[str, Any]:
    line_items = list(project.get("line_items") or [])
    apparatus_candidates = list(project.get("expanded_apparatus_candidates") or [])
    apparatus_by_line: Dict[str, List[Dict[str, Any]]] = {}
    for candidate in apparatus_candidates:
        apparatus_by_line.setdefault(str(candidate.get("line_id")), []).append(candidate)

    workpackages: List[Dict[str, Any]] = []
    workpackage_index_by_key: Dict[str, int] = {}

    for line_item in line_items:
        key = _workpackage_key(line_item)
        if key not in workpackage_index_by_key:
            workpackage_index_by_key[key] = len(workpackages)
            workpackage_id = f"candidate-wp-{len(workpackages) + 1:03d}"
            workpackages.append(
                {
                    "workpackage_id": workpackage_id,
                    "title": key,
                    "source_section": _json_safe(line_item.get("section")),
                    "source_scope_sheet": _json_safe(line_item.get("scope_sheet")),
                    "drawing_refs": [],
                    "planned_hours": 0.0,
                    "task_count": 0,
                    "apparatus_candidate_count": 0,
                    "tasks": [],
                }
            )

        workpackage = workpackages[workpackage_index_by_key[key]]
        line_candidates = apparatus_by_line.get(str(line_item.get("line_id")), [])
        planned_hours = _as_float(line_item.get("hrs_line"))
        if planned_hours is None:
            per_unit_hours = _as_float(line_item.get("hrs_per_unit"))
            quantity = _as_float(line_item.get("qty"))
            planned_hours = (per_unit_hours * quantity) if per_unit_hours is not None and quantity is not None else 0.0

        drawing_ref = _clean_text(line_item.get("drawing_ref"))
        if drawing_ref and drawing_ref not in workpackage["drawing_refs"]:
            workpackage["drawing_refs"].append(drawing_ref)

        task_number = sum(len(item["tasks"]) for item in workpackages) + 1
        task = {
            "task_id": f"candidate-task-{task_number:04d}",
            "source_line_id": line_item.get("line_id"),
            "title": _task_title(line_item),
            "apparatus_type": _json_safe(line_item.get("apparatus_type")),
            "designation": _json_safe(line_item.get("designation")),
            "quantity": line_item.get("qty") or len(line_candidates) or 1,
            "drawing_ref": _json_safe(line_item.get("drawing_ref")),
            "planned_hours": planned_hours,
            "source_ref": _source_ref(project, line_item),
            "apparatus_candidates": [
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "display_name": _json_safe(candidate.get("display_name")),
                    "apparatus_type": _json_safe(candidate.get("apparatus_type")),
                    "designation": _json_safe(candidate.get("designation")),
                    "drawing_ref": _json_safe(candidate.get("drawing_ref")),
                    "planned_hours": _json_safe(candidate.get("planned_hours")),
                    "source_line_id": candidate.get("line_id"),
                    "source_row": candidate.get("source_row"),
                    "scope_sheet": candidate.get("scope_sheet"),
                }
                for candidate in line_candidates
            ],
        }
        workpackage["tasks"].append(task)
        workpackage["task_count"] += 1
        workpackage["apparatus_candidate_count"] += len(line_candidates)
        workpackage["planned_hours"] = round(float(workpackage["planned_hours"]) + float(planned_hours or 0), 4)

    warnings = _build_warnings(project, trackers, line_items)
    human_decisions = _human_decisions(warnings)
    project_slug = _slug(project.get("project_name") or "project-miner")
    warning_counts = Counter(warning["severity"] for warning in warnings)
    source_freshness = _source_freshness_summary(project, trackers, seed)

    return {
        "candidate_id": f"pm-import-candidate-{project_slug}",
        "candidate_version": IMPORT_CANDIDATE_VERSION,
        "review_status": "draft_review_only",
        "mutation_authority": MUTATION_AUTHORITY,
        "project": {
            "name": _json_safe(project.get("project_name")),
            "location": _json_safe(project.get("location")),
            "drawing_package": _json_safe(project.get("drawing_package")),
            "issue_date": _json_safe(project.get("issue_date")),
            "source_format": project.get("source_format"),
            "source_sheet": project.get("source_sheet"),
            "scope_sheets": _json_safe(project.get("scope_sheets", [])),
        },
        "source_bundle": {
            **_json_safe(project.get("metadata", {})),
            "topology_label_count": len(project.get("topology_labels", [])),
            "topology_counts": _json_safe(project.get("topology_counts", {})),
            "project_data_entry": {
                "path": trackers.get("project_data_entry", {}).get("path"),
                "found": trackers.get("project_data_entry", {}).get("found"),
                "task_entry_count": trackers.get("project_data_entry", {}).get("task_entry_count"),
                "all_tasks_count": trackers.get("project_data_entry", {}).get("all_tasks_count"),
                "formula_error_row_count": trackers.get("project_data_entry", {}).get("formula_error_row_count"),
            },
            "reference_tracker": {
                "path": trackers.get("reference_tracker", {}).get("path"),
                "found": trackers.get("reference_tracker", {}).get("found"),
                "task_entry_count": trackers.get("reference_tracker", {}).get("task_entry_count"),
                "all_tasks_count": trackers.get("reference_tracker", {}).get("all_tasks_count"),
                "formula_error_row_count": trackers.get("reference_tracker", {}).get("formula_error_row_count"),
                "status_counts": _json_safe(trackers.get("reference_tracker", {}).get("status_counts", {})),
            },
            "equipment_workbook_path": seed.get("metadata", {}).get("equipment_workbook_path"),
            "equipment_workbook_found": seed.get("metadata", {}).get("equipment_workbook_found"),
            "capability_workbook_path": seed.get("metadata", {}).get("capability_workbook_path"),
            "capability_workbook_found": seed.get("metadata", {}).get("capability_workbook_found"),
        },
        "source_freshness": source_freshness,
        "summary": {
            "workpackage_count": len(workpackages),
            "task_count": len(line_items),
            "line_item_count": len(line_items),
            "apparatus_candidate_count": len(apparatus_candidates),
            "topology_label_count": len(project.get("topology_labels", [])),
            "crew_count": len(seed.get("crew", [])),
            "equipment_inventory_count": len(seed.get("equipment_inventory", [])),
            "standard_tech_list_count": len(seed.get("standard_tech_list", [])),
            "capability_count": len(seed.get("tech_capabilities", [])),
            "warning_count": len(warnings),
            "blocker_count": warning_counts.get("blocker", 0),
            "human_decision_count": len(human_decisions),
        },
        "workpackages": workpackages,
        "warnings": warnings,
        "human_decisions": human_decisions,
        "review_guidance": {
            "primary_review_goal": "Confirm exceptions, traceability gaps, duplicate-looking rows, and candidate grouping before any future import mutation.",
            "allowed_now": [
                "review_candidate",
                "export_json",
                "record_questions",
                "prepare_future_import_packet",
            ],
            "not_allowed_now": [
                "write_supabase",
                "run_workbook_macros",
                "auto_assign_work",
                "change_status",
                "mutate_schedule",
            ],
        },
    }


@lru_cache(maxsize=4)
def load_project_import_candidate(
    estimator_workbook_path: Optional[str] = None,
    sld_pdf_path: Optional[str] = None,
    equipment_workbook_path: Optional[str] = None,
    capability_workbook_path: Optional[str] = None,
    project_data_entry_workbook_path: Optional[str] = None,
    reference_tracker_workbook_path: Optional[str] = None,
) -> Dict[str, Any]:
    explicit_source_paths = any(
        path is not None
        for path in (
            estimator_workbook_path,
            sld_pdf_path,
            equipment_workbook_path,
            capability_workbook_path,
            project_data_entry_workbook_path,
            reference_tracker_workbook_path,
        )
    )
    if not explicit_source_paths:
        snapshot_candidate = load_project_import_candidate_snapshot()
        if snapshot_candidate is not None:
            return snapshot_candidate

    project = load_project_seed_sources(estimator_workbook_path, sld_pdf_path)
    trackers = load_project_tracker_sources(project_data_entry_workbook_path, reference_tracker_workbook_path)
    seed = load_seed_data(equipment_workbook_path, capability_workbook_path)
    return build_project_import_candidate(project, trackers, seed)
