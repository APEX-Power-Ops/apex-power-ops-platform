# Overlay Evidence Publication Tooling — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the producer tooling for the disposition-ledger signed-overlay contract — an overlay author/sign CLI, a standalone committed-artifact verifier, the `overlay-evidence` CI gate, and the two runbooks — exactly per the operator-approved design `docs/superpowers/specs/2026-07-12-overlay-evidence-publication-design.md` @ `8f6d41c4`.

**Architecture:** Three sibling CLI modules under `infra/database/schema-placement/` that REUSE the merged consumer contract (`disposition_overlay.py`) and the census gate (`verify_census.check_census`) — never re-implement them — plus a thin shell CI gate delegating repo-level logic to a Python driver. Everything is offline, fail-closed with stable codes, and validated with synthetic Ed25519 keys only.

**Tech Stack:** Python 3.11, `jsonschema==4.23.0`, `cryptography==49.0.0`, `referencing` (transitive), bash + git for the CI gate, `uv`-locked project (`uv run --project . --locked`). No new dependencies; `pyproject.toml`/`uv.lock` are NOT modified.

## Global Constraints (bind every task)

- **Spec authority:** the operator-approved design @ `8f6d41c4` governs. Where this plan resolves a spec ambiguity it says so explicitly in the task ("Plan decision"). No task may contradict the spec silently.
- **Schemas FROZEN.** `disposition.schema.json` and `overlay.schema.json` are read-only. No task edits them. A task believing it needs a schema edit is an escalation — STOP and report BLOCKED.
- **Frozen modules.** `disposition_overlay.py`, `disposition_signing.py`, `disposition_trust.py`, `disposition_provenance.py`, `collect_disposition.py`, `verify_census.py`, `check_disposition.py`, `keys/`, and the existing test suites are READ-ONLY inputs. (D3: the atomic-publish helper is REPLICATED in `author_overlay.py`, the collector is untouched.)
- **Module DAG (acyclic).** New modules MAY import `disposition_overlay`, `verify_census`, `disposition_signing`, `disposition_trust`, `disposition_provenance`. They MUST NOT import `check_disposition`. Nothing existing imports the new modules.
- **Value-silence (extended).** The Ed25519 private key comes ONLY from env `DISPOSITION_SIGNING_KEY` — never argv, never printed, never embedded; a load failure prints a generic message (`AO007`), never PEM content. The `--source-file` bytes are secret-bearing: the author only `read → sha256 → copy`s them, never prints or parses content; a read failure is `AO009` printing ONLY the path + `type(exc).__name__`, no stack trace.
- **COMPUTED, never typed.** `base_snapshot_sha256`, `disposition_schema_sha256`, `overlay_schema_sha256`, `project_ref`, `captured_at`, `producing_repo_sha`, `source_hash`, and (when a record is published) `source_locator` are computed by the tool. Operator supplies semantics only (`--input` core + `--source-custody-locator` in the null-`source_hash` case).
- **No-clobber, sidecar-first, atomic.** Publish = temp file + `flush` + `os.fsync` + `os.link` (atomic create-if-absent; `FileExistsError` → refuse), with a `finally` temp-unlink — a verbatim replica of `collect_disposition._write_bytes_atomic`'s no-clobber branch. Order: source record (when applicable) → sidecar → overlay. Never `os.rename`/`os.replace`.
- **Source-pinned trust anchor.** Signers resolve ONLY through `disposition_trust.resolve_pinned_key` (source-constant `TRUSTED_SIGNERS`). No caller-supplied trust map. Tests monkeypatch the module constant (in-process) or sed the constant in a SCRATCH-repo copy (CI e2e) — never weaken the shipped gate.
- **pytest is NOT a locked dep.** Every suite is a script `__main__` runner executed as `uv run --project . --locked python tests/<file>.py` from `infra/database/schema-placement/` (pattern: `_CASES` list of `(name, fn)`, fn returns truthy, runner prints `ok/FAIL` lines and exits 0/1 — mirror `tests/test_overlay_loader.py`).
- **TDD, negatives first.** Every task writes its failing tests BEFORE implementation and shows the RED run. **OPERATOR RIDER (binding):** the source-orphan CI guard is a FIRST-CLASS task (Task 7) whose failing test `source_record_without_overlay_fails` is written before any implementation, plus negative tests for **orphan, multiply-referenced, traversal, non-regular, and hash-mismatch** source records.
- **Synthetic keys ONLY.** All tests generate ephemeral Ed25519 keypairs via `cryptography`. The production signing key never appears anywhere; the production PUBLIC key/fingerprint are never replaced in the real tree (scratch-repo copies only).
- **Offline.** No DB, no network in any code or test. (The CI gate's `git fetch` runs only in real CI / scratch repos with a local `origin`.)
- **CI pinned constants (copy verbatim into the gate):** `--expect-project-ref fxoyniqnrlkxfligbxmg`, `--expect-database postgres`, `--expect-schemas public`, `--require-role-markers anon,authenticated,service_role`, `--key-id prod-disposition-ed25519-2026-07`; expected query bundle computed at HEAD via `collect_disposition.query_bundle_sha256()` (never the census's self-attested value).
- **TOOLING pathspec (drift checks, copy verbatim):** `author_overlay.py verify_overlay_artifact.py disposition_overlay.py verify_census.py collect_disposition.py disposition_signing.py disposition_trust.py disposition_provenance.py overlay.schema.json disposition.schema.json keys` (all under `infra/database/schema-placement/`). Plan decision: the gate scripts themselves (`ci/…`) are NOT in TOOLING — the gate always executes at HEAD, matching the census gate's precedent.
- **Host execution contract.** Build runs on the host worktree `/home/olares/code/apex/apex-schema-pub` (branch `schema-placement/overlay-publication`) over `ssh olares-mesh`; every command below is relative to `infra/database/schema-placement/` unless stated; export `PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH` first. Stage EXACT paths for every commit (never `git add <dir>`).
- **Error-code vocabulary (fixed by the spec + this plan):** `AO000` input unreadable/invalid · `AO001` census signature failed · `AO002` `--input` missing/invalid field (incl. an NA-reason supplied for a REQUIRED-producing dim) · `AO003` project-ref mismatch · `AO004` source-file/NA-reason/custody-locator exclusivity violation · `AO005` assembled overlay failed a consumer check (prints the underlying `OV0xx`) · `AO006` reserved · `AO007` signing key unset / invalid PEM / fingerprint ≠ pinned signer · `AO008` publish failed / path exists · `AO009` source-file unreadable (path + exception type only) · `AO010` provenance gate (dirty or HEAD ≠ `--expect-gate-repo-sha`) · `AO011` base census failed `verify_census` acceptance (prints `CN0xx`) · `AO012` in-memory sidecar verify failed · `AO013` signer key-id not resolvable through `TRUSTED_SIGNERS` (the spec's "key-resolution block, CN013-analog").

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `tests/_overlay_pub_fixtures.py` (new) | Shared synthetic fixtures: keypair, acceptance-grade census, overlay core, signed writers, trust patcher | 1 |
| `author_overlay.py` (new) | Author CLI: assemble → validate signed bytes → census acceptance → signer parity → atomic publish | 2–5 |
| `tests/test_author_overlay.py` (new) | Author suite (negatives first) | 2–5 |
| `verify_overlay_artifact.py` (new) | Standalone artifact + base-census verifier CLI | 6 |
| `tests/test_verify_overlay_artifact.py` (new) | Verifier suite | 6 |
| `ci/overlay_ci_checks.py` (new) | Repo-level CI driver: orphan guard, kind-sniff, census uniqueness, exactly-one binding, locator constraints + rehash, committed-set OV007, per-overlay orchestration | 7–8 |
| `ci/verify_committed_overlays.sh` (new) | Thin shell gate: fail-closed fetch, unique merge-base, `--no-renames --name-status` all-`A` immutability, mode check, delegate to driver | 9 |
| `tests/test_verify_committed_overlays.py` (new) | Driver unit suite + scratch-git-repo end-to-end gate suite | 7–9 |
| `.github/workflows/schema-placement-ci.yml` (modify) | Add 3 suites to the loop + the `overlay-evidence` job | 10 |
| `OVERLAY_COLLECTION_RUNBOOK.md` (new) | Six-dimension collection runbook (DO-NOT-RUN-until-GO) | 11 |
| `CENSUS_RUNBOOK.md` (modify) | PG17.6, `disposition_trust.py` anchor, post-census sequence, immutability note | 12 |
| — | Full regression + whole-branch cross-engine review | 13 |

**Interface map (single source of truth for cross-task names):**

```python
# author_overlay.py
AUTHOR_VERSION = "0.1.0"
class AuthorError(Exception): ...            # .code ("AO0xx"), .message; str() -> "AO0xx author: <message>"
def load_input_core(path) -> dict                                   # AO000/AO002
def compute_producing(dimension, gate_repo_sha, na_reason) -> tuple  # (sha_or_None, reason_or_None); raises AuthorError AO002
def read_source(source_file, na_reason, custody_locator) -> tuple
    # -> (source_bytes_or_None, na_reason_or_None, custody_or_None, ext_or_None)
    # raises AuthorError AO004 (exclusivity) / AO009 (unreadable; path + exception type only)
def assemble_overlay(core, *, census, census_sha256, contract, producing, source, captured_at_iso) -> dict
def validate_assembled(message: bytes, *, census, contract, expect_project_ref, census_bytes_sha, now) -> list
    # -> [(code, locus, msg)] running: parse_overlay -> isinstance guard -> validate_overlay ->
    #    check_binding -> check_observation_window -> captured_at<=now -> check_target -> intra check_conflict
def _write_bytes_atomic_noclobber(path, data) -> None               # replica; FileExistsError propagates
def publish_set(entries) -> None                                    # ordered [(path, bytes), ...]; AO008 wrapper
def canonical_names(dimension, census_sha256, captured_dt, out_dir, source_ext) -> dict
    # {"overlay": path, "sig": path, "source": path_or_None, "locator": "evidence/source/<name>" , "stamp": "<UTC>"}
    # probes -00..-99 suffix for a fully-free set (AO008 if none free)
def main(argv=None) -> int

# verify_overlay_artifact.py
def verify_artifact(overlay_bytes, sig_bytes, census, census_bytes, *, signer, contract,
                    expect_project_ref, now) -> list                # [(code, locus, msg)]; artifact-side only
def main(argv=None) -> int

# ci/overlay_ci_checks.py
SP = "infra/database/schema-placement"
PINNED = {"project_ref": "fxoyniqnrlkxfligbxmg", "database": "postgres", "schemas": "public",
          "role_markers": "anon,authenticated,service_role", "key_id": "prod-disposition-ed25519-2026-07"}
TOOLING = [...]                                                     # the Global-Constraints list, SP-prefixed
def normalize_locator(locator) -> tuple                             # (ok: bool, normalized_or_reason: str)
def orphan_check(overlay_docs, source_paths) -> list                # FAIL strings; RIDER function
def kind_sniff(files) -> list                                       # files: [(path, bytes)]; FAIL strings
def census_uniqueness(census_files) -> list                         # [(path, bytes)]; FAIL strings
def committed_set_ov007(overlay_docs) -> list                       # docs: [(path, dict)]; FAIL strings
def match_census(base_hash, census_files) -> tuple                  # (path_or_None, fail_or_None)
def source_rehash(doc, sp_dir, protected_sources) -> list           # locator constraints + sha256 compare
def main(argv=None) -> int                                          # --base <sha>; orchestrates; exit 0/1
```

---

### Task 1: Shared synthetic fixtures (`tests/_overlay_pub_fixtures.py`)

**Files:**
- Create: `infra/database/schema-placement/tests/_overlay_pub_fixtures.py`
- Test: self-check block in the same file (run directly; NOT registered in the CI loop — every later suite exercises it)

**Interfaces:**
- Consumes (existing code): `test_overlay_loader._zero_census(oids)` (proven schema-valid zero-width census), `disposition_signing` (`build_sig_sidecar`, `load_public_key_pem`, `public_key_fingerprint`), `disposition_trust.TRUSTED_SIGNERS`, `disposition_overlay.load_overlay_contract`, `verify_census.check_census`.
- Produces (used by Tasks 2–9): `KEY_ID="pub-test-ed25519"`, `PROJECT_REF="fxoyniqnrlkxfligbxmg"`, `FAKE_REPO_SHA`, `FAKE_QB`, `keypair() -> (priv, pub_pem)`, `priv_pem(priv) -> str`, `spki_fp(pub_pem) -> str`, `canon(obj) -> bytes`, `sidecar_bytes_for(message, priv) -> bytes`, `trusted(key_id, fp)` (contextmanager), `write_keys_dir(d, pub_pem, key_id=KEY_ID) -> keys_dir`, `acceptance_census(oids, *, repo_sha=FAKE_REPO_SHA, qb=FAKE_QB) -> dict`, `acceptance_expects(census) -> dict` (keys: `project_ref, database, schemas, census_repo_sha, role_markers, query_bundle_sha256`), `overlay_core(dimension, assignments, window=None) -> dict`, `write_signed(dirpath, basename, obj, priv) -> (path, sig_path, obj_bytes, sig_bytes)`.

- [ ] **Step 1: Write the fixtures module with a self-check `__main__`**

```python
"""Shared synthetic fixtures for the overlay-publication suites (Tasks 2-9).

Synthetic Ed25519 keys ONLY -- the production signing key never appears in tests. The census
fixture is ACCEPTANCE-GRADE: it passes the full verify_census.check_census contract with the
expects returned by acceptance_expects(), and reuses test_overlay_loader._zero_census for the
schema-valid relation bodies (zero-width windows, six not_observed dims)."""
import contextlib
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disposition_overlay as dov  # noqa: E402
import disposition_signing as ds  # noqa: E402
import disposition_trust as dt  # noqa: E402
import verify_census as vc  # noqa: E402
import test_overlay_loader as tol  # noqa: E402 -- reuse the proven schema-valid census builder

KEY_ID = "pub-test-ed25519"
PROJECT_REF = "fxoyniqnrlkxfligbxmg"
FAKE_REPO_SHA = "a" * 40
FAKE_QB = "b" * 64


def keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, pub_pem


def priv_pem(priv):
    from cryptography.hazmat.primitives import serialization
    return priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                              serialization.NoEncryption()).decode("utf-8")


def spki_fp(pub_pem):
    return ds.public_key_fingerprint(ds.load_public_key_pem(pub_pem))


def canon(obj) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")


def sidecar_bytes_for(message: bytes, priv) -> bytes:
    return canon(ds.build_sig_sidecar(message, priv))


@contextlib.contextmanager
def trusted(key_id, fingerprint):
    prev = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        dt.TRUSTED_SIGNERS.clear()
        dt.TRUSTED_SIGNERS.update(prev)


def write_keys_dir(d, pub_pem, key_id=KEY_ID):
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, key_id + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    return keys_dir


def acceptance_census(oids, *, repo_sha=FAKE_REPO_SHA, qb=FAKE_QB):
    """A census that passes the FULL check_census contract with acceptance_expects(census)."""
    c = tol._zero_census(oids)
    n = len(c["relations"])
    c.update({
        "project_ref": PROJECT_REF, "repo_sha": repo_sha, "query_bundle_sha256": qb,
        "collector_version": "0.1.0", "relation_count": n, "catalog_relation_count": n,
        "generator": "collect_disposition/0.1.0",
        "collection_scope": {
            "schemas": ["public"], "expected_database": "postgres",
            "required_role_markers": ["anon", "authenticated", "service_role"],
            "repo_sha": repo_sha, "query_bundle_sha256": qb, "collector_version": "0.1.0"},
        "target_identity": {
            "current_database": "postgres", "current_user": "postgres",
            "server_version": "PostgreSQL 17.6 (synthetic)", "server_version_num": 170006,
            "transaction_read_only": True, "expected_database": "postgres",
            "platform_role_markers": ["anon", "authenticated", "authenticator", "postgres", "service_role"],
            "guard_passed": True},
    })
    # NOTE: c["observed_at"] is NOT overridden -- _zero_census keys every zero-width consumer
    # window to its own observed_at (OV021 coherence).
    return c


def acceptance_expects(census):
    cs = census["collection_scope"]
    return {"project_ref": census["project_ref"], "database": cs["expected_database"],
            "schemas": list(cs["schemas"]), "census_repo_sha": cs["repo_sha"],
            "role_markers": list(cs["required_role_markers"]),
            "query_bundle_sha256": cs["query_bundle_sha256"]}


def overlay_core(dimension, assignments, window=None):
    return {"dimension": dimension, "assignments": assignments,
            "observation_window": window or {"started_at": "2026-07-11T00:00:00+00:00",
                                             "ended_at": "2026-07-12T00:00:00+00:00"},
            "authority": "synthetic-test-authority", "collection_method": "synthetic-test-method"}


def write_signed(dirpath, basename, obj, priv):
    obj_bytes = canon(obj)
    path = os.path.join(dirpath, basename)
    sig_path = path + ".sig"
    with open(path, "wb") as fh:
        fh.write(obj_bytes)
    sig_bytes = sidecar_bytes_for(obj_bytes, priv)
    with open(sig_path, "wb") as fh:
        fh.write(sig_bytes)
    return path, sig_path, obj_bytes, sig_bytes


if __name__ == "__main__":
    contract = dov.load_overlay_contract()
    census = acceptance_census(["public.t1", "public.t2"])
    schema_errs = list(contract.disposition_validator.iter_errors(census))
    exp = acceptance_expects(census)
    diags = vc.check_census(census, expect_project_ref=exp["project_ref"], expect_database=exp["database"],
                            expect_schemas=exp["schemas"], expect_repo_sha=exp["census_repo_sha"],
                            require_role_markers=exp["role_markers"],
                            expect_query_bundle_sha256=exp["query_bundle_sha256"])
    priv, pub = keypair()
    msg = canon(census)
    ok, reason = ds.verify_sidecar_bytes_with_key(msg, sidecar_bytes_for(msg, priv),
                                                  ds.load_public_key_pem(pub))
    good = not schema_errs and not diags and ok
    print(f"  {'ok  ' if not schema_errs else 'FAIL'}: census fixture schema-valid ({len(schema_errs)} errors)")
    for dg in diags[:10]:
        print("    ", dg.render())
    print(f"  {'ok  ' if not diags else 'FAIL'}: census fixture acceptance-green ({len(diags)} diags)")
    print(f"  {'ok  ' if ok else 'FAIL'}: sign/verify round-trip ({reason or 'ok'})")
    print("\n=== OVERLAY PUB FIXTURES: {} ===".format("ALL PASS" if good else "FAILURES PRESENT"))
    raise SystemExit(0 if good else 1)
```

- [ ] **Step 2: Run the self-check — it must pass immediately (fixtures build on merged, tested code)**

Run (from `infra/database/schema-placement/`): `uv run --project . --locked python tests/_overlay_pub_fixtures.py`
Expected: three `ok` lines + `=== OVERLAY PUB FIXTURES: ALL PASS ===`, exit 0.
If `acceptance-green` FAILs, the printed CN diags name the field to fix — fix the FIXTURE overrides in `acceptance_census` (e.g. a `collection_scope`/`target_identity` key the schema names differently), never the frozen verifier. If `_zero_census` already emits any of the overridden top-level fields with different required keys, mirror ITS shapes.

- [ ] **Step 3: Commit**

```bash
git add infra/database/schema-placement/tests/_overlay_pub_fixtures.py
git commit -m "test(schema-placement): shared synthetic fixtures for the overlay-publication suites"
```

---

### Task 2: Author core — input validation, producing category, source reading

**Files:**
- Create: `infra/database/schema-placement/author_overlay.py` (docstring + `AuthorError` + `AO_CODES` + `_canon` + `load_input_core` + `compute_producing` + `read_source`)
- Test: `infra/database/schema-placement/tests/test_author_overlay.py` (new; `_CASES` runner)

**Interfaces:**
- Consumes: `disposition_overlay.DIMENSIONS`, `dov._PRODUCING_SHA_REQUIRED`, `dov._PRODUCING_SHA_FORBIDDEN` (frozen constants).
- Produces: `AuthorError(code, message)` — `str(e) == f"{code} author: {message}"`, attrs `.code`/`.message`; `AO_CODES` dict; `_canon(doc) -> bytes` (`json.dumps(doc, indent=2, sort_keys=True).encode("utf-8")` — THE signed-message serialization, byte-identical to `collect_disposition._serialize_snapshot`); `load_input_core(path) -> dict` (AO000/AO002); `compute_producing(dimension, gate_repo_sha, na_reason) -> (sha_or_None, reason_or_None)` (AO002 on category misuse); `read_source(source_file, na_reason, custody_locator) -> (bytes|None, reason|None, custody|None, ext|None)` (AO004/AO009).

- [ ] **Step 1: Write the failing tests (negatives FIRST)**

Create `tests/test_author_overlay.py`:

```python
"""Offline suite for author_overlay.py (overlay author/sign CLI). Script __main__ runner."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _overlay_pub_fixtures as fx  # noqa: E402
import author_overlay as ao  # noqa: E402

_CASES = []


def _err_code(fn, *a, **k):
    try:
        fn(*a, **k)
        return None
    except ao.AuthorError as exc:
        return exc.code


def _input_unreadable_AO000():
    return _err_code(ao.load_input_core, os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "core.json")) == "AO000"


def _input_not_object_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        open(p, "w").write("[1,2]")
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_missing_field_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        json.dump({"dimension": "advisor_findings"}, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_bad_dimension_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["dimension"] = "not_a_dimension"
        json.dump(core, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_empty_assignments_AO002():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        core["assignments"] = []
        json.dump(core, open(p, "w"))
        return _err_code(ao.load_input_core, p) == "AO002"


def _input_valid_core_loads():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "core.json")
        core = fx.overlay_core("advisor_findings", [{"object_id": "public.t1", "value": {}}])
        json.dump(core, open(p, "w"))
        return ao.load_input_core(p)["dimension"] == "advisor_findings"


SHA = "c" * 40


def _producing_required_uses_gate_sha():
    return ao.compute_producing("consumer_evidence.static_repo", SHA, None) == (SHA, None)


def _producing_required_rejects_reason_AO002():
    return _err_code(ao.compute_producing, "in_data_api_exposed_schema", SHA, "why") == "AO002"


def _producing_forbidden_needs_reason_AO002():
    return _err_code(ao.compute_producing, "advisor_findings", SHA, None) == "AO002"


def _producing_forbidden_null_plus_reason():
    return ao.compute_producing("consumer_evidence.runtime_logs", SHA, "logs are not a repo") == (None, "logs are not a repo")


def _producing_conditional_both_shapes():
    a = ao.compute_producing("consumer_evidence.external_clients", SHA, None) == (SHA, None)
    b = ao.compute_producing("consumer_evidence.external_clients", SHA, "no repo inventory") == (None, "no repo inventory")
    return a and b


def _source_both_supplied_AO004():
    return _err_code(ao.read_source, "/tmp/x", "reason", "custody:ref") == "AO004"


def _source_neither_supplied_AO004():
    return _err_code(ao.read_source, None, None, None) == "AO004"


def _source_custody_without_reason_AO004():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.txt")
        open(p, "w").write("x")
        return _err_code(ao.read_source, p, None, "custody:ref") == "AO004"


def _source_reason_without_custody_AO004():
    return _err_code(ao.read_source, None, "api snapshot", None) == "AO004"


def _source_unreadable_AO009_value_silent():
    try:
        ao.read_source(os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "evidence.log"), None, None)
        return False
    except ao.AuthorError as exc:
        return exc.code == "AO009" and "FileNotFoundError" in exc.message


def _source_file_read_and_ext():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "advisor.json")
        open(p, "wb").write(b'{"advisor": []}')
        data, reason, custody, ext = ao.read_source(p, None, None)
        return data == b'{"advisor": []}' and reason is None and custody is None and ext == ".json"


def _source_na_path():
    data, reason, custody, ext = ao.read_source(None, "no artifact for this source", "vault:custody/2026-07")
    return data is None and reason == "no artifact for this source" and custody == "vault:custody/2026-07" and ext is None


_CASES += [
    ("input_unreadable_AO000", _input_unreadable_AO000),
    ("input_not_object_AO002", _input_not_object_AO002),
    ("input_missing_field_AO002", _input_missing_field_AO002),
    ("input_bad_dimension_AO002", _input_bad_dimension_AO002),
    ("input_empty_assignments_AO002", _input_empty_assignments_AO002),
    ("input_valid_core_loads", _input_valid_core_loads),
    ("producing_required_uses_gate_sha", _producing_required_uses_gate_sha),
    ("producing_required_rejects_reason_AO002", _producing_required_rejects_reason_AO002),
    ("producing_forbidden_needs_reason_AO002", _producing_forbidden_needs_reason_AO002),
    ("producing_forbidden_null_plus_reason", _producing_forbidden_null_plus_reason),
    ("producing_conditional_both_shapes", _producing_conditional_both_shapes),
    ("source_both_supplied_AO004", _source_both_supplied_AO004),
    ("source_neither_supplied_AO004", _source_neither_supplied_AO004),
    ("source_custody_without_reason_AO004", _source_custody_without_reason_AO004),
    ("source_reason_without_custody_AO004", _source_reason_without_custody_AO004),
    ("source_unreadable_AO009_value_silent", _source_unreadable_AO009_value_silent),
    ("source_file_read_and_ext", _source_file_read_and_ext),
    ("source_na_path", _source_na_path),
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
    print("\n=== AUTHOR OVERLAY SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
```

- [ ] **Step 2: Run to verify RED**

Run: `uv run --project . --locked python tests/test_author_overlay.py`
Expected: traceback `ModuleNotFoundError: No module named 'author_overlay'` (an import-time abort IS the red run).

- [ ] **Step 3: Write the minimal implementation**

Create `author_overlay.py`:

```python
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
```

- [ ] **Step 4: Run to verify GREEN**

Run: `uv run --project . --locked python tests/test_author_overlay.py`
Expected: 18 `ok` lines, `=== AUTHOR OVERLAY SUITE: ALL PASS ===`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/author_overlay.py infra/database/schema-placement/tests/test_author_overlay.py
git commit -m "feat(schema-placement): overlay author core -- input validation, producing categories, value-silent source intake (TDD)"
```

---

### Task 3: Author assemble + validate-the-signed-bytes

**Files:**
- Modify: `infra/database/schema-placement/author_overlay.py` (append `assemble_overlay`, `validate_assembled`)
- Test: `infra/database/schema-placement/tests/test_author_overlay.py` (append cases)

**Interfaces:**
- Consumes: Task 2's names; `dov.parse_overlay`, `dov.validate_overlay`, `dov.check_binding`, `dov.check_observation_window`, `dov.check_target`, `dov.check_conflict`, `dov.load_overlay_contract`, `dov._parse_iso`.
- Produces: `assemble_overlay(core, *, census, census_sha256, contract, producing, source_hash, source_hash_reason, source_locator, captured_at_iso) -> dict`; `validate_assembled(message: bytes, *, census, census_bytes_sha, contract, expect_project_ref, now) -> list[(code, locus, msg)]` — round-trips the EXACT serialized bytes through `parse_overlay`, then the consumer's per-artifact checks + OV010 future-half (`captured_at <= now`) + the intra-overlay flat OV007; schema failure SHORT-CIRCUITS.

- [ ] **Step 1: Append the failing tests (negatives first)**

Append to `tests/test_author_overlay.py` (before the `__main__` block; add imports at the top of the appended section):

```python
import hashlib  # noqa: E402

import disposition_overlay as dov  # noqa: E402

NOW = dov._parse_iso("2026-07-12T12:00:00+00:00")


def _assembled(dimension="in_data_api_exposed_schema", value=None, window=None,
               captured="2026-07-12T06:00:00+00:00", oids=("public.t1", "public.t2"),
               assignments=None):
    census = fx.acceptance_census(list(oids))
    census_bytes = fx.canon(census)
    census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core(
        dimension,
        assignments or [{"object_id": "public.t1", "value": value or {"state": "observed", "value": False}}],
        window=window)
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=("d" * 40, None), source_hash="e" * 64,
                              source_hash_reason=None, source_locator="evidence/source/x.source.json",
                              captured_at_iso=captured)
    return ao._canon(doc), census, census_sha, contract


def _validate(message, census, census_sha, contract):
    return ao.validate_assembled(message, census=census, census_bytes_sha=census_sha,
                                 contract=contract, expect_project_ref=fx.PROJECT_REF, now=NOW)


def _assembled_clean_validates():
    m, c, s, k = _assembled()
    return _validate(m, c, s, k) == []


def _bad_window_yields_OV009():
    m, c, s, k = _assembled(window={"started_at": "2026-07-12T00:00:00+00:00",
                                    "ended_at": "2026-07-11T00:00:00+00:00"})
    return any(d[0] == "OV009" for d in _validate(m, c, s, k))


def _future_captured_yields_OV010():
    m, c, s, k = _assembled(captured="2027-01-01T00:00:00+00:00")
    return any(d[0] == "OV010" for d in _validate(m, c, s, k))


def _unknown_object_yields_OV005():
    m, c, s, k = _assembled(oids=("public.t1",),
                            assignments=[{"object_id": "public.nope",
                                          "value": {"state": "observed", "value": False}}])
    return any(d[0] == "OV005" for d in _validate(m, c, s, k))


def _intra_duplicate_yields_OV007():
    a = {"object_id": "public.t1", "value": {"state": "observed", "value": False}}
    m, c, s, k = _assembled(assignments=[a, dict(a)])
    return any(d[0] == "OV007" for d in _validate(m, c, s, k))


def _wrong_value_shape_yields_OV008_only():
    # advisor_findings requires observed_advisor_array; an observed_bool must FAIL schema and
    # SHORT-CIRCUIT (no binding/target diags on a schema-invalid doc).
    m, c, s, k = _assembled(dimension="advisor_findings", value={"state": "observed", "value": True})
    # producing: advisor is FORBIDDEN -- rebuild with null+reason so ONLY the value shape is wrong.
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census); census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core("advisor_findings",
                           [{"object_id": "public.t1", "value": {"state": "observed", "value": True}}])
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=(None, "advisor API snapshot"),
                              source_hash="e" * 64, source_hash_reason=None,
                              source_locator="evidence/source/x.source.json",
                              captured_at_iso="2026-07-12T06:00:00+00:00")
    diags = _validate(ao._canon(doc), census, census_sha, contract)
    return diags and all(d[0] == "OV008" for d in diags)


