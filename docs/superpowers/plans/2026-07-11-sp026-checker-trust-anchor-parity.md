# SP026 Checker Trust-Anchor Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the ratified source-constant trust anchor to `check_disposition.py`'s destructive-DDL preapply gate — replacing caller-selectable `--verify-key` with anchor-resolved `--key-id`, binding the checker's own checkout to a reviewed gate SHA, and binding the receipt to the exact signature bytes verified.

**Architecture:** Extract a single reviewed trust root (`disposition_trust.py`) and a single git-provenance module (`disposition_provenance.py`); keep `disposition_signing.py` as pure crypto mechanism. Refactor the collector and the census-acceptance gate onto the shared modules behavior-preservingly, then harden the preapply checker (SP026 anchor + SP028 checkout gate + content-bound receipt).

**Tech Stack:** Python 3.11, `cryptography==49.0.0` (lazy-imported Ed25519), `jsonschema`, `uv`-managed deterministic env (`pyproject.toml` + `uv.lock`). All work under `infra/database/schema-placement/` on host worktree `/home/olares/code/apex/apex-schema-sp026` (branch `schema-placement/sp026-trust-anchor-parity`, off `main@965c466d`).

## Global Constraints

- Spec of record: `docs/superpowers/specs/2026-07-11-sp026-checker-trust-anchor-parity-design.md` @ `95be014e`.
- Dependency graph: `disposition_signing`(mechanism) ; `disposition_trust`(policy, imports signing) ; `disposition_provenance`(git checks) ; `collect_disposition` imports signing+provenance ; `verify_census` imports signing+trust+provenance (+ `collect_disposition` for `query_bundle_sha256`) ; `check_disposition` imports signing+trust+provenance. Collector NEVER imports trust; checker NEVER imports the collector.
- Provenance functions are PUBLIC cross-module names: `git_head_sha(repo_dir)`, `git_worktree_clean(repo_dir)`. Consumers call `disposition_provenance.<name>`; tests monkeypatch `disposition_provenance.<name>`.
- Trust map is immutable from the production API: `resolve_pinned_key(keys_dir, key_id)` has NO public `trusted_signers` param and reads the module constant `TRUSTED_SIGNERS`. Tests monkeypatch `disposition_trust.TRUSTED_SIGNERS`.
- `resolve_pinned_key` returns `(ResolvedSigner | None, reason)`; `ResolvedSigner` has `key_id, public_key, spki_sha256, pubkey_path, pem_sha256`.
- Diagnostic codes: SP026 reworded off `--verify-key`; CN001 reworded off `--verify-key`; new SP028 for checkout provenance (SP027 is the destructive-evidence floor — untouched).
- SP028 truth table (exactly two GREEN paths): `(--expect-gate-repo-sha, --require-clean-checkout, --allow-unbound-checkout)` = `(present, present, absent)` → Bound GREEN (`checkout_bound=true, production_eligible=true`); `(absent, absent, present)` → Authoring-only GREEN (`checkout_bound=false, production_eligible=false`); **any other combination → SP028**.
- SP028 gate runs IMMEDIATELY after argument parsing, BEFORE any input document is read or trusted.
- Authoring GREEN banner on stdout is the distinct `=== DISPOSITION GATE (preapply): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ===` plus an advisory stderr WARNING; bound GREEN keeps `=== DISPOSITION GATE (preapply): GREEN ===`. The em-dash is literal; source and asserting test share the identical UTF-8 string.
- Receipt records `signer{key_id,spki_sha256,pem_sha256}`, `snapshot_signature_sha256`, `gate_repo_sha`, `checkout_bound`, `production_eligible`; NO `verify_key` path; no second read of the sidecar at receipt time.
- Behavior-preserving refactors for `collect_disposition` (42 cases green) and `verify_census` (31 pre-existing cases green; CN013/CN017 unchanged).
- No `--verify-key` flag/`args.verify_key` in any active code; historical evidence files unchanged byte-for-byte.
- **Test-runner registration differs per file (verified):** `test_verify_census.py`, `test_disposition_trust.py`, `test_disposition_provenance.py` use a module-level `ALL` list. `test_check_disposition.py` has NO `ALL`; its `__main__` runner (which CI executes via `python tests/test_check_disposition.py`) iterates `BASELINES`, the `NEG` dict, and an **inline `units` list** of `(name, bool_returning_callable)` pairs at `~:465`. New `test_check_disposition` cases MUST be added to that inline `units` list as **bool-returning helpers** (a `test_*` wrapper that returns `None` registers as `bool(None) == False` → FAIL). `test_collect_disposition.py` runs via its own `ALL` at `:693`.
- No database access, no production write, no A1–A3 in this packet. Governed squash-merge after green CI + cross-engine IRP; no admin bypass.
- Test command: `uv run --project . --locked python tests/<suite>.py` from `infra/database/schema-placement/`. Every commit stages exact paths only (never `git add <dir>` in this worktree).

---

### Task 1: `disposition_provenance.py` (new git-checks module)

**Files:**
- Create: `infra/database/schema-placement/disposition_provenance.py`
- Test: `infra/database/schema-placement/tests/test_disposition_provenance.py`

**Interfaces:**
- Produces: `git_head_sha(repo_dir) -> str | None`, `git_worktree_clean(repo_dir) -> bool` (public; fail-closed).

- [ ] **Step 1: Write the failing test** — `tests/test_disposition_provenance.py`:

```python
"""Offline tests for disposition_provenance.py (git HEAD / clean-worktree checks)."""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disposition_provenance as dp  # noqa: E402


def _git(d, *args):
    subprocess.run(["git", "-C", d, *args], check=True, capture_output=True, text=True)


def _init_repo(d):
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@example.com")
    _git(d, "config", "user.name", "t")
    with open(os.path.join(d, "f.txt"), "w", encoding="utf-8") as fh:
        fh.write("x\n")
    _git(d, "add", "f.txt")
    _git(d, "commit", "-q", "-m", "init")
    return subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], check=True,
                          capture_output=True, text=True).stdout.strip()


def test_head_sha_returns_commit():
    with tempfile.TemporaryDirectory() as d:
        head = _init_repo(d)
        assert dp.git_head_sha(d) == head


def test_worktree_clean_true_then_dirty():
    with tempfile.TemporaryDirectory() as d:
        _init_repo(d)
        assert dp.git_worktree_clean(d) is True
        with open(os.path.join(d, "untracked.txt"), "w", encoding="utf-8") as fh:
            fh.write("y\n")
        assert dp.git_worktree_clean(d) is False


def test_non_git_dir_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        assert dp.git_head_sha(d) is None
        assert dp.git_worktree_clean(d) is False


ALL = [
    ("head_sha_returns_commit", test_head_sha_returns_commit),
    ("worktree_clean_true_then_dirty", test_worktree_clean_true_then_dirty),
    ("non_git_dir_fails_closed", test_non_git_dir_fails_closed),
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_disposition_provenance.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'disposition_provenance'`.

- [ ] **Step 3: Create `disposition_provenance.py`** (helpers moved verbatim from `collect_disposition.py:591-611`, renamed public):

