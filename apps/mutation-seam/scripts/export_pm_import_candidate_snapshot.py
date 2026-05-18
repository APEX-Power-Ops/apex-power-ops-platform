from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.project_import_admission_plan import build_project_import_admission_plan
from app.project_import_candidate import clear_project_import_candidate_cache, load_project_import_candidate
from app.project_seed_sources import clear_project_seed_cache
from app.project_tracker_sources import clear_project_tracker_cache
from app.seed_workbooks import clear_seed_cache


SNAPSHOT_MANIFEST_SCHEMA_VERSION = "pm_import_candidate_snapshot_manifest_v1"
SNAPSHOT_AUTHORITY = "derived_source_snapshot_no_live"
PAYLOAD_CANDIDATE = "candidate.json"
PAYLOAD_ADMISSION_PLAN = "admission-plan.json"
PAYLOAD_MANIFEST = "manifest.json"
PAYLOAD_SHA256SUMS = "SHA256SUMS.txt"


def _set_env_from_args(args: argparse.Namespace) -> None:
    if args.planning_root:
        os.environ["APEX_PROJECT_MINER_PLANNING_ROOT"] = args.planning_root
    if args.estimator_workbook:
        os.environ["APEX_PROJECT_ESTIMATOR_WORKBOOK"] = args.estimator_workbook
    if args.sld_pdf:
        os.environ["APEX_PROJECT_SLD_PDF"] = args.sld_pdf
    if args.equipment_workbook:
        os.environ["APEX_FIELD_SEED_EQUIPMENT_WORKBOOK"] = args.equipment_workbook
    if args.capability_workbook:
        os.environ["APEX_FIELD_SEED_CAPABILITY_WORKBOOK"] = args.capability_workbook
    if args.data_entry_workbook:
        os.environ["APEX_PROJECT_DATA_ENTRY_WORKBOOK"] = args.data_entry_workbook
    if args.reference_tracker_workbook:
        os.environ["APEX_REFERENCE_TRACKER_WORKBOOK"] = args.reference_tracker_workbook


def _clear_caches() -> None:
    clear_project_import_candidate_cache()
    clear_project_seed_cache()
    clear_project_tracker_cache()
    clear_seed_cache()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, default=str) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _path_file_name(path_text: Any) -> str | None:
    if not path_text:
        return None
    text = str(path_text)
    if "\\" in text:
        return PureWindowsPath(text).name or None
    return Path(text).name or None


def _redact_source_file(source: dict[str, Any]) -> dict[str, Any]:
    file_name = _path_file_name(source.get("path"))
    extension = Path(file_name).suffix.lower() if file_name else None
    return {
        "source_id": source.get("source_id"),
        "label": source.get("label"),
        "file_name": file_name,
        "extension": extension,
        "found": bool(source.get("found")),
        "size_bytes": source.get("size_bytes"),
        "modified_at": source.get("modified_at"),
        "freshness_status": source.get("freshness_status"),
        "fingerprint": source.get("fingerprint"),
    }


def _warning_codes(candidate: dict[str, Any]) -> list[str]:
    return sorted(
        str(warning.get("code"))
        for warning in candidate.get("warnings", [])
        if warning.get("code")
    )


