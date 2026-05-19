# PM Lane 399 - Import-Intake Fallback Candidate-Label Alignment Closeout Handoff

## Outcome

Executed PM Lane 399 as a bounded import-intake fallback-label coherence tranche.

Selected outcome: `PM_IMPORT_INTAKE_FALLBACK_CANDIDATE_LABEL_ALIGNMENT`

The canonical `/pm-review/import-intake` route already had Lane 398 fallback filename alignment, but review surfaces and export builders still leaked `candidate-unknown`, `unknown`, and `current Project Miner candidate` when candidate identity or project name was absent. This lane normalizes those fallback labels through shared route helpers.

## Change Surface

Updated file:

- `apps/operations-web/app/pm-review/import-intake/page.tsx`

Implemented change:

- Added one shared fallback candidate ID helper for export-facing labels
- Added one shared fallback context-label helper for PM review surfaces
- Routed dry-run idempotency, PM review surfaces, and browser-local export builders through those helpers

## Validation

Focused local validation passed:

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

- No route change.
- No payload-schema change.
- No export-button label or handler change.
- No browser storage key change.
- No hosted/public-proof claim.
- No approval, import, assignment, schedule/status, field, production, customer, or finance authority widening.
- No backend mutation or autonomous AI business-state mutation.

## Next Branch Set

The import-intake route now has coherent fallback naming for both local artifact filenames and local candidate/context labels. The next bounded PM move should target a real PM behavior, proof surface, or authority surface rather than more fallback text cleanup inside this route.