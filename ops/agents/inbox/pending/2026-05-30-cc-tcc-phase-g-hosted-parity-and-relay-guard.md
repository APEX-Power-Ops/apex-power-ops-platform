---
dispatch_id: 2026-05-30-cc-tcc-phase-g-hosted-parity-and-relay-guard
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-30-tcc-phase-g-hosted-parity-and-relay-guard-closeout.md
---

# TCC Phase G — hosted parity (breaker lane) + relay prod-500 guard

**Lane:** TCC Runtime 017 (matrix #83), Phase G (hosted) per the campaign closeout (substrate STATE §61). **Operator authorization: GRANTED 2026-05-30** (G-1 + G-2; G-3 relay-table-load deferred). **Follow the inbox lifecycle:** `git mv pending→claimed` + commit + **push to claim BEFORE executing** (the claim-push is the mutex — the relay dispatch squashed it; restore it here), then `claimed→done` at closeout.

## Context (already true — verified from prod by Desktop)
The Render service `apex-platform-control-plane-api` has `autoDeploy: true` and serves **`https://control.apexpowerops.com`**. The validated TCC build is ALREADY deployed there: `/health/ready` = `ready / database connected / catalog_available`, all TCC routes present in OpenAPI, and `GET /api/v1/neta/catalog/status` = `{"catalog":"live","manufacturer_count":63,"sensor_count":17831}` — byte-identical to Phase F. So this dispatch does NOT deploy anything new for the breaker lane; it **proves hosted parity** and **fixes one prod bug**.

## G-1 — Formalize breaker-lane hosted parity (read-only, against the deployed public host)
Run the Phase-F surfaces against **`--base-url https://control.apexpowerops.com`** instead of localhost (same scripts you used in Phase F):
1. **Deployed baseline smoke:** `apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com` (health / ready / openapi baseline per `apps/control-plane-api/DEPLOYMENT_VALIDATION.md`).
2. **Catalog parity anchor:** confirm `GET /api/v1/neta/catalog/status` on the public host = `live / 63 / 17831`.
3. **Family smoke (breaker):** point the NETA family smoke you used in Phase F (`scripts/smoke_local_neta_family_routes.py`) at `--base-url https://control.apexpowerops.com`; ETU + TMT + EMT known-scenario validation green.
4. **ETU SQL parity:** `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url https://control.apexpowerops.com` — route side = public host; SQL side = governed Supabase via `APEX_OLARES_LIVE_DSN` (`source /home/olares/apex-secrets/olares/ai-live-dsn.env`) → expect **3 pass / 0 warn**.

Record each surface's result. **Read-only throughout** — GET + plot-compute only; no writes to the governed DB. Relay surfaces are expected to fail/skip here — that is G-2's target, not a G-1 failure.

## G-2 — Fix the relay prod 500 (guard → 503)
`GET https://control.apexpowerops.com/api/v1/neta/relay/sections` currently returns **`Internal Server Error` (500)** because the relay work-schema tables are absent from the governed DB (the same gap that made the local relay live-integration SKIP — locally it skipped gracefully; in prod the route has no guard, so it 500s).
- **Guard the relay routes** (`/relay/{sections,context,settings,plot-tcc}` in `apps/control-plane-api/services/neta/router.py`) so that when the relay work-schema tables are absent they return a clean **HTTP 503** with a clear detail (e.g. `relay catalog unavailable: work-schema tables not present`) instead of a 500. **Reuse the same table-presence detection the relay live-integration test uses for its skip** — do not invent a new probe.
- **Do NOT load relay data** — that is the deferred G-3. This is purely graceful degradation: absent → honest 503.
- **Tests:** add/extend route tests so the relay routes return 503 (not 500) when the work-schema is absent; existing relay route tests (mocked) + the golden families stay green. **Leave the breaker routes untouched.**
- **Verify on prod:** commit + push (autoDeploy redeploys). After Render propagation (~2–3 min, or trigger the `deployed-control-plane-smoke` workflow), confirm `GET /api/v1/neta/relay/sections` on the public host now returns **503** (not 500).

## Guardrails
- **Read-only** against the governed Supabase (G-1 probes + the G-2 guard add NO writes). DSN out-of-band; never printed/committed; watch the stale-`.env`-shadow trap.
- No breaker-route changes; no auth changes; no relay-data load; no new route. **Scoped `git add`** (never `-A`). Exclude residue (`.vscode/tasks.json`, `output/`, `pnpm-lock.yaml`).
- If the relay table-presence detection isn't cleanly reusable from the test helper, **STOP and surface to Desktop** before widening scope.

## Closeout
Write the closeout to the `closeout:` path. Record: G-1 each surface's result (where parity is confirmed); G-2 the guard + route tests + the **post-deploy prod verification that `/relay/sections` now returns 503, not 500**. Then `git mv claimed/ → done/`, commit, push. Return to Desktop for review → that closes TCC Phase G (breaker hosted + parity-proven; relay honest in prod; relay-hosted-live = the scoped G-3 follow-on).
