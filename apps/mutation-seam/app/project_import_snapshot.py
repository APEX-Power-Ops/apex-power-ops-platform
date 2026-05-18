from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


SNAPSHOT_ENV_VAR = "APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH"
SNAPSHOT_MANIFEST_SCHEMA_VERSION = "pm_import_candidate_snapshot_manifest_v1"
SNAPSHOT_AUTHORITY = "derived_source_snapshot_no_live"
PAYLOAD_CANDIDATE = "candidate.json"
PAYLOAD_ADMISSION_PLAN = "admission-plan.json"
PAYLOAD_MANIFEST = "manifest.json"
PAYLOAD_SHA256SUMS = "SHA256SUMS.txt"


def clear_project_import_snapshot_cache() -> None:
    load_project_import_snapshot_bundle.cache_clear()


def _snapshot_root_from_env() -> Path | None:
    path_text = os.getenv(SNAPSHOT_ENV_VAR, "").strip()
    if not path_text:
        return None
    path = Path(path_text)
    return path.parent if path.is_file() else path


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Snapshot payload must be a JSON object: {path.name}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_sha256sums(path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        digest, _, file_name = stripped.partition("  ")
        if not digest or not file_name:
            raise ValueError(f"Invalid snapshot checksum line: {line!r}")
        hashes[file_name.strip()] = digest.strip().lower()
    return hashes


def _verify_required_file(root: Path, file_name: str) -> Path:
    path = root / file_name
    if not path.is_file():
        raise FileNotFoundError(f"Snapshot file is required but missing: {file_name}")
    return path


def _verify_hashes(root: Path, required_files: list[str]) -> None:
    sha_path = _verify_required_file(root, PAYLOAD_SHA256SUMS)
    expected_hashes = _read_sha256sums(sha_path)
    for file_name in required_files:
        expected = expected_hashes.get(file_name)
        if not expected:
            raise ValueError(f"Snapshot checksum is missing required file: {file_name}")
        actual = _sha256_file(_verify_required_file(root, file_name))
        if actual != expected:
            raise ValueError(f"Snapshot checksum mismatch for {file_name}")


def _verify_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SNAPSHOT_MANIFEST_SCHEMA_VERSION:
        raise ValueError("Snapshot manifest schema_version is not supported")
    if manifest.get("authority") != SNAPSHOT_AUTHORITY:
        raise ValueError("Snapshot manifest authority is not supported")
    if manifest.get("mutation_authority") != "not_admitted":
        raise ValueError("Snapshot manifest must preserve mutation_authority not_admitted")


def _verify_payloads(
    manifest: dict[str, Any],
    candidate: dict[str, Any],
    admission_plan: dict[str, Any],
) -> None:
    candidate_id = manifest.get("candidate_id")
    if candidate.get("mutation_authority") != "not_admitted":
        raise ValueError("Snapshot candidate must preserve mutation_authority not_admitted")
    if admission_plan.get("mutation_authority") != "not_admitted":
        raise ValueError("Snapshot admission plan must preserve mutation_authority not_admitted")
    if candidate_id and candidate.get("candidate_id") != candidate_id:
        raise ValueError("Snapshot candidate_id does not match manifest")
    if candidate_id and admission_plan.get("candidate_id") != candidate_id:
        raise ValueError("Snapshot admission plan candidate_id does not match manifest")


@lru_cache(maxsize=1)
def load_project_import_snapshot_bundle() -> dict[str, Any] | None:
    root = _snapshot_root_from_env()
    if root is None:
        return None

    required_files = [PAYLOAD_CANDIDATE, PAYLOAD_ADMISSION_PLAN, PAYLOAD_MANIFEST]
    _verify_hashes(root, required_files)
    candidate = _read_json(root / PAYLOAD_CANDIDATE)
    admission_plan = _read_json(root / PAYLOAD_ADMISSION_PLAN)
    manifest = _read_json(root / PAYLOAD_MANIFEST)
    _verify_manifest(manifest)
    _verify_payloads(manifest, candidate, admission_plan)
    return {
        "root": str(root),
        "candidate": candidate,
        "admission_plan": admission_plan,
        "manifest": manifest,
    }


def load_project_import_candidate_snapshot() -> dict[str, Any] | None:
    bundle = load_project_import_snapshot_bundle()
    return None if bundle is None else dict(bundle["candidate"])


def load_project_import_admission_plan_snapshot() -> dict[str, Any] | None:
    bundle = load_project_import_snapshot_bundle()
    return None if bundle is None else dict(bundle["admission_plan"])
