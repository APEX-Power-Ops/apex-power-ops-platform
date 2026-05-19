# APEX PM Lane 398 - Import-Intake Fallback Artifact-ID Alignment Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_FALLBACK_ARTIFACT_ID_ALIGNMENT`

## Purpose

PM Lane 398 closes a narrow naming-coherence gap inside the canonical `/pm-review/import-intake` workbench.

The route already used `pm-import-intake-*` storage keys and the governed `import-intake` route name, but its browser-local export filename helpers still fell back to the older historical identifier `project-miner-intake` whenever `candidate_id` was absent. That mismatch could leak stale artifact names into local review packets and future handoff evidence even though the canonical route and current PM lane vocabulary had already moved to `import-intake`.

## Root Cause

`apps/operations-web/app/pm-review/import-intake/page.tsx` duplicated the same fallback string across every export filename helper:

```text
project-miner-intake
```

Because the fallback stem was repeated per helper instead of normalized once, the historical identifier persisted long after the route, storage keys, and PM lane naming had moved to `import-intake`.

## Change Surface

Updated file:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`

Implemented change:

1. Added one canonical fallback constant: `import-intake`
2. Added one shared `candidateFileStem(...)` helper for export filename generation
3. Routed all browser-local export filename helpers through that shared helper

Representative effect:

```text
Before fallback: project-miner-intake-intake-brief.md
After fallback:  import-intake-intake-brief.md
```

The same alignment now applies to the approval preview, dry-run artifacts, executor handoff, field-prep exports, admission drafts, pilot-launch exports, import exception register, and PM intake snapshot filenames.

## Local Validation

Focused validation for the touched route passed:

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

This lane does not:

1. change any route path,
2. change any export button label or click behavior,
3. change any browser storage key,
4. claim hosted or public-proof impact,
5. widen approval, import, assignment, schedule/status, field, production, customer, or finance authority,
6. add backend mutation or autonomous AI business-state mutation.

## Result

The canonical import-intake workbench now generates locally truthful fallback artifact names that match the governed route vocabulary. When no `candidate_id` is available, export filenames default to `import-intake-*` instead of leaking the stale historical `project-miner-intake` identifier.