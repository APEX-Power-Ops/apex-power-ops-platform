"""Reviewed source-constant trust anchor + signer resolution for disposition evidence (SP026).

The single trust ROOT: TRUSTED_SIGNERS maps an authorized signer id to the SHA-256 of its Ed25519
SubjectPublicKeyInfo DER. keys/<key-id>.pub.pem provides only public key MATERIAL, accepted only if its
SPKI fingerprint equals the pinned value. Both verify_census (census acceptance) and check_disposition
(preapply) resolve keys THROUGH this one anchor. disposition_signing is crypto MECHANISM; this is trust
POLICY. The map is immutable from the production API (no caller-supplied trust map); tests monkeypatch
the module constant."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass

import disposition_signing as ds

DEFAULT_KEYS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys")

# Repo-owned trust anchor (SOURCE CONSTANT): authorized signer id -> SHA-256 of its Ed25519 SPKI DER.
# keys/<key-id>.pub.pem is accepted only if its SPKI fingerprint equals the value pinned here (H1).
TRUSTED_SIGNERS = {
    "prod-disposition-ed25519-2026-07": "c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca",
}

# A signer id is a bare identifier — no path separators, no '..', no leading dot (F3).
_KEY_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@dataclass(frozen=True)
class ResolvedSigner:
    key_id: str
    public_key: object
    spki_sha256: str
    pubkey_path: str
    pem_sha256: str


def resolve_pinned_key(keys_dir, key_id):
    """Resolve an authorized signer id to a ResolvedSigner, anchored by the reviewed SOURCE CONSTANT
    TRUSTED_SIGNERS (the module constant — NOT a caller-supplied trust map). Fail-closed at each step,
    returning (None, reason):
      1. key_id must be a known signer in TRUSTED_SIGNERS;
      2. key_id must be a bare identifier, and the resolved key path must stay within keys_dir (F3);
      3. load keys_dir/<key_id>.pub.pem as public key MATERIAL and capture its exact PEM bytes;
      4. require its SPKI SHA-256 to equal the pinned constant (H1).
    Returns the loaded key OBJECT (not a path), so the caller verifies against the exact key it
    fingerprint-checked, with no re-open (H3)."""
    expected_fp = TRUSTED_SIGNERS.get(key_id)
    if expected_fp is None:
        return None, f"key-id {key_id!r} is not an authorized signer (not in the reviewed TRUSTED_SIGNERS anchor)"
    if not _KEY_ID_RE.match(key_id):
        return None, f"key-id {key_id!r} is not a bare identifier (path separators / '..' are rejected)"
    try:
        keys_dir = os.path.realpath(keys_dir)
        pub_path = os.path.realpath(os.path.join(keys_dir, f"{key_id}.pub.pem"))
        contained = os.path.commonpath([keys_dir, pub_path]) == keys_dir
    except (ValueError, OSError) as exc:
        return None, f"cannot resolve key path for key-id {key_id!r} ({type(exc).__name__})"
    if not contained:
        return None, f"resolved key path escapes the keys directory {keys_dir}"
    try:
        with open(pub_path, "rb") as fh:
            pem_bytes = fh.read()
        public_key = ds.load_public_key_pem(pem_bytes)
    except Exception as exc:  # noqa: BLE001 -- any load failure => cannot establish the anchor
        return None, f"cannot load key-id public key {pub_path} ({type(exc).__name__})"
    computed_fp = ds.public_key_fingerprint(public_key)
    if computed_fp != expected_fp.strip().lower():
        return None, f"public key SPKI sha256 {computed_fp} != pinned fingerprint for key-id {key_id!r}"
    return ResolvedSigner(key_id=key_id, public_key=public_key, spki_sha256=computed_fp,
                          pubkey_path=pub_path, pem_sha256=hashlib.sha256(pem_bytes).hexdigest()), ""
