# SP026 — Checker Trust-Anchor Parity (design)

**Status:** APPROVED (operator-ratified, two review rounds). Next step is the TDD implementation plan. No implementation, no database, no production action is authorized by this commit.

**Goal:** Extend the ratified source-constant trust anchor (`TRUSTED_SIGNERS` + `resolve_pinned_key`, from `verify_census` @ de3fa5de) to `check_disposition.py`'s destructive-DDL preapply gate, replacing the caller-selectable `--verify-key` with an anchor-resolved `--key-id`, and bind the checker's own checkout to a reviewed gate commit — closing the same H1 (caller-selectable signer) and H3 (resolve→re-open TOCTOU) defects on the last gate before destructive apply.

**Lane:** `schema-placement/sp026-trust-anchor-parity`, branched from clean `main@965c466d`, isolated host worktree `/home/olares/code/apex/apex-schema-sp026`.

## Global constraints (verbatim, operator-ratified)

- Dedicated module `disposition_trust.py` holds signer policy; `disposition_signing.py` stays crypto-mechanism only.
- Extract shared git checks into `disposition_provenance.py` (option b), exposed as **public** cross-module functions `git_head_sha()` / `git_worktree_clean()` — three consumers make the abstraction non-premature; importing the collector into the destructive checker is the wrong dependency direction.
- Checkout-provenance diagnostic is **`SP028`** (SP027 already protects the destructive-evidence floor).
- Bind the receipt to the **exact signature bytes verified**, not a later re-read.
- The trust map is immutable from the production API — no public caller-supplied trust map; tests monkeypatch the module constant.
- Never compare the checker's HEAD to the census snapshot's older `repo_sha`.
- Accidental unbound execution must be **impossible**: authoring mode is an explicit opt-in, not a silent default. A warning is not a security boundary.
- All production mutations and A1–A3 remain HELD; overlays and the first 3–5-view cluster follow after SP026 lands.

## 1. Problem

The offline checker's preapply gate is the last barrier before destructive DDL. Today (`check_disposition.py` @ `965c466d`):

- `:566` `--verify-key PATH` is **caller-selectable** — any forged keypair the caller points at is trusted (H1).
- `:603` `ds.verify_detached(doc_bytes["snapshot"], abspath(snapshot_sig), abspath(verify_key))` **re-opens the key by path** at verify time (H3), and the receipt (`:620–621`) records the caller `verify_key` **path** as if authoritative.

`verify_census` already closed this class with a source-constant anchor + key-object verification. SP026 brings the destructive gate to the same standard and adds a checkout-binding contract appropriate to a gate that runs from a *later* reviewed commit than the census it validates (the committed census was signed at `repo_sha a67d95ee`; the checker runs from the SP026 merge commit — the two are different by design).

## 2. Architecture — module dependency graph

```
disposition_signing.py       crypto mechanism only
disposition_trust.py         signer policy + key resolution;  imports disposition_signing
disposition_provenance.py    git HEAD / clean-worktree checks only  (public git_head_sha / git_worktree_clean)

collect_disposition.py       imports signing + provenance
verify_census.py             imports signing + trust + provenance  (+ collect_disposition for query_bundle_sha256, unchanged)
check_disposition.py         imports signing + trust + provenance
```

Each unit has one responsibility, a well-defined interface, and is independently testable. `disposition_trust.py` is the single reviewable trust root; `disposition_provenance.py` is the single home for checkout-provenance checks.

## 3. `disposition_signing.py` — mechanism (bytes-in-hand verification)

Add a mechanism-level helper so a caller can verify the **exact sidecar bytes it already holds** (no second read):

```python
def verify_sidecar_bytes_with_key(message: bytes, sidecar_bytes: bytes, public_key) -> tuple[bool, str]:
    """Verify a detached signature from sidecar bytes the caller ALREADY HAS IN HAND, against a
    public key OBJECT the caller already loaded and pinned. Parses the sidecar bytes (fail-closed)
    and delegates to verify_sidecar. Reads NOTHING from disk — the bytes verified are exactly the
    bytes the caller hashes into its receipt, closing the verify-then-rehash TOCTOU."""
    try:
        sidecar = json.loads(sidecar_bytes)
    except ValueError as exc:
        return False, f"cannot parse signature sidecar bytes ({type(exc).__name__})"
    return verify_sidecar(message, sidecar, public_key)
```

