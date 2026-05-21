from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import psycopg2


APP_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.project_seed_sources import clear_project_seed_cache, load_project_seed_sources


ROOT_DIR = Path(__file__).resolve().parent
DISCOVERY_DIR = ROOT_DIR / "discovery"
SAMPLE_DIR = ROOT_DIR / "sample"
WORKBOOK_PATH = Path(r"C:/Users/jjswe/Desktop/Project Miner PM Planning/Estimator R3 - Project Miner Temp Power Testing.xlsm")
PDF_PATH = Path(r"C:/Users/jjswe/Desktop/Project Miner PM Planning/Miner Temp SLD-AP-BCARRASCO.pdf")
PROJECT_ID = "pm-import-project-miner-temp-power"
EXPECTED_COUNTS = {
    "projects": 1,
    "tasks": 15,
    "apparatus": 184,
    "scopes": 0,
}
TEST_FILES = [
    "apps/mutation-seam/tests/test_project_seed_sources.py",
    "apps/mutation-seam/tests/test_workbook_seed_reads.py",
    "apps/mutation-seam/tests/test_pm_lane_seed.py",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate PM Lane 501 read-only discovery and sample artifacts.",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional UTC timestamp suffix in YYYYMMDDTHHMMSSZ format.",
    )
    return parser.parse_args()


