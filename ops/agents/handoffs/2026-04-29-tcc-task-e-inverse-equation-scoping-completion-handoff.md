# TCC TASK-E Inverse-Equation Scoping — Completion Handoff

**Date:** 2026-04-29
**Packet:** `2026-04-29-tcc-task-e-inverse-equation-scoping`
**Status:** **Closed PASS — 2026-04-29.** Bounded TASK-E scoping returned: a separately authored TASK-E execution packet MAY now be drafted against `EASYPOWER-CALC-ENGINE-SPEC.md` §G Path 2 (STD-side InvEq) + §J Path 2 (GF-side InvEq) with the exact included / excluded surfaces published in the scoping ruling document.

**Authority:** `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
**Authoring handoff:** `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-scoping-handoff.md`
**Scoping ruling document:** `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
**Active engine contract:** `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` (post-rewrite, 2026-04-29)
**Pass-5 evidence:** `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
**Pass-5 completion handoff:** `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-completion-handoff.md`
**Master plan:** `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md` DEC-021

---

## §1 — Outcome

**Outcome A (per the authoring handoff "Expected Decision" block):** A bounded later TASK-E execution packet IS now authorizable, with its exact included and excluded surfaces named.

The full scoping ruling — included surface, excluded surface, contract anchors, expected execution-packet shape, and STD/GF evidence-pedigree-asymmetry transparency note — is published in the scoping ruling document linked above. This handoff intentionally summarizes rather than duplicating that content.

---

## §2 — Required Outputs (from authoring handoff §"Required Outputs")

| # | Output | Where delivered |
|---|---|---|
| 1 | One scoping ruling document under `Development/Platform/TCC/` | `Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md` |
| 2 | One completion handoff | This file |
| 3 | Status / completion updates on the task packet | `Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md` (status banner + Completion Record) |
| 4 | Only the smallest authority updates if the scoping result changes posture | None required — see §6 |

All 4/4 delivered.

---

## §3 — Decision-Boundary answers (4/4)

1. **What exact inverse-equation behavior may a later TASK-E execution packet implement directly against the corrected spec?**
   STD-side InvEq dispatch (§G Path 2) for the 4,524 sensors with `DS3_SEC3_I2T = 2`, including the `DatSection3InvEq` row read via `dvlSSTGetInvEqDelays(nSection = 3)`, the `InOut ∈ {0, 2}` switch, the `*ICalc = (10, 10, 4, 4)` integrity check, and the 6-coefficient quadrant binding to `SetSTDB_*` / `CalcThermEq3`. PLUS GF-side InvEq dispatch (§J Path 2) for the 1,713 sensors with `DS1GF_SEC3_I2T = 2`, including the `DatSection1GfInvEq` row read via `dvlSSTGetInvEqDelays(nSection = 5)`, the `dvlDatInveqDelay` 216 B / 4-sub-block layout, the IdOp-`*Eq`-byte row-level Therm/Ansi selector, the slot-to-setter binding matrix (8 setters), the `byICalc = (in == 0) ? 2 : (in == 1) ? 1 : 0` translator, and the consumer-flag/InOut gating for flat-vs-inverse block selection. Full detail in scoping ruling §3.

2. **What exact surfaces remain excluded because they depend on still-open questions or ungated work?**
   §G Path 1, §G Path 3, §J Path 1, §J Path 3 (other paths within the same sections); §K override branches; §D LTPU, §E LTD, §F STPU, §H INST, §I GFPU pickup (other dispatch sections); all five §N open questions (N.1 through N.5); spec-policy deferred low-priority enums (`DS3_SEC3_I2T = 3`, `DS1GF_SEC3_I2T = 4`, `DatSection3STOvr` outlier, `DS4_OVR_CALC = 9`); kernel formula contents (governed by `TCC-*-ELEMENT-INTERPRETATION.md`, NOT redefined); validation matrix (TASK-C); fixtures (TASK-F); workbook reconciliation (TASK-D); interpretation-doc reconciliation (TASK-H); master-plan structural changes; spec edits; schema/API/UI/integration; parity claims of any kind. Special-case: WEG OCR Type A 7-sensor cohort (N.4) must be excluded by diagnostic surfacing even on InvEq path. Full detail in scoping ruling §4.

3. **What exact authority anchors must a later TASK-E execution packet cite?**
   Eleven anchors enumerated in scoping ruling §5: spec §G Path 2, spec §J Path 2 + recovered-native-contract subsection, spec §C InvEq row schemas, spec §O, spec §N, pass-5 evidence §12 + §8, pass-5 completion handoff, master plan DEC-021, `TCC-STD-ELEMENT-INTERPRETATION.md`, `TCC-GF-ELEMENT-INTERPRETATION.md`, and the scoping ruling document itself. The 2026-04-28 TASK-E blocker-closure packet must NOT be cited as runtime authority (preserved as historical posture only).

4. **Does the scoping result authorize a later execution packet now, or does it still preserve deferral?**
   It authorizes a later TASK-E execution packet now, with the exact included / excluded surfaces and authority anchors fixed by the scoping ruling document. Drafting that execution packet remains a separate governance step; this scoping packet does not pre-author it. Full expected execution-packet shape in scoping ruling §7.

---

## §4 — Acceptance Criteria (6/6 PASS)

| # | Criterion | Status |
|---|---|---|
| 1 | STD-side and GF-side scope assessed together against corrected spec | PASS — scoping ruling §3 covers both with shared row-reader / row-shape rationale |
| 2 | Later TASK-E execution scope named exactly enough that another agent could implement | PASS — scoping ruling §3 names selectors, row sources, switches, layouts, binding matrix, translator, kernel-binding pointers |
| 3 | Excluded surfaces named explicitly rather than implied | PASS — scoping ruling §4.1–§4.7 enumerate every adjacent category |
| 4 | No implementation, fixture, validation, or parity work authorized by accident | PASS — scoping ruling §4.6–§4.7 + §7 + §8 |
| 5 | Still-open §N questions remain out of scope unless corrected spec covers them | PASS — scoping ruling §4.4 explicit on all 5 |
| 6 | Next downstream governance move stated without ambiguity | PASS — scoping ruling §7 names a separately authored TASK-E execution packet |

---

## §5 — Stop-And-Flag check (5/5 negative)

| # | Trigger | Fired? |
|---|---|---|
| 1 | Corrected spec / pass-5 / DEC-021 disagree on TASK-E reliance | No |
| 2 | Only way to define scope is to assume closure of unrelated §N question | No |
| 3 | Scoping implicitly authorizes implementation / fixtures / validation / parity | No |
| 4 | Prior TASK-E scoping or execution packet discovered mid-run | No (only the 2026-04-28 blocker-closure pair exists; that is a different posture) |
| 5 | Clean downstream execution shape cannot be stated without reopening contract | No |

---

## §6 — Authority surfaces touched

| Surface | Action |
|---|---|
| `Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md` | **Created** (scoping ruling) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-scoping-completion-handoff.md` | **Created** (this file) |
| `Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md` | **Edited** (status banner + Completion Record) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-scoping-handoff.md` | **Edited** (closure status banner) |

No other surface touched. In particular:

- `EASYPOWER-CALC-ENGINE-SPEC.md` NOT edited — already aligned by the 2026-04-29 spec-rewrite packet; no contradiction discovered.
- `architecture-tcc-master-orchestration-1.md` NOT edited — DEC-021 already covers §O closure; DEC-005 already covers TASK-E general gating; scoping-only authority does not warrant a new DEC.
- Pass-5 evidence document NOT edited.
- Pass-5 completion handoff NOT edited.
- No `TCC-*-ELEMENT-INTERPRETATION.md` edited.
- Project memory updated with the scoping ruling closure (auto-memory `project_tcc_gf_loader_recovery_pass2.md` extension).

---

## §7 — Next operational move

A separately authored TASK-E execution packet may now be drafted. Expected shape per scoping ruling §7. This packet does not author it; drafting is a separate governance step.

If the user authors a TASK-E execution packet, the scoping ruling document plus its 11 authority anchors are sufficient to drive bounded implementation against §G Path 2 + §J Path 2 without reopening §O blocker closure.

If the user instead defers TASK-E execution further (for example, to allow TASK-G + TASK-H to ship first so that TASK-C and TASK-F unfreeze and a complete TASK-E + validation pipeline can be drafted at once), this scoping ruling stands as durable authority for whenever execution is later opened. Re-running the scoping packet would not be needed unless the corrected spec, pass-5 evidence, or DEC-021 changes.

---

*End of TCC TASK-E Inverse-Equation Scoping Completion Handoff.*
