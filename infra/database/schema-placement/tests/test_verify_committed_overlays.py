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


# ---- Phase-4.1 item 4: custody-locator URI rule (CI side, mirrors author_overlay.is_custody_uri) ----
def _custody_check_valid_uri_passes():
    docs = [("evidence/overlay-x.json", _doc(locator="vault:padloc/item/xyz", source_hash=None))]
    return cic.custody_locator_check(docs) == []


def _custody_check_filesystem_path_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="/etc/passwd", source_hash=None))]
    fails = cic.custody_locator_check(docs)
    return any("evidence/overlay-x.json" in f for f in fails)


def _custody_check_windows_drive_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="C:\\evidence\\out.log", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


def _custody_check_traversal_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="vault:../secrets", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


def _custody_check_backslash_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="vault:cus\\tody", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


def _custody_check_whitespace_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="vault:custody ref", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


def _custody_check_skips_non_null_source_hash():
    # a committed regular-evidence overlay (non-null source_hash) is out of scope for this check
    # even though its locator is a repo path, not a URI -- orphan_check/source_rehash own that.
    docs = [("evidence/overlay-x.json", _doc(locator="evidence/source/a.source.txt", source_hash="e" * 64))]
    return cic.custody_locator_check(docs) == []


def _custody_check_drive_relative_fails():
    # Cross-engine (Codex) Phase-4.1 follow-up finding: drive-RELATIVE Windows path (letter,
    # colon, no slash) must FAIL, not parse as scheme "C" + opaque.
    docs = [("evidence/overlay-x.json", _doc(locator="C:evidence-out.log", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


def _custody_check_single_letter_scheme_fails():
    docs = [("evidence/overlay-x.json", _doc(locator="x:opaque-ref", source_hash=None))]
    return any("evidence/overlay-x.json" in f for f in cic.custody_locator_check(docs))


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
    ("custody_check_valid_uri_passes", _custody_check_valid_uri_passes),
    ("custody_check_filesystem_path_fails", _custody_check_filesystem_path_fails),
    ("custody_check_windows_drive_fails", _custody_check_windows_drive_fails),
    ("custody_check_traversal_fails", _custody_check_traversal_fails),
    ("custody_check_backslash_fails", _custody_check_backslash_fails),
    ("custody_check_whitespace_fails", _custody_check_whitespace_fails),
    ("custody_check_skips_non_null_source_hash", _custody_check_skips_non_null_source_hash),
    ("custody_check_drive_relative_fails", _custody_check_drive_relative_fails),
    ("custody_check_single_letter_scheme_fails", _custody_check_single_letter_scheme_fails),
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

import shutil  # noqa: E402
import subprocess  # noqa: E402

import author_overlay as ao  # noqa: E402
import disposition_overlay as dov  # noqa: E402

SP = "infra/database/schema-placement"
SP_REAL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COPY = ["author_overlay.py", "verify_overlay_artifact.py", "disposition_overlay.py", "verify_census.py",
         "collect_disposition.py", "disposition_signing.py", "disposition_trust.py",
         "disposition_provenance.py", "overlay.schema.json", "disposition.schema.json",
         "pyproject.toml", "uv.lock", "ci/overlay_ci_checks.py", "ci/verify_committed_overlays.sh"]


def _sh(args, cwd, check=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{args} rc={r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


def _scratch(tmp):
    """Seed tree -> BARE origin -> work clone (a non-bare origin refuses pushes to its checked-out
    branch: receive.denyCurrentBranch -- plan-audit E2E-1, empirically confirmed). Returns
    (work_dir, priv, base_sha). PATCH (test-only, in the SCRATCH COPY): the synthetic public key
    replaces the prod pubkey file AND the TRUSTED_SIGNERS fingerprint line in disposition_trust.py
    is rewritten to the synthetic SPKI -- the shipped gate binary stays fail-closed; the scratch
    repo is a parallel universe signed by the test key under the SAME pinned key-id."""
    priv, pub = fx.keypair()
    seed = os.path.join(tmp, "seed")
    sp = os.path.join(seed, *SP.split("/"))
    os.makedirs(os.path.join(sp, "evidence", "source"), exist_ok=True)
    os.makedirs(os.path.join(sp, "keys"), exist_ok=True)
    os.makedirs(os.path.join(sp, "ci"), exist_ok=True)
    for name in _COPY:
        shutil.copy2(os.path.join(SP_REAL, *name.split("/")), os.path.join(sp, *name.split("/")))
    open(os.path.join(sp, "keys", "prod-disposition-ed25519-2026-07.pub.pem"), "wb").write(pub)
    trust = open(os.path.join(sp, "disposition_trust.py")).read()
    trust = trust.replace("c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca", fx.spki_fp(pub))
    open(os.path.join(sp, "disposition_trust.py"), "w").write(trust)
    _sh(["git", "init", "-q", "-b", "main"], seed)
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], seed)
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"], seed)
    base_sha = _sh(["git", "rev-parse", "HEAD"], seed).stdout.strip()
    origin = os.path.join(tmp, "origin.git")
    _sh(["git", "clone", "-q", "--bare", seed, origin], tmp)
    work = os.path.join(tmp, "work")
    _sh(["git", "clone", "-q", origin, work], tmp)
    return work, priv, base_sha


def _commit_all(work, msg):
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], work)
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], work)


