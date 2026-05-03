# TCC ETU Breaker-First Schema Augmentation - Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-schema-augmentation-deeper-dll-fidelity`
Status: **Closed PASS — 2026-04-29 (Lane 1 + UI Identity Display Closure Addendum).** Breaker-root `ac_dc_code` promoted to runtime `tcc_brk_iccb / mccb / pcb` via DDL on Supabase + sourced backfill from `BreakerICCB.Acdc / BreakerMCCB.Acdc / BreakerPCB.Acdc` in `D:\TCC_NEW.accdb` (654 of 785 rows backfilled; 131 explicit NULL where source had ambiguous AC+DC duplicates or runtime/source manufacturer-assignment mismatch). `/api/v1/neta/etu/breaker-cascade?acdc=0|1` is a truthful filter, not forward-compat. CTE projects `ac_dc_code`; `_build_etu_breaker_cascade_where` emits `ac_dc_code = :acdc`; endpoint scope flows acdc to all five facet queries. The ETU summary surface now also prefers selected breaker manufacturer / breaker / breaker style identity when breaker-half state exists, and falls back to the older derived `trip_style_name + sensor_rating` label only when no actual breaker-half selection is active. UI Identity Display Closure Addendum ratified: plumbing already present under Surface C, one new fallback-pinning test added, browser-level assertion already present, and final regression now stands at **69/69 PASS in 1.71 s**, zero regressions. **Conditional later breaker-style bridge lane remains AVAILABLE but NOT currently desired.** Implementation evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-LANE1-AC-DC-CODE-IMPLEMENTATION-EVIDENCE-2026-04-29.md`. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-schema-augmentation-lane1-ac-dc-code-completion-handoff.md`.

Original status (preserved): Ready for execution
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-2026-04-29.md`
Primary packet authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-PACKET-2026-04-29.md`
Primary contract authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
Alignment authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-DB-UI-CONTRACT-ALIGNMENT-STEPS-2026-04-29.md`

---

## Objective

Execute the separate breaker-first schema-augmentation lane only if the program
chooses to strengthen the ETU breaker half beyond the current manufacturer-axis
boundary.

This handoff authorizes only the work needed to:

1. preserve `ac_dc_code` as truthful breaker-root data,
2. make `/api/v1/neta/etu/breaker-cascade` filter truthfully by `acdc`,
3. tighten the ETU UI contract only where truthful breaker-root filtering is
   real,
4. leave any deeper breaker-style bridge work as a separate later packet.

This handoff does not authorize fabricated deeper narrowing, bridge promotion,
TMT reuse as ETU authority, calc-engine changes, or a blanket parity claim.

---

## §8. UI Identity Display Closure Addendum

This packet now has one bounded UI-facing closure note in addition to the
breaker-root runtime result.

Load-bearing statement:

1. The ETU summary may show selected breaker manufacturer / breaker / breaker
   style alongside trip-unit manufacturer / type / style when the operator has
   an actual breaker-half selection active.
2. If no breaker-half selection is active, the UI must continue to fall back to
   the derived breaker-context label built from `trip_style_name + sensor_rating`.
3. Provenance remains explicit: selection-backed breaker identity is rendered as
   selection-backed, while the fallback remains rendered as derived.
4. This is a presentation/identity closure only. It does not authorize, imply,
   or prove a deeper breaker-style-to-trip-style or breaker-style-to-sensor
   bridge.

Operator reading:

1. Do not reopen schema work for this display behavior.
2. Do not describe this display closure as broader DLL parity.
3. Do not remove the manufacturer-axis advisory.
4. Do not remove the deeper-structure warning.

---

## Confirmed Entry Gate

The lane is authorized because the required upstream state is already present on
disk:

1. the ETU alignment note already names schema augmentation as the separate
   later lane for deeper DLL fidelity,
2. the ETU DLL-authority revision remains active,
3. the ETU contract-reconciliation scoping ruling remains closed PASS,
4. Slice alpha evidence still records `acdc` as a forward-compatibility no-op,
5. Slice gamma evidence still records deeper structural narrowing as outside
   the current schema ceiling,
6. the breaker aligned-design materials already preserve candidate
   `ac_dc_code` surfaces for governed promotion,
7. no newer accepted artifact is present to supersede this packet.

If any of those statements fails when execution begins, stop and return a
contradiction report rather than widening the lane implicitly.

---

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SCHEMA-AUGMENTATION-DEEPER-DLL-FIDELITY-PACKET-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-DB-UI-CONTRACT-ALIGNMENT-STEPS-2026-04-29.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-DLL-AUTHORITY-REVISION-2026-04-29.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-CONTRACT-RECONCILIATION-RUNTIME-GAP-SCOPING-RULING-2026-04-29.md`
7. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-ALPHA-BREAKER-CASCADE-BACKEND-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
8. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-STAGE1-SLICE-GAMMA-CROSS-HALF-SQL-AND-UI-SCOPING-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
9. `source-domains/neta-ett-study-material/Development/Platform/TCC/specs-and-staging/TCC-RAW-TO-ALIGNED-BREAKER-MAPPING-SPEC.md`
10. relevant aligned breaker DDL and validation drafts under
    `source-domains/neta-ett-study-material/Development/Platform/TCC/specs-and-staging/`