```python
"""Git checkout-provenance checks shared by the disposition tooling (SP026). Pure git-subprocess
helpers with NO crypto and NO policy. The collector, the census-acceptance gate, and the preapply
checker all bind their evidence/trust to a reviewed commit through these functions. Kept here (not in
collect_disposition) so the destructive checker never imports the collector."""

from __future__ import annotations


def git_head_sha(repo_dir):
    """Return the HEAD sha of repo_dir, or None if it cannot be determined (fail-closed)."""
    import subprocess  # noqa: PLC0415 -- keeps subprocess off the offline import path
    try:
        out = subprocess.run(["git", "-C", repo_dir, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def git_worktree_clean(repo_dir):
    """True only if the git worktree has NO tracked-modified AND NO untracked changes. Fail-closed:
    any error => treated as dirty. A repo_sha only identifies the merged commit if the tree is clean."""
    import subprocess  # noqa: PLC0415
    try:
        out = subprocess.run(["git", "-C", repo_dir, "status", "--porcelain"],
                             capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() == ""
    except Exception:  # noqa: BLE001
        return False
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_disposition_provenance.py`
Expected: 3 `PASS` lines, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/disposition_provenance.py infra/database/schema-placement/tests/test_disposition_provenance.py
git commit -m "feat(schema-placement): disposition_provenance.py (public git checks, SP026)"
```

---

### Task 2: Refactor ALL provenance consumers onto `disposition_provenance`

Deleting the collector's git helpers breaks **every** consumer at once — the collector's own call sites, `verify_census`'s CN017 preflight, and three test stub sites. They change together (behavior-preserving). This task leaves NO reference to `collect_disposition._git_*`.

**Files:**
- Modify: `collect_disposition.py` (delete `_git_head_sha`/`_git_worktree_clean` defs at `:591`/`:601`; import `disposition_provenance`; call `dp.*` at `:650`/`:654`; fix comments `:621`/`:648`)
- Modify: `verify_census.py` (import `disposition_provenance`; switch the CN017 preflight at `:259-260` to `dp.*`)
- Modify: `tests/test_collect_disposition.py` (retarget BOTH stub sites: `_stub_git_provenance` at `:212-218` and the inline provenance patch in `_prep_provenance_env` at `:388-397`)
- Modify: `tests/test_verify_census.py` (retarget the `test_main_require_clean_checkout_preflight` stub at `:372-382` from `cds._git_*` to `dp.*`)

**Interfaces:**
- Consumes: `disposition_provenance.git_head_sha`, `disposition_provenance.git_worktree_clean`.

- [ ] **Step 1: Retarget every test stub to the provenance module**

In `tests/test_collect_disposition.py`, add near the imports:

```python
import disposition_provenance as dp  # noqa: E402
```

Replace `_stub_git_provenance`/`_restore_git_provenance` (`:212-224`) to save/patch `dp.git_head_sha`/`dp.git_worktree_clean`:

```python
def _stub_git_provenance(head=SHA, clean=True):
    """Patch the shared provenance helpers so collector main() runs without a real merged-main
    checkout. Production has NO --repo-sha bypass (D1); tests inject provenance here and pass
    --expect-repo-sha. Returns the saved originals for _restore_git_provenance."""
    saved = (dp.git_head_sha, dp.git_worktree_clean)
    dp.git_head_sha = lambda *a: head
    dp.git_worktree_clean = lambda *a: clean
    return saved


def _restore_git_provenance(saved):
    dp.git_head_sha, dp.git_worktree_clean = saved
```

Also fix the SECOND stub site inside `_prep_provenance_env` (`:388-397`), which currently saves/patches `cd._git_head_sha`/`cd._git_worktree_clean`: change every `cd._git_head_sha`/`cd._git_worktree_clean` there to `dp.git_head_sha`/`dp.git_worktree_clean` (the `cd.collect_from_db` part of that tuple stays).

In `tests/test_verify_census.py`, add near the imports:

```python
import disposition_provenance as dp  # noqa: E402
```

In `test_main_require_clean_checkout_preflight` (`:372-382`), change `saved = (cds._git_head_sha, cds._git_worktree_clean)` and the three `cds._git_head_sha = ...` / `cds._git_worktree_clean = ...` lines and the restore to use `dp.git_head_sha` / `dp.git_worktree_clean`.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_collect_disposition.py`
Expected: FAIL — the collector and verify_census still define/call `cds._git_*`, so patching `dp.*` does not intercept provenance; provenance-dependent cases fail.

- [ ] **Step 3: Refactor the consumers**

In `collect_disposition.py`: add `import disposition_provenance as dp` beside `import disposition_signing as ds` (`:67`); delete the `_git_head_sha` (`:591`) and `_git_worktree_clean` (`:601`) defs; change the two call sites (`:650`, `:654`) to `dp.git_head_sha(repo_dir)` / `dp.git_worktree_clean(repo_dir)`; update the comments at `:621`/`:648` to say `tests inject provenance by patching disposition_provenance.git_head_sha / git_worktree_clean`.

In `verify_census.py`: add `import disposition_provenance as dp` beside `import disposition_signing as ds` (`:33`); in the CN017 preflight change `cds._git_head_sha(vdir)` → `dp.git_head_sha(vdir)` and `cds._git_worktree_clean(vdir)` → `dp.git_worktree_clean(vdir)` (`:259-260`). Leave the local anchor (`TRUSTED_SIGNERS`/`resolve_pinned_key`) untouched — that moves in Task 5. `cds` stays imported (query bundle).

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_collect_disposition.py` (expected: 42 `PASS`).
Then: `uv run --project . --locked python tests/test_verify_census.py` (expected: all 31 `PASS` — the anchor is still local, only provenance moved).

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/collect_disposition.py infra/database/schema-placement/verify_census.py infra/database/schema-placement/tests/test_collect_disposition.py infra/database/schema-placement/tests/test_verify_census.py
git commit -m "refactor(schema-placement): all provenance consumers use disposition_provenance (behavior-preserving)"
```

---

### Task 3: `verify_sidecar_bytes_with_key` in `disposition_signing.py`

**Files:**
- Modify: `disposition_signing.py` (add helper; refactor `verify_detached_with_key` to delegate)
- Modify: `tests/test_check_disposition.py` (mechanism-agreement bool helpers → inline `units` list; this file already imports `disposition_signing as ds`)

**Interfaces:**
- Produces: `verify_sidecar_bytes_with_key(message: bytes, sidecar_bytes: bytes, public_key) -> tuple[bool, str]`.

- [ ] **Step 1: Write the failing tests** — in `tests/test_check_disposition.py`, add two **bool-returning** helpers (before the `__main__` block) and register them in the inline `units` list at `~:465`:

```python
def _sidecar_bytes_agree():
    priv, _pp, pub_pem = _ephemeral_keypair()
    pub = ds.load_public_key_pem(pub_pem)
    msg = b'{"kind":"evidence_snapshot"}'
    sidecar_bytes = json.dumps(ds.build_sig_sidecar(msg, priv)).encode("utf-8")
    ok, _ = ds.verify_sidecar_bytes_with_key(msg, sidecar_bytes, pub)
    return ok is True


def _sidecar_bytes_bad_json_fails_closed():
    _priv, _pp, pub_pem = _ephemeral_keypair()
    pub = ds.load_public_key_pem(pub_pem)
    ok, reason = ds.verify_sidecar_bytes_with_key(b"msg", b"{not json", pub)
    return ok is False and "sidecar" in reason
```

Add to the inline `units` list (`~:465`, alongside `("gate_receipt_pure", _receipt_pure)`):

