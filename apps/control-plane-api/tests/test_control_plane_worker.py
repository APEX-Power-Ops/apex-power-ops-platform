"""Tests for control-plane worker helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.control_plane.worker import QueuedJob, build_job_result, missing_worker_tables, process_job


def _queued_job() -> QueuedJob:
    return QueuedJob(
        job_id="job-123",
        action_type="run_render_validation",
        task_id="2026-03-28-ett-image-assets-pilot-001",
        subject_type="guide",
        subject_id="motor-control-centers-low-voltage",
        requested_by="11111111-1111-1111-1111-111111111111",
        request_payload={"guide_slug": "motor-control-centers-low-voltage"},
        priority="normal",
    )


def test_build_job_result_marks_mode_and_subject():
    result = build_job_result(_queued_job(), runner_id="worker-a", dry_run=True)

    assert "dry-run" in result["result_summary"]
    assert result["result_json"]["subject_id"] == "motor-control-centers-low-voltage"
    assert result["result_json"]["runner_id"] == "worker-a"
    assert result["evidence_artifacts"] == []


def test_process_job_returns_safe_stub_result(tmp_path: Path):
    fallback_job = QueuedJob(
        job_id="job-124",
        action_type="collect_validation_evidence",
        task_id="task-1",
        subject_type="guide",
        subject_id="motor-control-centers-low-voltage",
        requested_by="11111111-1111-1111-1111-111111111111",
        request_payload={"artifact_type": "screenshot"},
        priority="normal",
    )

    result = process_job(
        fallback_job,
        study_root=tmp_path,
        runner_id="worker-b",
        dry_run=False,
        db=_FakeSession({}),
    )

    assert "processed by worker-b" in result["result_summary"]
    assert result["result_json"]["action_type"] == "collect_validation_evidence"


def test_process_job_render_validation_static_audit(tmp_path: Path):
    guide_dir = tmp_path / "Development" / "staging" / "motor-control-centers-low-voltage"
    guide_dir.mkdir(parents=True)
    (guide_dir / "motor-control-centers-low-voltage-config.json").write_text(
        json.dumps({"guide_id": "SG-CT-MOTOR-CONTROL-CENTERS"}),
        encoding="utf-8",
    )
    (guide_dir / "SG-CT-MOTOR-CONTROL-CENTERS.md").write_text(
        "{{IMG: mcc-lineup-anatomy-overview}}\n{{IMG: mcc-wiring-interface-types}}\n",
        encoding="utf-8",
    )

    class _RenderSession:
        def execute(self, statement, params=None):
            sql = str(statement)
            if "to_regclass('public.image_assets')" in sql:
                return SimpleNamespace(
                    fetchone=lambda: _FakeRow(
                        {
                            "image_assets": "image_assets",
                            "image_guide_links": "image_guide_links",
                            "study_content": "study_content",
                            "mcp_validation_artifacts": "mcp_validation_artifacts",
                        }
                    )
                )
            if "FROM public.study_content" in sql:
                return SimpleNamespace(
                    fetchone=lambda: _FakeRow(
                        {
                            "content_id": "SG-CT-MOTOR-CONTROL-CENTERS",
                            "slug": "sg-ct-motor-control-centers",
                            "title": "Motor Control Centers",
                            "source_path": "Development/staging/motor-control-centers-low-voltage/SG-CT-MOTOR-CONTROL-CENTERS.md",
                            "status": "draft",
                            "quality_tier": "draft",
                        }
                    )
                )
            if "SELECT id, status, storage_bucket, storage_path, storage_url, width_px, height_px, alt_text, caption" in sql:
                return SimpleNamespace(
                    fetchall=lambda: [
                        _FakeRow(
                            {
                                "id": "mcc-lineup-anatomy-overview",
                                "status": "integrated",
                                "storage_bucket": "study-images",
                                "storage_path": "study-images/mcc/a.svg",
                                "storage_url": "https://example.com/a.svg",
                                "width_px": 1200,
                                "height_px": 800,
                                "alt_text": "Alt A",
                                "caption": "Caption A",
                            }
                        ),
                        _FakeRow(
                            {
                                "id": "mcc-wiring-interface-types",
                                "status": "integrated",
                                "storage_bucket": "study-images",
                                "storage_path": "study-images/mcc/b.svg",
                                "storage_url": "https://example.com/b.svg",
                                "width_px": 1200,
                                "height_px": 800,
                                "alt_text": "Alt B",
                                "caption": "Caption B",
                            }
                        ),
                    ]
                )
            if "FROM public.image_guide_links" in sql:
                return SimpleNamespace(
                    fetchall=lambda: [
                        _FakeRow(
                            {
                                "image_asset_id": "mcc-lineup-anatomy-overview",
                                "guide_slug": "motor-control-centers-low-voltage",
                                "guide_file": "SG-CT-MOTOR-CONTROL-CENTERS.md",
                                "line_number": 1,
                                "section_context": "LEVEL: III",
                            }
                        ),
                        _FakeRow(
                            {
                                "image_asset_id": "mcc-wiring-interface-types",
                                "guide_slug": "motor-control-centers-low-voltage",
                                "guide_file": "SG-CT-MOTOR-CONTROL-CENTERS.md",
                                "line_number": 2,
                                "section_context": "LEVEL: III",
                            }
                        ),
                    ]
                )
            raise AssertionError(f"Unexpected SQL: {sql}")

    result = process_job(
        _queued_job(),
        study_root=tmp_path,
        runner_id="worker-c",
        dry_run=True,
        db=_RenderSession(),
    )

    assert result["result_json"]["readiness"] == "render_ready"
    assert result["result_json"]["tag_count"] == 2
    assert result["result_json"]["asset_status_summary"]["integrated"] == 2
    assert result["evidence_artifacts"] == []


def test_process_job_list_workspace_directory(tmp_path: Path):
    target_dir = tmp_path / "Development" / "Control-Plane"
    target_dir.mkdir(parents=True)
    (target_dir / "a.md").write_text("alpha", encoding="utf-8")
    (target_dir / "subdir").mkdir()

    job = QueuedJob(
        job_id="job-dir",
        action_type="list_workspace_directory",
        task_id="task-dir",
        subject_type="workspace_dir",
        subject_id="Development/Control-Plane",
        requested_by="actor-dir",
        request_payload={"path": "Development/Control-Plane"},
        priority="normal",
    )

    result = process_job(job, study_root=tmp_path, runner_id="worker-dir", dry_run=False, db=_FakeSession({}))

    assert result["result_json"]["path"] == "Development/Control-Plane"
    assert {entry["name"] for entry in result["result_json"]["entries"]} == {"a.md", "subdir"}


def test_process_job_write_review_artifact(tmp_path: Path):
    (tmp_path / "Development" / "Validation-Runs").mkdir(parents=True)
    job = QueuedJob(
        job_id="job-write",
        action_type="write_review_artifact",
        task_id="task-write",
        subject_type="review_artifact",
        subject_id="Development/Validation-Runs/review.md",
        requested_by="actor-write",
        request_payload={
            "path": "Development/Validation-Runs/review.md",
            "content": "# Review\n\nLooks good.",
        },
        priority="normal",
    )

    result = process_job(job, study_root=tmp_path, runner_id="worker-write", dry_run=False, db=_FakeSession({}))

    target_path = tmp_path / "Development" / "Validation-Runs" / "review.md"
    assert target_path.exists()
    assert "Looks good." in target_path.read_text(encoding="utf-8")
    assert result["result_json"]["path"] == "Development/Validation-Runs/review.md"
    assert result["evidence_artifacts"] == ["Development/Validation-Runs/review.md"]


def test_process_job_git_status_uses_allowlisted_repo(tmp_path: Path):
    job = QueuedJob(
        job_id="job-git",
        action_type="git_status",
        task_id="task-git",
        subject_type="repo",
        subject_id="apex-power-ops-platform",
        requested_by="actor-git",
        request_payload={"repo_name": "apex-power-ops-platform"},
        priority="normal",
    )

    with patch("services.control_plane.worker.subprocess.run") as mock_run:
        mock_run.return_value = SimpleNamespace(returncode=0, stdout="## main\n M file.md\n", stderr="")
        result = process_job(job, study_root=tmp_path, runner_id="worker-git", dry_run=False, db=_FakeSession({}))

    assert result["result_json"]["repo_name"] == "apex-power-ops-platform"
    assert result["result_json"]["lines"][0] == "## main"
    assert "git status" in result["result_summary"]


def test_process_job_write_staging_authoring_candidate(tmp_path: Path):
    packet_dir = tmp_path / "Development" / "Agent-Inbox"
    packet_dir.mkdir(parents=True)
    target_dir = tmp_path / "Development" / "staging" / "example-guide"
    target_dir.mkdir(parents=True)
    target_path = target_dir / "SG-CT-EXAMPLE-GUIDE.md"
    target_path.write_text("Old content\n", encoding="utf-8")

    (packet_dir / "2026-03-29-example-authoring-001.json").write_text(
        json.dumps(
            {
                "task_id": "2026-03-29-example-authoring-001",
                "title": "Example authoring packet",
                "lane": "ett-content",
                "primary_repo": "apex-power-ops-platform",
                "objective": "Update one staging guide.",
                "status": "approved_for_local_action",
                "action_type": "edit",
                "risk_level": "high",
                "inputs": [],
                "output_targets": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                "approval": {
                    "writeback_required": True,
                    "human_signoff_required": False,
                    "frontier_review_required": True
                },
                "route": {
                    "preferred_executor": "ide-agent",
                    "preferred_model_tier": "tier-a",
                    "model_assignment_reason": "authoring packet",
                    "review_gate": "tier-a review before closeout",
                    "allow_automation_prepare_only": True,
                    "allow_auto_apply": True
                },
                "authoring": {
                    "enabled": True,
                    "mode": "staging_only",
                    "allowed_target_files": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                    "allow_create": False,
                    "allow_overwrite": True,
                    "validation_steps": ["packet closeout note"]
                }
            }
        ),
        encoding="utf-8",
    )

    job = QueuedJob(
        job_id="job-author",
        action_type="write_staging_authoring_candidate",
        task_id="2026-03-29-example-authoring-001",
        subject_type="authoring_target",
        subject_id="Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
        requested_by="actor-author",
        request_payload={
            "path": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
            "content": "New content\n",
            "overwrite": True,
        },
        priority="normal",
    )

    result = process_job(job, study_root=tmp_path, runner_id="worker-author", dry_run=False, db=_FakeSession({}))

    assert target_path.read_text(encoding="utf-8") == "New content\n"
    assert result["result_json"]["task_id"] == "2026-03-29-example-authoring-001"
    assert result["result_json"]["validation_steps"] == ["packet closeout note"]


def test_process_job_write_staging_authoring_candidate_rejects_unapproved_target(tmp_path: Path):
    packet_dir = tmp_path / "Development" / "Agent-Inbox"
    packet_dir.mkdir(parents=True)

    (packet_dir / "2026-03-29-example-authoring-002.json").write_text(
        json.dumps(
            {
                "task_id": "2026-03-29-example-authoring-002",
                "title": "Example authoring packet",
                "lane": "ett-content",
                "primary_repo": "apex-power-ops-platform",
                "objective": "Update one staging guide.",
                "status": "approved_for_local_action",
                "action_type": "edit",
                "risk_level": "high",
                "inputs": [],
                "output_targets": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                "approval": {
                    "writeback_required": True,
                    "human_signoff_required": False,
                    "frontier_review_required": True
                },
                "route": {
                    "preferred_executor": "ide-agent",
                    "preferred_model_tier": "tier-a",
                    "model_assignment_reason": "authoring packet",
                    "review_gate": "tier-a review before closeout",
                    "allow_automation_prepare_only": True,
                    "allow_auto_apply": True
                },
                "authoring": {
                    "enabled": True,
                    "mode": "staging_only",
                    "allowed_target_files": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                    "allow_create": False,
                    "allow_overwrite": True,
                    "validation_steps": []
                }
            }
        ),
        encoding="utf-8",
    )

    job = QueuedJob(
        job_id="job-author-2",
        action_type="write_staging_authoring_candidate",
        task_id="2026-03-29-example-authoring-002",
        subject_type="authoring_target",
        subject_id="Development/staging/example-guide/SG-CT-OTHER.md",
        requested_by="actor-author",
        request_payload={
            "path": "Development/staging/example-guide/SG-CT-OTHER.md",
            "content": "New content\n",
            "overwrite": True,
        },
        priority="normal",
    )

    with pytest.raises(ValueError, match="not allowed by the task packet"):
        process_job(job, study_root=tmp_path, runner_id="worker-author", dry_run=False, db=_FakeSession({}))


def test_process_job_write_staging_authoring_candidate_rejects_invalid_packet_status(tmp_path: Path):
    packet_dir = tmp_path / "Development" / "Agent-Inbox"
    packet_dir.mkdir(parents=True)
    target_dir = tmp_path / "Development" / "staging" / "example-guide"
    target_dir.mkdir(parents=True)
    (target_dir / "SG-CT-EXAMPLE-GUIDE.md").write_text("Old content\n", encoding="utf-8")

    (packet_dir / "2026-03-29-example-authoring-003.json").write_text(
        json.dumps(
            {
                "task_id": "2026-03-29-example-authoring-003",
                "title": "Example authoring packet",
                "lane": "ett-content",
                "primary_repo": "apex-power-ops-platform",
                "objective": "Update one staging guide.",
                "status": "prepared",
                "action_type": "edit",
                "risk_level": "high",
                "inputs": [],
                "output_targets": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                "approval": {
                    "writeback_required": True,
                    "human_signoff_required": False,
                    "frontier_review_required": True
                },
                "route": {
                    "preferred_executor": "ide-agent",
                    "preferred_model_tier": "tier-a",
                    "model_assignment_reason": "authoring packet",
                    "review_gate": "tier-a review before closeout",
                    "allow_automation_prepare_only": True,
                    "allow_auto_apply": True
                },
                "authoring": {
                    "enabled": True,
                    "mode": "staging_only",
                    "allowed_target_files": ["Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md"],
                    "allow_create": False,
                    "allow_overwrite": True,
                    "validation_steps": []
                }
            }
        ),
        encoding="utf-8",
    )

    job = QueuedJob(
        job_id="job-author-3",
        action_type="write_staging_authoring_candidate",
        task_id="2026-03-29-example-authoring-003",
        subject_type="authoring_target",
        subject_id="Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
        requested_by="actor-author",
        request_payload={
            "path": "Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md",
            "content": "New content\n",
            "overwrite": True,
        },
        priority="normal",
    )

    with pytest.raises(ValueError, match="status does not authorize queued staging authoring"):
        process_job(job, study_root=tmp_path, runner_id="worker-author", dry_run=False, db=_FakeSession({}))


class _FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class _FakeSession:
    def __init__(self, mapping):
        self.mapping = mapping

    def execute(self, _statement):
        return SimpleNamespace(fetchone=lambda: _FakeRow(self.mapping))


def test_missing_worker_tables_reports_unapplied_migration():
    session = _FakeSession({"mcp_local_action_queue": None, "mcp_job_runs": "mcp_job_runs"})

    missing = missing_worker_tables(session)

    assert missing == ["mcp_local_action_queue"]