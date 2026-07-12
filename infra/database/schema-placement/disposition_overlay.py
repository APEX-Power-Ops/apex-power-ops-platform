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


def _reject_dup_json_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def _reject_nonfinite(const):
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def verify_overlay(overlay_bytes: bytes, sig_bytes: bytes, public_key) -> tuple[bool, str]:
    """OV001: detached Ed25519 verify over the EXACT raw overlay bytes against the pinned key object.
    Delegates to disposition_signing (same anchor as the census). Fail-closed on any error."""
    return ds.verify_sidecar_bytes_with_key(overlay_bytes, sig_bytes, public_key)


def parse_overlay(overlay_bytes: bytes) -> dict:
    """Parse the SAME verified buffer (never a re-read). Strict: duplicate keys and non-finite JSON
    constants are rejected (parity with check_disposition.load_doc_from_text). Raises ValueError."""
    return json.loads(overlay_bytes.decode("utf-8"),
                      object_pairs_hook=_reject_dup_json_pairs, parse_constant=_reject_nonfinite)


def check_binding(doc, *, census_sha256, census_project_ref, expect_project_ref,
                  on_disk_disp_sha, on_disk_overlay_sha):
    """OV002 (base hash), OV003 (project ref, three-way), OV020 (schema drift)."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    if doc.get("base_snapshot_sha256") != census_sha256:
        out.append(("OV002", loc, f"base_snapshot_sha256 {doc.get('base_snapshot_sha256')} != census byte-hash {census_sha256}"))
    proj = doc.get("project_ref")
    if not (proj == census_project_ref == expect_project_ref):
        out.append(("OV003", loc, f"project_ref {proj!r} must equal census {census_project_ref!r} and --expect-project-ref {expect_project_ref!r}"))
    if doc.get("disposition_schema_sha256") != on_disk_disp_sha:
        out.append(("OV020", loc, "disposition_schema_sha256 != on-disk disposition.schema.json bytes (drift)"))
    if doc.get("overlay_schema_sha256") != on_disk_overlay_sha:
        out.append(("OV020", loc, "overlay_schema_sha256 != on-disk overlay.schema.json bytes (drift)"))
    return out


# producing_repo_sha applicability, three categories per Appendix B (audit round-3 F5):
_PRODUCING_SHA_REQUIRED = {"in_data_api_exposed_schema", "consumer_evidence.static_repo"}            # non-null, NO reason
_PRODUCING_SHA_FORBIDDEN = {"advisor_findings", "consumer_evidence.runtime_logs", "consumer_evidence.operator_declaration"}  # MUST be null + reason
# consumer_evidence.external_clients is CONDITIONAL: non-null (no reason) OR null + reason (the IFF fallthrough).


def validate_overlay(doc, validator):
    """OV008: JSON-Schema + FormatChecker validation against overlay.schema.json. Any
    referencing.Unresolvable (unseeded/remote $ref) is caught and mapped to a coded OV008."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    try:
        for err in sorted(validator.iter_errors(doc), key=lambda e: str(e.path)):
            path = "/".join(str(p) for p in err.path) or "<root>"
            out.append(("OV008", f"{loc}:{path}", err.message))
    except Unresolvable as exc:
        out.append(("OV008", loc, f"schema $ref unresolvable offline ({exc}) — no remote resolution permitted"))
    return out


def check_observation_window(doc, now):
    """OV009 (audit F2): per-overlay window guard applied to EVERY overlay (all six dimensions, incl.
    the Data-API-exposure overlay OV022 relies on): started_at < ended_at, ended_at <= captured_at,
    ended_at <= now. Fail-closed: a malformed/unparseable window is a single coded OV009, never an
    uncaught exception."""
    out = []
    loc = f"overlay:{doc.get('dimension')}"
    w = doc.get("observation_window") or {}
    try:
        s = _parse_iso(w["started_at"])
        e = _parse_iso(w["ended_at"])
        cap = _parse_iso(doc["captured_at"])
    except (KeyError, ValueError, TypeError, AttributeError):
        return [("OV009", loc, f"observation_window/captured_at malformed or unparseable: {w!r}")]
    if not (s < e):
        out.append(("OV009", loc, f"started_at {w['started_at']} must be < ended_at {w['ended_at']}"))
    if e > cap:
        out.append(("OV009", loc, f"ended_at {w['ended_at']} is after captured_at {doc['captured_at']}"))
    if e > now:
        out.append(("OV009", loc, f"ended_at {w['ended_at']} is in the future vs now {now.isoformat()}"))
    return out


def _base_slot(rel, dimension):
    if dimension.startswith("consumer_evidence."):
        return rel.get("consumer_evidence", {}).get(dimension.split(".", 1)[1], {})
    return rel.get(dimension, {})


