The commits and files live on the host worktree, not this workstation clone — consistent with the probes running against `git archive de3fa5de` on Olares. My adjudication therefore rests on the host-executed probe + adversarial evidence, which I note transparently in the memo.

# schema-placement CORRECTION tranche (git delta 898e3871..de3fa5de): source-constant TRUSTED_SIGNERS trust anchor + key-id sanitize/containment + verify_detached_with_key (H1/H3); collector --repo-sha removal + required --expect-repo-sha always-enforced (H2/F4); F10 REPEATABLE READ; F8 schema doc; runbook D4/D5 — Grounded Audit

## Verdict

**HOLDS — APPROVE AS TOOLING-ONLY, conditional, with three tracked follow-ups.**

The correction tranche does what its headline claims and introduces **no new defect**. Across five independent probe facets and a cross-engine adversarial pass, every confirmed finding is either a **test-coverage gap** or **defense-in-depth ordering observation** — all fail-closed, none reachable as a false-GREEN through the prescribed runbook from a clean merged-main checkout with the governed key committed at its true fingerprint. Grounded confirmations at de3fa5de:

- **H1 (sole trust root):** `verify_census.TRUSTED_SIGNERS` (verify_census.py:44-46) pins `prod-disposition-ed25519-2026-07 → c75785cd…dc592ca` as the only anchor. `resolve_pinned_key` (:111-140) rejects unknown key-id → CN013, enforces `_KEY_ID_RE` bare-id + realpath/commonpath containment, loads `keys/<id>.pub.pem` as **material**, and requires its SPKI-DER sha256 == the pinned constant before returning the **key object**. `main()` (:259) passes no `trusted_signers` override; there is no CLI override. The sibling `.spki-sha256` file is inert (0 verifier reads). 26/26 `test_verify_census.py` pass, including live CN013 rejection of a forged pubkey under the real key-id (69ba… ≠ c757…) and `../evil` traversal.
- **H3 (no resolve→reopen TOCTOU):** `verify_detached_with_key` (disposition_signing.py:121-132) is purely additive, opens **only** the sidecar, and verifies against the passed-in fingerprint-checked object. `main()` loads the key exactly once and reuses that object (verify_census.py:264) — confirmed by `verify_uses_pinned_key_object_after_file_swap`. The re-open variant `verify_detached` is not reached from `main()`.
- **H2/F4 (provenance always enforced):** `--repo-sha` is removed (argparse rejects it); `--expect-repo-sha` is required; git-HEAD / clean-worktree / HEAD==expect are enforced **before** the signing key is read and before the DB opens (collect_disposition.py main, ~L646-658).
- **F10:** `conn.isolation_level = REPEATABLE_READ` is set while IDLE, and `_collect` runs the census + independent `census_count` in one commit-free transaction → single MVCC snapshot. Mechanically sound.
- **F8/F11 + D4/D5:** schema `$comment` / loop-var corrections accurate; runbook pins `--expect-query-bundle-sha256=217ff3ad…`, which the adversarial engine independently recomputed to equal `query_bundle_sha256()` at de3fa5de. No stale `--repo-sha` leaks into runbook or CLI (only evidence records + the intentional D1 rejection test).

Both suites GREEN (26/26 verify + full collector suite). Approval is **conditional** on the prod-key-material precondition (see Unverified) and carries the follow-ups below.

## Findings (severity + grounded evidence)

No confirmed correctness defect. All findings are LOW.

**F-1 — TEST-COVERAGE GAP: crypto-verify-as-sole-gate path is uncovered (H3 regression exposure). LOW.**
The real security boundary when a sidecar omits/nulls/spoofs `public_key_sha256` is the final `verify_message(message, signature, pinned_K)` (disposition_signing.py:98). That boundary was proven to hold out-of-band for all five attacker variants (fp=fp(A) → cross-check reject; fp omitted/None → crypto reject; fp spoofed to fp(K) with a foreign signature → crypto reject; genuine-K with fp omitted → accept). But the committed suite never exercises it: the only wrong-key test, `test_main_wrong_key_CN001`, routes through `build_sig_sidecar`, which **always** stamps `public_key_sha256=fp(signer)`, so it rejects at the earlier cross-check and never reaches crypto-verify-as-sole-gate. The `if fp is not None` guard (disposition_signing.py:95-97) makes the cross-check skippable by design. *Failure scenario:* a future refactor that reorders or conditions the crypto verify behind the fingerprint check would silently regress the H1/H3 guarantee with a green suite.

