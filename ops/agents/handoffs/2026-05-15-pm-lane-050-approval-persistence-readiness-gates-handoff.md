# PM Lane 050 Handoff - Approval Persistence Readiness Gates

Date: 2026-05-15
Status: Local-current implemented
Scope: Project Miner intake workbench readiness context for future approval persistence

## Executive Summary

PM Lane 050 keeps the workbench moving toward real PM operations without opening a write path.

`/pm-review/import-intake` now includes an `Approval Persistence Readiness` panel. It shows what is locally ready for a later approval-persistence packet and what remains blocked before any live approval record, schema, adapter, or import mutation can exist.

This is local review context only. It does not approve, persist, import, create schema, run SQL, call live services, deploy, assign work, schedule work, change status, or mutate production state.

## What Changed

The import-intake workbench now displays six readiness gates:

1. `Approval preview context`
2. `Review checklist evidence`
3. `Hosted parity closeout`
4. `Schema authority`
5. `Approval persistence authority`
6. `Import mutation authority`

The first two can become ready from browser-local review prep. The remaining four stay blocked until later admitted packets close hosted parity, grant schema authority, grant approval persistence authority, and separately admit import mutation authority.

The Markdown PM brief now includes an `Approval Persistence Readiness` section with the gate count and gate status details.

## Boundary

This lane intentionally keeps PM Lane 049 as design-only. The future target remains:

```text
seam.pm_import_candidate_approvals
```

The future route remains:

```text
/api/v1/mutations/project-import-approvals
```

Those are still future surfaces. PM Lane 050 does not implement either one.

## Sidecar Result

A read-only sidecar reviewed the intended boundary and recommended:

1. keep future route/table wording framed as design-only,
2. avoid active authority language such as save, submit, approve, persist, or import,
3. keep exact read-count and zero-mutation smoke guards,
4. add browser-local proof for candidate-scoped `localStorage` state.

Those recommendations were accepted. The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, and did not call live services.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-050-approval-persistence-readiness-gates.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. focused import-intake Playwright smoke passed with `1 passed`.
4. focused PM intake Playwright smoke suite passed with `4 passed`.
5. packet JSON parse passed with `packet-json-ok`.
6. `git diff --check` passed with line-ending normalization warnings only.
7. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. SQL file creation,
3. SQL execution,
4. schema migration,
5. Supabase writes,
6. adapter implementation,
7. approval persistence,
8. import mutation,
9. live service calls,
10. Render redeploy,
11. Vercel promotion,
12. hosted parity claim,
13. service creation,
14. DNS, auth, ingress, or secret changes,
15. fixture replay,
16. workbook macro execution,
17. workbook writeback,
18. assignment mutation,
19. schedule mutation,
20. status mutation,
21. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 041A/041B as the hosted parity lanes. Once hosted parity is green or a blocker is precisely accepted, the next bounded execution packet can implement the dedicated approval schema and insert-only adapter from PM Lane 049, still without importing project rows.
