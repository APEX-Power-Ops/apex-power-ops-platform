# Relay Phase 4 Read-Only Preview Closeout

Date: 2026-05-30
Dispatch: `2026-05-30-cc-relay-phase-4-readonly-preview`
Status: Complete

## Scope

Implemented the Phase 4 read-only relay what-if preview against the existing governed relay surfaces.

The slice stayed inside:

1. existing `POST /api/v1/neta/relay/plot-tcc`,
2. existing six supported relay calc families,
3. operations-web relay compare/browser surface,
4. DB-less browser proof for the interactive loop.

No persistence, saved comparison, note, workspace, mutation-seam path, schema change, local PG dependency, model-code 7-9 admission, or database write was added.

## R1 Route Decision

Decision: extended the existing `POST /api/v1/neta/relay/plot-tcc` route.

No new route was required.

Added an optional `candidate_overrides` request object:

1. `pickup_multiplier`,
2. `time_dial`,
3. `voltage_threshold_multiplier`.

All candidate fields are positive-only and ephemeral. Invalid candidate input returns validation or bounded route errors instead of a 500.

The route still selects a stored governed relay preview option, evaluates through the shared calc package, and returns one preview curve. Candidate pickup and voltage-threshold multipliers normalize the evaluated current multiples server-side while preserving the requested multiples for display. Analytical candidate time-dial values are evaluated through the existing family calculators. TCP stored-point rows reject mismatched candidate time-dial values cleanly because those rows are bound to stored time-dial selections.

Route test evidence:

```text
source /home/olares/apex-secrets/olares/ai-live-dsn.env && cd apps/control-plane-api && PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_routes.py -q
7 passed, 1 warning in 0.99s
```

## R2 Browser Wiring

Added the operations-web interactive read-only preview surface:

1. candidate sliders for pickup multiplier, time dial, and voltage threshold,
2. debounced call back to `POST /relay/plot-tcc` with `candidate_overrides`,
3. baseline vs what-if SVG overlay,
4. click-to-drop fault-current markers,
5. TCP time-dial slider disabled because TCP point rows are stored time-dial selections.

The browser does not calculate relay trip times. It only renders the server-returned baseline and candidate curves.

## R3 Proof And No-Regression Evidence

Validation run:

```text
cd packages/calc-engine && PYTHONPATH=src ../../apps/control-plane-api/.venv/bin/python -m pytest tests/test_relay_golden_fixtures.py -q
19 passed
```

```text
apps/operations-web/node_modules/.bin/tsc --noEmit --project apps/operations-web/tsconfig.json
PASS
```

```text
cd apps/operations-web && node_modules/.bin/next build
PASS
```

```text
cd apps/operations-web && CI=1 node_modules/.bin/playwright test tests/browser-shell.relay.smoke.spec.ts
1 passed
```

The browser proof validates explicit relay selection, baseline route calls, slider-driven candidate recalculation, overlay rendering, marker creation/clear, and the existing compare-state reset behavior.

Live read-only relay integration was attempted with the governed host DSN sourced from `/home/olares/apex-secrets/olares/ai-live-dsn.env` without printing the secret:

```text
source /home/olares/apex-secrets/olares/ai-live-dsn.env && cd apps/control-plane-api && PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_live_integration.py -q -rs
1 skipped, 1 warning in 1.09s
SKIPPED: Relay work-schema tables are not present in the active database
```

Playwright browser proof initially found the Chromium runtime missing from the host cache. Installed only the Playwright Chromium runtime into `/home/olares/.cache/ms-playwright/`, then reran the targeted browser smoke successfully. No package, lockfile, or repo dependency mutation was needed for that cache install.

`git diff --check` passed for the bounded touched path set.

## Boundary Confirmation

Read-only / no-persistence boundary held:

1. no DB writes,
2. no mutation-seam path,
3. no saved comparison or workspace state,
4. no schema migration,
5. no new route,
6. no browser-side relay trip-time math,
7. no model-code 7-9 admission.

Unrelated residue remained excluded from the packet scope, including the pre-existing `pnpm-lock.yaml` modification, `output/`, and canary actual artifacts.
