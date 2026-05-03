# TCC ETU / SST Remaining Gap Scoping — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-etu-sst-remaining-gap-scoping`
Status: **Closed PASS — scoping ruling published; three independently-scopable later slices authorized**

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-REMAINING-GAP-SCOPING-2026-04-29.md`
Execution handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-remaining-gap-scoping-handoff.md`
Primary gap authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md`
Closed-slice anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md`
Scoping ruling: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-REMAINING-GAP-SCOPING-RULING-2026-04-29.md`

---

## Summary

The remaining ETU / SST workflow-fidelity gap that survived the bounded
plug-terminal invalidation slice is now decomposed and ruled. The truthful
result on disk is that the gap is materially smaller than the 2026-04-29
audit's full surface enumeration suggested. Three independently scopable
later slices are now authorizable, each on a bounded surface that prevents
widening into TMT, EMT, schema, calc-engine, or parity-claim territory.

This packet is scoping only. No code, schema, or runtime change was made.
No parity claim is made.

---

## Files Read Or Touched

### Read for verification (no edits)

1. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-remaining-gap-scoping-handoff.md` — execution handoff manifest.
2. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-REMAINING-GAP-SCOPING-2026-04-29.md` — task authority.
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-BREAKER-TRIP-UNIT-FILTER-WORKFLOW-AUDIT-2026-04-29.md` — primary gap authority.
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-FILTER-WORKFLOW-IMPLEMENTATION-EVIDENCE-2026-04-29.md` — closed-slice anchor.
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-filter-workflow-implementation-completion-handoff.md` — closed-slice handoff.
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-EASYPOWER-CASCADE-UI-IMPLEMENTATION-PLAN-2026-03-24.md` — cascade-contract authority.
7. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SELECTION-MODEL-STATUS-2026-03-24.md` — bounded ETU runtime-posture authority.
8. `source-domains/tcc_v5_backend/services/neta/router.py` — backend route surfaces.
9. `source-domains/tcc_v5_backend/demo/neta_tcc.html` — frontend cascade and breaker-context-label seams.
10. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/20260426_006_phase3_atomic_swap.sql` — `vw_trip_unit_cascade` definition.

### Written

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ETU-SST-REMAINING-GAP-SCOPING-RULING-2026-04-29.md` — scoping ruling.
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-etu-sst-remaining-gap-scoping-completion-handoff.md` — this completion handoff.
3. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-ETU-SST-REMAINING-GAP-SCOPING-2026-04-29.md` — Status line + Completion Record.

No code, schema, migration, or runtime change was made.

---

## Included And Excluded Surfaces For Any Later Separate Implementation Packet

### Included (a later separate packet, authored against ANY ONE of these slices, is authorizable)

1. Guided-selection step-indicator display affordance bundling Surface A
   (named-step identity tuples) and Surface D (guided-workflow shape). UI only.
2. Breaker-context provenance disclosure on ETU resolved-equipment summary
   surfaces (Surface C). UI attribution only.
3. Bounded plug-aware reverse-filter compatibility lookup endpoint plus a
   small UI affordance (Surface B). Mixed (one new backend route + small UI),
   strictly scoped as compatibility-validation, never as upstream selector.

### Excluded (any later packet must explicitly disclaim each)

1. TMT cascade work of any kind.
2. EMT cascade work of any kind.
3. Schema or migration changes.
4. Calc-engine or curve-formula changes.
5. Inventing a full breaker-side runtime hierarchy.
6. Promoting plug to an upstream selector.
7. Parity claims against EasyPower.
8. Reopening the closed plug-terminal invalidation slice.
9. Replacing `fn_sensor_available_settings(sensor_id)` with multi-step
   per-table fetchers.

---

## Verification / Inspection Step Run

Per Acceptance Criterion 5 / Required Output 4, two focused inspection
queries were run against the canonical Postgres database via the Supabase MCP.

**Inspection 1 — `vw_trip_unit_cascade` exposes no breaker-half columns.**
The view definition lives in
`migrations/phase3_supabase_rebuild/20260426_006_phase3_atomic_swap.sql`
lines 338-376. Information-schema query confirmed 19 columns, all on the
trip-unit + sensor side; zero `breaker_id`, `breaker_name`, `breaker_class`,
or `breaker_style_id` columns. This grounds Surface C's classification: any
"stronger breaker-half representation" work must remain attribution / labeling
honesty, not ancestry invention.

