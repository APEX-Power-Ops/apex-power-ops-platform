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


# ---- Task 8: kind-sniff, census uniqueness, sig pairing, exactly-one census binding,
# committed-set OV007, strict_parse ----
def _kind_sniff_catches_hidden_overlay():
    hidden = fx.canon({"kind": "evidence_overlay", "x": 1})
    files = [("evidence/notes.md", b"# just docs"),
             ("evidence/HIDDEN.JSON", hidden),                       # extension case
             ("evidence/source/x.source.dat", hidden),               # hidden under source/
             ("evidence/overlay-good.json", fx.canon({"kind": "evidence_overlay"}))]
    fails = cic.kind_sniff(files)
    return (any("HIDDEN.JSON" in f for f in fails) and any("x.source.dat" in f for f in fails)
            and not any("overlay-good.json" in f for f in fails))


def _census_uniqueness_fails_duplicates():
    b = fx.canon({"kind": "evidence_snapshot", "n": 1})
    fails = cic.census_uniqueness([("evidence/census-prod-A.json", b), ("evidence/census-prod-B.json", b)])
    return any("byte-identical" in f for f in fails)


def _sig_pairing_both_directions():
    fails = cic.sig_pairing(["evidence/overlay-a.json", "evidence/overlay-b.json"],
                            ["evidence/overlay-a.json.sig", "evidence/overlay-c.json.sig"])
    return any("overlay-b.json" in f for f in fails) and any("overlay-c.json.sig" in f for f in fails)


def _match_census_exactly_one():
    b1, b2 = b"census-one", b"census-two"
    files = [("evidence/census-prod-1.json", b1), ("evidence/census-prod-2.json", b2)]
    h1 = hashlib.sha256(b1).hexdigest()
    p, f = cic.match_census(h1, files)
    zero_p, zero_f = cic.match_census("0" * 64, files)
    dup_files = files + [("evidence/census-prod-3.json", b1)]
    amb_p, amb_f = cic.match_census(h1, dup_files)
    return (p == "evidence/census-prod-1.json" and f is None
            and zero_p is None and "no committed census" in zero_f
            and amb_p is None and "ambiguous" in amb_f)


def _committed_set_ov007_cross_overlay():
    base = "c" * 64
    d1 = {"base_snapshot_sha256": base, "dimension": "advisor_findings",
          "assignments": [{"object_id": "public.t1"}]}
    d2 = {"base_snapshot_sha256": base, "dimension": "advisor_findings",
          "assignments": [{"object_id": "public.t1"}]}          # same (dim, oid), DIFFERENT overlay
    other = {"base_snapshot_sha256": "d" * 64, "dimension": "advisor_findings",
             "assignments": [{"object_id": "public.t1"}]}        # different census -> no conflict
    fails = cic.committed_set_ov007([("evidence/overlay-1.json", d1), ("evidence/overlay-2.json", d2),
                                     ("evidence/overlay-3.json", other)])
    return any("OV007" in f for f in fails) and not any("overlay-3" in f for f in fails)


def _strict_parse_rejects_dup_keys_and_nonfinite():
    try:
        cic.strict_parse(b'{"a": 1, "a": 2}')
        return False
    except ValueError:
        pass
    try:
        cic.strict_parse(b'{"a": NaN}')
        return False
    except ValueError:
        return True


# ---- OPERATOR FOLD (Phase-4 GO): main()'s collection helper must FAIL a non-dict overlay
# document, not crash and not silently accept it into overlay_docs ----
def _collect_overlay_docs_rejects_non_dict():
    files = [("evidence/overlay-list.json", b"[]"), ("evidence/overlay-str.json", b'"x"')]
    docs, fails = cic._collect_overlay_docs(
        ["evidence/overlay-list.json", "evidence/overlay-str.json"], files)
    return (docs == []
            and any("overlay-list.json" in f and "not a JSON object" in f for f in fails)
            and any("overlay-str.json" in f and "not a JSON object" in f for f in fails))


_CASES += [
    ("kind_sniff_catches_hidden_overlay", _kind_sniff_catches_hidden_overlay),
    ("census_uniqueness_fails_duplicates", _census_uniqueness_fails_duplicates),
    ("sig_pairing_both_directions", _sig_pairing_both_directions),
    ("match_census_exactly_one", _match_census_exactly_one),
    ("committed_set_ov007_cross_overlay", _committed_set_ov007_cross_overlay),
    ("strict_parse_rejects_dup_keys_and_nonfinite", _strict_parse_rejects_dup_keys_and_nonfinite),
    ("collect_overlay_docs_rejects_non_dict", _collect_overlay_docs_rejects_non_dict),
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
