# TCC Relay Tranche 5 Browser And Coordination Adoption Execution Handoff

Date: 2026-04-30
Status: Pre-execution boundary for the next relay slice
Authority: `Platform-Authority/TCC-RELAY-TRANCHE-5-BROWSER-AND-COORDINATION-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
Upstream authority: `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
Prior tranche closure: `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-4-read-only-control-plane-api-adoption-execution-completion-handoff.md`
External reviewed packet: `D:\apex-power-ops-platform\spec\relay-family-scoping\HANDOFF_TO_COPILOT.md`

---

## Objective

Carry the relay lane from bounded control-plane read-only adoption into the
smallest approved browser consumer slice.

Only `apps/operations-web` read-only relay browse, context, settings, preview,
and user-facing warning / provenance disclosures are in scope.

---

## Mandatory Read Set

Read these surfaces before touching the browser lane:

1. `Platform-Authority/TCC-RELAY-RUNTIME-ADOPTION-SCOPING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-EXECUTION-TRANCHE-PLANNING-PACKET-2026-04-30.md`
3. `Platform-Authority/TCC-RELAY-TRANCHE-5-BROWSER-AND-COORDINATION-ADOPTION-EXECUTION-PACKET-2026-04-30.md`
4. `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-4-read-only-control-plane-api-adoption-execution-completion-handoff.md`
5. `apex-power-ops-platform/apps/operations-web/README.md`
6. `apex-power-ops-platform/apps/operations-web/app/page.tsx`
7. `apex-power-ops-platform/apps/operations-web/app/apparatus-resource-explorer.tsx`
8. `apex-power-ops-platform/apps/operations-web/lib/apparatus-resources.ts`
9. `apex-power-ops-platform/apps/operations-web/tests/browser-shell.smoke.spec.ts`

---

## Canonical Scope Boundary

The next implementation move is limited to:

1. one bounded relay browser component under `apps/operations-web/app/`,
2. one bounded relay browser API-consumption helper under `apps/operations-web/lib/`,
3. focused browser validation under `apps/operations-web/tests/`.

And to read-only browser consumers only.

---

## Explicitly Blocked In This Slice

Do not open:

1. browser-side direct database access,
2. write paths,
3. optimizer or recommendation workflows,
4. browser-side relay math that bypasses the shared calc package and relay API,
5. display-name-only curve identity,
6. silent removal of provenance or unsupported warnings.

---

## Expected Outcome From This Handoff

If followed correctly, the next repo-native move will produce one bounded
relay browser consumer slice inside `apps/operations-web`, consuming the now-live
read-only relay API for search, context, settings, and preview, surfacing
provenance and storage-kind identity, preserving explicit unsupported-family
behavior, and leaving write surfaces closed.