# PM Lane 080 Handoff - Local PM Intake Route Link Grouping

Date: 2026-05-16
Status: Local-current implemented
Scope: Browser-local grouping of existing `/pm-review/import-intake` route links

## Executive Summary

PM Lane 080 groups the existing route links in the Daily Intake Starting Point header on `/pm-review/import-intake`.

The same five links are now grouped into:

1. Shell,
2. Intake Reads,
3. PM Workfront.

This is markup and orientation only. It preserves every existing href, route target, quick-jump link, export action, output status, generated filename, export content, read seam, and storage boundary.

It does not add a new route, output, export contract, local storage key, backend route, hosted proof, approval record, import mutation, task, issue, field record, or production write.

## Why This Lane

PM Lane 077 grouped output actions. PM Lane 078 grouped output feedback. PM Lane 079 grouped the quick-jump rail.

The remaining first-screen flat navigation cluster was the `PM intake route links` row: shell, import candidate, admission plan, approval readiness, and PM workfront. PM Lane 080 keeps the same route set but makes the row easier to scan without changing route behavior.

## Sidecar Result

A read-only sidecar recommended PM Lane 080 as the next local slice after PM Lane 079. The recommendation was accepted with a narrow boundary:

1. group only existing route links,
2. preserve every href and route target,
3. do not modify quick-jump, export, status, storage, read, hosted, or mutation behavior,
4. keep PM Lane 076 as the hosted parity delegation boundary.

A separate read-only sidecar recommended PM Lane 081 as local PM intake helper panel stack grouping. It made no edits, ran no tests, created no artifacts, staged nothing, committed nothing, pushed nothing, and accessed no live services.

## What Changed

Operations-web:

1. adds route-link group metadata for Shell, Intake Reads, and PM Workfront,
2. renders the existing route links under those group headings,
3. preserves the existing route-link hrefs for `/`, `/pm-review/import-candidate`, `/pm-review/import-admission-plan`, `/pm-review/import-approval-readiness`, and `/pm-review/workfront`,
4. leaves the quick-jump rail, output action rail, output status rail, exports, localStorage keys, and read seams unchanged.

Focused smoke:

1. asserts the three route-link group headings,
2. asserts group link counts of 1, 3, and 1,
3. asserts each existing route-link href appears exactly once,
4. preserves existing output action, quick-jump, localStorage, download, and zero-mutation coverage.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-080-local-pm-intake-route-link-grouping.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM route-link grouping wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed` after rebuilding the production bundle used by `next start`.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new routes,
3. route target changes,
4. quick-jump link changes,
5. output action changes,
6. output status changes,
7. new localStorage keys,
8. new export actions,
9. new export artifacts,
10. export contract widening,
11. export filename changes,
12. export content changes,
13. new read seams,
14. mutation seam changes,
15. hosted parity claims,
16. SQL file creation,
17. SQL execution,
18. schema migration,
19. Supabase writes,
20. approval persistence,
21. import mutation,
22. live service calls,
23. Render redeploy,
24. Vercel promotion,
25. new service creation,
26. DNS, auth, ingress, or secret changes,
27. fixture replay,
28. workbook macro execution,
29. workbook writeback,
30. work authorization,
31. field release,
32. issue creation,
33. task creation,
34. live work order creation,
35. durable field records,
36. production tracking writes,
37. assignment mutation,
38. schedule mutation,
39. status mutation,
40. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. continue a small local workbench friction reduction recommended by the read-only sidecar, provided it does not overlap with route-link grouping.

The current sidecar recommendation for that local follow-on is PM Lane 081: group the helper-panel stack below the quick-jump rail while preserving existing panel IDs, aria labels, route links, quick jumps, exports, statuses, storage keys, reads, hosted posture, and mutation boundaries.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
