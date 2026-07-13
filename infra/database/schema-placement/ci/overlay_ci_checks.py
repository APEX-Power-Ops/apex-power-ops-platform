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