def _na_reason_fields_assemble_green():
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census); census_sha = hashlib.sha256(census_bytes).hexdigest()
    contract = dov.load_overlay_contract()
    core = fx.overlay_core("advisor_findings",
                           [{"object_id": "public.t1", "value": {"state": "observed", "value": ["lint:ok"]}}])
    doc = ao.assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                              producing=(None, "advisor API snapshot, not a repo"),
                              source_hash=None, source_hash_reason="no committed artifact",
                              source_locator="vault:custody/2026-07",
                              captured_at_iso="2026-07-12T06:00:00+00:00")
    ok_fields = (doc["producing_repo_sha"] is None
                 and doc["producing_repo_sha_not_applicable_reason"] == "advisor API snapshot, not a repo"
                 and doc["source_hash"] is None
                 and doc["source_hash_not_applicable_reason"] == "no committed artifact")
    return ok_fields and _validate(ao._canon(doc), census, census_sha, contract) == []


_CASES += [
    ("assembled_clean_validates", _assembled_clean_validates),
    ("bad_window_yields_OV009", _bad_window_yields_OV009),
    ("future_captured_yields_OV010", _future_captured_yields_OV010),
    ("unknown_object_yields_OV005", _unknown_object_yields_OV005),
    ("intra_duplicate_yields_OV007", _intra_duplicate_yields_OV007),
    ("wrong_value_shape_yields_OV008_only", _wrong_value_shape_yields_OV008_only),
    ("na_reason_fields_assemble_green", _na_reason_fields_assemble_green),
]
```

- [ ] **Step 2: Run to verify RED**

Run: `uv run --project . --locked python tests/test_author_overlay.py`
Expected: the 7 new cases FAIL with `EXC module 'author_overlay' has no attribute 'assemble_overlay'`; the 18 Task-2 cases stay `ok`.

- [ ] **Step 3: Implement**

Append to `author_overlay.py`:

```python
def assemble_overlay(core, *, census, census_sha256, contract, producing, source_hash,
                     source_hash_reason, source_locator, captured_at_iso):
    """Mechanical binder (spec 3.3): every binding value is COMPUTED by the caller pipeline;
    the operator core contributes semantics only. NA-reason fields appear IFF the value is null
    (the OV012/OV019 IFF shapes)."""
    doc = {
        "kind": "evidence_overlay", "overlay_version": "1",
        "dimension": core["dimension"],
        "source_type": dov.DIMENSIONS[core["dimension"]][1],
        "authority": core["authority"], "collection_method": core["collection_method"],
        "source_locator": source_locator, "source_hash": source_hash,
        "base_snapshot_sha256": census_sha256,
        "disposition_schema_sha256": contract.disp_sha256,
        "overlay_schema_sha256": contract.overlay_sha256,
        "project_ref": census.get("project_ref"),
        "captured_at": captured_at_iso,
        "observation_window": core["observation_window"],
        "producing_repo_sha": producing[0],
        "assignments": core["assignments"],
    }
    if source_hash is None:
        doc["source_hash_not_applicable_reason"] = source_hash_reason
    if producing[0] is None:
        doc["producing_repo_sha_not_applicable_reason"] = producing[1]
    for k in ("operator_identity", "attestation_ref"):
        if k in core:
            doc[k] = core[k]
    return doc