11. `source-domains/tcc_v5_backend/services/neta/router.py`
12. `source-domains/tcc_v5_backend/services/neta/schemas.py`
13. focused ETU breaker-cascade and cascade tests under
    `source-domains/tcc_v5_backend/tests/`

---

## First-Code And First-Validation Anchors

Start from the nearest schema-preservation and route-contract seams rather than
mapping adjacent product areas.

First anchors:

1. breaker aligned staging specs,
2. breaker-cascade route and schemas,
3. ETU cascade route,
4. focused breaker-cascade and cascade tests.

Local hypothesis:

- `acdc` can be promoted truthfully with a bounded breaker-root schema lift,
  and this lane should stop at breaker-root truth rather than absorb deeper
  bridge work.

Cheapest falsifying check:

- after the first substantive schema or bridge change, run the narrowest row-
  parity or route validation that can prove the new filter or bridge is backed
  by persisted data rather than inference.

---

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. this remains a separate schema-augmentation lane,
2. no already-closed Stage 1 surface is being reopened,
3. the program still wants fidelity beyond manufacturer-axis only.

### 2. Land breaker-root preservation first

Required outcomes:

1. `ac_dc_code` exists on promoted breaker-root authority surfaces,
2. row-parity is proven,
3. `acdc` can become truthful without claiming deeper structural narrowing.

### 3. Stop at breaker-root truth unless reauthorized

Required outcomes:

1. no deeper bridge is silently promoted,
2. the completion note states whether a separate later bridge packet is still
   desired,
3. UI wording tightens only to the breaker-root truth this lane actually lands.

### 4. Reconcile authority surfaces minimally

Required outcomes:

1. one implementation-evidence note is written,
2. one completion handoff is written,
3. the completion ruling states whether breaker-root closure PASSed and whether
   any later bridge packet is still desired.

---

## Hard Limits

1. No fabricated deeper narrowing from manufacturer equality alone.
2. No bridge promotion in this packet.
3. No TMT or EMT lane edits.
4. No calc-engine changes.
5. No broad UI redesign beyond truthful breaker-half filtering.
6. No blanket DLL-parity claim.

---

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact schema and runtime surfaces changed,
2. exact proof basis used for `acdc`,
3. exact tests and validation queries run,
4. exact evidence artifact path,
5. exact completion handoff path,
6. exact ruling: breaker-root PASS or blocker, plus whether a later bridge
   packet is still desired.
7. if UI summary identity changed, exact statement of whether it is
   selection-backed display only or a new structural bridge claim.