# TCC ETU / SST Remaining Gap Scoping — Execution Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-remaining-gap-scoping`
Status: Closed PASS — 2026-04-29. Scoping ruling published and three later
separate implementation slices are now authorizable. See
`2026-04-29-tcc-etu-sst-remaining-gap-scoping-completion-handoff.md` and
`TCC-ETU-SST-REMAINING-GAP-SCOPING-RULING-2026-04-29.md`.

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-REMAINING-GAP-SCOPING-2026-04-29.md`
Primary gap authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
Closed implementation slice:
- `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
- `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-filter-workflow-implementation-completion-handoff.md`

---

## Objective

Scope the ETU / SST workflow-fidelity gap that still remains open after the
bounded plug-terminal invalidation fix.

This handoff authorizes scoping only. It does not authorize implementation,
schema changes, TMT / EMT work, calc-engine work, or parity claims.

---

## Required Reads

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-REMAINING-GAP-SCOPING-2026-04-29.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-filter-workflow-implementation-completion-handoff.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md`
7. `source-domains/tcc_v5_backend/demo/neta_tcc.html`
8. `source-domains/tcc_v5_backend/services/neta/router.py`

---

## Included Surface

1. Richer DAT-family SQL surfacing for the ETU / SST lane.
2. Plug-aware reverse filtering or validation lookups.
3. Stronger explicit breaker-half representation within the existing bounded ETU
   posture.
4. The boundary between collapsed `sensor_id` runtime support and the richer
   guided-selection contract the audit still names as missing.

---

## Excluded Surface

1. Immediate implementation.
2. TMT or EMT work.
3. Schema or migration work.
4. Calc-engine or curve-formula work.
5. Full breaker-hierarchy invention.
6. Parity claims.

---

## First Anchors

1. Audit Gap 1 — breaker-half / trip-unit-half linkage.
2. Audit Gap 3 — plug-aware reverse filtering as advanced compatibility
   behavior.
3. Audit Gap 4 — richer DAT-family SQL contract than the current frontend
   contract.
4. The ETU / SST implementation evidence showing exactly what is already closed.
5. The current ETU / SST frontend and backend seams in `neta_tcc.html` and
   `router.py`.

---

## Non-Negotiable Boundaries

1. Do not implement repairs in this packet.
2. Do not widen from ETU / SST into TMT or EMT.
3. Do not invent a full breaker-side runtime hierarchy.
4. Do not reopen the already-closed plug-terminal invalidation slice.
5. Do not claim parity.

---

## Expected Deliverables Back To Copilot

1. Exact files read or touched.
2. The included and excluded surfaces for any later separate implementation
   packet.
3. The verification or inspection step run and result.
4. One explicit downstream ruling saying whether a later separate
   implementation packet is now authorizable and on what exact bounded surface.