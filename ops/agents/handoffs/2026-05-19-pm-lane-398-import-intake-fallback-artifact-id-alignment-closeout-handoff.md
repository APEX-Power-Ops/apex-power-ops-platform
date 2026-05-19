# PM Lane 398 - Import-Intake Fallback Artifact-ID Alignment Closeout Handoff

## Outcome

Executed PM Lane 398 as a bounded import-intake naming-coherence tranche.

Selected outcome: `PM_IMPORT_INTAKE_FALLBACK_ARTIFACT_ID_ALIGNMENT`

The canonical `/pm-review/import-intake` route was already using `import-intake` in route naming and local storage keys, but browser-local export filename helpers still fell back to the historical identifier `project-miner-intake`. This lane normalizes that fallback so local artifacts no longer leak stale lane vocabulary when `candidate_id` is absent.

## Change Surface

Updated file:

- `apps/operations-web/app/pm-review/import-intake/page.tsx`

Implemented change:

- Added one canonical fallback constant: `import-intake`
- Added one shared `candidateFileStem(...)` helper
- Routed all browser-local export filename helpers through that helper

## Validation

Focused local validation passed:

```text
get_errors on apps/operations-web/app/pm-review/import-intake/page.tsx
No new change-specific diagnostics; existing inline-style warnings remain pre-existing in that file.

corepack pnpm --dir apps/operations-web typecheck
PASS
```

Focused source confirmation:

```text
apps/operations-web/app/pm-review/import-intake/page.tsx
No remaining source matches for: project-miner-intake
```

## Boundary

- No route change.
- No export-button label or handler change.
- No browser storage key change.
- No hosted/public-proof claim.
- No approval, import, assignment, schedule/status, field, production, customer, or finance authority widening.
- No backend mutation or autonomous AI business-state mutation.

## Next Branch Set

The import-intake artifact naming surface is now locally coherent with the governed route vocabulary. The next bounded PM move should target a real PM behavior, hosted proof gap, or authority surface rather than more stale fallback naming inside this route.