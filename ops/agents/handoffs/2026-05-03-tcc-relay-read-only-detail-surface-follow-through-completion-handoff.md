# TCC Relay Read-Only Detail Surface Follow-Through — Completion Handoff

Date: 2026-05-03
Status: Closed PASS in repo; browser-local read-only follow-through
Authority: governed by the existing relay browser and Phase 3 no-write boundary listed below

## Authority

This closure is grounded in:

1. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
3. `apex-power-ops-platform/docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
4. `apex-power-ops-platform/docs/architecture/TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`
5. `apex-power-ops-platform/docs/architecture/TCC-RELAY-SCHEMA-TO-UI-READ-ONLY-IMPLEMENTATION-PLAN-2026-05-03.md`
6. `apex-power-ops-platform/docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`

If any summary here conflicts with the root `Platform-Authority` packet stack or the closed Phase 3 decision memo, those governing surfaces win.

## Scope Of This Closure

This closure records the first follow-through step from the read-only schema-to-UI implementation plan.

The slice stays browser-local inside `apps/operations-web` and consumes only already-published read-only relay route data.

This slice does not:

1. add writes,
2. add any new backend route,
3. add any schema or migration change,
4. add browser-direct database access,
5. add browser-side relay evaluator logic,
6. reopen saved comparisons, workspaces, or authored note workflows,
7. widen unsupported families into fake supported behavior.

## Files Changed

Edits stayed inside the approved browser and architecture surfaces:

1. `apps/operations-web/app/relay-selection-panels.tsx` — new browser-local relay presentation module holding reusable search-card, per-side compare panel, and primary-detail components aligned to the read-only relay data model.
2. `apps/operations-web/app/relay-resource-explorer.tsx` — narrowed into the relay search and orchestration shell that delegates rendering to the new read-only selection components.
3. `apps/operations-web/app/globals.css` — added styles for the primary-detail surface and its grid/header layout while preserving the existing compare layout.
4. `apps/operations-web/tests/browser-shell.smoke.spec.ts` — extended the relay smoke assertions to verify the new primary-detail surface renders governed curve-parent and preview-option inventory.
5. `docs/architecture/TCC-RELAY-SCHEMA-TO-UI-READ-ONLY-IMPLEMENTATION-PLAN-2026-05-03.md` — design-only plan created to fix the next bounded read-only UI sequence that this slice implements.
6. `ops/agents/handoffs/2026-05-03-tcc-relay-read-only-detail-surface-follow-through-completion-handoff.md` — this closure record.

No edits were made to `apps/control-plane-api/`, `packages/calc-engine/`, `apps/mutation-seam/`, or `infra/database/`.

## Behaviors Added Or Reinforced

This slice adds or reinforces the following read-only browser behaviors:

1. the relay explorer is now split into smaller read-model-aligned browser components rather than holding all per-side presentation in one file,
2. the primary TD-section now exposes a stronger detail surface for setting-range inventory, curve-parent inventory, and stored preview-option inventory,
3. the detail surface still relies only on existing governed route responses already returned by the browser seam,
4. compare remains capped at two explicit TD-sections and still preserves per-side source identity,
5. no route widening was required to expose the stronger primary detail view.

## What Remains Deferred

This slice does not reopen any of the items still held outside the current relay lane:

1. saved compare pairs,
2. study workspaces,
3. authored operator notes,
4. approval surfaces,
5. route widening for convenience only,
6. browser-side evaluator substitution,
7. training or site-specific overlay surfaces.

## Validation Results

### 1. `corepack pnpm typecheck`

```
> tsc --noEmit
```

Result: PASS.

### 2. `corepack pnpm build`

```
> next build
✓ Compiled successfully
✓ Finished TypeScript
✓ Generating static pages
```

Result: PASS.

### 3. Focused relay browser smoke

Focused check executed against a manually started local server because Playwright's configured `webServer` wrapper still spawns `pnpm` directly on this Windows workstation.

Executed proof:

1. `corepack pnpm exec next start -p 3030`
2. `OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL=http://127.0.0.1:3030 corepack pnpm exec playwright test tests/browser-shell.smoke.spec.ts --grep "relay browser requires explicit selection before loading bounded compare details"`

Observed result:

```
Running 1 test using 1 worker
  1 passed (2.4s)
```

Result: PASS.

### 4. `git diff --check`

Whitespace and conflict-marker check against the touched relay browser files plus the new plan document.

Result: PASS.

## Disposition

1. browser-local relay refactor: PASS,
2. primary-detail read-only surface: PASS,
3. route and schema boundary preservation: PASS,
4. focused validation: PASS.

Overall: this follow-through step closes PASS in repo and stays fully inside the current relay no-write boundary.

## Recommended Next Actions

1. treat this primary-detail slice as the first implemented step from the read-only schema-to-UI plan,
2. if more relay detail shape is needed, prefer one bounded read-only control-plane detail bundle route rather than browser-side reconstruction,
3. widen compare further only after the detail surface proves sufficient and still truthful,
4. continue to keep all persisted relay state behind the separately governed `apps/mutation-seam/` path rather than the browser lane.