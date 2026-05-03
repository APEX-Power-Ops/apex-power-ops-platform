# TCC Relay Post-Ladder Phase 1 Hosted Proof And Promotion — Preflight Handoff

Date: 2026-04-30
Status: Public seam green; promoted-host still pending deployed browser host
Authority: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md`
Prior ladder closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-5-browser-and-coordination-adoption-execution-completion-handoff.md`

---

## Objective

Run the first truthful hosted-proof step for the landed relay stack and capture blockers explicitly instead of assuming promoted-host readiness.

---

## Executed proof

The following public-host command was run from the active repo workspace:

1. `c:/APEX Platform/.venv/Scripts/python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route`

Observed result:

1. `HEALTH_STATUS 200`
2. `DISCOVERY_STATUS 200`
3. `MCP_STATUS 200`
4. `OPENAPI_STATUS 200`
5. `APPARATUS_ROUTE_STATUS 503` with migration-gated handler-owned response
6. `READY_STATUS 200` but payload reported `status: not_ready`, `database: unreachable`, and password authentication failure for the Supabase pooler user
7. overall script result: `RESULT FAIL` because readiness did not report database connected

Hosted rerun on 2026-05-01 confirmed the blocker is still live:

1. the same public-host command was rerun against `https://control.apexpowerops.com`,
2. `HEALTH_STATUS`, `DISCOVERY_STATUS`, `MCP_STATUS`, and `OPENAPI_STATUS` remained green,
3. `APPARATUS_ROUTE_STATUS` remained handler-owned `503`, not framework `404`,
4. `READY_STATUS` remained `200` with payload `status: not_ready`, `database: unreachable`, and password authentication failure for user `postgres`,
5. the failing host remained `aws-0-us-west-2.pooler.supabase.com:5432`,
6. overall result still failed only on readiness.

Hosted rerun later on 2026-05-01 cleared the blocker:

1. the deployed Render runtime on pod `mhr8c` was verified to have `DATABASE_URL` exactly equal to the governed session-pooler credential,
2. a live `psycopg2.connect(os.environ['DATABASE_URL'])` succeeded inside the Render shell,
3. the same public-host smoke command then returned `READY_STATUS 200` with payload `status: ready` and `database: connected`,
4. `APPARATUS_ROUTE_STATUS` returned handler-owned `404` for the governed not-found UUID instead of a framework miss,
5. the overall script result became `RESULT PASS`.

---

## Current blocker state

The public control-plane readiness blocker is closed.

The remaining Phase 1 blocker is:

1. no deployed `operations-web` base URL is present on disk or in the current workspace environment, so promoted-host browser proof cannot be executed yet.

Repo-side proof machinery is no longer the blocker:

1. `apps/operations-web/scripts/smoke-promoted-host.mjs` was updated to tolerate the active Windows workstation path by using `corepack` instead of assuming bare `pnpm`,
2. the same wrapper now supports `--local-control-plane-runtime` so workstation-local hosted validation does not incorrectly demand public-host discovery semantics,
3. a local hosted rerun completed with `PROMOTED_HOST_SUMMARY failed=0` against `http://127.0.0.1:3030` plus `http://127.0.0.1:8010`.

---

## Delegation required

The next truthful delegated actions are:

1. external deploy owner provides the intended promoted `operations-web` base URL, using `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-phase-1-operations-web-promoted-host-delegation-handoff.md`,
2. run the promoted-host browser-plus-seam smoke against the provided host.

---

## Explicit no-go during blockage

Do not claim full promoted-host relay proof is green.

Do not widen browser or workflow phases as a substitute for hosted-proof closure.

---

## Expected next move from this handoff

Now that the public seam gate is green, the next truthful rerun is:

1. `apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url <real-host> --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`

Until then, Phase 1 remains partially complete with the control-plane seam proven green and the promoted browser host still pending.