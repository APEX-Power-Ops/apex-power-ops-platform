# TCC GF-Side Inverse-Equation Dispatch-Profile Reverse-Engineering Handoff

Date: 2026-04-28
Packet: `2026-04-28-tcc-gf-side-inverse-equation-dispatch-re`
Status: **Executed / closed**
Completion handoff: `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-dispatch-re-completion-handoff.md`
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Objective

This handoff delegates the next honest calc-engine TCC lane after TASK-019A
preserved the TASK-E block.

Claude Code should execute only this bounded reverse-engineering lane:

1. re-state the exact GF-side inverse-equation blocker preserved by TASK-019A,
2. reverse-engineer the GF-side `DatSection1GfInvEq` dispatch profiles strongly
   enough to test profile-to-`CTccLVBreakerCurveGF`-setter bindings,
3. resolve the per-value semantic of `*ICalc ∈ {1, 4, 8, 10}` if that can be
   done honestly,
4. publish one exact blocker-status ruling: CLOSED, PARTIALLY CLOSED, or NOT
   CLOSED,
5. authorize only a later separate TASK-E scoping packet if blocker closure is
   actually earned.

This handoff does **not** authorize TASK-E implementation, GF-side parity
claims, fixture generation, Tier B reopening, or Phase 6 structural work.

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already
recorded on disk:

1. Spec §O still records the GF-side inverse-equation dispatch blocker in
   front of TASK-E.
2. TASK-019A closed PASS on 2026-04-28 with blocker result **NOT CLOSED**.
3. TASK-E remains BLOCKED; no execution, scoping, or splitting packet is
   authorized from TASK-019A.
4. The master plan now records this separately authored RE packet as the next
   honest calc-engine move.
5. No accepted reverse-engineering evidence already exists on disk that fully
   closes the blocker.
6. No separate TASK-E execution or scoping packet exists on disk.

If any one of those statements fails when execution begins, stop and return a
contradiction report instead of performing new reverse-engineering work.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
2. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-BLOCKER-CLOSURE-2026-04-28.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-B-DVL-DISPATCH-ENUMERATION-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
6. `source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`
7. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`

## First Anchors

Start from the known blocker and known structural profiles, not from a broad
re-discovery pass across the entire calc engine.

### Blocker anchors

1. spec §J Path 2,
2. spec §O,
3. TASK-B §3.9,
4. TASK-019A evidence §§6 to 8.

Local hypothesis for the first slice:

- the only honest next move is the RE lane that tries to close the named
  blocker itself; no scope split or documentation-only interpretation can do
  that truthfully.

Cheapest falsifying check:

- verify whether accepted evidence already on disk fully closes the blocker. If
  yes, stop and report that this packet is unnecessary.

### RE anchors

1. GF-side `DatSection1GfInvEq` profile table,
2. `CTccLVBreakerCurveGF` runtime surface,
3. existing findings in `DLL_SEMANTIC_FINDINGS.md`.

Local hypothesis for the RE slice:

- a bounded RE pass can either close or materially narrow the blocker without
  widening into TASK-E implementation.

Cheapest falsifying check:

- if no binary-backed or file-backed evidence moves the blocker dimensions
  forward, preserve NOT CLOSED and return the exact unresolved gap.

## Execution Order

### 1. Reconfirm the blocker boundary

Required outcomes:

1. TASK-019A still governs the current block.
2. No TASK-E scope or execution packet has opened.
3. This packet remains a bounded RE lane only.

### 2. Restate accepted structural knowledge

Required outcomes:

1. All GF-side `DatSection1GfInvEq` profiles from TASK-B §3.9 are restated
   exactly.
2. The accepted unknowns from TASK-019A are restated exactly.
3. The RE target is explicit before any new evidence is interpreted.

### 3. Perform bounded reverse engineering

Required outcomes:

1. Attempt profile-to-setter binding for every known GF-side profile.
2. Attempt per-value semantic resolution for `*ICalc ∈ {1, 4, 8, 10}`.
3. Preserve unknowns explicitly where evidence does not close them.

Execution rules:

1. Prefer binary-backed evidence, accepted decompilation evidence, and stable
   on-disk findings over speculation.
2. Do not translate naming similarity into semantic certainty.
3. Keep implementation design out of scope.

### 4. Publish the blocker ruling

Required outcomes:

1. One exact blocker-status ruling is published.
2. One exact downstream ruling is published.
3. The remaining gap is preserved exactly if blocker closure is incomplete.

Execution rules:

1. Do not authorize TASK-E implementation from this packet.
2. At most, authorize a later separate TASK-E scoping packet.
3. Prefer preserving the block over inventing closure.

## Hard Limits

1. No TASK-E implementation in this packet.
2. No GF-side parity claim unless the blocker is fully closed.
3. No fixture generation, test generation, or runtime code changes.
4. No Tier B reopening or Phase 6 widening.
5. No invented semantics for unresolved `*ICalc`, `*Eq`, or `InOut` behavior.

## Execution Result

Execution closed PASS with the blocker materially narrowed but still preserved.

1. The GF-side inverse-equation dispatch blocker named in
   `EASYPOWER-CALC-ENGINE-SPEC.md` §O is **NOT CLOSED**.
2. The kernel side is now reverse-engineered from `TccBase.dll`: per-slot
   kernel discriminator is bound to `{0=Therm, 1=Ansi, 2=FDly}`, per-kernel
   `byICalc` is bound to `{0→ref[16], 1→ref[13], 2→ref[12], else→no curve}`,
   and the four slot-byte pairs `(272/273, 376/377, 480/481, 584/585)` inside
   normal-mode `GFInverseEqDelay` at offset `264` are bound to the four setter
   families.
3. Profile-by-profile binding result is **NOT BOUND × 3** because the loader
   that reads `DatSection1GfInvEq` rows and invokes the
   `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters is not present in
   any decompiled managed IL on disk, and cross-repo grep returns only the 8
   setter definitions with zero callers.
4. Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}`
   translation remains unresolved; the "*Eq selects setter family" hypothesis
   is recorded but explicitly not adopted.
5. TASK-E remains **BLOCKED**. No execution, scoping, or splitting packet is
   authorized or implied by this ruling.
6. All four merge gates passed and all five hard limits were respected.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact new evidence reviewed or produced,
3. exact profile-by-profile binding result,
4. exact `*ICalc` semantic result,
5. exact blocker-status ruling,
6. exact downstream authorization ruling.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Entry-gate RE posture reconfirmed | PASS | **PASS** |
| GF-side profile-by-profile binding result stated exactly | PASS | **PASS** |
| `*ICalc` semantic posture stated exactly | PASS | **PASS** |
| One explicit blocker-status and downstream ruling published | PASS | **PASS** |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is
executing a bounded reverse-engineering packet whose only purpose is to test
whether the §O blocker can now be closed honestly. If the blocker is not fully
closed on disk, preserve that result exactly and do not imply TASK-E scope or
parity by narrative drift.