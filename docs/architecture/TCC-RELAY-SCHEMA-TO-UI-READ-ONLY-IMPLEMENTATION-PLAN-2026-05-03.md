# TCC Relay Schema-To-UI Read-Only Implementation Plan

Date: 2026-05-03
Status: Design-only implementation plan
Scope: Translate the already-landed relay schema substrate and read-only relay API into the next bounded UI-development sequence without opening writes

## Purpose

The relay schema substrate already exists in the database.

The read-only control-plane relay routes already exist.

The first bounded browser compare slice is already closed PASS.

What is still useful now is a concrete implementation plan for how to continue turning the relay schema into operator-facing UI value without violating the current relay governance boundary.

This document exists to fix that next read-only implementation sequence.

This document does not:

1. open any relay write workflow,
2. authorize any schema migration,
3. authorize browser-direct database access,
4. widen the browser into browser-side relay evaluation,
5. replace the closed Phase 3 decision memo.

## Governing Inputs

This plan is grounded in:

1. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-completion-handoff.md`
3. `apex-power-ops-platform/docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
4. `apex-power-ops-platform/docs/architecture/TCC-RELAY-PHASE-3-WRITE-WORKFLOW-DESIGN-DECISION-MEMO-2026-05-03.md`
5. `apex-power-ops-platform/infra/database/migrations/work/010_tcc_relay_tables.sql`
6. `apex-power-ops-platform/apps/operations-web/lib/relay-resources.ts`
7. `apex-power-ops-platform/apps/operations-web/app/relay-resource-explorer.tsx`
8. `apex-power-ops-platform/apps/control-plane-api/tests/test_neta_relay_routes.py`

If any recommendation here conflicts with the root `Platform-Authority` packet stack or the closed Phase 3 decision memo, those governing surfaces win.

## Current Floor

The current relay floor is already stronger than a design-only mock surface.

The following are already true:

1. source-faithful relay substrate tables exist under `work.tcc_relay*`,
2. read-only relay route contracts exist for section search, context, settings, and TCC preview,
3. the browser already consumes those routes through `apps/operations-web/lib/relay-resources.ts`,
4. the first compare-oriented UI slice is already live and promoted-host validated,
5. no relay write workflow is open now,
6. any future relay write must route through `apps/mutation-seam/`, not through the browser lane.

That means the next useful UI work is not schema creation.

It is read-only schema adoption through better browser composition.

## Relay Data Model That The UI Should Treat As Stable Inputs

The browser should not think in terms of raw tables.

It should think in terms of bounded read models derived from the relay substrate.

The stable read-model groups are:

1. relay identity:
   `tcc_relays`, `tcc_relay_devices`, `tcc_relay_td_sections`
2. line and section context:
   `tcc_relay_line_sections`
3. settings ranges and discrete values:
   `tcc_relay_ranges`, `tcc_relay_discrete_values`
4. family-specific preview parents and rows:
   the typed family parent and child tables admitted by Tranche 1
5. plotted preview points:
   `tcc_relay_curve_points_tcp` or family constants resolved through governed backend behavior

UI implementation should stay coupled to those read-model groups, not to raw table enumeration.

## Recommended Read-Only UI Sequence

The next bounded read-only implementation sequence should be:

### 1. Freeze The Browser-Owned Relay Contract

Treat the current browser seam in `apps/operations-web/lib/relay-resources.ts` as the only admissible browser contract.

Implementation rule:

1. every new relay UI surface should consume typed resources from this seam,
2. no component should fetch relay data from ad hoc URLs,
3. no component should know SQL table names,
4. no browser code should infer unsupported behavior by reimplementing backend logic.

Immediate outcome:

1. UI work stays swappable even if the control-plane read model evolves,
2. schema adoption happens through typed resources rather than direct substrate knowledge.

### 2. Add A Relay Detail Surface Before Adding More Compare Complexity

The next UI slice should likely be a single-selection detail surface, not a wider compare workspace.

Why this comes next:

1. the current compare slice already proves two-sided selection,
2. the UI still benefits from a clearer one-side drill-in screen that exposes the relay schema more fully,
3. detail-first screens let operators understand a relay TD-section before comparing it.

Recommended detail sections:

1. identity and provenance,
2. resolved line sections,
3. range and discrete setting inventory,
4. preview-option inventory,
5. supported or unsupported posture with explicit reason strings.

Implementation home:

1. `apps/operations-web/app/relay-resource-explorer.tsx`, or
2. a closely adjacent browser component under the same `apps/operations-web/app/` lane if the current file becomes too large.

