"""Local worker helpers for processing control-plane queue items."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
import re
import subprocess
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


_REQUIRED_WORKER_TABLES = (
    "mcp_local_action_queue",
    "mcp_job_runs",
)

_REQUIRED_RENDER_TABLES = (
    "image_assets",
    "image_guide_links",
    "study_content",
    "mcp_validation_artifacts",
)

_IMG_TAG_PATTERN = re.compile(r"\{\{IMG:\s*([a-z0-9][a-z0-9\-]*)", re.IGNORECASE)

_DEFAULT_ALLOWED_READ_ROOTS = (
    "Development/Agent-Inbox",
    "Development/Control-Plane",
    "Development/staging",
    "Development/Validation-Runs",
    "Visual-Assets/Guide-Images",
)

_DEFAULT_ALLOWED_WRITE_ROOTS = (
    "Development/Validation-Runs",
    "Development/Agent-Logs",
)

_DEFAULT_ALLOWED_GIT_REPOS = {
    "apex-power-ops-platform": ".",
}

_BRIDGE_CONFIG_PATH = Path("Development") / "Control-Plane" / "chatgpt-secure-bridge-config.local.json"
_TASK_PACKET_ROOT = Path("Development") / "Agent-Inbox"
_MAX_READ_LINES = 400
_MAX_SEARCH_RESULTS = 50
_MAX_AUTHORING_BYTES = 2_000_000
_AUTHORING_EXECUTION_ALLOWED_PACKET_STATUSES = {"approved_for_local_action", "awaiting_results"}


@dataclass(frozen=True)
class QueuedJob:
    job_id: str
    action_type: str
    task_id: str | None
    subject_type: str
    subject_id: str
    requested_by: str
    request_payload: dict[str, Any]
    priority: str


def _load_bridge_config(study_root: Path) -> dict[str, Any]:
    config = {
        "allowed_read_roots": list(_DEFAULT_ALLOWED_READ_ROOTS),
        "allowed_write_roots": list(_DEFAULT_ALLOWED_WRITE_ROOTS),
        "allowed_git_repos": dict(_DEFAULT_ALLOWED_GIT_REPOS),
    }

    config_path = study_root / _BRIDGE_CONFIG_PATH
    if not config_path.exists():
        return config

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return config

    if isinstance(payload.get("allowed_read_roots"), list):
        config["allowed_read_roots"] = [str(item) for item in payload["allowed_read_roots"] if str(item).strip()]
    if isinstance(payload.get("allowed_write_roots"), list):
        config["allowed_write_roots"] = [str(item) for item in payload["allowed_write_roots"] if str(item).strip()]
    if isinstance(payload.get("allowed_git_repos"), dict):
        config["allowed_git_repos"] = {
            str(key): str(value)
            for key, value in payload["allowed_git_repos"].items()
            if str(key).strip() and str(value).strip()
        }
    return config


def _is_within_root(candidate: Path, root: Path) -> bool:
    return candidate == root or root in candidate.parents


def _resolve_allowed_path(
    study_root: Path,
    relative_path: str,
    *,
    allowed_roots: list[str],
    require_exists: bool,
    expected_kind: str,
) -> Path:
    raw_path = str(relative_path or "").strip().replace("\\", "/")
    if not raw_path:
        raise ValueError("path is required")

    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        raise ValueError("absolute paths are not allowed")

    candidate = (study_root / path_obj).resolve(strict=False)
    resolved_roots = [(study_root / Path(item)).resolve(strict=False) for item in allowed_roots]
    if not any(_is_within_root(candidate, root) for root in resolved_roots):
        raise ValueError("path is outside the secure bridge allowlist")

    if require_exists and not candidate.exists():
        raise FileNotFoundError(f"path not found: {raw_path}")

    if expected_kind == "file" and candidate.exists() and not candidate.is_file():
        raise ValueError("expected a file path")
    if expected_kind == "dir" and candidate.exists() and not candidate.is_dir():
        raise ValueError("expected a directory path")
    return candidate


def _resolve_git_repo_path(study_root: Path, repo_name: str) -> Path:
    config = _load_bridge_config(study_root)
    repo_map = config["allowed_git_repos"]
    if repo_name not in repo_map:
        raise ValueError("repo is not in the secure bridge git allowlist")

    repo_value = Path(repo_map[repo_name])
    repo_path = repo_value if repo_value.is_absolute() else (study_root / repo_value)
    repo_path = repo_path.resolve(strict=False)
    if not repo_path.exists() or not repo_path.is_dir():
        raise FileNotFoundError(f"git repo path not found: {repo_path}")
    return repo_path


def _result_payload(job: QueuedJob, runner_id: str, action_result: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "job_id": job.job_id,
        "action_type": job.action_type,
        "subject_type": job.subject_type,
        "subject_id": job.subject_id,
        "runner_id": runner_id,
        "processed_at": now_iso(),
    }
    payload.update(action_result)
    return payload


def _list_workspace_directory(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    config = _load_bridge_config(study_root)
    target_path = _resolve_allowed_path(
        study_root,
        str(job.request_payload.get("path") or ""),
        allowed_roots=config["allowed_read_roots"],
        require_exists=True,
        expected_kind="dir",
    )
    entries = [
        {"name": child.name, "kind": "dir" if child.is_dir() else "file"}
        for child in sorted(target_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    ]
    result_json = _result_payload(
        job,
        runner_id,
        {
            "path": str(target_path.relative_to(study_root)).replace("\\", "/"),
            "entries": entries,
        },
    )
    return {
        "result_summary": f"listed {len(entries)} entries in {result_json['path']}",
        "result_json": result_json,
        "evidence_artifacts": [],
    }


def _read_workspace_file(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    config = _load_bridge_config(study_root)
    target_path = _resolve_allowed_path(
        study_root,
        str(job.request_payload.get("path") or job.subject_id or ""),
        allowed_roots=config["allowed_read_roots"],
        require_exists=True,
        expected_kind="file",
    )
    start_line = max(1, int(job.request_payload.get("start_line") or 1))
    requested_end = int(job.request_payload.get("end_line") or start_line + 79)
    end_line = max(start_line, min(requested_end, start_line + _MAX_READ_LINES - 1))
    lines = target_path.read_text(encoding="utf-8").splitlines()
    excerpt = lines[start_line - 1:end_line]
    result_json = _result_payload(
        job,
        runner_id,
        {
            "path": str(target_path.relative_to(study_root)).replace("\\", "/"),
            "start_line": start_line,
            "end_line": min(end_line, len(lines)),
            "line_count": len(lines),
            "content": "\n".join(excerpt),
        },
    )
    return {
        "result_summary": f"read lines {result_json['start_line']}-{result_json['end_line']} from {result_json['path']}",
        "result_json": result_json,
        "evidence_artifacts": [],
    }


def _search_workspace(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    config = _load_bridge_config(study_root)
    query = str(job.request_payload.get("query") or "").strip()
    if not query:
        raise ValueError("search query is required")

    root_hint = str(job.request_payload.get("path") or "").strip()
    if root_hint:
        search_roots = [
            _resolve_allowed_path(
                study_root,
                root_hint,
                allowed_roots=config["allowed_read_roots"],
                require_exists=True,
                expected_kind="dir",
            )
        ]
    else:
        search_roots = [
            _resolve_allowed_path(
                study_root,
                item,
                allowed_roots=config["allowed_read_roots"],
                require_exists=True,
                expected_kind="dir",
            )
            for item in config["allowed_read_roots"]
        ]

    include_globs = job.request_payload.get("include_globs") or ["**/*.md", "**/*.json", "**/*.txt", "**/*.py", "**/*.sql", "**/*.ps1"]
    include_globs = [str(item) for item in include_globs]
    case_sensitive = bool(job.request_payload.get("case_sensitive") or False)
    max_results = max(1, min(int(job.request_payload.get("max_results") or 20), _MAX_SEARCH_RESULTS))

    matches: list[dict[str, Any]] = []
    normalized_query = query if case_sensitive else query.lower()
    for root in search_roots:
        for file_path in sorted(root.rglob("*")):
            if len(matches) >= max_results:
                break
            if not file_path.is_file():
                continue
            relative_path = str(file_path.relative_to(study_root)).replace("\\", "/")
            if include_globs and not any(fnmatch(relative_path, pattern) for pattern in include_globs):
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                haystack = line if case_sensitive else line.lower()
                if normalized_query in haystack:
                    matches.append({
                        "path": relative_path,
                        "line_number": line_number,
                        "line": line,
                    })
                    if len(matches) >= max_results:
                        break
        if len(matches) >= max_results:
            break

    result_json = _result_payload(
        job,
        runner_id,
        {
            "query": query,
            "match_count": len(matches),
            "matches": matches,
        },
    )
    return {
        "result_summary": f"search returned {len(matches)} matches for '{query}'",
        "result_json": result_json,
        "evidence_artifacts": [],
    }


def _write_review_artifact(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    config = _load_bridge_config(study_root)
    content = str(job.request_payload.get("content") or "")
    if not content:
        raise ValueError("review artifact content is required")
    target_path = _resolve_allowed_path(
        study_root,
        str(job.request_payload.get("path") or ""),
        allowed_roots=config["allowed_write_roots"],
        require_exists=False,
        expected_kind="file",
    )
    overwrite = bool(job.request_payload.get("overwrite") or False)
    if target_path.exists() and not overwrite:
        raise FileExistsError("review artifact already exists and overwrite was not approved")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    result_json = _result_payload(
        job,
        runner_id,
        {
            "path": str(target_path.relative_to(study_root)).replace("\\", "/"),
            "bytes_written": len(content.encode("utf-8")),
            "overwrite": overwrite,
        },
    )
    return {
        "result_summary": f"wrote review artifact to {result_json['path']}",
        "result_json": result_json,
        "evidence_artifacts": [result_json["path"]],
    }


def _write_staging_authoring_candidate(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    content = str(job.request_payload.get("content") or "")
    if not content:
        raise ValueError("authoring content is required")

    content_bytes = len(content.encode("utf-8"))
    if content_bytes > _MAX_AUTHORING_BYTES:
        raise ValueError("authoring content exceeds the secure bridge size limit")

    packet, authoring, target_path, requested_path = _resolve_packet_authoring_target(job, study_root)
    allow_create = bool(authoring.get("allow_create") or False)
    allow_overwrite = bool(authoring.get("allow_overwrite") or False)
    overwrite_requested = bool(job.request_payload.get("overwrite") or False)

    if target_path.exists():
        if not allow_overwrite:
            raise FileExistsError("task packet does not allow overwriting the authoring target")
        if not overwrite_requested:
            raise FileExistsError("overwrite was not requested for the existing authoring target")
    elif not allow_create:
        raise FileNotFoundError("task packet does not allow creating the authoring target")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    validation_steps = [str(step) for step in authoring.get("validation_steps") or [] if str(step).strip()]
    result_json = _result_payload(
        job,
        runner_id,
        {
            "task_id": str(packet.get("task_id") or job.task_id or ""),
            "path": requested_path,
            "bytes_written": content_bytes,
            "overwrite": overwrite_requested,
            "validation_steps": validation_steps,
            "authoring_mode": "staging_only",
        },
    )
    return {
        "result_summary": f"wrote staging authoring candidate to {result_json['path']}",
        "result_json": result_json,
        "evidence_artifacts": [result_json["path"]],
    }


def _git_status(job: QueuedJob, study_root: Path, runner_id: str) -> dict[str, Any]:
    repo_name = str(job.request_payload.get("repo_name") or "apex-power-ops-platform").strip()
    repo_path = _resolve_git_repo_path(study_root, repo_name)
    completed = subprocess.run(
        ["git", "-C", str(repo_path), "status", "--short", "--branch"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git status failed")
    output = completed.stdout.strip()
    result_json = _result_payload(
        job,
        runner_id,
        {
            "repo_name": repo_name,
            "output": output,
            "lines": output.splitlines() if output else [],
        },
    )
    return {
        "result_summary": f"retrieved git status for {repo_name}",
        "result_json": result_json,
        "evidence_artifacts": [],
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_mapping(row: Any) -> dict[str, Any]:
    return dict(row._mapping) if row is not None else {}


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {} if value is None else dict(value)


def _load_task_packet(study_root: Path, task_id: str) -> dict[str, Any]:
    normalized_task_id = str(task_id or "").strip()
    if not normalized_task_id:
        raise ValueError("task_id is required for packet-scoped authoring")

    packet_path = study_root / _TASK_PACKET_ROOT / f"{normalized_task_id}.json"
    if not packet_path.exists():
        raise FileNotFoundError(f"task packet not found: {packet_path}")

    try:
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"task packet is not valid JSON: {packet_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("task packet must deserialize to an object")
    return payload


def _normalize_relative_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _resolve_packet_authoring_target(job: QueuedJob, study_root: Path) -> tuple[dict[str, Any], dict[str, Any], Path, str]:
    packet = _load_task_packet(study_root, job.task_id or "")
    packet_status = str(packet.get("status") or "").strip()
    if packet_status not in _AUTHORING_EXECUTION_ALLOWED_PACKET_STATUSES:
        raise ValueError("task packet status does not authorize queued staging authoring")

    packet_action_type = str(packet.get("action_type") or "").strip()
    if packet_action_type not in {"draft", "edit"}:
        raise ValueError("task packet action_type does not authorize staging authoring")

    authoring = _json_object(packet.get("authoring"))
    if not bool(authoring.get("enabled") or False):
        raise ValueError("task packet does not enable staging authoring")
    if str(authoring.get("mode") or "").strip() != "staging_only":
        raise ValueError("task packet authoring mode is not supported")

    route = _json_object(packet.get("route"))
    if not bool(route.get("allow_auto_apply") or False):
        raise ValueError("task packet does not permit auto-apply authoring")

    requested_path = _normalize_relative_path(str(job.request_payload.get("path") or job.subject_id or ""))
    if not requested_path:
        raise ValueError("authoring target path is required")

    allowed_target_files = [
        _normalize_relative_path(str(item))
        for item in authoring.get("allowed_target_files") or []
        if _normalize_relative_path(str(item))
    ]
    if requested_path not in allowed_target_files:
        raise ValueError("authoring target path is not allowed by the task packet")
    if not requested_path.startswith("Development/staging/"):
        raise ValueError("authoring target must remain inside Development/staging/")

    target_path = _resolve_allowed_path(
        study_root,
        requested_path,
        allowed_roots=["Development/staging"],
        require_exists=False,
        expected_kind="file",
    )
    return packet, authoring, target_path, requested_path


def missing_worker_tables(db: Session) -> list[str]:
    row = db.execute(
        text(
            """
            SELECT
                to_regclass('public.mcp_local_action_queue') AS mcp_local_action_queue,
                to_regclass('public.mcp_job_runs') AS mcp_job_runs
            """
        )
    ).fetchone()
    payload = _row_mapping(row)
    return [table_name for table_name in _REQUIRED_WORKER_TABLES if payload.get(table_name) is None]


def build_job_result(job: QueuedJob, runner_id: str, dry_run: bool) -> dict[str, Any]:
    mode = "dry-run" if dry_run else "live"
    summary = f"{job.action_type} processed by {runner_id} in {mode} mode"
    result_json = {
        "job_id": job.job_id,
        "action_type": job.action_type,
        "subject_type": job.subject_type,
        "subject_id": job.subject_id,
        "runner_id": runner_id,
        "mode": mode,
        "processed_at": now_iso(),
        "request_payload": job.request_payload,
    }
    return {"result_summary": summary, "result_json": result_json, "evidence_artifacts": []}


def _discover_markdown_path(guide_dir: Path, guide_id: str) -> Path:
    preferred_path = guide_dir / f"{guide_id}.md"
    if preferred_path.exists():
        return preferred_path

    markdown_files = sorted(guide_dir.glob("*.md"))
    if len(markdown_files) == 1:
        return markdown_files[0]

    raise FileNotFoundError(f"Unable to resolve guide markdown file in {guide_dir}")


def _load_guide_surface(study_root: Path, guide_slug: str) -> dict[str, Any]:
    guide_dir = study_root / "Development" / "staging" / guide_slug
    if not guide_dir.exists():
        raise FileNotFoundError(f"Guide staging directory not found: {guide_dir}")

    config_path = guide_dir / f"{guide_slug}-config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Guide config file not found: {config_path}")

    config_json = json.loads(config_path.read_text(encoding="utf-8"))
    guide_id = str(config_json.get("guide_id") or "").strip()
    if not guide_id:
        raise ValueError(f"Guide config missing guide_id: {config_path}")

    markdown_path = _discover_markdown_path(guide_dir, guide_id)
    markdown_text = markdown_path.read_text(encoding="utf-8")

    return {
        "guide_dir": guide_dir,
        "config_path": config_path,
        "config_json": config_json,
        "guide_id": guide_id,
        "markdown_path": markdown_path,
        "tag_ids": _IMG_TAG_PATTERN.findall(markdown_text),
    }


def _missing_render_validation_tables(db: Session) -> list[str]:
    row = db.execute(
        text(
            """
            SELECT
                to_regclass('public.image_assets') AS image_assets,
                to_regclass('public.image_guide_links') AS image_guide_links,
                to_regclass('public.study_content') AS study_content,
                to_regclass('public.mcp_validation_artifacts') AS mcp_validation_artifacts
            """
        )
    ).fetchone()
    payload = _row_mapping(row)
    return [table_name for table_name in _REQUIRED_RENDER_TABLES if payload.get(table_name) is None]


def _fetch_render_validation_rows(
    db: Session,
    content_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    content_row = db.execute(
        text(
            """
            SELECT content_id, slug, title, source_path, status, quality_tier
            FROM public.study_content
            WHERE content_id = :content_id
            LIMIT 1
            """
        ),
        {"content_id": content_id},
    ).fetchone()
    link_rows = db.execute(
        text(
            """
            SELECT image_asset_id, guide_slug, guide_file, line_number, section_context
            FROM public.image_guide_links
            WHERE content_id = :content_id
            ORDER BY line_number NULLS LAST, image_asset_id
            """
        ),
        {"content_id": content_id},
    ).fetchall()
    asset_rows = db.execute(
        text(
            """
            SELECT id, status, storage_bucket, storage_path, storage_url, width_px, height_px, alt_text, caption
            FROM public.image_assets
            WHERE id IN (
                SELECT image_asset_id
                FROM public.image_guide_links
                WHERE content_id = :content_id
            )
            ORDER BY id
            """
        ),
        {"content_id": content_id},
    ).fetchall()
    return (
        _row_mapping(content_row) if content_row is not None else None,
        [_row_mapping(row) for row in link_rows],
        [_row_mapping(row) for row in asset_rows],
    )


def _store_validation_artifact(
    db: Session,
    *,
    job: QueuedJob,
    runner_id: str,
    artifact_title: str,
    summary: str,
    artifact_json: dict[str, Any],
) -> str:
    artifact_id = f"artifact-{uuid4()}"
    db.execute(
        text(
            """
            INSERT INTO public.mcp_validation_artifacts (
                artifact_id,
                artifact_type,
                subject_type,
                subject_id,
                title,
                summary,
                artifact_json,
                created_by
            )
            VALUES (
                :artifact_id,
                'render_validation_report',
                :subject_type,
                :subject_id,
                :title,
                :summary,
                CAST(:artifact_json AS jsonb),
                :created_by
            )
            """
        ),
        {
            "artifact_id": artifact_id,
            "subject_type": job.subject_type,
            "subject_id": job.subject_id,
            "title": artifact_title,
            "summary": summary,
            "artifact_json": json.dumps(artifact_json),
            "created_by": runner_id,
        },
    )
    return artifact_id


def _run_render_validation(
    job: QueuedJob,
    study_root: Path,
    runner_id: str,
    dry_run: bool,
    db: Session,
) -> dict[str, Any]:
    missing_tables = _missing_render_validation_tables(db)
    if missing_tables:
        raise RuntimeError(
            "Render validation dependencies missing in database: " + ", ".join(missing_tables)
        )

    guide_slug = str(job.request_payload.get("guide_slug") or job.subject_id or "").strip()
    validation_target = str(job.request_payload.get("validation_target") or "render-validation").strip()
    expected_asset_ids = [str(item) for item in job.request_payload.get("expected_asset_ids", [])]
    if not guide_slug:
        raise ValueError("Render validation job missing guide_slug")

    guide_surface = _load_guide_surface(study_root, guide_slug)
    guide_id = guide_surface["guide_id"]
    tag_ids = guide_surface["tag_ids"]
    tag_id_set = set(tag_ids)
    expected_id_set = set(expected_asset_ids)

    content_row, link_rows, asset_rows = _fetch_render_validation_rows(db, guide_id)
    linked_ids = [str(row["image_asset_id"]) for row in link_rows]
    linked_id_set = set(linked_ids)
    asset_by_id = {str(row["id"]): row for row in asset_rows}

    missing_link_ids = sorted(tag_id_set - linked_id_set)
    extra_link_ids = sorted(linked_id_set - tag_id_set)
    missing_asset_rows = sorted(linked_id_set - set(asset_by_id.keys()))
    expected_missing_ids = sorted(expected_id_set - tag_id_set) if expected_id_set else []
    expected_extra_ids = sorted(tag_id_set - expected_id_set) if expected_id_set else []

    integrated_asset_ids: list[str] = []
    non_integrated_asset_ids: list[str] = []
    storage_ready_asset_ids: list[str] = []
    dimension_ready_asset_ids: list[str] = []
    for asset_id, asset_row in asset_by_id.items():
        if asset_row.get("status") == "integrated":
            integrated_asset_ids.append(asset_id)
        else:
            non_integrated_asset_ids.append(asset_id)
        if asset_row.get("storage_path") and asset_row.get("storage_url"):
            storage_ready_asset_ids.append(asset_id)
        if (asset_row.get("width_px") or 0) > 0 and (asset_row.get("height_px") or 0) > 0:
            dimension_ready_asset_ids.append(asset_id)

    readiness = "render_ready"
    if missing_link_ids or extra_link_ids or missing_asset_rows:
        readiness = "mapping_mismatch"
    elif len(integrated_asset_ids) != len(tag_id_set):
        readiness = "asset_integration_pending"
    elif len(storage_ready_asset_ids) != len(tag_id_set):
        readiness = "storage_pending"
    elif len(dimension_ready_asset_ids) != len(tag_id_set):
        readiness = "dimension_validation_pending"

    result_json = {
        "job_id": job.job_id,
        "action_type": job.action_type,
        "subject_type": job.subject_type,
        "subject_id": job.subject_id,
        "runner_id": runner_id,
        "mode": "dry-run" if dry_run else "live",
        "processed_at": now_iso(),
        "validation_target": validation_target,
        "guide_slug": guide_slug,
        "guide_id": guide_id,
        "markdown_path": str(guide_surface["markdown_path"]),
        "config_path": str(guide_surface["config_path"]),
        "tag_count": len(tag_ids),
        "tag_ids": tag_ids,
        "expected_asset_ids": expected_asset_ids,
        "expected_missing_ids": expected_missing_ids,
        "expected_extra_ids": expected_extra_ids,
        "linked_asset_count": len(linked_ids),
        "linked_asset_ids": linked_ids,
        "missing_link_ids": missing_link_ids,
        "extra_link_ids": extra_link_ids,
        "missing_asset_rows": missing_asset_rows,
        "asset_status_summary": {
            "integrated": len(integrated_asset_ids),
            "non_integrated": len(non_integrated_asset_ids),
            "storage_ready": len(storage_ready_asset_ids),
            "dimension_ready": len(dimension_ready_asset_ids),
        },
        "integrated_asset_ids": sorted(integrated_asset_ids),
        "non_integrated_asset_ids": sorted(non_integrated_asset_ids),
        "storage_ready_asset_ids": sorted(storage_ready_asset_ids),
        "dimension_ready_asset_ids": sorted(dimension_ready_asset_ids),
        "study_content": content_row,
        "link_rows": link_rows,
        "assets": asset_rows,
        "readiness": readiness,
    }

    summary = (
        f"render validation audit for {guide_id}: readiness={readiness}; "
        f"tags={len(tag_ids)}; linked={len(linked_ids)}; integrated={len(integrated_asset_ids)}"
    )

    evidence_artifacts: list[str] = []
    if not dry_run:
        evidence_artifacts.append(
            _store_validation_artifact(
                db,
                job=job,
                runner_id=runner_id,
                artifact_title=f"Render validation audit -- {guide_id}",
                summary=summary,
                artifact_json=result_json,
            )
        )

    return {
        "result_summary": summary,
        "result_json": result_json,
        "evidence_artifacts": evidence_artifacts,
    }


def claim_next_job(db: Session, runner_id: str) -> QueuedJob | None:
    row = db.execute(
        text(
            """
            WITH next_job AS (
                SELECT job_id
                FROM public.mcp_local_action_queue
                WHERE status = 'queued'
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 4
                        WHEN 'high' THEN 3
                        WHEN 'normal' THEN 2
                        WHEN 'low' THEN 1
                        ELSE 0
                    END DESC,
                    created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE public.mcp_local_action_queue queue
            SET status = 'claimed',
                claimed_at = NOW(),
                claimed_by = :runner_id
            FROM next_job
            WHERE queue.job_id = next_job.job_id
            RETURNING
                queue.job_id,
                queue.action_type,
                queue.task_id,
                queue.subject_type,
                queue.subject_id,
                queue.requested_by,
                queue.request_payload,
                queue.priority
            """
        ),
        {"runner_id": runner_id},
    ).fetchone()
    if row is None:
        return None
    payload = _row_mapping(row)
    return QueuedJob(
        job_id=payload["job_id"],
        action_type=payload["action_type"],
        task_id=payload.get("task_id"),
        subject_type=payload["subject_type"],
        subject_id=payload["subject_id"],
        requested_by=payload["requested_by"],
        request_payload=_json_object(payload.get("request_payload")),
        priority=payload["priority"],
    )


def mark_job_running(db: Session, job_id: str) -> None:
    db.execute(
        text(
            """
            UPDATE public.mcp_local_action_queue
            SET status = 'running'
            WHERE job_id = :job_id
            """
        ),
        {"job_id": job_id},
    )


def complete_job(
    db: Session,
    job: QueuedJob,
    runner_id: str,
    result_summary: str,
    result_json: dict[str, Any],
    evidence_artifacts: list[str] | None = None,
) -> None:
    evidence_artifacts = evidence_artifacts or []
    db.execute(
        text(
            """
            UPDATE public.mcp_local_action_queue
            SET status = 'completed',
                completed_at = NOW()
            WHERE job_id = :job_id
            """
        ),
        {"job_id": job.job_id},
    )
    db.execute(
        text(
            """
            INSERT INTO public.mcp_job_runs (
                job_id,
                status,
                result_summary,
                result_json,
                evidence_artifacts,
                runner_id,
                started_at,
                completed_at
            )
            VALUES (
                :job_id,
                'completed',
                :result_summary,
                CAST(:result_json AS jsonb),
                CAST(:evidence_artifacts AS jsonb),
                :runner_id,
                NOW(),
                NOW()
            )
            """
        ),
        {
            "job_id": job.job_id,
            "result_summary": result_summary,
            "result_json": json.dumps(result_json),
            "evidence_artifacts": json.dumps(evidence_artifacts),
            "runner_id": runner_id,
        },
    )


def fail_job(db: Session, job: QueuedJob, runner_id: str, error_message: str) -> None:
    db.execute(
        text(
            """
            UPDATE public.mcp_local_action_queue
            SET status = 'failed',
                completed_at = NOW()
            WHERE job_id = :job_id
            """
        ),
        {"job_id": job.job_id},
    )
    db.execute(
        text(
            """
            INSERT INTO public.mcp_job_runs (
                job_id,
                status,
                result_summary,
                result_json,
                evidence_artifacts,
                runner_id,
                started_at,
                completed_at
            )
            VALUES (
                :job_id,
                'failed',
                :result_summary,
                CAST(:result_json AS jsonb),
                '[]'::jsonb,
                :runner_id,
                NOW(),
                NOW()
            )
            """
        ),
        {
            "job_id": job.job_id,
            "result_summary": error_message,
            "result_json": json.dumps({"error": error_message}),
            "runner_id": runner_id,
        },
    )


def process_job(job: QueuedJob, study_root: Path, runner_id: str, dry_run: bool, db: Session) -> dict[str, Any]:
    if job.action_type == "run_render_validation":
        return _run_render_validation(job, study_root=study_root, runner_id=runner_id, dry_run=dry_run, db=db)
    if job.action_type == "list_workspace_directory":
        return _list_workspace_directory(job, study_root=study_root, runner_id=runner_id)
    if job.action_type == "read_workspace_file":
        return _read_workspace_file(job, study_root=study_root, runner_id=runner_id)
    if job.action_type == "search_workspace":
        return _search_workspace(job, study_root=study_root, runner_id=runner_id)
    if job.action_type == "write_review_artifact":
        return _write_review_artifact(job, study_root=study_root, runner_id=runner_id)
    if job.action_type == "write_staging_authoring_candidate":
        return _write_staging_authoring_candidate(job, study_root=study_root, runner_id=runner_id)
    if job.action_type == "git_status":
        return _git_status(job, study_root=study_root, runner_id=runner_id)
    return build_job_result(job, runner_id=runner_id, dry_run=dry_run)