# IRP Review Record — Ops Recognition Bridge Slice-1 Spec

**Artifact:** `docs/superpowers/specs/2026-06-23-ops-recognition-bridge-design.md` @ `512b25bb` (lane `ops/recognition-bridge`, off main `1c07d7ca`).
**Mode/Depth:** Audit / Deep. **Engines:** Claude grounded-audit (7 agents, 5 probes + adversarial + lead) · Codex `codex exec` (gpt-5.5) · **live `ops_dev` grounding** (the third engine — closed the others' "could not query live DB" caveat).
**Date:** 2026-06-23.

## Verdict
**NOT-READY for `writing-plans` as written — fixable with spec edits, no re-architecture.** Both engines agree the core architecture is sound (attestation as the sole sanctioned writer of `status='Complete'`; append-only ledger carrying a `completion_attestation_id` trace; function-only mutation) and that R1/R2 genuinely closed their tier. But there is **1 CRITICAL** (live-data, neither engine could see it), **5 blocking High**, and a **should-fix Medium** tier to correct first.

## Cross-engine + live-grounding delta (the value of three lenses)
- **Live-grounding ALONE caught the CRITICAL:** the `source='ops-intake'` predicate matches **0** live Miner rows. Both engines explicitly flagged they could not query `ops_dev`; the slice's whole value prop is "demonstrate on Miner."
- **Codex ALONE caught:** attestation-row **mutability** (the ledger is append-only but the new FK points to a mutable audit row with no immutability guard).
- **Claude ALONE caught:** §5.11 `search_path` **privilege-escalation** (`public` in a SECURITY DEFINER path) and the **post-reversal lineage** state (reverse→revoke leaves `recognized_event_id`→NULL + revoked attestation + NULL-attestation reversal row).
- **Convergent (both):** INSERT-bypass of the BEFORE-UPDATE-only guard; security boundary insufficient for a revenue path; revoke lock-order; firewall regression tests; `/rollup` view undefined; `obligation_clearance` unpinned; down-migration trace loss.

## Findings (consolidated, by severity)

### CRITICAL-1 — source-predicate matches zero live rows (live-grounding)
All 5,344 Miner apparatus are `source='miner_rev10.xlsm'`, `provenance_status='approved'`, `legacy_source_id` set. The current `ops-intake` *code* stamps `source='ops-intake'`, but Miner predates that and is **intentionally** filename-sourced so the intake engine treats it as **foreign / no-backfill** (operator ruling). So §5.3 attest gate, §5.7 guard, and §5.8 worklist eligibility (all keyed on `source='ops-intake'`) match **0** Miner rows → the slice is inert on its demonstration dataset. **Fix (decision D1):** replace the `source='ops-intake'` literal with `provenance_status='approved'` (matches all 5,344 Miner + all future intake; semantically "a finalized apparatus eligible for completion-recognition," decoupled from the intake-ownership marker the operator deliberately varied). Verified: dropping the literal → 5,344 eligible.

### BLOCKING (High)
- **B1 INSERT-bypass (both).** §5.7 guard is `BEFORE UPDATE` only; `status`/`source` are insertable, so a direct `INSERT … status='Complete'` lands a Complete row with no attestation. **Fix:** make the guard `BEFORE INSERT OR UPDATE` with **TG_OP-aware** logic — on INSERT fire iff `new.status='Complete'` (do NOT use the `IS DISTINCT FROM` transition test on INSERT, or it fires on every normal `Not Started` intake insert and breaks intake); on UPDATE keep the transition test. Plus the role boundary must `REVOKE INSERT`, not only `UPDATE`.
- **B2 attestation-row mutability (Codex).** `ops.completion_attestation` has no immutability guard, yet a recognized $ now depends on it. Direct DML can rewrite `apparatus_id/attested_by/prior_status/provenance/reason` after the fact. **Fix:** add a `revrec_immutable`-style trigger — append-only except the single sanctioned `revoked_at/by/reason` transition (and only `NULL→value`, once).
- **B3 §5.11 search_path escalation (Claude).** `set search_path = ops, public, pg_temp` in a SECURITY DEFINER function is the textbook escalation hole (anyone who can `CREATE` in `public` shadows an unqualified call as the owner). **Fix:** `ops, pg_temp` only + `REVOKE CREATE ON SCHEMA public FROM PUBLIC`.
- **B4 §5.9 down cannot "restore" (Claude).** `005_…_down.sql` **DROPs** `approve_and_recognize` + `trg_revrec_insert_integrity`; there is no "005 body" to restore. The 009 down must `create or replace` both back to their **verbatim 005 UP bodies** (preserving the review-fixed `is distinct from` null-safety + `for update of a2` serialization). **Fix:** transcribe verbatim + a down test that **source-diffs** the restored bodies against `005`, not a happy-path recognize.
- **B5 post-reversal lineage (Claude).** The sanctioned attest→recognize→reverse→revoke cycle leaves `recognized_event_id`→NULL (view drops reversed events), a revoked attestation, and a NULL-`completion_attestation_id` reversal row. §5.2's "every recognized $ → its attestation" is **active-at-write**, not still-active; §5.8 flags + §5.10 tests never model the post-reversal state. **Fix:** state the invariant precisely, model post-reversal flags in §5.8, test the full cycle in §5.10.
- **B6 security boundary = hard PROD gate (both).** The ctx-guard is forgeable by any `postgres`-connected session; for a "sole sanctioned writer" revenue path, host-gating is the *dev* posture only. **Fix (decision D2):** 009 may merge + apply to `ops_dev` on the interim ctx-guard posture, but **MUST NOT reach prod until** the `ops_app` REVOKE boundary (REVOKE UPDATE+INSERT on `ops.apparatus`; no direct DML on `completion_attestation` or the ledger; mutation fns SECURITY DEFINER, `search_path=ops,pg_temp`) is applied. Make it an explicit release-gate in the spec, not a "lane-wide nicety."

### SHOULD-FIX (Medium)
- **M1 revoke lock-order (both, cites D-OPS-12).** §5.4 reads `sum(recognized_amount)` without locking the apparatus → benign revoke can non-deterministically abort + a TOCTOU. **Fix:** `perform 1 from ops.apparatus where id=<attestation.apparatus_id> for update` before the net-gate; pins the lane "apparatus before ledger rows" order; revoke must NOT row-lock ledger events.
- **M2 `/rollup` undefined (both).** §7/§8 expose `/rollup` + a panel but §5 defines no rollup view; existing `v_scope_recognition`/`v_project_recognition` carry `scope_id/project_id`, not `project_number` → needs an `ops.projects` join. **Fix:** define the rollup view in §5 + a test.
- **M3 clearance-enum validation (both).** `obligation_clearance` values are `('provided','not_applicable')` (005:8); the recognize route takes them free-form → an out-of-enum value yields a raw PG cast error, breaking the value-free 400 contract. **Fix:** pin + request-side-validate + test invalid.
- **M4 firewall regression tests (both).** §5.6 rewrites the integrity trigger; §5.10 tests only the new attestation cases, not that all original 005 checks (lineage/active/Complete/frozen/amount/snapshot/idempotency) survive. **Fix:** add regression coverage.
- **M5 missing tests (Claude).** Cross-apparatus mismatch for §5.6's `apparatus_id=new.apparatus_id`; recognize-with-no-active-attestation for §5.5's new branch; a genuine partial-unique **race** (not the sequential status-gate the current "second active" test exercises).

### MINOR (document / pin)
- §5.6 reversal arm relies on an **undocumented column-default-NULL coupling** (`reverse_recognition` omits the column; a future non-null default breaks it). Document.
- §5.5 `approve_and_recognize` as written ships **INVOKER** (no SECURITY/search_path clause) → the GUC guard runs in the caller's context; decide DEFINER vs INVOKER under the role boundary.
- Document the `apparatus_freeze_guard`+`is_frozen` composition that makes the live `quoted_revenue` read in `can_recognize`/`can_attest` safe, and the `apparatus_protect_recognition` backstop on the revoke restore.

## Now-verified (live grounding closed these "unverified" flags)
- Worklist coverage: all 5,344 Miner apparatus are active + frozen-basis + `quoted_revenue`>0 → **0 silently dropped** once D1 fixes the predicate.
- Distinct sources for Miner = 1 (`miner_rev10.xlsm`); 0 already-Complete (clean slate).
- **Still unverified (carry to build):** the deployed `ops_dev` `approve_and_recognize`/integrity-trigger bodies were assumed == the `005` file (lane dev-only/unmerged); diff deployed-vs-file at build time (matters for B4).

## Operator decisions (with leans)
- **D1 (CRITICAL predicate):** replace `source='ops-intake'` → `provenance_status='approved'` across §5.3/§5.7/§5.8. **Lean: yes** (matches all live Miner + future intake; correct semantics; preserves Miner's foreign/no-backfill status).
- **D2 (security):** role boundary deferred out of the dev slice but a **hard prod-apply gate** (REVOKE UPDATE+INSERT + SECURITY DEFINER + `search_path=ops,pg_temp`). **Lean: yes.**
- **D3 (supersession):** keep the partial-unique index; have §10 spell out the `production_tracking` supersession sequence (reverse→revoke-PM→attest→re-recognize) instead of glossing "supersedes by policy." **Lean: yes.**
- **D4 (disposition):** I fold CRITICAL + all blocking + should-fix into a **round-3 spec revision**, you take a final glance, then `writing-plans`. **Lean: yes.**