def check_target(doc, census_rel_index):
    """OV004/OV005/OV006/OV013/OV012/OV019/OV014. Validation, NOT execution-authorization."""
    out = []
    dimension = doc.get("dimension")
    loc = f"overlay:{dimension}"
    if dimension not in DIMENSIONS:
        out.append(("OV004", loc, f"dimension {dimension!r} is not one of the six permitted paths"))
        return out  # nothing else is meaningful for an unknown dimension
    _vdef, fixed_source = DIMENSIONS[dimension]
    if doc.get("source_type") != fixed_source:
        out.append(("OV013", loc, f"source_type {doc.get('source_type')!r} != fixed {fixed_source!r} for {dimension}"))
    # OV019 IFF (audit F9): a source_hash_not_applicable_reason is required IFF source_hash is null.
    sh = doc.get("source_hash")
    sh_reason = (doc.get("source_hash_not_applicable_reason") or "").strip()
    if sh is None and not sh_reason:
        out.append(("OV019", loc, "source_hash is null without source_hash_not_applicable_reason"))
    elif sh is not None and sh_reason:
        out.append(("OV019", loc, "source_hash is non-null but a source_hash_not_applicable_reason is also present (must be absent)"))
    # OV012 IFF: required dims need a non-null producing_repo_sha with NO reason; other dims need null+reason.
    prs = doc.get("producing_repo_sha")
    prs_reason = (doc.get("producing_repo_sha_not_applicable_reason") or "").strip()
    if dimension in _PRODUCING_SHA_REQUIRED:                 # required: non-null, no reason
        if not prs:
            out.append(("OV012", loc, f"producing_repo_sha required for {dimension} but absent/null"))
        elif prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is non-null but a not_applicable_reason is also present (must be absent)"))
    elif dimension in _PRODUCING_SHA_FORBIDDEN:              # forbidden: MUST be null + reason
        if prs is not None:
            out.append(("OV012", loc, f"producing_repo_sha is not applicable for {dimension}; it must be null with a not_applicable_reason"))
        elif not prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is null without producing_repo_sha_not_applicable_reason"))
    else:                                                    # conditional (external_clients): IFF null<->reason
        if prs is None and not prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is null without producing_repo_sha_not_applicable_reason"))
        elif prs is not None and prs_reason:
            out.append(("OV012", loc, "producing_repo_sha is non-null but a not_applicable_reason is also present (must be absent)"))
    if dimension == "consumer_evidence.operator_declaration":
        if not (doc.get("operator_identity") or "").strip() or not (doc.get("attestation_ref") or "").strip():
            out.append(("OV014", loc, "operator_declaration overlay missing operator_identity/attestation_ref provenance"))
    for a in doc.get("assignments", []):
        oid = a.get("object_id")
        rel = census_rel_index.get(oid)
        if rel is None:
            out.append(("OV005", f"{loc}:{oid}", "assignment object_id absent from the census"))
            continue
        if _base_slot(rel, dimension).get("state") != "not_observed":
            out.append(("OV006", f"{loc}:{oid}", f"base slot state={_base_slot(rel, dimension).get('state')} (only not_observed is overlayable)"))
    return out


def check_conflict(assignment_keys):
    """OV007: reject any (dimension, object_id) pair assigned more than once, within OR across
    overlays, even if the values are identical. assignment_keys is the full flat list."""
    out = []
    counts = {}
    for key in assignment_keys:
        counts[key] = counts.get(key, 0) + 1
    for (dimension, oid), n in sorted(counts.items()):
        if n > 1:
            out.append(("OV007", f"overlay:{dimension}:{oid}", f"(dimension, object_id) assigned {n} times (across or within overlays)"))
    return out


def precheck_base_window(census):
    """OV021 (UNCONDITIONAL preapply precheck — runs even with zero overlays): every relation's base
    consumer window must be the canonical zero-width {observed_at, observed_at} the collector emits.
    String-equality to observed_at; a signed-but-hand-crafted non-zero window is caught before merge."""
    out = []
    observed_at = census.get("observed_at")
    for r in census.get("relations", []):
        w = r.get("consumer_evidence", {}).get("observation_window", {})
        if not (w.get("started_at") == observed_at and w.get("ended_at") == observed_at):
            out.append(("OV021", f"census:{r.get('object_id')}",
                        f"base consumer window {w} is not the canonical zero-width {{{observed_at}, {observed_at}}}"))
    return out


