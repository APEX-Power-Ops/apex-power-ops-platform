# APEX PM Lane 401 - Import-Intake Approval-Readback Count Copy Alignment Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_APPROVAL_READBACK_COUNT_COPY_ALIGNMENT`

## Purpose

PM Lane 401 closes the next adjacent coherence gap inside the canonical `/pm-review/import-intake` workbench.

After PM Lane 400 promoted the latest import-intake route to production, the public workbench still showed a mixed approval-readback posture: `Approval Status Readback` reported an existing approval record for the current candidate while nearby readiness and guardrail copy still claimed approval rows were at zero. That left the route internally contradictory on the same page.

## Root Cause

`apps/operations-web/app/pm-review/import-intake/page.tsx` mixed dynamic approval-readback status with hardcoded zero-row boundary strings in the readiness gates, PM operating queue, and current guardrails.

Representative stale phrases before this lane:

```text
Hosted schema, approval status readback, approval POST route registration, and bounded MCP read proof are green with zero approval rows.
Treat hosted schema, hosted readback, and bounded Supabase read proof as green, with approval rows still at zero.
```

## Change Surface

Updated file:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`

Implemented change:

1. Added shared helpers for approval-record count summaries and count-aware boundary detail
2. Routed approval persistence readiness copy through those helpers
3. Routed PM operating queue boundary copy through those helpers
4. Routed current guardrail copy through those helpers

Representative effect:

```text
Before: approval rows still at zero
After:  current readback shows 1 approval record for this candidate
```

## Local Validation

Focused validation for the touched route passed:

```text
grep in apps/operations-web/app/pm-review/import-intake/page.tsx
No remaining source matches for:
- approval rows still at zero
- green with zero approval rows

corepack pnpm --dir apps/operations-web typecheck
PASS
```

## Boundary

This lane does not:

1. change any route path,
2. change any payload schema field or approval-readback storage shape,
3. add or wire a browser approval button or POST,
4. admit approval-row creation, import mutation, assignment, schedule/status, field, production, customer, or finance writes,
5. claim hosted or public-proof impact,
6. change services, schema, secrets, or auth,
7. add autonomous AI business-state mutation.

## Result

The canonical import-intake workbench now keeps its approval-readback boundary copy consistent with the actual approval status readback count. When the current candidate already has approval records, the readiness and guardrail surfaces no longer claim the route is still at zero rows; when the count is truly zero, the zero-row boundary copy remains available through the same shared helpers.