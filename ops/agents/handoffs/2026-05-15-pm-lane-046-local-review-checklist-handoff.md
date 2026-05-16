# PM Lane 046 Handoff - Project Miner PM Intake Local Review Checklist

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Browser-local PM review checklist on `/pm-review/import-intake`

## Executive Summary

PM Lane 046 adds a candidate-scoped, browser-local review checklist to the Project Miner intake workbench:

```text
Local Review Checklist
```

The checklist gives Jason or a bounded executor a lightweight way to mark what has been reviewed before exporting the PM intake brief. It stays local to the browser and current candidate, and it does not approve, persist, import, assign, schedule, change status, mutate production data, or claim hosted parity.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-046-local-review-checklist.json`

## Checklist Behavior

The checklist is stored only in browser `localStorage` under the current candidate:

```text
pm-import-intake-review-checklist:${candidate_id}
```

The checklist covers:

1. source freshness reviewed,
2. warnings reviewed,
3. PM decisions captured,
4. admission no-go checks reviewed,
5. approval storage understood,
6. hosted parity acknowledged,
7. write guardrails confirmed.

The `Export PM Brief` Markdown now includes a `Local Review Checklist` section with progress and checked/unchecked states. This makes the brief better as review context or executor handoff without turning it into approval or persistence.

## Sidecar Result

A read-only sidecar confirmed the safest scope:

1. candidate-scoped browser-local checklist only,
2. review-prep confirmations only,
3. local Markdown export evidence only,
4. no approval, persistence, imports, schema migration, backend mutations, hosted deployment, or live service validation.

The sidecar also recommended a catch-all unmocked `/api/v1/**` smoke guard. That recommendation was accepted so the import-intake smoke fails if the route makes any accidental live or unmocked API call.

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
5. the checklist starts at `0 of 7`,
6. checking two boxes shows `2 of 7`,
7. the downloaded brief includes the checked and unchecked checklist states,
8. clearing the checklist returns the UI to `0 of 7`.

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

Keep PM Lane 041A/041B as the hosted parity lanes. Locally, the next product slice should either prepare the dedicated approval-persistence schema and adapter admission packet as design-only, or add more exception-first review aids to the intake workbench if Jason needs another low-friction review reducer before persistence.
