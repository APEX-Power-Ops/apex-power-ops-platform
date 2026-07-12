"""Loader tests for disposition_overlay.py (Tasks 2-8). Offline; throwaway fixture keys only.

Runner: uv run --project . --locked python tests/test_overlay_loader.py
"""
import copy
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # tests/ dir, to reuse the real helpers
import disposition_overlay as ov  # noqa: E402
import disposition_signing as _ds  # noqa: E402
import test_check_disposition as tcd  # noqa: E402 -- reuse the SCHEMA-VALID snapshot/rel helpers (audit F5)

# Canonical, mutually-coherent fixture clock (audit F5). base census observed_at == tcd._snapshot's;
# NOW is after it; the default overlay captured_at and window sit inside [.., NOW] with
# base_observed_at IN the default window (ended_at == base_observed_at), so the default derivation is
# valid and every timestamp is internally consistent.
CENSUS_OBSERVED_AT = "2026-07-10T20:00:00Z"    # == tcd._snapshot observed_at (base_observed_at)
NOW_ISO = "2026-07-11T00:00:00Z"
DEF_CAPTURED = "2026-07-10T21:00:00Z"          # <= NOW, >= every default window ended_at
DEF_WIN = {"started_at": "2026-06-05T00:00:00Z", "ended_at": CENSUS_OBSERVED_AT}  # ~35d; ended == base_observed_at
_CONTRACT = ov.load_overlay_contract()


def _ephemeral_keypair():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(obj, priv):
    body = _canon(obj)
    sidecar = json.dumps(_ds.build_sig_sidecar(body, priv)).encode("utf-8")
    return body, sidecar


def _no_bool():
    return {"state": "not_observed", "detail": "pending"}


def _no_ci():
    return {"state": "not_observed", "found_consumers": None, "ref": None, "detail": "pending"}


def _zero_census(oids):
    """A fully SCHEMA-VALID census built from tcd._snapshot/_rel (all required top-level fields:
    repo_sha, collector_version, query_bundle_sha256, catalog_relation_count, collection_scope,
    target_identity, ...), forced to the canonical zero-width consumer window + all six overlay dims
    not_observed. database_deps stays observed (NOT an overlay target). Reuses the real helpers (F5)."""
    rels = []
    for oid in oids:
        schema, name = oid.split(".", 1)
        r = tcd._rel(oid, schema, name, "v")
        r["in_data_api_exposed_schema"] = _no_bool()
        r["advisor_findings"] = _no_bool()
        ce = r["consumer_evidence"]
        ce["observation_window"] = {"started_at": CENSUS_OBSERVED_AT, "ended_at": CENSUS_OBSERVED_AT}
        for dim in ("static_repo", "runtime_logs", "external_clients", "operator_declaration"):
            ce[dim] = _no_ci()
        # database_deps stays observed (tcd._rel set it observed) — not an overlay target
        rels.append(r)
    return tcd._snapshot(rels)  # sets observed_at == CENSUS_OBSERVED_AT + all required snapshot fields


def _overlay(dimension, source_type, assignments, census_bytes=None, **overrides):
    """A well-formed overlay bound to census_bytes. Default source_hash/producing_repo_sha are NON-null
    with NO *_not_applicable_reason (IFF-valid, audit F9); dimensions needing null+reason override both."""
    doc = {"kind": "evidence_overlay", "overlay_version": "1",
           "dimension": dimension, "source_type": source_type,
           "authority": "test", "collection_method": "test", "source_locator": "test:x",
           "source_hash": "e" * 64,
           "base_snapshot_sha256": hashlib.sha256(census_bytes).hexdigest() if census_bytes else "a" * 64,
           "disposition_schema_sha256": _CONTRACT.disp_sha256, "overlay_schema_sha256": _CONTRACT.overlay_sha256,
           "project_ref": "fxoyniqnrlkxfligbxmg",
           "captured_at": DEF_CAPTURED, "observation_window": dict(DEF_WIN),
           "producing_repo_sha": "d" * 40,
           "assignments": assignments}
    doc.update(overrides)
    return doc


def _codes(diags):
    return sorted({c for c, _l, _m in diags})


# ---- Task 2: signature + binding ----
def _tampered_byte_fails_OV001():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    tampered = bytearray(body); tampered[10] ^= 0x01
    ok, _r = ov.verify_overlay(bytes(tampered), sig, pub)
    return ok is False


