from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Dict, List

from app.project_import_candidate import IMPORT_CANDIDATE_VERSION, MUTATION_AUTHORITY, load_project_import_candidate
from app.project_import_snapshot import load_project_import_admission_plan_snapshot


ADMISSION_PLAN_VERSION = "pm_import_admission_plan_read_only_v1"


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


def _warning_codes(candidate: Dict[str, Any]) -> List[str]:
    return sorted(
        str(warning.get("code"))
        for warning in candidate.get("warnings", [])
        if warning.get("code")
    )


def _shape_fingerprint(candidate: Dict[str, Any]) -> str:
    workpackage_shape = []
    for workpackage in candidate.get("workpackages", []):
        tasks = []
        for task in workpackage.get("tasks", []):
            tasks.append(
                {
                    "task_id": task.get("task_id"),
                    "source_line_id": task.get("source_line_id"),
                    "title": task.get("title"),
                    "quantity": task.get("quantity"),
                    "drawing_ref": task.get("drawing_ref"),
                    "source_ref": task.get("source_ref"),
                    "apparatus_candidate_count": len(task.get("apparatus_candidates", [])),
                }
            )
        workpackage_shape.append(
            {
                "workpackage_id": workpackage.get("workpackage_id"),
                "title": workpackage.get("title"),
                "task_count": workpackage.get("task_count"),
                "apparatus_candidate_count": workpackage.get("apparatus_candidate_count"),
                "planned_hours": workpackage.get("planned_hours"),
                "tasks": tasks,
            }
        )
    return _stable_hash(workpackage_shape)


def _idempotency_plan(candidate: Dict[str, Any], shape_fingerprint: str) -> Dict[str, Any]:
    summary = candidate.get("summary", {})
    source_freshness = candidate.get("source_freshness", {})
    components = {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "source_stat_fingerprint": source_freshness.get("aggregate_fingerprint"),
        "shape_fingerprint": shape_fingerprint,
        "workpackage_count": summary.get("workpackage_count"),
        "task_count": summary.get("task_count"),
        "apparatus_candidate_count": summary.get("apparatus_candidate_count"),
        "warning_codes": _warning_codes(candidate),
    }
    return {
        "strategy": "candidate_version_source_shape_counts",
        "components": components,
        "sample_key": f"pm-import:{_stable_hash(components)}",
        "collision_policy": "same key must be treated as a replay of the same approved candidate; changed candidate/source/shape must produce a new key",
    }


def _target_row_plan(candidate: Dict[str, Any]) -> Dict[str, Any]:
    summary = candidate.get("summary", {})
    task_count = int(summary.get("task_count") or 0)
    apparatus_count = int(summary.get("apparatus_candidate_count") or 0)
    workpackage_count = int(summary.get("workpackage_count") or 0)
    return {
        "project_rows": 1 if task_count else 0,
        "workpackage_rows": workpackage_count,
        "task_rows": task_count,
        "apparatus_rows": apparatus_count,
        "source_trace_rows": task_count + apparatus_count,
        "warning_review_rows": int(summary.get("warning_count") or 0),
        "approval_rows": 1,
        "write_authority": MUTATION_AUTHORITY,
    }


def _warning_breakdown(candidate: Dict[str, Any]) -> Dict[str, int]:
    severities = Counter(str(warning.get("severity") or "unknown") for warning in candidate.get("warnings", []))
    return dict(sorted(severities.items()))


