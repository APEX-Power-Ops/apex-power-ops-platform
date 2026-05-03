# TCC Relay Phase 2 First Compare Slice Implementation Handoff

Date: 2026-05-03
Status: Closed PASS in repo; promoted-host browser-smoke rerun remains externally blocked on redeploy of the hosted operations-web bundle
Execution instance: Claude Code
Scope: implement the first bounded Phase 2 compare-oriented browser slice in `apps/operations-web` using the exploratory compare memo as product guidance without widening the existing relay authority boundary

Completion handoff: `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`

## Authority

This handoff is governed by:

1. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-SCOPING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
3. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
4. `docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
5. `docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`

If any summary in this handoff conflicts with the root `Platform-Authority` packet stack, the root packet stack wins.

## Objective

Execute the memo's recommended next implementation slice inside the already-approved Phase 2 browser widening lane.

This is a bounded read-only compare slice.

It does not reopen writes, browser-side relay math, optimizer behavior, or schema widening.

## Execution Order

This execution order is now completed in repo. The resulting closure is recorded in the completion handoff above.

The remaining next action is external to this implementation handoff: redeploy the promoted operations-web host and rerun the promoted-host smoke script.

The completed implementation order was:

1. preserve the newly added cross-reference from the active Phase 2 handoff to the exploratory compare memo,
2. implement the first compare-oriented browser slice inside the approved `apps/operations-web` surface,
3. validate with focused browser proof, `typecheck`, `build`, and promoted-host rerun,
4. write a dated completion or blocker handoff.

## Approved File Surface

Keep edits bounded to:

1. `apps/operations-web/app/relay-resource-explorer.tsx`
2. `apps/operations-web/app/page.tsx`
3. `apps/operations-web/app/globals.css`
4. `apps/operations-web/lib/relay-resources.ts`
5. `apps/operations-web/tests/browser-shell.smoke.spec.ts`

Do not widen beyond that file set unless the governing Phase 2 execution packet is explicitly amended.

## Required Implementation Slice

Implement the memo's first adoption slice exactly this way:

1. add explicit two-sided TD-section selection to the existing relay explorer,
2. stop silently defaulting to the first TD-section when more than one candidate exists,
3. require explicit selection before treating context, settings, or preview fetches as the current working relay,
4. allow bounded compare for at most two explicitly selected TD-sections,
5. add read-only compare views for context, settings, and preview,
6. preserve source-faithful identity on both sides through `td_section_source_id`, `relay_device_source_id`, `family_name`, and `storage_kind`,
7. keep unsupported or partially supported sections visible with explicit warnings and reasons on each side.

## Explicit No-Go Items

The following remain out of scope for this slice:

1. no writes,
2. no recommendations,
3. no optimizer or ranking behavior,
4. no browser-side relay evaluator logic,
5. no browser-direct database access,
6. no training or commissioning tabs,
7. no site-specific narrative overlays,
8. no identity collapse or hidden template substitution,
9. no widening of backend routes or schema.

## Validation Requirements

These validations were completed for the repo closure; see the completion handoff for exact results. The promoted-host browser-smoke rerun remains blocked until the host is redeployed from current source.

The required validation set for this handoff was:

1. focused browser smoke update in `apps/operations-web/tests/browser-shell.smoke.spec.ts`,
2. `corepack pnpm --filter @apex/operations-web typecheck`,
3. `corepack pnpm --filter @apex/operations-web build`,
4. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`.

## Required Output

Implementation and validation are complete in repo. The dated closure handoff written for this execution is:

`ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`

That closure records:

1. exact files changed,
2. exact compare behaviors added,
3. any remaining unsupported or deferred pieces left out intentionally,
4. validation results,
5. whether the first compare slice closed PASS or remains blocked.

## Copy-Paste Prompt For Claude Code

```text
Act as the implementation owner for the active TCC relay Phase 2 browser widening lane.

Read these first:
- C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md
- C:/APEX Platform/apex-power-ops-platform/docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md
- C:/APEX Platform/apex-power-ops-platform/docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md

Execute the first bounded compare-oriented implementation slice now.

Constraints:
1. Keep edits inside:
   - C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/relay-resource-explorer.tsx
   - C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/page.tsx
   - C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/globals.css
   - C:/APEX Platform/apex-power-ops-platform/apps/operations-web/lib/relay-resources.ts
   - C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.smoke.spec.ts
2. Add explicit two-sided TD-section selection.
3. Stop silently defaulting when more than one TD-section candidate exists.
4. Require explicit selection before context, settings, or preview fetches become the working relay.
5. Allow bounded compare for at most two explicitly selected TD-sections.
6. Add read-only compare views for context, settings, and preview.
7. Preserve per-side source identity through `td_section_source_id`, `relay_device_source_id`, `family_name`, and `storage_kind`.
8. Keep unsupported or partially supported sections visible with explicit per-side warnings.

Do not do any of the following:
1. no writes
2. no recommendations
3. no optimizer or ranking behavior
4. no browser-side relay evaluator logic
5. no browser-direct database access
6. no training tabs
7. no site-specific overlays
8. no backend or schema widening

Validation required after the implementation edit:
1. update and run the focused browser smoke slice
2. `corepack pnpm --filter @apex/operations-web typecheck`
3. `corepack pnpm --filter @apex/operations-web build`
4. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`

After implementation and validation, write a dated completion or blocker handoff under:
- C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/

Summarize:
1. exact files changed
2. compare behaviors added
3. what remains intentionally deferred
4. validation results
5. PASS or blocked disposition
```