def validate_assembled(message, *, census, census_bytes_sha, contract, expect_project_ref, now):
    """Validate the EXACT signed bytes (spec 3.5 + round-1 DAG-F5): round-trip through
    parse_overlay so the dup-key/non-finite guard covers what is signed, then run the consumer's
    per-artifact checks, the OV010 future-half, and the intra-overlay flat OV007. Any schema
    failure SHORT-CIRCUITS (mirrors load_and_merge -- a schema-invalid doc is not safe to
    bind/window/target)."""
    loc = "author:assembled"
    try:
        doc = dov.parse_overlay(message)
    except ValueError as exc:
        return [("OV008", loc, f"serialized overlay does not re-parse ({exc})")]
    if not isinstance(doc, dict):
        return [("OV008", loc, f"serialized overlay is not a JSON object (got {type(doc).__name__})")]
    diags = dov.validate_overlay(doc, contract.overlay_validator)
    if diags:
        return diags
    diags += dov.check_binding(doc, census_sha256=census_bytes_sha,
                               census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref,
                               on_disk_disp_sha=contract.disp_sha256,
                               on_disk_overlay_sha=contract.overlay_sha256)
    diags += dov.check_observation_window(doc, now)
    try:
        if dov._parse_iso(doc["captured_at"]) > now:
            diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at is in the future"))
    except (KeyError, ValueError, TypeError):
        diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at unparseable"))
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}
    diags += dov.check_target(doc, rel_index)
    diags += dov.check_conflict([(doc.get("dimension"), a.get("object_id"))
                                 for a in doc.get("assignments", [])])
    return diags
```

- [ ] **Step 4: Run to verify GREEN** — `uv run --project . --locked python tests/test_author_overlay.py`; Expected: 25 `ok`, ALL PASS, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/author_overlay.py infra/database/schema-placement/tests/test_author_overlay.py
git commit -m "feat(schema-placement): author assemble + validate-the-signed-bytes (consumer checks + OV010 future-half + intra OV007)"
```

---

### Task 4: Author census acceptance + signer parity + in-memory sidecar verify

**Files:**
- Modify: `infra/database/schema-placement/author_overlay.py` (append `accept_census`, `load_signing_key`, `build_and_check_sidecar`)
- Test: `infra/database/schema-placement/tests/test_author_overlay.py` (append cases)

**Interfaces:**
- Consumes: `ds.verify_sidecar_bytes_with_key`, `ds.load_private_key_pem`, `ds.public_key_fingerprint`, `ds.build_sig_sidecar`, `vc.load_snapshot_from_bytes`, `vc.check_census`, `dt.resolve_pinned_key` / `ResolvedSigner` (`.public_key`, `.spki_sha256`, `.key_id`).
- Produces: `accept_census(census_bytes, sig_bytes, *, signer, expects) -> dict` — sig verify (AO001) → `vc.load_snapshot_from_bytes` parse (AO000) → explicit AO003 project-ref assert → FULL `vc.check_census` (AO011, prints leading CN diags); `expects` is the `acceptance_expects` dict shape; `load_signing_key(env_name, signer) -> private_key` (AO007: unset / invalid PEM / fingerprint mismatch — all value-silent); `build_and_check_sidecar(message, private_key, signer) -> sidecar_bytes` (AO012).

- [ ] **Step 1: Append the failing tests (negatives first)**

Append to `tests/test_author_overlay.py`:

```python
import disposition_signing as ds  # noqa: E402
import disposition_trust as dt  # noqa: E402


def _signer_and_census(tmpdir, priv=None, pub=None):
    priv2, pub2 = fx.keypair()
    priv, pub = priv or priv2, pub or pub2
    keys_dir = fx.write_keys_dir(tmpdir, pub)
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)):
        signer, reason = dt.resolve_pinned_key(keys_dir, fx.KEY_ID)
    assert signer is not None, reason
    census = fx.acceptance_census(["public.t1"])
    census_bytes = fx.canon(census)
    sig_bytes = fx.sidecar_bytes_for(census_bytes, priv)
    return signer, census, census_bytes, sig_bytes, priv


def _census_accepts_green():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        got = ao.accept_census(cb, sb, signer=signer, expects=fx.acceptance_expects(census))
        return got["project_ref"] == fx.PROJECT_REF


def _tampered_census_AO001():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        bad = cb[:-2] + b" }"
        return _err_code(ao.accept_census, bad, sb, signer=signer,
                         expects=fx.acceptance_expects(census)) == "AO001"


def _foreign_signed_census_AO001():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, _sb, _ = _signer_and_census(d)
        foreign_priv, _fp = fx.keypair()
        foreign_sig = fx.sidecar_bytes_for(cb, foreign_priv)
        return _err_code(ao.accept_census, cb, foreign_sig, signer=signer,
                         expects=fx.acceptance_expects(census)) == "AO001"


def _project_mismatch_AO003():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        expects = fx.acceptance_expects(census)
        expects["project_ref"] = "otherproject"
        return _err_code(ao.accept_census, cb, sb, signer=signer, expects=expects) == "AO003"


def _out_of_scope_census_AO011():
    with tempfile.TemporaryDirectory() as d:
        signer, census, cb, sb, _ = _signer_and_census(d)
        expects = fx.acceptance_expects(census)
        expects["schemas"] = ["public", "extra_schema"]  # CN005 inside check_census
        return _err_code(ao.accept_census, cb, sb, signer=signer, expects=expects) == "AO011"


def _key_env_unset_AO007():
    os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
    with tempfile.TemporaryDirectory() as d:
        signer, *_ = _signer_and_census(d)
        return _err_code(ao.load_signing_key, "TEST_SIGNING_KEY_XYZ", signer) == "AO007"


def _key_invalid_pem_AO007_value_silent():
    os.environ["TEST_SIGNING_KEY_XYZ"] = "not-a-pem"
    try:
        with tempfile.TemporaryDirectory() as d:
            signer, *_ = _signer_and_census(d)
            try:
                ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
                return False
            except ao.AuthorError as exc:
                return exc.code == "AO007" and "not-a-pem" not in str(exc)
    finally:
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


def _key_wrong_signer_AO007():
    wrong_priv, _ = fx.keypair()  # valid Ed25519 key, NOT the pinned signer
    os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(wrong_priv)
    try:
        with tempfile.TemporaryDirectory() as d:
            signer, *_ = _signer_and_census(d)
            try:
                ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
                return False
            except ao.AuthorError as exc:
                return exc.code == "AO007" and "wrong signer" in exc.message
    finally:
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


def _key_parity_green_and_sidecar_verifies():
    with tempfile.TemporaryDirectory() as d:
        signer, _census, cb, _sb, priv = _signer_and_census(d)
        os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(priv)
        try:
            key = ao.load_signing_key("TEST_SIGNING_KEY_XYZ", signer)
            sidecar = ao.build_and_check_sidecar(b"message-bytes", key, signer)
            ok, _ = ds.verify_sidecar_bytes_with_key(b"message-bytes", sidecar, signer.public_key)
            return ok
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)


_CASES += [
    ("census_accepts_green", _census_accepts_green),
    ("tampered_census_AO001", _tampered_census_AO001),
    ("foreign_signed_census_AO001", _foreign_signed_census_AO001),
    ("project_mismatch_AO003", _project_mismatch_AO003),
    ("out_of_scope_census_AO011", _out_of_scope_census_AO011),
    ("key_env_unset_AO007", _key_env_unset_AO007),
    ("key_invalid_pem_AO007_value_silent", _key_invalid_pem_AO007_value_silent),
    ("key_wrong_signer_AO007", _key_wrong_signer_AO007),
    ("key_parity_green_and_sidecar_verifies", _key_parity_green_and_sidecar_verifies),
]
```

- [ ] **Step 2: Run to verify RED** — Expected: the 9 new cases FAIL (`no attribute 'accept_census'`); prior 25 stay `ok`.

- [ ] **Step 3: Implement**

Append to `author_overlay.py`:

