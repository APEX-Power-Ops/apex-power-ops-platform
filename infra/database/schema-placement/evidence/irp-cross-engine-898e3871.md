# Cross-engine review — census-hardening tranche (delta 588da50b..898e3871)

Deep, pre-merge, security-led. Two engines, independent:
- **Codex** `gpt-5.5` @ xhigh, `codex exec review --base 588da50b` in a detached worktree pinned at 898e3871. Full log: `evidence/codex-review-898e3871-full.log`.
- **Claude grounded-audit** (`irp-grounded-audit.js`, Deep, 5 self-contained probes → adversarial regression hunt → synthesis), all reading committed blobs at 898e3871. Run `wf_aad098e8-791`.

All findings below were **independently re-verified by Claude (this session) against the committed blobs at 898e3871** — not taken on either engine's word.

## Verdict (both engines agree)
**APPROVE AS TOOLING-ONLY, CONDITIONAL.** No false-GREEN is reachable through the documented runbook from a genuinely clean merged-main checkout: every new control is wired fail-closed (collector asserts clean-worktree + expect-repo-sha BEFORE the signing key is read and BEFORE the DB opens — proven by `collect_from_db` never called in the dirty/wrong-head tests; CN013 verifies the signature before the snapshot is parsed; CN004/CN009/CN014/CN015/CN016 fail-closed; value-silence clean). **Severity ceiling = Medium/Important — no Fatal, no reachable false-GREEN in the prescribed flow.** The real threat surface is **operator misuse, not external attack** (any valid signature needs the operator-held `DISPOSITION_SIGNING_KEY`). But two of the tranche's own headline claims **exceed what the code enforces**, and both are corroborated across ≥3 independent probes + the adversarial pass + Codex.

## Cross-engine convergence (the two headliners — found by BOTH engines)

### H1 — Trust anchor is caller-selectable, not repo-owned  [Codex P1 (PROVEN) · Claude F1/F3]
`verify_census.resolve_pinned_key` (verify_census.py:92–108) loads BOTH `<key-id>.pub.pem` AND `<key-id>.spki-sha256` from the **same caller-supplied `--keys-dir`**. CN013 only proves the pubkey matches its **own sibling** fingerprint file — self-referential, zero binding to any git-committed blob. `--keys-dir` is overridable (only `os.path.abspath`, no `realpath`/`commonpath`/containment). `--key-id` is unsanitized → absolute/`..` path escape (join drops the base). **A caller who controls `--keys-dir` (or writes the working-tree `keys/`) supplies a self-consistent key+fingerprint+matching private key, signs a forged census, and both CN013 and CN001 pass GREEN.** Codex *proved it* with a runnable exploit (`rc 0 / GREEN` on an ephemeral keypair in a tmp keys-dir via an absolute `--key-id`); the tranche's own `test_main_green_e2e` already demonstrates the attacker shape (tmp keys-dir, sibling fingerprint). Directly regresses the Q1 "repo-owned, not caller-selected" control the tranche claimed to add.

### H2 — Ungated `--repo-sha` is a master-bypass of the provenance gate  [Codex P1 · Claude F2]
`collect_disposition.py` main() L641–654: `if args.repo_sha: repo_sha = args.repo_sha` short-circuits the entire `else` — skipping `_git_head_sha`, `_git_worktree_clean`, **and** the `--expect-repo-sha` match. `--repo-sha $MAIN_SHA` from a **dirty/tampered** worktree still reads the signing key, connects the DB, and signs — stamping the clean merged SHA. Labeled "tests only" but **nothing enforces that at runtime** (no `--allow-unclean` gate). It also **silently no-ops `--expect-repo-sha`** (the comparison lives only in the skipped `else`). Amplification (adversarial pass connected what the probes reported separately): under this bypass a tampered collector controls BOTH `relation_count` and `catalog_relation_count` (both `QUERY_BUNDLE` results in the same process), so CN009's three-way equality is trivially satisfiable — **the independent count is a regression/bug backstop, not an adversarial control.** Regresses the Q2 provenance control.