def _gate(work):
    return subprocess.run(["bash", f"{SP}/ci/verify_committed_overlays.sh"],
                          cwd=work, capture_output=True, text=True)


def _fixture_census(work, priv, base_sha):
    """Committed acceptance census whose repo_sha == the scratch BASE commit and whose qb == the
    scratch tree's real query bundle (the driver recomputes it at HEAD)."""
    sys.path.insert(0, SP_REAL)
    import collect_disposition as cds
    census = fx.acceptance_census(["public.t1", "public.t2"], repo_sha=base_sha,
                                  qb=cds.query_bundle_sha256())
    sp = os.path.join(work, *SP.split("/"))
    # Harness fold (controller-authorized): git does not track the seed's empty evidence/ dirs,
    # so the work clone materializes without them -- create before every write into them.
    os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
    cpath, _cs, cb, _sb = fx.write_signed(os.path.join(sp, "evidence"), "census-prod-scratch.json",
                                          census, priv)
    return census, cb, "evidence/census-prod-scratch.json"


def _fixture_overlay(work, priv, census, census_bytes, base_sha, *, name="overlay-consumer_evidence_static_repo-scratch.json",
                     source_name="overlay-consumer_evidence_static_repo-scratch.source.txt",
                     oid="public.t1", source_data=b"public.t1: 0 refs\n"):
    sp = os.path.join(work, *SP.split("/"))
    contract = dov.load_overlay_contract()
    src_rel = None
    source_hash, source_reason, locator = None, "no artifact", "vault:custody/x"
    if source_name is not None:
        src_abs = os.path.join(sp, "evidence", "source", source_name)
        os.makedirs(os.path.dirname(src_abs), exist_ok=True)
        open(src_abs, "wb").write(source_data)
        source_hash, source_reason = __import__("hashlib").sha256(source_data).hexdigest(), None
        locator = "evidence/source/" + source_name
    core = fx.overlay_core("consumer_evidence.static_repo",
                           [{"object_id": oid, "value": {"state": "observed", "found_consumers": 0, "ref": "scan:t"}}])
    doc = ao.assemble_overlay(core, census=census,
                              census_sha256=hashlib.sha256(census_bytes).hexdigest(), contract=contract,
                              producing=(base_sha, None), source_hash=source_hash,
                              source_hash_reason=source_reason, source_locator=locator,
                              captured_at_iso="2026-07-12T06:00:00+00:00")
    os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
    fx.write_signed(os.path.join(sp, "evidence"), name, doc, priv)
    return doc


def _e2e_green_overlay_pr():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        r = _gate(work)
        return r.returncode == 0 and "ALL COMMITTED OVERLAY ARTIFACTS VERIFIED" in r.stdout