```python
def accept_census(census_bytes, sig_bytes, *, signer, expects):
    """FULL census acceptance, not just signature (spec 3.4; operator round-1 #2). Order:
    signature over the exact bytes -> the census gate's own strict parse -> explicit AO003 ->
    check_census. The bytes verified ARE the bytes parsed (read-once discipline)."""
    ok, reason = ds.verify_sidecar_bytes_with_key(census_bytes, sig_bytes, signer.public_key)
    if not ok:
        raise AuthorError("AO001", f"census signature verification failed: {reason}")
    try:
        census = vc.load_snapshot_from_bytes(census_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AuthorError("AO000", f"cannot parse census ({type(exc).__name__})")
    if not isinstance(census, dict):
        raise AuthorError("AO000", f"census is not a JSON object (got {type(census).__name__})")
    if census.get("project_ref") != expects["project_ref"]:
        raise AuthorError("AO003", f"census project_ref {census.get('project_ref')!r} != --expect-project-ref {expects['project_ref']!r}")
    diags = vc.check_census(census,
                            expect_project_ref=expects["project_ref"],
                            expect_database=expects["database"],
                            expect_schemas=expects["schemas"],
                            expect_repo_sha=expects["census_repo_sha"],
                            require_role_markers=expects["role_markers"],
                            expect_query_bundle_sha256=expects["query_bundle_sha256"])
    if diags:
        head = "; ".join(d.render() for d in diags[:5])
        more = f" (+{len(diags) - 5} more)" if len(diags) > 5 else ""
        raise AuthorError("AO011", f"base census failed acceptance: {head}{more}")
    return census


def load_signing_key(env_name, signer):
    """Signer parity (spec 3.5; operator round-1 #5). Value-silent: the PEM never appears in any
    message; explicit coded checks, never a bare assert."""
    pem = os.environ.get(env_name)
    if not pem:
        raise AuthorError("AO007", f"env var {env_name} is not set (the signing key is never passed on the command line)")
    try:
        key = ds.load_private_key_pem(pem.encode("utf-8"))
    except Exception:  # noqa: BLE001 -- never surface key material
        raise AuthorError("AO007", f"{env_name} is not a valid Ed25519 private key PEM")
    fp = ds.public_key_fingerprint(key.public_key())
    if fp != signer.spki_sha256:
        raise AuthorError("AO007", f"signing key SPKI {fp[:12]}... is a valid Ed25519 key but the wrong signer (pinned {signer.key_id!r})")
    return key


def build_and_check_sidecar(message, private_key, signer):
    """Sign, then verify IN MEMORY against the pinned public key BEFORE anything is written
    (spec 3.5, AO012). Returns the exact sidecar bytes to publish."""
    sidecar_bytes = _canon(ds.build_sig_sidecar(message, private_key))
    ok, reason = ds.verify_sidecar_bytes_with_key(message, sidecar_bytes, signer.public_key)
    if not ok:
        raise AuthorError("AO012", f"in-memory sidecar verification failed: {reason}")
    return sidecar_bytes
```

- [ ] **Step 4: Run to verify GREEN** — 34 `ok`, ALL PASS, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/author_overlay.py infra/database/schema-placement/tests/test_author_overlay.py
git commit -m "feat(schema-placement): author full census acceptance + signer parity + in-memory sidecar verify"
```

---

### Task 5: Author publish (atomic, no-clobber), canonical names, provenance gate, `main()`

**Files:**
- Modify: `infra/database/schema-placement/author_overlay.py` (append `_write_bytes_atomic_noclobber`, `publish_set`, `canonical_names`, `main`, `__main__` guard)
- Test: `infra/database/schema-placement/tests/test_author_overlay.py` (append cases)

**Interfaces:**
- Consumes: everything above; `dp.git_head_sha`, `dp.git_worktree_clean` (tests patch BOTH — the collector-test pattern; no runtime bypass exists).
- Produces: `_write_bytes_atomic_noclobber(path, data)` (temp+fsync+`os.link`, `finally` unlink — the D3 replica; `FileExistsError` propagates); `publish_set(entries)` — ordered `[(path, bytes), ...]`, wraps failures as AO008; `canonical_names(dimension, census_sha256, captured_dt, out_dir, source_ext) -> dict` with keys `overlay, sig, source (None when source_ext is None), locator (None when no source), stamp` — first candidate without suffix, then `-01..-99` (AO008 exhausted); `main(argv=None) -> int` (0 published / 2 refused).

**`main()` argv (exact):** `--census`, `--census-sig`, `--key-id`, `--keys-dir` (default `dt.DEFAULT_KEYS_DIR`), `--input`, `--source-file`, `--source-hash-na-reason`, `--source-custody-locator`, `--producing-repo-sha-na-reason`, `--expect-gate-repo-sha` (required), `--expect-project-ref` (required), `--expect-database` (required), `--expect-schemas` (required, comma-separated), `--expect-census-repo-sha` (required), `--require-role-markers` (default `anon,authenticated,service_role`), `--expect-query-bundle-sha256` (required), `--out-dir` (default `os.path.join(SP_DIR, "evidence")`), `--signing-key-env` (default `DISPOSITION_SIGNING_KEY`).

**`main()` order (spec 3.2–3.5; D4):** (1) AO010 provenance gate — `dp.git_head_sha(SP_DIR)` == `--expect-gate-repo-sha` AND `dp.git_worktree_clean(SP_DIR)`, BEFORE the signing key or ANY evidence input is read; (2) `dt.resolve_pinned_key` → AO013; (3) read census+sig bytes ONCE (AO000) → `accept_census`; (4) `load_input_core` + `read_source` + `compute_producing(core["dimension"], head, ...)`; (5) `dov.load_overlay_contract()` (OverlayRegistryError → AO000) + ONE clock read `captured_dt = datetime.now(timezone.utc).replace(microsecond=0)` (drives BOTH `captured_at` and the path stamp) + `canonical_names`; (6) `assemble_overlay` → `_canon` → `validate_assembled` (any diag: print each `f"{code} {locus}: {msg}"` to stderr, then AO005); (7) `load_signing_key` → `build_and_check_sidecar`; (8) `publish_set`: source record first (when present), then sidecar, then overlay; (9) green line `=== OVERLAY AUTHORED: <dimension> n=<len(assignments)> -> <overlay path> (census <sha12>, signer <key_id>) ===`, return 0. All `AuthorError` → print `str(exc)` to stderr, return 2.

- [ ] **Step 1: Append the failing tests (negatives + partial-publication + e2e green)**

```python
import contextlib  # noqa: E402
import io  # noqa: E402

import disposition_provenance as dp  # noqa: E402

GATE_SHA = "f" * 40


@contextlib.contextmanager
def _provenance(head=GATE_SHA, clean=True):
    orig_head, orig_clean = dp.git_head_sha, dp.git_worktree_clean
    dp.git_head_sha = lambda _d: head
    dp.git_worktree_clean = lambda _d: clean
    try:
        yield
    finally:
        dp.git_head_sha, dp.git_worktree_clean = orig_head, orig_clean


def _noclobber_refuses_existing():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.json")
        open(p, "wb").write(b"old")
        try:
            ao._write_bytes_atomic_noclobber(p, b"new")
            return False
        except FileExistsError:
            return open(p, "rb").read() == b"old" and not [f for f in os.listdir(d) if f.startswith(".")]


def _publish_set_partial_failure_AO008():
    # sidecar target pre-exists: source publishes, sidecar refuses -> AO008; overlay NEVER written;
    # no temp residue anywhere (the finally-unlink).
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "source", "r.source.txt")
        sig = os.path.join(d, "o.json.sig")
        ovl = os.path.join(d, "o.json")
        open(sig, "wb").write(b"squatter")
        code = _err_code(ao.publish_set, [(src, b"S"), (sig, b"G"), (ovl, b"O")])
        residue = [f for f in os.listdir(d) if f.startswith(".")]
        return (code == "AO008" and os.path.exists(src) and not os.path.exists(ovl)
                and open(sig, "rb").read() == b"squatter" and not residue)


def _canonical_names_counter():
    with tempfile.TemporaryDirectory() as d:
        from datetime import datetime, timezone
        dt_ = datetime(2026, 7, 12, 6, 0, 0, tzinfo=timezone.utc)
        first = ao.canonical_names("consumer_evidence.static_repo", "ab" * 32, dt_, d, ".txt")
        base = "overlay-consumer_evidence_static_repo-abababababab-20260712T060000Z"
        if os.path.basename(first["overlay"]) != base + ".json":
            return False
        if first["locator"] != "evidence/source/" + base + ".source.txt":
            return False
        open(first["overlay"], "wb").write(b"x")  # occupy -> next call must pick -01
        second = ao.canonical_names("consumer_evidence.static_repo", "ab" * 32, dt_, d, ".txt")
        return os.path.basename(second["overlay"]) == base + "-01.json"


def _main_env(d, *, dimension="consumer_evidence.static_repo", with_source=True):
    """Build a full green argv + env for main(); returns (argv, cleanup_ctx, signer_pub_fp)."""
    priv, pub = fx.keypair()
    keys_dir = fx.write_keys_dir(d, pub)
    census = fx.acceptance_census(["public.t1"])
    cpath, cs_path, _cb, _sb = fx.write_signed(d, "census-prod-fixture.json", census, priv)
    core = fx.overlay_core(dimension, [{"object_id": "public.t1",
                                        "value": {"state": "observed", "found_consumers": 0, "ref": "scan:t"}}])
    ipath = os.path.join(d, "core.json")
    json.dump(core, open(ipath, "w"))
    out_dir = os.path.join(d, "out")
    os.makedirs(out_dir, exist_ok=True)
    exp = fx.acceptance_expects(census)
    argv = ["--census", cpath, "--census-sig", cs_path, "--key-id", fx.KEY_ID, "--keys-dir", keys_dir,
            "--input", ipath, "--expect-gate-repo-sha", GATE_SHA,
            "--expect-project-ref", exp["project_ref"], "--expect-database", exp["database"],
            "--expect-schemas", ",".join(exp["schemas"]), "--expect-census-repo-sha", exp["census_repo_sha"],
            "--require-role-markers", ",".join(exp["role_markers"]),
            "--expect-query-bundle-sha256", exp["query_bundle_sha256"],
            "--out-dir", out_dir, "--signing-key-env", "TEST_SIGNING_KEY_XYZ"]
    if with_source:
        spath = os.path.join(d, "scan-output.txt")
        open(spath, "wb").write(b"public.t1: 0 refs\n")
        argv += ["--source-file", spath]
    os.environ["TEST_SIGNING_KEY_XYZ"] = fx.priv_pem(priv)
    return argv, pub, out_dir


def _run_main(argv, pub):
    err = io.StringIO()
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)), contextlib.redirect_stderr(err):
        rc = ao.main(argv)
    return rc, err.getvalue()


def _main_green_publishes_triple():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, out_dir = _main_env(d)
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        if rc != 0:
            print("    stderr:", err)
            return False
        names = sorted(os.listdir(out_dir))
        overlays = [n for n in names if n.endswith(".json")]
        sigs = [n for n in names if n.endswith(".json.sig")]
        sources = os.listdir(os.path.join(out_dir, "source"))
        if not (len(overlays) == 1 and len(sigs) == 1 and len(sources) == 1):
            return False
        doc = json.load(open(os.path.join(out_dir, overlays[0])))
        return (doc["producing_repo_sha"] == GATE_SHA
                and doc["source_locator"] == "evidence/source/" + sources[0]
                and doc["source_hash"] is not None)


def _main_dirty_worktree_AO010_before_key():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        os.environ.pop("TEST_SIGNING_KEY_XYZ", None)  # key ABSENT: AO010 must fire first anyway
        with _provenance(clean=False):
            rc, err = _run_main(argv, pub)
        return rc == 2 and "AO010" in err and "AO007" not in err


def _main_wrong_head_AO010():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        try:
            with _provenance(head="0" * 40):
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO010" in err


def _main_unpinned_key_id_AO013():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        argv[argv.index("--key-id") + 1] = "not-a-pinned-signer"
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO013" in err


def _main_bad_assembly_refuses_to_sign_AO005():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, out_dir = _main_env(d)
        ipath = argv[argv.index("--input") + 1]
        core = json.load(open(ipath))
        core["observation_window"] = {"started_at": "2026-07-12T00:00:00+00:00",
                                      "ended_at": "2026-07-11T00:00:00+00:00"}  # OV009
        json.dump(core, open(ipath, "w"))
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        published = os.listdir(out_dir)
        published_src = os.listdir(os.path.join(out_dir, "source")) if os.path.isdir(os.path.join(out_dir, "source")) else []
        return rc == 2 and "OV009" in err and "AO005" in err and published == [] and published_src == []


def _main_value_silent_key_never_echoed():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _main_env(d)
        os.environ["TEST_SIGNING_KEY_XYZ"] = "-----BEGIN PRIVATE KEY-----\nGARBAGE\n-----END PRIVATE KEY-----"
        try:
            with _provenance():
                rc, err = _run_main(argv, pub)
        finally:
            os.environ.pop("TEST_SIGNING_KEY_XYZ", None)
        return rc == 2 and "AO007" in err and "GARBAGE" not in err


