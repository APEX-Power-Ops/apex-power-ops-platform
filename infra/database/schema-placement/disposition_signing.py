"""Ed25519 detached-signature helpers for disposition evidence snapshots (correction tranche, F1).

The dominant residual the audits surfaced: the offline checker trusts a self-attested, UNSIGNED
snapshot — guard_passed / project_ref / target_identity / consumer_evidence are plain writable
JSON, so a hand-authored snapshot validates and could carry a destructive decision GREEN. This
module binds a snapshot to a genuine census run: the collector SIGNS the exact snapshot bytes with
a private key injected via env (value-silent, Infisical-held); the checker VERIFIES the detached
signature against a committed public key BEFORE it trusts the snapshot.

Because the signature covers the WHOLE snapshot document, it binds every field inside it —
project_ref, query_bundle_sha256, collector_version, repo_sha (collector commit), target_identity,
and observed_at — with no separate binding needed.

cryptography is imported LAZILY inside each function so `import disposition_signing` stays cheap and
the collector's offline core keeps its no-heavy-deps-on-import property.

Signature sidecar (JSON) format — a detached signature over the RAW snapshot file bytes:
    {"algo": "ed25519",
     "signature": "<hex, 64-byte raw Ed25519 signature>",
     "signed_sha256": "<hex sha256 of the exact snapshot bytes; redundant convenience>",
     "public_key_sha256": "<hex sha256 of the signer's SubjectPublicKeyInfo DER; key fingerprint>"}
"""

from __future__ import annotations

import hashlib
import json


def _ed25519():
    from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: PLC0415
    return ed25519


def load_private_key_pem(pem_bytes):
    """Load an unencrypted PKCS8 PEM Ed25519 private key. Raises on any other key type/format."""
    from cryptography.hazmat.primitives import serialization  # noqa: PLC0415
    key = serialization.load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, _ed25519().Ed25519PrivateKey):
        raise ValueError("not an Ed25519 private key")
    return key


def load_public_key_pem(pem_bytes):
    """Load a SubjectPublicKeyInfo PEM Ed25519 public key. Raises on any other key type/format."""
    from cryptography.hazmat.primitives import serialization  # noqa: PLC0415
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, _ed25519().Ed25519PublicKey):
        raise ValueError("not an Ed25519 public key")
    return key


def public_key_fingerprint(public_key) -> str:
    from cryptography.hazmat.primitives import serialization  # noqa: PLC0415
    der = public_key.public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(der).hexdigest()


def sign_message(message: bytes, private_key) -> bytes:
    return private_key.sign(message)  # Ed25519 -> raw 64-byte signature


def verify_message(message: bytes, signature: bytes, public_key) -> bool:
    """Fail-closed: ANY exception (InvalidSignature, malformed inputs) => False."""
    try:
        public_key.verify(signature, message)
        return True
    except Exception:  # noqa: BLE001 -- a verifier must treat every failure as "does not verify"
        return False


def build_sig_sidecar(message: bytes, private_key) -> dict:
    return {
        "algo": "ed25519",
        "signature": sign_message(message, private_key).hex(),
        "signed_sha256": hashlib.sha256(message).hexdigest(),
        "public_key_sha256": public_key_fingerprint(private_key.public_key()),
    }


def verify_sidecar(message: bytes, sidecar, public_key) -> tuple[bool, str]:
    """Verify a sidecar against message bytes and a public key. Cross-checks the declared digest and
    key fingerprint before the cryptographic verify, so a mismatched key or tampered payload is
    named precisely. Returns (ok, reason); reason is '' on success."""
    if not isinstance(sidecar, dict) or sidecar.get("algo") != "ed25519":
        return False, "signature sidecar is missing or not an ed25519 sidecar"
    try:
        signature = bytes.fromhex(sidecar.get("signature") or "")
    except (ValueError, TypeError):
        return False, "signature is not valid hex"
    declared = sidecar.get("signed_sha256")
    if declared is not None and declared != hashlib.sha256(message).hexdigest():
        return False, "signed_sha256 does not match the snapshot bytes (payload tampered)"
    fp = sidecar.get("public_key_sha256")
    if fp is not None and fp != public_key_fingerprint(public_key):
        return False, "public_key_sha256 does not match the supplied verify key (signed by a different key)"
    if not verify_message(message, signature, public_key):
        return False, "Ed25519 signature does not verify against the supplied verify key"
    return True, ""


def verify_detached(message: bytes, sig_path, pubkey_path) -> tuple[bool, str]:
    """Verify a detached signature over message bytes the caller ALREADY HAS IN HAND. Reads only the
    sidecar and the public key from disk — never the message — so the bytes verified are EXACTLY the
    bytes the caller parses/trusts, closing the verify-then-reparse TOCTOU (Codex P1). Fail-closed on
    any read/parse/verify error."""
    try:
        with open(sig_path, "rb") as fh:
            sidecar = json.loads(fh.read())
    except (OSError, ValueError) as exc:
        return False, f"cannot read/parse signature sidecar ({type(exc).__name__})"
    try:
        with open(pubkey_path, "rb") as fh:
            public_key = load_public_key_pem(fh.read())
    except Exception as exc:  # noqa: BLE001 -- any key-load failure => cannot verify => fail closed
        return False, f"cannot load verify key ({type(exc).__name__})"
    return verify_sidecar(message, sidecar, public_key)


def verify_sidecar_bytes_with_key(message: bytes, sidecar_bytes: bytes, public_key) -> tuple[bool, str]:
    """Verify a detached signature from sidecar bytes the caller ALREADY HAS IN HAND, against a public
    key OBJECT the caller already loaded and pinned. Parses the sidecar bytes (fail-closed) and
    delegates to verify_sidecar. Reads NOTHING from disk — the bytes verified are exactly the bytes the
    caller hashes into its receipt (SP026)."""
    try:
        sidecar = json.loads(sidecar_bytes)
    except ValueError as exc:
        return False, f"cannot parse signature sidecar bytes ({type(exc).__name__})"
    return verify_sidecar(message, sidecar, public_key)


def verify_detached_with_key(message: bytes, sig_path, public_key) -> tuple[bool, str]:
    """Path-based convenience wrapper: read the sidecar bytes once, then verify_sidecar_bytes_with_key.
    Verifies against a public key OBJECT the caller already loaded and pinned; reads ONLY the sidecar
    (never the key), so the fingerprint-checked key IS the verify key (closes the resolve->re-open
    TOCTOU, H3). Fail-closed on any read/parse/verify error."""
    try:
        with open(sig_path, "rb") as fh:
            sidecar_bytes = fh.read()
    except OSError as exc:
        return False, f"cannot read signature sidecar ({type(exc).__name__})"
    return verify_sidecar_bytes_with_key(message, sidecar_bytes, public_key)


def verify_snapshot_files(snapshot_path, sig_path, pubkey_path) -> tuple[bool, str]:
    """Convenience wrapper: read the snapshot bytes from disk, then verify_detached. Used by tests and
    any caller that has only the path. The checker's main gate uses verify_detached directly on the
    bytes it already read, so it never reads the snapshot twice."""
    try:
        with open(snapshot_path, "rb") as fh:
            message = fh.read()
    except OSError as exc:
        return False, f"cannot read snapshot ({type(exc).__name__})"
    return verify_detached(message, sig_path, pubkey_path)