def _e2e_source_only_pr_fails():
    # RIDER at the GATE level: an added evidence/source/** record with NO overlay -> FAIL,
    # even though the added-overlay set is empty (steps 1-2 run before the early exit).
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        sp = os.path.join(work, *SP.split("/"))
        os.makedirs(os.path.join(sp, "evidence", "source"), exist_ok=True)
        open(os.path.join(sp, "evidence", "source", "orphan.source.txt"), "wb").write(b"stray")
        _commit_all(work, "source-only PR")
        r = _gate(work)
        return r.returncode == 1 and "orphan source record" in r.stdout


def _e2e_rename_modify_fails():
    # Round-2b CI2b-1 (empirically pinned): rename+modify must FAIL via --no-renames all-A,
    # not slip through as status R.
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, cpath = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "push", "-q", "origin", "main"], work)
        sp = os.path.join(work, *SP.split("/"))
        old = os.path.join(sp, "evidence", "overlay-consumer_evidence_static_repo-scratch.json")
        new = old.replace("scratch", "scratch-renamed")
        data = open(old, "rb").read()
        os.remove(old)
        open(new, "wb").write(data[:-2] + b" }")   # rename + modify (similarity high -> status R)
        _commit_all(work, "rename+modify tamper")
        r = _gate(work)
        # --no-renames decomposes to A+D; the D trips all-A -> the failure MUST be the
        # immutability step (not some unrelated rc=1 path; plan-audit E2E-3 anti-vacuity).
        return r.returncode == 1 and "immutability" in r.stdout


def _e2e_modify_census_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        _census, _cb, cpath = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "push", "-q", "origin", "main"], work)
        sp = os.path.join(work, *SP.split("/"))
        p = os.path.join(sp, *cpath.split("/"))
        open(p, "ab").write(b"\n")
        _commit_all(work, "tamper census")
        r = _gate(work)
        return r.returncode == 1 and "immutability" in r.stdout


def _e2e_delete_sidecar_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "push", "-q", "origin", "main"], work)
        sp = os.path.join(work, *SP.split("/"))
        os.remove(os.path.join(sp, "evidence", "overlay-consumer_evidence_static_repo-scratch.json.sig"))
        _commit_all(work, "delete sidecar")
        r = _gate(work)
        return r.returncode == 1 and "immutability" in r.stdout


def _e2e_symlink_under_evidence_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        # commit a symlink blob (mode 120000) under evidence/source/ without touching the fs:
        r1 = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=work, input="target",
                            capture_output=True, text=True)
        _sh(["git", "update-index", "--add", "--cacheinfo",
             f"120000,{r1.stdout.strip()},{SP}/evidence/source/link.source.txt"], work)
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "symlink"], work)
        r = _gate(work)
        return r.returncode == 1 and "non-regular" in r.stdout


def _e2e_cross_pr_committed_set_dup_fails():
    # A duplicate (dimension, object_id) against an ALREADY-MERGED overlay for the same census.
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence 1")
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "push", "-q", "origin", "main"], work)
        _fixture_overlay(work, priv, census, cb, base,
                         name="overlay-consumer_evidence_static_repo-scratch2.json",
                         source_name="overlay-consumer_evidence_static_repo-scratch2.source.txt",
                         source_data=b"second scan\n")  # SAME (dimension, public.t1)
        _commit_all(work, "overlay evidence 2 (dup)")
        r = _gate(work)
        return r.returncode == 1 and "OV007" in r.stdout


def _e2e_duplicate_census_bytes_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        sp = os.path.join(work, *SP.split("/"))
        shutil.copy2(os.path.join(sp, "evidence", "census-prod-scratch.json"),
                     os.path.join(sp, "evidence", "census-prod-scratch-copy.json"))
        shutil.copy2(os.path.join(sp, "evidence", "census-prod-scratch.json.sig"),
                     os.path.join(sp, "evidence", "census-prod-scratch-copy.json.sig"))
        _commit_all(work, "duplicate census bytes")
        r = _gate(work)
        return r.returncode == 1 and "byte-identical" in r.stdout


