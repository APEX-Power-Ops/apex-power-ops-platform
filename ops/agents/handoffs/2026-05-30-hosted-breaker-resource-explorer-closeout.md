# Hosted Breaker Resource Explorer Closeout

Dispatch: `2026-05-30-cc-hosted-breaker-resource-explorer`
Executor: Codex
Date: 2026-05-31
Status: Repo implementation complete and pushed; production alias verification is still waiting on a fresh `operations.apexpowerops.com` deployment.

## Claim

- Claim commit pushed: `ee266c1f` (`claim: 2026-05-30-cc-hosted-breaker-resource-explorer by codex`)
- Predecessor was already done: `2026-05-30-cc-ltpu-stpu-tolerance-characterization`
- No `.env*` or credential contents were read.

## Implementation

Implementation commit pushed: `b665258f` (`feat: add operations breaker resource explorer`)

Added:

- `apps/operations-web/lib/breaker-resources.ts`
- `apps/operations-web/app/breaker-resource-explorer.tsx`
- `apps/operations-web/app/breaker-selection-panels.tsx`
- `apps/operations-web/tests/browser-shell.breaker.smoke.spec.ts`

Updated:

- `apps/operations-web/app/page.tsx`
- `apps/operations-web/app/globals.css`

The explorer is mounted on the operations-web home page beside the relay explorer. It provides an ETU/TMT/EMT family selector, bounded browse results, explicit selected-row loading, context/settings panels, and a static SVG plot that renders only server-returned curve points. It does not add what-if sliders, browser-side curve math, backend routes, schema changes, data changes, or writes.

## Routes Consumed

Catalog:

- `GET /api/v1/neta/catalog/status`

ETU:

- `GET /api/v1/neta/etu/search`
- `GET /api/v1/neta/etu/breaker-cascade`
- `GET /api/v1/neta/context/{sensor_id}`
- `GET /api/v1/neta/settings/{sensor_id}`
- `POST /api/v1/neta/plot-tcc`

TMT:

- `GET /api/v1/neta/tmt/facets`
- `GET /api/v1/neta/tmt/frames`
- `GET /api/v1/neta/tmt/context/{frame_id}`
- `GET /api/v1/neta/tmt/settings/{frame_id}`
- `POST /api/v1/neta/tmt/plot-tcc`

EMT:

- `GET /api/v1/neta/emt/facets`
- `GET /api/v1/neta/emt/frames`
- `GET /api/v1/neta/emt/context/{frame_id}`
- `GET /api/v1/neta/emt/settings/{section_id}`
- `POST /api/v1/neta/emt/plot-tcc`

Non-200 handling is centralized in `BreakerResourcesError`; route `detail`/`error` messages are surfaced directly in the browser lane instead of being masked.

## Live Route Evidence

Read-only sweep against `https://control.apexpowerops.com/api/v1/neta` passed with no route non-200s:

| Family | Live row | Context | Settings / inventory | Plot result |
| --- | --- | --- | --- | --- |
| Catalog | `catalog=live` | `63` manufacturers | `17,831` ETU sensors | n/a |
| ETU | sensor `3629` — `(Generic) / Std / 800 A` | context sensor `3629` | `39` selected setting values, `23` breaker matches | `2` curves, `7` expected markers |
| TMT | frame `8038` — `ABB / Tmax [IEC] / 630.0` | context frame `8038` | `4` trip classes | `1` curve, `28` points |
| EMT | frame `2953` — `Allis-Chalmers / SOC Trip / 250` | context frame `2953`, section `6200`, band `12354` | section/band inventory loaded | `2` curves, `22` total points |

## Validation

- `pnpm -C apps/operations-web typecheck`
  - Result: pass
- `pnpm -C apps/operations-web build`
  - Result: pass
- `pnpm -C apps/operations-web exec playwright test tests/browser-shell.breaker.smoke.spec.ts`
  - Result: `1 passed`
  - Covers ETU, TMT, and EMT browse/load flows, all context/settings routes, all three plot routes, and curve SVG rendering.
- `pnpm -C apps/operations-web exec playwright test tests/browser-shell.relay.smoke.spec.ts`
  - Result: `1 passed`
  - Confirms the adjacent relay explorer was not regressed by the new home-page mount.
- `git diff --check -- apps/operations-web/app/globals.css apps/operations-web/app/page.tsx apps/operations-web/app/breaker-resource-explorer.tsx apps/operations-web/app/breaker-selection-panels.tsx apps/operations-web/lib/breaker-resources.ts apps/operations-web/tests/browser-shell.breaker.smoke.spec.ts`
  - Result: clean

## Hosted Status

The implementation commit was pushed to `main`, but `https://operations.apexpowerops.com` did not show the new breaker heading after a six-attempt poll (`6 x 10s`) on 2026-05-31:

- observed: `hosted_breaker_heading_not_seen`

A local browser attempt against `NEXT_PUBLIC_CONTROL_PLANE_BASE_URL=https://control.apexpowerops.com` also proved why local-live browser proof is not equivalent to production alias proof: public control-plane CORS does not allow `http://127.0.0.1:3032`. The governed browser proof must therefore run from the deployed operations-web origin after the Vercel production alias receives a fresh deployment.

## Boundary

Changed only operations-web frontend/test surfaces and this closeout. No backend, route, schema, calc-engine, data, migration, credential, or package/lockfile changes were made. Existing unrelated local residue (`pnpm-lock.yaml`, `output/`, and canary actual JSON files) was left untouched.
