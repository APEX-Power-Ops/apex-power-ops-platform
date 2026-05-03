# TCC TASK-E Inverse-Equation Path Execution — Authoring Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-task-e-inverse-equation-path-execution`
Status: **Closed PASS — 2026-04-29.** Bounded TASK-E implementation landed inside contract. STD `*ICalc` integrity check + GF dispatch metadata (Therm/Ansi family, byICalc translator, slot-to-setter binding matrix BOUND × 3, consumer-flag/InOut block-kind gating, packaged `GFInvEqRowDispatch`) + WEG OCR Type A diagnostic exclusion all wired in `tcc_v5_backend/services/calc_engine/etu_delay_routing.py`. Focused validation `pytest tests/test_etu_delay_routing.py` 43/43 PASS (19 pre-existing + 24 new); zero regressions in TASK-E surfaces. No parity claim; IEEE solver kernel math untouched. Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-completion-handoff.md`. No spec edit, no master-plan edit; smallest-necessary authority updates only.

Original status (preserved): Ready for execution.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
Scoping authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
Primary contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`

---

## Objective

Execute bounded TASK-E implementation for the inverse-equation runtime surface
now that the 2026-04-29 scoping ruling closed PASS with Outcome A.

This handoff authorizes implementation only inside the included surface already
fixed by the scoping ruling. It does not authorize validation matrices,
fixtures, parity claims, override work, or broader dispatch work.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
4. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
5. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
7. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-scoping-completion-handoff.md`

---

## Included Surface

1. STD-side InvEq path (`DS3_SEC3_I2T = 2`) per scoping ruling §3.1.
2. GF-side InvEq path (`DS1GF_SEC3_I2T = 2`) per scoping ruling §3.2.
3. Spec-policy fall-through routing for `DS3_SEC3_I2T = 3` and
   `DS1GF_SEC3_I2T = 4` only as already-governed routing, not as new InvEq
   implementations.
4. Diagnostic exclusion for WEG OCR Type A unresolved pickup
   (`DS1GF_PICKUP_CALC = 6`).

---

## Excluded Surface

The full excluded surface is the scoping ruling's §4 and remains binding here,
including:

1. validation matrices,
2. fixtures,
3. parity claims,
4. override branches,
5. §N open-question implementation,
6. non-InvEq dispatch work,
7. spec / master-plan drift unless contradiction-driven.

---

## Deliverables

1. bounded platform code changes,
2. one execution evidence document under `Development/Platform/TCC/`,
3. one completion handoff,
4. task-file status and Completion Record updates,
5. at least one focused executable validation step.

---

## First Anchors

1. Find the owning platform dispatch surface for `DS3_SEC3_I2T` /
   `DS1GF_SEC3_I2T` selection.
2. Extend that surface to wire the STD-side InvEq path inside contract.
3. Extend the nearby GF surface to match the recovered GF-side populator
   contract.
4. Add the WEG unresolved-pickup diagnostic exclusion.

---

## Non-Negotiable Boundaries

1. Do not widen beyond the included surface.
2. Do not run TASK-C or TASK-F work inside this packet.
3. Do not claim parity.
4. Do not rewrite the spec unless a direct contradiction is discovered.
5. Do not treat unresolved §N items as implicitly closed.