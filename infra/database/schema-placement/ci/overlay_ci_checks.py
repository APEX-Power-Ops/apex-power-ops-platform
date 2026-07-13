"""Repo-level checks for the overlay-evidence CI gate (spec 4.2). Pure functions first (unit-
tested with plain data); the git-facing driver (main) is Task 8. Every violation is a stable
'FAIL: ...' string; the gate prints them and exits non-zero."""
from __future__ import annotations

import hashlib
import json
import os
import posixpath

SOURCE_PREFIX = "evidence/source/"


def normalize_locator(locator):
    """Locator constraints (spec 4.2 step 4; round-2b CI2b-2): reject absolute paths, '..'
    components, backslashes, and anything not strictly under evidence/source/. Returns
    (ok, normalized_or_reason)."""
    if not isinstance(locator, str) or not locator:
        return False, "locator is not a non-empty string"
    if "\\" in locator:
        return False, "locator contains a backslash"
    if posixpath.isabs(locator):
        return False, "locator is an absolute path"
    norm = posixpath.normpath(locator)
    if norm.startswith("..") or "/../" in norm:
        return False, "locator escapes via '..'"
    if not norm.startswith(SOURCE_PREFIX) or norm == SOURCE_PREFIX.rstrip("/"):
        return False, f"locator is not under {SOURCE_PREFIX}"
    return True, norm


def orphan_check(overlay_docs, source_paths):
    """RIDER (operator round-2c, strong form): every committed regular blob under
    evidence/source/ must be referenced by EXACTLY ONE committed overlay's source_locator
    (non-null source_hash docs only). Runs UNCONDITIONALLY -- a source-only PR fails here.
    Also FAILs a non-null-hash overlay whose (valid) locator names a missing source record."""
    refs = {}
    fails = []
    for path, doc in overlay_docs:
        if doc.get("source_hash") is None:
            continue  # NA-case: locator is an out-of-band custody ref, not a repo path
        ok, norm = normalize_locator(doc.get("source_locator"))
        if not ok:
            fails.append(f"FAIL: {path}: source_locator invalid ({norm})")
            continue
        refs.setdefault(norm, []).append(path)
    for src in sorted(source_paths):
        n = len(refs.get(src, []))
        if n == 0:
            fails.append(f"FAIL: {src}: orphan source record (referenced by no committed overlay)")
        elif n > 1:
            fails.append(f"FAIL: {src}: source record referenced by {n} overlays ({', '.join(sorted(refs[src]))})")
    for locator, owners in sorted(refs.items()):
        if locator not in set(source_paths):
            fails.append(f"FAIL: {owners[0]}: source_locator {locator} is missing from the committed source records")
    return fails


def source_rehash(doc, sp_dir, protected_sources):
    """Rehash the committed source record behind a non-null source_hash (spec 4.2 step 4):
    locator normalizes, is a COMMITTED REGULAR blob (member of protected_sources -- symlinks/
    gitlinks/uncommitted files are excluded upstream), and its bytes hash to source_hash."""
    if doc.get("source_hash") is None:
        return []
    ok, norm = normalize_locator(doc.get("source_locator"))
    if not ok:
        return [f"FAIL: source_locator invalid ({norm})"]
    if norm not in protected_sources:
        return [f"FAIL: {norm}: not a committed regular source record under {SOURCE_PREFIX}"]
    try:
        with open(os.path.join(sp_dir, norm.replace("/", os.sep)), "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
    except OSError as exc:
        return [f"FAIL: {norm}: cannot read source record ({type(exc).__name__})"]
    if got != doc.get("source_hash"):
        return [f"FAIL: {norm}: rehash {got[:12]}... != overlay source_hash {str(doc.get('source_hash'))[:12]}..."]
    return []


import re
import subprocess
import sys

SP = "infra/database/schema-placement"
PINNED = {"project_ref": "fxoyniqnrlkxfligbxmg", "database": "postgres", "schemas": "public",
          "role_markers": "anon,authenticated,service_role", "key_id": "prod-disposition-ed25519-2026-07"}
TOOLING = [f"{SP}/{n}" for n in (
    "author_overlay.py", "verify_overlay_artifact.py", "disposition_overlay.py", "verify_census.py",
    "collect_disposition.py", "disposition_signing.py", "disposition_trust.py",
    "disposition_provenance.py", "overlay.schema.json", "disposition.schema.json", "keys")]
_CANONICAL_OVERLAY = re.compile(r"^evidence/overlay-[^/]+\.json$")


def _reject_dup(pairs):
    """D3 replica target: author_overlay.py's load_input_core keeps a byte-parallel copy of this
    function (as _reject_dup_keys) for its own --input strict-parse (Phase-4.1 item 2)."""
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def _reject_nonfinite(const):
    """D3 replica target: author_overlay.py's _reject_nonfinite_const."""
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def strict_parse(data: bytes):
    """D3 replica target: author_overlay.py's _strict_parse_input. Kept byte-parallel per D3
    precedent -- edit both copies together if this contract changes."""
    return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_dup, parse_constant=_reject_nonfinite)