### 3. Split The Current Explorer Into Read-Model Components

Before widening behavior further, split the relay explorer UI into browser-local components aligned to the read-model groups.

Suggested component boundaries:

1. relay search and selection shell,
2. per-side identity and provenance card,
3. line-section list,
4. ranges and discrete-values card,
5. preview-options card,
6. plotted-preview card,
7. warning and unsupported-state banner block.

Why:

1. the current single file already carries multiple distinct views,
2. future read-only widening will become brittle if every next slice edits one monolithic component,
3. this refactor is still browser-local and does not require backend widening.

### 4. Prefer Backend-Composed Read Models Over Browser Reconstruction

If the next UI slice needs more shape than the current routes provide, extend the control-plane read-only routes instead of teaching the browser to reconstruct table relationships.

Backend rule:

1. compose relay responses in the control-plane API,
2. keep them read-only,
3. keep source identity explicit,
4. do not add write-capable routes,
5. do not widen schema only to satisfy browser convenience.

Good future read-only additions, if needed:

1. a detail bundle endpoint that returns one TD-section's identity, line sections, ranges, discrete values, and preview inventory together,
2. a compare-summary endpoint that returns two already-resolved sides in one response without collapsing identity,
3. a browse endpoint with stronger filter facets over the existing search surface.

Bad additions:

1. raw table passthrough endpoints,
2. browser-only evaluator shortcuts,
3. endpoints that merge left and right selections into one recommended result.

### 5. Expand Compare Only Along The Already-Admitted Read-Only Axes

If compare is widened after the detail slice, the next read-only additions should stay inside the already-admitted concept memo.

Admissible next compare moves:

1. stronger per-side range comparison,
2. stronger per-side preview-option selection,
3. clearer differences between supported and unsupported families,
4. better explicit empty-state behavior when one side lacks preview data,
5. URL-safe deep links for read-only compare state.

Still blocked:

1. saved compare pairs,
2. study workspaces,
3. operator-authored notes,
4. approval surfaces,
5. anything that persists relay operator state on the server.

### 6. Keep Provenance And Warning Disclosure As First-Class UI Elements

Every future relay UI slice should explicitly surface:

1. `td_section_source_id`,
2. `relay_device_source_id`,
3. `family_name`,
4. `storage_kind`,
5. supported or unsupported status,
6. any governed `unsupported_reason`,
7. any preview-surface qualification such as first-published-option or no-preview-available disclosures.

This is not secondary polish.

It is part of the truth contract.

### 7. Add Focused UI Validation Per Slice

Each read-only UI slice should add proof in this order:

1. focused route-contract proof if control-plane responses changed,
2. focused browser smoke additions for the new read-only behavior,
3. `corepack pnpm --filter @apex/operations-web typecheck`,
4. `corepack pnpm --filter @apex/operations-web build`,
5. promoted-host smoke rerun if the slice changes visible browser behavior.

That keeps relay UI widening bounded to executable proof rather than screenshot confidence.

## Concrete Build Order

If this plan is executed as implementation work later, the smallest practical build order is:

1. browser-local refactor of `relay-resource-explorer.tsx` into smaller read-model-aligned components,
2. add a single-selection detail mode that exposes ranges, discrete values, and preview inventory more fully,
3. extend browser smoke coverage for detail-mode disclosures,
4. only then decide whether any additional control-plane read model is truly needed,
5. if needed, add one bounded read-only detail bundle route and corresponding tests,
6. widen compare only after the detail path is clear and still truthful.

## Explicitly Out Of Scope

This plan does not authorize:

1. any relay write table,
2. any saved-comparison storage,
3. any mutation route in `apps/control-plane-api/`,
4. any browser-direct database access,
5. any relay evaluator logic in the browser,
6. any recommendation, ranking, or optimizer layer,
7. any site-specific narrative or training overlay,
8. any widening of unsupported families into fake supported behavior.

If later work needs persisted relay state, it must reopen through the separately governed `apps/mutation-seam/` path fixed by the closed Phase 3 decision memo.

## Bottom Line

The relay schema-to-UI next step is not new schema.

It is disciplined read-only adoption of the existing relay substrate through typed browser seams, control-plane-composed read models, detail-first UI slices, and proof-backed compare widening.

The clean next executable UI move is:

1. refactor the current relay explorer into read-model-aligned components,
2. add a stronger single-selection detail surface,
3. widen compare only after that detail surface is proven.