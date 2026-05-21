# APEX PM Lane 403 - Import-Intake Post-Approval Prerequisite Reconciliation Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_POST_APPROVAL_PREREQUISITE_RECONCILIATION`

## Purpose

PM Lane 403 closes the next bounded product tranche after PM Lane 402 proved the live hosted approval readback and hydrated browser state.

The remaining local inconsistency was inside the import-intake route itself: several downstream field-execution, assignment, authorization, pilot-launch, and export surfaces still described the first approval row as blocked even though the live approval-status readback already returned `approved_for_import_packet` with one approval record for the current candidate.

## Root Cause

The route had already been partially reconciled in PM Lane 401 with count-aware approval-readback copy, but several downstream builders still carried older hardcoded first-row assumptions.

Those stale assumptions appeared in:

1. downstream draft/export gate items,
2. pilot-launch approval live-gate text,
3. repeated hosted approval remaining-block summaries,
4. the dry-run write-boundary panel,
5. the focused import-intake smoke assertion that still expected the older fallback wording.

## Change Surface

Product files changed:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Repo governance files changed:

1. `PROJECT_STATUS.md`
2. `docs/operations/APEX-PM-LANE-403-IMPORT-INTAKE-POST-APPROVAL-PREREQUISITE-RECONCILIATION-PACKET-2026-05-19.md`
3. `ops/agents/handoffs/2026-05-19-pm-lane-403-import-intake-post-approval-prerequisite-reconciliation-closeout-handoff.md`

## Implementation

`/pm-review/import-intake` now uses shared approval-state helpers so accepted hosted approval state drives downstream copy and readiness consistently.

Implemented behavior:

1. added shared helpers that recognize an accepted approval record when readback returns `approved_for_import_packet` with a nonzero approval-record count,
2. changed downstream prerequisite items from unconditional `blocked` to approval-state-aware `ready/blocked` status where appropriate,
3. updated downstream detail text so accepted approval state becomes “prerequisite satisfied” instead of “first row still blocked”,
4. updated repeated boundary/export lines so accepted readback switches from “first approval-row creation” wording to “additional approval-row mutation” wording while keeping browser submission and project import blocked,
5. updated the focused import-intake smoke assertion to match the current zero-record fallback wording that remains valid for mocked blocked-state coverage.

## Validation

Focused validation passed:

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit

corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
1 passed
```

## Boundary

This lane does not:

1. add or change backend routes,
2. wire browser approval POST,
3. create or mutate approval rows,
4. admit project import or downstream write authority,
5. change schema, payload shape, or hosted services,
6. widen assignment, schedule/status, field, production, customer, finance, auth, ingress, or secret scope,
7. perform autonomous AI business-state mutation.

## Result

The import-intake route now truthfully reflects the current post-approval hosted state across its downstream prerequisite panels and exported draft artifacts. An accepted approval record is treated as an already-satisfied prerequisite where appropriate, while browser approval submission, additional approval-row mutation, and all downstream write paths remain explicitly blocked until later admitted packets.