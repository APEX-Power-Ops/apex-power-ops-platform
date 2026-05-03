# TCC TASK-E Inverse-Equation Scoping — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-task-e-inverse-equation-scoping`
Status: **Closed PASS — 2026-04-29.** Outcome A (Expected Decision option 1): a bounded later TASK-E execution packet IS now authorizable, with included surface, excluded surface, contract anchors, and expected execution-packet shape published in `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-task-e-inverse-equation-scoping-completion-handoff.md`. No spec edit, no master-plan edit, no parity claim, no implementation; smallest-necessary authority updates only.

Original status (preserved): Ready for execution.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
Primary contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Critical evidence anchors:
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
- `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-completion-handoff.md`
- `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md` (DEC-021)
- `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-SPEC-REWRITE-AFTER-GF-INVERSE-EQUATION-BLOCKER-CLOSURE-2026-04-29.md`

---

## Objective

Define the exact bounded scope for a later TASK-E execution packet now that:

1. the GF-side inverse-equation blocker is closed by accepted pass-5 evidence,
2. the active spec is aligned to that closure,
3. the corrected §O text explicitly names a separately authored TASK-E scoping
   packet as the next downstream governance move.

This handoff authorizes only scoping. It does not authorize implementation,
tests, fixtures, validation matrices, runtime edits, or parity claims.

---

## Entry Gate

Proceed only if all of the following still hold:

1. `EASYPOWER-CALC-ENGINE-SPEC.md` contains the §J recovered-native-contract
   subsection and the §O TASK-E-scoping paragraph.
2. DEC-021 still records the §O blocker as closed.
3. No TASK-E scoping packet or TASK-E execution packet already exists on disk.
4. No contradiction has appeared between the corrected spec and the accepted
   pass-5 evidence.

If any item fails, stop and publish the contradiction instead of widening the
lane.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-completion-handoff.md`
5. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
6. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-BLOCKER-CLOSURE-2026-04-28.md`

---

## First Anchors

1. Spec §O authorization paragraph: verify that the next governed move is a
   separate TASK-E scoping packet rather than implementation.
2. Spec §G Path 2 + §J Path 2: identify the exact corrected contract surface a
   later execution packet may rely on.
3. Spec §N: identify every open question that must remain excluded from a later
   execution packet unless already covered by the corrected contract.

---

## Required Outputs

1. one scoping ruling document under `Development/Platform/TCC/`,
2. one completion handoff,
3. status / completion updates on the task packet,
4. only the smallest authority updates if the scoping result changes posture.

---

## Non-Negotiable Boundaries

1. Do not implement TASK-E.
2. Do not write tests, fixtures, or runtime code.
3. Do not claim parity.
4. Do not reopen §O blocker closure unless a file-backed contradiction is found.
5. Do not silently import unresolved §N work into the later execution scope.

---

## Expected Decision

Return one of two exact outcomes:

1. a bounded later TASK-E execution packet is now authorizable, with its exact
   included and excluded surfaces named, or
2. TASK-E execution still cannot be cleanly scoped, with the exact remaining
   reason preserved.