```python
        ("verify_sidecar_bytes_ok", _sidecar_bytes_agree),
        ("verify_sidecar_bytes_bad_json", _sidecar_bytes_bad_json_fails_closed),
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: FAIL — `AttributeError: module 'disposition_signing' has no attribute 'verify_sidecar_bytes_with_key'` (reported as a FAIL unit).

- [ ] **Step 3: Add the helper and refactor the wrapper** — in `disposition_signing.py`, insert `verify_sidecar_bytes_with_key` immediately after `verify_sidecar` (`:100`) and replace `verify_detached_with_key` (`:121-132`):

```python
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
```

- [ ] **Step 4: Run to verify it passes (and no regression)**

Run: `uv run --project . --locked python tests/test_check_disposition.py` (expected: all units `ok`, incl. the two new ones).
Then: `uv run --project . --locked python tests/test_verify_census.py` (expected: 31 `PASS` — `verify_detached_with_key` behavior identical).

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/disposition_signing.py infra/database/schema-placement/tests/test_check_disposition.py
git commit -m "feat(schema-placement): verify_sidecar_bytes_with_key mechanism helper (SP026)"
```

---

### Task 4: `disposition_trust.py` (new anchor + `ResolvedSigner`)

**Files:**
- Create: `infra/database/schema-placement/disposition_trust.py`
- Test: `infra/database/schema-placement/tests/test_disposition_trust.py`

**Interfaces:**
- Produces: `TRUSTED_SIGNERS`, `_KEY_ID_RE`, `DEFAULT_KEYS_DIR`, `ResolvedSigner(key_id, public_key, spki_sha256, pubkey_path, pem_sha256)`, `resolve_pinned_key(keys_dir, key_id) -> tuple[ResolvedSigner | None, str]`.

- [ ] **Step 1: Write the failing tests** — `tests/test_disposition_trust.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_disposition_trust.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'disposition_trust'`.

- [ ] **Step 3: Create `disposition_trust.py`**:

```python
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_disposition_trust.py`
Expected: 7 `PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/disposition_trust.py infra/database/schema-placement/tests/test_disposition_trust.py
git commit -m "feat(schema-placement): disposition_trust.py source-constant anchor + ResolvedSigner (SP026)"
```

---

### Task 5: Migrate `verify_census.py` onto the shared anchor

Provenance already moved in Task 2. This task moves the ANCHOR: delete verify_census's local anchor, import `disposition_trust`, use `signer.public_key`, reword CN001, and migrate every test that referenced the deleted anchor symbols.

**Files:**
- Modify: `verify_census.py` (delete local anchor; import `dt`; verify via `signer.public_key`; reword CN001 at `:62`; `--keys-dir` default → `dt.DEFAULT_KEYS_DIR`)
- Modify: `tests/test_verify_census.py` (retarget `_trusted` and ALL anchor-referencing tests to `dt`)

**Interfaces:**
- Consumes: `disposition_trust.{TRUSTED_SIGNERS, DEFAULT_KEYS_DIR, resolve_pinned_key, ResolvedSigner}`.

- [ ] **Step 1: Migrate every anchor reference in the tests** — in `tests/test_verify_census.py`:

Add near the imports (Task 2 already added `import disposition_provenance as dp`):

```python
import disposition_trust as dt  # noqa: E402
```

Replace the `_trusted` context manager (`:164-174`) to patch the anchor's home module `dt.TRUSTED_SIGNERS`:

```python
@contextlib.contextmanager
def _trusted(key_id, fingerprint):
    """Temporarily pin a signer id -> SPKI fingerprint in the reviewed source-constant anchor
    (disposition_trust.TRUSTED_SIGNERS, where resolve_pinned_key reads it). Restores afterward."""
    prev = dict(dt.TRUSTED_SIGNERS)
    dt.TRUSTED_SIGNERS[key_id] = fingerprint
    try:
        yield
    finally:
        dt.TRUSTED_SIGNERS.clear()
        dt.TRUSTED_SIGNERS.update(prev)
```

Migrate EVERY remaining `vc.TRUSTED_SIGNERS` / `vc.resolve_pinned_key` / `vc.DEFAULT_KEYS_DIR` reference to `dt.*` — grep first to enumerate (`git grep -nE "vc\.(resolve_pinned_key|TRUSTED_SIGNERS|DEFAULT_KEYS_DIR)" -- tests/test_verify_census.py`). This INCLUDES the **comment** at `:194` (`# vc.TRUSTED_SIGNERS, not this file` → `# disposition_trust.TRUSTED_SIGNERS, not this file`), because the Step-4 grep-guard matches comments too and must reach zero hits. The executable references are at `:289`, `:304`, `:341-342`, `:344`, `:397`:
- `test_resolve_pinned_key_returns_key_object` (`:289`): change `key, reason = vc.resolve_pinned_key(kd, KEY_ID)` → `signer, reason = dt.resolve_pinned_key(kd, KEY_ID)` and assert on the struct (`signer.public_key is not None and signer.spki_sha256 == _fp(pub_pem) and signer.key_id == KEY_ID`).
- `test_verify_uses_pinned_key_object_after_file_swap` (`:304`): `signer, reason = dt.resolve_pinned_key(kd, KEY_ID)`; keep asserting `ds.verify_detached_with_key(snap_bytes, sig_path, signer.public_key)` is ok after swapping the on-disk key.
- `test_committed_prod_key_resolves_and_no_private_material` (`:341-344`): `assert PROD_KEY_ID in dt.TRUSTED_SIGNERS`; `signer, reason = dt.resolve_pinned_key(dt.DEFAULT_KEYS_DIR, PROD_KEY_ID)`; assert `signer is not None`; `for root,_dirs,files in os.walk(dt.DEFAULT_KEYS_DIR): ...`.
- `test_key_id_traversal_rejected_even_with_planted_key` (`:397`): `signer, reason = dt.resolve_pinned_key(kd, "../evil")`; assert `signer is None`.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_verify_census.py`
Expected: FAIL — `main()` still calls the local `resolve_pinned_key` (returning a bare key), and `_trusted` now patches `dt.TRUSTED_SIGNERS` which the local anchor ignores.

- [ ] **Step 3: Migrate the anchor in `verify_census.py`**:

- Add `import disposition_trust as dt` beside `import disposition_signing as ds` (`:33`).
- Delete the local `DEFAULT_KEYS_DIR` (`:36`), `TRUSTED_SIGNERS` (`:45-47`), `_KEY_ID_RE` (`:51`), and the entire `resolve_pinned_key` (`:112-146` — the function ENDS at line 146 (`    return public_key, ""`); do NOT overrun into `_validator` at `:149-153`).
- In `main()` argparse, change the `--keys-dir` default from `DEFAULT_KEYS_DIR` to `dt.DEFAULT_KEYS_DIR`.
- Reword CN001 (`:62`) from `"snapshot signature is missing or does not verify against --verify-key"` to:

```python
    "CN001": "snapshot signature is missing or does not verify against the pinned signer (--key-id resolved through the reviewed TRUSTED_SIGNERS anchor)",
```

- In the verify block (`:277-284`), change:

```python
    public_key, kreason = resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
    if public_key is None:
        print(Diagnostic("CN013", "key-id", kreason).render())
        print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
        return 1
    ok, reason = ds.verify_detached_with_key(snap_bytes, os.path.abspath(args.snapshot_sig), public_key)
