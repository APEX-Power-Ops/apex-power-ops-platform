# PM Lane 083 Handoff - Local PM Intake Authority Wording Smoke Guard

Date: 2026-05-16
Status: Local-current implemented
Scope: Test-only authority wording guard for `/pm-review/import-intake`

## Executive Summary

PM Lane 083 hardens the focused `/pm-review/import-intake` browser smoke after PM Lane 082 stabilized the detail workbench shape.

The smoke now includes a reusable guard that rejects visible action controls implying approval, persistence, import, assignment, schedule, status, task or issue creation, field release, work order, hosted proof, or production readiness. It also verifies the post-082 detail-workbench headings remain review/detail/boundary oriented.

This is test-only governance. It does not add UI, routes, outputs, export contracts, local storage keys, backend routes, hosted proof, approval records, import mutations, tasks, issues, field records, or production writes.

## Why This Lane

PM Lane 080 through PM Lane 082 reduced scan friction by grouping route links, helper panels, and detail panels.

The next risk was governance drift: as the workbench becomes more usable, wording or controls could accidentally start to sound like live production authority. PM Lane 083 turns that manual review concern into a focused smoke assertion.

## Sidecar Result

A read-only sidecar from PM Lane 082 recommended PM Lane 083 as the next local slice after the detail workbench stabilized. The recommendation was accepted with a narrow boundary:

1. touch only the focused import-intake smoke unless the guard catches unsafe wording,
2. do not weaken the existing authority wording scan,
3. preserve route links, quick jumps, exports, statuses, storage, reads, hosted posture, and mutation behavior,
4. keep PM Lane 076 as the hosted parity delegation boundary.

A separate read-only sidecar completed the next-lane scout and recommended PM Lane 084 as Local PM Intake Detail Group Collapse Controls. That sidecar made no file changes and noted the Lane 084 scope should preserve PM Lane 083's no-implied-authority guard.

## What Changed

Operations-web focused smoke:

1. imports the Playwright `Page` type for a reusable helper,
2. adds `impliedAuthorityControlNames`,
3. adds `unsafeAuthorityTextPhrases`,
4. adds `expectNoImpliedAuthorityControls(page)`,
5. asserts no implied-authority action controls before and after local interactions,
6. asserts PM Lane 082 detail-workbench headings remain `Review Snapshot Detail`, `Source and Exception Detail`, `Approval Prep Detail`, `Executor Closeout Detail`, `Field Prep Detail`, and `Authority Boundary Detail`,
7. asserts the visible workbench does not contain hosted-proof or production-readiness authority phrases,
8. preserves existing route-link, quick-jump, export, output-status, localStorage, read-count, download, and zero-mutation coverage.

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

Authority wording scan:

```powershell
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-083-local-pm-intake-authority-wording-smoke-guard.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM authority wording scan passed with no matches after the smoke guard avoided literal forbidden phrases in test source.
4. focused import-intake Playwright smoke passed with `1 passed` after rebuilding the production bundle used by `next start`.
5. focused PM intake Playwright smoke suite passed with `4 passed` after rerunning separately from the production build.
6. initial full-suite attempt run in parallel with the production build failed with a server-start race, not a product assertion failure.
7. packet JSON parse passed with `packet-json-ok`.
8. `git diff --check` passed.
9. `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. UI changes unless the guard catches unsafe wording,
2. backend endpoint changes,
3. new routes,
4. route target changes,
5. quick-jump link changes,
6. output action changes,
7. output status changes,
8. detail panel content changes,
9. detail panel id changes,
10. existing detail panel aria-label changes,
11. new localStorage keys,
12. new export actions,
13. new export artifacts,
14. export contract widening,
15. export filename changes,
16. export content changes,
17. new read seams,
18. mutation seam changes,
19. hosted parity claims,
20. SQL file creation,
21. SQL execution,
22. schema migration,
23. Supabase writes,
24. approval persistence,
25. import mutation,
26. live service calls,
27. Render redeploy,
28. Vercel promotion,
29. new service creation,
30. DNS, auth, ingress, or secret changes,
31. fixture replay,
32. workbook macro execution,
33. workbook writeback,
34. work authorization,
35. field release,
36. issue creation,
37. task creation,
38. live work order creation,
39. durable field records,
40. production tracking writes,
41. assignment mutation,
42. schedule mutation,
43. status mutation,
44. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. continue PM Lane 084, Local PM Intake Detail Group Collapse Controls, as a browser-local default-open collapse-control ergonomics slice that preserves PM Lane 083's authority guard.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
