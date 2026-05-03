# TCC Relay Post-Ladder Phase 2 Browser Surface Widening Handoff

Date: 2026-04-30
Status: Gate open and first bounded compare slice closed PASS in repo; promoted-host browser-smoke rerun remains blocked on a pre-existing hosted-bundle redeploy gap
Authority: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-SCOPING-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md`

Execution packet: `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
Repo closure for the first bounded compare slice: `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`

---

## Objective

Keep the read-only browser-value phase open for governed widening work, but record that the first bounded compare slice has already landed in repo without reopening writes or browser-side relay math.

---

## Correct target-homes for the now-open phase

1. `apps/operations-web/app/`
2. `apps/operations-web/lib/`
3. `apps/operations-web/tests/`

---

## Correct scope for the now-open phase

1. better section selection,
2. bounded read-only compare,
3. stronger provenance and warning disclosure,
4. focused browser proof updates.

---

## Gate resolution

The prior gate is now satisfied by the public-host closure captured in the Phase 1 handoff and the promoted-host proof recorded in `apps/operations-web/DEPLOYMENT_VALIDATION.md`.

This phase remains the active relay lane.

Its first bounded compare slice is now closed PASS in repo and captured in the completion handoff linked above.

The remaining near-term blocker is external to the approved source file surface: the promoted operations-web host still serves a pre-compare-slice bundle and must be redeployed before the promoted-host browser-smoke rerun can pass.

Implementation remains bounded by the existing execution packet:

1. keep changes inside the approved `apps/operations-web` file surface,
2. do not widen backend routes, schema, or relay evaluator placement,
3. validate with focused browser proof updates plus `typecheck`, `build`, and promoted-host rerun against `https://operations.apexpowerops.com`.

---

## Compare concept reference

Use `docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md` as product guidance for the first compare-oriented Phase 2 implementation slice.

That memo does not widen the authority boundary.

It narrows the first adoption slice to:

1. explicit two-sided TD-section selection,
2. bounded read-only compare views for context, settings, and preview,
3. per-side source identity, family, storage-kind, and unsupported-state disclosure,
4. no browser-side evaluator logic, no training tabs, and no site-specific overlay surfaces.

---

## Immediate execution checklist

Use the Phase 2 execution packet as the exact implementation boundary.

Do this next:

1. treat the first compare-oriented implementation slice as already completed in repo per `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`,
2. open `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-operations-web-promoted-host-redeploy-blocker-handoff.md` for the current promoted-host redeploy blocker state,
3. clear the current deployment blocker named there before attempting another forced production redeploy,
4. only after that blocker is cleared and a new deployment succeeds, rerun `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`,
5. confirm the hosted browser-smoke step now sees `Search Relay Sections` and the labeled compare views,
6. keep any further widening bounded to `apps/operations-web/app/relay-resource-explorer.tsx`, `apps/operations-web/app/page.tsx`, `apps/operations-web/app/globals.css`, `apps/operations-web/lib/relay-resources.ts`, and `apps/operations-web/tests/browser-shell.smoke.spec.ts` unless a later packet widens scope,
7. continue to forbid writes, recommendations, optimizer behavior, browser-side relay math, and browser-direct database access.