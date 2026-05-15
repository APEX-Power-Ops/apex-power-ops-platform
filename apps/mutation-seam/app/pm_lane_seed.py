from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Tuple

from app.project_seed_sources import clear_project_seed_cache, load_project_seed_sources
from app.seed_workbooks import clear_seed_cache, load_seed_data


PROJECT_ID = "proj-001"
CHECKLIST_NAMES = ["Visual inspection", "Electrical testing", "Closeout capture"]
WORKPACKAGE_DEFS = {
    "mv_systems": ("wp-001", "Medium Voltage Systems"),
    "lv_distribution": ("wp-002", "Low Voltage Distribution"),
    "temporary_power": ("wp-003", "Temporary Power Skids"),
    "grounding": ("wp-004", "Grounding & Closeout"),
}


def _fallback_seed(now: str) -> Dict[str, Any]:
    return {
        "project": {
            "id": PROJECT_ID,
            "name": "Stack Data Center",
            "created_at": now,
            "updated_at": now,
        },
        "workpackages": [
            {
                "id": "wp-001",
                "project_id": PROJECT_ID,
                "name": "Electrical Systems",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "wp-002",
                "project_id": PROJECT_ID,
                "name": "Safety & Controls",
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
        ],
        "tasks": [
            {
                "id": "task-001",
                "workpackage_id": "wp-001",
                "project_id": PROJECT_ID,
                "name": "Ground Testing",
                "status": "not_started",
                "priority": 1.0,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "task-002",
                "workpackage_id": "wp-001",
                "project_id": PROJECT_ID,
                "name": "Insulation Testing",
                "status": "not_started",
                "priority": 0.8,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "task-003",
                "workpackage_id": "wp-002",
                "project_id": PROJECT_ID,
                "name": "Arc Flash Analysis",
                "status": "not_started",
                "priority": 0.6,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "task-004",
                "workpackage_id": "wp-002",
                "project_id": PROJECT_ID,
                "name": "Controls Documentation",
                "status": "not_started",
                "priority": 0.4,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
        ],
        "apparatus": [
            {
                "id": "app-001",
                "task_id": "task-001",
                "project_id": PROJECT_ID,
                "name": "Main Breaker 480V",
                "neta_standard": "ATS",
                "status": "not_started",
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "app-002",
                "task_id": "task-001",
                "project_id": PROJECT_ID,
                "name": "Distribution Panel",
                "neta_standard": "MTS",
                "status": "ready",
                "assigned_to": "tech-001",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "app-003",
                "task_id": "task-002",
                "project_id": PROJECT_ID,
                "name": "Cable Assembly A",
                "neta_standard": "ATS",
                "status": "active",
                "assigned_to": "tech-001",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "app-004",
                "task_id": "task-002",
                "project_id": PROJECT_ID,
                "name": "Cable Assembly B",
                "neta_standard": "ATS",
                "status": "not_started",
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "app-005",
                "task_id": "task-003",
                "project_id": PROJECT_ID,
                "name": "Control Transformer",
                "neta_standard": "MTS",
                "status": "not_started",
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "app-006",
                "task_id": "task-004",
                "project_id": PROJECT_ID,
                "name": "Safety Switch",
                "neta_standard": "MTS",
                "status": "ready",
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            },
        ],
        "checklist_items": [
            {
                "id": f"item-{index:03d}",
                "apparatus_id": app_id,
                "task_id": task_id,
                "project_id": PROJECT_ID,
                "name": name,
                "completed": False,
                "created_at": now,
                "updated_at": now,
            }
            for index, (app_id, task_id, name) in enumerate(
                [
                    ("app-001", "task-001", "Visual inspection"),
                    ("app-001", "task-001", "Continuity test"),
                    ("app-002", "task-001", "Visual inspection"),
                    ("app-002", "task-001", "Continuity test"),
                    ("app-003", "task-002", "Visual inspection"),
                    ("app-003", "task-002", "Continuity test"),
                    ("app-004", "task-002", "Visual inspection"),
                    ("app-004", "task-002", "Continuity test"),
                    ("app-005", "task-003", "Visual inspection"),
                    ("app-005", "task-003", "Continuity test"),
                    ("app-006", "task-004", "Visual inspection"),
                    ("app-006", "task-004", "Continuity test"),
                ],
                start=1,
            )
        ],
        "assignments": [
            {
                "id": "assign-001",
                "apparatus_id": "app-002",
                "task_id": "task-001",
                "project_id": PROJECT_ID,
                "assigned_to": "tech-001",
                "assigned_by": "lead-001",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "assign-002",
                "apparatus_id": "app-003",
                "task_id": "task-002",
                "project_id": PROJECT_ID,
                "assigned_to": "tech-001",
                "assigned_by": "lead-001",
                "created_at": now,
                "updated_at": now,
            },
        ],
        "hours": [],
        "snapshots": [
            {
                "id": "snap-001",
                "workpackage_id": "wp-001",
                "project_id": PROJECT_ID,
                "period_start": "2026-04-01",
                "period_end": "2026-04-15",
                "status": "submitted",
                "percent_complete": 45,
                "hours_reported": 120,
                "submitted_by": "lead-001",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "snap-002",
                "workpackage_id": "wp-002",
                "project_id": PROJECT_ID,
                "period_start": "2026-04-01",
                "period_end": "2026-04-15",
                "status": "draft",
                "percent_complete": 20,
                "hours_reported": 40,
                "submitted_by": "lead-001",
                "created_at": now,
                "updated_at": now,
            },
        ],
        "issues": [
            {
                "id": "issue-001",
                "apparatus_id": "app-003",
                "task_id": "task-002",
                "project_id": PROJECT_ID,
                "title": "Insulation resistance out of range",
                "severity": "medium",
                "status": "open",
                "blocks_completion": False,
                "reported_by": "tech-001",
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": "issue-002",
                "apparatus_id": "app-001",
                "task_id": "task-001",
                "project_id": PROJECT_ID,
                "title": "Ground rod connection loose",
                "severity": "high",
                "status": "open",
                "blocks_completion": True,
                "reported_by": "tech-001",
                "created_at": now,
                "updated_at": now,
            },
        ],
    }


def _section_label(section: Any) -> str:
    if section is None:
        return "Unmapped"
    if isinstance(section, float) and section.is_integer():
        return str(int(section))
    return str(section).strip()


def _workpackage_key(apparatus_type: str, section: Any) -> str:
    apparatus_type = str(apparatus_type or "")
    section_label = _section_label(section)
    if section_label == "7.13" or "Ground Resistance Test" in apparatus_type:
        return "grounding"
    if "PWR Skid" in apparatus_type:
        return "temporary_power"
    if (
        "Switch MV" in apparatus_type
        or "Conductors MV" in apparatus_type
        or "Switchgear - Medium Voltage" in apparatus_type
        or "Transformer - Pad Mount" in apparatus_type
    ):
        return "mv_systems"
    return "lv_distribution"


def _task_title(section: Any, apparatus_type: str) -> str:
    section_label = _section_label(section)
    if section_label == "Misc":
        return f"Miscellaneous - {apparatus_type}"
    return f"Section {section_label} - {apparatus_type}"


def _task_status(category: str, task_index: int) -> str:
    if category == "grounding":
        return "awaiting_review"
    if task_index <= 2:
        return "active"
    return "not_started"


def _seed_assignment(index: int, tech_ids: List[str]) -> Tuple[str, str | None]:
    if index == 1:
        return "not_started", None
    if index == 2:
        return "ready", tech_ids[0]
    if index == 3:
        return "active", tech_ids[0]
    if index % 29 == 0:
        return "complete", tech_ids[index % len(tech_ids)]
    if index % 19 == 0:
        return "on_hold", tech_ids[index % len(tech_ids)]
    if index % 11 == 0:
        return "active", tech_ids[index % len(tech_ids)]
    if index % 7 == 0:
        return "ready", tech_ids[index % len(tech_ids)]
    return "not_started", None


def _checklist_completed(status: str, checklist_index: int) -> bool:
    if status == "complete":
        return True
    if status in {"active", "on_hold"}:
        return checklist_index == 0
    return False


def build_pm_lane_seed(now: str) -> Dict[str, Any]:
    clear_project_seed_cache()
    clear_seed_cache()
    project_plan = load_project_seed_sources()
    if not project_plan.get("expanded_apparatus_candidates"):
        return _fallback_seed(now)

    crew = load_seed_data().get("crew") or []
    tech_ids = [row.get("id") for row in crew if row.get("id")][:3]
    if not tech_ids:
        tech_ids = ["tech-001", "tech-002", "tech-003"]

    workpackages: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    tasks: List[Dict[str, Any]] = []
    line_to_task_id: Dict[str, str] = {}
    task_to_workpackage_id: Dict[str, str] = {}

    for line_item in project_plan["line_items"]:
        category = _workpackage_key(line_item.get("apparatus_type"), line_item.get("section"))
        workpackage_id, workpackage_name = WORKPACKAGE_DEFS[category]
        if workpackage_id not in workpackages:
            workpackages[workpackage_id] = {
                "id": workpackage_id,
                "project_id": PROJECT_ID,
                "name": workpackage_name,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            }

        task_id = f"task-{len(tasks) + 1:03d}"
        task_status = _task_status(category, len(tasks) + 1)
        task = {
            "id": task_id,
            "workpackage_id": workpackage_id,
            "project_id": PROJECT_ID,
            "name": _task_title(line_item.get("section"), line_item.get("apparatus_type")),
            "status": task_status,
            "priority": max(0.2, round(1.0 - (len(tasks) * 0.06), 2)),
            "assigned_to": None,
            "section": _section_label(line_item.get("section")),
            "drawing_ref": line_item.get("drawing_ref"),
            "created_at": now,
            "updated_at": now,
        }
        tasks.append(task)
        line_to_task_id[line_item["line_id"]] = task_id
        task_to_workpackage_id[task_id] = workpackage_id

    apparatus: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    checklist_items: List[Dict[str, Any]] = []
    hours: List[Dict[str, Any]] = []

    for index, candidate in enumerate(project_plan["expanded_apparatus_candidates"], start=1):
        apparatus_id = f"app-{index:03d}"
        status, assigned_to = _seed_assignment(index, tech_ids)
        task_id = line_to_task_id[candidate["line_id"]]
        apparatus_row = {
            "id": apparatus_id,
            "task_id": task_id,
            "project_id": PROJECT_ID,
            "name": candidate.get("display_name") or candidate.get("apparatus_type"),
            "neta_standard": f"Section {_section_label(candidate.get('section'))}",
            "status": status,
            "assigned_to": assigned_to,
            "source_apparatus_type": candidate.get("apparatus_type"),
            "source_designation": candidate.get("designation"),
            "source_drawing_ref": candidate.get("drawing_ref"),
            "created_at": now,
            "updated_at": now,
        }
        apparatus.append(apparatus_row)

        for checklist_index, checklist_name in enumerate(CHECKLIST_NAMES):
            checklist_items.append(
                {
                    "id": f"item-{len(checklist_items) + 1:03d}",
                    "apparatus_id": apparatus_id,
                    "task_id": task_id,
                    "project_id": PROJECT_ID,
                    "name": checklist_name,
                    "completed": _checklist_completed(status, checklist_index),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if assigned_to:
            assignments.append(
                {
                    "id": f"assign-{len(assignments) + 1:03d}",
                    "apparatus_id": apparatus_id,
                    "task_id": task_id,
                    "project_id": PROJECT_ID,
                    "assigned_to": assigned_to,
                    "assigned_by": "lead-001",
                    "created_at": now,
                    "updated_at": now,
                }
            )

        planned_hours = float(candidate.get("planned_hours") or 0)
        if status in {"active", "on_hold", "complete"}:
            multiplier = 1.0 if status == "complete" else 0.6 if status == "active" else 0.35
            hours.append(
                {
                    "id": f"hours-{len(hours) + 1:03d}",
                    "apparatus_id": apparatus_id,
                    "task_id": task_id,
                    "project_id": PROJECT_ID,
                    "hours": round(max(1.0, planned_hours * multiplier), 2),
                    "date": "2026-03-05",
                    "reported_by": assigned_to or tech_ids[0],
                    "created_at": now,
                    "updated_at": now,
                }
            )

    if len(tasks) >= 4:
        tasks[3]["status"] = "awaiting_review"
    elif tasks and not any(task["status"] == "awaiting_review" for task in tasks):
        tasks[-1]["status"] = "awaiting_review"

    awaiting_review_task_ids = {task["id"] for task in tasks if task["status"] == "awaiting_review"}
    for workpackage in workpackages.values():
        if any(task["workpackage_id"] == workpackage["id"] and task["id"] in awaiting_review_task_ids for task in tasks):
            workpackage["status"] = "awaiting_review"

    apparatus_by_id = {row["id"]: row for row in apparatus}
    issue_target_ids = {
        "issue-001": "app-003" if len(apparatus) >= 3 else apparatus[0]["id"],
        "issue-002": "app-001",
        "issue-003": next((row["id"] for row in apparatus if row["status"] == "on_hold"), apparatus[min(6, len(apparatus) - 1)]["id"]),
        "issue-004": next((row["id"] for row in apparatus if row["status"] == "complete"), apparatus[min(10, len(apparatus) - 1)]["id"]),
    }

    issues = [
        {
            "id": "issue-001",
            "apparatus_id": issue_target_ids["issue-001"],
            "task_id": apparatus_by_id[issue_target_ids["issue-001"]]["task_id"],
            "project_id": PROJECT_ID,
            "title": "Insulation resistance out of range",
            "severity": "medium",
            "status": "open",
            "blocks_completion": False,
            "reported_by": tech_ids[0],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "issue-002",
            "apparatus_id": issue_target_ids["issue-002"],
            "task_id": apparatus_by_id[issue_target_ids["issue-002"]]["task_id"],
            "project_id": PROJECT_ID,
            "title": "Ground rod connection loose",
            "severity": "high",
            "status": "open",
            "blocks_completion": True,
            "reported_by": tech_ids[0],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "issue-003",
            "apparatus_id": issue_target_ids["issue-003"],
            "task_id": apparatus_by_id[issue_target_ids["issue-003"]]["task_id"],
            "project_id": PROJECT_ID,
            "title": "Transformer test variance needs PM review",
            "severity": "high",
            "status": "escalated",
            "blocks_completion": True,
            "reported_by": tech_ids[1] if len(tech_ids) > 1 else tech_ids[0],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "issue-004",
            "apparatus_id": issue_target_ids["issue-004"],
            "task_id": apparatus_by_id[issue_target_ids["issue-004"]]["task_id"],
            "project_id": PROJECT_ID,
            "title": "As-built labels need reconciliation",
            "severity": "low",
            "status": "open",
            "blocks_completion": False,
            "reported_by": tech_ids[2] if len(tech_ids) > 2 else tech_ids[0],
            "created_at": now,
            "updated_at": now,
        },
    ]

    workpackage_rows = list(workpackages.values())
    snapshots: List[Dict[str, Any]] = []
    for index, workpackage in enumerate(workpackage_rows[:3], start=1):
        task_ids = {task["id"] for task in tasks if task["workpackage_id"] == workpackage["id"]}
        workpackage_apparatus = [row for row in apparatus if row["task_id"] in task_ids]
        complete_count = sum(1 for row in workpackage_apparatus if row["status"] == "complete")
        percent_complete = round((complete_count / max(1, len(workpackage_apparatus))) * 100)
        workpackage_hours = sum(entry["hours"] for entry in hours if entry["task_id"] in task_ids)
        snapshots.append(
            {
                "id": f"snap-{index:03d}",
                "workpackage_id": workpackage["id"],
                "project_id": PROJECT_ID,
                "period_start": "2026-03-01",
                "period_end": "2026-03-15",
                "status": "submitted" if index == 1 else "draft" if index == 2 else "awaiting_review",
                "percent_complete": percent_complete,
                "hours_reported": round(workpackage_hours, 2),
                "submitted_by": "lead-001",
                "created_at": now,
                "updated_at": now,
            }
        )

    return {
        "project": {
            "id": PROJECT_ID,
            "name": project_plan.get("project_name") or "Miner Temp Power",
            "location": project_plan.get("location"),
            "drawing_package": project_plan.get("drawing_package"),
            "issue_date": project_plan.get("issue_date"),
            "created_at": now,
            "updated_at": now,
        },
        "workpackages": workpackage_rows,
        "tasks": tasks,
        "apparatus": apparatus,
        "checklist_items": checklist_items,
        "assignments": assignments,
        "hours": hours,
        "snapshots": snapshots,
        "issues": issues,
    }
