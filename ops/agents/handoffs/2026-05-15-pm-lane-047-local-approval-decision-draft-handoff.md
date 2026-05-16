# PM Lane 047 Handoff - Project Miner PM Intake Approval-Decision Draft

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Browser-local approval-decision draft on `/pm-review/import-intake`

## Executive Summary

PM Lane 047 adds a candidate-scoped, browser-local decision draft to the Project Miner intake workbench:

```text
Local Approval Decision Draft
```

The draft captures a future approval decision value, review notes, and local-only attestation for the Markdown PM brief. It is designed to reduce future packet relay work without creating an approval record or admitting any persistence, import, schema, backend, hosted, assignment, schedule, status, or production write path.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-047-local-approval-decision-draft.json`

## Draft Behavior

The draft is stored only in browser `localStorage` under the current candidate:

```text
pm-import-intake-approval-draft:${candidate_id}
```

The draft includes:

1. `Decision draft`, sourced from the read-only `approval_record_contract.permitted_decisions`,
2. `Review notes draft`, for PM exception assumptions and open questions,
3. `Local-only draft attestation`, confirming that a later admitted packet must own approval persistence or import mutation,
4. `Clear decision draft`, which resets local browser state.

The `Export PM Brief` Markdown now includes:

1. `## Local Approval Decision Draft`,
2. draft-present status,
3. decision draft value,
4. attestation status,
5. review notes draft.

This section is review-prep context only. It is not the canonical approval record.

## Sidecar Result

A read-only sidecar confirmed that the safest next slice is smoke coverage and retention of the local approval-decision draft UI, not backend or schema work.

The accepted sidecar recommendations were:

1. keep the draft browser-local and candidate-scoped,
2. use permitted decisions from the read-only approval contract,
3. include notes and local-only attestation,
4. include the draft in the Markdown PM brief,
5. assert clear/reset behavior,
6. preserve no live service calls and no mutation calls.

The smoke uses `return_for_revision` as the exercised decision value so the local proof does not imply that the screen approved the candidate.

## Validation

Commands run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Operations-web typecheck:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Result:

```text
passed
```

Operations-web production build:

```powershell
corepack pnpm --filter @apex/operations-web build
```

Result:

```text
passed; route output included /pm-review/import-intake
```

Focused import-intake smoke:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Result:

```text
1 passed
```

Focused PM intake smoke suite:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Result:

```text
4 passed
```

The strengthened import-intake smoke proves:

1. all four PM intake reads are called exactly once,
2. no unmocked `/api/v1/**` request is allowed,
3. zero mutation routes are called,
4. no `Approve`, `Persist`, `Submit`, or `Import` button is present,
5. the local decision draft renders,
6. `return_for_revision` can be selected from permitted decisions,
7. review notes and local-only attestation are captured,
8. the downloaded brief includes the local decision draft section,
9. clearing the decision draft resets select, notes, attestation, and disables the clear button.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. hosted deployment,
3. Vercel promotion,
4. Render redeploy,
5. approval persistence,
6. import mutation,
7. schema migration,
8. SQL write,
9. live database write,
10. workbook macro execution,
11. workbook writeback,
12. service admission,
13. auth or ingress widening,
14. assignment mutation,
15. schedule mutation,
16. status mutation,
17. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 041A/041B as the hosted parity lanes. Locally, the next useful product slice is an approval-persistence schema and adapter admission packet in design-only form, using the draft decision shape as evidence input but still deferring actual persistence until hosted parity is green or the blocker is precisely accepted.
