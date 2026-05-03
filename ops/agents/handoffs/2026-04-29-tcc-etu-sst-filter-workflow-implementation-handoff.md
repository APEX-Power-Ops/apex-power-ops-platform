# TCC ETU / SST Filter-Workflow Implementation — Authoring Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-filter-workflow-implementation`
Status: Closed PASS — 2026-04-29. Bounded cascade-terminal invalidation slice
landed inside contract with no parity claim. See
`2026-04-29-tcc-etu-sst-filter-workflow-implementation-completion-handoff.md`
and `TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md`.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-2026-04-29.md`
Workflow audit authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
Planning authority:
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md`
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md`

---

## Objective

Execute bounded implementation for the ETU / SST filter-workflow lane so the
current TCC selection surface restores the missing dependency-aware cascade
behavior evidenced in the EasyPower audit.

This handoff authorizes implementation only inside the ETU / SST lane already
bounded by the audit and planning authorities. It does not authorize TMT or
EMT work, schema redesign, calc-engine changes, or parity claims.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md`
5. `source-domains/neta-ett-study-material/Development/DLL_END_TO_END_MAPPING.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-DLL-SQL-SEQUENCE-MAP-2026-03-22.md`
7. `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`

---

## Included Surface

1. ETU / SST lane only.
2. Dependency-aware narrowing for manufacturer, type, style, and sensor.
3. Upstream invalidation of stale downstream selections.
4. Curve and plug restoration as downstream dependent outputs of resolved sensor
   identity.
5. Bounded breaker-context carry-through that remains additive operator context
   rather than a full breaker-hierarchy claim.

---

## Excluded Surface

1. TMT implementation,
2. EMT implementation,
3. schema or database redesign,
4. calc-engine or curve-formula changes,
5. broader family-unification work,
6. parity claims.

---

## Deliverables

1. bounded ETU / SST code changes,
2. one implementation evidence document under `Development/Platform/TCC/`,
3. one completion handoff,
4. task-file status and Completion Record updates,
5. at least one focused executable validation step.

---

## First Anchors

1. the current ETU selection surface that already carries manufacturer, trip
   type, trip style, and sensor state,
2. the invalidation path that should clear or refresh downstream controls when
   upstream identity changes,
3. the current curve and plug population path where dependent behavior is still
   incomplete,
4. any ETU route or backend helper currently returning filtered option sets or
   resolved sensor context,
5. the audit's `dvlSSTSelectCombos(...)`, `dvlSSTPopulateSensorCombo(...)`,
   `dvlSSTReadSSTSensorID(...)`, and plug-query anchors for matching workflow
   intent.

---

## Non-Negotiable Boundaries

1. Do not widen from ETU / SST into TMT or EMT.
2. Do not flatten family-specific ETU behavior into a fake universal selector
   model.
3. Do not treat plug or curve as independent top-level selectors.
4. Do not invent a full breaker-side runtime hierarchy.
5. Do not claim parity.