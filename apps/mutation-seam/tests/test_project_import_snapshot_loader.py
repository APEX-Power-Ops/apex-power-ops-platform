import base64
import hashlib
import json

import pytest

from app.project_import_candidate import clear_project_import_candidate_cache
from app.project_import_snapshot import (
    PAYLOAD_ADMISSION_PLAN,
    PAYLOAD_CANDIDATE,
    PAYLOAD_MANIFEST,
    PAYLOAD_SHA256SUMS,
    SNAPSHOT_AUTHORITY,
    SNAPSHOT_ENV_VAR,
    SNAPSHOT_MANIFEST_SCHEMA_VERSION,
    clear_project_import_snapshot_cache,
    load_project_import_snapshot_bundle,
)


def _make_token() -> dict[str, str]:
    payload = {
        "actor_id": "pm-001",
        "actor_role": "pm",
        "project_scope": ["proj-001"],
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return {"Authorization": f"Bearer {encoded}"}


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_payload(path, value) -> str:
    payload = _json_bytes(value)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _write_snapshot(snapshot_dir, candidate=None, admission_plan=None):
    candidate = candidate or {
        "candidate_id": "pm-import-candidate-miner-temp-power",
        "candidate_version": "pm_import_candidate_read_only_v1",
        "mutation_authority": "not_admitted",
        "summary": {
            "workpackage_count": 7,
            "task_count": 15,
            "apparatus_candidate_count": 184,
            "warning_count": 1,
        },
        "warnings": [{"code": "PROJECT_DATA_ENTRY_FORMULA_ERRORS", "severity": "warning"}],
        "source_freshness": {"aggregate_fingerprint": "snapshot-source"},
        "workpackages": [],
    }
    admission_plan = admission_plan or {
        "admission_plan_id": "pm-import-candidate-miner-temp-power-admission-plan",
        "admission_plan_version": "pm_import_admission_plan_read_only_v1",
        "candidate_id": "pm-import-candidate-miner-temp-power",
        "candidate_version": "pm_import_candidate_read_only_v1",
        "mutation_authority": "not_admitted",
        "source_stat_fingerprint": "snapshot-source",
        "candidate_shape_fingerprint": "snapshot-shape",
        "target_row_plan": {"task_rows": 15, "apparatus_rows": 184},
    }
    manifest = {
        "schema_version": SNAPSHOT_MANIFEST_SCHEMA_VERSION,
        "authority": SNAPSHOT_AUTHORITY,
        "candidate_id": candidate["candidate_id"],
        "candidate_version": candidate["candidate_version"],
        "mutation_authority": "not_admitted",
        "source_stat_fingerprint": "snapshot-source",
        "candidate_shape_fingerprint": "snapshot-shape",
    }

    snapshot_dir.mkdir()
    hashes = {
        PAYLOAD_CANDIDATE: _write_payload(snapshot_dir / PAYLOAD_CANDIDATE, candidate),
        PAYLOAD_ADMISSION_PLAN: _write_payload(snapshot_dir / PAYLOAD_ADMISSION_PLAN, admission_plan),
        PAYLOAD_MANIFEST: _write_payload(snapshot_dir / PAYLOAD_MANIFEST, manifest),
    }
    (snapshot_dir / PAYLOAD_SHA256SUMS).write_text(
        "".join(f"{digest}  {file_name}\n" for file_name, digest in sorted(hashes.items())),
        encoding="utf-8",
    )
    return candidate, admission_plan


def test_snapshot_env_candidate_and_admission_routes_override_missing_sources(client, monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "snapshot"
    candidate, admission_plan = _write_snapshot(snapshot_dir)
    monkeypatch.setenv(SNAPSHOT_ENV_VAR, str(snapshot_dir))
    clear_project_import_candidate_cache()

    candidate_response = client.get("/api/v1/reads/project-import-candidate", headers=_make_token())
    plan_response = client.get("/api/v1/reads/project-import-admission-plan", headers=_make_token())

    assert candidate_response.status_code == 200
    assert candidate_response.json()["candidate_id"] == candidate["candidate_id"]
    assert candidate_response.json()["summary"]["task_count"] == 15
    assert candidate_response.json()["summary"]["apparatus_candidate_count"] == 184
    assert candidate_response.json()["mutation_authority"] == "not_admitted"
    assert plan_response.status_code == 200
    assert plan_response.json()["candidate_id"] == admission_plan["candidate_id"]
    assert plan_response.json()["source_stat_fingerprint"] == "snapshot-source"
    assert plan_response.json()["candidate_shape_fingerprint"] == "snapshot-shape"
    assert plan_response.json()["mutation_authority"] == "not_admitted"


def test_explicit_source_paths_bypass_snapshot_env(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "snapshot"
    _write_snapshot(snapshot_dir)
    monkeypatch.setenv(SNAPSHOT_ENV_VAR, str(snapshot_dir))
    clear_project_import_candidate_cache()

    from app.project_import_candidate import load_project_import_candidate

    candidate = load_project_import_candidate(str(tmp_path / "missing-estimator.xlsm"), str(tmp_path / "missing.pdf"))

    assert candidate["candidate_id"] == "pm-import-candidate-project-miner"
    assert candidate["summary"]["task_count"] == 0
    assert candidate["mutation_authority"] == "not_admitted"


def test_snapshot_loader_rejects_checksum_mismatch(monkeypatch, tmp_path):
    snapshot_dir = tmp_path / "snapshot"
    _write_snapshot(snapshot_dir)
    (snapshot_dir / PAYLOAD_CANDIDATE).write_text('{"candidate_id":"tampered"}\n', encoding="utf-8")
    monkeypatch.setenv(SNAPSHOT_ENV_VAR, str(snapshot_dir))
    clear_project_import_snapshot_cache()

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_project_import_snapshot_bundle()