_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]+):(.+)$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
# Phase-4.2 operator policy: the ONLY approved out-of-band custody schemes. Additions require a
# governed tooling change (a reviewed source change to this constant, in BOTH D3 replicas).
APPROVED_CUSTODY_SCHEMES = frozenset({"vault", "infisical"})


def is_custody_uri(value):
    """D3 replica of author_overlay.py's is_custody_uri -- kept byte-parallel (Phase-4.1 item 4
    + cross-engine follow-up + Phase-4.2 scheme pin). Custody-locator URI rule: must be
    '<scheme>:<opaque-reference>' -- scheme matches [A-Za-z][A-Za-z0-9+.-]+ (TWO+ characters:
    single-letter schemes are rejected wholesale, closing the drive-RELATIVE Windows path gap,
    e.g. 'C:evidence-out.log'), followed by ':' and a non-empty opaque part, AND the scheme --
    case-normalized via .lower() FIRST (operator policy: mixed-case approved schemes are
    accepted) -- must be a member of APPROVED_CUSTODY_SCHEMES. Rejects absolute paths (leading
    '/' or a Windows drive letter -- the explicit drive regex stays as defense in depth),
    relative filesystem paths (no scheme/colon), '..' traversal, backslashes, and any
    whitespace. Returns (ok, reason_or_value)."""
    if not isinstance(value, str) or not value:
        return False, "custody locator is not a non-empty string"
    if any(ch.isspace() for ch in value):
        return False, "custody locator contains whitespace"
    if "\\" in value:
        return False, "custody locator contains a backslash"
    if ".." in value:
        return False, "custody locator contains '..'"
    if value.startswith("/"):
        return False, "custody locator is an absolute path"
    if _WINDOWS_DRIVE_RE.match(value):
        return False, "custody locator is a Windows drive path"
    m = _SCHEME_RE.match(value)
    if not m:
        return False, "custody locator is not URI-like (expected <scheme>:<opaque-reference>, scheme >= 2 chars)"
    if m.group(1).lower() not in APPROVED_CUSTODY_SCHEMES:
        return False, (f"custody scheme {m.group(1).lower()!r} not in APPROVED_CUSTODY_SCHEMES "
                       f"({', '.join(sorted(APPROVED_CUSTODY_SCHEMES))})")
    return True, value


def custody_locator_check(overlay_docs):
    """Focused check (Phase-4.1 item 4): every committed overlay with a null source_hash (the
    NA/custody path) must carry a source_locator that is URI-like (is_custody_uri). Runs
    UNCONDITIONALLY over every committed overlay doc -- unlike orphan_check, which only inspects
    non-null-hash docs, this is the mirror image and only inspects null-hash docs."""
    fails = []
    for path, doc in overlay_docs:
        if doc.get("source_hash") is not None:
            continue
        ok, reason = is_custody_uri(doc.get("source_locator"))
        if not ok:
            fails.append(f"FAIL: {path}: {reason}")
    return fails


def kind_sniff(files):
    """Content-sniff EVERY committed file under evidence/ regardless of extension or case
    (round-2b CI2b-3): a parsed object with kind=evidence_overlay off the canonical path FAILs."""
    fails = []
    for path, data in files:
        try:
            doc = strict_parse(data)
        except (ValueError, UnicodeDecodeError):
            continue  # not JSON -> opaque (source records, docs)
        if isinstance(doc, dict) and doc.get("kind") == "evidence_overlay" and not _CANONICAL_OVERLAY.match(path):
            fails.append(f"FAIL: {path}: evidence_overlay document outside the canonical evidence/overlay-*.json path")
    return fails


