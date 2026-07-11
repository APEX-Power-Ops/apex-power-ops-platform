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
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

import yaml
from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposition.schema.json")
DIMS = ("static_repo", "database_deps", "runtime_logs", "external_clients", "operator_declaration")
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
    "SP009": "consumer observation_window violates started<=ended<=observed_at",
    "SP010": "a required observation is not freshly observed",
    "SP011": "target_entity does not resolve to an accepted entity_map entry",
    "SP012": "target_schema does not resolve to an accepted physical_schema",
    "SP013": "consumer conclusion contradicts an observed evidence dimension",
    "SP014": "evidence path is missing, escapes an approved root, or is not a regular file",
    "SP015": "compat exit_condition threshold is not finite",
    "SP016": "cluster member decision is not accepted (required for preapply)",
    "SP017": "cluster is empty after resolution",
    "SP018": "manifest is not accepted with a cluster approval (required for preapply)",
    "SP019": "entity_map is not accepted but a decision needs entity/schema resolution",
    "SP020": "duplicate decision_id / entity_id / physical_schema identity",
    "SP021": "manifest evidence_snapshot differs from the supplied --snapshot",
    "SP022": "unresolved consumer-evidence dimension for a no_consumer conclusion",
    "SP023": "target_entity's physical_schema disagrees with target_schema",
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


def load_doc(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith(".json"):
        return json.loads(text, object_pairs_hook=_reject_dup_json_pairs)
    return yaml.load(text, Loader=NoDupSafeLoader)


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
def semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path):
    d = []
    relations = snapshot.get("relations", [])
    rel_by_oid = {}
    for r in relations:
        rel_by_oid.setdefault(r["object_id"], []).append(r)

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

    # --- snapshot freshness (SP008) ---
    observed_at = parse_dt(snapshot["observed_at"])
    if observed_at > now:
        d.append(Diagnostic("SP008", "snapshot", f"observed_at {snapshot['observed_at']} is after --now"))
    max_stale = manifest.get("max_staleness_hours")
    if max_stale is not None and (now - observed_at).total_seconds() / 3600.0 > max_stale:
        d.append(Diagnostic("SP008", "snapshot", f"age exceeds max_staleness_hours {max_stale}"))
    min_window = manifest.get("minimum_consumer_window_hours") or 0

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

        # window ordering (strict) + minimum duration, scoped to this cluster's source relations (SP009)
        for r in src_rels:
            w = r.get("consumer_evidence", {}).get("observation_window")
            if isinstance(w, dict) and "started_at" in w and "ended_at" in w:
                s, e = parse_dt(w["started_at"]), parse_dt(w["ended_at"])
                if not (s < e <= observed_at):
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window {w['started_at']}..{w['ended_at']} must satisfy started<ended<=observed_at ({snapshot['observed_at']})"))
                elif (e - s).total_seconds() / 3600.0 < min_window:
                    d.append(Diagnostic("SP009", f"decision:{did}:{r['object_id']}", f"window duration {(e - s).total_seconds() / 3600.0:.2f}h < minimum_consumer_window_hours {min_window}"))

        # target resolution (SP019/SP011/SP012/SP023)
        te, ts = row.get("target_entity"), row.get("target_schema")
        if (te is not None or ts is not None) and not entity_map_accepted:
            d.append(Diagnostic("SP019", f"decision:{did}", f"entity_map.approval={entity_map.get('approval')} (targets require accepted map)"))
        if te is not None and te not in accepted_entities:
            d.append(Diagnostic("SP011", f"decision:{did}", f"target_entity {te} not an accepted entity"))
        if ts is not None and ts not in accepted_schemas:
            d.append(Diagnostic("SP012", f"decision:{did}", f"target_schema {ts} not an accepted physical_schema"))
        if te in accepted_entities and ts is not None and accepted_entities[te].get("physical_schema") != ts:
            d.append(Diagnostic("SP023", f"decision:{did}", f"entity {te} maps to {accepted_entities[te].get('physical_schema')} but target_schema is {ts}"))

        # required observations fresh for source relations (SP010)
        for r in src_rels:
            for field in req_obs:
                fv = r.get(field)
                if not isinstance(fv, dict) or fv.get("state") != "observed":
                    st = fv.get("state") if isinstance(fv, dict) else "missing"
                    d.append(Diagnostic("SP010", f"decision:{did}:{r['object_id']}:{field}", f"state={st} (required observed)"))

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

        # compat threshold finite (SP015)
        cc = row.get("compatibility_contract")
        if isinstance(cc, dict) and cc.get("required") and isinstance(cc.get("exit_condition"), dict):
            thr = cc["exit_condition"].get("threshold")
            if not isinstance(thr, (int, float)) or isinstance(thr, bool) or not math.isfinite(thr):
                d.append(Diagnostic("SP015", f"decision:{did}", f"exit_condition threshold {thr} is not finite"))

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
        if isinstance(_rd, dict) and _rd.get("recovery_proof"):
            path_refs.append(_rd["recovery_proof"])
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


def run(snapshot, decisions, entity_map, manifest, now, mode, roots, validator, snapshot_path=None):
    docs = {"evidence_snapshot": snapshot, "decisions_file": decisions, "entity_map": entity_map, "cluster_manifest": manifest}
    diags = schema_validate(docs, validator)
    if diags:
        return sorted(diags, key=lambda x: x.key())
    diags = semantic_check(snapshot, decisions, entity_map, manifest, now, mode, roots, snapshot_path)
    return sorted(diags, key=lambda x: x.key())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline semantic gate for the disposition ledger.")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--entity-map", required=True, dest="entity_map")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--now", required=True, help="ISO-8601 timestamp; injected (no wall-clock).")
    ap.add_argument("--mode", default="preapply", choices=["preapply"])
    ap.add_argument("--root", action="append", default=[], dest="roots", required=True, help="approved evidence root (repeatable, REQUIRED).")
    args = ap.parse_args(argv)

    try:
        snapshot = load_doc(args.snapshot)
        decisions = load_doc(args.decisions)
        entity_map = load_doc(args.entity_map)
        manifest = load_doc(args.manifest)
        now = parse_dt(args.now)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"SP000 input: {exc}", file=sys.stderr)
        return 2

    roots = [os.path.abspath(r) for r in args.roots]
    diags = run(snapshot, decisions, entity_map, manifest, now, args.mode, roots, _validator(), os.path.abspath(args.snapshot))

    for dg in diags:
        print(dg.render())
    if diags:
        print(f"=== DISPOSITION GATE ({args.mode}): {len(diags)} BLOCKING ===")
        return 1
    print(f"=== DISPOSITION GATE ({args.mode}): GREEN ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