def _no_go_checks(candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    summary = candidate.get("summary", {})
    source_freshness = candidate.get("source_freshness", {})
    warnings = candidate.get("warnings", [])
    blocker_count = int(summary.get("blocker_count") or 0)
    task_count = int(summary.get("task_count") or 0)
    warning_count = int(summary.get("warning_count") or 0)
    missing_source_count = int(source_freshness.get("missing_count") or 0)

    return [
        {
            "check_id": "candidate-has-no-blockers",
            "status": "pass" if blocker_count == 0 else "no_go",
            "message": f"{blocker_count} blocker warning(s) reported by the import candidate.",
            "required_resolution": "Resolve blocker warnings before any import mutation can be admitted.",
        },
        {
            "check_id": "candidate-has-importable-shape",
            "status": "pass" if task_count > 0 else "no_go",
            "message": f"{task_count} task row(s) and {summary.get('apparatus_candidate_count') or 0} apparatus candidate row(s) are proposed.",
            "required_resolution": "A candidate with no proposed task rows cannot be imported.",
        },
        {
            "check_id": "source-fingerprint-is-present",
            "status": "pass" if source_freshness.get("aggregate_fingerprint") else "no_go",
            "message": f"Source fingerprint: {source_freshness.get('aggregate_fingerprint') or 'missing'}.",
            "required_resolution": "Refresh the candidate from source files until a source fingerprint is available.",
        },
        {
            "check_id": "source-files-are-accounted-for",
            "status": "pass" if missing_source_count == 0 else "needs_human_acceptance",
            "message": f"{missing_source_count} source file(s) are missing or not stat-readable.",
            "required_resolution": "Resolve missing required files or explicitly accept optional missing source evidence before import.",
        },
        {
            "check_id": "warnings-reviewed-by-pm",
            "status": "pass" if warning_count == 0 else "needs_human_acceptance",
            "message": f"{warning_count} warning signal(s) must be reviewed: {', '.join(_warning_codes(candidate)) or 'none'}.",
            "required_resolution": "Record warning-code acceptance in the future approval record before import.",
        },
        {
            "check_id": "approval-record-required",
            "status": "pending_future_admission",
            "message": "No server-side approval record is admitted in this tranche.",
            "required_resolution": "A later packet must admit approval persistence before import can execute.",
        },
        {
            "check_id": "hosted-parity-required",
            "status": "pending_future_admission",
            "message": "Hosted Render/Vercel proof remains separate from this local read-only plan.",
            "required_resolution": "Prove hosted parity or explicitly approve a local-only rehearsal boundary before import.",
        },
        {
            "check_id": "mutation-path-not-admitted",
            "status": "no_go",
            "message": "This endpoint is a read-only plan and has no import mutation authority.",
            "required_resolution": "A separate packet must admit a narrow idempotent mutation before writes are possible.",
        },
    ]


def _readiness_status(no_go_checks: List[Dict[str, Any]]) -> str:
    if any(check.get("status") == "no_go" and check.get("check_id") != "mutation-path-not-admitted" for check in no_go_checks):
        return "blocked_before_admission_design"
    if any(check.get("status") == "needs_human_acceptance" for check in no_go_checks):
        return "needs_human_acceptance_before_import_packet"
    return "design_ready_write_not_admitted"


def _approval_record_contract(candidate: Dict[str, Any], shape_fingerprint: str) -> Dict[str, Any]:
    return {
        "record_type": "pm_import_candidate_approval",
        "storage_authority": "not_admitted",
        "required_fields": [
            "candidate_id",
            "candidate_version",
            "source_stat_fingerprint",
            "candidate_shape_fingerprint",
            "idempotency_key",
            "decision",
            "approved_by_actor_id",
            "approved_at_utc",
            "accepted_warning_codes",
            "accepted_no_go_overrides",
            "review_notes",
        ],
        "permitted_decisions": [
            "approve_for_import_packet",
            "return_for_revision",
            "reject_candidate",
        ],
        "minimum_expected_values": {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_version": candidate.get("candidate_version"),
            "source_stat_fingerprint": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
            "candidate_shape_fingerprint": shape_fingerprint,
            "accepted_warning_codes": _warning_codes(candidate),
        },
        "operator_attestation": "The PM must confirm the candidate shape, source fingerprint, warning acceptance, and no-go override list before any future import mutation may be admitted.",
    }


def _diff_checks(candidate: Dict[str, Any], shape_fingerprint: str) -> List[Dict[str, Any]]:
    summary = candidate.get("summary", {})
    return [
        {
            "check_id": "candidate-id-version-match",
            "compare": ["approval_record.candidate_id", "approval_record.candidate_version"],
            "expected": [candidate.get("candidate_id"), candidate.get("candidate_version")],
            "failure_action": "stop import and regenerate approval packet",
        },
        {
            "check_id": "source-stat-fingerprint-match",
            "compare": ["approval_record.source_stat_fingerprint", "current_candidate.source_freshness.aggregate_fingerprint"],
            "expected": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
            "failure_action": "stop import and refresh source review because source files changed",
        },
        {
            "check_id": "candidate-shape-fingerprint-match",
            "compare": ["approval_record.candidate_shape_fingerprint", "current_candidate.shape_fingerprint"],
            "expected": shape_fingerprint,
            "failure_action": "stop import and re-review workpackages, tasks, and apparatus",
        },
        {
            "check_id": "summary-counts-match",
            "compare": ["workpackage_count", "task_count", "apparatus_candidate_count"],
            "expected": {
                "workpackage_count": summary.get("workpackage_count"),
                "task_count": summary.get("task_count"),
                "apparatus_candidate_count": summary.get("apparatus_candidate_count"),
            },
            "failure_action": "stop import and regenerate idempotency key",
        },
        {
            "check_id": "warning-code-set-match",
            "compare": ["approval_record.accepted_warning_codes", "current_candidate.warning_codes"],
            "expected": _warning_codes(candidate),
            "failure_action": "stop import and get renewed PM warning acceptance",
        },
    ]


def build_project_import_admission_plan(candidate: Dict[str, Any]) -> Dict[str, Any]:
    shape_fingerprint = _shape_fingerprint(candidate)
    no_go_checks = _no_go_checks(candidate)
    return {
        "admission_plan_id": f"{candidate.get('candidate_id')}-admission-plan",
        "admission_plan_version": ADMISSION_PLAN_VERSION,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version") or IMPORT_CANDIDATE_VERSION,
        "review_status": "read_only_admission_design",
        "readiness_status": _readiness_status(no_go_checks),
        "mutation_authority": MUTATION_AUTHORITY,
        "candidate_shape_fingerprint": shape_fingerprint,
        "source_stat_fingerprint": (candidate.get("source_freshness") or {}).get("aggregate_fingerprint"),
        "target_row_plan": _target_row_plan(candidate),
        "warning_breakdown": _warning_breakdown(candidate),
        "approval_record_contract": _approval_record_contract(candidate, shape_fingerprint),
        "idempotency_plan": _idempotency_plan(candidate, shape_fingerprint),
        "preview_to_import_diff_checks": _diff_checks(candidate, shape_fingerprint),
        "no_go_checks": no_go_checks,
        "future_import_sequence": [
            "PM reviews import candidate warnings, source freshness, and proposed rows.",
            "A later packet admits approval persistence and records a PM approval record.",
            "The import packet re-reads the candidate and compares source, shape, count, and warning fingerprints.",
            "The import mutation rejects changed candidates and replays identical idempotency keys safely.",
            "Only accepted candidates write project, workpackage, task, apparatus, source trace, warning review, and approval rows.",
        ],
        "not_allowed_now": [
            "persist_approval_record",
            "write_supabase",
            "run_workbook_macros",
            "write_workbooks",
            "import_project_rows",
            "assign_work",
            "mutate_schedule",
            "change_status",
            "autonomous_ai_business_state_mutation",
        ],
    }


def load_project_import_admission_plan() -> Dict[str, Any]:
    snapshot_plan = load_project_import_admission_plan_snapshot()
    if snapshot_plan is not None:
        return snapshot_plan
    return build_project_import_admission_plan(load_project_import_candidate())
