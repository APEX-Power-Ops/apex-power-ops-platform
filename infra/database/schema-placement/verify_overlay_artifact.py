"""Standalone committed-artifact verifier for a signed evidence overlay + its bound census.

Scope (spec 4.1): an ARTIFACT INTEGRITY + BASE-CENSUS-ACCEPTANCE gate. It verifies both detached
signatures against the source-pinned signer, runs the FULL verify_census.check_census contract on
the base census, and re-runs the consumer's per-artifact checks (schema, binding, window, the
OV010 future-half captured_at<=now, target, intra-overlay OV007) over the exact committed bytes.
It does NOT run cluster derivation (OV011/015/016/017/018/021/022) or the manifest-staleness half
of OV010 -- those belong to check_disposition --mode preapply. A GREEN here is NOT
evidence-readiness."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone

import disposition_overlay as dov
import disposition_signing as ds
import disposition_trust as dt
import verify_census as vc


def verify_artifact(overlay_bytes, *, census, census_bytes_sha, contract, expect_project_ref, now):
    """Artifact-side pipeline AFTER signature + census acceptance. Fail-closed and coded: a signed
    non-object or schema-invalid payload yields OV008 and SHORT-CIRCUITS (round-1 DAG-F1/CC4)."""
    loc = "artifact:overlay"
    try:
        doc = dov.parse_overlay(overlay_bytes)
    except ValueError as exc:
        return [("OV008", loc, f"overlay does not parse ({exc})")]
    if not isinstance(doc, dict):
        return [("OV008", loc, f"overlay is not a JSON object (got {type(doc).__name__})")]
    diags = dov.validate_overlay(doc, contract.overlay_validator)
    if diags:
        return diags
    diags += dov.check_binding(doc, census_sha256=census_bytes_sha,
                               census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref,
                               on_disk_disp_sha=contract.disp_sha256,
                               on_disk_overlay_sha=contract.overlay_sha256)
    diags += dov.check_observation_window(doc, now)
    try:
        if dov._parse_iso(doc["captured_at"]) > now:
            diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at is in the future"))
    except (KeyError, ValueError, TypeError):
        diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at unparseable"))
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}
    diags += dov.check_target(doc, rel_index)
    diags += dov.check_conflict([(doc.get("dimension"), a.get("object_id"))
                                 for a in doc.get("assignments", [])])
    return diags


def _blocking(lines):
    for line in lines:
        print(line)
    print(f"=== OVERLAY ARTIFACT: {len(lines)} BLOCKING ===")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Standalone verifier for a committed overlay + its bound census.")
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--overlay-sig", required=True, dest="overlay_sig")
    ap.add_argument("--census", required=True)
    ap.add_argument("--census-sig", required=True, dest="census_sig")
    ap.add_argument("--key-id", required=True, dest="key_id")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir")
    ap.add_argument("--expect-project-ref", required=True, dest="expect_project_ref")
    ap.add_argument("--expect-database", required=True, dest="expect_database")
    ap.add_argument("--expect-schemas", required=True, dest="expect_schemas")
    ap.add_argument("--expect-census-repo-sha", required=True, dest="expect_census_repo_sha")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role", dest="require_role_markers")
    ap.add_argument("--expect-query-bundle-sha256", required=True, dest="expect_query_bundle_sha256")
    args = ap.parse_args(argv)

    signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
    if signer is None:
        return _blocking([f"key-id: {kreason}"])
    try:
        with open(args.overlay, "rb") as fh:
            overlay_bytes = fh.read()
        with open(args.overlay_sig, "rb") as fh:
            overlay_sig_bytes = fh.read()
        with open(args.census, "rb") as fh:
            census_bytes = fh.read()
        with open(args.census_sig, "rb") as fh:
            census_sig_bytes = fh.read()
    except OSError as exc:
        print(f"OV000 input: cannot read artifact inputs ({type(exc).__name__})", file=sys.stderr)
        return 2
    ok, reason = ds.verify_sidecar_bytes_with_key(overlay_bytes, overlay_sig_bytes, signer.public_key)
    if not ok:
        return _blocking([f"OV001 overlay: signature verification failed: {reason}"])
    ok, reason = ds.verify_sidecar_bytes_with_key(census_bytes, census_sig_bytes, signer.public_key)
    if not ok:
        return _blocking([f"OV001 census: base census signature verification failed: {reason}"])
    try:
        census = vc.load_snapshot_from_bytes(census_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"OV000 input: cannot parse census ({type(exc).__name__})", file=sys.stderr)
        return 2
    cdiags = vc.check_census(census,
                             expect_project_ref=args.expect_project_ref,
                             expect_database=args.expect_database,
                             expect_schemas=[s.strip() for s in args.expect_schemas.split(",") if s.strip()],
                             expect_repo_sha=args.expect_census_repo_sha,
                             require_role_markers=[s.strip() for s in args.require_role_markers.split(",") if s.strip()],
                             expect_query_bundle_sha256=args.expect_query_bundle_sha256)
    if cdiags:
        return _blocking([d.render() for d in cdiags])
    try:
        contract = dov.load_overlay_contract()
    except dov.OverlayRegistryError as exc:
        return _blocking([f"OV008 contract: cannot build offline overlay contract ({type(exc).__name__})"])
    now = datetime.now(timezone.utc)
    diags = verify_artifact(overlay_bytes, census=census,
                            census_bytes_sha=hashlib.sha256(census_bytes).hexdigest(),
                            contract=contract, expect_project_ref=args.expect_project_ref, now=now)
    if diags:
        return _blocking([f"{c} {l}: {m}" for c, l, m in diags])
    doc = dov.parse_overlay(overlay_bytes)
    print(f"=== OVERLAY ARTIFACT: GREEN ({doc['dimension']}, {len(doc['assignments'])} assignments, "
          f"census {hashlib.sha256(census_bytes).hexdigest()[:12]}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
