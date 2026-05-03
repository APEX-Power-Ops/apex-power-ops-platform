# TCC GF-Side Inverse-Equation Loader Recovery And Profile-Binding Handoff

Date: 2026-04-28
Packet: `2026-04-28-tcc-gf-side-inverse-equation-loader-recovery`
Status: **Reopened / closed PASS (pass 2) 2026-04-28** — blocker NOT CLOSED, materially narrowed further than the prior pass left it (loader is binary-confirmed absent from all four local candidate binaries: `TccBase.dll`, `EasyPower.DeviceLibrary.dll`, `EasyPower.DataLayer.dll`, `EasyPower.DatabaseBrowser.dll`); profile-binding remains NOT BOUND × 3; `*ICalc`-to-`byICalc` translation remains UNRESOLVED; TASK-E remains BLOCKED.
Previous completion handoff: `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff.md`
Pass-2 completion handoff: `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md`
Pass-2 evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md`
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`
Reopen basis: `source-domains/neta-ett-study-material/Development/temp/EasyPower.DeviceLibrary.dll` and `source-domains/neta-ett-study-material/Development/temp/TccBase.dll` are now present on local disk, satisfying the binary-availability half of DEC-018 for a fresh GF-targeted pass.

## Objective

This handoff delegates the next honest calc-engine TCC lane after TASK-019B
materially narrowed but did not close the §O blocker.

Claude Code should execute only this bounded loader-recovery lane:

1. restate the exact GF-side inverse-equation blocker preserved by TASK-019A
   and TASK-019B,
2. recover the loader path that reads `DatSection1GfInvEq` rows and invokes the
   `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters,
3. recover any translation from database `*ICalc ∈ {1, 4, 8, 10}` to kernel
   `byICalc ∈ {0, 1, 2}`,
4. publish one exact profile-by-profile binding result for all three TASK-B
   §3.9 GF-side profiles,
5. publish one exact blocker-status ruling: CLOSED, PARTIALLY CLOSED, or NOT
   CLOSED,
6. authorize only a later separate TASK-E scoping packet if blocker closure is
   actually earned.

This handoff does **not** authorize TASK-E implementation, GF-side parity
claims, fixture generation, Tier B reopening, or Phase 6 structural work.

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already
recorded on disk:

1. Spec §O still records the GF-side inverse-equation dispatch blocker in
   front of TASK-E.
2. TASK-019A closed PASS with blocker result **NOT CLOSED**.
3. TASK-019B closed PASS with blocker result **NOT CLOSED but materially
   narrowed**.
4. TASK-E remains BLOCKED; no execution, scoping, or splitting packet is
   authorized.
5. The master plan now permits a separately authored loader-recovery RE packet
   under its own authority.
6. No accepted loader-recovery evidence already exists on disk that fully
   closes the blocker.
7. Local copies of `Development/temp/EasyPower.DeviceLibrary.dll` and
   `Development/temp/TccBase.dll` are present on disk, satisfying the
   binary-availability half of DEC-018 for a reopened GF-targeted pass.

If any one of those statements fails when execution begins, stop and return a
contradiction report instead of performing new reverse-engineering work.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
2. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-BLOCKER-CLOSURE-2026-04-28.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-B-DVL-DISPATCH-ENUMERATION-2026-04-26.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
7. `source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`
8. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`

## First Anchors

Start from the exact remaining loader-side gap, not from another kernel-only
reverse-engineering pass.

### Blocker anchors

1. spec §J Path 2,
2. spec §O,
3. TASK-B §3.9,
4. TASK-019A evidence §§6 to 8,
5. TASK-019B evidence §§6 to 10.

Local hypothesis for the first slice:

- the only honest next move is to recover the missing loader path itself; no
  more kernel-only reading can close the blocker.

Cheapest falsifying check:

- verify whether accepted evidence already on disk fully recovers the loader
  and binds all three profiles. If yes, stop and report that this packet is
  unnecessary.

### Loader anchors

1. native-side `TccBase.dll` paths below the managed IL ceiling,
2. runtime call flow from `EasyPower.exe` into the eight GF-side setters,
3. preserved decompile and Ghidra artifacts already named in prior evidence.

Local hypothesis for the loader slice:

- the remaining gap can be closed only by recovering a caller path not present
  in decompiled managed IL, either by native RE or direct runtime observation.

Cheapest falsifying check:

- if neither native-side RE nor bounded runtime observation can recover the
  loader strongly enough to bind even one profile, preserve NOT CLOSED and
  return the exact narrowed gap.

## Execution Order

### 1. Reconfirm the blocker boundary

Required outcomes:

1. TASK-019A and TASK-019B still govern the current block.
2. No TASK-E scope or execution packet has opened.
3. This packet remains a bounded loader-recovery lane only.