**F-2 — TEST-COVERAGE GAP: F10 REPEATABLE READ has no passing test behind it. LOW.**
The two added lines (`conn.read_only = True; conn.isolation_level = REPEATABLE_READ`) live in `collect_from_db`, which is GO-gated and **stubbed by a lambda in every collector test** (suite header: "The live census … is GO-gated and NOT exercised here"). 67/67 collector tests pass, but the F10 lines are on no executed path. The attribute was confirmed to resolve (`psycopg.IsolationLevel.REPEATABLE_READ == 3`, no AttributeError under psycopg 3.2.9/3.3.4), but the runtime snapshot-consistency behavior is proven only by code-read. *Failure scenario:* a prod-pinned psycopg without this API, or a pooler that rejects `BEGIN … REPEATABLE READ READ ONLY`, would surface only at the live census — never in CI.

**F-3 — TEST-INTEGRITY: traversal test (`test_main_key_id_traversal_rejected_CN013`) is weakly isolated. LOW.**
It injects `../evil` into `TRUSTED_SIGNERS` but plants **no loadable forged key** at the traversal destination (`_write_signed` writes only `keys/test-ed25519.pub.pem`). It passes today for the right reason (`_KEY_ID_RE` fires first: reason "key-id ../evil is not a bare identifier"), but if **both** the regex and the realpath/commonpath containment were deleted, the test would **still pass** via a file-not-found CN013. *Failure scenario:* a regression that removes the traversal defenses would not be caught by this test.

**F-4 — STRUCTURAL (informational): traversal guards are reachable only for an already-pinned key-id. LOW / not a defect.**
`resolve_pinned_key` checks `TRUSTED_SIGNERS` membership (:124-127, unknown → CN013) **before** `_KEY_ID_RE` (:128) and containment (:132-134). Any key-id reaching the regex/containment is already a committed bare-identifier anchor entry, so those checks never reject a reachable production input — they are belt-and-suspenders behind the source-constant anchor. Benign in production (the only pinned id matches the regex, confirmed by `test_main_forged_key_under_real_key_id` reaching the fingerprint step), and defense-in-depth still holds. Noted so the anchor is understood as the sole real gate.

## Regression risks (from the adversarial pass)

The adversarial pass confirms **no defect introduced** by the delta. The residual risks are all **pre-existing / left-open**, not tranche regressions, and all fail closed:

- **RR-1 (systemic parity gap) — `check_disposition.py:603` SP026 apply-gate still anchors on a caller-supplied path.** The apply-time decision gate that authorizes the actual destructive DDL is untouched by this tranche and still calls `ds.verify_detached(… os.path.abspath(args.verify_key))` — the exact H1-class caller-selectable-anchor pattern this tranche closed in `verify_census`. The prior review scoped H1/H3 to `verify_census` only; `check_disposition.py` is not in the changed-file list. This is a genuine parity gap on the **higher-consequence** gate, not a regression. → Follow-up packet.
- **RR-2 (code vs runbook asymmetry) — `--expect-query-bundle-sha256` remains OPTIONAL.** `check_census` computes `exp_qb = expect_query_bundle_sha256 or cds.query_bundle_sha256()`. If an operator omits the flag **and** runs the verifier from the same clean-main checkout as the census (the prescribed flow), CN006 is self-referential and passes regardless of the census SQL. Prior-review F6 was closed by runbook discipline (D4 pin), not code enforcement — asymmetric with `--expect-repo-sha`, which was made required. Defense-in-depth only (SQL text is transitively pinned by the signed `repo_sha==expect_repo_sha` at a reviewed commit; fails closed against a differing checkout). → Follow-up.
- **RR-3 (future-refactor exposure)** — the F-1 crypto-verify coverage gap is the regression vector most likely to bite silently; treat it as a guard to add, not a live defect.

