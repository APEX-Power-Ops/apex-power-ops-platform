# TCC Relay Phase 2 First Compare Slice Implementation — Completion Handoff

Date: 2026-05-03
Status: Slice closed PASS in repo and on promoted host after 2026-05-03 hosted deployment recovery
Authority: governed by the Phase 2 packet stack listed below

## Authority

This closure is governed by:

1. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-SCOPING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-POST-LADDER-PHASE-2-BROWSER-SURFACE-WIDENING-EXECUTION-PACKET-2026-05-01.md`
3. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md`
4. `docs/architecture/TCC-RELAY-EXPLORATORY-COMPARE-CONCEPT-ADOPTION-MEMO-2026-05-03.md`
5. `docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`
6. `ops/agents/handoffs/2026-05-03-tcc-relay-phase-2-first-compare-slice-implementation-handoff.md`

If any summary here conflicts with the root `Platform-Authority` packet stack, the root stack wins.

## Scope Of This Closure

This closure records the first bounded Phase 2 compare-oriented browser slice landing inside the approved `apps/operations-web` file surface, validated locally end-to-end, and then validated again on the promoted host after the hosted deployment recovery completed on 2026-05-03.

This slice does not:

1. add writes,
2. add recommendations,
3. add optimizer or ranking behavior,
4. add browser-side relay evaluator logic,
5. add browser-direct database access,
6. add training, commissioning, or site-specific narrative tabs,
7. widen backend routes or schema,
8. collapse or simplify per-side source identity.

## Files Changed

Edits stayed inside the approved surface:

1. `apps/operations-web/app/relay-resource-explorer.tsx` — re-grouped each per-side selection panel into three explicitly labeled compare views (`Context`, `Settings`, `Preview`) with a `data-relay-compare-view` data attribute on each section, and added neutral fallback banners for empty resolved-line-section and empty preview-option states so unsupported sides still surface read-only structure rather than disappearing.
2. `apps/operations-web/app/globals.css` — added `.relay-compare-section`, `.relay-compare-section-header`, `.relay-compare-section-eyebrow`, `.relay-compare-section-title`, and `.relay-nested-card h5` styles to render the three compare views with consistent visual grouping inside both the primary and compare panels.
3. `apps/operations-web/tests/browser-shell.smoke.spec.ts` — extended the existing relay compare assertions to require that `Context`, `Settings`, and `Preview` sections each render exactly twice (once per side) and that source-faithful per-side identity is observed inside those sections (primary side IEC `constants` + section `Phase OC section` + curve `IEC Very Inverse`; compare side `lrm` + section `Ground OC section` + explicit "no preview curve" disclosure).

The handoff also touched two non-implementation governance files inside the repo, both already part of the open Phase 2 widening work (no implementation impact):

1. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-1-hosted-proof-and-promotion-preflight-handoff.md` (uncommitted Phase 1 closure-state edits already present before this slice)
2. `ops/agents/handoffs/2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md` (uncommitted compare-memo cross-reference already present and preserved by this slice)

`apps/operations-web/app/page.tsx` and `apps/operations-web/lib/relay-resources.ts` were not edited; the existing seam types and homepage composition already covered the slice contract without widening.

## Compare Behaviors Added Or Reinforced

The slice now satisfies the seven compare-behavior requirements end-to-end:

1. **Explicit two-sided TD-section selection** — primary and compare selects each carry an empty placeholder option; the compare select disables the option matching the current primary so two distinct TD-sections are required for compare.
2. **No silent default** — when a search returns more than one candidate, neither select is auto-populated; the panel exposes an inline banner "Select a primary TD-section before the browser treats any relay preview as current." until an explicit choice is made.
3. **Explicit selection gate before fetches** — `handleLoadSelection` refuses to issue context, settings, or preview requests until `primarySectionId` resolves to a real section in the current search response; the smoke proof confirms zero context, settings, or plot requests fire before that gate clears.
4. **Bounded compare for ≤ 2 explicitly selected TD-sections** — the panel cannot enter compare mode without a distinct compare TD-section, and the same TD-section ID cannot occupy both slots simultaneously.
5. **Read-only compare views for context, settings, and preview** — each per-side panel now renders three labeled sub-sections (`Context`, `Settings`, `Preview`) so the compare contract is visually and structurally three-view rather than blended; preview falls back to an explicit "no preview curve was returned" disclosure when no governed plot is published.
6. **Per-side source-faithful identity** — `td_section_source_id`, `relay_device_source_id`, `family_name`, `storage_kind`, `manufacturer_source_id`, and `standard_code` are surfaced inside each side's `Context` view; compare never collapses identity into a merged template.
7. **Unsupported and partially supported sections remain visible with explicit warnings** — unsupported sections remain selectable, and explicit banners surface (a) an "Unsupported sections remain selectable for disclosure-only compare." banner inside both the search card and the panel warning block, (b) the governed `unsupported_reason` strings emitted by the context, settings, and plot routes, and (c) a "first published governed option out of N options" disclosure when multiple preview options exist for a TD-section.

## What Remains Intentionally Deferred

Per the exploratory compare memo's `Defer Later` and `Reject For Current Lane` sections, none of the following landed in this slice:

1. dedicated voltage / frequency / differential / LoE / directional / composite-logic training tabs,
2. tester or commissioning guidance layers,
3. site-specific narrative or workbook companion overlays,
4. browser-side relay evaluator logic, family analytical substitution, or placeholder curve models,
5. recommendation, ranking, optimizer, or auto-selection behavior,
6. backend-route widening, schema widening, or relay-evaluator placement changes,
7. write workflow design.

Compare cardinality remains capped at two explicit TD-sections.

## Validation Results

### 1. Focused browser smoke

```
corepack pnpm exec playwright test tests/browser-shell.smoke.spec.ts
```

Local execution against `next start -p 3030` with a hand-started server (the bundled `webServer` command `pnpm exec next start -p 3030` failed with `'pnpm' is not recognized` inside Playwright's spawned shell on this Windows workstation; reusing an existing local server is allowed by `reuseExistingServer: !process.env.CI`):

```
Running 3 tests using 1 worker
  ok 1 tests\browser-shell.smoke.spec.ts:3:5 › root shell renders and blocks invalid apparatus IDs before backend fetch (517ms)
  ok 2 tests\browser-shell.smoke.spec.ts:69:5 › relay browser requires explicit selection before loading bounded compare details (635ms)
  ok 3 tests\browser-shell.smoke.spec.ts:402:5 › re-homed browser surfaces render their expected headings in a real browser (3.0s)
  3 passed (5.9s)