def _git_output(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_dirty_state() -> str:
    status = _git_output("status", "--short")
    if status == "unknown":
        return "unknown"
    return "dirty" if status else "clean"


def build_snapshot_manifest(
    candidate: dict[str, Any],
    admission_plan: dict[str, Any],
    payload_hashes: dict[str, str],
    *,
    generated_at_utc: str | None = None,
    generator_repo_head: str | None = None,
    generator_dirty_state: str | None = None,
) -> dict[str, Any]:
    summary = candidate.get("summary", {})
    source_freshness = candidate.get("source_freshness", {})
    source_files = source_freshness.get("source_files", [])
    return {
        "schema_version": SNAPSHOT_MANIFEST_SCHEMA_VERSION,
        "authority": SNAPSHOT_AUTHORITY,
        "generated_at_utc": generated_at_utc
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator_repo_head": generator_repo_head or _git_output("rev-parse", "HEAD"),
        "generator_dirty_state": generator_dirty_state or _git_dirty_state(),
        "candidate_id": candidate.get("candidate_id"),
        "candidate_version": candidate.get("candidate_version"),
        "admission_plan_version": admission_plan.get("admission_plan_version"),
        "mutation_authority": candidate.get("mutation_authority"),
        "source_stat_fingerprint": admission_plan.get("source_stat_fingerprint")
        or source_freshness.get("aggregate_fingerprint"),
        "candidate_shape_fingerprint": admission_plan.get("candidate_shape_fingerprint"),
        "workpackage_count": summary.get("workpackage_count"),
        "task_count": summary.get("task_count"),
        "apparatus_candidate_count": summary.get("apparatus_candidate_count"),
        "warning_codes": _warning_codes(candidate),
        "payload_files": [
            {"file_name": file_name, "sha256": payload_hash}
            for file_name, payload_hash in sorted(payload_hashes.items())
        ],
        "source_files_redacted": [
            _redact_source_file(source)
            for source in source_files
            if isinstance(source, dict)
        ],
        "not_allowed_now": [
            "approval_post",
            "approval_row_creation",
            "project_import",
            "supabase_write",
            "render_env_update",
            "render_deploy",
            "hosted_loader",
            "source_workbook_writeback",
            "source_pdf_edit",
            "workbook_macro",
            "business_state_mutation",
        ],
    }


def _prepare_output_dir(output_dir: Path, *, allow_repo_output: bool, overwrite: bool) -> None:
    resolved_output = output_dir.resolve()
    if _is_relative_to(resolved_output, REPO_ROOT) and not allow_repo_output:
        raise ValueError(
            "Snapshot output inside the repo is blocked by default; pass --allow-repo-output only for an admitted ignored runtime path."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = [path for path in output_dir.iterdir() if path.name in {PAYLOAD_CANDIDATE, PAYLOAD_ADMISSION_PLAN, PAYLOAD_MANIFEST, PAYLOAD_SHA256SUMS}]
    if existing and not overwrite:
        names = ", ".join(sorted(path.name for path in existing))
        raise FileExistsError(f"Snapshot output files already exist: {names}. Pass --overwrite to replace them.")


def export_project_import_candidate_snapshot(
    candidate: dict[str, Any],
    admission_plan: dict[str, Any],
    output_dir: Path,
    *,
    allow_repo_output: bool = False,
    overwrite: bool = False,
    generated_at_utc: str | None = None,
    generator_repo_head: str | None = None,
    generator_dirty_state: str | None = None,
) -> dict[str, Any]:
    _prepare_output_dir(output_dir, allow_repo_output=allow_repo_output, overwrite=overwrite)

    candidate_bytes = _json_bytes(candidate)
    admission_plan_bytes = _json_bytes(admission_plan)
    payload_hashes = {
        PAYLOAD_CANDIDATE: _sha256(candidate_bytes),
        PAYLOAD_ADMISSION_PLAN: _sha256(admission_plan_bytes),
    }
    manifest = build_snapshot_manifest(
        candidate,
        admission_plan,
        payload_hashes,
        generated_at_utc=generated_at_utc,
        generator_repo_head=generator_repo_head,
        generator_dirty_state=generator_dirty_state,
    )
    manifest_bytes = _json_bytes(manifest)
    all_hashes = {
        **payload_hashes,
        PAYLOAD_MANIFEST: _sha256(manifest_bytes),
    }

    (output_dir / PAYLOAD_CANDIDATE).write_bytes(candidate_bytes)
    (output_dir / PAYLOAD_ADMISSION_PLAN).write_bytes(admission_plan_bytes)
    (output_dir / PAYLOAD_MANIFEST).write_bytes(manifest_bytes)
    sha256sums = "".join(f"{digest}  {file_name}\n" for file_name, digest in sorted(all_hashes.items()))
    (output_dir / PAYLOAD_SHA256SUMS).write_text(sha256sums, encoding="utf-8")

    return {
        "output_dir": str(output_dir),
        "manifest_path": str(output_dir / PAYLOAD_MANIFEST),
        "sha256sums_path": str(output_dir / PAYLOAD_SHA256SUMS),
        "files": sorted([*all_hashes.keys(), PAYLOAD_SHA256SUMS]),
        "sha256": all_hashes,
        "manifest": manifest,
        "mutation_authority": candidate.get("mutation_authority"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a hash-signed, runtime-only Project Miner import candidate snapshot without writing database state.",
    )
    parser.add_argument("--output-dir", required=True, help="Explicit runtime output directory for snapshot files.")
    parser.add_argument("--allow-repo-output", action="store_true", help="Allow output under this repository only when a packet admits an ignored runtime path.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing snapshot output files in the output directory.")
    parser.add_argument("--planning-root", help="Folder containing Project Miner source files.")
    parser.add_argument("--estimator-workbook", help="Specific estimator workbook to preview.")
    parser.add_argument("--sld-pdf", help="Specific SLD or drawing PDF to preview.")
    parser.add_argument("--equipment-workbook", help="Specific equipment inventory workbook to preview.")
    parser.add_argument("--capability-workbook", help="Specific technician capability workbook to preview.")
    parser.add_argument("--data-entry-workbook", help="Specific RESA project data entry workbook to preview.")
    parser.add_argument("--reference-tracker-workbook", help="Specific reference tracker workbook to preview.")
    args = parser.parse_args()

    _set_env_from_args(args)
    _clear_caches()
    candidate = load_project_import_candidate()
    admission_plan = build_project_import_admission_plan(candidate)
    result = export_project_import_candidate_snapshot(
        candidate,
        admission_plan,
        Path(args.output_dir),
        allow_repo_output=args.allow_repo_output,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