def derive_windows(effective, *, cluster_src_oids, contrib_by_oid, now, base_observed_at, max_consumer_evidence_age_hours):
    """For each UNIQUE cluster-source object_id (T3), derive the consumer window from the relation's
    observed consumer contributors in contrib_by_oid[oid] — a LOCAL {oid: [(started, ended, captured), ...]}
    map (over CONSUMER_CONTRIB_DIMS) passed by the orchestrator, NEVER read off the effective snapshot
    (audit #9) — and write {S, E} ISO-8601 strings into the effective view. Returns
    (diagnostics, derived_window_object_ids). Fail-closed per the §3 predicate."""
    # Recency-policy precheck (Codex-P2): an absent/non-finite max_consumer_evidence_age_hours is a
    # DETERMINISTIC coded OV016 reported BEFORE any per-relation contributor check, so a missing CLI
    # flag can never be masked by an OV018 on a zero-contributor relation.
    if not (_finite(max_consumer_evidence_age_hours) and max_consumer_evidence_age_hours > 0):
        return [("OV016", "overlay-derive:policy", f"max_consumer_evidence_age_hours {max_consumer_evidence_age_hours!r} absent or non-finite (required recency floor, fail-closed)")], set()
    out = []
    derived = set()
    contrib = contrib_by_oid
    rel_by_oid = {r["object_id"]: r for r in effective.get("relations", [])}
    for oid in sorted(cluster_src_oids):  # a set => each object_id derived exactly once (T3)
        windows = contrib.get(oid, [])
        loc = f"overlay-derive:{oid}"
        if not windows:
            out.append(("OV018", loc, "zero observed consumer contributors for a cluster-source relation"))
            continue
        s = max(w[0] for w in windows)
        e = min(w[1] for w in windows)
        min_captured = min(w[2] for w in windows)
        if s >= e:
            out.append(("OV011", loc, f"derived window empty: S {s.isoformat()} >= E {e.isoformat()}"))
            continue
        if e > min_captured:
            out.append(("OV009", loc, f"E {e.isoformat()} > min captured_at {min_captured.isoformat()} (defense assert)"))
            continue
        if e > now:
            out.append(("OV009", loc, f"derived E {e.isoformat()} is in the future vs now {now.isoformat()}"))
            continue
        if (now - e).total_seconds() / 3600.0 > max_consumer_evidence_age_hours:  # per-relation recency (max_age validated above)
            out.append(("OV016", loc, f"stale: now-E {(now - e).total_seconds() / 3600.0:.1f}h > max {max_consumer_evidence_age_hours}h"))
            continue
        if not (s <= base_observed_at <= e):
            out.append(("OV017", loc, f"base_observed_at {base_observed_at.isoformat()} not within derived window [{s.isoformat()}, {e.isoformat()}]"))
            continue
        rel_by_oid[oid]["consumer_evidence"]["observation_window"] = {"started_at": s.isoformat(), "ended_at": e.isoformat()}
        derived.add(oid)
    return out, derived


def check_delete_floor_coherence(effective, *, delete_src_oids, external_na_oids,
                                 in_data_api_windows, derived_windows):
    """OV022 (T1-scoped): for a delete-conclusion source relation whose external_clients overlay
    resolves to not_applicable (invoking the SP027 waiver, which requires in_data_api observed false),
    the observed-FALSE in_data_api overlay's observation_window (looked up by the exact
    (dimension, object_id) assignment, T2) must COVER the derived consumer window [S, E]
    (started_at <= S and ended_at >= E), proving the relation was unexposed THROUGHOUT the evidence
    interval. OV022 evaluates ONLY when an observed-false in_data_api overlay backs the waiver (its
    window is in in_data_api_windows). The coherent routing for the other cases (audit round-3 F2):
    a MISSING in_data_api overlay leaves the gate-required dimension unresolved and is caught by
    **OV015** (cluster-completeness, before run()); an **observed-TRUE** overlay defers here and
    **SP027** denies the waiver at the semantic gate; only an observed-false overlay with an inadequate
    window is OV022 — none of these short-circuit their ratified diagnostic. When external_clients is
    observed (oid not in external_na_oids), OV022 is not evaluated (T1)."""
    out = []
    for oid in sorted(delete_src_oids & external_na_oids):  # T1: only not_applicable-waiver deletes
        se = derived_windows.get(oid)
        if se is None:
            continue  # no derived window (already rejected upstream by OV018/OV011/etc.)
        s, e = se
        api = in_data_api_windows.get(oid)
        if api is None:
            continue  # no observed-false in_data_api overlay backs the waiver -> SP027 denies it (defer)
        api_s, api_e = api
        if not (api_s <= s and api_e >= e):
            out.append(("OV022", f"overlay-delete:{oid}",
                        f"in_data_api window [{api_s.isoformat()}, {api_e.isoformat()}] does not cover derived consumer window [{s.isoformat()}, {e.isoformat()}]"))
    return out
