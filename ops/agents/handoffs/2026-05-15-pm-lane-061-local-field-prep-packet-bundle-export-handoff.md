# PM Lane 061 Handoff - Local Field Prep Packet Bundle Export

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local Field Prep Packet Markdown bundle in the Project Miner intake workbench

## Executive Summary

PM Lane 061 adds `Export Field Prep Packet` to `/pm-review/import-intake`.

The export creates one browser-local Markdown packet that bundles the field prep queue, coverage snapshot, conversation agenda, readiness evidence, questions draft, observation scratchpad, review/closeout context, workflow gates, future-not-admitted surfaces, and guardrails.

The practical purpose is to reduce Jason's export and relay burden before Temp Power work begins. Instead of pulling five separate prep artifacts into a PM, lead, customer, or field conversation, the workbench can produce one local prep bundle.

This is not an admitted execution packet or import packet. It is browser-local conversation prep only and grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, or mutate production state.

## What Changed

The workbench now includes:

1. `Export Field Prep Packet`
2. `fieldPrepPacketFileName(...)`
3. `buildFieldPrepPacket(...)`
4. `fieldPrepPacketStatus`
5. focused smoke coverage for download filename, bundle content, no new localStorage key, exact four read seams, zero mutation calls, reset behavior, and no approve/persist/submit/import controls

The packet is derived from existing loaded reads and existing browser-local state. It adds no new form and no new storage key.

## Bundle Contents

The Markdown packet includes:

1. candidate context,
2. proposed workpackage, task, apparatus, warning, and human-decision counts,
3. local field prep queue,
4. local field prep coverage snapshot,
5. local field prep conversation agenda,
6. checked field readiness evidence,
7. field questions draft,
8. field observation scratchpad,
9. review and executor closeout context,
10. PM operating queue,
11. workflow gates,
12. future-not-admitted surfaces,
13. not-allowed guardrails,
14. minimum-use instructions.

The download filename is:

```text
<candidate_id>-field-prep-packet.md
```

## Boundary

The packet consumes only:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
browser-local review checklist
browser-local approval-decision draft
browser-local executor closeout checklist
browser-local field readiness checklist
browser-local field questions draft
browser-local field observation scratchpad
derived local PM operating queue
derived local field prep queue
derived local field prep coverage snapshot
derived local field prep conversation agenda
```

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the planned scope and confirmed a browser-local `Project Miner Local Field Prep Packet` Markdown export is a reasonable bounded next step if treated only as consolidation/export ergonomics.

It specifically warned that the word `Packet` can sound like an admitted APEX execution packet or import packet, so the implemented wording repeats `Local Field Prep Packet`, `browser-local conversation prep only`, and the no-authority boundary.

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

Field-prep packet wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-061-local-field-prep-packet-bundle-export.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. field-prep packet wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed` after a stale source-fingerprint expectation in the new packet assertion was corrected.
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

After this local bundle is validated, the next PM lane should either improve exception-review ergonomics inside the same intake workbench or prepare a separate explicit admission packet for durable execution tracking. Durable field records and production tracking should remain blocked until that later packet exists and is accepted.
