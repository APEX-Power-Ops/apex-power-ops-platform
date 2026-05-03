# TCC GF-Side Inverse-Equation Dispatch-Profile RE — Completion Handoff

Date: 2026-04-28
Packet: `2026-04-28-tcc-gf-side-inverse-equation-dispatch-re`
Status: **Closed PASS**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Companion ruling: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-BLOCKER-CLOSURE-2026-04-28.md`

## Headline Result

The bounded GF-side inverse-equation dispatch-profile RE packet executed end
to end. The truthful ruling on disk is:

> **The GF-side inverse-equation dispatch blocker named in
> `EASYPOWER-CALC-ENGINE-SPEC.md` §O is NOT CLOSED, but materially narrowed.**

The kernel side of the blocker is now reverse-engineered from `TccBase.dll`
binary; the loader side — the code that reads `DatSection1GfInvEq` rows and
calls the `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters — is not
present in any decompiled managed IL on disk. By the parent task's
Stop-And-Flag rule 1, no profile-to-setter binding is asserted; by Hard
Limit 2, no GF-side parity claim is implied.

TASK-E remains BLOCKED. No TASK-E execution, scoping, or splitting packet is
authorized. No spec, master-plan, runtime, schema, migration, fixture, or
test edits were made beyond the Authority-Surface Reconciliation list in the
evidence document §11.

## Exact Files Changed

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
   — new evidence document.
2. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`
   — Status banner advanced from "Authored 2026-04-28. Not yet executed." to
   "Closed PASS 2026-04-28"; Completion Record advanced from placeholder to
   five-item closure record.
3. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
   — Current Program Posture extended from 14 items to 15 items (item 12
   advanced to record this packet's closure result; new item 13 records that
   no calc-engine move is automatically queued; old items 13/14 renumbered to
   14/15); Stakeholder Approval Posture row "GF-side inverse-equation
   dispatch-profile RE packet" advanced from "Approved and next" to
   "Approved and closed"; Phase 6 implementation table TASK-019B row given
   its closure result with checkmark and date; Decision Ledger gained
   DEC-016.
4. This completion handoff.

No other authority surface is touched. The active calc-engine spec is **not**
edited; the per-element interpretation docs are **not** edited; the TASK-CC
findings ledger is **not** edited; runtime, schema, migration, fixture, and
test surfaces are **not** edited.

## Exact New Evidence Reviewed Or Produced

### New evidence reviewed (file-backed and binary-backed)

1. ILSpy decompile `C:\Users\jjswe\Box\TCC_Master\DLL\CTccLVBreakerCurveGF.cs`
   — read end to end with focus on:
   - `CalcAnsiEqGF` (lines 86–212) — `byICalc ∈ {0, 1, 2}` reference-current
     selector;
   - `CalcThermEq` (lines 219–305) — same `byICalc ∈ {0, 1, 2}` selector;
   - per-band runtime dispatcher (lines 1217–1402, inside switch case 3) —
     reads slot kernel discriminator at offsets `[272]`, `[376]`, `[480]`,
     `[584]` and per-slot byICalc at offsets `[273]`, `[377]`, `[481]`,
     `[585]`;
   - `GetInverseEnteredAt` (lines 656–664) — corroborates the
     `{0 → ref[16], 1 → ref[13], 2 → ref[12]}` mapping;
   - `NormalizeAmps` / `NormalizeGFPU` (lines 728–759) — adjacent enum
     `{1, 2, 6, 7, 8, 9}`, separate from kernel `byICalc` and from database
     `DS1GF_PICKUP_CALC`;
   - 8 setter definitions (lines 1913–2070) — all 8 write a specific
     `0`/`1` to the slot kernel discriminator and copy the byICalc parameter
     plus the equation coefficients into the slot's doubles.
2. Whole-module decompile
   `C:\Users\jjswe\Box\TCC_Master\Decompile\TCCBase\-Module-.cs` — read the
   `GFInverseEqDelayData` constructor + `IsTherm`/`IsAnsi`/`IsFDly` (lines
   7602–7656), the `GFInverseEqDelay` constructor + `IsIn`/`IsOut` (lines
   7659–7683), and the `CTccLVBreakerCurveGF` constructor (lines 7685–7752)
   showing two `GFInverseEqDelay` instances at offsets `264` and `824`.
3. ILSpy struct files
   `C:\APEX Platform\source-domains\neta-ett-study-material\Development\temp\ilspy-easypower\TccBase\GFInverseEqDelay.cs`
   (size = 424) and
   `C:\APEX Platform\source-domains\neta-ett-study-material\Development\temp\ilspy-easypower\TccBase\GFInverseEqDelayData.cs`
   (size = 104; nested unnamed types named `sTherm` (40 bytes), `sAnsi`
   (48 bytes), `sFDly` (8 bytes)).
4. Loader audit — searched for callers of all eight GF setters across:
   - `C:\Users\jjswe\Box\TCC_Master\DLL\` and `C:\Users\jjswe\Box\TCC_Master\Decompile\`,
   - `C:\APEX Platform\source-domains\neta-ett-study-material\Development\temp\ilspy-easypower-database\`,
     `…\ilspy-easypower-types\`, `…\ilspy-easypower-equipment-ui\`,
     `…\ilspy-easypower-exe\`, `…\ilspy-easypower-exe-il\`, `…\ilspy-dvleng\`.
   Result: only the 8 setter **definitions** themselves; **zero callers**.
   Same posture as TASK-CC §5 found for SST-side `SetSTDB_*` / `CalcThermEq3`
   on Series B.
5. `EasyPower.DeviceLibrary.DeviceLibrary.cs` — reviewed `ReadGroundDelay`
   (lines 1275–1304); confirmed it only reads `[Desc]` from
   `DatSection1GfInvEq` for UI display, does NOT load math row data and does
   NOT call any setter.

### New evidence produced

The single deliverable is the evidence document at
`Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-DISPATCH-RE-2026-04-28.md`.
It records:

- the 6 entry-gate verifications,
- the binary-backed sources actually consulted and the cross-repo grep that
  proves the loader is not on disk,
- the structural inputs restated verbatim (TASK-B §3.9 profiles, `*ICalc`
  enum, available kernels and setters, accepted unknowns),
- the bounded RE recovery of memory layout, kernel discriminator encoding,
  in-class dispatcher branching, and kernel `byICalc` semantics,
- the profile-by-profile binding result (NOT BOUND × 3),
- the per-value `*ICalc` semantic result (kernel-internal mapping resolved;
  database-to-kernel translation unresolved),
- the blocker-status ruling (NOT CLOSED),
- the TASK-E scope decision (BLOCKED),
- the next-step ruling (continued block, with the exact narrowed gap named),
- authority-surface reconciliation, acceptance-criteria mapping (6 of 6
  PASS), and hard-limit reconciliation (5 of 5 PASS).

## Exact Profile-By-Profile Binding Result

| Profile | Composition | n | Style attribution | Binding |
|---|---|---|---|---|
| InOut=0 | `*ICalc=(8,8,4,4)`, `*Eq=(0,0,0,0)` | 1,690 | unattributed | **NOT BOUND** |
| InOut=1 | `*ICalc=(4,4,8,8)`, `*Eq=(0,0,1,1)` | 100 | Federal Pioneer LSIG / LSIG (2) / LVPCB | **NOT BOUND** |
| InOut=2 | `*ICalc=(8,8,1,1)`, `*Eq=(0,0,0,0)` | 6,760 | most Square D Micrologic 6.x and MTZ frames | **NOT BOUND** |

For each profile: the eight candidate setters
(`Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}`) and the kernel byICalc
semantics are now known from binary, but the loader call site that takes a
specific `DatSection1GfInvEq` row and invokes a specific setter with a
specific byICalc value is not on disk. The "*Eq byte selects setter family"
hypothesis (motivated by the recovered `IsTherm=0, IsAnsi=1` encoding and the
fact that GF-side `*Eq=1` only appears in the InOut=1 profile) is recorded
in evidence §6.2 and §7 but explicitly **not adopted** per Stop-And-Flag
rule 2.

## Exact `*ICalc` Semantic Result

| `*ICalc` | Kernel-internal semantic if passed directly | Loader-observed translation | Final per-value semantic |
|---|---|---|---|
| `1` | reference current = `((double*)P_0)[13]` | not on disk | partially resolved — kernel-side recovered, loader-side translation unverified |
| `4` | falls through; kernel emits zero curve points | not on disk | unresolved |
| `8` | falls through; kernel emits zero curve points | not on disk | unresolved |
| `10` | falls through; kernel emits zero curve points | not on disk | unresolved (also: value `10` does not appear in any GF-side `DatSection1GfInvEq` row per TASK-B §3.9; appears only on STD side) |

The kernel-internal `byICalc ∈ {0, 1, 2}` mapping is fully reverse-engineered
from binary. The translation between database `*ICalc ∈ {1, 4, 8, 10}` and
kernel `byICalc` is not recovered from accessible disk evidence. Direct
pass-through is implausible (would yield zero curves for the dominant
InOut=0 and InOut=1 profiles), but implausibility is not the same as a
recovered translation table.

## Exact Blocker-Status Ruling

**NOT CLOSED.**

The §O blocker — "the 5 `*ICalc` `{1, 4, 8, 10}` GF-side dispatch profiles
in §J Path 2 must be reverse-engineered before claiming GF-side parity" —
is materially narrowed but not resolved by anything on disk today. Material
RE progress was earned and is recorded in evidence §5.1–§5.4:

1. per-slot kernel discriminator bound to `{0=Therm, 1=Ansi, 2=FDly}`;
2. kernel `byICalc` parameter bound to
   `{0 → ref[16], 1 → ref[13], 2 → ref[12], else → no curve}`;
3. per-slot offsets `(272/273, 376/377, 480/481, 584/585)` bound to the
   four setter families.

But the actual §O question — profile-to-setter binding — requires the
loader, which is not on disk.

## Exact Downstream Authorization Ruling

**Continued block. TASK-E remains BLOCKED.**

1. No TASK-E execution packet is authorized.
2. No TASK-E scoping or splitting packet is implied or queued.
3. No TASK-F fixture-generation packet is authorized; deferred independently.
4. No spec reopen, master-plan re-sequencing, or policy change is implied.
   Spec §O retains its current "Authorized in narrow scope only after the
   matching open question closes" wording without modification. Master-plan
   TASK-019 retains its current "Open TASK-E inverse-equation scoping only
   after the matching calc-engine open question closes honestly enough to
   support bounded implementation or parity claims" wording.
5. The exact remaining gap is preserved verbatim and **narrowed** to:
   "locate the loader code that reads `DatSection1GfInvEq` rows and calls
   the `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}(byICalc, …)`
   setters, and recover the row-column-to-setter-argument binding plus any
   `*ICalc`-to-`byICalc` translation."
6. Tier B Slice 3 measurement-target gate (DEC-013), the consumer-need /
   adoption-reopen-trigger gate (DEC-012), and the post-Slice-2 adoption
   HOLD (DEC-010) all remain operative without modification.

## Merge Gate Outcomes

| Gate | Target result | Actual outcome |
|---|---|---|
| Entry-gate RE posture reconfirmed | PASS | **PASS** — 6 of 6 verified (evidence §2) |
| GF-side profile-by-profile binding result stated exactly | PASS | **PASS** — three profiles addressed individually, all NOT BOUND with explicit reasons (evidence §6) |
| `*ICalc` semantic posture stated exactly | PASS | **PASS** — kernel-internal mapping bound, database-to-kernel translation explicitly unresolved (evidence §7) |
| One explicit blocker-status and downstream ruling published | PASS | **PASS** — NOT CLOSED + TASK-E remains BLOCKED (evidence §8 / §9 / §10) |

## Auditor Note

Copilot remains the project manager and auditor. Claude Code executed a
bounded reverse-engineering packet whose only purpose was to test whether
the §O blocker can now be closed honestly. The blocker is not fully closed
on disk, so this packet preserved that result exactly and did not imply
TASK-E scope or parity by narrative drift. The kernel-side recovery is
substantial and verifiable from `TccBase.dll` directly; the loader-side gap
is preserved exactly so that any future RE packet has a concrete starting
scope.