```

to:

```python
    signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
    if signer is None:
        print(Diagnostic("CN013", "key-id", kreason).render())
        print("=== CENSUS ACCEPTANCE: 1 BLOCKING ===")
        return 1
    ok, reason = ds.verify_detached_with_key(snap_bytes, os.path.abspath(args.snapshot_sig), signer.public_key)
```

- [ ] **Step 4: Run to verify it passes (with a residual-reference guard)**

Run: `git grep -nE "vc\.(resolve_pinned_key|TRUSTED_SIGNERS|DEFAULT_KEYS_DIR)" -- infra/database/schema-placement/tests/test_verify_census.py` — expected: no output (every reference migrated).
Then: `uv run --project . --locked python tests/test_verify_census.py` — expected: all 31 `PASS` (CN013/CN017 unchanged).
Then: `uv run --project . --locked python tests/test_disposition_trust.py` and `tests/test_collect_disposition.py` — expected: `PASS` (no cross-suite regression).

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/verify_census.py infra/database/schema-placement/tests/test_verify_census.py
git commit -m "refactor(schema-placement): verify_census uses shared disposition_trust anchor + CN001 reword (behavior-preserving)"
```

---

### Task 6: `check_disposition.py` SP026 anchor migration (flags + verify + receipt signer fields)

**Files:**
- Modify: `check_disposition.py` (import `dt`; CODES SP026 reword at `:63`; argparse `--key-id`/`--keys-dir`, remove `--verify-key` at `:566`; SP026 gate uses anchor + bytes-in-hand at `:597-609`; `build_receipt` records signer content, drops `verify_key` path at `:161`)
- Modify: `tests/test_check_disposition.py` (add `_preapply_base`/`_preapply_signed_paths`/`_trusted`; rework the signed preapply case; drop the obsolete `receipt_missing_key_raises` unit; assert signer fields)

**Interfaces:**
- Consumes: `disposition_trust.{DEFAULT_KEYS_DIR, resolve_pinned_key}`, `disposition_signing.verify_sidecar_bytes_with_key`.
- Produces: `build_receipt(*, mode, now_iso, expect_project_ref, doc_bytes, doc_paths, signer, snapshot_signature_sha256, roots, decisions)` (checkout fields added in Task 7); receipt with `signer{key_id,spki_sha256,pem_sha256}` + `snapshot_signature_sha256`; no `verify_key` field.
- `_preapply_base(d) -> (base_argv, snap_obj)`; `_preapply_signed_paths(d, snap) -> (snap_path, sig_path, keys_dir, fp)`.

- [ ] **Step 1: Update the tests** — in `tests/test_check_disposition.py`:

Add imports near the top (beside `import disposition_signing as ds`):

```python
import contextlib  # noqa: E402  (if not already present)
import disposition_trust as dt  # noqa: E402
```

Add the shared helpers + a `_trusted` context manager (bool-returning tests below use them):

```python
KEY_ID = "test-ed25519"

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

def _preapply_base(d):
    """Write a GREEN harden bundle's decisions/entity_map/manifest into dir d; return (base_argv, snap).
    The manifest's evidence_snapshot is set to 'snap.json' — the basename _preapply_signed_paths writes —
    so it resolves within --root d (SP021). The snapshot itself is passed via --snapshot separately."""
    snap, dec, em, man, _sp = harden_bundle()
    man = copy.deepcopy(man)
    man["evidence_snapshot"] = "snap.json"
    for nm, doc in (("dec.json", dec), ("em.json", em), ("man.json", man)):
        with open(os.path.join(d, nm), "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
    base = ["--decisions", os.path.join(d, "dec.json"), "--entity-map", os.path.join(d, "em.json"),
            "--manifest", os.path.join(d, "man.json"), "--now", "2026-07-10T21:00:00Z", "--root", d,
            "--expect-project-ref", "fxoyniqnrlkxfligbxmg"]
    return base, snap

def _preapply_signed_paths(d, snap):
    priv, _pp, pub_pem = _ephemeral_keypair()
    snap_bytes = json.dumps(snap, indent=2, sort_keys=True).encode("utf-8")
    snap_path = os.path.join(d, "snap.json")
    with open(snap_path, "wb") as fh:
        fh.write(snap_bytes)
    sig_path = snap_path + ".sig"
    with open(sig_path, "w", encoding="utf-8") as fh:
        json.dump(ds.build_sig_sidecar(snap_bytes, priv), fh)
    keys_dir = os.path.join(d, "keys")
    os.makedirs(keys_dir, exist_ok=True)
    with open(os.path.join(keys_dir, KEY_ID + ".pub.pem"), "wb") as fh:
        fh.write(pub_pem)
    return snap_path, sig_path, keys_dir, _fp(pub_pem)
```

Add the Task-6 bool helpers (NO checkout flags — there is no SP028 gate yet, so `--key-id` preapply is already GREEN):

```python
def _preapply_anchor_green():
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        with _trusted(KEY_ID, fp):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                 "--key-id", KEY_ID, "--keys-dir", keys_dir, "--receipt-out", receipt_path])
        if rc != 0:
            return False
        rec = json.load(open(receipt_path, encoding="utf-8"))
        return (rec["gate"] == "green" and rec["signer"]["key_id"] == KEY_ID and rec["signer"]["spki_sha256"] == fp
                and "verify_key" not in json.dumps(rec)
                and rec["snapshot_signature_sha256"] == hashlib.sha256(open(sig_path, "rb").read()).hexdigest())

# The SP026 negatives assert the SP026 CODE (not just rc). When Task 7 inserts the SP028 gate BEFORE
# the SP026 gate, a flag-less run would block on SP028 and turn these RED — forcing Task 7 to add
# --allow-unbound-checkout here so execution still reaches the SP026 path (guard against silent masking).
def _preapply_missing_key_blocks():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, _kd, _fp2 = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path])  # no --key-id
        return rc == 1 and "SP026" in buf.getvalue()

def _preapply_unknown_key_blocks():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, _fp2 = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path,
                                 "--key-id", "not-a-signer", "--keys-dir", keys_dir])
        return rc == 1 and "SP026" in buf.getvalue()
```

Register these in the inline `units` list (`~:465`):

```python
        ("preapply_anchor_green", _preapply_anchor_green),
        ("preapply_missing_key_blocks", _preapply_missing_key_blocks),
        ("preapply_unknown_key_blocks", _preapply_unknown_key_blocks),
```

Update the existing `_sig_gate_e2e` (`:350`): it used `--verify-key pub_path`. Replace its GREEN/missing/tampered invocations to write `keys/<KEY_ID>.pub.pem`, wrap in `_trusted(KEY_ID, _fp(pub_pem))`, and pass `--key-id KEY_ID --keys-dir keys_dir` (no checkout flag — Task 7 adds it). Capture stdout on the `missing`/`tampered` branches and assert `"SP026" in out` (not merely `rc == 1`), so Task 7's SP028 insertion cannot silently mask them. Update `_receipt_pure` (`:272`) to call `build_receipt` with the new signature: pass `signer={"key_id":"k","spki_sha256":"00"*32,"pem_sha256":"11"*32}` and `snapshot_signature_sha256="22"*32`, and remove the `extra_paths=...` argument. DELETE `_receipt_missing_key_raises` (`:303`), its pytest wrapper `def test_receipt_missing_key_raises(): assert _receipt_missing_key_raises()` (`:318-319`), and its `units` entry `("receipt_missing_key_raises", _receipt_missing_key_raises)` (`:472`); add a comment there: `# F7 obsolete under SP026: the receipt binds snapshot_signature_sha256 from in-hand sig bytes; there is no second read to guard.`

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: FAIL (non-zero exit). Note: passing `--key-id` before argparse knows it makes `ap.parse_args` raise `SystemExit(2)`, which the `__main__` runner's `except Exception` does NOT catch (SystemExit is a BaseException) — so the run aborts at the first such unit with a traceback rather than printing clean per-unit FAIL lines. A non-zero exit is the valid red signal here; units after the first offender do not run until the impl lands.