def _utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _resolve_dsn() -> str:
    for env_name in ("LANE_501_ONBOARDING_DESIGN_ADMIN_DSN", "SEAM_DATABASE_URL", "DATABASE_URL"):
        value = os.environ.get(env_name)
        if value:
            return value
    raise RuntimeError(
        "No database DSN found. Set LANE_501_ONBOARDING_DESIGN_ADMIN_DSN, SEAM_DATABASE_URL, or DATABASE_URL."
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _statement_verb(query: str) -> str:
    stripped = query.lstrip()
    if not stripped:
        return ""
    return stripped.split(None, 1)[0].upper()


def _query_rows(
    cursor: psycopg2.extensions.cursor,
    sql_log: list[dict[str, Any]],
    name: str,
    query: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    verb = _statement_verb(query)
    sql_log.append({"name": name, "verb": verb, "query": query.strip(), "params": list(params)})
    if verb not in {"SELECT", "WITH"}:
        raise RuntimeError(f"Non-read-only SQL verb detected: {verb} in {name}")
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _query_row(
    cursor: psycopg2.extensions.cursor,
    sql_log: list[dict[str, Any]],
    name: str,
    query: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any]:
    rows = _query_rows(cursor, sql_log, name, query, params)
    return rows[0] if rows else {}


def _flatten_keys(payload: Any, prefix: str = "") -> dict[str, set[str]]:
    summary: dict[str, set[str]] = defaultdict(set)
    if isinstance(payload, dict):
        for key, value in payload.items():
            full_key = f"{prefix}.{key}" if prefix else key
            summary[full_key].add(type(value).__name__)
            nested = _flatten_keys(value, full_key)
            for nested_key, nested_types in nested.items():
                summary[nested_key].update(nested_types)
    elif isinstance(payload, list) and payload:
        for item in payload[:3]:
            nested = _flatten_keys(item, prefix)
            for nested_key, nested_types in nested.items():
                summary[nested_key].update(nested_types)
    return summary


def _sample_value(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _sample_value(value) for key, value in list(payload.items())[:4]}
    if isinstance(payload, list):
        return [_sample_value(item) for item in payload[:2]]
    return payload


def _summarize_json_rows(rows: list[dict[str, Any]], json_field: str) -> dict[str, Any]:
    samples = [row.get(json_field) for row in rows if row.get(json_field) is not None]
    key_types: dict[str, list[str]] = {}
    merged = defaultdict(set)
    for sample in samples[:5]:
        for key, types in _flatten_keys(sample).items():
            merged[key].update(types)
    for key, types in merged.items():
        key_types[key] = sorted(types)
    return {
        "row_count_sampled": len(samples[:5]),
        "key_types": key_types,
        "example": _sample_value(samples[0]) if samples else None,
    }


def _extract_suffix(identifier: str, marker: str) -> str:
    match = re.search(rf"-{re.escape(marker)}-(\d+)$", identifier)
    if match:
        return match.group(1)
    return identifier.rsplit("-", 1)[-1]


def _derive_scope_id(project_id: str, workpackage_id: str) -> str:
    suffix = _extract_suffix(workpackage_id, "wp")
    return f"{project_id}-scope-{suffix}"


def _load_phase_0_data(dsn: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sql_log: list[dict[str, Any]] = []
    conn = psycopg2.connect(dsn)
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cursor:
            migration_state = _query_row(
                cursor,
                sql_log,
                "migration_016_state",
                """
                SELECT
                    EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'seam'
                          AND table_name = 'apparatus'
                          AND column_name = 'scope_id'
                          AND data_type = 'text'
                          AND is_nullable = 'YES'
                    ) AS scope_id_text_nullable,
                    EXISTS (
                        SELECT 1
                        FROM pg_constraint c
                        JOIN pg_class source_table ON source_table.oid = c.conrelid
                        JOIN pg_namespace source_ns ON source_ns.oid = source_table.relnamespace
                        JOIN pg_class target_table ON target_table.oid = c.confrelid
                        JOIN pg_namespace target_ns ON target_ns.oid = target_table.relnamespace
                        WHERE c.contype = 'f'
                          AND source_ns.nspname = 'seam'
                          AND source_table.relname = 'apparatus'
                          AND c.conname = 'apparatus_scope_id_fkey'
                          AND target_ns.nspname = 'seam'
                          AND target_table.relname = 'scopes'
                    ) AS has_scope_fk,
                    EXISTS (
                        SELECT 1
                        FROM pg_indexes
                        WHERE schemaname = 'seam'
                          AND tablename = 'apparatus'
                          AND indexname = 'apparatus_scope_id_idx'
                    ) AS has_scope_idx,
                    has_table_privilege('pm', 'seam.projects', 'SELECT,INSERT,UPDATE') AS pm_projects_siu,
                    has_table_privilege('pm', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS pm_tasks_siu,
                    has_table_privilege('pm', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS pm_apparatus_siu,
                    has_table_privilege('operations', 'seam.projects', 'SELECT,INSERT,UPDATE') AS operations_projects_siu,
                    has_table_privilege('operations', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS operations_tasks_siu,
                    has_table_privilege('operations', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS operations_apparatus_siu,
                    has_table_privilege('anon', 'seam.projects', 'SELECT,INSERT,UPDATE') AS anon_projects_siu,
                    has_table_privilege('anon', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS anon_tasks_siu,
                    has_table_privilege('anon', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS anon_apparatus_siu,
                    has_table_privilege('authenticated', 'seam.projects', 'SELECT,INSERT,UPDATE') AS authenticated_projects_siu,
                    has_table_privilege('authenticated', 'seam.tasks', 'SELECT,INSERT,UPDATE') AS authenticated_tasks_siu,
                    has_table_privilege('authenticated', 'seam.apparatus', 'SELECT,INSERT,UPDATE') AS authenticated_apparatus_siu
                """,
            )

            row_counts = _query_row(
                cursor,
                sql_log,
                "row_counts",
                """
                SELECT
                    (SELECT count(*) FROM seam.projects) AS projects,
                    (SELECT count(*) FROM seam.tasks) AS tasks,
                    (SELECT count(*) FROM seam.apparatus) AS apparatus,
                    (SELECT count(*) FROM seam.scopes) AS scopes
                """,
            )

            project_rows = _query_rows(
                cursor,
                sql_log,
                "project_rows",
                "SELECT id, data FROM seam.projects ORDER BY id",
            )
            task_rows = _query_rows(
                cursor,
                sql_log,
                "task_rows",
                "SELECT id, workpackage_id, status, data FROM seam.tasks ORDER BY id",
            )
            apparatus_rows = _query_rows(
                cursor,
                sql_log,
                "apparatus_rows",
                "SELECT id, scope_id, data FROM seam.apparatus ORDER BY id",
            )
            workpackage_rows = _query_rows(
                cursor,
                sql_log,
                "workpackage_rows",
                "SELECT id, data FROM seam.workpackages ORDER BY id",
            )
            apparatus_key_probe = _query_row(
                cursor,
                sql_log,
                "apparatus_key_probe",
                """
                SELECT
                    count(*) FILTER (WHERE data ? 'source_row') AS has_source_row,
                    count(*) FILTER (WHERE data ? 'source_line_id') AS has_source_line_id,
                    count(*) FILTER (WHERE data ? 'source_designation') AS has_source_designation,
                    count(*) FILTER (WHERE data ? 'source_apparatus_type') AS has_source_apparatus_type,
                    count(*) FILTER (WHERE data ? 'source_drawing_ref') AS has_source_drawing_ref,
                    count(*) FILTER (WHERE data ? 'source_candidate_apparatus_id') AS has_source_candidate_apparatus_id,
                    count(*) FILTER (WHERE data ? 'task_id') AS has_task_id,
                    count(*) FILTER (WHERE data ? 'name') AS has_name
                FROM seam.apparatus
                """,
            )
            task_scope_probe = _query_row(
                cursor,
                sql_log,
                "task_scope_probe",
                """
                SELECT
                    count(*) FILTER (WHERE data ? 'scope_id') AS task_data_scope_id,
                    count(*) FILTER (WHERE data ? 'scope_sheet') AS task_data_scope_sheet,
                    count(*) FILTER (WHERE data ? 'scope_name') AS task_data_scope_name,
                    count(*) FILTER (WHERE data ? 'scope_reference') AS task_data_scope_reference,
                    count(*) FILTER (WHERE data ? 'source_line_id') AS task_data_source_line_id,
                    count(*) FILTER (WHERE data ? 'source_designation') AS task_data_source_designation,
                    count(*) FILTER (WHERE data ? 'source_apparatus_type') AS task_data_source_apparatus_type
                FROM seam.tasks
                """,
            )
    finally:
        conn.close()

    phase_0 = {
        "migration_016_state": migration_state,
        "row_counts": row_counts,
        "project_rows": project_rows,
        "task_rows": task_rows,
        "apparatus_rows": apparatus_rows,
        "workpackage_rows": workpackage_rows,
        "project_data_summary": _summarize_json_rows(project_rows[:1], "data"),
        "task_data_summary": _summarize_json_rows(task_rows[:5], "data"),
        "apparatus_data_summary": _summarize_json_rows(apparatus_rows[:5], "data"),
        "workpackage_data_summary": _summarize_json_rows(workpackage_rows[:5], "data"),
        "apparatus_key_probe": apparatus_key_probe,
        "task_scope_probe": task_scope_probe,
    }
    return phase_0, sql_log


def _run_extractor() -> dict[str, Any]:
    clear_project_seed_cache()
    return load_project_seed_sources(str(WORKBOOK_PATH), str(PDF_PATH))


def _run_test_subset() -> dict[str, Any]:
    command = [str(REPO_ROOT / ".venv" / "Scripts" / "pytest.exe"), *TEST_FILES]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _key_stats(existing_keys: list[str | None], extractor_keys: list[str | None]) -> dict[str, Any]:
    existing_filtered = [value for value in existing_keys if value]
    extractor_filtered = [value for value in extractor_keys if value]
    existing_counter = Counter(existing_filtered)
    extractor_counter = Counter(extractor_filtered)
    existing_duplicates = sum(count - 1 for count in existing_counter.values() if count > 1)
    extractor_duplicates = sum(count - 1 for count in extractor_counter.values() if count > 1)
    return {
        "existing_non_null": len(existing_filtered),
        "extractor_non_null": len(extractor_filtered),
        "existing_duplicate_entries": existing_duplicates,
        "extractor_duplicate_entries": extractor_duplicates,
        "expected_collision_rate": {
            "existing": round(existing_duplicates / len(existing_filtered), 4) if existing_filtered else 0.0,
            "extractor": round(extractor_duplicates / len(extractor_filtered), 4) if extractor_filtered else 0.0,
        },
    }


def _candidate_key_entries(phase_0: dict[str, Any], extractor_output: dict[str, Any]) -> list[dict[str, Any]]:
    apparatus_rows = phase_0["apparatus_rows"]
    candidates = extractor_output["expanded_apparatus_candidates"]

    return [
        {
            "field_name": "source_candidate_apparatus_id",
            "jsonb_field": "data.source_candidate_apparatus_id",
            "extractor_field": "expanded_apparatus_candidates[].candidate_id",
            "uniqueness_assumption": "Exact candidate identifier survives unchanged from extractor to imported apparatus row.",
            "collision_stats": _key_stats(
                [row["data"].get("source_candidate_apparatus_id") for row in apparatus_rows],
                [candidate.get("candidate_id") for candidate in candidates],
            ),
        },
        {
            "field_name": "source_line_id_plus_name",
            "jsonb_field": "data.source_line_id + data.name",
            "extractor_field": "expanded_apparatus_candidates[].line_id + display_name",
            "uniqueness_assumption": "Line identity plus expanded display name stays unique within one workbook version.",
            "collision_stats": _key_stats(
                [f"{row['data'].get('source_line_id')}|{row['data'].get('name')}" for row in apparatus_rows],
                [f"{candidate.get('line_id')}|{candidate.get('display_name')}" for candidate in candidates],
            ),
        },
        {
            "field_name": "source_row_designation_type_name",
            "jsonb_field": "data.source_row + data.source_designation + data.source_apparatus_type + data.name",
            "extractor_field": "expanded_apparatus_candidates[].source_row + designation + apparatus_type + display_name",
            "uniqueness_assumption": "Workbook row, designation, apparatus type, and expanded display name together disambiguate repeated quantities.",
            "collision_stats": _key_stats(
                [
                    f"{row['data'].get('source_row')}|{row['data'].get('source_designation')}|{row['data'].get('source_apparatus_type')}|{row['data'].get('name')}"
                    for row in apparatus_rows
                ],
                [
                    f"{candidate.get('source_row')}|{candidate.get('designation')}|{candidate.get('apparatus_type')}|{candidate.get('display_name')}"
                    for candidate in candidates
                ],
            ),
        },
        {
            "field_name": "source_row_designation_type_only",
            "jsonb_field": "data.source_row + data.source_designation + data.source_apparatus_type",
            "extractor_field": "expanded_apparatus_candidates[].source_row + designation + apparatus_type",
            "uniqueness_assumption": "Weak fallback only; repeated quantity rows collide because the same source row expands to multiple apparatus rows.",
            "collision_stats": _key_stats(
                [
                    f"{row['data'].get('source_row')}|{row['data'].get('source_designation')}|{row['data'].get('source_apparatus_type')}"
                    for row in apparatus_rows
                ],
                [
                    f"{candidate.get('source_row')}|{candidate.get('designation')}|{candidate.get('apparatus_type')}"
                    for candidate in candidates
                ],
            ),
        },
    ]


def _build_identifier_scheme(phase_0: dict[str, Any]) -> dict[str, Any]:
    project_ids = [row["id"] for row in phase_0["project_rows"]]
    task_ids = [row["id"] for row in phase_0["task_rows"][:5]]
    apparatus_ids = [row["id"] for row in phase_0["apparatus_rows"][:5]]
    workpackage_ids = [row["id"] for row in phase_0["workpackage_rows"][:5]]
    project_id = project_ids[0]
    return {
        "project_ids": project_ids,
        "task_id_samples": task_ids,
        "apparatus_id_samples": apparatus_ids,
        "workpackage_id_samples": workpackage_ids,
        "documented_patterns": {
            "project": r"^pm-import-project-[a-z0-9-]+$",
            "task": r"^pm-import-project-[a-z0-9-]+-task-\d{4}$",
            "apparatus": r"^pm-import-project-[a-z0-9-]+-app-\d{4}$",
            "workpackage": r"^pm-import-project-[a-z0-9-]+-wp-\d{3}$",
            "proposed_scope": rf"^{re.escape(project_id)}-scope-\d{{3}}$",
        },
        "proposed_scope_examples": [
            _derive_scope_id(project_id, row["id"])
            for row in phase_0["workpackage_rows"][:3]
        ],
    }


def _build_scope_records(phase_0: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    scopes: list[dict[str, Any]] = []
    mapping: dict[str, str] = {}
    project_id = phase_0["project_rows"][0]["id"]
    for row in phase_0["workpackage_rows"]:
        workpackage_id = row["id"]
        data = row["data"]
        scope_id = _derive_scope_id(project_id, workpackage_id)
        mapping[workpackage_id] = scope_id
        section_name = data.get("source_section") if data.get("source_section") is not None else data.get("name")
        scopes.append(
            {
                "id": scope_id,
                "project_id": project_id,
                "name": f"Section {section_name}",
                "scope_type": "flat_quote_section_rollup",
                "total_hours": data.get("planned_hours"),
                "quoted_amount": None,
                "multiplier": None,
                "source_section": data.get("source_section"),
                "derivation_basis": {
                    "strategy": "existing_workpackage_section_rollup",
                    "source_workpackage_id": workpackage_id,
                    "source_candidate_workpackage_id": data.get("source_candidate_workpackage_id"),
                    "source_scope_sheet": data.get("source_scope_sheet"),
                    "source_drawing_refs": data.get("source_drawing_refs", []),
                    "task_count": data.get("task_count"),
                    "apparatus_count": data.get("apparatus_count"),
                },
            }
        )
    return scopes, mapping


def _reconcile(
    phase_0: dict[str, Any],
    extractor_output: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    project_id = phase_0["project_rows"][0]["id"]
    tasks_by_id = {row["id"]: row for row in phase_0["task_rows"]}
    apparatus_rows = phase_0["apparatus_rows"]
    scopes, workpackage_to_scope = _build_scope_records(phase_0)

    existing_by_candidate_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    existing_by_line_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    existing_by_row_designation_type_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in apparatus_rows:
        data = row["data"]
        candidate_id = data.get("source_candidate_apparatus_id")
        if candidate_id:
            existing_by_candidate_id[candidate_id].append(row)
        line_name_key = f"{data.get('source_line_id')}|{data.get('name')}"
        existing_by_line_name[line_name_key].append(row)
        detailed_key = (
            f"{data.get('source_row')}|{data.get('source_designation')}|"
            f"{data.get('source_apparatus_type')}|{data.get('name')}"
        )
        existing_by_row_designation_type_name[detailed_key].append(row)

    matched: list[dict[str, Any]] = []
    unmatched_extractor: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    matched_existing_ids: set[str] = set()

    for candidate in extractor_output["expanded_apparatus_candidates"]:
        candidate_id = candidate.get("candidate_id")
        primary_matches = existing_by_candidate_id.get(candidate_id, [])
        line_name_key = f"{candidate.get('line_id')}|{candidate.get('display_name')}"
        detailed_key = (
            f"{candidate.get('source_row')}|{candidate.get('designation')}|"
            f"{candidate.get('apparatus_type')}|{candidate.get('display_name')}"
        )
        fallback_matches = existing_by_line_name.get(line_name_key, [])
        detailed_matches = existing_by_row_designation_type_name.get(detailed_key, [])

        chosen_row: dict[str, Any] | None = None
        matched_by = None
        if len(primary_matches) == 1:
            chosen_row = primary_matches[0]
            matched_by = "source_candidate_apparatus_id"
        elif len(primary_matches) > 1:
            conflicts.append(
                {
                    "extractor_candidate_id": candidate_id,
                    "reason": "multiple_existing_rows_for_source_candidate_apparatus_id",
                    "existing_row_ids": [row["id"] for row in primary_matches],
                }
            )
            continue
        elif len(fallback_matches) == 1:
            chosen_row = fallback_matches[0]
            matched_by = "source_line_id_plus_name"
        elif len(fallback_matches) > 1:
            conflicts.append(
                {
                    "extractor_candidate_id": candidate_id,
                    "reason": "multiple_existing_rows_for_source_line_id_plus_name",
                    "existing_row_ids": [row["id"] for row in fallback_matches],
                }
            )
            continue
        elif len(detailed_matches) == 1:
            chosen_row = detailed_matches[0]
            matched_by = "source_row_designation_type_name"
        elif len(detailed_matches) > 1:
            conflicts.append(
                {
                    "extractor_candidate_id": candidate_id,
                    "reason": "multiple_existing_rows_for_source_row_designation_type_name",
                    "existing_row_ids": [row["id"] for row in detailed_matches],
                }
            )
            continue

        if chosen_row is None:
            unmatched_extractor.append(
                {
                    "extractor_candidate_id": candidate_id,
                    "display_name": candidate.get("display_name"),
                    "line_id": candidate.get("line_id"),
                    "source_row": candidate.get("source_row"),
                    "designation": candidate.get("designation"),
                    "apparatus_type": candidate.get("apparatus_type"),
                    "drawing_ref": candidate.get("drawing_ref"),
                }
            )
            continue

        if chosen_row["id"] in matched_existing_ids:
            conflicts.append(
                {
                    "extractor_candidate_id": candidate_id,
                    "reason": "existing_row_matched_multiple_extractor_candidates",
                    "existing_row_ids": [chosen_row["id"]],
                }
            )
            continue

        matched_existing_ids.add(chosen_row["id"])
        existing_data = chosen_row["data"]
        task_id = existing_data.get("task_id")
        task_row = tasks_by_id.get(task_id)
        workpackage_id = task_row.get("workpackage_id") if task_row else None
        scope_id = workpackage_to_scope.get(workpackage_id)
        matched.append(
            {
                "id": chosen_row["id"],
                "scope_id": scope_id,
                "match_status": "matched",
                "match_confidence": "confident" if matched_by == "source_candidate_apparatus_id" else "probable",
                "matched_by": matched_by,
                "match_keys": {
                    "source_candidate_apparatus_id": existing_data.get("source_candidate_apparatus_id"),
                    "source_line_id": existing_data.get("source_line_id"),
                    "source_row": existing_data.get("source_row"),
                    "source_designation": existing_data.get("source_designation"),
                    "source_apparatus_type": existing_data.get("source_apparatus_type"),
                    "display_name": existing_data.get("name"),
                },
                "existing_row_ref": {
                    "task_id": task_id,
                    "workpackage_id": workpackage_id,
                    "status": chosen_row.get("scope_id"),
                    "source_candidate_apparatus_id": existing_data.get("source_candidate_apparatus_id"),
                },
                "extractor_candidate": {
                    "candidate_id": candidate.get("candidate_id"),
                    "line_id": candidate.get("line_id"),
                    "display_name": candidate.get("display_name"),
                    "source_row": candidate.get("source_row"),
                    "designation": candidate.get("designation"),
                    "apparatus_type": candidate.get("apparatus_type"),
                    "drawing_ref": candidate.get("drawing_ref"),
                    "section": candidate.get("section"),
                },
                "source_traceability": {
                    "workbook_path": str(WORKBOOK_PATH),
                    "source_sheet": extractor_output.get("source_sheet"),
                    "source_format": extractor_output.get("source_format"),
                    "scope_sheet": candidate.get("scope_sheet"),
                    "source_row": candidate.get("source_row"),
                    "drawing_ref": candidate.get("drawing_ref"),
                },
            }
        )

    unmatched_existing = []
    for row in apparatus_rows:
        if row["id"] in matched_existing_ids:
            continue
        data = row["data"]
        unmatched_existing.append(
            {
                "id": row["id"],
                "display_name": data.get("name"),
                "task_id": data.get("task_id"),
                "source_candidate_apparatus_id": data.get("source_candidate_apparatus_id"),
                "source_line_id": data.get("source_line_id"),
                "source_row": data.get("source_row"),
                "source_designation": data.get("source_designation"),
                "source_apparatus_type": data.get("source_apparatus_type"),
            }
        )

    report_body = {
        "algorithm_version": "lane_501_hybrid_review_v1",
        "project_id": project_id,
        "generated_from": {
            "workbook_path": str(WORKBOOK_PATH),
            "source_format": extractor_output.get("source_format"),
            "source_sheet": extractor_output.get("source_sheet"),
        },
        "outcome_counts": {
            "matched": len(matched),
            "unmatched_existing": len(unmatched_existing),
            "unmatched_extractor": len(unmatched_extractor),
            "conflicting": len(conflicts),
        },
        "matched": matched,
        "unmatched_existing": unmatched_existing,
        "unmatched_extractor": unmatched_extractor,
        "conflicting": conflicts,
    }
    report = {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "report_content_sha256": _sha256(report_body),
        "report_body": report_body,
        "admission_ready": len(conflicts) == 0,
        "admission_ready_reason": (
            "ready_for_explicit_operator_admission_after_report_hash_review"
            if len(conflicts) == 0
            else "not_ready_until_conflicts_are_resolved"
        ),
    }

    intermediate = {
        "$schema": "./contract/intermediate_ingest_contract_v1.schema.json",
        "contract_version": "v1",
        "source_provenance": {
            "extractor_version": "app.project_seed_sources.load_project_seed_sources",
            "workbook_path": str(WORKBOOK_PATH),
            "workbook_sheets_used": ([extractor_output.get("source_sheet")] if extractor_output.get("source_sheet") else [])
            + extractor_output.get("scope_sheets", []),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "source_format": extractor_output.get("source_format"),
            "source_sheet": extractor_output.get("source_sheet"),
            "scope_sheets": extractor_output.get("scope_sheets", []),
            "sld_pdf_path": str(PDF_PATH),
            "topology_counts": extractor_output.get("topology_counts", {}),
            "candidate_count": len(extractor_output.get("expanded_apparatus_candidates", [])),
        },
        "project": {
            "id": project_id,
            "name": phase_0["project_rows"][0]["data"].get("name"),
            "data": phase_0["project_rows"][0]["data"],
        },
        "scopes": scopes,
        "apparatus": matched + [
            {
                "id": None,
                "scope_id": None,
                "match_status": "unmatched_extractor",
                "match_confidence": "none",
                "matched_by": None,
                "match_keys": {
                    "source_candidate_apparatus_id": row.get("extractor_candidate_id"),
                    "source_line_id": row.get("line_id"),
                    "source_row": row.get("source_row"),
                    "source_designation": row.get("designation"),
                    "source_apparatus_type": row.get("apparatus_type"),
                    "display_name": row.get("display_name"),
                },
                "existing_row_ref": None,
                "extractor_candidate": row,
                "source_traceability": {
                    "workbook_path": str(WORKBOOK_PATH),
                    "source_sheet": extractor_output.get("source_sheet"),
                    "source_format": extractor_output.get("source_format"),
                    "scope_sheet": None,
                    "source_row": row.get("source_row"),
                    "drawing_ref": row.get("drawing_ref"),
                },
            }
            for row in unmatched_extractor
        ],
        "reconciliation": {
            "algorithm_version": report["report_body"]["algorithm_version"],
            "report_content_sha256": report["report_content_sha256"],
            "outcome_counts": report["report_body"]["outcome_counts"],
        },
    }
    return report, intermediate


def _build_discovery_payload(
    phase_0: dict[str, Any],
    extractor_output: dict[str, Any],
    test_result: dict[str, Any],
    sql_log: list[dict[str, Any]],
) -> dict[str, Any]:
    identifier_scheme = _build_identifier_scheme(phase_0)
    match_key_candidates = _candidate_key_entries(phase_0, extractor_output)
    row_counts_match = {
        key: phase_0["row_counts"].get(key) == expected
        for key, expected in EXPECTED_COUNTS.items()
    }
    no_write_verification = {
        "statement_count": len(sql_log),
        "non_select_statements": [entry for entry in sql_log if entry["verb"] not in {"SELECT", "WITH"}],
        "passed": all(entry["verb"] in {"SELECT", "WITH"} for entry in sql_log),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase_0_findings": {
            "migration_016_clean_state": phase_0["migration_016_state"],
            "production_row_count_sanity": {
                "actual": phase_0["row_counts"],
                "expected": EXPECTED_COUNTS,
                "matches_expected": row_counts_match,
            },
            "seam_projects_data_jsonb_sampling": {
                "sample_rows": phase_0["project_rows"],
                "summary": phase_0["project_data_summary"],
            },
            "seam_tasks_data_jsonb_sampling": {
                "sample_rows": phase_0["task_rows"][:5],
                "summary": phase_0["task_data_summary"],
                "scope_probe": phase_0["task_scope_probe"],
            },
            "seam_apparatus_data_jsonb_sampling": {
                "sample_rows": phase_0["apparatus_rows"][:5],
                "summary": phase_0["apparatus_data_summary"],
                "key_probe": phase_0["apparatus_key_probe"],
            },
            "extractor_rerun": {
                "source_format": extractor_output.get("source_format"),
                "source_sheet": extractor_output.get("source_sheet"),
                "scope_sheets": extractor_output.get("scope_sheets", []),
                "scope_count": extractor_output.get("scope_count"),
                "line_item_count": len(extractor_output.get("line_items", [])),
                "apparatus_candidate_count": len(extractor_output.get("expanded_apparatus_candidates", [])),
                "metadata": extractor_output.get("metadata", {}),
            },
            "lane_029_extractor_compatibility": test_result,
            "match_key_candidate_enumeration": match_key_candidates,
            "identifier_scheme_verification": identifier_scheme,
            "existing_workpackage_sampling": {
                "sample_rows": phase_0["workpackage_rows"][:5],
                "summary": phase_0["workpackage_data_summary"],
            },
            "no_write_verification": no_write_verification,
        }
    }


def _format_markdown_report(report: dict[str, Any]) -> str:
    body = report["report_body"]

    def _examples(rows: list[dict[str, Any]], limit: int = 3) -> str:
        if not rows:
            return "None."
        lines = []
        for row in rows[:limit]:
            lines.append(f"- {json.dumps(row, default=_json_default, sort_keys=True)}")
        return "\n".join(lines)

    return "\n".join(
        [
            "# Miner Temp Power Testing Reconciliation Report",
            "",
            f"Generated: {report['report_generated_at']}",
            f"Report Content SHA256: `{report['report_content_sha256']}`",
            "",
            "## Summary",
            "",
            f"- Matched rows: {body['outcome_counts']['matched']}",
            f"- Unmatched existing rows: {body['outcome_counts']['unmatched_existing']}",
            f"- Unmatched extractor candidates: {body['outcome_counts']['unmatched_extractor']}",
            f"- Conflicting rows: {body['outcome_counts']['conflicting']}",
            f"- Verdict: {'ready' if report['admission_ready'] else 'not-ready'}",
            f"- Rationale: {report['admission_ready_reason']}",
            "",
            "## Matched Rows",
            "",
            _examples(body["matched"]),
            "",
            "## Unmatched Existing Rows",
            "",
            _examples(body["unmatched_existing"]),
            "",
            "## Unmatched Extractor Candidates",
            "",
            _examples(body["unmatched_extractor"]),
            "",
            "## Conflicting Rows",
            "",
            _examples(body["conflicting"], limit=20),
            "",
            "## Summary Verdict",
            "",
            (
                "Ready for Lane 502 admission review because the current sample produced zero conflicts; "
                "Lane 502 still requires an explicit operator admission phrase bound to the report content hash above."
                if report["admission_ready"]
                else "Not ready for Lane 502 admission because one or more conflicts must be resolved first."
            ),
            "",
        ]
    )


def main() -> int:
    args = _parse_args()
    timestamp = args.timestamp or _utc_now_compact()
    dsn = _resolve_dsn()

    phase_0, sql_log = _load_phase_0_data(dsn)
    extractor_output = _run_extractor()
    test_result = _run_test_subset()
    discovery_payload = _build_discovery_payload(phase_0, extractor_output, test_result, sql_log)
    report, intermediate = _reconcile(phase_0, extractor_output)

    extractor_path = DISCOVERY_DIR / f"extractor_output_r3_temp_power_{timestamp}.json"
    data_samples_path = DISCOVERY_DIR / f"data_jsonb_samples_{timestamp}.json"
    sql_log_path = DISCOVERY_DIR / f"no_write_sql_log_{timestamp}.txt"
    intermediate_path = SAMPLE_DIR / f"miner_temp_power_testing_intermediate_{timestamp}.json"
    reconciliation_json_path = SAMPLE_DIR / f"miner_temp_power_testing_reconciliation_{timestamp}.json"
    reconciliation_md_path = SAMPLE_DIR / f"miner_temp_power_testing_reconciliation_{timestamp}.md"

    _write_json(extractor_path, extractor_output)
    _write_json(data_samples_path, discovery_payload)
    _write_text(
        sql_log_path,
        "\n\n".join(
            [
                f"[{index:02d}] {entry['name']} VERB={entry['verb']} PARAMS={json.dumps(entry['params'], default=_json_default)}\n{entry['query']}"
                for index, entry in enumerate(sql_log, start=1)
            ]
        )
        + "\n",
    )
    _write_json(intermediate_path, intermediate)
    _write_json(reconciliation_json_path, report)
    _write_text(reconciliation_md_path, _format_markdown_report(report))

    summary = {
        "timestamp": timestamp,
        "extractor_output": extractor_path.as_posix(),
        "data_samples": data_samples_path.as_posix(),
        "sql_log": sql_log_path.as_posix(),
        "intermediate": intermediate_path.as_posix(),
        "reconciliation_json": reconciliation_json_path.as_posix(),
        "reconciliation_md": reconciliation_md_path.as_posix(),
        "row_counts": phase_0["row_counts"],
        "test_passed": test_result["passed"],
        "report_content_sha256": report["report_content_sha256"],
    }
    print(json.dumps(summary, indent=2, default=_json_default))
    return 0 if test_result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())