Refactor `verify_detached_with_key(message, sig_path, public_key)` to read the sidecar bytes once and delegate to `verify_sidecar_bytes_with_key` — **behavior preserved** (it remains the path-based convenience wrapper for existing callers, e.g. `verify_census`). `verify_sidecar`, `load_public_key_pem`, `public_key_fingerprint` are unchanged. `verify_detached(message, sig_path, pubkey_path)` (path-based *key*) is retained for its non-gate callers (e.g. `verify_snapshot_files`); after SP026 no active security gate resolves a key by caller-supplied path — an acceptance grep asserts this.

## 4. `disposition_trust.py` — signer policy (new)

Holds the reviewed trust root, moved verbatim from `verify_census` and tightened per the immutable-anchor rule:

- `TRUSTED_SIGNERS = {"prod-disposition-ed25519-2026-07": "c75785cd002977f3ce4794f55ea3b1437be5c60a07c36727372c53bd3dc592ca"}`
- `_KEY_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")`
- `DEFAULT_KEYS_DIR = <this module's dir>/keys` (co-located in `schema-placement/`, so still resolves to `keys/`)
- A structured resolved-signer value object:

```python
@dataclass(frozen=True)
class ResolvedSigner:
    key_id: str          # the authorized signer id
    public_key: object    # in-memory Ed25519 public key object (already loaded)
    spki_sha256: str      # SPKI SHA-256, == the pinned TRUSTED_SIGNERS fingerprint
    pubkey_path: str      # resolved realpath of the loaded .pub.pem
    pem_sha256: str       # SHA-256 of the EXACT PEM bytes loaded (for the receipt)
```

- `resolve_pinned_key(keys_dir, key_id) -> tuple[ResolvedSigner | None, str]` — **no public `trusted_signers` parameter**; it reads the module constant. Steps (all fail-closed, returning `(None, reason)`):
  1. `key_id` is a known signer in `TRUSTED_SIGNERS` (the reviewed anchor).
  2. `key_id` matches `_KEY_ID_RE` (rejects path separators / `..`).
  3. realpath containment: the resolved `keys_dir/<key_id>.pub.pem` is contained within the realpath'd `keys_dir`.
  4. read the PEM bytes once; `public_key = ds.load_public_key_pem(pem_bytes)`; `pem_sha256 = sha256(pem_bytes)`.
  5. `ds.public_key_fingerprint(public_key)` equals the pinned fingerprint (else reject).
  6. return the populated `ResolvedSigner`.

Tests exercise policy by monkeypatching `disposition_trust.TRUSTED_SIGNERS` (module constant) — the existing `verify_census` `_trusted` context manager re-points to this module. No production caller can inject a trust map.

## 5. `disposition_provenance.py` — git checks (new)

Holds only the two pure git-subprocess helpers, moved from `collect_disposition.py` and **renamed to public cross-module names**:

- `git_head_sha(repo_dir) -> str | None`
- `git_worktree_clean(repo_dir) -> bool`

No crypto, no policy. `query_bundle_sha256()` stays in `collect_disposition.py` (it is a collector/query concern, not provenance).

## 6. `collect_disposition.py` — refactor (behavior-preserving)

