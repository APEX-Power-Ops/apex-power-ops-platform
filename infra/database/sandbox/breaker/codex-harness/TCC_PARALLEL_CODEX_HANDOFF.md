# TCC Parallel Codex — Handoff & Mandate (#79 follow-on)

You are a SEPARATE, PARALLEL Codex working the TCC (lvbreakertcc) lane ONLY, in the
background. The estimator / takeoff / ops work is on a different thread — stay out of it.

## Hard fences (NEVER cross)
- Work ONLY in TCC lanes/worktrees. Do NOT touch estimator, takeoff, ops, records, learning, or any other lane.
- Use ONLY the breaker SANDBOX clone in `$BREAKER_SANDBOX_DSN`. NEVER connect to prod, Supabase, or any other DB. No outbound DB calls.
- NO prod writes, NO merges, NO promotion. Produce findings, candidate SQL, dry-run evidence, and recommendations ONLY. Every prod-bound action waits for the operator's explicit gate (delivered via the main thread).
- Behavioral calc-engine rulings are Access (`TCC_NEW.accdb`) authority and are NOT available here. Where a finding needs behavioral fixtures, FLAG and defer — do not guess.

## Already done on the main thread (do not redo)
- #79 audit complete. **F-79-01 is CLOSED**: migration `027_sst_mismatch_classkey_fix.sql` (SST mismatch view re-keyed to `(breaker_class, breaker_style_id)`) was APPLIED to prod 2026-06-26 (before 8 -> after 53, +45). Do NOT re-touch F-79-01.
- Audit artifacts: `findings-79.md` + `candidate-patches/` (on branch `codex/breaker-79audit`); migrations `027`/`028` (+downs) on this branch `lvbreaker/tcc-79-contract-fixes`.

## Your mandate (bounded TCC-only tasks)

### Task A — review 028 / F-79-02 (additive TMT serving-contract views)
Independently review `infra/database/migrations/tcc/028_lvbreakertcc_tmt_serving_contract_views.sql` (+ `_down`).
- Verify the three views are correct, additive, fail-closed, and reversible against the sandbox clone.
- Confirm the count-free partition invariant (serving + hazards = total) and that nothing reads the views yet (creating them changes no serving behavior).
- Stress the per-class joins (MCCB / ICCB / PCB) and the orphan branch; flag any frame mis-classification or double-count.
- Dry-run down->up on the sandbox and record evidence. Recommend GO / NO-GO for a future operator-gated prod apply. Do NOT apply to prod.

### Task B — F-79-03 triangulation (prod data ALREADY gathered; document + recommend)
The main thread already ran the read-only prod counts. This table is AUTHORITATIVE — do NOT try to re-fetch prod (you cannot reach it):

| table | Master Reference | PROD (live read-only) | SANDBOX |
|---|---|---|---|
| brk_iccb / brk_iccb_styles | 29 / 608 | 29 / 608 | 29 / 608 |
| brk_mccb / brk_mccb_styles | 640 / 10335 | 640 / 10335 | 640 / 10335 |
| brk_pcb / brk_pcb_styles | 157 / 3279 | 157 / 3279 | 157 / 3279 |
| tmt_frames | 42238 | 42069 | 42069 |
| tmt_amps | 67206 | 66960 | 66960 |
| tmt_settings | 58041 | 57983 | 57983 |
| tmt_curves | 1143458 | 1139025 | 1139025 |
| tmt_thermal_adj | 21790 | 14620 | 14620 |

Conclusion the main thread already drew: **PROD == SANDBOX for every table** -> the T7 restore is faithful and the deltas are NOT a restore artifact. The gap is **prod-vs-Master-Reference** (biggest: `tmt_thermal_adj` -7170, ~33% short; `tmt_curves` -4433).
YOUR JOB: characterize the gap. Find WHERE the Master Reference numbers originate in `reference/tcc/` and judge whether the MR is the stale party or prod is genuinely short (an Access->Supabase load gap). If deciding needs the Access source, FLAG it as an Access-authority follow-up. Produce a triangulation note + recommendation. There is NO migration here (F-79-03 is data-fidelity, not a contract fix).

### Task C — F-010 / F-011 label authority
The main thread found NO checked-in F-010/F-011 definition in `reference/`, `docs/`, or platform STATE; the audit's hazard->label mapping is INFERENCE (already annotated provisional in `findings-79.md`). Search the TCC material once more for the real authority. If found, confirm or correct the mapping. If not found, recommend the labels stay provisional and are NOT used in any prod migration name/comment.

### Task D — F-79-04 (D4/D5 helper/override columns)
Stays PARKED behind Access authority. No action beyond confirming it remains correctly deferred.

## Deliverables (in your worktree, on your branch)
- `tcc-parallel-findings.md` — Task A verdict, Task B triangulation note, Task C authority result, Task D confirmation.
- `candidate-patches/` — any NEW candidate SQL (sandbox-applied only), each self-verifying + reversible, with NO hardcoded sandbox counts in any prod-bound body (use live `RAISE NOTICE` + count-free invariants, as 027/028 do).
- Dry-run evidence for anything proposed.

Stop at recommendations. The operator gates every prod action through the main thread.