def _e2e_hidden_overlay_off_path_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        sp = os.path.join(work, *SP.split("/"))
        hidden = fx.canon({"kind": "evidence_overlay", "smuggled": True})
        os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
        open(os.path.join(sp, "evidence", "notes.JSON"), "wb").write(hidden)
        _commit_all(work, "hidden overlay")
        r = _gate(work)
        return r.returncode == 1 and "canonical" in r.stdout


def _e2e_census_nonancestor_fails():
    # Matrix row "self-referential census binding": a census whose repo_sha is NOT an ancestor of
    # HEAD must fail the non-self-referential binding (plan-audit ECMC-1/SPEC-1).
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        sys.path.insert(0, SP_REAL)
        import collect_disposition as cds
        census = fx.acceptance_census(["public.t1", "public.t2"], repo_sha="1" * 40,
                                      qb=cds.query_bundle_sha256())
        sp = os.path.join(work, *SP.split("/"))
        os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
        _cp, _cs, cb, _sb = fx.write_signed(os.path.join(sp, "evidence"),
                                            "census-prod-scratch.json", census, priv)
        _commit_all(work, "census evidence (foreign repo_sha)")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        r = _gate(work)
        return r.returncode == 1 and "not an ancestor" in r.stdout


def _e2e_tooling_drift_since_census_fails():
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        sp = os.path.join(work, *SP.split("/"))
        open(os.path.join(sp, "disposition_overlay.py"), "a").write("\n# drift\n")
        _commit_all(work, "tooling drift after census")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        r = _gate(work)
        return r.returncode == 1 and "TOOLING changed" in r.stdout


def _e2e_forbidden_dim_null_producing_green():
    # FORBIDDEN dim (advisor_findings): producing null+reason, NA source (custody locator, NO
    # source record) -- proves the driver's null-safe skip and the NA pair path THROUGH the gate.
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        sp = os.path.join(work, *SP.split("/"))
        contract = dov.load_overlay_contract()
        core = fx.overlay_core("advisor_findings",
                               [{"object_id": "public.t2", "value": {"state": "observed", "value": ["lint:ok"]}}])
        doc = ao.assemble_overlay(core, census=census, census_sha256=hashlib.sha256(cb).hexdigest(),
                                  contract=contract, producing=(None, "advisor API snapshot"),
                                  source_hash=None, source_hash_reason="no committed artifact",
                                  source_locator="vault:custody/advisor-2026-07",
                                  captured_at_iso="2026-07-12T06:00:00+00:00")
        os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
        fx.write_signed(os.path.join(sp, "evidence"), "overlay-advisor_findings-scratch.json", doc, priv)
        _commit_all(work, "advisor overlay (NA pair, null producing)")
        r = _gate(work)
        return r.returncode == 0 and "ALL COMMITTED OVERLAY ARTIFACTS VERIFIED" in r.stdout


def _e2e_bad_custody_locator_fails():
    # Phase-4.1 item 4, e2e: a committed NA-case overlay whose source_locator is a filesystem
    # path (not a URI) must FAIL the whole gate via custody_locator_check, even though every
    # other check (orphan/rehash/OV007/etc.) is satisfied -- mirrors
    # e2e_forbidden_dim_null_producing_green's GREEN NA-pair shape but with a bad locator.
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        sp = os.path.join(work, *SP.split("/"))
        contract = dov.load_overlay_contract()
        core = fx.overlay_core("advisor_findings",
                               [{"object_id": "public.t2", "value": {"state": "observed", "value": ["lint:ok"]}}])
        doc = ao.assemble_overlay(core, census=census, census_sha256=hashlib.sha256(cb).hexdigest(),
                                  contract=contract, producing=(None, "advisor API snapshot"),
                                  source_hash=None, source_hash_reason="no committed artifact",
                                  source_locator="/etc/advisor-export.log",  # path-like -- must FAIL
                                  captured_at_iso="2026-07-12T06:00:00+00:00")
        os.makedirs(os.path.join(sp, "evidence"), exist_ok=True)
        fx.write_signed(os.path.join(sp, "evidence"), "overlay-advisor_findings-scratch-badcustody.json", doc, priv)
        _commit_all(work, "advisor overlay (bad custody locator)")
        r = _gate(work)
        return r.returncode == 1 and "custody locator" in r.stdout