_CASES += [
    ("noclobber_refuses_existing", _noclobber_refuses_existing),
    ("publish_set_partial_failure_AO008", _publish_set_partial_failure_AO008),
    ("canonical_names_counter", _canonical_names_counter),
    ("main_green_publishes_triple", _main_green_publishes_triple),
    ("main_dirty_worktree_AO010_before_key", _main_dirty_worktree_AO010_before_key),
    ("main_wrong_head_AO010", _main_wrong_head_AO010),
    ("main_unpinned_key_id_AO013", _main_unpinned_key_id_AO013),
    ("main_bad_assembly_refuses_to_sign_AO005", _main_bad_assembly_refuses_to_sign_AO005),
    ("main_value_silent_key_never_echoed", _main_value_silent_key_never_echoed),
]
```

- [ ] **Step 2: Run to verify RED** — the 9 new cases FAIL (`no attribute '_write_bytes_atomic_noclobber'` / `'main'`); prior 34 stay `ok`.

- [ ] **Step 3: Implement**

Append to `author_overlay.py`:

```python
def _write_bytes_atomic_noclobber(path, data):
    """D3 replica of collect_disposition._write_bytes_atomic's NO-CLOBBER branch, verbatim
    semantics: temp sibling + flush + fsync, os.link (atomic create-if-absent; FileExistsError if
    present -- no check-then-act race), finally-unlink of the temp. Never os.rename/os.replace."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp = os.path.join(directory, f".{os.path.basename(path)}.tmp-{os.getpid()}")
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.link(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def publish_set(entries):
    """Ordered no-clobber publish (spec 3.5): source record first (when present), then sidecar,
    then overlay -- a partial failure can never leave an overlay without its signature."""
    for path, data in entries:
        try:
            _write_bytes_atomic_noclobber(path, data)
        except FileExistsError:
            raise AuthorError("AO008", f"refusing to overwrite existing {path} (no-clobber)")
        except OSError as exc:
            raise AuthorError("AO008", f"publish failed for {path} ({type(exc).__name__})")


def canonical_names(dimension, census_sha256, captured_dt, out_dir, source_ext):
    """Spec 3.6 naming: overlay-<dim-slug>-<census12>-<UTC>[-NN].json (+ .json.sig), source record
    under source/ with .source.<ext>. The stamp derives from the SAME captured_dt written into the
    doc (single clock). First candidate has no suffix; -01..-99 on collision; AO008 when exhausted."""
    slug = dimension.replace(".", "_")
    stamp = captured_dt.strftime("%Y%m%dT%H%M%SZ")
    for n in range(100):
        suffix = "" if n == 0 else f"-{n:02d}"
        base = f"overlay-{slug}-{census_sha256[:12]}-{stamp}{suffix}"
        overlay = os.path.join(out_dir, base + ".json")
        sig = overlay + ".sig"
        source = os.path.join(out_dir, "source", base + ".source" + source_ext) if source_ext is not None else None
        candidates = [p for p in (overlay, sig, source) if p]
        if not any(os.path.exists(p) for p in candidates):
            locator = ("evidence/source/" + os.path.basename(source)) if source else None
            return {"overlay": overlay, "sig": sig, "source": source, "locator": locator,
                    "stamp": stamp + suffix}
    raise AuthorError("AO008", "no free canonical name (suffixes -01..-99 exhausted for this census+dimension+second)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Author + sign ONE per-dimension evidence overlay bound to a signed census.")
    ap.add_argument("--census", required=True)
    ap.add_argument("--census-sig", required=True, dest="census_sig")
    ap.add_argument("--key-id", required=True, dest="key_id")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir")
    ap.add_argument("--input", required=True, help="operator-semantics overlay core JSON (spec 3.1)")
    ap.add_argument("--source-file", default=None, dest="source_file")
    ap.add_argument("--source-hash-na-reason", default=None, dest="source_hash_na_reason")
    ap.add_argument("--source-custody-locator", default=None, dest="source_custody_locator")
    ap.add_argument("--producing-repo-sha-na-reason", default=None, dest="producing_na_reason")
    ap.add_argument("--expect-gate-repo-sha", required=True, dest="expect_gate_repo_sha",
                    help="REQUIRED (D4): the author's clean merged-main HEAD; asserted before any read.")
    ap.add_argument("--expect-project-ref", required=True, dest="expect_project_ref")
    ap.add_argument("--expect-database", required=True, dest="expect_database")
    ap.add_argument("--expect-schemas", required=True, dest="expect_schemas")
    ap.add_argument("--expect-census-repo-sha", required=True, dest="expect_census_repo_sha")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role", dest="require_role_markers")
    ap.add_argument("--expect-query-bundle-sha256", required=True, dest="expect_query_bundle_sha256")
    ap.add_argument("--out-dir", default=os.path.join(SP_DIR, "evidence"), dest="out_dir")
    ap.add_argument("--signing-key-env", default="DISPOSITION_SIGNING_KEY", dest="signing_key_env")
    args = ap.parse_args(argv)

    try:
        # 1. Provenance gate FIRST (D4): before the signing key or ANY evidence input is read.
        head = dp.git_head_sha(SP_DIR)
        if not head or not dp.git_worktree_clean(SP_DIR):
            raise AuthorError("AO010", "author checkout is DIRTY or HEAD undeterminable -- run from a clean merged-main checkout")
        if head != args.expect_gate_repo_sha:
            raise AuthorError("AO010", f"git HEAD {head[:12]} != --expect-gate-repo-sha {args.expect_gate_repo_sha[:12]}")
        # 2. Pinned signer.
        signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
        if signer is None:
            raise AuthorError("AO013", kreason)
        # 3. Census bytes read ONCE + FULL acceptance.
        try:
            with open(args.census, "rb") as fh:
                census_bytes = fh.read()
            with open(args.census_sig, "rb") as fh:
                census_sig_bytes = fh.read()
        except OSError as exc:
            raise AuthorError("AO000", f"cannot read census/sig ({type(exc).__name__})")
        expects = {"project_ref": args.expect_project_ref, "database": args.expect_database,
                   "schemas": [s.strip() for s in args.expect_schemas.split(",") if s.strip()],
                   "census_repo_sha": args.expect_census_repo_sha,
                   "role_markers": [s.strip() for s in args.require_role_markers.split(",") if s.strip()],
                   "query_bundle_sha256": args.expect_query_bundle_sha256}
        census = accept_census(census_bytes, census_sig_bytes, signer=signer, expects=expects)
        # 4. Operator semantics + source + producing category.
        core = load_input_core(args.input)
        source_bytes, source_reason, custody, source_ext = read_source(
            args.source_file, args.source_hash_na_reason, args.source_custody_locator)
        producing = compute_producing(core["dimension"], head, args.producing_na_reason)
        # 5. Contract + ONE clock read + canonical names.
        try:
            contract = dov.load_overlay_contract()
        except dov.OverlayRegistryError as exc:
            raise AuthorError("AO000", f"cannot build overlay contract ({type(exc).__name__})")
        captured_dt = datetime.now(timezone.utc).replace(microsecond=0)
        census_sha = hashlib.sha256(census_bytes).hexdigest()
        names = canonical_names(core["dimension"], census_sha, captured_dt, args.out_dir, source_ext)
        source_hash = hashlib.sha256(source_bytes).hexdigest() if source_bytes is not None else None
        source_locator = names["locator"] if source_bytes is not None else custody
        # 6. Assemble -> validate the EXACT signed bytes.
        doc = assemble_overlay(core, census=census, census_sha256=census_sha, contract=contract,
                               producing=producing, source_hash=source_hash,
                               source_hash_reason=source_reason, source_locator=source_locator,
                               captured_at_iso=captured_dt.isoformat())
        message = _canon(doc)
        diags = validate_assembled(message, census=census, census_bytes_sha=census_sha,
                                   contract=contract, expect_project_ref=args.expect_project_ref,
                                   now=captured_dt)
        if diags:
            for code, locus, msg in diags:
                print(f"{code} {locus}: {msg}", file=sys.stderr)
            raise AuthorError("AO005", f"assembled overlay failed {len(diags)} consumer check(s) -- refusing to sign")
        # 7. Signer parity + in-memory-verified sidecar; 8. ordered no-clobber publish.
        private_key = load_signing_key(args.signing_key_env, signer)
        sidecar_bytes = build_and_check_sidecar(message, private_key, signer)
        entries = ([(names["source"], source_bytes)] if source_bytes is not None else [])
        entries += [(names["sig"], sidecar_bytes), (names["overlay"], message)]
        publish_set(entries)
    except AuthorError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"=== OVERLAY AUTHORED: {core['dimension']} n={len(core['assignments'])} -> {names['overlay']} "
          f"(census {census_sha[:12]}, signer {signer.key_id}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify GREEN** — `uv run --project . --locked python tests/test_author_overlay.py`; Expected: 43 `ok`, ALL PASS, exit 0.

- [ ] **Step 5: Regression — the merged suites must stay green (unmasked exit codes, one command per suite)**

Run each of: `uv run --project . --locked python tests/test_overlay_schema.py`, `tests/test_overlay_loader.py`, `tests/test_check_disposition.py` — Expected: ALL PASS, exit 0 each.

- [ ] **Step 6: Commit**

```bash
git add infra/database/schema-placement/author_overlay.py infra/database/schema-placement/tests/test_author_overlay.py
git commit -m "feat(schema-placement): author publish (atomic sidecar-first no-clobber), canonical names, D4 provenance gate, main()"
```

---

### Task 6: Standalone verifier — `verify_overlay_artifact.py`

**Files:**
- Create: `infra/database/schema-placement/verify_overlay_artifact.py`
- Test: `infra/database/schema-placement/tests/test_verify_overlay_artifact.py` (new; `_CASES` runner — same harness shape as Task 2's)

**Interfaces:**
- Consumes: `dt.resolve_pinned_key`, `ds.verify_sidecar_bytes_with_key`, `vc.load_snapshot_from_bytes` / `vc.check_census`, `dov.parse_overlay` / `load_overlay_contract` / `validate_overlay` / `check_binding` / `check_observation_window` / `check_target` / `check_conflict` / `_parse_iso`; fixtures `fx.*`; the AUTHOR (Task 5) for one cross-check case.
- Produces: `verify_artifact(overlay_bytes, *, census, census_bytes_sha, contract, expect_project_ref, now) -> list[(code, locus, msg)]` — the artifact-side pipeline AFTER signatures/census acceptance: `parse_overlay` (ValueError → OV008) → `isinstance(doc, dict)` guard (OV008, never a crash) → `validate_overlay` (SHORT-CIRCUIT on any schema error) → `check_binding` → `check_observation_window` → `captured_at <= now` (OV010 future-half) → `check_target` → intra-overlay `check_conflict`. `main(argv=None) -> int` — argv: `--overlay`, `--overlay-sig`, `--census`, `--census-sig`, `--key-id`, `--keys-dir` (default `dt.DEFAULT_KEYS_DIR`), `--expect-project-ref`, `--expect-database`, `--expect-schemas`, `--expect-census-repo-sha`, `--require-role-markers` (default as usual), `--expect-query-bundle-sha256`. Exit 2 = unreadable input; 1 = any blocking diagnostic; 0 = green (`=== OVERLAY ARTIFACT: GREEN (<dimension>, <n> assignments, census <sha12>) ===`).

**`main()` order (spec 4.1):** resolve signer (block prints reason + `=== OVERLAY ARTIFACT: 1 BLOCKING ===`, exit 1) → read overlay bytes ONCE + sig bytes (OSError → exit 2) → `ds.verify_sidecar_bytes_with_key(overlay_bytes, sig_bytes, signer.public_key)` (OV001, exit 1) → read census bytes+sig ONCE → verify census sig (OV001 `census` locus, exit 1) → `vc.load_snapshot_from_bytes` (exit 2 on parse) → `vc.check_census(...)` with the expects (print CN diags, exit 1) → `dov.load_overlay_contract()` (OV008 on `OverlayRegistryError`, exit 1) → `now = datetime.now(timezone.utc)` → `verify_artifact(...)` → print diags / green. **Docstring MUST state** (spec 4.1): this is an artifact + base-census-acceptance gate; it does NOT run cluster derivation (OV011/015/016/017/018/021/022) or the manifest-staleness half of OV010 — a green verify is NOT evidence-readiness.

- [ ] **Step 1: Write the failing tests (negatives first).** Create `tests/test_verify_overlay_artifact.py` with the standard runner and these cases (helper `_ctx()` builds signer+census via the Task-4 pattern; helper `_green_overlay(census, census_bytes)` assembles+signs a valid overlay via `author_overlay.assemble_overlay` + `fx` — reusing the author keeps producer/consumer parity honest):

```python
"""Offline suite for verify_overlay_artifact.py. Script __main__ runner."""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _overlay_pub_fixtures as fx  # noqa: E402
import author_overlay as ao  # noqa: E402
import disposition_overlay as dov  # noqa: E402
import disposition_trust as dt  # noqa: E402
import verify_overlay_artifact as voa  # noqa: E402

_CASES = []
NOW = dov._parse_iso("2026-07-12T12:00:00+00:00")


def _ctx():
    priv, pub = fx.keypair()
    census = fx.acceptance_census(["public.t1", "public.t2"])
    census_bytes = fx.canon(census)
    contract = dov.load_overlay_contract()
    return priv, pub, census, census_bytes, contract


def _mk_overlay(census, census_bytes, contract, **kw):
    core = fx.overlay_core(kw.pop("dimension", "in_data_api_exposed_schema"),
                           kw.pop("assignments", [{"object_id": "public.t1",
                                                   "value": {"state": "observed", "value": False}}]),
                           window=kw.pop("window", None))
    doc = ao.assemble_overlay(core, census=census,
                              census_sha256=hashlib.sha256(census_bytes).hexdigest(), contract=contract,
                              producing=kw.pop("producing", ("d" * 40, None)),
                              source_hash=kw.pop("source_hash", "e" * 64),
                              source_hash_reason=kw.pop("source_hash_reason", None),
                              source_locator=kw.pop("source_locator", "evidence/source/x.source.json"),
                              captured_at_iso=kw.pop("captured", "2026-07-12T06:00:00+00:00"))
    doc.update(kw)  # raw overrides for tamper-shaped cases
    return doc


def _va(doc_or_bytes, census, census_bytes, contract):
    b = doc_or_bytes if isinstance(doc_or_bytes, bytes) else ao._canon(doc_or_bytes)
    return voa.verify_artifact(b, census=census,
                               census_bytes_sha=hashlib.sha256(census_bytes).hexdigest(),
                               contract=contract, expect_project_ref=fx.PROJECT_REF, now=NOW)


def _green_artifact_verifies():
    _p, _u, census, cb, k = _ctx()
    return _va(_mk_overlay(census, cb, k), census, cb, k) == []


def _signed_non_object_is_coded_OV008():
    _p, _u, census, cb, k = _ctx()
    diags = _va(fx.canon([1, 2, 3]), census, cb, k)  # a JSON array -- must NOT crash
    return diags and all(d[0] == "OV008" for d in diags)


def _wrong_base_hash_OV002():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, base_snapshot_sha256="0" * 64)
    return any(d[0] == "OV002" for d in _va(doc, census, cb, k))


def _schema_sha_drift_OV020():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, overlay_schema_sha256="0" * 64)
    return any(d[0] == "OV020" for d in _va(doc, census, cb, k))


def _future_captured_OV010():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k, captured="2027-01-01T00:00:00+00:00")
    return any(d[0] == "OV010" for d in _va(doc, census, cb, k))


def _intra_dup_OV007():
    _p, _u, census, cb, k = _ctx()
    a = {"object_id": "public.t1", "value": {"state": "observed", "value": False}}
    doc = _mk_overlay(census, cb, k, assignments=[a, dict(a)])
    return any(d[0] == "OV007" for d in _va(doc, census, cb, k))


def _schema_invalid_short_circuits():
    _p, _u, census, cb, k = _ctx()
    doc = _mk_overlay(census, cb, k)
    del doc["authority"]  # schema-invalid -> OV008 only, nothing downstream
    diags = _va(doc, census, cb, k)
    return diags and all(d[0] == "OV008" for d in diags)


# ---- main() e2e ----
def _files(d):
    priv, pub = fx.keypair()
    keys_dir = fx.write_keys_dir(d, pub)
    census = fx.acceptance_census(["public.t1"])
    cpath, cspath, cb, _ = fx.write_signed(d, "census-prod-fixture.json", census, priv)
    contract = dov.load_overlay_contract()
    doc = _mk_overlay(census, cb, contract,
                      assignments=[{"object_id": "public.t1", "value": {"state": "observed", "value": False}}])
    opath, ospath, _ob, _sb = fx.write_signed(d, "overlay-fixture.json", doc, priv)
    exp = fx.acceptance_expects(census)
    argv = ["--overlay", opath, "--overlay-sig", ospath, "--census", cpath, "--census-sig", cspath,
            "--key-id", fx.KEY_ID, "--keys-dir", keys_dir,
            "--expect-project-ref", exp["project_ref"], "--expect-database", exp["database"],
            "--expect-schemas", ",".join(exp["schemas"]), "--expect-census-repo-sha", exp["census_repo_sha"],
            "--require-role-markers", ",".join(exp["role_markers"]),
            "--expect-query-bundle-sha256", exp["query_bundle_sha256"]]
    return argv, pub, opath


def _run_main(argv, pub):
    out = io.StringIO()
    with fx.trusted(fx.KEY_ID, fx.spki_fp(pub)), contextlib.redirect_stdout(out):
        rc = voa.main(argv)
    return rc, out.getvalue()


def _main_green():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        rc, out = _run_main(argv, pub)
        return rc == 0 and "GREEN" in out


def _main_tampered_overlay_OV001():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, opath = _files(d)
        data = open(opath, "rb").read()
        open(opath, "wb").write(data[:-2] + b" }")
        rc, out = _run_main(argv, pub)
        return rc == 1 and "OV001" in out


def _main_bad_census_scope_CN005():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        argv[argv.index("--expect-schemas") + 1] = "public,extra"
        rc, out = _run_main(argv, pub)
        return rc == 1 and "CN005" in out


def _main_unpinned_key_blocks():
    with tempfile.TemporaryDirectory() as d:
        argv, pub, _ = _files(d)
        argv[argv.index("--key-id") + 1] = "unpinned-id"
        rc, out = _run_main(argv, pub)
        return rc == 1 and "authorized signer" in out


_CASES += [
    ("green_artifact_verifies", _green_artifact_verifies),
    ("signed_non_object_is_coded_OV008", _signed_non_object_is_coded_OV008),
    ("wrong_base_hash_OV002", _wrong_base_hash_OV002),
    ("schema_sha_drift_OV020", _schema_sha_drift_OV020),
    ("future_captured_OV010", _future_captured_OV010),
    ("intra_dup_OV007", _intra_dup_OV007),
    ("schema_invalid_short_circuits", _schema_invalid_short_circuits),
    ("main_green", _main_green),
    ("main_tampered_overlay_OV001", _main_tampered_overlay_OV001),
    ("main_bad_census_scope_CN005", _main_bad_census_scope_CN005),
    ("main_unpinned_key_blocks", _main_unpinned_key_blocks),
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
    print("\n=== VERIFY OVERLAY ARTIFACT SUITE: {} ===".format("ALL PASS" if ok else "FAILURES PRESENT"))
    raise SystemExit(0 if ok else 1)
```

- [ ] **Step 2: Run to verify RED** — `uv run --project . --locked python tests/test_verify_overlay_artifact.py`; Expected: `ModuleNotFoundError: No module named 'verify_overlay_artifact'`.

- [ ] **Step 3: Implement** — create `verify_overlay_artifact.py`:

```python
"""Standalone committed-artifact verifier for a signed evidence overlay + its bound census.

