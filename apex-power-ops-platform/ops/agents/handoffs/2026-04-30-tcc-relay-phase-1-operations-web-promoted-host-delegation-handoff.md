# TCC Relay Phase 1 Operations Web Promoted-Host Delegation Handoff

Date: 2026-04-30
Status: Closed PASS; promoted host supplied and validated on 2026-05-01
Parent phase: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
Parent preflight: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`

---

## Objective

Record closure of the missing deployed `operations-web` host target needed for promoted-host relay browser proof.

---

## Verified facts

At the time this handoff was authored:

1. no deployed `operations-web` base URL was present in the active workspace environment,
2. no browser-host deployment target was discoverable in the tracked repo deployment surfaces,
3. the promoted-host smoke machinery already exists in:
   - `apps/operations-web/scripts/smoke-promoted-host.mjs`
   - `.github/workflows/operations-web-hosted-smoke.yml`
4. the repo-owned wrapper has now been hardened for the active Windows workstation path:
   - it can launch browser smoke through `corepack` instead of requiring bare `pnpm` on `PATH`,
   - it supports `--local-control-plane-runtime` for truthful workstation-local validation,
   - it was rerun successfully end to end against a local hosted stack before this handoff remained externally blocked.

---

## Closure outcome

The formerly missing deployment detail is now resolved.

Closed facts:

1. the promoted browser host is `https://operations.apexpowerops.com`,
2. the deployed shell was refreshed by forced Vercel rebuild on 2026-05-01,
3. the live host now serves the landed relay browser slice,
4. the promoted-host wrapper completed with `PROMOTED_HOST_SUMMARY failed=0` against that host and `https://control.apexpowerops.com`.

This handoff is therefore a resolved closure record, not an active request to an external deploy owner.

---

## Executed proof once the host URL was known

The deployed-host proof path is now concrete:

1. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`

Or equivalently through the existing workflow / task surface.

For workstation-local validation only, the wrapper may also be run with:

1. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url http://127.0.0.1:3030 --control-plane-base-url http://127.0.0.1:8010 --skip-authenticated-checks --local-control-plane-runtime`

Success criteria met:

1. backend seam proof green first,
2. hosted route smoke passes,
3. promoted-host Playwright browser smoke passes,
4. the wrapper ends with `PROMOTED_HOST_SUMMARY failed=0`.