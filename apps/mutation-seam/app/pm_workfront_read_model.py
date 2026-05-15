from __future__ import annotations

from typing import Any, Dict, List

from app.seed_workbooks import load_seed_data


OPEN_ISSUE_STATUSES = {"open", "escalated", "new", "in_review"}


def _is_open_issue(issue: Dict[str, Any]) -> bool:
    return str(issue.get("status") or "").lower() not in {"resolved", "closed", "complete"}


def _status_label(status: Any) -> str:
    return str(status or "unknown").replace("_", " ")


def _crew_name_map() -> Dict[str, str]:
    return {
        str(row.get("id")): str(row.get("name"))
        for row in load_seed_data().get("crew", [])
        if row.get("id") and row.get("name")
    }


def _readiness(row: Dict[str, Any], blocking_issues: List[Dict[str, Any]]) -> str:
    status = str(row.get("status") or "").lower()
    if blocking_issues or status == "on_hold":
        return "blocked"
    if not row.get("assigned_to"):
        return "unassigned"
    if status in {"ready", "not_started"}:
        return "ready"
    if status == "active":
        return "in_progress"
    if status == "complete":
        return "complete"
    if status == "awaiting_review":
        return "pm_review"
    return "monitor"


def _next_action(
    row: Dict[str, Any],
    readiness: str,
    blocking_issues: List[Dict[str, Any]],
    checklist_complete_count: int,
    checklist_total_count: int,
) -> str:
    status = str(row.get("status") or "").lower()
    if blocking_issues:
        title = blocking_issues[0].get("title") or "blocking issue"
        return f"Resolve blocker: {title}"
    if readiness == "blocked":
        return "Review hold reason before dispatch"
    if readiness == "unassigned":
        return "Assign owner"
    if readiness == "ready":
        return "Start field work"
    if status == "active" and checklist_complete_count < checklist_total_count:
        remaining = checklist_total_count - checklist_complete_count
        return f"Complete {remaining} checklist item{'s' if remaining != 1 else ''}"
    if status == "complete":
        return "PM confirm closeout"
    if status == "awaiting_review":
        return "PM review required"
    return "Monitor for next status"


def build_pm_workfront_read_model(
    *,
    apparatus_rows: List[Dict[str, Any]],
    assignment_rows: List[Dict[str, Any]],
    task_rows: List[Dict[str, Any]],
    workpackage_rows: List[Dict[str, Any]],
    issue_rows: List[Dict[str, Any]],
    checklist_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a read-only PM workfront projection from seam store rows."""
    crew_names = _crew_name_map()
    task_map = {row.get("id"): row for row in task_rows}
    workpackage_map = {row.get("id"): row for row in workpackage_rows}
    assignment_by_apparatus = {row.get("apparatus_id"): row for row in assignment_rows if row.get("apparatus_id")}

    open_issues_by_apparatus: Dict[str, List[Dict[str, Any]]] = {}
    for issue in issue_rows:
        apparatus_id = issue.get("apparatus_id")
        if apparatus_id and _is_open_issue(issue):
            open_issues_by_apparatus.setdefault(str(apparatus_id), []).append(issue)

    checklist_by_apparatus: Dict[str, List[Dict[str, Any]]] = {}
    for item in checklist_rows:
        apparatus_id = item.get("apparatus_id")
        if apparatus_id:
            checklist_by_apparatus.setdefault(str(apparatus_id), []).append(item)

    rows: List[Dict[str, Any]] = []
    for apparatus in apparatus_rows:
        apparatus_id = str(apparatus.get("id"))
        task = task_map.get(apparatus.get("task_id"), {})
        workpackage = workpackage_map.get(task.get("workpackage_id"), {})
        assignment = assignment_by_apparatus.get(apparatus_id, {})
        owner_id = apparatus.get("assigned_to") or assignment.get("assigned_to")
        issues = open_issues_by_apparatus.get(apparatus_id, [])
        blocking_issues = [
            issue for issue in issues
            if issue.get("blocks_completion") or str(issue.get("status") or "").lower() == "escalated"
        ]
        checklist = checklist_by_apparatus.get(apparatus_id, [])
        checklist_complete_count = sum(1 for item in checklist if item.get("completed"))
        checklist_total_count = len(checklist)
        readiness = _readiness(apparatus, blocking_issues)

        rows.append(
            {
                "id": f"workfront-{apparatus_id}",
                "apparatus_id": apparatus_id,
                "apparatus_name": apparatus.get("name") or apparatus_id,
                "status": apparatus.get("status") or "unknown",
                "status_label": _status_label(apparatus.get("status")),
                "readiness": readiness,
                "blocked": readiness == "blocked",
                "blocker_count": len(blocking_issues),
                "open_issue_count": len(issues),
                "blocking_issue_titles": [issue.get("title") or issue.get("id") for issue in blocking_issues],
                "owner_id": owner_id,
                "owner_name": crew_names.get(str(owner_id), owner_id) if owner_id else None,
                "task_id": task.get("id"),
                "task_name": task.get("name"),
                "workpackage_id": workpackage.get("id"),
                "workpackage_name": workpackage.get("name"),
                "designation": apparatus.get("source_designation"),
                "apparatus_type": apparatus.get("source_apparatus_type"),
                "drawing_ref": apparatus.get("source_drawing_ref") or task.get("drawing_ref"),
                "checklist_complete_count": checklist_complete_count,
                "checklist_total_count": checklist_total_count,
                "next_action": _next_action(
                    apparatus,
                    readiness,
                    blocking_issues,
                    checklist_complete_count,
                    checklist_total_count,
                ),
            }
        )

    readiness_order = {
        "blocked": 0,
        "unassigned": 1,
        "pm_review": 2,
        "ready": 3,
        "in_progress": 4,
        "monitor": 5,
        "complete": 6,
    }
    rows.sort(key=lambda row: (readiness_order.get(row["readiness"], 99), row.get("workpackage_name") or "", row["apparatus_name"]))

    summary = {
        "total_count": len(rows),
        "blocked_count": sum(1 for row in rows if row["readiness"] == "blocked"),
        "unassigned_count": sum(1 for row in rows if row["readiness"] == "unassigned"),
        "ready_count": sum(1 for row in rows if row["readiness"] == "ready"),
        "in_progress_count": sum(1 for row in rows if row["readiness"] == "in_progress"),
        "pm_review_count": sum(1 for row in rows if row["readiness"] == "pm_review"),
        "complete_count": sum(1 for row in rows if row["readiness"] == "complete"),
    }

    return {
        "summary": summary,
        "rows": rows,
        "advisory": {
            "mode": "read_only",
            "ai_mutation_authority": "not_admitted",
            "recommended_focus": rows[0]["next_action"] if rows else "No apparatus workfront rows are available",
        },
    }