Scope (spec 4.1): an ARTIFACT INTEGRITY + BASE-CENSUS-ACCEPTANCE gate. It verifies both detached
signatures against the source-pinned signer, runs the FULL verify_census.check_census contract on
the base census, and re-runs the consumer's per-artifact checks (schema, binding, window, the
OV010 future-half captured_at<=now, target, intra-overlay OV007) over the exact committed bytes.
It does NOT run cluster derivation (OV011/015/016/017/018/021/022) or the manifest-staleness half
of OV010 -- those belong to check_disposition --mode preapply. A GREEN here is NOT
evidence-readiness."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone

import disposition_overlay as dov
import disposition_signing as ds
import disposition_trust as dt
import verify_census as vc


def verify_artifact(overlay_bytes, *, census, census_bytes_sha, contract, expect_project_ref, now):
    """Artifact-side pipeline AFTER signature + census acceptance. Fail-closed and coded: a signed
    non-object or schema-invalid payload yields OV008 and SHORT-CIRCUITS (round-1 DAG-F1/CC4)."""
    loc = "artifact:overlay"
    try:
        doc = dov.parse_overlay(overlay_bytes)
    except ValueError as exc:
        return [("OV008", loc, f"overlay does not parse ({exc})")]
    if not isinstance(doc, dict):
        return [("OV008", loc, f"overlay is not a JSON object (got {type(doc).__name__})")]
    diags = dov.validate_overlay(doc, contract.overlay_validator)
    if diags:
        return diags
    diags += dov.check_binding(doc, census_sha256=census_bytes_sha,
                               census_project_ref=census.get("project_ref"),
                               expect_project_ref=expect_project_ref,
                               on_disk_disp_sha=contract.disp_sha256,
                               on_disk_overlay_sha=contract.overlay_sha256)
    diags += dov.check_observation_window(doc, now)
    try:
        if dov._parse_iso(doc["captured_at"]) > now:
            diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at is in the future"))
    except (KeyError, ValueError, TypeError):
        diags.append(("OV010", f"overlay:{doc.get('dimension')}", "captured_at unparseable"))
    rel_index = {r["object_id"]: r for r in census.get("relations", [])}
    diags += dov.check_target(doc, rel_index)
    diags += dov.check_conflict([(doc.get("dimension"), a.get("object_id"))
                                 for a in doc.get("assignments", [])])
    return diags


def _blocking(lines):
    for line in lines:
        print(line)
    print(f"=== OVERLAY ARTIFACT: {len(lines)} BLOCKING ===")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Standalone verifier for a committed overlay + its bound census.")
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--overlay-sig", required=True, dest="overlay_sig")
    ap.add_argument("--census", required=True)
    ap.add_argument("--census-sig", required=True, dest="census_sig")
    ap.add_argument("--key-id", required=True, dest="key_id")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir")
    ap.add_argument("--expect-project-ref", required=True, dest="expect_project_ref")
    ap.add_argument("--expect-database", required=True, dest="expect_database")
    ap.add_argument("--expect-schemas", required=True, dest="expect_schemas")
    ap.add_argument("--expect-census-repo-sha", required=True, dest="expect_census_repo_sha")
    ap.add_argument("--require-role-markers", default="anon,authenticated,service_role", dest="require_role_markers")
    ap.add_argument("--expect-query-bundle-sha256", required=True, dest="expect_query_bundle_sha256")
    args = ap.parse_args(argv)

    signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
    if signer is None:
        return _blocking([f"key-id: {kreason}"])
    try:
        with open(args.overlay, "rb") as fh:
            overlay_bytes = fh.read()
        with open(args.overlay_sig, "rb") as fh:
            overlay_sig_bytes = fh.read()
        with open(args.census, "rb") as fh:
            census_bytes = fh.read()
        with open(args.census_sig, "rb") as fh:
            census_sig_bytes = fh.read()
    except OSError as exc:
        print(f"OV000 input: cannot read artifact inputs ({type(exc).__name__})", file=sys.stderr)
        return 2
    ok, reason = ds.verify_sidecar_bytes_with_key(overlay_bytes, overlay_sig_bytes, signer.public_key)
    if not ok:
        return _blocking([f"OV001 overlay: signature verification failed: {reason}"])
    ok, reason = ds.verify_sidecar_bytes_with_key(census_bytes, census_sig_bytes, signer.public_key)
    if not ok:
        return _blocking([f"OV001 census: base census signature verification failed: {reason}"])
    try:
        census = vc.load_snapshot_from_bytes(census_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"OV000 input: cannot parse census ({type(exc).__name__})", file=sys.stderr)
        return 2
    cdiags = vc.check_census(census,
                             expect_project_ref=args.expect_project_ref,
                             expect_database=args.expect_database,
                             expect_schemas=[s.strip() for s in args.expect_schemas.split(",") if s.strip()],
                             expect_repo_sha=args.expect_census_repo_sha,
                             require_role_markers=[s.strip() for s in args.require_role_markers.split(",") if s.strip()],
                             expect_query_bundle_sha256=args.expect_query_bundle_sha256)
    if cdiags:
        return _blocking([d.render() for d in cdiags])
    try:
        contract = dov.load_overlay_contract()
    except dov.OverlayRegistryError as exc:
        return _blocking([f"OV008 contract: cannot build offline overlay contract ({type(exc).__name__})"])
    now = datetime.now(timezone.utc)
    diags = verify_artifact(overlay_bytes, census=census,
                            census_bytes_sha=hashlib.sha256(census_bytes).hexdigest(),
                            contract=contract, expect_project_ref=args.expect_project_ref, now=now)
    if diags:
        return _blocking([f"{c} {l}: {m}" for c, l, m in diags])
    doc = dov.parse_overlay(overlay_bytes)
    print(f"=== OVERLAY ARTIFACT: GREEN ({doc['dimension']}, {len(doc['assignments'])} assignments, "
          f"census {hashlib.sha256(census_bytes).hexdigest()[:12]}) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify GREEN** — 11 `ok`, ALL PASS, exit 0. Also re-run `tests/test_author_overlay.py` (still 43 `ok`).

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/verify_overlay_artifact.py infra/database/schema-placement/tests/test_verify_overlay_artifact.py
git commit -m "feat(schema-placement): standalone overlay-artifact verifier (sig + full census acceptance + per-artifact checks)"
```

---

### Task 7: RIDER — source-record orphan guard + locator constraints (`ci/overlay_ci_checks.py`, part 1)

**OPERATOR RIDER (verbatim obligation):** this task is the FIRST-CLASS source-orphan CI task. The failing test `source_record_without_overlay_fails` is written BEFORE any implementation, together with the orphan / multiply-referenced / traversal / non-regular / hash-mismatch negatives.

**Files:**
- Create: `infra/database/schema-placement/ci/overlay_ci_checks.py` (part 1: `normalize_locator`, `orphan_check`, `source_rehash`)
- Test: `infra/database/schema-placement/tests/test_verify_committed_overlays.py` (new; `_CASES` runner)

**Interfaces:**
- Consumes: stdlib only for part 1 (`posixpath`, `hashlib`).
- Produces (all PURE — no git, unit-testable with plain data):
  - `normalize_locator(locator) -> (ok: bool, value: str)` — reject absolute paths, any `..` component, backslashes, and anything not strictly under `evidence/source/`; on ok, `value` is the normalized schema-placement-relative path.
  - `orphan_check(overlay_docs, source_paths) -> list[str]` — `overlay_docs`: `[(path, doc_dict)]` for EVERY committed overlay; `source_paths`: every committed regular blob under `evidence/source/` (schema-placement-relative). Builds the locator-reference multiset from docs with non-null `source_hash`; FAILs every source path referenced by ≠ 1 overlay (orphan = 0; multiply-referenced > 1) and every non-null-hash locator that is valid-but-missing from `source_paths`.
  - `source_rehash(doc, sp_dir, protected_sources) -> list[str]` — for a doc with non-null `source_hash`: locator must normalize, must be in `protected_sources` (the committed regular-blob set), and `sha256(file bytes at sp_dir/<locator>) == source_hash`; each violation is a `FAIL:` string. Null-`source_hash` docs return `[]` (skip — OV019 already forces the reason).

- [ ] **Step 1: Write the failing tests — the RIDER test FIRST**

Create `tests/test_verify_committed_overlays.py`:

```python
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
```

- [ ] **Step 2: Run to verify RED** — `uv run --project . --locked python tests/test_verify_committed_overlays.py`; Expected: `ModuleNotFoundError: No module named 'overlay_ci_checks'` — `source_record_without_overlay_fails` is RED before any implementation exists (the rider's ordering, satisfied literally).

- [ ] **Step 3: Implement part 1** — create `ci/overlay_ci_checks.py`:

```python
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
```

- [ ] **Step 4: Run to verify GREEN** — 9 `ok` (rider case first in the output), ALL PASS, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/ci/overlay_ci_checks.py infra/database/schema-placement/tests/test_verify_committed_overlays.py
git commit -m "feat(schema-placement): RIDER source-orphan guard + locator constraints + source rehash (failing tests first)"
```

---

### Task 8: CI driver — kind-sniff, census uniqueness, exactly-one binding, committed-set OV007, orchestration (`ci/overlay_ci_checks.py`, part 2)

**Files:**
- Modify: `infra/database/schema-placement/ci/overlay_ci_checks.py` (append part 2)
- Test: `infra/database/schema-placement/tests/test_verify_committed_overlays.py` (append pure-function cases; the git-facing `main` is exercised end-to-end in Task 9)

**Interfaces:**
- Consumes: part 1 names; `subprocess` (git + the verifier CLI); `collect_disposition.query_bundle_sha256` (imported inside `main` — the HEAD-computed reviewed bundle).
- Produces:
  - `strict_parse(data: bytes)` — `json.loads` with duplicate-key and non-finite rejection (the same hooks as `dov.parse_overlay`); raises `ValueError`.
  - `kind_sniff(files) -> list[str]` — `files`: `[(sp_relative_path, bytes)]` for EVERY committed file under `evidence/`; content-sniff regardless of extension/case; any parsed dict with `kind == "evidence_overlay"` whose path does not match `^evidence/overlay-[^/]+\.json$` → FAIL (round-2b CI2b-3).
  - `census_uniqueness(census_files) -> list[str]` — `[(path, bytes)]`; two committed censuses with identical `sha256(bytes)` → FAIL (round-2b CI2b-4).
  - `sig_pairing(overlay_paths, sig_paths) -> list[str]` — exactly one `<overlay>.sig` per `evidence/overlay-*.json` and vice-versa (orphan sidecar / unsigned overlay → FAIL).
  - `match_census(base_hash, census_files) -> (path_or_None, fail_or_None)` — exactly-one committed census whose byte-hash equals `base_snapshot_sha256` (0 → unbound FAIL; >1 → ambiguous FAIL).
  - `committed_set_ov007(overlay_docs) -> list[str]` — group EVERY committed overlay by `base_snapshot_sha256`; per group build the FLAT `(dimension, object_id)` list over every assignment (intra repeats included — `check_conflict` parity); any key seen twice → FAIL.
  - `main(argv=None) -> int` — `--base <sha>`; from the repo root (`git rev-parse --show-toplevel`): collect `git ls-files` inventories; run (unconditionally) `kind_sniff` + `census_uniqueness` + `sig_pairing` + `orphan_check`; derive `ADDED` via `git diff --no-renames --diff-filter=A --name-only <base> HEAD -- ':(glob)infra/database/schema-placement/evidence/overlay-*.json'`; if empty → print `no overlays added — repo-level checks green` and exit per accumulated fails; else per added overlay: `strict_parse` → `match_census` → census-binding mirror (`git merge-base --is-ancestor <census.repo_sha> HEAD` + `git diff --quiet <census.repo_sha> HEAD -- $TOOLING` + qb from `collect_disposition.query_bundle_sha256()`) → `source_rehash` → null-safe `producing_repo_sha` (`None` → skip; else ancestor + tooling drift) → run `verify_overlay_artifact.py` via `uv run --project <SP> --locked python <SP>/verify_overlay_artifact.py ...` with the PINNED constants + `--expect-census-repo-sha <census.repo_sha>` + `--expect-query-bundle-sha256 <qb>`; then `committed_set_ov007`. Exit 1 on any FAIL; else `=== ALL COMMITTED OVERLAY ARTIFACTS VERIFIED ===`.

- [ ] **Step 1: Append the failing tests (pure functions)**

```python
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


_CASES += [
    ("kind_sniff_catches_hidden_overlay", _kind_sniff_catches_hidden_overlay),
    ("census_uniqueness_fails_duplicates", _census_uniqueness_fails_duplicates),
    ("sig_pairing_both_directions", _sig_pairing_both_directions),
    ("match_census_exactly_one", _match_census_exactly_one),
    ("committed_set_ov007_cross_overlay", _committed_set_ov007_cross_overlay),
    ("strict_parse_rejects_dup_keys_and_nonfinite", _strict_parse_rejects_dup_keys_and_nonfinite),
]
```

- [ ] **Step 2: Run to verify RED** — the 6 new cases FAIL (`no attribute 'kind_sniff'`); the 9 Task-7 cases stay `ok`.

- [ ] **Step 3: Implement part 2** — append to `ci/overlay_ci_checks.py`:

```python
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
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen[k] = v
    return seen


def _reject_nonfinite(const):
    raise ValueError(f"non-finite JSON constant {const!r} not allowed")


def strict_parse(data: bytes):
    return json.loads(data.decode("utf-8"), object_pairs_hook=_reject_dup, parse_constant=_reject_nonfinite)


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

    overlay_docs = []
    for p in overlay_paths:
        data = dict(evidence_files)[p]
        try:
            doc = strict_parse(data)
        except ValueError as exc:
            fails.append(f"FAIL: {p}: overlay does not strict-parse ({exc})")
            continue
        overlay_docs.append((p, doc))

    # UNCONDITIONAL repo-level checks (before the added-set early exit; rider + spec 4.2 steps 1-2)
    fails += kind_sniff(evidence_files)
    fails += census_uniqueness(census_files)
    fails += sig_pairing(overlay_paths, sig_paths)
    fails += orphan_check(overlay_docs, source_paths)

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
```

- [ ] **Step 4: Run to verify GREEN** — 15 `ok`, ALL PASS, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/ci/overlay_ci_checks.py infra/database/schema-placement/tests/test_verify_committed_overlays.py
git commit -m "feat(schema-placement): overlay CI driver -- kind-sniff, census uniqueness, exactly-one binding, committed-set OV007, orchestration"
```

---

### Task 9: Shell gate (`ci/verify_committed_overlays.sh`) + scratch-git-repo end-to-end suite

**Files:**
- Create: `infra/database/schema-placement/ci/verify_committed_overlays.sh`
- Test: `infra/database/schema-placement/tests/test_verify_committed_overlays.py` (append the scratch-repo e2e section)

**Interfaces:**
- Consumes: Task 8's `ci/overlay_ci_checks.py --base <sha>`; the real tree's tooling files (copied into scratch repos); `author_overlay.assemble_overlay` / `fx.*` for fixture artifacts.
- Produces: the gate contract for Task 10 — `bash infra/database/schema-placement/ci/verify_committed_overlays.sh` exits 0 green / 1 FAIL, printing `FAIL:` lines.

- [ ] **Step 1: Append the failing e2e tests (the gate script does not exist yet)**

Append to `tests/test_verify_committed_overlays.py`:

```python
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
    """origin repo with the PATCHED tooling tree at <repo>/infra/database/schema-placement/,
    committed on main; then a clone (so origin/main exists). Returns (work_dir, priv, base_sha).
    PATCH (test-only, in the SCRATCH COPY): the synthetic public key replaces the prod pubkey
    file AND the TRUSTED_SIGNERS fingerprint line in disposition_trust.py is rewritten to the
    synthetic SPKI -- the shipped gate binary stays fail-closed; the scratch repo is a parallel
    universe signed by the test key under the SAME pinned key-id."""
    priv, pub = fx.keypair()
    origin = os.path.join(tmp, "origin")
    sp = os.path.join(origin, *SP.split("/"))
    os.makedirs(os.path.join(sp, "evidence", "source"), exist_ok=True)
    os.makedirs(os.path.join(sp, "keys"), exist_ok=True)
    os.makedirs(os.path.join(sp, "ci"), exist_ok=True)
    for name in _COPY:
        shutil.copy2(os.path.join(SP_REAL, *name.split("/")), os.path.join(sp, *name.split("/")))
    open(os.path.join(sp, "keys", "prod-disposition-ed25519-2026-07.pub.pem"), "wb").write(pub)
    trust = open(os.path.join(sp, "disposition_trust.py")).read()
    trust = trust.replace("c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca", fx.spki_fp(pub))
    open(os.path.join(sp, "disposition_trust.py"), "w").write(trust)
    _sh(["git", "init", "-q", "-b", "main"], origin)
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], origin)
    _sh(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base"], origin)
    base_sha = _sh(["git", "rev-parse", "HEAD"], origin).stdout.strip()
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
        return r.returncode == 1


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
        sp = os.path.join(work, *SP.split("/"))
        # commit a symlink blob (mode 120000) under evidence/source/ without touching the fs:
        blob = _sh(["git", "hash-object", "-w", "--stdin"], work).stdout.strip() if False else None
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
        open(os.path.join(sp, "evidence", "notes.JSON"), "wb").write(hidden)
        _commit_all(work, "hidden overlay")
        r = _gate(work)
        return r.returncode == 1 and "canonical" in r.stdout


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
]
```

**Fixture-shape note (build-time watch-items):** (a) `_fixture_overlay` writes fixture names OUTSIDE the author's `canonical_names` scheme on purpose — the gate must accept any `evidence/overlay-*.json` name and judge content, not naming beyond the glob; (b) the tamper cases PUSH main first so BASE(origin/main) contains the artifact and the tamper is a modification of COMMITTED evidence; (c) if the rename+modify case produces status `A`+`D` instead of `R` on some git config, the gate must STILL fail (the `D` trips all-`A`) — assert only `returncode == 1`, not the mechanism.

- [ ] **Step 2: Run to verify RED** — the 9 e2e cases FAIL (`No such file ... verify_committed_overlays.sh` propagated as `RuntimeError`/rc!=0 from `_scratch`'s copy step); the 15 unit cases stay `ok`.

- [ ] **Step 3: Implement the shell gate** — create `ci/verify_committed_overlays.sh`:

```bash
#!/usr/bin/env bash
# CI gate: the overlay-evidence contract (design spec 4.2 @ 8f6d41c4).
#  step 0  fail-closed fetch + UNIQUE merge-base (--all; exactly one line)
#  step 1  immutability: --no-renames --name-status over census/overlay/source/sig pathspecs,
#          FAIL unless EVERY entry is status A (rejects M, D, T, R, C, U, B; --no-renames
#          decomposes a rename+modify into A+D -- the empirically-pinned round-2b bypass);
#          plus a non-regular-mode check (120000 symlink / 160000 gitlink under evidence/)
#  step 2+ delegated to overlay_ci_checks.py (kind-sniff, census uniqueness, sig pairing,
#          SOURCE-ORPHAN GUARD (rider, unconditional), added-set per-overlay verification with
#          the non-self-referential census binding, committed-set OV007)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
SP=infra/database/schema-placement

