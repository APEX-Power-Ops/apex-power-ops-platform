"""Offline semantic gate for the schema-placement disposition ledger.

Pure and offline: NO live database access (only the later collector queries prod, read-only).
Runs JSON Schema validation first (FormatChecker), then the cross-document / time / context
checks the schema cannot express. Deterministic: --now injected; diagnostics sorted by
(code, locus). Exit 0 only when the requested mode's gate is fully green.

    check_disposition.py --snapshot S --decisions D --entity-map E --manifest M \
        --now 2026-07-11T00:00:00Z --mode preapply --root DIR [--root DIR ...]

--root is REQUIRED (no implicit root). Error codes are stable (SP0xx); see CODES.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

import yaml
from jsonschema import Draft202012Validator, FormatChecker

import disposition_provenance as dp
import disposition_signing as ds
import disposition_trust as dt

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposition.schema.json")
DIMS = ("static_repo", "database_deps", "runtime_logs", "external_clients", "operator_declaration")
_DELETE_MIN_WINDOW_HOURS = 720  # destructive-evidence floor: >= 30 days of consumer observation for a delete
_SIGNATURE_EXEMPT_MODES = frozenset()  # default-deny: EVERY mode requires a verified snapshot signature unless listed here (F5)
NON_PATH_SCHEMES = ("query", "sha", "ta", "telemetry", "urn", "ref", "http", "https")
_SCHEME_RE = re.compile(r"^([a-z][a-z0-9+.\-]*):")

CODES = {
    "SP001": "input failed JSON Schema validation",
    "SP002": "relation_count does not equal the number of relations",
    "SP003": "duplicate object_id in snapshot relations",
    "SP004": "object_id does not equal schema + '.' + name",
    "SP005": "cluster action_class disagrees with a member decision",
    "SP006": "manifest references an unknown decision_id",
    "SP007": "decision source_object is absent from the snapshot",
    "SP008": "snapshot is stale or observed in the future relative to --now",
    "SP009": "consumer observation_window violates started<ended<=observed_at (strict; a census-default zero-width window must be overlaid before preapply)",
    "SP010": "a required observation is not freshly observed",
    "SP011": "target_entity does not resolve to an accepted entity_map entry",
    "SP012": "target_schema does not resolve to an accepted physical_schema",
    "SP013": "consumer conclusion contradicts an observed evidence dimension",
    "SP014": "evidence path is missing, escapes an approved root, or is not a regular file",
    "SP015": "a gate number is not finite (compat exit_condition threshold / manifest staleness / consumer window)",
    "SP016": "cluster member decision is not accepted (required for preapply)",
    "SP017": "cluster is empty after resolution",
    "SP018": "manifest is not accepted with a cluster approval (required for preapply)",
    "SP019": "entity_map is not accepted but a decision needs entity/schema resolution",
    "SP020": "duplicate decision_id / entity_id / physical_schema identity",
    "SP021": "manifest evidence_snapshot differs from the supplied --snapshot",
    "SP022": "unresolved consumer-evidence dimension for a no_consumer conclusion",
    "SP023": "target_entity's physical_schema disagrees with target_schema",
    "SP024": "evidence_snapshot target_identity is absent/not-guard-passed, or its project binding is unasserted/mismatched",
    "SP025": "a target_object does not live in the decision's target_schema (relocation destination binding)",
    "SP026": "evidence_snapshot signature is missing or does not verify against the pinned signer (--key-id resolved through the reviewed TRUSTED_SIGNERS anchor); preapply requires a signed snapshot",
    "SP027": "accepted delete does not meet the destructive-evidence floor (a consumer dimension is not observed, external_clients is not_applicable while API-exposed, or the observation window is < 30 days)",
    "SP028": "checkout-provenance binding failed: for preapply supply either both --expect-gate-repo-sha and --require-clean-checkout (bound) OR --allow-unbound-checkout alone (authoring-only); any other combination is refused, and on the bound path the checker's git HEAD must be determinable, its worktree clean, and equal to the reviewed gate SHA (never the census snapshot's repo_sha)",
}


class Diagnostic:
    __slots__ = ("code", "locus", "message")

    def __init__(self, code, locus, message):
        self.code, self.locus, self.message = code, locus, message

    def key(self):
        return (self.code, self.locus)

    def render(self):
        return f"{self.code} {self.locus}: {self.message}"


# ---- loaders that reject duplicate keys (YAML and JSON) --------------------
class NoDupSafeLoader(yaml.SafeLoader):
    pass


def _no_dup_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.YAMLError(f"duplicate key {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


NoDupSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)


def _reject_dup_json_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def _reject_nonfinite(const):
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def load_doc_from_text(text, path):
    """Parse an already-in-hand document string. Splitting this out lets main() read each input's
    bytes ONCE and parse from that same buffer, so the bytes gated/verified/hashed are identical to
    the bytes on disk at read time (no second read — Codex P1)."""
    if path.endswith(".json"):
        return json.loads(text, object_pairs_hook=_reject_dup_json_pairs, parse_constant=_reject_nonfinite)
    return yaml.load(text, Loader=NoDupSafeLoader)


def load_doc(path):
    with open(path, encoding="utf-8") as fh:
        return load_doc_from_text(fh.read(), path)


# ---- helpers ---------------------------------------------------------------
def parse_dt(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def is_path_ref(ref):
    m = _SCHEME_RE.match(ref or "")
    if m and m.group(1) in NON_PATH_SCHEMES:
        return False
    return bool(ref)


def resolve_within_roots(ref, roots):
    """Try EVERY root; return (realpath, '') iff the ref resolves within some root AND is a
    regular file. Otherwise (None, reason). Rejects absolute paths, traversal, symlink escape."""
    rel = ref.split("#", 1)[0]
    if os.path.isabs(rel):
        return None, "absolute path not allowed"
    within_but_bad = None
    for root in roots:
        rr = os.path.realpath(root)
        cand = os.path.realpath(os.path.join(rr, rel))
        if cand == rr or cand.startswith(rr + os.sep):
            if os.path.isfile(cand):
                return cand, ""
            within_but_bad = "not a regular file or missing"
    return None, within_but_bad or "escapes all approved roots"


def _sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def build_receipt(*, mode, now_iso, expect_project_ref, doc_bytes, doc_paths, signer, snapshot_signature_sha256,
                  gate_repo_sha, checkout_bound, production_eligible, roots, decisions):
    """Records the SHA-256 of the exact bytes the gate validated: the four CLI documents hashed from the
    IN-HAND bytes main() parsed, the pinned SIGNER content, and the snapshot signature bytes' hash (bound
    from the in-hand sig bytes — no second read). ADVISORY; emitted ONLY on a GREEN gate."""
    receipt = {"kind": "disposition_gate_receipt", "gate": "green", "mode": mode, "now": now_iso,
               "expect_project_ref": expect_project_ref, "inputs": {}, "evidence": [],
               "signer": signer, "snapshot_signature_sha256": snapshot_signature_sha256,
               "gate_repo_sha": gate_repo_sha, "checkout_bound": checkout_bound,
               "production_eligible": production_eligible}
    for name, data in doc_bytes.items():
        receipt["inputs"][name] = {"path": doc_paths.get(name), "sha256": hashlib.sha256(data).hexdigest()}
    seen = set()
    for row in decisions.get("rows", []):
        refs = list(row.get("evidence_refs", []))
        rd = row.get("retention_disposition")
        if isinstance(rd, dict):
            rp = rd.get("recovery_proof")
            if isinstance(rp, dict):
                refs.extend(rp.get(k) for k in ("artifact_path", "restore_validation_ref"))
            elif isinstance(rp, str):
                refs.append(rp)
        tr = row.get("transform")
        if isinstance(tr, dict) and tr.get("validation_report"):
            refs.append(tr["validation_report"])
        cc = row.get("compatibility_contract")
        if isinstance(cc, dict) and cc.get("telemetry_ref"):
            refs.append(cc["telemetry_ref"])
        for ref in refs:
            if isinstance(ref, str) and is_path_ref(ref):
                resolved, _reason = resolve_within_roots(ref, roots)
                if resolved and resolved not in seen:
                    seen.add(resolved)
                    receipt["evidence"].append({"ref": ref, "resolved": resolved, "sha256": _sha256_file(resolved)})
    receipt["evidence"].sort(key=lambda e: e["resolved"])
    return receipt


def _validator():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def schema_validate(docs, validator):
    out = []
    for kind, doc in docs.items():
        for err in sorted(validator.iter_errors(doc), key=lambda e: str(e.path)):
            path = "/".join(str(p) for p in err.path) or "<root>"
            out.append(Diagnostic("SP001", f"{kind}:{path}", err.message))
    return out


# ---- semantic checks -------------------------------------------------------
def semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path, expect_project_ref=None, derived_window_object_ids=None):
    d = []
    relations = snapshot.get("relations", [])
    rel_by_oid = {}
    for r in relations:
        rel_by_oid.setdefault(r["object_id"], []).append(r)

    # --- target-identity + project binding (SP024) ---
    # Schema already requires target_identity with guard_passed/transaction_read_only const true;
    # SP024 gives a coded gate for it AND binds the snapshot's project_ref to the expected project
    # (the checker cannot re-verify the DSN offline, so preapply MUST declare --expect-project-ref).
    ti = snapshot.get("target_identity")
    if not isinstance(ti, dict) or ti.get("guard_passed") is not True or ti.get("transaction_read_only") is not True:
        d.append(Diagnostic("SP024", "snapshot", f"target_identity absent or not guard-passed/read-only ({ti if not isinstance(ti, dict) else {'guard_passed': ti.get('guard_passed'), 'transaction_read_only': ti.get('transaction_read_only')}})"))
    if mode == "preapply":
        proj = snapshot.get("project_ref")
        if expect_project_ref is None:
            d.append(Diagnostic("SP024", "snapshot", "project binding not asserted; preapply requires --expect-project-ref"))
        elif proj != expect_project_ref:
            d.append(Diagnostic("SP024", "snapshot", f"project_ref {proj!r} != --expect-project-ref {expect_project_ref!r}"))

    # --- global census integrity (SP002-SP004) ---
    if snapshot.get("relation_count") != len(relations):
        d.append(Diagnostic("SP002", "snapshot", f"relation_count={snapshot.get('relation_count')} but {len(relations)} relations"))
    for oid, rs in sorted(rel_by_oid.items()):
        if len(rs) > 1:
            d.append(Diagnostic("SP003", f"snapshot:{oid}", f"object_id appears {len(rs)} times"))
    for r in relations:
        if r["object_id"] != f"{r['schema']}.{r['name']}":
            d.append(Diagnostic("SP004", f"snapshot:{r['object_id']}", f"!= {r['schema']}.{r['name']}"))

    # --- duplicate identities (SP020) ---
    for label, ids in (("decision", [row["decision_id"] for row in decisions.get("rows", [])]),
                       ("entity", [e["entity_id"] for e in entity_map.get("entities", [])]),
                       ("schema", [p["name"] for p in entity_map.get("physical_schemas", [])])):
        seen = set()
        for i in ids:
            if i in seen:
                d.append(Diagnostic("SP020", f"{label}:{i}", "duplicate identity"))
            seen.add(i)

    # --- non-finite gate numbers (SP015): NaN/Infinity load from JSON/YAML and silently defeat the
    #     SP008/SP009 comparisons (every comparison with NaN is False), so reject them before use
    #     (Codex R2: max_staleness_hours: .nan/.inf disables the stale check). ---
    def _finite(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

    for mfield in ("max_staleness_hours", "minimum_consumer_window_hours"):
        mv = manifest.get(mfield)
        if mv is not None and not _finite(mv):
            d.append(Diagnostic("SP015", f"manifest:{mfield}", f"{mfield}={mv} is not finite"))

    # --- snapshot freshness (SP008) ---
    observed_at = parse_dt(snapshot["observed_at"])
    if observed_at > now:
        d.append(Diagnostic("SP008", "snapshot", f"observed_at {snapshot['observed_at']} is after --now"))
    max_stale = manifest.get("max_staleness_hours")
    if _finite(max_stale) and (now - observed_at).total_seconds() / 3600.0 > max_stale:
        d.append(Diagnostic("SP008", "snapshot", f"age exceeds max_staleness_hours {max_stale}"))
    _mw = manifest.get("minimum_consumer_window_hours")
    min_window = _mw if _finite(_mw) else 0

    # --- manifest lifecycle for preapply (SP018) ---
    if mode == "preapply":
        if manifest.get("status") != "accepted" or not (manifest.get("technical_authority_approval") or "").strip():
            d.append(Diagnostic("SP018", "manifest", f"status={manifest.get('status')} / TA={manifest.get('technical_authority_approval')!r} (preapply requires accepted + non-empty approval)"))

    # --- manifest snapshot binding (SP014 existence + SP021 identity) ---
    # The manifest snapshot must ALWAYS be a filesystem artifact — resolve UNCONDITIONALLY (a
    # scheme reference like 'query:not-a-file' must not bypass the binding) and compare to the
    # canonical --snapshot real path.
    snap_ref = manifest.get("evidence_snapshot")
    if snap_ref:
        resolved, reason = resolve_within_roots(snap_ref, roots)
        if resolved is None:
            d.append(Diagnostic("SP014", "manifest:evidence_snapshot", f"{snap_ref}: {reason}"))
        elif snapshot_path is not None and resolved != os.path.realpath(snapshot_path):
            d.append(Diagnostic("SP021", "manifest:evidence_snapshot", f"{snap_ref} != --snapshot {snapshot_path}"))

    # --- resolution sets ---
    accepted_entities = {e["entity_id"]: e for e in entity_map.get("entities", []) if e.get("decision_status") == "accepted"}
    accepted_schemas = {p["name"] for p in entity_map.get("physical_schemas", []) if p.get("status") == "accepted"}
    entity_map_accepted = entity_map.get("approval") == "accepted"

    dec_by_id = {row["decision_id"]: row for row in decisions.get("rows", [])}
    resolved_rows = []
    for did in manifest.get("decision_ids", []):
        if did not in dec_by_id:
            d.append(Diagnostic("SP006", f"manifest:{did}", "unknown decision_id"))
        else:
            resolved_rows.append(dec_by_id[did])
    if not resolved_rows:
        d.append(Diagnostic("SP017", "manifest", "cluster resolves to zero decisions"))

    req_obs = [f for f in manifest.get("required_observations", []) if f != "consumer_evidence"]
    require_consumer_evidence = "consumer_evidence" in manifest.get("required_observations", [])
    m_action = manifest.get("action_class")

    for row in resolved_rows:
        did = row["decision_id"]
        if row.get("action_class") != m_action:
            d.append(Diagnostic("SP005", f"decision:{did}", f"action_class {row.get('action_class')} != manifest {m_action}"))
        if mode == "preapply" and row.get("decision_status") != "accepted":
            d.append(Diagnostic("SP016", f"decision:{did}", f"decision_status {row.get('decision_status')} (preapply requires accepted)"))

        src_rels = []
        for oid in row.get("source_objects", []):
            if oid not in rel_by_oid:
                d.append(Diagnostic("SP007", f"decision:{did}", f"source_object {oid} absent from snapshot"))
            else:
                src_rels.extend(rel_by_oid[oid])

        # window ordering (strict) + minimum duration, scoped to this cluster's source relations (SP009).
        # Provenance-conditional upper bound: for windows the overlay checker itself derived-and-wrote
        # (object_id in derived_window_object_ids), the `<= observed_at` bound is relaxed (future/recency/
        # anchor already enforced at merge by OV009/OV016/OV017); non-derived and no-provenance windows
        # keep the original s < e <= observed_at (fail-closed on an absent marker).
        for r in src_rels:
            w = r.get("consumer_evidence", {}).get("observation_window")
            if isinstance(w, dict) and "started_at" in w and "ended_at" in w:
                s, e = parse_dt(w["started_at"]), parse_dt(w["ended_at"])
                is_derived = derived_window_object_ids is not None and r["object_id"] in derived_window_object_ids
                ordered = (s < e) if is_derived else (s < e <= observed_at)
                if not ordered:
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window {w['started_at']}..{w['ended_at']} must satisfy started<ended{'' if is_derived else '<=observed_at'} ({snapshot['observed_at']})"))
                elif (e - s).total_seconds() / 3600.0 < min_window:
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window duration {(e - s).total_seconds() / 3600.0:.2f}h < minimum_consumer_window_hours {min_window}"))

        # target resolution (SP019/SP011/SP012/SP023) + destination binding (SP025)
        te, ts = row.get("target_entity"), row.get("target_schema")
        if (te is not None or ts is not None) and not entity_map_accepted:
            d.append(Diagnostic("SP019", f"decision:{did}", f"entity_map.approval={entity_map.get('approval')} (targets require accepted map)"))
        if te is not None and te not in accepted_entities:
            d.append(Diagnostic("SP011", f"decision:{did}", f"target_entity {te} not an accepted entity"))
        # SP012: promotion INTO a canonical schema must resolve to an accepted physical_schema;
        # compat relocates to the PUBLIC compat surface and must therefore target EXACTLY 'public'
        # (Codex R2: exempting every compat let target_schema='evil' create objects in an unapproved schema).
        if ts is not None:
            if row.get("action_class") == "compat":
                if ts != "public":
                    d.append(Diagnostic("SP012", f"decision:{did}", f"compat target_schema {ts!r} must be the public compat surface"))
            elif ts not in accepted_schemas:
                d.append(Diagnostic("SP012", f"decision:{did}", f"target_schema {ts} not an accepted physical_schema"))
        if te in accepted_entities and ts is not None and accepted_entities[te].get("physical_schema") != ts:
            d.append(Diagnostic("SP023", f"decision:{did}", f"entity {te} maps to {accepted_entities[te].get('physical_schema')} but target_schema is {ts}"))
        # SP025: every target_object must live in the declared target_schema (relocation destination).
        if ts is not None:
            for tobj in row.get("target_objects", []):
                tschema = tobj.split(".", 1)[0]
                if tschema != ts:
                    d.append(Diagnostic("SP025", f"decision:{did}:{tobj}", f"target_object schema {tschema!r} != target_schema {ts!r}"))

        # required observations fresh for source relations (SP010)
        for r in src_rels:
            for field in req_obs:
                fv = r.get(field)
                if not isinstance(fv, dict) or fv.get("state") != "observed":
                    st = fv.get("state") if isinstance(fv, dict) else "missing"
                    d.append(Diagnostic("SP010", f"decision:{did}:{r['object_id']}:{field}", f"state={st} (required observed)"))
        # SP010: consumer_evidence is a nested object, so it is excluded from the generic loop above;
        # if the manifest EXPLICITLY requires it, enforce every consumer dimension observed/N-A here
        # (Codex R2: the requirement was silently dropped, letting a compat cluster green with
        # not_observed dims since compat has no resolved consumer_disposition).
        if require_consumer_evidence:
            for r in src_rels:
                ce = r.get("consumer_evidence", {})
                for dimname in DIMS:
                    st = ce.get(dimname, {}).get("state")
                    if st not in ("observed", "not_applicable"):
                        d.append(Diagnostic("SP010", f"decision:{did}:{r['object_id']}:consumer_evidence.{dimname}", f"state={st} (manifest required_observations includes consumer_evidence)"))

        # consumer conclusion — SP022 RESOLUTION applies to BOTH resolved conclusions (every dim
        # observed-or-not_applicable; operator_declaration observed); SP013 is the count agreement.
        conclusion = row.get("consumer_disposition")
        if conclusion in ("no_consumer", "has_consumers"):
            for r in src_rels:
                ce = r.get("consumer_evidence", {})
                observed_positive = False
                for dimname in DIMS:
                    dim = ce.get(dimname, {})
                    st = dim.get("state")
                    if dimname == "operator_declaration" and st != "observed":
                        d.append(Diagnostic("SP022", f"decision:{did}:{r['object_id']}:operator_declaration", f"state={st} (operator declaration must be observed)"))
                        continue
                    if dimname == "database_deps" and st != "observed":
                        d.append(Diagnostic("SP022", f"decision:{did}:{r['object_id']}:database_deps", f"state={st} (the machine dependency signal must be OBSERVED for a resolved conclusion; not_applicable is not permitted — finding #3)"))
                        continue
                    if st == "not_applicable":
                        continue
                    if st != "observed":
                        d.append(Diagnostic("SP022", f"decision:{did}:{r['object_id']}:{dimname}", f"state={st} (unresolved; a resolved conclusion needs every dim observed or not_applicable)"))
                        continue
                    if (dim.get("found_consumers") or 0) > 0:
                        observed_positive = True
                        if conclusion == "no_consumer":
                            d.append(Diagnostic("SP013", f"decision:{did}:{r['object_id']}:{dimname}", f"found_consumers={dim.get('found_consumers')} contradicts no_consumer"))
                if conclusion == "has_consumers" and not observed_positive:
                    d.append(Diagnostic("SP013", f"decision:{did}:{r['object_id']}", "has_consumers but no observed dimension found found_consumers>0"))

        # compat exit-condition gate numbers finite (SP015): threshold AND window_hours. The schema's
        # exclusiveMinimum:0 rejects NaN/-inf on window_hours but lets +inf through (inf > 0), and a
        # YAML .inf/.nan loads as a float — so an infinite exit window would silently defeat any
        # downstream "metric below threshold for window_hours" evaluation. Reject non-finite here
        # (correction tranche), mirroring the threshold check.
        # Check finiteness whenever an exit_condition is PRESENT — not only when required=true — so a
        # required=false contract carrying a non-finite window/threshold cannot slip past to a
        # downstream evaluator (F8). +inf enters via 1e999 overflow or YAML .inf, both passing the
        # schema's exclusiveMinimum:0.
        cc = row.get("compatibility_contract")
        if isinstance(cc, dict) and isinstance(cc.get("exit_condition"), dict):
            for numfield in ("threshold", "window_hours"):
                val = cc["exit_condition"].get(numfield)
                if not _finite(val):
                    d.append(Diagnostic("SP015", f"decision:{did}", f"exit_condition {numfield} {val} is not finite"))

        # SP014 (finding #5, correction tranche): a destructive delete's recovery_proof is a STRUCTURED
        # recovery_artifact — the checker resolves artifact_path within an approved root, verifies the
        # backup bytes hash to the declared sha256, resolves + non-empty-checks a restore_validation_ref
        # that is DISTINCT from artifact_path, and confirms the capture predates the census. This binds
        # STRUCTURE, not recoverability: that the backup ACTUALLY restores is an operator/apply-time
        # attestation the offline gate cannot verify (F2); the sha256 is author-declared, not an
        # independent source of truth.
        if row.get("action_class") == "delete" and row.get("decision_status") == "accepted":
            art = (row.get("retention_disposition") or {}).get("recovery_proof")
            if not isinstance(art, dict):
                d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", "delete recovery_proof must be a structured recovery_artifact"))
            else:
                art_resolved = None
                ap = art.get("artifact_path")
                if not (ap and is_path_ref(ap)):
                    d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery artifact_path {ap!r} must be a filesystem artifact under an approved root, not a scheme reference"))
                else:
                    resolved, reason = resolve_within_roots(ap, roots)
                    if resolved is None:
                        d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery artifact_path {ap}: {reason}"))
                    elif os.path.getsize(resolved) == 0:
                        d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery artifact {ap} is an EMPTY file — a recovery artifact must have content"))
                    else:
                        art_resolved = resolved
                        with open(resolved, "rb") as _fh:
                            actual = hashlib.sha256(_fh.read()).hexdigest()
                        if actual != art.get("sha256"):
                            d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery artifact sha256 {art.get('sha256')} does not match the actual bytes ({actual})"))
                rvr = art.get("restore_validation_ref")
                if not (rvr and is_path_ref(rvr)):
                    d.append(Diagnostic("SP014", f"decision:{did}:restore_validation_ref", f"restore_validation_ref {rvr!r} must be a filesystem artifact under an approved root"))
                else:
                    rvr_res, rvr_reason = resolve_within_roots(rvr, roots)
                    if rvr_res is None:
                        d.append(Diagnostic("SP014", f"decision:{did}:restore_validation_ref", f"restore_validation_ref {rvr}: {rvr_reason}"))
                    elif os.path.getsize(rvr_res) == 0:
                        d.append(Diagnostic("SP014", f"decision:{did}:restore_validation_ref", "restore_validation_ref is an EMPTY file — a restore-validation proof must have content (F2)"))
                    # Compare the RESOLVED files, not the declared path strings: a symlink/hardlink/path
                    # alias pointing restore_validation_ref at the backup would pass a string-inequality
                    # check yet be the same inode (operator finding). os.path.samefile catches it.
                    elif art_resolved is not None and os.path.samefile(rvr_res, art_resolved):
                        d.append(Diagnostic("SP014", f"decision:{did}:restore_validation_ref", "restore_validation_ref resolves to the SAME file as artifact_path (alias/symlink) — a backup is not its own restore proof (F2)"))
                cap = art.get("captured_at")
                if cap:
                    # The schema's date-time format now rejects calendar-invalid values (rfc3339-validator),
                    # but do NOT rely on that here (F1): a parse failure is a coded SP014, never a silent
                    # pass and never an uncaught traceback.
                    try:
                        cap_dt = parse_dt(cap)
                    except (ValueError, TypeError):
                        cap_dt = None
                        d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery captured_at {cap!r} is not a valid RFC3339 datetime"))
                    if cap_dt is not None and cap_dt > observed_at:
                        d.append(Diagnostic("SP014", f"decision:{did}:recovery_proof", f"recovery captured_at {cap} is after observed_at {snapshot['observed_at']}"))

            # SP027 destructive-evidence floor: NO discretionary waiver to catalog + declaration alone.
            # database_deps/static_repo/runtime_logs/operator_declaration must be OBSERVED for EVERY
            # source relation; external_clients OBSERVED, or not_applicable ONLY when the relation's API
            # exposure is OBSERVED false; and the consumer observation window must span >= 30 days.
            for r in src_rels:
                ce = r.get("consumer_evidence", {})
                for dimname in ("database_deps", "static_repo", "runtime_logs", "operator_declaration"):
                    if ce.get(dimname, {}).get("state") != "observed":
                        d.append(Diagnostic("SP027", f"decision:{did}:{r['object_id']}:{dimname}", f"delete floor requires {dimname} OBSERVED (got {ce.get(dimname, {}).get('state')})"))
                ext = ce.get("external_clients", {})
                if ext.get("state") == "not_applicable":
                    exposed = r.get("in_data_api_exposed_schema", {})
                    if not (isinstance(exposed, dict) and exposed.get("state") == "observed" and exposed.get("value") is False):
                        d.append(Diagnostic("SP027", f"decision:{did}:{r['object_id']}:external_clients", "external_clients not_applicable requires in_data_api_exposed_schema OBSERVED false"))
                elif ext.get("state") != "observed":
                    d.append(Diagnostic("SP027", f"decision:{did}:{r['object_id']}:external_clients", f"delete floor requires external_clients observed (got {ext.get('state')})"))
                w = ce.get("observation_window")
                if isinstance(w, dict) and "started_at" in w and "ended_at" in w:
                    hours = (parse_dt(w["ended_at"]) - parse_dt(w["started_at"])).total_seconds() / 3600.0
                    if hours < _DELETE_MIN_WINDOW_HOURS:
                        d.append(Diagnostic("SP027", f"decision:{did}:{r['object_id']}:runtime_logs", f"delete requires an observation window >= {_DELETE_MIN_WINDOW_HOURS}h (30d); got {hours:.1f}h"))

        # ALL path-capable references (SP014): evidence_refs + transform.validation_report +
        # compat.telemetry_ref + retention.recovery_proof + each source relation's consumer dim refs.
        path_refs = list(row.get("evidence_refs", []))
        _tr = row.get("transform")
        if isinstance(_tr, dict) and _tr.get("validation_report"):
            path_refs.append(_tr["validation_report"])
        _cc = row.get("compatibility_contract")
        if isinstance(_cc, dict) and _cc.get("telemetry_ref"):
            path_refs.append(_cc["telemetry_ref"])
        _rd = row.get("retention_disposition")
        if isinstance(_rd, dict) and isinstance(_rd.get("recovery_proof"), str):
            path_refs.append(_rd["recovery_proof"])  # legacy string form; the structured delete artifact is resolved above
        for r in src_rels:
            for dimname in DIMS:
                _ref = r.get("consumer_evidence", {}).get(dimname, {}).get("ref")
                if _ref:
                    path_refs.append(_ref)
        for ref in path_refs:
            if is_path_ref(ref):
                resolved, reason = resolve_within_roots(ref, roots)
                if resolved is None:
                    d.append(Diagnostic("SP014", f"decision:{did}", f"path ref {ref}: {reason}"))

    return d


def run(snapshot, decisions, entity_map, manifest, now, mode, roots, validator, snapshot_path=None, expect_project_ref=None, derived_window_object_ids=None):
    docs = {"evidence_snapshot": snapshot, "decisions_file": decisions, "entity_map": entity_map, "cluster_manifest": manifest}
    diags = schema_validate(docs, validator)
    # Pin each CLI input to its EXPECTED kind (finding #8): the top-level oneOf accepts any of the
    # four document types, so a wrong-kind file (e.g. a decisions_file passed as --snapshot) would
    # otherwise pass schema validation and then crash on a missing field mid-semantic-check.
    for expected, doc in docs.items():
        if isinstance(doc, dict) and doc.get("kind") != expected:
            diags.append(Diagnostic("SP001", f"{expected}:kind", f"expected kind={expected!r}, got {doc.get('kind')!r}"))
    if diags:
        return sorted(diags, key=lambda x: x.key())
    diags = semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path, expect_project_ref, derived_window_object_ids)
    return sorted(diags, key=lambda x: x.key())


def _checkout_gate(expect_gate_repo_sha, require_clean_checkout, allow_unbound):
    """SP028: decide the checkout binding from the flag combination alone, BEFORE any input document is
    read. Returns (ok, checkout_bound, production_eligible, gate_repo_sha, diagnostic_or_None). Only the
    bound path runs a git check, against the checker's own repo dir. Accidental unbound is impossible:
    neither-flag-nor-opt-in is refused."""
    has_gate = bool(expect_gate_repo_sha)
    has_clean = bool(require_clean_checkout)
    has_allow = bool(allow_unbound)
    if has_gate and has_clean and not has_allow:
        cdir = os.path.dirname(os.path.abspath(__file__))
        head = dp.git_head_sha(cdir)
        if not head or not dp.git_worktree_clean(cdir):
            return False, None, None, None, Diagnostic("SP028", "checkout", "checker checkout is DIRTY or its git HEAD is undeterminable — run preapply from a clean checkout at --expect-gate-repo-sha")
        if head != expect_gate_repo_sha:
            return False, None, None, None, Diagnostic("SP028", "checkout", f"checker git HEAD {head[:12]} != --expect-gate-repo-sha {expect_gate_repo_sha[:12]} (never the census snapshot repo_sha)")
        return True, True, True, expect_gate_repo_sha, None
    if (not has_gate) and (not has_clean) and has_allow:
        return True, False, False, None, None
    return False, None, None, None, Diagnostic("SP028", "checkout", "supply BOTH --expect-gate-repo-sha and --require-clean-checkout (bound), OR --allow-unbound-checkout alone (authoring-only); any other combination is refused")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline semantic gate for the disposition ledger.")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--entity-map", required=True, dest="entity_map")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--now", required=True, help="ISO-8601 timestamp; injected (no wall-clock).")
    ap.add_argument("--mode", default="preapply", choices=["preapply"])
    ap.add_argument("--expect-project-ref", default=None, dest="expect_project_ref", help="bind the snapshot's project_ref (REQUIRED for preapply; SP024).")
    ap.add_argument("--snapshot-sig", default=None, dest="snapshot_sig", help="path to the snapshot's detached Ed25519 signature sidecar (REQUIRED for preapply; SP026).")
    ap.add_argument("--key-id", default=None, dest="key_id", help="authorized signer id pinned in the TRUSTED_SIGNERS anchor (REQUIRED for preapply; SP026).")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir", help="dir holding <key-id>.pub.pem (public key MATERIAL only; the trust anchor is the source constant).")
    ap.add_argument("--expect-gate-repo-sha", default=None, dest="expect_gate_repo_sha", help="the reviewed merged commit the CHECKER must run from (bound preapply; SP028). Independent of the census snapshot repo_sha.")
    ap.add_argument("--require-clean-checkout", action="store_true", dest="require_clean_checkout", help="with --expect-gate-repo-sha, enforce the checker's own worktree is clean and at that SHA (SP028).")
    ap.add_argument("--allow-unbound-checkout", action="store_true", dest="allow_unbound_checkout", help="explicit opt-in for authoring-only unbound runs (production_eligible=false); refused together with the binding flags (SP028).")
    ap.add_argument("--receipt-out", default=None, dest="receipt_out", help="on GREEN, write a gate receipt (input SHA-256 digests) here for the apply runner to rehash.")
    ap.add_argument("--root", action="append", default=[], dest="roots", required=True, help="approved evidence root (repeatable, REQUIRED).")
    args = ap.parse_args(argv)

    # --- SP028 checkout-provenance gate: runs IMMEDIATELY after argument parsing, BEFORE any input
    # document is read, binding (or explicitly opting out of binding) the checker's OWN checkout to a
    # reviewed gate SHA. Accidental unbound is impossible (neither-flag-nor-opt-in -> SP028).
    ok, checkout_bound, production_eligible, gate_repo_sha, cdiag = _checkout_gate(
        args.expect_gate_repo_sha, args.require_clean_checkout, args.allow_unbound_checkout)
    if not ok:
        print(cdiag.render())
        print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ===")
        return 1

    # Read every input's bytes ONCE and parse from that same buffer, so the bytes the gate verifies
    # (SP026) and pins in the receipt are identical to the bytes it parsed and trusted (Codex P1).
    try:
        doc_bytes = {}
        for name, p in (("snapshot", args.snapshot), ("decisions", args.decisions),
                        ("entity_map", args.entity_map), ("manifest", args.manifest)):
            with open(p, "rb") as fh:
                doc_bytes[name] = fh.read()
        snapshot = load_doc_from_text(doc_bytes["snapshot"].decode("utf-8"), args.snapshot)
        decisions = load_doc_from_text(doc_bytes["decisions"].decode("utf-8"), args.decisions)
        entity_map = load_doc_from_text(doc_bytes["entity_map"].decode("utf-8"), args.entity_map)
        manifest = load_doc_from_text(doc_bytes["manifest"].decode("utf-8"), args.manifest)
        now = parse_dt(args.now)
    except (OSError, ValueError, yaml.YAMLError, UnicodeDecodeError) as exc:
        print(f"SP000 input: {exc}", file=sys.stderr)
        return 2

    roots = [os.path.abspath(r) for r in args.roots]

    # --- signature gate (SP026), BEFORE any semantic trust. The offline checker cannot bind a
    # self-attested snapshot (guard_passed/project_ref/target_identity/consumer_evidence are plain
    # JSON) to a genuine read-only census without verifying the collector's detached Ed25519
    # signature over the exact snapshot bytes (F1). preapply REQUIRES --snapshot-sig + --key-id;
    # a missing or non-verifying signature blocks and the semantic gate never runs. Default-deny:
    # gated for EVERY mode except an explicit exempt set (empty today), so a future --mode added to
    # argparse choices cannot silently run the gate unsigned (F5).
    signer = None
    sig_bytes = b""
    if args.mode not in _SIGNATURE_EXEMPT_MODES:
        if not args.snapshot_sig or not args.key_id:
            dg = Diagnostic("SP026", "snapshot", "preapply requires --snapshot-sig and --key-id (an unsigned snapshot is not trusted)")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        try:
            with open(os.path.abspath(args.snapshot_sig), "rb") as fh:
                sig_bytes = fh.read()
        except OSError as exc:
            dg = Diagnostic("SP026", "snapshot", f"cannot read signature sidecar ({type(exc).__name__})")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
        if signer is None:
            dg = Diagnostic("SP026", "snapshot", kreason)
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        ok, reason = ds.verify_sidecar_bytes_with_key(doc_bytes["snapshot"], sig_bytes, signer.public_key)
        if not ok:
            dg = Diagnostic("SP026", "snapshot", f"signature verification failed: {reason}")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1

    diags = run(snapshot, decisions, entity_map, manifest, now, args.mode, roots, _validator(), os.path.abspath(args.snapshot), args.expect_project_ref)

    for dg in diags:
        print(dg.render())
    if diags:
        print(f"=== DISPOSITION GATE ({args.mode}): {len(diags)} BLOCKING ===")
        return 1
    if args.receipt_out:
        if signer is None:
            print("SP000: receipt requested but the gate ran signature-exempt (no signer); refusing an incomplete receipt", file=sys.stderr)
            return 1
        doc_paths = {"snapshot": os.path.abspath(args.snapshot), "decisions": os.path.abspath(args.decisions),
                     "entity_map": os.path.abspath(args.entity_map), "manifest": os.path.abspath(args.manifest)}
        signer_meta = {"key_id": signer.key_id, "spki_sha256": signer.spki_sha256, "pem_sha256": signer.pem_sha256}
        snapshot_signature_sha256 = hashlib.sha256(sig_bytes).hexdigest()
        try:
            receipt = build_receipt(mode=args.mode, now_iso=args.now, expect_project_ref=args.expect_project_ref,
                                    doc_bytes=doc_bytes, doc_paths=doc_paths, signer=signer_meta,
                                    snapshot_signature_sha256=snapshot_signature_sha256,
                                    gate_repo_sha=gate_repo_sha, checkout_bound=checkout_bound,
                                    production_eligible=production_eligible, roots=roots, decisions=decisions)
            with open(args.receipt_out, "w", encoding="utf-8") as fh:
                json.dump(receipt, fh, indent=2, sort_keys=True)
        except OSError as exc:
            print(f"SP000: gate is GREEN but the receipt could not be produced ({type(exc).__name__}); refusing to emit an incomplete receipt", file=sys.stderr)
            return 1
        print(f"=== gate receipt written: {args.receipt_out} ({len(receipt['evidence'])} evidence files pinned) ===")
    if checkout_bound:
        print(f"=== DISPOSITION GATE ({args.mode}): GREEN ===")
    else:
        print("WARNING: unbound checkout — the trust anchor was trusted WITHOUT a reviewed gate SHA; authoring-only, not valid for production apply", file=sys.stderr)
        print(f"=== DISPOSITION GATE ({args.mode}): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