- [ ] **Step 3: Implement in `check_disposition.py`**:

- Add `import disposition_trust as dt` beside `import disposition_signing as ds` (`:33`).
- Reword CODES `SP026` (`:63`):

```python
    "SP026": "evidence_snapshot signature is missing or does not verify against the pinned signer (--key-id resolved through the reviewed TRUSTED_SIGNERS anchor); preapply requires a signed snapshot",
```

- In `main()` argparse, remove the `--verify-key` line (`:566`) and add after `--snapshot-sig` (`:565`):

```python
    ap.add_argument("--key-id", default=None, dest="key_id", help="authorized signer id pinned in the TRUSTED_SIGNERS anchor (REQUIRED for preapply; SP026).")
    ap.add_argument("--keys-dir", default=dt.DEFAULT_KEYS_DIR, dest="keys_dir", help="dir holding <key-id>.pub.pem (public key MATERIAL only; the trust anchor is the source constant).")
```

- Replace the SP026 signature gate (`:597-608`) — also update the `:591-596` comment that says `REQUIRES --snapshot-sig + --verify-key` to `--snapshot-sig + --key-id`:

```python
    signer = None
    sig_bytes = b""
    if args.mode not in _SIGNATURE_EXEMPT_MODES:
        if not args.snapshot_sig or not args.key_id:
            dg = Diagnostic("SP026", "snapshot", "preapply requires --snapshot-sig and --key-id (an unsigned snapshot is not trusted)")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        try:
            with open(os.path.abspath(args.snapshot_sig), "rb") as fh:
                sig_bytes = fh.read()
        except OSError as exc:
            dg = Diagnostic("SP026", "snapshot", f"cannot read signature sidecar ({type(exc).__name__})")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        signer, kreason = dt.resolve_pinned_key(os.path.abspath(args.keys_dir), args.key_id)
        if signer is None:
            dg = Diagnostic("SP026", "snapshot", kreason)
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
        ok, reason = ds.verify_sidecar_bytes_with_key(doc_bytes["snapshot"], sig_bytes, signer.public_key)
        if not ok:
            dg = Diagnostic("SP026", "snapshot", f"signature verification failed: {reason}")
            print(dg.render()); print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ==="); return 1
```

- Replace `build_receipt` (`:161`) signature + the input-recording block (delete the `for name, p in extra_paths.items()` loop and the docstring line referencing `signature / verify-key`):

```python
def build_receipt(*, mode, now_iso, expect_project_ref, doc_bytes, doc_paths, signer, snapshot_signature_sha256, roots, decisions):
    """Records the SHA-256 of the exact bytes the gate validated: the four CLI documents hashed from the
    IN-HAND bytes main() parsed, the pinned SIGNER content, and the snapshot signature bytes' hash (bound
    from the in-hand sig bytes — no second read). ADVISORY; emitted ONLY on a GREEN gate."""
    receipt = {"kind": "disposition_gate_receipt", "gate": "green", "mode": mode, "now": now_iso,
               "expect_project_ref": expect_project_ref, "inputs": {}, "evidence": [],
               "signer": signer, "snapshot_signature_sha256": snapshot_signature_sha256}
    for name, data in doc_bytes.items():
        receipt["inputs"][name] = {"path": doc_paths.get(name), "sha256": hashlib.sha256(data).hexdigest()}
```

(the evidence-refs loop below is unchanged.)

- Replace the receipt-build call site (`:617-630`). Guard on `signer is not None` (defensive: today `_SIGNATURE_EXEMPT_MODES` is empty so signer is always set on GREEN, but a future exempt mode must not build a signer-less receipt):

```python
    if args.receipt_out:
        if signer is None:
            print("SP000: receipt requested but the gate ran signature-exempt (no signer); refusing an incomplete receipt", file=sys.stderr)
            return 1
        doc_paths = {"snapshot": os.path.abspath(args.snapshot), "decisions": os.path.abspath(args.decisions),
                     "entity_map": os.path.abspath(args.entity_map), "manifest": os.path.abspath(args.manifest)}
        signer_meta = {"key_id": signer.key_id, "spki_sha256": signer.spki_sha256, "pem_sha256": signer.pem_sha256}
        snapshot_signature_sha256 = hashlib.sha256(sig_bytes).hexdigest()
        try:
            receipt = build_receipt(mode=args.mode, now_iso=args.now, expect_project_ref=args.expect_project_ref,
                                    doc_bytes=doc_bytes, doc_paths=doc_paths, signer=signer_meta,
                                    snapshot_signature_sha256=snapshot_signature_sha256, roots=roots, decisions=decisions)
            with open(args.receipt_out, "w", encoding="utf-8") as fh:
                json.dump(receipt, fh, indent=2, sort_keys=True)
        except OSError as exc:
            print(f"SP000: gate is GREEN but the receipt could not be produced ({type(exc).__name__}); refusing to emit an incomplete receipt", file=sys.stderr)
            return 1
        print(f"=== gate receipt written: {args.receipt_out} ({len(receipt['evidence'])} evidence files pinned) ===")
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: all units `ok` (incl. `preapply_anchor_green`, `preapply_missing_key_blocks`, `preapply_unknown_key_blocks`, the reworked `signature_gate_end_to_end`, and `gate_receipt_pure`). Re-run `tests/test_verify_census.py` — 31 `PASS`.

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/check_disposition.py infra/database/schema-placement/tests/test_check_disposition.py
git commit -m "feat(schema-placement): check_disposition SP026 anchor migration + content-bound receipt"
```

---

### Task 7: `check_disposition.py` SP028 checkout gate (flags + gate-before-read + truth table + receipt binding)

Introducing the SP028 gate makes a flag-less preapply block. So this task ALSO updates the Task-6 GREEN preapply helpers to add `--allow-unbound-checkout` (authoring), keeping them green.

**Files:**
- Modify: `check_disposition.py` (import `dp`; CODES SP028; three flags; `_checkout_gate` helper; gate before doc read; distinct banner + warning; receipt `checkout_bound`/`production_eligible`/`gate_repo_sha`)
- Modify: `tests/test_check_disposition.py` (add `--allow-unbound-checkout` to the Task-6 GREEN helpers; add SP028 truth-table, gate-before-read, banner, and bound-green bool helpers → inline `units` list)

**Interfaces:**
- Consumes: `disposition_provenance.{git_head_sha, git_worktree_clean}`.
- Produces: `_checkout_gate(expect_gate_repo_sha, require_clean_checkout, allow_unbound) -> (ok, checkout_bound, production_eligible, gate_repo_sha, diagnostic_or_None)`.