git fetch --quiet origin main    # FAIL-CLOSED: a fetch failure aborts (no '|| true')

BASES=$(git merge-base --all origin/main HEAD)
if [ "$(printf '%s\n' "$BASES" | grep -c .)" -ne 1 ]; then
  echo "FAIL: merge-base of origin/main and HEAD is empty or ambiguous"; exit 1
fi
BASE=$BASES

# step 1a: immutability -- every touched evidence artifact must be status A
BAD=$(git diff --no-renames --name-status "$BASE" HEAD -- \
        ":(glob)$SP/evidence/census-prod-*.json" \
        ":(glob)$SP/evidence/overlay-*.json" \
        "$SP/evidence/source" \
        ":(glob)$SP/evidence/**/*.sig" \
      | awk '$1 != "A"' || true)
if [ -n "$BAD" ]; then
  echo "FAIL: immutability -- committed evidence was modified/deleted/renamed/typechanged:"
  printf '%s\n' "$BAD"
  exit 1
fi

# step 1b: non-regular modes under evidence/ (symlink/gitlink)
MODES=$(git ls-files -s -- "$SP/evidence" | awk '$1 == "120000" || $1 == "160000"' || true)
if [ -n "$MODES" ]; then
  echo "FAIL: non-regular file mode under $SP/evidence:"
  printf '%s\n' "$MODES"
  exit 1
fi

# steps 2-5: repo-level + per-added-overlay checks (python driver; runs its unconditional
# checks -- incl. the source-orphan guard -- even when zero overlays are added)
uv run --project "$SP" --locked python "$SP/ci/overlay_ci_checks.py" --base "$BASE"
```

Then `chmod +x ci/verify_committed_overlays.sh`.

- [ ] **Step 4: Run to verify GREEN** — `uv run --project . --locked python tests/test_verify_committed_overlays.py`; Expected: 24 `ok` (15 unit + 9 e2e), ALL PASS, exit 0. This run is slower (~1–3 min: scratch clones + nested `uv run`); that is expected.

- [ ] **Step 5: Manual gate check on the REAL branch (no overlays added → green)**

Run from the repo root: `bash infra/database/schema-placement/ci/verify_committed_overlays.sh`
Expected: `no overlays added -- unconditional repo-level checks complete` then `=== ALL COMMITTED OVERLAY ARTIFACTS VERIFIED ===`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add infra/database/schema-placement/ci/verify_committed_overlays.sh infra/database/schema-placement/tests/test_verify_committed_overlays.py
git commit -m "feat(schema-placement): overlay-evidence shell gate (rename-proof immutability, mode check) + scratch-repo e2e suite"
```

---

### Task 10: Workflow wiring (`.github/workflows/schema-placement-ci.yml`)

**Files:**
- Modify: `.github/workflows/schema-placement-ci.yml` (two edits)

**Interfaces:**
- Consumes: Task 9's gate script; the three new suites.
- Produces: CI runs the 11-suite loop + the `overlay-evidence` job on every schema-placement PR.

- [ ] **Step 1: Edit the suites loop** — in the `suites` job, change the loop list line to:

```yaml
          for t in test_disposition_schema test_check_disposition test_collect_disposition test_verify_census test_disposition_trust test_disposition_provenance test_overlay_schema test_overlay_loader test_author_overlay test_verify_overlay_artifact test_verify_committed_overlays; do
```

- [ ] **Step 2: Append the `overlay-evidence` job** (mirror of `census-evidence`; SHA-pinned actions copied verbatim from the existing jobs):

```yaml
  # Artifact gate: committed overlay evidence must be signed by the pinned signer, bound to a
  # committed census (non-self-referentially), source-rehashable, orphan-free, immutable
  # (rename-proof), and free of committed-set OV007 duplicates. Runs the shell gate, which
  # delegates repo-level logic to ci/overlay_ci_checks.py. Needs full history for merge-base
  # and the repo_sha ancestry/drift assertions.
  overlay-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
        with:
          python-version: '3.11'
      - name: Install uv (pinned)
        run: python -m pip install 'uv==0.11.21'
      - name: Verify committed overlay artifacts (signed, census-bound, source-rehashable, orphan-free)
        run: bash infra/database/schema-placement/ci/verify_committed_overlays.sh
```

- [ ] **Step 3: Validate the YAML + whitespace**

Run from the repo root:
`(cd infra/database/schema-placement && uv run --project . --locked python -c "import yaml,sys; yaml.safe_load(open('../../../.github/workflows/schema-placement-ci.yml')); print('YAML OK')")`
Expected: `YAML OK`.
Then: `EMPTY=$(git hash-object -t tree /dev/null); git diff --check "$EMPTY" HEAD -- .github/workflows/schema-placement-ci.yml` — Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/schema-placement-ci.yml
git commit -m "ci(schema-placement): register the three overlay-publication suites + the overlay-evidence artifact gate"
```

---

### Task 11: `OVERLAY_COLLECTION_RUNBOOK.md` (six-dimension collection runbook)

**Files:**
- Create: `infra/database/schema-placement/OVERLAY_COLLECTION_RUNBOOK.md`

**Interfaces:** Consumes the Task-5 author CLI contract (flag names copied exactly). Documentation task — its verification step is grep-based.

- [ ] **Step 1: Write the runbook** with EXACTLY this content:

```markdown
# Overlay evidence collection runbook (disposition ledger)

> **DO NOT RUN until the operator gives an explicit per-dimension collection GO (roadmap Phase 9).**
> Prepared procedure only. Each of the six dimensions gets its OWN source-specific GO, so one
> source failure cannot contaminate the others. Every overlay binds to the CURRENT fresh signed
> census (Phase 6/7); never author against a stale census.

## 0. Preconditions

1. Clean merged-main checkout; record `GATE_SHA=$(git rev-parse origin/main)` after
   `git fetch origin main`, and confirm `git rev-parse HEAD` equals it with a clean
   `git status --porcelain`. The author refuses otherwise (AO010).
2. The fresh signed census + sidecar (committed under `evidence/`), its merged `repo_sha`
   (`CENSUS_SHA`), and the reviewed query-bundle hash
   (`QB=$(cd infra/database/schema-placement && uv run --project . --locked python -c "import collect_disposition as c; print(c.query_bundle_sha256())")`).
