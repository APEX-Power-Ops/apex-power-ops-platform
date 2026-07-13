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