**Inspection 2 — No plug-aware reverse-filter routine or view exists.**
Information-schema queries against `routines` and `views` for any name
matching `%plug%`, `%matching%`, `%reverse%`, or `%sensor_by%` returned
empty result sets. This grounds Surface B's classification: a later Surface B
packet is a true net-new bounded addition.

Both queries are recorded verbatim in the scoping ruling.

---

## Acceptance Criteria Trace

| Criterion | Status |
|---|---|
| 1. Remaining ETU / SST gap decomposed into explicit included and excluded surfaces | PASS — see scoping ruling §"Decomposition" and §"Included / Excluded Surface". |
| 2. Already-satisfied surfaces not accidentally rescoped as still missing | PASS — each surface has an explicit "Already satisfied" subsection. |
| 3. Breaker-half representation handled as bounded context, not fake full hierarchy | PASS — Surface C scoped to attribution / labeling only; runtime-hierarchy invention explicitly excluded. |
| 4. Plug-aware reverse filtering described as ETU/SST-only and not widened into TMT/EMT | PASS — Surface B excludes TMT/EMT and excludes upstream-selector promotion. |
| 5. At least one focused verification or inspection step run | PASS — two SQL information-schema inspections recorded in scoping ruling. |
| 6. Ruling states clearly whether a later separate implementation packet is authorizable | PASS — three independently scopable slices authorized. |
| 7. No implementation or parity claim made | PASS — no code, schema, or runtime change; parity explicitly disclaimed. |

---

## Decision Boundary Answers

The execution handoff's Decision Boundary asked four questions. Answers:

1. **What exact ETU / SST workflow-fidelity surfaces still remain open after
   the plug-terminal invalidation fix?**
   Surface A (richer DAT-family SQL surfacing — UI display fidelity only),
   Surface B (plug-aware reverse filtering as compatibility lookup), Surface C
   (breaker-half representation as attribution honesty), and Surface D
   (guided-selection UI shape — same data slice as Surface A).

2. **Which of those are frontend-only, backend-support, or mixed?**
   A: frontend-only. B: mixed. C: frontend-only. D: frontend-only.

3. **Can a later separate implementation packet now be authored honestly, and
   if so, what exact surface may it include?**
   Yes. Three independently scopable slices are authorizable:
   - a bundled A+D guided-workflow display affordance,
   - a Surface C breaker-context provenance disclosure,
   - a Surface B reverse-filter compatibility lookup.
   Each must be its own separately governed packet.

4. **What exact surfaces must remain excluded to avoid widening into TMT /
   EMT, parity claims, or a false breaker hierarchy?**
   The nine items listed under "Excluded" above. Most load-bearing: no TMT
   or EMT widening; no full breaker-side runtime hierarchy invention; no
   promotion of plug to an upstream selector.

---

## Out-Of-Scope Items Explicitly Not Touched

1. TMT cascade — no edits.
2. EMT cascade — no edits.
3. Schema or migrations — none.
4. Calc-engine or curve-formula semantics — none.
5. Backend router endpoints, schemas, or RPCs — none.
6. Frontend HTML / JS — none.
7. The closed plug-terminal invalidation slice — not reopened.
8. Parity acceptance — not claimed.
9. Full breaker-side runtime hierarchy — not introduced.

---

## Exact Downstream Ruling

A later separate implementation packet on the remaining ETU / SST gap surface
**is authorizable**, on **exactly the following bounded surfaces**:

1. A guided-selection step-indicator display affordance bundling Surface A
   (named-step identity tuples) and Surface D (guided-workflow shape) — UI
   only, no backend or schema change.
2. A breaker-context provenance disclosure on user-visible ETU summary
   surfaces covering Surface C — UI attribution only, no backend extension to
   invent breaker-side ancestry.
3. A bounded plug-aware reverse-filter compatibility lookup covering Surface B
   — one new backend route plus one small UI affordance, scoped strictly as a
   compatibility-validation control and not as an upstream selector promotion.

Each slice must be authored as its own separately governed packet. Bundling
two or three of them into one packet is **not** authorized by this ruling.

This completion handoff does not pre-authorize any of the three later packets.
The user remains the next authorizing party for each.

---

## Bottom Line

The remaining ETU / SST workflow-fidelity gap is now decomposed, classified,
and ruled. Three independently-scopable later slices are authorizable; one
prior surface (richer DAT-family SQL surfacing) collapses into a UI-only
display question rather than a runtime-extension question. The runtime
remains operationally satisfied; the missing fidelity is in user-visible
workflow shape and attribution honesty, plus one bounded compatibility
lookup.

The scoping packet is closed PASS.
