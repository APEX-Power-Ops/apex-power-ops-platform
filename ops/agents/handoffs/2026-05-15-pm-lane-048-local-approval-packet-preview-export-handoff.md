# PM Lane 048 Handoff - Project Miner PM Intake Approval Packet Preview Export

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Browser-only approval packet preview JSON export from `/pm-review/import-intake`

## Executive Summary

PM Lane 048 adds a local export action to the Project Miner intake workbench:

```text
Export Approval Preview JSON
```

The downloaded JSON is a structured preview of the future approval-persistence packet input. It combines the current read-only candidate, admission plan, approval contract, approval storage plan, local checklist, and local approval-decision draft without creating an approval record or admitting any persistence, import, backend, schema, hosted, assignment, schedule, status, or production write path.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-048-local-approval-packet-preview-export.json`

## Preview Behavior

The preview is generated entirely in the browser from:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

The downloaded filename is derived from the candidate id:

```text
pm-import-candidate-miner-temp-power-approval-packet-preview.json
```

The JSON includes:

1. preview kind and version,
2. browser-local timestamp,
3. mutation and persistence authority,
4. candidate identity and source fingerprint,
5. approval contract shape,
6. approval storage plan target table and route,
7. local checklist evidence,
8. local approval-decision draft,
9. future packet boundary and required later authority.

This artifact is context for a later admitted packet only. It is not a canonical approval record.

## Sidecar Result

A read-only sidecar confirmed the safest scope:

1. browser-only JSON download,
2. only four current read surfaces plus local checklist and local draft state,
3. no backend route,
4. no schema,
5. no persistence,
6. no import,
7. no hosted service call,
8. no production write.

The sidecar recommended the exact JSON fields and smoke assertions used in this tranche.

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
5. the JSON preview downloads with the expected filename,
6. the parsed JSON includes candidate identity, source fingerprint, contract, storage, checklist, draft decision, notes, attestation, and future boundary,
7. the preview is reported as prepared without a server write.

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

Keep PM Lane 041A/041B as the hosted parity lanes. Locally, the next useful product slice is to author the approval-persistence schema and adapter admission packet in design-only form, using the preview JSON shape as the input contract and keeping actual persistence blocked until the packet is explicitly admitted.
