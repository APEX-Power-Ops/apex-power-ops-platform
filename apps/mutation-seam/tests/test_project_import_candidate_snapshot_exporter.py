import hashlib
import json
from pathlib import Path

import pytest

from app.project_import_admission_plan import build_project_import_admission_plan
from scripts.export_pm_import_candidate_snapshot import (
    PAYLOAD_ADMISSION_PLAN,
    PAYLOAD_CANDIDATE,
    PAYLOAD_MANIFEST,
    REPO_ROOT,
    SNAPSHOT_AUTHORITY,
    SNAPSHOT_MANIFEST_SCHEMA_VERSION,
    build_snapshot_manifest,
    export_project_import_candidate_snapshot,
)


def _candidate() -> dict:
    return {
        "candidate_id": "pm-import-candidate-miner-temp-power",
        "candidate_version": "pm_import_candidate_read_only_v1",
        "review_status": "draft_review_only",
        "mutation_authority": "not_admitted",
        "project": {"name": "Miner Temp Power"},
        "source_freshness": {
            "aggregate_fingerprint": "sourcefingerprint123",
            "source_files": [
                {
                    "source_id": "estimator_workbook",
                    "label": "Estimator workbook",
                    "path": r"C:\Users\jjswe\Desktop\Project Miner PM Planning\Estimator R3 - Project Miner Temp Power Testing.xlsm",
                    "found": True,
                    "size_bytes": 12345,
                    "modified_at": "2026-05-17T12:00:00Z",
                    "fingerprint": "estimatorfingerprint",
                    "freshness_status": "available",
                },
                {
                    "source_id": "sld_pdf",
                    "label": "SLD or drawing PDF",
                    "path": "/private/source/Miner Temp SLD-AP-BCARRASCO.pdf",
                    "found": True,
                    "size_bytes": 6789,
                    "modified_at": "2026-05-17T12:01:00Z",
                    "fingerprint": "pdffingerprint",
                    "freshness_status": "available",
                },
            ],
        },
        "summary": {
            "workpackage_count": 1,
            "task_count": 1,
            "apparatus_candidate_count": 1,
            "warning_count": 1,
            "blocker_count": 0,
        },
        "workpackages": [
            {
                "workpackage_id": "candidate-wp-001",
                "title": "Temp Power",
                "task_count": 1,
                "apparatus_candidate_count": 1,
                "planned_hours": 24,
                "tasks": [
                    {
                        "task_id": "candidate-task-0001",
                        "source_line_id": "miner-line-015",
                        "title": "Ground Resistance Test Lot",
                        "quantity": 3,
                        "drawing_ref": "E01-00",
                        "source_ref": {"source_row": 28},
                        "apparatus_candidates": [
                            {"candidate_id": "candidate-apparatus-0001"},
                        ],
                    }
                ],
            }
        ],
        "warnings": [
            {
                "severity": "warning",
                "code": "PROJECT_DATA_ENTRY_FORMULA_ERRORS",
                "message": "Synthetic warning for exporter test.",
            }
        ],
    }


def _plan(candidate: dict) -> dict:
    return build_project_import_admission_plan(candidate)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_snapshot_manifest_redacts_source_paths():
    candidate = _candidate()
    plan = _plan(candidate)

    manifest = build_snapshot_manifest(
        candidate,
        plan,
        {PAYLOAD_CANDIDATE: "a" * 64, PAYLOAD_ADMISSION_PLAN: "b" * 64},
        generated_at_utc="2026-05-18T00:00:00Z",
        generator_repo_head="test-head",
        generator_dirty_state="clean",
    )

    encoded = json.dumps(manifest, sort_keys=True)
    assert manifest["schema_version"] == SNAPSHOT_MANIFEST_SCHEMA_VERSION
    assert manifest["authority"] == SNAPSHOT_AUTHORITY
    assert r"C:\Users\jjswe" not in encoded
    assert "/private/source" not in encoded
    assert "Estimator R3 - Project Miner Temp Power Testing.xlsm" in encoded
    assert "Miner Temp SLD-AP-BCARRASCO.pdf" in encoded
    assert "path" not in manifest["source_files_redacted"][0]
    assert manifest["mutation_authority"] == "not_admitted"


def test_export_project_import_candidate_snapshot_writes_hashes_and_runtime_payloads(tmp_path):
    candidate = _candidate()
    plan = _plan(candidate)
    output_dir = tmp_path / "snapshot"

    result = export_project_import_candidate_snapshot(
        candidate,
        plan,
        output_dir,
        generated_at_utc="2026-05-18T00:00:00Z",
        generator_repo_head="test-head",
        generator_dirty_state="clean",
    )

    assert sorted(result["files"]) == [
        "SHA256SUMS.txt",
        PAYLOAD_ADMISSION_PLAN,
        PAYLOAD_CANDIDATE,
        PAYLOAD_MANIFEST,
    ]
    assert result["mutation_authority"] == "not_admitted"
    assert (output_dir / PAYLOAD_CANDIDATE).exists()
    assert (output_dir / PAYLOAD_ADMISSION_PLAN).exists()
    assert (output_dir / PAYLOAD_MANIFEST).exists()
    assert result["sha256"][PAYLOAD_CANDIDATE] == _sha256(output_dir / PAYLOAD_CANDIDATE)
    assert result["sha256"][PAYLOAD_ADMISSION_PLAN] == _sha256(output_dir / PAYLOAD_ADMISSION_PLAN)
    assert result["sha256"][PAYLOAD_MANIFEST] == _sha256(output_dir / PAYLOAD_MANIFEST)

    manifest = json.loads((output_dir / PAYLOAD_MANIFEST).read_text(encoding="utf-8"))
    candidate_payload = json.loads((output_dir / PAYLOAD_CANDIDATE).read_text(encoding="utf-8"))
    admission_payload = json.loads((output_dir / PAYLOAD_ADMISSION_PLAN).read_text(encoding="utf-8"))
    sha256sums = (output_dir / "SHA256SUMS.txt").read_text(encoding="utf-8")

    assert candidate_payload["mutation_authority"] == "not_admitted"
    assert admission_payload["mutation_authority"] == "not_admitted"
    assert manifest["candidate_id"] == "pm-import-candidate-miner-temp-power"
    assert manifest["task_count"] == 1
    assert manifest["apparatus_candidate_count"] == 1
    assert manifest["warning_codes"] == ["PROJECT_DATA_ENTRY_FORMULA_ERRORS"]
    assert "candidate.json" in sha256sums
    assert "admission-plan.json" in sha256sums
    assert "manifest.json" in sha256sums


def test_export_project_import_candidate_snapshot_rejects_repo_output_without_explicit_flag():
    candidate = _candidate()
    plan = _plan(candidate)
    repo_output = REPO_ROOT / "output" / "pm-lane-273-rejected-test"

    with pytest.raises(ValueError):
        export_project_import_candidate_snapshot(candidate, plan, repo_output)

    assert not repo_output.exists()
