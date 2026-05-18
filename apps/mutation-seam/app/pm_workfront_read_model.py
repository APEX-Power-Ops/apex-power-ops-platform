from __future__ import annotations

from typing import Any, Dict, List

from app.seed_workbooks import load_seed_data


OPEN_ISSUE_STATUSES = {"open", "escalated", "new", "in_review"}
PM_DECISION_ACTIONS = {"approve", "reject", "escalate_review", "resolve_escalated", "re_escalate", "return_to_lead"}


def _is_open_issue(issue: Dict[str, Any]) -> bool:
    return str(issue.get("status") or "").lower() not in {"resolved", "closed", "complete"}


def _status_label(status: Any) -> str:
    return str(status or "unknown").replace("_", " ")


def _event_timestamp(event: Dict[str, Any]) -> str:
    return str(event.get("timestamp") or event.get("server_timestamp") or event.get("client_timestamp") or "")


def _event_summary(event: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not event:
        return None

    return {
        "id": event.get("id"),
        "mutation_id": event.get("mutation_id"),
        "actor_id": event.get("actor_id"),
        "actor_role": event.get("actor_role"),
        "action_type": event.get("action_type"),
        "entity_id": event.get("entity_id"),
        "reason": event.get("reason"),
        "timestamp": _event_timestamp(event),
        "from_status": (event.get("from_state") or {}).get("status"),
        "to_status": (event.get("to_state") or {}).get("status"),
    }


def _crew_name_map() -> Dict[str, str]:
    return {
        str(row.get("id")): str(row.get("name"))
        for row in load_seed_data().get("crew", [])
        if row.get("id") and row.get("name")
    }


def _readiness(
    row: Dict[str, Any],
    blocking_issues: List[Dict[str, Any]],
    owner_id: Any = None,
) -> str:
    status = str(row.get("status") or "").lower()
    if blocking_issues or status == "on_hold":
        return "blocked"
    if not owner_id:
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


def _issue_summary(issue: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": issue.get("id"),
        "title": issue.get("title"),
        "status": issue.get("status"),
        "severity": issue.get("severity"),
        "blocks_completion": bool(issue.get("blocks_completion")),
        "reported_by": issue.get("reported_by"),
        "pm_followup_note": issue.get("pm_followup_note"),
        "pm_followup_sent_at": issue.get("pm_followup_sent_at"),
        "pm_followup_workfront_row_id": issue.get("pm_followup_workfront_row_id") or issue.get("workfront_row_id"),
    }


def _advisory_brief(
    *,
    apparatus: Dict[str, Any],
    readiness: str,
    blocking_issues: List[Dict[str, Any]],
    owner_name: str | None,
    task: Dict[str, Any],
    workpackage: Dict[str, Any],
    checklist_complete_count: int,
    checklist_total_count: int,
    next_action: str,
) -> str:
    apparatus_name = apparatus.get("name") or apparatus.get("id") or "Unmapped apparatus"
    owner_label = owner_name or "unassigned"
    drawing_ref = apparatus.get("source_drawing_ref") or task.get("drawing_ref") or "no drawing reference"
    workpackage_name = workpackage.get("name") or "unmapped work package"
    task_name = task.get("name") or "unmapped task"
    blocker = blocking_issues[0].get("title") if blocking_issues else None
    issue_clause = f" Blocking issue: {blocker}." if blocker else ""
    checklist_clause = f" Checklist {checklist_complete_count}/{checklist_total_count}."

    return (
        f"{apparatus_name} is {readiness.replace('_', ' ')} for {workpackage_name} / {task_name}; "
        f"owner {owner_label}; reference {drawing_ref}.{issue_clause}{checklist_clause} "
        f"Requested lead follow-up: {next_action}."
    )


def build_pm_workfront_read_model(
    *,
    apparatus_rows: List[Dict[str, Any]],
    assignment_rows: List[Dict[str, Any]],
    task_rows: List[Dict[str, Any]],
    workpackage_rows: List[Dict[str, Any]],
    issue_rows: List[Dict[str, Any]],
    checklist_rows: List[Dict[str, Any]],
    audit_rows: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build a read-only PM workfront projection from seam store rows."""
    crew_names = _crew_name_map()
    task_map = {row.get("id"): row for row in task_rows}
    workpackage_map = {row.get("id"): row for row in workpackage_rows}
    assignment_by_apparatus = {row.get("apparatus_id"): row for row in assignment_rows if row.get("apparatus_id")}
    audit_by_entity_id: Dict[str, List[Dict[str, Any]]] = {}
    for event in audit_rows or []:
        entity_id = event.get("entity_id")
        if entity_id and (event.get("action_type") in PM_DECISION_ACTIONS or event.get("actor_role") == "pm"):
            audit_by_entity_id.setdefault(str(entity_id), []).append(event)

    for events in audit_by_entity_id.values():
        events.sort(key=_event_timestamp, reverse=True)

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
        if apparatus.get("planning_context_only"):
            continue
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
        returnable_issue = next(
            (issue for issue in blocking_issues if str(issue.get("status") or "").lower() == "escalated"),
            None,
        )
        latest_followup_issue = next((issue for issue in blocking_issues if issue.get("pm_followup_note")), None)
        issue_ids = [str(issue.get("id")) for issue in blocking_issues if issue.get("id")]
        issue_decisions = [event for issue_id in issue_ids for event in audit_by_entity_id.get(issue_id, [])]
        issue_decisions.sort(key=_event_timestamp, reverse=True)
        last_pm_decision = _event_summary(issue_decisions[0] if issue_decisions else None)
        checklist = checklist_by_apparatus.get(apparatus_id, [])
        checklist_complete_count = sum(1 for item in checklist if item.get("completed"))
        checklist_total_count = len(checklist)
        readiness = _readiness(apparatus, blocking_issues, owner_id)
        next_action = _next_action(
            apparatus,
            readiness,
            blocking_issues,
            checklist_complete_count,
            checklist_total_count,
        )
        owner_name = crew_names.get(str(owner_id), owner_id) if owner_id else None
        advisory_brief = _advisory_brief(
            apparatus=apparatus,
            readiness=readiness,
            blocking_issues=blocking_issues,
            owner_name=owner_name,
            task=task,
            workpackage=workpackage,
            checklist_complete_count=checklist_complete_count,
            checklist_total_count=checklist_total_count,
            next_action=next_action,
        )
        lens_tags = ["all", readiness]
        if blocking_issues:
            lens_tags.append("blocked")
        if returnable_issue:
            lens_tags.append("needs_pm_disposition")
        if latest_followup_issue or (last_pm_decision and last_pm_decision.get("action_type") == "return_to_lead"):
            lens_tags.append("returned_to_lead")
        if blocking_issues and not latest_followup_issue:
            lens_tags.append("stale_blocker")
        if not owner_id:
            lens_tags.append("unassigned")

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
                "primary_blocking_issue_id": blocking_issues[0].get("id") if blocking_issues else None,
                "returnable_issue_id": returnable_issue.get("id") if returnable_issue else None,
                "blocking_issue_titles": [issue.get("title") or issue.get("id") for issue in blocking_issues],
                "blocking_issues": [_issue_summary(issue) for issue in blocking_issues],
                "latest_pm_followup_note": latest_followup_issue.get("pm_followup_note") if latest_followup_issue else None,
                "latest_pm_followup_sent_at": latest_followup_issue.get("pm_followup_sent_at") if latest_followup_issue else None,
                "last_pm_decision": last_pm_decision,
                "lens_tags": sorted(set(lens_tags)),
                "owner_id": owner_id,
                "owner_name": owner_name,
                "task_id": task.get("id"),
                "task_name": task.get("name"),
                "workpackage_id": workpackage.get("id"),
                "workpackage_name": workpackage.get("name"),
                "designation": apparatus.get("source_designation"),
                "apparatus_type": apparatus.get("source_apparatus_type"),
                "drawing_ref": apparatus.get("source_drawing_ref") or task.get("drawing_ref"),
                "checklist_complete_count": checklist_complete_count,
                "checklist_total_count": checklist_total_count,
                "next_action": next_action,
                "ai_advisory": {
                    "mode": "draft_only",
                    "mutation_authority": "not_admitted",
                    "target_audience": "lead",
                    "brief": advisory_brief,
                },
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
    lenses = {
        "all_count": len(rows),
        "blocked_count": sum(1 for row in rows if "blocked" in row["lens_tags"]),
        "needs_pm_disposition_count": sum(1 for row in rows if "needs_pm_disposition" in row["lens_tags"]),
        "returned_to_lead_count": sum(1 for row in rows if "returned_to_lead" in row["lens_tags"]),
        "stale_blocker_count": sum(1 for row in rows if "stale_blocker" in row["lens_tags"]),
        "unassigned_count": sum(1 for row in rows if "unassigned" in row["lens_tags"]),
    }

    return {
        "summary": summary,
        "lenses": lenses,
        "rows": rows,
        "advisory": {
            "mode": "read_only",
            "ai_mutation_authority": "not_admitted",
            "recommended_focus": rows[0]["next_action"] if rows else "No apparatus workfront rows are available",
        },
    }
