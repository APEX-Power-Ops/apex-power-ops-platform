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


# ---- OV015 cluster-completeness (advisory; audit F7) ----
_PERMITTED_OVERLAY_TARGETS = set(DIMENSIONS)  # the six permitted overlay paths
_CONSUMER_REQUIRED_EXPANSION = tuple(f"consumer_evidence.{d}" for d in CONSUMER_CONTRIB_DIMS)


def _gate_required_dims(row, manifest):
    """Permitted-overlay-target dimensions a decision's source relations must have resolved: the
    permitted-target subset of manifest.required_observations (consumer_evidence expands to the four
    contributor dims) UNION the consumer dims for a resolved consumer_disposition (SP022) UNION the
    delete-floor dims + in_data_api for a delete (SP027 external_clients waiver)."""
    req = set()
    for f in manifest.get("required_observations", []):
        if f == "consumer_evidence":
            req.update(_CONSUMER_REQUIRED_EXPANSION)
        elif f in _PERMITTED_OVERLAY_TARGETS:
            req.add(f)
    if row.get("consumer_disposition") in ("no_consumer", "has_consumers"):
        req.update(_CONSUMER_REQUIRED_EXPANSION)
    if row.get("action_class") == "delete":
        req.update(_CONSUMER_REQUIRED_EXPANSION)
        req.add("in_data_api_exposed_schema")
    return req & _PERMITTED_OVERLAY_TARGETS


def check_cluster_completeness(base_census, effective, manifest, decisions):
    """OV015 (advisory, audit F7): every cluster-source relation must have each gate-required
    permitted-overlay-target dimension resolved (state != not_observed) in the effective view — unless
    it was already observed in the BASE census (e.g. database_deps, which is not an overlay target).
    SP009/SP022/SP027 on the effective view remain authoritative; OV015 names the missing overlay early."""
    out = []
    dec_by_id = {row["decision_id"]: row for row in decisions.get("rows", [])}
    base_index = {r["object_id"]: r for r in base_census.get("relations", [])}
    eff_index = {r["object_id"]: r for r in effective.get("relations", [])}
    for did in manifest.get("decision_ids", []):
        row = dec_by_id.get(did)
        if not row:
            continue
        for oid in row.get("source_objects", []):
            base_rel, eff_rel = base_index.get(oid), eff_index.get(oid)
            if base_rel is None or eff_rel is None:
                continue
            for dim in sorted(_gate_required_dims(row, manifest)):
                if _base_slot(base_rel, dim).get("state") == "not_observed" and _base_slot(eff_rel, dim).get("state") == "not_observed":
                    out.append(("OV015", f"cluster:{did}:{oid}:{dim}", f"gate-required dimension {dim} is unresolved (no permitted overlay)"))
    return out


@dataclass
class MergeResult:
    effective_snapshot: dict
    derived_window_object_ids: set
    receipt_overlays: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)


