"""Offline CENSUS-ACCEPTANCE gate for a raw signed census snapshot.

This is DISTINCT from check_disposition.py's preapply DECISION gate. A RAW census intentionally
carries zero-width consumer windows and `not_observed` overlay fields, and there are NO ledger
documents yet (decisions / entity_map / cluster_manifest), so a legitimate raw census CANNOT and
MUST NOT pass preapply. This gate instead proves that a snapshot is a genuine, signed, IN-SCOPE
read-only census of the expected target at the expected merged-repo commit — the acceptance step
before a census becomes authoritative evidence.

    verify_census.py --snapshot S --snapshot-sig SIG --key-id <signer id> [--keys-dir DIR] \
        --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres \
        --expect-schemas public --expect-repo-sha <merged main SHA> \
        --require-role-markers anon,authenticated,service_role [--expect-query-bundle-sha256 HEX]

The trust anchor is REVIEWED VERIFIER SOURCE: --key-id must name a signer pinned in the TRUSTED_SIGNERS
source constant, and keys/<key-id>.pub.pem is accepted only if its SPKI fingerprint equals the pinned
value (it is public key MATERIAL, not the anchor — a caller-supplied keys dir cannot substitute its own
key). The detached Ed25519 signature is verified against that pinned key BEFORE the snapshot is parsed
(CN001/CN013). Error codes are stable (CN0xx). Exit 0 only when every assertion holds.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from jsonschema import Draft202012Validator, FormatChecker

import collect_disposition as cds  # for the authoritative query_bundle_sha256() of THIS repo checkout
import disposition_provenance as dp
import disposition_signing as ds
import disposition_trust as dt

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "disposition.schema.json")

# relation fact fields (each an observation with a `state`); a census-acceptance rejects ANY that
# came back query_failed (an incomplete census must not become authoritative).
_FACT_FIELDS = ("owner", "rls_enabled", "is_security_definer_view", "in_data_api_exposed_schema",
                "anon_effective_privs", "authenticated_effective_privs", "inbound_fk_count",
                "outbound_fk_count", "dependent_objects", "row_estimate", "advisor_findings")
_CONSUMER_DIMS = ("static_repo", "database_deps", "runtime_logs", "external_clients", "operator_declaration")

CODES = {
    "CN000": "input could not be read/parsed",
    "CN001": "snapshot signature is missing or does not verify against the pinned signer (--key-id resolved through the reviewed TRUSTED_SIGNERS anchor)",
    "CN002": "snapshot failed JSON Schema validation or is not kind=evidence_snapshot",
    "CN003": "project_ref does not match --expect-project-ref",
    "CN004": "current_database / collection_scope.expected_database does not match --expect-database",
    "CN005": "collection_scope.schemas does not match --expect-schemas",
    "CN006": "query_bundle_sha256 does not match the expected collector query bundle",
    "CN007": "repo_sha does not match --expect-repo-sha (the merged main commit)",
    "CN008": "required role markers not asserted in collection_scope / not present in target_identity",
    "CN009": "relation_count does not equal the number of relations",
    "CN010": "relation object_id does not equal schema + '.' + name",
    "CN011": "a catalog query group came back query_failed (census is incomplete)",
    "CN012": "a relation is outside the requested collection scope",
    "CN013": "signer --key-id is not an authorized signer, or its public key's SPKI fingerprint does not match the reviewed TRUSTED_SIGNERS anchor",
    "CN014": "empty census (zero relations) is not accepted",
    "CN015": "duplicate object_id (two relation records share an identity)",
    "CN016": "internal inconsistency: a top-level field disagrees with collection_scope (collector_version / repo_sha / query_bundle_sha256)",
    "CN017": "verifier preflight: the acceptance gate is not running a clean checkout of reviewed source at --expect-repo-sha",
}


class Diagnostic:
    __slots__ = ("code", "locus", "message")

    def __init__(self, code, locus, message):
        self.code, self.locus, self.message = code, locus, message

    def key(self):
        return (self.code, self.locus)

    def render(self):
        return f"{self.code} {self.locus}: {self.message}"


def _reject_nonfinite(const):
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def _reject_dup_json_pairs(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def load_snapshot_from_bytes(data: bytes):
    return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_dup_json_pairs, parse_constant=_reject_nonfinite)


def _validator():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def check_census(snapshot, *, expect_project_ref, expect_database, expect_schemas, expect_repo_sha,
                 require_role_markers, expect_query_bundle_sha256=None, validator=None):
    """Semantic census-acceptance checks on an already-parsed (and signature-verified) snapshot.
    Returns a sorted list of Diagnostics; empty means accept."""
    d = []
    validator = validator or _validator()
    for err in sorted(validator.iter_errors(snapshot), key=lambda e: str(e.path)):
        path = "/".join(str(p) for p in err.path) or "<root>"
        d.append(Diagnostic("CN002", f"snapshot:{path}", err.message))
    if isinstance(snapshot, dict) and snapshot.get("kind") != "evidence_snapshot":
        d.append(Diagnostic("CN002", "snapshot:kind", f"expected kind=evidence_snapshot, got {snapshot.get('kind')!r}"))
    if d:
        return sorted(d, key=lambda x: x.key())  # structure untrustworthy; don't read fields

    cs = snapshot.get("collection_scope", {})
    ti = snapshot.get("target_identity", {})

    if snapshot.get("project_ref") != expect_project_ref:
        d.append(Diagnostic("CN003", "snapshot", f"project_ref {snapshot.get('project_ref')!r} != --expect-project-ref {expect_project_ref!r}"))
    if (ti.get("current_database") != expect_database or cs.get("expected_database") != expect_database
            or ti.get("expected_database") != expect_database):
        d.append(Diagnostic("CN004", "snapshot", f"database current={ti.get('current_database')!r} scope={cs.get('expected_database')!r} ti.expected={ti.get('expected_database')!r} != --expect-database {expect_database!r}"))
    # internal consistency: the top-level provenance fields must agree with their collection_scope echo
    for f in ("collector_version", "repo_sha", "query_bundle_sha256"):
        if snapshot.get(f) != cs.get(f):
            d.append(Diagnostic("CN016", f"snapshot:{f}", f"top-level {snapshot.get(f)!r} != collection_scope {cs.get(f)!r}"))
    if sorted(cs.get("schemas", [])) != sorted(expect_schemas):
        d.append(Diagnostic("CN005", "snapshot:collection_scope", f"schemas {sorted(cs.get('schemas', []))} != --expect-schemas {sorted(expect_schemas)}"))

    exp_qb = expect_query_bundle_sha256 or cds.query_bundle_sha256()
    if snapshot.get("query_bundle_sha256") != exp_qb or cs.get("query_bundle_sha256") != exp_qb:
        d.append(Diagnostic("CN006", "snapshot", f"query_bundle_sha256 does not match the expected collector query bundle ({exp_qb[:12]}...)"))
    if snapshot.get("repo_sha") != expect_repo_sha or cs.get("repo_sha") != expect_repo_sha:
        d.append(Diagnostic("CN007", "snapshot", f"repo_sha snapshot={snapshot.get('repo_sha')!r} scope={cs.get('repo_sha')!r} != --expect-repo-sha {expect_repo_sha!r}"))

    req = set(require_role_markers)
    markers = set(ti.get("platform_role_markers", []))
    if sorted(cs.get("required_role_markers", [])) != sorted(req):
        d.append(Diagnostic("CN008", "snapshot:collection_scope", f"required_role_markers {sorted(cs.get('required_role_markers', []))} != {sorted(req)}"))
    if not req.issubset(markers):
        d.append(Diagnostic("CN008", "snapshot:target_identity", f"platform_role_markers {sorted(markers)} missing {sorted(req - markers)}"))

    rels = snapshot.get("relations", [])
    n = len(rels)
    if snapshot.get("relation_count") != n or snapshot.get("catalog_relation_count") != n:
        d.append(Diagnostic("CN009", "snapshot", f"relation_count={snapshot.get('relation_count')} / catalog_relation_count={snapshot.get('catalog_relation_count')} but {n} relations — the emitted list, its count, and the independent catalog count must all agree"))
    if not rels:
        d.append(Diagnostic("CN014", "snapshot", "empty census (zero relations) is not accepted"))
    # duplicate object_id: JSON Schema uniqueItems catches only byte-identical records, not two
    # DIFFERING records sharing an identity (operator finding).
    oid_counts = {}
    for r in rels:
        oid_counts[r.get("object_id")] = oid_counts.get(r.get("object_id"), 0) + 1
    for oid, cnt in sorted((o, c) for o, c in oid_counts.items() if c > 1):
        d.append(Diagnostic("CN015", f"snapshot:{oid}", f"object_id appears {cnt} times (duplicate identity)"))

    scope = set(cs.get("schemas", []))
    for r in rels:
        oid = r.get("object_id")
        if oid != f"{r.get('schema')}.{r.get('name')}":
            d.append(Diagnostic("CN010", f"snapshot:{oid}", f"!= {r.get('schema')}.{r.get('name')}"))
        if r.get("schema") not in scope:
            d.append(Diagnostic("CN012", f"snapshot:{oid}", f"schema {r.get('schema')!r} is outside the requested scope {sorted(scope)}"))
        for f in _FACT_FIELDS:
            fv = r.get(f)
            if isinstance(fv, dict) and fv.get("state") == "query_failed":
                d.append(Diagnostic("CN011", f"snapshot:{oid}:{f}", "catalog query group came back query_failed"))
        ce = r.get("consumer_evidence", {})
        for dim in _CONSUMER_DIMS:
            dv = ce.get(dim)
            if isinstance(dv, dict) and dv.get("state") == "query_failed":
                d.append(Diagnostic("CN011", f"snapshot:{oid}:consumer_evidence.{dim}", "catalog query group came back query_failed"))

    return sorted(d, key=lambda x: x.key())


def main(argv=None):
    ap = argparse.ArgumentParser(description="Offline census-acceptance gate for a signed census snapshot.")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--snapshot-sig", required=True, dest="snapshot_sig")
    ap.add_argument("--key-id", required=True, dest="key_id",
                    help="authorized signer id pinned in the TRUSTED_SIGNERS source anchor, e.g. "
                         "prod-disposition-ed25519-2026-07; keys/<key-id>.pub.pem must match its pinned SPKI fingerprint.")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir",
                    help="dir holding <key-id>.pub.pem (public key MATERIAL only; the trust anchor is the source constant).")
    ap.add_argument("--expect-project-ref", required=True, dest="expect_project_ref")
    ap.add_argument("--expect-database", required=True, dest="expect_database")
    ap.add_argument("--expect-schemas", required=True, dest="expect_schemas", help="comma-separated requested schemas.")
    ap.add_argument("--expect-repo-sha", required=True, dest="expect_repo_sha", help="the MERGED main commit the census must identify.")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role", dest="require_role_markers")
    ap.add_argument("--expect-query-bundle-sha256", required=True, dest="expect_query_bundle_sha256",
                    help="REQUIRED: the reviewed collector query-bundle hash CN006 must match (removes the "
                         "self-referential default; must equal collect_disposition.query_bundle_sha256() at the census commit).")
    ap.add_argument("--require-clean-checkout", action="store_true", dest="require_clean_checkout",
                    help="preflight: assert the verifier's OWN git checkout is clean AND at --expect-repo-sha before "
                         "trusting TRUSTED_SIGNERS + keys/ (binds the acceptance gate to reviewed source). The runbook sets this.")
    args = ap.parse_args(argv)

    # Verifier provenance preflight (opt-in; the runbook sets it): the trust anchor is verifier SOURCE
    # (TRUSTED_SIGNERS) + the keys/ material it loads, so bind BOTH to the reviewed merged commit before
    # trusting them. Fail-closed on a dirty / undeterminable / mismatched checkout.
    if args.require_clean_checkout:
        vdir = os.path.dirname(os.path.abspath(__file__))
        head = dp.git_head_sha(vdir)
        if not head or not dp.git_worktree_clean(vdir):
            print(Diagnostic("CN017", "verifier", "verifier checkout is DIRTY or its git HEAD is undeterminable — run acceptance from a clean merged-main checkout so TRUSTED_SIGNERS + keys/ are reviewed source").render())
            print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
            return 1
        if head != args.expect_repo_sha:
            print(Diagnostic("CN017", "verifier", f"verifier git HEAD {head[:12]} != --expect-repo-sha {args.expect_repo_sha[:12]} — the acceptance gate must run reviewed source at the expected merged commit").render())
            print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
            return 1

    # Read the snapshot bytes ONCE and verify the signature BEFORE parsing (a forged/tampered snapshot
    # must never be parsed or trusted). The bytes verified are exactly the bytes parsed below.
    try:
        with open(args.snapshot, "rb") as fh:
            snap_bytes = fh.read()
    except OSError as exc:
        print(f"CN000 input: cannot read snapshot ({type(exc).__name__})", file=sys.stderr)
        return 2
    # Resolve the trust anchor from the reviewed SOURCE CONSTANT (TRUSTED_SIGNERS), not a caller path,
    # and verify against the loaded key OBJECT so the fingerprint-checked key IS the verify key (H1/H3).
    signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
    if signer is None:
        print(Diagnostic("CN013", "key-id", kreason).render())
        print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
        return 1
    ok, reason = ds.verify_detached_with_key(snap_bytes, os.path.abspath(args.snapshot_sig), signer.public_key)
    if not ok:
        print(Diagnostic("CN001", "snapshot", f"signature verification failed: {reason}").render())
        print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
        return 1
    try:
        snapshot = load_snapshot_from_bytes(snap_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"CN000 input: cannot parse snapshot ({exc})", file=sys.stderr)
        return 2

    expect_schemas = [s.strip() for s in args.expect_schemas.split(",") if s.strip()]
    require_role_markers = [s.strip() for s in args.require_role_markers.split(",") if s.strip()]
    diags = check_census(snapshot, expect_project_ref=args.expect_project_ref, expect_database=args.expect_database,
                         expect_schemas=expect_schemas, expect_repo_sha=args.expect_repo_sha,
                         require_role_markers=require_role_markers, expect_query_bundle_sha256=args.expect_query_bundle_sha256)
    for dg in diags:
        print(dg.render())
    if diags:
        print(f"=== CENSUS ACCEPTANCE: {len(diags)} BLOCKING ===")
        return 1
    print(f"=== CENSUS ACCEPTANCE: GREEN ({snapshot['relation_count']} relations, scope {sorted(snapshot['collection_scope']['schemas'])}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