def _good_signature_verifies():
    priv, pub = _ephemeral_keypair()
    body, sig = _sign(_overlay("consumer_evidence.static_repo", "repository_scan",
                               [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}]), priv)
    ok, _r = ov.verify_overlay(body, sig, pub)
    return ok is True


def _base_hash_mismatch_OV002():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}])
    doc["base_snapshot_sha256"] = "f" * 64  # not the census hash
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV002" in _codes(diags)


def _project_mismatch_OV003():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, project_ref="other-project")
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=doc["disposition_schema_sha256"], on_disk_overlay_sha=doc["overlay_schema_sha256"])
    return "OV003" in _codes(diags)


def _schema_drift_OV020():
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, disposition_schema_sha256="0" * 64)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV020" in _codes(diags)


def _schema_drift_overlay_branch_OV020():
    # The overlay_schema_sha256 half of OV020 must fire independently of the disposition half
    # (regression: the disp-branch test alone left this half unexercised).
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb, overlay_schema_sha256="0" * 64)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV020" in _codes(diags)


def _project_mismatch_census_vs_expect_OV003():
    # OV003 is a THREE-way equality: a doc whose project_ref matches the census must STILL be rejected
    # when census_project_ref != expect_project_ref (the --expect-project-ref axis, not just the doc's).
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb)  # doc.project_ref == census_project_ref == fxoyniqnrlkxfligbxmg
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="a-different-expected-ref",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return "OV003" in _codes(diags)


def _check_binding_clean_no_diags():
    # The POSITIVE side of the fail-closed contract: a correctly-bound overlay yields NO diagnostics.
    census = _zero_census(["public.v"]); cb = _canon(census)
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=cb)
    diags = ov.check_binding(doc, census_sha256=hashlib.sha256(cb).hexdigest(),
                             census_project_ref="fxoyniqnrlkxfligbxmg", expect_project_ref="fxoyniqnrlkxfligbxmg",
                             on_disk_disp_sha=_CONTRACT.disp_sha256, on_disk_overlay_sha=_CONTRACT.overlay_sha256)
    return diags == []


def _parse_overlay_rejects_duplicate_keys():
    # A JSON body with a repeated object key must raise ValueError (parser-confusion guard, fail-closed).
    try:
        ov.parse_overlay(b'{"kind": "evidence_overlay", "kind": "sneaky"}')
        return False  # must have raised
    except ValueError:
        return True
    except Exception:
        return False


def _parse_overlay_rejects_nonfinite():
    # NaN / Infinity / -Infinity JSON constants must raise ValueError (Python json accepts them by default).
    for body in (b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'):
        try:
            ov.parse_overlay(body)
            return False  # must have raised
        except ValueError:
            continue
        except Exception:
            return False
    return True


def _parse_overlay_accepts_valid_body():
    # Non-vacuity guard for the two reject tests: a well-formed overlay body parses to a dict.
    census_bytes = _canon(_zero_census(["public.v"]))
    doc = _overlay("consumer_evidence.static_repo", "repository_scan",
                   [{"object_id": "public.v", "value": {"state": "observed", "found_consumers": 0, "ref": "s:1"}}],
                   census_bytes=census_bytes)
    parsed = ov.parse_overlay(_canon(doc))
    return isinstance(parsed, dict) and parsed.get("kind") == "evidence_overlay"


_CASES = [
    ("tampered_byte_fails_OV001", _tampered_byte_fails_OV001),
    ("good_signature_verifies", _good_signature_verifies),
    ("base_hash_mismatch_OV002", _base_hash_mismatch_OV002),
    ("project_mismatch_OV003", _project_mismatch_OV003),
    ("schema_drift_OV020", _schema_drift_OV020),
    ("schema_drift_overlay_branch_OV020", _schema_drift_overlay_branch_OV020),
    ("project_mismatch_census_vs_expect_OV003", _project_mismatch_census_vs_expect_OV003),
    ("check_binding_clean_no_diags", _check_binding_clean_no_diags),
    ("parse_overlay_rejects_duplicate_keys", _parse_overlay_rejects_duplicate_keys),
    ("parse_overlay_rejects_nonfinite", _parse_overlay_rejects_nonfinite),
    ("parse_overlay_accepts_valid_body", _parse_overlay_accepts_valid_body),
]

if __name__ == "__main__":
    ok = True
    for name, fn in _CASES:
        try:
            r = bool(fn())
        except Exception as exc:  # noqa: BLE001
            r = False; name = f"{name} (EXC {exc})"
        ok = ok and r
        print(f"  {'ok  ' if r else 'FAIL'}: {name}")
    print("\n=== OVERLAY LOADER SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
