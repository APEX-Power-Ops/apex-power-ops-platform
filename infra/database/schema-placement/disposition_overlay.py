"""Signed evidence-overlay loader for the schema-placement disposition ledger (overlay packet).

LEAF module: imports disposition_signing (crypto mechanism), stdlib, jsonschema, referencing.
It MUST NOT import check_disposition (which imports THIS) — the acyclic module DAG the census/SP026
work established is preserved. Pure and offline: no DB, no network, no signing key. Fail-closed:
every ambiguous/missing/unresolvable condition is a coded OV0xx, never an uncaught exception.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import CannotDetermineSpecification, Unresolvable

import disposition_signing as ds

SP_DIR = os.path.dirname(os.path.abspath(__file__))
OVERLAY_SCHEMA_PATH = os.path.join(SP_DIR, "overlay.schema.json")
DISPOSITION_SCHEMA_PATH = os.path.join(SP_DIR, "disposition.schema.json")

# dimension path -> (census typed $def, fixed source_type). Mirrors spec Appendix B.
DIMENSIONS = {
    "in_data_api_exposed_schema": ("observed_bool", "platform_config"),
    "advisor_findings": ("observed_advisor_array", "advisor_api"),
    "consumer_evidence.static_repo": ("consumer_evidence_dim", "repository_scan"),
    "consumer_evidence.runtime_logs": ("consumer_evidence_dim", "runtime_logs"),
    "consumer_evidence.external_clients": ("consumer_evidence_dim", "external_client_inventory"),
    "consumer_evidence.operator_declaration": ("consumer_evidence_dim", "operator_declaration"),
}
# consumer dimensions that contribute a windowed interval (database_deps is anchored at base_observed_at).
CONSUMER_CONTRIB_DIMS = ("static_repo", "runtime_logs", "external_clients", "operator_declaration")

OV_CODES = {
    "OV001": "overlay signature missing or fails against the pinned signer (exact raw bytes)",
    "OV002": "base_snapshot_sha256 != the supplied census file byte-hash",
    "OV003": "project_ref mismatch (overlay vs census vs --expect-project-ref)",
    "OV004": "dimension not one of the six permitted paths",
    "OV005": "assignment object_id absent from the census",
    "OV006": "target base slot is not not_observed",
    "OV007": "duplicate/conflicting (dimension, object_id) across or within overlays",
    "OV008": "value/schema violation, registry-unresolvable, or format failure (coded)",
    "OV009": "observation_window malformed, started>=ended, ended>captured, or future",
    "OV010": "overlay captured_at future or staler than the manifest max_staleness_hours",
    "OV011": "derived consumer window empty (S >= E)",
    "OV012": "producing_repo_sha required-but-absent, or null without reason",
    "OV013": "source_type does not match the dimension's fixed mapping",
    "OV014": "operator_declaration overlay missing operator_identity or attestation_ref",
    "OV015": "partial cluster coverage — a gate-required permitted-overlay-target dimension is unresolved",
    "OV016": "consumer window stale (now - E > max_consumer_evidence_age_hours; absent/non-finite also OV016)",
    "OV017": "temporal incoherence: base_observed_at not within the derived window [S, E]",
    "OV018": "zero contributing observed consumer overlays for a cluster-source relation",
    "OV019": "source_hash is null without source_hash_not_applicable_reason",
    "OV020": "overlay disposition_schema_sha256/overlay_schema_sha256 != on-disk schema bytes (drift)",
    "OV021": "base census consumer window is not the canonical zero-width {observed_at, observed_at}",
    "OV022": "delete-floor incoherence: in_data_api overlay window does not cover the derived consumer window",
}


class OverlayRegistryError(Exception):
    """Registry could not be built offline, or a schema $ref was unresolvable. Callers map to OV008."""


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_iso(value):
    """Mirror of check_disposition.parse_dt (kept local to preserve the leaf-module DAG). tz-aware UTC."""
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


@dataclass(frozen=True)
class OverlayContract:
    """Read-once schema contract (audit F4 + round-4 F1): the exact schema bytes, their SHA-256, and
    BOTH validators — the census `disposition_validator` (raw + effective snapshot) and the
    `overlay_validator` — all from a SINGLE read of the two schema files. The gate loads this once and
    uses it for every validation stage, so a concurrent schema edit cannot make raw validation, OV020
    binding, and effective-view validation see different bytes."""
    disp_bytes: bytes
    disp_sha256: str
    overlay_bytes: bytes
    overlay_sha256: str
    disposition_validator: object
    overlay_validator: object


def load_overlay_contract():
    """Build the OverlayContract: read both schema files ONCE (bytes), hash those exact bytes, parse
    them, and construct BOTH validators from the in-hand parsed content — the census
    `disposition_validator` (self-contained `#/$defs` refs; used for raw + effective-view SP001) and the
    `overlay_validator` (seeded offline `referencing.Registry`, no retrieve callback → remote/unseeded
    resolution is impossible). Raises OverlayRegistryError on any load/build failure (callers map to a
    coded OV008). The gate calls this ONCE and threads the contract to every validation stage; the
    schema files are never reopened during a run (audit round-4 F1)."""
    try:
        with open(DISPOSITION_SCHEMA_PATH, "rb") as fh:
            disp_bytes = fh.read()
        with open(OVERLAY_SCHEMA_PATH, "rb") as fh:
            overlay_bytes = fh.read()
        disp = json.loads(disp_bytes)
        overlay = json.loads(overlay_bytes)
        Draft202012Validator.check_schema(disp)
        Draft202012Validator.check_schema(overlay)
        registry = Registry().with_resources([
            (disp["$id"], Resource.from_contents(disp)),
            (overlay["$id"], Resource.from_contents(overlay)),
        ])  # no retrieve= => network/unseeded resolution raises Unresolvable, never fetches
        disposition_validator = Draft202012Validator(disp, format_checker=FormatChecker())  # census, self-contained #/$defs
        overlay_validator = Draft202012Validator(overlay, registry=registry, format_checker=FormatChecker())
        return OverlayContract(disp_bytes=disp_bytes, disp_sha256=_sha256_hex(disp_bytes),
                               overlay_bytes=overlay_bytes, overlay_sha256=_sha256_hex(overlay_bytes),
                               disposition_validator=disposition_validator, overlay_validator=overlay_validator)
    except (OSError, ValueError, KeyError, Unresolvable, SchemaError, CannotDetermineSpecification) as exc:
        raise OverlayRegistryError(f"cannot build offline overlay contract ({type(exc).__name__}: {exc})") from exc
