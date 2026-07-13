"""Overlay author/sign CLI for the disposition-ledger signed-overlay contract (publication packet).

Assembles ONE per-dimension evidence overlay bound to a signed census, validates the EXACT
serialized bytes through the merged consumer's own per-artifact checks (disposition_overlay),
verifies the base census through the FULL census-acceptance contract (verify_census.check_census),
enforces signer parity against the source-pinned trust anchor (disposition_trust), and publishes
{source record?, sidecar, overlay} atomically, sidecar-first, no-clobber.

Fail-closed: stable AO0xx codes, never a stack trace. Value-silent: the signing key comes ONLY
from env (never argv/printed); --source-file content is secret-bearing and is only read+hashed
(AO009 reports path + exception type, never content)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import disposition_overlay as dov
import disposition_provenance as dp
import disposition_signing as ds
import disposition_trust as dt
import verify_census as vc

SP_DIR = os.path.dirname(os.path.abspath(__file__))
AUTHOR_VERSION = "0.1.0"

AO_CODES = {
    "AO000": "input unreadable/invalid",
    "AO001": "census signature failed (untrusted/forged base)",
    "AO002": "--input missing/invalid field (incl. NA-reason misuse for the dimension)",
    "AO003": "--expect-project-ref != census.project_ref",
    "AO004": "source-file / NA-reason / custody-locator exclusivity violation",
    "AO005": "assembled overlay failed a consumer check (see the OV0xx lines above)",
    "AO006": "reserved",
    "AO007": "signing key unset, invalid PEM, or fingerprint != pinned signer",
    "AO008": "publish failed / path exists (no-clobber)",
    "AO009": "source-file unreadable (path + exception type only; value-silent)",
    "AO010": "provenance gate: dirty worktree or HEAD != --expect-gate-repo-sha",
    "AO011": "base census failed verify_census acceptance (see the CN0xx detail)",
    "AO012": "in-memory sidecar verification failed",
    "AO013": "signer key-id not resolvable through the TRUSTED_SIGNERS anchor",
}


class AuthorError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code} author: {message}")
        self.code, self.message = code, message


def _canon(doc) -> bytes:
    """THE signed-message serialization -- byte-identical to collect_disposition._serialize_snapshot."""
    return json.dumps(doc, indent=2, sort_keys=True).encode("utf-8")


_CORE_REQUIRED = ("dimension", "assignments", "observation_window", "authority", "collection_method")


def load_input_core(path):
    """Operator SEMANTICS only (spec 3.1). AO000 unreadable/unparseable; AO002 structurally invalid.
    Full per-field validation is the consumer schema's job (validate_assembled)."""
    try:
        with open(path, "rb") as fh:
            core = json.loads(fh.read().decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise AuthorError("AO000", f"cannot read/parse --input ({type(exc).__name__})")
    if not isinstance(core, dict):
        raise AuthorError("AO002", f"--input must be a JSON object (got {type(core).__name__})")
    missing = [k for k in _CORE_REQUIRED if k not in core]
    if missing:
        raise AuthorError("AO002", "--input missing required field(s): " + ",".join(missing))
    if core["dimension"] not in dov.DIMENSIONS:
        raise AuthorError("AO002", f"--input dimension {core['dimension']!r} is not one of the six permitted paths")
    if not isinstance(core["assignments"], list) or not core["assignments"]:
        raise AuthorError("AO002", "--input assignments must be a non-empty array")
    return core


def compute_producing(dimension, gate_repo_sha, na_reason):
    """The three OV012 categories (spec 3.3). For REQUIRED dims, producing_repo_sha is the AUTHOR's
    schema-pub clean-merged-main HEAD (== --expect-gate-repo-sha) -- NEVER the external scanned-repo
    commit (those are enumerated in the source record). Returns (sha_or_None, reason_or_None)."""
    reason = (na_reason or "").strip()
    if dimension in dov._PRODUCING_SHA_REQUIRED:
        if reason:
            raise AuthorError("AO002", f"--producing-repo-sha-na-reason must be ABSENT for {dimension} (producing_repo_sha is required)")
        return gate_repo_sha, None
    if dimension in dov._PRODUCING_SHA_FORBIDDEN:
        if not reason:
            raise AuthorError("AO002", f"--producing-repo-sha-na-reason is REQUIRED for {dimension} (producing_repo_sha must be null)")
        return None, reason
    if reason:  # conditional (external_clients): null + reason
        return None, reason
    return gate_repo_sha, None  # conditional: repo-backed inventory -> author HEAD


def read_source(source_file, na_reason, custody_locator):
    """Value-silent source intake (spec 3.1 + round-2b Codex P2). Exactly one of source_file /
    na_reason; custody_locator IFF na_reason. Returns (bytes|None, reason|None, custody|None,
    ext|None). AO009 reports ONLY path + exception type -- source content is secret-bearing."""
    has_file = source_file is not None
    has_reason = bool((na_reason or "").strip())
    has_custody = bool((custody_locator or "").strip())
    if has_file == has_reason:
        raise AuthorError("AO004", "exactly one of --source-file / --source-hash-na-reason is required")
    if has_reason != has_custody:
        raise AuthorError("AO004", "--source-custody-locator is required with --source-hash-na-reason and forbidden otherwise")
    if has_file:
        try:
            with open(source_file, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            raise AuthorError("AO009", f"source-file unreadable: {source_file} ({type(exc).__name__})")
        ext = os.path.splitext(source_file)[1] or ".dat"
        return data, None, None, ext
    return None, na_reason.strip(), custody_locator.strip(), None


def assemble_overlay(core, *, census, census_sha256, contract, producing, source_hash,
                     source_hash_reason, source_locator, captured_at_iso):
    """Mechanical binder (spec 3.3): every binding value is COMPUTED by the caller pipeline;
    the operator core contributes semantics only. NA-reason fields appear IFF the value is null
    (the OV012/OV019 IFF shapes)."""
    doc = {
        "kind": "evidence_overlay", "overlay_version": "1",
        "dimension": core["dimension"],
        "source_type": dov.DIMENSIONS[core["dimension"]][1],
        "authority": core["authority"], "collection_method": core["collection_method"],
        "source_locator": source_locator, "source_hash": source_hash,
        "base_snapshot_sha256": census_sha256,
        "disposition_schema_sha256": contract.disp_sha256,
        "overlay_schema_sha256": contract.overlay_sha256,
        "project_ref": census.get("project_ref"),
        "captured_at": captured_at_iso,
        "observation_window": core["observation_window"],
        "producing_repo_sha": producing[0],
        "assignments": core["assignments"],
    }
    if source_hash is None:
        doc["source_hash_not_applicable_reason"] = source_hash_reason
    if producing[0] is None:
        doc["producing_repo_sha_not_applicable_reason"] = producing[1]
    for k in ("operator_identity", "attestation_ref"):
        if k in core:
            doc[k] = core[k]
    return doc


def validate_assembled(message, *, census, census_bytes_sha, contract, expect_project_ref, now):
    """Validate the EXACT signed bytes (spec 3.5 + round-1 DAG-F5): round-trip through
    parse_overlay so the dup-key/non-finite guard covers what is signed, then run the consumer's
    per-artifact checks, the OV010 future-half, and the intra-overlay flat OV007. Any schema
    failure SHORT-CIRCUITS (mirrors load_and_merge -- a schema-invalid doc is not safe to
    bind/window/target)."""
    loc = "author:assembled"
    try:
        doc = dov.parse_overlay(message)
    except ValueError as exc:
        return [("OV008", loc, f"serialized overlay does not re-parse ({exc})")]
    if not isinstance(doc, dict):
        return [("OV008", loc, f"serialized overlay is not a JSON object (got {type(doc).__name__})")]
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


def accept_census(census_bytes, sig_bytes, *, signer, expects):
    """FULL census acceptance, not just signature (spec 3.4; operator round-1 #2). Order:
    signature over the exact bytes -> the census gate's own strict parse -> explicit AO003 ->
    check_census. The bytes verified ARE the bytes parsed (read-once discipline)."""
    ok, reason = ds.verify_sidecar_bytes_with_key(census_bytes, sig_bytes, signer.public_key)
    if not ok:
        raise AuthorError("AO001", f"census signature verification failed: {reason}")
    try:
        census = vc.load_snapshot_from_bytes(census_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthorError("AO000", f"cannot parse census ({type(exc).__name__})")
    if not isinstance(census, dict):
        raise AuthorError("AO000", f"census is not a JSON object (got {type(census).__name__})")
    if census.get("project_ref") != expects["project_ref"]:
        raise AuthorError("AO003", f"census project_ref {census.get('project_ref')!r} != --expect-project-ref {expects['project_ref']!r}")
    diags = vc.check_census(census,
                            expect_project_ref=expects["project_ref"],
                            expect_database=expects["database"],
                            expect_schemas=expects["schemas"],
                            expect_repo_sha=expects["census_repo_sha"],
                            require_role_markers=expects["role_markers"],
                            expect_query_bundle_sha256=expects["query_bundle_sha256"])
    if diags:
        head = "; ".join(d.render() for d in diags[:5])
        more = f" (+{len(diags) - 5} more)" if len(diags) > 5 else ""
        raise AuthorError("AO011", f"base census failed acceptance: {head}{more}")
    return census


def load_signing_key(env_name, signer):
    """Signer parity (spec 3.5; operator round-1 #5). Value-silent: the PEM never appears in any
    message; explicit coded checks, never a bare assert."""
    pem = os.environ.get(env_name)
    if not pem:
        raise AuthorError("AO007", f"env var {env_name} is not set (the signing key is never passed on the command line)")
    try:
        key = ds.load_private_key_pem(pem.encode("utf-8"))
    except Exception:  # noqa: BLE001 -- never surface key material
        raise AuthorError("AO007", f"{env_name} is not a valid Ed25519 private key PEM")
    fp = ds.public_key_fingerprint(key.public_key())
    if fp != signer.spki_sha256:
        raise AuthorError("AO007", f"signing key SPKI {fp[:12]}... is a valid Ed25519 key but the wrong signer (pinned {signer.key_id!r})")
    return key


def build_and_check_sidecar(message, private_key, signer):
    """Sign, then verify IN MEMORY against the pinned public key BEFORE anything is written
    (spec 3.5, AO012). Returns the exact sidecar bytes to publish."""
    sidecar_bytes = _canon(ds.build_sig_sidecar(message, private_key))
    ok, reason = ds.verify_sidecar_bytes_with_key(message, sidecar_bytes, signer.public_key)
    if not ok:
        raise AuthorError("AO012", f"in-memory sidecar verification failed: {reason}")
    return sidecar_bytes


def _write_bytes_atomic_noclobber(path, data):
    """D3 replica of collect_disposition._write_bytes_atomic's NO-CLOBBER branch, verbatim
    semantics: temp sibling + flush + fsync, os.link (atomic create-if-absent; FileExistsError if
    present -- no check-then-act race), finally-unlink of the temp. Never os.rename/os.replace."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = os.path.join(directory, f".{os.path.basename(path)}.tmp-{os.getpid()}")
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def publish_set(entries):
    """Ordered no-clobber publish (spec 3.5): source record first (when present), then sidecar,
    then overlay -- a partial failure can never leave an overlay without its signature."""
    for path, data in entries:
        try:
            _write_bytes_atomic_noclobber(path, data)
        except FileExistsError:
            raise AuthorError("AO008", f"refusing to overwrite existing {path} (no-clobber)")
        except OSError as exc:
            raise AuthorError("AO008", f"publish failed for {path} ({type(exc).__name__})")


def canonical_names(dimension, census_sha256, captured_dt, out_dir, source_ext):
    """Spec 3.6 naming: overlay-<dim-slug>-<census12>-<UTC>[-NN].json (+ .json.sig), source record
    under source/ with .source.<ext>. The stamp derives from the SAME captured_dt written into the
    doc (single clock). First candidate has no suffix; -01..-99 on collision; AO008 when exhausted."""
    slug = dimension.replace(".", "_")
    stamp = captured_dt.strftime("%Y%m%dT%H%M%SZ")
    for n in range(100):
        suffix = "" if n == 0 else f"-{n:02d}"
        base = f"overlay-{slug}-{census_sha256[:12]}-{stamp}{suffix}"
        overlay = os.path.join(out_dir, base + ".json")
        sig = overlay + ".sig"
        source = os.path.join(out_dir, "source", base + ".source" + source_ext) if source_ext is not None else None
        candidates = [p for p in (overlay, sig, source) if p]
        if not any(os.path.exists(p) for p in candidates):
            locator = ("evidence/source/" + os.path.basename(source)) if source else None
            return {"overlay": overlay, "sig": sig, "source": source, "locator": locator,
                    "stamp": stamp + suffix}
    raise AuthorError("AO008", "no free canonical name (suffixes -01..-99 exhausted for this census+dimension+second)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Author + sign ONE per-dimension evidence overlay bound to a signed census.")
    ap.add_argument("--census", required=True)
    ap.add_argument("--census-sig", required=True, dest="census_sig")
    ap.add_argument("--key-id", required=True, dest="key_id")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir")
    ap.add_argument("--input", required=True, help="operator-semantics overlay core JSON (spec 3.1)")
    ap.add_argument("--source-file", default=None, dest="source_file")
    ap.add_argument("--source-hash-na-reason", default=None, dest="source_hash_na_reason")
    ap.add_argument("--source-custody-locator", default=None, dest="source_custody_locator")
    ap.add_argument("--producing-repo-sha-na-reason", default=None, dest="producing_na_reason")
    ap.add_argument("--expect-gate-repo-sha", required=True, dest="expect_gate_repo_sha",
                    help="REQUIRED (D4): the author's clean merged-main HEAD; asserted before any read.")
    ap.add_argument("--expect-project-ref", required=True, dest="expect_project_ref")
    ap.add_argument("--expect-database", required=True, dest="expect_database")
    ap.add_argument("--expect-schemas", required=True, dest="expect_schemas")
    ap.add_argument("--expect-census-repo-sha", required=True, dest="expect_census_repo_sha")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role", dest="require_role_markers")
    ap.add_argument("--expect-query-bundle-sha256", required=True, dest="expect_query_bundle_sha256")
    ap.add_argument("--out-dir", default=os.path.join(SP_DIR, "evidence"), dest="out_dir")
    ap.add_argument("--signing-key-env", default="DISPOSITION_SIGNING_KEY", dest="signing_key_env")
    args = ap.parse_args(argv)

    try:
        # 1. Provenance gate FIRST (D4): before the signing key or ANY evidence input is read.
        head = dp.git_head_sha(SP_DIR)
        if not head or not dp.git_worktree_clean(SP_DIR):
            raise AuthorError("AO010", "author checkout is DIRTY or HEAD undeterminable -- run from a clean merged-main checkout")
        if head != args.expect_gate_repo_sha:
            raise AuthorError("AO010", f"git HEAD {head[:12]} != --expect-gate-repo-sha {args.expect_gate_repo_sha[:12]}")
        # 2. Pinned signer.
        signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
        if signer is None:
            raise AuthorError("AO013", kreason)
        # 3. Census bytes read ONCE + FULL acceptance.
        try:
            with open(args.census, "rb") as fh:
                census_bytes = fh.read()
            with open(args.census_sig, "rb") as fh:
                census_sig_bytes = fh.read()
        except OSError as exc:
            raise AuthorError("AO000", f"cannot read census/sig ({type(exc).__name__})")
        expects = {"project_ref": args.expect_project_ref, "database": args.expect_database,
                   "schemas": [s.strip() for s in args.expect_schemas.split(",") if s.strip()],
                   "census_repo_sha": args.expect_census_repo_sha,
                   "role_markers": [s.strip() for s in args.require_role_markers.split(",") if s.strip()],
                   "query_bundle_sha256": args.expect_query_bundle_sha256}
        census = accept_census(census_bytes, census_sig_bytes, signer=signer, expects=expects)
        # 4. Operator semantics + source + producing category.
        core = load_input_core(args.input)
        source_bytes, source_reason, custody, source_ext = read_source(
            args.source_file, args.source_hash_na_reason, args.source_custody_locator)
        producing = compute_producing(core["dimension"], head, args.producing_na_reason)
        # 5. Contract + ONE clock read + canonical names.
        try:
            contract = dov.load_overlay_contract()
        except dov.OverlayRegistryError as exc:
            raise AuthorError("AO000", f"cannot build overlay contract ({type(exc).__name__})")
        captured_dt = datetime.now(timezone.utc).replace(microsecond=0)
        census_sha = hashlib.sha256(census_bytes).hexdigest()
        names = canonical_names(core["dimension"], census_sha, captured_dt, args.out_dir, source_ext)
        source_hash = hashlib.sha256(source_bytes).hexdigest() if source_bytes is not None else None
        source_locator = names["locator"] if source_bytes is not None else custody
        # 6. Assemble -> validate the EXACT signed bytes.
        doc = assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                               producing=producing, source_hash=source_hash,
                               source_hash_reason=source_reason, source_locator=source_locator,
                               captured_at_iso=captured_dt.isoformat())
        message = _canon(doc)
        diags = validate_assembled(message, census=census, census_bytes_sha=census_sha,
                                   contract=contract, expect_project_ref=args.expect_project_ref,
                                   now=captured_dt)
        if diags:
            for code, locus, msg in diags:
                print(f"{code} {locus}: {msg}", file=sys.stderr)
            raise AuthorError("AO005", f"assembled overlay failed {len(diags)} consumer check(s) -- refusing to sign")
        # 7. Signer parity + in-memory-verified sidecar; 8. ordered no-clobber publish.
        private_key = load_signing_key(args.signing_key_env, signer)
        sidecar_bytes = build_and_check_sidecar(message, private_key, signer)
        entries = ([(names["source"], source_bytes)] if source_bytes is not None else [])
        entries += [(names["sig"], sidecar_bytes), (names["overlay"], message)]
        publish_set(entries)
    except AuthorError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"=== OVERLAY AUTHORED: {core['dimension']} n={len(core['assignments'])} -> {names['overlay']} "
          f"(census {census_sha[:12]}, signer {signer.key_id}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
