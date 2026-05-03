# TCC TASK-C Inverse-Equation Validation / Parity — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-task-c-inverse-equation-validation-parity`
Status: **Closed PASS — 2026-04-29.** Bounded representative inverse-equation validation surface lands inside contract; the post-TASK-E dispatcher exercises correctly on real `Stdlib.mdb` rows for STD-side `(10,10,4,4)` integrity, GF-side Therm + Ansi family/block/byICalc/setter dispatch, and WEG OCR Type A diagnostic exclusion (all 7 SensorIDs). Focused validation 18/18 PASS; combined adjacent regression 61/61 PASS; zero regressions. No divergence detected; no full-surface parity claimed. Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-C-INVERSE-EQUATION-VALIDATION-PARITY-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-c-inverse-equation-validation-parity-completion-handoff.md`.

Original status (preserved): Ready for execution.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-C-INVERSE-EQUATION-VALIDATION-PARITY-2026-04-29.md`
Primary contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
TASK-E execution evidence:
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
- `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-completion-handoff.md`

---

## Objective

Execute the next bounded calc-engine validation lane after TASK-E.

This handoff authorizes only representative inverse-equation validation for the
post-TASK-E dispatcher surface, plus the smallest fixture capture needed to run
that validation reproducibly in repo-owned tests. It does not authorize new
runtime implementation, spec edits, or broad parity claims.

---

## Confirmed Entry Gate

This packet is authorized because:

1. TASK-G already published the active engine contract,
2. TASK-H is already recorded as done in the Series B findings trail,
3. the earlier safe direct-band TASK-C surface is already closed PASS,
4. TASK-E inverse-equation implementation is already closed PASS,
5. the TASK-E completion handoff explicitly names this later separate
   validation / parity packet as the next operational move.

If any one of those statements fails when execution begins, stop and return a
blocker report instead of writing tests or fixtures from stale inputs.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-C-INVERSE-EQUATION-VALIDATION-PARITY-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-PATH-EXECUTION-2026-04-29.md`
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-path-execution-completion-handoff.md`
6. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
7. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
8. `source-domains/tcc_v5_backend/services/calc_engine/etu_delay_routing.py`
9. the nearest existing pytest seam under `source-domains/tcc_v5_backend/tests/`

---

## Included Surface

1. Representative STD-side inverse-equation validation.
2. Representative GF-side inverse-equation validation.
3. WEG OCR Type A diagnostic-exclusion validation.
4. The smallest repo-owned fixture capture needed to make that validation
   reproducible.
5. Evidence capture describing whether the representative cohort passes or
   exposes bounded divergence.

---

## Excluded Surface

1. New runtime implementation.
2. Safe direct-band TASK-C surfaces already closed on 2026-04-27.
3. Broad TASK-F infrastructure.
4. TMT or EMT work.
5. Non-InvEq dispatch validation.
6. Spec, interpretation-doc, or master-plan edits.
7. Full-surface parity claims.

---

## First Anchors

1. The post-TASK-E dispatcher seam in `etu_delay_routing.py`.
2. The existing focused tests in `tests/test_etu_delay_routing.py`.
3. The TASK-E evidence sections that enumerate the routed STD and GF surfaces.
4. The smallest representative row set in `Stdlib.mdb` needed to cover the
   distinct STD and GF inverse-equation families already on disk.
5. The WEG exclusion tests that should remain diagnostic-only.

---

## Non-Negotiable Boundaries

1. Do not widen from representative validation into fresh implementation.
2. Do not claim full-surface parity.
3. Do not reopen the already-closed safe direct-band TASK-C surface.
4. Do not widen fixture capture beyond the minimal representative InvEq cohort.
5. Do not resolve still-open §N questions by test inference.

---

## Expected Deliverables Back To Copilot

1. Exact files changed.
2. Exact fixtures added or updated.
3. Exact tests added or updated for STD-side, GF-side, and WEG exclusion.
4. Exact validation command run and result.
5. One explicit downstream statement saying whether the representative
   inverse-equation validation surface passed, failed, or exposed bounded
   divergence, and what remains deferred.