def census_uniqueness(census_files):
    """Round-2b CI2b-4: two byte-identical committed censuses would make every bound overlay
    permanently ambiguous under the exactly-one rule while immutability forbids deletion."""
    by_hash = {}
    fails = []
    for path, data in census_files:
        by_hash.setdefault(hashlib.sha256(data).hexdigest(), []).append(path)
    for h, paths in sorted(by_hash.items()):
        if len(paths) > 1:
            fails.append(f"FAIL: byte-identical committed censuses share sha256 {h[:12]}...: {', '.join(sorted(paths))}")
    return fails


def sig_pairing(overlay_paths, sig_paths):
    overlays, sigs = set(overlay_paths), set(sig_paths)
    fails = []
    for o in sorted(overlays):
        if o + ".sig" not in sigs:
            fails.append(f"FAIL: {o}: missing sidecar {o}.sig")
    for s in sorted(sigs):
        if s[: -len(".sig")] not in overlays:
            fails.append(f"FAIL: {s}: orphan sidecar (no overlay)")
    return fails


def match_census(base_hash, census_files):
    matches = [p for p, data in census_files if hashlib.sha256(data).hexdigest() == base_hash]
    if not matches:
        return None, f"FAIL: no committed census matches base_snapshot_sha256 {str(base_hash)[:12]}..."
    if len(matches) > 1:
        return None, f"FAIL: ambiguous base_snapshot_sha256 {str(base_hash)[:12]}... matches {len(matches)} censuses"
    return matches[0], None


def committed_set_ov007(overlay_docs):
    """check_conflict parity over the WHOLE committed set (round-1 op#4/Codex P2): per bound
    census, the FLAT (dimension, object_id) list over every assignment of every overlay --
    intra-overlay repeats included -- must be duplicate-free."""
    groups = {}
    for path, doc in overlay_docs:
        groups.setdefault(doc.get("base_snapshot_sha256"), []).append((path, doc))
    fails = []
    for base, docs in sorted(groups.items(), key=lambda x: str(x[0])):
        counts = {}
        for path, doc in docs:
            for a in doc.get("assignments", []):
                key = (doc.get("dimension"), a.get("object_id"))
                counts.setdefault(key, []).append(path)
        for (dim, oid), owners in sorted(counts.items(), key=lambda x: (str(x[0][0]), str(x[0][1]))):
            if len(owners) > 1:
                fails.append(f"FAIL: OV007 census {str(base)[:12]}...: ({dim}, {oid}) assigned "
                             f"{len(owners)} times across {', '.join(sorted(set(owners)))}")
    return fails


# ---- git-facing driver (exercised end-to-end by the Task-9 scratch-repo suite) ----
def _git(args, **kw):
    return subprocess.run(["git"] + args, capture_output=True, text=True, **kw)


def _ls(pathspec):
    out = _git(["ls-files", "--", pathspec]).stdout
    return [line for line in out.splitlines() if line]


def _read_repo_file(path):
    with open(path.replace("/", os.sep), "rb") as fh:
        return fh.read()


def _sp_rel(path):
    return path[len(SP) + 1:] if path.startswith(SP + "/") else path


