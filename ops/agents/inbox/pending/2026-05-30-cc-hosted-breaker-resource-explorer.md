---
dispatch_id: 2026-05-30-cc-hosted-breaker-resource-explorer
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-ltpu-stpu-tolerance-characterization
closeout: ops/agents/handoffs/2026-05-30-hosted-breaker-resource-explorer-closeout.md
---

# Hosted breaker resource explorer — converge breaker onto operations.apex (Breaker↔Relay Parity step 3)

**Lane:** TCC Breaker↔Relay Parity — **step 3 of 3** (UI convergence; Decision 011). **Operator authorization: GRANTED.** This is a **frontend convergence build** on the host VS Code seat. Follow the inbox lifecycle (claim-push BEFORE executing).

## Why
Parity steps 1 & 2 are closed — **calc/data parity is met on both lanes** (relay proven vs live §69; breaker ETU tolerance characterized vs source §70). The breaker **backend** is already hosted-parity-proven against `control.apexpowerops.com` (ETU SQL parity 3/0; catalog 63/17,831). The relay **frontend** (`RelayResourceExplorer`) is the proven hosted template on `operations.apexpowerops.com`, and CORS is already shipped (§67) so cross-origin reads from the operations-web shell work. The only thing the breaker lane lacks is the hosted browser surface relay now has. Per Decision 011 (single hosted product UI), breaker should look/work like relay in the field — the breaker's current consumer is a **local-only demo** (`neta_tcc.html` @127.0.0.1:8765, never hosted). This dispatch closes that gap.

## Goal
A **read-only hosted breaker resource explorer** in `apps/operations-web`, mounted on `operations.apexpowerops.com`, mirroring `RelayResourceExplorer`, covering the three breaker families **ETU / TMT / EMT**, consuming the **existing, proven** breaker routes (no backend changes).

### Scope — IN
- New frontend surface mirroring the relay pattern:
  - `apps/operations-web/app/breaker-resource-explorer.tsx` (mirror `app/relay-resource-explorer.tsx`)
  - selection panels as needed (mirror `app/relay-selection-panels.tsx`)
  - `apps/operations-web/lib/breaker-resources.ts` (mirror `lib/relay-resources.ts`) — typed client over the breaker routes, using `lib/browser-env.ts` `controlPlaneBaseUrl` (same cross-origin path relay uses, already CORS-backed)
  - mount in `app/page.tsx` alongside the relay explorer
- **Family select** (ETU / TMT / EMT) → browse → **context + settings view** → **static trip curve** rendered from the server plot route. Read-only.
- Honest unavailable-state handling like relay (if a route/family is unavailable, surface a clear message — mirror the relay "could not be reached"/empty-state treatment; do not crash the shell).

### Routes to consume (already proven — consume as-is, do NOT modify)
- Catalog: `GET /api/v1/neta/catalog/status`
- **ETU:** `GET /etu/search`, `GET /etu/breaker-cascade`, `GET /context/{sensor_id}`, `GET /settings/{sensor_id}`, **plot via `POST /api/v1/neta/plot-tcc`** (ETU uses the base plot route — NOT an `/etu/plot-tcc`; also `POST /calculate`, `POST /evaluate` exist if needed)
- **TMT:** `GET /tmt/facets`, `GET /tmt/frames`, `GET /tmt/context/{frame_id}`, `GET /tmt/settings/{frame_id}`, `POST /tmt/plot-tcc`
- **EMT:** `GET /emt/facets`, `GET /emt/frames`, `GET /emt/context/{frame_id}`, `GET /emt/settings/{section_id}`, `POST /emt/plot-tcc`

### Scope — OUT (do not do in this dispatch)
- **No interactive what-if / override sliders.** Matching relay's *hosted read surface* is the convergence goal; the breaker analog of relay Phase 4 (interactive trip-envelope preview) is a separate future sub-lane.
- **No backend / route / schema / calc / data changes.** Routes are proven — consume them. (The Decision-012 `tcc.*` schema migration is a separate deliberate track; it repoints route SQL underneath these routes transparently — the frontend talks to `/api/v1/neta/*`, not tables, so it is migration-agnostic. Do not touch it here.)
- **No browser-side curve math.** Render server-returned curve points only (same boundary verified for relay Phase 4 — the browser plots, the server computes).
- The apparatus-anchored `GET /apparatus/{apparatus_id}/resources` (point-of-need retrieval) is a richer follow-on — **note it for a future dispatch, not in scope here.**

## Verify
- `pnpm -C apps/operations-web tsc --noEmit` clean (or repo's typecheck script) + `next build` succeeds.
- The explorer renders ETU / TMT / EMT catalog data from the live routes (against `control.apexpowerops.com`, or local control-plane for dev) — **zero error banners** on the happy path.
- A static trip curve renders for at least one section per family from the server plot route.
- A Playwright smoke mirroring the relay smoke (cards render, no error banner) — extend the existing operations-web Playwright surface if present.
- Provide a screenshot or Playwright artifact showing the hosted breaker explorer rendering real catalog + a curve.

## Guardrails
- **Frontend-only + read-only.** No backend, route, schema, calc-engine, data, or migration changes.
- Reuse the relay pattern faithfully (same fetch/error/empty-state shape) — convergence means *parity of surface*, not a bespoke redesign.
- Honor the existing `503` (relay work-schema) / `500` guards — if any breaker route returns non-200, surface it honestly, don't mask.
- Do NOT read `.env*` / credential files for contents. Scoped `git add` (never `-A`).

## Closeout
Record: surfaces added (files), routes consumed per family, typecheck/build results, Playwright/screenshot evidence, and any route that returned a non-200 (so we know the hosted breaker surface's real coverage). Then `git mv claimed/ → done/`, commit, push, return to Desktop. This delivers **Breaker↔Relay Parity step 3** — breaker converged onto operations.apex, both lanes now hosted-visible with parity of surface.
