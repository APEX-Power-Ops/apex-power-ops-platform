---
dispatch_id: 2026-05-31-cc-tcc-explorer-quickwins
target: CC
priority: 1
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: 2026-05-30-cc-d012-relay-orm-hygiene
closeout: ops/agents/handoffs/2026-05-31-tcc-explorer-quickwins-closeout.md
---

# TCC Explorer quick wins — render the NETA test-plan table + tolerance bands + search precision + relabel

**Lane:** TCC breaker explorer EasyPower-realign, quick-wins (no schema). **Spec of record:** `apps/operations-web/TCC_EXPLORER_REALIGN_SPEC_2026-05-31.md` (read it first — §A workflow, §B the 7-element tolerance test plan, §D fix plan). These four changes deliver the operator's stated purpose — **per-element pickup/time-delay tolerances for NETA testing** — without any DB/schema work, because the test plan is already computed and already fetched. **CODE-ONLY; reversible; parity-gated.** Follow the inbox lifecycle (claim-push BEFORE editing).

## The four changes

### 1. [UI — highest value] Render the NETA test-plan table
The explorer already fetches `selection.plot.table_rows` (`EtuPlotResponse.table_rows: EtuPlotTableRow[]`, `lib/breaker-resources.ts:186-223`) via `buildEtuPlotRequest`→`fetchEtuPlot` — but `breaker-selection-panels.tsx` renders only the curve + markers, never the table. **Add a "NETA Test Plan" table section** in `breaker-selection-panels.tsx` consuming `table_rows`, with columns:
`Element | Setting | Test current (×mult) | Expected pickup | Lo | Hi | Expected time | Time-lo | Time-hi | Method`
mapping to `EtuPlotTableRow` fields (`element, setting, test_multiple, expected_current, limit_low, limit_high, expected_time, time_limit_low, time_limit_high, calc_method, notes`). Skip rows where the element is absent (null expected / calc_method indicating −1). Render time fields only when present (pickup-only elements have null times). Do the same for TMT/EMT where their plot responses carry tolerance rows/fields (`TMTSettingOption.tol_lo/hi`, `EMTSectionSummary.pickup_tol_lo/hi`) — if the TMT/EMT plot payloads don't already carry a comparable per-element row set, surface their available tolerance fields as the equivalent table and note the asymmetry in the closeout.

### 2. [UI] Tolerances as NETA bands
Wherever tolerances are shown as raw `tol -10 to +10` (e.g. `breaker-selection-panels.tsx:706`), render them as the **band the tester uses**: `expected → [lo, hi]` (absolute values where an expected exists; otherwise the ± percentages clearly labeled). Reuse the table_rows `limit_low/high` for ETU.

### 3. [backend + UI] Search precision (the "GE" problem)
- **UI:** remove the hardcoded default seed `etu: 'GE'` (`breaker-resource-explorer.tsx:50`) so the explorer doesn't auto-flood on load (start empty or a neutral placeholder).
- **Backend:** in `_build_etu_search_where` (`apps/control-plane-api/services/neta/router.py:1668-1687`), make `q` **manufacturer-prioritized** instead of a blanket `%q%` across 4 columns: rank/anchor exact + prefix `manufacturer_name` matches first and demote `trip_type_name/trip_style_name/sensor_desc` to a secondary fallback (or gate the style/desc match so short tokens match manufacturer on a word/prefix boundary). Keep it a single route, backward-compatible.
- **Acceptance:** live `GET /etu/search?q=GE` returns real **GE / GEIS** manufacturer rows at the TOP (not `(Generic)`/`Challenger`/`Atom Power` substring noise); `q=Challenger` still returns Challenger; empty `q` still returns the family.

### 4. [UI] Relabel
"Breaker family" → **"Trip Unit Type"** (`breaker-resource-explorer.tsx:423`), matching EasyPower Axis-2 vocabulary. (Do NOT build the construction axis here — that's the dual-axis rebuild dispatch.)

## Execute (gated)
1. **Claim** (git mv pending→claimed, push) BEFORE editing.
2. Implement 1-4. Scoped edits: `breaker-selection-panels.tsx`, `breaker-resource-explorer.tsx`, `lib/breaker-resources.ts` (if a request param/type tweak is needed), `router.py:1668-1687`.
3. **Local:** operations-web typecheck + build + breaker Playwright smoke (extend the smoke to assert the test-plan table renders for a known ETU sensor); control-plane ETU search tests (`tests/test_etu_search_route.py` — there's a GE assertion at ~:80; update/extend it for the new ranking). Report pass counts.
4. **Commit + push** (Render redeploys control-plane; Vercel redeploys operations-web). Wait for both deploys.
5. **Post-deploy gate:**
   - `GET /api/v1/neta/etu/search?q=GE&limit=5` → real GE/GEIS rows at top (manufacturer match wins).
   - ETU SQL parity probe 3/0; relay parity 6/6; breaker `catalog/status` 63/17831 (no regression).
   - operations-web: the breaker explorer renders the NETA test-plan table for a selected ETU sensor (verify via the Playwright smoke or a hosted check).
   - Any FAIL → revert, report.

## Guardrails
- **Quick wins only.** No dual-axis form / no breaker-construction axis (next dispatch). No DB DDL. Schema-qualification already done (D-012).
- Scoped `git add` (the listed files + the smoke + closeout). DSN out-of-band; no `.env*` contents.

## Closeout
Record: each of the 4 changes (with the test-plan table columns shown), local test results, commit hash(es), both deploy confirmations, the post-deploy gate (esp. `q=GE` now manufacturer-first + the rendered table), and TMT/EMT tolerance-table handling. Then `git mv` claimed→done, commit, push. **Next:** the dual-axis rebuild dispatch (`2026-05-31-cc-tcc-explorer-dualaxis-rebuild`).