3. `DISPOSITION_SIGNING_KEY` in Infisical (operator custody — the key never enters the repo,
   argv, logs, or this runbook). Injection via `infra/infisical/inject.sh prod`.
4. An out-of-repo output dir: `OUT="$HOME/overlay-evidence/$(date -u +%Y%m%dT%H%M%SZ)"`.

## 1. Value-silence discipline (MANDATORY)

- Signing key from env ONLY; `set +x`; never echo it.
- **Raw source evidence is secret-bearing** (runtime logs and advisor output may embed DSN
  fragments): never `cat` it into a transcript. The committed source record for logs is a
  NORMALIZED, REDACTED extract; raw un-redacted material stays in separate custody (Vault),
  referenced from the record.
- Secret-scan and redact any transcript before committing evidence.

## 2. The six dimensions

| Dimension (`source_type`) | Authoritative source | assignment `value` shape | `producing_repo_sha` | source record → `source_hash` |
|---|---|---|---|---|
| `in_data_api_exposed_schema` (`platform_config`) | Data-API **exposed-schemas platform config** (declared config, NOT the runtime `pgrst.db_schemas` GUC) | `{"state":"observed","value":<bool>}` | REQUIRED = author HEAD (`GATE_SHA`) | committed config export |
| `advisor_findings` (`advisor_api`) | Supabase **advisor API** (security + performance) | `{"state":"observed","value":["<finding>",...]}` | FORBIDDEN → null + reason | committed advisor JSON |
| `consumer_evidence.static_repo` (`repository_scan`) | **Static scan** of platform repos for references to each object | consumer_evidence_dim: observed → `{"state":"observed","found_consumers":<int>,"ref":"<scan ref>"}` | REQUIRED = author HEAD | scan output **+ an enumeration of EVERY scanned {repo_root, commit_sha}** (one `producing_repo_sha` never stands in for multiple external repos) |
| `consumer_evidence.runtime_logs` (`runtime_logs`) | Production **query/pg logs** over the window | consumer_evidence_dim | FORBIDDEN → null + reason | **redacted** log extract + raw-custody note |
| `consumer_evidence.external_clients` (`external_client_inventory`) | External API-client / integration inventory | consumer_evidence_dim | CONDITIONAL (author HEAD if repo-committed inventory; else null + reason) | committed inventory |
| `consumer_evidence.operator_declaration` (`operator_declaration`) | Signed **operator attestation** (core carries `operator_identity` + `attestation_ref`) | consumer_evidence_dim | FORBIDDEN → null + reason | committed attestation, or null + reason with `--source-custody-locator` |

Non-observed consumer states use `{"state":"...","found_consumers":null,"ref":null,"detail":"..."}`.

## 3. Window + freshness discipline (make preapply SATISFIABLE)

- Per overlay (enforced at author time): `started_at < ended_at <= captured_at` and `ended_at <=
  now` (OV009); `captured_at` is set by the tool clock (its future-half is OV010).
- At the cluster gate the consumer window derives as `S = max(started_at)`, `E = min(ended_at)`
  across the OBSERVED consumer overlays per relation. It must be non-empty (OV011), bracket the
  census instant `S <= observed_at <= E` (OV017), and — for a delete whose `external_clients` is
  `not_applicable` — the observed-FALSE `in_data_api_exposed_schema` window must COVER `[S, E]`
  (OV022). So: choose consumer windows that OVERLAP and BRACKET `observed_at`, and give the
  `in_data_api` overlay a window at least as wide as the intersection.
- **OV016 freshness is measured at PREAPPLY time against `E = min(ended_at)` — the
  earliest-ending consumer window, not `captured_at`.** Collect all consumer evidence for a
  cluster close together, and run `check_disposition --mode preapply` within
  `--max-consumer-evidence-age-hours` (planned value: 720) of the earliest `ended_at`.

## 4. Author one overlay (per-dimension GO)

Write the semantics core (`core.json`): `dimension`, `assignments`, `observation_window`,
`authority`, `collection_method` (+ `operator_identity`/`attestation_ref` for the declaration
dimension). Then:

    infra/infisical/inject.sh prod -- \
      uv run --project infra/database/schema-placement --locked \
        python infra/database/schema-placement/author_overlay.py \
          --census <committed census path> --census-sig <committed census .sig> \
          --key-id prod-disposition-ed25519-2026-07 \
          --input core.json \
          --source-file <raw-or-redacted evidence file> \
          --expect-gate-repo-sha "$GATE_SHA" \
          --expect-project-ref fxoyniqnrlkxfligbxmg --expect-database postgres \
          --expect-schemas public --expect-census-repo-sha "$CENSUS_SHA" \
          --require-role-markers anon,authenticated,service_role \
          --expect-query-bundle-sha256 "$QB" \
          --out-dir "$OUT"

For a no-artifact dimension replace `--source-file` with
`--source-hash-na-reason "<why>" --source-custody-locator "<vault ref>"`.
For FORBIDDEN/`external_clients`-null dimensions add `--producing-repo-sha-na-reason "<why>"`.
The tool validates BEFORE signing (AO005 prints the exact OV codes), enforces signer parity
(AO007), verifies the sidecar in memory (AO012), and publishes
`$OUT/{overlay,overlay.sig,source/record}` no-clobber with canonical names.

## 5. Verify + commit (evidence PR, Phase 10 GO)

Verify locally: `verify_overlay_artifact.py --overlay ... --overlay-sig ... --census ...
--census-sig ... --key-id prod-disposition-ed25519-2026-07 --expect-project-ref
fxoyniqnrlkxfligbxmg --expect-database postgres --expect-schemas public
--expect-census-repo-sha "$CENSUS_SHA" --expect-query-bundle-sha256 "$QB"` → GREEN. Copy the
triple into `infra/database/schema-placement/evidence/` PRESERVING NAMES (the overlay's
`source_locator` is the schema-placement-relative destination `evidence/source/<name>`), commit
via a governed evidence PR, and let the `overlay-evidence` CI independently re-verify every
artifact (immutability, orphan guard, census binding, source rehash, committed-set OV007).
```

- [ ] **Step 2: Verify** — `grep -c "DO NOT RUN" OVERLAY_COLLECTION_RUNBOOK.md` → `1`; `grep -c "source-custody-locator" OVERLAY_COLLECTION_RUNBOOK.md` → ≥1; `grep -c "min(ended_at)" OVERLAY_COLLECTION_RUNBOOK.md` → ≥1.

- [ ] **Step 3: Commit**

```bash
git add infra/database/schema-placement/OVERLAY_COLLECTION_RUNBOOK.md
git commit -m "docs(schema-placement): six-dimension overlay collection runbook (DO-NOT-RUN-until-GO)"
```

---

### Task 12: `CENSUS_RUNBOOK.md` corrections

**Files:**
- Modify: `infra/database/schema-placement/CENSUS_RUNBOOK.md` (three exact edits)

- [ ] **Step 1: Edit 1 — PG17.6.** Replace (line ~7): `Prod project: \`fxoyniqnrlkxfligbxmg\` (Supabase, managed non-super \`postgres\`, PG16).` with `Prod project: \`fxoyniqnrlkxfligbxmg\` (Supabase, managed non-super \`postgres\`, PG17.6 — per the committed census \`target_identity.server_version\`, \`server_version_num\` 170006).`

- [ ] **Step 2: Edit 2 — trust-anchor location.** In precondition 3 (line ~20), replace `The trust anchor is the \`TRUSTED_SIGNERS\` constant in \`verify_census.py\` (reviewed verifier source),` with `The trust anchor is the \`TRUSTED_SIGNERS\` source constant in \`disposition_trust.py\` (the SHARED reviewed anchor — \`verify_census\` AND \`check_disposition\` both resolve signers through \`disposition_trust.resolve_pinned_key\`),`

- [ ] **Step 3: Edit 3 — post-census sequence + immutability note.** Replace the final section (from `**After the census:** build the signed-overlay packet` through the end of the file) with:

```markdown
**After the census (current sequence — each step operator-gated):** the signed-overlay CONSUMER
(`disposition_overlay.py`, OV001–OV022) and the overlay PUBLICATION tooling (`author_overlay.py`,
`verify_overlay_artifact.py`, the `overlay-evidence` CI gate, `OVERLAY_COLLECTION_RUNBOOK.md`) are
merged. Next: **fresh census → definer-view reconciliation → collect + sign the six per-dimension
overlays (`author_overlay.py`, bound to the fresh census byte-hash, each with a committed source
record) → formal cluster gate (`check_disposition --mode preapply` over census + all overlays) →
apply runner** (revalidate-everything: read-once, verify snapshot+overlay sigs vs the pinned key,
re-run schema/semantic/target gates, bind+hash the exact migration SQL, restore-test the backup in
disposable PostgreSQL, recheck identity+drift immediately before SQL). The apply gate remains HELD.

**Evidence immutability:** the `overlay-evidence` CI job also rejects any MODIFY/DELETE/RENAME/
TYPECHANGE of committed `census-prod-*.json`, `overlay-*.json`, `evidence/source/**`, or `*.sig`
artifacts (`git diff --no-renames --name-status`, all-`A` required) — closing the census gate's
added-only blind spot. Committed evidence is immutable; supersede with a fresh artifact, never an
edit.
```

- [ ] **Step 4: Verify** — `grep -c "PG17.6" CENSUS_RUNBOOK.md` → 1; `grep -c "disposition_trust.py" CENSUS_RUNBOOK.md` → ≥1; `grep -c "PG16" CENSUS_RUNBOOK.md` → 0; `grep -c "no-renames" CENSUS_RUNBOOK.md` → 1.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/CENSUS_RUNBOOK.md
git commit -m "docs(schema-placement): census runbook corrections -- PG17.6, disposition_trust.py anchor, current post-census sequence"
```

---

### Task 13: Full regression + whole-branch cross-engine review (pre-PR gate)

**Files:** none created — verification + review only.

- [ ] **Step 1: Full suite regression — all 11 suites, UNMASKED exit codes** (one command per suite; never pipe through `tail`/`head` — a pipe masks the exit code):

Run from `infra/database/schema-placement/`, in order, asserting exit 0 on EACH:
```
uv run --project . --locked python tests/test_disposition_schema.py
uv run --project . --locked python tests/test_check_disposition.py
uv run --project . --locked python tests/test_collect_disposition.py
uv run --project . --locked python tests/test_verify_census.py
uv run --project . --locked python tests/test_disposition_trust.py
uv run --project . --locked python tests/test_disposition_provenance.py
uv run --project . --locked python tests/test_overlay_schema.py
uv run --project . --locked python tests/test_overlay_loader.py
uv run --project . --locked python tests/test_author_overlay.py
uv run --project . --locked python tests/test_verify_overlay_artifact.py
uv run --project . --locked python tests/test_verify_committed_overlays.py
```
Expected: `ALL PASS`, exit 0 — all 11 (the GO's "full eight-suite regression" = the 8 merged suites, all of which must stay green untouched, plus the 3 new ones).

- [ ] **Step 2: Gate self-checks on the branch**

```
bash infra/database/schema-placement/ci/verify_committed_census.sh     # expect: nothing to verify, exit 0
bash infra/database/schema-placement/ci/verify_committed_overlays.sh   # expect: no overlays added, exit 0
EMPTY=$(git hash-object -t tree /dev/null); git diff --check "$EMPTY" HEAD -- infra/database/schema-placement .github/workflows/schema-placement-ci.yml   # expect: no output
```

- [ ] **Step 3: Whole-branch cross-engine review (GO requirement 7 — BEFORE any PR)**

Dispatch the whole-branch review per superpowers:requesting-code-review (most capable model), reviewing `main..HEAD` against the approved design @ `8f6d41c4` and this plan; AND run the Codex pass:
`ssh olares-mesh 'cd /home/olares/code/apex/apex-schema-pub && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && codex exec review --base main -m gpt-5.5 --dangerously-bypass-approvals-and-sandbox'`
Fold Critical/Important findings via fix tasks (re-running Steps 1–2 after), append the review record to `infra/database/schema-placement/evidence/irp-cross-engine-overlay-publication.md` (a new ROUND section), and commit it.

- [ ] **Step 4: STOP.** Report branch tip, per-suite totals, review verdicts, and any deferred Minors. **Do NOT push, do NOT open a PR** — Phase 5 (push + governed squash PR) requires its own operator GO.

---

## Plan decisions (spec-ambiguity resolutions — flagged for the reviewer)

1. **`--out-dir` + computed canonical names** replace the spec §3.1 flag sketch `--out/--sig-out/--source-out`: §3.6's canonical-naming + `-NN` counter is the binding requirement (CI enforces the canonical glob), so the tool computes names inside `--out-dir` rather than accepting hand-typed paths that could manufacture CI failures. The runbook copies the final triple into `evidence/` preserving names; `source_locator` is computed as the repo DESTINATION path (`evidence/source/<name>`), valid wherever the triple is first published.
2. **AO013 added** for the signer key-id resolution block (the spec's §11 "key-resolution block (CN013-analog)" row had no AO number); AO006 stays reserved (intra-overlay dup surfaces as OV007 via AO005).
3. **Gate scripts are not in TOOLING** (census-gate precedent: the gate executes at HEAD; its own drift is meaningless to measure against itself).
4. **The CI driver lives in `ci/overlay_ci_checks.py`** (python) with a thin shell entry — the spec's step semantics are unchanged; shell does fetch/merge-base/immutability/modes, python does everything requiring JSON/set logic. This maximizes unit-testability of the rider functions.
5. **The e2e suite patches the SCRATCH-repo copy** of `disposition_trust.py`/`keys/` to a synthetic signer (same key-id). The shipped anchor is never weakened; no env override exists in the gate.

## Execution & review protocol (build phase)

- REQUIRED SUB-SKILL: superpowers:subagent-driven-development — fresh implementer per task on the host worktree over mesh, per-task spec+quality review (opus on Tasks 5, 8, 9), RED→GREEN fixes, ledger at `.superpowers/sdd/progress.md`.
- Review agents are READ-ONLY on the live tree; adjudicate vs the host ref at the pinned HEAD.
- Every suite run uses the unmasked single-command form above. Stage exact paths; re-check HEAD before each host write (a concurrent operator writer exists).
- HOLDS: no push, no PR, no merge, no evidence collection, no signing with the production key, no DB, no prod — Phase 4 authorizes BUILD ONLY.
