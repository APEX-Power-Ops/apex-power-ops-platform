---
dispatch_id: 2026-05-31-cc-tcc-explorer-dualaxis-rebuild
target: CC
priority: 2
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: 2026-05-31-cc-tcc-explorer-quickwins
closeout: ops/agents/handoffs/2026-05-31-tcc-explorer-dualaxis-rebuild-closeout.md
---

# TCC Explorer dual-axis rebuild — EasyPower breaker × trip-unit selection with manufacturer cross-filter

**Lane:** TCC breaker explorer EasyPower-realign, structural. **Spec of record:** `apps/operations-web/TCC_EXPLORER_REALIGN_SPEC_2026-05-31.md` (§A target workflow + §D items 5-7). Builds on the quick-wins dispatch (predecessor). Reshapes the single-`family` explorer into EasyPower's **two-axis, manufacturer-cross-filtered** selection. **Primarily operations-web (UI composition); no new backend endpoints/views** — both axes already exist server-side (the gating data fact is RESOLVED: `/etu/search` has no construction column, so dual filtering is a manufacturer intersection). **CODE-ONLY; reversible; parity-gated.** Follow the inbox lifecycle (claim-push BEFORE editing).

## Target (from spec §A)
Two axes present together, terminating in a fully-qualified `(breaker_style, sensor/frame)` device:
- **Axis 1 — Breaker:** `Mfr → Class {ICCB|MCCB|PCB} → Breaker → Style` via `GET /etu/breaker-cascade` (`fetchEtuBreakerCascade`, `lib/breaker-resources.ts:594`; params `manufacturer_id/breaker_class/breaker_id/breaker_style_id`).
- **Axis 2 — Trip unit:** `Mfr → Type {ETU|TMT|EMT} → Style → Sensor/Rating` via `/etu/search` (+ TMT/EMT search).
- **Cross-filter at `manufacturer_id` ONLY** (no deeper mapping persisted). Selecting on one axis narrows the other to compatible manufacturers.

## Execute (gated)
1. **Claim** before editing.
2. **Pre-build verification (report):** confirm against live + code (a) `/etu/breaker-cascade` returns the `manufacturer_id/breaker_class/breaker_id/breaker_style_id` cascade levels and accepts `trip_type_id`/`sensor_id` cross-filter params; (b) `/etu/search` accepts `manufacturer_id` (`router.py:3062`); (c) **whether EMT exposes ANY construction signal** (spec §D-7 open question) — if not, EMT axis-1 is manufacturer-only; document it.
3. **Build the dual-axis form** (`breaker-resource-explorer.tsx` + panels):
   - Render **Axis 1 (breaker cascade)** as a primary front-of-form control for all families (move it out of the passive post-selection "breaker matches" card).
   - Keep **Axis 2 (trip-unit)** with the Type {ETU/TMT/EMT} + style/sensor + the (quick-wins) manufacturer-prioritized search.
   - **Cross-filter wiring:** breaker-half selections (manufacturer, and where applicable class) constrain Axis-2 search via `manufacturer_id`; trip-unit-half selections pass `trip_type_id`/`sensor_id` into the breaker-cascade. Order-independent (tester may start on either axis); both narrow to the shared manufacturer set.
   - On both axes committed → load `/context` + `/settings` → `/plot-tcc` → render the NETA test-plan table (from the quick-wins work), scoped by the chosen breaker context label.
4. **Local:** typecheck + build + extend the breaker Playwright smoke to cover the dual-axis flow (pick a breaker class + a trip-unit, assert cross-filter narrows manufacturers, assert the device loads + the test-plan table renders). Report pass counts.
5. **Commit + push**; wait for Vercel (+ Render if any backend param tweak). 
6. **Post-deploy gate:**
   - Dual-axis flow works hosted: selecting Breaker Class=ICCB narrows trip-unit manufacturers; selecting Trip Unit Type=ETU narrows breaker manufacturers; a committed `(breaker, sensor)` loads context+settings+test-plan table.
   - No regression: ETU 3/0, relay 6/6, breaker catalog 63/17831, TMT/EMT facets 200.
   - Any FAIL → revert, report.

## Guardrails
- **Composition + UI only** (plus at most passing an existing `manufacturer_id`/cross-filter param). **No new endpoints, no new views, no DB DDL.** If the build appears to need a new backend join/view, STOP and report (the design is manufacturer-intersection by spec).
- Scoped `git add`. DSN out-of-band; no `.env*` contents.

## Closeout
Record: the pre-build verification (cascade params + EMT construction finding), the dual-axis form structure, cross-filter wiring, local + smoke results, commit hash(es), deploy confirmation, the post-deploy dual-axis gate, and any EMT-axis decision. Then `git mv` claimed→done, commit, push. **On PASS, the explorer matches EasyPower's dual breaker×trip-unit methodology and delivers the NETA pickup/time-delay tolerance test plan end-to-end.**