- [ ] **Step 1: Write the failing tests** — in `tests/test_check_disposition.py`:

Add `import disposition_provenance as dp  # noqa: E402` and provenance stub helpers:

```python
def _stub_dp(head, clean=True):
    saved = (dp.git_head_sha, dp.git_worktree_clean)
    dp.git_head_sha = lambda *a: head
    dp.git_worktree_clean = lambda *a: clean
    return saved

def _restore_dp(saved):
    dp.git_head_sha, dp.git_worktree_clean = saved
```

Append `"--allow-unbound-checkout"` to the argv of **every** Task-6 preapply helper — the GREEN `_preapply_anchor_green`, BOTH SP026 negatives `_preapply_missing_key_blocks` / `_preapply_unknown_key_blocks`, and the `GREEN`/`missing`/`tampered` invocations inside `_sig_gate_e2e` — so each passes the new SP028 gate (authoring) and execution still reaches the SP026 path. Until this flag is added, the negatives' `"SP026" in out` assertions go RED (they block on SP028), which is the intended guard against SP028 silently masking the SP026 checks. Add the SP028 bool helpers:

```python
def _checkout_matrix():
    g = cd._checkout_gate
    r = []
    r.append(g(None, False, False)[0] is False)                       # (0,0,0) SP028
    r.append(g(None, False, True) == (True, False, False, None, None))  # (0,0,1) authoring
    saved = _stub_dp("deadbeef", clean=True)
    try:
        r.append(g("deadbeef", True, False)[:4] == (True, True, True, "deadbeef"))  # (1,1,0) bound
        r.append(g("cafef00d", True, False)[0] is False)              # wrong gate sha -> SP028
        _restore_dp(saved); saved = _stub_dp("deadbeef", clean=False)
        r.append(g("deadbeef", True, False)[0] is False)              # dirty -> SP028
        _restore_dp(saved); saved = _stub_dp(None, clean=True)
        r.append(g("deadbeef", True, False)[0] is False)              # undeterminable HEAD (git_head_sha->None) -> SP028
    finally:
        _restore_dp(saved)
    r.append(g("deadbeef", False, False)[0] is False)                 # (1,0,0) SP028
    r.append(g(None, True, False)[0] is False)                        # (0,1,0) SP028
    r.append(g("deadbeef", True, True)[0] is False)                   # (1,1,1) SP028
    r.append(g("deadbeef", False, True)[0] is False)                  # (1,0,1) SP028
    r.append(g(None, True, True)[0] is False)                         # (0,1,1) SP028
    return all(r)

def _neither_flag_blocks_sp028():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        buf = io.StringIO()
        with _trusted(KEY_ID, fp), contextlib.redirect_stdout(buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID, "--keys-dir", keys_dir])
    return rc == 1 and "SP028" in buf.getvalue()

def _sp028_precedes_doc_read():
    # a nonexistent snapshot/decisions path + no checkout flags must fail SP028 (rc 1), NOT SP000 (rc 2):
    # the gate refuses before any document read.
    import io
    with tempfile.TemporaryDirectory() as d:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cd.main(["--snapshot", os.path.join(d, "nope.json"), "--decisions", os.path.join(d, "nope.json"),
                          "--entity-map", os.path.join(d, "nope.json"), "--manifest", os.path.join(d, "nope.json"),
                          "--now", "2026-07-10T21:00:00Z", "--root", d, "--expect-project-ref", "fxoyniqnrlkxfligbxmg"])
    return rc == 1 and "SP028" in buf.getvalue()

def _authoring_banner_and_receipt():
    import io
    banner = "=== DISPOSITION GATE (preapply): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ==="  # exact literal (em-dash)
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        out_buf, err_buf = io.StringIO(), io.StringIO()
        with _trusted(KEY_ID, fp), contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID,
                                 "--keys-dir", keys_dir, "--allow-unbound-checkout", "--receipt-out", receipt_path])
        out, err = out_buf.getvalue(), err_buf.getvalue()
        rec = json.load(open(receipt_path, encoding="utf-8"))
    return (rc == 0 and banner in out and "WARNING: unbound checkout" in err
            and rec["checkout_bound"] is False and rec["production_eligible"] is False and rec["gate_repo_sha"] is None)

def _bound_green_receipt():
    import io
    with tempfile.TemporaryDirectory() as d:
        base, snap = _preapply_base(d)
        snap_path, sig_path, keys_dir, fp = _preapply_signed_paths(d, snap)
        receipt_path = os.path.join(d, "receipt.json")
        saved = _stub_dp("deadbeef", clean=True)
        buf = io.StringIO()
        try:
            with _trusted(KEY_ID, fp), contextlib.redirect_stdout(buf):
                rc = cd.main(base + ["--snapshot", snap_path, "--snapshot-sig", sig_path, "--key-id", KEY_ID,
                                     "--keys-dir", keys_dir, "--expect-gate-repo-sha", "deadbeef",
                                     "--require-clean-checkout", "--receipt-out", receipt_path])
            out = buf.getvalue()
            rec = json.load(open(receipt_path, encoding="utf-8"))
        finally:
            _restore_dp(saved)
    return (rc == 0 and "AUTHORING ONLY" not in out and rec["checkout_bound"] is True
            and rec["production_eligible"] is True and rec["gate_repo_sha"] == "deadbeef")
```