## Engine-unique catches

### Codex-only — H3 (Medium). Fingerprint and signature verify DIFFERENT key reads (intra-verify TOCTOU)
verify_census.py:229 — `resolve_pinned_key` verifies the fingerprint on the bytes it opened, then returns the **path**; `ds.verify_detached` **re-opens** `pub_path`. If the file (or a symlink) is swapped between the two reads, the fingerprint is checked on key A while the signature is verified against key B. Fix: `resolve_pinned_key` returns the loaded public-key object/bytes; verify against that exact object. (Same read-once discipline as the checker's SP026.)

### Claude-only
- **F4 (Low).** Collector does not fail-closed on a **missing `--expect-repo-sha`** (default None; HEAD assertion guarded `if args.expect_repo_sha`). A clean checkout of an *arbitrary* commit signs successfully; merged-main binding then rests only on the downstream verifier + operator memory.
- **F6 (Low).** The runbook doesn't pass `--expect-query-bundle-sha256`, so CN006's `exp_qb` defaults to the verifier's OWN checkout bundle — always green regardless of SQL run. All three "anchors" (key via keys_dir, SQL via `cds` import, repo_sha via operator HEAD) collapse to "trust the runtime checkout." Fail-closed against a *differing* checkout, so false-assurance not exploit.
- **F7 (Low).** `resolve_pinned_key` reads `.spki-sha256` under `except OSError` only → a non-UTF-8 file raises `UnicodeDecodeError` (ValueError) → uncaught traceback instead of clean CN013. Catch `Exception`.
- **F8/F9 (Low).** `collector_version` + several `target_identity` fields (`current_user`, `server_version[_num]`, top-level `generator`) are signed but **unconsumed** by any CN check — false assurance (none scope-defining; `transaction_read_only`/`guard_passed` ARE enforced via schema `const true`).
- **F10 (Low).** No explicit isolation level between `census` and `census_count` → under READ COMMITTED a concurrent committed DDL between them trips CN009 (fail-**closed** false-reject, not slip-past). `REPEATABLE READ` would remove the window.
- **F11 (cosmetic).** `n` shadowed in `check_census` (CN009's `len(rels)` vs CN015 loop var).

### Verified-good (both engines confirm these controls hold)
Scope/consistency asserts (CN003–CN008, CN012, CN016) — no out-of-scope or internally-inconsistent census can pass; both signed copies (top-level + collection_scope) cross-checked. `_git_worktree_clean` fail-closed (untracked `??` counts dirty; any git error → dirty). Provenance ordering correct (before key read + DB open). Independent count is a genuine **honest-code** regression backstop. Value-silence: no findings.

## Documentation defects (must correct before census output is cited as governance evidence)
- **F1 prose:** "the trust anchor is repo-owned, not a caller-supplied path" (docstring + runbook) overstates the enforced property.
- **F5 prose:** CENSUS_RUNBOOK claims fingerprint `c75785cd…3dc592ca` is "verified to match the committed public key," but **no `keys/` is committed at 898e3871** — the assertion is unbacked at this SHA (key deferred to the governed keypair commit).

## Unverified / caveats
- Byte-level re-read of 898e3871 from the workstation was not possible for the workflow's final agent (dev-residency: commits live on the host clone) — but **this session re-verified every H1/H2/H3 anchor against the committed blobs via `git show 898e3871:…`**.
- Live PG16 execution of census-vs-census_count universe-identity not run (asserted from byte-identical SQL text; census_count separately re-validated returns a count on PG16.13).
- `inject.sh` value-silence is out of the tranche delta — child-only guarantee depends on it (recommend a separate confirmation).
- `disposition_signing.py` unchanged this tranche (empty diff); `public_key_fingerprint` SPKI-DER-sha256 read as fail-closed but not executed.
