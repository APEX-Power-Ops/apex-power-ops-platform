# APEX PM Lane 399 - Import-Intake Fallback Candidate-Label Alignment Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_FALLBACK_CANDIDATE_LABEL_ALIGNMENT`

## Purpose

PM Lane 399 closes the next adjacent naming-coherence gap inside the canonical `/pm-review/import-intake` workbench.

PM Lane 398 already aligned browser-local export filenames to the canonical `import-intake` fallback stem, but several review surfaces and export builders still fell back to stale or generic candidate labels such as `candidate-unknown`, `unknown`, and `current Project Miner candidate` when candidate identity or project name was absent. That left the route with mixed fallback vocabulary even after the filename fix.

## Root Cause

`apps/operations-web/app/pm-review/import-intake/page.tsx` still duplicated fallback candidate labels across dry-run idempotency, PM review panels, and browser-local export builders instead of computing them through one route-owned helper.

Representative stale values before this lane:

```text
candidate-unknown
unknown
current Project Miner candidate
```

## Change Surface

Updated file:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`

Implemented change:

1. Added one shared fallback candidate ID helper for export-facing labels
2. Added one shared fallback context-label helper for PM review surfaces
3. Routed dry-run idempotency, PM daily/field review surfaces, and browser-local export builders through those helpers

Representative effect:

```text
Before: Candidate: unknown
After:  Candidate: import-intake

Before: current Project Miner candidate
After:  current import-intake candidate
```

## Local Validation

Focused validation for the touched route passed:

```text
grep in apps/operations-web/app/pm-review/import-intake/page.tsx
No remaining source matches for:
- candidate-unknown
- unknown candidate fallback lines
- current Project Miner candidate

corepack pnpm --dir apps/operations-web typecheck
PASS
```

## Boundary

This lane does not:

1. change any route path,
2. change any payload schema field or stored candidate identity shape,
3. change any export button label or click behavior,
4. change any browser storage key,
5. claim hosted or public-proof impact,
6. widen approval, import, assignment, schedule/status, field, production, customer, or finance authority,
7. add backend mutation or autonomous AI business-state mutation.

## Result

The canonical import-intake workbench now uses one route-accurate fallback vocabulary for both local artifact filenames and local candidate labels. When candidate identity or project name is missing, browser-local PM review surfaces and export artifacts default to `import-intake` and `current import-intake candidate` instead of leaking stale or generic placeholder text.