Register in the inline `units` list: `("checkout_matrix", _checkout_matrix)`, `("neither_flag_blocks_sp028", _neither_flag_blocks_sp028)`, `("sp028_precedes_doc_read", _sp028_precedes_doc_read)`, `("authoring_banner_and_receipt", _authoring_banner_and_receipt)`, `("bound_green_receipt", _bound_green_receipt)`.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: FAIL (non-zero exit). `_checkout_matrix` errors with `AttributeError: module 'check_disposition' has no attribute '_checkout_gate'`; the new checkout flags are unknown to argparse so those helpers raise `SystemExit(2)` (a BaseException the `__main__` runner's `except Exception` does not catch) → the run aborts at the first offending unit rather than printing clean per-unit FAILs. A non-zero exit is the valid red signal.

- [ ] **Step 3: Implement in `check_disposition.py`**:

- Add `import disposition_provenance as dp` beside `import disposition_trust as dt` (`:33`).
- Add CODES `SP028` after `SP027`:

```python
    "SP028": "checkout-provenance binding failed: for preapply supply either both --expect-gate-repo-sha and --require-clean-checkout (bound) OR --allow-unbound-checkout alone (authoring-only); any other combination is refused, and on the bound path the checker's git HEAD must be determinable, its worktree clean, and equal to the reviewed gate SHA (never the census snapshot's repo_sha)",
```

- Add the `_checkout_gate` helper just above `main`:

```python
def _checkout_gate(expect_gate_repo_sha, require_clean_checkout, allow_unbound):
    """SP028: decide the checkout binding from the flag combination alone, BEFORE any input document is
    read. Returns (ok, checkout_bound, production_eligible, gate_repo_sha, diagnostic_or_None). Only the
    bound path runs a git check, against the checker's own repo dir. Accidental unbound is impossible:
    neither-flag-nor-opt-in is refused."""
    has_gate = bool(expect_gate_repo_sha)
    has_clean = bool(require_clean_checkout)
    has_allow = bool(allow_unbound)
    if has_gate and has_clean and not has_allow:
        cdir = os.path.dirname(os.path.abspath(__file__))
        head = dp.git_head_sha(cdir)
        if not head or not dp.git_worktree_clean(cdir):
            return False, None, None, None, Diagnostic("SP028", "checkout", "checker checkout is DIRTY or its git HEAD is undeterminable — run preapply from a clean checkout at --expect-gate-repo-sha")
        if head != expect_gate_repo_sha:
            return False, None, None, None, Diagnostic("SP028", "checkout", f"checker git HEAD {head[:12]} != --expect-gate-repo-sha {expect_gate_repo_sha[:12]} (never the census snapshot repo_sha)")
        return True, True, True, expect_gate_repo_sha, None
    if (not has_gate) and (not has_clean) and has_allow:
        return True, False, False, None, None
    return False, None, None, None, Diagnostic("SP028", "checkout", "supply BOTH --expect-gate-repo-sha and --require-clean-checkout (bound), OR --allow-unbound-checkout alone (authoring-only); any other combination is refused")
```

- Add the three flags in argparse (after `--keys-dir`):

```python
    ap.add_argument("--expect-gate-repo-sha", default=None, dest="expect_gate_repo_sha", help="the reviewed merged commit the CHECKER must run from (bound preapply; SP028). Independent of the census snapshot repo_sha.")
    ap.add_argument("--require-clean-checkout", action="store_true", dest="require_clean_checkout", help="with --expect-gate-repo-sha, enforce the checker's own worktree is clean and at that SHA (SP028).")
    ap.add_argument("--allow-unbound-checkout", action="store_true", dest="allow_unbound_checkout", help="explicit opt-in for authoring-only unbound runs (production_eligible=false); refused together with the binding flags (SP028).")
```

- Immediately after `args = ap.parse_args(argv)` (BEFORE the document-read `try:` block), run the SP028 gate:

```python
    ok, checkout_bound, production_eligible, gate_repo_sha, cdiag = _checkout_gate(
        args.expect_gate_repo_sha, args.require_clean_checkout, args.allow_unbound_checkout)
    if not ok:
        print(cdiag.render())
        print(f"=== DISPOSITION GATE ({args.mode}): 1 BLOCKING ===")
        return 1
```

- Replace the final GREEN banner (`:631`) with the bound/authoring split:

```python
    if checkout_bound:
        print(f"=== DISPOSITION GATE ({args.mode}): GREEN ===")
    else:
        print("WARNING: unbound checkout — the trust anchor was trusted WITHOUT a reviewed gate SHA; authoring-only, not valid for production apply", file=sys.stderr)
        print(f"=== DISPOSITION GATE ({args.mode}): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ===")
    return 0
```

- Extend `build_receipt` to record the checkout binding — new signature + header dict:

```python
def build_receipt(*, mode, now_iso, expect_project_ref, doc_bytes, doc_paths, signer, snapshot_signature_sha256,
                  gate_repo_sha, checkout_bound, production_eligible, roots, decisions):
    ...
    receipt = {"kind": "disposition_gate_receipt", "gate": "green", "mode": mode, "now": now_iso,
               "expect_project_ref": expect_project_ref, "inputs": {}, "evidence": [],
               "signer": signer, "snapshot_signature_sha256": snapshot_signature_sha256,
               "gate_repo_sha": gate_repo_sha, "checkout_bound": checkout_bound,
               "production_eligible": production_eligible}
```

- Pass the three values at the receipt-build call site:

```python
            receipt = build_receipt(mode=args.mode, now_iso=args.now, expect_project_ref=args.expect_project_ref,
                                    doc_bytes=doc_bytes, doc_paths=doc_paths, signer=signer_meta,
                                    snapshot_signature_sha256=snapshot_signature_sha256,
                                    gate_repo_sha=gate_repo_sha, checkout_bound=checkout_bound,
                                    production_eligible=production_eligible, roots=roots, decisions=decisions)
```

Update `_receipt_pure` in the test to pass `gate_repo_sha=None, checkout_bound=False, production_eligible=False`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run --project . --locked python tests/test_check_disposition.py`
Expected: all units `ok`, including `checkout_matrix`, `neither_flag_blocks_sp028`, `sp028_precedes_doc_read`, `authoring_banner_and_receipt`, `bound_green_receipt`, and the Task-6 GREEN helpers (now with `--allow-unbound-checkout`).

- [ ] **Step 5: Commit**

```bash
git add infra/database/schema-placement/check_disposition.py infra/database/schema-placement/tests/test_check_disposition.py
git commit -m "feat(schema-placement): check_disposition SP028 checkout gate + production_eligible receipt"
```

---

### Task 8: Explicit committed-census re-verification (real verifier command)

**Files:**
- Modify: `infra/database/schema-placement/tests/test_verify_census.py` (add a test that runs the real `verify_census` entrypoint against the committed prod census; register in `ALL`)

**Interfaces:**
- Consumes: the committed `evidence/census-prod-*.json` (+ `.sig`), `keys/prod-disposition-ed25519-2026-07.pub.pem`, the real `dt.TRUSTED_SIGNERS` anchor (no monkeypatch). `QB = cds.query_bundle_sha256()` (unchanged by SP026; equals the census bundle `217ff3…`). `repo_sha` = the census's own `a67d95ee…`.

- [ ] **Step 1: Write the test (proof, passes immediately)** — add to `tests/test_verify_census.py`:

```python
def test_committed_prod_census_reverifies_through_shared_anchor():
    # SP026: the REAL committed production census must still verify GREEN through the refactored
    # disposition_trust anchor — proving the refactor is behavior-preserving for genuine evidence.
    # This runs the ACTUAL verifier entrypoint; it does NOT rely on the CI 'no new snapshots' path.
    import glob
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    snaps = sorted(glob.glob(os.path.join(here, "evidence", "census-prod-*.json")))
    assert snaps, "no committed census artifact found"
    snap = snaps[-1]
    sig = snap + ".sig"
    repo_sha = json.load(open(snap, encoding="utf-8"))["repo_sha"]
    keys_dir = os.path.join(here, "keys")
    rc = vc.main(["--snapshot", snap, "--snapshot-sig", sig, "--key-id", PROD_KEY_ID, "--keys-dir", keys_dir,
                  "--expect-project-ref", PROJECT, "--expect-database", "postgres", "--expect-schemas", "public",
                  "--expect-repo-sha", repo_sha, "--require-role-markers", ",".join(MARKERS),
                  "--expect-query-bundle-sha256", QB])
    assert rc == 0
```

Register `("committed_prod_census_reverifies", test_committed_prod_census_reverifies_through_shared_anchor)` in `ALL`.

- [ ] **Step 2: Run to verify it passes (proof, not red)**

Run: `uv run --project . --locked python tests/test_verify_census.py`
Expected: `PASS committed_prod_census_reverifies` (verified independently — the real command already prints `=== CENSUS ACCEPTANCE: GREEN (118 relations, scope ['public']) ===`). If it FAILS, the shared-anchor refactor changed behavior — STOP and fix, do not weaken the test.

- [ ] **Step 3: Commit**

```bash
git add infra/database/schema-placement/tests/test_verify_census.py
git commit -m "test(schema-placement): explicit real-command re-verify of the committed prod census (SP026)"
```

---

### Task 9: CI + tooling inventory

**Files:**
- Modify: `.github/workflows/schema-placement-ci.yml` (add the two new suites to the offline loop at `:32`)
- Modify: `infra/database/schema-placement/ci/verify_committed_census.sh` (add the two new modules to `TOOLING` at `:17`)

- [ ] **Step 1: Add the new suites to CI** — in `.github/workflows/schema-placement-ci.yml`, change the loop (`:32`) to:

```yaml
          for t in test_disposition_schema test_check_disposition test_collect_disposition test_verify_census test_disposition_trust test_disposition_provenance; do
```

- [ ] **Step 2: Add the new modules to the artifact tooling inventory** — in `ci/verify_committed_census.sh`, change `TOOLING` (`:17`) to:

```bash
TOOLING=("$SP/verify_census.py" "$SP/collect_disposition.py" "$SP/disposition_signing.py" "$SP/disposition_trust.py" "$SP/disposition_provenance.py" "$SP/disposition.schema.json" "$SP/keys")
```

- [ ] **Step 3: Verify locally**

Run: `uv run --project . --locked python tests/test_disposition_trust.py && uv run --project . --locked python tests/test_disposition_provenance.py`
Then: `bash ci/verify_committed_census.sh` (expected: "no census artifacts added on this branch (vs origin/main) — nothing to verify", exit 0 — SP026 adds no census; the explicit re-verify is Task 8).
Then: `git diff --check $(git hash-object -t tree /dev/null) HEAD -- infra/database/schema-placement .github/workflows/schema-placement-ci.yml` (expected: no output).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/schema-placement-ci.yml infra/database/schema-placement/ci/verify_committed_census.sh
git commit -m "ci(schema-placement): run new trust/provenance suites + add modules to census tooling inventory"
```

---

### Task 10: Full-suite green, whitespace, cross-engine IRP, finish branch (operator-gated)

**Files:** none (verification + governance).

- [ ] **Step 1: Run every locked suite (fail-loud, unmasked)**

Run, from `infra/database/schema-placement/`:

```bash
rc=0
for t in test_disposition_schema test_check_disposition test_collect_disposition test_verify_census test_disposition_trust test_disposition_provenance; do
  echo "=== $t ==="
  uv run --project . --locked python "tests/$t.py" || { echo "FAILED: $t"; rc=1; }
done
exit $rc
```

Expected: every suite exits 0 and the loop exits 0. Confirm counts: verify_census 32 (31 + committed-census reverify), collector 42, trust 7, provenance 3, and every check_disposition unit `ok`.

- [ ] **Step 2: No-`--verify-key` audit (exact match, no false-fail)**

Run: `git grep -n -- '--verify-key' -- infra/database/schema-placement ':(exclude)infra/database/schema-placement/evidence'` and `git grep -n 'args\.verify_key' -- infra/database/schema-placement`.
Expected: NO hits for either (the flag and its dest are fully removed). The benign crypto-mechanism prose "verify key" in `disposition_signing.py:97,99,117` and `verify_census.py` is EXPECTED and permitted — do not grep for it. Confirm `evidence/` is byte-identical: `git diff --stat main..HEAD -- infra/database/schema-placement/evidence` prints nothing.

- [ ] **Step 3: Whitespace / conflict-marker check**

Run: `git diff --check $(git hash-object -t tree /dev/null) HEAD -- infra/database/schema-placement .github/workflows/schema-placement-ci.yml`
Expected: no output (clean).

- [ ] **Step 4: Cross-engine IRP (mandatory pre-merge)**

Run the grounded Claude audit + Codex on `main..HEAD`:
- Claude: `superpowers:requesting-code-review` / IRP grounded-audit over the diff.
- Codex: `ssh olares-mesh 'export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; cd /home/olares/code/apex/apex-schema-sp026; codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-5.5 -c model_reasoning_effort=xhigh review --base main'`
Fold findings; fix Critical/Important; re-run the full suite.

- [ ] **Step 5: Finish the branch (operator-gated)**

Use `superpowers:finishing-a-development-branch`. Open a governed PR (`schema-placement/sp026-trust-anchor-parity` → `main`); squash-merge after green CI + IRP, no admin bypass. Do NOT merge without explicit operator authorization. All production mutations + A1–A3 remain HELD; overlays + the first 3–5-view cluster follow after SP026 lands.

---

## Self-review notes

- **Spec coverage:** §2 graph → Tasks 1–7; §3 helper → Task 3; §4 anchor/`ResolvedSigner` → Task 4; §5 provenance → Task 1; §6 collector refactor → Task 2; §7 verify_census refactor → Tasks 2 (provenance) + 5 (anchor); §8 flags/gate-order/verify/banner → Tasks 6–7; §9 receipt → Tasks 6–7; §10 SP026/SP028/CN001 text → Tasks 5–7; §11 CI/inventory → Task 9; §12 test matrix → Tasks 1,3,4,6,7,8; §13 acceptance → Task 10.
- **Adversarial matrix mapping (§12):** item 1 (Task 6 `_preapply_missing_key_blocks`, asserts the SP026 code); item 2 (removed `--verify-key` rejected — covered by the Task 10 exact grep, no dedicated unit); items 3–8 (Task 4); 9 (Tasks 6–7); 10 (Task 7, all 8 flag combos + `git_head_sha→None` + gate-before-read); 11 (Task 8, real command); 12 (Task 3).
- **Cross-engine review folded (Codex + 3 Claude lenses):** all-consumers provenance switch co-located in Task 2 (no broken intermediate state); Task 5 migrates every `vc.*` anchor reference (not just two) + rewords CN001; Task 6 uses no `--allow-unbound-checkout` (added in Task 7); `test_check_disposition` registrations target the inline `units` list of bool helpers (no phantom `ALL`); `_checkout_matrix` covers all 8 flag combos; a gate-before-read (`SP028` not `SP000`) test added; `_preapply_base`/`_preapply_signed_paths` defined concretely from the existing `harden_bundle()` 5-tuple with manifest `evidence_snapshot` basename reconciliation; receipt guarded on `signer is not None`; Task 10 grep is exact (`--verify-key`/`args.verify_key`) and the suite loop is fail-loud (`rc` accumulator); line anchors corrected (SP026 :63, DEFAULT_KEYS_DIR :36, `resolve_pinned_key` :112-146, verify block :277-284).
- **Second-pass cross-engine fixes folded (Codex + 3 Claude lenses on v2):** SP026 negatives now assert the `SP026` code (not just rc) and Task 7 adds `--allow-unbound-checkout` to every preapply helper so SP028 cannot mask them; `_checkout_matrix` covers all 8 combos + `git_head_sha→None`; authoring test asserts the full literal banner + stderr warning; Task 5 delete range corrected to `:112-146` (no `_validator` overrun) and the `:194` comment migrated; the obsolete `test_receipt_missing_key_raises` wrapper (`:318-319`) removed; red-step notes acknowledge argparse `SystemExit` aborts the runner.
- **Type consistency:** `resolve_pinned_key -> (ResolvedSigner|None, str)` used identically in Tasks 4/5/6; `_checkout_gate -> (ok, checkout_bound, production_eligible, gate_repo_sha, diag)` used identically in Task 7 tests + impl; `build_receipt` signature evolves once (Task 6 adds `signer`/`snapshot_signature_sha256`, Task 7 adds `gate_repo_sha`/`checkout_bound`/`production_eligible`) with every call site + `_receipt_pure` updated in the same task.