def _collect_overlay_docs(overlay_paths, evidence_files):
    """Parse every committed overlay path into (path, doc) for the driver's downstream checks.
    A document that strict-parses but is NOT a JSON object (bare list/string/number/etc.) is a
    FAIL -- neither a crash nor silent acceptance into overlay_docs (operator Phase-4 GO fold:
    isinstance(doc, dict) guard before the doc is appended)."""
    by_path = dict(evidence_files)
    docs = []
    fails = []
    for p in overlay_paths:
        data = by_path[p]
        try:
            doc = strict_parse(data)
        except ValueError as exc:
            fails.append(f"FAIL: {p}: overlay does not strict-parse ({exc})")
            continue
        if not isinstance(doc, dict):
            fails.append(f"FAIL: {p}: overlay document is not a JSON object (got {type(doc).__name__})")
            continue
        docs.append((p, doc))
    return docs, fails


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    args = ap.parse_args(argv)
    fails = []

    top = _git(["rev-parse", "--show-toplevel"]).stdout.strip()
    os.chdir(top)

    evidence_files = [(_sp_rel(p), _read_repo_file(p)) for p in _ls(f"{SP}/evidence")]
    census_files = [(p, b) for p, b in evidence_files if _CANONICAL_OVERLAY.match(p) is None
                    and re.match(r"^evidence/census-prod-[^/]+\.json$", p)]
    overlay_paths = [p for p, _ in evidence_files if _CANONICAL_OVERLAY.match(p)]
    sig_paths = [p for p, _ in evidence_files if p.endswith(".sig") and p.startswith("evidence/overlay-")]
    # committed REGULAR blobs under evidence/source/ (the shell mode-check has already failed
    # 120000/160000 anywhere under evidence/, so ls-files membership here == regular blob)
    source_paths = [_sp_rel(p) for p in _ls(f"{SP}/evidence/source")]

    overlay_docs, parse_fails = _collect_overlay_docs(overlay_paths, evidence_files)
    fails += parse_fails

    # UNCONDITIONAL repo-level checks (before the added-set early exit; rider + spec 4.2 steps 1-2)
    fails += kind_sniff(evidence_files)
    fails += census_uniqueness(census_files)
    fails += sig_pairing(overlay_paths, sig_paths)
    fails += orphan_check(overlay_docs, source_paths)
    fails += custody_locator_check(overlay_docs)

    added = [line for line in _git(["diff", "--no-renames", "--diff-filter=A", "--name-only",
                                    args.base, "HEAD", "--",
                                    f":(glob){SP}/evidence/overlay-*.json"]).stdout.splitlines() if line]
    if not added:
        print("no overlays added -- unconditional repo-level checks complete")
    else:
        sys.path.insert(0, SP)
        import collect_disposition as cds  # noqa: PLC0415 -- HEAD-computed reviewed bundle
        qb = cds.query_bundle_sha256()
        for rel in [p[len(SP) + 1:] for p in added]:
            doc = dict(overlay_docs).get(rel)
            if doc is None:
                continue  # strict-parse already failed it
            census_path, fail = match_census(doc.get("base_snapshot_sha256"), census_files)
            if fail:
                fails.append(f"{fail} (overlay {rel})")
                continue
            census_repo_sha = strict_parse(dict(census_files)[census_path]).get("repo_sha", "")
            # census-binding mirror (round-2 OCA-1): never self-referential
            if _git(["merge-base", "--is-ancestor", census_repo_sha, "HEAD"]).returncode != 0:
                fails.append(f"FAIL: {rel}: census repo_sha {census_repo_sha[:12]} is not an ancestor of HEAD")
                continue
            if _git(["diff", "--quiet", census_repo_sha, "HEAD", "--"] + TOOLING).returncode != 0:
                fails.append(f"FAIL: {rel}: TOOLING changed since census repo_sha {census_repo_sha[:12]}")
                continue
            fails += [f"{f} (overlay {rel})" for f in source_rehash(doc, SP, set(source_paths))]
            prs = doc.get("producing_repo_sha")
            prs = "" if prs is None else str(prs)   # null-safe (round-2 CI-F2)
            if prs:
                if _git(["merge-base", "--is-ancestor", prs, "HEAD"]).returncode != 0:
                    fails.append(f"FAIL: {rel}: producing_repo_sha {prs[:12]} is not an ancestor of HEAD")
                if _git(["diff", "--quiet", prs, "HEAD", "--"] + TOOLING).returncode != 0:
                    fails.append(f"FAIL: {rel}: TOOLING changed since producing_repo_sha {prs[:12]}")
            r = subprocess.run(
                ["uv", "run", "--project", SP, "--locked", "python", f"{SP}/verify_overlay_artifact.py",
                 "--overlay", f"{SP}/{rel}", "--overlay-sig", f"{SP}/{rel}.sig",
                 "--census", f"{SP}/{census_path}", "--census-sig", f"{SP}/{census_path}.sig",
                 "--key-id", PINNED["key_id"],
                 "--expect-project-ref", PINNED["project_ref"], "--expect-database", PINNED["database"],
                 "--expect-schemas", PINNED["schemas"], "--expect-census-repo-sha", census_repo_sha,
                 "--require-role-markers", PINNED["role_markers"], "--expect-query-bundle-sha256", qb],
                capture_output=True, text=True)
            print(r.stdout, end="")
            if r.returncode != 0:
                fails.append(f"FAIL: {rel}: verify_overlay_artifact rejected (rc={r.returncode})")
        fails += committed_set_ov007(overlay_docs)

    for f in fails:
        print(f)
    if fails:
        print(f"=== OVERLAY EVIDENCE: {len(fails)} FAILURE(S) ===")
        return 1
    print("=== ALL COMMITTED OVERLAY ARTIFACTS VERIFIED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
