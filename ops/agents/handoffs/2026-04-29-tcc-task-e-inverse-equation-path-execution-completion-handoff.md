# TCC TASK-E Inverse-Equation Path Execution — Completion Handoff

**Date:** 2026-04-29
**Packet:** `2026-04-29-tcc-task-e-inverse-equation-path-execution`
**Status:** **Closed PASS — 2026-04-29.** Bounded TASK-E implementation landed inside contract; 43/43 focused tests pass; no regressions in any surface TASK-E touched; no parity claim.

**Authority:** `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
**Authoring handoff:** `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-handoff.md`
**Execution evidence:** `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
**Scoping ruling:** `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
**Active engine contract:** `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
**Pass-5 evidence:** `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
**Master plan:** `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md` DEC-021

---

## §1 — Outcome

Bounded TASK-E execution **landed inside contract**. Both inverse-equation paths defined by `EASYPOWER-CALC-ENGINE-SPEC.md` §G Path 2 (STD-side) and §J Path 2 (GF-side, including the recovered-native-contract subsection) are now wired in the platform dispatcher with the contract anchors authorized by the scoping ruling. The runtime slice is ready for a separately authorized validation/parity packet.

**No parity claim.** The IEEE inverse-time solver remains the platform's existing numerical kernel for INVEQ curves on both paths; whether its output matches the EasyPower native runtime row-for-row is a separate question deferred to a future validation packet.

---

## §2 — Required Outputs (6/6 delivered)

| # | Output | Where delivered |
|---|---|---|
| 1 | Bounded platform code changes implementing only the included surface | `services/calc_engine/etu_delay_routing.py` — module docstring extension + new constants/dataclasses/functions (STD `*ICalc` integrity, GF dispatch metadata, WEG diagnostic exclusion); `dispatch_gfd_delay` and `route_delay_curve` extended with optional `gf_pickup_calc_code` arg |
| 2 | One evidence document under `Development/Platform/TCC/` | `Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md` — 13 sections covering closure ruling, entry-gate, owning surface, implementation deltas, test additions, validation results, acceptance audit, decision boundary, stop-and-flag, hard limits, authority surfaces, evidence-pedigree asymmetry, next move |
| 3 | One completion handoff | This file |
| 4 | Status / Completion Record updates on the task file | `Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md` — status banner + Completion Record block updated below in §6 |
| 5 | At least one focused executable validation step | `pytest tests/test_etu_delay_routing.py` — **43/43 passed** (19 pre-existing + 24 new TASK-E tests); plus 9-file adjacent regression subset 112/116 (4 failures = pre-existing Supabase schema issue in `test_packet_014_browser_proof.py`); plus full `tests/` suite 304/342 (36 failures all in Supabase-REST/DB/auth/UI surfaces TASK-E never touched). See evidence §6 for full breakdown |
| 6 | One closure ruling | This file §1 + evidence §1 |

All 6/6 delivered.

---

## §3 — Decision-Boundary answers (4/4)

1. **Did bounded TASK-E implementation land for the STD-side and GF-side InvEq paths inside contract?** Yes. STD-side `*ICalc = (10, 10, 4, 4)` integrity expectation surfaced as `STD_INVEQ_ICALC_EXPECTED` constant + `std_inveq_icalc_integrity_ok()` predicate. GF-side recovered native contract surfaced as `GFInvEqFamily` enum, `gf_inveq_family()` selector, `gf_inveq_byicalc()` translator (FUN_01208640 body verbatim), `GF_INVEQ_SLOT_BINDINGS` matrix (BOUND × 3 from pass-5 evidence §12), `gf_inveq_setter_for()` lookup, `gf_inveq_block_kind()` populator gating, and `dispatch_gf_inveq_row()` + `GFInvEqRowDispatch` packaging. INVEQ curve generation continues through the existing `IEEEInverseTimeSolver` (kernel formulas governed by interpretation docs per scoping ruling §4.6).

2. **Were excluded surfaces kept out of scope?** Yes. Scoping ruling §4 enumeration: §G Path 1 / Path 3, §J Path 1 / Path 3, §K override branches, §D / §E / §F / §H / §I dispatch sections, §N items (other than the explicitly authorized N.4 WEG diagnostic), validation matrices (TASK-C), fixtures (TASK-F), workbook reconciliation (TASK-D), interpretation-doc edits (TASK-H), schema/API/UI/integration, parity claims — all untouched. Spec NOT edited; master plan NOT edited; pass-5 evidence NOT edited; scoping ruling NOT edited; interpretation docs NOT edited; `IEEEInverseTimeSolver` NOT edited.

3. **Did the implementation preserve explicit diagnostic behavior for the WEG unresolved pickup cohort?** Yes. `dispatch_gfd_delay(.., gf_pickup_calc_code=6)` returns `supported=False, solver_path=None` with `unsupported_reason` text "WEG OCR Type A pickup unresolved (DS1GF_PICKUP_CALC = 6); see EASYPOWER-CALC-ENGINE-SPEC.md §N.4. GF curve withheld until a separately authored RE pass closes the pickup formula." `route_delay_curve(.., path='gfd', gf_pickup_calc_code=6)` propagates the diagnostic as a warning with empty points and no solver call. Pinned by tests `test_dispatch_gfd_delay_weg_excludes_inveq`, `test_dispatch_gfd_delay_weg_excludes_none_too`, and `test_route_delay_curve_weg_returns_warning_no_solver_call`.

4. **Is the runtime slice now ready for a later separate validation / parity packet, without claiming parity yet?** Yes. The dispatch-layer contract anchors are in place, pinned by tests, and traceable to the scoping ruling's 11 authority anchors. A separately authorized validation packet (TASK-C-style, deferred per spec §O until TASK-G + TASK-H ship) can compare runtime output against `Stdlib.mdb` row-for-row using the dispatch metadata recorded here as trace anchors. This packet does not author or pre-authorize that validation packet.

---

## §4 — Acceptance Criteria (6/6 PASS)

| # | Criterion | Status |
|---|---|---|
| 1 | Implementation bounded to included STD-side and GF-side InvEq surfaces | PASS — every change inside `etu_delay_routing.py` + its test file; nothing else touched |
| 2 | Excluded surfaces remain untouched or only routed through existing contract-policy fall-throughs | PASS — STD `=3` (TUSTD) and GFD `=4` (TUG) preserve their pre-existing diagnostic-fall-through behavior; all other excluded surfaces untouched |
| 3 | WEG OCR Type A unresolved pickup handled by explicit diagnostic exclusion rather than fake computation | PASS — explicit `unsupported_reason` citing §N.4; solver never called for WEG sensors |
| 4 | At least one focused executable validation step is run | PASS — `pytest tests/test_etu_delay_routing.py` 43/43 passed; broader suite confirms zero regressions in TASK-E surfaces |
| 5 | Evidence and completion handoff clearly map implementation back to scoping ruling's authority anchors | PASS — evidence §11 enumerates every authority surface; module docstring cites all 11 scoping-ruling anchors |
| 6 | No parity claim is made | PASS — explicit disclaimer in §1 here, evidence §1, and module docstring; closure ruling defers parity to separately authorized validation packet |

---

## §5 — Stop-And-Flag check (5/5 negative)

| # | Trigger | Fired? |
|---|---|---|
| 1 | Owning platform dispatch surface cannot be identified without broad speculative exploration | No |
| 2 | Implementation requires behavior outside the included surface or inside the excluded surface | No |
| 3 | The only available route would force TASK-C validation or TASK-F fixtures into this packet | No |
| 4 | The runtime slice contradicts the corrected spec or the scoping ruling | No |
| 5 | A parity claim becomes necessary to describe the result | No |

---

## §6 — Authority surfaces touched

| Surface | Action |
|---|---|
| `tcc_v5_backend/services/calc_engine/etu_delay_routing.py` | **Edited** (module docstring extension + new constants/dataclasses/functions; `dispatch_gfd_delay` and `route_delay_curve` extended with optional `gf_pickup_calc_code` arg with `None` default for backward compatibility) |
| `tcc_v5_backend/tests/test_etu_delay_routing.py` | **Edited** (24 new focused tests added; 19 pre-existing tests preserved unchanged) |
| `Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md` | **Created** (execution evidence) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-completion-handoff.md` | **Created** (this file) |
| `Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md` | **Edited** (status banner + Completion Record) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-handoff.md` | **Edited** (closure status banner appended) |

No other surface touched. In particular:

- `EASYPOWER-CALC-ENGINE-SPEC.md` NOT edited (already aligned by the 2026-04-29 spec-rewrite packet).
- `architecture-tcc-master-orchestration-1.md` NOT edited (DEC-021 covers §O closure; no new DEC needed at execution-only authority since no parity claim is made).
- Pass-5 evidence document NOT edited.
- Pass-5 completion handoff NOT edited.
- Scoping ruling document NOT edited.
- No `TCC-*-ELEMENT-INTERPRETATION.md` edited (TASK-H is independent per spec §O).
- `IEEEInverseTimeSolver` (`etu_curves.py`) NOT edited (kernel formulas governed by interpretation docs).
- Database schema NOT touched.
- Migration files NOT touched.

---

## §7 — Hard Limits / Approval Boundary honored

- No widening beyond the included surface. ✓
- No TASK-C validation matrix or TASK-F fixture work in this packet. ✓
- No parity claim. ✓
- No spec rewrite (no contradiction discovered). ✓
- No treatment of unresolved §N items as implicitly closed (N.1/N.2/N.3/N.5 untouched; N.4 surfaced via diagnostic exclusion only — the pickup formula remains unknown). ✓

---

## §8 — Test counts (executed inside this packet)

```
$ pytest tests/test_etu_delay_routing.py -v
============================= 43 passed in 0.55s ==============================

