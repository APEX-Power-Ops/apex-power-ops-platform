"""Offline tests for disposition_trust.py (source-constant anchor + signer resolution)."""

import contextlib
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disposition_signing as ds  # noqa: E402
import disposition_trust as dt  # noqa: E402

KEY_ID = "test-ed25519"
PROD_KEY_ID = "prod-disposition-ed25519-2026-07"


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub_pem


@contextlib.contextmanager
def _trusted(key_id, fingerprint):
    prev = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        dt.TRUSTED_SIGNERS.clear()
        dt.TRUSTED_SIGNERS.update(prev)


def _fp(pub_pem):
    return ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))


def _write_key(d, pub_pem, key_id=KEY_ID):
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, key_id + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    return keys_dir


def test_resolve_returns_structured_signer():
    _priv, pub_pem = _keypair()
    with tempfile.TemporaryDirectory() as d:
        keys_dir = _write_key(d, pub_pem)
        with _trusted(KEY_ID, _fp(pub_pem)):
            signer, reason = dt.resolve_pinned_key(keys_dir, KEY_ID)
    assert signer is not None and reason == ""
    assert signer.key_id == KEY_ID
    assert signer.spki_sha256 == _fp(pub_pem)
    assert signer.pem_sha256 == hashlib.sha256(pub_pem).hexdigest()
    assert signer.public_key is not None and os.path.isabs(signer.pubkey_path)


def test_unknown_signer_blocks():
    with tempfile.TemporaryDirectory() as d:
        signer, reason = dt.resolve_pinned_key(os.path.join(d, "keys"), "nope")
    assert signer is None and "authorized signer" in reason


def test_forged_key_under_prod_id_blocks():
    _priv, forged_pem = _keypair()
    with tempfile.TemporaryDirectory() as d:
        keys_dir = _write_key(d, forged_pem, key_id=PROD_KEY_ID)
        signer, reason = dt.resolve_pinned_key(keys_dir, PROD_KEY_ID)  # real anchor, no monkeypatch
    assert signer is None and "pinned fingerprint" in reason


def test_self_consistent_forged_keys_dir_blocks():
    _priv, forged_pem = _keypair()
    with tempfile.TemporaryDirectory() as d:
        keys_dir = _write_key(d, forged_pem, key_id=PROD_KEY_ID)
        with open(os.path.join(keys_dir, PROD_KEY_ID + ".spki-sha256"), "w", encoding="utf-8") as fh:
            fh.write(_fp(forged_pem) + "\n")
        signer, reason = dt.resolve_pinned_key(keys_dir, PROD_KEY_ID)
    assert signer is None and "pinned fingerprint" in reason


def test_key_id_traversal_blocks_even_when_trusted():
    _priv, pub_pem = _keypair()
    with tempfile.TemporaryDirectory() as d:
        keys_dir = os.path.join(d, "keys")
        os.makedirs(keys_dir)
        with open(os.path.join(d, "evil.pub.pem"), "wb") as fh:
            fh.write(pub_pem)
        with _trusted("../evil", _fp(pub_pem)):
            signer, reason = dt.resolve_pinned_key(keys_dir, "../evil")
    assert signer is None and "bare identifier" in reason


def test_pinned_key_object_survives_file_swap():
    priv, pub_pem = _keypair()
    with tempfile.TemporaryDirectory() as d:
        keys_dir = _write_key(d, pub_pem)
        with _trusted(KEY_ID, _fp(pub_pem)):
            signer, _ = dt.resolve_pinned_key(keys_dir, KEY_ID)
        _p2, pub2 = _keypair()
        with open(os.path.join(keys_dir, KEY_ID + ".pub.pem"), "wb") as fh:
            fh.write(pub2)
        msg = b'{"x":1}'
        sidecar = json.dumps(ds.build_sig_sidecar(msg, priv)).encode("utf-8")
        ok, _ = ds.verify_sidecar_bytes_with_key(msg, sidecar, signer.public_key)
    assert ok is True  # verified against the ORIGINAL resolved key object, not the swapped file


def test_committed_prod_key_resolves_and_no_private_material():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keys_dir = os.path.join(here, "keys")
    signer, reason = dt.resolve_pinned_key(keys_dir, PROD_KEY_ID)
    assert signer is not None and reason == ""
    for fn in os.listdir(keys_dir):
        assert "priv" not in fn.lower() and not fn.endswith(".key")


ALL = [
    ("resolve_returns_structured_signer", test_resolve_returns_structured_signer),
    ("unknown_signer_blocks", test_unknown_signer_blocks),
    ("forged_key_under_prod_id_blocks", test_forged_key_under_prod_id_blocks),
    ("self_consistent_forged_keys_dir_blocks", test_self_consistent_forged_keys_dir_blocks),
    ("key_id_traversal_blocks_even_when_trusted", test_key_id_traversal_blocks_even_when_trusted),
    ("pinned_key_object_survives_file_swap", test_pinned_key_object_survives_file_swap),
    ("committed_prod_key_resolves_and_no_private_material", test_committed_prod_key_resolves_and_no_private_material),
]

if __name__ == "__main__":
    ok = True
    for name, fn in ALL:
        try:
            fn()
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(0 if ok else 1)
