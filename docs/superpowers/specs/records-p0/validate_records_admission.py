#!/usr/bin/env python3
"""Fail-closed, DB-free validator for the Records admission packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "1.0.0"
GOAL_ID = "RECORDS-P0-AUTHORITY-AND-P1-ADMISSION-FRAMEWORK-001"
CANDIDATE_ID = "RECORDS-FIRST-SLICE-2026-07"
AUDIT_PATH = "/home/olares/code/apex/apex-learning-lane/notes/platform-status/2026-07-14-records-platform-and-field-execution-audit.md"
TOP_KEYS = set(
    "schema_version goal_id fixture_kind bindings candidate ratified_precedents "
    "open_human_decisions technical_invariants serving_guardrails authority_emissions "
    "acceptance_contract first_slice_candidates recommendation changed_paths".split()
)
ACCEPTANCE = (
    "office_user", "technician", "project", "apparatus", "template", "offline_capture",
    "reconnect", "governed_review", "acceptance_decision", "evidence_readback",
)
EMISSION_KEYS = set(
    "schema_change credential_minting deployment production_action role_activation "
    "data_api_exposure product_implementation".split()
)
FORBIDDEN_IDENTITIES = {
    "postgres", "records_fn_owner", "records_owner", "records_reclaim_owner", "service_role",
}
ROLE_CEILING = {"records_api", "records_auditor", "records_intake_writer"}
AUTHORIZED_PATHS = {
    ".github/workflows/records-authority-admission-ci.yml",
    "docs/lanes/README.md",
    "docs/superpowers/specs/records-p0/2026-07-16-records-p0-final-handoff.md",
    "docs/superpowers/specs/records-p0/2026-07-16-records-p0-review-record.md",
    "docs/superpowers/specs/records-p0/PRODUCT-ADMISSION-FRAMEWORK.md",
    "docs/superpowers/specs/records-p0/PROPOSED-FIRST-SLICE-DECISION-PACKET.md",
    "docs/superpowers/specs/records-p0/records-admission-manifest.json",
    "docs/superpowers/specs/records-p0/test_records_status_authority.py",
    "docs/superpowers/specs/records-p0/test_validate_records_admission.py",
    "docs/superpowers/specs/records-p0/validate_records_admission.py",
    "infra/database/migrations/records/MANIFEST.md",
    "reference/records/CURRENT-STATE.md",
    "reference/records/PUNCHLIST.md",
}
FORBIDDEN_PATHS = {
    "reference/records/SERVING_CONTRACT.md",
    "reference/records/SERVING_CONTRACT.yaml",
    "reference/records/test_serving_contract.py",
    "docs/operations/RECORDS-PROD-APPLY-EVIDENCE-2026-07-07.md",
}
ARTIFACT_PATHS = {
    "docs/superpowers/specs/records-p0/PRODUCT-ADMISSION-FRAMEWORK.md",
    "docs/superpowers/specs/records-p0/PROPOSED-FIRST-SLICE-DECISION-PACKET.md",
    "reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md",
    "reference/records/SERVING_CONTRACT.md",
    "reference/records/SERVING_CONTRACT.yaml",
    "reference/records/04-LV-CB-DATASHEET-SPEC.md",
    "reference/records/06-TRANSFORMER-DATASHEET-SPEC.md",
    "reference/records/10-GROUNDING-DATASHEET-SPEC.md",
    "reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md",
}
# path: (Git blob at the frozen base, SHA-256)
CANON = {
    "reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md": ("f02390980ac8d6f4dd97081481061eb911dd48b9", "ad404a27384e0262f3b0b005083c1c3d63314032ae4bd2b333be32d5c53628c0"),
    "reference/records/SERVING_CONTRACT.md": ("009abd4765b7f5ef30f0cecc408d111721f871ef", "d38a111046a7717e8ea5da82cfce4f2269602b8d0c61bff35d2d9211d04db1fa"),
    "reference/records/SERVING_CONTRACT.yaml": ("96eae45f751754e8ce50413a3e8448c866c05026", "e9b25be4c65665eebe19ea17b45a8769d5b9f63515b49531cf45432d12f4c8b6"),
    "reference/records/04-LV-CB-DATASHEET-SPEC.md": ("a18ac8a19f77df5b924112575aca8e924543edf6", "2d3fb3a34d7e231f4ba5d42060a780f37c9c4c17b8cfb9e64e837d1dc806478f"),
    "reference/records/06-TRANSFORMER-DATASHEET-SPEC.md": ("9f92017c65d4d9aec137376486b25ebcc88495ea", "accb8b7540979f70f99a92203a40a8b7f6381309f8ca68d171a776202902a320"),
    "reference/records/10-GROUNDING-DATASHEET-SPEC.md": ("f461df75e559b4256944d5c2f27885f56fc581b2", "af55fa3266bb7da32b022b18e1b1f8fd9758e46833913c96bd43ee4055edb339"),
    "reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md": ("378501ed523b1a0bbf218dfd559b0d2e191203cc", "71ef99d353cde389d813c3ddcad2eb7110c5d2f414fc6cba8959a3cecf8c13fe"),
}
OFFLINE_IDENTITY = "Jason Swenson, operator named by the ruled architecture record"
SERVING_IDENTITY = "Jason Swenson, author of the canonical Gate 9 v2 serving-contract commit"
OFFLINE_LOCATOR = "git:3d3ca14f547fb5ae9e8c3ceafd3f2ceda7785bfa:reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md@blob:f02390980ac8d6f4dd97081481061eb911dd48b9"
SERVING_LOCATOR = "git:a3f4cab25045017b332970a30fc974a7d19db0a9:reference/records/SERVING_CONTRACT.yaml@blob:96eae45f751754e8ce50413a3e8448c866c05026"
OFFLINE_SUPERSESSION = "A signed operator amendment must bind and supersede this ruled architecture artifact before dependent work."
SERVING_TRANSPORT_SUPERSESSION = "A signed Gate 5 posture decision must bind the superseded contract and land before any serving or grant change."
DATA_API_SUPERSESSION = "A signed Gate 5 posture decision must bind the superseded contract; exposure cannot be enabled by configuration drift."
PRIVILEGE_SUPERSESSION = "A signed Gate 5 posture decision must re-open the privilege boundary; owner or bypass runtime DSNs remain prohibited."
OFFLINE_AUTH = (
    OFFLINE_IDENTITY, OFFLINE_LOCATOR,
    CANON["reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md"][1],
    "2026-06-14T19:44:21-07:00", OFFLINE_SUPERSESSION,
)
SERVING_AUTH = (SERVING_IDENTITY, SERVING_LOCATOR, CANON["reference/records/SERVING_CONTRACT.yaml"][1], "2026-07-04T01:57:46+00:00")
# code: (subject, choice, exact identity/locator/digest/timestamp/supersession tuple)
PRECEDENTS = {
    "REC-R001": ("installable_pwa_client", "installable_pwa", OFFLINE_AUTH),
    "REC-R002": ("fully_offline_field_operation", "zero_connectivity_full_job", OFFLINE_AUTH),
    "REC-R003": ("sync_engine", "powersync", OFFLINE_AUTH),
    "REC-R004": ("serving_transport", "separate_direct_role_dsn", (*SERVING_AUTH, SERVING_TRANSPORT_SUPERSESSION)),
    "REC-R005": ("data_api_posture", "records_schema_excluded", (*SERVING_AUTH, DATA_API_SUPERSESSION)),
    "REC-R006": ("runtime_privilege_ceiling", "owners_superusers_and_bypass_identities_forbidden", (*SERVING_AUTH, PRIVILEGE_SUPERSESSION)),
}
DECISIONS = {
    "REC-D001": "First consumer, accountable owner, and release acceptor",
    "REC-D002": "Authorization tenancy and row-scope model",
    "REC-D003": "Authoritative human, device, and service-principal identity sources",
    "REC-D004": "Device assignment and revocation",
    "REC-D005": "Source-content use posture",
    "REC-D006": "Lifecycle, reviewer separation, and amendment semantics",
    "REC-D007": "Retention, legal hold, deletion, backup, and restore",
    "REC-D008": "Asset-tag scope and soft-reference reconciliation ownership",
    "REC-D009": "Exact first apparatus, template, and capture-mode slice",
    "REC-D010": "PowerSync hosting, operations, and custody",
    "REC-D011": "Acceptance evidence and signatory",
}
INVARIANTS = {
    "REC-I001": "Verified issuer, audience, signature, expiry, and token use",
    "REC-I002": "Server-side scope mapping and cross-project denial",
    "REC-I003": "Atomic route, idempotency key, request hash, mutation, audit, and response claim",
    "REC-I004": "Exact-response replay and same-key different-body rejection",
    "REC-I005": "Server-known device binding and monotonic revision compare-and-swap",
    "REC-I006": "Separate office and device authority",
    "REC-I007": "Governed lifecycle transitions and reviewer separation",
    "REC-I008": "Template, key, requiredness, kind, value, unit, and option validation",
    "REC-I009": "Immutable accepted evidence and controlled amendments",
}
# code: (apparatus, template, mode, path, blob, SHA-256)
SLICES = {
    "RFS-GROUNDING": ("grounding_system", "ats_grounding_v1", "field_entry", "reference/records/10-GROUNDING-DATASHEET-SPEC.md", *CANON["reference/records/10-GROUNDING-DATASHEET-SPEC.md"]),
    "RFS-LV-CB": ("cb_lv", "ats_lv_cb_v1", "field_entry", "reference/records/04-LV-CB-DATASHEET-SPEC.md", *CANON["reference/records/04-LV-CB-DATASHEET-SPEC.md"]),
    "RFS-DRY-XFMR": ("xfmr_dry", "ats_dry_xfmr_v1", "field_entry", "reference/records/06-TRANSFORMER-DATASHEET-SPEC.md", *CANON["reference/records/06-TRANSFORMER-DATASHEET-SPEC.md"]),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER_RE = re.compile(r"(^|[^a-z0-9])(todo|tbd|placeholder|unknown|n/?a|not decided|pending authority)([^a-z0-9]|$)", re.I)
AI_RE = re.compile(r"(^|[^a-z0-9])(codex|claude|chatgpt|artificial intelligence|ai[-_ ]?inferred)([^a-z0-9]|$)", re.I)


class DuplicateKeyError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"cannot parse admission manifest: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError("admission manifest root must be an object")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=False, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=not binary,
    )


def _forbidden_path(path: str) -> bool:
    return (
        path.endswith(".sql") or path.startswith(("apps/", "packages/"))
        or path in FORBIDDEN_PATHS or "PROD-APPLY-EVIDENCE" in path
        or "SERVING_CONTRACT" in path or "importer" in path.casefold()
    )


class Checker:
    def __init__(
        self,
        document: dict[str, Any],
        root: Path,
        base: str,
        tree: str,
        audit: str,
        *,
        audit_artifact: Path | None,
        external_audit_binding_only: bool,
    ) -> None:
        self.doc, self.root, self.base, self.tree, self.audit = document, root, base, tree, audit
        self.audit_artifact = audit_artifact
        self.external_audit_binding_only = external_audit_binding_only
        self.audit_artifact_verified = False
        self.fixture = "invalid"
        self.diag: list[dict[str, str]] = []
        self.artifacts: dict[str, str] = {}
        self.unresolved: list[str] = []

    def add(self, code: str, path: str, message: str) -> None:
        self.diag.append({"code": code, "path": path, "message": message})

    def obj(self, value: Any, path: str, keys: set[str], code: str = "REC-A001") -> dict[str, Any]:
        if not isinstance(value, dict):
            self.add(code, path, "must be an object")
            return {}
        if set(value) != keys:
            self.add(code, path, f"object keys differ; missing={sorted(keys - set(value))}, extra={sorted(set(value) - keys)}")
        return value

    def arr(self, value: Any, path: str, code: str) -> list[Any]:
        if not isinstance(value, list):
            self.add(code, path, "must be an array")
            return []
        return value

    def text(self, value: Any, path: str, code: str) -> str:
        if not isinstance(value, str) or not value.strip():
            self.add(code, path, "must be a non-empty string")
            return ""
        return value

    def false(self, value: Any, path: str, code: str) -> None:
        if value is not False:
            self.add(code, path, "must be the literal boolean false")

    def authority(
        self,
        value: Any,
        path: str,
        exact: tuple[str, str, str, str, str] | None = None,
    ) -> dict[str, Any]:
        keys = {"identity", "immutable_locator", "digest_algorithm", "digest", "timestamp", "supersession_rule"}
        item = self.obj(value, path, keys, "REC-A003")
        identity = self.text(item.get("identity"), f"{path}/identity", "REC-A003")
        locator = self.text(item.get("immutable_locator"), f"{path}/immutable_locator", "REC-A003")
        digest = self.text(item.get("digest"), f"{path}/digest", "REC-A003")
        timestamp = self.text(item.get("timestamp"), f"{path}/timestamp", "REC-A003")
        supersession = self.text(item.get("supersession_rule"), f"{path}/supersession_rule", "REC-A003")
        if identity and (PLACEHOLDER_RE.search(identity) or AI_RE.search(identity)):
            self.add("REC-A003", f"{path}/identity", "placeholder or AI authority is forbidden")
        if item.get("digest_algorithm") != "sha256":
            self.add("REC-A003", f"{path}/digest_algorithm", "must equal sha256")
        if digest and not SHA256_RE.fullmatch(digest):
            self.add("REC-A003", f"{path}/digest", "invalid SHA-256 digest")
        immutable = re.search(r"[0-9a-f]{40}", locator) or re.fullmatch(r"(?:urn:)?sha256:[0-9a-f]{64}", locator)
        mutable = re.search(r"(^|[:/@])(main|master|head|branch|refs/heads)([:/@]|$)", locator, re.I)
        if locator and (not immutable or mutable):
            self.add("REC-A003", f"{path}/immutable_locator", "must be immutable")
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            valid_time = parsed.tzinfo is not None and parsed.utcoffset() is not None
        except ValueError:
            valid_time = False
        if timestamp and not valid_time:
            self.add("REC-A003", f"{path}/timestamp", "timestamp needs timezone")
        if supersession and PLACEHOLDER_RE.search(supersession):
            self.add("REC-A003", f"{path}/supersession_rule", "placeholder supersession is forbidden")
        if exact and (identity, locator, digest, timestamp, supersession) != exact:
            self.add("REC-A003", path, "ratified authority differs from immutable precedent")
        return item

    def inventory(self, value: Any, path: str, expected: set[str], code: str) -> list[Any]:
        items = self.arr(value, path, code)
        codes = [item.get("code") for item in items if isinstance(item, dict) and isinstance(item.get("code"), str)]
        duplicates = sorted(key for key, count in Counter(codes).items() if count > 1)
        if duplicates:
            self.add(code, path, f"duplicate codes: {duplicates}")
        if set(codes) != expected or len(codes) != len(expected):
            self.add(code, path, f"code inventory differs: {sorted(codes)}")
        return items

    def safe_file(self, raw: Any, path: str) -> Path | None:
        text = self.text(raw, path, "REC-A005")
        pure = PurePosixPath(text)
        if not text or pure.is_absolute() or "\\" in text or any(part in {"", ".", ".."} for part in pure.parts):
            self.add("REC-A005", path, "unsafe artifact path")
            return None
        candidate = self.root.joinpath(*pure.parts)
        try:
            candidate.resolve(strict=False).relative_to(self.root.resolve())
        except ValueError:
            self.add("REC-A005", path, "artifact escapes repository")
            return None
        cursor = candidate
        while cursor != self.root and cursor != cursor.parent:
            if cursor.is_symlink():
                self.add("REC-A005", path, "artifact may not use symlinks")
                return None
            cursor = cursor.parent
        if not candidate.is_file():
            self.add("REC-A005", path, "artifact is not a file")
            return None
        return candidate

    def git_blob(self, commit: str, path: str, blob: str, locus: str) -> None:
        result = _git(self.root, "rev-parse", f"{commit}:{path}")
        if result.returncode or result.stdout.strip() != blob:
            self.add("REC-A005", locus, "commit/path does not resolve to declared blob")

    def bindings(self) -> None:
        item = self.obj(self.doc.get("bindings"), "/bindings", {"base_commit", "base_tree", "audit", "artifacts"}, "REC-A004")
        if item.get("base_commit") != self.base:
            self.add("REC-A004", "/bindings/base_commit", "stale base")
        if item.get("base_tree") != self.tree:
            self.add("REC-A004", "/bindings/base_tree", "stale base tree")
        audit = self.obj(item.get("audit"), "/bindings/audit", {"path", "digest_algorithm", "digest"}, "REC-A004")
        if audit.get("path") != AUDIT_PATH:
            self.add("REC-A004", "/bindings/audit/path", "wrong audit locator")
        if audit.get("digest_algorithm") != "sha256":
            self.add("REC-A004", "/bindings/audit/digest_algorithm", "must equal sha256")
        manifest_digest = audit.get("digest")
        manifest_digest_valid = (
            isinstance(manifest_digest, str)
            and SHA256_RE.fullmatch(manifest_digest) is not None
        )
        expected_digest_valid = SHA256_RE.fullmatch(self.audit) is not None
        if not manifest_digest_valid:
            self.add("REC-A004", "/bindings/audit/digest", "invalid audit SHA-256 digest")
        if not expected_digest_valid:
            self.add("REC-A004", "/bindings/audit/digest", "invalid frozen audit SHA-256 digest")
        if manifest_digest != self.audit:
            self.add(
                "REC-A004",
                "/bindings/audit/digest",
                "manifest audit digest differs from frozen expectation",
            )

        actual_digest = ""
        artifact_readable = False
        if self.audit_artifact is None:
            if not self.external_audit_binding_only:
                self.add(
                    "REC-A004",
                    "/bindings/audit",
                    "authorized audit artifact verification is required",
                )
        elif self.audit_artifact != Path(AUDIT_PATH):
            self.add(
                "REC-A004",
                "/bindings/audit/path",
                "audit artifact path differs from authorized locator",
            )
        elif self.audit_artifact.is_symlink():
            self.add("REC-A004", "/bindings/audit/path", "audit artifact may not be a symlink")
        elif not self.audit_artifact.is_file():
            self.add("REC-A004", "/bindings/audit/path", "audit artifact is not a file")
        else:
            try:
                actual_digest = _sha256(self.audit_artifact)
                artifact_readable = True
            except OSError as exc:
                self.add(
                    "REC-A004",
                    "/bindings/audit/path",
                    f"cannot hash audit artifact: {exc}",
                )
        if artifact_readable:
            if actual_digest != manifest_digest:
                self.add(
                    "REC-A004",
                    "/bindings/audit/digest",
                    "audit artifact digest differs from manifest binding",
                )
            if actual_digest != self.audit:
                self.add(
                    "REC-A004",
                    "/bindings/audit/digest",
                    "audit artifact digest differs from frozen expectation",
                )
            self.audit_artifact_verified = (
                audit.get("path") == AUDIT_PATH
                and audit.get("digest_algorithm") == "sha256"
                and manifest_digest_valid
                and expected_digest_valid
                and actual_digest == manifest_digest == self.audit
            )

        entries = self.arr(item.get("artifacts"), "/bindings/artifacts", "REC-A005")
        paths: list[str] = []
        for index, raw in enumerate(entries):
            locus = f"/bindings/artifacts/{index}"
            bound = self.obj(raw, locus, {"path", "digest_algorithm", "digest"}, "REC-A005")
            path, digest = bound.get("path"), bound.get("digest")
            if isinstance(path, str):
                paths.append(path)
            if bound.get("digest_algorithm") != "sha256":
                self.add("REC-A005", f"{locus}/digest_algorithm", "must equal sha256")
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                self.add("REC-A005", f"{locus}/digest", "invalid SHA-256 digest")
                digest = ""
            file = self.safe_file(path, f"{locus}/path")
            if file and digest and _sha256(file) != digest:
                self.add("REC-A005", f"{locus}/digest", "artifact digest mismatch")
            if isinstance(path, str) and digest:
                self.artifacts[path] = digest
        if set(paths) != ARTIFACT_PATHS or len(paths) != len(ARTIFACT_PATHS) or len({path.casefold() for path in paths}) != len(paths):
            self.add("REC-A005", "/bindings/artifacts", "artifact inventory differs")
        for path, (blob, digest) in CANON.items():
            if self.artifacts.get(path) != digest:
                self.add("REC-A005", f"/bindings/artifacts/{path}", "canonical digest differs")
            self.git_blob(self.base, path, blob, f"/bindings/artifacts/{path}")

    def candidate(self) -> dict[str, Any]:
        keys = {"id", "decision_status", "implementation_readiness", "execution_authorized"}
        item = self.obj(self.doc.get("candidate"), "/candidate", keys, "REC-A002")
        candidate_id = self.text(item.get("id"), "/candidate/id", "REC-A002")
        if candidate_id and candidate_id != CANDIDATE_ID:
            self.add("REC-A002", "/candidate/id", "candidate ID differs from frozen packet")
        self.false(item.get("execution_authorized"), "/candidate/execution_authorized", "REC-A009")
        state = (item.get("decision_status"), item.get("implementation_readiness"))
        if state[0] not in {"proposed", "accepted"}:
            self.add("REC-A002", "/candidate/decision_status", "unknown state")
        if state[1] not in {"held", "ready"}:
            self.add("REC-A002", "/candidate/implementation_readiness", "unknown state")
        expected = ("proposed", "held") if self.fixture == "real" else ("accepted", "ready")
        if state != expected:
            self.add("REC-A002", "/candidate", f"{self.fixture} state must be {expected}")
        return item

    def precedents(self) -> None:
        for index, raw in enumerate(self.inventory(self.doc.get("ratified_precedents"), "/ratified_precedents", set(PRECEDENTS), "REC-A003")):
            path = f"/ratified_precedents/{index}"
            item = self.obj(raw, path, {"code", "subject", "choice", "authority"}, "REC-A003")
            semantic = PRECEDENTS.get(item.get("code"))
            if not semantic:
                self.authority(item.get("authority"), f"{path}/authority")
                continue
            subject, choice, exact = semantic
            if (item.get("subject"), item.get("choice")) != (subject, choice):
                self.add("REC-A003", path, "precedent semantics differ")
            authority = self.authority(item.get("authority"), f"{path}/authority", exact)
            artifact = "reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md" if item.get("code") in {"REC-R001", "REC-R002", "REC-R003"} else "reference/records/SERVING_CONTRACT.yaml"
            if self.artifacts.get(artifact) != authority.get("digest"):
                self.add("REC-A005", f"{path}/authority/digest", "wrong authority artifact")

    def states(self, key: str, path: str, semantics: dict[str, str], code: str, real: str, synthetic: str, proof: str) -> None:
        for index, raw in enumerate(self.inventory(self.doc.get(key), path, set(semantics), code)):
            locus = f"{path}/{index}"
            if not isinstance(raw, dict):
                self.add(code, locus, "must be an object")
                continue
            state = raw.get("state")
            keys = {"code", "title", "state"} | ({proof} if state == synthetic else set())
            item = self.obj(raw, locus, keys, code)
            item_code = item.get("code")
            if item_code in semantics and item.get("title") != semantics[item_code]:
                self.add(code, f"{locus}/title", "stable semantics differ")
            if state not in {real, synthetic}:
                self.add(code, f"{locus}/state", "unknown state")
            if state == synthetic:
                self.authority(item.get(proof), f"{locus}/{proof}")
            wanted = real if self.fixture == "real" else synthetic
            if state != wanted:
                self.add(code, f"{locus}/state", f"{self.fixture} fixture requires {wanted}")
            if key == "open_human_decisions" and state == "unresolved" and isinstance(item_code, str):
                self.unresolved.append(item_code)
        self.unresolved = sorted(set(self.unresolved))

    def guardrails(self) -> None:
        keys = {"data_api_exposed", "runtime_identities", "forbidden_runtime_identities", "serving_role_ceiling", "migration_replay_authorized"}
        item = self.obj(self.doc.get("serving_guardrails"), "/serving_guardrails", keys, "REC-A008")
        self.false(item.get("data_api_exposed"), "/serving_guardrails/data_api_exposed", "REC-A008")
        self.false(item.get("migration_replay_authorized"), "/serving_guardrails/migration_replay_authorized", "REC-A008")
        forbidden = self.arr(item.get("forbidden_runtime_identities"), "/serving_guardrails/forbidden_runtime_identities", "REC-A008")
        ceiling = self.arr(item.get("serving_role_ceiling"), "/serving_guardrails/serving_role_ceiling", "REC-A008")
        if set(forbidden) != FORBIDDEN_IDENTITIES or len(forbidden) != len(FORBIDDEN_IDENTITIES):
            self.add("REC-A008", "/serving_guardrails/forbidden_runtime_identities", "inventory differs")
        if set(ceiling) != ROLE_CEILING or len(ceiling) != len(ROLE_CEILING):
            self.add("REC-A008", "/serving_guardrails/serving_role_ceiling", "ceiling differs")
        runtime = self.arr(item.get("runtime_identities"), "/serving_guardrails/runtime_identities", "REC-A008")
        if self.fixture == "real" and runtime:
            self.add("REC-A008", "/serving_guardrails/runtime_identities", "real candidate admits no runtime")
        names: list[str] = []
        for index, raw in enumerate(runtime):
            path = f"/serving_guardrails/runtime_identities/{index}"
            identity = self.obj(raw, path, {"name", "owner", "superuser", "bypassrls"}, "REC-A008")
            name = self.text(identity.get("name"), f"{path}/name", "REC-A008").casefold()
            names.append(name)
            if name in FORBIDDEN_IDENTITIES or name.endswith("_owner") or "bypass" in name or "superuser" in name or name not in ROLE_CEILING:
                self.add("REC-A008", f"{path}/name", "privileged runtime identity")
            for flag in ("owner", "superuser", "bypassrls"):
                self.false(identity.get(flag), f"{path}/{flag}", "REC-A008")
        if len(names) != len(set(names)):
            self.add("REC-A008", "/serving_guardrails/runtime_identities", "duplicate identity")

    def emissions_acceptance(self) -> None:
        emissions = self.obj(self.doc.get("authority_emissions"), "/authority_emissions", EMISSION_KEYS, "REC-A009")
        for key in EMISSION_KEYS:
            self.false(emissions.get(key), f"/authority_emissions/{key}", "REC-A009")
        acceptance = self.obj(self.doc.get("acceptance_contract"), "/acceptance_contract", {"elements", "ptm_office_import_is_field_proof"}, "REC-A010")
        if tuple(self.arr(acceptance.get("elements"), "/acceptance_contract/elements", "REC-A010")) != ACCEPTANCE:
            self.add("REC-A010", "/acceptance_contract/elements", "fixed contract differs")
        self.false(acceptance.get("ptm_office_import_is_field_proof"), "/acceptance_contract/ptm_office_import_is_field_proof", "REC-A010")

    def slices(self) -> None:
        items = self.arr(self.doc.get("first_slice_candidates"), "/first_slice_candidates", "REC-A011")
        if not 1 <= len(items) <= 3:
            self.add("REC-A011", "/first_slice_candidates", "must contain one to three candidates")
        codes: list[str] = []
        selected: list[str] = []
        for index, raw in enumerate(items):
            path = f"/first_slice_candidates/{index}"
            keys = {"code", "apparatus_key", "template_key", "capture_mode", "decision_status", "execution_authorized", "selected", "source_binding"}
            item = self.obj(raw, path, keys, "REC-A011")
            code = self.text(item.get("code"), f"{path}/code", "REC-A011")
            codes.append(code)
            self.false(item.get("execution_authorized"), f"{path}/execution_authorized", "REC-A009")
            if item.get("selected") is True:
                selected.append(code)
            elif item.get("selected") is not False:
                self.add("REC-A011", f"{path}/selected", "must be boolean")
            source = self.obj(item.get("source_binding"), f"{path}/source_binding", {"path", "git_blob", "digest_algorithm", "digest"}, "REC-A011")
            semantic = SLICES.get(code)
            if semantic:
                apparatus, template, mode, src_path, blob, digest = semantic
                actual = (item.get("apparatus_key"), item.get("template_key"), item.get("capture_mode"), source.get("path"), source.get("git_blob"), source.get("digest"))
                if actual != semantic or source.get("digest_algorithm") != "sha256":
                    self.add("REC-A011", path, "slice semantics or binding differs")
                if self.artifacts.get(src_path) != digest:
                    self.add("REC-A005", f"{path}/source_binding", "slice artifact differs")
                self.git_blob(self.base, src_path, blob, f"{path}/source_binding")
            status = item.get("decision_status")
            if self.fixture == "real" and (status != "proposed" or item.get("selected") is not False):
                self.add("REC-A011", path, "real slice must be proposed and unselected")
            elif self.fixture == "synthetic":
                wanted = "accepted" if item.get("selected") is True else "proposed"
                if status != wanted:
                    self.add("REC-A011", path, f"synthetic slice must be {wanted}")
        if set(codes) != set(SLICES) or len(codes) != len(SLICES):
            self.add("REC-A011", "/first_slice_candidates", "slice inventory differs")

        rec = self.obj(self.doc.get("recommendation"), "/recommendation", {"candidate_code", "decision_status", "ratified", "selected", "execution_authorized"}, "REC-A011")
        self.false(rec.get("execution_authorized"), "/recommendation/execution_authorized", "REC-A009")
        if rec.get("candidate_code") != "RFS-GROUNDING":
            self.add("REC-A011", "/recommendation/candidate_code", "wrong recommendation")
        actual = (rec.get("decision_status"), rec.get("ratified"), rec.get("selected"))
        expected = ("proposed", False, False) if self.fixture == "real" else ("accepted", True, True)
        wanted_selected = [] if self.fixture == "real" else ["RFS-GROUNDING"]
        if actual != expected or selected != wanted_selected:
            self.add("REC-A011", "/recommendation", "recommendation state differs")

    def changed_paths(self) -> list[str]:
        paths = self.arr(self.doc.get("changed_paths"), "/changed_paths", "REC-A012")
        valid_strings = all(isinstance(path, str) and path for path in paths)
        if not valid_strings or paths != sorted(paths) or len(paths) != len(set(paths)) or set(paths) != AUTHORIZED_PATHS:
            self.add("REC-A012", "/changed_paths", "must equal exact sorted authorized paths")
        for index, path in enumerate(paths):
            if not isinstance(path, str):
                continue
            pure = PurePosixPath(path)
            if pure.is_absolute() or "\\" in path or any(part in {"", ".", ".."} for part in pure.parts) or _forbidden_path(path):
                self.add("REC-A012", f"/changed_paths/{index}", "unsafe changed path")
        return [path for path in paths if isinstance(path, str)]

    def parse_status(self, payload: bytes) -> list[tuple[str, list[str]]]:
        tokens = payload.rstrip(b"\0").split(b"\0") if payload else []
        result: list[tuple[str, list[str]]] = []
        index = 0
        try:
            while index < len(tokens):
                status = tokens[index].decode("ascii")
                count = 2 if status[:1] in {"R", "C"} else 1
                names = [tokens[index + offset].decode("utf-8", "surrogateescape") for offset in range(1, count + 1)]
                result.append((status, names))
                index += count + 1
        except (IndexError, UnicodeError):
            self.add("REC-A012", "/changed_paths", "cannot parse Git status")
        return result

    def verify_git(self, declared: list[str]) -> None:
        tree = _git(self.root, "rev-parse", f"{self.base}^{{tree}}")
        if tree.returncode or tree.stdout.strip() != self.tree:
            self.add("REC-A004", "/bindings/base_tree", "Git cannot prove base tree")
        if _git(self.root, "merge-base", "--is-ancestor", self.base, "HEAD").returncode:
            self.add("REC-A012", "/changed_paths", "base is not ancestor of HEAD")
        dirty = _git(self.root, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True)
        if dirty.returncode or dirty.stdout:
            self.add("REC-A012", "/changed_paths", "worktree must be clean")
        merges = _git(self.root, "rev-list", "--merges", f"{self.base}..HEAD")
        if merges.returncode or merges.stdout.strip():
            self.add("REC-A012", "/changed_paths", "merge commits are forbidden")

        commits = _git(self.root, "rev-list", "--reverse", f"{self.base}..HEAD")
        if commits.returncode:
            self.add("REC-A012", "/changed_paths", "cannot enumerate history")
        else:
            for commit in commits.stdout.splitlines():
                diff = _git(self.root, "diff-tree", "--no-commit-id", "--name-status", "-r", "-z", commit, binary=True)
                if diff.returncode:
                    self.add("REC-A012", "/changed_paths", f"cannot inspect {commit}")
                    continue
                for status, names in self.parse_status(diff.stdout):
                    if status not in {"A", "M"}:
                        self.add("REC-A012", "/changed_paths", f"transient status {status} in {commit}")
                    for name in names:
                        if name not in AUTHORIZED_PATHS or _forbidden_path(name):
                            self.add("REC-A012", "/changed_paths", f"transient forbidden path {name} in {commit}")

        final = _git(self.root, "diff", "--name-status", "-z", f"{self.base}...HEAD", binary=True)
        actual: list[str] = []
        if final.returncode:
            self.add("REC-A012", "/changed_paths", "cannot inspect final diff")
        else:
            for status, names in self.parse_status(final.stdout):
                if status not in {"A", "M"} or len(names) != 1:
                    self.add("REC-A012", "/changed_paths", f"forbidden final status {status}")
                actual.extend(names)
        if set(actual) != set(declared) or len(actual) != len(declared):
            self.add("REC-A012", "/changed_paths", f"declared paths differ: {sorted(actual)}")

    def run(self, verify_git_diff: bool) -> dict[str, Any]:
        self.obj(self.doc, "/", TOP_KEYS)
        if self.doc.get("schema_version") != SCHEMA_VERSION:
            self.add("REC-A001", "/schema_version", f"must equal {SCHEMA_VERSION}")
        if self.doc.get("goal_id") != GOAL_ID:
            self.add("REC-A001", "/goal_id", f"must equal {GOAL_ID}")
        if self.doc.get("fixture_kind") not in {"real", "synthetic"}:
            self.add("REC-A001", "/fixture_kind", "must be real or synthetic")
        else:
            self.fixture = self.doc["fixture_kind"]

        self.bindings()
        candidate = self.candidate()
        self.precedents()
        self.states("open_human_decisions", "/open_human_decisions", DECISIONS, "REC-A006", "unresolved", "resolved", "authority")
        self.states("technical_invariants", "/technical_invariants", INVARIANTS, "REC-A007", "required", "satisfied", "evidence")
        self.guardrails()
        self.emissions_acceptance()
        self.slices()
        paths = self.changed_paths()
        if candidate.get("implementation_readiness") == "ready" and self.unresolved:
            self.add("REC-A006", "/candidate/implementation_readiness", "implementation-ready state is forbidden with unresolved decisions")
        if verify_git_diff:
            self.verify_git(paths)

        unique = {(item["code"], item["path"], item["message"]): item for item in self.diag}
        diagnostics = [unique[key] for key in sorted(unique)]
        admission = "INVALID" if diagnostics else "SATISFIABLE_FIXTURE" if self.fixture == "synthetic" else "HELD"
        return {
            "admission_result": admission,
            "audit_artifact_verified": self.audit_artifact_verified,
            "execution_authorized": False,
            "unresolved_decision_codes": self.unresolved,
            "diagnostics": diagnostics,
        }


def validate_manifest(
    document: dict[str, Any],
    repo_root: Path,
    *,
    expected_base: str,
    expected_tree: str,
    expected_audit_sha256: str,
    verify_git_diff: bool = False,
    audit_artifact: Path | None = None,
    external_audit_binding_only: bool = False,
) -> dict[str, Any]:
    if audit_artifact is not None and external_audit_binding_only:
        raise ValueError("audit artifact and external-binding-only mode are mutually exclusive")
    return Checker(
        document,
        repo_root,
        expected_base,
        expected_tree,
        expected_audit_sha256,
        audit_artifact=audit_artifact,
        external_audit_binding_only=external_audit_binding_only,
    ).run(verify_git_diff)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expect-base", required=True)
    parser.add_argument("--expect-tree", required=True)
    parser.add_argument("--expect-audit-sha256", required=True)
    parser.add_argument("--verify-git-diff", action="store_true")
    audit_mode = parser.add_mutually_exclusive_group(required=True)
    audit_mode.add_argument("--verify-authorized-audit-artifact", action="store_true")
    audit_mode.add_argument("--external-audit-binding-only", action="store_true")
    parser.add_argument(
        "--expect-admission-result",
        choices=("HELD", "SATISFIABLE_FIXTURE"),
    )
    args = parser.parse_args(argv)
    try:
        result = validate_manifest(
            load_manifest(args.manifest), args.repo_root,
            expected_base=args.expect_base, expected_tree=args.expect_tree,
            expected_audit_sha256=args.expect_audit_sha256,
            verify_git_diff=args.verify_git_diff,
            audit_artifact=(
                Path(AUDIT_PATH) if args.verify_authorized_audit_artifact else None
            ),
            external_audit_binding_only=args.external_audit_binding_only,
        )
    except ValueError as exc:
        result = {
            "admission_result": "INVALID", "audit_artifact_verified": False,
            "execution_authorized": False,
            "unresolved_decision_codes": [],
            "diagnostics": [{"code": "REC-A000", "path": "/", "message": str(exc)}],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.expect_admission_result is not None:
        return 0 if result["admission_result"] == args.expect_admission_result else 1
    return 0 if result["admission_result"] in {"HELD", "SATISFIABLE_FIXTURE"} else 1


if __name__ == "__main__":
    sys.exit(main())