```

Result: PASS for all three smoke tests, including the new per-side `Context` / `Settings` / `Preview` assertions.

### 2. `corepack pnpm --filter @apex/operations-web typecheck`

```
> tsc --noEmit
```

Exit 0, no diagnostics. Result: PASS.

### 3. `corepack pnpm --filter @apex/operations-web build`

```
✓ Compiled successfully in 2.5s
✓ Generating static pages using 21 workers (3/3) in 1417.7ms
Route (app)
┌ ○ /
└ ○ /_not-found
○ (Static) prerendered as static content
```

Result: PASS.

### 4. `node apps/operations-web/scripts/smoke-promoted-host.mjs --operations-web-base-url https://operations.apexpowerops.com --control-plane-base-url https://control.apexpowerops.com --skip-authenticated-checks`

Final production rerun after the 2026-05-03 hosted deployment recovery:

1. `backend-seam` against `https://control.apexpowerops.com`: `RESULT PASS`.
2. `hosted-routes` against `https://operations.apexpowerops.com`: `SMOKE_SUMMARY failed=0 passed=8`.
3. `browser-smoke` against `https://operations.apexpowerops.com`: all 3 tests passed, including the relay compare assertions that look for `Search Relay Sections` and the labeled `Context`, `Settings`, and `Preview` views.
4. final wrapper summary: `PROMOTED_HOST_SUMMARY failed=0`.

Hosted recovery dependency that cleared the earlier browser-smoke gap:

1. the Vercel project `rootDirectory` was restored to `apex-power-ops-platform/apps/operations-web` relative to the true git root `C:/APEX Platform`,
2. commit `2b572b3` (`fix(operations-web): align Vercel trace root`) moved `outputFileTracingRoot` and `turbopack.root` to the true repo root so Next runtime packaging succeeded on Vercel,
3. the resulting ready deployment was promoted to production as `dpl_2emJi8u3ZuMMKb42hDrWjo9Kxg5R`.

## Disposition

1. Bounded compare-slice implementation: PASS, fully inside the approved file surface.
2. `typecheck`: PASS.
3. `build`: PASS.
4. Focused browser smoke (local): PASS, 3/3.
5. Promoted-host script: PASS end to end against the production alias after the hosted deployment recovery.
6. Cross-reference from the active Phase 2 handoff to the exploratory compare memo: preserved (already present in the uncommitted edits to `2026-04-30-tcc-relay-post-ladder-phase-2-browser-surface-widening-handoff.md` and unchanged by this slice).

Overall: this slice closes PASS in repo and on promoted host. The earlier hosted gap is resolved and no longer blocks Phase 2 closure.

## Recommended Next Actions

1. Treat the first bounded Phase 2 compare slice as fully closed and promoted-host validated.
2. Open the Phase 3 write-workflow design lane in design space only if relay users now need persisted comparisons, saved studies, or authored relay workflow state.
3. Continue to treat the exploratory compare memo's `Defer Later` and `Reject For Current Lane` items as out of scope until a later authority packet explicitly opens them.