$ pytest tests/test_etu_delay_routing.py tests/test_sensor_context_route.py \
        tests/test_series_b_safe_parity.py -q
52 passed, 1 warning in 5.92s

$ pytest tests/test_etu_delay_routing.py tests/test_sensor_context_route.py \
        tests/test_series_b_safe_parity.py tests/test_stpu_override_enforcement.py \
        tests/test_family_selector_parity.py tests/test_packet_014_browser_proof.py \
        tests/test_vw_etu_browse.py tests/test_vw_etu_calc_context.py \
        tests/test_neta_plot_tcc.py -q
4 failed, 112 passed, 1 warning in 73.15s
# (4 failures = test_packet_014_browser_proof.py — Supabase REST schema mismatch on
#  tcc_manufacturers.name; pre-existing infrastructure issue, unrelated to TASK-E)

$ pytest tests/ --tb=short
36 failed, 304 passed, 2 skipped, 2 warnings in 563.37s (0:09:23)
# (All 36 failures in Supabase-REST / DB / auth / UI test files. None of the
#  failing files touch services/calc_engine/etu_delay_routing.py or its
#  surfaces. Pre-existing infrastructure issues independent of this packet.)
```

The directly-relevant test surface (`test_etu_delay_routing.py`) is **43/43 PASS** with zero regressions on the 19 pre-existing tests and 24/24 PASS on the new TASK-E tests.

---

## §9 — Next operational move

The runtime slice is ready for a later separately authored validation/parity packet. Such a packet — currently deferred per spec §O until TASK-G + TASK-H ship — would:

1. Generate fixtures from `Stdlib.mdb` per TASK-F-style governance.
2. Run row-for-row comparison of platform IEEE-solver output against EasyPower's native curves at curve-point resolution for representative sensors covering the STD-side (4,524-sensor) and GF-side (1,713-sensor) InvEq cohorts plus the WEG diagnostic-exclusion cohort.
3. Surface any divergence as a parity finding without reopening §O blocker closure.

This packet does **not** author or pre-authorize that validation packet. Drafting it remains a separate governance step.

---

*End of TCC TASK-E Inverse-Equation Path Execution Completion Handoff.*