### 2. Restate accepted structural and kernel-side knowledge

Required outcomes:

1. All GF-side profiles from TASK-B §3.9 are restated exactly.
2. The accepted kernel-side facts from TASK-019B are restated exactly.
3. The missing loader-side target is explicit before any new evidence is read.

### 3. Recover the loader path

Required outcomes:

1. Attempt native-side recovery of the caller path that populates the GF
   inverse-equation slots.
2. Attempt bounded dynamic instrumentation if native-side recovery alone is not
   sufficient.
3. Preserve unknowns explicitly where evidence does not close them.

Execution rules:

1. Prefer binary-backed evidence, instrumentation-backed traces, and stable
   on-disk findings over speculation.
2. Do not translate offset symmetry or naming similarity into semantic
   certainty.
3. Keep implementation design out of scope.

### 4. Publish the blocker ruling

Required outcomes:

1. One exact loader-recovery result is published.
2. One exact profile-by-profile binding result is published.
3. One exact blocker-status and downstream ruling is published.

Execution rules:

1. Do not authorize TASK-E implementation from this packet.
2. At most, authorize a later separate TASK-E scoping packet.
3. Prefer preserving the block over inventing closure.

## Hard Limits

1. No TASK-E implementation in this packet.
2. No GF-side parity claim unless the blocker is fully closed.
3. No fixture generation, test generation, or runtime code changes.
4. No Tier B reopening or Phase 6 widening.
5. No invented semantics for unresolved loader behavior, `*ICalc`, `*Eq`, or
   `InOut` behavior.

## Prior Execution Result (Preserved)

Execution closed PASS with the blocker materially narrowed further than
TASK-019B but still preserved.

1. The GF-side inverse-equation dispatch blocker named in
   `EASYPOWER-CALC-ENGINE-SPEC.md` §O is **NOT CLOSED**.
2. The user-pointed curve-class hierarchy files (`CTccCurveBase`,
   `CTccGenericCurveBase`, `CTccLVBreakerCurve{MCP,NSST,SST,TMT}`,
   `GFInverseEqDelay`, `GFInverseEqDelayData`, `SSTInverseEqDelay`,
   `SSTInverseEqDelayData`) are all empty-body `[NativeCppClass]` size-only
   struct stubs, proving the curve types are pure native C++ classes whose
   method bodies ILSpy cannot lift and that the loader is in unmanaged native
   code rather than any preserved managed-IL artifact.
3. The EasyPower.DeviceLibrary breaker layer is now proven read-only against
   the GF math rows: inspected breaker-named files act only as UI pickers,
   issuing description-and-setting `SELECT` queries for dropdowns and never
   reading GF inverse-equation coefficient columns.
4. EasyPower.exe is now proven read-only against the GF sub-curve: it has
   hundreds of `CTccLVBreakerCurveGF` references but zero setter calls and zero
   math-row column references, declares `ComputeAmps` and `ComputeTime` as
   extern imports from `TccBase.dll`, and accesses the GF curve as an embedded
   sub-region at byte offset `+376` of an enclosing LV breaker curve only to
   read the already-populated curve.
5. Profile-by-profile binding result remains **NOT BOUND × 3**.
6. Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}`
   translation remains **UNRESOLVED**.
7. During the prior execution, D drive was unavailable, so dynamic
   instrumentation against live `EasyPower.exe` and GF-targeted Ghidra against
   `TccBase.dll` / `EasyPower.DeviceLibrary.dll` were not executable in that
   pass; that recovery vector was preserved at closure.
8. TASK-E remains **BLOCKED**. No execution, scoping, or splitting packet is
   authorized or implied by this ruling.
9. All four merge gates passed and all five hard limits were respected.
10. This prior result is preserved as history only. The packet is now
    reopened because `Development/temp/EasyPower.DeviceLibrary.dll` and
    `Development/temp/TccBase.dll` are present on local disk and can support a
    fresh GF-targeted binary-backed pass.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact new evidence reviewed or produced,
3. exact loader-recovery result,
4. exact profile-by-profile binding result,
5. exact `*ICalc` translation result,
6. exact blocker-status ruling,
7. exact downstream authorization ruling.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Entry-gate loader-recovery posture reconfirmed | PASS | **PASS** |
| Loader path recovery result stated exactly | PASS | **PASS** |
| GF-side profile-by-profile binding result stated exactly | PASS | **PASS** |
| One explicit blocker-status and downstream ruling published | PASS | **PASS** |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is
executing a bounded loader-recovery packet whose only purpose is to test
whether the §O blocker can now be closed honestly. If the loader is not
recovered strongly enough to bind the GF-side profiles, preserve that result
exactly and do not imply TASK-E scope or parity by narrative drift.