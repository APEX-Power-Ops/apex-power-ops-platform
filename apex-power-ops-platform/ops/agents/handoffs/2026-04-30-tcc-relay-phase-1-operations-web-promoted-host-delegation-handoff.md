# TCC Relay Phase 1 Operations Web Promoted-Host Delegation Handoff

Date: 2026-04-30
Status: Delegated external deployment detail required
Parent phase: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
Parent preflight: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`

---

## Objective

Provide the missing deployed `operations-web` host target required to execute promoted-host relay browser proof.

---

## Verified facts

At the time of this handoff:

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

## What is needed from the external deploy owner

Provide the actual promoted `operations-web` base URL intended for hosted validation.

Examples of the required shape:

1. `https://<real-operations-web-host>`

This handoff does not assume provider choice.

---

## Required rerun once the host URL is known

After the deploy owner provides the real browser host URL, rerun:

1. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url <real-host> --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`

Or equivalently through the existing workflow / task surface.

For workstation-local validation only, the wrapper may also be run with:

1. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url http://127.0.0.1:3030 --control-plane-base-url http://127.0.0.1:8010 --skip-authenticated-checks --local-control-plane-runtime`

Success criteria:

1. backend seam proof is green first,
2. hosted route smoke passes,
3. promoted-host Playwright browser smoke passes,
4. the wrapper ends with `PROMOTED_HOST_SUMMARY failed=0`.