## Unverified / needs source

- **Prod public-key MATERIAL is NOT committed at de3fa5de.** `keys/` is empty (git ls-tree returns nothing). `resolve_pinned_key` was proven to accept a key **iff** its SPKI-DER sha256 == the pinned `c75785cd…dc592ca`, and `test_main_forged_key_under_real_key_id` drives the real constant under a forged key and correctly rejects (c293… ≠ c757…). But the binding "`keys/prod-disposition-ed25519-2026-07.pub.pem` SPKI == c757…" is **unverifiable from committed source** — it depends on the out-of-tree governed keypair matching the constant at run time. Fails CLOSED on mismatch (CN013, no bypass), but the prod GREEN path is **unexecutable at this SHA**. Known deferral (prior-review F5).
- **F10 runtime never exercised against a database.** No live census run; `collect_from_db` is GO-gated and stubbed. Live Supabase-pooler compatibility (`BEGIN … REPEATABLE READ READ ONLY` under transaction pooling) and the prod-pinned psycopg version (lazy import) were not observed — reasoned-sound from psycopg3/PG mechanics only.
- **This workstation clone does not contain de3fa5de/898e3871** (`git cat-file`/`rev-list` miss both; no `verify_census.py` present). All grounding above is the host-executed probe + adversarial evidence (tests run via uv on Olares; adversarial run from a `git archive de3fa5de` extraction). I did **not** re-execute from this machine.
- **F8 / F11 / D4 / D5** were confirmed by the single-engine adversarial pass (schema/loop-var accurate; query-bundle sha 217ff3ad recomputed), but were **out of scope for all five multi-probe facets** — single-engine grounding, not multi-source triangulated.
- `disposition_signing.verify_sidecar`'s non-strip/lower `public_key_sha256` casing permutations were reasoned from code, not exhaustively tested against a real prod sidecar (non-exploitable: the real gate is `verify_message` against the pinned object).
- `inject.sh` value-silence is outside the delta and was not examined; the collector's child-process signing-key/DSN value-silence guarantee depends on it.

## Operator decisions to surface (with leans)

**D-1 — Merge the tranche as tooling-only?**
Lean: **YES, approve.** Tranche holds; no new defect; all residuals fail-closed and none is a false-GREEN through the prescribed runbook. Merge under the standard solo-maintainer gate (green CI + this IRP record).

**D-2 — Precondition before any PROD census run: commit the governed prod public key and prove its SPKI-sha256 == c757…dc592ca.**
Lean: **REQUIRED, gating.** The prod GREEN path is unexecutable at this SHA (keys/ empty). Commit `keys/prod-disposition-ed25519-2026-07.pub.pem` via the separate governed keypair commit and verify its fingerprint equals the pinned constant **before** the first prod run. Fails closed if skipped, but the census cannot pass until this lands.

**D-3 — Open a follow-up packet to extend the source-constant anchor to the SP026 apply-gate (RR-1).**
Lean: **YES — higher priority than it looks.** `check_disposition.py:603` authorizes the destructive DDL yet still trusts a caller-supplied `--verify-key` path — the same H1-class pattern just closed in the verifier. Parity should land before any prod apply that relies on that gate.

**D-4 — Make `--expect-query-bundle-sha256` REQUIRED in code, symmetric with `--expect-repo-sha` (RR-2).**
Lean: **YES, low-cost hardening.** Closes the self-referential CN006 path; defense-in-depth since SQL is transitively pinned by `repo_sha`. Small change; do it with D-3.

**D-5 — Add three regression guards.**
Lean: **add (a)+(b) now, (c) as a branch dry-run.** (a) crypto-verify-as-sole-gate test (omitted/null/spoofed-to-fp(K) sidecar with a foreign signature) to lock F-1; (b) strengthen the traversal test to plant a loadable forged key at the destination so it fails if the regex+containment are removed (F-3); (c) a single F10 isolation-level smoke run against a Supabase branch DB (both direct and pooled DSN forms) per "prove on a branch" (F-2). (a) and (b) are cheap and close the two silent-regression vectors; (c) converts F10 from reasoned to observed.