def _e2e_source_hash_mismatch_fails():
    # The record is ADDED in the same PR (immutability passes) but its bytes no longer match the
    # overlay's source_hash -- the step-4 rehash wiring must FAIL (plan-audit E2E-2).
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        sp = os.path.join(work, *SP.split("/"))
        open(os.path.join(sp, "evidence", "source",
                          "overlay-consumer_evidence_static_repo-scratch.source.txt"), "wb").write(b"TAMPERED")
        _commit_all(work, "overlay evidence w/ tampered source record")
        r = _gate(work)
        return r.returncode == 1 and "source_hash" in r.stdout


def _e2e_modify_committed_source_record_fails():
    # The round-2 SRC-IMMUT headline itself: a later PR modifying a COMMITTED source record must
    # trip the evidence/source/** immutability pathspec (plan-audit SPEC-5).
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        _commit_all(work, "overlay evidence")
        _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "push", "-q", "origin", "main"], work)
        sp = os.path.join(work, *SP.split("/"))
        open(os.path.join(sp, "evidence", "source",
                          "overlay-consumer_evidence_static_repo-scratch.source.txt"), "ab").write(b"\nEDIT")
        _commit_all(work, "tamper committed source record")
        r = _gate(work)
        return r.returncode == 1 and "immutability" in r.stdout


def _e2e_added_overlay_bad_signature_fails():
    # Tampered-before-commit overlay: status A (immutability passes), so the verifier-subprocess
    # wiring must be what rejects it (OV001) -- proves the rc-propagation path (plan-audit E2E-2).
    with tempfile.TemporaryDirectory() as tmp:
        work, priv, base = _scratch(tmp)
        census, cb, _ = _fixture_census(work, priv, base)
        _commit_all(work, "census evidence")
        _fixture_overlay(work, priv, census, cb, base)
        sp = os.path.join(work, *SP.split("/"))
        p = os.path.join(sp, "evidence", "overlay-consumer_evidence_static_repo-scratch.json")
        data = open(p, "rb").read()
        open(p, "wb").write(data[:-2] + b" }")
        _commit_all(work, "overlay evidence (tampered pre-commit)")
        r = _gate(work)
        return r.returncode == 1 and "verify_overlay_artifact rejected" in r.stdout


_CASES += [
    ("e2e_green_overlay_pr", _e2e_green_overlay_pr),
    ("e2e_source_only_pr_fails", _e2e_source_only_pr_fails),
    ("e2e_rename_modify_fails", _e2e_rename_modify_fails),
    ("e2e_modify_census_fails", _e2e_modify_census_fails),
    ("e2e_delete_sidecar_fails", _e2e_delete_sidecar_fails),
    ("e2e_symlink_under_evidence_fails", _e2e_symlink_under_evidence_fails),
    ("e2e_cross_pr_committed_set_dup_fails", _e2e_cross_pr_committed_set_dup_fails),
    ("e2e_duplicate_census_bytes_fails", _e2e_duplicate_census_bytes_fails),
    ("e2e_hidden_overlay_off_path_fails", _e2e_hidden_overlay_off_path_fails),
    ("e2e_census_nonancestor_fails", _e2e_census_nonancestor_fails),
    ("e2e_tooling_drift_since_census_fails", _e2e_tooling_drift_since_census_fails),
    ("e2e_forbidden_dim_null_producing_green", _e2e_forbidden_dim_null_producing_green),
    ("e2e_bad_custody_locator_fails", _e2e_bad_custody_locator_fails),
    ("e2e_source_hash_mismatch_fails", _e2e_source_hash_mismatch_fails),
    ("e2e_modify_committed_source_record_fails", _e2e_modify_committed_source_record_fails),
    ("e2e_added_overlay_bad_signature_fails", _e2e_added_overlay_bad_signature_fails),
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
