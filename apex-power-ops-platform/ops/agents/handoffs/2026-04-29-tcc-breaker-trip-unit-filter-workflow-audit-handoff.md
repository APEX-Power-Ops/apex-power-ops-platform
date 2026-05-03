# TCC Breaker And Trip Unit Filter Workflow Audit — Authoring Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-breaker-trip-unit-filter-workflow-audit`
Status: Closed PASS — 2026-04-29. The governed audit artifact was already on
disk and has now been verified complete against the cited authority chain. See
`2026-04-29-tcc-breaker-trip-unit-filter-workflow-audit-completion-handoff.md`.

Authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
Primary decompile anchor: `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`
Supporting SQL / workflow authority:
- `source-domains/neta-ett-study-material/Development/DLL_END_TO_END_MAPPING.md`
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-DLL-SQL-SEQUENCE-MAP-2026-03-22.md`
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md`
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md`

---

## Objective

Execute the breaker / trip-unit filter-workflow audit slice for the SST / ETU
lane and record the EasyPower selection contract the current TCC front end is
missing.

This handoff authorizes only the audit slice:

1. trace the SQL-bearing and combo-driven filter workflow in `DvlEng.dll`,
2. distinguish exact preserved SQL from control-flow-backed inference,
3. compare that workflow to the current TCC front-end contract,
4. publish one governed audit artifact.

This handoff does not authorize implementation, endpoint changes, schema work,
or family expansion.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`
3. `source-domains/neta-ett-study-material/Development/DLL_END_TO_END_MAPPING.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-DLL-SQL-SEQUENCE-MAP-2026-03-22.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md`

---

## Included Surface

1. SST / ETU filter workflow only.
2. DAT-family selection and lookup flow from manufacturer through style,
   sensor, curve, and plug.
3. SQL-bearing workflow surfaces and the combo orchestration path in DVLEng.
4. Front-end fidelity gap statements already supported by the existing TCC
   planning and status docs.

---

## Excluded Surface

1. implementation planning or code changes,
2. schema or router changes,
3. parity claims,
4. TMT or EMT family workflow redesign,
5. calc-engine behavior or curve-formula semantics,
6. broad backend architecture changes.

---

## Deliverables

1. one governed audit artifact under `Development/Platform/TCC/`,
2. explicit distinction between exact SQL and workflow inference,
3. one front-end gap statement tied to the audited EasyPower workflow,
4. one next-honest-move recommendation without pre-authorizing implementation.

---

## First Anchors

1. `dvlSSTSelectCombos(...)` — combo orchestration and downstream invalidation.
2. `dvlSSTPopulateSensorCombo(...)` — style-scoped sensor filtering.
3. `dvlSSTReadSSTSensorID(...)` / `dvlSSTReadSST(...)` — identity-to-runtime
   handoff.
4. `dvlReadSSTSensorsByPlugs(...)` and the preserved `DatPlugs` queries —
   sensor-rooted plug behavior.
5. `TCC-DLL-SQL-SEQUENCE-MAP-2026-03-22.md` — upstream hardware-style lookup
   and family-routing context.

---

## Non-Negotiable Boundaries

1. Do not turn the audit into an implementation packet.
2. Do not invent literal SQL where the decompile only shows formatted resource
   strings.
3. Do not widen ETU findings into TMT or EMT claims.
4. Do not treat current backend runtime support as proof that the front-end
   workflow is already EasyPower-faithful.
5. Do not claim parity.