Remove the two git helpers' definitions (they move to `disposition_provenance` under public names); import and call `disposition_provenance.git_head_sha` / `git_worktree_clean`. The collector's `--expect-repo-sha` / clean-worktree provenance enforcement is unchanged in behavior. Collector imports **signing + provenance only** (never trust). Its 42-case suite stays green (its `_stub_git_provenance` monkeypatch retargets to the provenance module's public names).

## 7. `verify_census.py` — refactor (no behavior change)

- Delete its local `TRUSTED_SIGNERS` / `_KEY_ID_RE` / `DEFAULT_KEYS_DIR` / `resolve_pinned_key`; import them from `disposition_trust`.
- `main()` reads `signer.public_key` from the returned `ResolvedSigner` and calls `ds.verify_detached_with_key(snap_bytes, abspath(snapshot_sig), signer.public_key)` (its existing path-wrapper call is fine; it emits no receipt so it needs no bytes-in-hand change).
- Its `--require-clean-checkout` preflight switches `cds._git_head_sha`/`cds._git_worktree_clean` to `disposition_provenance.git_head_sha`/`git_worktree_clean` (`cds` is still imported for `query_bundle_sha256()`).
- CN013 / CN017 semantics and all flags are unchanged. The 31-case `test_verify_census` suite stays green (its `_trusted` monkeypatch now targets `disposition_trust.TRUSTED_SIGNERS`).

## 8. `check_disposition.py` — SP026 + SP028 hardening

**Flags:**
- Remove `--verify-key`.
- Add `--key-id` (dest `key_id`; required for preapply, enforced by the same default-deny mode gate as `--snapshot-sig`).
- Add `--keys-dir` (default `disposition_trust.DEFAULT_KEYS_DIR`).
- Add `--expect-gate-repo-sha` (dest `expect_gate_repo_sha`, default `None`).
- Add `--require-clean-checkout` (store_true).
- Add `--allow-unbound-checkout` (store_true) — the explicit opt-in that makes accidental unbound execution impossible.

**Checkout-provenance gate (SP028) — runs IMMEDIATELY after argument parsing, before any input document is read or trusted.** It binds the trust modules + `keys/` to a reviewed commit before they are loaded, measured against the checker's own repo dir (`dirname(abspath(__file__))`) via `disposition_provenance`. The flag combination alone determines eligibility; only the bound path performs a git check:

| `--expect-gate-repo-sha` | `--require-clean-checkout` | `--allow-unbound-checkout` | outcome |
|---|---|---|---|
| absent | absent | absent | **SP028** (accidental unbound is refused) |
| absent | absent | present | Authoring-only GREEN — `checkout_bound=false`, `production_eligible=false` |
| present | present | absent | Bound GREEN — enforce HEAD determinable **and** worktree clean **and** `HEAD == expect_gate_repo_sha` (else **SP028**); `checkout_bound=true`, `production_eligible=true` |
| any other combination | | | **SP028** |

"Any other combination" includes exactly-one-of-the-pair, the pair supplied together with `--allow-unbound-checkout`, and any binding flag alongside the opt-in — all refused. There are exactly two GREEN paths: **bound** (both binding flags, no opt-in) and **authoring-only** (opt-in, no binding flags). The gate NEVER references `snapshot.repo_sha`.

**Authoring-only output is visibly distinct.** On the authoring path the checker still verifies the signature (SP026) and runs the semantic gate, but its GREEN banner on **stdout** is the distinct:

```
=== DISPOSITION GATE (preapply): GREEN — AUTHORING ONLY; CHECKOUT UNBOUND ===
```

and it additionally prints an advisory `WARNING: unbound checkout — the trust anchor was trusted WITHOUT a reviewed gate SHA; authoring-only, not valid for production apply` to **stderr** (a second signal, not the boundary). The bound path prints the existing `=== DISPOSITION GATE (preapply): GREEN ===`. The security boundary is the flag gate (accidental unbound is impossible — it blocks SP028) plus the receipt's `production_eligible`, never a warning: production preapply runbooks and the future apply runner MUST pass the two binding flags and MUST reject any receipt whose `production_eligible != true`.

**Self-bootstrapping caveat (honesty note).** The gate measures the checker's own checkout using `disposition_provenance` helpers that live *in that same checkout* — exactly as `verify_census`'s CN017 preflight already does. It raises the bar against accidental drift (dirty tree / wrong commit); it cannot vouch for a fully-compromised worktree, because the git-check code is itself part of the bound set. The operator MUST launch the checker from a known-good clone; SP028 is drift-detection plus accident-prevention, not a defense against a hostile checkout.

**Signature gate (SP026), read-once / verify-in-hand** — runs only AFTER the SP028 gate passes:
1. the snapshot bytes are read once into `doc_bytes["snapshot"]` (the checker reads/trusts no input document until the SP028 gate has passed).
2. read the sidecar bytes once: `sig_bytes = open(abspath(snapshot_sig), "rb").read()` (fail-closed → SP026).
3. resolve the signer once: `signer, reason = dt.resolve_pinned_key(keys_dir, key_id)`; if `None` → SP026.
4. verify the in-hand bytes: `ok, reason = ds.verify_sidecar_bytes_with_key(doc_bytes["snapshot"], sig_bytes, signer.public_key)`; if not `ok` → SP026.
5. carry `signer` and `sha256(sig_bytes)` into the receipt (§9).

If either `--snapshot-sig` or `--key-id` is missing for a non-exempt mode, block SP026 before resolving anything (unchanged default-deny posture; `_SIGNATURE_EXEMPT_MODES` stays empty).

## 9. Receipt schema (`build_receipt`)

`build_receipt` no longer takes `extra_paths={snapshot_sig, verify_key}`. It records signer **content** and the checkout binding, not a caller key path:

- `signer`: `{ "key_id": ..., "spki_sha256": ..., "pem_sha256": ... }`
- `snapshot_signature_sha256`: SHA-256 of the exact sidecar bytes verified in §8 (steps 2/4)
- `gate_repo_sha`: the enforced `--expect-gate-repo-sha` on the bound path, else `null`
- `checkout_bound`: `true` on the bound path, `false` on the authoring path
- `production_eligible`: `true` on the bound path, `false` on the authoring path (moves in lockstep with `checkout_bound`)
- The existing four document input digests (`snapshot` / `decisions` / `entity_map` / `manifest` SHA-256) and the evidence-file digests are unchanged.
- **No authoritative `verify_key` path field.**

The future apply runner MUST require `production_eligible == true` (an authoring-only receipt can never authorize a production apply).

## 10. Diagnostic codes

- **SP026 (reword):** "evidence_snapshot signature is missing or does not verify against the pinned signer (`--key-id` resolved through the reviewed `TRUSTED_SIGNERS` anchor); preapply requires a signed snapshot." (No `--verify-key`.)
- **SP028 (new):** "checkout-provenance binding failed: for preapply, supply either both `--expect-gate-repo-sha` and `--require-clean-checkout` (bound) OR `--allow-unbound-checkout` alone (authoring-only); any other combination — including neither — is refused, and on the bound path the checker's git HEAD must be determinable, its worktree clean, and HEAD must equal the reviewed gate SHA (never the census snapshot's `repo_sha`)."

Audit and update any stale diagnostic text referencing the old caller-key model (SP026, and the CN-series docstrings/messages in `verify_census`), so no active code text names `--verify-key`.

## 11. CI + tooling inventory

- `.github/workflows/schema-placement-ci.yml` — add `test_disposition_trust` (and `test_disposition_provenance` if a separate file is used) to the offline-suite loop so CI runs every new test file. Register each new test module in its dual-runner `ALL` list.
- `ci/verify_committed_census.sh` — add `disposition_trust.py` and `disposition_provenance.py` to the `TOOLING` inventory (line 17), so a **future** census's added-in-PR tooling-unchanged check covers the new modules. This does not affect the SP026 PR itself (SP026 adds no census; `SNAPS` is empty and the gate correctly exits "nothing to verify") — consistent with the gate's by-design tolerance of legitimate tooling evolution.

## 12. Test strategy (TDD-first)

New `test_disposition_trust.py` (+ provenance tests in `test_disposition_provenance.py` or an existing suite), plus check-side tests in `test_check_disposition.py`. Minimum adversarial matrix:

1. Missing `--key-id` blocks (SP026).
2. Removed `--verify-key` is rejected by argparse (flag no longer exists).
3. Unknown signer id blocks (not in `TRUSTED_SIGNERS`).
4. Forged key committed under the production id blocks (SPKI ≠ pinned fingerprint).
5. Self-consistent forged `--keys-dir` blocks (its key's SPKI ≠ pinned).
6. `--key-id` traversal with a planted valid key blocks (`_KEY_ID_RE` + containment).
7. Key-file swap after resolution cannot affect verification (verification uses the pinned in-memory key object; `pem_sha256`/`spki_sha256` in the receipt bind the resolved bytes).
8. Foreign signature with an omitted/spoofed sidecar fingerprint blocks cryptographically (Ed25519 is the sole gate).
9. Receipt contains `signer` metadata + `snapshot_signature_sha256` + `gate_repo_sha` + `checkout_bound` + `production_eligible`, and no `verify_key` field.
10. SP028 truth table (§8) is exhaustively exercised: neither-flag-nor-opt-in blocks **SP028**; opt-in alone → authoring-only GREEN with the distinct stdout banner, the stderr warning, and `checkout_bound=false`/`production_eligible=false`; both binding flags (no opt-in) with a clean matching checkout → bound GREEN with `checkout_bound=true`/`production_eligible=true`; bound path with a dirty worktree / wrong gate SHA / undeterminable HEAD → **SP028**; exactly-one-of-the-pair, and the pair-plus-opt-in, → **SP028**. The gate runs before any input document is read.
11. **Explicit committed-census re-verification (real command):** run the actual `verify_census.py` command against the committed `evidence/census-prod-20260711T215509Z.json` (+ `.sig`, `repo_sha a67d95ee`) at SP026 HEAD and assert GREEN — proving the refactored shared anchor is behavior-preserving for the real production census. This is a deliberate invocation of the verifier, NOT reliance on the per-PR artifact gate's "no new snapshots" path.
12. Behavior-preservation: `verify_sidecar_bytes_with_key` and `verify_detached_with_key` agree for the same sidecar; the resolved `ResolvedSigner.public_key` verifies a genuine signature and no private material is present in `keys/`.

Green bar: all locked suites — schema, `test_check_disposition`, `test_collect_disposition`, `test_verify_census`, `test_disposition_trust`, `test_disposition_provenance` — plus `git diff --check` on edited files, run via `uv run --project infra/database/schema-placement --locked python tests/<suite>.py`.

## 13. Acceptance criteria

- Modules exist with the §2 dependency directions; collector never imports trust; checker never imports the collector; provenance exposes public `git_head_sha` / `git_worktree_clean`.
- `check_disposition` preapply: no `--verify-key`; `--key-id` resolves solely through `disposition_trust`; verification uses the in-hand bytes + pinned key object; receipt carries the §9 fields and no key path.
- SP028 gate behaves per the §8 table; **accidental unbound execution is impossible** (neither-flag-nor-opt-in blocks SP028); authoring-only is opt-in, visibly distinct on stdout, and records `checkout_bound=false`/`production_eligible=false`; the SP028 gate runs before any input document is read.
- `verify_census` refactor is behavior-preserving (31 cases green; CN013/CN017 unchanged).
- No active code text references `--verify-key`; historical evidence files are preserved byte-for-byte and unchanged.
- Both new modules are in the artifact tooling inventory; CI runs every new test file.
- The committed prod census explicitly re-verifies GREEN via the real `verify_census` command through the shared anchor.
- Focused cross-engine IRP (Claude grounded audit + Codex `-m gpt-5.5`, adversarial) passes; governed squash-merge after green CI, no admin bypass.
- No database access and no production write occur in this packet.

## 14. Implementation sequence

1. (done) Branch from clean `main@965c466d` in the isolated worktree `apex-schema-sp026`.
2. TDD `disposition_provenance.py` (move + publicize the two git helpers) + `disposition_trust.py` (anchor + `ResolvedSigner` + `resolve_pinned_key`) + `verify_sidecar_bytes_with_key` in `disposition_signing.py`.
3. Refactor `collect_disposition.py` and `verify_census.py` onto the shared modules (behavior-preserving); keep their suites green.
4. Harden SP026 + add the SP028 gate in `check_disposition.py` (flags, gate-before-read, authoring opt-in + distinct banner, verify flow, receipt).
5. Update receipt fields + diagnostic text + CI tooling inventory + suite loop.
6. Run the full offline suite + `git diff --check` + the explicit committed-census re-verification (real `verify_census` command).
7. Focused cross-engine review (Claude + Codex), fold findings.
8. Governed PR + squash-merge after green CI.
9. Then proceed to signed overlays bound to the base snapshot and the first 3–5-view disposition cluster.

## 15. Out of scope / guardrails

- No signed-overlay work, no cluster selection, no destructive disposition or apply in this packet.
- No DB connection, no prod mutation; A1–A3 remain HELD.
- No changes to the census evidence, the schema contract semantics, or the checker's semantic gate (SP001–SP027) beyond the SP026 text reword and the new SP028.
