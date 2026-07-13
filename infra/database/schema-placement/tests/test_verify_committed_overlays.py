"""Suite for the overlay-evidence CI gate: pure-function checks (Tasks 7-8) + scratch-git-repo
end-to-end gate cases (Task 9). Script __main__ runner."""
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ci"))

import _overlay_pub_fixtures as fx  # noqa: E402
import overlay_ci_checks as cic  # noqa: E402

_CASES = []


def _doc(locator="evidence/source/a.source.txt", source_hash="e" * 64):
    d = {"dimension": "consumer_evidence.static_repo", "source_locator": locator,
         "source_hash": source_hash, "base_snapshot_sha256": "c" * 64,
         "assignments": [{"object_id": "public.t1", "value": {}}]}
    if source_hash is None:
        d["source_hash_not_applicable_reason"] = "custody"
    return d


# ---- RIDER: the first-class failing test, before ANY implementation ----
def source_record_without_overlay_fails():
    fails = cic.orphan_check([], ["evidence/source/orphan.source.txt"])
    return any("orphan" in f and "orphan.source.txt" in f for f in fails)


def _referenced_source_passes():
    return cic.orphan_check([("evidence/overlay-x.json", _doc())], ["evidence/source/a.source.txt"]) == []


def _multiply_referenced_source_fails():
    docs = [("evidence/overlay-x.json", _doc()), ("evidence/overlay-y.json", _doc())]
    fails = cic.orphan_check(docs, ["evidence/source/a.source.txt"])
    return any("referenced by 2" in f for f in fails)


def _missing_referenced_source_fails():
    fails = cic.orphan_check([("evidence/overlay-x.json", _doc())], [])
    return any("missing" in f for f in fails)


def _na_doc_contributes_no_reference():
    docs = [("evidence/overlay-x.json", _doc(locator="vault:custody/x", source_hash=None))]
    fails = cic.orphan_check(docs, ["evidence/source/orphan.source.txt"])
    return any("orphan" in f for f in fails)  # the record is STILL an orphan


def _traversal_locator_fails():
    ok1, _ = cic.normalize_locator("evidence/source/../../keys/prod.pub.pem")
    ok2, _ = cic.normalize_locator("/etc/passwd")
    ok3, _ = cic.normalize_locator("evidence/census-run-2026-07-11.md")  # outside evidence/source/
    ok4, _ = cic.normalize_locator("evidence\\source\\x")  # backslash smuggling
    ok5, norm = cic.normalize_locator("evidence/source/ok.source.txt")
    return (not ok1) and (not ok2) and (not ok3) and (not ok4) and ok5 and norm == "evidence/source/ok.source.txt"


def _non_regular_source_fails():
    # protected_sources contains only committed REGULAR blobs; a locator pointing at anything
    # else (symlink, gitlink, uncommitted file) is absent from it -> FAIL.
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "evidence", "source"), exist_ok=True)
        p = os.path.join(d, "evidence", "source", "a.source.txt")
        open(p, "wb").write(b"data")
        doc = _doc(source_hash=hashlib.sha256(b"data").hexdigest())
        fails = cic.source_rehash(doc, d, protected_sources=set())  # not in the committed set
        return any("not a committed regular source record" in f for f in fails)


def _hash_mismatch_source_fails():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "evidence", "source"), exist_ok=True)
        open(os.path.join(d, "evidence", "source", "a.source.txt"), "wb").write(b"TAMPERED")
        doc = _doc(source_hash=hashlib.sha256(b"original").hexdigest())
        fails = cic.source_rehash(doc, d, protected_sources={"evidence/source/a.source.txt"})
        return any("source_hash" in f for f in fails)


def _rehash_green():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "evidence", "source"), exist_ok=True)
        open(os.path.join(d, "evidence", "source", "a.source.txt"), "wb").write(b"data")
        doc = _doc(source_hash=hashlib.sha256(b"data").hexdigest())
        return cic.source_rehash(doc, d, protected_sources={"evidence/source/a.source.txt"}) == []


_CASES += [
    ("source_record_without_overlay_fails", source_record_without_overlay_fails),  # RIDER, first
    ("referenced_source_passes", _referenced_source_passes),
    ("multiply_referenced_source_fails", _multiply_referenced_source_fails),
    ("missing_referenced_source_fails", _missing_referenced_source_fails),
    ("na_doc_contributes_no_reference", _na_doc_contributes_no_reference),
    ("traversal_locator_fails", _traversal_locator_fails),
    ("non_regular_source_fails", _non_regular_source_fails),
    ("hash_mismatch_source_fails", _hash_mismatch_source_fails),
    ("rehash_green", _rehash_green),
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
    print("\n=== VERIFY COMMITTED OVERLAYS SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
