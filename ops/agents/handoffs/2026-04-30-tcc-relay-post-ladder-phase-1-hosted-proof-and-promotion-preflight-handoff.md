# TCC Relay Post-Ladder Phase 1 Hosted Proof And Promotion — Preflight Handoff

Date: 2026-04-30
Status: Closed PASS on 2026-05-01 public hosts; promoted-host proof green and Phase 2 gate cleared
Authority: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md`
Prior ladder closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-5-browser-and-coordination-adoption-execution-completion-handoff.md`

---

## Objective

Record the truthful Phase 1 closure state for the landed relay stack after public seam proof and promoted-host browser proof both turned green.

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

Promoted-host rerun later on 2026-05-01 closed the remaining browser-host gate:

1. the deployed `operations-web` base URL was established as `https://operations.apexpowerops.com`,
2. a forced Vercel rebuild removed the stale root-shell behavior on that host,
3. the live shell served the landed relay browser slice,
4. the promoted-host wrapper completed with `PROMOTED_HOST_SUMMARY failed=0` against `https://operations.apexpowerops.com` plus `https://control.apexpowerops.com`,
5. Phase 1 closure conditions from the governing packet were fully satisfied.

---

## Current closure state

Phase 1 is closed PASS.

Closed proof now includes:

1. public control-plane readiness green,
2. relay-dependent seam green with handler-owned responses,
3. real promoted-host `operations-web` base URL present at `https://operations.apexpowerops.com`,
4. hosted route smoke and real-browser promoted-host smoke both green for the same deployed target.

Repo-side proof machinery is no longer the blocker:

1. `apps/operations-web/scripts/smoke-promoted-host.mjs` was updated to tolerate the active Windows workstation path by using `corepack` instead of assuming bare `pnpm`,
2. the same wrapper now supports `--local-control-plane-runtime` so workstation-local hosted validation does not incorrectly demand public-host discovery semantics,
3. a local hosted rerun completed with `PROMOTED_HOST_SUMMARY failed=0` against `http://127.0.0.1:3030` plus `http://127.0.0.1:8010`.

---

## Delegation outcome

The earlier external deploy dependency is now resolved:

1. the promoted `operations-web` base URL is known and proven,
2. the delegated blocker handoff is now a closure record rather than an active dependency.

---

## Explicit no-go after closure

Do not reopen Phase 1 merely because future hosted regression reruns may be needed.

Do not treat later browser widening, write design, or deferred enrichment as part of Phase 1 closure.

---

## Expected next move from this handoff

The next truthful relay move is Phase 2 browser surface widening under its already-approved execution packet:

1. keep implementation inside the bounded `apps/operations-web` file surface,
2. keep scope limited to explicit section selection, bounded read-only compare, and stronger provenance and warning disclosure,
3. reuse the public promoted-host proof path as post-edit validation.

Phase 1 no longer blocks Phase 2.