# Cross-engine RE-REVIEW — correction tranche (delta 898e3871..de3fa5de)

Deep, pre-merge, security-led. The correction tranche is new trust-anchor code, so it faced its own
adversarial pass before becoming the anchor for prod census evidence.
- **Codex** `gpt-5.5` @ xhigh, `review --base 898e3871` in a detached worktree. Full log: `codex-rereview-de3fa5de-full.log`.
- **Claude grounded-audit** (`irp-grounded-audit.js`, Deep, 5 probes → adversarial → synthesis), reading committed blobs at de3fa5de. Run `wf_4ae3ef43-96a`. Full memo: `claude-rereview-de3fa5de-memo.md`.

## Verdict — BOTH engines: the correction tranche HOLDS, no new defect introduced
- **Codex:** *"The changes harden the census collector and verifier as intended, and the targeted offline suites pass under the locked uv environment. I did not find an introduced correctness, security, or operational issue that warrants an inline finding."* (It independently re-derived `query_bundle_sha256()` = `217ff3ad…`, matching the runbook D4 pin.)
- **Claude:** *"HOLDS — APPROVE AS TOOLING-ONLY, conditional."* No confirmed correctness defect; every finding is a test-coverage gap or defense-in-depth observation, all fail-closed, none reachable as a false-GREEN through the prescribed runbook.

**Grounded confirmations at de3fa5de:** H1 — `TRUSTED_SIGNERS` (verify_census.py:44-46) is the sole trust root; `resolve_pinned_key` rejects unknown key-id, enforces `_KEY_ID_RE`+`commonpath` containment, requires loaded-pubkey SPKI == pinned constant, returns the key OBJECT; sibling `.spki-sha256` inert (0 reads). H3 — `verify_detached_with_key` sidecar-only; key loaded once and reused. H2/F4 — `--repo-sha` removed (argparse rejects), `--expect-repo-sha` required, clean+HEAD==expect enforced before key read/DB open. F10 — `REPEATABLE_READ` set while idle; census+census_count share one MVCC snapshot. F8/F11/D4/D5 accurate.

## Cross-engine delta
Codex: clean, no inline findings. Claude (deeper structural pass): LOW test-coverage/hardening items + surfaced the **pre-existing RR-1 parity gap on the higher-consequence apply gate** that neither the prior review nor Codex flagged. This is the value of the diverse-lens second engine.

## Findings — all LOW (no correctness defect)
- **F-1 (test-coverage):** the crypto-verify-as-sole-gate boundary (sidecar omits/nulls/spoofs `public_key_sha256`) was proven to hold out-of-band but had no committed test; `test_main_wrong_key_CN001` always routes through the earlier fingerprint cross-check. **CLOSED** by new guard `test_verify_detached_with_key_crypto_is_sole_gate`.
- **F-3 (test-integrity):** the traversal test would still pass via file-not-found if the regex+containment were removed. **CLOSED** by new guard `test_key_id_traversal_rejected_even_with_planted_key` (plants a loadable key at the traversal destination; asserts rejection reason is the sanitize/containment defense).
- **F-2 (test-coverage):** F10 `REPEATABLE_READ` lines live in the GO-gated, stubbed `collect_from_db`; attribute resolves (`psycopg.IsolationLevel.REPEATABLE_READ`) but runtime behavior is code-read only. → live branch smoke deferred (D-5c).
- **F-4 (informational):** traversal guards are only reachable for an already-pinned key-id (membership precedes regex/containment) — belt-and-suspenders behind the source-constant anchor. Not a defect.

## Regression risks (pre-existing / left-open — NOT tranche regressions, all fail-closed)
- **RR-1 (follow-up packet, HIGHER-consequence):** `check_disposition.py:603` SP026 apply-gate — the gate that authorizes the destructive DDL — still calls `ds.verify_detached(… os.path.abspath(args.verify_key))`, the same H1-class caller-selectable-anchor pattern this tranche closed in `verify_census`. Out of this tranche's scope (H1/H3 were scoped to verify_census). Parity should land before any prod apply relying on that gate.
- **RR-2 (follow-up):** `--expect-query-bundle-sha256` remains OPTIONAL in code (`exp_qb = expect_query_bundle_sha256 or cds.query_bundle_sha256()`); self-referential CN006 if omitted. Closed by runbook D4 discipline, not code — asymmetric with the now-required `--expect-repo-sha`. Defense-in-depth (SQL transitively pinned by signed repo_sha).

## Unverified / caveats
- Prod public-key MATERIAL is NOT committed at de3fa5de (`keys/` empty). resolve accepts iff loaded SPKI == `c757…`; the binding "committed prod pubkey SPKI == c757…" is unverifiable from source — fails CLOSED on mismatch, but the prod GREEN path is unexecutable until the governed keypair commit lands (prior F5 deferral).
- F10 runtime never exercised against a DB (GO-gated); live Supabase-pooler `BEGIN … REPEATABLE READ READ ONLY` compat reasoned-only.
- Codex's proven 898e3871 exploit was reproduced CLOSED against de3fa5de this session (rc 0 → rc 1 / CN013).

## Operator decisions to surface (with leans)
- **D-1 — merge tranche as tooling-only?** Lean YES (holds; residuals fail-closed).
- **D-2 — commit governed prod pubkey + prove SPKI == c757… before any prod census (= Q7 keys commit).** Lean REQUIRED/gating.
- **D-3 — follow-up packet: extend source-constant anchor to the SP026 apply-gate (RR-1).** Lean YES, higher priority than it looks.
- **D-4 — make `--expect-query-bundle-sha256` REQUIRED in code (RR-2).** Lean YES, low-cost; do it with D-3.
- **D-5 — regression guards.** (a) crypto-sole-gate + (b) traversal-with-planted-key: **DONE this session** (2 guards added; verify suite 26→28). (c) F10 isolation smoke on a Supabase branch: deferred to a live dry-run.