def load_and_merge(*, census, census_bytes, overlay_inputs, manifest, decisions, expect_project_ref,
                   now, max_consumer_evidence_age_hours, max_staleness_hours, resolved_signer, contract):
    """The step 1-8 pipeline. `contract` is the read-once OverlayContract (schema bytes+hashes+validator,
    audit F4 — schemas are NEVER reopened here). `overlay_inputs` = list of
    (overlay_path, sig_path, overlay_bytes, sig_bytes) read once by the caller. Verifies + binds +
    window-checks (OV009, per-overlay) + targets + de-conflicts each overlay; runs the UNCONDITIONAL
    OV021 precheck; deep-copies the census; sets each resolved dimension; derives per-relation consumer
    windows for EVERY cluster-source relation (contributor map kept LOCAL, audit #9); runs OV022 + OV015.
    Returns a MergeResult. NEVER mutates census. Any reject short-circuits to a red MergeResult."""
    diags = []
    census_sha = _sha256_hex(census_bytes)
    base_observed_at = _parse_iso(census.get("observed_at"))
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}

    # step 8 (OV021) runs UNCONDITIONALLY, even with zero overlays.
    diags += precheck_base_window(census)

    parsed = []            # (doc, overlay_path, sig_path, overlay_bytes, sig_bytes)
    all_keys = []          # (dimension, object_id) for OV007
    for overlay_path, sig_path, ob_bytes, sig_bytes in overlay_inputs:
        ok, reason = verify_overlay(ob_bytes, sig_bytes, resolved_signer.public_key)
        if not ok:
            diags.append(("OV001", f"overlay:{overlay_path}", f"signature verification failed: {reason}"))
            continue
        try:
            doc = parse_overlay(ob_bytes)          # parse the SAME verified buffer
        except ValueError as exc:
            diags.append(("OV008", f"overlay:{overlay_path}", f"parse failed ({exc})"))
            continue
        # A signed-but-non-object payload (JSON array/scalar) has no .get/.assignments — reject it as a
        # coded OV008 before any dict-shaped access, never an uncaught AttributeError (audit round-3 F1).
        if not isinstance(doc, dict):
            diags.append(("OV008", f"overlay:{overlay_path}", f"overlay is not a JSON object (got {type(doc).__name__})"))
            continue
        # SHORT-CIRCUIT on any schema/format/registry failure: a schema-invalid overlay is not safe to
        # bind / window-check / target / iterate (its assignments may be malformed). OV008 then continue.
        schema_diags = validate_overlay(doc, contract.overlay_validator)
        if schema_diags:
            diags.extend(schema_diags)
            continue
        diags += check_binding(doc, census_sha256=census_sha, census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref, on_disk_disp_sha=contract.disp_sha256,
                               on_disk_overlay_sha=contract.overlay_sha256)
        diags += check_observation_window(doc, now)   # OV009 per-overlay (audit F2), on a schema-valid doc
        diags += check_target(doc, rel_index)
        # OV010 per-overlay captured_at freshness (finite-guarded), reusing manifest max_staleness_hours.
        try:
            cap = _parse_iso(doc.get("captured_at"))
            if cap > now:
                diags.append(("OV010", f"overlay:{overlay_path}", "captured_at is in the future"))
            elif _finite(max_staleness_hours) and (now - cap).total_seconds() / 3600.0 > max_staleness_hours:
                diags.append(("OV010", f"overlay:{overlay_path}", f"captured_at staler than max_staleness_hours {max_staleness_hours}"))
        except (ValueError, TypeError):
            diags.append(("OV010", f"overlay:{overlay_path}", "captured_at unparseable"))
        for a in doc.get("assignments", []):
            all_keys.append((doc.get("dimension"), a.get("object_id")))
        parsed.append((doc, overlay_path, sig_path, ob_bytes, sig_bytes))
    diags += check_conflict(all_keys)

    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)

    # ---- build the effective view (deepcopy; census never mutated) ----
    effective = copy.deepcopy(census)
    eff_index = {r["object_id"]: r for r in effective["relations"]}
    contrib = {}                     # LOCAL: oid -> [(started, ended, captured)] (audit #9; NOT stashed on effective)
    in_data_api_windows = {}         # oid -> (started, ended) from the (in_data_api, oid) overlay (T2)
    external_state = {}              # oid -> external_clients state, for T1
    for doc, _op, _sp, _ob, _sb in parsed:
        dim = doc["dimension"]
        win = doc["observation_window"]
        w = (_parse_iso(win["started_at"]), _parse_iso(win["ended_at"]))
        cap = _parse_iso(doc["captured_at"])
        for a in doc["assignments"]:
            oid = a["object_id"]
            rel = eff_index[oid]
            if dim.startswith("consumer_evidence."):
                sub = dim.split(".", 1)[1]
                rel["consumer_evidence"][sub] = a["value"]
                if sub in CONSUMER_CONTRIB_DIMS and a["value"].get("state") == "observed":
                    contrib.setdefault(oid, []).append((w[0], w[1], cap))
                if sub == "external_clients":
                    external_state[oid] = a["value"].get("state")
            else:
                rel[dim] = a["value"]
                # Record the in_data_api window ONLY for an observed-FALSE overlay — the only shape that
                # backs the SP027 external_clients not_applicable waiver. A missing overlay leaves the
                # gate-required dim unresolved (-> OV015); an observed-true overlay leaves this unset so
                # OV022 defers and SP027 denies the waiver at the semantic gate (audit F2; T2).
                if dim == "in_data_api_exposed_schema" and a["value"].get("state") == "observed" and a["value"].get("value") is False:
                    in_data_api_windows[oid] = w

    # cluster-source object_ids across ALL decisions (deduped by object_id, T3), incl. retain.
    dec_by_id = {row["decision_id"]: row for row in decisions.get("rows", [])}
    cluster_src_oids = set()
    delete_src_oids = set()
    for did in manifest.get("decision_ids", []):
        row = dec_by_id.get(did)
        if not row:
            continue
        for oid in row.get("source_objects", []):
            if oid in eff_index:
                cluster_src_oids.add(oid)
                if row.get("action_class") == "delete":
                    delete_src_oids.add(oid)

    wdiags, derived = derive_windows(effective, cluster_src_oids=cluster_src_oids, contrib_by_oid=contrib,
                                     now=now, base_observed_at=base_observed_at,
                                     max_consumer_evidence_age_hours=max_consumer_evidence_age_hours)
    diags += wdiags
    derived_windows = {oid: (_parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["started_at"]),
                             _parse_iso(eff_index[oid]["consumer_evidence"]["observation_window"]["ended_at"]))
                       for oid in derived}
    external_na_oids = {oid for oid, st in external_state.items() if st == "not_applicable"}
    diags += check_delete_floor_coherence(effective, delete_src_oids=delete_src_oids,
                                          external_na_oids=external_na_oids,
                                          in_data_api_windows=in_data_api_windows, derived_windows=derived_windows)
    diags += check_cluster_completeness(census, effective, manifest, decisions)   # OV015 (audit F7)

    receipt_overlays = []
    for doc, op, sp, ob, sb in parsed:
        entry = {"path": op, "raw_sha256": _sha256_hex(ob), "sig_path": sp, "sig_sha256": _sha256_hex(sb),
                 "signer": {"key_id": resolved_signer.key_id, "spki_sha256": resolved_signer.spki_sha256},
                 "dimension": doc["dimension"], "object_ids": [a["object_id"] for a in doc.get("assignments", [])],
                 "object_id_count": len(doc.get("assignments", [])), "captured_at": doc["captured_at"],
                 "producing_repo_sha": doc.get("producing_repo_sha"), "source_hash": doc.get("source_hash"),
                 "disposition_schema_sha256": doc.get("disposition_schema_sha256"),
                 "overlay_schema_sha256": doc.get("overlay_schema_sha256")}
        if doc["dimension"] == "consumer_evidence.operator_declaration":
            entry["operator_identity"] = doc.get("operator_identity")
            entry["attestation_ref"] = doc.get("attestation_ref")
        receipt_overlays.append(entry)
    if diags:
        return MergeResult(effective_snapshot=None, derived_window_object_ids=set(), diagnostics=diags)
    return MergeResult(effective_snapshot=effective, derived_window_object_ids=derived,
                       receipt_overlays=receipt_overlays, diagnostics=[])
