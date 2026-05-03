# TCC Relay Post-Ladder Phase 2 Browser Surface Widening Execution Packet
## Date: 2026-05-01
## Status: Closed PASS after 2026-05-03 promoted-host recovery
## Scope: Record the bounded read-only browser widening slice that executed after Phase 1 proof turned green and fix the exact Phase 2 closure boundary

## 1. Purpose

Phase 2 already had an approved scoping packet.

This packet supplied the required execution artifact by fixing:

1. the exact `apps/operations-web` file surface,
2. the bounded selection and compare contract,
3. the validation and rollback proof.

The packet is no longer planning-only. The slice it governed is now closed PASS in repo and on promoted host.

## 2. Governing Inputs

1. `Platform-Authority/TCC-RELAY-POST-LADDER-FOLLOW-ON-PLANNING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-1-HOSTED-PROOF-AND-PROMOTION-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-SCOPING-PACKET-2026-04-30.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md`
5. `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
6. `apex-power-ops-platform/apps/operations-web/app/relay-resource-explorer.tsx`
7. `apex-power-ops-platform/apps/operations-web/app/page.tsx`
8. `apex-power-ops-platform/apps/operations-web/lib/relay-resources.ts`
9. `apex-power-ops-platform/apps/operations-web/tests/browser-shell.smoke.spec.ts`

## 3. Gate

The Phase 1 hosted-proof gate named by the original packet is now satisfied on public hosts.

Implementation under this packet is closed PASS.

The packet remains the historical execution authority for what Phase 2 was allowed to do; it is no longer the live active lane.

## 4. Exact Target-Homes

When this phase opens, implementation is limited to the following browser-owned files:

1. `apex-power-ops-platform/apps/operations-web/app/relay-resource-explorer.tsx`
2. `apex-power-ops-platform/apps/operations-web/app/page.tsx`
3. `apex-power-ops-platform/apps/operations-web/app/globals.css`
4. `apex-power-ops-platform/apps/operations-web/lib/relay-resources.ts`
5. `apex-power-ops-platform/apps/operations-web/tests/browser-shell.smoke.spec.ts`

Interpretation:

1. keep the widening inside the existing browser lane,
2. do not widen backend routes for this slice,
3. do not introduce browser-side direct database admission,
4. do not move relay evaluator logic into the browser.

## 5. Bounded Selection Contract

The Phase 2 selection slice must remain limited to the following behavior:

1. search results may no longer silently default to the first row when more than one TD-section is returned,
2. the user must explicitly select the active TD-section before context, settings, and preview fetches are treated as the current working relay,
3. the selected relay must remain identified by its source-faithful keys, including `td_section_source_id`, `relay_device_source_id`, `family_name`, and `storage_kind`,
4. unsupported sections must remain visible with explicit warnings instead of being simplified away.

## 6. Bounded Compare Contract

The Phase 2 compare slice must remain limited to the following read-only behavior:

1. compare supports at most two explicitly selected TD-sections at one time,
2. each side must preserve its own source identity, family, storage kind, and unsupported state,
3. compare may only render independent read-only context, settings, and preview results already available from the governed relay API,
4. compare must not manufacture a merged curve identity, recommendation, ranking, or optimization layer,
5. unsupported or partially supported selections must remain visible with their published warnings and reasons.

## 7. Explicitly Blocked

This packet remains NO-GO for:

1. saved-study or write workflows,
2. browser-side direct database access,
3. browser-side evaluator logic or analytical substitution,
4. any new control-plane route or schema widening added only to serve the browser slice,
5. recommendation, optimization, or auto-selection behavior that hides source identity.

## 8. Validation Requirements

Completed proof under this packet:

1. focused browser smoke updates in `apps/operations-web/tests/browser-shell.smoke.spec.ts` covering explicit section selection and bounded compare disclosure,
2. `corepack pnpm --filter @apex/operations-web typecheck`,
3. `corepack pnpm --filter @apex/operations-web build`,
4. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`, ending with `PROMOTED_HOST_SUMMARY failed=0` after the hosted recovery on 2026-05-03.

## 9. Rollback Requirements

Rollback for this phase is browser-local only.

1. revert the bounded `apps/operations-web` slice if the compare or selection UX proves misleading,
2. do not roll back shared calc, relay API, or schema work merely because this browser widening slice changes,
3. preserve explicit unsupported-state disclosure during rollback rather than hiding the affected relay paths.

## 10. Bottom Line

This packet is now closed PASS.

The correct next relay move is no longer more Phase 2 implementation. The next truthful move is Phase 3 write-workflow design authoring under a separate packet.