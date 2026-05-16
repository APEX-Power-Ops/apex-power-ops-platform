# PM Lane 062 Handoff - Local Import Exception Decision Register

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived import exception decision register and export in the Project Miner intake workbench

## Executive Summary

PM Lane 062 adds a `Local Import Exception Decision Register` and `Export Import Exception Register` action to `/pm-review/import-intake`.

The register consolidates source freshness evidence, candidate warning signals, human decision prompts, admission no-go checks, local decision draft evidence, and the future write boundary into covered/open/blocked review synthesis.

The point is practical: reduce Jason's exception-review burden before Temp Power intake decisions. He should not need to reconstruct the exception path from five separate panels or packet docs.

This is browser-local review synthesis only. It grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, or mutate production state.

## What Changed

The workbench now includes:

1. `Local Import Exception Decision Register`
2. `Export Import Exception Register`
3. `importExceptionRegisterFileName(...)`
4. `buildImportExceptionRegister(...)`
5. `buildImportExceptionRegisterExport(...)`
6. PM brief inclusion for the register
7. executor handoff inclusion for the register
8. focused smoke coverage for default and updated register states, no new localStorage key, standalone export content, PM brief content, executor handoff content, reset behavior, exact four read seams, zero mutation calls, and no approve/persist/submit/import controls

The register is derived from existing loaded reads and existing browser-local state. It adds no new form and no new storage key.

## Register Logic

The register uses three statuses:

1. `covered` means local review evidence is present.
2. `open` means local review evidence still needs attention.
3. `blocked` means the future write or import path remains blocked.

Current register items:

1. source freshness evidence,
2. candidate warning signals,
3. human decision prompts,
4. admission no-go checks,
5. local decision draft evidence,
6. future write boundary.

The word `covered` is review-synthesis language only. It does not mean resolved, admitted, or cleared for production action.

## Export Surfaces

The register appears in:

1. `/pm-review/import-intake`,
2. `Export PM Brief`,
3. `Export Executor Handoff`,
4. `Export Import Exception Register`.

It is intentionally not added to Approval Preview JSON or field-prep exports because this packet does not widen those contracts.

`Export Import Exception Register` produces:

```text
<candidate_id>-import-exception-register.md
```

## Boundary

The register consumes only:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
browser-local review checklist
browser-local approval-decision draft
derived local PM operating queue
derived local import exception decision register
```

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the planned scope and confirmed a browser-local derived `Local Import Exception Decision Register` is the right bounded PM lane after Lane 061. It recommended including the register in the PM brief and executor handoff, while keeping it out of Approval Preview JSON and field-prep exports unless a later packet explicitly widens those contracts.

The sidecar warned to keep `Local` and `browser-local review synthesis` prominent and to avoid language that implies approval, acceptance, release, admission, authorization, or production action.

The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, ran no macros, and did not access Supabase, Render, or Vercel.

## Validation

Commands are run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Operations-web typecheck:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Operations-web build:

```powershell
corepack pnpm --filter @apex/operations-web build
```

Exception-register wording scan:

```powershell
rg -n "ready for field|ready for execution|field ready|field log of record|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|assigned|scheduled|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused import-intake smoke:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused PM intake smoke suite:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Packet JSON parse:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-062-local-import-exception-decision-register.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. exception-register wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed` after duplicate text assertions were narrowed for the new register and the no-import-button guard was narrowed to a bare import action.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new localStorage keys,
3. durable field records,
4. production tracking writes,
5. work authorization,
6. field release,
7. issue creation,
8. task creation,
9. live work order creation,
10. live task creation,
11. hosted parity claims,
12. SQL file creation,
13. SQL execution,
14. schema migration,
15. Supabase writes,
16. adapter implementation,
17. approval persistence,
18. import mutation,
19. live service calls,
20. Render redeploy,
21. Vercel promotion,
22. service creation,
23. DNS, auth, ingress, or secret changes,
24. fixture replay,
25. workbook macro execution,
26. workbook writeback,
27. assignment mutation,
28. schedule mutation,
29. status mutation,
30. autonomous AI business-state mutation.

## Next Recommended Move

After this register is validated, the next PM lane should either improve visual scan ergonomics for the import-intake route or author the next explicit hosted parity/executor refresh if hosted proof becomes the controlling blocker. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are accepted.
